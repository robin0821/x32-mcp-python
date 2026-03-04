"""
Matrix output domain tools for the X32/M32 mixer.

X32 Matrix output addresses:
  /mtx/NN/mix/fader      - matrix fader (float 0.0-1.0)
  /mtx/NN/mix/on         - matrix on/off (int 1=on, 0=muted)
  /mtx/NN/mix/pan        - matrix pan (float 0.0-1.0)
  /mtx/NN/config/name    - matrix name (string)

The X32/M32 has 6 matrix outputs (1-6).
"""

from mcp.server.fastmcp import FastMCP
from src.services.x32_connection import X32Connection
from src.utils.db_converter import db_to_fader, fader_to_db, format_db
from src.utils.pan_converter import parse_pan, format_pan
from src.utils.error_helper import X32Error


def register_matrix_tools(mcp: FastMCP, connection: X32Connection) -> None:
    """Register all matrix output domain tools."""

    @mcp.tool(
        name="matrix_set_volume",
        description=(
            "Set the fader level for a matrix output on the X32/M32 mixer. "
            "The X32/M32 has 6 matrix outputs. "
            "Supports linear (0.0-1.0) or dB values (-90 to +10 dB)."
        ),
    )
    async def matrix_set_volume(matrix: int, value: float, unit: str = "linear") -> str:
        """
        Args:
            matrix: Matrix output number from 1 to 6
            value: Volume value
            unit: "linear" (0.0-1.0) or "db" (-90 to +10 dB). Default is "linear".
        """
        if not connection.connected:
            return X32Error.not_connected()
        if matrix < 1 or matrix > 6:
            return f"Invalid matrix number {matrix}. Must be 1–6."
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
            mtx = str(matrix).zfill(2)
            await connection.set_parameter(f"/mtx/{mtx}/mix/fader", fader_value)
            return f"Matrix {matrix} fader set to {format_db(db_value)} (linear: {fader_value:.3f})"
        except Exception as e:
            return f"Failed to set matrix volume: {e}"

    @mcp.tool(
        name="matrix_get_volume",
        description="Get the current fader level for a matrix output on the X32/M32.",
    )
    async def matrix_get_volume(matrix: int) -> str:
        """
        Args:
            matrix: Matrix output number from 1 to 6
        """
        if not connection.connected:
            return X32Error.not_connected()
        if matrix < 1 or matrix > 6:
            return f"Invalid matrix number {matrix}. Must be 1–6."
        try:
            mtx = str(matrix).zfill(2)
            fader = float(await connection.get_parameter(f"/mtx/{mtx}/mix/fader"))
            db_value = fader_to_db(fader)
            return f"Matrix {matrix} fader: {format_db(db_value)} (linear: {fader:.3f})"
        except Exception as e:
            return f"Failed to get matrix volume: {e}"

    @mcp.tool(
        name="matrix_mute",
        description="Mute or unmute a matrix output on the X32/M32 mixer.",
    )
    async def matrix_mute(matrix: int, muted: bool) -> str:
        """
        Args:
            matrix: Matrix output number from 1 to 6
            muted: True to mute, False to unmute
        """
        if not connection.connected:
            return X32Error.not_connected()
        if matrix < 1 or matrix > 6:
            return f"Invalid matrix number {matrix}. Must be 1–6."
        try:
            mtx = str(matrix).zfill(2)
            on_value = 0 if muted else 1
            await connection.set_parameter(f"/mtx/{mtx}/mix/on", on_value)
            state = "muted" if muted else "unmuted"
            return f"Matrix {matrix} is now {state}"
        except Exception as e:
            return f"Failed to mute/unmute matrix: {e}"

    @mcp.tool(
        name="matrix_get_mute",
        description="Get the mute state of a matrix output on the X32/M32 mixer.",
    )
    async def matrix_get_mute(matrix: int) -> str:
        """
        Args:
            matrix: Matrix output number from 1 to 6
        """
        if not connection.connected:
            return X32Error.not_connected()
        if matrix < 1 or matrix > 6:
            return f"Invalid matrix number {matrix}. Must be 1–6."
        try:
            mtx = str(matrix).zfill(2)
            on_val = await connection.get_parameter(f"/mtx/{mtx}/mix/on")
            muted = int(on_val) == 0
            state = "muted" if muted else "unmuted"
            return f"Matrix {matrix} is {state}"
        except Exception as e:
            return f"Failed to get matrix mute state: {e}"

    @mcp.tool(
        name="matrix_set_pan",
        description=(
            "Set the stereo pan for a matrix output on the X32/M32 mixer. "
            "Accepts linear (0.0-1.0), percentage (-100 to +100), or LR notation (L50, C, R100)."
        ),
    )
    async def matrix_set_pan(matrix: int, pan: str) -> str:
        """
        Args:
            matrix: Matrix output number from 1 to 6
            pan: Pan position as linear (0.0-1.0), percentage (-100 to 100), or LR notation
        """
        if not connection.connected:
            return X32Error.not_connected()
        if matrix < 1 or matrix > 6:
            return f"Invalid matrix number {matrix}. Must be 1–6."
        try:
            pan_value = parse_pan(pan)
            if pan_value is None:
                return f"Invalid pan value: {pan}. Use linear (0.0-1.0), percentage (-100 to 100), or LR notation."
            mtx = str(matrix).zfill(2)
            await connection.set_parameter(f"/mtx/{mtx}/mix/pan", pan_value)
            return f"Matrix {matrix} pan set to {format_pan(pan_value)}"
        except Exception as e:
            return f"Failed to set matrix pan: {e}"

    @mcp.tool(
        name="matrix_set_name",
        description="Set the name/label for a matrix output on the X32/M32 mixer.",
    )
    async def matrix_set_name(matrix: int, name: str) -> str:
        """
        Args:
            matrix: Matrix output number from 1 to 6
            name: Name/label string (max 12 characters)
        """
        if not connection.connected:
            return X32Error.not_connected()
        if matrix < 1 or matrix > 6:
            return f"Invalid matrix number {matrix}. Must be 1–6."
        try:
            mtx = str(matrix).zfill(2)
            await connection.set_parameter(f"/mtx/{mtx}/config/name", name)
            return f"Matrix {matrix} name set to '{name}'"
        except Exception as e:
            return f"Failed to set matrix name: {e}"

    @mcp.tool(
        name="matrix_get_dca",
        description=(
            "Get the DCA group assignments for a specific matrix output on the X32/M32 mixer. "
            "Returns which of the 8 DCA groups (1-8) the matrix output is assigned to."
        ),
    )
    async def matrix_get_dca(matrix: int) -> str:
        """
        Args:
            matrix: Matrix output number from 1 to 6
        """
        if not connection.connected:
            return X32Error.not_connected()
        if matrix < 1 or matrix > 6:
            return f"Invalid matrix number {matrix}. Must be 1–6."
        try:
            mtx = str(matrix).zfill(2)
            raw = await connection.get_parameter(f"/mtx/{mtx}/grp/dca")
            bitmask = int(raw)
            assigned = [dca for dca in range(1, 9) if bitmask & (1 << (dca - 1))]
            if assigned:
                dca_list = ", ".join(f"DCA {d}" for d in assigned)
                return f"Matrix {matrix} is assigned to: {dca_list} (raw value: {bitmask})"
            else:
                return f"Matrix {matrix} is not assigned to any DCA group (raw value: {bitmask})"
        except Exception as e:
            return f"Failed to get matrix DCA assignments: {e}"

    @mcp.tool(
        name="matrix_set_dca",
        description=(
            "Set the DCA group assignments for a specific matrix output on the X32/M32 mixer. "
            "Accepts a list of DCA groups (1-8) to assign the matrix output to. "
            "Pass an empty list to remove the matrix output from all DCA groups."
        ),
    )
    async def matrix_set_dca(matrix: int, dcas: list[int]) -> str:
        """
        Args:
            matrix: Matrix output number from 1 to 6
            dcas: List of DCA group numbers (1-8). Empty list removes all assignments.
        """
        if not connection.connected:
            return X32Error.not_connected()
        if matrix < 1 or matrix > 6:
            return f"Invalid matrix number {matrix}. Must be 1–6."
        invalid = [d for d in dcas if d < 1 or d > 8]
        if invalid:
            return f"Invalid DCA group(s): {invalid}. Each must be between 1 and 8."
        try:
            bitmask = 0
            for dca in dcas:
                bitmask |= 1 << (dca - 1)
            mtx = str(matrix).zfill(2)
            await connection.set_parameter(f"/mtx/{mtx}/grp/dca", bitmask)
            if dcas:
                dca_list = ", ".join(f"DCA {d}" for d in sorted(dcas))
                return f"Matrix {matrix} assigned to: {dca_list} (bitmask: {bitmask})"
            else:
                return f"Matrix {matrix} removed from all DCA groups (bitmask: 0)"
        except Exception as e:
            return f"Failed to set matrix DCA assignments: {e}"

    @mcp.tool(
        name="matrix_get_mute_group",
        description=(
            "Get the mute group assignments for a specific matrix output on the X32/M32 mixer. "
            "Returns which of the 6 mute groups (1-6) the matrix output is assigned to."
        ),
    )
    async def matrix_get_mute_group(matrix: int) -> str:
        """
        Args:
            matrix: Matrix output number from 1 to 6
        """
        if not connection.connected:
            return X32Error.not_connected()
        if matrix < 1 or matrix > 6:
            return f"Invalid matrix number {matrix}. Must be 1–6."
        try:
            mtx = str(matrix).zfill(2)
            raw = await connection.get_parameter(f"/mtx/{mtx}/grp/mute")
            bitmask = int(raw)
            assigned = [grp for grp in range(1, 7) if bitmask & (1 << (grp - 1))]
            if assigned:
                grp_list = ", ".join(f"Mute Group {g}" for g in assigned)
                return f"Matrix {matrix} is assigned to: {grp_list} (raw value: {bitmask})"
            else:
                return f"Matrix {matrix} is not assigned to any mute group (raw value: {bitmask})"
        except Exception as e:
            return f"Failed to get matrix mute group assignments: {e}"

    @mcp.tool(
        name="matrix_set_mute_group",
        description=(
            "Set the mute group assignments for a specific matrix output on the X32/M32 mixer. "
            "Accepts a list of mute groups (1-6) to assign the matrix output to. "
            "Pass an empty list to remove the matrix output from all mute groups."
        ),
    )
    async def matrix_set_mute_group(matrix: int, groups: list[int]) -> str:
        """
        Args:
            matrix: Matrix output number from 1 to 6
            groups: List of mute group numbers (1-6). Empty list removes all assignments.
        """
        if not connection.connected:
            return X32Error.not_connected()
        if matrix < 1 or matrix > 6:
            return f"Invalid matrix number {matrix}. Must be 1–6."
        invalid = [g for g in groups if g < 1 or g > 6]
        if invalid:
            return f"Invalid mute group(s): {invalid}. Each must be between 1 and 6."
        try:
            bitmask = 0
            for grp in groups:
                bitmask |= 1 << (grp - 1)
            mtx = str(matrix).zfill(2)
            await connection.set_parameter(f"/mtx/{mtx}/grp/mute", bitmask)
            if groups:
                grp_list = ", ".join(f"Mute Group {g}" for g in sorted(groups))
                return f"Matrix {matrix} assigned to: {grp_list} (bitmask: {bitmask})"
            else:
                return f"Matrix {matrix} removed from all mute groups (bitmask: 0)"
        except Exception as e:
            return f"Failed to set matrix mute group assignments: {e}"

    @mcp.tool(
        name="bus_set_send_to_matrix",
        description=(
            "Set the send level from a mix bus to a matrix output on the X32/M32 mixer. "
            "This controls how much of a mix bus is routed to a matrix output."
        ),
    )
    async def bus_set_send_to_matrix(bus: int, matrix: int, value: float, unit: str = "linear") -> str:
        """
        Args:
            bus: Mix bus number from 1 to 16
            matrix: Matrix output number from 1 to 6
            value: Send level value
            unit: "linear" (0.0-1.0) or "db" (-90 to +10 dB). Default is "linear".
        """
        if not connection.connected:
            return X32Error.not_connected()
        if bus < 1 or bus > 16:
            return X32Error.invalid_bus(bus)
        if matrix < 1 or matrix > 6:
            return f"Invalid matrix number {matrix}. Must be 1–6."
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
            bus_num = str(bus).zfill(2)
            mtx = str(matrix).zfill(2)
            await connection.set_parameter(f"/bus/{bus_num}/mix/{mtx}/level", fader_value)
            return f"Bus {bus} send to matrix {matrix}: {format_db(db_value)} (linear: {fader_value:.3f})"
        except Exception as e:
            return f"Failed to set bus send to matrix: {e}"