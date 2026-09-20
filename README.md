# LangGraph Agent

A Python-based AI agent built with **LangGraph**, **LangChain**, and **OpenAI**.

This project is being developed as the foundation for a future **LangGraph Adapter** that will integrate with a custom Agent OS.

## Current Status

The agent currently supports:

* Python 3.14
* `uv` project management
* LangGraph state-based execution
* OpenAI chat model
* Tool calling
* Tool registry
* Multiple tools
* Thread-based conversation state
* PostgreSQL checkpointing
* CLI execution

## Architecture

```text
                    LangGraph Agent
                           │
                           ▼
                       AgentState
                           │
                           ▼
                         LLM
                           │
                 ┌─────────┴─────────┐
                 │                   │
            Tool needed          No tool
                 │                   │
                 ▼                   ▼
             ToolNode              END
                 │
                 ▼
                LLM
                 │
                 ▼
                END
```

## Project Structure

```text
langgraph-agent/
├── pyproject.toml
├── README.md
├── uv.lock
├── .env
├── mcp_servers.json
├── examples/
│   ├── math_mcp_server.py
│   ├── weather_http_server.py
│   └── adapter_example.py
└── src/
    └── langgraph_agent/
        ├── __init__.py
        ├── agent.py
        ├── adapter.py
        ├── state.py
        ├── tools.py
        ├── mcp_client.py
        └── main.py
```

### Components

#### `agent.py`

Defines the LangGraph agent and execution flow.

Responsibilities:

* Create the ChatOpenAI model
* Bind tools to the model
* Create the LangGraph `StateGraph`
* Configure tool routing
* Configure the checkpointer
* Compile the graph

#### `state.py`

Defines the state used by LangGraph.

```text
AgentState
└── messages
```

Messages are managed using LangGraph's message reducer.

#### `tools.py`

Contains the agent's available tools.

Current tools:

* `calculator`
* `get_project_info`

Tools are exposed through a central registry:

```python
def get_tools():
    return [
        calculator,
        get_project_info,
    ]
```

This design will later allow additional native and MCP tools to be registered without coupling the agent graph to individual tools.

#### `main.py`

CLI entry point used to run the agent.

Example:

```bash
uv run langgraph-agent
```

#### `mcp_client.py`

Handles MCP server connections and tool discovery.

Responsibilities:

* Load MCP server configuration
* Connect to MCP servers via `MCPAdapter`
* Discover and cache available tools
* Manage connection lifecycle

#### `adapter.py`

Agent OS adapter interface for LangGraph integration.

Provides:

* `AgentAdapter` - Abstract base class for all adapters
* `LangGraphAdapter` - LangGraph-specific implementation
* `AgentConfig` - Agent configuration dataclass
* `ExecutionRequest` - Execution request dataclass
* `ExecutionResult` - Execution result dataclass

## Technology Stack

| Technology              | Purpose                              |
| ----------------------- | ------------------------------------ |
| Python 3.14             | Runtime                              |
| uv                      | Python project/dependency management |
| LangGraph               | Agent orchestration                  |
| LangChain               | LLM/tool abstractions                |
| LangChain OpenAI        | OpenAI integration                   |
| python-dotenv           | Environment configuration            |
| PostgreSQL              | Persistent thread state checkpointing |
| MCP                     | External tool integration            |

## Installation

### Requirements

Make sure the following are installed:

* Python 3.14
* `uv`

Check Python:

```bash
python3 --version
```

Check uv:

```bash
uv --version
```

### Install dependencies

Clone or enter the project:

```bash
cd langgraph-agent
```

Install dependencies:

```bash
uv sync
```

## Environment Configuration

Create a `.env` file:

```env
OPENAI_API_KEY=your_api_key_here
```

Do not commit `.env` to Git.

## Running the Agent

Run the project through the configured CLI entry point:

```bash
uv run langgraph-agent
```

You can also run the module directly:

```bash
uv run python -m langgraph_agent.main
```

## Tool Calling

The agent can decide whether a tool is required.

For example:

```text
User
 │
 │ "What is 125 multiplied by 37?"
 ▼
LLM
 │
 │ tool call
 ▼
calculator
 │
 │ 4625
 ▼
LLM
 │
 ▼
Final response
```

For a normal question that does not require a tool:

```text
User
 │
 ▼
LLM
 │
 ▼
Final response
```

## MCP Integration

The agent supports external tools via Model Context Protocol (MCP).

### Configuration

Create a `mcp_servers.json` file:

```json
{
  "mcpServers": {
    "math": {
      "command": "python",
      "args": ["examples/math_mcp_server.py"],
      "transport": "stdio"
    },
    "weather": {
      "url": "http://localhost:8000/mcp",
      "transport": "http"
    }
  }
}
```

### Transport Types

| Transport | Use Case | Config Fields |
|-----------|----------|---------------|
| `stdio` | Local servers | `command`, `args` |
| `http` | Remote servers (Streamable HTTP) | `url`, `headers` |
| `sse` | Legacy remote servers | `url`, `headers` |

### Authentication

For servers requiring authentication, add headers:

```json
{
  "mcpServers": {
    "secure-api": {
      "url": "https://api.example.com/mcp",
      "transport": "http",
      "headers": {
        "Authorization": "Bearer YOUR_TOKEN"
      }
    }
  }
}
```

### Running with MCP

```bash
uv run langgraph-agent
```

The agent will automatically discover and load tools from configured MCP servers.

## Agent OS Integration

The agent can be integrated with a custom Agent OS via the `LangGraphAdapter`.

### Usage

```python
from langgraph_agent import LangGraphAdapter, ExecutionRequest, AgentConfig

adapter = LangGraphAdapter()

request = ExecutionRequest(
    agent_config=AgentConfig(
        agent_id="my-agent",
        model="gpt-4o-mini",
        mcp_servers=["math"],
    ),
    messages=[{"role": "user", "content": "What is 2 + 2?"}],
)

result = await adapter.execute(request)
print(result.messages)
```

### Streaming

Stream real-time execution events:

```python
from langgraph_agent import LangGraphAdapter, ExecutionRequest, AgentConfig, StreamEventType

adapter = LangGraphAdapter()

request = ExecutionRequest(
    agent_config=AgentConfig(agent_id="my-agent"),
    messages=[{"role": "user", "content": "Calculate 15 * 7"}],
)

async for event in adapter.stream(request):
    if event.event_type == StreamEventType.LLM_COMPLETE:
        print(f"LLM: {event.data['content']}")
    elif event.event_type == StreamEventType.TOOL_RESULT:
        print(f"Tool result: {event.data['content']}")
    elif event.event_type == StreamEventType.ERROR:
        print(f"Error: {event.data['error']}")
```

### Streaming Event Types

| Event Type | Description |
|------------|-------------|
| `STATUS` | Execution started/completed |
| `NODE_START` | Graph node started |
| `NODE_COMPLETE` | Graph node completed |
| `TOOL_CALL` | Tool invocation |
| `TOOL_RESULT` | Tool execution result |
| `LLM_TOKEN` | Token-by-token LLM output |
| `LLM_COMPLETE` | LLM response completed |
| `ERROR` | Execution error |

### Capabilities

The LangGraph adapter supports:

* Tool calling (native + MCP)
* Thread-based conversation memory
* PostgreSQL checkpointing
* Async execution
* Event streaming

## Conversation Threads

The agent uses a `thread_id` to identify a conversation.

Example:

```python
config = {
    "configurable": {
        "thread_id": "demo-thread-1",
    }
}
```

Multiple invocations using the same thread can access the checkpointed conversation state.

Example:

```text
Thread: demo-thread-1

User:
"My name is Sajid."

Agent:
"Nice to meet you, Sajid!"

User:
"What is my name?"

Agent:
"Your name is Sajid."
```

Different thread IDs represent independent conversations:

```text
demo-thread-1
└── Conversation A

demo-thread-2
└── Conversation B
```

## Current Checkpointing

The current implementation uses PostgreSQL checkpointing via `PostgresSaver`.

```text
LangGraph
    │
    ▼
PostgresSaver
    │
    ▼
PostgreSQL Database
```

This provides persistent thread state across application restarts.

## Development Roadmap

### Phase 1 — Core Agent

* [x] Python 3.14 project
* [x] uv setup
* [x] LangGraph setup
* [x] OpenAI integration
* [x] Basic graph
* [x] Agent state

### Phase 2 — Tools

* [x] Tool calling
* [x] ToolNode
* [x] Conditional tool routing
* [x] Tool registry
* [x] Multiple tools

### Phase 3 — Memory

* [x] Thread IDs
* [x] Conversation state
* [x] PostgreSQL checkpointing
* [x] Persistent threads

### Phase 4 — MCP

* [x] MCP client
* [x] MCP tool discovery
* [x] MCP tool registry
* [x] External MCP servers (HTTP/SSE)
* [x] Tool authentication/configuration

### Phase 5 — Agent OS Integration

* [x] Agent adapter interface
* [x] LangGraph adapter implementation
* [x] Event streaming
* [ ] Agent OS orchestrator
* [ ] Error handling/reporting

## Target Architecture

The long-term goal is to keep Agent OS independent from the underlying agent framework.

```text
                         Agent OS
                             │
                     Agent Orchestrator
                             │
                      Agent Adapter
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
         LangGraph        OpenClaw        Custom
          Adapter          Adapter        Adapter
              │
              ▼
       Python LangGraph
           Agent
              │
        ┌─────┴─────┐
        ▼           ▼
     Native         MCP
      Tools         Tools
```

The core Agent OS should know about the abstract concepts:

```text
Agent
Task
Execution
Adapter
Result
```

It should not depend directly on LangGraph implementation details.

### Current Implementation

The `LangGraphAdapter` implements the `AgentAdapter` interface:

```python
class AgentAdapter(ABC):
    @abstractmethod
    async def execute(self, request: ExecutionRequest) -> ExecutionResult:
        pass

    @abstractmethod
    async def stream(self, request: ExecutionRequest):
        pass

    @abstractmethod
    def get_capabilities(self) -> list[str]:
        pass
```

This allows the Agent OS to use any adapter implementation without knowing the underlying framework.

## Git Workflow

Create a commit after completing a meaningful milestone:

```bash
git status
git add .
git commit -m "feat: description of change"
```

Example:

```bash
git commit -m "feat: add thread-based agent memory"
```

## Project Goal

This project is not intended to remain only a standalone chatbot.

The long-term goal is to turn this LangGraph agent into a reusable execution runtime that can be connected to a custom Agent OS through a dedicated adapter.

The planned architecture is:

```text
Custom Agent OS
       │
       ▼
LangGraph Adapter
       │
       ▼
LangGraph Agent
       │
   ┌───┴────┐
   ▼        ▼
 Tools      MCP
```

The implementation will be developed incrementally, starting with the standalone LangGraph agent and gradually adding persistence, MCP, observability, and Agent OS integration.
