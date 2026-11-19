# JL_SPP-ProtocolLib-DMX

**Pilotez les petits boîtiers Bluetooth « USB-RDM-DMX » depuis votre propre code — Python, C, C# ou Android.**

🇬🇧 [English version](README.md)

![Langages](https://img.shields.io/badge/librairies-Python%20%7C%20C99%20%7C%20C%23%20%7C%20Java-blue)
![Protocole](https://img.shields.io/badge/protocole-valid%C3%A9%20sur%20le%20mat%C3%A9riel-brightgreen)
![Contributions](https://img.shields.io/badge/modules%20d'appareils-contributions%20bienvenues-orange)

Ces petits boîtiers (puce Jieli, service série `JL_SPP`, vendus avec l'appli Android
**RY-AI**) reçoivent en Bluetooth un univers DMX de 512 canaux et le ressortent sur
leur prise XLR. Jusqu'ici, seule l'appli du téléphone savait leur parler. Ce dépôt
documente le protocole et fournit des librairies prêtes à l'emploi : un PC, un Mac,
Linux, un microcontrôleur ou votre propre appli Android peuvent piloter vos lumières.

```
 votre code ──► librairie jlspp-dmx ──► Bluetooth SPP ──► boîtier USB-RDM-DMX ──► XLR ──► appareils
               (trame + brouillage)     (port COM virtuel)
```

## Pourquoi l'utiliser

- **Quatre librairies, un seul comportement.** Python, C99, C# (.NET Standard 2.0)
  et Java / Android produisent exactement les mêmes trames, octet pour octet,
  vérifiées sur des [vecteurs de test](spec/test_vectors.json) communs.
- **Des appareils en modules.** Chaque projecteur est un petit *module* : une classe
  avec une fonction lisible par action (`set_color`, `set_gobo`, `set_wings`,
  `set_strobe`, `reset`…) plutôt que des numéros de canaux et des valeurs à retenir.
  On branche les modules dont on a besoin, et on écrit le sien en quelques dizaines
  de lignes.
- **Adressage facile.** On donne au module l'adresse DMX affichée sur l'appareil : il
  calcule ses canaux, vérifie qu'il tient dans l'univers et écrit dans un simple
  tableau de 512 octets. Plusieurs appareils partagent le même univers, sans état
  global.
- **Pas de grosse dépendance.** La librairie C n'alloue rien et ne fait aucune
  entrée/sortie (utilisable sur microcontrôleur) ; Python n'a besoin que de
  `pyserial` pour le port ; C# seulement de `System.IO.Ports`.
- **Documenté à l'octet près**, en distinguant ce qui a été vérifié sur le matériel
  de ce qui a seulement été lu dans l'appli décompilée.

## Démarrage rapide

**Python**

```bash
pip install ./python[serial]
```

```python
import time
from jlspp_dmx import DmxLink
from jlspp_dmx.fixtures import ChauvetSpot260X, Spot260XColor, MindiSpider

universe = bytearray(512)                         # index 0 = canal DMX 1

lyre = ChauvetSpot260X(address=1)                 # mode 14 canaux, canaux 1 à 14
spider = MindiSpider(address=29, address_quirk=False)

lyre.light_on(universe)
lyre.set_color(universe, Spot260XColor.BLUE)
spider.set_dimmer(universe, 255)
spider.set_wings(universe, 200, mirror=True)

with DmxLink("COM6") as link:                     # handshake + trame toutes les 100 ms
    link.set_universe(universe)
    time.sleep(5)
```

**C#**

```csharp
using JlSpp.Dmx;
using JlSpp.Dmx.Fixtures;

var universe = new byte[512];
var lyre = new ChauvetSpot260X(address: 1);
lyre.LightOn(universe);
lyre.SetColor(universe, Spot260XColor.Red);

using var link = new DmxLink("COM6");             // le port COM « JL_SPP » SORTANT
link.Open();                                      // ouverture + handshake de connexion
link.Start();                                     // envoi continu toutes les 100 ms
link.SetUniverse(universe);
```

**C** — la librairie construit les trames, l'écriture sur le port reste à votre
charge (exemple complet Win32 / POSIX : [c/examples/blink.c](c/examples/blink.c)) :

```c
uint8_t universe[JLSPP_UNIVERSE_SIZE] = {0}, frame[JLSPP_FRAME_LEN];
universe[0] = 255;                                /* canal 1 */
jlspp_build_frame(universe, code++, 0, 0, frame);
write_port(frame, JLSPP_FRAME_LEN);
```

**Android** — `SppDmxLink` ouvre une socket RFCOMM vers le boîtier appairé, voir
[android/](android).

Chaque dossier a son propre README avec la compilation et les tests :
[python](python) · [c](c) · [csharp](csharp) · [android](android).

## Modules d'appareils

| Module | Appareil | Modes | État |
|---|---|---|---|
| `ChauvetSpot260X` | Chauvet DJ Intimidator Spot 260X (lyre) | 14 et 8 canaux | 📄 table officielle Chauvet (guide rapide Rev. 1) |
| `MindiSpider` | Mindi Mini Spider 8x3W RGBW | 15 canaux | ✅ canaux, ailes et couleurs des LED confirmés |

Chaque module a sa table lisible dans [docs/fr/fixtures/](docs/fr/fixtures) et sa
version lisible par programme dans [spec/fixtures/](spec/fixtures).

L'appli [DmxCtrl](https://github.com/Tom-Rfid/DmxCtrl) pilote déjà d'autres appareils
(PAR LED UV, laser Showtec Galactic, machine à fumée Ayra) avec ses propres profils :
ce sont de bons candidats pour de nouveaux modules ici — voir plus bas.

### L'adressage en pratique

Un module n'a besoin que de son adresse de départ. Avec deux lyres et un Spider sur
la même ligne :

| Appareil | Adresse réglée sur l'appareil | Canaux utilisés |
|---|---|---|
| Intimidator Spot 260X n° 1 (14 can.) | 1 | 1–14 |
| Intimidator Spot 260X n° 2 (14 can.) | 15 | 15–28 |
| Mini Spider (15 can.) | 29 | 29–43 |

```python
lyres = [ChauvetSpot260X(address=a) for a in (1, 15)]
for l in lyres:
    l.set_pan_degrees(universe, 270)
```

Un module refuse une adresse qui déborderait de l'univers (`ValueError` en Python,
`ArgumentOutOfRangeException` en C#, `JLSPP_ERROR` en C).

> Lors des tout premiers essais, le Mini Spider semblait sauter son premier canal ;
> il s'adresse normalement une fois plusieurs appareils chaînés. Les librairies
> gardent ce décalage en option (`address_quirk`), activée par défaut pour rester
> compatibles : passez `False` pour un adressage normal. Détails dans
> [docs/fr/fixtures/mindi-mini-spider.md](docs/fr/fixtures/mindi-mini-spider.md).

## Ajoutez votre appareil — les contributions sont bienvenues !

**Tout le monde est le bienvenu pour ajouter un module d'appareil.** Vous avez un
projecteur qui n'est pas dans la liste ? Sa table DMX est en général dans la notice :
transformez-la en module et proposez une pull request. Une table seule, sans code,
est déjà une contribution utile.

1. **Table** — écrire `docs/fixtures/<marque>-<modele>.md` (en anglais, en copiant
   un existant ; la version française dans `docs/fr/fixtures/` est un plus) et
   marquer chaque canal ✅ testé sur l'appareil, 📄 d'après la notice ou ❓ supposé.
2. **Données** — ajouter `spec/fixtures/<marque>-<modele>.json` avec les mêmes canaux.
3. **Code** — ajouter un module dans un ou plusieurs langages, sur le modèle des
   existants :
   - Python : `python/src/jlspp_dmx/fixtures/<modele>.py`, exporté dans `fixtures/__init__.py`
   - C# : `csharp/src/JlSpp.Dmx/Fixtures/<Modele>.cs`
   - C : `c/include/jlspp_<modele>.h` + `c/src/jlspp_<modele>.c`
   - Java : `android/jlspp-dmx/src/main/java/io/github/tomrfid/jlsppdmx/<Modele>.java`

   Utiliser les aides communes (`clamp_byte`, `scale_into_range`, `middle`,
   `check_address`…) pour que tous les langages donnent les mêmes valeurs. Un seul
   langage suffit : quelqu'un d'autre pourra le porter.
4. **Test** — un test qui écrit un univers connu, idéalement vérifié sur l'appareil.

Guide complet : [CONTRIBUTING.md](CONTRIBUTING.md#-français). Les rapports de bug, les
essais sous Linux / macOS et les découvertes sur le RDM sont aussi les bienvenus.

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

## État

| Partie | État |
|---|---|
| Trame DMX, brouillage, handshakes | ✅ validé sur le matériel |
| Python, C, C# | ✅ testés sur les vecteurs de référence |
| Android | ⚠ écrite d'après l'appli d'origine, **pas encore compilée ni testée** |
| Scènes autonomes, RDM | 🔍 lu dans le code décompilé, à vérifier |

## Documentation

| | 🇫🇷 Français | 🇬🇧 English |
|---|---|---|
| Protocole (transport, handshakes, trames, scènes, RDM) | [protocol.md](docs/fr/protocol.md) | [protocol.md](docs/protocol.md) |
| Brouillage des canaux | [cipher.md](docs/fr/cipher.md) | [cipher.md](docs/cipher.md) |
| Se connecter sous Windows / Linux / macOS / Android | [platforms.md](docs/fr/platforms.md) | [platforms.md](docs/platforms.md) |
| Comment le protocole a été retrouvé | [reverse-engineering.md](docs/fr/reverse-engineering.md) | [reverse-engineering.md](docs/reverse-engineering.md) |
| Chauvet Intimidator Spot 260X | [table](docs/fr/fixtures/chauvet-intimidator-spot-260x.md) | [chart](docs/fixtures/chauvet-intimidator-spot-260x.md) |
| Mindi Mini Spider | [table](docs/fr/fixtures/mindi-mini-spider.md) | [chart](docs/fixtures/mindi-mini-spider.md) |

## Contenu du dépôt

```
docs/          spécification (anglais) — docs/fr/ en français
spec/          référence lisible par programme : tables de brouillage, vecteurs de test, tables d'appareils
python/        librairie Python (pyserial)
c/             librairie C99 sans dépendance (+ exemple Win32 / POSIX)
csharp/        librairie .NET Standard 2.0 (+ tests xUnit)
android/       librairie Android (Java, socket RFCOMM)
tools/         implémentation de référence et générateurs (tables, vecteurs de test)
```

Les tables et vecteurs de toutes les librairies sont générés depuis une seule
référence, [`tools/reference/cipher_reference.py`](tools/reference/cipher_reference.py) :

```bash
python tools/generate_spec.py     # spec/*.json
python tools/generate_tables.py   # tables Python, C, C#, Java + vecteurs C
```

## Projet lié

[**DmxCtrl**](https://github.com/Tom-Rfid/DmxCtrl) — console de lumière Windows
(WinForms, .NET 10) construite sur ce protocole : onglet Soirée, balayages, un onglet
par appareil, tempo au micro, exe portable en un seul fichier.

## Avertissement

Projet indépendant, sans lien avec le fabricant du boîtier ni avec Jieli. Le
protocole a été retrouvé pour l'interopérabilité avec du matériel dont on est
propriétaire.
