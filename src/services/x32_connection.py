"""
X32 Connection Manager
Manages UDP OSC connection to X32/M32 mixer
"""

import asyncio
import socket
import struct
import threading
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class OscArgument:
    """OSC message argument."""
    type: str
    value: Any


@dataclass
class OscMessage:
    """OSC message."""
    address: str
    args: list[OscArgument] = field(default_factory=list)


@dataclass
class X32ConnectionConfig:
    """X32/M32 connection configuration."""
    host: str
    port: int = 10023


@dataclass
class X32InfoResponse:
    """X32/M32 info response from /info command."""
    server_version: str
    server_name: str
    console_model: str
    console_version: str


@dataclass
class X32StatusResponse:
    """X32/M32 status response from /status command."""
    state: str
    ip_address: str
    server_name: str


def _pad4(n: int) -> int:
    """Round up to next multiple of 4."""
    return (n + 3) & ~3


def _encode_string(s: str) -> bytes:
    """Encode a string as OSC null-terminated padded to 4 bytes."""
    encoded = s.encode("utf-8") + b"\x00"
    return encoded.ljust(_pad4(len(encoded)), b"\x00")


def _encode_osc_message(address: str, args: list[Any] | None = None) -> bytes:
    """Encode an OSC message to bytes."""
    if args is None:
        args = []

    data = _encode_string(address)
    type_tags = ","
    arg_data = b""

    for arg in args:
        if isinstance(arg, bool):
            type_tags += "i"
            arg_data += struct.pack(">i", int(arg))
        elif isinstance(arg, int):
            type_tags += "i"
            arg_data += struct.pack(">i", arg)
        elif isinstance(arg, float):
            type_tags += "f"
            arg_data += struct.pack(">f", arg)
        elif isinstance(arg, str):
            type_tags += "s"
            arg_data += _encode_string(arg)
        else:
            type_tags += "s"
            arg_data += _encode_string(str(arg))

    data += _encode_string(type_tags)
    data += arg_data
    return data


def _decode_osc_message(data: bytes) -> OscMessage | None:
    """Decode an OSC message from bytes."""
    try:
        pos = 0
        end = data.index(b"\x00", pos)
        address = data[pos:end].decode("utf-8")
        pos = _pad4(end + 1)

        if pos >= len(data):
            return OscMessage(address=address)

        end = data.index(b"\x00", pos)
        type_tags = data[pos:end].decode("utf-8")
        pos = _pad4(end + 1)

        args: list[OscArgument] = []

        if type_tags.startswith(","):
            for tag in type_tags[1:]:
                if tag == "i":
                    value = struct.unpack(">i", data[pos: pos + 4])[0]
                    pos += 4
                    args.append(OscArgument(type="i", value=value))
                elif tag == "f":
                    value = struct.unpack(">f", data[pos: pos + 4])[0]
                    pos += 4
                    args.append(OscArgument(type="f", value=value))
                elif tag == "s":
                    end = data.index(b"\x00", pos)
                    value = data[pos:end].decode("utf-8")
                    pos = _pad4(end + 1)
                    args.append(OscArgument(type="s", value=value))
                elif tag == "b":
                    size = struct.unpack(">i", data[pos: pos + 4])[0]
                    pos += 4
                    value = data[pos: pos + size]
                    pos += _pad4(size)
                    args.append(OscArgument(type="b", value=value))
                elif tag == "T":
                    args.append(OscArgument(type="T", value=True))
                elif tag == "F":
                    args.append(OscArgument(type="F", value=False))
                elif tag == "N":
                    args.append(OscArgument(type="N", value=None))

        return OscMessage(address=address, args=args)
    except Exception:
        return None


class X32Connection:
    """
    X32/M32 OSC Connection Manager.
    Manages UDP OSC connection to X32/M32 mixer.
    """

    DEFAULT_TIMEOUT = 5.0  # seconds

    def __init__(self) -> None:
        self._sock: socket.socket | None = None
        self._config: X32ConnectionConfig | None = None
        self._is_connected: bool = False
        self._message_queue: dict[str, asyncio.Future] = {}
        self._receive_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._event_handlers: dict[str, list[Callable]] = {
            "connected": [],
            "disconnected": [],
            "error": [],
            "message": [],
        }

    def on(self, event: str, handler: Callable) -> None:
        """Register an event handler."""
        if event in self._event_handlers:
            self._event_handlers[event].append(handler)

    def _emit(self, event: str, *args: Any) -> None:
        """Emit an event to all registered handlers."""
        for handler in self._event_handlers.get(event, []):
            try:
                handler(*args)
            except Exception:
                pass

    async def connect(self, config: X32ConnectionConfig) -> None:
        """Connect to X32/M32 mixer."""
        if self._is_connected:
            raise Exception("Already connected to X32/M32")

        self._config = config
        self._loop = asyncio.get_event_loop()
        self._stop_event.clear()

        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._sock.bind(("0.0.0.0", 0))
            self._sock.connect((config.host, config.port))
            self._sock.settimeout(0.1)
            self._is_connected = True

            self._receive_thread = threading.Thread(
                target=self._receive_loop, daemon=True
            )
            self._receive_thread.start()

            self._emit("connected")
        except Exception as e:
            if self._sock:
                self._sock.close()
                self._sock = None
            self._is_connected = False
            raise Exception(f"Failed to connect to {config.host}:{config.port}: {e}") from e

    async def disconnect(self) -> None:
        """Disconnect from X32/M32 mixer."""
        if not self._is_connected:
            return

        self._stop_event.set()
        self._is_connected = False

        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None

        if self._receive_thread and self._receive_thread.is_alive():
            self._receive_thread.join(timeout=2.0)

        self._emit("disconnected")

    def _receive_loop(self) -> None:
        """Background thread to receive OSC messages."""
        while not self._stop_event.is_set():
            if not self._sock:
                break
            try:
                data = self._sock.recv(65536)
                msg = _decode_osc_message(data)
                if msg and self._loop:
                    self._loop.call_soon_threadsafe(self._handle_message, msg)
            except socket.timeout:
                continue
            except OSError:
                break

    def _handle_message(self, msg: OscMessage) -> None:
        """Handle an incoming OSC message (called in event loop thread)."""
        self._emit("message", msg)

        future = self._message_queue.get(msg.address)
        if future and not future.done():
            future.set_result(msg)

    async def send_message(
        self,
        address: str,
        args: list[Any] | None = None,
        wait_for_reply: bool = True,
    ) -> OscMessage | None:
        """Send an OSC message and optionally wait for a response."""
        if not self._is_connected or not self._sock:
            raise Exception("Not connected to X32/M32")

        if args is None:
            args = []

        data = _encode_osc_message(address, args)

        future: asyncio.Future | None = None
        if wait_for_reply:
            loop = asyncio.get_event_loop()
            future = loop.create_future()
            self._message_queue[address] = future

        try:
            self._sock.send(data)
        except Exception as e:
            if future and address in self._message_queue:
                del self._message_queue[address]
            raise e

        if not wait_for_reply:
            return None

        try:
            result = await asyncio.wait_for(future, timeout=self.DEFAULT_TIMEOUT)
            return result
        except asyncio.TimeoutError:
            self._message_queue.pop(address, None)
            raise Exception(f"Timeout waiting for response from {address}")
        finally:
            self._message_queue.pop(address, None)

    async def get_info(self) -> X32InfoResponse:
        """Get X32/M32 console information."""
        response = await self.send_message("/info")
        if not response:
            raise Exception("No response from /info")

        args = response.args
        if len(args) < 4:
            raise Exception("Invalid /info response format")

        return X32InfoResponse(
            server_version=str(args[0].value),
            server_name=str(args[1].value),
            console_model=str(args[2].value),
            console_version=str(args[3].value),
        )

    async def get_status(self) -> X32StatusResponse:
        """Get X32/M32 status."""
        response = await self.send_message("/status")
        if not response:
            raise Exception("No response from /status")

        args = response.args
        if len(args) < 3:
            raise Exception("Invalid /status response format")

        return X32StatusResponse(
            state=str(args[0].value),
            ip_address=str(args[1].value),
            server_name=str(args[2].value),
        )

    @property
    def connected(self) -> bool:
        """Check if connected."""
        return self._is_connected

    def get_config(self) -> X32ConnectionConfig | None:
        """Get current connection config."""
        return self._config

    async def get_parameter(self, address: str) -> Any:
        """Get parameter value from X32/M32."""
        response = await self.send_message(address)
        if not response or not response.args:
            raise Exception(f"No value returned from {address}")
        return response.args[0].value

    async def set_parameter(self, address: str, value: Any) -> None:
        """Set parameter value on X32/M32."""
        await self.send_message(address, [value], wait_for_reply=False)

    async def get_channel_parameter(self, channel: int, param: str) -> Any:
        """Get a channel parameter."""
        if channel < 1 or channel > 32:
            raise Exception("Channel must be between 1 and 32")
        ch = str(channel).zfill(2)
        return await self.get_parameter(f"/ch/{ch}/{param}")

    async def set_channel_parameter(self, channel: int, param: str, value: Any) -> None:
        """Set a channel parameter."""
        if channel < 1 or channel > 32:
            raise Exception("Channel must be between 1 and 32")
        ch = str(channel).zfill(2)
        await self.set_parameter(f"/ch/{ch}/{param}", value)

    async def request_meters(self, meter_id: str, *extra_args: int) -> list[float] | None:
        """
        Request meter data from the X32/M32.

        Sends:  /meters ,s[ii]  <meter_id> [extra_args...]
        Reply arrives addressed to <meter_id> (e.g. /meters/1) as an OSC blob.

        The blob layout (after the standard OSC address + ",b" type tag):
          4 bytes  – blob length, big-endian int
          4 bytes  – float count, little-endian int
          N × 4    – float values, little-endian

        Returns a list of floats, or None on timeout.
        """
        if not self._is_connected or not self._sock:
            raise Exception("Not connected to X32/M32")

        args: list[Any] = [meter_id] + list(extra_args)

        loop = asyncio.get_event_loop()
        future: asyncio.Future = loop.create_future()
        self._message_queue[meter_id] = future

        data = _encode_osc_message("/meters", args)
        try:
            self._sock.send(data)
        except Exception as e:
            self._message_queue.pop(meter_id, None)
            raise e

        try:
            msg = await asyncio.wait_for(future, timeout=self.DEFAULT_TIMEOUT)
        except asyncio.TimeoutError:
            self._message_queue.pop(meter_id, None)
            return None
        finally:
            self._message_queue.pop(meter_id, None)

        if not msg or not msg.args:
            return None

        # The first argument should be a blob ('b' type)
        blob: bytes | None = None
        for arg in msg.args:
            if arg.type == "b":
                blob = arg.value
                break

        if blob is None:
            return None

        # Decode: first 4 bytes = float count (little-endian int32)
        if len(blob) < 4:
            return None

        float_count = struct.unpack_from("<i", blob, 0)[0]
        expected_bytes = 4 + float_count * 4
        if len(blob) < expected_bytes:
            return None

        floats = list(struct.unpack_from(f"<{float_count}f", blob, 4))
        return floats

    async def get_bus_parameter(self, bus: int, param: str) -> Any:
        """Get a bus parameter."""
        if bus < 1 or bus > 16:
            raise Exception("Bus must be between 1 and 16")
        bus_num = str(bus).zfill(2)
        return await self.get_parameter(f"/bus/{bus_num}/{param}")

    async def set_bus_parameter(self, bus: int, param: str, value: Any) -> None:
        """Set a bus parameter."""
        if bus < 1 or bus > 16:
            raise Exception("Bus must be between 1 and 16")
        bus_num = str(bus).zfill(2)
        await self.set_parameter(f"/bus/{bus_num}/{param}", value)