"""
DMX messages of the Mindi Mini Spider 8x3W RGBW (15-channel mode).
See docs/fixtures/mindi-mini-spider.md.

ADDRESS QUIRK (observed on the fixture): when set to address N, the Spider ignores
channel N and listens from N+1. This class applies that shift by default
(``address_quirk=True``): give it the address SHOWN on the fixture display.

Example::

    universe = bytearray(512)
    spider = MindiSpider(address=1)
    spider.set_dimmer(universe, 255)
    spider.set_wings(universe, 200, mirror=True)
    spider.set_led(universe, 1, 255)
"""

from enum import IntEnum
from typing import MutableSequence, Sequence

from ._common import check_address, clamp_byte


class SpiderChannel(IntEnum):
    """Channels of the Spider (1..15), from its manual."""
    MOTOR_1 = 1          # wing 1 position: 0..255 = 0..135 degrees
    MOTOR_2 = 2          # wing 2 position: 0..255 = 0..135 degrees
    DIMMER = 3           # master dimmer
    STROBE = 4           # 0 = no strobe, then flash speed
    LED_1 = 5            # LED 1..8: intensity of each LED
    LED_2 = 6            #   (color ASSUMED: red, green, blue, white, twice)
    LED_3 = 7
    LED_4 = 8
    LED_5 = 9
    LED_6 = 10
    LED_7 = 11
    LED_8 = 12
    MACRO = 13           # built-in effect programs
    EFFECT_SPEED = 14    # effect speed, slow -> fast
    RESET = 15           # keep at 0


CHANNEL_COUNT = 15
LED_COUNT = 8
MOTOR_MAX_DEGREES = 135.0

# ASSUMED split of the LEDs between the two wings (to be checked on the fixture).
LEFT_WING_LEDS = (1, 2, 3, 4)
RIGHT_WING_LEDS = (5, 6, 7, 8)


def mirrored(position: int) -> int:
    """Symmetric wing position: 0 <-> 255, 128 stays (almost) in the middle."""
    return 255 - clamp_byte(position)


def motor_degrees(value: int) -> float:
    """Motor DMX value -> wing angle (0..135 degrees according to the manual)."""
    return clamp_byte(value) * MOTOR_MAX_DEGREES / 255.0


class MindiSpider:
    """Computes the DMX channels of one Spider and writes them into a universe
    (512 values, index 0 = channel 1: a bytearray, a list...)."""

    def __init__(self, address: int, address_quirk: bool = True):
        """
        :param address: DMX address shown on the fixture.
        :param address_quirk: True (default) if the fixture ignores its first channel,
            as observed on our unit. Use False for a unit that behaves normally.
        """
        self.address = address
        self.address_quirk = address_quirk
        check_address(address, self.footprint_size)

    # ------------------------------------------------------------------ channels

    @property
    def quirk_offset(self) -> int:
        """1 when the address quirk is applied, else 0."""
        return 1 if self.address_quirk else 0

    @property
    def footprint_size(self) -> int:
        """Number of DMX channels used, the ignored one included (16 with the quirk)."""
        return CHANNEL_COUNT + self.quirk_offset

    @property
    def footprint(self) -> range:
        """DMX channels used, the ignored one included."""
        return range(self.address, self.address + self.footprint_size)

    def dmx_channel(self, channel: SpiderChannel) -> int:
        """Absolute DMX channel (1..512) of a Spider function."""
        return self.address + self.quirk_offset + int(channel) - 1

    def set(self, universe: MutableSequence[int], channel: SpiderChannel, value: int) -> None:
        """Writes one Spider channel into the universe."""
        universe[self.dmx_channel(channel) - 1] = clamp_byte(value)

    # ----------------------------------------------------------------- functions

    def set_dimmer(self, universe: MutableSequence[int], level: int) -> None:
        """Master dimmer 0..255. Must be open, otherwise the LEDs stay dark."""
        self.set(universe, SpiderChannel.DIMMER, level)

    def set_strobe(self, universe: MutableSequence[int], speed: int) -> None:
        """Strobe speed; 0 = no strobe."""
        self.set(universe, SpiderChannel.STROBE, speed)

    def stop_strobe(self, universe: MutableSequence[int]) -> None:
        """Same as set_strobe(universe, 0)."""
        self.set_strobe(universe, 0)

    def set_led(self, universe: MutableSequence[int], led: int, level: int) -> None:
        """Intensity of one LED. led: 1..8."""
        if not 1 <= led <= LED_COUNT:
            raise ValueError("LED number must be 1..8")
        self.set(universe, SpiderChannel(SpiderChannel.LED_1 + led - 1), level)

    def set_leds(self, universe: MutableSequence[int], leds: Sequence[int], level: int) -> None:
        """Same intensity for a group of LEDs (e.g. LEFT_WING_LEDS)."""
        for led in leds:
            self.set_led(universe, led, level)

    def set_wing_motor(self, universe: MutableSequence[int], wing: int, position: int) -> None:
        """Position of one wing. wing: 1 or 2; position: 0..255 (= 0..135 degrees)."""
        if wing not in (1, 2):
            raise ValueError("wing must be 1 or 2")
        motor = SpiderChannel.MOTOR_1 if wing == 1 else SpiderChannel.MOTOR_2
        self.set(universe, motor, position)

    def set_wings(self, universe: MutableSequence[int], position: int, mirror: bool = False) -> None:
        """Moves both wings.

        With ``mirror``, wing 2 takes the symmetric position (255 - position): the
        wings start from opposite sides and meet in the middle.
        """
        self.set_wing_motor(universe, 1, position)
        self.set_wing_motor(universe, 2, mirrored(position) if mirror else position)

    def set_macro(self, universe: MutableSequence[int], value: int, speed: int = 128) -> None:
        """Built-in effect program (raw value, see the manual) and its speed."""
        self.set(universe, SpiderChannel.MACRO, value)
        self.set(universe, SpiderChannel.EFFECT_SPEED, speed)
