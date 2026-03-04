"""
Dynamics domain tools
Gate/expander and compressor controls for input channels on the X32/M32 mixer.

X32 Gate addresses (per channel):
  /ch/NN/gate/on        - gate on/off (int 0/1)
  /ch/NN/gate/mode      - gate mode (int 0=EXP2, 1=EXP3, 2=EXP4, 3=GATE, 4=DUCK)
  /ch/NN/gate/thr       - threshold (float 0.0-1.0, maps -80 to 0 dB)
  /ch/NN/gate/range     - range (float 0.0-1.0, maps 3 to 60 dB)
  /ch/NN/gate/atk       - attack (float 0.0-1.0)
  /ch/NN/gate/hold      - hold (float 0.0-1.0)
  /ch/NN/gate/rel       - release (float 0.0-1.0)

X32 Compressor/Dynamics addresses (per channel):
  /ch/NN/dyn/on         - compressor on/off (int 0/1)
  /ch/NN/dyn/mode       - mode (int 0=COMP, 1=EXP)
  /ch/NN/dyn/det        - detection (int 0=PEAK, 1=RMS)
  /ch/NN/dyn/env        - envelope (int 0=LIN, 1=LOG)
  /ch/NN/dyn/thr        - threshold (float 0.0-1.0, maps -60 to 0 dB)
  /ch/NN/dyn/rat        - ratio (float 0.0-1.0, maps 1.0 to inf)
  /ch/NN/dyn/kg         - knee (float 0.0-1.0)
  /ch/NN/dyn/atk        - attack (float 0.0-1.0)
  /ch/NN/dyn/hold       - hold (float 0.0-1.0)
  /ch/NN/dyn/rel        - release (float 0.0-1.0)
  /ch/NN/dyn/mgain      - makeup gain (float 0.0-1.0, maps 0 to 24 dB)
  /ch/NN/dyn/mix        - mix/blend (float 0.0-1.0)

Threshold mapping (gate):    thr_db = param * 80 - 80    (0→-80, 1→0)
Threshold mapping (comp):    thr_db = param * 60 - 60    (0→-60, 1→0)
Ratio mapping:               ratio = 1 + param * 99       (approx; X32 uses non-linear)
Makeup gain mapping:         mgain_db = param * 24        (0 to 24 dB)
"""

from mcp.server.fastmcp import FastMCP
from src.services.x32_connection import X32Connection
from src.utils.error_helper import X32Error


# --- Gate helpers ---

def _gate_thr_to_param(db: float) -> float:
    """Convert gate threshold dB (-80 to 0) to X32 param (0.0–1.0)."""
    db = max(-80.0, min(0.0, db))
    return (db + 80.0) / 80.0


def _gate_param_to_thr(param: float) -> float:
    return param * 80.0 - 80.0


# --- Compressor helpers ---

def _comp_thr_to_param(db: float) -> float:
    """Convert compressor threshold dB (-60 to 0) to X32 param (0.0–1.0)."""
    db = max(-60.0, min(0.0, db))
    return (db + 60.0) / 60.0


def _comp_param_to_thr(param: float) -> float:
    return param * 60.0 - 60.0


# Ratio table: X32 encodes ratio as an index into a stepped list.
# Approximate continuous mapping: ratio = 1 + param * 99 (good enough for set; read is approximate).
_RATIO_STEPS = [1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.8, 2.0, 2.5, 3.0,
                3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 7.0, 8.0, 10.0, 12.0, 16.0,
                20.0, 1000.0]  # 1000 = inf


def _ratio_to_param(ratio: float) -> float:
    """Convert ratio (1.0–20.0+) to X32 float param (0.0–1.0) via nearest step."""
    best = min(range(len(_RATIO_STEPS)), key=lambda i: abs(_RATIO_STEPS[i] - ratio))
    return best / (len(_RATIO_STEPS) - 1)


def _param_to_ratio(param: float) -> str:
    idx = round(param * (len(_RATIO_STEPS) - 1))
    idx = max(0, min(len(_RATIO_STEPS) - 1, idx))
    val = _RATIO_STEPS[idx]
    return "∞:1" if val >= 100 else f"{val:.1f}:1"


def _mgain_to_param(db: float) -> float:
    """Convert makeup gain dB (0–24) to X32 param (0.0–1.0)."""
    db = max(0.0, min(24.0, db))
    return db / 24.0


def _param_to_mgain(param: float) -> float:
    return param * 24.0


def register_dynamics_tools(mcp: FastMCP, connection: X32Connection) -> None:
    """Register all dynamics (gate + compressor) domain tools."""

    # ===== GATE TOOLS =====

    @mcp.tool(
        name="channel_set_gate_on",
        description=(
            "Enable or disable the noise gate/expander for a specific input channel on the X32/M32."
        ),
    )
    async def channel_set_gate_on(channel: int, on: bool) -> str:
        """
        Args:
            channel: Input channel number from 1 to 32
            on: True to enable gate, False to disable/bypass
        """
        if not connection.connected:
            return X32Error.not_connected()
        if channel < 1 or channel > 32:
            return X32Error.invalid_channel(channel)
        try:
            ch = str(channel).zfill(2)
            await connection.set_parameter(f"/ch/{ch}/gate/on", 1 if on else 0)
            state = "enabled" if on else "disabled"
            return f"Channel {channel} gate is now {state}"
        except Exception as e:
            return f"Failed to set gate on/off: {e}"

    @mcp.tool(
        name="channel_get_gate_on",
        description="Get the gate enabled/bypass state for a specific input channel.",
    )
    async def channel_get_gate_on(channel: int) -> str:
        """
        Args:
            channel: Input channel number from 1 to 32
        """
        if not connection.connected:
            return X32Error.not_connected()
        if channel < 1 or channel > 32:
            return X32Error.invalid_channel(channel)
        try:
            ch = str(channel).zfill(2)
            val = await connection.get_parameter(f"/ch/{ch}/gate/on")
            state = "enabled" if int(val) == 1 else "disabled"
            return f"Channel {channel} gate is {state}"
        except Exception as e:
            return f"Failed to get gate on/off: {e}"

    @mcp.tool(
        name="channel_set_gate_threshold",
        description=(
            "Set the threshold for the noise gate on a specific input channel. "
            "Signals below this level will be gated (attenuated). Range: -80 to 0 dB."
        ),
    )
    async def channel_set_gate_threshold(channel: int, threshold_db: float) -> str:
        """
        Args:
            channel: Input channel number from 1 to 32
            threshold_db: Gate threshold in dB from -80.0 to 0.0
        """
        if not connection.connected:
            return X32Error.not_connected()
        if channel < 1 or channel > 32:
            return X32Error.invalid_channel(channel)
        if threshold_db < -80.0 or threshold_db > 0.0:
            return f"Invalid threshold {threshold_db} dB. Must be -80.0 to 0.0 dB."
        try:
            ch = str(channel).zfill(2)
            param = _gate_thr_to_param(threshold_db)
            await connection.set_parameter(f"/ch/{ch}/gate/thr", param)
            return f"Channel {channel} gate threshold set to {threshold_db:.1f} dB"
        except Exception as e:
            return f"Failed to set gate threshold: {e}"

    @mcp.tool(
        name="channel_get_gate_threshold",
        description="Get the gate threshold (in dB) for a specific input channel.",
    )
    async def channel_get_gate_threshold(channel: int) -> str:
        """
        Args:
            channel: Input channel number from 1 to 32
        """
        if not connection.connected:
            return X32Error.not_connected()
        if channel < 1 or channel > 32:
            return X32Error.invalid_channel(channel)
        try:
            ch = str(channel).zfill(2)
            param = float(await connection.get_parameter(f"/ch/{ch}/gate/thr"))
            thr_db = _gate_param_to_thr(param)
            return f"Channel {channel} gate threshold: {thr_db:.1f} dB"
        except Exception as e:
            return f"Failed to get gate threshold: {e}"

    @mcp.tool(
        name="channel_set_gate_attack",
        description=(
            "Set the attack time for the gate on a specific input channel. "
            "Controls how quickly the gate opens when signal exceeds threshold. "
            "Value is a normalised float 0.0 (fastest) to 1.0 (slowest)."
        ),
    )
    async def channel_set_gate_attack(channel: int, attack: float) -> str:
        """
        Args:
            channel: Input channel number from 1 to 32
            attack: Attack time 0.0 (fastest) to 1.0 (slowest)
        """
        if not connection.connected:
            return X32Error.not_connected()
        if channel < 1 or channel > 32:
            return X32Error.invalid_channel(channel)
        if attack < 0.0 or attack > 1.0:
            return X32Error.invalid_linear(attack)
        try:
            ch = str(channel).zfill(2)
            await connection.set_parameter(f"/ch/{ch}/gate/atk", attack)
            return f"Channel {channel} gate attack set to {attack:.3f}"
        except Exception as e:
            return f"Failed to set gate attack: {e}"

    @mcp.tool(
        name="channel_set_gate_release",
        description=(
            "Set the release time for the gate on a specific input channel. "
            "Controls how quickly the gate closes after signal drops below threshold. "
            "Value is a normalised float 0.0 (fastest) to 1.0 (slowest)."
        ),
    )
    async def channel_set_gate_release(channel: int, release: float) -> str:
        """
        Args:
            channel: Input channel number from 1 to 32
            release: Release time 0.0 (fastest) to 1.0 (slowest)
        """
        if not connection.connected:
            return X32Error.not_connected()
        if channel < 1 or channel > 32:
            return X32Error.invalid_channel(channel)
        if release < 0.0 or release > 1.0:
            return X32Error.invalid_linear(release)
        try:
            ch = str(channel).zfill(2)
            await connection.set_parameter(f"/ch/{ch}/gate/rel", release)
            return f"Channel {channel} gate release set to {release:.3f}"
        except Exception as e:
            return f"Failed to set gate release: {e}"

    @mcp.tool(
        name="channel_get_gate_info",
        description=(
            "Get a full summary of the gate/expander settings for a specific input channel, "
            "including on/off state, threshold, attack, hold, and release."
        ),
    )
    async def channel_get_gate_info(channel: int) -> str:
        """
        Args:
            channel: Input channel number from 1 to 32
        """
        if not connection.connected:
            return X32Error.not_connected()
        if channel < 1 or channel > 32:
            return X32Error.invalid_channel(channel)
        try:
            ch = str(channel).zfill(2)
            on_val = int(await connection.get_parameter(f"/ch/{ch}/gate/on"))
            thr = float(await connection.get_parameter(f"/ch/{ch}/gate/thr"))
            atk = float(await connection.get_parameter(f"/ch/{ch}/gate/atk"))
            hold = float(await connection.get_parameter(f"/ch/{ch}/gate/hold"))
            rel = float(await connection.get_parameter(f"/ch/{ch}/gate/rel"))
            state = "ON" if on_val == 1 else "OFF"
            thr_db = _gate_param_to_thr(thr)
            return (
                f"Channel {channel} gate: {state}, "
                f"threshold={thr_db:.1f} dB, "
                f"attack={atk:.3f}, hold={hold:.3f}, release={rel:.3f}"
            )
        except Exception as e:
            return f"Failed to get gate info: {e}"

    # ===== COMPRESSOR TOOLS =====

    @mcp.tool(
        name="channel_set_compressor_on",
        description=(
            "Enable or disable the compressor/dynamics processor for a specific input channel on the X32/M32."
        ),
    )
    async def channel_set_compressor_on(channel: int, on: bool) -> str:
        """
        Args:
            channel: Input channel number from 1 to 32
            on: True to enable compressor, False to disable/bypass
        """
        if not connection.connected:
            return X32Error.not_connected()
        if channel < 1 or channel > 32:
            return X32Error.invalid_channel(channel)
        try:
            ch = str(channel).zfill(2)
            await connection.set_parameter(f"/ch/{ch}/dyn/on", 1 if on else 0)
            state = "enabled" if on else "disabled"
            return f"Channel {channel} compressor is now {state}"
        except Exception as e:
            return f"Failed to set compressor on/off: {e}"

    @mcp.tool(
        name="channel_get_compressor_on",
        description="Get the compressor enabled/bypass state for a specific input channel.",
    )
    async def channel_get_compressor_on(channel: int) -> str:
        """
        Args:
            channel: Input channel number from 1 to 32
        """
        if not connection.connected:
            return X32Error.not_connected()
        if channel < 1 or channel > 32:
            return X32Error.invalid_channel(channel)
        try:
            ch = str(channel).zfill(2)
            val = await connection.get_parameter(f"/ch/{ch}/dyn/on")
            state = "enabled" if int(val) == 1 else "disabled"
            return f"Channel {channel} compressor is {state}"
        except Exception as e:
            return f"Failed to get compressor on/off: {e}"

    @mcp.tool(
        name="channel_set_compressor_threshold",
        description=(
            "Set the threshold for the compressor on a specific input channel. "
            "Signals above this level will be compressed. Range: -60 to 0 dB."
        ),
    )
    async def channel_set_compressor_threshold(channel: int, threshold_db: float) -> str:
        """
        Args:
            channel: Input channel number from 1 to 32
            threshold_db: Compressor threshold in dB from -60.0 to 0.0
        """
        if not connection.connected:
            return X32Error.not_connected()
        if channel < 1 or channel > 32:
            return X32Error.invalid_channel(channel)
        if threshold_db < -60.0 or threshold_db > 0.0:
            return f"Invalid threshold {threshold_db} dB. Must be -60.0 to 0.0 dB."
        try:
            ch = str(channel).zfill(2)
            param = _comp_thr_to_param(threshold_db)
            await connection.set_parameter(f"/ch/{ch}/dyn/thr", param)
            return f"Channel {channel} compressor threshold set to {threshold_db:.1f} dB"
        except Exception as e:
            return f"Failed to set compressor threshold: {e}"

    @mcp.tool(
        name="channel_get_compressor_threshold",
        description="Get the compressor threshold (in dB) for a specific input channel.",
    )
    async def channel_get_compressor_threshold(channel: int) -> str:
        """
        Args:
            channel: Input channel number from 1 to 32
        """
        if not connection.connected:
            return X32Error.not_connected()
        if channel < 1 or channel > 32:
            return X32Error.invalid_channel(channel)
        try:
            ch = str(channel).zfill(2)
            param = float(await connection.get_parameter(f"/ch/{ch}/dyn/thr"))
            thr_db = _comp_param_to_thr(param)
            return f"Channel {channel} compressor threshold: {thr_db:.1f} dB"
        except Exception as e:
            return f"Failed to get compressor threshold: {e}"

    @mcp.tool(
        name="channel_set_compressor_ratio",
        description=(
            "Set the compression ratio for a specific input channel. "
            "1.0 = no compression, higher = more compression. "
            "Common values: 2, 4, 8, 10, 20. Use a very large number (e.g. 100) for limiting."
        ),
    )
    async def channel_set_compressor_ratio(channel: int, ratio: float) -> str:
        """
        Args:
            channel: Input channel number from 1 to 32
            ratio: Compression ratio from 1.0 to 100.0 (use 100+ for limiting/infinite)
        """
        if not connection.connected:
            return X32Error.not_connected()
        if channel < 1 or channel > 32:
            return X32Error.invalid_channel(channel)
        if ratio < 1.0:
            return f"Invalid ratio {ratio}. Must be >= 1.0."
        try:
            ch = str(channel).zfill(2)
            param = _ratio_to_param(ratio)
            await connection.set_parameter(f"/ch/{ch}/dyn/rat", param)
            ratio_display = _param_to_ratio(param)
            return f"Channel {channel} compressor ratio set to {ratio_display}"
        except Exception as e:
            return f"Failed to set compressor ratio: {e}"

    @mcp.tool(
        name="channel_get_compressor_ratio",
        description="Get the compression ratio for a specific input channel.",
    )
    async def channel_get_compressor_ratio(channel: int) -> str:
        """
        Args:
            channel: Input channel number from 1 to 32
        """
        if not connection.connected:
            return X32Error.not_connected()
        if channel < 1 or channel > 32:
            return X32Error.invalid_channel(channel)
        try:
            ch = str(channel).zfill(2)
            param = float(await connection.get_parameter(f"/ch/{ch}/dyn/rat"))
            ratio_str = _param_to_ratio(param)
            return f"Channel {channel} compressor ratio: {ratio_str}"
        except Exception as e:
            return f"Failed to get compressor ratio: {e}"

    @mcp.tool(
        name="channel_set_compressor_attack",
        description=(
            "Set the attack time for the compressor on a specific input channel. "
            "Controls how quickly compression engages after the signal exceeds the threshold. "
            "Value is a normalised float 0.0 (fastest) to 1.0 (slowest)."
        ),
    )
    async def channel_set_compressor_attack(channel: int, attack: float) -> str:
        """
        Args:
            channel: Input channel number from 1 to 32
            attack: Attack time 0.0 (fastest) to 1.0 (slowest)
        """
        if not connection.connected:
            return X32Error.not_connected()
        if channel < 1 or channel > 32:
            return X32Error.invalid_channel(channel)
        if attack < 0.0 or attack > 1.0:
            return X32Error.invalid_linear(attack)
        try:
            ch = str(channel).zfill(2)
            await connection.set_parameter(f"/ch/{ch}/dyn/atk", attack)
            return f"Channel {channel} compressor attack set to {attack:.3f}"
        except Exception as e:
            return f"Failed to set compressor attack: {e}"

    @mcp.tool(
        name="channel_set_compressor_release",
        description=(
            "Set the release time for the compressor on a specific input channel. "
            "Controls how quickly compression disengages after the signal drops below threshold. "
            "Value is a normalised float 0.0 (fastest) to 1.0 (slowest)."
        ),
    )
    async def channel_set_compressor_release(channel: int, release: float) -> str:
        """
        Args:
            channel: Input channel number from 1 to 32
            release: Release time 0.0 (fastest) to 1.0 (slowest)
        """
        if not connection.connected:
            return X32Error.not_connected()
        if channel < 1 or channel > 32:
            return X32Error.invalid_channel(channel)
        if release < 0.0 or release > 1.0:
            return X32Error.invalid_linear(release)
        try:
            ch = str(channel).zfill(2)
            await connection.set_parameter(f"/ch/{ch}/dyn/rel", release)
            return f"Channel {channel} compressor release set to {release:.3f}"
        except Exception as e:
            return f"Failed to set compressor release: {e}"

    @mcp.tool(
        name="channel_set_compressor_makeup_gain",
        description=(
            "Set the makeup gain for the compressor on a specific input channel. "
            "This compensates for gain reduction from compression. Range: 0 to 24 dB."
        ),
    )
    async def channel_set_compressor_makeup_gain(channel: int, gain_db: float) -> str:
        """
        Args:
            channel: Input channel number from 1 to 32
            gain_db: Makeup gain in dB from 0.0 to 24.0
        """
        if not connection.connected:
            return X32Error.not_connected()
        if channel < 1 or channel > 32:
            return X32Error.invalid_channel(channel)
        if gain_db < 0.0 or gain_db > 24.0:
            return f"Invalid makeup gain {gain_db} dB. Must be 0.0 to 24.0 dB."
        try:
            ch = str(channel).zfill(2)
            param = _mgain_to_param(gain_db)
            await connection.set_parameter(f"/ch/{ch}/dyn/mgain", param)
            return f"Channel {channel} compressor makeup gain set to {gain_db:.1f} dB"
        except Exception as e:
            return f"Failed to set compressor makeup gain: {e}"

    @mcp.tool(
        name="channel_get_compressor_makeup_gain",
        description="Get the compressor makeup gain (in dB) for a specific input channel.",
    )
    async def channel_get_compressor_makeup_gain(channel: int) -> str:
        """
        Args:
            channel: Input channel number from 1 to 32
        """
        if not connection.connected:
            return X32Error.not_connected()
        if channel < 1 or channel > 32:
            return X32Error.invalid_channel(channel)
        try:
            ch = str(channel).zfill(2)
            param = float(await connection.get_parameter(f"/ch/{ch}/dyn/mgain"))
            mgain_db = _param_to_mgain(param)
            return f"Channel {channel} compressor makeup gain: {mgain_db:.1f} dB"
        except Exception as e:
            return f"Failed to get compressor makeup gain: {e}"

    @mcp.tool(
        name="channel_get_compressor_info",
        description=(
            "Get a full summary of the compressor settings for a specific input channel, "
            "including on/off state, threshold, ratio, attack, release, and makeup gain."
        ),
    )
    async def channel_get_compressor_info(channel: int) -> str:
        """
        Args:
            channel: Input channel number from 1 to 32
        """
        if not connection.connected:
            return X32Error.not_connected()
        if channel < 1 or channel > 32:
            return X32Error.invalid_channel(channel)
        try:
            ch = str(channel).zfill(2)
            on_val = int(await connection.get_parameter(f"/ch/{ch}/dyn/on"))
            thr = float(await connection.get_parameter(f"/ch/{ch}/dyn/thr"))
            rat = float(await connection.get_parameter(f"/ch/{ch}/dyn/rat"))
            atk = float(await connection.get_parameter(f"/ch/{ch}/dyn/atk"))
            rel = float(await connection.get_parameter(f"/ch/{ch}/dyn/rel"))
            mg = float(await connection.get_parameter(f"/ch/{ch}/dyn/mgain"))
            state = "ON" if on_val == 1 else "OFF"
            thr_db = _comp_param_to_thr(thr)
            ratio_str = _param_to_ratio(rat)
            mgain_db = _param_to_mgain(mg)
            return (
                f"Channel {channel} compressor: {state}, "
                f"threshold={thr_db:.1f} dB, ratio={ratio_str}, "
                f"attack={atk:.3f}, release={rel:.3f}, makeup gain={mgain_db:.1f} dB"
            )
        except Exception as e:
            return f"Failed to get compressor info: {e}"
