"""
Jira Tools
===========

MCP-style tools for Jira integration.

These tools simulate connecting to Jira via MCP to:
- Search for related tickets and known issues
- Create new tickets for tracking customer issues

In production, these would connect to a real Jira MCP server.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Optional, Type

from pydantic import BaseModel, Field

from src.triage_agent.tools.base import BaseTool

logger = logging.getLogger(__name__)


# =============================================================================
# Mock Jira Data
# =============================================================================

MOCK_JIRA_ISSUES = [
    {
        "key": "SUPPORT-1234",
        "summary": "Enterprise dashboard loading slowly for BigCorp",
        "description": "Customer reports dashboard takes 10+ seconds to load. Affecting multiple users.",
        "status": "In Progress",
        "priority": "High",
        "issue_type": "Bug",
        "assignee": "sarah.chen",
        "reporter": "enterprise-support",
        "created": "2024-01-14T10:00:00Z",
        "updated": "2024-01-15T09:30:00Z",
        "labels": ["enterprise", "performance", "dashboard"]
    },
    {
        "key": "SUPPORT-1198",
        "summary": "Intermittent 503 errors on API gateway",
        "description": "Multiple customers reporting 503 errors during peak hours. Primarily affecting us-east region.",
        "status": "Open",
        "priority": "Critical",
        "issue_type": "Bug",
        "assignee": "mike.ops",
        "reporter": "monitoring-bot",
        "created": "2024-01-15T08:30:00Z",
        "updated": "2024-01-15T10:00:00Z",
        "labels": ["outage", "api", "us-east"]
    },
    {
        "key": "SUPPORT-1156",
        "summary": "Password reset emails not being delivered",
        "description": "Some customers report not receiving password reset emails. Issue traced to email provider.",
        "status": "Resolved",
        "priority": "Medium",
        "issue_type": "Bug",
        "assignee": "emma.support",
        "reporter": "support-queue",
        "created": "2024-01-10T14:00:00Z",
        "updated": "2024-01-12T16:00:00Z",
        "labels": ["authentication", "email"]
    },
    {
        "key": "FEAT-892",
        "summary": "Add dark mode to dashboard",
        "description": "Customer request for dark mode theme option in the dashboard UI.",
        "status": "Backlog",
        "priority": "Low",
        "issue_type": "Feature Request",
        "assignee": None,
        "reporter": "product-feedback",
        "created": "2024-01-05T11:00:00Z",
        "updated": "2024-01-05T11:00:00Z",
        "labels": ["feature-request", "ui", "dashboard"]
    },
    {
        "key": "SUPPORT-1189",
        "summary": "Billing discrepancy for Pro tier customers",
        "description": "Several Pro customers charged incorrect amount. Finance investigating.",
        "status": "In Progress",
        "priority": "High",
        "issue_type": "Bug",
        "assignee": "billing-team",
        "reporter": "finance-alerts",
        "created": "2024-01-13T09:00:00Z",
        "updated": "2024-01-14T17:00:00Z",
        "labels": ["billing", "pro-tier", "urgent"]
    },
]

# Track created issues for demo
MOCK_CREATED_ISSUES = []
_issue_counter = 1300


# =============================================================================
# Jira Search Tool
# =============================================================================

class JiraSearchInput(BaseModel):
    """Input schema for Jira issue search."""
    jql: str = Field(
        ...,
        description=(
            "JQL (Jira Query Language) query to search issues. "
            "Examples: 'project = SUPPORT AND status != Done', "
            "'text ~ \"login issue\"', 'priority = Critical'"
        )
    )
    max_results: int = Field(
        10,
        description="Maximum number of issues to return",
        ge=1,
        le=50
    )


class JiraIssue(BaseModel):
    """A Jira issue result."""
    key: str
    summary: str
    status: str
    priority: str
    issue_type: str
    assignee: Optional[str] = None
    created: str
    updated: str
    labels: list[str] = Field(default_factory=list)


class JiraSearchOutput(BaseModel):
    """Output schema for Jira issue search."""
    issues: list[JiraIssue] = Field(default_factory=list)
    total: int = 0
    jql_processed: str = ""


class JiraSearchTool(BaseTool[JiraSearchInput, JiraSearchOutput]):
    """
    Tool for searching Jira issues.
    
    Use this tool to find related tickets, check if an issue is already
    being tracked, or find previous solutions to similar problems.
    
    When to use:
    - Check if issue already exists before creating a duplicate
    - Find related issues for context
    - Look up previous solutions for similar problems
    - Check status of known bugs
    
    JQL Examples:
    - Find open support tickets: 'project = SUPPORT AND status != Done'
    - Search by keyword: 'text ~ "dashboard slow"'
    - Find critical bugs: 'priority = Critical AND type = Bug'
    - Find by label: 'labels = enterprise'
    """
    
    name: str = "jira_search"
    description: str = (
        "Search Jira issues using JQL (Jira Query Language). "
        "Use this to find related tickets, check if an issue already exists, "
        "or look up previous solutions. Returns matching issues with status and details."
    )
    input_model: Type[JiraSearchInput] = JiraSearchInput
    output_model: Type[JiraSearchOutput] = JiraSearchOutput
    
    def _execute(self, input_data: JiraSearchInput) -> JiraSearchOutput:
        """Search mock Jira issues using simplified JQL parsing."""
        jql_lower = input_data.jql.lower()
        results = []
        
        for issue in MOCK_JIRA_ISSUES:
            match = True
            
            # Simple JQL parsing (mock implementation)
            # Check status filter
            if "status != done" in jql_lower:
                if issue["status"].lower() == "done":
                    match = False
            if "status = open" in jql_lower:
                if issue["status"].lower() != "open":
                    match = False
            
            # Check priority filter
            if "priority = critical" in jql_lower:
                if issue["priority"].lower() != "critical":
                    match = False
            if "priority = high" in jql_lower:
                if issue["priority"].lower() != "high":
                    match = False
            
            # Check text search
            if "text ~" in jql_lower or "text~" in jql_lower:
                # Extract search term (simplified)
                search_terms = []
                for term in jql_lower.split('"'):
                    if len(term) > 2 and "~" not in term and "=" not in term:
                        search_terms.append(term.strip())
                
                if search_terms:
                    text_match = False
                    for term in search_terms:
                        if (term in issue["summary"].lower() or 
                            term in issue["description"].lower()):
                            text_match = True
                            break
                    if not text_match:
                        match = False
            
            # Check label filter
            if "labels =" in jql_lower or "labels=" in jql_lower:
                for label in issue["labels"]:
                    if label.lower() in jql_lower:
                        break
                else:
                    match = False
            
            if match:
                results.append(JiraIssue(
                    key=issue["key"],
                    summary=issue["summary"],
                    status=issue["status"],
                    priority=issue["priority"],
                    issue_type=issue["issue_type"],
                    assignee=issue["assignee"],
                    created=issue["created"],
                    updated=issue["updated"],
                    labels=issue["labels"]
                ))
        
        # Limit results
        results = results[:input_data.max_results]
        
        return JiraSearchOutput(
            issues=results,
            total=len(results),
            jql_processed=input_data.jql
        )


# =============================================================================
# Jira Create Tool
# =============================================================================

class JiraCreateInput(BaseModel):
    """Input schema for creating Jira issues."""
    project: str = Field(
        default="SUPPORT",
        description="Project key (e.g., SUPPORT, FEAT, ENG)"
    )
    issue_type: str = Field(
        ...,
        description="Issue type: Bug, Task, Story, or Feature Request"
    )
    summary: str = Field(
        ...,
        description="Issue title/summary (brief description)",
        max_length=255
    )
    description: Optional[str] = Field(
        None,
        description="Detailed issue description"
    )
    priority: str = Field(
        default="Medium",
        description="Priority: Critical, High, Medium, Low, or Lowest"
    )
    labels: list[str] = Field(
        default_factory=list,
        description="Labels to apply to the issue"
    )
    assignee: Optional[str] = Field(
        None,
        description="Username to assign the issue to"
    )


class JiraCreateOutput(BaseModel):
    """Output schema for creating Jira issues."""
    success: bool = True
    key: str = ""
    id: str = ""
    url: str = ""
    created_at: str = ""
    error: Optional[str] = None


class JiraCreateTool(BaseTool[JiraCreateInput, JiraCreateOutput]):
    """
    Tool for creating Jira issues.
    
    Use this tool to create tracking tickets for customer issues that
    need to be escalated, investigated by engineering, or tracked
    over time.
    
    When to use:
    - Bug needs engineering investigation
    - Issue affects multiple customers
    - Customer requests feature enhancement
    - Complex issue requiring multi-step resolution
    - SLA-tracked enterprise issues
    
    Best practices:
    - Always search first to avoid duplicates
    - Include customer tier in labels (enterprise, pro)
    - Set appropriate priority based on impact
    - Include relevant context in description
    """
    
    name: str = "jira_create"
    description: str = (
        "Create a new Jira issue for tracking. Use this to escalate bugs "
        "to engineering, create tickets for complex issues, or log feature requests. "
        "Always search for existing issues first to avoid duplicates."
    )
    input_model: Type[JiraCreateInput] = JiraCreateInput
    output_model: Type[JiraCreateOutput] = JiraCreateOutput
    
    def _execute(self, input_data: JiraCreateInput) -> JiraCreateOutput:
        """Create a mock Jira issue."""
        global _issue_counter
        
        # Generate issue key
        _issue_counter += 1
        issue_key = f"{input_data.project}-{_issue_counter}"
        issue_id = str(10000 + _issue_counter)
        created_at = datetime.now(timezone.utc).isoformat()
        
        # Store the created issue
        new_issue = {
            "key": issue_key,
            "id": issue_id,
            "summary": input_data.summary,
            "description": input_data.description,
            "status": "Open",
            "priority": input_data.priority,
            "issue_type": input_data.issue_type,
            "assignee": input_data.assignee,
            "labels": input_data.labels,
            "created": created_at,
            "updated": created_at
        }
        MOCK_CREATED_ISSUES.append(new_issue)
        
        logger.info(f"Created Jira issue: {issue_key} - {input_data.summary}")
        
        return JiraCreateOutput(
            success=True,
            key=issue_key,
            id=issue_id,
            url=f"https://company.atlassian.net/browse/{issue_key}",
            created_at=created_at
        )