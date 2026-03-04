"""
Bus domain tools
Semantic, task-based tools for mix bus control
"""

from mcp.server.fastmcp import FastMCP
from src.services.x32_connection import X32Connection
from src.utils.db_converter import db_to_fader, fader_to_db, format_db
from src.utils.color_converter import get_color_value, get_available_colors
from src.utils.pan_converter import parse_pan, format_pan
from src.utils.error_helper import X32Error


def register_bus_tools(mcp: FastMCP, connection: X32Connection) -> None:
    """Register all bus domain tools."""

    @mcp.tool(
        name="bus_set_volume",
        description=(
            "Set the fader level (volume) for a specific mix bus on the X32/M32 mixer. "
            "Supports both linear values (0.0-1.0) and decibel values (-90 to +10 dB). "
            "Unity gain is 0 dB or 0.75 linear."
        ),
    )
    async def bus_set_volume(bus: int, value: float, unit: str = "linear") -> str:
        """
        Args:
            bus: Mix bus number from 1 to 16
            value: Volume value (interpretation depends on unit parameter)
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
            await connection.set_bus_parameter(bus, "mix/fader", fader_value)
            return f"Set bus {bus} to {format_db(db_value)} (linear: {fader_value:.3f})"
        except Exception as e:
            return f"Failed to set bus volume: {e}"

    @mcp.tool(
        name="bus_mute",
        description=(
            "Mute or unmute a specific mix bus on the X32/M32 mixer. "
            "This controls the bus on/off state."
        ),
    )
    async def bus_mute(bus: int, muted: bool) -> str:
        """
        Args:
            bus: Mix bus number from 1 to 16
            muted: True to mute the bus, False to unmute
        """
        if not connection.connected:
            return X32Error.not_connected()
        if bus < 1 or bus > 16:
            return X32Error.invalid_bus(bus)
        try:
            on_value = 0 if muted else 1
            await connection.set_bus_parameter(bus, "mix/on", on_value)
            state = "muted" if muted else "unmuted"
            return f"Bus {bus} is now {state}"
        except Exception as e:
            return f"Failed to mute/unmute bus: {e}"

    @mcp.tool(
        name="bus_set_pan",
        description=(
            "Set the stereo pan position for a specific mix bus on the X32/M32 mixer. "
            "Accepts linear (0.0-1.0), percentage (-100 to +100), or LR notation (L50, C, R100)."
        ),
    )
    async def bus_set_pan(bus: int, pan: str) -> str:
        """
        Args:
            bus: Mix bus number from 1 to 16
            pan: Pan position as linear (0.0-1.0), percentage (-100 to 100), or LR notation (L50, C, R100)
        """
        if not connection.connected:
            return X32Error.not_connected()
        if bus < 1 or bus > 16:
            return X32Error.invalid_bus(bus)
        try:
            pan_value = parse_pan(pan)
            if pan_value is None:
                return f"Invalid pan value: {pan}. Use linear (0.0-1.0), percentage (-100 to 100), or LR notation."
            await connection.set_bus_parameter(bus, "mix/pan", pan_value)
            return f"Set bus {bus} pan to {format_pan(pan_value)}"
        except Exception as e:
            return f"Failed to set bus pan: {e}"

    @mcp.tool(
        name="bus_get_volume",
        description="Get the current fader level (volume) for a specific mix bus.",
    )
    async def bus_get_volume(bus: int) -> str:
        """
        Args:
            bus: Mix bus number from 1 to 16
        """
        if not connection.connected:
            return X32Error.not_connected()
        if bus < 1 or bus > 16:
            return X32Error.invalid_bus(bus)
        try:
            fader_value = await connection.get_bus_parameter(bus, "mix/fader")
            db_value = fader_to_db(float(fader_value))
            return f"Bus {bus} fader: {format_db(db_value)} (linear: {float(fader_value):.3f})"
        except Exception as e:
            return f"Failed to get bus volume: {e}"

    @mcp.tool(
        name="bus_get_mute",
        description="Get the current mute state of a specific mix bus.",
    )
    async def bus_get_mute(bus: int) -> str:
        """
        Args:
            bus: Mix bus number from 1 to 16
        """
        if not connection.connected:
            return X32Error.not_connected()
        if bus < 1 or bus > 16:
            return X32Error.invalid_bus(bus)
        try:
            on_value = await connection.get_bus_parameter(bus, "mix/on")
            muted = int(on_value) == 0
            state = "muted" if muted else "unmuted"
            return f"Bus {bus} is {state}"
        except Exception as e:
            return f"Failed to get bus mute state: {e}"

    @mcp.tool(
        name="bus_set_name",
        description="Set the name/label for a specific mix bus on the X32/M32 mixer.",
    )
    async def bus_set_name(bus: int, name: str) -> str:
        """
        Args:
            bus: Mix bus number from 1 to 16
            name: Bus name/label (max 12 characters)
        """
        if not connection.connected:
            return X32Error.not_connected()
        if bus < 1 or bus > 16:
            return X32Error.invalid_bus(bus)
        try:
            await connection.set_bus_parameter(bus, "config/name", name)
            return f"Set bus {bus} name to '{name}'"
        except Exception as e:
            return f"Failed to set bus name: {e}"

    @mcp.tool(
        name="bus_get_pan",
        description="Get the current stereo pan position for a specific mix bus.",
    )
    async def bus_get_pan(bus: int) -> str:
        """
        Args:
            bus: Mix bus number from 1 to 16
        """
        if not connection.connected:
            return X32Error.not_connected()
        if bus < 1 or bus > 16:
            return X32Error.invalid_bus(bus)
        try:
            pan_value = await connection.get_bus_parameter(bus, "mix/pan")
            return f"Bus {bus} pan: {format_pan(float(pan_value))}"
        except Exception as e:
            return f"Failed to get bus pan: {e}"

    @mcp.tool(
        name="bus_get_name",
        description="Get the current name/label for a specific mix bus.",
    )
    async def bus_get_name(bus: int) -> str:
        """
        Args:
            bus: Mix bus number from 1 to 16
        """
        if not connection.connected:
            return X32Error.not_connected()
        if bus < 1 or bus > 16:
            return X32Error.invalid_bus(bus)
        try:
            name = await connection.get_bus_parameter(bus, "config/name")
            return f"Bus {bus} name: '{name}'"
        except Exception as e:
            return f"Failed to get bus name: {e}"

    @mcp.tool(
        name="bus_set_color",
        description="Set the color for a specific mix bus strip on the X32/M32 mixer.",
    )
    async def bus_set_color(bus: int, color: str) -> str:
        """
        Args:
            bus: Mix bus number from 1 to 16
            color: Color name (red, blue, green, yellow, magenta, cyan, white, off) or number (0-15)
        """
        if not connection.connected:
            return X32Error.not_connected()
        if bus < 1 or bus > 16:
            return X32Error.invalid_bus(bus)
        color_value = get_color_value(color)
        if color_value is None:
            available = ", ".join(get_available_colors())
            return f"Invalid color '{color}'. Available colors: {available}"
        try:
            await connection.set_bus_parameter(bus, "config/color", color_value)
            return f"Set bus {bus} color to {color} (value: {color_value})"
        except Exception as e:
            return f"Failed to set bus color: {e}"

    @mcp.tool(
        name="bus_get_dca",
        description=(
            "Get the DCA group assignments for a specific mix bus on the X32/M32 mixer. "
            "Returns which of the 8 DCA groups (1-8) the bus is assigned to."
        ),
    )
    async def bus_get_dca(bus: int) -> str:
        """
        Args:
            bus: Mix bus number from 1 to 16
        """
        if not connection.connected:
            return X32Error.not_connected()
        if bus < 1 or bus > 16:
            return X32Error.invalid_bus(bus)
        try:
            bus_num = str(bus).zfill(2)
            raw = await connection.get_parameter(f"/bus/{bus_num}/grp/dca")
            bitmask = int(raw)
            assigned = [dca for dca in range(1, 9) if bitmask & (1 << (dca - 1))]
            if assigned:
                dca_list = ", ".join(f"DCA {d}" for d in assigned)
                return f"Bus {bus} is assigned to: {dca_list} (raw value: {bitmask})"
            else:
                return f"Bus {bus} is not assigned to any DCA group (raw value: {bitmask})"
        except Exception as e:
            return f"Failed to get bus DCA assignments: {e}"

    @mcp.tool(
        name="bus_set_dca",
        description=(
            "Set the DCA group assignments for a specific mix bus on the X32/M32 mixer. "
            "Accepts a list of DCA groups (1-8) to assign the bus to. "
            "Pass an empty list to remove the bus from all DCA groups."
        ),
    )
    async def bus_set_dca(bus: int, dcas: list[int]) -> str:
        """
        Args:
            bus: Mix bus number from 1 to 16
            dcas: List of DCA group numbers (1-8) to assign the bus to. Empty list removes all assignments.
        """
        if not connection.connected:
            return X32Error.not_connected()
        if bus < 1 or bus > 16:
            return X32Error.invalid_bus(bus)
        invalid = [d for d in dcas if d < 1 or d > 8]
        if invalid:
            return f"Invalid DCA group(s): {invalid}. Each must be between 1 and 8."
        try:
            bitmask = 0
            for dca in dcas:
                bitmask |= 1 << (dca - 1)
            bus_num = str(bus).zfill(2)
            await connection.set_parameter(f"/bus/{bus_num}/grp/dca", bitmask)
            if dcas:
                dca_list = ", ".join(f"DCA {d}" for d in sorted(dcas))
                return f"Bus {bus} assigned to: {dca_list} (bitmask: {bitmask})"
            else:
                return f"Bus {bus} removed from all DCA groups (bitmask: 0)"
        except Exception as e:
            return f"Failed to set bus DCA assignments: {e}"

    @mcp.tool(
        name="bus_get_mute_group",
        description=(
            "Get the mute group assignments for a specific mix bus on the X32/M32 mixer. "
            "Returns which of the 6 mute groups (1-6) the bus is assigned to."
        ),
    )
    async def bus_get_mute_group(bus: int) -> str:
        """
        Args:
            bus: Mix bus number from 1 to 16
        """
        if not connection.connected:
            return X32Error.not_connected()
        if bus < 1 or bus > 16:
            return X32Error.invalid_bus(bus)
        try:
            bus_num = str(bus).zfill(2)
            raw = await connection.get_parameter(f"/bus/{bus_num}/grp/mute")
            bitmask = int(raw)
            assigned = [grp for grp in range(1, 7) if bitmask & (1 << (grp - 1))]
            if assigned:
                grp_list = ", ".join(f"Mute Group {g}" for g in assigned)
                return f"Bus {bus} is assigned to: {grp_list} (raw value: {bitmask})"
            else:
                return f"Bus {bus} is not assigned to any mute group (raw value: {bitmask})"
        except Exception as e:
            return f"Failed to get bus mute group assignments: {e}"

    @mcp.tool(
        name="bus_set_mute_group",
        description=(
            "Set the mute group assignments for a specific mix bus on the X32/M32 mixer. "
            "Accepts a list of mute groups (1-6) to assign the bus to. "
            "Pass an empty list to remove the bus from all mute groups."
        ),
    )
    async def bus_set_mute_group(bus: int, groups: list[int]) -> str:
        """
        Args:
            bus: Mix bus number from 1 to 16
            groups: List of mute group numbers (1-6) to assign the bus to. Empty list removes all assignments.
        """
        if not connection.connected:
            return X32Error.not_connected()
        if bus < 1 or bus > 16:
            return X32Error.invalid_bus(bus)
        invalid = [g for g in groups if g < 1 or g > 6]
        if invalid:
            return f"Invalid mute group(s): {invalid}. Each must be between 1 and 6."
        try:
            bitmask = 0
            for grp in groups:
                bitmask |= 1 << (grp - 1)
            bus_num = str(bus).zfill(2)
            await connection.set_parameter(f"/bus/{bus_num}/grp/mute", bitmask)
            if groups:
                grp_list = ", ".join(f"Mute Group {g}" for g in sorted(groups))
                return f"Bus {bus} assigned to: {grp_list} (bitmask: {bitmask})"
            else:
                return f"Bus {bus} removed from all mute groups (bitmask: 0)"
        except Exception as e:
            return f"Failed to set bus mute group assignments: {e}"
