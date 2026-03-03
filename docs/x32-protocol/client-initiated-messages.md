# Client Initiated Messages (Client → X32 Console)

List of messages sent by a client to the X32/M32 console.

## Basic Information Queries

### Info Request

| Operation    | OSC Address | Parameters | Comments                              |
| ------------ | ----------- | ---------- | ------------------------------------- |
| Info request | `/info`     | None       | Server responds with `/info` message  |
|              | `/xinfo`    | None       | Server responds with `/xinfo` message |

### Status Request

| Operation      | OSC Address | Parameters | Comments                               |
| -------------- | ----------- | ---------- | -------------------------------------- |
| Status request | `/status`   | None       | Server responds with `/status` message |

## Parameter Control

### Set X32 Parameter

| Operation         | OSC Address             | Parameters                               | Comments                                                                                                                                                   |
| ----------------- | ----------------------- | ---------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Set X32 parameter | `<OSC Address Pattern>` | `<string \| int \| float \| blob value>` | Sets the value of a console parameter, e.g.: `/ch/01/mix/fader~~~,f~~<float>`<br>If it exists and value is in range, the new value takes place in the X32. |

**Examples:**

```
/ch/01/mix/fader ,f 0.75
/bus/01/mix/on ,i 1
/ch/01/config/name ,s "Vocal"
```

### Get X32 Parameter

| Operation         | OSC Address             | Parameters | Comments                                                                                                                                                                                   |
| ----------------- | ----------------------- | ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Get X32 parameter | `<OSC Address Pattern>` | None       | Requests the value of a console parameter, e.g. `/ch/01/mix/fader~~~~`<br>If it exists, the current value is echoed back by server, e.g.: `/ch/01/mix/fader~~~,f~~<float>` |

**Examples:**

```
Request:  /ch/01/mix/fader
Response: /ch/01/mix/fader ,f 0.75
```

## X32 Node Control

### Set X32 Node Data

| Operation         | OSC Address | Parameters | Comments                                                                                                                                                                                          |
| ----------------- | ----------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Set X32 node data | `/`         | `<string>` | Updates the values of a set of console parameters. A full set of X32node values can be sent to the server as plain text and matching `/node` formats, e.g.: `/~~~,s~~prefs/iQ/01 none Linear 0~~` |

### Get X32 Node Data

| Operation         | OSC Address | Parameters | Comments                                                                                                                                                                                                                                                                                                  |
| ----------------- | ----------- | ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Get X32 node data | `/node`     | `<string>` | Requests the values of a set of console parameters, e.g.: `/node~~~,s~~prefs/iQ/01~~~~`<br>The current values for the full set corresponding to the request are returned by the server in plain text (string of characters, ending with a linefeed), e.g.: `node~~~,s~~/-prefs/iQ/01 none Linear 0\n~~~~` |

## Metering

### Get X32 Meters

| Operation      | OSC Address | Parameters                                                                                                   | Comments                                                                                                                                                                                                                                                                  |
| -------------- | ----------- | ------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Get X32 meters | `/meters`   | `<string>`<br>`<optional int: chn_meter_id>`<br>`<optional int: grp_meter_id>`<br>`<optional int: priority>` | Results in regular updates meter values as a single binary blob. Timeout is 10 seconds, e.g. `/meters ,s meters/1` will return bursts of 96 float meter values (32 input, 32 gate and 32 dynamic gain reductions) for 10s.<br>See "Meter requests" for additional details |

**Examples:**

```
/meters ,s meters/0    # Basic metering
/meters ,s meters/1    # Input/gate/dynamics metering (96 floats)
```

## Subscriptions

### Subscribe to Data

| Operation                  | OSC Address  | Parameters                | Comments                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| -------------------------- | ------------ | ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Subscribe to data from X32 | `/subscribe` | `<string> <optional int>` | Client describes to X32 server what information it is interested in receiving, and at which frequency the update is reported, until a timeout of 10 seconds is reached.<br><br>**Examples:**<br>`/subscribe ,s /-stat/solosw/01`<br>or<br>`/subscribe ,si /-stat/solosw/01 1`<br>Will report about 200 updates of the state of solo switch for channel 01 over the span of 10s.<br><br>`/subscribe ,si /-stat/solosw/01 50`<br>Will report about 4 updates of the state of solo switch for channel 01 |

**Time Factor Table:**

| Factor | Updates (over 10 seconds) |
| ------ | ------------------------- |
| 0      | ~200                      |
| 1      | ~200                      |
| 10     | ~20                       |
| 50     | ~4                        |

### Subscribe to Data Formats

| Operation                 | OSC Address        | Parameters                         | Comments                                                                                                                                                                                                                                                |
| ------------------------- | ------------------ | ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Subscribe to data formats | `/formatsubscribe` | `<string>...<string><int>...<int>` | Client describes to X32 server what information it is interested in receiving, e.g.:<br>`/formatsubscribe ,ssiii /mfm_c /dca/*/on 1 8 8`<br>Reports a blob of 36 bytes for about 10s.<br>The last `<int>` specifies the frequency factor of the report. |

### Subscribe to Batch Data

| Operation                           | OSC Address       | Parameters                         | Comments                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| ----------------------------------- | ----------------- | ---------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Subscribe to batch data from server | `/batchsubscribe` | `<string>...<string><int>...<int>` | Client request from X32 server data to receive, e.g.:<br>`/batchsubscribe ,ssiii /x_meters_0 /meters/0 0 69 1`<br>Reports a blob of 70 floats for about 10s.<br><br>`/batchsubscribe ,ssiii /x_meters_8 /meters/8 0 5 1`<br>Reports a blob of 6 floats for about 10s.<br><br>`/batchsubscribe ,ssiii /mfm_a /mix/on 0 63 8`<br>Reports a blob of 276 bytes for about 10s.<br><br>The last `<int>` specifies the frequency factor of the report. |

## Subscription Management

### Renew Data Request

| Operation          | OSC Address | Parameters | Comments                                                                                                                |
| ------------------ | ----------- | ---------- | ----------------------------------------------------------------------------------------------------------------------- |
| Renew data request | `/renew`    | `<string>` | Requests renewing of data described in `<string>`, e.g.<br>`/renew~~,s~~meters/5~~~~`<br>`/renew~~,s~~hidden/states~~~` |

### Register for Updates

| Operation            | OSC Address | Parameters | Comments                                                                                                                                                                                                                         |
| -------------------- | ----------- | ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Register for updates | `/xremote`  | None       | **Triggers X32 to send all parameter changes to maximum four active clients.** Timeout is 10 seconds, e.g. the `/xremote` command has to be renewed before this delay in order to avoid losing information from The X32 console. |

**Important:**

- `/xremote` supports **up to 4 active clients simultaneously**
- Has a 10-second timeout — resending every 9 seconds is recommended
- Receives all parameter change events generated on the X32/M32

## Message Format Examples

### Read (Get) Requests

```
/ch/01/mix/fader          # No parameters
/bus/05/mix/on            # No parameters
/main/st/mix/fader        # No parameters
```

### Write (Set) Requests

```
/ch/01/mix/fader ,f 0.75        # float value
/ch/01/mix/on ,i 1              # integer value
/ch/01/config/name ,s "Vocal"   # string value
/ch/01/eq/1 ,ifff 2 0.265 0.5 0.465  # multiple values
```

### Subscribe Requests

```
/subscribe ,s /-stat/solosw/01          # default (~200 updates)
/subscribe ,si /-stat/solosw/01 1       # ~200 updates
/subscribe ,si /-stat/solosw/01 10      # ~20 updates
/subscribe ,si /-stat/solosw/01 50      # ~4 updates
```

### X32 Node Requests

```
# Read
/node ,s ch/01

# Write
/ ,s ch/01 newname 10 CY 1
```

## Notes

1. **Timeout**: All subscription commands (`/subscribe`, `/formatsubscribe`, `/batchsubscribe`, `/xremote`) expire automatically after 10 seconds
2. **Renewal**: Resend `/renew` or the same command within 10 seconds to keep the subscription active
3. **Client limit**: `/xremote` supports up to 4 simultaneous clients
4. **Response format**: The server echoes back received commands to support data flow control
5. **Parameter validation**: Values outside the valid range are rejected or rounded to the nearest valid value

## References

- [OSC-Protocal.md](../OSC-Protocal.md) - OSC Protocol Core Guide
- [X32-OSC-Protocol-Summary.md](../X32-OSC-Protocol-Summary.md) - Full Protocol Summary