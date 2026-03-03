# Server Replies or Server Initiated Messages (X32 Console → Client)

List of responses and automatic messages sent from the X32/M32 console to clients.

## Information Query Responses

### Info Request Response

| Operation    | OSC Address | Parameters                                                                                                    | Comments                                                                                                                            |
| ------------ | ----------- | ------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| Info request | `/info`     | `<string server_version>`<br>`<string server_name>`<br>`<string console_model>`<br>`<string console_version>` | Returns names and version numbers, e.g.:<br>`/info~~~,ssss~~~V2.05~~~osc-server~~X32C~~2.08~~~~`<br>(`~` stands for null character) |

**Response examples:**

```
/info~~~,ssss~~~V2.05~~~osc-server~~X32~2.12~~~~
/info~~~,ssss~~~V2.05~~~osc-server~~X32RACK~2.12~~~~
/info~~~,ssss~~~V2.05~~~osc-server~~X32C~~2.12~~~~
/info~~~,ssss~~~V2.05~~~osc-server~~X32P~2.12~~~~
/info~~~,ssss~~~V2.05~~~osc-server~~M32~2.12~~~~
/info~~~,ssss~~~V2.05~~~osc-server~~M32C~2.12~~~~
```

**Parameter descriptions:**

- `server_version`: server version (e.g. "V2.05")
- `server_name`: server name (e.g. "osc-server")
- `console_model`: console model (e.g. "X32", "X32C", "M32", "X32RACK")
- `console_version`: console firmware version (e.g. "2.12")

### XInfo Request Response

| Operation     | OSC Address | Parameters                                                                                                      | Comments                                                                                             |
| ------------- | ----------- | --------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| XInfo request | `/xinfo`    | `<string network_address>`<br>`<string network_name>`<br>`<string console_model>`<br>`<string console_version>` | Returns network information, e.g.:<br>`/xinfo~~,ssss~~~192.168.1.62~~~~X32-02-4A-53~~~~X32~3.04~~~~` |

**Response example:**

```
/xinfo~~,ssss~~~192.168.1.62~~~~X32-02-4A-53~~~~X32~3.04~~~~
```

**Parameter descriptions:**

- `network_address`: IP address (e.g. "192.168.1.62")
- `network_name`: network name / hostname (e.g. "X32-02-4A-53")
- `console_model`: console model (e.g. "X32")
- `console_version`: console version (e.g. "3.04")

### Status Request Response

| Operation      | OSC Address | Parameters                                                          | Comments                                                                                                                          |
| -------------- | ----------- | ------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| Status request | `/status`   | `<string state>`<br>`<string IP_address>`<br>`<string server_name>` | Returns console status and IP, e.g.:<br>`/status~,sss~~~~active~~192.168.0.64~~~~osc-server~~`<br>(`~` stands for null character) |

**Response example:**

```
/status~,sss~~~~active~~192.168.0.64~~~~osc-server~~
```

**Parameter descriptions:**

- `state`: console state (e.g. "active")
- `IP_address`: console IP address (e.g. "192.168.0.64")
- `server_name`: server name (e.g. "osc-server")

## Console Change Notifications

### Console Changes

| Operation       | OSC Address             | Parameters                 | Comments                                                                                                                                                                                                                                                                |
| --------------- | ----------------------- | -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Console changes | `<OSC Address Pattern>` | `<string \| int \| float>` | **If `/xremote` is active**, the X32 console echoes the value of a console parameter in response to a set command from another client or X32 parameter change, e.g.<br><br>`/-stat/solosw/01~~~~,i~~[1]`<br>`/-stat/solo~,i~~[1]`<br>`/ch/01/mix/01/pan~~~,f~~[1.0000]` |

**Important:**

- `/xremote` must be active to receive change notifications automatically
- Includes both commands from other clients and changes made directly on the X32 console
- All UI changes are sent: fader moves, bank changes, screen updates, etc.

**Examples:**

When a Solo switch is toggled on the console:

```
/-stat/solosw/01~~~~,i~~[1]
/-stat/solo~,i~~[1]
```

When another client changes the panning:

```
/ch/01/mix/01/pan~~~,f~~[1.0000]
```

When a channel fader is moved:

```
/ch/01/mix/fader~~~,f~~[0.7500]
```

When a channel mute is toggled:

```
/ch/01/mix/on~~~,i~~[0]
```

## Parameter Get Responses

When a client queries (Get) a parameter, the server responds with the current value at the same address.

**Request:**

```
/ch/01/mix/fader~~~,~~~
```

**Response:**

```
/ch/01/mix/fader~~~,f~~[0.8250]
```

**Request:**

```
/bus/05/mix/on~~~,~~~
```

**Response:**

```
/bus/05/mix/on~~~,i~~[1]
```

## Subscription Data Responses

### Subscribe Response

When a specific parameter is subscribed to via `/subscribe`, it is automatically sent whenever that parameter changes.

**Subscription request:**

```
/subscribe ,si /-stat/solosw/01 10
```

**Response (approximately 20 times over 10 seconds):**

```
/-stat/solosw/01~~~~,i~~[0]
/-stat/solosw/01~~~~,i~~[1]
/-stat/solosw/01~~~~,i~~[0]
...
```

### BatchSubscribe Response

When multiple parameters are subscribed to at once via `/batchsubscribe`, data is sent in blob format.

**Subscription request:**

```
/batchsubscribe ,ssiii /x_meters_0 /meters/0 0 69 1
```

**Response:**

- A blob containing 70 float values (sent for approximately 10 seconds)

### Meters Response

When metering data is requested via `/meters`, meter values in blob format are sent at regular intervals.

**Request:**

```
/meters ,s meters/1
```

**Response:**

- 96 float meter values (32 input, 32 gate, 32 dynamic gain reductions)
- Sent in bursts for approximately 10 seconds

## X32 Node Responses

### Node Data Response

When X32 node data is requested via `/node`, the full set of parameters for that node is returned as a string.

**Request:**

```
/node~~~,s~~ch/01~~~~
```

**Response:**

```
node~~~,s~~ch/01 "Vocal" 10 CY 1~~~~
```

The response is in plain text format (string of characters, ending with a linefeed).

## Echo Back

The X32/M32 echoes back received commands to support data flow control.

**Client sends:**

```
/ch/01/mix/fader ,f 0.75
```

**Server echoes back:**

```
/ch/01/mix/fader ,f 0.75
```

This allows applications to:

1. Confirm that a command was successfully transmitted
2. Read the UDP buffer before sending the next command (preventing overrun)
3. Control data flow

## Timeout and Automatic Expiry

All subscription commands expire automatically after 10 seconds:

| Command            | Timeout | Renewal Method                                              |
| ------------------ | ------- | ----------------------------------------------------------- |
| `/xremote`         | 10 s    | Resend `/xremote` every 9 seconds                           |
| `/subscribe`       | 10 s    | `/renew ,s <address>` or resend `/subscribe`                |
| `/formatsubscribe` | 10 s    | `/renew ,s <name>` or resend `/formatsubscribe`             |
| `/batchsubscribe`  | 10 s    | `/renew ,s <name>` or resend `/batchsubscribe`              |
| `/meters`          | 10 s    | Resend `/meters`                                            |

## Response Format Summary

| Data Type | Format                             | Example                          |
| --------- | ---------------------------------- | -------------------------------- |
| String    | null-terminated, 4-byte padded     | `"Vocal"~~~~`                    |
| Integer   | 32-bit signed, big-endian          | `[1]`, `[0]`                     |
| Float     | 32-bit signed, big-endian, 0.0~1.0 | `[0.7500]`, `[1.0000]`           |
| Blob      | Binary data, length-prefixed       | Meter data, batch subscribe data |

## References

- [client-initiated-messages.md](./client-initiated-messages.md) - Client → Server messages
- [multiple-client-management.md](./multiple-client-management.md) - Multi-client management
- [OSC-Protocal.md](../OSC-Protocal.md) - OSC Protocol Core Guide