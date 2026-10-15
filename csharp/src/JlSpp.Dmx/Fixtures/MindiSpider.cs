using System;
using System.Collections.Generic;

namespace JlSpp.Dmx.Fixtures
{
    /// <summary>Channels of the Mindi Mini Spider 8x3W RGBW in 15-channel mode (from its manual).</summary>
    public enum SpiderChannel
    {
        /// <summary>Wing 1 position: 0..255 = 0..135 degrees.</summary>
        Motor1 = 1,
        /// <summary>Wing 2 position: 0..255 = 0..135 degrees.</summary>
        Motor2 = 2,
        /// <summary>Master dimmer.</summary>
        Dimmer = 3,
        /// <summary>0 = no strobe, then flash speed.</summary>
        Strobe = 4,
        /// <summary>LED 1 (channels 5..12 = LED 1..8, color ASSUMED: red, green, blue, white, twice).</summary>
        Led1 = 5,
        /// <summary>Built-in effect programs.</summary>
        Macro = 13,
        /// <summary>Effect speed (slow -> fast).</summary>
        EffectSpeed = 14,
        /// <summary>Reset: keep at 0.</summary>
        Reset = 15,
    }

    /// <summary>
    /// DMX messages of the Mini Spider (see docs/fixtures/mindi-mini-spider.md).
    /// <para>
    /// ADDRESS QUIRK (observed on the fixture): when set to address N, the Spider ignores
    /// channel N and listens from N+1. With <c>addressQuirk = true</c> (default), give the
    /// address SHOWN on the fixture display.
    /// </para>
    /// <code>
    /// var universe = new byte[512];
    /// var spider = new MindiSpider(address: 1);
    /// spider.SetDimmer(universe, 255);
    /// spider.SetWings(universe, 200, mirror: true);
    /// </code>
    /// </summary>
    public sealed class MindiSpider
    {
        /// <summary>Channels in the manual (15-channel mode).</summary>
        public const int ChannelCount = 15;

        /// <summary>Number of LEDs.</summary>
        public const int LedCount = 8;

        /// <summary>Wing angle for motor value 255.</summary>
        public const double MotorMaxDegrees = 135.0;

        /// <summary>LEDs of the left wing (ASSUMED, to be checked on the fixture).</summary>
        public static readonly IReadOnlyList<int> LeftWingLeds = new[] { 1, 2, 3, 4 };

        /// <summary>LEDs of the right wing (ASSUMED, to be checked on the fixture).</summary>
        public static readonly IReadOnlyList<int> RightWingLeds = new[] { 5, 6, 7, 8 };

        /// <param name="address">DMX address shown on the fixture.</param>
        /// <param name="addressQuirk">True (default) if the fixture ignores its first channel, as observed on our unit.</param>
        public MindiSpider(int address, bool addressQuirk = true)
        {
            Address = address;
            AddressQuirk = addressQuirk;
            FixtureMath.CheckAddress(address, FootprintSize);
        }

        /// <summary>DMX address shown on the fixture.</summary>
        public int Address { get; }

        /// <summary>True if the shift of one channel is applied.</summary>
        public bool AddressQuirk { get; }

        /// <summary>Number of DMX channels used, the ignored one included (16 with the quirk).</summary>
        public int FootprintSize => ChannelCount + QuirkOffset;

        private int QuirkOffset => AddressQuirk ? 1 : 0;

        // ---------------------------------------------------------------- channels

        /// <summary>Absolute DMX channel (1..512) of a Spider function.</summary>
        public int DmxChannel(SpiderChannel channel) => DmxChannel((int)channel);

        private int DmxChannel(int spiderChannel) => Address + QuirkOffset + spiderChannel - 1;

        private void Set(byte[] universe, int spiderChannel, int value) =>
            universe[DmxChannel(spiderChannel) - 1] = FixtureMath.ClampByte(value);

        // --------------------------------------------------------------- functions

        /// <summary>Master dimmer. Must be open, otherwise the LEDs stay dark.</summary>
        public void SetDimmer(byte[] universe, byte level) => Set(universe, (int)SpiderChannel.Dimmer, level);

        /// <summary>Strobe speed; 0 = no strobe.</summary>
        public void SetStrobe(byte[] universe, byte speed) => Set(universe, (int)SpiderChannel.Strobe, speed);

        /// <summary>Same as <c>SetStrobe(universe, 0)</c>.</summary>
        public void StopStrobe(byte[] universe) => SetStrobe(universe, 0);

        /// <summary>Intensity of one LED (1..8).</summary>
        public void SetLed(byte[] universe, int led, byte level)
        {
            if (led < 1 || led > LedCount)
            {
                throw new ArgumentOutOfRangeException(nameof(led), "LED number must be 1..8.");
            }
            Set(universe, (int)SpiderChannel.Led1 + led - 1, level);
        }

        /// <summary>Same intensity for a group of LEDs (e.g. <see cref="LeftWingLeds"/>).</summary>
        public void SetLeds(byte[] universe, IEnumerable<int> leds, byte level)
        {
            foreach (int led in leds)
            {
                SetLed(universe, led, level);
            }
        }

        /// <summary>Position of one wing (1 or 2), 0..255 = 0..135 degrees.</summary>
        public void SetWingMotor(byte[] universe, int wing, byte position)
        {
            if (wing != 1 && wing != 2)
            {
                throw new ArgumentOutOfRangeException(nameof(wing), "Wing must be 1 or 2.");
            }
            Set(universe, wing == 1 ? (int)SpiderChannel.Motor1 : (int)SpiderChannel.Motor2, position);
        }

        /// <summary>
        /// Moves both wings. With <paramref name="mirror"/>, wing 2 takes the symmetric position
        /// (255 - position): the wings start from opposite sides and meet in the middle.
        /// </summary>
        public void SetWings(byte[] universe, byte position, bool mirror = false)
        {
            SetWingMotor(universe, 1, position);
            SetWingMotor(universe, 2, mirror ? Mirrored(position) : position);
        }

        /// <summary>Built-in effect program (raw value, see the manual) and its speed.</summary>
        public void SetMacro(byte[] universe, byte value, byte speed = 128)
        {
            Set(universe, (int)SpiderChannel.Macro, value);
            Set(universe, (int)SpiderChannel.EffectSpeed, speed);
        }

        /// <summary>Symmetric wing position: 0 &lt;-&gt; 255.</summary>
        public static byte Mirrored(byte position) => (byte)(255 - position);

        /// <summary>Motor DMX value -> wing angle (0..135 degrees).</summary>
        public static double MotorDegrees(byte value) => value * MotorMaxDegrees / 255.0;
    }
}
