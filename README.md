# XM32-MCP Python

A Python MCP (Model Context Protocol) server for controlling Behringer X32 / Midas M32 digital mixing consoles via OSC (Open Sound Control) over UDP.

## Requirements

- Python 3.11+
- `mcp[cli]` package

## Installation

```bash
pip install -r requirements.txt
```

## Running

### stdio (default) — for Claude Desktop and local MCP clients

The client spawns the process and communicates over stdin/stdout:

```bash
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
      "args": ["/path/to/xm32-mcp-python/main.py"]
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
.
├── main.py                       # Entry point
├── requirements.txt
├── pyproject.toml
├── src/
│   ├── server.py                 # FastMCP server setup & tool registration
│   ├── services/
│   │   └── x32_connection.py     # UDP OSC connection manager
│   ├── tools/
│   │   ├── automix.py            # Automix (gain-sharing) tools
│   │   ├── aux.py                # Aux input tools
│   │   ├── bus.py                # Mix bus tools
│   │   ├── channel.py            # Input channel tools
│   │   ├── connection.py         # Connect / disconnect / info / status
│   │   ├── dca.py                # DCA group tools
│   │   ├── dynamics.py           # (helpers used by channel dynamics)
│   │   ├── eq.py                 # (helpers used by channel/bus EQ)
│   │   ├── fx.py                 # FX rack tools
│   │   ├── main.py               # Main LR & mono output tools
│   │   ├── matrix.py             # Matrix output tools
│   │   ├── meters.py             # Meter request tools
│   │   ├── mute.py               # Mute group tools
│   │   ├── parameter.py          # Low-level OSC parameter get/set
│   │   ├── scene.py              # Scene / show tools
│   │   └── usb.py                # USB recorder / player tools
│   └── utils/
│       ├── color_converter.py    # X32 color name ↔ integer mapping
│       ├── db_converter.py       # dB ↔ linear fader conversion
│       ├── icon_converter.py     # X32 icon name ↔ integer mapping
│       ├── pan_converter.py      # Pan % / LR notation ↔ linear
│       └── error_helper.py       # Standardised error messages
```

## Available Tools

### Connection
| Tool | Description |
|------|-------------|
| `connection_connect` | Connect to mixer (host, port=10023) |
| `connection_disconnect` | Disconnect from mixer |
| `connection_get_info` | Get console model / firmware info (`/info`) |
| `connection_get_status` | Get connection status (`/status`) |

### Channels (1–32)
| Tool | Description |
|------|-------------|
| `channel_get_volume` | Get fader level |
| `channel_set_volume` | Set fader level (linear 0–1 or dB) |
| `channel_get_mute` | Get mute state |
| `channel_mute` | Mute / unmute channel |
| `channel_get_pan` | Get pan position |
| `channel_set_pan` | Set pan position |
| `channel_get_name` | Get channel name |
| `channel_set_name` | Set channel name (max 12 chars) |
| `channel_set_color` | Set strip color |
| `channel_get_icon` | Get channel icon |
| `channel_set_icon` | Set channel icon |
| `channel_get_source` | Get input source |
| `channel_set_source` | Set input source |
| `channel_set_gain` | Set preamp trim/gain |
| `channel_get_send_to_bus` | Get send level to a mix bus |
| `channel_set_send_to_bus` | Set send level to a mix bus |
| `channel_set_send_to_bus_on` | Enable / disable send to a mix bus |
| `channel_set_send_pre_post` | Set send pre/post EQ for a mix bus |
| `channel_get_send_to_aux` | Get send level to an aux |
| `channel_set_send_to_aux` | Set send level to an aux |
| `channel_get_dca` | Get DCA group assignment bitmap |
| `channel_set_dca` | Assign channel to DCA groups |
| `channel_get_mute_group` | Get mute group assignment bitmap |
| `channel_set_mute_group` | Assign channel to mute groups |
| `channel_get_eq_on` | Get EQ on/off state |
| `channel_set_eq_on` | Enable / disable EQ |
| `channel_get_eq_band` | Get all parameters for an EQ band |
| `channel_get_eq_frequency` | Get EQ band frequency |
| `channel_set_eq_frequency` | Set EQ band frequency (Hz) |
| `channel_get_eq_gain` | Get EQ band gain |
| `channel_set_eq_gain` | Set EQ band gain (dB) |
| `channel_get_eq_q` | Get EQ band Q factor |
| `channel_set_eq_q` | Set EQ band Q factor |
| `channel_get_gate_on` | Get gate on/off state |
| `channel_set_gate_on` | Enable / disable gate |
| `channel_get_gate_info` | Get full gate parameter set |
| `channel_get_gate_threshold` | Get gate threshold |
| `channel_set_gate_threshold` | Set gate threshold (dB) |
| `channel_set_gate_attack` | Set gate attack time (ms) |
| `channel_set_gate_release` | Set gate release time (ms) |
| `channel_get_compressor_on` | Get compressor on/off state |
| `channel_set_compressor_on` | Enable / disable compressor |
| `channel_get_compressor_info` | Get full compressor parameter set |
| `channel_get_compressor_threshold` | Get compressor threshold |
| `channel_set_compressor_threshold` | Set compressor threshold (dB) |
| `channel_get_compressor_ratio` | Get compressor ratio |
| `channel_set_compressor_ratio` | Set compressor ratio |
| `channel_set_compressor_attack` | Set compressor attack time (ms) |
| `channel_set_compressor_release` | Set compressor release time (ms) |
| `channel_get_compressor_makeup_gain` | Get compressor make-up gain |
| `channel_set_compressor_makeup_gain` | Set compressor make-up gain (dB) |

### Mix Buses (1–16)
| Tool | Description |
|------|-------------|
| `bus_get_volume` | Get fader level |
| `bus_set_volume` | Set fader level (linear 0–1 or dB) |
| `bus_get_mute` | Get mute state |
| `bus_mute` | Mute / unmute bus |
| `bus_get_pan` | Get pan position |
| `bus_set_pan` | Set pan position |
| `bus_get_name` | Get bus name |
| `bus_set_name` | Set bus name (max 12 chars) |
| `bus_set_color` | Set strip color |
| `bus_get_dca` | Get DCA group assignment bitmap |
| `bus_set_dca` | Assign bus to DCA groups |
| `bus_get_mute_group` | Get mute group assignment bitmap |
| `bus_set_mute_group` | Assign bus to mute groups |
| `bus_set_send_to_matrix` | Set send level from bus to a matrix output |

### Aux Inputs (1–8)
| Tool | Description |
|------|-------------|
| `aux_get_volume` | Get fader level |
| `aux_set_volume` | Set fader level (linear 0–1 or dB) |
| `aux_get_mute` | Get mute state |
| `aux_mute` | Mute / unmute aux input |
| `aux_set_pan` | Set pan position |
| `aux_set_name` | Set aux name (max 12 chars) |
| `aux_get_dca` | Get DCA group assignment bitmap |
| `aux_set_dca` | Assign aux to DCA groups |
| `aux_get_mute_group` | Get mute group assignment bitmap |
| `aux_set_mute_group` | Assign aux to mute groups |

### FX (slots 1–8)
| Tool | Description |
|------|-------------|
| `fx_get_info` | Get FX type and source info |
| `fx_set_type` | Set effect type (integer enum) |
| `fx_set_source` | Set FX source input |
| `fx_set_on` | Enable / disable FX slot |
| `fx_set_mix` | Set FX wet/dry mix |
| `fx_get_param` | Get a specific FX parameter (1–64) |
| `fx_set_param` | Set a specific FX parameter (1–64) |
| `fx_get_return_volume` | Get FX return fader level |
| `fx_set_return_volume` | Set FX return fader level |
| `fx_mute_return` | Mute / unmute FX return |
| `fx_get_dca` | Get FX return DCA assignment bitmap |
| `fx_set_dca` | Assign FX return to DCA groups |
| `fx_get_mute_group` | Get FX return mute group assignment |
| `fx_set_mute_group` | Assign FX return to mute groups |

### Matrix Outputs (1–6)
| Tool | Description |
|------|-------------|
| `matrix_get_volume` | Get fader level |
| `matrix_set_volume` | Set fader level (linear 0–1 or dB) |
| `matrix_get_mute` | Get mute state |
| `matrix_mute` | Mute / unmute matrix output |
| `matrix_set_pan` | Set pan position |
| `matrix_set_name` | Set matrix name (max 12 chars) |
| `matrix_get_dca` | Get DCA group assignment bitmap |
| `matrix_set_dca` | Assign matrix to DCA groups |
| `matrix_get_mute_group` | Get mute group assignment bitmap |
| `matrix_set_mute_group` | Assign matrix to mute groups |

### DCA Groups (1–8)
| Tool | Description |
|------|-------------|
| `dca_get_volume` | Get DCA fader level |
| `dca_set_volume` | Set DCA fader level (linear 0–1 or dB) |
| `dca_get_mute` | Get DCA mute state |
| `dca_mute` | Mute / unmute DCA group |
| `dca_get_name` | Get DCA name |
| `dca_set_name` | Set DCA name (max 12 chars) |
| `dca_get_color` | Get DCA color |
| `dca_set_color` | Set DCA color |
| `dca_get_icon` | Get DCA icon |
| `dca_set_icon` | Set DCA icon |

### Main LR & Mono/Center
| Tool | Description |
|------|-------------|
| `main_get_volume` | Get main LR fader level |
| `main_set_volume` | Set main LR fader level (linear 0–1 or dB) |
| `main_get_mute` | Get main LR mute state |
| `main_mute` | Mute / unmute main LR |
| `main_get_pan` | Get main LR pan |
| `main_set_pan` | Set main LR pan |
| `mono_get_volume` | Get mono/center fader level |
| `mono_set_volume` | Set mono/center fader level (linear 0–1 or dB) |
| `mono_get_mute` | Get mono/center mute state |
| `mono_mute` | Mute / unmute mono/center |

### Mute Groups (1–6)
| Tool | Description |
|------|-------------|
| `mute_group_get` | Get active state of a mute group |
| `mute_group_set` | Activate / deactivate a mute group |
| `mute_group_get_all` | Get active state of all 6 mute groups |

### Meters
| Tool | Description |
|------|-------------|
| `meters_get_overview` | Get all input + bus + fx return levels (`/meters/0`) |
| `meters_get_channels` | Get 32 ch input + gate/dyn GR values (`/meters/1`) |
| `meters_get_buses` | Get bus + matrix + main LR/M levels (`/meters/2`) |
| `meters_get_aux_fx` | Get aux send + FX return levels (`/meters/3`) |
| `meters_get_in_out` | Get input + output + P16 + aux levels (`/meters/4`) |
| `meters_get_surface` | Get console surface VU meters (`/meters/5`) |
| `meters_get_channel_strip` | Get 4-value strip meters for one channel (`/meters/6`) |
| `meters_get_bus_sends` | Get 16 bus-send meter values (`/meters/7`) |
| `meters_get_matrix_sends` | Get 6 matrix-send meter values (`/meters/8`) |

### Scene / Show Management
| Tool | Description |
|------|-------------|
| `scene_get_current` | Get currently selected scene index |
| `scene_recall` | Load a scene (0–99) |
| `scene_save` | Save current state to a scene slot (0–99) |
| `scene_get_name` | Get name of a scene |
| `scene_set_name` | Set name of a scene |

### USB Recorder / Player
| Tool | Description |
|------|-------------|
| `usb_get_status` | Get recorder/player status |
| `usb_play` | Start playback |
| `usb_pause` | Pause playback |
| `usb_record_start` | Start recording |
| `usb_record_stop` | Stop recording |
| `usb_fast_forward` | Fast-forward |
| `usb_rewind` | Rewind |
| `usb_next_track` | Skip to next track |
| `usb_prev_track` | Skip to previous track |
| `usb_get_playback_track` | Get current playback track |
| `usb_set_playback_track` | Select a playback track by number |
| `usb_get_playback_gain` | Get playback output gain |
| `usb_set_playback_gain` | Set playback output gain |
| `usb_get_playback_mode` | Get playback mode (single / folder) |
| `usb_set_playback_mode` | Set playback mode |
| `usb_get_record_gain` | Get recording input gain |
| `usb_set_record_gain` | Set recording input gain |
| `usb_get_record_source` | Get recording source |
| `usb_set_record_source` | Set recording source |

### Automix
| Tool | Description |
|------|-------------|
| `automix_configure` | Configure the automix engine (group assignment, etc.) |
| `automix_get_status` | Get current automix status |
| `automix_reset` | Reset automix state / fader presets |
| `automix_learn_faders_from_mixer` | Learn fader positions from the mixer |
| `automix_set_fader_high` | Set the "open" fader level for a channel |
| `automix_set_fader_low` | Set the "attenuated" fader level for a channel |
| `automix_run_cycle` | Run a single automix decision cycle |
| `automix_run_cycles` | Run multiple automix cycles with a configurable interval |

### Low-level Parameters
| Tool | Description |
|------|-------------|
| `parameter_get` | Get any OSC parameter by full address |
| `parameter_set_float` | Set a float parameter by full address |
| `parameter_set_int` | Set an integer parameter by full address |
| `parameter_set_string` | Set a string parameter by full address |

## Fader Scale Reference

The X32/M32 uses a 4-segment pseudo-logarithmic scale for fader values:

| dB | Linear (OSC float) |
|----|-------------------|
| +10 dB (max) | 1.000 |
| 0 dB (unity) | 0.750 |
| −10 dB | ≈ 0.500 |
| −30 dB | ≈ 0.250 |
| −60 dB | ≈ 0.063 |
| −∞ (off) | 0.000 |

Conversion formula (float → dB):
```
f >= 0.5  → dB = f * 40 − 30
f >= 0.25 → dB = f * 80 − 50
f >= 0.0625 → dB = f * 160 − 70
f >= 0.0  → dB = f * 480 − 90
```

## OSC Protocol Notes

- **Transport**: UDP, default port **10023** (X32/M32) or **10024** (XAir)
- **Format**: Big-endian, 4-byte aligned/padded (OSC 1.0)
- **Read**: Send address with no arguments → console echoes current value
- **Write**: Send address with argument(s) → console applies value
- **Subscriptions** (`/xremote`, `/subscribe`): push updates for 10 seconds; must be renewed before expiry
- **Recommended network**: 100 Mbps wired Ethernet (WiFi may drop UDP packets under load)

## X32/M32 Address Pattern Reference

Key address families exposed through the low-level `parameter_*` tools:

```
/ch/[01-32]/...        Input channels
/auxin/[01-08]/...     Aux inputs
/fxrtn/[01-08]/...     FX returns
/bus/[01-16]/...       Mix buses
/mtx/[01-06]/...       Matrix outputs
/main/st/...           Main stereo LR
/main/m/...            Main mono / center
/dca/[1-8]/...         DCA groups
/fx/[1-8]/...          FX engine slots
/headamp/[000-127]/... Head-amp gain & phantom power
/outputs/main/[01-16]  XLR output patch
/config/...            Global config (routing, linking, etc.)
/-prefs/...            Console preferences
/-stat/...             Console status (solo, screen, etc.)
/-action/...           Actions (go scene, clear solo, etc.)
/-usb/...              USB drive directory / tape
/meters/[0-16]         Meter data (blobs)