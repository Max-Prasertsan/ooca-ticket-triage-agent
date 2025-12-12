"""
PagerDuty Tools
================

MCP-style tools for PagerDuty integration.

These tools simulate connecting to PagerDuty via MCP to:
- Check for active incidents that may be related to customer issues
- Create incidents to page on-call engineers for critical issues

In production, these would connect to a real PagerDuty MCP server.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Optional, Type

from pydantic import BaseModel, Field

from src.triage_agent.tools.base import BaseTool

logger = logging.getLogger(__name__)


# =============================================================================
# Mock PagerDuty Data
# =============================================================================

MOCK_ACTIVE_INCIDENTS = [
    {
        "id": "P-INC-2024-0115-001",
        "title": "Elevated API error rates in us-east-1",
        "status": "triggered",
        "urgency": "high",
        "service": "api-gateway",
        "service_id": "SVC-API-001",
        "created_at": "2024-01-15T08:45:00Z",
        "escalation_policy": "Engineering On-Call",
        "assigned_to": "david.wang",
        "description": "API gateway showing 5% error rate, primarily 503 responses.",
        "num_alerts": 12
    },
    {
        "id": "P-INC-2024-0115-002",
        "title": "Database replication lag warning",
        "status": "acknowledged",
        "urgency": "low",
        "service": "database-primary",
        "service_id": "SVC-DB-001",
        "created_at": "2024-01-15T10:30:00Z",
        "escalation_policy": "DBA On-Call",
        "assigned_to": "anna.dba",
        "description": "Replica lag increased to 30 seconds. Monitoring.",
        "num_alerts": 3
    },
]

MOCK_ON_CALL_SCHEDULE = {
    "engineering": {
        "user": "david.wang",
        "email": "david.wang@company.com",
        "phone": "+1-555-0101",
        "shift_start": "2024-01-15T00:00:00Z",
        "shift_end": "2024-01-22T00:00:00Z"
    },
    "support": {
        "user": "emma.support",
        "email": "emma@company.com",
        "phone": "+1-555-0102",
        "shift_start": "2024-01-15T08:00:00Z",
        "shift_end": "2024-01-15T20:00:00Z"
    },
    "dba": {
        "user": "anna.dba",
        "email": "anna.dba@company.com",
        "phone": "+1-555-0103",
        "shift_start": "2024-01-14T00:00:00Z",
        "shift_end": "2024-01-21T00:00:00Z"
    }
}

# Track created incidents for demo
MOCK_CREATED_INCIDENTS = []
_incident_counter = 3


# =============================================================================
# PagerDuty Incidents Tool
# =============================================================================

class PagerDutyIncidentsInput(BaseModel):
    """Input schema for getting active PagerDuty incidents."""
    service_id: Optional[str] = Field(
        None,
        description="Filter by service ID (e.g., SVC-API-001). If not provided, returns all."
    )
    urgency: Optional[str] = Field(
        None,
        description="Filter by urgency: 'high' or 'low'. If not provided, returns all."
    )
    status: Optional[str] = Field(
        None,
        description="Filter by status: 'triggered', 'acknowledged', or 'resolved'."
    )


class PagerDutyIncident(BaseModel):
    """A PagerDuty incident."""
    id: str
    title: str
    status: str
    urgency: str
    service: str
    created_at: str
    assigned_to: Optional[str] = None
    description: str = ""
    num_alerts: int = 0


class PagerDutyIncidentsOutput(BaseModel):
    """Output schema for PagerDuty incidents query."""
    incidents: list[PagerDutyIncident] = Field(default_factory=list)
    total: int = 0
    has_critical: bool = False


class PagerDutyIncidentsTool(BaseTool[PagerDutyIncidentsInput, PagerDutyIncidentsOutput]):
    """
    Tool for checking active PagerDuty incidents.
    
    Use this tool to check if there are ongoing incidents that might be
    related to the customer's issue. This helps determine if the problem
    is already known and being worked on.
    
    When to use:
    - Customer reports outage or service issues
    - Multiple customers reporting similar problems
    - Error patterns that might indicate system-wide issues
    - Before escalating to check if incident already exists
    
    This tool helps avoid duplicate escalations and provides context
    about ongoing infrastructure issues.
    """
    
    name: str = "pagerduty_incidents"
    description: str = (
        "Check for active PagerDuty incidents. Use this to see if there are "
        "ongoing incidents related to the customer's issue, check if the problem "
        "is already being investigated, or get context about system-wide issues."
    )
    input_model: Type[PagerDutyIncidentsInput] = PagerDutyIncidentsInput
    output_model: Type[PagerDutyIncidentsOutput] = PagerDutyIncidentsOutput
    
    def _execute(self, input_data: PagerDutyIncidentsInput) -> PagerDutyIncidentsOutput:
        """Get mock active incidents."""
        results = []
        
        for incident in MOCK_ACTIVE_INCIDENTS:
            # Apply filters
            if input_data.service_id and incident["service_id"] != input_data.service_id:
                continue
            if input_data.urgency and incident["urgency"] != input_data.urgency:
                continue
            if input_data.status and incident["status"] != input_data.status:
                continue
            
            results.append(PagerDutyIncident(
                id=incident["id"],
                title=incident["title"],
                status=incident["status"],
                urgency=incident["urgency"],
                service=incident["service"],
                created_at=incident["created_at"],
                assigned_to=incident["assigned_to"],
                description=incident["description"],
                num_alerts=incident["num_alerts"]
            ))
        
        # Check if any are high urgency
        has_critical = any(i.urgency == "high" for i in results)
        
        return PagerDutyIncidentsOutput(
            incidents=results,
            total=len(results),
            has_critical=has_critical
        )


# =============================================================================
# PagerDuty Create Incident Tool
# =============================================================================

class PagerDutyCreateInput(BaseModel):
    """Input schema for creating PagerDuty incidents."""
    title: str = Field(
        ...,
        description="Incident title - brief description of the issue"
    )
    service_id: str = Field(
        default="SVC-SUPPORT-001",
        description="Service ID to page (determines escalation policy)"
    )
    urgency: str = Field(
        default="high",
        description="Urgency: 'high' (pages immediately) or 'low' (no immediate page)"
    )
    description: str = Field(
        default="",
        description="Detailed incident description with context"
    )
    ticket_id: Optional[str] = Field(
        None,
        description="Associated support ticket ID for reference"
    )
    customer: Optional[str] = Field(
        None,
        description="Customer name/identifier if enterprise"
    )


class PagerDutyCreateOutput(BaseModel):
    """Output schema for creating PagerDuty incidents."""
    success: bool = True
    incident_id: str = ""
    status: str = ""
    created_at: str = ""
    assigned_to: Optional[str] = None
    escalation_policy: str = ""
    error: Optional[str] = None


class PagerDutyCreateTool(BaseTool[PagerDutyCreateInput, PagerDutyCreateOutput]):
    """
    Tool for creating PagerDuty incidents to page on-call engineers.
    
    Use this tool to page on-call engineers for CRITICAL issues that
    require immediate human intervention. This should be used sparingly
    and only for truly urgent situations.
    
    When to use:
    - Production outage affecting enterprise customers
    - Security incidents
    - Data integrity issues
    - Issues where SLA is at risk
    
    When NOT to use:
    - Feature requests
    - Non-urgent bugs
    - Issues with known workarounds
    - Already-acknowledged incidents (check first!)
    
    IMPORTANT: Always check active incidents before creating a new one
    to avoid duplicate pages.
    """
    
    name: str = "pagerduty_create"
    description: str = (
        "Create a PagerDuty incident to page on-call engineers. "
        "Use ONLY for CRITICAL issues requiring immediate intervention, such as "
        "production outages or enterprise customer emergencies. "
        "Always check active incidents first to avoid duplicates."
    )
    input_model: Type[PagerDutyCreateInput] = PagerDutyCreateInput
    output_model: Type[PagerDutyCreateOutput] = PagerDutyCreateOutput
    
    def _execute(self, input_data: PagerDutyCreateInput) -> PagerDutyCreateOutput:
        """Create a mock PagerDuty incident."""
        global _incident_counter
        
        # Generate incident ID
        _incident_counter += 1
        today = datetime.now().strftime("%Y-%m%d")
        incident_id = f"P-INC-{today}-{_incident_counter:03d}"
        created_at = datetime.now(timezone.utc).isoformat()
        
        # Determine on-call person based on service
        on_call = MOCK_ON_CALL_SCHEDULE.get("engineering", {})
        assigned_to = on_call.get("user", "on-call-engineer")
        
        # Build description with context
        full_description = input_data.description
        if input_data.ticket_id:
            full_description += f"\n\nSupport Ticket: {input_data.ticket_id}"
        if input_data.customer:
            full_description += f"\nCustomer: {input_data.customer}"
        
        # Store the created incident
        new_incident = {
            "id": incident_id,
            "title": input_data.title,
            "status": "triggered",
            "urgency": input_data.urgency,
            "service_id": input_data.service_id,
            "description": full_description,
            "created_at": created_at,
            "assigned_to": assigned_to,
            "escalation_policy": "Engineering On-Call"
        }
        MOCK_CREATED_INCIDENTS.append(new_incident)
        
        logger.info(f"Created PagerDuty incident: {incident_id} - {input_data.title}")
        logger.info(f"Paging on-call: {assigned_to}")
        
        return PagerDutyCreateOutput(
            success=True,
            incident_id=incident_id,
            status="triggered",
            created_at=created_at,
            assigned_to=assigned_to,
            escalation_policy="Engineering On-Call"
        )