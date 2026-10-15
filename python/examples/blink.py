"""
Link test: makes channels 1..N blink once per second.
This is the test that validated the protocol on the real interface.

    pip install pyserial
    python examples/blink.py COM6 44        (port, last channel)
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from jlspp_dmx import DmxLink  # noqa: E402

port = sys.argv[1] if len(sys.argv) > 1 else "COM6"
last_channel = int(sys.argv[2]) if len(sys.argv) > 2 else 44

with DmxLink(port, on_error=lambda e: print("link lost:", e)) as link:
    print(f"Blinking channels 1 to {last_channel} on {port} - Ctrl+C to stop.")
    try:
        on = False
        while True:
            on = not on
            link.set_channels(1, [255 if on else 0] * last_channel)
            time.sleep(1)
    except KeyboardInterrupt:
        link.blackout()
        link.send_frame()  # make sure the fixtures end dark
