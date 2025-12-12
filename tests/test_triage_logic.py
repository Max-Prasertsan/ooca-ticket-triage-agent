"""
Triage Logic Tests
===================

Tests for the business logic engine including:
- Urgency override rules
- Risk signal detection
- Specialist queue assignment
- Action determination
- Issue type detection
"""

import pytest

from src.triage_agent.core.triage_logic import TriageLogic
from src.triage_agent.models.ticket import SupportTicket
from src.triage_agent.models.triage_output import (
    UrgencyLevel,
    IssueType,
    CustomerSentiment,
    RiskSignal,
    RecommendedAction,
    SpecialistQueue,
)


# Helper to create tickets for testing
def make_ticket(
    subject: str = "Test",
    body: str = "Test body",
    tier: str = "pro",
    email: str = "test@example.com"
) -> SupportTicket:
    """Create a test ticket."""
    return SupportTicket(
        ticket_id="TEST-001",
        subject=subject,
        body=body,
        customer_email=email,
        customer_tier=tier
    )


class TestUrgencyOverrides:
    """Tests for urgency override rules."""
    
    def test_enterprise_outage_becomes_critical(self, triage_logic):
        """Test that enterprise + outage keywords = CRITICAL."""
        ticket = make_ticket(
            subject="System is down",
            body="Our production system is down!",
            tier="enterprise"
        )
        
        result = triage_logic.calculate_urgency_override(ticket, "medium")
        
        assert result == UrgencyLevel.CRITICAL
    
    def test_critical_keywords_upgrade_to_high(self, triage_logic):
        """Test that critical keywords upgrade low/medium to HIGH."""
        ticket = make_ticket(
            subject="URGENT issue",
            body="URGENT: Security breach detected!",
            tier="pro"
        )
        
        result = triage_logic.calculate_urgency_override(ticket, "low")
        
        assert result == UrgencyLevel.HIGH
    
    def test_enterprise_low_becomes_medium(self, triage_logic):
        """Test that enterprise + low urgency = MEDIUM minimum."""
        ticket = make_ticket(
            subject="General question",
            body="General question about features",
            tier="enterprise"
        )
        
        result = triage_logic.calculate_urgency_override(ticket, "low")
        
        assert result == UrgencyLevel.MEDIUM
    
    def test_non_enterprise_unchanged(self, triage_logic):
        """Test that non-enterprise low urgency stays low."""
        ticket = make_ticket(
            subject="General question",
            body="General question",
            tier="free"
        )
        
        result = triage_logic.calculate_urgency_override(ticket, "low")
        
        # No override should be returned
        assert result is None
    
    def test_already_critical_no_override(self, triage_logic):
        """Test that critical urgency gets no override needed."""
        ticket = make_ticket(
            subject="Simple question",
            body="Simple question",
            tier="free"
        )
        
        result = triage_logic.calculate_urgency_override(ticket, "critical")
        
        # No override needed when already critical
        assert result is None


class TestRiskSignalDetection:
    """Tests for risk signal detection."""
    
    def test_detect_churn_risk(self, triage_logic):
        """Test detection of churn risk signals."""
        ticket = make_ticket(
            body="I'm thinking of canceling my subscription and switching to a competitor."
        )
        
        signals = triage_logic.detect_risk_signals(ticket)
        
        assert RiskSignal.CHURN_RISK in signals
    
    def test_detect_legal_threat(self, triage_logic):
        """Test detection of legal threat signals."""
        ticket = make_ticket(
            body="I'm contacting my lawyer about this issue."
        )
        
        signals = triage_logic.detect_risk_signals(ticket)
        
        assert RiskSignal.LEGAL_THREAT in signals
    
    def test_detect_charge_dispute(self, triage_logic):
        """Test detection of charge dispute signals."""
        ticket = make_ticket(
            body="I'm going to dispute this charge with my credit card company. Chargeback incoming!"
        )
        
        signals = triage_logic.detect_risk_signals(ticket)
        
        assert RiskSignal.CHARGE_DISPUTE in signals
    
    def test_detect_social_media_threat(self, triage_logic):
        """Test detection of social media threat signals."""
        ticket = make_ticket(
            body="I'm going to tweet about this terrible experience!"
        )
        
        signals = triage_logic.detect_risk_signals(ticket)
        
        assert RiskSignal.SOCIAL_MEDIA_THREAT in signals
    
    def test_detect_high_value_account(self, triage_logic):
        """Test detection of high value account signal."""
        ticket = make_ticket(
            body="Just a simple question",
            tier="enterprise"
        )
        
        signals = triage_logic.detect_risk_signals(ticket)
        
        assert RiskSignal.HIGH_VALUE_ACCOUNT in signals
    
    def test_multiple_signals_detected(self, triage_logic):
        """Test detection of multiple risk signals."""
        ticket = make_ticket(
            body="I'm canceling and contacting my lawyer about this fraudulent charge!",
            tier="enterprise"
        )
        
        signals = triage_logic.detect_risk_signals(ticket)
        
        assert len(signals) >= 2
    
    def test_no_signals_for_positive_message(self, triage_logic):
        """Test no false positives for positive messages."""
        ticket = make_ticket(
            body="Love the product! Just have a quick question.",
            tier="free"
        )
        
        signals = triage_logic.detect_risk_signals(ticket)
        
        # Should only have signals if tier warrants it
        assert RiskSignal.CHURN_RISK not in signals
        assert RiskSignal.LEGAL_THREAT not in signals


class TestSpecialistQueueAssignment:
    """Tests for specialist queue assignment."""
    
    def test_billing_issue_to_billing_queue(self, triage_logic):
        """Test that billing issues go to billing queue."""
        ticket = make_ticket(tier="pro")
        
        queue = triage_logic.determine_specialist_queue(
            issue_type=IssueType.BILLING,
            urgency=UrgencyLevel.MEDIUM,
            ticket=ticket,
            risk_signals=[]
        )
        
        assert queue == SpecialistQueue.BILLING
    
    def test_outage_to_infra_queue(self, triage_logic):
        """Test that outages go to infrastructure queue."""
        ticket = make_ticket(tier="pro")
        
        queue = triage_logic.determine_specialist_queue(
            issue_type=IssueType.OUTAGE,
            urgency=UrgencyLevel.HIGH,
            ticket=ticket,
            risk_signals=[]
        )
        
        assert queue == SpecialistQueue.INFRA
    
    def test_enterprise_high_urgency_to_enterprise_success(self, triage_logic):
        """Test that enterprise + high urgency goes to enterprise success."""
        ticket = make_ticket(tier="enterprise")
        
        queue = triage_logic.determine_specialist_queue(
            issue_type=IssueType.BUG,
            urgency=UrgencyLevel.HIGH,
            ticket=ticket,
            risk_signals=[RiskSignal.HIGH_VALUE_ACCOUNT]
        )
        
        assert queue == SpecialistQueue.ENTERPRISE_SUCCESS
    
    def test_critical_bug_to_tier_2(self, triage_logic):
        """Test that critical bugs go to tier 2."""
        ticket = make_ticket(tier="pro")
        
        queue = triage_logic.determine_specialist_queue(
            issue_type=IssueType.BUG,
            urgency=UrgencyLevel.CRITICAL,
            ticket=ticket,
            risk_signals=[]
        )
        
        assert queue == SpecialistQueue.TIER_2
    
    def test_legal_threat_to_enterprise_success(self, triage_logic):
        """Test that legal threats go to enterprise success."""
        ticket = make_ticket(tier="pro")
        
        queue = triage_logic.determine_specialist_queue(
            issue_type=IssueType.OTHER,  # Not billing, so legal threat takes precedence
            urgency=UrgencyLevel.MEDIUM,
            ticket=ticket,
            risk_signals=[RiskSignal.LEGAL_THREAT]
        )
        
        assert queue == SpecialistQueue.ENTERPRISE_SUCCESS


class TestActionDetermination:
    """Tests for recommended action determination."""
    
    def test_critical_urgency_escalates(self, triage_logic):
        """Test that critical urgency triggers escalation."""
        ticket = make_ticket(tier="pro")
        
        action = triage_logic.determine_action(
            urgency=UrgencyLevel.CRITICAL,
            sentiment=CustomerSentiment.NEUTRAL,
            issue_type=IssueType.OUTAGE,
            risk_signals=[],
            ticket=ticket,
            has_kb_results=True
        )
        
        assert action == RecommendedAction.ESCALATE_TO_HUMAN
    
    def test_legal_threat_escalates(self, triage_logic):
        """Test that legal threats trigger escalation."""
        ticket = make_ticket(tier="pro")
        
        action = triage_logic.determine_action(
            urgency=UrgencyLevel.MEDIUM,
            sentiment=CustomerSentiment.NEGATIVE,
            issue_type=IssueType.BILLING,
            risk_signals=[RiskSignal.LEGAL_THREAT],
            ticket=ticket,
            has_kb_results=True
        )
        
        assert action == RecommendedAction.ESCALATE_TO_HUMAN
    
    def test_very_negative_with_churn_escalates(self, triage_logic):
        """Test that very negative sentiment + churn risk escalates."""
        ticket = make_ticket(tier="pro")
        
        action = triage_logic.determine_action(
            urgency=UrgencyLevel.MEDIUM,
            sentiment=CustomerSentiment.VERY_NEGATIVE,
            issue_type=IssueType.BILLING,
            risk_signals=[RiskSignal.CHURN_RISK],
            ticket=ticket,
            has_kb_results=True
        )
        
        assert action == RecommendedAction.ESCALATE_TO_HUMAN
    
    def test_enterprise_routes_to_specialist(self, triage_logic):
        """Test that enterprise customers route to specialist."""
        ticket = make_ticket(tier="enterprise")
        
        action = triage_logic.determine_action(
            urgency=UrgencyLevel.LOW,
            sentiment=CustomerSentiment.NEUTRAL,
            issue_type=IssueType.OTHER,
            risk_signals=[RiskSignal.HIGH_VALUE_ACCOUNT],
            ticket=ticket,
            has_kb_results=True
        )
        
        assert action == RecommendedAction.ROUTE_TO_SPECIALIST
    
    def test_simple_request_auto_responds(self, triage_logic):
        """Test that simple requests can auto-respond."""
        ticket = make_ticket(tier="free")
        
        action = triage_logic.determine_action(
            urgency=UrgencyLevel.LOW,
            sentiment=CustomerSentiment.POSITIVE,
            issue_type=IssueType.FEATURE_REQUEST,
            risk_signals=[],
            ticket=ticket,
            has_kb_results=True
        )
        
        assert action == RecommendedAction.AUTO_RESPOND


class TestIssueTypeDetection:
    """Tests for issue type detection from keywords."""
    
    def test_detect_billing_keywords(self, triage_logic):
        """Test detection of billing issue type."""
        ticket = make_ticket(
            body="I have a question about my invoice and billing cycle"
        )
        
        issue_type = triage_logic.detect_issue_type_from_keywords(ticket)
        
        assert issue_type == IssueType.BILLING
    
    def test_detect_outage_keywords(self, triage_logic):
        """Test detection of outage issue type."""
        ticket = make_ticket(
            body="The service is down and I'm getting 503 errors"
        )
        
        issue_type = triage_logic.detect_issue_type_from_keywords(ticket)
        
        assert issue_type == IssueType.OUTAGE
    
    def test_detect_bug_keywords(self, triage_logic):
        """Test detection of bug issue type."""
        ticket = make_ticket(
            body="I found a bug - the button doesn't work and shows an error"
        )
        
        issue_type = triage_logic.detect_issue_type_from_keywords(ticket)
        
        assert issue_type == IssueType.BUG
    
    def test_detect_feature_request(self, triage_logic):
        """Test detection of feature request."""
        ticket = make_ticket(
            body="It would be great if you could add a dark mode feature"
        )
        
        issue_type = triage_logic.detect_issue_type_from_keywords(ticket)
        
        assert issue_type == IssueType.FEATURE_REQUEST
    
    def test_detect_account_keywords(self, triage_logic):
        """Test detection of account issue type."""
        ticket = make_ticket(
            body="I can't login and need to reset my password"
        )
        
        issue_type = triage_logic.detect_issue_type_from_keywords(ticket)
        
        assert issue_type == IssueType.ACCOUNT
    
    def test_default_to_none_for_unknown(self, triage_logic):
        """Test default to None for unrecognized text."""
        ticket = make_ticket(
            body="Hello, I have a general inquiry about something"
        )
        
        issue_type = triage_logic.detect_issue_type_from_keywords(ticket)
        
        # Returns None if no keywords match
        assert issue_type is None