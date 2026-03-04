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
        name="aux_get_dca",
        description=(
            "Get the DCA group assignments for a specific AUX input return on the X32/M32 mixer. "
            "Returns which of the 8 DCA groups (1-8) the AUX input is assigned to."
        ),
    )
    async def aux_get_dca(aux: int) -> str:
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
            raw = await connection.get_parameter(f"/auxin/{aux_num}/grp/dca")
            bitmask = int(raw)
            assigned = [dca for dca in range(1, 9) if bitmask & (1 << (dca - 1))]
            if assigned:
                dca_list = ", ".join(f"DCA {d}" for d in assigned)
                return f"AUX {aux} is assigned to: {dca_list} (raw value: {bitmask})"
            else:
                return f"AUX {aux} is not assigned to any DCA group (raw value: {bitmask})"
        except Exception as e:
            return f"Failed to get AUX DCA assignments: {e}"

    @mcp.tool(
        name="aux_set_dca",
        description=(
            "Set the DCA group assignments for a specific AUX input return on the X32/M32 mixer. "
            "Accepts a list of DCA groups (1-8) to assign the AUX input to. "
            "Pass an empty list to remove the AUX input from all DCA groups."
        ),
    )
    async def aux_set_dca(aux: int, dcas: list[int]) -> str:
        """
        Args:
            aux: AUX input return number from 1 to 8
            dcas: List of DCA group numbers (1-8). Empty list removes all assignments.
        """
        if not connection.connected:
            return X32Error.not_connected()
        if aux < 1 or aux > 8:
            return f"Invalid AUX number {aux}. Must be 1–8."
        invalid = [d for d in dcas if d < 1 or d > 8]
        if invalid:
            return f"Invalid DCA group(s): {invalid}. Each must be between 1 and 8."
        try:
            bitmask = 0
            for dca in dcas:
                bitmask |= 1 << (dca - 1)
            aux_num = str(aux).zfill(2)
            await connection.set_parameter(f"/auxin/{aux_num}/grp/dca", bitmask)
            if dcas:
                dca_list = ", ".join(f"DCA {d}" for d in sorted(dcas))
                return f"AUX {aux} assigned to: {dca_list} (bitmask: {bitmask})"
            else:
                return f"AUX {aux} removed from all DCA groups (bitmask: 0)"
        except Exception as e:
            return f"Failed to set AUX DCA assignments: {e}"

    @mcp.tool(
        name="aux_get_mute_group",
        description=(
            "Get the mute group assignments for a specific AUX input return on the X32/M32 mixer. "
            "Returns which of the 6 mute groups (1-6) the AUX input is assigned to."
        ),
    )
    async def aux_get_mute_group(aux: int) -> str:
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
            raw = await connection.get_parameter(f"/auxin/{aux_num}/grp/mute")
            bitmask = int(raw)
            assigned = [grp for grp in range(1, 7) if bitmask & (1 << (grp - 1))]
            if assigned:
                grp_list = ", ".join(f"Mute Group {g}" for g in assigned)
                return f"AUX {aux} is assigned to: {grp_list} (raw value: {bitmask})"
            else:
                return f"AUX {aux} is not assigned to any mute group (raw value: {bitmask})"
        except Exception as e:
            return f"Failed to get AUX mute group assignments: {e}"

    @mcp.tool(
        name="aux_set_mute_group",
        description=(
            "Set the mute group assignments for a specific AUX input return on the X32/M32 mixer. "
            "Accepts a list of mute groups (1-6) to assign the AUX input to. "
            "Pass an empty list to remove the AUX input from all mute groups."
        ),
    )
    async def aux_set_mute_group(aux: int, groups: list[int]) -> str:
        """
        Args:
            aux: AUX input return number from 1 to 8
            groups: List of mute group numbers (1-6). Empty list removes all assignments.
        """
        if not connection.connected:
            return X32Error.not_connected()
        if aux < 1 or aux > 8:
            return f"Invalid AUX number {aux}. Must be 1–8."
        invalid = [g for g in groups if g < 1 or g > 6]
        if invalid:
            return f"Invalid mute group(s): {invalid}. Each must be between 1 and 6."
        try:
            bitmask = 0
            for grp in groups:
                bitmask |= 1 << (grp - 1)
            aux_num = str(aux).zfill(2)
            await connection.set_parameter(f"/auxin/{aux_num}/grp/mute", bitmask)
            if groups:
                grp_list = ", ".join(f"Mute Group {g}" for g in sorted(groups))
                return f"AUX {aux} assigned to: {grp_list} (bitmask: {bitmask})"
            else:
                return f"AUX {aux} removed from all mute groups (bitmask: 0)"
        except Exception as e:
            return f"Failed to set AUX mute group assignments: {e}"

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