"""
Simple error helper for X32-MCP
Centralized error messages for MVP
"""


class X32Error:
    """Simple error message helper for X32/M32 MCP tools."""

    @staticmethod
    def not_connected() -> str:
        """Returns error message when X32/M32 connection is required but not established."""
        return (
            'Not connected to X32/M32 mixer.\n\n'
            'Use connection_connect first:\n'
            '  connection_connect with host="192.168.1.100" and port=10023'
        )

    @staticmethod
    def invalid_channel(channel: int) -> str:
        """Returns error message for invalid channel number."""
        return f"Invalid channel: {channel}. Must be 1-32."

    @staticmethod
    def invalid_bus(bus: int) -> str:
        """Returns error message for invalid bus number."""
        return f"Invalid bus: {bus}. Must be 1-16."

    @staticmethod
    def invalid_fx(fx: int) -> str:
        """Returns error message for invalid FX rack number."""
        return f"Invalid FX rack: {fx}. Must be 1-8."

    @staticmethod
    def invalid_db(value: float) -> str:
        """Returns error message for dB value out of valid range."""
        return (
            f"Invalid dB value: {value}. Must be between -90 and +10 dB.\n"
            "Unity gain = 0 dB."
        )

    @staticmethod
    def invalid_linear(value: float) -> str:
        """Returns error message for linear value out of valid range."""
        return (
            f"Invalid linear value: {value}. Must be between 0.0 and 1.0.\n"
            "Unity gain = 0.75."
        )

    @staticmethod
    def connection_failed(host: str, port: int, error: str) -> str:
        """Returns error message for connection failures with troubleshooting steps."""
        return (
            f"Failed to connect to {host}:{port}\n\n"
            f"Error: {error}\n\n"
            "Check:\n"
            "1. Mixer is powered on\n"
            "2. IP address is correct\n"
            "3. Network connection\n"
            f"4. Port {port} is not blocked"
        )

    @staticmethod
    def osc_failed(operation: str, error: Exception | str) -> str:
        """Returns error message for OSC operation failures."""
        error_msg = str(error)
        return f"Failed to {operation}: {error_msg}"