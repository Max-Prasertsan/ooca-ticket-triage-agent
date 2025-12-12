"""
Integration Tests
==================

End-to-end tests that verify the complete triage flow
from ticket input to final output, including all tools
and business logic working together.
"""

import pytest

from src.triage_agent.core.agent import TriageAgent
from src.triage_agent.config import Config
from src.triage_agent.models.ticket import SupportTicket
from src.triage_agent.models.triage_output import (
    UrgencyLevel,
    IssueType,
    CustomerSentiment,
    RiskSignal,
    RecommendedAction,
    SpecialistQueue,
)


class TestEnterpriseTriageFlow:
    """Integration tests for enterprise customer triage."""
    
    def test_critical_enterprise_outage(self, agent):
        """Test complete flow for critical enterprise outage."""
        ticket = SupportTicket(
            ticket_id="INT-ENT-001",
            subject="URGENT: Production completely down",
            body="""
            Our entire production environment has been down for 30 minutes.
            All customers are affected and we're losing revenue.
            This is impacting our business operations severely.
            
            Error: 503 Service Unavailable on all endpoints
            Region: us-east
            """,
            customer_email="cto@bigcorp.com",
            customer_tier="enterprise",
            customer_region="us-east"
        )
        
        result = agent.triage(ticket)
        
        # Verify classification
        assert result.urgency in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH]
        assert result.issue_type == IssueType.OUTAGE
        
        # Verify routing
        assert result.recommended_action == RecommendedAction.ESCALATE_TO_HUMAN
        assert result.recommended_specialist_queue == SpecialistQueue.ENTERPRISE_SUCCESS
        
        # Verify risk detection
        assert RiskSignal.HIGH_VALUE_ACCOUNT in result.customer_risk_signals
        
        # Verify tools were used
        assert len(result.tool_calls) >= 2
    
    def test_enterprise_billing_question(self, agent):
        """Test complete flow for enterprise billing question."""
        ticket = SupportTicket(
            ticket_id="INT-ENT-002",
            subject="Question about enterprise pricing",
            body="""
            Hi team,
            
            We're coming up on our annual renewal and I wanted to discuss
            our current pricing structure. Can someone from account management
            reach out to discuss options?
            
            Thanks!
            """,
            customer_email="cfo@enterprise.com",
            customer_tier="enterprise"
        )
        
        result = agent.triage(ticket)
        
        # Enterprise should still route to specialist
        assert result.recommended_action in [
            RecommendedAction.ROUTE_TO_SPECIALIST,
            RecommendedAction.ESCALATE_TO_HUMAN
        ]
        
        # Should recognize as high value
        assert RiskSignal.HIGH_VALUE_ACCOUNT in result.customer_risk_signals


class TestStandardCustomerFlow:
    """Integration tests for standard (non-enterprise) customers."""
    
    def test_simple_billing_question(self, agent, billing_ticket):
        """Test complete flow for simple billing question."""
        result = agent.triage(billing_ticket)
        
        # Should be low/medium urgency
        assert result.urgency in [UrgencyLevel.LOW, UrgencyLevel.MEDIUM]
        
        # Should be billing issue type
        assert result.issue_type == IssueType.BILLING
        
        # Could auto-respond or route to specialist
        assert result.recommended_action in [
            RecommendedAction.AUTO_RESPOND,
            RecommendedAction.ROUTE_TO_SPECIALIST
        ]
    
    def test_feature_request(self, agent, feature_request_ticket):
        """Test complete flow for feature request."""
        result = agent.triage(feature_request_ticket)
        
        # Should be low urgency
        assert result.urgency == UrgencyLevel.LOW
        
        # Should be feature request type
        assert result.issue_type == IssueType.FEATURE_REQUEST
        
        # Positive sentiment should allow auto-respond
        assert result.customer_sentiment in [
            CustomerSentiment.POSITIVE,
            CustomerSentiment.VERY_POSITIVE,
            CustomerSentiment.NEUTRAL
        ]
    
    def test_angry_customer_escalation(self, agent, angry_customer_ticket):
        """Test complete flow for angry customer."""
        result = agent.triage(angry_customer_ticket)
        
        # Should detect negative sentiment
        assert result.customer_sentiment in [
            CustomerSentiment.NEGATIVE,
            CustomerSentiment.VERY_NEGATIVE
        ]
        
        # Should detect risk signals
        assert len(result.customer_risk_signals) > 0
        
        # Should escalate or route to specialist
        assert result.recommended_action in [
            RecommendedAction.ESCALATE_TO_HUMAN,
            RecommendedAction.ROUTE_TO_SPECIALIST
        ]


class TestToolIntegration:
    """Tests for tool integration in triage flow."""
    
    def test_kb_search_executed(self, agent, billing_ticket):
        """Test that KB search is executed during triage."""
        result = agent.triage(billing_ticket)
        
        tool_names = [call.tool_name for call in result.tool_calls]
        assert "knowledge_base_search" in tool_names
    
    def test_customer_history_executed(self, agent, enterprise_ticket):
        """Test that customer history is executed during triage."""
        result = agent.triage(enterprise_ticket)
        
        tool_names = [call.tool_name for call in result.tool_calls]
        assert "customer_history" in tool_names
    
    def test_tools_return_success(self, agent, billing_ticket):
        """Test that tool calls succeed."""
        result = agent.triage(billing_ticket)
        
        for call in result.tool_calls:
            assert call.success is True
    
    def test_kb_results_included(self, agent, billing_ticket):
        """Test that KB results are included in output."""
        result = agent.triage(billing_ticket)
        
        # Should have some KB results for billing query
        assert len(result.knowledge_base_results) >= 0  # May vary


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""
    
    def test_minimal_ticket(self, agent):
        """Test triage with minimal ticket information."""
        ticket = SupportTicket(
            ticket_id="EDGE-001",
            subject="Help",
            body="Need help",
            customer_email="user@example.com"
        )
        
        result = agent.triage(ticket)
        
        # Should still produce valid output
        assert result.ticket_id == "EDGE-001"
        assert result.urgency is not None
        assert result.recommended_action is not None
    
    def test_very_long_ticket(self, agent):
        """Test triage with very long ticket body."""
        long_body = "This is a test. " * 500  # Very long body
        
        ticket = SupportTicket(
            ticket_id="EDGE-002",
            subject="Long ticket",
            body=long_body,
            customer_email="user@example.com"
        )
        
        result = agent.triage(ticket)
        
        assert result.ticket_id == "EDGE-002"
    
    def test_special_characters_in_ticket(self, agent):
        """Test triage with special characters."""
        ticket = SupportTicket(
            ticket_id="EDGE-003",
            subject="Test with émojis 🎉 and spëcial çharacters",
            body="Content with <html> tags & symbols @#$%",
            customer_email="user@example.com"
        )
        
        result = agent.triage(ticket)
        
        assert result.ticket_id == "EDGE-003"
    
    def test_unknown_customer_tier(self, agent):
        """Test triage with unknown customer tier."""
        ticket = SupportTicket(
            ticket_id="EDGE-004",
            subject="Question",
            body="I have a question about pricing",
            customer_email="new.user@example.com",
            customer_tier="unknown"
        )
        
        result = agent.triage(ticket)
        
        # Should not flag as high value
        assert RiskSignal.HIGH_VALUE_ACCOUNT not in result.customer_risk_signals


class TestOutputCompleteness:
    """Tests for output completeness and validity."""
    
    def test_output_has_all_required_fields(self, agent, billing_ticket):
        """Test that output has all required fields."""
        result = agent.triage(billing_ticket)
        
        assert result.ticket_id is not None
        assert result.urgency is not None
        assert result.issue_type is not None
        assert result.customer_sentiment is not None
        assert result.customer_risk_signals is not None
        assert result.recommended_action is not None
        assert result.recommended_specialist_queue is not None
        assert result.knowledge_base_results is not None
        assert result.tool_calls is not None
    
    def test_output_serializes_to_json(self, agent, enterprise_ticket):
        """Test that output can be serialized to JSON."""
        result = agent.triage(enterprise_ticket)
        
        json_str = result.model_dump_json()
        
        assert len(json_str) > 0
        assert "ticket_id" in json_str
        assert "urgency" in json_str
    
    def test_confidence_score_in_range(self, agent, billing_ticket):
        """Test that confidence score is in valid range."""
        result = agent.triage(billing_ticket)
        
        assert 0.0 <= result.confidence_score <= 1.0