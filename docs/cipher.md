# Scrambling of the DMX channels

🇫🇷 [Version française](fr/cipher.md)

This is **not** cryptography: it is a table substitution (S-box), chosen from a
counter. It must still be reproduced exactly, otherwise the box ignores the frame.
Source: class `com.example.rybt32.Util.Code` of the RY-AI app.

## Tables

Reference file: [`spec/cipher_tables.json`](../spec/cipher_tables.json).

| Table | Size | Role |
|---|---|---|
| `password[5][256]` | 5 permutations of 0..255 | scrambling |
| `decode[5][256]` | inverse permutations of `password` | unscrambling |
| `sin[256]` | sine curve 0..255 | table choice + key byte |

## Scrambling (`Code.Encryption1`)

```
inputs: frame, start, length, codeNum (0..255), marker
table = password[ sin[codeNum] % 5 ]
for p from start to start + length - 1:
    frame[p] = table[ (frame[p] + codeNum) mod 256 ]
frame[marker]     = sin[codeNum]
frame[marker + 1] = codeNum
```

For a console frame: `start = 5`, `length = 512`, `marker = 517`.

## Unscrambling (`Code.Decode`)

```
table = decode[ frame[marker] % 5 ]
key   = frame[marker + 1]
for each scrambled byte b: clear = (table[b] - key) mod 256
```

## Constants mangled by the decompiler

In the code decompiled by jadx, three numbers of these tables show up as Android /
Kotlin constants that have nothing to do with the subject: jadx replaced literals by
a visible constant that has the same value.

| In the decompiled code | Real value |
|---|---|
| `WorkQueueKt.MASK` | 127 |
| `ItemTouchHelper.Callback.DEFAULT_DRAG_ANIMATION_DURATION` | 200 |
| `ItemTouchHelper.Callback.DEFAULT_SWIPE_ANIMATION_DURATION` | 250 |

Check: with these values, each of the 10 tables is a complete permutation of 0..255
(sum 32640, 256 distinct values), scrambling then unscrambling gives back the
original bytes for every `codeNum`, and the frames produced are accepted by the box.

## Regenerating the tables and vectors

```bash
python tools/generate_spec.py     # spec/*.json from tools/reference/cipher_reference.py
python tools/generate_tables.py   # Python, C, C#, Java tables + C vectors
```
