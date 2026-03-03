# X32/M32 OSC Protocol Practical Examples

This document covers practical usage examples of the X32/M32 OSC protocol.

## Float Type — Detailed Examples

### Volume Fader Control

Setting channel 01 volume to 3 dB:

**OSC standard notation (0.0 ~ 1.0 range):**

```
/ch/01/mix/fader~~~,f~~[0.8250]
```

**Hex representation:**

```
2f63682f30312f6d69782f66616465720000002c6600003f5334cd
```

Breakdown:

- `2f63682f30312f6d69782f6661646572000000`: `/ch/01/mix/fader` + padding
- `2c660000`: `,f` + padding
- `3f5334cd`: 0.8250 as 32-bit float (big-endian)

### Pan Control

Setting channel 02 pan to "half right" (50% right):

**OSC standard notation:**

```
/ch/02/mix/pan~~,f~~[0.7500]
```

**Hex representation:**

```
2f63682f30322f6d69782f70616e00002c6600003f400000
```

Breakdown:

- `2f63682f30322f6d69782f70616e0000`: `/ch/02/mix/pan` + padding
- `2c660000`: `,f` + padding
- `3f400000`: 0.7500 as 32-bit float (big-endian)

## X32 Node Style Notation

Floats in **standard OSC commands** are mapped to the [0.0 ~ 1.0] range, but **X32 node style commands** can use the **actual value range**.

### Setting Volume Fader in X32 Node Style

Set channel 01 volume to 3 dB (using actual range):

```
/~~~,s~~ch/01/mix/fader 3~~
```

**Hex representation:**

```
2f0000002c7300002f63682f30312f6d69782f666164657220666616465722203313000
```

**Volume range**: [-90 dB, +10 dB, 1024 steps] → pseudo-logarithmic scale (-90 dB ~ +10 dB)

**Additional examples:**

| Target dB | Float (OSC) | Hex (float part) | X32 node notation |
| --------- | ----------- | ---------------- | ----------------- |
| +10 dB    | 1.0         | `3f800000`       | `10`              |
| 0 dB      | ~0.75       | (varies)         | `0`               |
| -5 dB     | ~0.72       | `2d3500`         | `-5`              |
| -90 dB    | 0.0         | `00000000`       | `-90`             |
| -20.5 dB  | ~0.63       | `2d32302e35`     | `-20.5`           |

**Command examples:**

```
/~~~,s~~ch/01/mix/fader 10~        # +10 dB
/~~~,s~~ch/01/mix/fader 0~~        # 0 dB
/~~~,s~~ch/01/mix/fader -5~        # -5 dB
/~~~,s~~ch/01/mix/fader -90~~~~    # -90 dB (minimum)
/~~~,s~~ch/01/mix/fader -20.5~~    # -20.5 dB
```

### Setting Pan in X32 Node Style

Set channel 02 pan to "right, 50% level":

```
/~~~,s~~ch/02/mix/pan 50~~
```

**Hex representation:**

```
2f0000002c7300002f63682f30322f6d69782f70616e203530353400000
```

**Pan range**: [-100.0, +100.0, step 2.0] → linear scale

- `-100.0`: full left
- `0.0`: centre
- `+100.0`: full right
- Step: 2.0 (e.g. -100, -98, -96, ..., 0, ..., 98, 100)

## Multiple Argument Command Examples

### EQ Settings (Multiple Parameters)

Setting EQ band 1 on channel 01:

**Single command (recommended):**

```
/ch/01/eq/1 ,ifff [2] [0.2650] [0.5000] [0.4648]
```

**Separate commands (equivalent):**

```
/ch/01/eq/1/t~~~,i~~[2]          # Type (enum: 2)
/ch/01/eq/1/f~~~,f~~[0.2650]     # Frequency
/ch/01/eq/1/g~~~,f~~[0.5000]     # Gain
/ch/01/eq/1/q~~~,f~~[0.4648]     # Q factor
```

**Hex representation (last command — Q factor):**

```
/  c  h  /  0  1  /  e  q  /  1  /  q  ~  ~  ~  ,  f  ~  ~ [0.4648]
2f 63 68 2f 30 31 2f 65 71 2f 31 2f 71 00 00 00 2c 66 00 00 3eedfa44
```

Parameter breakdown:

- **Type (t)**: Integer, EQ type (0=LCut, 1=LShv, 2=PEQ, 3=VEQ, 4=HShv, 5=HCut)
- **Frequency (f)**: Float, frequency (20 Hz ~ 20 kHz, 201 steps)
- **Gain (g)**: Float, gain (-15 dB ~ +15 dB)
- **Q factor (q)**: Float, Q value (0.3 ~ 10.0)

## Enum Type Examples

### Sending an Enum as a String

Set gate mode to "GATE":

```
/ch/01/gate/mode~~~~,s~~GATE~~~~
```

**Hex:**

```
2f63682f30312f676174652f6d6f6465000000002c7300004741544500000000
```

Breakdown:

- `2f63682f30312f676174652f6d6f6465000000`: `/ch/01/gate/mode` + padding
- `2c730000`: `,s` + padding
- `47415445`: "GATE" (ASCII)
- `00000000`: null termination + padding

### Sending an Enum as an Integer

Same command using an integer index:

```
/ch/01/gate/mode~~~~,i~~[3]
```

**Hex:**

```
2f63682f30312f676174652f6d6f6465000000002c69000000000003
```

Breakdown:

- `2f63682f30312f676174652f6d6f6465000000`: `/ch/01/gate/mode` + padding
- `2c690000`: `,i` + padding
- `00000003`: integer 3 (big-endian)

**Enum values:**

- `0`: EXP2
- `1`: EXP3
- `2`: EXP4
- `3`: GATE
- `4`: DUCK

## X32/M32 Response Examples

### /info Response — Detailed

**Request:**

```
/info~~~,~~~
```

**X32 Standard response:**

```
/info~~~,ssss~~~V2.05~~~osc-server~~X32~2.10~~~~
```

**Hex breakdown:**

```
2f696e666f000000                    # /info + padding
2c73737373000000                    # ,ssss + padding
5632 2e30 3500 0000                 # "V2.05" + null + padding
6f73 632d 7365 7276 6572 0000      # "osc-server" + null + padding
5833 3200 0000 0000                 # "X32" + null + padding
322e 3130 0000 0000                 # "2.10" + null + padding
```

### /status Response — Detailed

**Request:**

```
/status~,~~~
```

**Response:**

```
/status~,sss~~~~active~~192.168.0.64~~~~osc-server~~
```

**Hex breakdown:**

```
2f73746174757300                    # /status + padding
2c737373000000                      # ,sss + padding
6163746976650000                    # "active" + null + padding
3139322e3136382e302e363400000000   # "192.168.0.64" + null + padding
6f73632d7365727665720000           # "osc-server" + null + padding
```

### Parameter Get/Set Response

**Get request:**

```
/fx/4/par/23~~~~,~~~
```

**Response:**

```
/fx/4/par/23~~~~,f~~[0.5]
```

**Hex (response):**

```
/  f  x  /  4  /  p  a  r  /  2  3  ~  ~  ~  ~  ,  f  ~  ~ [0.5]
2f 66 78 2f 34 2f 70 61 72 2f 32 33 00 00 00 00 2c 66 00 00 3f000000
```

Breakdown:

- `2f66782f342f7061722f3233000000`: `/fx/4/par/23` + padding
- `2c660000`: `,f` + padding
- `3f000000`: 0.5 as 32-bit float (big-endian)

## Subscribe Examples

### Basic Subscription

Subscribe to solo switch state (channel 01):

```
/subscribe ,si /-stat/solosw/01 1
```

**Server response (approximately 200 times over 10 seconds):**

```
/-stat/solosw/01~~~~,i~~[0]
/-stat/solosw/01~~~~,i~~[1]
/-stat/solosw/01~~~~,i~~[0]
...
```

### Low-Frequency Subscription

```
/subscribe ,si /-stat/solosw/01 50
```

**Server response (approximately 4 times over 10 seconds):**

```
/-stat/solosw/01~~~~,i~~[1]
(after 2.5s)
/-stat/solosw/01~~~~,i~~[1]
(after 2.5s)
/-stat/solosw/01~~~~,i~~[0]
(after 2.5s)
/-stat/solosw/01~~~~,i~~[0]
```

## /xremote Examples

### Registering for Auto-Updates

**Registration request:**

```
/xremote~~~,~~~
```

**Auto-push (on fader move):**

```
/ch/01/mix/fader~~~,f~~[0.7500]
/ch/01/mix/fader~~~,f~~[0.7510]
/ch/01/mix/fader~~~,f~~[0.7520]
...
```

**Auto-push (on mute toggle):**

```
/ch/01/mix/on~~~,i~~[0]
/-stat/solosw/01~~~~,i~~[0]
```

**Auto-push (on channel name change):**

```
/ch/01/config/name~~,s~~Vocal~~~~
```

## X32 Node Command Examples

### Reading Node Data

**Request:**

```
/node~~~,s~~ch/01~~~~
```

**Response:**

```
node~~~,s~~ch/01 "Vocal" 10 CY 1~~~~
```

Response parameters:

- `ch/01`: node path
- `"Vocal"`: channel name
- `10`: icon number
- `CY`: colour code (Cyan/Yellow)
- `1`: source number

### Writing Node Data

**Single parameter update:**

```
/~~~,s~~ch/01 NewName~~~~
```

**Full configuration update:**

```
/~~~,s~~ch/01 "Guitar" 15 RD 2~~~~
```

## Useful Conversion Tables

### Float → dB Conversion (Volume Fader)

| Float | dB                 | Use Case       |
| ----- | ------------------ | -------------- |
| 0.00  | -∞ (or -90 dB)     | Full mute      |
| 0.25  | ~-60 dB            | Very quiet     |
| 0.50  | ~-30 dB            | Quiet          |
| 0.75  | ~0 dB              | Unity gain     |
| 0.82  | ~+3 dB             | Slightly louder|
| 1.00  | +10 dB             | Maximum        |

### Float → Pan Conversion

| Float | Pan Position | Description  |
| ----- | ------------ | ------------ |
| 0.00  | -100 (L100)  | Full left    |
| 0.25  | -50 (L50)    | 50% left     |
| 0.50  | 0 (C)        | Centre       |
| 0.75  | +50 (R50)    | 50% right    |
| 1.00  | +100 (R100)  | Full right   |

## Notes

### X32/M32 "node" Command Special Rules

When a string (`,s`) is sent as a node address in the X32/M32 "node" command, it is interpreted differently (intended for internal X32-edit use).

Therefore the following command:

```
/ch/[01..32]/config ,siii [name] [1] [3] [1]
```

is semantically valid and OSC-compliant, but **does not work on X32/M32**.

This **does work correctly on XAir series**.

**Correct approach (X32/M32):**

```
/ch/01/config/name ,s Vocal
/ch/01/config/icon ,i 1
/ch/01/config/color ,i 3
/ch/01/config/source ,i 1
```

Or using X32 node style:

```
/~~~,s~~ch/01/config Vocal 1 3 1
```

## Debugging Tips

### Interpreting Hex Dumps

When debugging OSC messages in hex:

1. **Find the address**: starts with `/` (2f)
2. **Find the type tag**: starts with `,` (2c)
3. **Check 4-byte boundaries**: look for 00-padded sections
4. **Float values**: always 4 bytes (e.g. 3f000000 = 0.5)
5. **Integer values**: always 4 bytes (e.g. 00000001 = 1)
6. **String values**: null-terminated, 4-byte aligned

### Common Mistakes

1. **Missing type tag**: prefer `/info~~~,~~~` over `/info`
2. **Float out of range**: using values outside 0.0 ~ 1.0
3. **Missing padding**: not observing 4-byte alignment
4. **Endianness error**: must use big-endian, not little-endian
5. **Missing string null termination**: strings must end with \0

## References

- [OSC-Protocal.md](../OSC-Protocal.md) - OSC Protocol Core Guide
- [client-initiated-messages.md](./client-initiated-messages.md) - Client message list
- [server-replies.md](./server-replies.md) - Server reply list
- [X32-OSC-Protocol-Summary.md](../X32-OSC-Protocol-Summary.md) - Full Protocol Summary