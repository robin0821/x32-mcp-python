"""
X32/M32 MCP Server
Main server entry point using FastMCP
"""

import sys
from pathlib import Path

# Ensure the project root is on sys.path so that both
#   `python main.py`  (imports src as a package)
#   `mcp run src/server.py`  (loads this file directly)
# can resolve the src.* imports.
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from mcp.server.fastmcp import FastMCP
from src.services.x32_connection import X32Connection
from src.tools import register_all_tools

# Create the connection singleton
connection = X32Connection()

# Create the FastMCP server instance
mcp = FastMCP(
    name="XM32-MCP",
    instructions=(
        "You are controlling a Behringer X32 or Midas M32 digital mixing console via OSC (Open Sound Control) protocol. "
        "The mixer provides extensive control over audio mixing including channels, buses, effects, and routing.\n\n"
        "Key concepts:\n"
        "- Channels (1-32): Input channels for microphones, instruments, etc.\n"
        "- Buses (1-16): Mix buses for monitors, groups, aux sends\n"
        "- FX (1-8): Built-in effects processors\n"
        "- Main LR: The main stereo output\n"
        "- Mono/Center: The mono/center output\n\n"
        "Before using any mixer control tools, you must first connect using connection_connect.\n"
        "Fader levels: 0.0 = silence, 0.75 = unity gain (0 dB), 1.0 = maximum (+10 dB).\n"
        "Channel on/off: 1 = active (unmuted), 0 = muted."
    ),
)

# Register all tools
register_all_tools(mcp, connection)