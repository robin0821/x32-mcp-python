"""
USB domain tools
Semantic, task-based tools for X32/M32 USB recording and playback control.

Logic references:
  https://github.com/pmaillot/X32-Behringer/blob/master/X32USB.c

OSC addresses used:
  /-stat/usbmounted          int  0=not mounted, 1=mounted
  /-stat/usbrecord           int  0=stopped, 1=recording
  /-stat/usbplay             int  0=stopped/paused, 1=playing

  /-action/usbrecord         int  1=start recording, 0=stop recording
  /-action/usbplay           int  1=start/resume play, 0=pause/stop
  /-action/usbrwinding       int  1=rewind
  /-action/usbffwinding      int  1=fast-forward
  /-action/usbnextsong       int  1=next track
  /-action/usbprevsong       int  1=previous track

  /urec/input/source         int  0=MainLR, 1-8=Aux1-8, 9-14=P16 1-16(pairs), 15-16=Out1-8(pairs)
  /urec/input/gain           float 0.0-1.0  input trim
  /urec/output/gain          float 0.0-1.0  playback output trim
  /urec/output/track         int  0-based track index
  /urec/output/mode          int  0=single, 1=folder, 2=repeat
"""

from mcp.server.fastmcp import FastMCP
from src.services.x32_connection import X32Connection
from src.utils.db_converter import db_to_fader, fader_to_db, format_db
from src.utils.error_helper import X32Error

# Source index → human-readable name (matches X32USB.c enum)
_RECORD_SOURCES: dict[int, str] = {
    0: "Main L+R",
    1: "Aux 1",
    2: "Aux 2",
    3: "Aux 3",
    4: "Aux 4",
    5: "Aux 5",
    6: "Aux 6",
    7: "Aux 7",
    8: "Aux 8",
    9: "P16 1-2",
    10: "P16 3-4",
    11: "P16 5-6",
    12: "P16 7-8",
    13: "P16 9-10",
    14: "P16 11-12",
    15: "Out 1-2",
    16: "Out 3-4",
}

_PLAYBACK_MODES: dict[int, str] = {
    0: "single",
    1: "folder",
    2: "repeat",
}
_PLAYBACK_MODE_BY_NAME: dict[str, int] = {v: k for k, v in _PLAYBACK_MODES.items()}


def _source_name(idx: int) -> str:
    return _RECORD_SOURCES.get(idx, f"unknown ({idx})")


def _mode_name(idx: int) -> str:
    return _PLAYBACK_MODES.get(idx, f"unknown ({idx})")


def register_usb_tools(mcp: FastMCP, connection: X32Connection) -> None:
    """Register all USB recording/playback domain tools."""

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------
    @mcp.tool(
        name="usb_get_status",
        description=(
            "Get a full status snapshot of the USB recorder/player on the X32/M32 mixer. "
            "Returns mount state, record state, play state, recording source, "
            "input/output trim gains, active track index, and playback mode."
        ),
    )
    async def usb_get_status() -> str:
        if not connection.connected:
            return X32Error.not_connected()
        try:
            mounted_raw = await connection.get_parameter("/-stat/usbmounted")
            record_raw = await connection.get_parameter("/-stat/usbrecord")
            play_raw = await connection.get_parameter("/-stat/usbplay")

            mounted = int(mounted_raw) != 0
            recording = int(record_raw) != 0
            playing = int(play_raw) != 0

            source_raw = await connection.get_parameter("/urec/input/source")
            in_gain_raw = await connection.get_parameter("/urec/input/gain")
            out_gain_raw = await connection.get_parameter("/urec/output/gain")
            track_raw = await connection.get_parameter("/urec/output/track")
            mode_raw = await connection.get_parameter("/urec/output/mode")

            source_idx = int(source_raw)
            in_gain = float(in_gain_raw)
            out_gain = float(out_gain_raw)
            track_idx = int(track_raw)
            mode_idx = int(mode_raw)

            lines = [
                "=== USB Recorder/Player Status ===",
                f"  USB Mounted    : {'Yes' if mounted else 'No'}",
                f"  Recording      : {'Yes' if recording else 'No'}",
                f"  Playing        : {'Yes' if playing else 'No'}",
                f"  Record Source  : {_source_name(source_idx)} (index {source_idx})",
                f"  Input Gain     : {format_db(fader_to_db(in_gain))} (linear {in_gain:.3f})",
                f"  Output Gain    : {format_db(fader_to_db(out_gain))} (linear {out_gain:.3f})",
                f"  Active Track   : {track_idx}",
                f"  Playback Mode  : {_mode_name(mode_idx)} (index {mode_idx})",
            ]
            return "\n".join(lines)
        except Exception as e:
            return f"Failed to get USB status: {e}"

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------
    @mcp.tool(
        name="usb_record_start",
        description=(
            "Start USB recording on the X32/M32 mixer. "
            "Sends /-action/usbrecord with value 1. "
            "A USB drive must be mounted and the mixer must not already be recording."
        ),
    )
    async def usb_record_start() -> str:
        if not connection.connected:
            return X32Error.not_connected()
        try:
            # Check mount and record state
            mounted_raw = await connection.get_parameter("/-stat/usbmounted")
            if int(mounted_raw) == 0:
                return "Cannot start recording: no USB drive is mounted."
            record_raw = await connection.get_parameter("/-stat/usbrecord")
            if int(record_raw) != 0:
                return "USB recording is already in progress."

            await connection.set_parameter("/-action/usbrecord", 1)
            return "USB recording started."
        except Exception as e:
            return f"Failed to start USB recording: {e}"

    @mcp.tool(
        name="usb_record_stop",
        description=(
            "Stop USB recording on the X32/M32 mixer. "
            "Sends /-action/usbrecord with value 0."
        ),
    )
    async def usb_record_stop() -> str:
        if not connection.connected:
            return X32Error.not_connected()
        try:
            await connection.set_parameter("/-action/usbrecord", 0)
            return "USB recording stopped."
        except Exception as e:
            return f"Failed to stop USB recording: {e}"

    # ------------------------------------------------------------------
    # Playback transport
    # ------------------------------------------------------------------
    @mcp.tool(
        name="usb_play",
        description=(
            "Start or resume USB playback on the X32/M32 mixer. "
            "Sends /-action/usbplay with value 1."
        ),
    )
    async def usb_play() -> str:
        if not connection.connected:
            return X32Error.not_connected()
        try:
            mounted_raw = await connection.get_parameter("/-stat/usbmounted")
            if int(mounted_raw) == 0:
                return "Cannot start playback: no USB drive is mounted."
            await connection.set_parameter("/-action/usbplay", 1)
            return "USB playback started."
        except Exception as e:
            return f"Failed to start USB playback: {e}"

    @mcp.tool(
        name="usb_pause",
        description=(
            "Pause USB playback on the X32/M32 mixer. "
            "Sends /-action/usbplay with value 0."
        ),
    )
    async def usb_pause() -> str:
        if not connection.connected:
            return X32Error.not_connected()
        try:
            await connection.set_parameter("/-action/usbplay", 0)
            return "USB playback paused."
        except Exception as e:
            return f"Failed to pause USB playback: {e}"

    @mcp.tool(
        name="usb_rewind",
        description=(
            "Rewind to the beginning of the current track on the X32/M32 mixer. "
            "Sends /-action/usbrwinding with value 1."
        ),
    )
    async def usb_rewind() -> str:
        if not connection.connected:
            return X32Error.not_connected()
        try:
            await connection.set_parameter("/-action/usbrwinding", 1)
            return "USB rewinding to start of track."
        except Exception as e:
            return f"Failed to rewind USB: {e}"

    @mcp.tool(
        name="usb_fast_forward",
        description=(
            "Fast-forward on the X32/M32 mixer USB player. "
            "Sends /-action/usbffwinding with value 1."
        ),
    )
    async def usb_fast_forward() -> str:
        if not connection.connected:
            return X32Error.not_connected()
        try:
            await connection.set_parameter("/-action/usbffwinding", 1)
            return "USB fast-forwarding."
        except Exception as e:
            return f"Failed to fast-forward USB: {e}"

    @mcp.tool(
        name="usb_next_track",
        description=(
            "Skip to the next track on the X32/M32 mixer USB player. "
            "Sends /-action/usbnextsong with value 1."
        ),
    )
    async def usb_next_track() -> str:
        if not connection.connected:
            return X32Error.not_connected()
        try:
            await connection.set_parameter("/-action/usbnextsong", 1)
            return "USB skipped to next track."
        except Exception as e:
            return f"Failed to skip to next USB track: {e}"

    @mcp.tool(
        name="usb_prev_track",
        description=(
            "Skip to the previous track on the X32/M32 mixer USB player. "
            "Sends /-action/usbprevsong with value 1."
        ),
    )
    async def usb_prev_track() -> str:
        if not connection.connected:
            return X32Error.not_connected()
        try:
            await connection.set_parameter("/-action/usbprevsong", 1)
            return "USB skipped to previous track."
        except Exception as e:
            return f"Failed to skip to previous USB track: {e}"

    # ------------------------------------------------------------------
    # Recording source
    # ------------------------------------------------------------------
    @mcp.tool(
        name="usb_set_record_source",
        description=(
            "Set the recording source for the X32/M32 USB recorder. "
            "Accepted values: 0=Main L+R, 1-8=Aux 1-8, 9-14=P16 pairs 1-12, 15-16=Out pairs 1-4. "
            "You may pass an integer index or a source name such as 'Main L+R', 'Aux 3', 'P16 1-2'."
        ),
    )
    async def usb_set_record_source(source: str) -> str:
        """
        Args:
            source: Source index (0-16) or name string (e.g. 'Main L+R', 'Aux 1', 'P16 1-2').
        """
        if not connection.connected:
            return X32Error.not_connected()

        # Try integer first
        source_idx: int | None = None
        try:
            source_idx = int(source)
        except ValueError:
            # Search by name (case-insensitive)
            source_lower = source.strip().lower()
            for idx, name in _RECORD_SOURCES.items():
                if name.lower() == source_lower:
                    source_idx = idx
                    break

        if source_idx is None or source_idx not in _RECORD_SOURCES:
            available = ", ".join(f"{k}={v}" for k, v in sorted(_RECORD_SOURCES.items()))
            return f"Invalid source '{source}'. Available: {available}"

        try:
            await connection.set_parameter("/urec/input/source", source_idx)
            return f"USB record source set to {_source_name(source_idx)} (index {source_idx})."
        except Exception as e:
            return f"Failed to set USB record source: {e}"

    @mcp.tool(
        name="usb_get_record_source",
        description="Get the current recording source for the X32/M32 USB recorder.",
    )
    async def usb_get_record_source() -> str:
        if not connection.connected:
            return X32Error.not_connected()
        try:
            raw = await connection.get_parameter("/urec/input/source")
            idx = int(raw)
            return f"USB record source: {_source_name(idx)} (index {idx})"
        except Exception as e:
            return f"Failed to get USB record source: {e}"

    # ------------------------------------------------------------------
    # Input / output gain
    # ------------------------------------------------------------------
    @mcp.tool(
        name="usb_set_record_gain",
        description=(
            "Set the input trim (gain) for the X32/M32 USB recorder. "
            "Accepts a linear value (0.0-1.0) or a dB value (-90 to +10). "
            "Unity is 0 dB / 0.75 linear."
        ),
    )
    async def usb_set_record_gain(value: float, unit: str = "linear") -> str:
        """
        Args:
            value: Gain value.
            unit:  'linear' (0.0-1.0) or 'db' (-90 to +10). Default 'linear'.
        """
        if not connection.connected:
            return X32Error.not_connected()
        if unit == "db":
            if value < -90 or value > 10:
                return X32Error.invalid_db(value)
            fader_value = db_to_fader(value)
            db_value = value
        else:
            if value < 0 or value > 1:
                return X32Error.invalid_linear(value)
            fader_value = value
            db_value = fader_to_db(value)
        try:
            await connection.set_parameter("/urec/input/gain", float(fader_value))
            return f"USB record input gain set to {format_db(db_value)} (linear {fader_value:.3f})."
        except Exception as e:
            return f"Failed to set USB record gain: {e}"

    @mcp.tool(
        name="usb_get_record_gain",
        description="Get the current input trim (gain) for the X32/M32 USB recorder.",
    )
    async def usb_get_record_gain() -> str:
        if not connection.connected:
            return X32Error.not_connected()
        try:
            raw = await connection.get_parameter("/urec/input/gain")
            fv = float(raw)
            return f"USB record input gain: {format_db(fader_to_db(fv))} (linear {fv:.3f})"
        except Exception as e:
            return f"Failed to get USB record gain: {e}"

    @mcp.tool(
        name="usb_set_playback_gain",
        description=(
            "Set the output trim (gain) for the X32/M32 USB player. "
            "Accepts a linear value (0.0-1.0) or a dB value (-90 to +10). "
            "Unity is 0 dB / 0.75 linear."
        ),
    )
    async def usb_set_playback_gain(value: float, unit: str = "linear") -> str:
        """
        Args:
            value: Gain value.
            unit:  'linear' (0.0-1.0) or 'db' (-90 to +10). Default 'linear'.
        """
        if not connection.connected:
            return X32Error.not_connected()
        if unit == "db":
            if value < -90 or value > 10:
                return X32Error.invalid_db(value)
            fader_value = db_to_fader(value)
            db_value = value
        else:
            if value < 0 or value > 1:
                return X32Error.invalid_linear(value)
            fader_value = value
            db_value = fader_to_db(value)
        try:
            await connection.set_parameter("/urec/output/gain", float(fader_value))
            return f"USB playback output gain set to {format_db(db_value)} (linear {fader_value:.3f})."
        except Exception as e:
            return f"Failed to set USB playback gain: {e}"

    @mcp.tool(
        name="usb_get_playback_gain",
        description="Get the current output trim (gain) for the X32/M32 USB player.",
    )
    async def usb_get_playback_gain() -> str:
        if not connection.connected:
            return X32Error.not_connected()
        try:
            raw = await connection.get_parameter("/urec/output/gain")
            fv = float(raw)
            return f"USB playback output gain: {format_db(fader_to_db(fv))} (linear {fv:.3f})"
        except Exception as e:
            return f"Failed to get USB playback gain: {e}"

    # ------------------------------------------------------------------
    # Track selection
    # ------------------------------------------------------------------
    @mcp.tool(
        name="usb_set_playback_track",
        description=(
            "Select a specific track for USB playback on the X32/M32 mixer. "
            "Track index is 0-based (0 = first track on the USB drive)."
        ),
    )
    async def usb_set_playback_track(track: int) -> str:
        """
        Args:
            track: 0-based track index.
        """
        if not connection.connected:
            return X32Error.not_connected()
        if track < 0:
            return "Track index must be >= 0."
        try:
            await connection.set_parameter("/urec/output/track", track)
            return f"USB playback track set to index {track}."
        except Exception as e:
            return f"Failed to set USB playback track: {e}"

    @mcp.tool(
        name="usb_get_playback_track",
        description="Get the current playback track index for the X32/M32 USB player (0-based).",
    )
    async def usb_get_playback_track() -> str:
        if not connection.connected:
            return X32Error.not_connected()
        try:
            raw = await connection.get_parameter("/urec/output/track")
            return f"USB playback track index: {int(raw)}"
        except Exception as e:
            return f"Failed to get USB playback track: {e}"

    # ------------------------------------------------------------------
    # Playback mode
    # ------------------------------------------------------------------
    @mcp.tool(
        name="usb_set_playback_mode",
        description=(
            "Set the playback mode for the X32/M32 USB player. "
            "Modes: 'single' (play one track and stop), "
            "'folder' (play all tracks in folder sequentially), "
            "'repeat' (loop current track or folder). "
            "You may also pass the numeric index: 0=single, 1=folder, 2=repeat."
        ),
    )
    async def usb_set_playback_mode(mode: str) -> str:
        """
        Args:
            mode: 'single', 'folder', 'repeat', or numeric index 0-2.
        """
        if not connection.connected:
            return X32Error.not_connected()

        mode_idx: int | None = None
        try:
            mode_idx = int(mode)
        except ValueError:
            mode_idx = _PLAYBACK_MODE_BY_NAME.get(mode.strip().lower())

        if mode_idx is None or mode_idx not in _PLAYBACK_MODES:
            available = ", ".join(f"'{n}' ({i})" for i, n in sorted(_PLAYBACK_MODES.items()))
            return f"Invalid mode '{mode}'. Available: {available}"

        try:
            await connection.set_parameter("/urec/output/mode", mode_idx)
            return f"USB playback mode set to '{_mode_name(mode_idx)}' (index {mode_idx})."
        except Exception as e:
            return f"Failed to set USB playback mode: {e}"

    @mcp.tool(
        name="usb_get_playback_mode",
        description="Get the current playback mode for the X32/M32 USB player.",
    )
    async def usb_get_playback_mode() -> str:
        if not connection.connected:
            return X32Error.not_connected()
        try:
            raw = await connection.get_parameter("/urec/output/mode")
            idx = int(raw)
            return f"USB playback mode: {_mode_name(idx)} (index {idx})"
        except Exception as e:
            return f"Failed to get USB playback mode: {e}"