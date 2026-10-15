"""
jlspp_dmx - DMX protocol of the "USB-RDM-DMX" Bluetooth interfaces (Jieli chip,
JL_SPP service, RY-AI Android app).

    from jlspp_dmx import build_frame, decode_frame, DmxLink
    from jlspp_dmx.fixtures import ChauvetSpot260X, MindiSpider

See docs/protocol.md for the specification.
"""

from .cipher import decrypt, encrypt
from .frame import (
    FRAME_LENGTH,
    HANDSHAKE_CONNECT,
    HANDSHAKE_DISCONNECT,
    MARKER_OFFSET,
    PAYLOAD_START,
    UNIVERSE_SIZE,
    DecodedFrame,
    build_frame,
    decode_frame,
    is_frame,
)
from .link import DmxLink

__version__ = "0.2.0"

__all__ = [
    "encrypt", "decrypt",
    "FRAME_LENGTH", "UNIVERSE_SIZE", "PAYLOAD_START", "MARKER_OFFSET",
    "HANDSHAKE_CONNECT", "HANDSHAKE_DISCONNECT",
    "DecodedFrame", "build_frame", "decode_frame", "is_frame",
    "DmxLink",
]
