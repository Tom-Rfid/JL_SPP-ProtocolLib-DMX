# jlspp-dmx (Python)

Pilotage des boîtiers Bluetooth DMX « JL_SPP » (appli RY-AI). Python ≥ 3.9.
Spécification : [../docs/protocol.md](../docs/protocol.md).

## Installation

```bash
pip install ./python[serial]   # depuis la racine du dépôt ; [serial] ajoute pyserial
```

Sans `[serial]`, seule la construction et le décodage des trames sont disponibles.

## Utilisation

```python
import time
from jlspp_dmx import DmxLink

with DmxLink("COM6") as link:     # Linux : "/dev/rfcomm0"
    link.set_channel(1, 255)      # canaux 1..512
    link.set_channels(10, [255, 128, 0])
    time.sleep(5)
# à la sortie : arrêt de l'envoi, handshake de déconnexion, fermeture
```

Construire les trames soi-même (univers de 512 octets, index 0 = canal 1) :

```python
from jlspp_dmx.frame import build_frame, decode_frame, HANDSHAKE_CONNECT

universe = bytearray(512)
universe[0] = 255
frame = build_frame(universe, code_num=0)   # 521 octets
decoded = decode_frame(frame)               # .universe, .code_num, .scene, .speed
```

Mindi Mini Spider (voir [../docs/fixtures/mindi-mini-spider.md](../docs/fixtures/mindi-mini-spider.md)) :

```python
from jlspp_dmx.fixtures import MindiSpider

spider = MindiSpider(address=1)             # adresse affichée, décalage géré
universe = bytearray(512)
spider.set_dimmer(universe, 255)
spider.set_wings(universe, 200, mirror=True)
```

Chauvet Intimidator Spot 260X (voir [../docs/fixtures/chauvet-intimidator-spot-260x.md](../docs/fixtures/chauvet-intimidator-spot-260x.md)) :

```python
from jlspp_dmx.fixtures import ChauvetSpot260X, GoboRotation, Spot260XColor, Spot260XGobo

spot = ChauvetSpot260X(address=17)          # mode 14 canaux par défaut
spot.light_on(universe)                     # dimmer 100 % + obturateur ouvert
spot.set_pan_degrees(universe, 270)
spot.set_color(universe, Spot260XColor.RED)
spot.set_gobo(universe, Spot260XGobo.GOBO_3)
spot.set_gobo_rotation(universe, GoboRotation.CLOCKWISE, speed=100)
link.set_universe(universe)
```

## Exemples

```bash
python python/examples/blink.py COM6
python python/examples/spider_wings.py COM6 1
python python/examples/spot260x_show.py COM6 17
```

## Tests

```bash
cd python
python -m unittest discover -s tests -v
```
