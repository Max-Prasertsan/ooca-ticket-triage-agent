"""
Data Models Package
===================

This package contains all Pydantic data models used throughout the application.

Modules:
    ticket: Input ticket schema definitions
    triage_output: Agent output schema definitions  
    tools: Tool input/output schema definitions
"""

from src.triage_agent.models.ticket import SupportTicket
from src.triage_agent.models.triage_output import (
    CustomerSentiment,
    IssueType,
    KnowledgeBaseResult,
    RecommendedAction,
    RiskSignal,
    SpecialistQueue,
    ToolCallRecord,
    TriageOutput,
    UrgencyLevel,
)
from src.triage_agent.models.tools import (
    CustomerHistoryInput,
    CustomerHistoryOutput,
    KnowledgeBaseInput,
    KnowledgeBaseOutput,
    RegionStatusInput,
    RegionStatusOutput,
)

__all__ = [
    # Ticket models
    "SupportTicket",
    # Output models
    "TriageOutput",
    "UrgencyLevel",
    "IssueType",
    "CustomerSentiment",
    "RiskSignal",
    "RecommendedAction",
    "SpecialistQueue",
    "KnowledgeBaseResult",
    "ToolCallRecord",
    # Tool models
    "KnowledgeBaseInput",
    "KnowledgeBaseOutput",
    "CustomerHistoryInput",
    "CustomerHistoryOutput",
    "RegionStatusInput",
    "RegionStatusOutput",
]