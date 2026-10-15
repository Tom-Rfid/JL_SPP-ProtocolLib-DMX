# JL_SPP-ProtocolLib-DMX

Documentation et librairies pour piloter les petits boîtiers **Bluetooth « USB-RDM-DMX »**
(puce Jieli, service `JL_SPP`, appli Android **RY-AI**) depuis un PC, un Mac, Linux
ou une appli Android.

Le boîtier reçoit en Bluetooth SPP (port série virtuel) un univers DMX de 512 canaux
légèrement brouillé, et le ressort sur sa prise XLR. Le protocole a été retrouvé à
partir de l'appli d'origine puis validé sur le matériel (2 lyres Chauvet Intimidator
Spot 260X + 1 Mindi Mini Spider).

## Contenu

```
docs/                      la spécification
  protocol.md              transport, handshakes, trame DMX, scènes, RDM
  cipher.md                le brouillage des canaux
  platforms.md             se connecter sous Windows / Linux / macOS / Android
  reverse-engineering.md   comment le protocole a été retrouvé
  fixtures/
    mindi-mini-spider.md             messagerie DMX du Mindi Mini Spider (et son décalage d'adresse)
    chauvet-intimidator-spot-260x.md messagerie DMX de la Chauvet Intimidator Spot 260X (8 et 14 canaux)
spec/                      données de référence lisibles par programme
  cipher_tables.json       tables de brouillage
  test_vectors.json        trames de test (univers → trame attendue)
  fixtures/                tables DMX des appareils (JSON)
python/                    librairie Python (pyserial)
c/                         librairie C99 sans dépendance (+ exemple Win32/POSIX)
csharp/                    librairie .NET Standard 2.0 (+ tests xunit)
android/                   librairie Android (Java, socket RFCOMM)
tools/                     référence et générateurs (tables, vecteurs de test)
```

## État

| Partie | État |
|---|---|
| Trame DMX, brouillage, handshakes | ✅ validé sur le matériel |
| Python | ✅ tests sur les vecteurs de référence |
| C | ✅ tests sur les vecteurs de référence (MSVC) |
| C# | ✅ tests sur les vecteurs de référence |
| Android | ⚠ écrite d'après l'appli d'origine, **pas encore compilée ni testée** |
| Scènes autonomes, RDM | 🔍 lu dans le code décompilé, à vérifier |
| Mindi Mini Spider | ✅ canaux et décalage d'adresse ; ❓ couleur et position des LED |
| Chauvet Intimidator Spot 260X | 📄 table DMX officielle Chauvet (guide rapide Rev. 1), modes 8 et 14 canaux |

Les quatre librairies produisent octet pour octet les mêmes trames : elles sont
testées contre [`spec/test_vectors.json`](spec/test_vectors.json). Chacune fournit
aussi des aides par appareil (`MindiSpider`, `ChauvetSpot260X`) : une fonction
lisible par action (`set_color`, `set_gobo`, `set_strobe`, `reset`…) plutôt que des
numéros de canaux et des valeurs à retenir. Le code est commenté en anglais.

## Le protocole en bref

1. Ouvrir le port série du boîtier (Windows : le port COM **sortant** « JL_SPP »).
2. Envoyer `BB 99 77 01 77 99`.
3. Toutes les 100 ms, envoyer une trame de 521 octets :

   | Octets | Contenu |
   |---|---|
   | 0 | `00` |
   | 1-2 | `4B 54` (« KT ») |
   | 3-4 | scène, vitesse (`00 00` en pilotage direct) |
   | 5-516 | canaux 1 à 512 **brouillés** |
   | 517-518 | clé : `sin[code]`, `code` (compteur 0..255) |
   | 519-520 | `54 4B` (« TK ») |

4. En partant, envoyer `BB 77 99 10 99 77 00 55` puis fermer.

Détails : [docs/protocol.md](docs/protocol.md) et [docs/cipher.md](docs/cipher.md).

## Démarrage rapide

**Python**

```bash
pip install ./python[serial]
```

```python
import time
from jlspp_dmx import DmxLink

with DmxLink("COM6") as link:    # handshake + envoi continu
    link.set_channel(1, 255)
    time.sleep(5)
```

Avec les aides d'appareils :

```python
from jlspp_dmx.fixtures import ChauvetSpot260X, Spot260XColor

universe = bytearray(512)
spot = ChauvetSpot260X(address=17)
spot.light_on(universe)
spot.set_color(universe, Spot260XColor.BLUE)
link.set_universe(universe)
```

**C#**

```csharp
using JlSpp.Dmx;

using var link = new DmxLink("COM6");
link.Open();
link.Start();
link.SetChannel(1, 255);
```

**C** : la librairie construit les trames, l'écriture sur le port reste à votre
charge (voir [c/examples/blink.c](c/examples/blink.c)).

```c
uint8_t universe[JLSPP_UNIVERSE_SIZE] = {0}, frame[JLSPP_FRAME_LEN];
universe[0] = 255;                       /* canal 1 */
jlspp_build_frame(universe, code++, 0, 0, frame);
```

Chaque dossier a son propre README avec la compilation et les tests.

## Régénérer les tables

Les tables et vecteurs de toutes les librairies sont générés depuis une seule
référence, [`tools/reference/cipher_reference.py`](tools/reference/cipher_reference.py) :

```bash
python tools/generate_spec.py     # spec/*.json
python tools/generate_tables.py   # tables Python, C, C#, Java + vecteurs C
```

## Projet lié

[DmxCtrl](https://github.com/Tom-Rfid/DmxCtrl) : console de lumière Windows
(WinForms) construite sur ce protocole.

## Avertissement

Projet indépendant, sans lien avec le fabricant du boîtier ni avec Jieli. Le
protocole a été retrouvé pour l'interopérabilité avec du matériel dont on est
propriétaire.
