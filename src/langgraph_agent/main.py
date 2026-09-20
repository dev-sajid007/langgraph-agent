import asyncio

from dotenv import load_dotenv

load_dotenv()

from langchain_core.messages import HumanMessage

from .agent import agent, close, create_agent
from .mcp_client import MCPClient
from .tools import get_all_tools


async def run_with_mcp():
    """Run agent with MCP tools."""
    mcp_client = MCPClient()

    try:
        # Load MCP config from env or file
        mcp_config = MCPClient.load_config_from_env()
        if not mcp_config:
            from .mcp_client import get_mcp_config_from_file
            mcp_config = get_mcp_config_from_file()

        if mcp_config:
            print("Connecting to MCP servers...")
            mcp_tools = await mcp_client.connect(mcp_config)
            print(f"Loaded {len(mcp_tools)} MCP tools")

            # Create agent with native + MCP tools
            all_tools = get_all_tools(mcp_tools)
            mcp_agent = create_agent(all_tools)
        else:
            print("No MCP config found, using native tools only")
            mcp_agent = agent

        config = {
            "configurable": {
                "thread_id": "mcp-thread-1",
            }
        }

        first = await mcp_agent.ainvoke(
            {
                "messages": [
                    HumanMessage(content="My name is Sajid.")
                ]
            },
            config=config,
        )

        print("First:", first["messages"][-1].content)

        second = await mcp_agent.ainvoke(
            {
                "messages": [
                    HumanMessage(content="What is my name?")
                ]
            },
            config=config,
        )

        print("Second:", second["messages"][-1].content)

    finally:
        await mcp_client.disconnect()
        close()


def main():
    """CLI entry point."""
    asyncio.run(run_with_mcp())


if __name__ == "__main__":
    main()