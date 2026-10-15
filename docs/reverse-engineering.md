# Comment le protocole a été retrouvé

Rétro-ingénierie menée pour pouvoir piloter, depuis un PC, un boîtier que seule
une appli Android savait commander (interopérabilité).

## Étapes

1. **Identification du transport.** Sous Windows, l'appairage du boîtier crée un
   port COM nommé `JL_SPP` (puce Jieli). Le code de l'appli (`bt/BtClient.java`)
   ouvre `createRfcommSocketToServiceRecord(00001101-…)` : c'est du **SPP classique**.
2. **Décompilation de l'APK** RY-AI 1.3.3 avec jadx.
3. **Séquence de connexion** (`bt/BtReceiver.java`) : dès la liaison établie, l'appli
   appelle `ConsoleFragment.SendBTConnectData()` (handshake) puis lit les réponses
   en boucle (`readBTData()` → `util.transaleBTData()`).
4. **Trame DMX** (`ConsoleFragment.SendConsloeData()`) : buffer de 521 octets
   encadré par `KT … TK`, envoyé toutes les 100 ms, avec un appel à
   `code.Encryption1(trame, 5, 512, MainActivity.CodeNum(), 517)`.
5. **Brouillage** (`Util/Code.java`) : tables recopiées, puis trois valeurs
   reconstituées (artefact jadx, voir [cipher.md](cipher.md)) et validées
   automatiquement (permutations, aller-retour).
6. **Compteur** (`MainActivity.CodeNum()`) : 0..255 incrémenté à chaque trame.
7. **Validation sur le matériel** : test de clignotement (tous les canaux patchés
   alternent 0 / 255 chaque seconde) réussi sur 2 lyres et un Mini Spider.

## Classes de l'appli utiles

| Classe | Contenu |
|---|---|
| `bt.BtClient` | connexion SPP |
| `bt.BtReceiver` | séquence de connexion, lecture |
| `ConsoleFragment` | handshakes, trame console, trame download |
| `Util.Code` | brouillage |
| `Util.util` | décodage des trames reçues, RDM |
| `MainActivity.CodeNum()` | compteur |
| `uiAdapter.MyDeviceAdapter` | commandes RDM (identify, adresse, mode) |

## Ce qui reste à vérifier

- Trame download vers la mémoire du boîtier (scènes autonomes).
- Commandes RDM (en-tête et longueur) et réponses de recherche RDM.
- Cadence d'envoi plus rapide que 100 ms (mouvements plus fluides ?).
