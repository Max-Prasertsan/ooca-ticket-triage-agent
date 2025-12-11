"""
Triage Logic Module
====================

Contains deterministic business rules for triage decisions.

This module implements the business logic layer that augments
LLM decisions with rule-based overrides and validation.
"""

import logging
import re
from typing import Optional

from src.triage_agent.models.ticket import SupportTicket
from src.triage_agent.models.triage_output import (
    CustomerSentiment,
    IssueType,
    RecommendedAction,
    RiskSignal,
    SpecialistQueue,
    UrgencyLevel,
)

logger = logging.getLogger(__name__)


class TriageLogic:
    """
    Business logic layer for triage decisions.
    
    Implements deterministic rules that can override or validate
    LLM-generated classifications. This provides a safety net
    for critical business rules that must always be enforced.
    
    Example:
        >>> logic = TriageLogic()
        >>> urgency = logic.calculate_urgency_override(ticket, "medium")
        >>> if urgency:
        ...     print(f"Override to: {urgency}")
    """
    
    # Keywords indicating high urgency
    CRITICAL_KEYWORDS = [
        "production down", "system down", "completely down",
        "security breach", "data leak", "data loss",
        "all users affected", "cannot access",
        "losing money", "losing customers", "urgent",
        "emergency", "critical", "asap", "immediately"
    ]
    
    # Keywords indicating potential churn risk
    CHURN_KEYWORDS = [
        "cancel", "canceling", "cancellation",
        "switch provider", "switching", "competitor",
        "leaving", "frustrated", "disappointed",
        "not worth", "waste of money", "refund"
    ]
    
    # Keywords indicating legal/dispute risk
    LEGAL_KEYWORDS = [
        "lawyer", "attorney", "legal action",
        "lawsuit", "sue", "court",
        "dispute", "chargeback", "fraud"
    ]
    
    # Keywords indicating social media threat
    SOCIAL_MEDIA_KEYWORDS = [
        "twitter", "tweet", "post about",
        "tell everyone", "review", "public",
        "social media", "linkedin", "facebook"
    ]
    
    def calculate_urgency_override(
        self,
        ticket: SupportTicket,
        llm_urgency: str
    ) -> Optional[UrgencyLevel]:
        """
        Calculate if urgency should be overridden based on business rules.
        
        Args:
            ticket: The support ticket.
            llm_urgency: The LLM-suggested urgency level.
        
        Returns:
            Optional[UrgencyLevel]: Override urgency if rules apply, None otherwise.
        """
        text = ticket.get_full_text().lower()
        
        # Rule 1: Enterprise customers with outage indicators = CRITICAL
        if ticket.is_enterprise():
            outage_indicators = ["down", "outage", "unavailable", "503", "500"]
            if any(indicator in text for indicator in outage_indicators):
                logger.info(f"Urgency override: Enterprise + outage = CRITICAL")
                return UrgencyLevel.CRITICAL
        
        # Rule 2: Critical keywords always bump to at least HIGH
        if any(kw in text for kw in self.CRITICAL_KEYWORDS):
            if llm_urgency in ["low", "medium"]:
                logger.info(f"Urgency override: Critical keywords found = HIGH")
                return UrgencyLevel.HIGH
        
        # Rule 3: Enterprise customer + negative sentiment = at least HIGH
        if ticket.is_enterprise() and llm_urgency == "low":
            logger.info(f"Urgency override: Enterprise customer = at least MEDIUM")
            return UrgencyLevel.MEDIUM
        
        return None
    
    def detect_risk_signals(self, ticket: SupportTicket) -> list[RiskSignal]:
        """
        Detect customer risk signals from ticket content.
        
        Args:
            ticket: The support ticket.
        
        Returns:
            list[RiskSignal]: List of detected risk signals.
        """
        text = ticket.get_full_text().lower()
        signals = []
        
        # Check for churn risk
        if any(kw in text for kw in self.CHURN_KEYWORDS):
            signals.append(RiskSignal.CHURN_RISK)
        
        # Check for legal threat
        if any(kw in text for kw in self.LEGAL_KEYWORDS):
            signals.append(RiskSignal.LEGAL_THREAT)
        
        # Check for social media threat
        if any(kw in text for kw in self.SOCIAL_MEDIA_KEYWORDS):
            signals.append(RiskSignal.SOCIAL_MEDIA_THREAT)
        
        # Check for charge dispute indicators
        dispute_keywords = ["chargeback", "dispute", "unauthorized charge", "fraud"]
        if any(kw in text for kw in dispute_keywords):
            signals.append(RiskSignal.CHARGE_DISPUTE)
        
        # High-value account risk
        if ticket.is_enterprise():
            signals.append(RiskSignal.HIGH_VALUE_ACCOUNT)
        
        return signals
    
    def determine_specialist_queue(
        self,
        issue_type: IssueType,
        urgency: UrgencyLevel,
        ticket: SupportTicket,
        risk_signals: list[RiskSignal]
    ) -> SpecialistQueue:
        """
        Determine the appropriate specialist queue for routing.
        
        Args:
            issue_type: Classified issue type.
            urgency: Classified urgency level.
            ticket: The support ticket.
            risk_signals: Detected risk signals.
        
        Returns:
            SpecialistQueue: The recommended specialist queue.
        """
        # Enterprise customers with high urgency go to enterprise success
        if ticket.is_enterprise() and urgency in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH]:
            return SpecialistQueue.ENTERPRISE_SUCCESS
        
        # Billing issues go to billing team
        if issue_type == IssueType.BILLING:
            return SpecialistQueue.BILLING
        
        # Outages go to infrastructure team
        if issue_type == IssueType.OUTAGE:
            return SpecialistQueue.INFRA
        
        # Complex bugs or critical issues go to tier 2
        if urgency == UrgencyLevel.CRITICAL or issue_type == IssueType.BUG:
            return SpecialistQueue.TIER_2
        
        # Legal threats need special handling
        if RiskSignal.LEGAL_THREAT in risk_signals:
            return SpecialistQueue.ENTERPRISE_SUCCESS
        
        return SpecialistQueue.NONE
    
    def determine_action(
        self,
        urgency: UrgencyLevel,
        sentiment: CustomerSentiment,
        issue_type: IssueType,
        risk_signals: list[RiskSignal],
        ticket: SupportTicket,
        has_kb_results: bool
    ) -> RecommendedAction:
        """
        Determine the recommended action for the ticket.
        
        Args:
            urgency: Classified urgency level.
            sentiment: Customer sentiment.
            issue_type: Issue type classification.
            risk_signals: Detected risk signals.
            ticket: The support ticket.
            has_kb_results: Whether relevant KB articles were found.
        
        Returns:
            RecommendedAction: The recommended action to take.
        """
        # Always escalate critical issues
        if urgency == UrgencyLevel.CRITICAL:
            return RecommendedAction.ESCALATE_TO_HUMAN
        
        # Escalate if legal threat detected
        if RiskSignal.LEGAL_THREAT in risk_signals:
            return RecommendedAction.ESCALATE_TO_HUMAN
        
        # Escalate very negative sentiment with churn risk
        if (sentiment == CustomerSentiment.VERY_NEGATIVE and 
            RiskSignal.CHURN_RISK in risk_signals):
            return RecommendedAction.ESCALATE_TO_HUMAN
        
        # Route enterprise customers to specialists
        if ticket.is_enterprise():
            return RecommendedAction.ROUTE_TO_SPECIALIST
        
        # Route high urgency to specialists
        if urgency == UrgencyLevel.HIGH:
            return RecommendedAction.ROUTE_TO_SPECIALIST
        
        # Route negative sentiment to specialists
        if sentiment in [CustomerSentiment.VERY_NEGATIVE, CustomerSentiment.NEGATIVE]:
            return RecommendedAction.ROUTE_TO_SPECIALIST
        
        # Feature requests can be auto-responded
        if issue_type == IssueType.FEATURE_REQUEST and has_kb_results:
            return RecommendedAction.AUTO_RESPOND
        
        # Simple billing questions with KB results can be auto-responded
        if issue_type == IssueType.BILLING and urgency == UrgencyLevel.LOW and has_kb_results:
            return RecommendedAction.AUTO_RESPOND
        
        # Low urgency with positive sentiment and KB results
        if (urgency == UrgencyLevel.LOW and 
            sentiment in [CustomerSentiment.POSITIVE, CustomerSentiment.NEUTRAL] and
            has_kb_results):
            return RecommendedAction.AUTO_RESPOND
        
        # Default to routing to specialist for safety
        return RecommendedAction.ROUTE_TO_SPECIALIST
    
    def detect_issue_type_from_keywords(self, ticket: SupportTicket) -> Optional[IssueType]:
        """
        Detect issue type based on keyword matching.
        
        This provides a fallback or validation for LLM classification.
        
        Args:
            ticket: The support ticket.
        
        Returns:
            Optional[IssueType]: Detected issue type or None.
        """
        text = ticket.get_full_text().lower()
        
        # Billing indicators
        billing_keywords = ["billing", "invoice", "charge", "payment", "subscription", "refund", "price"]
        if any(kw in text for kw in billing_keywords):
            return IssueType.BILLING
        
        # Outage indicators
        outage_keywords = ["down", "outage", "unavailable", "503", "500", "not working", "cant access"]
        if any(kw in text for kw in outage_keywords):
            return IssueType.OUTAGE
        
        # Bug indicators
        bug_keywords = ["bug", "error", "broken", "doesn't work", "crash", "issue"]
        if any(kw in text for kw in bug_keywords):
            return IssueType.BUG
        
        # Feature request indicators
        feature_keywords = ["feature", "request", "suggestion", "would be nice", "add support for", "idea"]
        if any(kw in text for kw in feature_keywords):
            return IssueType.FEATURE_REQUEST
        
        # Account indicators
        account_keywords = ["account", "login", "password", "access", "permission", "locked"]
        if any(kw in text for kw in account_keywords):
            return IssueType.ACCOUNT
        
        return None