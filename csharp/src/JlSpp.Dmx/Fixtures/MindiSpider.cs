using System;

namespace JlSpp.Dmx.Fixtures
{
    /// <summary>Canaux du Mindi Mini Spider 8x3W RGBW en mode 15 canaux (d'apres la notice).</summary>
    public enum SpiderChannel
    {
        /// <summary>Position aile 1 : 0..255 = 0..135 degres.</summary>
        Motor1 = 1,
        /// <summary>Position aile 2 : 0..255 = 0..135 degres.</summary>
        Motor2 = 2,
        /// <summary>Dimmer general.</summary>
        Dimmer = 3,
        /// <summary>0 = pas de strobe, puis vitesse du flash.</summary>
        Strobe = 4,
        /// <summary>LED 1 (canaux 5..12 = LED 1..8, couleur supposee R, V, B, Blanc x2).</summary>
        Led1 = 5,
        /// <summary>Programmes d'effets integres.</summary>
        Macro = 13,
        /// <summary>Vitesse des effets (lent -> rapide).</summary>
        EffectSpeed = 14,
        /// <summary>Reset : laisser a 0.</summary>
        Reset = 15,
    }

    /// <summary>
    /// Messagerie DMX du Mini Spider (voir docs/fixtures/mindi-mini-spider.md).
    /// BIZARRERIE CONSTATEE : regle sur l'adresse N, le Spider ignore le canal N et ecoute a
    /// partir de N+1 ; avec <c>addressQuirk = true</c> (defaut), on donne l'adresse AFFICHEE.
    /// </summary>
    public sealed class MindiSpider
    {
        public const int ChannelCount = 15;
        public static readonly int[] LeftWingLeds = { 1, 2, 3, 4 };   // SUPPOSE, a verifier
        public static readonly int[] RightWingLeds = { 5, 6, 7, 8 };  // SUPPOSE, a verifier

        public MindiSpider(int address, bool addressQuirk = true)
        {
            if (address < 1 || address > 512)
            {
                throw new ArgumentOutOfRangeException(nameof(address), "Adresse DMX 1..512.");
            }
            Address = address;
            AddressQuirk = addressQuirk;
        }

        public int Address { get; }
        public bool AddressQuirk { get; }

        /// <summary>Numero de canal DMX absolu (1..512) d'une fonction du Spider.</summary>
        public int DmxChannel(SpiderChannel channel) => DmxChannel((int)channel);

        private int DmxChannel(int spiderChannel) => Address + spiderChannel - 1 + (AddressQuirk ? 1 : 0);

        private void Set(byte[] universe, int spiderChannel, int value) =>
            universe[DmxChannel(spiderChannel) - 1] = (byte)Math.Max(0, Math.Min(255, value));

        public void SetDimmer(byte[] universe, byte level) => Set(universe, (int)SpiderChannel.Dimmer, level);

        /// <summary>0 = pas de strobe.</summary>
        public void SetStrobe(byte[] universe, byte speed) => Set(universe, (int)SpiderChannel.Strobe, speed);

        /// <summary>led : 1..8.</summary>
        public void SetLed(byte[] universe, int led, byte level)
        {
            if (led < 1 || led > 8)
            {
                throw new ArgumentOutOfRangeException(nameof(led), "LED 1 a 8.");
            }
            Set(universe, (int)SpiderChannel.Led1 + led - 1, level);
        }

        /// <summary>
        /// Ailes : avec <paramref name="mirror"/>, l'aile 2 prend la position symetrique
        /// (255 - position) : elles partent de cotes opposes et se rejoignent au milieu.
        /// </summary>
        public void SetWings(byte[] universe, byte position, bool mirror = false)
        {
            Set(universe, (int)SpiderChannel.Motor1, position);
            Set(universe, (int)SpiderChannel.Motor2, mirror ? 255 - position : position);
        }

        /// <summary>Valeur DMX moteur -> angle (0..135 degres).</summary>
        public static double MotorDegrees(byte value) => value * 135.0 / 255.0;
    }
}
