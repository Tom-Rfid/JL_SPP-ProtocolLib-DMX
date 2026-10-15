# Se connecter au boîtier selon la plateforme

Le boîtier est un périphérique Bluetooth **SPP** : une fois appairé, il se pilote
comme un port série. Seule l'étape d'appairage dépend du système.

## Windows ✅

1. Paramètres → Bluetooth → ajouter l'appareil `RY-…`.
2. Windows crée deux ports COM (Plus de paramètres Bluetooth → Ports COM) :
   - **entrant** (ex. COM5) : ne pas utiliser ;
   - **sortant** « `JL_SPP` » (ex. COM6) : **c'est celui-là**.
3. Ouvrir ce port avec n'importe quelle librairie série (pyserial, `SerialPort`
   .NET, `CreateFile` Win32…).

L'ouverture peut prendre quelques secondes (établissement de la liaison radio) :
dans une interface graphique, ouvrir le port hors du thread de l'interface.

## Linux 🔍 (non testé)

```bash
bluetoothctl            # pair <MAC>, trust <MAC>
sdptool browse <MAC>    # repérer le canal RFCOMM du service JL_SPP (souvent 1)
sudo rfcomm bind 0 <MAC> 1
# le port est /dev/rfcomm0
```

## macOS 🔍 (non testé)

Après appairage, un port `/dev/tty.<nom>-…` apparaît normalement pour les
appareils SPP. Selon la version de macOS, sa création peut ne pas être automatique.

## Android ✅ (méthode de l'appli d'origine)

Socket RFCOMM vers l'appareil appairé avec l'UUID SPP standard, voir
[`android/`](../android) (`SppDmxLink`). Permission `BLUETOOTH_CONNECT` à
l'exécution à partir d'Android 12.
