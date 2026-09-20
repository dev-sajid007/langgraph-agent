"""Example MCP server with HTTP transport."""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("WeatherHTTP")


@mcp.tool()
async def get_weather(location: str) -> str:
    """Get weather for a location."""
    return f"Weather in {location}: Sunny, 72F"


@mcp.tool()
async def get_forecast(location: str, days: int) -> str:
    """Get weather forecast for multiple days."""
    return f"{days}-day forecast for {location}: Mostly sunny"


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
