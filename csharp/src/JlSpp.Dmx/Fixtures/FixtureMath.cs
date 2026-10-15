using System;

namespace JlSpp.Dmx.Fixtures
{
    /// <summary>
    /// Small helpers shared by the fixture classes. Integer maths only, so that every
    /// language of the project gives the same values.
    /// </summary>
    internal static class FixtureMath
    {
        /// <summary>Clamps any int into a DMX value 0..255.</summary>
        public static byte ClampByte(int value) => (byte)Math.Max(0, Math.Min(255, value));

        /// <summary>Maps <paramref name="amount"/> 0..255 linearly onto the DMX range low..high (0 -> low, 255 -> high).</summary>
        public static byte ScaleIntoRange(int amount, int low, int high) => (byte)(low + ClampByte(amount) * (high - low) / 255);

        /// <summary>Middle of a DMX range: the safest value to select a slot (color, gobo...).</summary>
        public static byte Middle(int low, int high) => (byte)((low + high) / 2);

        /// <summary>Throws unless a fixture of <paramref name="footprint"/> channels fits at <paramref name="address"/>.</summary>
        public static void CheckAddress(int address, int footprint)
        {
            int lastStart = DmxFrame.UniverseSize - footprint + 1;
            if (address < 1 || address > lastStart)
            {
                throw new ArgumentOutOfRangeException(nameof(address),
                    $"DMX address must be 1..{lastStart} for a {footprint}-channel fixture.");
            }
        }
    }
}
