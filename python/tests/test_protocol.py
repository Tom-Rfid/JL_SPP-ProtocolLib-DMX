"""Tests against spec/test_vectors.json (frames validated on the hardware) and the
fixture charts in spec/fixtures/.

Run:  python -m unittest discover -s python/tests   (or: pytest python/tests)
"""

import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC_DIR = HERE.parent.parent / "spec"
sys.path.insert(0, str(HERE.parent / "src"))

from jlspp_dmx import (  # noqa: E402
    HANDSHAKE_CONNECT, HANDSHAKE_DISCONNECT, build_frame, decode_frame, is_frame,
)
from jlspp_dmx.fixtures import (  # noqa: E402
    ChauvetSpot260X, GoboRotation, MindiSpider, SpiderChannel, Spot260XColor,
    Spot260XFunction, Spot260XGobo, Spot260XMode, StrobeEffect,
)
from jlspp_dmx.fixtures.chauvet_spot260x import (  # noqa: E402
    CHANNEL_MAP, gobo_shake_range, movement_macro_range,
)

VECTORS = json.loads((SPEC_DIR / "test_vectors.json").read_text(encoding="utf-8"))
SPOT_CHART = json.loads((SPEC_DIR / "fixtures" / "chauvet-intimidator-spot-260x.json").read_text(encoding="utf-8"))


def vector_universe(name: str) -> bytes:
    """Universe of the test vector called ``name``."""
    vec = next(v for v in VECTORS["vectors"] if v["name"] == name)
    return bytes.fromhex(vec["universe_hex"])


def chart_value(function: str, label: str) -> int:
    """'value' of the range labelled ``label`` in the 260X chart."""
    channel = next(c for c in SPOT_CHART["channels"] if c["function"] == function)
    return next(r["value"] for r in channel["ranges"] if r["label"] == label)


class TestFrames(unittest.TestCase):
    def test_build_frame_matches_every_vector(self):
        for vec in VECTORS["vectors"]:
            with self.subTest(vec["name"]):
                universe = bytes.fromhex(vec["universe_hex"])
                frame = build_frame(universe, vec["code_num"], vec["scene"], vec["speed"])
                self.assertEqual(frame.hex(), vec["frame_hex"])

    def test_decode_frame_gives_back_the_universe(self):
        for vec in VECTORS["vectors"]:
            with self.subTest(vec["name"]):
                decoded = decode_frame(bytes.fromhex(vec["frame_hex"]))
                self.assertEqual(decoded.universe.hex(), vec["universe_hex"])
                self.assertEqual(decoded.code_num, vec["code_num"])

    def test_handshakes(self):
        self.assertEqual(HANDSHAKE_CONNECT.hex(), VECTORS["handshake_connect_hex"])
        self.assertEqual(HANDSHAKE_DISCONNECT.hex(), VECTORS["handshake_disconnect_hex"])

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            build_frame([0] * 10, 1)
        self.assertFalse(is_frame(b"\x00" * 521))


class TestMindiSpider(unittest.TestCase):
    def test_address_quirk_shifts_by_one(self):
        spider = MindiSpider(address=1)
        self.assertEqual(spider.dmx_channel(SpiderChannel.MOTOR_1), 2)
        self.assertEqual(spider.dmx_channel(SpiderChannel.RESET), 16)
        self.assertEqual(list(spider.footprint), list(range(1, 17)))
        self.assertEqual(MindiSpider(1, address_quirk=False).dmx_channel(SpiderChannel.MOTOR_1), 1)

    def test_helpers_reproduce_the_spider_vector(self):
        universe = bytearray(512)
        spider = MindiSpider(address=1)
        spider.set_wings(universe, 200, mirror=True)
        spider.set_dimmer(universe, 255)
        spider.set_led(universe, 1, 255)
        spider.set_led(universe, 5, 255)
        self.assertEqual(bytes(universe), vector_universe("mindi_spider_address1_code7"))


class TestChauvetSpot260X(unittest.TestCase):
    def test_helpers_reproduce_the_two_heads_vector(self):
        universe = bytearray(512)

        head1 = ChauvetSpot260X(address=17)
        head1.set_pan(universe, 0x8000)
        head1.set_tilt(universe, 0x4000)
        head1.set_color(universe, Spot260XColor.RED)
        head1.set_gobo(universe, Spot260XGobo.GOBO_3)
        head1.set_gobo_rotation(universe, GoboRotation.CLOCKWISE, speed=128)
        head1.set_prism(universe, True)
        head1.set_focus(universe, 128)
        head1.light_on(universe)

        head2 = ChauvetSpot260X(address=31)
        head2.set_pan(universe, 0x8000)
        head2.set_tilt(universe, 0x4000)
        head2.set_color(universe, Spot260XColor.BLUE)
        head2.set_gobo(universe, Spot260XGobo.OPEN)
        head2.set_focus(universe, 128)
        head2.set_dimmer(universe, 255)
        head2.set_strobe(universe, speed=128)

        self.assertEqual(bytes(universe), vector_universe("chauvet_spot260x_two_heads_code9"))

    def test_channel_maps_match_the_chart(self):
        for channel in SPOT_CHART["channels"]:
            function = Spot260XFunction(channel["function"])
            for mode, key in ((Spot260XMode.CHANNELS_14, "channel_14ch"), (Spot260XMode.CHANNELS_8, "channel_8ch")):
                with self.subTest(function=function, mode=mode):
                    self.assertEqual(CHANNEL_MAP[mode].get(function), channel[key])

    def test_slot_values_match_the_chart(self):
        for color in Spot260XColor:
            label = "CTO" if color is Spot260XColor.CTO else color.name.capitalize()  # "RED" -> "Red"
            self.assertEqual(color, chart_value("color_wheel", label))
        self.assertEqual(Spot260XGobo.OPEN, chart_value("gobo_wheel", "Open"))
        for n in range(1, 8):
            self.assertEqual(Spot260XGobo[f"GOBO_{n}"], chart_value("gobo_wheel", f"Gobo {n}"))

    def test_eight_channel_mode(self):
        spot = ChauvetSpot260X(address=1, mode=Spot260XMode.CHANNELS_8)
        self.assertFalse(spot.has(Spot260XFunction.DIMMER))
        self.assertEqual(spot.dmx_channel(Spot260XFunction.SHUTTER), 8)
        with self.assertRaises(ValueError):
            spot.set_dimmer(bytearray(512), 255)
        universe = bytearray(512)
        spot.set_pan(universe, 0x1234)       # no fine channel: only the coarse byte is written
        self.assertEqual(universe[0], 0x12)
        self.assertEqual(universe[1], 0)

    def test_ranges(self):
        self.assertEqual(gobo_shake_range(7), (64, 71))
        self.assertEqual(gobo_shake_range(1), (112, 119))
        self.assertEqual(movement_macro_range(1), (8, 23))
        self.assertEqual(movement_macro_range(8, sound_active=True), (248, 255))

    def test_speed_scaling(self):
        universe = bytearray(512)
        spot = ChauvetSpot260X(address=1)
        shutter = spot.dmx_channel(Spot260XFunction.SHUTTER) - 1
        color = spot.dmx_channel(Spot260XFunction.COLOR_WHEEL) - 1
        spot.set_strobe(universe, 255, StrobeEffect.RANDOM)
        self.assertEqual(universe[shutter], 215)
        spot.set_color_rainbow(universe, 255)        # fastest forward rainbow is 190
        self.assertEqual(universe[color], 190)
        spot.set_color_rainbow(universe, 0)
        self.assertEqual(universe[color], 221)

    def test_address_limits(self):
        ChauvetSpot260X(address=499)
        with self.assertRaises(ValueError):
            ChauvetSpot260X(address=500)
        ChauvetSpot260X(address=505, mode=Spot260XMode.CHANNELS_8)


if __name__ == "__main__":
    unittest.main()
