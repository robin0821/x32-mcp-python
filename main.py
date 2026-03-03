"""
X32/M32 MCP Server - Main entry point

Transport options:
  stdio (default) - for local MCP clients like Claude Desktop that spawn this process
  sse             - HTTP Server-Sent Events, run: python main.py --transport sse
  streamable-http - Streamable HTTP,         run: python main.py --transport streamable-http
"""

import argparse
from src.server import mcp

def main():
    parser = argparse.ArgumentParser(description="XM32-MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="MCP transport to use (default: stdio)",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to for SSE/streamable-http (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to listen on for SSE/streamable-http (default: 8000)",
    )
    args = parser.parse_args()

    if args.transport == "stdio":
        # Standard stdio transport — used by Claude Desktop and most local MCP clients.
        # The client spawns this process and speaks MCP over stdin/stdout.
        mcp.run(transport="stdio")
    elif args.transport == "sse":
        # HTTP Server-Sent Events transport.
        # Client connects to http://<host>:<port>/sse
        mcp.run(transport="sse", host=args.host, port=args.port)
    elif args.transport == "streamable-http":
        # Streamable HTTP transport (newer MCP spec).
        # Client connects to http://<host>:<port>/mcp
        mcp.run(transport="streamable-http", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
