"""
Meters domain tools
Semantic, task-based tools for reading X32/M32 meter values
"""

from mcp.server.fastmcp import FastMCP
from src.services.x32_connection import X32Connection
from src.utils.error_helper import X32Error


def _fmt(value: float) -> str:
    """Format a meter float to a percentage-style string."""
    return f"{value * 100:.1f}%"


def _level_to_dbfs(value: float) -> str:
    """Convert a linear meter float [0, 1] to a rough dBFS string."""
    if value <= 0.0:
        return "-inf dBFS"
    import math
    db = 20.0 * math.log10(value)
    return f"{db:+.1f} dBFS"


def _format_floats(floats: list[float], labels: list[str] | None = None) -> str:
    """Format a list of meter floats as a readable multi-line string."""
    lines = []
    for i, val in enumerate(floats):
        label = labels[i] if labels and i < len(labels) else f"ch {i + 1:02d}"
        lines.append(f"  {label:<22s}: {_fmt(val):>8s}  ({_level_to_dbfs(val)})")
    return "\n".join(lines)


def register_meters_tools(mcp: FastMCP, connection: X32Connection) -> None:
    """Register all meters domain tools."""

    # ------------------------------------------------------------------
    # /meters/0 – Overview (70 floats)
    # 32 input channels + 8 aux returns + 4x2 FX returns + 16 bus masters
    # + 6 matrixes
    # ------------------------------------------------------------------
    @mcp.tool(
        name="meters_get_overview",
        description=(
            "Get an overview of all meter levels from the X32/M32 mixer (METERS page). "
            "Returns 70 float values: 32 input channels, 8 aux returns, "
            "8 FX returns, 16 bus masters, 6 matrix outputs. "
            "Values are linear [0.0–1.0] representing digital audio level."
        ),
    )
    async def meters_get_overview() -> str:
        if not connection.connected:
            return X32Error.not_connected()
        floats = await connection.request_meters("/meters/0")
        if floats is None:
            return "Failed to retrieve meter data (timeout or connection error)."
        labels = (
            [f"Input ch {i+1:02d}" for i in range(32)]
            + [f"Aux in {i+1}" for i in range(8)]
            + [f"FX rtn {i+1}" for i in range(8)]
            + [f"Bus {i+1:02d}" for i in range(16)]
            + [f"Matrix {i+1}" for i in range(6)]
        )
        return f"Overview meters ({len(floats)} channels):\n" + _format_floats(floats, labels)

    # ------------------------------------------------------------------
    # /meters/1 – Channel page (96 floats)
    # 32 input ch + 32 gate GR + 32 dynamics GR
    # ------------------------------------------------------------------
    @mcp.tool(
        name="meters_get_channels",
        description=(
            "Get channel strip meter levels from the X32/M32 mixer (METERS/channel page). "
            "Returns 96 values: 32 input channel levels, 32 gate gain reductions, "
            "32 dynamics/compressor gain reductions."
        ),
    )
    async def meters_get_channels() -> str:
        if not connection.connected:
            return X32Error.not_connected()
        floats = await connection.request_meters("/meters/1")
        if floats is None:
            return "Failed to retrieve meter data (timeout or connection error)."
        labels = (
            [f"Input ch {i+1:02d}  level" for i in range(32)]
            + [f"Gate GR ch {i+1:02d}" for i in range(32)]
            + [f"Dyn GR  ch {i+1:02d}" for i in range(32)]
        )
        return f"Channel meters ({len(floats)} values):\n" + _format_floats(floats, labels)

    # ------------------------------------------------------------------
    # /meters/2 – Mix bus page (49 floats)
    # ------------------------------------------------------------------
    @mcp.tool(
        name="meters_get_buses",
        description=(
            "Get mix bus meter levels from the X32/M32 mixer (METERS/mix bus page). "
            "Returns 49 values: 16 bus masters, 6 matrixes, 2 main LR, 1 mono M/C, "
            "plus their dynamics gain reductions."
        ),
    )
    async def meters_get_buses() -> str:
        if not connection.connected:
            return X32Error.not_connected()
        floats = await connection.request_meters("/meters/2")
        if floats is None:
            return "Failed to retrieve meter data (timeout or connection error)."
        labels = (
            [f"Bus {i+1:02d}    level" for i in range(16)]
            + [f"Matrix {i+1}  level" for i in range(6)]
            + ["Main L  level", "Main R  level", "Mono    level"]
            + [f"Bus {i+1:02d}    dyn GR" for i in range(16)]
            + [f"Matrix {i+1}  dyn GR" for i in range(6)]
            + ["Main LR dyn GR", "Mono    dyn GR"]
        )
        return f"Bus meters ({len(floats)} values):\n" + _format_floats(floats, labels)

    # ------------------------------------------------------------------
    # /meters/3 – Aux/FX page (22 floats)
    # ------------------------------------------------------------------
    @mcp.tool(
        name="meters_get_aux_fx",
        description=(
            "Get aux and FX return meter levels from the X32/M32 mixer (METERS/aux/fx page). "
            "Returns 22 values: 6 aux sends, 8 aux returns, 8 FX returns."
        ),
    )
    async def meters_get_aux_fx() -> str:
        if not connection.connected:
            return X32Error.not_connected()
        floats = await connection.request_meters("/meters/3")
        if floats is None:
            return "Failed to retrieve meter data (timeout or connection error)."
        labels = (
            [f"Aux send {i+1}" for i in range(6)]
            + [f"Aux rtn  {i+1}" for i in range(8)]
            + [f"FX rtn   {i+1}" for i in range(8)]
        )
        return f"Aux/FX meters ({len(floats)} values):\n" + _format_floats(floats, labels)

    # ------------------------------------------------------------------
    # /meters/4 – In/Out page (82 floats)
    # ------------------------------------------------------------------
    @mcp.tool(
        name="meters_get_in_out",
        description=(
            "Get input/output meter levels from the X32/M32 mixer (METERS/in/out page). "
            "Returns 82 values covering all input channels, aux returns, outputs, "
            "P16 ultranet outputs, aux sends, AES/EBU, and monitor outputs."
        ),
    )
    async def meters_get_in_out() -> str:
        if not connection.connected:
            return X32Error.not_connected()
        floats = await connection.request_meters("/meters/4")
        if floats is None:
            return "Failed to retrieve meter data (timeout or connection error)."
        labels = (
            [f"Input ch {i+1:02d}" for i in range(32)]
            + [f"Aux rtn  {i+1}" for i in range(8)]
            + [f"Output   {i+1:02d}" for i in range(16)]
            + [f"P16      {i+1:02d}" for i in range(16)]
            + [f"Aux send {i+1}" for i in range(6)]
            + ["AES/EBU L", "AES/EBU R"]
            + ["Monitor L", "Monitor R"]
        )
        return f"In/Out meters ({len(floats)} values):\n" + _format_floats(floats, labels)

    # ------------------------------------------------------------------
    # /meters/5 – Console surface VU meters (27 floats)
    # Requires chn_meter_id (0-3) and grp_meter_id (0-3)
    # ------------------------------------------------------------------
    @mcp.tool(
        name="meters_get_surface",
        description=(
            "Get console surface VU meter levels from the X32/M32 mixer. "
            "Returns 27 values: 16 channel meters, 8 group meters, 2 main LR, 1 mono M/C. "
            "channel_bank selects which 16 channels: "
            "0=ch1-16, 1=ch17-32, 2=aux/fx returns, 3=bus masters. "
            "group_bank selects which groups: "
            "0=DCA1-8, 1=bus1-8, 2=bus9-16, 3=matrixes."
        ),
    )
    async def meters_get_surface(
        channel_bank: int = 0, group_bank: int = 0
    ) -> str:
        """
        Args:
            channel_bank: 0=ch1-16, 1=ch17-32, 2=aux/fx returns, 3=bus masters
            group_bank:   0=DCA1-8, 1=bus1-8,  2=bus9-16,        3=matrixes
        """
        if not connection.connected:
            return X32Error.not_connected()
        if channel_bank not in range(4):
            return "channel_bank must be 0-3."
        if group_bank not in range(4):
            return "group_bank must be 0-3."

        ch_bank_names = ["ch1-16", "ch17-32", "aux/fx returns", "bus masters"]
        grp_bank_names = ["DCA1-8", "bus1-8", "bus9-16", "matrixes"]

        floats = await connection.request_meters("/meters/5", channel_bank, group_bank)
        if floats is None:
            return "Failed to retrieve meter data (timeout or connection error)."

        ch_start = channel_bank * 16 + 1
        ch_labels = [f"CH {ch_start + i:02d}" for i in range(16)]
        grp_labels = [f"GRP ({grp_bank_names[group_bank]}) {i+1}" for i in range(8)]
        labels = ch_labels + grp_labels + ["Main L", "Main R", "Mono"]

        return (
            f"Surface meters — channels: {ch_bank_names[channel_bank]}, "
            f"groups: {grp_bank_names[group_bank]} ({len(floats)} values):\n"
            + _format_floats(floats, labels)
        )

    # ------------------------------------------------------------------
    # /meters/6 – Channel strip meters (4 floats for one channel)
    # ------------------------------------------------------------------
    @mcp.tool(
        name="meters_get_channel_strip",
        description=(
            "Get the 4 channel strip meter values for a single channel on the X32/M32 mixer. "
            "Returns: pre-fader level, gate gain reduction, dynamics gain reduction, "
            "post-fader level. "
            "channel_id is 0-71 (0-31=ch1-32, 32-39=aux1-8, 40-47=fxrtn1-8, "
            "48-63=bus1-16, 64-69=matrix1-6, 70=LR, 71=mono)."
        ),
    )
    async def meters_get_channel_strip(channel_id: int) -> str:
        """
        Args:
            channel_id: 0-71 — see description for mapping
        """
        if not connection.connected:
            return X32Error.not_connected()
        if channel_id < 0 or channel_id > 71:
            return "channel_id must be 0-71."

        floats = await connection.request_meters("/meters/6", channel_id)
        if floats is None:
            return "Failed to retrieve meter data (timeout or connection error)."

        # Human-readable channel name
        if channel_id <= 31:
            ch_name = f"Input ch {channel_id + 1:02d}"
        elif channel_id <= 39:
            ch_name = f"Aux in {channel_id - 31}"
        elif channel_id <= 47:
            ch_name = f"FX rtn {channel_id - 39}"
        elif channel_id <= 63:
            ch_name = f"Bus {channel_id - 47:02d}"
        elif channel_id <= 69:
            ch_name = f"Matrix {channel_id - 63}"
        elif channel_id == 70:
            ch_name = "Main L/R"
        else:
            ch_name = "Mono/M"

        labels = ["Pre-fader level", "Gate GR", "Dyn GR", "Post-fader level"]
        return (
            f"Channel strip meters for {ch_name} (channel_id={channel_id}):\n"
            + _format_floats(floats, labels)
        )

    # ------------------------------------------------------------------
    # /meters/7 – Bus send meters (16 floats)
    # ------------------------------------------------------------------
    @mcp.tool(
        name="meters_get_bus_sends",
        description=(
            "Get the 16 bus send meter levels from the X32/M32 mixer. "
            "Returns one level per bus send (bus 1-16)."
        ),
    )
    async def meters_get_bus_sends() -> str:
        if not connection.connected:
            return X32Error.not_connected()
        floats = await connection.request_meters("/meters/7")
        if floats is None:
            return "Failed to retrieve meter data (timeout or connection error)."
        labels = [f"Bus send {i+1:02d}" for i in range(16)]
        return f"Bus send meters ({len(floats)} values):\n" + _format_floats(floats, labels)

    # ------------------------------------------------------------------
    # /meters/8 – Matrix send meters (6 floats)
    # ------------------------------------------------------------------
    @mcp.tool(
        name="meters_get_matrix_sends",
        description=(
            "Get the 6 matrix send meter levels from the X32/M32 mixer. "
            "Returns one level per matrix send (matrix 1-6)."
        ),
    )
    async def meters_get_matrix_sends() -> str:
        if not connection.connected:
            return X32Error.not_connected()
        floats = await connection.request_meters("/meters/8")
        if floats is None:
            return "Failed to retrieve meter data (timeout or connection error)."
        labels = [f"Matrix send {i+1}" for i in range(6)]
        return f"Matrix send meters ({len(floats)} values):\n" + _format_floats(floats, labels)
