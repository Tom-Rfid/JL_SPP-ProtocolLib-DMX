# JL_SPP DMX protocol — specification

🇫🇷 [Version française](fr/protocol.md)

Bluetooth "USB-RDM-DMX" boxes sold with the **RY-AI** Android app (package
`com.example.rybt32`, version 1.3.3 studied). Jieli Bluetooth chip, serial service
advertised as **`JL_SPP`**.

Legend: ✅ verified on the hardware · 🔍 read in the decompiled app, not verified.

## 1. Transport ✅

| Item | Value |
|---|---|
| Radio | **Classic** Bluetooth (not BLE) |
| Profile | SPP (RFCOMM), UUID `00001101-0000-1000-8000-00805F9B34FB` |
| Bluetooth name | `RY-…` (e.g. `RY-A1096A-6319`) |
| Baud rate | not relevant (virtual port); 9600 is fine |
| Role of the controller | **client**: it opens the link to the box |

On Windows, pairing creates two COM ports: use the **outgoing** one
(see [platforms.md](platforms.md)).

## 2. Dialogue sequence ✅

```
open the port / RFCOMM socket
  → connect handshake               BB 99 77 01 77 99
  → DMX frame (521 bytes)           every 100 ms, continuously
  → DMX frame …
  → disconnect handshake            BB 77 99 10 99 77 00 55
close
```

Handshakes are sent **in clear**. DMX frames must be repeated continuously (the app
sends one every 100 ms, even when nothing changes): it is the usual DMX refresh.

## 3. "Console" DMX frame (521 bytes) ✅

| Byte(s) | Content | In clear? |
|---|---|---|
| 0 | `0x00` | yes |
| 1–2 | `'K' 'T'` (`4B 54`) | yes |
| 3 | scene: `0` = direct control | yes |
| 4 | speed: `0` in direct control | yes |
| 5–516 | **512 DMX channels**: channel 1 → byte 5, channel *n* → byte 4 + *n* | **scrambled** |
| 517 | key 1 = `SIN[codeNum]` | yes |
| 518 | key 2 = `codeNum` | yes |
| 519–520 | `'T' 'K'` (`54 4B`) | yes |

- `codeNum`: 0..255 counter, incremented by the app on every frame. It is written in
  the frame (byte 518): the box does not need to be in sync, any value works.
- Scrambling of bytes 5..516: see [cipher.md](cipher.md).

### Playing stored scenes 🔍

While a sequence (scenes 1..8) is playing, the app sets byte 3 = scene number and
byte 4 = speed, computed by:

```
Sin_Speed(i) = 0                                                        if i = 0
             = 103 - (int(((sin(i * 0.35294117647058826 * π / 180) + 1) * 0.5) * 200) - 99)  otherwise
```

### App blackout 🔍

The app sends a frame with every channel at 0 (same structure).

## 4. "Download" frame to the box memory (522 bytes) 🔍

`SendDownData()` function: stores a sequence of steps in a scene of the box
(stand-alone mode, without the phone). One frame per step, every 300 ms.

| Byte(s) | Content |
|---|---|
| 0 | `0xBB` |
| 1–2 | `'D' 'U'` (`44 55`) |
| 3 | scene number (1..8) |
| 4 | number of steps in the sequence |
| 5 | step number (1..n) |
| 6–517 | channels 1..512 **scrambled** (the app only fills 1..96) |
| 518–519 | key (`SIN[codeNum]`, `codeNum`) |
| 520–521 | `'U' 'D'` |

## 5. RDM commands 🔍 (partial)

The RDM tab of the app builds an `RDMHeadData` array, of which we know:

| Byte | Role |
|---|---|
| 4 | command: `0` identify off, `1` identify on, `2` change the DMX address, `3` change the mode (personality) |
| 5–10 | RDM UID of the fixture (6 bytes) |
| 11–12 | parameters: address (high byte, low byte) for `2`; mode number (1..n) then `0` for `3` |

Bytes 0–3 and the total length are unknown (the `RDMFragment` class was not studied).

## 6. Frames received from the box 🔍

Decoded by `util.transaleBTData()`:

| Starts with | Size | Content |
|---|---|---|
| `44 55` ("DU") | 103-byte blocks | content of a stored scene: byte 2 = scene number; bytes 4..102 = 99 bytes including 96 scrambled channels (decoded with the key at the end of the block: `Decode(block, 1, 96, 97)` on the 99 bytes) |
| `00 CC` | 46-byte records | answer to an RDM discovery: UID = bytes 10..15, channel count = 35..36, current mode = 37, mode count = 38, DMX address = 39..40 (big-endian), checksum = sum of bytes 0..43 (high byte in 44, low byte in 45) |
| `0F 0F 0F nn … F0 F0 F0` | 12 bytes | end of RDM discovery: `nn` = number of fixtures found |

## 7. BLE variant of the app

The app also contains BLE code (`BLE` class) for other models. It is **not** used by
the box studied here, which works over SPP.

## 8. Implementations

| Language | Folder | Tested against `spec/test_vectors.json` |
|---|---|---|
| Python | [`python/`](../python) | ✅ |
| C99 | [`c/`](../c) | ✅ (MSVC) |
| C# (.NET Standard 2.0) | [`csharp/`](../csharp) | ✅ |
| Java / Android | [`android/`](../android) | ⚠ written but not compiled yet |
