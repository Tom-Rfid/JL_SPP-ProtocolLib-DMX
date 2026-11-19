# How the protocol was recovered

🇫🇷 [Version française](fr/reverse-engineering.md)

Reverse engineering carried out to drive, from a PC, a box that only an Android app
could control (interoperability).

## Steps

1. **Identifying the transport.** On Windows, pairing the box creates a COM port
   named `JL_SPP` (Jieli chip). The app code (`bt/BtClient.java`) opens
   `createRfcommSocketToServiceRecord(00001101-…)`: this is **classic SPP**.
2. **Decompiling the APK** of RY-AI 1.3.3 with jadx.
3. **Connection sequence** (`bt/BtReceiver.java`): as soon as the link is up, the app
   calls `ConsoleFragment.SendBTConnectData()` (handshake) then reads the answers in
   a loop (`readBTData()` → `util.transaleBTData()`).
4. **DMX frame** (`ConsoleFragment.SendConsloeData()`): 521-byte buffer framed by
   `KT … TK`, sent every 100 ms, with a call to
   `code.Encryption1(frame, 5, 512, MainActivity.CodeNum(), 517)`.
5. **Scrambling** (`Util/Code.java`): tables copied, then three values rebuilt (jadx
   artefact, see [cipher.md](cipher.md)) and checked automatically (permutations,
   round trip).
6. **Counter** (`MainActivity.CodeNum()`): 0..255, incremented on every frame.
7. **Validation on the hardware**: blink test (every patched channel alternates
   0 / 255 every second) passed on 2 moving heads and a Mini Spider.

## Useful classes of the app

| Class | Content |
|---|---|
| `bt.BtClient` | SPP connection |
| `bt.BtReceiver` | connection sequence, reading |
| `ConsoleFragment` | handshakes, console frame, download frame |
| `Util.Code` | scrambling |
| `Util.util` | decoding of received frames, RDM |
| `MainActivity.CodeNum()` | counter |
| `uiAdapter.MyDeviceAdapter` | RDM commands (identify, address, mode) |

## Still to verify

- Download frame to the box memory (stand-alone scenes).
- RDM commands (header and length) and RDM discovery answers.
- A send rate faster than 100 ms (smoother movements?).
