"""
Serial link to the JL_SPP interface (Bluetooth SPP seen as a serial port).

    Windows : "outgoing" COM port created when pairing (e.g. COM6)
    Linux   : /dev/rfcomm0 after `rfcomm bind` (see docs/platforms.md)
    macOS   : /dev/tty.<name>-... (untested)

Example::

    from jlspp_dmx import DmxLink

    with DmxLink("COM6") as link:      # opens, sends the handshake, starts sending at 10 Hz
        link.set_channel(1, 255)
        time.sleep(5)
                                       # on exit: stop, disconnect handshake, close

Requires pyserial (``pip install jlspp-dmx[serial]``).
"""

import threading
import time
from typing import Callable, Iterable, Optional

from .frame import HANDSHAKE_CONNECT, HANDSHAKE_DISCONNECT, UNIVERSE_SIZE, build_frame


def check_channel(channel: int) -> None:
    """Raises ValueError unless 1 <= channel <= 512."""
    if not 1 <= channel <= UNIVERSE_SIZE:
        raise ValueError("a DMX channel goes from 1 to 512")


class DmxLink:
    """Keeps sending the DMX universe to the interface, like the original app (one
    frame every ``interval`` seconds, 0.1 s by default).

    Thread-safe: channels can be changed from any thread while frames are being sent.
    """

    def __init__(self, port: str, interval: float = 0.1, baudrate: int = 9600,
                 on_error: Optional[Callable[[Exception], None]] = None):
        """
        :param port: serial port name ("COM6", "/dev/rfcomm0"...).
        :param interval: seconds between two frames (0.1 = original app).
        :param baudrate: irrelevant on a Bluetooth virtual port, kept for pyserial.
        :param on_error: called from the sending thread if the link is lost.
        """
        self.port_name = port
        self.interval = interval
        self.baudrate = baudrate
        self.on_error = on_error
        self.frames_sent = 0
        self._universe = bytearray(UNIVERSE_SIZE)  # index 0 = channel 1
        self._lock = threading.Lock()               # protects _universe
        self._serial = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._code_num = 0

    # ------------------------------------------------------------------ channels

    def set_channel(self, channel: int, value: int) -> None:
        """Sets one channel. channel: 1..512; value: 0..255."""
        check_channel(channel)
        with self._lock:
            self._universe[channel - 1] = value & 0xFF

    def set_channels(self, first_channel: int, values: Iterable[int]) -> None:
        """Sets consecutive channels starting at ``first_channel``."""
        for offset, value in enumerate(values):
            self.set_channel(first_channel + offset, value)

    def set_universe(self, universe: Iterable[int]) -> None:
        """Replaces the whole universe (512 values, index 0 = channel 1)."""
        data = bytes(universe)
        if len(data) != UNIVERSE_SIZE:
            raise ValueError(f"a universe must hold {UNIVERSE_SIZE} values")
        with self._lock:
            self._universe[:] = data

    def get_channel(self, channel: int) -> int:
        """Current value of one channel (1..512)."""
        check_channel(channel)
        with self._lock:
            return self._universe[channel - 1]

    def blackout(self) -> None:
        """Sets every channel to 0."""
        with self._lock:
            self._universe[:] = bytes(UNIVERSE_SIZE)

    def snapshot(self) -> bytes:
        """Copy of the current universe."""
        with self._lock:
            return bytes(self._universe)

    # ---------------------------------------------------------------- connection

    def open(self) -> None:
        """Opens the port and sends the connect handshake."""
        import serial  # late import: the frame functions stay usable without pyserial

        self._serial = serial.Serial(self.port_name, self.baudrate, timeout=1, write_timeout=2)
        self._write(HANDSHAKE_CONNECT)

    def send_frame(self) -> None:
        """Sends a single frame with the current state of the universe."""
        if self._serial is None:
            raise RuntimeError("port not open: call open() first")
        self._write(build_frame(self.snapshot(), self._next_code_num()))
        self.frames_sent += 1

    def start(self) -> None:
        """Starts sending frames continuously from a background thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._send_loop, name="jlspp-dmx-send", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stops the background sending (the port stays open)."""
        self._running = False
        if self._thread is not None and self._thread is not threading.current_thread():
            self._thread.join(timeout=2)
        self._thread = None

    def close(self) -> None:
        """Stops sending, sends the disconnect handshake and closes the port."""
        self.stop()
        if self._serial is None:
            return
        try:
            self._write(HANDSHAKE_DISCONNECT)
        except Exception:  # the interface may already have dropped the link
            pass
        self._serial.close()
        self._serial = None

    # ------------------------------------------------------------------ internals

    def _write(self, data: bytes) -> None:
        self._serial.write(data)
        self._serial.flush()

    def _next_code_num(self) -> int:
        """Counter 0..255 written in each frame (any value works, the original app increments it)."""
        self._code_num = (self._code_num + 1) & 0xFF
        return self._code_num

    def _send_loop(self) -> None:
        next_time = time.monotonic()
        while self._running:
            try:
                self.send_frame()
            except Exception as exc:  # link lost
                self._running = False
                if self.on_error is not None:
                    self.on_error(exc)
                return
            next_time += self.interval
            time.sleep(max(0.001, next_time - time.monotonic()))

    def __enter__(self) -> "DmxLink":
        self.open()
        self.start()
        return self

    def __exit__(self, *exc) -> None:
        self.close()
