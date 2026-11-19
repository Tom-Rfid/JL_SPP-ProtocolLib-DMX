# DMX messages — Mindi Mini Spider 8x3W RGBW

🇫🇷 [Version française](../fr/fixtures/mindi-mini-spider.md)

"Spider" light with 2 motorised wings, each carrying four 3 W LEDs (red, green,
blue, white). **15-channel** DMX mode (a 7-channel mode also exists, not documented
here).
Machine-readable file: [`spec/fixtures/mindi-mini-spider.json`](../../spec/fixtures/mindi-mini-spider.json).

Legend: ✅ observed on the fixture · 📄 from the manual.

## Addressing ✅

Set to address **N**, the Spider reads its 15 channels from **N to N + 14**, like any
DMX fixture. Example: address 29 → channels 29 to 43, the next fixture can start at
channel 44.

> **History.** During the first tests, the Spider seemed to ignore channel N and
> read its channels from N + 1. This shift went away once several fixtures were
> daisy-chained on the DMX line (validated in October 2026): it most likely came from
> a test with a single fixture plugged in. Since version 0.3.0 the libraries use
> normal addressing by default and keep the shift as an option for a unit that would
> really do it: `address_quirk=True` in Python, `addressQuirk: true` in C# and Java,
> `jlspp_spider_init_quirk()` in C.

## Channels

| Spider channel | DMX channel (address 1) | Function | Values | |
|---|---|---|---|---|
| 1 | 1 | Motor 1 — **left** wing position | 0..255 = 0..135° | ✅ |
| 2 | 2 | Motor 2 — **right** wing position | 0..255 = 0..135° | ✅ |
| 3 | 3 | Master dimmer | 0 = off … 255 = full | ✅ |
| 4 | 4 | Strobe | 0 = no strobe, then flash speed | ✅ |
| 5 | 5 | LED 1 — red, left wing | 0..255 | ✅ |
| 6 | 6 | LED 2 — green, left wing | 0..255 | ✅ |
| 7 | 7 | LED 3 — blue, left wing | 0..255 | ✅ |
| 8 | 8 | LED 4 — white, left wing | 0..255 | ✅ |
| 9 | 9 | LED 5 — red, right wing | 0..255 | ✅ |
| 10 | 10 | LED 6 — green, right wing | 0..255 | ✅ |
| 11 | 11 | LED 7 — blue, right wing | 0..255 | ✅ |
| 12 | 12 | LED 8 — white, right wing | 0..255 | ✅ |
| 13 | 13 | Macros: built-in effect programs | ranges from the manual | 📄 |
| 14 | 14 | Effect speed | slow → fast | 📄 |
| 15 | 15 | Reset | **keep at 0** | 📄 |

## Recipes

The master dimmer (Spider channel 3) must be open, otherwise the LEDs stay dark
whatever their values.

| Effect | Setting |
|---|---|
| Wings together | motor 1 = motor 2 = *p* |
| Mirrored wings (opposite sides, meeting in the middle) | motor 1 = *p*, motor 2 = 255 − *p* |
| Wings in the middle | motor 1 = motor 2 ≈ 128 |
| Left wing only | dimmer 255, LED 1-4 > 0, LED 5-8 = 0 |
| No strobe | strobe = 0 |

Test vectors: `mindi_spider_address29_code7` (address 29, normal addressing) and
`mindi_spider_address1_code7` (address 1 with the shift option, channels 2 to 16).

## With the libraries

```python
from jlspp_dmx.fixtures import MindiSpider, LEFT_WING_LEDS
spider = MindiSpider(address=29)
universe = bytearray(512)
spider.set_dimmer(universe, 255)
spider.set_wings(universe, 200, mirror=True)
spider.set_leds(universe, LEFT_WING_LEDS, 255)
```

```csharp
var spider = new MindiSpider(address: 29);
var universe = new byte[512];
spider.SetDimmer(universe, 255);
spider.SetWings(universe, 200, mirror: true);
```

```c
uint8_t universe[512] = {0};
jlspp_spider spider;
jlspp_spider_init(&spider, 29);
jlspp_spider_set_dimmer(&spider, universe, 255);
jlspp_spider_set_wings(&spider, universe, 200, 1);
```

```java
MindiSpider spider = new MindiSpider(29);
spider.setDimmer(universe, 255);
spider.setWings(universe, 200, true);
```
