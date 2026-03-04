"""
EQ domain tools
Per-band parametric EQ controls for channels on the X32/M32 mixer.

X32 EQ addresses:
  /ch/NN/eq/on          - EQ on/off (int 0/1)
  /ch/NN/eq/N/type      - band type (int 0-5)
  /ch/NN/eq/N/f         - frequency (float 0.0-1.0, maps 20-20000 Hz log)
  /ch/NN/eq/N/g         - gain (float 0.0-1.0, maps -15 to +15 dB)
  /ch/NN/eq/N/q         - Q (float 0.0-1.0, maps 10 to 0.3 log)

Frequency mapping (X32 protocol):  f_hz = 20 * (1000 ** param)
Gain mapping:                       gain_db = (param * 30) - 15
Q mapping:                          q = 10 ** (1 - 2 * param)   (approx)
"""

import math
from mcp.server.fastmcp import FastMCP
from src.services.x32_connection import X32Connection
from src.utils.error_helper import X32Error


def _freq_to_param(freq_hz: float) -> float:
    """Convert frequency in Hz (20–20000) to X32 float param (0.0–1.0)."""
    freq_hz = max(20.0, min(20000.0, freq_hz))
    return math.log10(freq_hz / 20.0) / math.log10(1000.0)


def _param_to_freq(param: float) -> float:
    """Convert X32 float param (0.0–1.0) to frequency in Hz."""
    return 20.0 * (1000.0 ** param)


def _gain_db_to_param(gain_db: float) -> float:
    """Convert gain in dB (-15 to +15) to X32 float param (0.0–1.0)."""
    gain_db = max(-15.0, min(15.0, gain_db))
    return (gain_db + 15.0) / 30.0


def _param_to_gain_db(param: float) -> float:
    """Convert X32 float param (0.0–1.0) to gain in dB."""
    return (param * 30.0) - 15.0


def _q_to_param(q: float) -> float:
    """Convert Q factor (0.3–10) to X32 float param (0.0–1.0)."""
    # X32: q = 10^(1 - 2*param)  =>  param = (1 - log10(q)) / 2
    q = max(0.3, min(10.0, q))
    return (1.0 - math.log10(q)) / 2.0


def _param_to_q(param: float) -> float:
    """Convert X32 float param (0.0–1.0) to Q factor."""
    return 10.0 ** (1.0 - 2.0 * param)


_BAND_TYPES = {0: "LC", 1: "LP", 2: "Parametric", 3: "VEQ", 4: "HP", 5: "HC"}


def register_eq_tools(mcp: FastMCP, connection: X32Connection) -> None:
    """Register all EQ domain tools."""

    @mcp.tool(
        name="channel_set_eq_on",
        description=(
            "Enable or disable the parametric EQ for a specific input channel on the X32/M32. "
            "When disabled, the EQ is bypassed entirely."
        ),
    )
    async def channel_set_eq_on(channel: int, on: bool) -> str:
        """
        Args:
            channel: Input channel number from 1 to 32
            on: True to enable EQ, False to bypass/disable
        """
        if not connection.connected:
            return X32Error.not_connected()
        if channel < 1 or channel > 32:
            return X32Error.invalid_channel(channel)
        try:
            ch = str(channel).zfill(2)
            await connection.set_parameter(f"/ch/{ch}/eq/on", 1 if on else 0)
            state = "enabled" if on else "disabled"
            return f"Channel {channel} EQ is now {state}"
        except Exception as e:
            return f"Failed to set EQ on/off: {e}"

    @mcp.tool(
        name="channel_get_eq_on",
        description="Get the EQ enabled/bypass state for a specific input channel.",
    )
    async def channel_get_eq_on(channel: int) -> str:
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
            val = await connection.get_parameter(f"/ch/{ch}/eq/on")
            state = "enabled" if int(val) == 1 else "disabled"
            return f"Channel {channel} EQ is {state}"
        except Exception as e:
            return f"Failed to get EQ on/off: {e}"

    @mcp.tool(
        name="channel_set_eq_gain",
        description=(
            "Set the gain for a specific EQ band on an input channel. "
            "The X32/M32 has 4-band parametric EQ per channel."
        ),
    )
    async def channel_set_eq_gain(channel: int, band: int, gain_db: float) -> str:
        """
        Args:
            channel: Input channel number from 1 to 32
            band: EQ band number from 1 to 4 (1=low shelf, 2=low-mid, 3=high-mid, 4=high shelf)
            gain_db: Gain in dB from -15.0 to +15.0
        """
        if not connection.connected:
            return X32Error.not_connected()
        if channel < 1 or channel > 32:
            return X32Error.invalid_channel(channel)
        if band < 1 or band > 4:
            return f"Invalid EQ band {band}. Must be 1–4."
        if gain_db < -15.0 or gain_db > 15.0:
            return f"Invalid gain {gain_db} dB. Must be -15.0 to +15.0 dB."
        try:
            ch = str(channel).zfill(2)
            param = _gain_db_to_param(gain_db)
            await connection.set_parameter(f"/ch/{ch}/eq/{band}/g", param)
            return f"Channel {channel} EQ band {band} gain set to {gain_db:+.1f} dB"
        except Exception as e:
            return f"Failed to set EQ gain: {e}"

    @mcp.tool(
        name="channel_get_eq_gain",
        description="Get the gain (in dB) for a specific EQ band on an input channel.",
    )
    async def channel_get_eq_gain(channel: int, band: int) -> str:
        """
        Args:
            channel: Input channel number from 1 to 32
            band: EQ band number from 1 to 4
        """
        if not connection.connected:
            return X32Error.not_connected()
        if channel < 1 or channel > 32:
            return X32Error.invalid_channel(channel)
        if band < 1 or band > 4:
            return f"Invalid EQ band {band}. Must be 1–4."
        try:
            ch = str(channel).zfill(2)
            param = float(await connection.get_parameter(f"/ch/{ch}/eq/{band}/g"))
            gain_db = _param_to_gain_db(param)
            return f"Channel {channel} EQ band {band} gain: {gain_db:+.1f} dB"
        except Exception as e:
            return f"Failed to get EQ gain: {e}"

    @mcp.tool(
        name="channel_set_eq_frequency",
        description=(
            "Set the centre/corner frequency for a specific EQ band on an input channel. "
            "Range is 20 Hz to 20 kHz."
        ),
    )
    async def channel_set_eq_frequency(channel: int, band: int, frequency_hz: float) -> str:
        """
        Args:
            channel: Input channel number from 1 to 32
            band: EQ band number from 1 to 4
            frequency_hz: Frequency in Hz from 20 to 20000
        """
        if not connection.connected:
            return X32Error.not_connected()
        if channel < 1 or channel > 32:
            return X32Error.invalid_channel(channel)
        if band < 1 or band > 4:
            return f"Invalid EQ band {band}. Must be 1–4."
        if frequency_hz < 20 or frequency_hz > 20000:
            return f"Invalid frequency {frequency_hz} Hz. Must be 20–20000 Hz."
        try:
            ch = str(channel).zfill(2)
            param = _freq_to_param(frequency_hz)
            await connection.set_parameter(f"/ch/{ch}/eq/{band}/f", param)
            freq_display = f"{frequency_hz:.0f} Hz" if frequency_hz < 1000 else f"{frequency_hz / 1000:.2f} kHz"
            return f"Channel {channel} EQ band {band} frequency set to {freq_display}"
        except Exception as e:
            return f"Failed to set EQ frequency: {e}"

    @mcp.tool(
        name="channel_get_eq_frequency",
        description="Get the centre/corner frequency (in Hz) for a specific EQ band on an input channel.",
    )
    async def channel_get_eq_frequency(channel: int, band: int) -> str:
        """
        Args:
            channel: Input channel number from 1 to 32
            band: EQ band number from 1 to 4
        """
        if not connection.connected:
            return X32Error.not_connected()
        if channel < 1 or channel > 32:
            return X32Error.invalid_channel(channel)
        if band < 1 or band > 4:
            return f"Invalid EQ band {band}. Must be 1–4."
        try:
            ch = str(channel).zfill(2)
            param = float(await connection.get_parameter(f"/ch/{ch}/eq/{band}/f"))
            freq_hz = _param_to_freq(param)
            freq_display = f"{freq_hz:.0f} Hz" if freq_hz < 1000 else f"{freq_hz / 1000:.2f} kHz"
            return f"Channel {channel} EQ band {band} frequency: {freq_display}"
        except Exception as e:
            return f"Failed to get EQ frequency: {e}"

    @mcp.tool(
        name="channel_set_eq_q",
        description=(
            "Set the Q (bandwidth) factor for a specific EQ band on an input channel. "
            "Higher Q = narrower band. Range 0.3 to 10."
        ),
    )
    async def channel_set_eq_q(channel: int, band: int, q: float) -> str:
        """
        Args:
            channel: Input channel number from 1 to 32
            band: EQ band number from 1 to 4
            q: Q factor from 0.3 (wide) to 10.0 (narrow)
        """
        if not connection.connected:
            return X32Error.not_connected()
        if channel < 1 or channel > 32:
            return X32Error.invalid_channel(channel)
        if band < 1 or band > 4:
            return f"Invalid EQ band {band}. Must be 1–4."
        if q < 0.3 or q > 10.0:
            return f"Invalid Q {q}. Must be 0.3–10.0."
        try:
            ch = str(channel).zfill(2)
            param = _q_to_param(q)
            await connection.set_parameter(f"/ch/{ch}/eq/{band}/q", param)
            return f"Channel {channel} EQ band {band} Q set to {q:.2f}"
        except Exception as e:
            return f"Failed to set EQ Q: {e}"

    @mcp.tool(
        name="channel_get_eq_q",
        description="Get the Q factor for a specific EQ band on an input channel.",
    )
    async def channel_get_eq_q(channel: int, band: int) -> str:
        """
        Args:
            channel: Input channel number from 1 to 32
            band: EQ band number from 1 to 4
        """
        if not connection.connected:
            return X32Error.not_connected()
        if channel < 1 or channel > 32:
            return X32Error.invalid_channel(channel)
        if band < 1 or band > 4:
            return f"Invalid EQ band {band}. Must be 1–4."
        try:
            ch = str(channel).zfill(2)
            param = float(await connection.get_parameter(f"/ch/{ch}/eq/{band}/q"))
            q = _param_to_q(param)
            return f"Channel {channel} EQ band {band} Q: {q:.2f}"
        except Exception as e:
            return f"Failed to get EQ Q: {e}"

    @mcp.tool(
        name="channel_get_eq_band",
        description=(
            "Get all EQ parameters (gain, frequency, Q, type) for a specific band on an input channel. "
            "Returns a summary of the full band settings."
        ),
    )
    async def channel_get_eq_band(channel: int, band: int) -> str:
        """
        Args:
            channel: Input channel number from 1 to 32
            band: EQ band number from 1 to 4
        """
        if not connection.connected:
            return X32Error.not_connected()
        if channel < 1 or channel > 32:
            return X32Error.invalid_channel(channel)
        if band < 1 or band > 4:
            return f"Invalid EQ band {band}. Must be 1–4."
        try:
            ch = str(channel).zfill(2)
            g_param = float(await connection.get_parameter(f"/ch/{ch}/eq/{band}/g"))
            f_param = float(await connection.get_parameter(f"/ch/{ch}/eq/{band}/f"))
            q_param = float(await connection.get_parameter(f"/ch/{ch}/eq/{band}/q"))
            t_param = int(await connection.get_parameter(f"/ch/{ch}/eq/{band}/type"))
            gain_db = _param_to_gain_db(g_param)
            freq_hz = _param_to_freq(f_param)
            q_val = _param_to_q(q_param)
            band_type = _BAND_TYPES.get(t_param, str(t_param))
            freq_display = f"{freq_hz:.0f} Hz" if freq_hz < 1000 else f"{freq_hz / 1000:.2f} kHz"
            return (
                f"Channel {channel} EQ band {band}: "
                f"type={band_type}, freq={freq_display}, gain={gain_db:+.1f} dB, Q={q_val:.2f}"
            )
        except Exception as e:
            return f"Failed to get EQ band info: {e}"