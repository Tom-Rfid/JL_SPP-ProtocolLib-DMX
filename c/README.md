# jlspp_dmx (C99)

Construction et décodage des trames DMX des boîtiers « JL_SPP », plus les aides des
appareils documentés. Pas de dépendance, pas d'allocation, pas d'entrée/sortie :
utilisable sur PC comme sur microcontrôleur. Spécification : [../docs/protocol.md](../docs/protocol.md).

| Fichier | Rôle |
|---|---|
| `include/jlspp_dmx.h` | API : `jlspp_build_frame`, `jlspp_decode_frame`, handshakes… |
| `include/jlspp_mindi_spider.h` | Mindi Mini Spider (`jlspp_spider_*`) |
| `include/jlspp_chauvet_spot260x.h` | Chauvet Intimidator Spot 260X (`jlspp_spot260x_*`) |
| `src/` | implémentation, tables générées |
| `examples/blink.c` | exemple complet : port série Win32 ou POSIX + envoi à 10 Hz |

## Utilisation

```c
#include "jlspp_dmx.h"
#include "jlspp_chauvet_spot260x.h"

uint8_t universe[JLSPP_UNIVERSE_SIZE] = {0};   /* index 0 = canal 1 */
uint8_t frame[JLSPP_FRAME_LEN];
uint8_t code = 0;
jlspp_spot260x spot;

jlspp_spot260x_init(&spot, 17, JLSPP_SPOT260X_MODE_14CH);
jlspp_spot260x_light_on(&spot, universe, 255);
jlspp_spot260x_set_color(&spot, universe, JLSPP_SPOT260X_RED);

write_port(JLSPP_HANDSHAKE_CONNECT, sizeof JLSPP_HANDSHAKE_CONNECT);
for (;;) {                                      /* toutes les JLSPP_SEND_INTERVAL_MS */
    jlspp_build_frame(universe, code++, 0, 0, frame);
    write_port(frame, JLSPP_FRAME_LEN);
}
```

Les fonctions qui peuvent échouer (fonction absente du mode 8 canaux, numéro hors
plage…) renvoient `JLSPP_OK` ou `JLSPP_ERROR`.

## Compilation

CMake :

```bash
cmake -S c -B c/build
cmake --build c/build
ctest --test-dir c/build
```

MSVC sans CMake (depuis une invite « x64 Native Tools ») :

```bat
c\build_msvc.bat
```

L'exemple : `blink COM6` (Windows) ou `blink /dev/rfcomm0` (Linux/macOS).
