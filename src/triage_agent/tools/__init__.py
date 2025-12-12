"""
Tools Package
==============

This package contains all tool implementations for the triage agent.

Tools follow a common interface defined in `base.py` and can be easily
added or removed without modifying the core agent logic.

Native Tools:
    - KnowledgeBaseTool: Search the knowledge base for relevant articles
    - CustomerHistoryTool: Look up customer history and risk indicators
    - RegionStatusTool: Check regional service health status

MCP-Style Integration Tools:
    - SlackSearchTool: Search Slack messages for internal context
    - SlackPostTool: Post notifications to Slack channels
    - JiraSearchTool: Search Jira for related tickets
    - JiraCreateTool: Create Jira tickets for tracking
    - PagerDutyIncidentsTool: Check active incidents
    - PagerDutyCreateTool: Page on-call engineers

All tools work together seamlessly - the agent uses them based on the
situation to gather context, take actions, and route appropriately.
"""

from src.triage_agent.tools.base import BaseTool, ToolRegistry
from src.triage_agent.tools.customer_history import CustomerHistoryTool
from src.triage_agent.tools.knowledge_base import KnowledgeBaseTool
from src.triage_agent.tools.region_status import RegionStatusTool
from src.triage_agent.tools.slack import SlackSearchTool, SlackPostTool
from src.triage_agent.tools.jira import JiraSearchTool, JiraCreateTool
from src.triage_agent.tools.pagerduty import PagerDutyIncidentsTool, PagerDutyCreateTool

__all__ = [
    # Base classes
    "BaseTool",
    "ToolRegistry",
    # Native tools
    "KnowledgeBaseTool",
    "CustomerHistoryTool",
    "RegionStatusTool",
    # Slack tools (MCP-style)
    "SlackSearchTool",
    "SlackPostTool",
    # Jira tools (MCP-style)
    "JiraSearchTool",
    "JiraCreateTool",
    # PagerDuty tools (MCP-style)
    "PagerDutyIncidentsTool",
    "PagerDutyCreateTool",
    # Factory functions
    "create_default_tools",
    "create_tool_registry",
]


def create_default_tools(include_mcp: bool = True) -> list[BaseTool]:
    """
    Create the default set of tools for the triage agent.
    
    Args:
        include_mcp: Whether to include MCP-style tools (Slack, Jira, PagerDuty).
                     Defaults to True for full functionality.
    
    Returns:
        list[BaseTool]: List of instantiated tool objects.
    """
    # Core native tools - always included
    tools = [
        KnowledgeBaseTool(),
        CustomerHistoryTool(),
        RegionStatusTool(),
    ]
    
    # MCP-style integration tools - included by default
    if include_mcp:
        tools.extend([
            # Slack integration
            SlackSearchTool(),
            SlackPostTool(),
            # Jira integration
            JiraSearchTool(),
            JiraCreateTool(),
            # PagerDuty integration
            PagerDutyIncidentsTool(),
            PagerDutyCreateTool(),
        ])
    
    return tools


def create_tool_registry(include_mcp: bool = True) -> ToolRegistry:
    """
    Create a tool registry with all default tools registered.
    
    Args:
        include_mcp: Whether to include MCP-style tools. Defaults to True.
    
    Returns:
        ToolRegistry: Registry with all tools available.
    """
    registry = ToolRegistry()
    for tool in create_default_tools(include_mcp=include_mcp):
        registry.register(tool)
    return registry