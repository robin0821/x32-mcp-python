# X32/M32 OSC Protocol Summary

## Overview

The X32 and M32 are digital mixer product lines manufactured by Behringer and Midas. They support remote control via the **OSC (Open Sound Control)** protocol.

This document is based on the "UNOFFICIAL X32-M32 OSC REMOTE PROTOCOL" (version 4.02-01, Jan 12, 2020).

## UDP Communication Specification

### Basic Port Information

- **X32/M32 series**: UDP port **10023** (default)
- **XAir series**: UDP port **10024**

### Communication Model

```
Client (app/tablet/PC) ──UDP 10023──> X32/M32 Server
Client                 <──UDP Reply── X32/M32 Server
```

- **Protocol**: UDP (User Datagram Protocol)
- **Server port**: 10023 (X32/M32 listens on this port)
- **Client port**: replies are sent back to whichever port the client used
- **Reliability**: UDP does not guarantee packet ordering or retransmission
- **Network**: wired Ethernet is recommended (beware of buffer overflows on WiFi)

### UDP Communication Notes

1. **Buffer overflow**: UDP does not report packet loss — handle with care
2. **WiFi limitation**: 54 Mbps WiFi can drop packets under heavy data load
3. **Recommended connection**: 100 Mbps wired Ethernet
4. **Timeout**: most subscription commands expire automatically after 10 seconds

## OSC Message Format

### Basic Structure

An OSC message is composed as follows:

```
[OSC Address Pattern (4-byte aligned)] + [Type Tag String (4-byte aligned)] + [Arguments (4-byte aligned)]
```

All data is:

- **Big-endian** byte order
- **4-byte aligned/padded** (padded with null bytes)
- Compliant with OSC 1.0 specification

### OSC Type Tags

| Type Tag | Description             | Range / Format         |
| -------- | ----------------------- | ---------------------- |
| `i`      | 32-bit integer (signed) | Integer value          |
| `f`      | 32-bit float (signed)   | 0.0 – 1.0              |
| `s`      | String                  | Null-terminated        |
| `b`      | Blob                    | Arbitrary binary data  |

### Message Examples

#### 1. Simple Request (no arguments)

```
/info~~~,~~~
```

- `~~~` represents null bytes (\0)
- Type tag string: `,~~~` (empty argument list)

Example reply (X32 Standard):

```
/info~~~,ssss~~~V2.05~~~osc-server~~X32~2.12~~~~
```

#### 2. Single Argument

```
/ch/01/config/name~~,s~~name~~~~
```

- Address: `/ch/01/config/name`
- Type tag: `,s` (one string)
- Argument: `name`

#### 3. Multiple Arguments

```
/ch/01/eq/1 ,ifff [2] [0.2650] [0.5000] [0.4648]
```

- Address: `/ch/01/eq/1`
- Type tag: `,ifff` (one int + three floats)
- Arguments: `2, 0.2650, 0.5000, 0.4648`

#### 4. Hexadecimal Representation Example

```
/ch/01/eq/1/q~~~,f~~[0.4648]
```

Hex:

```
2f63682f30312f65712f312f710000002c6600003eedfa44
```

Breakdown:

- `2f63682f30312f65712f312f71000000`: `/ch/01/eq/1/q` + padding
- `2c660000`: `,f` + padding
- `3eedfa44`: 0.4648 (big-endian float)

### Float Value Encoding

Floats are 32-bit big-endian values in the range 0.0 – 1.0:

```
0.0 = 0x00000000
0.5 = 0x3f000000
1.0 = 0x3f800000
```

### Enum Type

Enums can be sent as a string or an integer:

```
/ch/01/gate/mode~~~~,s~~GATE~~~~
```

or

```
/ch/01/gate/mode~~~~,i~~[3]
```

## Communication Modes

### 1. Immediate Mode

The server responds immediately to a client request:

```
Client: /ch/01/mix/fader~~~,~~~
Server: /ch/01/mix/fader~~~,f~~[0.8250]
```

### 2. Deferred Mode

Use the `/xremote` command to automatically receive change notifications:

```
Client: /xremote~~~,~~~
Server: (automatically sends changes, 10-second timeout)
```

- Whenever a parameter changes on the X32/M32, the change is automatically pushed to all registered clients
- The `/xremote` command must be re-sent every 10 seconds to keep the subscription alive

### 3. Subscription Mode

Receive periodic updates for a specific parameter:

```
/subscribe ,si /ch/01/mix/on 10
```

- Receive approximately 20 updates over 10 seconds (when factor is 10)

## Key OSC Commands

| Command          | Description                          | Example                          |
| ---------------- | ------------------------------------ | -------------------------------- |
| `/info`          | Query X32/M32 version information    | `/info~~~,~~~`                   |
| `/status`        | Query current status                 | `/status~,~~~`                   |
| `/xremote`       | Enable auto-update subscription (10s)| `/xremote~~~,~~~`                |
| `/subscribe`     | Subscribe to a specific parameter    | `/subscribe ,si /ch/01/mix/on 1` |
| `/node`          | Query X32 node data                  | `/node~~~,s~~ch/01`              |
| `/meters/[0-16]` | Request metering data                | `/meters/0`                      |
| `/ch/[01-32]/*`  | Channel-related commands             | `/ch/01/mix/fader~~~,f~~[0.75]`  |
| `/bus/[01-16]/*` | Bus-related commands                 | `/bus/01/mix/on~~~,i~~[1]`       |
| `/main/st/*`     | Main stereo commands                 | `/main/st/mix/fader~~~,f~~[0.8]` |

## Multiple Client Management

- The X32/M32 supports **multiple simultaneous UDP clients**
- Each client must independently register with `/xremote`
- Changes made by one client are propagated to all registered clients

## Address Pattern Structure

Key address patterns:

```
/ | /-action | /add | /auxin | /batchsubscribe | /bus | /ch | /config |
/copy | /dca | /delete | /formatsubscribe | /fx | /fxrtn | /headamp |
/info | /-insert | /-libs | /load | /main/m | /main/st | /meters | /mtx |
/node | /outputs | /renew | /save | /-show | /-snap | /-stat | /status |
/subscribe | /unsubscribe | /undo | /urec | /xinfo | /xremote | /xremoteinfo
```

### Channel Structure Examples

```
/ch/[01-32]/config/name        - Channel name
/ch/[01-32]/mix/fader          - Fader level
/ch/[01-32]/mix/on             - Channel on/off
/ch/[01-32]/mix/pan            - Panning
/ch/[01-32]/eq/[1-4]/*         - EQ settings
/ch/[01-32]/gate/*             - Gate settings
/ch/[01-32]/dyn/*              - Dynamics settings
```

## References

- OSC specification: http://opensoundcontrol.org/
- X32_Command utility: https://sites.google.com/site/patrickmaillot/x32
- GitHub repository: https://github.com/pmaillot/X32-Behringer

## Example Code (C / UDP Connection)

```c
#include <sys/socket.h>
#include <netinet/in.h>
#include <string.h>

// X32 connection setup
int Xfd;
struct sockaddr_in Xip;

// X32 IP and port
char Xip_str[] = "192.168.0.64";
char Xport_str[] = "10023";

// Create UDP socket
Xfd = socket(PF_INET, SOCK_DGRAM, IPPROTO_UDP);

// Configure server address struct
memset(&Xip, 0, sizeof(Xip));
Xip.sin_family = AF_INET;
Xip.sin_port = htons(atoi(Xport_str));
inet_pton(AF_INET, Xip_str, &Xip.sin_addr);

// Send data
sendto(Xfd, buffer, len, 0, (struct sockaddr*)&Xip, sizeof(Xip));

// Receive data
recvfrom(Xfd, buffer, bufsize, 0, NULL, NULL);
```

## License and Disclaimer

This is an unofficial document and is not supported by Behringer or Midas. Every effort has been made for accuracy, but errors or inaccuracies may exist.

Original document by: Patrick-Gilles Maillot (version 4.02-01, Jan 12, 2020)