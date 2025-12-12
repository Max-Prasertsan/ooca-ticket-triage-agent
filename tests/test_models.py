"""
Model Tests
============

Tests for Pydantic models including validation,
serialization, and schema generation.
"""

import json
import pytest

from src.triage_agent.models.ticket import SupportTicket
from src.triage_agent.models.triage_output import (
    TriageOutput,
    UrgencyLevel,
    IssueType,
    CustomerSentiment,
    RiskSignal,
    RecommendedAction,
    SpecialistQueue,
)


class TestSupportTicket:
    """Tests for SupportTicket model."""
    
    def test_create_basic_ticket(self):
        """Test creating a basic support ticket."""
        ticket = SupportTicket(
            ticket_id="T-001",
            subject="Test subject",
            body="Test body content",
            customer_email="test@example.com"
        )
        
        assert ticket.ticket_id == "T-001"
        assert ticket.subject == "Test subject"
        assert ticket.body == "Test body content"
        assert ticket.customer_email == "test@example.com"
    
    def test_ticket_with_optional_fields(self):
        """Test creating a ticket with all optional fields."""
        ticket = SupportTicket(
            ticket_id="T-002",
            subject="Full ticket",
            body="Body content",
            customer_email="customer@example.com",
            customer_name="John Doe",
            customer_tier="enterprise",
            customer_region="us-west"
        )
        
        assert ticket.customer_name == "John Doe"
        assert ticket.customer_tier == "enterprise"
        assert ticket.customer_region == "us-west"
    
    def test_ticket_email_validation_valid(self):
        """Test that valid emails are accepted."""
        ticket = SupportTicket(
            ticket_id="T-003",
            subject="Test",
            body="Body",
            customer_email="valid.email@domain.com"
        )
        
        assert "@" in ticket.customer_email
    
    def test_ticket_email_validation_invalid(self):
        """Test that invalid emails are rejected."""
        with pytest.raises(ValueError):
            SupportTicket(
                ticket_id="T-004",
                subject="Test",
                body="Body",
                customer_email="not-an-email"
            )
    
    def test_ticket_get_full_text(self):
        """Test get_full_text method."""
        ticket = SupportTicket(
            ticket_id="T-005",
            subject="Subject here",
            body="Body content here",
            customer_email="test@example.com"
        )
        
        full_text = ticket.get_full_text()
        assert "Subject here" in full_text
        assert "Body content here" in full_text
    
    def test_ticket_is_enterprise(self):
        """Test is_enterprise method."""
        enterprise = SupportTicket(
            ticket_id="T-006",
            subject="Test",
            body="Body",
            customer_email="test@example.com",
            customer_tier="enterprise"
        )
        
        non_enterprise = SupportTicket(
            ticket_id="T-007",
            subject="Test",
            body="Body",
            customer_email="test@example.com",
            customer_tier="pro"
        )
        
        assert enterprise.is_enterprise() is True
        assert non_enterprise.is_enterprise() is False


class TestTriageOutput:
    """Tests for TriageOutput model."""
    
    def test_create_basic_output(self):
        """Test creating a basic triage output."""
        output = TriageOutput(
            ticket_id="T-001",
            urgency=UrgencyLevel.HIGH,
            issue_type=IssueType.BUG,
            customer_sentiment=CustomerSentiment.NEGATIVE,
            customer_risk_signals=[],
            recommended_action=RecommendedAction.ROUTE_TO_SPECIALIST,
            recommended_specialist_queue=SpecialistQueue.TIER_2,
            knowledge_base_results=[],
            tool_calls=[]
        )
        
        assert output.ticket_id == "T-001"
        assert output.urgency == UrgencyLevel.HIGH
    
    def test_output_json_serialization(self):
        """Test that output can be serialized to JSON."""
        output = TriageOutput(
            ticket_id="T-002",
            urgency=UrgencyLevel.CRITICAL,
            issue_type=IssueType.OUTAGE,
            customer_sentiment=CustomerSentiment.VERY_NEGATIVE,
            customer_risk_signals=[RiskSignal.CHURN_RISK],
            recommended_action=RecommendedAction.ESCALATE_TO_HUMAN,
            recommended_specialist_queue=SpecialistQueue.ENTERPRISE_SUCCESS,
            knowledge_base_results=[],
            tool_calls=[]
        )
        
        json_str = output.model_dump_json()
        data = json.loads(json_str)
        
        assert data["ticket_id"] == "T-002"
        assert data["urgency"] == "critical"
        assert data["issue_type"] == "outage"
    
    def test_output_with_all_risk_signals(self):
        """Test output with multiple risk signals."""
        output = TriageOutput(
            ticket_id="T-003",
            urgency=UrgencyLevel.HIGH,
            issue_type=IssueType.BILLING,
            customer_sentiment=CustomerSentiment.VERY_NEGATIVE,
            customer_risk_signals=[
                RiskSignal.CHURN_RISK,
                RiskSignal.CHARGE_DISPUTE,
                RiskSignal.LEGAL_THREAT,
            ],
            recommended_action=RecommendedAction.ESCALATE_TO_HUMAN,
            recommended_specialist_queue=SpecialistQueue.BILLING,
            knowledge_base_results=[],
            tool_calls=[]
        )
        
        assert len(output.customer_risk_signals) == 3
        assert RiskSignal.CHURN_RISK in output.customer_risk_signals


class TestEnums:
    """Tests for enum values."""
    
    def test_urgency_levels(self):
        """Test all urgency levels exist."""
        assert UrgencyLevel.CRITICAL.value == "critical"
        assert UrgencyLevel.HIGH.value == "high"
        assert UrgencyLevel.MEDIUM.value == "medium"
        assert UrgencyLevel.LOW.value == "low"
    
    def test_issue_types(self):
        """Test all issue types exist."""
        assert IssueType.BILLING.value == "billing"
        assert IssueType.OUTAGE.value == "outage"
        assert IssueType.BUG.value == "bug"
        assert IssueType.FEATURE_REQUEST.value == "feature_request"
        assert IssueType.ACCOUNT.value == "account"
        assert IssueType.OTHER.value == "other"
    
    def test_sentiment_values(self):
        """Test all sentiment values exist."""
        assert CustomerSentiment.VERY_NEGATIVE.value == "very_negative"
        assert CustomerSentiment.NEGATIVE.value == "negative"
        assert CustomerSentiment.NEUTRAL.value == "neutral"
        assert CustomerSentiment.POSITIVE.value == "positive"
        assert CustomerSentiment.VERY_POSITIVE.value == "very_positive"
    
    def test_action_values(self):
        """Test all action values exist."""
        assert RecommendedAction.AUTO_RESPOND.value == "auto_respond"
        assert RecommendedAction.ROUTE_TO_SPECIALIST.value == "route_to_specialist"
        assert RecommendedAction.ESCALATE_TO_HUMAN.value == "escalate_to_human"