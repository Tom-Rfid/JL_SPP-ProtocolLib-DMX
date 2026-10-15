"""
Channel scrambling of the JL_SPP DMX protocol (port of Code.java, RY-AI Android app).

This is NOT cryptography: it is a byte substitution (S-box) chosen by a counter
``code_num`` (0..255) that the sender writes into the frame. It must still be
reproduced exactly, otherwise the interface ignores the frames.

    table  = PASSWORD[SIN[code_num] % 5]
    output = table[(byte + code_num) % 256]
    frame[marker]     = SIN[code_num]
    frame[marker + 1] = code_num

See docs/cipher.md.
"""

from ._tables import DECODE, PASSWORD, SIN

TABLE_COUNT = 5  # number of substitution tables


def scramble_table(code_num: int) -> bytes:
    """Substitution table used for a given counter value."""
    return PASSWORD[SIN[code_num] % TABLE_COUNT]


def unscramble_table(sin_value: int) -> bytes:
    """Inverse table, found from the SIN value written in the frame."""
    return DECODE[sin_value % TABLE_COUNT]


def scramble_byte(value: int, code_num: int, table: bytes) -> int:
    """Scrambles one channel value: shift it by the counter, then substitute it."""
    return table[(value + code_num) & 0xFF]


def unscramble_byte(value: int, key: int, table: bytes) -> int:
    """Inverse of scramble_byte: substitute back, then remove the counter shift."""
    return (table[value] - key) & 0xFF


def encrypt(frame: bytes, start: int, length: int, code_num: int, marker_offset: int) -> bytearray:
    """Same as ``Code.Encryption1``.

    Returns a copy of ``frame`` where ``frame[start:start+length]`` is scrambled and
    the 2 key bytes are written at ``marker_offset`` and ``marker_offset + 1``.
    """
    code_num &= 0xFF
    table = scramble_table(code_num)
    out = bytearray(frame)
    for pos in range(start, start + length):
        out[pos] = scramble_byte(frame[pos], code_num, table)
    out[marker_offset] = SIN[code_num]
    out[marker_offset + 1] = code_num
    return out


def decrypt(frame: bytes, start: int, length: int, marker_offset: int) -> bytearray:
    """Same as ``Code.Decode``: reads the 2 key bytes back from the frame and
    returns a copy where ``frame[start:start+length]`` is in clear."""
    table = unscramble_table(frame[marker_offset])
    key = frame[marker_offset + 1]
    out = bytearray(frame)
    for pos in range(start, start + length):
        out[pos] = unscramble_byte(frame[pos], key, table)
    return out
