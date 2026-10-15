# JlSpp.Dmx (C# / .NET)

Librairie .NET Standard 2.0 (utilisable depuis .NET Framework 4.6.1+, .NET 6/8/10,
Mono) pour les boîtiers Bluetooth DMX « JL_SPP ». Seule dépendance :
`System.IO.Ports`. Spécification : [../docs/protocol.md](../docs/protocol.md).

## Utilisation

```csharp
using JlSpp.Dmx;

using var link = new DmxLink("COM6");   // port COM "sortant" JL_SPP
link.ConnectionLost += (_, ex) => Console.WriteLine(ex.Message);
link.Open();                            // ouverture + handshake de connexion
link.Start();                           // envoi continu toutes les 100 ms
link.SetChannel(1, 255);                // canaux 1..512, modifiables depuis tout thread
// Dispose : arrêt, handshake de déconnexion, fermeture
```

`Open()` peut prendre quelques secondes (liaison radio) : dans une interface
graphique, l'appeler hors du thread de l'interface (`Task.Run`).

Construire les trames soi-même :

```csharp
var universe = new byte[512];           // index 0 = canal 1
byte[] frame = DmxFrame.Build(universe, codeNum: 0);
byte[] back = DmxFrame.DecodeUniverse(frame, out byte code);
```

Mindi Mini Spider :

```csharp
using JlSpp.Dmx.Fixtures;

var spider = new MindiSpider(address: 1);   // adresse affichée, décalage géré
spider.SetDimmer(universe, 255);
spider.SetWings(universe, 200, mirror: true);
```

## Compilation et tests

```bash
cd csharp
dotnet build
dotnet test
dotnet run --project examples/JlSpp.Dmx.Blink -- COM6
```
