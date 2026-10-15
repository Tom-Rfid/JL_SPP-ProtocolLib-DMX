"""Tests contre spec/test_vectors.json (trames validees sur le materiel).
Lancement : python -m unittest discover -s python/tests   (ou pytest python/tests)"""

import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from jlspp_dmx import (  # noqa: E402
    HANDSHAKE_CONNECT, HANDSHAKE_DISCONNECT, build_frame, decode_frame, is_frame,
)
from jlspp_dmx.fixtures import MindiSpider, SpiderChannel  # noqa: E402

SPEC = json.loads((HERE.parent.parent / "spec" / "test_vectors.json").read_text(encoding="utf-8"))


class TestVectors(unittest.TestCase):
    def test_build_frame_matches_every_vector(self):
        for vec in SPEC["vectors"]:
            with self.subTest(vec["name"]):
                universe = bytes.fromhex(vec["universe_hex"])
                frame = build_frame(universe, vec["code_num"], vec["scene"], vec["speed"])
                self.assertEqual(frame.hex(), vec["frame_hex"])

    def test_decode_frame_gives_back_the_universe(self):
        for vec in SPEC["vectors"]:
            with self.subTest(vec["name"]):
                decoded = decode_frame(bytes.fromhex(vec["frame_hex"]))
                self.assertEqual(decoded.universe.hex(), vec["universe_hex"])
                self.assertEqual(decoded.code_num, vec["code_num"])

    def test_handshakes(self):
        self.assertEqual(HANDSHAKE_CONNECT.hex(), SPEC["handshake_connect_hex"])
        self.assertEqual(HANDSHAKE_DISCONNECT.hex(), SPEC["handshake_disconnect_hex"])

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

    def test_spider_vector_is_reproduced_with_the_helper(self):
        universe = bytearray(512)
        spider = MindiSpider(address=1)
        spider.set_wings(universe, 200, mirror=True)
        spider.set_dimmer(universe, 255)
        spider.set_led(universe, 1, 255)
        spider.set_led(universe, 5, 255)
        vec = next(v for v in SPEC["vectors"] if v["name"] == "mindi_spider_adresse1_code7")
        self.assertEqual(bytes(universe).hex(), vec["universe_hex"])


if __name__ == "__main__":
    unittest.main()
