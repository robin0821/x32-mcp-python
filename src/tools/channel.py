"""
Channel domain tools
Semantic, task-based tools for channel control
"""

from mcp.server.fastmcp import FastMCP
from src.services.x32_connection import X32Connection
from src.utils.db_converter import db_to_fader, fader_to_db, format_db
from src.utils.color_converter import get_color_value, get_available_colors
from src.utils.pan_converter import parse_pan, format_pan
from src.utils.error_helper import X32Error


def register_channel_tools(mcp: FastMCP, connection: X32Connection) -> None:
    """Register all channel domain tools."""

    @mcp.tool(
        name="channel_set_volume",
        description=(
            "Set the fader level (volume) for a specific input channel on the X32/M32 mixer. "
            "Supports both linear values (0.0-1.0) and decibel values (-90 to +10 dB). "
            "Unity gain is 0 dB or 0.75 linear."
        ),
    )
    async def channel_set_volume(channel: int, value: float, unit: str = "linear") -> str:
        """
        Args:
            channel: Input channel number from 1 to 32
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
            await connection.set_channel_parameter(channel, "mix/fader", fader_value)
            return f"Set channel {channel} to {format_db(db_value)} (linear: {fader_value:.3f})"
        except Exception as e:
            return f"Failed to set channel volume: {e}"

    @mcp.tool(
        name="channel_set_gain",
        description=(
            "Set the preamp gain for a specific input channel on the X32/M32 mixer. "
            "This controls the input gain stage before the channel processing."
        ),
    )
    async def channel_set_gain(channel: int, gain: float) -> str:
        """
        Args:
            channel: Input channel number from 1 to 32
            gain: Preamp gain level from 0.0 to 1.0
        """
        if not connection.connected:
            return X32Error.not_connected()
        if gain < 0 or gain > 1:
            return X32Error.invalid_linear(gain)
        try:
            await connection.set_channel_parameter(channel, "head/gain", gain)
            return f"Set channel {channel} preamp gain to {gain}"
        except Exception as e:
            return f"Failed to set channel gain: {e}"

    @mcp.tool(
        name="channel_mute",
        description=(
            "Mute or unmute a specific input channel on the X32/M32 mixer. "
            "This controls the channel on/off state."
        ),
    )
    async def channel_mute(channel: int, muted: bool) -> str:
        """
        Args:
            channel: Input channel number from 1 to 32
            muted: True to mute the channel, False to unmute
        """
        if not connection.connected:
            return X32Error.not_connected()
        try:
            # X32: mix/on = 1 means ON (unmuted), 0 means OFF (muted)
            on_value = 0 if muted else 1
            await connection.set_channel_parameter(channel, "mix/on", on_value)
            state = "muted" if muted else "unmuted"
            return f"Channel {channel} is now {state}"
        except Exception as e:
            return f"Failed to mute/unmute channel: {e}"

    @mcp.tool(
        name="channel_set_pan",
        description=(
            "Set the stereo pan position for a specific input channel on the X32/M32 mixer. "
            "Accepts various formats: linear (0.0-1.0), percentage (-100 to +100), "
            "or LR notation (L50, C, R100)."
        ),
    )
    async def channel_set_pan(channel: int, pan: str) -> str:
        """
        Args:
            channel: Input channel number from 1 to 32
            pan: Pan position as linear (0.0-1.0), percentage (-100 to 100), or LR notation (L50, C, R100)
        """
        if not connection.connected:
            return X32Error.not_connected()
        try:
            pan_value = parse_pan(pan)
            if pan_value is None:
                return f"Invalid pan value: {pan}. Use linear (0.0-1.0), percentage (-100 to 100), or LR notation (L50, C, R100)."
            await connection.set_channel_parameter(channel, "mix/pan", pan_value)
            return f"Set channel {channel} pan to {format_pan(pan_value)}"
        except Exception as e:
            return f"Failed to set channel pan: {e}"

    @mcp.tool(
        name="channel_get_volume",
        description="Get the current fader level (volume) for a specific input channel.",
    )
    async def channel_get_volume(channel: int) -> str:
        """
        Args:
            channel: Input channel number from 1 to 32
        """
        if not connection.connected:
            return X32Error.not_connected()
        try:
            fader_value = await connection.get_channel_parameter(channel, "mix/fader")
            db_value = fader_to_db(float(fader_value))
            return f"Channel {channel} fader: {format_db(db_value)} (linear: {float(fader_value):.3f})"
        except Exception as e:
            return f"Failed to get channel volume: {e}"

    @mcp.tool(
        name="channel_get_mute",
        description="Get the current mute state of a specific input channel.",
    )
    async def channel_get_mute(channel: int) -> str:
        """
        Args:
            channel: Input channel number from 1 to 32
        """
        if not connection.connected:
            return X32Error.not_connected()
        try:
            on_value = await connection.get_channel_parameter(channel, "mix/on")
            muted = int(on_value) == 0
            state = "muted" if muted else "unmuted"
            return f"Channel {channel} is {state}"
        except Exception as e:
            return f"Failed to get channel mute state: {e}"

    @mcp.tool(
        name="channel_set_name",
        description="Set the name/label for a specific input channel on the X32/M32 mixer.",
    )
    async def channel_set_name(channel: int, name: str) -> str:
        """
        Args:
            channel: Input channel number from 1 to 32
            name: Channel name/label (max 12 characters)
        """
        if not connection.connected:
            return X32Error.not_connected()
        try:
            await connection.set_channel_parameter(channel, "config/name", name)
            return f"Set channel {channel} name to '{name}'"
        except Exception as e:
            return f"Failed to set channel name: {e}"

    @mcp.tool(
        name="channel_set_color",
        description=(
            "Set the color for a specific input channel strip on the X32/M32 mixer. "
            "Colors are used to visually identify channels on the console."
        ),
    )
    async def channel_set_color(channel: int, color: str) -> str:
        """
        Args:
            channel: Input channel number from 1 to 32
            color: Color name (e.g., red, blue, green, yellow, magenta, cyan, white, off) or number (0-15)
        """
        if not connection.connected:
            return X32Error.not_connected()
        color_value = get_color_value(color)
        if color_value is None:
            available = ", ".join(get_available_colors())
            return f"Invalid color '{color}'. Available colors: {available}"
        try:
            await connection.set_channel_parameter(channel, "config/color", color_value)
            return f"Set channel {channel} color to {color} (value: {color_value})"
        except Exception as e:
            return f"Failed to set channel color: {e}"

    @mcp.tool(
        name="channel_set_send_to_bus",
        description=(
            "Set the send level from an input channel to a mix bus on the X32/M32 mixer. "
            "This controls how much of the channel signal is sent to a particular bus."
        ),
    )
    async def channel_set_send_to_bus(
        channel: int, bus: int, value: float, unit: str = "linear"
    ) -> str:
        """
        Args:
            channel: Input channel number from 1 to 32
            bus: Mix bus number from 1 to 16
            value: Send level value
            unit: "linear" (0.0-1.0) or "db" (-90 to +10 dB). Default is "linear".
        """
        if not connection.connected:
            return X32Error.not_connected()
        if bus < 1 or bus > 16:
            return X32Error.invalid_bus(bus)
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
            ch = str(channel).zfill(2)
            bus_num = str(bus).zfill(2)
            await connection.set_parameter(f"/ch/{ch}/mix/{bus_num}/level", fader_value)
            return f"Set channel {channel} send to bus {bus}: {format_db(db_value)} (linear: {fader_value:.3f})"
        except Exception as e:
            return f"Failed to set channel send to bus: {e}"

    @mcp.tool(
        name="channel_set_send_to_bus_on",
        description="Enable or disable the send from an input channel to a mix bus.",
    )
    async def channel_set_send_to_bus_on(channel: int, bus: int, enabled: bool) -> str:
        """
        Args:
            channel: Input channel number from 1 to 32
            bus: Mix bus number from 1 to 16
            enabled: True to enable the send, False to disable
        """
        if not connection.connected:
            return X32Error.not_connected()
        if bus < 1 or bus > 16:
            return X32Error.invalid_bus(bus)
        try:
            ch = str(channel).zfill(2)
            bus_num = str(bus).zfill(2)
            on_value = 1 if enabled else 0
            await connection.set_parameter(f"/ch/{ch}/mix/{bus_num}/on", on_value)
            state = "enabled" if enabled else "disabled"
            return f"Channel {channel} send to bus {bus} is {state}"
        except Exception as e:
            return f"Failed to set channel send on/off: {e}"