"""
Main/LR bus tools
Semantic, task-based tools for main LR bus control
"""

from mcp.server.fastmcp import FastMCP
from src.services.x32_connection import X32Connection
from src.utils.db_converter import db_to_fader, fader_to_db, format_db
from src.utils.pan_converter import parse_pan, format_pan
from src.utils.error_helper import X32Error


def register_main_tools(mcp: FastMCP, connection: X32Connection) -> None:
    """Register all main LR bus tools."""

    @mcp.tool(
        name="main_set_volume",
        description=(
            "Set the main LR fader level (volume) on the X32/M32 mixer. "
            "Supports both linear values (0.0-1.0) and decibel values (-90 to +10 dB). "
            "Unity gain is 0 dB or 0.75 linear."
        ),
    )
    async def main_set_volume(value: float, unit: str = "linear") -> str:
        """
        Args:
            value: Volume value (interpretation depends on unit parameter)
            unit: "linear" (0.0-1.0) or "db" (-90 to +10 dB). Default is "linear".
        """
        if not connection.connected:
            return X32Error.not_connected()
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
            await connection.set_parameter("/main/st/mix/fader", fader_value)
            return f"Set main LR to {format_db(db_value)} (linear: {fader_value:.3f})"
        except Exception as e:
            return f"Failed to set main volume: {e}"

    @mcp.tool(
        name="main_get_volume",
        description="Get the current main LR fader level (volume) on the X32/M32 mixer.",
    )
    async def main_get_volume() -> str:
        if not connection.connected:
            return X32Error.not_connected()
        try:
            fader_value = await connection.get_parameter("/main/st/mix/fader")
            db_value = fader_to_db(float(fader_value))
            return f"Main LR fader: {format_db(db_value)} (linear: {float(fader_value):.3f})"
        except Exception as e:
            return f"Failed to get main volume: {e}"

    @mcp.tool(
        name="main_mute",
        description="Mute or unmute the main LR output on the X32/M32 mixer.",
    )
    async def main_mute(muted: bool) -> str:
        """
        Args:
            muted: True to mute the main LR, False to unmute
        """
        if not connection.connected:
            return X32Error.not_connected()
        try:
            on_value = 0 if muted else 1
            await connection.set_parameter("/main/st/mix/on", on_value)
            state = "muted" if muted else "unmuted"
            return f"Main LR is now {state}"
        except Exception as e:
            return f"Failed to mute/unmute main LR: {e}"

    @mcp.tool(
        name="main_get_mute",
        description="Get the current mute state of the main LR output on the X32/M32 mixer.",
    )
    async def main_get_mute() -> str:
        if not connection.connected:
            return X32Error.not_connected()
        try:
            on_value = await connection.get_parameter("/main/st/mix/on")
            muted = int(on_value) == 0
            state = "muted" if muted else "unmuted"
            return f"Main LR is {state}"
        except Exception as e:
            return f"Failed to get main mute state: {e}"

    @mcp.tool(
        name="main_set_pan",
        description=(
            "Set the stereo pan position for the main LR output on the X32/M32 mixer. "
            "Accepts linear (0.0-1.0), percentage (-100 to +100), or LR notation (L50, C, R100)."
        ),
    )
    async def main_set_pan(pan: str) -> str:
        """
        Args:
            pan: Pan position as linear (0.0-1.0), percentage (-100 to 100), or LR notation
        """
        if not connection.connected:
            return X32Error.not_connected()
        try:
            pan_value = parse_pan(pan)
            if pan_value is None:
                return f"Invalid pan value: {pan}. Use linear (0.0-1.0), percentage (-100 to 100), or LR notation."
            await connection.set_parameter("/main/st/mix/pan", pan_value)
            return f"Main LR pan set to {format_pan(pan_value)}"
        except Exception as e:
            return f"Failed to set main pan: {e}"

    @mcp.tool(
        name="main_get_pan",
        description="Get the current stereo pan position of the main LR output on the X32/M32 mixer.",
    )
    async def main_get_pan() -> str:
        if not connection.connected:
            return X32Error.not_connected()
        try:
            pan_value = float(await connection.get_parameter("/main/st/mix/pan"))
            return f"Main LR pan: {format_pan(pan_value)}"
        except Exception as e:
            return f"Failed to get main pan: {e}"

    @mcp.tool(
        name="mono_set_volume",
        description=(
            "Set the mono/center fader level on the X32/M32 mixer. "
            "Supports both linear values (0.0-1.0) and decibel values (-90 to +10 dB)."
        ),
    )
    async def mono_set_volume(value: float, unit: str = "linear") -> str:
        """
        Args:
            value: Volume value
            unit: "linear" (0.0-1.0) or "db" (-90 to +10 dB). Default is "linear".
        """
        if not connection.connected:
            return X32Error.not_connected()
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
            await connection.set_parameter("/main/m/mix/fader", fader_value)
            return f"Set mono/center to {format_db(db_value)} (linear: {fader_value:.3f})"
        except Exception as e:
            return f"Failed to set mono volume: {e}"

    @mcp.tool(
        name="mono_get_volume",
        description="Get the current mono/center fader level on the X32/M32 mixer.",
    )
    async def mono_get_volume() -> str:
        if not connection.connected:
            return X32Error.not_connected()
        try:
            fader_value = float(await connection.get_parameter("/main/m/mix/fader"))
            db_value = fader_to_db(fader_value)
            return f"Mono/center fader: {format_db(db_value)} (linear: {fader_value:.3f})"
        except Exception as e:
            return f"Failed to get mono volume: {e}"

    @mcp.tool(
        name="mono_mute",
        description="Mute or unmute the mono/center output on the X32/M32 mixer.",
    )
    async def mono_mute(muted: bool) -> str:
        """
        Args:
            muted: True to mute the mono output, False to unmute
        """
        if not connection.connected:
            return X32Error.not_connected()
        try:
            on_value = 0 if muted else 1
            await connection.set_parameter("/main/m/mix/on", on_value)
            state = "muted" if muted else "unmuted"
            return f"Mono/center is now {state}"
        except Exception as e:
            return f"Failed to mute/unmute mono: {e}"

    @mcp.tool(
        name="mono_get_mute",
        description="Get the current mute state of the mono/center output on the X32/M32 mixer.",
    )
    async def mono_get_mute() -> str:
        if not connection.connected:
            return X32Error.not_connected()
        try:
            on_value = await connection.get_parameter("/main/m/mix/on")
            muted = int(on_value) == 0
            state = "muted" if muted else "unmuted"
            return f"Mono/center is {state}"
        except Exception as e:
            return f"Failed to get mono mute state: {e}"
