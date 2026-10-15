"""
Trames DMX JL_SPP (521 octets) et poignees de main.

Structure (voir docs/protocol.md) ::

    [0]        0x00
    [1] [2]    'K' 'T'          marqueurs de debut, en clair
    [3]        scene  (0 = pilotage direct)
    [4]        vitesse (0 en pilotage direct)
    [5..516]   512 canaux DMX brouilles (canal 1 -> octet 5)
    [517]      SIN[code_num]    )  cle, ecrite par encrypt()
    [518]      code_num         )
    [519][520] 'T' 'K'          marqueurs de fin, en clair

Convention de toute la librairie : un *univers* est une suite de 512 octets dont
l'index 0 correspond au canal DMX 1.
"""

from typing import NamedTuple, Sequence

from .cipher import decrypt, encrypt

FRAME_LENGTH = 521
UNIVERSE_SIZE = 512
PAYLOAD_START = 5
MARKER_OFFSET = 517

HANDSHAKE_CONNECT = bytes([0xBB, 0x99, 0x77, 0x01, 0x77, 0x99])
HANDSHAKE_DISCONNECT = bytes([0xBB, 0x77, 0x99, 0x10, 0x99, 0x77, 0x00, 0x55])


class DecodedFrame(NamedTuple):
    universe: bytes
    code_num: int
    scene: int
    speed: int


def build_frame(universe: Sequence[int], code_num: int, scene: int = 0, speed: int = 0) -> bytes:
    """Construit une trame complete, prete a etre ecrite sur le port serie.

    :param universe: 512 valeurs 0..255 (index 0 = canal DMX 1).
    :param code_num: compteur 0..255, normalement incremente a chaque trame.
    :param scene: octet 3 (0 = pilotage direct ; 1..8 = scene memorisee du boitier, non verifie).
    :param speed: octet 4 (0 en pilotage direct).
    """
    if len(universe) != UNIVERSE_SIZE:
        raise ValueError(f"l'univers doit contenir {UNIVERSE_SIZE} valeurs (recu {len(universe)})")
    buf = bytearray(FRAME_LENGTH)
    buf[1], buf[2] = ord("K"), ord("T")
    buf[3], buf[4] = scene & 0xFF, speed & 0xFF
    buf[PAYLOAD_START:PAYLOAD_START + UNIVERSE_SIZE] = bytes(universe)
    buf[519], buf[520] = ord("T"), ord("K")
    return bytes(encrypt(buf, PAYLOAD_START, UNIVERSE_SIZE, code_num, MARKER_OFFSET))


def is_frame(frame: bytes) -> bool:
    """Verifie la longueur et les marqueurs en clair d'une trame."""
    return (len(frame) == FRAME_LENGTH and frame[1:3] == b"KT" and frame[519:521] == b"TK")


def decode_frame(frame: bytes) -> DecodedFrame:
    """Operation inverse de build_frame (utile pour analyser une capture)."""
    if not is_frame(frame):
        raise ValueError("ce n'est pas une trame DMX JL_SPP valide (longueur ou marqueurs KT/TK)")
    clear = decrypt(frame, PAYLOAD_START, UNIVERSE_SIZE, MARKER_OFFSET)
    return DecodedFrame(bytes(clear[PAYLOAD_START:PAYLOAD_START + UNIVERSE_SIZE]), frame[518], frame[3], frame[4])
