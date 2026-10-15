// Test de liaison : fait clignoter les canaux 1..N une fois par seconde pendant 20 s.
//   dotnet run --project examples/JlSpp.Dmx.Blink -- COM6 44

using JlSpp.Dmx;

string port = args.Length > 0 ? args[0] : "COM6";
int last = args.Length > 1 ? int.Parse(args[1]) : 44;

using var link = new DmxLink(port);
link.ConnectionLost += (_, ex) => Console.WriteLine($"Liaison perdue : {ex.Message}");
link.Open();
link.Start();
Console.WriteLine($"Clignotement des canaux 1 à {last} sur {port} pendant 20 s...");

for (int second = 0; second < 20; second++)
{
    byte value = second % 2 == 0 ? (byte)255 : (byte)0;
    for (int channel = 1; channel <= last; channel++)
    {
        link.SetChannel(channel, value);
    }
    Thread.Sleep(1000);
}

link.Blackout();
link.SendFrame();
Console.WriteLine($"Terminé ({link.FramesSent} trames envoyées).");
