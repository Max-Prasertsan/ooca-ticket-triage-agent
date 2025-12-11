"""
Tools Package
==============

This package contains all tool implementations for the triage agent.

Tools follow a common interface defined in `base.py` and can be easily
added or removed without modifying the core agent logic.

Available Tools:
    - KnowledgeBaseTool: Search the knowledge base for relevant articles
    - CustomerHistoryTool: Look up customer history and risk indicators
    - RegionStatusTool: Check regional service health status
"""

from src.triage_agent.tools.base import BaseTool, ToolRegistry
from src.triage_agent.tools.customer_history import CustomerHistoryTool
from src.triage_agent.tools.knowledge_base import KnowledgeBaseTool
from src.triage_agent.tools.region_status import RegionStatusTool

__all__ = [
    "BaseTool",
    "ToolRegistry",
    "KnowledgeBaseTool",
    "CustomerHistoryTool",
    "RegionStatusTool",
]


def create_default_tools() -> list[BaseTool]:
    """
    Create the default set of tools for the triage agent.
    
    Returns:
        list[BaseTool]: List of instantiated tool objects.
    """
    return [
        KnowledgeBaseTool(),
        CustomerHistoryTool(),
        RegionStatusTool(),
    ]


def create_tool_registry() -> ToolRegistry:
    """
    Create a tool registry with all default tools registered.
    
    Returns:
        ToolRegistry: Registry with all tools available.
    """
    registry = ToolRegistry()
    for tool in create_default_tools():
        registry.register(tool)
    return registry