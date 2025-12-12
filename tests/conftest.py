"""
Test Fixtures
==============

Shared fixtures and configuration for the test suite.
"""

import pytest

from src.triage_agent.config import Config
from src.triage_agent.core.agent import TriageAgent
from src.triage_agent.core.triage_logic import TriageLogic
from src.triage_agent.tools import create_tool_registry
from src.triage_agent.models.ticket import SupportTicket, SAMPLE_TICKETS


@pytest.fixture
def config():
    """Create a test configuration."""
    return Config()


@pytest.fixture
def agent(config):
    """Create a test agent instance."""
    return TriageAgent(config)


@pytest.fixture
def triage_logic():
    """Create a triage logic instance."""
    return TriageLogic()


@pytest.fixture
def tool_registry():
    """Create a full tool registry with all tools."""
    return create_tool_registry(include_mcp=True)


@pytest.fixture
def tool_registry_native_only():
    """Create a tool registry with only native tools."""
    return create_tool_registry(include_mcp=False)


@pytest.fixture
def sample_tickets():
    """Return the sample tickets."""
    return SAMPLE_TICKETS


@pytest.fixture
def enterprise_ticket():
    """Create an enterprise customer ticket."""
    return SupportTicket(
        ticket_id="TEST-ENT-001",
        subject="URGENT: Production system down",
        body="""
        Our entire production environment has been down for 30 minutes.
        All customers are affected and we're losing revenue.
        Error: 503 Service Unavailable on all endpoints.
        Region: us-east
        """,
        customer_email="cto@bigcorp.com",
        customer_name="Sarah Chen",
        customer_tier="enterprise",
        customer_region="us-east"
    )


@pytest.fixture
def billing_ticket():
    """Create a billing inquiry ticket."""
    return SupportTicket(
        ticket_id="TEST-BILL-001",
        subject="Question about my invoice",
        body="""
        Hi, I noticed a charge on my latest invoice that I don't recognize.
        Can you help me understand what it's for?
        
        Invoice #: INV-2024-0042
        Amount: $149.99
        """,
        customer_email="mike@startup.io",
        customer_tier="pro"
    )


@pytest.fixture
def feature_request_ticket():
    """Create a feature request ticket."""
    return SupportTicket(
        ticket_id="TEST-FEAT-001",
        subject="Feature request: Dark mode",
        body="""
        Love the product! Would be great if you could add a dark mode
        option to the dashboard. My eyes would thank you :)
        """,
        customer_email="emma@techco.com",
        customer_tier="pro"
    )


@pytest.fixture
def angry_customer_ticket():
    """Create an angry customer ticket."""
    return SupportTicket(
        ticket_id="TEST-ANGRY-001",
        subject="THIS IS UNACCEPTABLE",
        body="""
        I'VE BEEN TRYING TO GET HELP FOR 3 DAYS!!!
        Your service is terrible and I'm going to cancel my subscription.
        I'm also going to post about this on Twitter and warn everyone.
        If I don't hear back TODAY I'm disputing all charges with my bank.
        """,
        customer_email="angry@customer.com",
        customer_tier="pro"
    )