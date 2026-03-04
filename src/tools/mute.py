"""
Mute Group domain tools
Semantic, task-based tools for mute group control
"""

from mcp.server.fastmcp import FastMCP
from src.services.x32_connection import X32Connection
from src.utils.error_helper import X32Error


def register_mute_tools(mcp: FastMCP, connection: X32Connection) -> None:
    """Register all mute group domain tools."""

    @mcp.tool(
        name="mute_group_set",
        description=(
            "Activate or deactivate a mute group on the X32/M32 mixer. "
            "When a mute group is ON (active), all channels assigned to that group are muted. "
            "There are 6 mute groups available (1–6)."
        ),
    )
    async def mute_group_set(group: int, active: bool) -> str:
        """
        Args:
            group: Mute group number from 1 to 6
            active: True to activate (mute) the group, False to deactivate (unmute)
        """
        if not connection.connected:
            return X32Error.not_connected()
        if group < 1 or group > 6:
            return f"Invalid mute group {group}. Must be between 1 and 6."
        try:
            value = 1 if active else 0
            await connection.set_parameter(f"/config/mute/{group}", value)
            state = "ON (active)" if active else "OFF (inactive)"
            return f"Mute group {group} is now {state}"
        except Exception as e:
            return f"Failed to set mute group {group}: {e}"

    @mcp.tool(
        name="mute_group_get",
        description=(
            "Get the current state of a mute group on the X32/M32 mixer. "
            "Returns whether the mute group is active (ON) or inactive (OFF). "
            "There are 6 mute groups available (1–6)."
        ),
    )
    async def mute_group_get(group: int) -> str:
        """
        Args:
            group: Mute group number from 1 to 6
        """
        if not connection.connected:
            return X32Error.not_connected()
        if group < 1 or group > 6:
            return f"Invalid mute group {group}. Must be between 1 and 6."
        try:
            raw = await connection.get_parameter(f"/config/mute/{group}")
            active = int(raw) == 1
            state = "ON (active)" if active else "OFF (inactive)"
            return f"Mute group {group} is {state}"
        except Exception as e:
            return f"Failed to get mute group {group} state: {e}"

    @mcp.tool(
        name="mute_group_get_all",
        description=(
            "Get the current state of all 6 mute groups on the X32/M32 mixer. "
            "Returns which mute groups are active (ON) and which are inactive (OFF)."
        ),
    )
    async def mute_group_get_all() -> str:
        """Get the state of all 6 mute groups at once."""
        if not connection.connected:
            return X32Error.not_connected()
        try:
            results = []
            for group in range(1, 7):
                raw = await connection.get_parameter(f"/config/mute/{group}")
                active = int(raw) == 1
                state = "ON" if active else "OFF"
                results.append(f"  Mute Group {group}: {state}")
            return "Mute group states:\n" + "\n".join(results)
        except Exception as e:
            return f"Failed to get mute group states: {e}"