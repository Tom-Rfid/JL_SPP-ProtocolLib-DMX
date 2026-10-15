# Protocole DMX JL_SPP — spécification

Boîtiers Bluetooth « USB-RDM-DMX » vendus avec l'appli Android **RY-AI** (paquet
`com.example.rybt32`, version 1.3.3 étudiée). Puce Bluetooth Jieli, service série
annoncé sous le nom **`JL_SPP`**.

Légende : ✅ vérifié sur le matériel · 🔍 lu dans le code décompilé de l'appli, non vérifié.

## 1. Transport ✅

| Élément | Valeur |
|---|---|
| Radio | Bluetooth **classique** (pas BLE) |
| Profil | SPP (RFCOMM), UUID `00001101-0000-1000-8000-00805F9B34FB` |
| Nom Bluetooth | `RY-…` (ex. `RY-A1096A-6319`) |
| Débit série | sans objet (port virtuel) ; 9600 convient |
| Rôle du pilote | **client** : il ouvre la liaison vers le boîtier |

Sous Windows, l'appairage crée deux ports COM : utiliser le port **sortant**
(voir [platforms.md](platforms.md)).

## 2. Séquence de dialogue ✅

```
ouverture du port / socket RFCOMM
  → handshake de connexion          BB 99 77 01 77 99
  → trame DMX (521 octets)          toutes les 100 ms, en continu
  → trame DMX …
  → handshake de déconnexion        BB 77 99 10 99 77 00 55
fermeture
```

Les handshakes sont envoyés **en clair**. Les trames DMX doivent être répétées en
continu (l'appli envoie toutes les 100 ms, même si rien ne change) : c'est le
rafraîchissement DMX habituel.

## 3. Trame DMX « console » (521 octets) ✅

| Octet(s) | Contenu | En clair ? |
|---|---|---|
| 0 | `0x00` | oui |
| 1–2 | `'K' 'T'` (`4B 54`) | oui |
| 3 | scène : `0` = pilotage direct | oui |
| 4 | vitesse : `0` en pilotage direct | oui |
| 5–516 | **512 canaux DMX** : canal 1 → octet 5, canal *n* → octet 4 + *n* | **brouillés** |
| 517 | clé 1 = `SIN[codeNum]` | oui |
| 518 | clé 2 = `codeNum` | oui |
| 519–520 | `'T' 'K'` (`54 4B`) | oui |

- `codeNum` : compteur 0..255 incrémenté à chaque trame par l'appli. Il est écrit
  dans la trame (octet 518) : le boîtier n'a pas besoin d'être synchronisé, toute
  valeur fonctionne.
- Brouillage des octets 5..516 : voir [cipher.md](cipher.md).

### Lecture de scènes mémorisées 🔍

Pendant la lecture d'une séquence (scènes 1..8), l'appli met l'octet 3 = numéro de
scène et l'octet 4 = vitesse, calculée par :

```
Sin_Speed(i) = 0                                                        si i = 0
             = 103 - (int(((sin(i * 0.35294117647058826 * π / 180) + 1) * 0.5) * 200) - 99)  sinon
```

### Blackout de l'appli 🔍

L'appli envoie une trame dont tous les canaux valent 0 (même structure).

## 4. Trame « download » vers la mémoire du boîtier (522 octets) 🔍

Fonction `SendDownData()` : enregistre une séquence de pas dans une scène du boîtier
(fonctionnement autonome sans téléphone). Une trame par pas, toutes les 300 ms.

| Octet(s) | Contenu |
|---|---|
| 0 | `0xBB` |
| 1–2 | `'D' 'U'` (`44 55`) |
| 3 | numéro de scène (1..8) |
| 4 | nombre de pas de la séquence |
| 5 | numéro du pas (1..n) |
| 6–517 | canaux 1..512 **brouillés** (seuls 1..96 sont remplis par l'appli) |
| 518–519 | clé (`SIN[codeNum]`, `codeNum`) |
| 520–521 | `'U' 'D'` |

## 5. Commandes RDM 🔍 (partiel)

L'onglet RDM de l'appli construit un tableau `RDMHeadData` dont on connaît :

| Octet | Rôle |
|---|---|
| 4 | commande : `0` identify off, `1` identify on, `2` changer l'adresse DMX, `3` changer le mode (personality) |
| 5–10 | UID RDM de l'appareil (6 octets) |
| 11–12 | paramètres : adresse (poids fort, poids faible) pour `2` ; numéro de mode (1..n) puis `0` pour `3` |

Les octets 0–3 et la longueur totale ne sont pas connus (classe `RDMFragment` non
étudiée).

## 6. Trames reçues du boîtier 🔍

Décodées par `util.transaleBTData()` :

| Début | Taille | Contenu |
|---|---|---|
| `44 55` (« DU ») | blocs de 103 octets | contenu d'une scène mémorisée : octet 2 = n° de scène ; octets 4..102 = 99 octets dont 96 canaux brouillés (déchiffrement avec la clé en fin de bloc : `Decode(bloc, 1, 96, 97)` sur les 99 octets) |
| `00 CC` | enregistrements de 46 octets | réponse à une recherche RDM : UID = octets 10..15, nombre de canaux = 35..36, mode courant = 37, nombre de modes = 38, adresse DMX = 39..40 (gros-boutiste), somme de contrôle = somme des octets 0..43 (poids fort en 44, poids faible en 45) |
| `0F 0F 0F nn … F0 F0 F0` | 12 octets | fin de recherche RDM : `nn` = nombre d'appareils trouvés |

## 7. Variante BLE de l'appli

L'appli contient aussi un code BLE (classe `BLE`) pour d'autres modèles. Il n'est
**pas** utilisé par le boîtier étudié, qui fonctionne en SPP.

## 8. Implémentations

| Langage | Dossier | Testée contre `spec/test_vectors.json` |
|---|---|---|
| Python | [`python/`](../python) | ✅ |
| C99 | [`c/`](../c) | ✅ (MSVC) |
| C# (.NET Standard 2.0) | [`csharp/`](../csharp) | ✅ |
| Java / Android | [`android/`](../android) | ⚠ écrite mais pas compilée |
