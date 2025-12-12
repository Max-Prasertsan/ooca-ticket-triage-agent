"""
Native Tools Tests
===================

Tests for native tool implementations:
- KnowledgeBaseTool
- CustomerHistoryTool
- RegionStatusTool
"""

import pytest

from src.triage_agent.tools.knowledge_base import (
    KnowledgeBaseTool,
    KnowledgeBaseInput,
)
from src.triage_agent.tools.customer_history import (
    CustomerHistoryTool,
    CustomerHistoryInput,
)
from src.triage_agent.tools.region_status import (
    RegionStatusTool,
    RegionStatusInput,
)


class TestKnowledgeBaseTool:
    """Tests for the knowledge base search tool."""
    
    def test_tool_has_correct_name(self):
        """Test tool has correct name."""
        tool = KnowledgeBaseTool()
        assert tool.name == "knowledge_base_search"
    
    def test_tool_has_description(self):
        """Test tool has a description."""
        tool = KnowledgeBaseTool()
        assert len(tool.description) > 0
    
    def test_search_returns_results(self):
        """Test that search returns results for valid query."""
        tool = KnowledgeBaseTool()
        result = tool.execute(KnowledgeBaseInput(query="password reset"))
        
        assert result.total_matches > 0
        assert len(result.results) > 0
    
    def test_search_results_have_relevance_scores(self):
        """Test that results have relevance scores between 0 and 1."""
        tool = KnowledgeBaseTool()
        result = tool.execute(KnowledgeBaseInput(query="billing"))
        
        for article in result.results:
            assert 0.0 <= article.relevance_score <= 1.0
    
    def test_search_respects_max_results(self):
        """Test that search respects max_results parameter."""
        tool = KnowledgeBaseTool()
        result = tool.execute(KnowledgeBaseInput(
            query="account",
            max_results=2
        ))
        
        assert len(result.results) <= 2
    
    def test_search_with_category_filter(self):
        """Test search with category filter."""
        tool = KnowledgeBaseTool()
        result = tool.execute(KnowledgeBaseInput(
            query="help",
            category_filter="billing"
        ))
        
        # Results should be filtered by category
        assert result is not None
    
    def test_empty_query_returns_empty(self):
        """Test that empty query returns no results."""
        tool = KnowledgeBaseTool()
        result = tool.execute(KnowledgeBaseInput(query="xyznonexistent123"))
        
        assert result.total_matches == 0


class TestCustomerHistoryTool:
    """Tests for the customer history lookup tool."""
    
    def test_tool_has_correct_name(self):
        """Test tool has correct name."""
        tool = CustomerHistoryTool()
        assert tool.name == "customer_history"
    
    def test_tool_has_description(self):
        """Test tool has a description."""
        tool = CustomerHistoryTool()
        assert len(tool.description) > 0
    
    def test_known_customer_lookup(self):
        """Test looking up a known customer."""
        tool = CustomerHistoryTool()
        result = tool.execute(CustomerHistoryInput(
            customer_email="cto@bigcorp.com"
        ))
        
        assert result.customer_email == "cto@bigcorp.com"
        assert result.customer_name == "Sarah Chen"
        assert result.account_tier == "enterprise"
    
    def test_known_customer_has_lifetime_value(self):
        """Test that known customer has lifetime value."""
        tool = CustomerHistoryTool()
        result = tool.execute(CustomerHistoryInput(
            customer_email="cto@bigcorp.com"
        ))
        
        assert result.lifetime_value > 0
    
    def test_unknown_customer_returns_defaults(self):
        """Test that unknown customer returns default values."""
        tool = CustomerHistoryTool()
        result = tool.execute(CustomerHistoryInput(
            customer_email="unknown@example.com"
        ))
        
        assert result.account_tier == "unknown"
        assert result.lifetime_value == 0
    
    def test_customer_risk_indicator(self):
        """Test that at-risk customers are identified."""
        tool = CustomerHistoryTool()
        result = tool.execute(CustomerHistoryInput(
            customer_email="angry.customer@example.com"
        ))
        
        assert result.is_at_risk is True


class TestRegionStatusTool:
    """Tests for the region status tool."""
    
    def test_tool_has_correct_name(self):
        """Test tool has correct name."""
        tool = RegionStatusTool()
        assert tool.name == "region_status"
    
    def test_tool_has_description(self):
        """Test tool has a description."""
        tool = RegionStatusTool()
        assert len(tool.description) > 0
    
    def test_known_region_returns_status(self):
        """Test that known region returns status."""
        tool = RegionStatusTool()
        result = tool.execute(RegionStatusInput(region="us-east"))
        
        assert result.region == "us-east"
        assert result.overall_status in ["healthy", "degraded", "outage"]
    
    def test_degraded_region_has_incidents(self):
        """Test that degraded region reports incidents."""
        tool = RegionStatusTool()
        result = tool.execute(RegionStatusInput(region="us-east"))
        
        # us-east is mocked as degraded
        if result.overall_status == "degraded":
            assert len(result.active_incidents) > 0
    
    def test_healthy_region(self):
        """Test a healthy region."""
        tool = RegionStatusTool()
        result = tool.execute(RegionStatusInput(region="us-west"))
        
        assert result.overall_status == "healthy"
    
    def test_unknown_region_returns_unknown_status(self):
        """Test that unknown region returns unknown status."""
        tool = RegionStatusTool()
        result = tool.execute(RegionStatusInput(region="unknown-region"))
        
        assert result.overall_status == "unknown"
    
    def test_region_has_services_list(self):
        """Test that region status includes services list."""
        tool = RegionStatusTool()
        result = tool.execute(RegionStatusInput(region="us-east"))
        
        assert len(result.services) > 0
    
    def test_region_has_timestamp(self):
        """Test that region status includes timestamp."""
        tool = RegionStatusTool()
        result = tool.execute(RegionStatusInput(region="eu-west"))
        
        assert result.last_updated is not None