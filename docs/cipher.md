# Brouillage des canaux DMX

Ce n'est **pas** de la cryptographie : une substitution par table (S-box), choisie
selon un compteur. Il faut pourtant la reproduire exactement, sinon le boîtier
ignore la trame. Source : classe `com.example.rybt32.Util.Code` de l'appli RY-AI.

## Tables

Fichier de référence : [`spec/cipher_tables.json`](../spec/cipher_tables.json).

| Table | Taille | Rôle |
|---|---|---|
| `password[5][256]` | 5 permutations de 0..255 | brouillage |
| `decode[5][256]` | permutations inverses de `password` | débrouillage |
| `sin[256]` | courbe sinusoïdale 0..255 | choix de la table + octet de clé |

## Brouillage (`Code.Encryption1`)

```
entrées : trame, start, length, codeNum (0..255), marker
table = password[ sin[codeNum] % 5 ]
pour p de start à start + length - 1 :
    trame[p] = table[ (trame[p] + codeNum) mod 256 ]
trame[marker]     = sin[codeNum]
trame[marker + 1] = codeNum
```

Pour une trame console : `start = 5`, `length = 512`, `marker = 517`.

## Débrouillage (`Code.Decode`)

```
table = decode[ trame[marker] % 5 ]
clé   = trame[marker + 1]
pour chaque octet brouillé b : clair = (table[b] - clé) mod 256
```

## Constantes déformées par la décompilation

Dans le code décompilé par jadx, trois nombres de ces tables apparaissent sous la
forme de constantes Android/Kotlin qui n'ont rien à voir avec le sujet. jadx a
remplacé des littéraux par une constante visible ayant la même valeur :

| Dans le code décompilé | Valeur réelle |
|---|---|
| `WorkQueueKt.MASK` | 127 |
| `ItemTouchHelper.Callback.DEFAULT_DRAG_ANIMATION_DURATION` | 200 |
| `ItemTouchHelper.Callback.DEFAULT_SWIPE_ANIMATION_DURATION` | 250 |

Vérification : avec ces valeurs, chacune des 10 tables est une permutation complète
de 0..255 (somme 32640, 256 valeurs distinctes), le chiffrement suivi du
déchiffrement redonne les octets d'origine pour tout `codeNum`, et les trames
produites sont acceptées par le boîtier.

## Régénérer les tables et vecteurs

```bash
python tools/generate_spec.py     # spec/*.json depuis tools/reference/cipher_reference.py
python tools/generate_tables.py   # tables Python, C, C#, Java + vecteurs C
```
