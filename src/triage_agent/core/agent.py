"""
Triage Agent Module
====================

Main orchestrator for the support ticket triage agent.

This module coordinates:
- LLM interactions via OpenAI API
- Tool execution and management
- Response parsing and validation
- Business rule application
"""

import json
import logging
from typing import Any, Optional

from openai import OpenAI

from src.triage_agent.config import Config
from src.triage_agent.core.triage_logic import TriageLogic
from src.triage_agent.models.ticket import SupportTicket
from src.triage_agent.models.triage_output import (
    CustomerSentiment,
    IssueType,
    KnowledgeBaseResult,
    RecommendedAction,
    RiskSignal,
    SpecialistQueue,
    ToolCallRecord,
    TriageOutput,
    UrgencyLevel,
)
from src.triage_agent.prompts.system_prompt import (
    get_json_schema_prompt,
    get_system_prompt,
    get_tool_usage_prompt,
)
from src.triage_agent.tools import ToolRegistry, create_tool_registry
from src.triage_agent.tools.base import BaseTool, ToolExecutionError

logger = logging.getLogger(__name__)


class TriageAgent:
    """
    Main triage agent orchestrator.
    
    Coordinates the triage process including:
    - Sending tickets to the LLM with appropriate prompts
    - Handling tool calls from the LLM
    - Parsing and validating responses
    - Applying business rule overrides
    
    Attributes:
        config: Application configuration.
        client: OpenAI client instance.
        tool_registry: Registry of available tools.
        triage_logic: Business rule logic handler.
    
    Example:
        >>> agent = TriageAgent(Config())
        >>> result = agent.triage(ticket)
        >>> print(result.urgency)
    """
    
    def __init__(
        self,
        config: Config,
        tool_registry: Optional[ToolRegistry] = None,
        client: Optional[OpenAI] = None
    ):
        """
        Initialize the triage agent.
        
        Args:
            config: Application configuration.
            tool_registry: Optional custom tool registry.
            client: Optional OpenAI client (for testing).
        """
        self.config = config
        self.tool_registry = tool_registry or create_tool_registry()
        self.triage_logic = TriageLogic()
        
        # Initialize OpenAI client if API key is available
        if config.is_api_key_set():
            self.client = client or OpenAI(api_key=config.openai_api_key)
        else:
            self.client = None
            logger.warning("OpenAI API key not set - using mock mode")
    
    def triage(self, ticket: SupportTicket) -> TriageOutput:
        """
        Triage a support ticket.
        
        This is the main entry point for processing a ticket.
        
        Args:
            ticket: The support ticket to triage.
        
        Returns:
            TriageOutput: Complete triage output with classifications and recommendations.
        """
        logger.info(f"Starting triage for ticket: {ticket.ticket_id}")
        
        # If no API key, use rule-based fallback
        if not self.client:
            logger.info("Using rule-based fallback (no API key)")
            return self._rule_based_triage(ticket)
        
        try:
            return self._llm_triage(ticket)
        except Exception as e:
            logger.error(f"LLM triage failed: {e}, falling back to rules")
            return self._rule_based_triage(ticket)
    
    def _llm_triage(self, ticket: SupportTicket) -> TriageOutput:
        """
        Triage using the LLM with tool calls.
        
        Args:
            ticket: The support ticket.
        
        Returns:
            TriageOutput: LLM-generated triage output.
        """
        tool_calls_made: list[ToolCallRecord] = []
        
        # Prepare the initial messages
        messages = [
            {"role": "system", "content": get_system_prompt()},
            {"role": "user", "content": self._format_ticket_prompt(ticket)}
        ]
        
        # Get tool schemas
        tools = self.tool_registry.get_schemas()
        
        # Initial API call
        response = self.client.chat.completions.create(
            model=self.config.openai_model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=self.config.openai_temperature,
            max_tokens=4096
        )
        
        # Handle tool calls in a loop
        max_iterations = 10
        iteration = 0
        
        while response.choices[0].message.tool_calls and iteration < max_iterations:
            iteration += 1
            assistant_message = response.choices[0].message
            messages.append(assistant_message)
            
            # Process each tool call
            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                
                logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
                
                # Execute the tool
                tool_result, success, error_msg = self._execute_tool(
                    tool_name, tool_args
                )
                
                # Record the tool call
                tool_calls_made.append(ToolCallRecord(
                    tool_name=tool_name,
                    inputs=tool_args,
                    outputs=tool_result if success else {},
                    success=success,
                    error_message=error_msg
                ))
                
                # Add tool result to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_result)
                })
            
            # Continue the conversation
            response = self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=self.config.openai_temperature,
                max_tokens=4096
            )
        
        # Parse the final response
        final_content = response.choices[0].message.content
        triage_output = self._parse_llm_response(
            final_content, ticket, tool_calls_made
        )
        
        # Apply business rule overrides
        triage_output = self._apply_business_rules(triage_output, ticket)
        
        return triage_output
    
    def _execute_tool(
        self,
        tool_name: str,
        tool_args: dict[str, Any]
    ) -> tuple[dict[str, Any], bool, Optional[str]]:
        """
        Execute a tool and return results.
        
        Args:
            tool_name: Name of the tool to execute.
            tool_args: Arguments to pass to the tool.
        
        Returns:
            Tuple of (result_dict, success_bool, error_message_or_none)
        """
        try:
            if not self.tool_registry.has_tool(tool_name):
                return {"error": f"Unknown tool: {tool_name}"}, False, f"Unknown tool: {tool_name}"
            
            tool = self.tool_registry.get(tool_name)
            input_data = tool.validate_input(tool_args)
            result = tool.execute(input_data)
            
            return result.model_dump(), True, None
            
        except ToolExecutionError as e:
            logger.error(f"Tool execution error: {e}")
            return {"error": str(e)}, False, str(e)
        except Exception as e:
            logger.error(f"Unexpected tool error: {e}")
            return {"error": str(e)}, False, str(e)
    
    def _format_ticket_prompt(self, ticket: SupportTicket) -> str:
        """
        Format the ticket as a prompt for the LLM.
        
        Args:
            ticket: The support ticket.
        
        Returns:
            str: Formatted prompt text.
        """
        tool_reminder = get_tool_usage_prompt(self.tool_registry.get_names())
        json_reminder = get_json_schema_prompt()
        
        return f"""Please triage the following support ticket:

---
TICKET ID: {ticket.ticket_id}
SUBJECT: {ticket.subject}
CUSTOMER EMAIL: {ticket.customer_email}
CUSTOMER NAME: {ticket.customer_name or 'Not provided'}
CUSTOMER TIER: {ticket.customer_tier}
CUSTOMER REGION: {ticket.customer_region or 'Not specified'}
CHANNEL: {ticket.channel}
TIMESTAMP: {ticket.timestamp or 'Not provided'}

TICKET BODY:
{ticket.body}
---

{tool_reminder}

After using the tools, provide your final triage assessment.

{json_reminder}
"""
    
    def _parse_llm_response(
        self,
        content: str,
        ticket: SupportTicket,
        tool_calls: list[ToolCallRecord]
    ) -> TriageOutput:
        """
        Parse the LLM response into a TriageOutput.
        
        Args:
            content: Raw LLM response content.
            ticket: The original ticket.
            tool_calls: List of tool calls made.
        
        Returns:
            TriageOutput: Parsed triage output.
        """
        try:
            # Clean up the response (remove markdown code blocks if present)
            content = content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()
            
            # Parse JSON
            data = json.loads(content)
            
            # Extract KB results
            kb_results = []
            for kb in data.get("knowledge_base_results", []):
                kb_results.append(KnowledgeBaseResult(
                    id=kb.get("id", ""),
                    title=kb.get("title", ""),
                    url=kb.get("url", ""),
                    relevance_score=float(kb.get("relevance_score", 0.0)),
                    snippet=kb.get("snippet")
                ))
            
            # Parse risk signals
            risk_signals = []
            for signal in data.get("customer_risk_signals", []):
                try:
                    risk_signals.append(RiskSignal(signal))
                except ValueError:
                    logger.warning(f"Unknown risk signal: {signal}")
            
            return TriageOutput(
                ticket_id=ticket.ticket_id,
                urgency=UrgencyLevel(data.get("urgency", "medium")),
                product=data.get("product"),
                issue_type=IssueType(data.get("issue_type", "other")),
                customer_sentiment=CustomerSentiment(data.get("customer_sentiment", "neutral")),
                customer_risk_signals=risk_signals,
                recommended_action=RecommendedAction(data.get("recommended_action", "route_to_specialist")),
                recommended_specialist_queue=SpecialistQueue(data.get("recommended_specialist_queue", "none")),
                knowledge_base_results=kb_results,
                suggested_reply=data.get("suggested_reply"),
                tool_calls=tool_calls,
                confidence_score=float(data.get("confidence_score", 0.8)),
                reasoning=data.get("reasoning")
            )
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            logger.debug(f"Raw content: {content}")
            # Return a safe fallback
            return self._create_fallback_output(ticket, tool_calls, str(e))
    
    def _create_fallback_output(
        self,
        ticket: SupportTicket,
        tool_calls: list[ToolCallRecord],
        error: str
    ) -> TriageOutput:
        """
        Create a fallback output when parsing fails.
        
        Args:
            ticket: The original ticket.
            tool_calls: Tool calls made.
            error: Error message.
        
        Returns:
            TriageOutput: Safe fallback output.
        """
        return TriageOutput(
            ticket_id=ticket.ticket_id,
            urgency=UrgencyLevel.MEDIUM,
            product=None,
            issue_type=IssueType.OTHER,
            customer_sentiment=CustomerSentiment.NEUTRAL,
            customer_risk_signals=[],
            recommended_action=RecommendedAction.ROUTE_TO_SPECIALIST,
            recommended_specialist_queue=SpecialistQueue.TIER_2,
            knowledge_base_results=[],
            suggested_reply=None,
            tool_calls=tool_calls,
            confidence_score=0.3,
            reasoning=f"Fallback triage due to parsing error: {error}"
        )
    
    def _apply_business_rules(
        self,
        output: TriageOutput,
        ticket: SupportTicket
    ) -> TriageOutput:
        """
        Apply business rule overrides to the triage output.
        
        Args:
            output: Initial triage output.
            ticket: The original ticket.
        
        Returns:
            TriageOutput: Output with business rules applied.
        """
        # Check for urgency override
        urgency_override = self.triage_logic.calculate_urgency_override(
            ticket, output.urgency.value
        )
        if urgency_override:
            output.urgency = urgency_override
        
        # Add any missed risk signals
        detected_signals = self.triage_logic.detect_risk_signals(ticket)
        for signal in detected_signals:
            if signal not in output.customer_risk_signals:
                output.customer_risk_signals.append(signal)
        
        # Recalculate action based on updated urgency and signals
        has_kb = len(output.knowledge_base_results) > 0
        new_action = self.triage_logic.determine_action(
            output.urgency,
            output.customer_sentiment,
            output.issue_type,
            output.customer_risk_signals,
            ticket,
            has_kb
        )
        
        # Only override if our rules say to escalate/route
        if new_action.value != output.recommended_action.value:
            if new_action in [RecommendedAction.ESCALATE_TO_HUMAN, RecommendedAction.ROUTE_TO_SPECIALIST]:
                output.recommended_action = new_action
        
        # Update specialist queue
        output.recommended_specialist_queue = self.triage_logic.determine_specialist_queue(
            output.issue_type,
            output.urgency,
            ticket,
            output.customer_risk_signals
        )
        
        return output
    
    def _rule_based_triage(self, ticket: SupportTicket) -> TriageOutput:
        """
        Perform rule-based triage without LLM.
        
        Used as fallback when API is unavailable or for testing.
        
        Args:
            ticket: The support ticket.
        
        Returns:
            TriageOutput: Rule-based triage output.
        """
        logger.info(f"Performing rule-based triage for: {ticket.ticket_id}")
        
        tool_calls: list[ToolCallRecord] = []
        kb_results: list[KnowledgeBaseResult] = []
        
        # Execute tools manually
        # 1. Search knowledge base
        from src.triage_agent.tools.knowledge_base import KnowledgeBaseTool
        from src.triage_agent.models.tools import KnowledgeBaseInput
        
        kb_tool = KnowledgeBaseTool()
        query_terms = ticket.subject.lower().split()[:4]
        kb_input = KnowledgeBaseInput(query=" ".join(query_terms))
        
        try:
            kb_output = kb_tool.execute(kb_input)
            tool_calls.append(ToolCallRecord(
                tool_name="knowledge_base_search",
                inputs=kb_input.model_dump(),
                outputs=kb_output.model_dump(),
                success=True
            ))
            
            for article in kb_output.results[:3]:
                kb_results.append(KnowledgeBaseResult(
                    id=article.id,
                    title=article.title,
                    url=article.url,
                    relevance_score=article.relevance_score
                ))
        except Exception as e:
            logger.error(f"KB search failed: {e}")
        
        # 2. Check customer history
        from src.triage_agent.tools.customer_history import CustomerHistoryTool
        from src.triage_agent.models.tools import CustomerHistoryInput
        
        history_tool = CustomerHistoryTool()
        history_input = CustomerHistoryInput(customer_email=ticket.customer_email)
        
        customer_tier = ticket.customer_tier
        try:
            history_output = history_tool.execute(history_input)
            tool_calls.append(ToolCallRecord(
                tool_name="customer_history",
                inputs=history_input.model_dump(),
                outputs=history_output.model_dump(),
                success=True
            ))
            customer_tier = history_output.account_tier
        except Exception as e:
            logger.error(f"Customer history lookup failed: {e}")
        
        # Detect issue type from keywords
        issue_type = self.triage_logic.detect_issue_type_from_keywords(ticket)
        if not issue_type:
            issue_type = IssueType.OTHER
        
        # Determine urgency
        urgency = UrgencyLevel.MEDIUM
        text = ticket.get_full_text().lower()
        
        if any(kw in text for kw in ["urgent", "critical", "emergency", "down", "asap"]):
            urgency = UrgencyLevel.HIGH
        if ticket.is_enterprise() and "down" in text:
            urgency = UrgencyLevel.CRITICAL
        if issue_type == IssueType.FEATURE_REQUEST:
            urgency = UrgencyLevel.LOW
        
        # Detect sentiment (simple keyword-based)
        sentiment = CustomerSentiment.NEUTRAL
        negative_words = ["frustrated", "angry", "terrible", "worst", "unacceptable", "disappointed"]
        positive_words = ["thanks", "great", "love", "amazing", "appreciate"]
        
        if any(w in text for w in negative_words):
            sentiment = CustomerSentiment.NEGATIVE
        if any(w in text for w in positive_words):
            sentiment = CustomerSentiment.POSITIVE
        
        # Detect risk signals
        risk_signals = self.triage_logic.detect_risk_signals(ticket)
        
        # Determine action
        action = self.triage_logic.determine_action(
            urgency, sentiment, issue_type, risk_signals, ticket, len(kb_results) > 0
        )
        
        # Determine queue
        queue = self.triage_logic.determine_specialist_queue(
            issue_type, urgency, ticket, risk_signals
        )
        
        return TriageOutput(
            ticket_id=ticket.ticket_id,
            urgency=urgency,
            product=None,
            issue_type=issue_type,
            customer_sentiment=sentiment,
            customer_risk_signals=risk_signals,
            recommended_action=action,
            recommended_specialist_queue=queue,
            knowledge_base_results=kb_results,
            suggested_reply=None,
            tool_calls=tool_calls,
            confidence_score=0.6,
            reasoning="Rule-based triage (LLM unavailable)"
        )