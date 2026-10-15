"""
Brouillage JL_SPP DMX (portage de Code.java, appli Android RY-AI).

Ce n'est pas de la cryptographie : une substitution par table (S-box) choisie selon
un compteur ``code_num`` (0..255) que l'emetteur ecrit dans la trame. Il faut
pourtant le reproduire exactement, sinon le boitier ignore les trames.

    table  = PASSWORD[SIN[code_num] % 5]
    sortie = table[(octet + code_num) % 256]
    trame[marker]     = SIN[code_num]
    trame[marker + 1] = code_num
"""

from ._tables import DECODE, PASSWORD, SIN


def encrypt(frame: bytes, start: int, length: int, code_num: int, marker_offset: int) -> bytearray:
    """Equivalent de ``Code.Encryption1`` : retourne une copie de ``frame`` dont
    ``frame[start:start+length]`` est brouille et ou les 2 octets de cle sont ecrits
    a ``marker_offset``."""
    code_num &= 0xFF
    out = bytearray(frame)
    table = PASSWORD[SIN[code_num] % 5]
    out[marker_offset] = SIN[code_num]
    out[marker_offset + 1] = code_num
    for pos in range(start, start + length):
        out[pos] = table[(frame[pos] + code_num) & 0xFF]
    return out


def decrypt(frame: bytes, start: int, length: int, marker_offset: int) -> bytearray:
    """Equivalent de ``Code.Decode`` : relit les 2 octets de cle ecrits dans la trame
    et retrouve les octets en clair."""
    out = bytearray(frame)
    table = DECODE[frame[marker_offset] % 5]
    key = frame[marker_offset + 1]
    for pos in range(start, start + length):
        out[pos] = (table[frame[pos]] - key) & 0xFF
    return out
