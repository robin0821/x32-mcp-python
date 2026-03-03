# Multiple Client Management

## Overview

A single X32/M32 can manage updates to and from multiple simultaneous UDP clients.

## Basic Principle

To stay in sync with changes occurring at the X32 level — whether changes made directly on the desk or changes requested by another remote client — **each client must register to receive updates from the X32**.

This is done via the `/xremote` command.

## /xremote Command

### Basic Behaviour

After receiving an `/xremote` command, the X32 sends the following changes to the client:

**Changes that are sent:**

- Fader movements
- Bank change requests
- Screen updates
- All parameter changes

**Changes that are not sent:**

- Changes with no direct impact on the connected client
- Changes strictly local to the X32/M32
- Example: pressing one of the view buttons on a Standard X32/M32

### Timeout and Renewal

**Important**: Registration for desk updates is maintained for **10 seconds only** after the `/xremote` command.

- **Timeout**: 10 seconds
- **Recommended renewal interval**: resend `/xremote` every 9 seconds
- **If not renewed**: the update process stops automatically and information is lost

### Command Format

```
/xremote~~~,~~~
```

**Parameters**: none

## Usage Examples

### Basic Registration

```javascript
// Initial registration
send('/xremote');

// Renew every 9 seconds
setInterval(() => {
    send('/xremote');
}, 9000);
```

### Python Example

```python
import socket
import time
from threading import Thread

def keep_xremote_alive(sock, x32_address):
    """Function to maintain the X32 connection"""
    while True:
        # Send /xremote command
        message = b'/xremote\x00\x00\x00,\x00\x00\x00'
        sock.sendto(message, x32_address)
        # Wait 9 seconds
        time.sleep(9)

# Create UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
x32_address = ('192.168.1.100', 10023)

# Keep /xremote alive in a background thread
thread = Thread(target=keep_xremote_alive, args=(sock, x32_address), daemon=True)
thread.start()

# Receive updates in the main loop
while True:
    data, addr = sock.recvfrom(1024)
    # Process update
    print(f"Received: {data}")
```

### Node.js Example

```javascript
const dgram = require('dgram');
const osc = require('osc-min');

const client = dgram.createSocket('udp4');
const X32_HOST = '192.168.1.100';
const X32_PORT = 10023;

// Function to send /xremote
function sendXremote() {
    const buf = osc.toBuffer({
        address: '/xremote',
        args: []
    });
    client.send(buf, 0, buf.length, X32_PORT, X32_HOST);
}

// Initial registration
sendXremote();

// Renew every 9 seconds
setInterval(sendXremote, 9000);

// Receive updates
client.on('message', (msg, rinfo) => {
    try {
        const oscMsg = osc.fromBuffer(msg);
        console.log('Received:', oscMsg.address, oscMsg.args);
    } catch (err) {
        console.error('OSC parse error:', err);
    }
});
```

## Other Subscription Methods

In addition to `/xremote`, other commands can be used to receive regular updates from the server.

See the **"Subscribing to X32/M32 Updates"** section for details.

| Command            | Description                     | Timeout |
| ------------------ | ------------------------------- | ------- |
| `/subscribe`       | Subscribe to a specific param   | 10 s    |
| `/formatsubscribe` | Format-based subscription       | 10 s    |
| `/batchsubscribe`  | Batch parameter subscription    | 10 s    |
| `/meters`          | Meter data subscription         | 10 s    |

## Multi-Client Scenarios

### Simultaneous Connections

The X32/M32 supports simultaneous connections from multiple clients.

**Example scenario:**

```
Client A (iPad)  ──┐
Client B (PC)    ──┼──> X32/M32 Console
Client C (Phone) ──┘
```

### Change Propagation

1. **Client A** changes the fader on channel 1

    ```
    Client A → X32: /ch/01/mix/fader ,f 0.75
    ```

2. **X32** sends the change to all registered clients

    ```
    X32 → Client A: /ch/01/mix/fader ,f 0.75
    X32 → Client B: /ch/01/mix/fader ,f 0.75
    X32 → Client C: /ch/01/mix/fader ,f 0.75
    ```

3. The same applies to changes made on the **physical console**
    ```
    [User touches fader on X32]
    X32 → Client A: /ch/01/mix/fader ,f 0.80
    X32 → Client B: /ch/01/mix/fader ,f 0.80
    X32 → Client C: /ch/01/mix/fader ,f 0.80
    ```

### Maintaining Synchronisation

All clients must independently maintain `/xremote`:

```
Time    Client A        Client B        Client C
0s      /xremote        /xremote        /xremote
9s      /xremote        /xremote        /xremote
18s     /xremote        (timeout!)      /xremote
27s     /xremote        (no updates)    /xremote
```

**Client B** did not resend `/xremote` at 18 s, so its updates stopped.

## Implementation Recommendations

### 1. Robust Timer Implementation

```typescript
class X32Connection {
    private xremoteTimer?: NodeJS.Timeout;

    startXremote() {
        this.sendXremote();
        this.xremoteTimer = setInterval(() => {
            this.sendXremote();
        }, 9000); // every 9 seconds
    }

    stopXremote() {
        if (this.xremoteTimer) {
            clearInterval(this.xremoteTimer);
            this.xremoteTimer = undefined;
        }
    }

    sendXremote() {
        const msg = osc.toBuffer({ address: '/xremote', args: [] });
        this.socket.send(msg, X32_PORT, X32_HOST);
    }
}
```

### 2. Connection State Monitoring

```typescript
class X32Connection {
    private lastUpdateTime: number = 0;

    onMessage(msg: Buffer) {
        this.lastUpdateTime = Date.now();
        // Process message
    }

    checkConnection() {
        const now = Date.now();
        if (now - this.lastUpdateTime > 15000) { // 15 seconds
            console.warn('No updates received - connection may be lost');
            // Reconnection logic
        }
    }
}
```

### 3. Reconnection Logic

```typescript
class X32Connection {
    reconnect() {
        console.log('Reconnecting to X32...');
        this.stopXremote();

        // Wait briefly then restart
        setTimeout(() => {
            this.startXremote();
            console.log('Reconnected to X32');
        }, 1000);
    }
}
```

### 4. Error Handling

```typescript
class X32Connection {
    sendXremote() {
        try {
            const msg = osc.toBuffer({ address: '/xremote', args: [] });
            this.socket.send(msg, X32_PORT, X32_HOST, err => {
                if (err) {
                    console.error('Failed to send /xremote:', err);
                    this.reconnect();
                }
            });
        } catch (error) {
            console.error('Error creating /xremote message:', error);
        }
    }
}
```

## Client Application Examples

### X32Saver (Linux/Windows)

For real-world usage examples, refer to the following applications:

1. **X32Saver.c** (Linux or Windows)
    - Maintaining connection using `/xremote`
    - Implementing periodic renewal

2. **X32 data echo in Go**
    - Go language implementation
    - Concurrency handling example

See the examples section at the end of the documentation for details.

## Network Considerations

### UDP Characteristics

- **Connectionless**: does not track connection state
- **Unreliable**: packets may be lost
- **No ordering guarantee**: messages may not arrive in order

### Recommendations

1. **Use wired connections**
    - 100 Mbps Ethernet is preferred over WiFi
    - Minimises packet loss

2. **Buffer management**
    - Set UDP receive buffer size sufficiently large
    - Prevent overflow

3. **Timeout handling**
    - Send `/xremote` slightly more often than every 9 seconds
    - Account for network latency

4. **Error recovery**
    - Detect connection drops
    - Implement automatic reconnection

## Debugging Tips

### Logging

```typescript
class X32Connection {
    private debug = true;

    sendXremote() {
        if (this.debug) {
            console.log(`[${new Date().toISOString()}] Sending /xremote`);
        }
        // Send logic
    }

    onMessage(msg: Buffer) {
        if (this.debug) {
            console.log(`[${new Date().toISOString()}] Received:`, msg);
        }
        // Processing logic
    }
}
```

### Connection Testing

```bash
# Test sending /xremote (using an OSC utility)
oscsend 192.168.1.100 10023 /xremote

# Monitor responses
oscdump 10023
```

### Wireshark Analysis

1. Filter UDP port 10023: `udp.port == 10023`
2. Verify `/xremote` messages
3. Check 9-second intervals
4. Analyse response message patterns

## Performance Optimisation

### Selective Subscription

Instead of receiving all changes, subscribe only to what you need:

```typescript
// Instead of receiving everything with:
// send("/xremote");

// Subscribe to specific channels only:
send('/subscribe ,si /ch/01/mix/fader 10');
send('/subscribe ,si /ch/02/mix/fader 10');
```

### Batch Processing

```typescript
class X32Connection {
    private updateQueue: Array<OSCMessage> = [];

    onMessage(msg: OSCMessage) {
        this.updateQueue.push(msg);
    }

    processBatch() {
        // Process in batches every 100 ms
        setInterval(() => {
            if (this.updateQueue.length > 0) {
                const batch = this.updateQueue.splice(0);
                this.processMessages(batch);
            }
        }, 100);
    }
}
```

## References

- [client-initiated-messages.md](./client-initiated-messages.md) - `/xremote` details
- [server-replies.md](./server-replies.md) - Server response formats
- [examples.md](./examples.md) - Implementation examples
- [OSC-Protocal.md](../OSC-Protocal.md) - OSC Protocol Guide

## Summary

- **Registration**: all clients register for updates via the `/xremote` command
- **Timeout**: 10 seconds (resending every 9 seconds is recommended)
- **Simultaneous connections**: multiple clients supported at the same time
- **Change propagation**: automatically sent to all registered clients
- **Local changes**: changes made directly on the console are also sent
- **Network**: wired connection recommended; be aware of UDP characteristics