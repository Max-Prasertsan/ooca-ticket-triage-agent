"""
MCP Tools Tests
================

Tests for MCP-style integration tools:
- SlackSearchTool, SlackPostTool
- JiraSearchTool, JiraCreateTool
- PagerDutyIncidentsTool, PagerDutyCreateTool
"""

import pytest

from src.triage_agent.tools.slack import (
    SlackSearchTool,
    SlackSearchInput,
    SlackPostTool,
    SlackPostInput,
)
from src.triage_agent.tools.jira import (
    JiraSearchTool,
    JiraSearchInput,
    JiraCreateTool,
    JiraCreateInput,
)
from src.triage_agent.tools.pagerduty import (
    PagerDutyIncidentsTool,
    PagerDutyIncidentsInput,
    PagerDutyCreateTool,
    PagerDutyCreateInput,
)


class TestSlackSearchTool:
    """Tests for Slack search tool."""
    
    def test_tool_has_correct_name(self):
        """Test tool has correct name."""
        tool = SlackSearchTool()
        assert tool.name == "slack_search"
    
    def test_search_returns_messages(self):
        """Test that search returns messages."""
        tool = SlackSearchTool()
        result = tool.execute(SlackSearchInput(
            query="incident outage",
            limit=5
        ))
        
        assert result.total_matches > 0
        assert len(result.messages) <= 5
    
    def test_search_messages_have_required_fields(self):
        """Test that messages have required fields."""
        tool = SlackSearchTool()
        result = tool.execute(SlackSearchInput(query="support"))
        
        if result.messages:
            msg = result.messages[0]
            assert msg.channel is not None
            assert msg.user is not None
            assert msg.text is not None
            assert msg.timestamp is not None
    
    def test_search_with_channel_filter(self):
        """Test search with channel filter."""
        tool = SlackSearchTool()
        result = tool.execute(SlackSearchInput(
            query="escalation",
            channel="#support-escalations"
        ))
        
        for msg in result.messages:
            assert msg.channel == "#support-escalations"
    
    def test_messages_have_relevance_scores(self):
        """Test that messages have relevance scores."""
        tool = SlackSearchTool()
        result = tool.execute(SlackSearchInput(query="incident"))
        
        for msg in result.messages:
            assert 0.0 <= msg.relevance_score <= 1.0


class TestSlackPostTool:
    """Tests for Slack post tool."""
    
    def test_tool_has_correct_name(self):
        """Test tool has correct name."""
        tool = SlackPostTool()
        assert tool.name == "slack_post"
    
    def test_post_succeeds(self):
        """Test that posting a message succeeds."""
        tool = SlackPostTool()
        result = tool.execute(SlackPostInput(
            channel="#test-channel",
            message="Test notification"
        ))
        
        assert result.success is True
    
    def test_post_returns_message_id(self):
        """Test that post returns message ID."""
        tool = SlackPostTool()
        result = tool.execute(SlackPostInput(
            channel="#support",
            message="Alert message"
        ))
        
        assert result.message_id is not None
        assert len(result.message_id) > 0
    
    def test_post_returns_channel(self):
        """Test that post returns channel."""
        tool = SlackPostTool()
        result = tool.execute(SlackPostInput(
            channel="#incidents",
            message="Incident update"
        ))
        
        assert result.channel == "#incidents"
    
    def test_post_returns_timestamp(self):
        """Test that post returns timestamp."""
        tool = SlackPostTool()
        result = tool.execute(SlackPostInput(
            channel="#test",
            message="Test"
        ))
        
        assert result.posted_at is not None


class TestJiraSearchTool:
    """Tests for Jira search tool."""
    
    def test_tool_has_correct_name(self):
        """Test tool has correct name."""
        tool = JiraSearchTool()
        assert tool.name == "jira_search"
    
    def test_search_returns_issues(self):
        """Test that search returns issues."""
        tool = JiraSearchTool()
        result = tool.execute(JiraSearchInput(
            jql="project = SUPPORT AND status != Done"
        ))
        
        assert result.total > 0
        assert len(result.issues) > 0
    
    def test_issues_have_required_fields(self):
        """Test that issues have required fields."""
        tool = JiraSearchTool()
        result = tool.execute(JiraSearchInput(jql="project = SUPPORT"))
        
        if result.issues:
            issue = result.issues[0]
            assert issue.key is not None
            assert issue.summary is not None
            assert issue.status is not None
            assert issue.priority is not None
    
    def test_search_with_text_query(self):
        """Test search with text query."""
        tool = JiraSearchTool()
        result = tool.execute(JiraSearchInput(
            jql='text ~ "dashboard"'
        ))
        
        assert result.total > 0
    
    def test_search_respects_max_results(self):
        """Test that search respects max_results."""
        tool = JiraSearchTool()
        result = tool.execute(JiraSearchInput(
            jql="project = SUPPORT",
            max_results=2
        ))
        
        assert len(result.issues) <= 2


class TestJiraCreateTool:
    """Tests for Jira create tool."""
    
    def test_tool_has_correct_name(self):
        """Test tool has correct name."""
        tool = JiraCreateTool()
        assert tool.name == "jira_create"
    
    def test_create_succeeds(self):
        """Test that creating an issue succeeds."""
        tool = JiraCreateTool()
        result = tool.execute(JiraCreateInput(
            project="SUPPORT",
            issue_type="Bug",
            summary="Test issue",
            priority="High"
        ))
        
        assert result.success is True
    
    def test_create_returns_key(self):
        """Test that create returns issue key."""
        tool = JiraCreateTool()
        result = tool.execute(JiraCreateInput(
            project="SUPPORT",
            issue_type="Bug",
            summary="Test bug"
        ))
        
        assert result.key is not None
        assert result.key.startswith("SUPPORT-")
    
    def test_create_returns_url(self):
        """Test that create returns issue URL."""
        tool = JiraCreateTool()
        result = tool.execute(JiraCreateInput(
            project="SUPPORT",
            issue_type="Task",
            summary="Test task"
        ))
        
        assert result.url is not None
        assert "atlassian.net" in result.url
    
    def test_create_with_all_fields(self):
        """Test creating with all optional fields."""
        tool = JiraCreateTool()
        result = tool.execute(JiraCreateInput(
            project="SUPPORT",
            issue_type="Bug",
            summary="Full issue",
            description="Detailed description",
            priority="Critical",
            labels=["enterprise", "urgent"],
            assignee="support-agent"
        ))
        
        assert result.success is True


class TestPagerDutyIncidentsTool:
    """Tests for PagerDuty incidents tool."""
    
    def test_tool_has_correct_name(self):
        """Test tool has correct name."""
        tool = PagerDutyIncidentsTool()
        assert tool.name == "pagerduty_incidents"
    
    def test_get_incidents_returns_results(self):
        """Test that getting incidents returns results."""
        tool = PagerDutyIncidentsTool()
        result = tool.execute(PagerDutyIncidentsInput())
        
        assert result.total > 0
        assert len(result.incidents) > 0
    
    def test_incidents_have_required_fields(self):
        """Test that incidents have required fields."""
        tool = PagerDutyIncidentsTool()
        result = tool.execute(PagerDutyIncidentsInput())
        
        if result.incidents:
            incident = result.incidents[0]
            assert incident.id is not None
            assert incident.title is not None
            assert incident.status in ["triggered", "acknowledged", "resolved"]
            assert incident.urgency in ["high", "low"]
    
    def test_filter_by_urgency(self):
        """Test filtering incidents by urgency."""
        tool = PagerDutyIncidentsTool()
        result = tool.execute(PagerDutyIncidentsInput(urgency="high"))
        
        for incident in result.incidents:
            assert incident.urgency == "high"
    
    def test_has_critical_flag(self):
        """Test has_critical flag is set correctly."""
        tool = PagerDutyIncidentsTool()
        result = tool.execute(PagerDutyIncidentsInput())
        
        has_high = any(i.urgency == "high" for i in result.incidents)
        assert result.has_critical == has_high


class TestPagerDutyCreateTool:
    """Tests for PagerDuty create incident tool."""
    
    def test_tool_has_correct_name(self):
        """Test tool has correct name."""
        tool = PagerDutyCreateTool()
        assert tool.name == "pagerduty_create"
    
    def test_create_succeeds(self):
        """Test that creating an incident succeeds."""
        tool = PagerDutyCreateTool()
        result = tool.execute(PagerDutyCreateInput(
            title="Test incident",
            service_id="SVC-TEST"
        ))
        
        assert result.success is True
    
    def test_create_returns_incident_id(self):
        """Test that create returns incident ID."""
        tool = PagerDutyCreateTool()
        result = tool.execute(PagerDutyCreateInput(
            title="Test incident",
            service_id="SVC-TEST"
        ))
        
        assert result.incident_id is not None
        assert result.incident_id.startswith("P-INC-")
    
    def test_create_returns_triggered_status(self):
        """Test that new incidents have triggered status."""
        tool = PagerDutyCreateTool()
        result = tool.execute(PagerDutyCreateInput(
            title="Urgent issue",
            service_id="SVC-PROD"
        ))
        
        assert result.status == "triggered"
    
    def test_create_returns_assigned_user(self):
        """Test that create returns assigned user."""
        tool = PagerDutyCreateTool()
        result = tool.execute(PagerDutyCreateInput(
            title="Critical alert",
            service_id="SVC-PROD",
            urgency="high"
        ))
        
        assert result.assigned_to is not None
    
    def test_create_with_customer_context(self):
        """Test creating with customer context."""
        tool = PagerDutyCreateTool()
        result = tool.execute(PagerDutyCreateInput(
            title="Enterprise outage",
            service_id="SVC-ENTERPRISE",
            urgency="high",
            description="Production down",
            ticket_id="T-12345",
            customer="BigCorp"
        ))
        
        assert result.success is True


class TestToolRegistration:
    """Tests for MCP tool registration."""
    
    def test_all_mcp_tools_in_registry(self, tool_registry):
        """Test all MCP tools are in default registry."""
        mcp_tools = [
            "slack_search",
            "slack_post",
            "jira_search",
            "jira_create",
            "pagerduty_incidents",
            "pagerduty_create",
        ]
        
        for tool_name in mcp_tools:
            assert tool_registry.has_tool(tool_name), f"Missing: {tool_name}"
    
    def test_mcp_tools_excluded_when_disabled(self, tool_registry_native_only):
        """Test MCP tools excluded when include_mcp=False."""
        mcp_tools = [
            "slack_search",
            "slack_post",
            "jira_search",
            "jira_create",
            "pagerduty_incidents",
            "pagerduty_create",
        ]
        
        for tool_name in mcp_tools:
            assert not tool_registry_native_only.has_tool(tool_name)
    
    def test_native_tools_always_present(self, tool_registry_native_only):
        """Test native tools present even without MCP."""
        assert tool_registry_native_only.has_tool("knowledge_base_search")
        assert tool_registry_native_only.has_tool("customer_history")
        assert tool_registry_native_only.has_tool("region_status")