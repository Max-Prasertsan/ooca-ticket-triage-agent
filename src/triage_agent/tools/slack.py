"""
Slack Tools
============

MCP-style tools for Slack integration.

These tools simulate connecting to Slack via MCP to:
- Search messages for relevant context about customer issues
- Post notifications to support channels

In production, these would connect to a real Slack MCP server.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Optional, Type

from pydantic import BaseModel, Field

from src.triage_agent.tools.base import BaseTool

logger = logging.getLogger(__name__)


# =============================================================================
# Mock Slack Data
# =============================================================================

MOCK_SLACK_MESSAGES = [
    {
        "channel": "#support-escalations",
        "user": "sarah.chen",
        "user_display": "Sarah Chen",
        "text": "Heads up team - BigCorp reported intermittent issues with their dashboard this morning. Engineering is investigating.",
        "timestamp": "2024-01-15T09:30:00Z",
        "thread_replies": 3
    },
    {
        "channel": "#engineering",
        "user": "mike.ops",
        "user_display": "Mike (DevOps)",
        "text": "Deploying hotfix for the authentication service. Should resolve the 503 errors some users are seeing.",
        "timestamp": "2024-01-15T10:15:00Z",
        "thread_replies": 5
    },
    {
        "channel": "#incidents",
        "user": "pagerduty-bot",
        "user_display": "PagerDuty Bot",
        "text": "🚨 INCIDENT OPENED: Elevated error rates on us-east-1 API gateway. On-call: @david.wang",
        "timestamp": "2024-01-15T08:45:00Z",
        "thread_replies": 12
    },
    {
        "channel": "#support-escalations",
        "user": "emma.support",
        "user_display": "Emma (Support Lead)",
        "text": "FYI - We've had 3 enterprise customers report billing discrepancies this week. Finance team is reviewing.",
        "timestamp": "2024-01-14T16:20:00Z",
        "thread_replies": 2
    },
    {
        "channel": "#customer-success",
        "user": "james.csm",
        "user_display": "James (CSM)",
        "text": "BigCorp renewal coming up next month. They've been happy with the new features but mentioned some performance concerns.",
        "timestamp": "2024-01-12T14:00:00Z",
        "thread_replies": 4
    },
]

MOCK_POSTED_MESSAGES = []


# =============================================================================
# Slack Search Tool
# =============================================================================

class SlackSearchInput(BaseModel):
    """Input schema for Slack message search."""
    query: str = Field(
        ...,
        description="Search query - keywords to find in Slack messages"
    )
    channel: Optional[str] = Field(
        None,
        description="Specific channel to search (e.g., #support-escalations). If not provided, searches all channels."
    )
    limit: int = Field(
        5,
        description="Maximum number of messages to return",
        ge=1,
        le=20
    )


class SlackMessage(BaseModel):
    """A Slack message result."""
    channel: str
    user: str
    user_display: str
    text: str
    timestamp: str
    thread_replies: int = 0
    relevance_score: float = 0.0


class SlackSearchOutput(BaseModel):
    """Output schema for Slack message search."""
    messages: list[SlackMessage] = Field(default_factory=list)
    total_matches: int = 0
    query_processed: str = ""


class SlackSearchTool(BaseTool[SlackSearchInput, SlackSearchOutput]):
    """
    Tool for searching Slack messages.
    
    Use this tool to find relevant context about a customer's issue from
    internal Slack discussions. This can reveal:
    - Previous discussions about the customer
    - Known incidents affecting their region/product
    - Internal notes from other support agents
    - Engineering updates about related issues
    
    When to use:
    - Enterprise customers (check for account-specific context)
    - Outage/incident reports (check #incidents, #engineering)
    - Escalations (check #support-escalations)
    - Billing issues (check for finance team discussions)
    """
    
    name: str = "slack_search"
    description: str = (
        "Search Slack messages for relevant context about a customer issue. "
        "Returns matching messages from support, engineering, and incident channels. "
        "Use this to find previous discussions, known incidents, or internal context."
    )
    input_model: Type[SlackSearchInput] = SlackSearchInput
    output_model: Type[SlackSearchOutput] = SlackSearchOutput
    
    def _execute(self, input_data: SlackSearchInput) -> SlackSearchOutput:
        """Search mock Slack messages."""
        query_lower = input_data.query.lower()
        query_terms = query_lower.split()
        
        results = []
        for msg in MOCK_SLACK_MESSAGES:
            # Filter by channel if specified
            if input_data.channel and msg["channel"] != input_data.channel:
                continue
            
            # Calculate relevance score
            text_lower = msg["text"].lower()
            channel_lower = msg["channel"].lower()
            
            score = 0.0
            matches = 0
            for term in query_terms:
                if term in text_lower:
                    score += 0.3
                    matches += 1
                if term in channel_lower:
                    score += 0.1
                if term in msg["user_display"].lower():
                    score += 0.1
            
            # Boost recent messages
            if "2024-01-15" in msg["timestamp"]:
                score += 0.1
            
            # Boost messages with engagement
            if msg["thread_replies"] > 5:
                score += 0.1
            
            if score > 0:
                results.append(SlackMessage(
                    channel=msg["channel"],
                    user=msg["user"],
                    user_display=msg["user_display"],
                    text=msg["text"],
                    timestamp=msg["timestamp"],
                    thread_replies=msg["thread_replies"],
                    relevance_score=min(score, 1.0)
                ))
        
        # Sort by relevance and limit
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        results = results[:input_data.limit]
        
        return SlackSearchOutput(
            messages=results,
            total_matches=len(results),
            query_processed=input_data.query
        )


# =============================================================================
# Slack Post Tool
# =============================================================================

class SlackPostInput(BaseModel):
    """Input schema for posting Slack messages."""
    channel: str = Field(
        ...,
        description="Channel to post to (e.g., #support-escalations, #incidents)"
    )
    message: str = Field(
        ...,
        description="Message content to post. Supports Slack markdown formatting."
    )
    thread_ts: Optional[str] = Field(
        None,
        description="Thread timestamp to reply in a thread (optional)"
    )


class SlackPostOutput(BaseModel):
    """Output schema for posting Slack messages."""
    success: bool = True
    message_id: str = ""
    channel: str = ""
    posted_at: str = ""
    error: Optional[str] = None


class SlackPostTool(BaseTool[SlackPostInput, SlackPostOutput]):
    """
    Tool for posting messages to Slack channels.
    
    Use this tool to notify teams about escalations, post updates to
    incident channels, or alert on-call engineers about critical issues.
    
    When to use:
    - Critical escalations → post to #support-escalations
    - Active incidents → post to #incidents
    - Engineering issues → post to #engineering
    - Enterprise customer issues → post to #customer-success
    
    Important: Only use for genuinely important notifications.
    Avoid spamming channels with routine updates.
    """
    
    name: str = "slack_post"
    description: str = (
        "Post a message to a Slack channel. Use this to notify teams about "
        "escalations, alert on-call engineers, or update incident channels. "
        "Only use for important notifications that require team awareness."
    )
    input_model: Type[SlackPostInput] = SlackPostInput
    output_model: Type[SlackPostOutput] = SlackPostOutput
    
    def _execute(self, input_data: SlackPostInput) -> SlackPostOutput:
        """Post to mock Slack."""
        # Generate mock message ID
        msg_id = f"msg_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(MOCK_POSTED_MESSAGES)}"
        posted_at = datetime.now(timezone.utc).isoformat()
        
        # Store the posted message (for demo purposes)
        MOCK_POSTED_MESSAGES.append({
            "id": msg_id,
            "channel": input_data.channel,
            "message": input_data.message,
            "thread_ts": input_data.thread_ts,
            "posted_at": posted_at
        })
        
        logger.info(f"Posted to {input_data.channel}: {input_data.message[:50]}...")
        
        return SlackPostOutput(
            success=True,
            message_id=msg_id,
            channel=input_data.channel,
            posted_at=posted_at
        )