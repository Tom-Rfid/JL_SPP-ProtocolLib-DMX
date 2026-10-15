"""
JL_SPP DMX frames (521 bytes) and handshakes.

Frame layout (see docs/protocol.md)::

    [0]        0x00
    [1] [2]    'K' 'T'          start marker, in clear
    [3]        scene            0 = direct control
    [4]        speed            0 in direct control
    [5..516]   512 DMX channels, scrambled (channel 1 -> byte 5)
    [517]      SIN[code_num]    )  key, written by encrypt()
    [518]      code_num         )
    [519][520] 'T' 'K'          end marker, in clear

Convention of the whole library: a *universe* is a sequence of 512 bytes where
index 0 is DMX channel 1.
"""

from typing import NamedTuple, Sequence

from .cipher import decrypt, encrypt

FRAME_LENGTH = 521   # bytes in one DMX frame
UNIVERSE_SIZE = 512  # DMX channels in one universe
PAYLOAD_START = 5    # frame byte holding DMX channel 1
MARKER_OFFSET = 517  # frame bytes 517 and 518 hold the key

START_MARKER = b"KT"  # frame bytes 1..2
END_MARKER = b"TK"    # frame bytes 519..520
END_MARKER_OFFSET = 519

# Sent in clear: right after opening the port / right before closing it.
HANDSHAKE_CONNECT = bytes([0xBB, 0x99, 0x77, 0x01, 0x77, 0x99])
HANDSHAKE_DISCONNECT = bytes([0xBB, 0x77, 0x99, 0x10, 0x99, 0x77, 0x00, 0x55])


class DecodedFrame(NamedTuple):
    """Content of a frame once unscrambled."""
    universe: bytes  # 512 channel values, index 0 = channel 1
    code_num: int    # counter written by the sender
    scene: int       # byte 3
    speed: int       # byte 4


def check_universe(universe: Sequence[int]) -> None:
    """Raises ValueError unless the universe has exactly 512 values."""
    if len(universe) != UNIVERSE_SIZE:
        raise ValueError(f"a universe must hold {UNIVERSE_SIZE} values (got {len(universe)})")


def build_clear_frame(universe: Sequence[int], scene: int = 0, speed: int = 0) -> bytearray:
    """Builds a frame whose channels are still in clear (before scrambling)."""
    check_universe(universe)
    buf = bytearray(FRAME_LENGTH)
    buf[1:3] = START_MARKER
    buf[3] = scene & 0xFF
    buf[4] = speed & 0xFF
    buf[PAYLOAD_START:PAYLOAD_START + UNIVERSE_SIZE] = bytes(universe)
    buf[END_MARKER_OFFSET:END_MARKER_OFFSET + 2] = END_MARKER
    return buf


def build_frame(universe: Sequence[int], code_num: int, scene: int = 0, speed: int = 0) -> bytes:
    """Builds a complete frame, ready to be written to the serial port.

    :param universe: 512 values 0..255 (index 0 = DMX channel 1).
    :param code_num: counter 0..255, normally incremented for every frame.
    :param scene: byte 3 (0 = direct control; 1..8 = scene stored in the interface, unverified).
    :param speed: byte 4 (0 in direct control).
    """
    clear = build_clear_frame(universe, scene, speed)
    return bytes(encrypt(clear, PAYLOAD_START, UNIVERSE_SIZE, code_num, MARKER_OFFSET))


def is_frame(frame: bytes) -> bool:
    """True if the frame has the right length and the clear KT / TK markers."""
    return (len(frame) == FRAME_LENGTH
            and frame[1:3] == START_MARKER
            and frame[END_MARKER_OFFSET:END_MARKER_OFFSET + 2] == END_MARKER)


def decode_frame(frame: bytes) -> DecodedFrame:
    """Inverse of build_frame (useful to analyse a capture)."""
    if not is_frame(frame):
        raise ValueError("not a valid JL_SPP DMX frame (length or KT/TK markers)")
    clear = decrypt(frame, PAYLOAD_START, UNIVERSE_SIZE, MARKER_OFFSET)
    universe = bytes(clear[PAYLOAD_START:PAYLOAD_START + UNIVERSE_SIZE])
    return DecodedFrame(universe=universe, code_num=frame[MARKER_OFFSET + 1], scene=frame[3], speed=frame[4])
