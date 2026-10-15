"""Small helpers shared by the fixture classes."""

from typing import Tuple

DMX_MAX = 255


def clamp_byte(value: int) -> int:
    """Clamps any number into a DMX value 0..255."""
    return max(0, min(DMX_MAX, int(value)))


def scale_into_range(amount: int, low: int, high: int) -> int:
    """Maps ``amount`` 0..255 linearly onto the DMX range ``low..high``.

    Used for "slow to fast" ranges: 0 gives ``low``, 255 gives ``high``.
    Integer maths so that every language of the project gives the same result.
    """
    return low + clamp_byte(amount) * (high - low) // DMX_MAX


def middle(low: int, high: int) -> int:
    """Middle of a DMX range: the safest value to select a slot (color, gobo...)."""
    return (low + high) // 2


def split_16bit(position: int) -> Tuple[int, int]:
    """Splits a 16-bit position 0..65535 into (coarse, fine) bytes."""
    position = max(0, min(0xFFFF, int(position)))
    return position >> 8, position & 0xFF


def check_address(address: int, footprint: int) -> None:
    """Raises ValueError unless a fixture of ``footprint`` channels fits at ``address``."""
    last_start = 512 - footprint + 1
    if not 1 <= address <= last_start:
        raise ValueError(f"DMX address must be 1..{last_start} for a {footprint}-channel fixture")
