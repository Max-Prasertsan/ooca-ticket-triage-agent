"""
Support Ticket Triage Agent
============================

An enterprise-grade AI agent for automated customer support ticket triage.

This package provides:
- Intelligent ticket classification (urgency, sentiment, issue type)
- Knowledge base search integration
- Customer history analysis
- Automated routing decisions
- Suggested response generation

Example usage:
    >>> from src.triage_agent.core.agent import TriageAgent
    >>> from src.triage_agent.models.ticket import SupportTicket
    >>> from src.triage_agent.config import Config
    >>>
    >>> agent = TriageAgent(Config())
    >>> ticket = SupportTicket(
    ...     ticket_id="T-001",
    ...     subject="Login Issue",
    ...     body="I can't log in to my account",
    ...     customer_email="user@example.com"
    ... )
    >>> result = agent.triage(ticket)
"""

__version__ = "1.0.0"
__author__ = "AI Engineering Team"