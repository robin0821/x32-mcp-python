"""
AUX bus domain tools for the X32/M32 mixer.

X32 AUX output addresses (auxin = aux return inputs, auxrtn = aux output buses):
  /auxin/NN/mix/fader    - AUX input fader (float 0.0-1.0)
  /auxin/NN/mix/on       - AUX input on/off (int 1=on, 0=mute)
  /auxin/NN/mix/pan      - AUX input pan (float 0.0-1.0)
  /auxin/NN/config/name  - AUX input name (string)

  /ch/NN/mix/NN/level    - channel send to aux level (bus indices 17-22 for Aux 1-6 on X32)

Note: On the X32/M32, AUX outputs (1-6) map to mix buses 17-22 in the OSC address space.
The auxin/ namespace refers to the 8 aux input returns (line inputs on the rear panel).
"""

from mcp.server.fastmcp import FastMCP
from src.services.x32_connection import X32Connection
from src.utils.db_converter import db_to_fader, fader_to_db, format_db
from src.utils.pan_converter import parse_pan, format_pan
from src.utils.error_helper import X32Error


def register_aux_tools(mcp: FastMCP, connection: X32Connection) -> None:
    """Register all AUX domain tools."""

    @mcp.tool(
        name="aux_set_volume",
        description=(
            "Set the fader level for an AUX input return on the X32/M32 mixer. "
            "AUX inputs are the rear-panel line inputs (aux returns 1-8). "
            "Supports linear (0.0-1.0) or dB values (-90 to +10 dB)."
        ),
    )
    async def aux_set_volume(aux: int, value: float, unit: str = "linear") -> str:
        """
        Args:
            aux: AUX input return number from 1 to 8
            value: Volume value
            unit: "linear" (0.0-1.0) or "db" (-90 to +10 dB). Default is "linear".
        """
        if not connection.connected:
            return X32Error.not_connected()
        if aux < 1 or aux > 8:
            return f"Invalid AUX number {aux}. Must be 1–8."
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
            aux_num = str(aux).zfill(2)
            await connection.set_parameter(f"/auxin/{aux_num}/mix/fader", fader_value)
            return f"AUX {aux} fader set to {format_db(db_value)} (linear: {fader_value:.3f})"
        except Exception as e:
            return f"Failed to set AUX volume: {e}"

    @mcp.tool(
        name="aux_get_volume",
        description="Get the current fader level for an AUX input return on the X32/M32.",
    )
    async def aux_get_volume(aux: int) -> str:
        """
        Args:
            aux: AUX input return number from 1 to 8
        """
        if not connection.connected:
            return X32Error.not_connected()
        if aux < 1 or aux > 8:
            return f"Invalid AUX number {aux}. Must be 1–8."
        try:
            aux_num = str(aux).zfill(2)
            fader = float(await connection.get_parameter(f"/auxin/{aux_num}/mix/fader"))
            db_value = fader_to_db(fader)
            return f"AUX {aux} fader: {format_db(db_value)} (linear: {fader:.3f})"
        except Exception as e:
            return f"Failed to get AUX volume: {e}"

    @mcp.tool(
        name="aux_mute",
        description="Mute or unmute an AUX input return on the X32/M32 mixer.",
    )
    async def aux_mute(aux: int, muted: bool) -> str:
        """
        Args:
            aux: AUX input return number from 1 to 8
            muted: True to mute, False to unmute
        """
        if not connection.connected:
            return X32Error.not_connected()
        if aux < 1 or aux > 8:
            return f"Invalid AUX number {aux}. Must be 1–8."
        try:
            aux_num = str(aux).zfill(2)
            on_value = 0 if muted else 1
            await connection.set_parameter(f"/auxin/{aux_num}/mix/on", on_value)
            state = "muted" if muted else "unmuted"
            return f"AUX {aux} is now {state}"
        except Exception as e:
            return f"Failed to mute/unmute AUX: {e}"

    @mcp.tool(
        name="aux_get_mute",
        description="Get the mute state of an AUX input return on the X32/M32 mixer.",
    )
    async def aux_get_mute(aux: int) -> str:
        """
        Args:
            aux: AUX input return number from 1 to 8
        """
        if not connection.connected:
            return X32Error.not_connected()
        if aux < 1 or aux > 8:
            return f"Invalid AUX number {aux}. Must be 1–8."
        try:
            aux_num = str(aux).zfill(2)
            on_val = await connection.get_parameter(f"/auxin/{aux_num}/mix/on")
            muted = int(on_val) == 0
            state = "muted" if muted else "unmuted"
            return f"AUX {aux} is {state}"
        except Exception as e:
            return f"Failed to get AUX mute state: {e}"

    @mcp.tool(
        name="aux_set_pan",
        description=(
            "Set the stereo pan for an AUX input return on the X32/M32 mixer. "
            "Accepts linear (0.0-1.0), percentage (-100 to +100), or LR notation (L50, C, R100)."
        ),
    )
    async def aux_set_pan(aux: int, pan: str) -> str:
        """
        Args:
            aux: AUX input return number from 1 to 8
            pan: Pan position as linear (0.0-1.0), percentage (-100 to 100), or LR notation
        """
        if not connection.connected:
            return X32Error.not_connected()
        if aux < 1 or aux > 8:
            return f"Invalid AUX number {aux}. Must be 1–8."
        try:
            pan_value = parse_pan(pan)
            if pan_value is None:
                return f"Invalid pan value: {pan}. Use linear (0.0-1.0), percentage (-100 to 100), or LR notation."
            aux_num = str(aux).zfill(2)
            await connection.set_parameter(f"/auxin/{aux_num}/mix/pan", pan_value)
            return f"AUX {aux} pan set to {format_pan(pan_value)}"
        except Exception as e:
            return f"Failed to set AUX pan: {e}"

    @mcp.tool(
        name="aux_set_name",
        description="Set the name/label for an AUX input return on the X32/M32 mixer.",
    )
    async def aux_set_name(aux: int, name: str) -> str:
        """
        Args:
            aux: AUX input return number from 1 to 8
            name: Name/label string (max 12 characters)
        """
        if not connection.connected:
            return X32Error.not_connected()
        if aux < 1 or aux > 8:
            return f"Invalid AUX number {aux}. Must be 1–8."
        try:
            aux_num = str(aux).zfill(2)
            await connection.set_parameter(f"/auxin/{aux_num}/config/name", name)
            return f"AUX {aux} name set to '{name}'"
        except Exception as e:
            return f"Failed to set AUX name: {e}"

    @mcp.tool(
        name="channel_set_send_to_aux",
        description=(
            "Set the send level from an input channel to an AUX output bus on the X32/M32 mixer. "
            "On the X32, AUX outputs 1-6 correspond to mix buses 17-22."
        ),
    )
    async def channel_set_send_to_aux(
        channel: int, aux: int, value: float, unit: str = "linear"
    ) -> str:
        """
        Args:
            channel: Input channel number from 1 to 32
            aux: AUX output bus number from 1 to 6
            value: Send level value
            unit: "linear" (0.0-1.0) or "db" (-90 to +10 dB). Default is "linear".
        """
        if not connection.connected:
            return X32Error.not_connected()
        if channel < 1 or channel > 32:
            return X32Error.invalid_channel(channel)
        if aux < 1 or aux > 6:
            return f"Invalid AUX output number {aux}. Must be 1–6."
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
            # AUX 1-6 map to mix buses 17-22 on X32
            bus_idx = str(aux + 16).zfill(2)
            await connection.set_parameter(f"/ch/{ch}/mix/{bus_idx}/level", fader_value)
            return f"Channel {channel} send to AUX {aux}: {format_db(db_value)} (linear: {fader_value:.3f})"
        except Exception as e:
            return f"Failed to set channel send to AUX: {e}"

    @mcp.tool(
        name="channel_get_send_to_aux",
        description=(
            "Get the send level from an input channel to an AUX output bus on the X32/M32 mixer."
        ),
    )
    async def channel_get_send_to_aux(channel: int, aux: int) -> str:
        """
        Args:
            channel: Input channel number from 1 to 32
            aux: AUX output bus number from 1 to 6
        """
        if not connection.connected:
            return X32Error.not_connected()
        if channel < 1 or channel > 32:
            return X32Error.invalid_channel(channel)
        if aux < 1 or aux > 6:
            return f"Invalid AUX output number {aux}. Must be 1–6."
        try:
            ch = str(channel).zfill(2)
            bus_idx = str(aux + 16).zfill(2)
            fader = float(await connection.get_parameter(f"/ch/{ch}/mix/{bus_idx}/level"))
            db_value = fader_to_db(fader)
            return f"Channel {channel} send to AUX {aux}: {format_db(db_value)} (linear: {fader:.3f})"
        except Exception as e:
            return f"Failed to get channel send to AUX: {e}"