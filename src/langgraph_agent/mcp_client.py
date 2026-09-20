import os
from typing import Any

from langchain.mcp import MCPAdapter


class MCPClient:
    """Manages MCP server connections and tool discovery."""

    def __init__(self):
        self._adapter: MCPAdapter | None = None
        self._tools: list[Any] = []

    async def connect(self, server_config: dict[str, Any]) -> list[Any]:
        """Connect to MCP servers and return available tools."""
        self._adapter = MCPAdapter(server_config)
        await self._adapter.__aenter__()
        self._tools = await self._adapter.list_tools()
        return self._tools

    async def connect_from_configs(self, configs: list[Any]) -> list[Any]:
        """Connect to MCP servers from MCPServerConfig objects."""
        mcp_servers = {}

        for config in configs:
            server_entry: dict[str, Any] = {}

            if config.transport == "stdio":
                server_entry["command"] = config.command
                if config.args:
                    server_entry["args"] = config.args
            elif config.transport in ("http", "sse"):
                if not config.url:
                    raise ValueError(f"URL required for {config.transport} transport")
                server_entry["url"] = config.url
                server_entry["transport"] = config.transport
                if config.headers:
                    server_entry["headers"] = config.headers
            else:
                raise ValueError(f"Unknown transport: {config.transport}")

            mcp_servers[config.name] = server_entry

        full_config = {"mcpServers": mcp_servers}
        return await self.connect(full_config)

    async def disconnect(self):
        """Disconnect from MCP servers."""
        if self._adapter:
            await self._adapter.__aexit__(None, None, None)
            self._adapter = None
            self._tools = []

    def get_tools(self) -> list[Any]:
        """Return cached MCP tools."""
        return self._tools

    @staticmethod
    def load_config_from_env() -> dict[str, Any] | None:
        """Load MCP server config from MCP_SERVERS env var (JSON)."""
        import json

        config_str = os.environ.get("MCP_SERVERS")
        if config_str:
            return json.loads(config_str)
        return None


def get_mcp_config_from_file(path: str = "mcp_servers.json") -> dict[str, Any] | None:
    """Load MCP config from a JSON file."""
    import json

    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None
