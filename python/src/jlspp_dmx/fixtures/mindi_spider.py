"""
Messagerie DMX du Mindi Mini Spider 8x3W RGBW (mode 15 canaux).
Voir docs/fixtures/mindi-mini-spider.md.

BIZARRERIE CONSTATEE : regle sur l'adresse N, le Spider ignore le canal N et ecoute
a partir de N+1. Cette classe applique ce decalage (``address_quirk=True`` par defaut) :
on lui donne l'adresse AFFICHEE sur l'appareil.

Exemple ::

    spider = MindiSpider(address=1)
    spider.set_dimmer(universe, 255)
    spider.set_wings(universe, 200, mirror=True)
    spider.set_led(universe, 1, 255)
"""

from enum import IntEnum
from typing import MutableSequence, Sequence


class SpiderChannel(IntEnum):
    """Canaux du Spider (1..15), d'apres la notice."""
    MOTOR_1 = 1          # position aile 1 : 0..255 = 0..135 degres
    MOTOR_2 = 2          # position aile 2 : 0..255 = 0..135 degres
    DIMMER = 3           # dimmer general
    STROBE = 4           # 0 = pas de strobe, puis vitesse du flash
    LED_1 = 5            # LED 1 a 8 : intensite de chaque LED (couleur supposee R,V,B,Blanc x2)
    LED_2 = 6
    LED_3 = 7
    LED_4 = 8
    LED_5 = 9
    LED_6 = 10
    LED_7 = 11
    LED_8 = 12
    MACRO = 13           # programmes d'effets integres
    EFFECT_SPEED = 14    # vitesse des effets, lent -> rapide
    RESET = 15           # laisser a 0


CHANNEL_COUNT = 15

# Repartition SUPPOSEE des LED sur les 2 ailes (a verifier sur l'appareil).
LEFT_WING_LEDS = (1, 2, 3, 4)
RIGHT_WING_LEDS = (5, 6, 7, 8)


class MindiSpider:
    """Calcule les numeros de canaux DMX d'un Spider et ecrit dans un univers
    (512 octets, index 0 = canal 1 : bytearray, liste, ou DmxLink via ses methodes)."""

    def __init__(self, address: int, address_quirk: bool = True):
        if not 1 <= address <= 512:
            raise ValueError("adresse DMX 1..512")
        self.address = address
        self.address_quirk = address_quirk

    def dmx_channel(self, channel: SpiderChannel) -> int:
        """Numero de canal DMX absolu (1..512) d'une fonction du Spider."""
        return self.address + int(channel) - 1 + (1 if self.address_quirk else 0)

    @property
    def footprint(self) -> range:
        """Canaux DMX occupes (y compris le canal ignore par la bizarrerie d'adresse)."""
        last = self.dmx_channel(SpiderChannel.RESET)
        return range(self.address, last + 1)

    def _set(self, universe: MutableSequence[int], channel: SpiderChannel, value: int) -> None:
        universe[self.dmx_channel(channel) - 1] = max(0, min(255, int(value)))

    def set_dimmer(self, universe: MutableSequence[int], level: int) -> None:
        self._set(universe, SpiderChannel.DIMMER, level)

    def set_strobe(self, universe: MutableSequence[int], speed: int) -> None:
        """0 = pas de strobe."""
        self._set(universe, SpiderChannel.STROBE, speed)

    def set_led(self, universe: MutableSequence[int], led: int, level: int) -> None:
        """led : 1..8."""
        if not 1 <= led <= 8:
            raise ValueError("LED 1 a 8")
        self._set(universe, SpiderChannel(SpiderChannel.LED_1 + led - 1), level)

    def set_wings(self, universe: MutableSequence[int], position: int, mirror: bool = False) -> None:
        """Positionne les 2 ailes. Avec ``mirror``, l'aile 2 prend la position symetrique
        (255 - position) : les ailes partent de cotes opposes et se rejoignent au milieu."""
        position = max(0, min(255, int(position)))
        self._set(universe, SpiderChannel.MOTOR_1, position)
        self._set(universe, SpiderChannel.MOTOR_2, 255 - position if mirror else position)

    def set_wing_leds(self, universe: MutableSequence[int], leds: Sequence[int], level: int) -> None:
        """Meme niveau pour un groupe de LED (ex. LEFT_WING_LEDS)."""
        for led in leds:
            self.set_led(universe, led, level)

    @staticmethod
    def motor_degrees(value: int) -> float:
        """Valeur DMX moteur -> angle (0..135 degres d'apres la notice)."""
        return value * 135.0 / 255.0
