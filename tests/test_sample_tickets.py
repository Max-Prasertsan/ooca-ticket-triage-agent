"""
Test Sample Tickets
====================

Tests for the triage agent using sample tickets.

These tests verify:
- Agent processes tickets without errors
- Output schema is valid
- Classification results are reasonable
- Tools are called appropriately
"""

import json
import pytest
from unittest.mock import MagicMock, patch

from src.triage_agent.config import Config
from src.triage_agent.core.agent import TriageAgent
from src.triage_agent.core.triage_logic import TriageLogic
from src.triage_agent.models.ticket import SAMPLE_TICKETS, SupportTicket
from src.triage_agent.models.triage_output import (
    CustomerSentiment,
    IssueType,
    RecommendedAction,
    RiskSignal,
    SpecialistQueue,
    TriageOutput,
    UrgencyLevel,
)
from src.triage_agent.tools import create_tool_registry
from src.triage_agent.tools.knowledge_base import KnowledgeBaseTool
from src.triage_agent.tools.customer_history import CustomerHistoryTool
from src.triage_agent.tools.region_status import RegionStatusTool
from src.triage_agent.models.tools import (
    KnowledgeBaseInput,
    CustomerHistoryInput,
    RegionStatusInput,
)


class TestTriageAgent:
    """Test suite for the TriageAgent class."""
    
    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return Config(openai_api_key="")  # No API key for rule-based testing
    
    @pytest.fixture
    def agent(self, config):
        """Create a test agent."""
        return TriageAgent(config)
    
    def test_agent_initialization(self, agent):
        """Test that agent initializes correctly."""
        assert agent is not None
        assert agent.tool_registry is not None
        assert len(agent.tool_registry) >= 2
    
    def test_tool_registry_has_required_tools(self, agent):
        """Test that required tools are registered."""
        assert agent.tool_registry.has_tool("knowledge_base_search")
        assert agent.tool_registry.has_tool("customer_history")
        assert agent.tool_registry.has_tool("region_status")
    
    def test_process_critical_ticket(self, agent):
        """Test processing a critical production outage ticket."""
        ticket = SAMPLE_TICKETS[0]  # Critical enterprise outage
        result = agent.triage(ticket)
        
        # Verify output structure
        assert isinstance(result, TriageOutput)
        assert result.ticket_id == ticket.ticket_id
        
        # Verify urgency is HIGH or CRITICAL for enterprise outage
        assert result.urgency in [UrgencyLevel.HIGH, UrgencyLevel.CRITICAL]
        
        # Verify appropriate action
        assert result.recommended_action in [
            RecommendedAction.ESCALATE_TO_HUMAN,
            RecommendedAction.ROUTE_TO_SPECIALIST
        ]
        
        # Verify risk signals detected
        assert RiskSignal.HIGH_VALUE_ACCOUNT in result.customer_risk_signals
    
    def test_process_billing_question(self, agent):
        """Test processing a simple billing question."""
        ticket = SAMPLE_TICKETS[1]  # Billing question
        result = agent.triage(ticket)
        
        assert isinstance(result, TriageOutput)
        assert result.ticket_id == ticket.ticket_id
        
        # Should be lower urgency
        assert result.urgency in [UrgencyLevel.LOW, UrgencyLevel.MEDIUM]
        
        # Should detect billing issue type
        assert result.issue_type == IssueType.BILLING
    
    def test_process_feature_request(self, agent):
        """Test processing a feature request."""
        ticket = SAMPLE_TICKETS[2]  # Feature request
        result = agent.triage(ticket)
        
        assert isinstance(result, TriageOutput)
        assert result.ticket_id == ticket.ticket_id
        
        # Should be low urgency
        assert result.urgency == UrgencyLevel.LOW
        
        # Should detect feature request
        assert result.issue_type == IssueType.FEATURE_REQUEST
        
        # Sentiment should be positive (complimentary tone)
        assert result.customer_sentiment in [
            CustomerSentiment.POSITIVE,
            CustomerSentiment.NEUTRAL
        ]
    
    def test_all_sample_tickets_process(self, agent):
        """Test that all sample tickets process without errors."""
        for ticket in SAMPLE_TICKETS:
            result = agent.triage(ticket)
            
            # Basic validation
            assert result.ticket_id == ticket.ticket_id
            assert result.urgency is not None
            assert result.issue_type is not None
            assert result.customer_sentiment is not None
            assert result.recommended_action is not None
    
    def test_tool_calls_are_recorded(self, agent):
        """Test that tool calls are recorded in output."""
        ticket = SAMPLE_TICKETS[0]
        result = agent.triage(ticket)
        
        # Should have at least 2 tool calls (KB search + customer history)
        assert len(result.tool_calls) >= 2
        
        # Verify tool call structure
        for call in result.tool_calls:
            assert call.tool_name is not None
            assert call.inputs is not None
            assert isinstance(call.success, bool)


class TestTriageLogic:
    """Test suite for the TriageLogic class."""
    
    @pytest.fixture
    def logic(self):
        """Create a triage logic instance."""
        return TriageLogic()
    
    def test_urgency_override_enterprise_outage(self, logic):
        """Test that enterprise + outage triggers CRITICAL override."""
        ticket = SupportTicket(
            ticket_id="T-TEST",
            subject="System down",
            body="Our system is completely down and unavailable",
            customer_email="test@example.com",
            customer_tier="enterprise"
        )
        
        override = logic.calculate_urgency_override(ticket, "medium")
        assert override == UrgencyLevel.CRITICAL
    
    def test_risk_signal_detection_churn(self, logic):
        """Test churn risk detection."""
        ticket = SupportTicket(
            ticket_id="T-TEST",
            subject="Considering canceling",
            body="I'm thinking about canceling my subscription and switching to a competitor",
            customer_email="test@example.com"
        )
        
        signals = logic.detect_risk_signals(ticket)
        assert RiskSignal.CHURN_RISK in signals
    
    def test_risk_signal_detection_legal(self, logic):
        """Test legal threat detection."""
        ticket = SupportTicket(
            ticket_id="T-TEST",
            subject="Legal action",
            body="I'm going to contact my lawyer about this issue",
            customer_email="test@example.com"
        )
        
        signals = logic.detect_risk_signals(ticket)
        assert RiskSignal.LEGAL_THREAT in signals
    
    def test_specialist_queue_billing(self, logic):
        """Test billing issues route to billing queue."""
        ticket = SupportTicket(
            ticket_id="T-TEST",
            subject="Billing",
            body="Question about billing",
            customer_email="test@example.com",
            customer_tier="pro"
        )
        
        queue = logic.determine_specialist_queue(
            IssueType.BILLING,
            UrgencyLevel.MEDIUM,
            ticket,
            []
        )
        assert queue == SpecialistQueue.BILLING
    
    def test_specialist_queue_enterprise(self, logic):
        """Test enterprise customers route to enterprise success."""
        ticket = SupportTicket(
            ticket_id="T-TEST",
            subject="Help needed",
            body="Need assistance",
            customer_email="test@example.com",
            customer_tier="enterprise"
        )
        
        queue = logic.determine_specialist_queue(
            IssueType.OTHER,
            UrgencyLevel.HIGH,
            ticket,
            [RiskSignal.HIGH_VALUE_ACCOUNT]
        )
        assert queue == SpecialistQueue.ENTERPRISE_SUCCESS
    
    def test_issue_type_detection_billing(self, logic):
        """Test billing keyword detection."""
        ticket = SupportTicket(
            ticket_id="T-TEST",
            subject="Question about my invoice",
            body="I noticed a charge on my billing statement",
            customer_email="test@example.com"
        )
        
        issue_type = logic.detect_issue_type_from_keywords(ticket)
        assert issue_type == IssueType.BILLING
    
    def test_issue_type_detection_outage(self, logic):
        """Test outage keyword detection."""
        ticket = SupportTicket(
            ticket_id="T-TEST",
            subject="Service down",
            body="The service is unavailable and showing 503 error",
            customer_email="test@example.com"
        )
        
        issue_type = logic.detect_issue_type_from_keywords(ticket)
        assert issue_type == IssueType.OUTAGE


class TestTools:
    """Test suite for individual tools."""
    
    def test_knowledge_base_tool_search(self):
        """Test knowledge base search returns results."""
        tool = KnowledgeBaseTool()
        input_data = KnowledgeBaseInput(query="password reset")
        
        result = tool.execute(input_data)
        
        assert result is not None
        assert len(result.results) > 0
        assert result.query_processed == "password reset"
    
    def test_knowledge_base_tool_relevance(self):
        """Test that relevance scores are calculated."""
        tool = KnowledgeBaseTool()
        input_data = KnowledgeBaseInput(query="billing cycle payment")
        
        result = tool.execute(input_data)
        
        for article in result.results:
            assert 0.0 <= article.relevance_score <= 1.0
    
    def test_customer_history_known_customer(self):
        """Test customer history for known customer."""
        tool = CustomerHistoryTool()
        input_data = CustomerHistoryInput(customer_email="cto@bigcorp.com")
        
        result = tool.execute(input_data)
        
        assert result.customer_name == "Sarah Chen"
        assert result.account_tier == "enterprise"
        assert result.lifetime_value > 0
    
    def test_customer_history_unknown_customer(self):
        """Test customer history for unknown customer."""
        tool = CustomerHistoryTool()
        input_data = CustomerHistoryInput(customer_email="unknown@example.com")
        
        result = tool.execute(input_data)
        
        assert result.account_tier == "unknown"
        assert result.lifetime_value == 0.0
    
    def test_region_status_known_region(self):
        """Test region status for known region."""
        tool = RegionStatusTool()
        input_data = RegionStatusInput(region="us-east")
        
        result = tool.execute(input_data)
        
        assert result.region == "us-east"
        assert result.overall_status in ["healthy", "degraded", "outage"]
        assert len(result.services) > 0
    
    def test_region_status_unknown_region(self):
        """Test region status for unknown region."""
        tool = RegionStatusTool()
        input_data = RegionStatusInput(region="unknown-region")
        
        result = tool.execute(input_data)
        
        assert result.overall_status == "unknown"


class TestToolRegistry:
    """Test suite for the tool registry."""
    
    def test_create_default_tools(self):
        """Test creating default tool registry."""
        registry = create_tool_registry()
        
        assert len(registry) >= 3
        assert registry.has_tool("knowledge_base_search")
        assert registry.has_tool("customer_history")
        assert registry.has_tool("region_status")
    
    def test_get_schemas(self):
        """Test getting OpenAI-compatible schemas."""
        registry = create_tool_registry()
        schemas = registry.get_schemas()
        
        assert len(schemas) >= 3
        for schema in schemas:
            assert "type" in schema
            assert schema["type"] == "function"
            assert "function" in schema
            assert "name" in schema["function"]
            assert "description" in schema["function"]


class TestModels:
    """Test suite for Pydantic models."""
    
    def test_support_ticket_validation(self):
        """Test support ticket validation."""
        ticket = SupportTicket(
            ticket_id="T-001",
            subject="Test",
            body="Test body",
            customer_email="test@example.com"
        )
        
        assert ticket.ticket_id == "T-001"
        assert ticket.customer_tier == "unknown"  # Default
    
    def test_support_ticket_email_validation(self):
        """Test email validation."""
        with pytest.raises(ValueError):
            SupportTicket(
                ticket_id="T-001",
                subject="Test",
                body="Test body",
                customer_email="invalid-email"
            )
    
    def test_triage_output_serialization(self):
        """Test triage output can be serialized to JSON."""
        output = TriageOutput(
            ticket_id="T-001",
            urgency=UrgencyLevel.HIGH,
            product="api",
            issue_type=IssueType.BUG,
            customer_sentiment=CustomerSentiment.NEGATIVE,
            customer_risk_signals=[RiskSignal.CHURN_RISK],
            recommended_action=RecommendedAction.ROUTE_TO_SPECIALIST,
            recommended_specialist_queue=SpecialistQueue.TIER_2,
            knowledge_base_results=[],
            tool_calls=[]
        )
        
        json_str = output.model_dump_json()
        data = json.loads(json_str)
        
        assert data["ticket_id"] == "T-001"
        assert data["urgency"] == "high"


# Integration test - requires all components to work together
class TestIntegration:
    """Integration tests for the complete triage flow."""
    
    def test_full_triage_flow(self):
        """Test complete triage flow with rule-based fallback."""
        config = Config(openai_api_key="")
        agent = TriageAgent(config)
        
        ticket = SupportTicket(
            ticket_id="INT-001",
            subject="URGENT: Cannot access dashboard - production down",
            body="""
            Our entire team cannot access the dashboard since this morning.
            We're losing money every minute this is down.
            This is affecting our production environment.
            Please help immediately!
            
            Account ID: ENT-5000
            Region: us-east
            """,
            customer_email="cto@bigcorp.com",
            customer_tier="enterprise",
            customer_region="us-east"
        )
        
        result = agent.triage(ticket)
        
        # Verify comprehensive triage
        assert result.ticket_id == "INT-001"
        assert result.urgency in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH]
        assert result.recommended_action == RecommendedAction.ESCALATE_TO_HUMAN
        assert RiskSignal.HIGH_VALUE_ACCOUNT in result.customer_risk_signals
        assert len(result.tool_calls) >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])