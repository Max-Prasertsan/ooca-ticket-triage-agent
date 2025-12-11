"""
Prompts Package
================

Contains system prompts and prompt templates for the triage agent.

Modules:
    system_prompt: Main system prompt for the triage agent
"""

from src.triage_agent.prompts.system_prompt import (
    SYSTEM_PROMPT,
    get_system_prompt,
    get_tool_usage_prompt,
)

__all__ = [
    "SYSTEM_PROMPT",
    "get_system_prompt",
    "get_tool_usage_prompt",
]