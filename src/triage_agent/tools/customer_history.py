"""
Customer History Tool
======================

Tool for looking up customer information, past tickets,
and risk indicators from the CRM system.

This implementation uses mock data for demonstration.
In production, this would integrate with a real CRM
(Salesforce, HubSpot, etc.).
"""

import logging
from typing import Type

from src.triage_agent.models.tools import (
    CustomerHistoryInput,
    CustomerHistoryOutput,
    PastTicketSummary,
)
from src.triage_agent.tools.base import BaseTool

logger = logging.getLogger(__name__)


# Mock customer database
MOCK_CUSTOMERS = {
    "cto@bigcorp.com": {
        "name": "Sarah Chen",
        "tier": "enterprise",
        "created": "2021-03-15",
        "lifetime_value": 500000.00,
        "is_at_risk": False,
        "notes": "Key enterprise account. Direct line to CEO. Very technical.",
        "past_tickets": [
            {
                "ticket_id": "T-0891",
                "date": "2023-11-20",
                "subject": "API rate limits",
                "resolution": "Increased limits per SLA",
                "satisfaction_score": 5
            },
            {
                "ticket_id": "T-0654",
                "date": "2023-08-05",
                "subject": "SSO configuration help",
                "resolution": "Configured SAML integration",
                "satisfaction_score": 5
            }
        ]
    },
    "mike.johnson@startup.io": {
        "name": "Mike Johnson",
        "tier": "pro",
        "created": "2023-09-01",
        "lifetime_value": 1200.00,
        "is_at_risk": False,
        "notes": None,
        "past_tickets": [
            {
                "ticket_id": "T-0923",
                "date": "2023-12-01",
                "subject": "Upgrade to Pro",
                "resolution": "Assisted with upgrade",
                "satisfaction_score": 4
            }
        ]
    },
    "emma.dev@techcompany.com": {
        "name": "Emma Rodriguez",
        "tier": "pro",
        "created": "2022-06-20",
        "lifetime_value": 3600.00,
        "is_at_risk": False,
        "notes": "Very engaged user. Active in community forums.",
        "past_tickets": [
            {
                "ticket_id": "T-0445",
                "date": "2023-02-14",
                "subject": "Feature suggestion: Export formats",
                "resolution": "Forwarded to product team",
                "satisfaction_score": 5
            }
        ]
    },
    "angry.customer@example.com": {
        "name": "Angry Customer",
        "tier": "pro",
        "created": "2022-01-10",
        "lifetime_value": 2400.00,
        "is_at_risk": True,
        "notes": "Has escalated twice in the past. Requested refund once.",
        "past_tickets": [
            {
                "ticket_id": "T-0201",
                "date": "2023-06-15",
                "subject": "Service outage complaint",
                "resolution": "Applied service credit",
                "satisfaction_score": 2
            },
            {
                "ticket_id": "T-0156",
                "date": "2023-04-20",
                "subject": "Billing dispute",
                "resolution": "Partial refund processed",
                "satisfaction_score": 3
            }
        ]
    }
}


class CustomerHistoryTool(BaseTool[CustomerHistoryInput, CustomerHistoryOutput]):
    """
    Tool for looking up customer history and risk indicators.
    
    Retrieves customer information from the CRM including:
    - Account details and tier
    - Past ticket history
    - Customer lifetime value
    - Risk indicators
    
    Attributes:
        name: "customer_history"
        description: Description for the AI agent
        input_model: CustomerHistoryInput
        output_model: CustomerHistoryOutput
    
    Example:
        >>> tool = CustomerHistoryTool()
        >>> input_data = CustomerHistoryInput(customer_email="user@example.com")
        >>> result = tool.execute(input_data)
        >>> print(result.account_tier)
        'enterprise'
    """
    
    name: str = "customer_history"
    description: str = (
        "Look up customer information and history from the CRM. "
        "Returns account details, subscription tier, past ticket history, "
        "lifetime value, and any risk indicators. Use this to understand "
        "the customer's context and history with support."
    )
    input_model: Type[CustomerHistoryInput] = CustomerHistoryInput
    output_model: Type[CustomerHistoryOutput] = CustomerHistoryOutput
    
    def _execute(self, input_data: CustomerHistoryInput) -> CustomerHistoryOutput:
        """
        Execute customer history lookup.
        
        Args:
            input_data: Customer email and lookup options.
        
        Returns:
            CustomerHistoryOutput: Customer information and history.
        """
        email = input_data.customer_email.lower()
        logger.debug(f"Looking up customer: {email}")
        
        # Check if customer exists in mock database
        if email in MOCK_CUSTOMERS:
            customer = MOCK_CUSTOMERS[email]
            
            # Build past tickets list if requested
            past_tickets = []
            if input_data.include_tickets and customer.get("past_tickets"):
                past_tickets = [
                    PastTicketSummary(
                        ticket_id=t["ticket_id"],
                        date=t["date"],
                        subject=t["subject"],
                        resolution=t["resolution"],
                        satisfaction_score=t.get("satisfaction_score")
                    )
                    for t in customer["past_tickets"]
                ]
            
            # Calculate average satisfaction
            avg_satisfaction = None
            if past_tickets:
                scores = [t.satisfaction_score for t in past_tickets if t.satisfaction_score]
                if scores:
                    avg_satisfaction = sum(scores) / len(scores)
            
            logger.info(f"Found customer: {email} (tier: {customer['tier']})")
            
            return CustomerHistoryOutput(
                customer_email=email,
                customer_name=customer["name"],
                account_tier=customer["tier"],
                account_created=customer["created"],
                lifetime_value=customer["lifetime_value"],
                past_tickets=past_tickets,
                past_ticket_count=len(past_tickets),
                average_satisfaction=avg_satisfaction,
                is_at_risk=customer.get("is_at_risk", False),
                notes=customer.get("notes")
            )
        
        # Customer not found - return minimal data
        logger.info(f"Customer not found: {email}, returning default profile")
        
        return CustomerHistoryOutput(
            customer_email=email,
            customer_name=None,
            account_tier="unknown",
            account_created=None,
            lifetime_value=0.0,
            past_tickets=[],
            past_ticket_count=0,
            average_satisfaction=None,
            is_at_risk=False,
            notes="New customer - no history available"
        )