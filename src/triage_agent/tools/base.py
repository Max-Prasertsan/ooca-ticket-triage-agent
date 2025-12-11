"""
Base Tool Interface
====================

Defines the abstract base class for all tools and the tool registry.

This module implements the Strategy pattern for tools, allowing
easy addition and removal of tools without modifying core agent logic.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Generic, Type, TypeVar

from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Type variables for generic tool typing
InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)


class BaseTool(ABC, Generic[InputT, OutputT]):
    """
    Abstract base class for all triage agent tools.
    
    All tools must implement this interface to be usable by the agent.
    The interface ensures consistent behavior and enables easy testing.
    
    Attributes:
        name: Unique identifier for the tool.
        description: Human-readable description for the agent.
        input_model: Pydantic model class for input validation.
        output_model: Pydantic model class for output validation.
    
    Example:
        >>> class MyTool(BaseTool[MyInput, MyOutput]):
        ...     name = "my_tool"
        ...     description = "Does something useful"
        ...     input_model = MyInput
        ...     output_model = MyOutput
        ...
        ...     def _execute(self, input_data: MyInput) -> MyOutput:
        ...         return MyOutput(result="success")
    """
    
    name: str
    description: str
    input_model: Type[InputT]
    output_model: Type[OutputT]
    
    def execute(self, input_data: InputT) -> OutputT:
        """
        Execute the tool with the given input.
        
        This method handles logging and error wrapping. Subclasses
        should implement _execute() instead of overriding this.
        
        Args:
            input_data: Validated input data matching input_model.
        
        Returns:
            OutputT: Tool output matching output_model.
        
        Raises:
            ToolExecutionError: If the tool fails to execute.
        """
        logger.info(f"Executing tool '{self.name}' with input: {input_data}")
        try:
            result = self._execute(input_data)
            logger.info(f"Tool '{self.name}' completed successfully")
            return result
        except Exception as e:
            logger.error(f"Tool '{self.name}' failed: {e}")
            raise ToolExecutionError(
                tool_name=self.name,
                message=str(e),
                original_error=e
            ) from e
    
    @abstractmethod
    def _execute(self, input_data: InputT) -> OutputT:
        """
        Internal execution method to be implemented by subclasses.
        
        Args:
            input_data: Validated input data.
        
        Returns:
            OutputT: Tool execution result.
        """
        pass
    
    def validate_input(self, raw_input: dict[str, Any]) -> InputT:
        """
        Validate and parse raw input dictionary.
        
        Args:
            raw_input: Raw input dictionary from the agent.
        
        Returns:
            InputT: Validated input model instance.
        
        Raises:
            ValidationError: If input doesn't match schema.
        """
        return self.input_model.model_validate(raw_input)
    
    def get_schema(self) -> dict[str, Any]:
        """
        Get the OpenAI-compatible function schema for this tool.
        
        Returns:
            dict: Function schema for OpenAI function calling.
        """
        input_schema = self.input_model.model_json_schema()
        
        # Remove title and description from top level (OpenAI doesn't use them)
        input_schema.pop("title", None)
        
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": input_schema
            }
        }
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name='{self.name}'>"


class ToolExecutionError(Exception):
    """
    Exception raised when a tool fails to execute.
    
    Attributes:
        tool_name: Name of the tool that failed.
        message: Error message.
        original_error: The original exception if available.
    """
    
    def __init__(
        self,
        tool_name: str,
        message: str,
        original_error: Exception | None = None
    ):
        self.tool_name = tool_name
        self.message = message
        self.original_error = original_error
        super().__init__(f"Tool '{tool_name}' failed: {message}")


class ToolRegistry:
    """
    Registry for managing available tools.
    
    The registry provides a centralized place to register, retrieve,
    and list tools available to the agent.
    
    Example:
        >>> registry = ToolRegistry()
        >>> registry.register(KnowledgeBaseTool())
        >>> tool = registry.get("knowledge_base_search")
        >>> tools = registry.get_all()
    """
    
    def __init__(self):
        """Initialize an empty tool registry."""
        self._tools: dict[str, BaseTool] = {}
    
    def register(self, tool: BaseTool) -> None:
        """
        Register a tool with the registry.
        
        Args:
            tool: Tool instance to register.
        
        Raises:
            ValueError: If a tool with the same name already exists.
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        
        self._tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")
    
    def unregister(self, tool_name: str) -> None:
        """
        Remove a tool from the registry.
        
        Args:
            tool_name: Name of the tool to remove.
        
        Raises:
            KeyError: If the tool is not registered.
        """
        if tool_name not in self._tools:
            raise KeyError(f"Tool '{tool_name}' is not registered")
        
        del self._tools[tool_name]
        logger.debug(f"Unregistered tool: {tool_name}")
    
    def get(self, tool_name: str) -> BaseTool:
        """
        Get a tool by name.
        
        Args:
            tool_name: Name of the tool to retrieve.
        
        Returns:
            BaseTool: The requested tool.
        
        Raises:
            KeyError: If the tool is not registered.
        """
        if tool_name not in self._tools:
            raise KeyError(f"Tool '{tool_name}' is not registered")
        return self._tools[tool_name]
    
    def get_all(self) -> list[BaseTool]:
        """
        Get all registered tools.
        
        Returns:
            list[BaseTool]: List of all registered tools.
        """
        return list(self._tools.values())
    
    def get_names(self) -> list[str]:
        """
        Get names of all registered tools.
        
        Returns:
            list[str]: List of tool names.
        """
        return list(self._tools.keys())
    
    def get_schemas(self) -> list[dict[str, Any]]:
        """
        Get OpenAI function schemas for all registered tools.
        
        Returns:
            list[dict]: List of function schemas.
        """
        return [tool.get_schema() for tool in self._tools.values()]
    
    def has_tool(self, tool_name: str) -> bool:
        """
        Check if a tool is registered.
        
        Args:
            tool_name: Name of the tool to check.
        
        Returns:
            bool: True if the tool is registered.
        """
        return tool_name in self._tools
    
    def __len__(self) -> int:
        return len(self._tools)
    
    def __contains__(self, tool_name: str) -> bool:
        return tool_name in self._tools
    
    def __repr__(self) -> str:
        return f"<ToolRegistry tools={list(self._tools.keys())}>"