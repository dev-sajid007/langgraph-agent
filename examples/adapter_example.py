"""Example script demonstrating Agent OS adapter usage."""

import asyncio

from langgraph_agent import (
    AgentConfig,
    ExecutionRequest,
    LangGraphAdapter,
    StreamEventType,
)


async def main():
    """Run example agent execution."""
    adapter = LangGraphAdapter()

    # Create execution request
    request = ExecutionRequest(
        agent_config=AgentConfig(
            agent_id="example-agent",
            model="gpt-4o-mini",
            temperature=0.0,
        ),
        messages=[
            {"role": "user", "content": "What is 15 * 7?"},
        ],
    )

    print(f"Executing task: {request.task_id}")
    print(f"Thread ID: {request.thread_id}")
    print("\n--- Streaming Events ---")

    # Stream execution events
    async for event in adapter.stream(request):
        if event.event_type == StreamEventType.STATUS:
            print(f"[STATUS] {event.data}")
        elif event.event_type == StreamEventType.LLM_COMPLETE:
            print(f"[LLM] {event.data['content']}")
        elif event.event_type == StreamEventType.TOOL_RESULT:
            print(f"[TOOL] {event.data['content']}")
        elif event.event_type == StreamEventType.ERROR:
            print(f"[ERROR] {event.data['error']}")

    # Check capabilities
    print(f"\nCapabilities: {adapter.get_capabilities()}")


if __name__ == "__main__":
    asyncio.run(main())
