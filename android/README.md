# jlspp-dmx (Android)

> ⚠ **Pas encore compilée ni testée.** Le code reprend la méthode de l'appli
> d'origine (socket RFCOMM, UUID SPP) et la même construction de trame que les
> autres librairies, mais il n'a été ni compilé ni essayé sur un téléphone.
> Retours bienvenus.

Module de librairie Android (Java 8, minSdk 21), package `io.github.tomrfid.jlsppdmx`.

| Classe | Rôle |
|---|---|
| `DmxFrame` | construction et décodage des trames, handshakes |
| `Cipher`, `CipherTables` | brouillage (tables générées) |
| `SppDmxLink` | connexion RFCOMM au boîtier appairé + envoi à 10 Hz |
| `MindiSpider` | canaux du Mindi Mini Spider |

## Utilisation

```java
BluetoothDevice device = adapter.getRemoteDevice("XX:XX:XX:XX:XX:XX"); // boîtier appairé
SppDmxLink link = new SppDmxLink(device);
link.connect();                 // bloquant : hors du thread UI
link.start();
link.setChannel(1, 255);        // canaux 1..512
// ...
link.close();
```

Permissions : `BLUETOOTH_CONNECT` à demander à l'exécution à partir d'Android 12
(déclarée dans le manifeste du module).

## Compilation

Nécessite un JDK 17 et le SDK Android. Le wrapper Gradle n'est pas inclus :

```bash
cd android
gradle wrapper
./gradlew :jlspp-dmx:assembleRelease :jlspp-dmx:testDebugUnitTest
```

Le test unitaire `DmxFrameTest` vérifie les trames contre `spec/test_vectors.json`.
