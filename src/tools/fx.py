"""
FX domain tools
Semantic, task-based tools for FX rack control
"""

from mcp.server.fastmcp import FastMCP
from src.services.x32_connection import X32Connection
from src.utils.db_converter import db_to_fader, fader_to_db, format_db
from src.utils.error_helper import X32Error


def register_fx_tools(mcp: FastMCP, connection: X32Connection) -> None:
    """Register all FX domain tools."""

    @mcp.tool(
        name="fx_get_info",
        description=(
            "Get information about the current FX (effects) settings for a specific FX rack slot "
            "on the X32/M32 mixer. Returns the effect type and parameters."
        ),
    )
    async def fx_get_info(fx: int) -> str:
        """
        Args:
            fx: FX rack slot number from 1 to 8
        """
        if not connection.connected:
            return X32Error.not_connected()
        if fx < 1 or fx > 8:
            return X32Error.invalid_fx(fx)
        try:
            fx_num = str(fx).zfill(2)
            fx_type = await connection.get_parameter(f"/fx/{fx_num}/source")
            return f"FX {fx} source: {fx_type}"
        except Exception as e:
            return f"Failed to get FX info: {e}"

    @mcp.tool(
        name="fx_set_source",
        description=(
            "Set the source for a specific FX rack slot on the X32/M32 mixer. "
            "This determines what signal feeds into the FX processor."
        ),
    )
    async def fx_set_source(fx: int, source: int) -> str:
        """
        Args:
            fx: FX rack slot number from 1 to 8
            source: Source index value (0 = off, 1-64 = various sources)
        """
        if not connection.connected:
            return X32Error.not_connected()
        if fx < 1 or fx > 8:
            return X32Error.invalid_fx(fx)
        try:
            fx_num = str(fx).zfill(2)
            await connection.set_parameter(f"/fx/{fx_num}/source", source)
            return f"Set FX {fx} source to {source}"
        except Exception as e:
            return f"Failed to set FX source: {e}"

    @mcp.tool(
        name="fx_set_type",
        description=(
            "Set the effect type for a specific FX rack slot on the X32/M32 mixer. "
            "The type determines which DSP algorithm is used."
        ),
    )
    async def fx_set_type(fx: int, effect_type: int) -> str:
        """
        Args:
            fx: FX rack slot number from 1 to 8
            effect_type: Effect type index (see X32/M32 documentation for valid values)
        """
        if not connection.connected:
            return X32Error.not_connected()
        if fx < 1 or fx > 8:
            return X32Error.invalid_fx(fx)
        try:
            fx_num = str(fx).zfill(2)
            await connection.set_parameter(f"/fx/{fx_num}/source", effect_type)
            return f"Set FX {fx} type to {effect_type}"
        except Exception as e:
            return f"Failed to set FX type: {e}"

    @mcp.tool(
        name="fx_get_return_volume",
        description=(
            "Get the return level for a specific FX rack slot on the X32/M32 mixer."
        ),
    )
    async def fx_get_return_volume(fx: int) -> str:
        """
        Args:
            fx: FX rack slot number from 1 to 8
        """
        if not connection.connected:
            return X32Error.not_connected()
        if fx < 1 or fx > 8:
            return X32Error.invalid_fx(fx)
        try:
            fx_num = str(fx).zfill(2)
            fader = await connection.get_parameter(f"/fxrtn/{fx_num}/mix/fader")
            db_value = fader_to_db(float(fader))
            return f"FX {fx} return fader: {format_db(db_value)} (linear: {float(fader):.3f})"
        except Exception as e:
            return f"Failed to get FX return volume: {e}"

    @mcp.tool(
        name="fx_set_return_volume",
        description=(
            "Set the return level for a specific FX rack slot on the X32/M32 mixer. "
            "This controls how much of the wet FX signal is returned to the mix."
        ),
    )
    async def fx_set_return_volume(fx: int, value: float, unit: str = "linear") -> str:
        """
        Args:
            fx: FX rack slot number from 1 to 8
            value: Return level value
            unit: "linear" (0.0-1.0) or "db" (-90 to +10 dB). Default is "linear".
        """
        if not connection.connected:
            return X32Error.not_connected()
        if fx < 1 or fx > 8:
            return X32Error.invalid_fx(fx)
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
            fx_num = str(fx).zfill(2)
            await connection.set_parameter(f"/fxrtn/{fx_num}/mix/fader", fader_value)
            return f"Set FX {fx} return to {format_db(db_value)} (linear: {fader_value:.3f})"
        except Exception as e:
            return f"Failed to set FX return volume: {e}"

    @mcp.tool(
        name="fx_mute_return",
        description="Mute or unmute the return channel for a specific FX rack slot.",
    )
    async def fx_mute_return(fx: int, muted: bool) -> str:
        """
        Args:
            fx: FX rack slot number from 1 to 8
            muted: True to mute the FX return, False to unmute
        """
        if not connection.connected:
            return X32Error.not_connected()
        if fx < 1 or fx > 8:
            return X32Error.invalid_fx(fx)
        try:
            fx_num = str(fx).zfill(2)
            on_value = 0 if muted else 1
            await connection.set_parameter(f"/fxrtn/{fx_num}/mix/on", on_value)
            state = "muted" if muted else "unmuted"
            return f"FX {fx} return is now {state}"
        except Exception as e:
            return f"Failed to mute/unmute FX return: {e}"

    @mcp.tool(
        name="fx_set_on",
        description=(
            "Enable or disable an FX insert block on the X32/M32 mixer. "
            "When disabled, the effect is bypassed."
        ),
    )
    async def fx_set_on(fx: int, on: bool) -> str:
        """
        Args:
            fx: FX rack slot number from 1 to 8
            on: True to enable the effect, False to bypass/disable
        """
        if not connection.connected:
            return X32Error.not_connected()
        if fx < 1 or fx > 8:
            return X32Error.invalid_fx(fx)
        try:
            fx_num = str(fx).zfill(2)
            await connection.set_parameter(f"/fx/{fx_num}/on", 1 if on else 0)
            state = "enabled" if on else "disabled"
            return f"FX {fx} is now {state}"
        except Exception as e:
            return f"Failed to set FX on/off: {e}"

    @mcp.tool(
        name="fx_set_mix",
        description=(
            "Set the wet/dry mix level for an FX slot on the X32/M32 mixer. "
            "0.0 = fully dry (no effect), 1.0 = fully wet (full effect)."
        ),
    )
    async def fx_set_mix(fx: int, mix: float) -> str:
        """
        Args:
            fx: FX rack slot number from 1 to 8
            mix: Wet/dry mix level from 0.0 (dry) to 1.0 (wet)
        """
        if not connection.connected:
            return X32Error.not_connected()
        if fx < 1 or fx > 8:
            return X32Error.invalid_fx(fx)
        if mix < 0.0 or mix > 1.0:
            return X32Error.invalid_linear(mix)
        try:
            fx_num = str(fx).zfill(2)
            await connection.set_parameter(f"/fx/{fx_num}/mix", mix)
            return f"FX {fx} mix set to {mix:.3f} ({mix * 100:.0f}% wet)"
        except Exception as e:
            return f"Failed to set FX mix: {e}"

    @mcp.tool(
        name="fx_set_param",
        description=(
            "Set a specific parameter value for an FX slot on the X32/M32 mixer. "
            "Parameters are effect-specific (see X32/M32 documentation for parameter lists). "
            "Parameter numbers are 1-based (1 to 16)."
        ),
    )
    async def fx_set_param(fx: int, param: int, value: float) -> str:
        """
        Args:
            fx: FX rack slot number from 1 to 8
            param: Parameter number from 1 to 16
            value: Parameter value from 0.0 to 1.0
        """
        if not connection.connected:
            return X32Error.not_connected()
        if fx < 1 or fx > 8:
            return X32Error.invalid_fx(fx)
        if param < 1 or param > 16:
            return f"Invalid parameter number {param}. Must be 1–16."
        if value < 0.0 or value > 1.0:
            return X32Error.invalid_linear(value)
        try:
            fx_num = str(fx).zfill(2)
            par_num = str(param).zfill(2)
            await connection.set_parameter(f"/fx/{fx_num}/par/{par_num}", value)
            return f"FX {fx} parameter {param} set to {value:.3f}"
        except Exception as e:
            return f"Failed to set FX parameter: {e}"

    @mcp.tool(
        name="fx_get_param",
        description=(
            "Get the current value of a specific parameter for an FX slot on the X32/M32 mixer."
        ),
    )
    async def fx_get_param(fx: int, param: int) -> str:
        """
        Args:
            fx: FX rack slot number from 1 to 8
            param: Parameter number from 1 to 16
        """
        if not connection.connected:
            return X32Error.not_connected()
        if fx < 1 or fx > 8:
            return X32Error.invalid_fx(fx)
        if param < 1 or param > 16:
            return f"Invalid parameter number {param}. Must be 1–16."
        try:
            fx_num = str(fx).zfill(2)
            par_num = str(param).zfill(2)
            value = float(await connection.get_parameter(f"/fx/{fx_num}/par/{par_num}"))
            return f"FX {fx} parameter {param}: {value:.3f}"
        except Exception as e:
            return f"Failed to get FX parameter: {e}"
