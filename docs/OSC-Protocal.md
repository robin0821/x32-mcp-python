# X32/M32 OSC Protocol Core Guide

## UDP Communication Basics

- **Port**: UDP **10023** (X32/M32 default), UDP **10024** (XAir series)
- **Protocol**: UDP (User Datagram Protocol)
- **Communication**: X32/M32 listens on UDP 10023, responds to the port used by the client
- **Data Format**: Big-endian, 4-byte aligned/padded (padded with null bytes)
- **Notes**:
    - UDP does not report packet loss — beware of buffer overflow
    - WiFi (54 Mbps) may drop packets under heavy data transfer
    - 100 Mbps wired Ethernet connection is recommended

## OSC Message Structure

```
[Address Pattern (4-byte aligned)] + [Type Tag String (4-byte aligned)] + [Arguments (4-byte aligned)]
```

### Type Tags

| Type | Description           | Range                     |
| ---- | --------------------- | ------------------------- |
| `i`  | 32-bit signed integer | Integer value             |
| `f`  | 32-bit signed float   | 0.0 ~ 1.0                 |
| `s`  | String                | null-terminated           |
| `b`  | Blob                  | Arbitrary binary data     |

### Message Examples

```
/info~~~,~~~                          (no arguments)
/ch/01/config/name~~,s~~name~~~~     (one string)
/ch/01/eq/1 ,ifff [2] [0.26] [0.5] [0.46]  (one int + three floats)
```

## X32/M32 OSC Protocol Parameters

### Type Rules (Get/Set Parameter) and Data Formatting

The X32/M32 follows the OSC 1.0 specification and implements 4 basic OSC type tags: **int32**, **float32**, **string**, **blob**

#### Data Format Rules

- **All parameters are big-endian and 4-byte aligned/padded** (per OSC spec)
- **Padding is performed with null bytes (\0)**
- **Float parameters must be in the range 0.0 ~ 1.0**
    ```
    0.0 → 0x00000000 (big-endian)
    0.5 → 0x3f000000 (big-endian)
    1.0 → 0x3f800000 (big-endian)
    ```
- **Integer and float parameters are signed 32-bit values**
- **Strings must be null-terminated**
- **Enum parameters can be sent as a string or an integer**
- **Boolean parameters map to enum type {OFF, ON} or OSC integer {0, 1}**
- **Blob (arbitrary binary data) follows section-specific rules**

#### OSC Command Structure

An OSC command consists of:

- **4-byte padded OSC message (Address Pattern)**
- **4-byte padded type tag string**
- **If a non-empty type tag string is present, one or more 4-byte aligned/padded arguments**

#### OSC 1.0 Compatibility

The OSC 1.0 spec notes that older OSC implementations may omit the type tag string, and the X32/M32 supports this.

**Example: Command without type tag (legacy OSC format)**

```
/info~~~              (non-compliant with OSC 1.0, but accepted by X32/M32)
/info~~~,~~~          (OSC 1.0 compliant — recommended)
```

#### Special Considerations for Float Type

The X32/M32 only recognises a **discrete subset of values** within the float range [0.0, 1.0].

- The "known" values are determined by the destination they are applied to
- The number of steps determines which values are recognised
- **Example**: EQ frequency — `[20.0, 20k, 201]`
    - The range 20 Hz ~ 20 kHz is divided into 201 discrete values
    - Similarly, the [0.0, 1.0] range is divided into 201 "known" float values
- **Float values outside the range are rounded to the nearest known value**

This is particularly useful when:

- Converting text-format data returned by the `/node` command to float values
- Sending OSC data as text inside MIDI Sysex commands

#### Special Considerations for Enum Type

Enums can be **sent as a string or an integer**.

**Example: Setting channel 01 gate mode**

Enum type: `{EXP2, EXP3, EXP4, GATE, DUCK}`

Method 1 — set to "GATE" using a string:

```
/ch/01/gate/mode~~~~,s~~GATE~~~~
```

Hex:

```
2f63682f30312f676174652f6d6f6465000000002c7300004741544500000000
```

Method 2 — set to "GATE" using an integer (index 3):

```
/ch/01/gate/mode~~~~,i~~[3]
```

Hex:

```
2f63682f30312f676174652f6d6f6465000000002c69000000000003
```

**Note**: This applies only to "enum" types. For example, the key source for dynamics only accepts an "int" value between 0 and 64 — it is not an enum:

```
/ch/[01-32]/dyn/keysrc    (int 0~64 only, not an enum)
```

### Command Examples

#### Simple OSC Command (no arguments)

OSC 1.0 compliant:

```
/info~~~,~~~
```

Legacy format (accepted by X32/M32):

```
/info~~~
```

#### OSC Command with a Single Argument

```
/ch/01/config/name~~,s~~name~~~~
```

#### OSC Command with Multiple Arguments

```
/ch/01/eq/1 ,ifff [2] [0.2650] [0.5000] [0.4648]
```

This is equivalent to the following four simple commands:

```
/ch/01/eq/1/t~~~,i~~[2]
/ch/01/eq/1/f~~~,f~~[0.2650]
/ch/01/eq/1/g~~~,f~~[0.5000]
/ch/01/eq/1/q~~~,f~~[0.4648]
```

#### Hex Representation

Hex representation of the last command:

```
/  c  h  /  0  1  /  e  q  /  1  /  q  ~  ~  ~  ,  f  ~  ~ [0.4648]
2f 63 68 2f 30 31 2f 65 71 2f 31 2f 71 00 00 00 2c 66 00 00 3eedfa44
```

- `3eedfa44`: 32-bit float big-endian representation of 0.4648
- `~`: null character (\0)

### X32/M32 Response Examples

#### `/info` Response

**Request:**

```
/info~~~,~~~
```

**Response (X32 Standard):**

```
/info~~~,ssss~~~V2.05~~~osc-server~~X32~2.10~~~~
```

48-byte response

**Responses by model:**

```
X32 Standard:  /info~~~,ssss~~~V2.05~~~osc-server~~X32~2.12~~~~
X32 Rack:      /info~~~,ssss~~~V2.05~~~osc-server~~X32RACK~2.12~~~~
X32 Compact:   /info~~~,ssss~~~V2.05~~~osc-server~~X32C~~2.12~~~~
X32 Producer:  /info~~~,ssss~~~V2.05~~~osc-server~~X32P~2.12~~~~
X32 Core:      /info~~~,ssss~~~V2.05~~~osc-server~~X32CORE~2.12~~~~
M32 Standard:  /info~~~,ssss~~~V2.05~~~osc-server~~M32~2.12~~~~
M32 Compact:   /info~~~,ssss~~~V2.05~~~osc-server~~M32C~2.12~~~~
M32 Rack:      /info~~~,ssss~~~V2.05~~~osc-server~~M32R~2.12~~~~
```

**XAir series (uses UDP port 10024):**

```
XR18: /info~~~,ssss~~~V0.04~~~XR18-1D-DA-B4~~~XR18~~~~1.12~~~~
XR16: /info~~~,ssss~~~V0.04~~~XR16-1D-DA-B4~~~XR16~~~~1.12~~~~
XR12: /info~~~,ssss~~~V0.04~~~XR12-1D-DA-B4~~~XR12~~~~1.12~~~~
```

#### `/status` Response

**Request:**

```
/status~,~~~
```

**Response:**

```
/status~,sss~~~~active~~192.168.0.64~~~~osc-server~~
```

52-byte response

#### Parameter Get Response

**Request:**

```
/fx/4/par/23~~~~,~~~
```

**Response:**

```
/fx/4/par/23~~~~,f~~[float 0.5]
```

24-byte response

Hex:

```
2f66782f342f7061722f3233000000002c6600003f000000
```

## Communication Modes

#### Immediate & Deferred Update Modes

- **Immediate**: The client sends a command to a specific OSC address and the console **responds or applies the value immediately**. **Multiple response messages may be returned** for a single request.
    - Example: `/showdump` returns configuration data as **multiple successive packets** from a single request.
- **Deferred**: Modes such as `/xremote`, `/subscribe`, and `/batchsubscribe` **push state changes for 10 seconds**. The client must **resend the renewal command within 10 seconds** to keep the push active.
    - Changes made on the server UI or by another client trigger automatic notifications.
    - This mode is used when the **event stream matters more than individual values** (e.g., fader moves, mute state changes).
- In summary, what consumes network bandwidth is not the size of the data itself, but the **frequency of continuous events and how clients maintain their connections**. The values transmitted are mostly **simple floats or enums**, so the data overhead is very light.

#### Connection (Session Persistence)

##### Multi-Client Management

- X32/M32 supports **multiple UDP clients simultaneously**
- Each client must independently register via `/xremote` or `/subscribe`
- Changes made by one client are propagated to all registered clients

##### `/xremote`

- Pushes **all state changes from the server (console)** to the **client**
- Has a **10-second timeout** — must be resent approximately every **9 seconds** to stay active
- Streams all UI changes including fader moves, bank changes, and screen updates
- Use case: Receiving the **full UI change stream**

```
Client: /xremote~~~,~~~  (no parameters)
Server: (automatically pushes changes for 10 seconds)
```

##### `/subscribe`

- Specify a **particular OSC address** to receive push updates for **only that parameter's change events**
- The `time_factor` argument controls the **update frequency (resolution)**:
    - `0` → approximately 200 updates (over 10 seconds)
    - `1` → approximately 100 updates
    - `10` → approximately 20 updates
    - `50` → approximately 4 updates
- Use case: Receiving a **selective/targeted change stream**

```
/subscribe ,si /ch/01/mix/on 10
(receive ~20 updates over 10 seconds for channel 1 On/Off state)
```

##### `/batchsubscribe`

- Subscribe to multiple parameters at once; supports wildcards (`*`)
- Example: `/ch/**/mix/on` (On/Off state for all channels)

#### Read vs. Write

- Sending an OSC address **without arguments** → **Read request** for that parameter
- Sending the same OSC address **with arguments** → **Write** a value to that parameter
    - Example:
        - Read:  `/ch/01/mix/fader`
        - Write: `/ch/01/mix/fader ,f 0.75`

#### Message Address Pattern

- In the X32/M32, OSC address strings act as **function endpoints (API endpoints)**, and all mixer parameters are accessed via the following **address families (categories)**:
    - This list is not "an address scheme OSC must support" — it is the **set of controllable commands provided by the X32**
- Therefore: **OSC = message format**, **Address Pattern = X32 control command API**

```
<OSC Address Pattern> ::=
/ | /-action | /add | /auxin | /batchsubscribe | /bus | /ch | /config |
/copy | /dca | /delete | /formatsubscribe | /fx | /fxrtn | /headamp |
/info | /-insert | /-libs | /load | /main/m | /main/st | /meters | /mtx |
/node | /outputs | /-prefs | /rename | /renew | /save | /-show | /showdump |
/-snap | /-stat | /status | /subscribe | /-undo | /unsubscribe | /-urec |
/-usb | /xinfo | /xremote | /xremoteinfo
```

### Key Commands

| Command           | Description                         | Example                                       |
| ----------------- | ----------------------------------- | --------------------------------------------- |
| `/info`           | Query X32/M32 version info          | `/info~~~,~~~`                                |
| `/status`         | Query current status                | `/status~,~~~`                                |
| `/xremote`        | Enable auto-update (10 seconds)     | `/xremote~~~,~~~`                             |
| `/subscribe`      | Subscribe to a specific parameter   | `/subscribe ,si /ch/01/mix/on 1`              |
| `/batchsubscribe` | Batch subscribe to multiple params  | `/batchsubscribe ,ssiii /ch/**/mix/on 0 31 1` |
| `/renew`          | Renew subscription                  | `/renew ,s /meters/5`                         |
| `/unsubscribe`    | Cancel subscription                 | `/unsubscribe`                                |
| `/node`           | Query X32 node data                 | `/node~~~,s~~ch/01`                           |
| `/`               | Write X32 node data                 | `/~~~,s~~ch/01 newname 10 CY 1`               |
| `/meters/[0-16]`  | Request metering data               | `/meters/0`                                   |

### Address Pattern Structure Examples

- Each address pattern has **sub-addresses and parameter structures per section**
- The Address Pattern is best understood as a **tree-shaped control API that directly exposes the mixer's internal parameter structure**

#### Channel Control

```
/ch/[01-32]/config/name        - Channel name
/ch/[01-32]/config/icon        - Channel icon
/ch/[01-32]/config/color       - Channel color
/ch/[01-32]/mix/fader          - Fader level
/ch/[01-32]/mix/on             - Channel On/Off (Mute)
/ch/[01-32]/mix/pan            - Panning
/ch/[01-32]/eq/[1-4]/*         - EQ settings (4-band)
/ch/[01-32]/gate/*             - Gate settings
/ch/[01-32]/dyn/*              - Dynamics/Compressor settings
```

#### Bus Control

```
/bus/[01-16]/mix/fader         - Bus fader
/bus/[01-16]/mix/on            - Bus On/Off
/bus/[01-16]/mix/pan           - Bus panning
```

#### Main Output

```
/main/st/mix/fader             - Main stereo fader
/main/st/mix/on                - Main stereo On/Off
/main/m/mix/fader              - Main mono fader
/main/m/mix/on                 - Main mono On/Off
```

### Command Format Notation

Commands can be represented in two formats in documentation and CLI:

#### Human-readable format

```
<command> <format> <parameters>
/ch/01/mix/fader ,f [0.7]
```

#### Actual network packet format (including OSC 4-byte padding)

```
<command>~~~<format>~~~<parameter> <parameter> …
/ch/01/mix/fader~~~ ,f~~~ [0.7]
```

- Here `~~~` represents the **conceptual notation for byte-alignment space created by OSC string padding (\0)**