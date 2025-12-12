"""
Agent Tests
============

Tests for the TriageAgent class including initialization,
ticket processing, and tool orchestration.
"""

import pytest

from src.triage_agent.core.agent import TriageAgent
from src.triage_agent.config import Config
from src.triage_agent.models.triage_output import (
    UrgencyLevel,
    RecommendedAction,
    RiskSignal,
)


class TestAgentInitialization:
    """Tests for agent initialization."""
    
    def test_agent_creates_successfully(self, config):
        """Test that agent initializes without errors."""
        agent = TriageAgent(config)
        assert agent is not None
    
    def test_agent_has_tool_registry(self, agent):
        """Test that agent has a tool registry."""
        assert agent.tool_registry is not None
    
    def test_agent_has_required_native_tools(self, agent):
        """Test that required native tools are registered."""
        assert agent.tool_registry.has_tool("knowledge_base_search")
        assert agent.tool_registry.has_tool("customer_history")
        assert agent.tool_registry.has_tool("region_status")
    
    def test_agent_has_mcp_tools(self, agent):
        """Test that MCP tools are registered by default."""
        assert agent.tool_registry.has_tool("slack_search")
        assert agent.tool_registry.has_tool("slack_post")
        assert agent.tool_registry.has_tool("jira_search")
        assert agent.tool_registry.has_tool("jira_create")
        assert agent.tool_registry.has_tool("pagerduty_incidents")
        assert agent.tool_registry.has_tool("pagerduty_create")
    
    def test_agent_has_nine_tools_total(self, agent):
        """Test that agent has all 9 tools."""
        assert len(agent.tool_registry) == 9


class TestTicketProcessing:
    """Tests for ticket processing."""
    
    def test_process_critical_ticket(self, agent, enterprise_ticket):
        """Test processing a critical enterprise ticket."""
        result = agent.triage(enterprise_ticket)
        
        assert result.ticket_id == enterprise_ticket.ticket_id
        assert result.urgency in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH]
        assert result.recommended_action == RecommendedAction.ESCALATE_TO_HUMAN
    
    def test_process_billing_ticket(self, agent, billing_ticket):
        """Test processing a billing inquiry ticket."""
        result = agent.triage(billing_ticket)
        
        assert result.ticket_id == billing_ticket.ticket_id
        assert result.urgency in [UrgencyLevel.LOW, UrgencyLevel.MEDIUM]
    
    def test_process_feature_request(self, agent, feature_request_ticket):
        """Test processing a feature request ticket."""
        result = agent.triage(feature_request_ticket)
        
        assert result.ticket_id == feature_request_ticket.ticket_id
        assert result.urgency == UrgencyLevel.LOW
    
    def test_all_sample_tickets_process(self, agent, sample_tickets):
        """Test that all sample tickets process without errors."""
        for ticket in sample_tickets:
            result = agent.triage(ticket)
            assert result.ticket_id == ticket.ticket_id
            assert result.urgency is not None
            assert result.recommended_action is not None


class TestToolCalls:
    """Tests for tool call recording."""
    
    def test_tool_calls_are_recorded(self, agent, enterprise_ticket):
        """Test that tool calls are recorded in output."""
        result = agent.triage(enterprise_ticket)
        
        # Should have at least 2 tool calls (KB + customer history)
        assert len(result.tool_calls) >= 2
    
    def test_tool_calls_have_names(self, agent, billing_ticket):
        """Test that tool calls have tool names."""
        result = agent.triage(billing_ticket)
        
        for call in result.tool_calls:
            assert call.tool_name is not None
            assert len(call.tool_name) > 0
    
    def test_tool_calls_have_success_status(self, agent, feature_request_ticket):
        """Test that tool calls have success status."""
        result = agent.triage(feature_request_ticket)
        
        for call in result.tool_calls:
            assert isinstance(call.success, bool)


class TestRiskDetection:
    """Tests for risk signal detection in agent."""
    
    def test_enterprise_flagged_as_high_value(self, agent, enterprise_ticket):
        """Test that enterprise customers are flagged as high value."""
        result = agent.triage(enterprise_ticket)
        
        assert RiskSignal.HIGH_VALUE_ACCOUNT in result.customer_risk_signals
    
    def test_angry_customer_detected(self, agent, angry_customer_ticket):
        """Test that angry customers trigger risk signals."""
        result = agent.triage(angry_customer_ticket)
        
        # Should detect at least one risk signal
        assert len(result.customer_risk_signals) > 0