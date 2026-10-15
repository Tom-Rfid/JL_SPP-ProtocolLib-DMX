"""
Intimidator Spot 260X: the head draws a circle and changes color every 2 seconds.

    python examples/spot260x_show.py COM6 17      (port, DMX address set in the fixture menu)

The fixture must be in 14-channel mode (menu Run Mode > DMX > 14CH).
"""

import math
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from jlspp_dmx import DmxLink  # noqa: E402
from jlspp_dmx.fixtures import ChauvetSpot260X, Spot260XColor, Spot260XGobo  # noqa: E402

port = sys.argv[1] if len(sys.argv) > 1 else "COM6"
spot = ChauvetSpot260X(address=int(sys.argv[2]) if len(sys.argv) > 2 else 17)
universe = bytearray(512)
colors = [Spot260XColor.RED, Spot260XColor.GREEN, Spot260XColor.BLUE, Spot260XColor.MAGENTA]

with DmxLink(port) as link:
    spot.apply_defaults(universe)
    spot.light_on(universe)
    spot.set_gobo(universe, Spot260XGobo.GOBO_2)
    start = time.monotonic()
    try:
        while True:
            t = time.monotonic() - start
            # circle of +/- 30 degrees around the middle of the pan/tilt travel
            spot.set_pan_degrees(universe, 270 + 30 * math.cos(t))
            spot.set_tilt_degrees(universe, 117 + 30 * math.sin(t))
            spot.set_color(universe, colors[int(t // 2) % len(colors)])
            link.set_universe(universe)
            time.sleep(0.05)
    except KeyboardInterrupt:
        link.blackout()
        link.send_frame()
