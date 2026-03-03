# XM32-MCP Python

A Python MCP (Model Context Protocol) server for controlling Behringer X32 / Midas M32 digital mixing consoles via OSC (Open Sound Control) over UDP.

## Requirements

- Python 3.11+
- `mcp[cli]` package

## Installation

```bash
cd python
pip install -r requirements.txt
```

## Running

### stdio (default) — for Claude Desktop and local MCP clients

The client spawns the process and communicates over stdin/stdout:

```bash
cd python
python main.py
# or explicitly:
python main.py --transport stdio
```

### SSE (Server-Sent Events) — HTTP-based clients

Starts an HTTP server; clients connect to `http://host:port/sse`:

```bash
python main.py --transport sse --host 0.0.0.0 --port 8000
```

### Streamable HTTP — newer MCP HTTP transport

Starts an HTTP server; clients connect to `http://host:port/mcp`:

```bash
python main.py --transport streamable-http --host 0.0.0.0 --port 8000
```

## MCP Client Configuration

### Claude Desktop (stdio)

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "xm32": {
      "command": "python",
      "args": ["/path/to/XM32-MCP/python/main.py"]
    }
  }
}
```

### HTTP-based client (SSE)

```json
{
  "mcpServers": {
    "xm32": {
      "url": "http://localhost:8000/sse"
    }
  }
}
```

## Project Structure

```
python/
├── main.py                     # Entry point
├── requirements.txt
├── src/
│   ├── server.py               # FastMCP server setup
│   ├── services/
│   │   └── x32_connection.py   # UDP OSC connection manager
│   ├── tools/
│   │   ├── channel.py          # Channel fader/mute/pan/name/color/sends
│   │   ├── bus.py              # Mix bus fader/mute/pan/name/color
│   │   ├── fx.py               # FX rack source/type/return
│   │   ├── main.py             # Main LR and Mono outputs
│   │   ├── parameter.py        # Low-level OSC parameter get/set
│   │   └── connection.py       # Connect/disconnect/info/status
│   └── utils/
│       ├── color_converter.py  # X32 color name <-> integer mapping
│       ├── db_converter.py     # dB <-> linear fader conversion
│       ├── pan_converter.py    # Pan percentage/LR notation <-> linear
│       └── error_helper.py     # Standardised error messages
```

## Available Tools

### Connection
| Tool | Description |
|------|-------------|
| `connection_connect` | Connect to mixer (host, port=10023) |
| `connection_disconnect` | Disconnect from mixer |
| `connection_get_info` | Get console model/firmware info |
| `connection_get_status` | Get connection status |

### Channels (1-32)
| Tool | Description |
|------|-------------|
| `channel_set_volume` | Set fader level (linear or dB) |
| `channel_get_volume` | Get fader level |
| `channel_mute` | Mute/unmute channel |
| `channel_get_mute` | Get mute state |
| `channel_set_pan` | Set pan position |
| `channel_set_name` | Set channel name |
| `channel_set_color` | Set strip color |
| `channel_set_gain` | Set preamp gain |
| `channel_set_send_to_bus` | Set send level to a bus |
| `channel_set_send_to_bus_on` | Enable/disable send to bus |

### Buses (1-16)
| Tool | Description |
|------|-------------|
| `bus_set_volume` | Set fader level (linear or dB) |
| `bus_get_volume` | Get fader level |
| `bus_mute` | Mute/unmute bus |
| `bus_get_mute` | Get mute state |
| `bus_set_pan` | Set pan position |
| `bus_set_name` | Set bus name |
| `bus_set_color` | Set strip color |

### FX (1-8)
| Tool | Description |
|------|-------------|
| `fx_get_info` | Get FX source info |
| `fx_set_source` | Set FX source |
| `fx_set_type` | Set effect type |
| `fx_get_return_volume` | Get FX return fader |
| `fx_set_return_volume` | Set FX return fader |
| `fx_mute_return` | Mute/unmute FX return |

### Main / Mono
| Tool | Description |
|------|-------------|
| `main_set_volume` | Set main LR fader |
| `main_get_volume` | Get main LR fader |
| `main_mute` | Mute/unmute main LR |
| `main_get_mute` | Get main LR mute state |
| `mono_set_volume` | Set mono/center fader |
| `mono_mute` | Mute/unmute mono/center |

### Low-level Parameters
| Tool | Description |
|------|-------------|
| `parameter_get` | Get any OSC parameter by address |
| `parameter_set_float` | Set float parameter by address |
| `parameter_set_int` | Set integer parameter by address |
| `parameter_set_string` | Set string parameter by address |

## Fader Scale Reference

| dB | Linear |
|----|--------|
| +10 dB (max) | 1.0 |
| 0 dB (unity) | 0.75 |
| -10 dB | ~0.397 |
| -30 dB | ~0.137 |
| -60 dB | ~0.025 |
| -∞ (off) | 0.0 |