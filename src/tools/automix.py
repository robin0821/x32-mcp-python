"""
Automix domain tools
Implements automixing functionality based on X32Automix.c by Patrick-Gilles Maillot.

Logic overview:
- Reads channel meter levels (/meters/1) for channels in the configured range
- If a channel level exceeds the threshold: raise its fader to the pre-recorded "high" value
  and record the time of the last active event
- If a channel level falls below the threshold AND the hold-time has expired:
  lower its fader to the pre-recorded "low" value
- NOM (Number Of Mics): adjusts the overall mix (LR or a bus) by ±3 dB each time
  the number of active channels doubles or halves
- Fader low/high values are learned automatically: whenever a fader is moved while the
  channel is in its current state (high or low), that value becomes the new preset
"""

import asyncio
import math
import struct
import time
from dataclasses import dataclass, field
from typing import Optional

from mcp.server.fastmcp import FastMCP
from src.services.x32_connection import X32Connection
from src.utils.error_helper import X32Error

# ---------------------------------------------------------------------------
# Automix state – one shared instance per server process
# ---------------------------------------------------------------------------

@dataclass
class ChannelState:
    """Per-channel automix state."""
    fader_low: float = 0.0          # pre-recorded low fader value  (linear 0..1)
    fader_high: float = 0.75        # pre-recorded high fader value (linear 0..1, ~0 dB)
    is_active: bool = False         # True when channel is "up" / above threshold
    last_active_ts: float = 0.0     # epoch time of last above-threshold meter read


@dataclass
class AutomixConfig:
    """Automix configuration parameters."""
    ch_start: int = 1               # first channel to monitor (1-based)
    ch_stop: int = 32               # last channel to monitor  (1-based)
    threshold: float = 0.005        # meter level threshold (linear)
    hold_time: float = 5.0          # seconds to wait before lowering fader
    use_bus: bool = False           # True = control a bus; False = control main L/R
    bus_num: int = 1                # bus number when use_bus=True (1-16)
    nom_enabled: bool = False       # NOM (Number Of Mics) feature
    # Runtime NOM bookkeeping
    nom_active_ch: int = 0
    nom_old_active_ch: int = 0
    nom_act_ch_saved: int = 1


@dataclass
class AutomixState:
    """Complete automix runtime state."""
    config: AutomixConfig = field(default_factory=AutomixConfig)
    channels: list[ChannelState] = field(
        default_factory=lambda: [ChannelState() for _ in range(32)]
    )
    running: bool = False
    cycle_count: int = 0


# Module-level singleton
_state = AutomixState()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fader_to_db(v: float) -> float:
    """Convert linear fader value [0..1] to dB (X32 4-range curve)."""
    if v >= 0.5:
        return v * 40.0 - 30.0
    elif v >= 0.25:
        return v * 80.0 - 50.0
    elif v >= 0.0625:
        return v * 160.0 - 70.0
    else:
        return v * 480.0 - 90.0


def _db_to_fader(db: float) -> float:
    """Convert dB to linear fader value [0..1] (X32 4-range curve)."""
    db = max(-90.0, min(10.0, db))
    if db < -60.0:
        f = (db + 90.0) / 480.0
    elif db < -30.0:
        f = (db + 70.0) / 160.0
    elif db < -10.0:
        f = (db + 50.0) / 80.0
    else:
        f = (db + 30.0) / 40.0
    # round to nearest 1/1024 (matches C code: roundf(f * 1024) / 1024)
    f = round(f * 1024) / 1024
    return max(0.0, min(1.0, f))


def _format_fader(v: float) -> str:
    db = _fader_to_db(v)
    return f"{db:+.1f} dB (linear {v:.3f})"


async def _request_channel_meters(connection: X32Connection) -> Optional[list[float]]:
    """
    Request /meters/1 (96 floats: 32 levels + 32 gate GR + 32 dyn GR).
    Meter blob floats are little-endian 32-bit IEEE 754.
    Returns None on timeout or decode failure.
    """
    try:
        # Send:  /meters ,siii /meters/1 0 0 0
        # The meter address is /meters, the string arg selects the bank.
        response = await connection.send_message(
            "/meters",
            ["/meters/1", 0, 0, 0],
            wait_for_reply=True,
        )
        if response is None:
            return None
        # Look for blob argument
        for arg in response.args:
            if arg.type == "b" and isinstance(arg.value, (bytes, bytearray)):
                blob: bytes = bytes(arg.value)
                # blob: first 4 bytes = count (little-endian int32)
                if len(blob) < 4:
                    return None
                count = struct.unpack_from("<i", blob, 0)[0]
                floats: list[float] = []
                offset = 4
                for _ in range(count):
                    if offset + 4 > len(blob):
                        break
                    (fv,) = struct.unpack_from("<f", blob, offset)
                    floats.append(fv)
                    offset += 4
                return floats if floats else None
        return None
    except Exception:
        return None


async def _set_channel_fader(connection: X32Connection, channel: int, value: float) -> None:
    """Set the main fader for a 1-based channel index."""
    ch = str(channel).zfill(2)
    await connection.set_parameter(f"/ch/{ch}/mix/fader", float(value))


async def _get_channel_fader(connection: X32Connection, channel: int) -> float:
    """Get the main fader for a 1-based channel index."""
    ch = str(channel).zfill(2)
    result = await connection.get_parameter(f"/ch/{ch}/mix/fader")
    return float(result)


def _mix_address(config: AutomixConfig) -> str:
    """Return the OSC address for the overall-mix fader."""
    if config.use_bus:
        bus = str(config.bus_num).zfill(2)
        return f"/bus/{bus}/mix/fader"
    return "/main/st/mix/fader"


async def _adjust_mix_db(connection: X32Connection, config: AutomixConfig, delta_db: float) -> None:
    """Add delta_db to the main-mix or bus-mix fader (NOM adjustment)."""
    addr = _mix_address(config)
    try:
        current = float(await connection.get_parameter(addr))
        db_now = _fader_to_db(current)
        db_new = max(-90.0, min(10.0, db_now + delta_db))
        new_val = _db_to_fader(db_new)
        await connection.set_parameter(addr, new_val)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Tool registration
# ---------------------------------------------------------------------------

def register_automix_tools(mcp: FastMCP, connection: X32Connection) -> None:
    """Register all automix domain tools."""

    # ------------------------------------------------------------------
    # Configure
    # ------------------------------------------------------------------
    @mcp.tool(
        name="automix_configure",
        description=(
            "Configure the automix engine parameters. "
            "Call this before running automix cycles. "
            "Parameters control which channels are monitored, the signal threshold, "
            "hold time before a channel is lowered, and whether NOM (Number Of Mics) "
            "gain compensation is applied to the main LR or a specific bus."
        ),
    )
    async def automix_configure(
        ch_start: int = 1,
        ch_stop: int = 32,
        threshold: float = 0.005,
        hold_time: float = 5.0,
        use_bus: bool = False,
        bus_num: int = 1,
        nom_enabled: bool = False,
    ) -> str:
        """
        Args:
            ch_start:    First channel to include in automix (1-32). Default 1.
            ch_stop:     Last channel to include in automix (1-32). Default 32.
            threshold:   Linear meter level above which a channel is considered active.
                         Default 0.005 (~-46 dBFS). Increase to reduce sensitivity.
            hold_time:   Seconds to hold a channel at its high fader value after the
                         signal drops below threshold before lowering it. Default 5.0.
            use_bus:     If True, NOM compensation targets a mix bus instead of main LR.
            bus_num:     Bus number (1-16) when use_bus is True. Default 1.
            nom_enabled: Enable NOM (Number Of Mics) automatic gain compensation.
                         Adjusts overall mix -3 dB when active count doubles,
                         +3 dB when active count halves. Default False.
        """
        if ch_start < 1 or ch_start > 32:
            return "ch_start must be between 1 and 32."
        if ch_stop < 1 or ch_stop > 32:
            return "ch_stop must be between 1 and 32."
        if ch_start > ch_stop:
            return "ch_start must be <= ch_stop."
        if threshold < 0.0 or threshold > 1.0:
            return "threshold must be between 0.0 and 1.0."
        if hold_time < 0.0:
            return "hold_time must be >= 0."
        if use_bus and (bus_num < 1 or bus_num > 16):
            return "bus_num must be between 1 and 16."

        cfg = _state.config
        cfg.ch_start = ch_start
        cfg.ch_stop = ch_stop
        cfg.threshold = threshold
        cfg.hold_time = hold_time
        cfg.use_bus = use_bus
        cfg.bus_num = bus_num
        cfg.nom_enabled = nom_enabled
        cfg.nom_active_ch = 0
        cfg.nom_old_active_ch = 0
        cfg.nom_act_ch_saved = 1

        mix_target = f"bus {bus_num}" if use_bus else "main L/R"
        return "\n".join([
            "Automix configured:",
            f"  Channels   : {ch_start} – {ch_stop}",
            f"  Threshold  : {threshold:.4f} (linear)",
            f"  Hold time  : {hold_time:.1f} s",
            f"  NOM        : {'enabled' if nom_enabled else 'disabled'}",
            f"  Mix target : {mix_target}",
        ])

    # ------------------------------------------------------------------
    # Set fader presets for a channel
    # ------------------------------------------------------------------
    @mcp.tool(
        name="automix_set_fader_low",
        description=(
            "Set the pre-recorded 'low' (inactive) fader position for a channel in the "
            "automix engine. When a channel drops below the threshold and its hold time "
            "has expired, the automix will move the fader to this value. "
            "Accepts a linear value (0.0–1.0) or a dB value."
        ),
    )
    async def automix_set_fader_low(channel: int, value: float, unit: str = "linear") -> str:
        """
        Args:
            channel: Input channel number (1-32).
            value:   Fader level.
            unit:    "linear" (0.0-1.0) or "db" (-90 to +10). Default "linear".
        """
        if channel < 1 or channel > 32:
            return X32Error.invalid_channel(channel)
        if unit == "db":
            if value < -90 or value > 10:
                return X32Error.invalid_db(value)
            fv = _db_to_fader(value)
        else:
            if value < 0 or value > 1:
                return X32Error.invalid_linear(value)
            fv = value
        _state.channels[channel - 1].fader_low = fv
        return f"Channel {channel} low fader set to {_format_fader(fv)}"

    @mcp.tool(
        name="automix_set_fader_high",
        description=(
            "Set the pre-recorded 'high' (active) fader position for a channel in the "
            "automix engine. When a channel rises above the threshold, the automix will "
            "move the fader to this value. "
            "Accepts a linear value (0.0–1.0) or a dB value."
        ),
    )
    async def automix_set_fader_high(channel: int, value: float, unit: str = "linear") -> str:
        """
        Args:
            channel: Input channel number (1-32).
            value:   Fader level.
            unit:    "linear" (0.0-1.0) or "db" (-90 to +10). Default "linear".
        """
        if channel < 1 or channel > 32:
            return X32Error.invalid_channel(channel)
        if unit == "db":
            if value < -90 or value > 10:
                return X32Error.invalid_db(value)
            fv = _db_to_fader(value)
        else:
            if value < 0 or value > 1:
                return X32Error.invalid_linear(value)
            fv = value
        _state.channels[channel - 1].fader_high = fv
        return f"Channel {channel} high fader set to {_format_fader(fv)}"

    @mcp.tool(
        name="automix_learn_faders_from_mixer",
        description=(
            "Read the current fader positions from the mixer for all configured channels "
            "and store them as either 'high' or 'low' presets depending on each channel's "
            "current active state. Mirrors the 'learn' behaviour of X32Automix.c where "
            "manually moving a fader while the channel is in its current state updates "
            "the corresponding preset."
        ),
    )
    async def automix_learn_faders_from_mixer(preset: str = "auto") -> str:
        """
        Args:
            preset: Which preset to update for all channels: "low", "high", or "auto"
                    (uses each channel's current active state to decide). Default "auto".
        """
        if not connection.connected:
            return X32Error.not_connected()
        if preset not in ("low", "high", "auto"):
            return "preset must be 'low', 'high', or 'auto'."

        cfg = _state.config
        results: list[str] = []
        errors: list[str] = []

        for ch_idx in range(cfg.ch_start - 1, cfg.ch_stop):
            channel = ch_idx + 1
            try:
                fv = await _get_channel_fader(connection, channel)
                cs = _state.channels[ch_idx]
                if preset == "high" or (preset == "auto" and cs.is_active):
                    cs.fader_high = fv
                    results.append(f"  ch {channel:02d} HIGH <- {_format_fader(fv)}")
                else:
                    cs.fader_low = fv
                    results.append(f"  ch {channel:02d} LOW  <- {_format_fader(fv)}")
            except Exception as e:
                errors.append(f"  ch {channel:02d} error: {e}")

        lines = [f"Learned fader presets (preset={preset}):"] + results
        if errors:
            lines += ["Errors:"] + errors
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Run one automix cycle
    # ------------------------------------------------------------------
    @mcp.tool(
        name="automix_run_cycle",
        description=(
            "Execute a single automix processing cycle: read the channel meter levels from "
            "the mixer, compare each monitored channel against the threshold, raise or lower "
            "faders as needed, and apply NOM gain compensation if enabled. "
            "Returns a summary of all fader changes made during this cycle. "
            "Call this tool repeatedly (e.g. every 50–500 ms) to run continuous automixing."
        ),
    )
    async def automix_run_cycle() -> str:
        """Run one automix cycle (read meters → compare → adjust faders)."""
        if not connection.connected:
            return X32Error.not_connected()

        cfg = _state.config
        now = time.monotonic()

        # Request meter bank 1 (first 32 floats = input channel pre-fader levels)
        meter_floats = await _request_channel_meters(connection)
        if meter_floats is None:
            return (
                "Automix cycle: could not read meter data from mixer "
                "(timeout or connection error). Cycle skipped."
            )

        changes: list[str] = []
        active_count = 0

        for ch_idx in range(cfg.ch_start - 1, cfg.ch_stop):
            channel = ch_idx + 1
            cs = _state.channels[ch_idx]
            level = meter_floats[ch_idx] if ch_idx < len(meter_floats) else 0.0

            if level > cfg.threshold:
                # Channel is active – update last-active timestamp
                cs.last_active_ts = now
                if not cs.is_active:
                    # Transition: inactive → active → raise fader
                    cs.is_active = True
                    cfg.nom_active_ch += 1
                    try:
                        await _set_channel_fader(connection, channel, cs.fader_high)
                        changes.append(
                            f"  ch {channel:02d}  ↑ ACTIVE   fader → {_format_fader(cs.fader_high)}"
                            f"  (meter {level:.4f})"
                        )
                    except Exception as e:
                        changes.append(f"  ch {channel:02d}  ↑ ACTIVE   fader set failed: {e}")
                active_count += 1
            else:
                # Channel is quiet
                if cs.is_active:
                    # Still in hold period?
                    if (cs.last_active_ts + cfg.hold_time) < now:
                        # Hold expired → lower fader
                        cs.is_active = False
                        cfg.nom_active_ch = max(0, cfg.nom_active_ch - 1)
                        try:
                            await _set_channel_fader(connection, channel, cs.fader_low)
                            changes.append(
                                f"  ch {channel:02d}  ↓ INACTIVE fader → {_format_fader(cs.fader_low)}"
                                f"  (meter {level:.4f})"
                            )
                        except Exception as e:
                            changes.append(f"  ch {channel:02d}  ↓ INACTIVE fader set failed: {e}")
                    else:
                        hold_remaining = (cs.last_active_ts + cfg.hold_time) - now
                        active_count += 1   # still counted as active during hold
                        changes.append(
                            f"  ch {channel:02d}  ⏳ HOLD     {hold_remaining:.1f}s remaining"
                            f"  (meter {level:.4f})"
                        )

        # NOM processing
        nom_changes: list[str] = []
        if cfg.nom_enabled:
            if cfg.nom_active_ch != cfg.nom_old_active_ch:
                if cfg.nom_active_ch >= cfg.nom_act_ch_saved * 2:
                    await _adjust_mix_db(connection, cfg, -3.0)
                    cfg.nom_act_ch_saved = min(32, cfg.nom_act_ch_saved * 2)
                    nom_changes.append(
                        f"  NOM: active channels doubled to {cfg.nom_active_ch} → mix -3 dB"
                    )
                elif cfg.nom_active_ch <= cfg.nom_act_ch_saved // 2:
                    if cfg.nom_active_ch > 0:
                        await _adjust_mix_db(connection, cfg, +3.0)
                        nom_changes.append(
                            f"  NOM: active channels halved to {cfg.nom_active_ch} → mix +3 dB"
                        )
                    cfg.nom_act_ch_saved = max(1, cfg.nom_act_ch_saved // 2)
                cfg.nom_old_active_ch = cfg.nom_active_ch

        _state.cycle_count += 1

        lines = [
            f"Automix cycle #{_state.cycle_count}: "
            f"{active_count} active / {cfg.ch_stop - cfg.ch_start + 1} monitored channels"
        ]
        if changes:
            lines += ["Fader changes:"] + changes
        else:
            lines.append("  No fader changes this cycle.")
        if nom_changes:
            lines += nom_changes
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Run multiple cycles with a sleep interval
    # ------------------------------------------------------------------
    @mcp.tool(
        name="automix_run_cycles",
        description=(
            "Run multiple consecutive automix cycles with a configurable interval between "
            "them. Useful for applying automixing over a short burst rather than calling "
            "automix_run_cycle individually. Returns a summary after all cycles complete."
        ),
    )
    async def automix_run_cycles(count: int = 10, interval_ms: int = 100) -> str:
        """
        Args:
            count:       Number of cycles to run. Default 10.
            interval_ms: Milliseconds to wait between cycles (10–5000). Default 100.
        """
        if not connection.connected:
            return X32Error.not_connected()
        if count < 1 or count > 200:
            return "count must be between 1 and 200."
        if interval_ms < 10 or interval_ms > 5000:
            return "interval_ms must be between 10 and 5000."

        cfg = _state.config
        total_changes = 0
        total_activations = 0
        total_deactivations = 0

        for i in range(count):
            now = time.monotonic()
            meter_floats = await _request_channel_meters(connection)
            if meter_floats is None:
                if i < count - 1:
                    await asyncio.sleep(interval_ms / 1000.0)
                continue

            for ch_idx in range(cfg.ch_start - 1, cfg.ch_stop):
                channel = ch_idx + 1
                cs = _state.channels[ch_idx]
                level = meter_floats[ch_idx] if ch_idx < len(meter_floats) else 0.0

                if level > cfg.threshold:
                    cs.last_active_ts = now
                    if not cs.is_active:
                        cs.is_active = True
                        cfg.nom_active_ch += 1
                        total_activations += 1
                        total_changes += 1
                        try:
                            await _set_channel_fader(connection, channel, cs.fader_high)
                        except Exception:
                            pass
                else:
                    if cs.is_active and (cs.last_active_ts + cfg.hold_time) < now:
                        cs.is_active = False
                        cfg.nom_active_ch = max(0, cfg.nom_active_ch - 1)
                        total_deactivations += 1
                        total_changes += 1
                        try:
                            await _set_channel_fader(connection, channel, cs.fader_low)
                        except Exception:
                            pass

            # NOM
            if cfg.nom_enabled and cfg.nom_active_ch != cfg.nom_old_active_ch:
                if cfg.nom_active_ch >= cfg.nom_act_ch_saved * 2:
                    await _adjust_mix_db(connection, cfg, -3.0)
                    cfg.nom_act_ch_saved = min(32, cfg.nom_act_ch_saved * 2)
                elif cfg.nom_active_ch <= cfg.nom_act_ch_saved // 2 and cfg.nom_active_ch > 0:
                    await _adjust_mix_db(connection, cfg, +3.0)
                    cfg.nom_act_ch_saved = max(1, cfg.nom_act_ch_saved // 2)
                cfg.nom_old_active_ch = cfg.nom_active_ch

            _state.cycle_count += 1
            if i < count - 1:
                await asyncio.sleep(interval_ms / 1000.0)

        active_now = sum(1 for cs in _state.channels if cs.is_active)
        return "\n".join([
            f"Automix: completed {count} cycles ({interval_ms} ms interval).",
            f"  Total fader changes  : {total_changes}",
            f"  Channel activations  : {total_activations}",
            f"  Channel deactivations: {total_deactivations}",
            f"  Currently active     : {active_now} channel(s)",
            f"  Total cycles run     : {_state.cycle_count}",
        ])

    # ------------------------------------------------------------------
    # Get status
    # ------------------------------------------------------------------
    @mcp.tool(
        name="automix_get_status",
        description=(
            "Get the current state of the automix engine: configuration, per-channel "
            "active/inactive state, fader presets, and cycle counters."
        ),
    )
    async def automix_get_status() -> str:
        cfg = _state.config
        mix_target = f"bus {cfg.bus_num}" if cfg.use_bus else "main L/R"
        lines = [
            "=== Automix Status ===",
            f"  Channels   : {cfg.ch_start} – {cfg.ch_stop}",
            f"  Threshold  : {cfg.threshold:.4f} (linear)",
            f"  Hold time  : {cfg.hold_time:.1f} s",
            f"  NOM        : {'enabled' if cfg.nom_enabled else 'disabled'}",
            f"  Mix target : {mix_target}",
            f"  Total cycles: {_state.cycle_count}",
            "",
            "Channel presets and state:",
            f"  {'CH':>3}  {'State':>8}  {'Low fader':>14}  {'High fader':>14}",
        ]
        for ch_idx in range(cfg.ch_start - 1, cfg.ch_stop):
            ch = ch_idx + 1
            cs = _state.channels[ch_idx]
            state_str = "ACTIVE" if cs.is_active else "inactive"
            lines.append(
                f"  {ch:>3}  {state_str:>8}  "
                f"{_format_fader(cs.fader_low):>14}  "
                f"{_format_fader(cs.fader_high):>14}"
            )
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------
    @mcp.tool(
        name="automix_reset",
        description=(
            "Reset the automix engine state: clears all channel active flags, "
            "resets NOM counters, and optionally resets the fader presets to defaults "
            "(low=0.0, high=0.75). Does not change the configuration parameters."
        ),
    )
    async def automix_reset(reset_fader_presets: bool = False) -> str:
        """
        Args:
            reset_fader_presets: If True, also reset low/high fader presets to defaults.
                                 Default False.
        """
        for cs in _state.channels:
            cs.is_active = False
            cs.last_active_ts = 0.0
            if reset_fader_presets:
                cs.fader_low = 0.0
                cs.fader_high = 0.75

        _state.config.nom_active_ch = 0
        _state.config.nom_old_active_ch = 0
        _state.config.nom_act_ch_saved = 1
        _state.cycle_count = 0

        msg = "Automix state reset."
        if reset_fader_presets:
            msg += " Fader presets restored to defaults (low=0.0, high=0.75)."
        return msg
