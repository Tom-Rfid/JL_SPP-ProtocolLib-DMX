# JL_SPP-ProtocolLib-DMX

**Drive cheap Bluetooth "USB-RDM-DMX" boxes from your own code — Python, C, C# or Android.**

🇫🇷 Version française plus bas : [lire en français](#-version-française) · [README.fr.md](README.fr.md)

![Languages](https://img.shields.io/badge/libraries-Python%20%7C%20C99%20%7C%20C%23%20%7C%20Java-blue)
![Protocol](https://img.shields.io/badge/protocol-validated%20on%20hardware-brightgreen)
![Contributions](https://img.shields.io/badge/fixture%20modules-contributions%20welcome-orange)

These little boxes (Jieli chip, `JL_SPP` serial service, sold with the **RY-AI**
Android app) receive a 512-channel DMX universe over Bluetooth and send it out on
their XLR plug. Until now only the phone app could talk to them. This repository
documents the protocol and gives you ready-made libraries, so a PC, a Mac, a Linux
box, a microcontroller or your own Android app can run your lights.

```
 your code ──► jlspp-dmx library ──► Bluetooth SPP ──► USB-RDM-DMX box ──► XLR ──► fixtures
              (frame + scrambling)    (virtual COM)
```

## Why use it

- **Four libraries, one behaviour.** Python, C99, C# (.NET Standard 2.0) and Java /
  Android build the very same frames, byte for byte, checked against shared
  [test vectors](spec/test_vectors.json).
- **Modular fixtures.** Each light is a small *fixture module*: a class with one
  readable function per action (`set_color`, `set_gobo`, `set_wings`, `set_strobe`,
  `reset`…) instead of channel numbers and magic values. Plug in the modules you
  need, write your own in a few dozen lines.
- **Easy addressing.** Give a module the DMX address shown on the fixture; it works
  out its own channels, checks that it fits in the universe and writes into a plain
  512-byte array. Several fixtures share the same universe, no global state.
- **No heavy dependencies.** The C library has no allocation and no I/O (works on a
  microcontroller); Python only needs `pyserial` to talk to the port; C# only
  `System.IO.Ports`.
- **Documented down to the byte**, with what was verified on real hardware and what
  was only read in the decompiled app clearly marked.

## Quick start

**Python**

```bash
pip install ./python[serial]
```

```python
import time
from jlspp_dmx import DmxLink
from jlspp_dmx.fixtures import ChauvetSpot260X, Spot260XColor, MindiSpider

universe = bytearray(512)                         # index 0 = DMX channel 1

head = ChauvetSpot260X(address=1)                 # 14-channel mode, channels 1-14
spider = MindiSpider(address=29, address_quirk=False)

head.light_on(universe)
head.set_color(universe, Spot260XColor.BLUE)
spider.set_dimmer(universe, 255)
spider.set_wings(universe, 200, mirror=True)

with DmxLink("COM6") as link:                     # handshake + frames every 100 ms
    link.set_universe(universe)
    time.sleep(5)
```

**C#**

```csharp
using JlSpp.Dmx;
using JlSpp.Dmx.Fixtures;

var universe = new byte[512];
var head = new ChauvetSpot260X(address: 1);
head.LightOn(universe);
head.SetColor(universe, Spot260XColor.Red);

using var link = new DmxLink("COM6");             // the OUTGOING "JL_SPP" COM port
link.Open();                                      // open + connect handshake
link.Start();                                     // continuous sending every 100 ms
link.SetUniverse(universe);
```

**C** — the library builds frames, you write them to the port your way
(full Win32 / POSIX example in [c/examples/blink.c](c/examples/blink.c)):

```c
uint8_t universe[JLSPP_UNIVERSE_SIZE] = {0}, frame[JLSPP_FRAME_LEN];
universe[0] = 255;                                /* channel 1 */
jlspp_build_frame(universe, code++, 0, 0, frame);
write_port(frame, JLSPP_FRAME_LEN);
```

**Android** — `SppDmxLink` opens an RFCOMM socket to the paired box, see
[android/](android).

Each folder has its own README with build and test commands:
[python](python) · [c](c) · [csharp](csharp) · [android](android).

## Fixture modules

| Module | Fixture | Modes | Status |
|---|---|---|---|
| `ChauvetSpot260X` | Chauvet DJ Intimidator Spot 260X (moving head) | 14 and 8 channels | 📄 official Chauvet chart (Quick Reference Guide Rev. 1) |
| `MindiSpider` | Mindi Mini Spider 8x3W RGBW | 15 channels | ✅ channels, wings and LED colours confirmed |

Each module comes with a human-readable chart in [docs/fixtures/](docs/fixtures) and a
machine-readable one in [spec/fixtures/](spec/fixtures).

The [DmxCtrl](https://github.com/Tom-Rfid/DmxCtrl) app already drives more fixtures
(UV LED PAR, Showtec Galactic laser, Ayra fog machine) through its own profiles: they
are good candidates for new modules here — see below.

### Addressing in practice

A module only needs its start address. With two moving heads and a Spider on the
same line:

| Fixture | Address set on the fixture | Channels used |
|---|---|---|
| Intimidator Spot 260X #1 (14 ch) | 1 | 1–14 |
| Intimidator Spot 260X #2 (14 ch) | 15 | 15–28 |
| Mini Spider (15 ch) | 29 | 29–43 |

```python
heads = [ChauvetSpot260X(address=a) for a in (1, 15)]
for h in heads:
    h.set_pan_degrees(universe, 270)
```

A module refuses an address that would overflow the universe (`ValueError` in
Python, `ArgumentOutOfRangeException` in C#, `JLSPP_ERROR` in C).

> The Mini Spider seemed to skip its first channel during the very first tests; it
> addresses normally once several fixtures are chained. The libraries keep that
> shift as an option (`address_quirk`), on by default for compatibility — pass
> `False` for normal addressing. Details in
> [docs/fixtures/mindi-mini-spider.md](docs/fixtures/mindi-mini-spider.md).

## Add your own fixture — contributions welcome!

**Everybody is welcome to add a fixture module.** You own a light that is not in the
list? Its DMX chart is usually in the manual: turn it into a module and open a pull
request. Even a chart alone (no code) is a useful contribution.

1. **Chart** — write `docs/fixtures/<brand>-<model>.md` (copy an existing one), and
   mark each channel ✅ tested on the fixture, 📄 from the manual or ❓ assumed.
2. **Data** — add `spec/fixtures/<brand>-<model>.json` with the same channels.
3. **Code** — add a module in one language or more, following the existing ones:
   - Python: `python/src/jlspp_dmx/fixtures/<model>.py`, exported in `fixtures/__init__.py`
   - C#: `csharp/src/JlSpp.Dmx/Fixtures/<Model>.cs`
   - C: `c/include/jlspp_<model>.h` + `c/src/jlspp_<model>.c`
   - Java: `android/jlspp-dmx/src/main/java/io/github/tomrfid/jlsppdmx/<Model>.java`

   Use the shared helpers (`clamp_byte`, `scale_into_range`, `middle`,
   `check_address`…) so that every language gives the same values. One language is
   fine: someone else can port it.
4. **Test** — a test that writes a known universe, ideally checked on the real fixture.

Full guide: [CONTRIBUTING.md](CONTRIBUTING.md). Bug reports, tests on Linux / macOS
and RDM findings are welcome too.

## The protocol in short

1. Open the box serial port (Windows: the **outgoing** "JL_SPP" COM port).
2. Send `BB 99 77 01 77 99`.
3. Every 100 ms, send a 521-byte frame:

   | Bytes | Content |
   |---|---|
   | 0 | `00` |
   | 1-2 | `4B 54` ("KT") |
   | 3-4 | scene, speed (`00 00` in direct control) |
   | 5-516 | channels 1 to 512, **scrambled** |
   | 517-518 | key: `sin[code]`, `code` (counter 0..255) |
   | 519-520 | `54 4B` ("TK") |

4. When leaving, send `BB 77 99 10 99 77 00 55`, then close.

## Status

| Part | Status |
|---|---|
| DMX frame, scrambling, handshakes | ✅ validated on the hardware |
| Python, C, C# | ✅ tested against the reference vectors |
| Android | ⚠ written from the original app, **not compiled or tested yet** |
| Stand-alone scenes, RDM | 🔍 read in the decompiled code, to be checked |

## Documentation

| | 🇬🇧 English | 🇫🇷 Français |
|---|---|---|
| Protocol (transport, handshakes, frames, scenes, RDM) | [protocol.md](docs/protocol.md) | [protocol.md](docs/fr/protocol.md) |
| Channel scrambling | [cipher.md](docs/cipher.md) | [cipher.md](docs/fr/cipher.md) |
| Connecting on Windows / Linux / macOS / Android | [platforms.md](docs/platforms.md) | [platforms.md](docs/fr/platforms.md) |
| How the protocol was recovered | [reverse-engineering.md](docs/reverse-engineering.md) | [reverse-engineering.md](docs/fr/reverse-engineering.md) |
| Chauvet Intimidator Spot 260X | [chart](docs/fixtures/chauvet-intimidator-spot-260x.md) | [table](docs/fr/fixtures/chauvet-intimidator-spot-260x.md) |
| Mindi Mini Spider | [chart](docs/fixtures/mindi-mini-spider.md) | [table](docs/fr/fixtures/mindi-mini-spider.md) |

## Repository layout

```
docs/          specification (English) — docs/fr/ in French
spec/          machine-readable reference: scrambling tables, test vectors, fixture charts
python/        Python library (pyserial)
c/             dependency-free C99 library (+ Win32 / POSIX example)
csharp/        .NET Standard 2.0 library (+ xUnit tests)
android/       Android library (Java, RFCOMM socket)
tools/         reference implementation and generators (tables, test vectors)
```

Tables and vectors of every library are generated from one reference,
[`tools/reference/cipher_reference.py`](tools/reference/cipher_reference.py):

```bash
python tools/generate_spec.py     # spec/*.json
python tools/generate_tables.py   # Python, C, C#, Java tables + C vectors
```

## Related project

[**DmxCtrl**](https://github.com/Tom-Rfid/DmxCtrl) — a Windows light console
(WinForms, .NET 10) built on this protocol: party tab, sweeps, one tab per fixture,
microphone tempo, portable single-file exe.

## Disclaimer

Independent project, not affiliated with the box manufacturer or with Jieli. The
protocol was recovered for interoperability with hardware we own.

---

## 🇫🇷 Version française

**Pilotez les petits boîtiers Bluetooth « USB-RDM-DMX » depuis votre propre code —
Python, C, C# ou Android.**

Documentation et librairies pour les boîtiers à puce Jieli (service `JL_SPP`, appli
Android RY-AI) : protocole complet, quatre librairies qui produisent les mêmes trames
octet pour octet, et des **modules d'appareils** faciles à combiner, à adresser et à
écrire soi-même. **Tout le monde est le bienvenu pour ajouter le module de son
appareil.**

👉 **[Lire le README complet en français](README.fr.md)** ·
[documentation en français](docs/fr/protocol.md)
