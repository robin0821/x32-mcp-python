# X32/M32 Meter Requests

## Overview

The `/meters` OSC command is used to obtain meter data or retrieve a specific set of meter values.

### Basic Information

- **Update interval**: 50 ms (variable depending on console processing capacity)
- **Timeout**: 10 seconds
- **Data format**: OSC blob (binary data)
- **Value range**: Float [0.0, 1.0] (linear audio level, digital 0 = full-scale)
    - Internal headroom: up to 8.0 (+18 dBfs) allowed

## `/meters` Command Format

```
/meters ,siii <meter_request> [time_factor]
```

### Parameters

| Parameter         | Type           | Description                                     |
| ----------------- | -------------- | ----------------------------------------------- |
| `siii`            | Type tags      | String + 2 integers (varies by meter type)      |
| `<meter_request>` | string         | Meter request ID (see list below)               |
| `[time_factor]`   | int (optional) | Controls update frequency                       |

### Time Factor

`time_factor` is a value between 1 and 99 that sets the interval between two consecutive meter messages.

**Formula**: interval = `50 ms × time_factor`

**Timeout**: active for 10 seconds

| time_factor  | Updates (10 seconds) | Interval |
| ------------ | -------------------- | -------- |
| <2 or >99    | ~200                 | ~50 ms   |
| 2            | ~100                 | 100 ms   |
| 10           | ~20                  | 500 ms   |
| 40           | ~5                   | 2 s      |
| 80~99        | ~3                   | 4~5 s    |

**Note**: If `time_factor` is outside the range [1, 99] it is treated the same as 1.

## Response Format (OSC Blob)

The data returned by the X32/M32 server in response to a `/meters` request is in **OSC-blob** format (an arbitrary set of binary data).

### Blob Structure

```
<meter_id> ,b~~<int1><int2><nativefloat>…<nativefloat>
```

**Field descriptions:**

- `<meter_id>`: meter ID (padded with null bytes)
- `,b~~`: blob format indicator (padded with null bytes)
- `<int1>`: blob length in bytes, 32-bit big-endian
- `<int2>`: number of `<nativefloat>` values, 32-bit little-endian
- `<nativefloat>`: meter values, 32-bit floats, little-endian

**Important**: Float values are encoded in **little-endian** (unlike the OSC standard big-endian).

### Example

**Request:**

```
/meters~,si~/meters/6~~16
```

Hex:

```
2f6d6574657273002c7369002f6d65746572732f36000000000000010
/  m e t e r s ~ , s i ~ / m e t e r s / 6 ~ ~ ~ [ 16]
```

**Response:**

```
2f6d657465727332f3600000002c6200000000014040000000fd1d2137fdff7f3f000803f6ebbd534
/  m e t e r s / 6 ~ ~ ~ , b ~ ~ [ int1 ][ int2 ][nfloat][nfloat][nfloat][nfloat]
```

Returns a single blob of 4-channel strip meter values (pre-fade, gate, dyn gain reduction, post-fade) for channel 17 approximately every 50 ms for 10 seconds.

## All Meter IDs

### /meters/0

**Description**: Returns meter values for the METERS page (not used by X32-Edit)

**Contents**:

- 32 input channels
- 8 aux returns
- 4x2 st fx returns
- 16 bus masters
- 6 matrixes

**Returns**: 70 float values (single binary blob)

**Example**:

```
/meters ,s meters/0
```

---

### /meters/1

**Description**: Returns meter values for the METERS/channel page

**Contents**:

- 32 input channels
- 32 gate gain reductions
- 32 dynamics gain reductions

**Returns**: 96 float values (single OSC blob)

**Example**:

```
/meters ,s meters/1
```

---

### /meters/2

**Description**: Returns meter values for the METERS/mix bus page

**Contents**:

- 16 bus masters
- 6 matrixes
- 2 main LR
- 1 mono M/C
- 16 bus master dynamics gain reductions
- 6 matrix dynamics gain reductions
- 1 main LR dynamics gain reduction
- 1 mono M/C dynamics gain reduction

**Returns**: 49 float values (single OSC blob)

**Example**:

```
/meters ,s meters/2
```

---

### /meters/3

**Description**: Returns meter values for the METERS/aux/fx page

**Contents**:

- 6 aux sends
- 8 aux returns
- 4x2 st fx returns

**Returns**: 22 float values (single OSC blob)

**Example**:

```
/meters ,s meters/3
```

---

### /meters/4

**Description**: Returns meter values for the METERS/in/out page

**Contents**:

- 32 input channels
- 8 aux returns
- 16 outputs
- 16 P16 Ultranet outputs
- 6 aux sends
- 2 digital AES/EBU out
- 2 monitor outputs

**Returns**: 82 float values (single OSC blob)

**Example**:

```
/meters ,s meters/4
```

---

### /meters/5 `<chn_meter_id>` `<grp_meter_id>`

**Description**: Returns Console Surface VU Meters (channel, group, and main meters)

**Parameters**:

- `<chn_meter_id>`: channel meter selection
    - `0`: channels 1–16
    - `1`: channels 17–32
    - `2`: aux/fx returns
    - `3`: bus masters
- `<grp_meter_id>`: group meter selection
    - `1`: mix bus 1–8
    - `2`: mix bus 9–16
    - `3`: matrixes

**Contents**:

- 16 channel meters
- 8 group meters
- 2 main LR
- 1 mono M/C

**Returns**: 27 float values (single OSC blob)

**Examples**:

```
/meters ,sii meters/5 0 1
/meters ,sii meters/5 1 2
/meters ,sii meters/5 2 3
```

---

### /meters/6 `<channel_id>`

**Description**: Returns Channel Strip Meters (post gain/trim, gate, dyn gain reduction, post-fade)

**Parameters**:

- `<channel_id>`: channel number (0...71)
    - 0–31: input channels 1–32
    - 32–39: aux returns 1–8
    - 40–47: fx returns 1–8
    - 48–63: bus masters 1–16
    - 64–69: matrixes 1–6
    - 70–71: main LR

**Returns**: 4 float values (single OSC blob)

1. Post gain/trim level
2. Gate reduction
3. Dynamics gain reduction
4. Post-fader level

**Examples**:

```
/meters ,si meters/6 0      # Channel 1
/meters ,si meters/6 16     # Channel 17
/meters ,si meters/6 32     # Aux return 1
/meters ,si meters/6 48     # Bus master 1
```

---

### /meters/7

**Description**: Returns Bus Send meter values

**Contents**:

- 16 bus send meters

**Returns**: 16 float values (Bus sends 1–16)

**Example**:

```
/meters ,s meters/7
```

---

### /meters/8

**Description**: Returns Matrix Send meter values

**Contents**:

- 6 matrix send meters

**Returns**: 6 float values (Matrix sends 1–6)

**Example**:

```
/meters ,s meters/8
```

---

### /meters/9

**Description**: Returns Effect Send and Return meter values

**Contents**:

- 2 effects send meters and 2 effects return meters per FX slot (8 slots)

**Returns**: 32 float values (4 × FX1, 4 × FX2, ... 4 × FX8)

**Example**:

```
/meters ,s meters/9
```

---

### /meters/10

**Description**: Meters dedicated to certain effects (e.g. Dual DeEsser, Stereo DeEsser, Stereo Fair Compressor)

**Returns**: 32 float values

**Example**:

```
/meters ,s meters/10
```

---

### /meters/11

**Description**: Returns meter values for the Monitor page

**Contents**:

- Mon Left
- Mon Right
- Talk A/B level
- Threshold/GR
- Osc Tone level

**Returns**: 5 float values

**Example**:

```
/meters ,s meters/11
```

---

### /meters/12

**Description**: Returns meter values for the Recorder page

**Contents**:

- RecInput L
- RecInput R
- Playback L
- Playback R

**Returns**: 4 float values

**Example**:

```
/meters ,s meters/12
```

---

### /meters/13

**Description**: Returns meter values for the METERS page (simplified version)

**Contents**:

- 32 input channels
- 8 aux returns
- 4x2 st fx returns

**Returns**: 48 float values

**Example**:

```
/meters ,s meters/13
```

---

### /meters/14

**Description**: Dedicated to certain effects (e.g. Precision Limiter, Combinator, Stereo Fair Compressor)

**Returns**: 80 float values

**Example**:

```
/meters ,s meters/14
```

---

### /meters/15

**Description**: Dedicated to RTA and certain effects (e.g. Dual GEQ, Stereo GEQ)

**Returns**: 50 32-bit values (single OSC blob)

**Special format**: **Little-endian coded short integers**

**Data format**:

- Returns 100 consecutive little-endian short ints
- Range: `[0x8000, 0x0000]`
- Each short int represents an RTA dB level (range: [-128.0, 0.0])
- **Conversion formula**: `float_value = short_int / 256.0`

**Example values**:

- `0x08000c0` (short int) → two values:
    - `0x8000` → -128.0 dB (after conversion)
    - `0xc000` → -64.0 dB (after conversion)
- `0x40e0ffff` (short int) → two consecutive RTA values:
    - `-31.75 dB`
    - `-0.004 dB`

**Clipping indicator**: Short int value `0x0000` (or `0.0 dB`) → signal clipping has occurred

**Frequency mapping** (100 short ints → 100 frequencies):

| Hz     | Hz     | Hz     | Hz     | Hz     | Hz     | Hz     | Hz     | Hz     | Hz     |
| ------ | ------ | ------ | ------ | ------ | ------ | ------ | ------ | ------ | ------ |
| 20     | 21     | 22     | 24     | 26     | 28     | 30     | 32     | 34     | 36     |
| 39     | 42     | 45     | 48     | 52     | 55     | 59     | 63     | 68     | 73     |
| 78     | 84     | 90     | 96     | 103    | 110    | 118    | 127    | 136    | 146    |
| 156    | 167    | 179    | 192    | 206    | 221    | 237    | 254    | 272    | 292    |
| 313    | 335    | 359    | 385    | 412    | 442    | 474    | 508    | 544    | 583    |
| 625    | 670    | 718    | 769    | 825    | 884    | 947    | 1.02K  | 1.09K  | 1.17K  |
| 1.25K  | 1.34K  | 1.44K  | 1.54K  | 1.65K  | 1.77K  | 1.89K  | 2.03K  | 2.18K  | 2.33K  |
| 2.50K  | 2.68K  | 2.87K  | 3.08K  | 3.30K  | 3.54K  | 3.79K  | 4.06K  | 4.35K  | 4.67K  |
| 5.00K  | 5.36K  | 5.74K  | 6.16K  | 6.60K  | 7.07K  | 7.58K  | 8.12K  | 8.71K  | 9.33K  |
| 10.00K | 10.72K | 11.49K | 12.31K | 13.20K | 14.14K | 15.16K | 16.25K | 17.41K | 18.66K |

**Example**:

```
/meters ,s meters/15
```

---

### /meters/16

**Description**: Dedicated to Comp and Automix

**Returns**: 48 32-bit values (single OSC blob)

**Special format**: **Little-endian coded short integers**

**Data composition**:

**First 44 values** (32-bit values):

- 32 channel gate gains
- 32 channel comp gains
- 16 bus comp gains
- 6 matrix comp gains
- 2 (L/R and Mono) comp gains

**Data format**:

- Little-endian coded short ints
- Each short int represents a floating-point level
- Range: `[0, 1.0]`
- **Conversion formula**: `float_value = short_int / 32767.0`

**Last 4 float values**:

- 8 automix (channels 01...08) gains
- Encoded as consecutive shorts using Log₂(value) × 256

**Example**:

```
/meters ,s meters/16
```

## Practical Usage Examples

### Basic Metering

```bash
# All input channel metering
/meters ,s meters/0

# Per-channel detailed metering (including gate and dynamics)
/meters ,s meters/1

# Mix bus metering
/meters ,s meters/2
```

### Specific Channel Strip Metering

```bash
# 4 meter values for channel 1
/meters ,si meters/6 0

# 4 meter values for channel 17
/meters ,si meters/6 16

# Meter values for bus master 1
/meters ,si meters/6 48
```

### Console VU Meters

```bash
# Channels 1–16 + mix bus 1–8
/meters ,sii meters/5 0 1

# Channels 17–32 + mix bus 9–16
/meters ,sii meters/5 1 2

# aux/fx returns + matrixes
/meters ,sii meters/5 2 3
```

### Adjusting Update Frequency

```bash
# Fast updates (50 ms interval, ~200 per 10 s)
/meters ,si meters/6 0 1

# Medium speed (500 ms interval, ~20 per 10 s)
/meters ,si meters/6 0 10

# Slow updates (4 s interval, ~3 per 10 s)
/meters ,si meters/6 0 80
```

### RTA Analysis

```bash
# Receive RTA data (100 frequency bands)
/meters ,s meters/15
```

## Interpreting Meter Values

### Standard Float Meters (meters/0–14)

- **Range**: `[0.0, 1.0]`
- **Meaning**: linear audio level
- **0.0**: silence or -∞ dB
- **1.0**: full-scale (0 dBFS)
- **>1.0**: clipping (up to 8.0 = +18 dBfs, internal headroom)

**dB conversion example**:

```
float_to_db(value) = 20 × log₁₀(value)

0.001 → -60 dB
0.01  → -40 dB
0.1   → -20 dB
0.5   → -6 dB
0.75  → -2.5 dB
1.0   → 0 dBFS
```

### RTA Short Int Values (meters/15)

- **Range**: `[0x8000, 0x0000]` (little-endian short)
- **Meaning**: RTA dB level
- **Conversion**: `dB = short_int / 256.0`
- **Result range**: `[-128.0 dB, 0.0 dB]`
- **Clipping**: `0x0000` = 0.0 dB → signal clipping

### Comp/Automix Short Int Values (meters/16)

- **Range**: `[0, 0x7FFF]` (little-endian short)
- **Meaning**: gain reduction or level
- **Conversion**: `float = short_int / 32767.0`
- **Result range**: `[0.0, 1.0]`

## Notes

1. **Little-endian vs Big-endian**
    - OSC standard: Big-endian
    - Meter blob floats: **Little-endian**
    - RTA/Comp shorts: **Little-endian**

2. **Timeout management**
    - All `/meters` commands expire automatically after 10 seconds
    - Resend every 9 seconds for continuous metering

3. **Buffer overflow**
    - 50 ms update interval is very fast
    - Packet loss is possible over WiFi
    - Increase `time_factor` to reduce update frequency

4. **Data sizes**
    - `/meters/1`: 96 floats × 4 bytes = 384 bytes
    - `/meters/4`: 82 floats × 4 bytes = 328 bytes
    - `/meters/15`: 50 shorts × 2 bytes = 100 bytes (100 RTA values)

5. **Channel ID mapping** (`/meters/6`):
    ```
    0-31:   Input channels 1-32
    32-39:  Aux returns 1-8
    40-47:  FX returns 1-8
    48-63:  Bus masters 1-16
    64-69:  Matrixes 1-6
    70-71:  Main LR
    ```

## References

- [client-initiated-messages.md](./client-initiated-messages.md) - Client message list
- [server-replies.md](./server-replies.md) - Server reply list
- [examples.md](./examples.md) - Practical examples
- [OSC-Protocal.md](../OSC-Protocal.md) - OSC Protocol Core Guide