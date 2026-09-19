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
* In-memory checkpointing
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
└── src/
    └── langgraph_agent/
        ├── __init__.py
        ├── agent.py
        ├── state.py
        ├── tools.py
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

## Technology Stack

| Technology              | Purpose                              |
| ----------------------- | ------------------------------------ |
| Python 3.14             | Runtime                              |
| uv                      | Python project/dependency management |
| LangGraph               | Agent orchestration                  |
| LangChain               | LLM/tool abstractions                |
| LangChain OpenAI        | OpenAI integration                   |
| python-dotenv           | Environment configuration            |
| In-memory checkpointing | Thread state persistence             |

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

The current implementation uses an in-memory checkpointer.

```text
LangGraph
    │
    ▼
InMemorySaver
    │
    ▼
Process Memory
```

This means checkpoint state is lost when the application process terminates.

Persistent database-backed checkpointing is planned for a future milestone.

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
* [x] In-memory checkpointing
* [ ] PostgreSQL checkpointing
* [ ] Persistent threads

### Phase 4 — MCP

* [ ] MCP client
* [ ] MCP tool discovery
* [ ] MCP tool registry
* [ ] External MCP servers
* [ ] Tool authentication/configuration

### Phase 5 — Agent OS Integration

```text
Agent OS
    │
    ▼
Agent Orchestrator
    │
    ▼
LangGraph Adapter
    │
    ▼
Python LangGraph Agent
    │
    ├── LLM
    ├── Native Tools
    └── MCP Tools
```

Planned adapter responsibilities:

* Receive an execution request from Agent OS
* Create/resume a LangGraph thread
* Load agent configuration
* Load available tools
* Execute the LangGraph agent
* Stream execution events
* Return the final result
* Report execution errors/status

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
