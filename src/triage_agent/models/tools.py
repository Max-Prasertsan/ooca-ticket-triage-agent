"""
Tool Input/Output Models
=========================

Defines Pydantic schemas for all tool inputs and outputs.

Each tool has a dedicated input and output model to ensure
type safety and validation at tool boundaries.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field


# =============================================================================
# Knowledge Base Tool Models
# =============================================================================

class KnowledgeBaseInput(BaseModel):
    """
    Input schema for knowledge base search tool.
    
    Attributes:
        query: Search query string
        max_results: Maximum number of results to return
        category_filter: Optional category to filter by
    """
    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Search query for the knowledge base",
        examples=["password reset", "billing cycle"]
    )
    max_results: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of results to return"
    )
    category_filter: Optional[str] = Field(
        default=None,
        description="Optional category to filter results",
        examples=["authentication", "billing", "api"]
    )


class KnowledgeBaseArticle(BaseModel):
    """
    A single knowledge base article.
    
    Attributes:
        id: Unique article identifier
        title: Article title
        url: Full URL to the article
        category: Article category
        content_snippet: Brief excerpt of article content
        relevance_score: Computed relevance to the query
    """
    id: str = Field(..., description="Unique article identifier")
    title: str = Field(..., description="Article title")
    url: str = Field(..., description="Full URL to the article")
    category: str = Field(..., description="Article category")
    content_snippet: str = Field(..., description="Brief excerpt of content")
    relevance_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Relevance score (0.0-1.0)"
    )


class KnowledgeBaseOutput(BaseModel):
    """
    Output schema for knowledge base search tool.
    
    Attributes:
        results: List of matching articles
        total_matches: Total number of matches found
        query_processed: The processed query string
    """
    results: list[KnowledgeBaseArticle] = Field(
        default_factory=list,
        description="List of matching articles"
    )
    total_matches: int = Field(
        default=0,
        description="Total number of matches in the knowledge base"
    )
    query_processed: str = Field(
        ...,
        description="The query string that was processed"
    )


# =============================================================================
# Customer History Tool Models
# =============================================================================

class CustomerHistoryInput(BaseModel):
    """
    Input schema for customer history lookup tool.
    
    Attributes:
        customer_email: Email address of the customer
        include_tickets: Whether to include past ticket history
        include_billing: Whether to include billing history
    """
    customer_email: str = Field(
        ...,
        description="Customer email address to look up",
        examples=["customer@example.com"]
    )
    include_tickets: bool = Field(
        default=True,
        description="Include past ticket history"
    )
    include_billing: bool = Field(
        default=True,
        description="Include billing history"
    )


class PastTicketSummary(BaseModel):
    """Summary of a past support ticket."""
    ticket_id: str
    date: str
    subject: str
    resolution: str
    satisfaction_score: Optional[int] = None


class CustomerHistoryOutput(BaseModel):
    """
    Output schema for customer history lookup tool.
    
    Attributes:
        customer_email: The looked up customer email
        customer_name: Customer's name
        account_tier: Subscription tier
        account_created: Account creation date
        lifetime_value: Total customer value
        past_tickets: List of past ticket summaries
        past_ticket_count: Total number of past tickets
        average_satisfaction: Average CSAT score
        is_at_risk: Whether customer is flagged as at-risk
        notes: Internal notes about the customer
    """
    customer_email: str = Field(..., description="Customer email")
    customer_name: Optional[str] = Field(None, description="Customer name")
    account_tier: str = Field(..., description="Subscription tier")
    account_created: Optional[str] = Field(None, description="Account creation date")
    lifetime_value: float = Field(default=0.0, description="Total customer value in USD")
    past_tickets: list[PastTicketSummary] = Field(
        default_factory=list,
        description="Summary of past tickets"
    )
    past_ticket_count: int = Field(default=0, description="Total past tickets")
    average_satisfaction: Optional[float] = Field(
        None,
        ge=1.0,
        le=5.0,
        description="Average CSAT score (1-5)"
    )
    is_at_risk: bool = Field(default=False, description="Customer at-risk flag")
    notes: Optional[str] = Field(None, description="Internal customer notes")


# =============================================================================
# Region Status Tool Models
# =============================================================================

class RegionStatusInput(BaseModel):
    """
    Input schema for region status check tool.
    
    Attributes:
        region: Region identifier to check
        check_services: Specific services to check (empty for all)
    """
    region: str = Field(
        ...,
        description="Region identifier",
        examples=["us-east", "us-west", "eu-west", "apac"]
    )
    check_services: list[str] = Field(
        default_factory=list,
        description="Specific services to check (empty for all)",
        examples=[["api", "dashboard", "auth"]]
    )


class ServiceStatus(BaseModel):
    """Status of an individual service."""
    service_name: str = Field(..., description="Name of the service")
    status: str = Field(
        ...,
        description="Service status",
        examples=["operational", "degraded", "outage"]
    )
    latency_ms: Optional[int] = Field(None, description="Current latency in ms")
    last_incident: Optional[str] = Field(None, description="Last incident timestamp")


class RegionStatusOutput(BaseModel):
    """
    Output schema for region status check tool.
    
    Attributes:
        region: The checked region
        overall_status: Overall region health status
        services: Status of individual services
        active_incidents: List of active incident IDs
        last_updated: When status was last updated
    """
    region: str = Field(..., description="Region identifier")
    overall_status: str = Field(
        ...,
        description="Overall region status",
        examples=["healthy", "degraded", "outage"]
    )
    services: list[ServiceStatus] = Field(
        default_factory=list,
        description="Status of individual services"
    )
    active_incidents: list[str] = Field(
        default_factory=list,
        description="List of active incident IDs"
    )
    last_updated: str = Field(..., description="ISO timestamp of last update")


# =============================================================================
# Generic Tool Models
# =============================================================================

class ToolError(BaseModel):
    """
    Standard error response for tool failures.
    
    Attributes:
        error_code: Machine-readable error code
        error_message: Human-readable error description
        recoverable: Whether the error is recoverable
    """
    error_code: str = Field(..., description="Machine-readable error code")
    error_message: str = Field(..., description="Human-readable error description")
    recoverable: bool = Field(
        default=True,
        description="Whether the operation can be retried"
    )