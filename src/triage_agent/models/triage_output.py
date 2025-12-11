"""
Triage Output Models
=====================

Defines the schema for agent triage output, including all enums and nested models.

This module provides comprehensive type definitions for the structured output
that the triage agent produces after processing a support ticket.
"""

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class UrgencyLevel(str, Enum):
    """
    Ticket urgency classification levels.
    
    Attributes:
        CRITICAL: Immediate attention required (system down, data loss, security breach)
        HIGH: Urgent issue affecting business operations
        MEDIUM: Important issue that needs attention within business hours
        LOW: Non-urgent inquiry or request
    """
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IssueType(str, Enum):
    """
    Classification of the type of support issue.
    
    Attributes:
        BILLING: Payment, invoicing, subscription issues
        OUTAGE: Service unavailability or downtime
        BUG: Software defects or unexpected behavior
        FEATURE_REQUEST: Request for new functionality
        ACCOUNT: Account access, settings, permissions
        OTHER: Issues that don't fit other categories
    """
    BILLING = "billing"
    OUTAGE = "outage"
    BUG = "bug"
    FEATURE_REQUEST = "feature_request"
    ACCOUNT = "account"
    OTHER = "other"


class CustomerSentiment(str, Enum):
    """
    Customer sentiment classification.
    
    Attributes:
        VERY_NEGATIVE: Angry, threatening, extremely frustrated
        NEGATIVE: Frustrated, disappointed, unhappy
        NEUTRAL: Neither positive nor negative
        POSITIVE: Satisfied, appreciative
        VERY_POSITIVE: Enthusiastic, highly satisfied
    """
    VERY_NEGATIVE = "very_negative"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    VERY_POSITIVE = "very_positive"


class RiskSignal(str, Enum):
    """
    Customer risk indicators that may require special handling.
    
    Attributes:
        CHURN_RISK: Customer may cancel or leave
        CHARGE_DISPUTE: Potential chargeback or payment dispute
        LEGAL_THREAT: Customer mentions legal action
        SOCIAL_MEDIA_THREAT: Threat to publicize on social media
        ESCALATION_HISTORY: Customer has escalated before
        HIGH_VALUE_ACCOUNT: High revenue customer at risk
        COMPLIANCE_ISSUE: Potential regulatory or compliance concern
    """
    CHURN_RISK = "churn_risk"
    CHARGE_DISPUTE = "charge_dispute"
    LEGAL_THREAT = "legal_threat"
    SOCIAL_MEDIA_THREAT = "social_media_threat"
    ESCALATION_HISTORY = "escalation_history"
    HIGH_VALUE_ACCOUNT = "high_value_account"
    COMPLIANCE_ISSUE = "compliance_issue"


class RecommendedAction(str, Enum):
    """
    Recommended next action for the ticket.
    
    Attributes:
        AUTO_RESPOND: Send automated response from templates
        ROUTE_TO_SPECIALIST: Route to specialized support queue
        ESCALATE_TO_HUMAN: Requires immediate human intervention
    """
    AUTO_RESPOND = "auto_respond"
    ROUTE_TO_SPECIALIST = "route_to_specialist"
    ESCALATE_TO_HUMAN = "escalate_to_human"


class SpecialistQueue(str, Enum):
    """
    Specialist queues for routing.
    
    Attributes:
        BILLING: Billing and payment specialists
        INFRA: Infrastructure and technical operations
        ENTERPRISE_SUCCESS: Enterprise customer success managers
        TIER_2: Advanced technical support
        SECURITY: Security incident response team
        NONE: No specialist routing needed
    """
    BILLING = "billing"
    INFRA = "infra"
    ENTERPRISE_SUCCESS = "enterprise_success"
    TIER_2 = "tier_2"
    SECURITY = "security"
    NONE = "none"


class KnowledgeBaseResult(BaseModel):
    """
    A single knowledge base search result.
    
    Attributes:
        id: Unique identifier of the KB article
        title: Article title
        url: URL to the full article
        relevance_score: How relevant this article is (0.0-1.0)
        snippet: Brief excerpt from the article
    """
    id: str = Field(
        ...,
        description="Unique identifier of the KB article",
        examples=["KB-001", "DOC-AUTH-005"]
    )
    title: str = Field(
        ...,
        description="Title of the knowledge base article",
        examples=["How to Reset Your Password"]
    )
    url: str = Field(
        ...,
        description="URL to the full article",
        examples=["https://help.example.com/articles/password-reset"]
    )
    relevance_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Relevance score from 0.0 to 1.0",
        examples=[0.95]
    )
    snippet: Optional[str] = Field(
        default=None,
        description="Brief excerpt from the article",
        examples=["To reset your password, go to Settings > Security..."]
    )


class ToolCallRecord(BaseModel):
    """
    Record of a tool call made during triage.
    
    Attributes:
        tool_name: Name of the tool that was called
        inputs: Input parameters passed to the tool
        outputs: Output returned by the tool
        success: Whether the tool call succeeded
        error_message: Error message if the call failed
    """
    tool_name: str = Field(
        ...,
        description="Name of the tool that was called",
        examples=["knowledge_base_search", "customer_history"]
    )
    inputs: dict[str, Any] = Field(
        ...,
        description="Input parameters passed to the tool",
        examples=[{"query": "password reset"}]
    )
    outputs: dict[str, Any] = Field(
        default_factory=dict,
        description="Output returned by the tool",
        examples=[{"results": []}]
    )
    success: bool = Field(
        default=True,
        description="Whether the tool call succeeded"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if the call failed"
    )


class TriageOutput(BaseModel):
    """
    Complete triage output for a support ticket.
    
    This is the main output schema produced by the triage agent after
    processing a support ticket. It contains all classification results,
    tool outputs, and recommended actions.
    
    Attributes:
        ticket_id: ID of the processed ticket
        urgency: Classified urgency level
        product: Detected product/feature area
        issue_type: Classification of issue type
        customer_sentiment: Detected customer sentiment
        customer_risk_signals: List of detected risk signals
        recommended_action: Recommended next action
        recommended_specialist_queue: Queue to route to if applicable
        knowledge_base_results: Relevant KB articles found
        suggested_reply: Draft response for the customer
        tool_calls: Record of all tool calls made
        confidence_score: Overall confidence in triage (0.0-1.0)
        reasoning: Brief explanation of triage decisions
    
    Example:
        >>> output = TriageOutput(
        ...     ticket_id="T-001",
        ...     urgency=UrgencyLevel.HIGH,
        ...     product="authentication",
        ...     issue_type=IssueType.ACCOUNT,
        ...     customer_sentiment=CustomerSentiment.NEGATIVE,
        ...     customer_risk_signals=[RiskSignal.CHURN_RISK],
        ...     recommended_action=RecommendedAction.ROUTE_TO_SPECIALIST,
        ...     recommended_specialist_queue=SpecialistQueue.TIER_2,
        ...     knowledge_base_results=[],
        ...     suggested_reply="I understand your frustration...",
        ...     tool_calls=[]
        ... )
    """
    
    ticket_id: str = Field(
        ...,
        description="ID of the processed ticket"
    )
    
    urgency: UrgencyLevel = Field(
        ...,
        description="Classified urgency level"
    )
    
    product: Optional[str] = Field(
        default=None,
        description="Detected product or feature area",
        examples=["authentication", "billing", "api", "dashboard"]
    )
    
    issue_type: IssueType = Field(
        ...,
        description="Classification of the issue type"
    )
    
    customer_sentiment: CustomerSentiment = Field(
        ...,
        description="Detected customer sentiment"
    )
    
    customer_risk_signals: list[RiskSignal] = Field(
        default_factory=list,
        description="List of detected risk signals"
    )
    
    recommended_action: RecommendedAction = Field(
        ...,
        description="Recommended next action"
    )
    
    recommended_specialist_queue: SpecialistQueue = Field(
        default=SpecialistQueue.NONE,
        description="Specialist queue to route to if applicable"
    )
    
    knowledge_base_results: list[KnowledgeBaseResult] = Field(
        default_factory=list,
        description="Relevant knowledge base articles found"
    )
    
    suggested_reply: Optional[str] = Field(
        default=None,
        description="Draft response for the customer"
    )
    
    tool_calls: list[ToolCallRecord] = Field(
        default_factory=list,
        description="Record of all tool calls made during triage"
    )
    
    confidence_score: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Overall confidence in triage decisions"
    )
    
    reasoning: Optional[str] = Field(
        default=None,
        description="Brief explanation of triage decisions"
    )
    
    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "ticket_id": "T-001",
                "urgency": "high",
                "product": "authentication",
                "issue_type": "account",
                "customer_sentiment": "negative",
                "customer_risk_signals": ["churn_risk"],
                "recommended_action": "route_to_specialist",
                "recommended_specialist_queue": "tier_2",
                "knowledge_base_results": [
                    {
                        "id": "KB-AUTH-001",
                        "title": "Account Recovery Steps",
                        "url": "https://help.example.com/account-recovery",
                        "relevance_score": 0.92
                    }
                ],
                "suggested_reply": "I understand how frustrating it must be...",
                "tool_calls": [
                    {
                        "tool_name": "knowledge_base_search",
                        "inputs": {"query": "account locked"},
                        "outputs": {"results": []},
                        "success": True
                    }
                ],
                "confidence_score": 0.85,
                "reasoning": "High urgency due to enterprise customer with account access issue"
            }
        }