"""
Support Ticket Model
=====================

Defines the schema for incoming customer support tickets.

This module provides the `SupportTicket` Pydantic model that represents
a customer support ticket with all relevant metadata for triage processing.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class SupportTicket(BaseModel):
    """
    Represents an incoming customer support ticket.
    
    This model captures all relevant information about a support request
    that the triage agent needs to process and classify.
    
    Attributes:
        ticket_id: Unique identifier for the ticket.
        subject: The ticket subject/title.
        body: The main content of the support request.
        customer_email: Customer's email address.
        customer_name: Optional customer name.
        customer_tier: Customer tier (free, pro, enterprise).
        customer_region: Geographic region of the customer.
        timestamp: When the ticket was created.
        channel: How the ticket was submitted.
        attachments: List of attachment filenames.
        metadata: Additional ticket metadata.
    
    Example:
        >>> ticket = SupportTicket(
        ...     ticket_id="T-12345",
        ...     subject="Cannot access dashboard",
        ...     body="I've been trying to log in for hours...",
        ...     customer_email="user@company.com",
        ...     customer_tier="enterprise"
        ... )
    """
    
    ticket_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique identifier for the ticket",
        examples=["T-12345", "TICKET-001"]
    )
    
    subject: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="The ticket subject line",
        examples=["Cannot login to my account", "Billing discrepancy"]
    )
    
    body: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="The main content of the support request",
        examples=["I've been trying to access my dashboard but keep getting an error..."]
    )
    
    customer_email: str = Field(
        ...,
        description="Customer's email address",
        examples=["customer@example.com"]
    )
    
    customer_name: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Customer's full name if available",
        examples=["John Doe"]
    )
    
    customer_tier: Optional[str] = Field(
        default="unknown",
        description="Customer subscription tier",
        examples=["free", "pro", "enterprise"]
    )
    
    customer_region: Optional[str] = Field(
        default=None,
        description="Geographic region of the customer",
        examples=["us-east", "eu-west", "apac"]
    )
    
    timestamp: Optional[str] = Field(
        default=None,
        description="ISO 8601 timestamp when ticket was created",
        examples=["2024-01-15T10:30:00Z"]
    )
    
    channel: Optional[str] = Field(
        default="web",
        description="Channel through which ticket was submitted",
        examples=["web", "email", "api", "chat"]
    )
    
    attachments: list[str] = Field(
        default_factory=list,
        description="List of attachment filenames",
        examples=[["screenshot.png", "error_log.txt"]]
    )
    
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional ticket metadata",
        examples=[{"browser": "Chrome", "os": "Windows 11"}]
    )
    
    @field_validator("customer_email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Basic email format validation."""
        if "@" not in v or "." not in v:
            raise ValueError("Invalid email format")
        return v.lower().strip()
    
    @field_validator("customer_tier")
    @classmethod
    def normalize_tier(cls, v: Optional[str]) -> str:
        """Normalize customer tier to lowercase."""
        if v is None:
            return "unknown"
        return v.lower().strip()
    
    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: Optional[str]) -> Optional[str]:
        """Validate timestamp format if provided."""
        if v is None:
            return None
        try:
            # Attempt to parse ISO format
            datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError("Timestamp must be in ISO 8601 format")
        return v
    
    def get_full_text(self) -> str:
        """
        Get combined subject and body for analysis.
        
        Returns:
            str: Combined ticket text.
        """
        return f"{self.subject}\n\n{self.body}"
    
    def is_enterprise(self) -> bool:
        """
        Check if customer is on enterprise tier.
        
        Returns:
            bool: True if enterprise customer.
        """
        return self.customer_tier.lower() == "enterprise"
    
    def has_attachments(self) -> bool:
        """
        Check if ticket has attachments.
        
        Returns:
            bool: True if attachments present.
        """
        return len(self.attachments) > 0


# Sample tickets for demonstration
SAMPLE_TICKETS = [
    SupportTicket(
        ticket_id="T-001",
        subject="URGENT: Production system completely down",
        body="""Our entire production environment has been down for the past 2 hours. 
        We're losing thousands of dollars per minute. This is affecting all of our customers 
        and we need immediate assistance. We've already tried restarting services but nothing 
        works. Our CEO is demanding answers and we're considering switching providers if this 
        isn't resolved immediately. 
        
        Error message: "Service Unavailable - Error 503"
        Region: us-east-1
        Account ID: ENT-9999
        
        Please escalate this to your highest priority team NOW.""",
        customer_email="cto@bigcorp.com",
        customer_name="Sarah Chen",
        customer_tier="enterprise",
        customer_region="us-east",
        timestamp="2024-01-15T14:30:00Z",
        channel="web",
        metadata={"account_value": 500000, "employees": 5000}
    ),
    SupportTicket(
        ticket_id="T-002", 
        subject="Question about billing cycle",
        body="""Hi there,
        
        I just have a quick question about when my billing cycle renews. I signed up on 
        January 5th but I'm seeing a charge dated January 1st on my statement. 
        
        Can you clarify how the billing dates work? I want to make sure I understand 
        before my next renewal.
        
        Thanks!
        Mike""",
        customer_email="mike.johnson@startup.io",
        customer_name="Mike Johnson",
        customer_tier="pro",
        customer_region="us-west",
        timestamp="2024-01-15T09:15:00Z",
        channel="email"
    ),
    SupportTicket(
        ticket_id="T-003",
        subject="Feature request: Dark mode",
        body="""Hello,
        
        I love your product and use it every day! I was wondering if you have any plans 
        to add a dark mode option? I often work late at night and the bright interface 
        can be a bit harsh on the eyes.
        
        Just a suggestion - keep up the great work!
        
        Best,
        Emma""",
        customer_email="emma.dev@techcompany.com",
        customer_name="Emma Rodriguez",
        customer_tier="pro",
        customer_region="eu-west",
        timestamp="2024-01-15T22:45:00Z",
        channel="web"
    ),
]