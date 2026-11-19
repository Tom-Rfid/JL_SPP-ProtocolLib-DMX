# Messagerie DMX — Mindi Mini Spider 8x3W RGBW

🇬🇧 [English version](../../fixtures/mindi-mini-spider.md)

Projecteur « spider » à 2 ailes motorisées portant chacune 4 LED de 3 W
(rouge, vert, bleu, blanc). Mode DMX **15 canaux** (un mode 7 canaux existe aussi,
non documenté ici).
Fichier lisible par programme : [`spec/fixtures/mindi-mini-spider.json`](../../../spec/fixtures/mindi-mini-spider.json).

Légende : ✅ constaté sur l'appareil · 📄 d'après la notice.

## Adressage ✅

Réglé sur l'adresse **N**, le Spider lit ses 15 canaux de **N à N + 14**, comme
n'importe quel appareil DMX. Exemple : adresse 29 → canaux 29 à 43, l'appareil
suivant peut se placer au canal 44.

> **Historique.** Lors des premiers essais, le Spider semblait ignorer le canal N
> et lire ses canaux à partir de N + 1. Ce décalage a disparu une fois plusieurs
> appareils chaînés sur la ligne DMX (validé en octobre 2026) : il venait très
> probablement d'un test avec un seul appareil branché. Les librairies gardent une
> option pour ce cas (`address_quirk` en Python, `addressQuirk` en C# et Java,
> `quirk_offset` en C), **activée par défaut pour rester compatibles** avec les
> versions précédentes : passez `False` / `false` / `0` pour un adressage normal.

## Canaux

| Canal Spider | Canal DMX (adresse 1) | Fonction | Valeurs | |
|---|---|---|---|---|
| 1 | 1 | Moteur 1 — position de l'aile **gauche** | 0..255 = 0..135° | ✅ |
| 2 | 2 | Moteur 2 — position de l'aile **droite** | 0..255 = 0..135° | ✅ |
| 3 | 3 | Dimmer général | 0 = éteint … 255 = plein feu | ✅ |
| 4 | 4 | Strobe | 0 = pas de strobe, puis vitesse du flash | ✅ |
| 5 | 5 | LED 1 — rouge, aile gauche | 0..255 | ✅ |
| 6 | 6 | LED 2 — vert, aile gauche | 0..255 | ✅ |
| 7 | 7 | LED 3 — bleu, aile gauche | 0..255 | ✅ |
| 8 | 8 | LED 4 — blanc, aile gauche | 0..255 | ✅ |
| 9 | 9 | LED 5 — rouge, aile droite | 0..255 | ✅ |
| 10 | 10 | LED 6 — vert, aile droite | 0..255 | ✅ |
| 11 | 11 | LED 7 — bleu, aile droite | 0..255 | ✅ |
| 12 | 12 | LED 8 — blanc, aile droite | 0..255 | ✅ |
| 13 | 13 | Macros : programmes d'effets intégrés | plages selon la notice | 📄 |
| 14 | 14 | Vitesse des effets | lent → rapide | 📄 |
| 15 | 15 | Reset | **laisser à 0** | 📄 |

## Recettes

Le dimmer général (canal Spider 3) doit être ouvert, sinon les LED restent
éteintes quelles que soient leurs valeurs.

| Effet | Réglage |
|---|---|
| Ailes ensemble | moteur 1 = moteur 2 = *p* |
| Ailes en miroir (côtés opposés, se rejoignent au milieu) | moteur 1 = *p*, moteur 2 = 255 − *p* |
| Ailes au milieu | moteur 1 = moteur 2 ≈ 128 |
| Aile gauche seule allumée | dimmer 255, LED 1-4 > 0, LED 5-8 = 0 |
| Pas de strobe | strobe = 0 |

Le vecteur de test `mindi_spider_address1_code7` a été écrit avec l'ancien
décalage (Spider en adresse 1, canaux 2 à 16) : il reste valable pour vérifier
l'option `address_quirk`.

## Avec les librairies

```python
from jlspp_dmx.fixtures import MindiSpider, LEFT_WING_LEDS
spider = MindiSpider(address=29, address_quirk=False)
universe = bytearray(512)
spider.set_dimmer(universe, 255)
spider.set_wings(universe, 200, mirror=True)
spider.set_leds(universe, LEFT_WING_LEDS, 255)
```

```csharp
var spider = new MindiSpider(address: 29, addressQuirk: false);
var universe = new byte[512];
spider.SetDimmer(universe, 255);
spider.SetWings(universe, 200, mirror: true);
```

```c
uint8_t universe[512] = {0};
jlspp_spider spider;
jlspp_spider_init(&spider, 29);
spider.quirk_offset = 0;            /* adressage normal */
jlspp_spider_set_dimmer(&spider, universe, 255);
jlspp_spider_set_wings(&spider, universe, 200, 1);
```

```java
MindiSpider spider = new MindiSpider(29, false);
spider.setDimmer(universe, 255);
spider.setWings(universe, 200, true);
```
