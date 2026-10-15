# Messagerie DMX — Mindi Mini Spider 8x3W RGBW

Projecteur « spider » à 2 ailes motorisées portant chacune 4 LED de 3 W.
Mode DMX **15 canaux** (un mode 7 canaux existe aussi, non documenté ici).
Fichier lisible par programme : [`spec/fixtures/mindi-mini-spider.json`](../../spec/fixtures/mindi-mini-spider.json).

Légende : ✅ constaté sur l'appareil · 📄 d'après la notice · ❓ supposé.

## ⚠ Décalage d'adresse ✅

Réglé sur l'adresse **N**, le Spider **ignore le canal N** et lit ses 15 canaux à
partir de **N + 1**. Il occupe donc 16 canaux : N (vide) puis N+1 à N+15.

Exemple avec l'adresse affichée **1** : canal 1 ignoré, moteur 1 sur le canal 2,
reset sur le canal 16. L'appareil suivant se place au canal **17**.

Les librairies appliquent ce décalage par défaut (`address_quirk=True` en Python,
`addressQuirk: true` en C# et Java, `JLSPP_SPIDER_QUIRK_OFFSET 1` en C) : on leur
donne l'adresse **affichée** sur l'appareil.

## Canaux

| Canal Spider | Canal DMX (adresse 1) | Fonction | Valeurs | |
|---|---|---|---|---|
| — | 1 | (ignoré, voir ci-dessus) | — | ✅ |
| 1 | 2 | Moteur 1 — position de l'aile 1 | 0..255 = 0..135° | 📄 |
| 2 | 3 | Moteur 2 — position de l'aile 2 | 0..255 = 0..135° | 📄 |
| 3 | 4 | Dimmer général | 0 = éteint … 255 = plein feu | 📄 |
| 4 | 5 | Strobe | 0 = pas de strobe, puis vitesse du flash | 📄 |
| 5 | 6 | LED 1 — intensité | 0..255 (rouge ❓) | 📄 |
| 6 | 7 | LED 2 — intensité | 0..255 (vert ❓) | 📄 |
| 7 | 8 | LED 3 — intensité | 0..255 (bleu ❓) | 📄 |
| 8 | 9 | LED 4 — intensité | 0..255 (blanc ❓) | 📄 |
| 9 | 10 | LED 5 — intensité | 0..255 (rouge ❓) | 📄 |
| 10 | 11 | LED 6 — intensité | 0..255 (vert ❓) | 📄 |
| 11 | 12 | LED 7 — intensité | 0..255 (bleu ❓) | 📄 |
| 12 | 13 | LED 8 — intensité | 0..255 (blanc ❓) | 📄 |
| 13 | 14 | Macros : programmes d'effets intégrés | plages selon la notice | 📄 |
| 14 | 15 | Vitesse des effets | lent → rapide | 📄 |
| 15 | 16 | Reset | **laisser à 0** | 📄 |

❓ La couleur de chaque LED et leur répartition sur les ailes (LED 1-4 sur
l'aile gauche, LED 5-8 sur l'aile droite) restent à confirmer sur l'appareil.

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

Exemple d'univers (adresse affichée 1, ailes en miroir, dimmer à fond, LED 1 et 5
à fond) — c'est le vecteur de test `mindi_spider_adresse1_code7` :

| Canal DMX | 2 | 3 | 4 | 6 | 10 | autres |
|---|---|---|---|---|---|---|
| Valeur | 200 | 55 | 255 | 255 | 255 | 0 |

## Avec les librairies

```python
from jlspp_dmx.fixtures import MindiSpider
spider = MindiSpider(address=1)
universe = bytearray(512)
spider.set_dimmer(universe, 255)
spider.set_wings(universe, 200, mirror=True)
spider.set_led(universe, 1, 255)
```

```csharp
var spider = new MindiSpider(address: 1);
var universe = new byte[512];
spider.SetDimmer(universe, 255);
spider.SetWings(universe, 200, mirror: true);
```

```c
uint8_t universe[512] = {0};
jlspp_spider_set_wings(universe, 1, 200, 1);
universe[jlspp_spider_index(1, JLSPP_SPIDER_DIMMER)] = 255;
```
