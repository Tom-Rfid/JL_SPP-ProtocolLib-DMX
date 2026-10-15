"""
DMX messages of the Chauvet DJ Intimidator Spot 260X moving head.
Source: Intimidator Spot 260X Quick Reference Guide Rev. 1 (Chauvet).
See docs/fixtures/chauvet-intimidator-spot-260x.md.

The fixture has two DMX modes, chosen in its menu (Run Mode > DMX):

    14 channels: everything, with 16-bit pan/tilt and a dimmer
     8 channels: pan, tilt, color, gobo, gobo rotation, prism, focus, shutter

Example::

    universe = bytearray(512)
    spot = ChauvetSpot260X(address=17)            # 14-channel mode by default
    spot.light_on(universe)                       # dimmer 100 % + shutter open
    spot.set_pan_degrees(universe, 270)
    spot.set_color(universe, Spot260XColor.RED)
    spot.set_gobo(universe, Spot260XGobo.GOBO_3)
    spot.set_strobe(universe, speed=200)
"""

from enum import Enum, IntEnum
from typing import Dict, MutableSequence, Tuple

from ._common import check_address, clamp_byte, middle, scale_into_range, split_16bit

Universe = MutableSequence[int]
Range = Tuple[int, int]  # (low, high) DMX values, inclusive

PAN_RANGE_DEGREES = 540.0   # full pan travel (menu "Pan Angle" = 540, the default)
TILT_RANGE_DEGREES = 234.0  # full tilt travel (menu "Tilt Angle" = 234, the default)


# =============================================================================== modes

class Spot260XMode(IntEnum):
    """DMX mode chosen in the fixture menu. The value is the number of channels."""
    CHANNELS_8 = 8
    CHANNELS_14 = 14


class Spot260XFunction(Enum):
    """Everything the fixture can do over DMX."""
    PAN = "pan"
    PAN_FINE = "pan_fine"
    TILT = "tilt"
    TILT_FINE = "tilt_fine"
    PAN_TILT_SPEED = "pan_tilt_speed"
    COLOR_WHEEL = "color_wheel"
    GOBO_WHEEL = "gobo_wheel"
    GOBO_ROTATION = "gobo_rotation"
    PRISM = "prism"
    FOCUS = "focus"
    DIMMER = "dimmer"
    SHUTTER = "shutter"
    CONTROL = "control"
    MOVEMENT_MACRO = "movement_macro"


F = Spot260XFunction  # short alias, keeps the tables below readable

# Channel number (1-based, relative to the fixture address) of each function, per mode.
CHANNEL_MAP: Dict[Spot260XMode, Dict[Spot260XFunction, int]] = {
    Spot260XMode.CHANNELS_14: {
        F.PAN: 1, F.PAN_FINE: 2, F.TILT: 3, F.TILT_FINE: 4, F.PAN_TILT_SPEED: 5,
        F.COLOR_WHEEL: 6, F.GOBO_WHEEL: 7, F.GOBO_ROTATION: 8, F.PRISM: 9, F.FOCUS: 10,
        F.DIMMER: 11, F.SHUTTER: 12, F.CONTROL: 13, F.MOVEMENT_MACRO: 14,
    },
    Spot260XMode.CHANNELS_8: {
        F.PAN: 1, F.TILT: 2, F.COLOR_WHEEL: 3, F.GOBO_WHEEL: 4,
        F.GOBO_ROTATION: 5, F.PRISM: 6, F.FOCUS: 7, F.SHUTTER: 8,
    },
}

# Value a channel should have when nothing is asked: centered head, sharp focus,
# shutter open, everything else off.
DEFAULT_VALUES: Dict[Spot260XFunction, int] = {
    F.PAN: 128, F.TILT: 128, F.FOCUS: 128, F.SHUTTER: 255,
}


# =============================================================================== values

class Spot260XColor(IntEnum):
    """Color wheel slots. The value is the middle of the slot range."""
    WHITE = 3       # 0..6
    RED = 10        # 7..13
    ORANGE = 17     # 14..20
    YELLOW = 24     # 21..27
    GREEN = 31      # 28..34
    BLUE = 38       # 35..41
    CTO = 45        # 42..48 (warm white filter)
    CYAN = 52       # 49..55
    MAGENTA = 59    # 56..62


class Spot260XGobo(IntEnum):
    """Gobo wheel slots. The value is the middle of the slot range."""
    OPEN = 3        # 0..7 (no gobo)
    GOBO_1 = 11     # 8..15
    GOBO_2 = 19     # 16..23
    GOBO_3 = 27     # 24..31
    GOBO_4 = 35     # 32..39
    GOBO_5 = 43     # 40..47
    GOBO_6 = 51     # 48..55
    GOBO_7 = 59     # 56..63


class GoboRotation(Enum):
    """Gobo rotation channel: direction (the speed is given separately)."""
    NONE = "none"
    CLOCKWISE = "clockwise"
    COUNTER_CLOCKWISE = "counter_clockwise"
    BOUNCE = "bounce"


class StrobeEffect(Enum):
    """Kinds of strobe on the shutter channel."""
    NORMAL = "normal"
    PULSE = "pulse"
    RANDOM = "random"


class Spot260XReset(IntEnum):
    """Resets on the control channel (14-channel mode only)."""
    PAN = 99           # 96..103
    TILT = 107         # 104..111
    COLOR_WHEEL = 115  # 112..119
    GOBO_WHEEL = 123   # 120..127
    PRISM = 139        # 136..143
    FOCUS = 147        # 144..151
    ALL = 155          # 152..159


class BlackoutOnMove(IntEnum):
    """Light blacked out while something moves (control channel, 14-channel mode only)."""
    NONE = 0               # 0..7
    PAN_TILT = 11          # 8..15
    COLOR_WHEEL = 19       # 16..23
    GOBO_WHEEL = 27        # 24..31
    PAN_TILT_COLOR = 35    # 32..39
    PAN_TILT_GOBO = 43     # 40..47
    ALL = 51               # 48..55


# Raw ranges of the chart, used by the helpers below.
COLOR_INDEXING: Range = (65, 189)             # continuous wheel position
COLOR_RAINBOW: Range = (190, 221)             # rainbow, fast (190) to slow (221)
COLOR_RAINBOW_STOP = 222                      # 222..223
COLOR_RAINBOW_REVERSE: Range = (224, 255)     # reverse rainbow, slow to fast

GOBO_SHAKE_FIRST = 64                         # gobo 7 shake starts at 64, gobo 1 at 112
GOBO_SHAKE_WIDTH = 8
GOBO_CYCLE: Range = (128, 189)                # cycle effect, slow to fast
GOBO_CYCLE_STOP = 191                         # 190..193
GOBO_CYCLE_REVERSE: Range = (194, 255)        # reverse cycle, slow to fast

ROTATION_RANGES: Dict[GoboRotation, Range] = {
    GoboRotation.CLOCKWISE: (8, 119),
    GoboRotation.COUNTER_CLOCKWISE: (120, 231),
    GoboRotation.BOUNCE: (232, 255),
}

PRISM_OFF = 0                                 # 0..15
PRISM_ON = 255                                # 16..255: 3-facet prism

SHUTTER_CLOSED = 0                            # 0..3: no light
SHUTTER_OPEN = 255                            # 216..255 (4..7 is open too)
STROBE_RANGES: Dict[StrobeEffect, Range] = {
    StrobeEffect.NORMAL: (8, 76),
    StrobeEffect.PULSE: (77, 145),
    StrobeEffect.RANDOM: (146, 215),
}

MACRO_COUNT = 8
MOVEMENT_MACRO_FIRST = 8                      # macro 1 = 8..23, macro 2 = 24..39...
SOUND_MACRO_FIRST = 136                       # sound-active macro 1 = 136..151...
MACRO_WIDTH = 16


def gobo_shake_range(gobo: int) -> Range:
    """DMX range of the "shake" effect of gobo 1..7 (gobo 7 comes first on the wheel)."""
    if not 1 <= gobo <= 7:
        raise ValueError("gobo number must be 1..7")
    low = GOBO_SHAKE_FIRST + (7 - gobo) * GOBO_SHAKE_WIDTH
    return low, low + GOBO_SHAKE_WIDTH - 1


def movement_macro_range(number: int, sound_active: bool = False) -> Range:
    """DMX range of movement macro 1..8 (or of its sound-active version)."""
    if not 1 <= number <= MACRO_COUNT:
        raise ValueError("macro number must be 1..8")
    first = SOUND_MACRO_FIRST if sound_active else MOVEMENT_MACRO_FIRST
    low = first + (number - 1) * MACRO_WIDTH
    return low, min(low + MACRO_WIDTH - 1, 255)


def degrees_to_16bit(degrees: float, full_range: float) -> int:
    """Angle 0..full_range -> 16-bit position 0..65535, rounded half up (same as C/C#/Java)."""
    degrees = max(0.0, min(full_range, float(degrees)))
    return int(degrees * 0xFFFF / full_range + 0.5)


# =============================================================================== fixture

class ChauvetSpot260X:
    """Computes the DMX channels of one Intimidator Spot 260X and writes them into a
    universe (512 values, index 0 = channel 1)."""

    def __init__(self, address: int, mode: Spot260XMode = Spot260XMode.CHANNELS_14):
        """
        :param address: DMX address set in the fixture menu (1..499 in 14-channel mode).
        :param mode: DMX mode set in the fixture menu.
        """
        self.address = address
        self.mode = Spot260XMode(mode)
        check_address(address, self.footprint_size)

    # ------------------------------------------------------------------ channels

    @property
    def footprint_size(self) -> int:
        """Number of DMX channels used (8 or 14)."""
        return int(self.mode)

    @property
    def footprint(self) -> range:
        """DMX channels used."""
        return range(self.address, self.address + self.footprint_size)

    def has(self, function: Spot260XFunction) -> bool:
        """True if the current mode has this function (no dimmer in 8-channel mode...)."""
        return function in CHANNEL_MAP[self.mode]

    def dmx_channel(self, function: Spot260XFunction) -> int:
        """Absolute DMX channel (1..512) of a function. ValueError if the mode lacks it."""
        if not self.has(function):
            raise ValueError(f"{function.value} is not available in {int(self.mode)}-channel mode")
        return self.address + CHANNEL_MAP[self.mode][function] - 1

    def set(self, universe: Universe, function: Spot260XFunction, value: int) -> None:
        """Writes the raw value of one function into the universe."""
        universe[self.dmx_channel(function) - 1] = clamp_byte(value)

    def apply_defaults(self, universe: Universe) -> None:
        """Centered head, sharp focus, shutter open, everything else at 0."""
        for function in CHANNEL_MAP[self.mode]:
            self.set(universe, function, DEFAULT_VALUES.get(function, 0))

    # ------------------------------------------------------------------ movement

    def _set_16bit(self, universe: Universe, coarse: Spot260XFunction, fine: Spot260XFunction,
                   position: int) -> None:
        """Writes a 16-bit position; the fine byte is dropped in 8-channel mode."""
        high, low = split_16bit(position)
        self.set(universe, coarse, high)
        if self.has(fine):
            self.set(universe, fine, low)

    def set_pan(self, universe: Universe, position: int) -> None:
        """Pan as a 16-bit position 0..65535 (0x8000 = middle)."""
        self._set_16bit(universe, F.PAN, F.PAN_FINE, position)

    def set_tilt(self, universe: Universe, position: int) -> None:
        """Tilt as a 16-bit position 0..65535 (0x8000 = middle)."""
        self._set_16bit(universe, F.TILT, F.TILT_FINE, position)

    def set_pan_degrees(self, universe: Universe, degrees: float,
                        full_range: float = PAN_RANGE_DEGREES) -> None:
        """Pan in degrees, 0..540 (pass full_range if the menu "Pan Angle" is 360 or 180)."""
        self.set_pan(universe, degrees_to_16bit(degrees, full_range))

    def set_tilt_degrees(self, universe: Universe, degrees: float,
                         full_range: float = TILT_RANGE_DEGREES) -> None:
        """Tilt in degrees, 0..234 (pass full_range if the menu "Tilt Angle" is 180 or 90)."""
        self.set_tilt(universe, degrees_to_16bit(degrees, full_range))

    def set_pan_tilt_speed(self, universe: Universe, value: int) -> None:
        """Movement speed, fixture convention: 0 = fastest, 255 = slowest. 14-channel mode only."""
        self.set(universe, F.PAN_TILT_SPEED, value)

    def set_movement_macro(self, universe: Universe, number: int, sound_active: bool = False) -> None:
        """Runs built-in movement macro 1..8 (optionally its sound-active version). 14-channel mode only."""
        self.set(universe, F.MOVEMENT_MACRO, middle(*movement_macro_range(number, sound_active)))

    def stop_movement_macro(self, universe: Universe) -> None:
        self.set(universe, F.MOVEMENT_MACRO, 0)

    # --------------------------------------------------------------------- color

    def set_color(self, universe: Universe, color: Spot260XColor) -> None:
        """Puts one color of the wheel in the beam."""
        self.set(universe, F.COLOR_WHEEL, Spot260XColor(color))

    def set_color_wheel_position(self, universe: Universe, position: int) -> None:
        """Continuous wheel position 0..255 (lets you stop between two colors)."""
        self.set(universe, F.COLOR_WHEEL, scale_into_range(position, *COLOR_INDEXING))

    def set_color_rainbow(self, universe: Universe, speed: int, reverse: bool = False) -> None:
        """Turns the color wheel continuously. speed: 0 = slowest, 255 = fastest."""
        if reverse:
            value = scale_into_range(speed, *COLOR_RAINBOW_REVERSE)
        else:
            # this range goes from fast to slow: flip it so that 255 is always the fastest
            low, high = COLOR_RAINBOW
            value = high - (scale_into_range(speed, low, high) - low)
        self.set(universe, F.COLOR_WHEEL, value)

    def stop_color_rainbow(self, universe: Universe) -> None:
        self.set(universe, F.COLOR_WHEEL, COLOR_RAINBOW_STOP)

    # ---------------------------------------------------------------------- gobo

    def set_gobo(self, universe: Universe, gobo: Spot260XGobo) -> None:
        """Puts one gobo in the beam (Spot260XGobo.OPEN = no gobo)."""
        self.set(universe, F.GOBO_WHEEL, Spot260XGobo(gobo))

    def set_gobo_shake(self, universe: Universe, gobo: int, speed: int) -> None:
        """Shakes gobo 1..7. speed: 0 = slowest, 255 = fastest."""
        self.set(universe, F.GOBO_WHEEL, scale_into_range(speed, *gobo_shake_range(gobo)))

    def set_gobo_cycle(self, universe: Universe, speed: int, reverse: bool = False) -> None:
        """Turns the gobo wheel continuously. speed: 0 = slowest, 255 = fastest."""
        cycle = GOBO_CYCLE_REVERSE if reverse else GOBO_CYCLE
        self.set(universe, F.GOBO_WHEEL, scale_into_range(speed, *cycle))

    def stop_gobo_cycle(self, universe: Universe) -> None:
        self.set(universe, F.GOBO_WHEEL, GOBO_CYCLE_STOP)

    def set_gobo_rotation(self, universe: Universe, rotation: GoboRotation, speed: int = 128) -> None:
        """Rotates the gobo itself. speed: 0 = slowest, 255 = fastest."""
        if rotation == GoboRotation.NONE:
            self.set(universe, F.GOBO_ROTATION, 0)
        else:
            self.set(universe, F.GOBO_ROTATION, scale_into_range(speed, *ROTATION_RANGES[rotation]))

    # ------------------------------------------------------------- prism / focus

    def set_prism(self, universe: Universe, on: bool) -> None:
        """3-facet prism in or out of the beam."""
        self.set(universe, F.PRISM, PRISM_ON if on else PRISM_OFF)

    def set_focus(self, universe: Universe, value: int) -> None:
        """Focus 0..255."""
        self.set(universe, F.FOCUS, value)

    # ---------------------------------------------------------- dimmer / shutter

    def set_dimmer(self, universe: Universe, level: int) -> None:
        """Dimmer 0..255 (0..100 %). 14-channel mode only."""
        self.set(universe, F.DIMMER, level)

    def open_shutter(self, universe: Universe) -> None:
        """Shutter open, no strobe."""
        self.set(universe, F.SHUTTER, SHUTTER_OPEN)

    def close_shutter(self, universe: Universe) -> None:
        """Shutter closed: no light at all."""
        self.set(universe, F.SHUTTER, SHUTTER_CLOSED)

    def set_strobe(self, universe: Universe, speed: int, effect: StrobeEffect = StrobeEffect.NORMAL) -> None:
        """Strobe. speed: 0 = slowest, 255 = fastest. Use open_shutter() to stop it."""
        self.set(universe, F.SHUTTER, scale_into_range(speed, *STROBE_RANGES[effect]))

    def light_on(self, universe: Universe, level: int = 255) -> None:
        """Makes the fixture emit light: dimmer at ``level`` (14-channel mode) and shutter open."""
        if self.has(F.DIMMER):
            self.set_dimmer(universe, level)
        self.open_shutter(universe)

    def blackout(self, universe: Universe) -> None:
        """No light: dimmer at 0 (14-channel mode) and shutter closed."""
        if self.has(F.DIMMER):
            self.set_dimmer(universe, 0)
        self.close_shutter(universe)

    # ------------------------------------------------------------------- control

    def set_blackout_on_move(self, universe: Universe, option: BlackoutOnMove) -> None:
        """Blacks out the beam while pan/tilt or a wheel moves. 14-channel mode only."""
        self.set(universe, F.CONTROL, BlackoutOnMove(option))

    def reset(self, universe: Universe, target: Spot260XReset = Spot260XReset.ALL) -> None:
        """Starts a reset. Call clear_control() a few seconds later. 14-channel mode only."""
        self.set(universe, F.CONTROL, Spot260XReset(target))

    def clear_control(self, universe: Universe) -> None:
        """Control channel back to "no function"."""
        self.set(universe, F.CONTROL, 0)
