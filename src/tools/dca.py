"""
DCA domain tools
Semantic, task-based tools for DCA group control
"""

from mcp.server.fastmcp import FastMCP
from src.services.x32_connection import X32Connection
from src.utils.db_converter import db_to_fader, fader_to_db, format_db
from src.utils.color_converter import get_color_value, get_available_colors
from src.utils.icon_converter import get_icon_value, get_icon_name, get_available_icons
from src.utils.error_helper import X32Error


def register_dca_tools(mcp: FastMCP, connection: X32Connection) -> None:
    """Register all DCA domain tools."""

    @mcp.tool(
        name="dca_set_volume",
        description=(
            "Set the fader level (volume) for a DCA group on the X32/M32 mixer. "
            "Supports both linear values (0.0-1.0) and decibel values (-90 to +10 dB). "
            "Unity gain is 0 dB or 0.75 linear."
        ),
    )
    async def dca_set_volume(dca: int, value: float, unit: str = "linear") -> str:
        """
        Args:
            dca: DCA group number from 1 to 8
            value: Volume value (interpretation depends on unit parameter)
            unit: "linear" (0.0-1.0) or "db" (-90 to +10 dB). Default is "linear".
        """
        if not connection.connected:
            return X32Error.not_connected()
        if dca < 1 or dca > 8:
            return f"Invalid DCA number {dca}. Must be 1–8."
        try:
            if unit == "db":
                if value < -90 or value > 10:
                    return X32Error.invalid_db(value)
                db_value = value
                fader_value = db_to_fader(value)
            else:
                if value < 0 or value > 1:
                    return X32Error.invalid_linear(value)
                fader_value = value
                db_value = fader_to_db(value)
            await connection.set_parameter(f"/dca/{dca}/fader", fader_value)
            return f"Set DCA {dca} to {format_db(db_value)} (linear: {fader_value:.3f})"
        except Exception as e:
            return f"Failed to set DCA volume: {e}"

    @mcp.tool(
        name="dca_get_volume",
        description="Get the current fader level (volume) for a DCA group.",
    )
    async def dca_get_volume(dca: int) -> str:
        """
        Args:
            dca: DCA group number from 1 to 8
        """
        if not connection.connected:
            return X32Error.not_connected()
        if dca < 1 or dca > 8:
            return f"Invalid DCA number {dca}. Must be 1–8."
        try:
            fader_value = await connection.get_parameter(f"/dca/{dca}/fader")
            db_value = fader_to_db(float(fader_value))
            return f"DCA {dca} fader: {format_db(db_value)} (linear: {float(fader_value):.3f})"
        except Exception as e:
            return f"Failed to get DCA volume: {e}"

    @mcp.tool(
        name="dca_mute",
        description=(
            "Mute or unmute a DCA group on the X32/M32 mixer. "
            "This controls the DCA on/off state."
        ),
    )
    async def dca_mute(dca: int, muted: bool) -> str:
        """
        Args:
            dca: DCA group number from 1 to 8
            muted: True to mute the DCA group, False to unmute
        """
        if not connection.connected:
            return X32Error.not_connected()
        if dca < 1 or dca > 8:
            return f"Invalid DCA number {dca}. Must be 1–8."
        try:
            # X32: /dca/N/on = 1 means ON (unmuted), 0 means OFF (muted)
            on_value = 0 if muted else 1
            await connection.set_parameter(f"/dca/{dca}/on", on_value)
            state = "muted" if muted else "unmuted"
            return f"DCA {dca} is now {state}"
        except Exception as e:
            return f"Failed to mute/unmute DCA: {e}"

    @mcp.tool(
        name="dca_get_mute",
        description="Get the current mute state of a DCA group.",
    )
    async def dca_get_mute(dca: int) -> str:
        """
        Args:
            dca: DCA group number from 1 to 8
        """
        if not connection.connected:
            return X32Error.not_connected()
        if dca < 1 or dca > 8:
            return f"Invalid DCA number {dca}. Must be 1–8."
        try:
            on_value = await connection.get_parameter(f"/dca/{dca}/on")
            muted = int(on_value) == 0
            state = "muted" if muted else "unmuted"
            return f"DCA {dca} is {state}"
        except Exception as e:
            return f"Failed to get DCA mute state: {e}"

    @mcp.tool(
        name="dca_set_name",
        description="Set the name/label for a DCA group on the X32/M32 mixer.",
    )
    async def dca_set_name(dca: int, name: str) -> str:
        """
        Args:
            dca: DCA group number from 1 to 8
            name: DCA name/label (max 12 characters)
        """
        if not connection.connected:
            return X32Error.not_connected()
        if dca < 1 or dca > 8:
            return f"Invalid DCA number {dca}. Must be 1–8."
        try:
            await connection.set_parameter(f"/dca/{dca}/config/name", name)
            return f"Set DCA {dca} name to '{name}'"
        except Exception as e:
            return f"Failed to set DCA name: {e}"

    @mcp.tool(
        name="dca_get_name",
        description="Get the current name/label for a DCA group.",
    )
    async def dca_get_name(dca: int) -> str:
        """
        Args:
            dca: DCA group number from 1 to 8
        """
        if not connection.connected:
            return X32Error.not_connected()
        if dca < 1 or dca > 8:
            return f"Invalid DCA number {dca}. Must be 1–8."
        try:
            name = await connection.get_parameter(f"/dca/{dca}/config/name")
            return f"DCA {dca} name: '{name}'"
        except Exception as e:
            return f"Failed to get DCA name: {e}"

    @mcp.tool(
        name="dca_set_icon",
        description=(
            "Set the icon for a DCA group on the X32/M32 mixer. "
            "Icons are used to visually identify DCA groups on the console. "
            "Accepts an icon name (e.g., 'kick_front', 'piano', 'male_vocal') or a number (1-74)."
        ),
    )
    async def dca_set_icon(dca: int, icon: str) -> str:
        """
        Args:
            dca: DCA group number from 1 to 8
            icon: Icon name (e.g., kick_front, piano, male_vocal) or number (1-74).
                  Use 'none' or 1 for no icon.
        """
        if not connection.connected:
            return X32Error.not_connected()
        if dca < 1 or dca > 8:
            return f"Invalid DCA number {dca}. Must be 1–8."
        icon_value = get_icon_value(icon)
        if icon_value is None:
            available = ", ".join(get_available_icons())
            return f"Invalid icon '{icon}'. Must be a number (1-74) or one of: {available}"
        try:
            await connection.set_parameter(f"/dca/{dca}/config/icon", icon_value)
            icon_display = get_icon_name(icon_value)
            return f"Set DCA {dca} icon to {icon_display} (value: {icon_value})"
        except Exception as e:
            return f"Failed to set DCA icon: {e}"

    @mcp.tool(
        name="dca_get_icon",
        description="Get the current icon for a DCA group.",
    )
    async def dca_get_icon(dca: int) -> str:
        """
        Args:
            dca: DCA group number from 1 to 8
        """
        if not connection.connected:
            return X32Error.not_connected()
        if dca < 1 or dca > 8:
            return f"Invalid DCA number {dca}. Must be 1–8."
        try:
            icon_value = await connection.get_parameter(f"/dca/{dca}/config/icon")
            icon_display = get_icon_name(int(icon_value))
            return f"DCA {dca} icon: {icon_display} (value: {int(icon_value)})"
        except Exception as e:
            return f"Failed to get DCA icon: {e}"

    @mcp.tool(
        name="dca_set_color",
        description=(
            "Set the color for a DCA group on the X32/M32 mixer. "
            "Colors are used to visually identify DCA groups on the console."
        ),
    )
    async def dca_set_color(dca: int, color: str) -> str:
        """
        Args:
            dca: DCA group number from 1 to 8
            color: Color name (e.g., red, blue, green, yellow, magenta, cyan, white, off)
                   or number (0-15)
        """
        if not connection.connected:
            return X32Error.not_connected()
        if dca < 1 or dca > 8:
            return f"Invalid DCA number {dca}. Must be 1–8."
        color_value = get_color_value(color)
        if color_value is None:
            available = ", ".join(get_available_colors())
            return f"Invalid color '{color}'. Available colors: {available}"
        try:
            await connection.set_parameter(f"/dca/{dca}/config/color", color_value)
            return f"Set DCA {dca} color to {color} (value: {color_value})"
        except Exception as e:
            return f"Failed to set DCA color: {e}"

    @mcp.tool(
        name="dca_get_color",
        description="Get the current color for a DCA group.",
    )
    async def dca_get_color(dca: int) -> str:
        """
        Args:
            dca: DCA group number from 1 to 8
        """
        if not connection.connected:
            return X32Error.not_connected()
        if dca < 1 or dca > 8:
            return f"Invalid DCA number {dca}. Must be 1–8."
        try:
            color_value = await connection.get_parameter(f"/dca/{dca}/config/color")
            return f"DCA {dca} color value: {int(color_value)}"
        except Exception as e:
            return f"Failed to get DCA color: {e}"