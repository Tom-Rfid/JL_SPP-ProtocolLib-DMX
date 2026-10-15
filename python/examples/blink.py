"""
Test de liaison : fait clignoter les canaux 1..N une fois par seconde.
C'est le test qui a valide le protocole sur le vrai boitier.

    pip install pyserial
    python examples/blink.py COM6 44
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from jlspp_dmx import DmxLink  # noqa: E402

port = sys.argv[1] if len(sys.argv) > 1 else "COM6"
last_channel = int(sys.argv[2]) if len(sys.argv) > 2 else 44

with DmxLink(port, on_error=lambda e: print("liaison perdue :", e)) as link:
    print(f"Clignotement des canaux 1 a {last_channel} sur {port} - Ctrl+C pour arreter.")
    try:
        on = False
        while True:
            on = not on
            link.set_channels(1, [255 if on else 0] * last_channel)
            time.sleep(1)
    except KeyboardInterrupt:
        link.blackout()
        link.send_frame()
