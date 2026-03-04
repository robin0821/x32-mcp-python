"""
Scene/Snapshot management tools for the X32/M32 mixer.

X32 scene OSC addresses (from reference osc-client.ts):
  /-snap/load          - recall scene by 0-based index (int arg)
  /-snap/store         - save scene by 0-based index (int arg)
  /-snap/NNN/name      - scene name string (NNN is 0-based, zero-padded to 3 digits)
  /-show/prepos/current - current scene index (int, 0-based)

Note: The X32 uses 0-based scene indices internally (0–99) but users typically
refer to scenes as 1–100. This implementation accepts 1-based scene numbers
and converts internally.
"""

from mcp.server.fastmcp import FastMCP
from src.services.x32_connection import X32Connection
from src.utils.error_helper import X32Error


def register_scene_tools(mcp: FastMCP, connection: X32Connection) -> None:
    """Register all scene/snapshot management tools."""

    @mcp.tool(
        name="scene_recall",
        description=(
            "Recall (load) a saved scene/snapshot on the X32/M32 mixer. "
            "This restores the mixer state saved in the specified scene slot. "
            "Scene numbers are 1 to 100."
        ),
    )
    async def scene_recall(scene: int) -> str:
        """
        Args:
            scene: Scene number from 1 to 100
        """
        if not connection.connected:
            return X32Error.not_connected()
        if scene < 1 or scene > 100:
            return f"Invalid scene number {scene}. Must be 1–100."
        try:
            scene_idx = scene - 1  # X32 is 0-based
            await connection.set_parameter("/-snap/load", scene_idx)
            return f"Recalled scene {scene} (index {scene_idx})"
        except Exception as e:
            return f"Failed to recall scene: {e}"

    @mcp.tool(
        name="scene_save",
        description=(
            "Save the current mixer state as a scene/snapshot on the X32/M32 mixer. "
            "Overwrites the specified scene slot. Scene numbers are 1 to 100."
        ),
    )
    async def scene_save(scene: int) -> str:
        """
        Args:
            scene: Scene number from 1 to 100
        """
        if not connection.connected:
            return X32Error.not_connected()
        if scene < 1 or scene > 100:
            return f"Invalid scene number {scene}. Must be 1–100."
        try:
            scene_idx = scene - 1  # X32 is 0-based
            await connection.set_parameter("/-snap/store", scene_idx)
            return f"Saved current mixer state to scene {scene} (index {scene_idx})"
        except Exception as e:
            return f"Failed to save scene: {e}"

    @mcp.tool(
        name="scene_get_name",
        description=(
            "Get the name of a saved scene/snapshot on the X32/M32 mixer. "
            "Scene numbers are 1 to 100."
        ),
    )
    async def scene_get_name(scene: int) -> str:
        """
        Args:
            scene: Scene number from 1 to 100
        """
        if not connection.connected:
            return X32Error.not_connected()
        if scene < 1 or scene > 100:
            return f"Invalid scene number {scene}. Must be 1–100."
        try:
            scene_idx = scene - 1  # X32 is 0-based
            snap_num = str(scene_idx).zfill(3)
            name = await connection.get_parameter(f"/-snap/{snap_num}/name")
            return f"Scene {scene} name: '{name}'"
        except Exception as e:
            err = str(e)
            if "Timeout" in err or "timeout" in err:
                return f"Scene {scene} is empty (no snapshot saved in that slot)"
            return f"Failed to get scene name: {e}"

    @mcp.tool(
        name="scene_set_name",
        description=(
            "Set the name of a scene/snapshot slot on the X32/M32 mixer. "
            "Scene numbers are 1 to 100."
        ),
    )
    async def scene_set_name(scene: int, name: str) -> str:
        """
        Args:
            scene: Scene number from 1 to 100
            name: Scene name (max 32 characters)
        """
        if not connection.connected:
            return X32Error.not_connected()
        if scene < 1 or scene > 100:
            return f"Invalid scene number {scene}. Must be 1–100."
        try:
            scene_idx = scene - 1
            snap_num = str(scene_idx).zfill(3)
            await connection.set_parameter(f"/-snap/{snap_num}/name", name)
            return f"Scene {scene} name set to '{name}'"
        except Exception as e:
            return f"Failed to set scene name: {e}"

    @mcp.tool(
        name="scene_get_current",
        description=(
            "Get the currently active scene/snapshot number on the X32/M32 mixer."
        ),
    )
    async def scene_get_current() -> str:
        if not connection.connected:
            return X32Error.not_connected()
        try:
            idx = int(await connection.get_parameter("/-show/prepos/current"))
            scene_num = idx + 1  # convert 0-based to 1-based
            return f"Current scene: {scene_num} (index {idx})"
        except Exception as e:
            return f"Failed to get current scene: {e}"