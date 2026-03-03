"""
Connection domain tools
Handles connection, disconnection, info, and status operations
"""

from mcp.server.fastmcp import FastMCP
from src.services.x32_connection import X32Connection, X32ConnectionConfig


def register_connection_tools(mcp: FastMCP, connection: X32Connection) -> None:
    """Register all connection domain tools."""

    @mcp.tool(
        name="connection_connect",
        description=(
            "Establishes a connection to an X32 or M32 digital mixing console using the OSC "
            "(Open Sound Control) protocol. Use this tool when you need to control mixer functions "
            "remotely. The mixer must be powered on and connected to the same network."
        ),
    )
    async def connection_connect(host: str, port: int = 10023) -> str:
        """
        Connect to X32/M32 mixer.

        Args:
            host: IP address of the X32/M32 mixer on the network (e.g., "192.168.1.100")
            port: OSC port number for communication with the mixer (standard port is 10023)
        """
        if connection.connected:
            return "Already connected to X32/M32 mixer"

        try:
            await connection.connect(X32ConnectionConfig(host=host, port=port))
            return f"Successfully connected to X32/M32 at {host}:{port}"
        except Exception as e:
            error_message = str(e)
            return "\n".join([
                f"Connection to X32/M32 mixer failed: {error_message}",
                "",
                "Common causes and solutions:",
                "1. Mixer is powered off or not on the network",
                "   -> Power on the mixer and ensure it is connected to the same network",
                "",
                "2. Incorrect IP address",
                f"   -> Verify the IP address (currently trying: {host})",
                "   -> Check mixer's network settings menu or use network scanning tools",
                "",
                "3. Firewall blocking UDP traffic",
                f"   -> Ensure port {port} (UDP) is not blocked by your firewall",
                "   -> Try temporarily disabling firewall to test connectivity",
                "",
                "4. Network routing issues",
                "   -> Ensure mixer and control computer are on the same subnet",
                "   -> Verify network cables are securely connected",
                "",
                "Next steps:",
                "- Verify mixer IP address in mixer's network settings",
                "- Ping the mixer to test basic network connectivity",
                "- Check that no other application is using the OSC port",
                f"- Try the standard X32/M32 port (10023) or check mixer documentation",
            ])

    @mcp.tool(
        name="connection_disconnect",
        description=(
            "Disconnects from the currently connected X32 or M32 digital mixing console. "
            "Use this tool to cleanly terminate the OSC connection when mixer control is no longer needed."
        ),
    )
    async def connection_disconnect() -> str:
        """Disconnect from X32/M32 mixer."""
        if not connection.connected:
            return "Not connected to X32/M32 mixer"

        try:
            await connection.disconnect()
            return "Successfully disconnected from X32/M32 mixer"
        except Exception as e:
            error_message = str(e)
            return "\n".join([
                f"Disconnection from X32/M32 mixer failed: {error_message}",
                "",
                "What this means:",
                "- The connection may already be closed or in an invalid state",
                "- Network resources might not be releasing properly",
                "",
                "Recommended actions:",
                "1. Check current connection status:",
                "   -> Use connection_get_status to verify connection state",
                "",
                "2. Force cleanup if needed:",
                "   -> The connection may be in a stuck state",
                "   -> Try restarting the MCP server if this persists",
                "",
                "Note: Even if disconnection fails, you can attempt connection_connect",
                "to establish a new connection. The connection state will be reset.",
            ])

    @mcp.tool(
        name="connection_get_info",
        description=(
            "Retrieves detailed console information from connected X32 or M32 digital mixing console. "
            "Returns model name, firmware version, server details, and other system information."
        ),
    )
    async def connection_get_info() -> str:
        """Get X32/M32 console information."""
        if not connection.connected:
            return "\n".join([
                "Cannot retrieve console information: Not connected to X32/M32 mixer",
                "",
                "What you need to do:",
                "1. First establish a connection using connection_connect",
                "",
                "Example usage:",
                "  Tool: connection_connect",
                "  Parameters:",
                '    host: "192.168.1.100"  (your mixer\'s IP address)',
                "    port: 10023             (standard X32/M32 OSC port)",
                "",
                "How to find your mixer's IP address:",
                "- On the mixer: Setup -> Network -> IP Address",
                "- Use a network scanning tool to discover devices",
                "- Check your router's DHCP client list",
            ])

        try:
            info = await connection.get_info()
            return "\n".join([
                f"Console Model: {info.console_model}",
                f"Console Version: {info.console_version}",
                f"Server Name: {info.server_name}",
                f"Server Version: {info.server_version}",
            ])
        except Exception as e:
            error_message = str(e)
            return "\n".join([
                f"Failed to retrieve console information: {error_message}",
                "",
                "Possible causes:",
                "1. Connection was lost - mixer may have been powered off",
                "2. Mixer is not responding - may be busy or overloaded",
                "",
                "How to fix:",
                "1. Check connection status with connection_get_status",
                "2. Reconnect: use connection_disconnect then connection_connect",
            ])

    @mcp.tool(
        name="connection_get_status",
        description=(
            "Retrieves the current operational status of the connected X32 or M32 digital mixing console. "
            "Returns connection state, network information, and server details."
        ),
    )
    async def connection_get_status() -> str:
        """Get X32/M32 connection status."""
        if not connection.connected:
            return "\n".join([
                "Cannot retrieve connection status: Not connected to X32/M32 mixer",
                "",
                "What you need to do:",
                "1. First establish a connection using connection_connect",
                "",
                "Example usage:",
                "  Tool: connection_connect",
                "  Parameters:",
                '    host: "192.168.1.100"  (your mixer\'s IP address)',
                "    port: 10023             (standard X32/M32 OSC port)",
            ])

        try:
            status = await connection.get_status()
            return "\n".join([
                f"State: {status.state}",
                f"IP Address: {status.ip_address}",
                f"Server Name: {status.server_name}",
            ])
        except Exception as e:
            error_message = str(e)
            return "\n".join([
                f"Failed to retrieve connection status: {error_message}",
                "",
                "Possible causes:",
                "1. Connection was lost",
                "2. Network issues - congestion, cable unplugged, WiFi interference",
                "",
                "How to fix:",
                "1. Verify basic connectivity - check mixer is powered on",
                "2. Reconnect: use connection_disconnect then connection_connect",
            ])