# Contributing

🇫🇷 [Français plus bas](#-français)

Thanks for helping! The most useful contributions are **new fixture modules**:
every light documented here saves the next person an evening with a manual and a
DMX tester. Bug reports, tests on Linux / macOS / Android and RDM findings are
welcome too.

## Adding a fixture module

### 1. The chart (`docs/fixtures/<brand>-<model>.md`)

Copy [mindi-mini-spider.md](docs/fixtures/mindi-mini-spider.md) or
[chauvet-intimidator-spot-260x.md](docs/fixtures/chauvet-intimidator-spot-260x.md)
and fill in:

- the DMX modes and how to select them in the fixture menu;
- how addressing works (where the fixture starts reading, footprint);
- one row per channel, with its value ranges;
- a status per channel: ✅ tested on the fixture · 📄 from the manual · ❓ assumed;
- the source (manual name and revision).

A French copy in `docs/fr/fixtures/` is welcome but not required.

### 2. The data (`spec/fixtures/<brand>-<model>.json`)

Same content, machine-readable. Follow the existing files: `manufacturer`, `model`,
`mode`, then a `channels` list with `channel`, `function`, `description`, `default`
and `verified`.

### 3. The code

One language is enough; ports to the others can come later.

| Language | Where | Example to copy |
|---|---|---|
| Python | `python/src/jlspp_dmx/fixtures/<model>.py`, export it in `fixtures/__init__.py` | `mindi_spider.py` |
| C# | `csharp/src/JlSpp.Dmx/Fixtures/<Model>.cs` | `MindiSpider.cs` |
| C | `c/include/jlspp_<model>.h`, `c/src/jlspp_<model>.c`, add it to `CMakeLists.txt` | `jlspp_mindi_spider.*` |
| Java | `android/jlspp-dmx/src/main/java/io/github/tomrfid/jlsppdmx/<Model>.java` | `MindiSpider.java` |

A module follows the same shape everywhere:

```python
from enum import IntEnum
from ._common import check_address, clamp_byte

class MyParChannel(IntEnum):
    DIMMER = 1
    RED = 2
    GREEN = 3
    BLUE = 4
    STROBE = 5

CHANNEL_COUNT = 5

class MyPar:
    """DMX messages of the <brand> <model> (5-channel mode). See docs/fixtures/<file>.md."""

    def __init__(self, address: int):
        self.address = address                     # address shown on the fixture
        check_address(address, CHANNEL_COUNT)      # refuses an address that overflows

    def dmx_channel(self, channel: MyParChannel) -> int:
        return self.address + int(channel) - 1

    def set(self, universe, channel: MyParChannel, value: int) -> None:
        universe[self.dmx_channel(channel) - 1] = clamp_byte(value)

    def set_rgb(self, universe, red: int, green: int, blue: int) -> None:
        self.set(universe, MyParChannel.RED, red)
        self.set(universe, MyParChannel.GREEN, green)
        self.set(universe, MyParChannel.BLUE, blue)
```

Rules that keep the libraries consistent:

- **The module writes into a universe it is given** (512 values, index 0 = channel 1);
  it never sends anything itself and keeps no global state.
- **The constructor takes the address shown on the fixture** and checks the footprint.
- **One readable function per action**; raw `set(channel, value)` stays available.
- **Integer maths only**, through the shared helpers (`clamp_byte`,
  `scale_into_range`, `middle`, `split_16bit`, `check_address`), so that every
  language gives the same bytes.
- To select a slot in a range (a colour, a gobo), send the **middle** of the range.
- Speeds go from **0 = slow to 255 = fast** in the API, even when the fixture range
  is reversed; document any exception.
- Never write reset or auto-program channels on your own: leave them at their default.
- Code comments in English.

### 4. The test

Add a test that builds a known universe with your module and checks the expected
channel values (`python/tests/`, `csharp/tests/`, `c/tests/`). If you can, check the
same universe on the real fixture and say so in the pull request.

## Running the tests

```bash
python -m unittest discover -s python/tests
cd csharp && dotnet test
cmake -S c -B c/build && cmake --build c/build && ctest --test-dir c/build
```

## Pull requests

- One fixture (or one topic) per pull request.
- Say which fixture you tested with, its firmware or revision if known, and which
  channels are still ❓.
- English or French, both are fine.
- By opening a pull request you agree that your contribution is published under the
  project's [MIT licence](LICENSE).

---

## 🇫🇷 Français

Merci de votre aide ! Les contributions les plus utiles sont les **nouveaux modules
d'appareils** : chaque projecteur documenté ici épargne au suivant une soirée avec
une notice et un testeur DMX. Les rapports de bug, les essais sous Linux / macOS /
Android et les découvertes sur le RDM sont aussi les bienvenus.

### Ajouter un module d'appareil

1. **La table** (`docs/fixtures/<marque>-<modele>.md`, en anglais) — copier une table
   existante et indiquer : les modes DMX et leur choix dans le menu, l'adressage
   (canal de départ, nombre de canaux), une ligne par canal avec ses plages, l'état
   de chaque canal (✅ testé · 📄 notice · ❓ supposé) et la source (notice, révision).
   Une version française dans `docs/fr/fixtures/` est un plus, pas une obligation.
2. **Les données** (`spec/fixtures/<marque>-<modele>.json`) — le même contenu, lisible
   par programme, sur le modèle des fichiers existants.
3. **Le code** — un seul langage suffit (voir le tableau et l'exemple Python
   ci-dessus). Règles communes :
   - le module écrit dans un univers qu'on lui passe (512 valeurs, index 0 = canal 1),
     n'envoie rien lui-même et n'a pas d'état global ;
   - le constructeur prend l'adresse affichée sur l'appareil et vérifie qu'il tient ;
   - une fonction lisible par action, `set(canal, valeur)` reste disponible ;
   - calculs entiers uniquement, avec les aides communes (`clamp_byte`,
     `scale_into_range`, `middle`, `split_16bit`, `check_address`) ;
   - pour choisir une case dans une plage (couleur, gobo), envoyer le **milieu** ;
   - les vitesses vont de **0 = lent à 255 = rapide** dans l'API ;
   - ne jamais écrire de soi-même sur les canaux de reset ou de programmes auto ;
   - commentaires du code en anglais.
4. **Le test** — construire un univers connu avec le module et vérifier les valeurs
   attendues ; si possible, le vérifier sur l'appareil et le dire dans la pull request.

### Pull requests

Un appareil (ou un sujet) par pull request ; préciser l'appareil utilisé pour les
essais et les canaux encore ❓. Français ou anglais, les deux conviennent. En
proposant une pull request, vous acceptez que votre contribution soit publiée sous la
[licence MIT](LICENSE) du projet.
