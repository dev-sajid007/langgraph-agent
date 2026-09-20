"""Agent OS Adapter interface for LangGraph agent."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator
from uuid import uuid4


class StreamEventType(str, Enum):
    """Types of streaming events."""

    NODE_START = "node_start"
    NODE_COMPLETE = "node_complete"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    LLM_TOKEN = "llm_token"
    LLM_COMPLETE = "llm_complete"
    ERROR = "error"
    STATUS = "status"


@dataclass
class StreamEvent:
    """Represents a streaming event during agent execution."""

    event_type: StreamEventType
    task_id: str
    thread_id: str
    node: str | None = None
    data: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server."""

    name: str
    transport: str = "stdio"  # "stdio", "http", "sse"
    url: str | None = None  # For http/sse transport
    command: str | None = None  # For stdio transport
    args: list[str] = field(default_factory=list)  # For stdio transport
    headers: dict[str, str] = field(default_factory=dict)  # For http/sse auth


@dataclass
class AgentConfig:
    """Configuration for an agent execution."""

    agent_id: str
    model: str = "gpt-4o-mini"
    temperature: float = 0.0
    tools: list[str] = field(default_factory=list)
    mcp_servers: list[str] = field(default_factory=list)
    mcp_server_configs: list[MCPServerConfig] = field(default_factory=list)


@dataclass
class ExecutionRequest:
    """Request to execute an agent task."""

    task_id: str = field(default_factory=lambda: str(uuid4()))
    thread_id: str = field(default_factory=lambda: str(uuid4()))
    agent_config: AgentConfig | None = None
    messages: list[dict[str, str]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """Result of an agent execution."""

    task_id: str
    thread_id: str
    status: str  # "completed", "failed", "pending"
    messages: list[dict[str, str]] = field(default_factory=list)
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class AgentAdapter(ABC):
    """Abstract base class for agent adapters."""

    @abstractmethod
    async def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Execute an agent task."""
        pass

    @abstractmethod
    async def stream(self, request: ExecutionRequest) -> AsyncIterator[StreamEvent]:
        """Stream execution events."""
        pass

    @abstractmethod
    def get_capabilities(self) -> list[str]:
        """Return adapter capabilities."""
        pass


class LangGraphAdapter(AgentAdapter):
    """LangGraph adapter for Agent OS integration."""

    def __init__(self):
        self._agent = None
        self._mcp_client = None

    async def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Execute an agent task using LangGraph."""
        from .agent import create_agent
        from .mcp_client import MCPClient
        from .tools import get_all_tools, get_native_tools

        mcp_client = MCPClient()

        try:
            # Setup tools
            tools = get_native_tools()

            # Connect to MCP servers if configured
            if request.agent_config:
                # Support both legacy string list and new MCPServerConfig list
                if request.agent_config.mcp_server_configs:
                    mcp_tools = await mcp_client.connect_from_configs(
                        request.agent_config.mcp_server_configs
                    )
                    tools = get_all_tools(mcp_tools)
                elif request.agent_config.mcp_servers:
                    mcp_config = {
                        "mcpServers": {
                            name: {"command": "python", "args": []}
                            for name in request.agent_config.mcp_servers
                        }
                    }
                    mcp_tools = await mcp_client.connect(mcp_config)
                    tools = get_all_tools(mcp_tools)

            # Create agent
            agent = create_agent(tools)

            # Prepare messages
            from langchain_core.messages import HumanMessage

            messages = [
                HumanMessage(content=msg.get("content", ""))
                for msg in request.messages
            ]

            # Execute
            config = {
                "configurable": {
                    "thread_id": request.thread_id,
                }
            }

            result = await agent.ainvoke(
                {"messages": messages},
                config=config,
            )

            # Extract response
            response_content = result["messages"][-1].content if result["messages"] else ""

            return ExecutionResult(
                task_id=request.task_id,
                thread_id=request.thread_id,
                status="completed",
                messages=[{"role": "assistant", "content": response_content}],
                metadata={"model": request.agent_config.model if request.agent_config else "gpt-4o-mini"},
            )

        except Exception as e:
            return ExecutionResult(
                task_id=request.task_id,
                thread_id=request.thread_id,
                status="failed",
                error=str(e),
            )
        finally:
            await mcp_client.disconnect()

    async def stream(self, request: ExecutionRequest) -> AsyncIterator[StreamEvent]:
        """Stream execution events using LangGraph astream."""
        from .agent import create_agent
        from .mcp_client import MCPClient
        from .tools import get_all_tools, get_native_tools

        mcp_client = MCPClient()

        try:
            # Setup tools
            tools = get_native_tools()

            # Connect to MCP servers if configured
            if request.agent_config:
                if request.agent_config.mcp_server_configs:
                    mcp_tools = await mcp_client.connect_from_configs(
                        request.agent_config.mcp_server_configs
                    )
                    tools = get_all_tools(mcp_tools)
                elif request.agent_config.mcp_servers:
                    mcp_config = {
                        "mcpServers": {
                            name: {"command": "python", "args": []}
                            for name in request.agent_config.mcp_servers
                        }
                    }
                    mcp_tools = await mcp_client.connect(mcp_config)
                    tools = get_all_tools(mcp_tools)

            # Create agent
            agent = create_agent(tools)

            # Prepare messages
            from langchain_core.messages import HumanMessage

            messages = [
                HumanMessage(content=msg.get("content", ""))
                for msg in request.messages
            ]

            # Emit status event
            yield StreamEvent(
                event_type=StreamEventType.STATUS,
                task_id=request.task_id,
                thread_id=request.thread_id,
                data="started",
            )

            # Stream execution
            config = {
                "configurable": {
                    "thread_id": request.thread_id,
                }
            }

            async for event in agent.astream(
                {"messages": messages},
                config=config,
                stream_mode="updates",
            ):
                # Process each node update
                for node_name, node_update in event.items():
                    if node_name == "call_model":
                        # LLM node completed
                        if "messages" in node_update:
                            for msg in node_update["messages"]:
                                yield StreamEvent(
                                    event_type=StreamEventType.LLM_COMPLETE,
                                    task_id=request.task_id,
                                    thread_id=request.thread_id,
                                    node=node_name,
                                    data={"content": msg.content},
                                )
                    elif node_name == "tools":
                        # Tool node completed
                        if "messages" in node_update:
                            for msg in node_update["messages"]:
                                yield StreamEvent(
                                    event_type=StreamEventType.TOOL_RESULT,
                                    task_id=request.task_id,
                                    thread_id=request.thread_id,
                                    node=node_name,
                                    data={
                                        "tool_call_id": getattr(msg, "tool_call_id", None),
                                        "content": msg.content,
                                    },
                                )

            # Emit completion event
            yield StreamEvent(
                event_type=StreamEventType.STATUS,
                task_id=request.task_id,
                thread_id=request.thread_id,
                data="completed",
            )

        except Exception as e:
            yield StreamEvent(
                event_type=StreamEventType.ERROR,
                task_id=request.task_id,
                thread_id=request.thread_id,
                data={"error": str(e)},
            )
        finally:
            await mcp_client.disconnect()

    def get_capabilities(self) -> list[str]:
        """Return adapter capabilities."""
        return [
            "tool_calling",
            "mcp_tools",
            "thread_memory",
            "postgresql_checkpointing",
            "streaming",
        ]
