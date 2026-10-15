# Messagerie DMX — Chauvet DJ Intimidator Spot 260X

Lyre spot LED 75 W : pan 540°, tilt 234°, roue de 9 couleurs, roue de 7 gobos
rotatifs, prisme 3 facettes, focus motorisé.

Source : **Intimidator Spot 260X Quick Reference Guide Rev. 1** (Chauvet).
Fichier lisible par programme : [`spec/fixtures/chauvet-intimidator-spot-260x.json`](../../spec/fixtures/chauvet-intimidator-spot-260x.json).

## Modes et adressage

Le mode se choisit dans le menu de l'appareil : **Run Mode → DMX → 14CH / 8CH**.
L'adresse se règle dans **Address** (001–512). Pas de décalage d'adresse
(contrairement au Mini Spider) : réglée sur N, la lyre lit ses canaux à partir de N.

| Mode | Canaux | Adresse de départ max |
|---|---|---|
| 14 canaux | tout, pan/tilt 16 bits, dimmer, reset, macros | 499 |
| 8 canaux | pan, tilt, couleur, gobo, rotation, prisme, focus, obturateur | 505 |

Exemple de patch avec le Mini Spider en adresse 1 (canaux 1–16) : lyre 1 en **17**
(17–30), lyre 2 en **31** (31–44).

## Canaux

| Fonction | 14 can. | 8 can. | Valeurs |
|---|---|---|---|
| Pan | 1 | 1 | 0–255 = 0–540° |
| Pan fin | 2 | — | octet de poids faible du pan |
| Tilt | 3 | 2 | 0–255 = 0–234° |
| Tilt fin | 4 | — | octet de poids faible du tilt |
| Vitesse pan/tilt | 5 | — | **0 = le plus rapide**, 255 = le plus lent |
| Roue de couleurs | 6 | 3 | voir ci-dessous |
| Roue de gobos | 7 | 4 | voir ci-dessous |
| Rotation du gobo | 8 | 5 | voir ci-dessous |
| Prisme | 9 | 6 | 0–15 sans prisme, 16–255 prisme 3 facettes |
| Focus | 10 | 7 | 0–255 |
| Dimmer | 11 | — | 0–255 = 0–100 % |
| Obturateur / strobe | 12 | 8 | voir ci-dessous |
| Fonctions (blackout, resets) | 13 | — | voir ci-dessous |
| Macros de mouvement | 14 | — | voir ci-dessous |

⚠ En mode 8 canaux il n'y a **pas de dimmer** : la lumière s'allume avec
l'obturateur ouvert (canal 8 à 255).

### Roue de couleurs

| Valeurs | Couleur | Valeur envoyée par les libs |
|---|---|---|
| 0–6 | Blanc | 3 |
| 7–13 | Rouge | 10 |
| 14–20 | Orange | 17 |
| 21–27 | Jaune | 24 |
| 28–34 | Vert | 31 |
| 35–41 | Bleu | 38 |
| 42–48 | CTO (blanc chaud) | 45 |
| 49–55 | Cyan | 52 |
| 56–62 | Magenta | 59 |
| 63–64 | Blanc | |
| 65–189 | Position continue de la roue (entre deux couleurs) | |
| 190–221 | Arc-en-ciel, **rapide → lent** | |
| 222–223 | Arrêt | |
| 224–255 | Arc-en-ciel inversé, lent → rapide | |

Les libs envoient le **milieu** de chaque plage : c'est la valeur la plus sûre
pour tomber franchement sur la couleur.

### Roue de gobos

| Valeurs | Effet |
|---|---|
| 0–7 | Ouvert (pas de gobo) |
| 8–15, 16–23, … 56–63 | Gobo 1 à 7 (par pas de 8) |
| 64–71 | Gobo 7 qui tremble, lent → rapide |
| 72–79 … 112–119 | Gobo 6 … gobo 1 qui tremble (ordre inversé) |
| 120–127 | Ouvert |
| 128–189 | Rotation de la roue, lent → rapide |
| 190–193 | Arrêt |
| 194–255 | Rotation inverse de la roue, lent → rapide |

### Rotation du gobo

| Valeurs | Effet |
|---|---|
| 0–7 | Pas de rotation |
| 8–119 | Sens horaire, lent → rapide |
| 120–231 | Sens anti-horaire, lent → rapide |
| 232–255 | Va-et-vient, lent → rapide |

### Obturateur / strobe

| Valeurs | Effet |
|---|---|
| 0–3 | **Fermé** (pas de lumière) |
| 4–7 | Ouvert |
| 8–76 | Strobe, lent → rapide |
| 77–145 | Strobe pulsé, lent → rapide |
| 146–215 | Strobe aléatoire, lent → rapide |
| 216–255 | Ouvert |

### Fonctions (canal 13, mode 14 canaux)

| Valeurs | Effet |
|---|---|
| 0–7 | Rien |
| 8–15 | Blackout pendant les mouvements pan/tilt |
| 16–23 | Blackout pendant la rotation de la roue de couleurs |
| 24–31 | Blackout pendant la rotation de la roue de gobos |
| 32–39 | Blackout pan/tilt + couleurs |
| 40–47 | Blackout pan/tilt + gobos |
| 48–55 | Blackout pan/tilt + couleurs + gobos |
| 96–103 | Reset pan |
| 104–111 | Reset tilt |
| 112–119 | Reset roue de couleurs |
| 120–127 | Reset roue de gobos |
| 136–143 | Reset prisme |
| 144–151 | Reset focus |
| 152–159 | Reset complet |
| autres | Rien |

Après un reset, remettre le canal à 0 au bout de quelques secondes.

### Macros de mouvement (canal 14, mode 14 canaux)

| Valeurs | Effet |
|---|---|
| 0–7 | Pas de macro |
| 8–23, 24–39, … 120–135 | Macro 1 à 8 (par pas de 16) |
| 136–151, … 232–247 | Macro au son 1 à 7 |
| 248–255 | Macro au son 8 |

## Recettes

| Effet | Réglage (mode 14 canaux) |
|---|---|
| Allumer | dimmer 255 + obturateur 255 |
| Éteindre sans perdre la position | obturateur 0 (ou dimmer 0) |
| Tête au centre | pan 128/0, tilt 128/0 |
| Mouvement fluide | pan/tilt en 16 bits (canaux fins) + vitesse 0 |
| Couleur fixe | roue = valeur du milieu de la couleur |

## Avec les librairies

Dans les libs, **toutes les vitesses vont de 0 = lent à 255 = rapide**, même quand la
plage DMX est à l'envers (arc-en-ciel). Seule exception : la vitesse pan/tilt reste à
la convention de l'appareil (0 = rapide).

```python
from jlspp_dmx.fixtures import ChauvetSpot260X, Spot260XColor, Spot260XGobo
spot = ChauvetSpot260X(address=17)            # mode 14 canaux par défaut
universe = bytearray(512)
spot.light_on(universe)
spot.set_pan_degrees(universe, 270)
spot.set_color(universe, Spot260XColor.RED)
spot.set_gobo(universe, Spot260XGobo.GOBO_3)
spot.set_strobe(universe, speed=200)
```

```csharp
var spot = new ChauvetSpot260X(address: 17);
var universe = new byte[512];
spot.LightOn(universe);
spot.SetPanDegrees(universe, 270);
spot.SetColor(universe, Spot260XColor.Red);
```

```c
jlspp_spot260x spot;
jlspp_spot260x_init(&spot, 17, JLSPP_SPOT260X_MODE_14CH);
jlspp_spot260x_light_on(&spot, universe, 255);
jlspp_spot260x_set_color(&spot, universe, JLSPP_SPOT260X_RED);
```

```java
ChauvetSpot260X spot = new ChauvetSpot260X(17);
spot.lightOn(universe, 255);
spot.setColor(universe, ChauvetSpot260X.Color.RED);
```

Le vecteur de test `chauvet_spot260x_two_heads_code9` (deux lyres en 17 et 31) est
reproduit par les aides de chaque langage.
