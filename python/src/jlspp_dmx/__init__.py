"""
jlspp_dmx - protocole DMX des boitiers Bluetooth « USB-RDM-DMX » (puce Jieli, service JL_SPP,
appli Android RY-AI).

    from jlspp_dmx import build_frame, decode_frame, DmxLink

Voir docs/protocol.md pour la specification.
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

__version__ = "0.1.0"

__all__ = [
    "encrypt", "decrypt",
    "FRAME_LENGTH", "UNIVERSE_SIZE", "PAYLOAD_START", "MARKER_OFFSET",
    "HANDSHAKE_CONNECT", "HANDSHAKE_DISCONNECT",
    "DecodedFrame", "build_frame", "decode_frame", "is_frame",
    "DmxLink",
]
