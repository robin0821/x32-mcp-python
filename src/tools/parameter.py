"""
Parameter tools
Low-level OSC parameter get/set tools for direct mixer control
"""

from mcp.server.fastmcp import FastMCP
from src.services.x32_connection import X32Connection
from src.utils.error_helper import X32Error


def register_parameter_tools(mcp: FastMCP, connection: X32Connection) -> None:
    """Register low-level parameter tools."""

    @mcp.tool(
        name="parameter_get",
        description=(
            "Get the value of any OSC parameter from the X32/M32 mixer using its full OSC address. "
            "This is a low-level tool for direct parameter access. "
            "Example addresses: /ch/01/mix/fader, /bus/01/mix/on, /main/st/mix/fader"
        ),
    )
    async def parameter_get(address: str) -> str:
        """
        Args:
            address: Full OSC address of the parameter (e.g., /ch/01/mix/fader)
        """
        if not connection.connected:
            return X32Error.not_connected()
        try:
            value = await connection.get_parameter(address)
            return f"{address} = {value}"
        except Exception as e:
            return f"Failed to get parameter {address}: {e}"

    @mcp.tool(
        name="parameter_set_float",
        description=(
            "Set a float parameter value on the X32/M32 mixer using its full OSC address. "
            "Use this for fader levels, gain, pan and other continuous values."
        ),
    )
    async def parameter_set_float(address: str, value: float) -> str:
        """
        Args:
            address: Full OSC address of the parameter (e.g., /ch/01/mix/fader)
            value: Float value to set
        """
        if not connection.connected:
            return X32Error.not_connected()
        try:
            await connection.set_parameter(address, float(value))
            return f"Set {address} = {value}"
        except Exception as e:
            return f"Failed to set parameter {address}: {e}"

    @mcp.tool(
        name="parameter_set_int",
        description=(
            "Set an integer parameter value on the X32/M32 mixer using its full OSC address. "
            "Use this for on/off states, color indices, and other integer values."
        ),
    )
    async def parameter_set_int(address: str, value: int) -> str:
        """
        Args:
            address: Full OSC address of the parameter (e.g., /ch/01/mix/on)
            value: Integer value to set
        """
        if not connection.connected:
            return X32Error.not_connected()
        try:
            await connection.set_parameter(address, int(value))
            return f"Set {address} = {value}"
        except Exception as e:
            return f"Failed to set parameter {address}: {e}"

    @mcp.tool(
        name="parameter_set_string",
        description=(
            "Set a string parameter value on the X32/M32 mixer using its full OSC address. "
            "Use this for channel names, labels, and other string values."
        ),
    )
    async def parameter_set_string(address: str, value: str) -> str:
        """
        Args:
            address: Full OSC address of the parameter (e.g., /ch/01/config/name)
            value: String value to set
        """
        if not connection.connected:
            return X32Error.not_connected()
        try:
            await connection.set_parameter(address, str(value))
            return f"Set {address} = '{value}'"
        except Exception as e:
            return f"Failed to set parameter {address}: {e}"