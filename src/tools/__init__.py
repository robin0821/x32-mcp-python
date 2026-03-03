"""Tools for X32/M32 MCP server."""

from mcp.server.fastmcp import FastMCP
from src.services.x32_connection import X32Connection
from src.tools.channel import register_channel_tools
from src.tools.bus import register_bus_tools
from src.tools.fx import register_fx_tools
from src.tools.main import register_main_tools
from src.tools.parameter import register_parameter_tools
from src.tools.connection import register_connection_tools


def register_all_tools(mcp: FastMCP, connection: X32Connection) -> None:
    """Register all available tools with the MCP server."""
    register_connection_tools(mcp, connection)
    register_channel_tools(mcp, connection)
    register_bus_tools(mcp, connection)
    register_fx_tools(mcp, connection)
    register_main_tools(mcp, connection)
    register_parameter_tools(mcp, connection)