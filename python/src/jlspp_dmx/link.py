"""
Liaison serie avec le boitier JL_SPP (Bluetooth SPP vu comme un port serie).

    Windows : port COM "sortant" cree a l'appairage (ex. COM6)
    Linux   : /dev/rfcomm0 apres `rfcomm bind` (voir docs/platforms.md)
    macOS   : /dev/tty.<nom>-... (non teste)

Exemple ::

    from jlspp_dmx import DmxLink

    with DmxLink("COM6") as link:      # ouvre, envoie le handshake, demarre l'envoi a 10 Hz
        link.set_channel(1, 255)
        time.sleep(5)
                                       # a la sortie : arret, handshake de deconnexion, fermeture

Necessite pyserial (``pip install jlspp-dmx[serial]``).
"""

import threading
import time
from typing import Callable, Iterable, Optional

from .frame import HANDSHAKE_CONNECT, HANDSHAKE_DISCONNECT, UNIVERSE_SIZE, build_frame


class DmxLink:
    """Envoie en continu l'univers DMX au boitier, comme l'appli d'origine (une trame
    toutes les ``interval`` secondes, 0,1 s par defaut). Thread-safe : on peut modifier
    les canaux depuis n'importe quel thread pendant que l'envoi tourne."""

    def __init__(self, port: str, interval: float = 0.1, baudrate: int = 9600,
                 on_error: Optional[Callable[[Exception], None]] = None):
        self.port_name = port
        self.interval = interval
        self.baudrate = baudrate  # sans importance sur un port Bluetooth virtuel
        self.on_error = on_error
        self.frames_sent = 0
        self._universe = bytearray(UNIVERSE_SIZE)
        self._lock = threading.Lock()
        self._serial = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._code_num = 0

    # ------------------------------------------------------------------ canaux

    def set_channel(self, channel: int, value: int) -> None:
        """channel : 1..512 ; value : 0..255."""
        if not 1 <= channel <= UNIVERSE_SIZE:
            raise ValueError("un canal DMX va de 1 a 512")
        with self._lock:
            self._universe[channel - 1] = value & 0xFF

    def set_channels(self, first_channel: int, values: Iterable[int]) -> None:
        """Ecrit plusieurs canaux consecutifs a partir de ``first_channel``."""
        for offset, value in enumerate(values):
            self.set_channel(first_channel + offset, value)

    def get_channel(self, channel: int) -> int:
        with self._lock:
            return self._universe[channel - 1]

    def blackout(self) -> None:
        with self._lock:
            self._universe[:] = bytes(UNIVERSE_SIZE)

    def snapshot(self) -> bytes:
        with self._lock:
            return bytes(self._universe)

    # --------------------------------------------------------------- connexion

    def open(self) -> None:
        """Ouvre le port et envoie le handshake de connexion."""
        import serial  # import tardif : la partie trames reste utilisable sans pyserial

        self._serial = serial.Serial(self.port_name, self.baudrate, timeout=1, write_timeout=2)
        self._serial.write(HANDSHAKE_CONNECT)
        self._serial.flush()

    def send_frame(self) -> None:
        """Envoie une seule trame avec l'etat actuel de l'univers."""
        if self._serial is None:
            raise RuntimeError("port non ouvert : appelle open() d'abord")
        self._code_num = (self._code_num + 1) & 0xFF
        self._serial.write(build_frame(self.snapshot(), self._code_num))
        self.frames_sent += 1

    def start(self) -> None:
        """Demarre l'envoi continu dans un thread d'arriere-plan."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, name="jlspp-dmx-send", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread is not None and self._thread is not threading.current_thread():
            self._thread.join(timeout=2)
        self._thread = None

    def close(self) -> None:
        """Arrete l'envoi, envoie le handshake de deconnexion et ferme le port."""
        self.stop()
        if self._serial is not None:
            try:
                self._serial.write(HANDSHAKE_DISCONNECT)
                self._serial.flush()
            except Exception:  # le boitier a peut-etre deja coupe
                pass
            self._serial.close()
            self._serial = None

    def _loop(self) -> None:
        next_time = time.monotonic()
        while self._running:
            try:
                self.send_frame()
            except Exception as exc:  # liaison perdue
                self._running = False
                if self.on_error is not None:
                    self.on_error(exc)
                return
            next_time += self.interval
            time.sleep(max(0.001, next_time - time.monotonic()))

    def __enter__(self) -> "DmxLink":
        self.open()
        self.start()
        return self

    def __exit__(self, *exc) -> None:
        self.close()
