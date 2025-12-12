"""
MCP Server Connection Example
==============================

This file provides skeleton code showing how to connect to a real MCP
(Model Context Protocol) server instead of using the mock implementations.

MCP is a protocol for connecting AI agents to external tools and services.
For more information, see: https://modelcontextprotocol.io/

The mock tools in this project (slack.py, jira.py, pagerduty.py) simulate
MCP server responses. In production, you would replace them with real
MCP client connections as shown below.

Usage:
    # 1. Install the MCP SDK
    pip install mcp

    # 2. Configure your MCP servers in mcp_config.json
    
    # 3. Use the MCPClient to connect and call tools
    from src.triage_agent.tools.mcp_example import MCPClient
    
    async with MCPClient("path/to/mcp_config.json") as client:
        result = await client.call_tool("slack", "search_messages", {"query": "outage"})
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Type

from pydantic import BaseModel

from src.triage_agent.tools.base import BaseTool

logger = logging.getLogger(__name__)


# =============================================================================
# MCP Configuration Models
# =============================================================================

@dataclass
class MCPServerConfig:
    """
    Configuration for connecting to an MCP server.
    
    Attributes:
        name: Unique identifier for the server (e.g., "slack", "jira")
        command: Command to start the MCP server process
        args: Arguments to pass to the server command
        env: Environment variables for the server process
        transport: Transport type ("stdio" or "http")
        url: URL for HTTP transport (if applicable)
    """
    name: str
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    transport: str = "stdio"  # "stdio" or "http"
    url: Optional[str] = None  # For HTTP transport


@dataclass
class MCPToolDefinition:
    """
    Definition of a tool exposed by an MCP server.
    
    Attributes:
        name: Tool name
        description: Human-readable description
        input_schema: JSON Schema for tool inputs
        server_name: Name of the MCP server that provides this tool
    """
    name: str
    description: str
    input_schema: dict[str, Any]
    server_name: str


# =============================================================================
# MCP Client (Skeleton Implementation)
# =============================================================================

class MCPClient:
    """
    Client for connecting to MCP servers.
    
    This is a skeleton implementation showing the interface. In production,
    you would use the official MCP SDK:
    
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
    
    Example:
        async with MCPClient("config.json") as client:
            # List available tools
            tools = await client.list_tools()
            
            # Call a tool
            result = await client.call_tool(
                server="slack",
                tool="search_messages", 
                arguments={"query": "incident"}
            )
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the MCP client.
        
        Args:
            config_path: Path to MCP configuration JSON file
        """
        self.config_path = config_path
        self.servers: dict[str, MCPServerConfig] = {}
        self.connections: dict[str, Any] = {}  # Active server connections
        self.tools: dict[str, MCPToolDefinition] = {}
        self._connected = False
    
    async def __aenter__(self):
        """Async context manager entry - connects to servers."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - disconnects from servers."""
        await self.disconnect()
    
    def load_config(self, config_path: str) -> dict[str, MCPServerConfig]:
        """
        Load MCP server configurations from a JSON file.
        
        Expected format:
        {
            "mcpServers": {
                "slack": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-slack"],
                    "env": {
                        "SLACK_BOT_TOKEN": "xoxb-your-token",
                        "SLACK_TEAM_ID": "T0123456789"
                    }
                },
                "github": {
                    "command": "npx", 
                    "args": ["-y", "@modelcontextprotocol/server-github"],
                    "env": {
                        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_xxxx"
                    }
                }
            }
        }
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Dictionary of server name to MCPServerConfig
        """
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"MCP config not found: {config_path}")
        
        with open(path) as f:
            config = json.load(f)
        
        servers = {}
        for name, server_config in config.get("mcpServers", {}).items():
            servers[name] = MCPServerConfig(
                name=name,
                command=server_config.get("command", ""),
                args=server_config.get("args", []),
                env=server_config.get("env", {}),
                transport=server_config.get("transport", "stdio"),
                url=server_config.get("url")
            )
        
        return servers
    
    async def connect(self) -> None:
        """
        Connect to all configured MCP servers.
        
        In production with the MCP SDK, this would look like:
        
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client
            
            server_params = StdioServerParameters(
                command=config.command,
                args=config.args,
                env=config.env
            )
            
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    self.connections[name] = session
        """
        if self.config_path:
            self.servers = self.load_config(self.config_path)
        
        for name, config in self.servers.items():
            try:
                # SKELETON: Replace with actual MCP connection
                # This is where you would use the MCP SDK to connect
                logger.info(f"Connecting to MCP server: {name}")
                logger.info(f"  Command: {config.command} {' '.join(config.args)}")
                
                # Placeholder for actual connection
                # self.connections[name] = await self._create_connection(config)
                
                # After connecting, discover available tools
                # tools = await self.connections[name].list_tools()
                # for tool in tools:
                #     self.tools[f"{name}.{tool.name}"] = MCPToolDefinition(...)
                
            except Exception as e:
                logger.error(f"Failed to connect to {name}: {e}")
        
        self._connected = True
    
    async def disconnect(self) -> None:
        """Disconnect from all MCP servers."""
        for name, connection in self.connections.items():
            try:
                # SKELETON: Close the connection
                # await connection.close()
                logger.info(f"Disconnected from MCP server: {name}")
            except Exception as e:
                logger.error(f"Error disconnecting from {name}: {e}")
        
        self.connections.clear()
        self._connected = False
    
    async def list_tools(self, server: Optional[str] = None) -> list[MCPToolDefinition]:
        """
        List available tools from connected MCP servers.
        
        Args:
            server: Optional server name to filter tools
            
        Returns:
            List of tool definitions
        """
        if server:
            return [t for t in self.tools.values() if t.server_name == server]
        return list(self.tools.values())
    
    async def call_tool(
        self,
        server: str,
        tool: str,
        arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Call a tool on an MCP server.
        
        Args:
            server: Name of the MCP server
            tool: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool execution result
            
        Example:
            result = await client.call_tool(
                server="slack",
                tool="search_messages",
                arguments={"query": "incident", "limit": 10}
            )
        """
        if server not in self.connections:
            raise ValueError(f"Not connected to server: {server}")
        
        # SKELETON: Replace with actual MCP tool call
        # In production with the MCP SDK:
        #
        # result = await self.connections[server].call_tool(tool, arguments)
        # return result.content
        
        logger.info(f"Calling {server}.{tool} with args: {arguments}")
        
        # Placeholder response
        return {
            "status": "skeleton",
            "message": f"Replace with actual MCP call to {server}.{tool}",
            "arguments_received": arguments
        }


# =============================================================================
# MCP Tool Wrapper (Skeleton)
# =============================================================================

class MCPToolWrapper(BaseTool):
    """
    Wrapper that converts an MCP tool into a BaseTool.
    
    This allows MCP tools to be used seamlessly alongside native tools
    in the triage agent's tool registry.
    
    Example:
        # Wrap an MCP tool
        slack_search = MCPToolWrapper(
            mcp_client=client,
            server_name="slack",
            tool_name="search_messages",
            description="Search Slack messages",
            input_model=SlackSearchInput,
            output_model=SlackSearchOutput
        )
        
        # Register with the agent
        agent.tool_registry.register(slack_search)
    """
    
    def __init__(
        self,
        mcp_client: MCPClient,
        server_name: str,
        tool_name: str,
        description: str,
        input_model: Type[BaseModel],
        output_model: Type[BaseModel]
    ):
        """
        Initialize the MCP tool wrapper.
        
        Args:
            mcp_client: Connected MCP client
            server_name: Name of the MCP server
            tool_name: Name of the tool on the server
            description: Tool description for the LLM
            input_model: Pydantic model for inputs
            output_model: Pydantic model for outputs
        """
        self.mcp_client = mcp_client
        self.server_name = server_name
        self.tool_name = tool_name
        self._name = f"{server_name}_{tool_name}"
        self._description = description
        self.input_model = input_model
        self.output_model = output_model
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def description(self) -> str:
        return self._description
    
    def _execute(self, input_data: BaseModel) -> BaseModel:
        """
        Execute the MCP tool synchronously.
        
        Note: MCP calls are async, so we run them in an event loop.
        In a fully async application, you would use _execute_async instead.
        """
        return asyncio.run(self._execute_async(input_data))
    
    async def _execute_async(self, input_data: BaseModel) -> BaseModel:
        """
        Execute the MCP tool asynchronously.
        
        Args:
            input_data: Validated input data
            
        Returns:
            Validated output data
        """
        # Convert Pydantic model to dict for MCP call
        arguments = input_data.model_dump()
        
        # Call the MCP tool
        result = await self.mcp_client.call_tool(
            server=self.server_name,
            tool=self.tool_name,
            arguments=arguments
        )
        
        # Convert result back to Pydantic model
        return self.output_model(**result)


# =============================================================================
# Example: Creating MCP Tools for the Triage Agent
# =============================================================================

async def create_mcp_tools(config_path: str) -> list[BaseTool]:
    """
    Create MCP-backed tools for the triage agent.
    
    This example shows how you would replace the mock tools with
    real MCP server connections.
    
    Args:
        config_path: Path to MCP configuration file
        
    Returns:
        List of MCP-backed tools
        
    Example mcp_config.json:
    {
        "mcpServers": {
            "slack": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-slack"],
                "env": {
                    "SLACK_BOT_TOKEN": "xoxb-your-token",
                    "SLACK_TEAM_ID": "T0123456789"
                }
            },
            "linear": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-linear"],
                "env": {
                    "LINEAR_API_KEY": "lin_api_xxxx"
                }
            }
        }
    }
    """
    from src.triage_agent.tools.slack import SlackSearchInput, SlackSearchOutput
    from src.triage_agent.tools.jira import JiraSearchInput, JiraSearchOutput
    
    # Connect to MCP servers
    client = MCPClient(config_path)
    await client.connect()
    
    tools = []
    
    # Wrap Slack MCP tools
    if "slack" in client.connections:
        tools.append(MCPToolWrapper(
            mcp_client=client,
            server_name="slack",
            tool_name="search_messages",
            description="Search Slack messages for relevant context",
            input_model=SlackSearchInput,
            output_model=SlackSearchOutput
        ))
    
    # Wrap Jira/Linear MCP tools  
    if "linear" in client.connections:
        tools.append(MCPToolWrapper(
            mcp_client=client,
            server_name="linear",
            tool_name="search_issues",
            description="Search Linear issues for related tickets",
            input_model=JiraSearchInput,  # Reuse similar schema
            output_model=JiraSearchOutput
        ))
    
    return tools


# =============================================================================
# Sample MCP Configuration File
# =============================================================================

SAMPLE_MCP_CONFIG = """
{
    "mcpServers": {
        "slack": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-slack"],
            "env": {
                "SLACK_BOT_TOKEN": "xoxb-your-bot-token",
                "SLACK_TEAM_ID": "T0123456789"
            }
        },
        "github": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-github"],
            "env": {
                "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_xxxxxxxxxxxx"
            }
        },
        "linear": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-linear"],
            "env": {
                "LINEAR_API_KEY": "lin_api_xxxxxxxxxxxx"
            }
        },
        "postgres": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-postgres"],
            "env": {
                "POSTGRES_CONNECTION_STRING": "postgresql://user:pass@localhost/db"
            }
        },
        "custom-server": {
            "transport": "http",
            "url": "http://localhost:8080/mcp",
            "env": {
                "API_KEY": "your-api-key"
            }
        }
    }
}
"""


def create_sample_config(output_path: str = "mcp_config.json") -> None:
    """
    Create a sample MCP configuration file.
    
    Args:
        output_path: Where to write the config file
    """
    with open(output_path, "w") as f:
        f.write(SAMPLE_MCP_CONFIG)
    print(f"Created sample MCP config at: {output_path}")
    print("Remember to replace placeholder values with your actual credentials!")


# =============================================================================
# Usage Example
# =============================================================================

if __name__ == "__main__":
    # Create sample config file
    create_sample_config("mcp_config.example.json")
    
    # Example of how you would use the MCP client
    async def main():
        # This is skeleton code - won't actually connect without real MCP SDK
        print("MCP Client Example (Skeleton)")
        print("=" * 50)
        
        client = MCPClient()
        
        # Manually add a server config for demo
        client.servers["slack"] = MCPServerConfig(
            name="slack",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-slack"],
            env={"SLACK_BOT_TOKEN": "xoxb-xxx"}
        )
        
        # Show what a tool call would look like
        result = await client.call_tool(
            server="slack",
            tool="search_messages",
            arguments={"query": "incident", "limit": 5}
        )
        
        print(f"Tool call result: {result}")
        print()
        print("To use real MCP servers:")
        print("1. pip install mcp")
        print("2. Configure mcp_config.json with your credentials")
        print("3. Replace skeleton code with actual MCP SDK calls")
    
    asyncio.run(main())