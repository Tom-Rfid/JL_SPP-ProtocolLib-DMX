# DMX messages — Chauvet DJ Intimidator Spot 260X

🇫🇷 [Version française](../fr/fixtures/chauvet-intimidator-spot-260x.md)

75 W LED spot moving head: pan 540°, tilt 234°, 9-colour wheel, wheel of 7 rotating
gobos, 3-facet prism, motorised focus.

Source: **Intimidator Spot 260X Quick Reference Guide Rev. 1** (Chauvet).
Machine-readable file: [`spec/fixtures/chauvet-intimidator-spot-260x.json`](../../spec/fixtures/chauvet-intimidator-spot-260x.json).

## Modes and addressing

The mode is picked in the fixture menu: **Run Mode → DMX → 14CH / 8CH**. The
address is set in **Address** (001–512): set to N, the head reads its channels
from N.

| Mode | Channels | Highest start address |
|---|---|---|
| 14 channels | everything, 16-bit pan/tilt, dimmer, reset, macros | 499 |
| 8 channels | pan, tilt, colour, gobo, rotation, prism, focus, shutter | 505 |

Example patch: head 1 at **1** (1–14), head 2 at **15** (15–28), Mini Spider at
**29** (29–43).

## Channels

| Function | 14 ch. | 8 ch. | Values |
|---|---|---|---|
| Pan | 1 | 1 | 0–255 = 0–540° |
| Pan fine | 2 | — | low byte of pan |
| Tilt | 3 | 2 | 0–255 = 0–234° |
| Tilt fine | 4 | — | low byte of tilt |
| Pan/tilt speed | 5 | — | **0 = fastest**, 255 = slowest |
| Colour wheel | 6 | 3 | see below |
| Gobo wheel | 7 | 4 | see below |
| Gobo rotation | 8 | 5 | see below |
| Prism | 9 | 6 | 0–15 no prism, 16–255 3-facet prism |
| Focus | 10 | 7 | 0–255 |
| Dimmer | 11 | — | 0–255 = 0–100 % |
| Shutter / strobe | 12 | 8 | see below |
| Functions (blackout, resets) | 13 | — | see below |
| Movement macros | 14 | — | see below |

⚠ The 8-channel mode has **no dimmer**: light comes on with the shutter open
(channel 8 at 255).

### Colour wheel

| Values | Colour | Value sent by the libraries |
|---|---|---|
| 0–6 | White | 3 |
| 7–13 | Red | 10 |
| 14–20 | Orange | 17 |
| 21–27 | Yellow | 24 |
| 28–34 | Green | 31 |
| 35–41 | Blue | 38 |
| 42–48 | CTO (warm white) | 45 |
| 49–55 | Cyan | 52 |
| 56–62 | Magenta | 59 |
| 63–64 | White | |
| 65–189 | Continuous wheel position (between two colours) | |
| 190–221 | Rainbow, **fast → slow** | |
| 222–223 | Stop | |
| 224–255 | Reverse rainbow, slow → fast | |

The libraries send the **middle** of each range: the safest value to land squarely
on the colour.

### Gobo wheel

| Values | Effect |
|---|---|
| 0–7 | Open (no gobo) |
| 8–15, 16–23, … 56–63 | Gobo 1 to 7 (steps of 8) |
| 64–71 | Gobo 7 shaking, slow → fast |
| 72–79 … 112–119 | Gobo 6 … gobo 1 shaking (reverse order) |
| 120–127 | Open |
| 128–189 | Wheel rotation, slow → fast |
| 190–193 | Stop |
| 194–255 | Reverse wheel rotation, slow → fast |

### Gobo rotation

| Values | Effect |
|---|---|
| 0–7 | No rotation |
| 8–119 | Clockwise, slow → fast |
| 120–231 | Counter-clockwise, slow → fast |
| 232–255 | Back and forth, slow → fast |

### Shutter / strobe

| Values | Effect |
|---|---|
| 0–3 | **Closed** (no light) |
| 4–7 | Open |
| 8–76 | Strobe, slow → fast |
| 77–145 | Pulse strobe, slow → fast |
| 146–215 | Random strobe, slow → fast |
| 216–255 | Open |

### Functions (channel 13, 14-channel mode)

| Values | Effect |
|---|---|
| 0–7 | Nothing |
| 8–15 | Blackout during pan/tilt movement |
| 16–23 | Blackout during colour wheel movement |
| 24–31 | Blackout during gobo wheel movement |
| 32–39 | Blackout pan/tilt + colours |
| 40–47 | Blackout pan/tilt + gobos |
| 48–55 | Blackout pan/tilt + colours + gobos |
| 96–103 | Pan reset |
| 104–111 | Tilt reset |
| 112–119 | Colour wheel reset |
| 120–127 | Gobo wheel reset |
| 136–143 | Prism reset |
| 144–151 | Focus reset |
| 152–159 | Full reset |
| others | Nothing |

After a reset, set the channel back to 0 after a few seconds.

### Movement macros (channel 14, 14-channel mode)

| Values | Effect |
|---|---|
| 0–7 | No macro |
| 8–23, 24–39, … 120–135 | Macro 1 to 8 (steps of 16) |
| 136–151, … 232–247 | Sound macro 1 to 7 |
| 248–255 | Sound macro 8 |

## Recipes

| Effect | Setting (14-channel mode) |
|---|---|
| Light on | dimmer 255 + shutter 255 |
| Light off, keeping the position | shutter 0 (or dimmer 0) |
| Head centred | pan 128/0, tilt 128/0 |
| Smooth movement | 16-bit pan/tilt (fine channels) + speed 0 |
| Fixed colour | wheel = middle value of the colour |

## With the libraries

In the libraries, **every speed goes from 0 = slow to 255 = fast**, even when the DMX
range is reversed (rainbow). Only exception: the pan/tilt speed keeps the fixture
convention (0 = fast).

```python
from jlspp_dmx.fixtures import ChauvetSpot260X, Spot260XColor, Spot260XGobo
spot = ChauvetSpot260X(address=17)            # 14-channel mode by default
universe = bytearray(512)
spot.light_on(universe)
spot.set_pan_degrees(universe, 270)
spot.set_color(universe, Spot260XColor.RED)
spot.set_gobo(universe, Spot260XGobo.GOBO_3)
spot.set_strobe(universe, speed=200)
```

```csharp
var spot = new ChauvetSpot260X(address: 17);
var universe = new byte[512];
spot.LightOn(universe);
spot.SetPanDegrees(universe, 270);
spot.SetColor(universe, Spot260XColor.Red);
```

```c
jlspp_spot260x spot;
jlspp_spot260x_init(&spot, 17, JLSPP_SPOT260X_MODE_14CH);
jlspp_spot260x_light_on(&spot, universe, 255);
jlspp_spot260x_set_color(&spot, universe, JLSPP_SPOT260X_RED);
```

```java
ChauvetSpot260X spot = new ChauvetSpot260X(17);
spot.lightOn(universe, 255);
spot.setColor(universe, ChauvetSpot260X.Color.RED);
```

The `chauvet_spot260x_two_heads_code9` test vector (two heads at 17 and 31) is
reproduced by the helpers of every language.
