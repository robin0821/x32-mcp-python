"""Tools for X32/M32 MCP server."""

from mcp.server.fastmcp import FastMCP
from src.services.x32_connection import X32Connection
from src.tools.channel import register_channel_tools
from src.tools.bus import register_bus_tools
from src.tools.fx import register_fx_tools
from src.tools.main import register_main_tools
from src.tools.parameter import register_parameter_tools
from src.tools.connection import register_connection_tools
from src.tools.automix import register_automix_tools
from src.tools.usb import register_usb_tools
from src.tools.eq import register_eq_tools
from src.tools.dynamics import register_dynamics_tools
from src.tools.scene import register_scene_tools
from src.tools.aux import register_aux_tools
from src.tools.matrix import register_matrix_tools
from src.tools.meters import register_meters_tools
from src.tools.dca import register_dca_tools
from src.tools.mute import register_mute_tools


def register_all_tools(mcp: FastMCP, connection: X32Connection) -> None:
    """Register all available tools with the MCP server."""
    register_connection_tools(mcp, connection)
    register_channel_tools(mcp, connection)
    register_bus_tools(mcp, connection)
    register_fx_tools(mcp, connection)
    register_main_tools(mcp, connection)
    register_parameter_tools(mcp, connection)
    register_automix_tools(mcp, connection)
    register_usb_tools(mcp, connection)
    register_eq_tools(mcp, connection)
    register_dynamics_tools(mcp, connection)
    register_scene_tools(mcp, connection)
    register_aux_tools(mcp, connection)
    register_matrix_tools(mcp, connection)
    register_meters_tools(mcp, connection)
    register_dca_tools(mcp, connection)
    register_mute_tools(mcp, connection)
