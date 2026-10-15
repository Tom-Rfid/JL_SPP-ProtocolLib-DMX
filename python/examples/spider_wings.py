"""
Mini Spider: both wings swing in mirror, left/right LEDs fade in turn.

    python examples/spider_wings.py COM6 1      (port, address shown on the Spider)
"""

import math
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from jlspp_dmx import DmxLink  # noqa: E402
from jlspp_dmx.fixtures import LEFT_WING_LEDS, RIGHT_WING_LEDS, MindiSpider  # noqa: E402

port = sys.argv[1] if len(sys.argv) > 1 else "COM6"
spider = MindiSpider(address=int(sys.argv[2]) if len(sys.argv) > 2 else 1)
universe = bytearray(512)

with DmxLink(port) as link:
    spider.set_dimmer(universe, 255)
    spider.stop_strobe(universe)
    start = time.monotonic()
    try:
        while True:
            t = time.monotonic() - start
            position = int(127.5 + 127.5 * math.sin(t))          # one back-and-forth every ~6 s
            spider.set_wings(universe, position, mirror=True)
            left = int(255 * (0.5 + 0.5 * math.sin(t * 2)))
            spider.set_leds(universe, LEFT_WING_LEDS, left)
            spider.set_leds(universe, RIGHT_WING_LEDS, 255 - left)
            link.set_universe(universe)
            time.sleep(0.05)
    except KeyboardInterrupt:
        link.blackout()
        link.send_frame()
