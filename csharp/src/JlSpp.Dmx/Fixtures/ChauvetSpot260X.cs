using System;
using System.Collections.Generic;

namespace JlSpp.Dmx.Fixtures
{
    /// <summary>
    /// DMX messages of the Chauvet DJ Intimidator Spot 260X moving head.
    /// Source: Intimidator Spot 260X Quick Reference Guide Rev. 1 (Chauvet);
    /// see docs/fixtures/chauvet-intimidator-spot-260x.md.
    /// <para>
    /// Every "speed" argument is 0 = slowest, 255 = fastest. Functions missing from the
    /// current mode (no dimmer in 8-channel mode...) throw <see cref="InvalidOperationException"/>;
    /// check with <see cref="Has"/>.
    /// </para>
    /// <code>
    /// var universe = new byte[512];
    /// var spot = new ChauvetSpot260X(address: 17);   // 14-channel mode by default
    /// spot.LightOn(universe);                        // dimmer 100 % + shutter open
    /// spot.SetPanDegrees(universe, 270);
    /// spot.SetColor(universe, Spot260XColor.Red);
    /// spot.SetGobo(universe, Spot260XGobo.Gobo3);
    /// spot.SetStrobe(universe, speed: 200);
    /// </code>
    /// </summary>
    public sealed class ChauvetSpot260X
    {
        /// <summary>Full pan travel with the default menu "Pan Angle" (540).</summary>
        public const double PanRangeDegrees = 540.0;

        /// <summary>Full tilt travel with the default menu "Tilt Angle" (234).</summary>
        public const double TiltRangeDegrees = 234.0;

        // ------------------------------------------------------------- chart ranges

        private const int ColorIndexingLow = 65, ColorIndexingHigh = 189;          // continuous wheel position
        private const int ColorRainbowLow = 190, ColorRainbowHigh = 221;           // fast (190) to slow (221)
        private const int ColorRainbowStop = 222;
        private const int ColorRainbowReverseLow = 224, ColorRainbowReverseHigh = 255;

        private const int GoboShakeFirst = 64, GoboShakeWidth = 8;                 // gobo 7 shake = 64..71 ... gobo 1 = 112..119
        private const int GoboCycleLow = 128, GoboCycleHigh = 189;
        private const int GoboCycleStop = 191;
        private const int GoboCycleReverseLow = 194, GoboCycleReverseHigh = 255;

        private const int PrismOff = 0, PrismOn = 255;                             // 16..255 = 3-facet prism
        private const int ShutterClosed = 0, ShutterOpen = 255;                    // 0..3 = no light, 216..255 = open

        private const int MacroCount = 8, MacroWidth = 16;
        private const int MovementMacroFirst = 8;                                  // macro 1 = 8..23
        private const int SoundMacroFirst = 136;                                   // sound-active macro 1 = 136..151

        /// <summary>Channel (1-based, relative to the address) of each function in 14-channel mode.</summary>
        private static readonly Dictionary<Spot260XFunction, int> Channels14 = new Dictionary<Spot260XFunction, int>
        {
            [Spot260XFunction.Pan] = 1,
            [Spot260XFunction.PanFine] = 2,
            [Spot260XFunction.Tilt] = 3,
            [Spot260XFunction.TiltFine] = 4,
            [Spot260XFunction.PanTiltSpeed] = 5,
            [Spot260XFunction.ColorWheel] = 6,
            [Spot260XFunction.GoboWheel] = 7,
            [Spot260XFunction.GoboRotation] = 8,
            [Spot260XFunction.Prism] = 9,
            [Spot260XFunction.Focus] = 10,
            [Spot260XFunction.Dimmer] = 11,
            [Spot260XFunction.Shutter] = 12,
            [Spot260XFunction.Control] = 13,
            [Spot260XFunction.MovementMacro] = 14,
        };

        /// <summary>Channel (1-based, relative to the address) of each function in 8-channel mode.</summary>
        private static readonly Dictionary<Spot260XFunction, int> Channels8 = new Dictionary<Spot260XFunction, int>
        {
            [Spot260XFunction.Pan] = 1,
            [Spot260XFunction.Tilt] = 2,
            [Spot260XFunction.ColorWheel] = 3,
            [Spot260XFunction.GoboWheel] = 4,
            [Spot260XFunction.GoboRotation] = 5,
            [Spot260XFunction.Prism] = 6,
            [Spot260XFunction.Focus] = 7,
            [Spot260XFunction.Shutter] = 8,
        };

        /// <param name="address">DMX address set in the fixture menu (1..499 in 14-channel mode).</param>
        /// <param name="mode">DMX mode set in the fixture menu.</param>
        public ChauvetSpot260X(int address, Spot260XMode mode = Spot260XMode.Channels14)
        {
            if (mode != Spot260XMode.Channels8 && mode != Spot260XMode.Channels14)
            {
                throw new ArgumentOutOfRangeException(nameof(mode));
            }
            Address = address;
            Mode = mode;
            FixtureMath.CheckAddress(address, FootprintSize);
        }

        /// <summary>DMX address set in the fixture menu.</summary>
        public int Address { get; }

        /// <summary>DMX mode set in the fixture menu.</summary>
        public Spot260XMode Mode { get; }

        /// <summary>Number of DMX channels used (8 or 14).</summary>
        public int FootprintSize => (int)Mode;

        private Dictionary<Spot260XFunction, int> ChannelMap => Mode == Spot260XMode.Channels8 ? Channels8 : Channels14;

        // ----------------------------------------------------------------- channels

        /// <summary>True if the current mode has this function.</summary>
        public bool Has(Spot260XFunction function) => ChannelMap.ContainsKey(function);

        /// <summary>Absolute DMX channel (1..512) of a function.</summary>
        public int DmxChannel(Spot260XFunction function)
        {
            if (!ChannelMap.TryGetValue(function, out int relative))
            {
                throw new InvalidOperationException($"{function} is not available in {(int)Mode}-channel mode.");
            }
            return Address + relative - 1;
        }

        /// <summary>Writes the raw value of one function into the universe.</summary>
        public void Set(byte[] universe, Spot260XFunction function, int value) =>
            universe[DmxChannel(function) - 1] = FixtureMath.ClampByte(value);

        /// <summary>Centered head, sharp focus, shutter open, everything else at 0.</summary>
        public void ApplyDefaults(byte[] universe)
        {
            foreach (var function in ChannelMap.Keys)
            {
                Set(universe, function, DefaultValue(function));
            }
        }

        private static int DefaultValue(Spot260XFunction function)
        {
            switch (function)
            {
                case Spot260XFunction.Pan:
                case Spot260XFunction.Tilt:
                case Spot260XFunction.Focus:
                    return 128;
                case Spot260XFunction.Shutter:
                    return ShutterOpen;
                default:
                    return 0;
            }
        }

        // ----------------------------------------------------------------- movement

        /// <summary>Pan as a 16-bit position 0..65535 (0x8000 = middle).</summary>
        public void SetPan(byte[] universe, ushort position) =>
            Set16Bit(universe, Spot260XFunction.Pan, Spot260XFunction.PanFine, position);

        /// <summary>Tilt as a 16-bit position 0..65535 (0x8000 = middle).</summary>
        public void SetTilt(byte[] universe, ushort position) =>
            Set16Bit(universe, Spot260XFunction.Tilt, Spot260XFunction.TiltFine, position);

        /// <summary>Pan in degrees, 0..540 (pass fullRange if the menu "Pan Angle" is 360 or 180).</summary>
        public void SetPanDegrees(byte[] universe, double degrees, double fullRange = PanRangeDegrees) =>
            SetPan(universe, DegreesTo16Bit(degrees, fullRange));

        /// <summary>Tilt in degrees, 0..234 (pass fullRange if the menu "Tilt Angle" is 180 or 90).</summary>
        public void SetTiltDegrees(byte[] universe, double degrees, double fullRange = TiltRangeDegrees) =>
            SetTilt(universe, DegreesTo16Bit(degrees, fullRange));

        /// <summary>Movement speed, FIXTURE convention: 0 = fastest, 255 = slowest. 14-channel mode only.</summary>
        public void SetPanTiltSpeed(byte[] universe, byte value) => Set(universe, Spot260XFunction.PanTiltSpeed, value);

        /// <summary>Runs built-in movement macro 1..8 (or its sound-active version). 14-channel mode only.</summary>
        public void SetMovementMacro(byte[] universe, int number, bool soundActive = false)
        {
            if (number < 1 || number > MacroCount)
            {
                throw new ArgumentOutOfRangeException(nameof(number), "Macro number must be 1..8.");
            }
            int low = (soundActive ? SoundMacroFirst : MovementMacroFirst) + (number - 1) * MacroWidth;
            int high = Math.Min(low + MacroWidth - 1, 255); // the last sound-active macro is only 248..255
            Set(universe, Spot260XFunction.MovementMacro, FixtureMath.Middle(low, high));
        }

        /// <summary>Stops the movement macro.</summary>
        public void StopMovementMacro(byte[] universe) => Set(universe, Spot260XFunction.MovementMacro, 0);

        // -------------------------------------------------------------------- color

        /// <summary>Puts one color of the wheel in the beam.</summary>
        public void SetColor(byte[] universe, Spot260XColor color) => Set(universe, Spot260XFunction.ColorWheel, (byte)color);

        /// <summary>Continuous wheel position 0..255 (lets you stop between two colors).</summary>
        public void SetColorWheelPosition(byte[] universe, byte position) =>
            Set(universe, Spot260XFunction.ColorWheel, FixtureMath.ScaleIntoRange(position, ColorIndexingLow, ColorIndexingHigh));

        /// <summary>Turns the color wheel continuously.</summary>
        public void SetColorRainbow(byte[] universe, byte speed, bool reverse = false)
        {
            int value;
            if (reverse)
            {
                value = FixtureMath.ScaleIntoRange(speed, ColorRainbowReverseLow, ColorRainbowReverseHigh);
            }
            else
            {
                // this range goes from fast to slow: flip it so that 255 is always the fastest
                int scaled = FixtureMath.ScaleIntoRange(speed, ColorRainbowLow, ColorRainbowHigh);
                value = ColorRainbowHigh - (scaled - ColorRainbowLow);
            }
            Set(universe, Spot260XFunction.ColorWheel, value);
        }

        /// <summary>Stops the color wheel where it is.</summary>
        public void StopColorRainbow(byte[] universe) => Set(universe, Spot260XFunction.ColorWheel, ColorRainbowStop);

        // --------------------------------------------------------------------- gobo

        /// <summary>Puts one gobo in the beam (<see cref="Spot260XGobo.Open"/> = no gobo).</summary>
        public void SetGobo(byte[] universe, Spot260XGobo gobo) => Set(universe, Spot260XFunction.GoboWheel, (byte)gobo);

        /// <summary>Shakes gobo 1..7.</summary>
        public void SetGoboShake(byte[] universe, int gobo, byte speed)
        {
            if (gobo < 1 || gobo > 7)
            {
                throw new ArgumentOutOfRangeException(nameof(gobo), "Gobo number must be 1..7.");
            }
            int low = GoboShakeFirst + (7 - gobo) * GoboShakeWidth; // gobo 7 comes first on the wheel
            Set(universe, Spot260XFunction.GoboWheel, FixtureMath.ScaleIntoRange(speed, low, low + GoboShakeWidth - 1));
        }

        /// <summary>Turns the gobo wheel continuously.</summary>
        public void SetGoboCycle(byte[] universe, byte speed, bool reverse = false)
        {
            int value = reverse
                ? FixtureMath.ScaleIntoRange(speed, GoboCycleReverseLow, GoboCycleReverseHigh)
                : FixtureMath.ScaleIntoRange(speed, GoboCycleLow, GoboCycleHigh);
            Set(universe, Spot260XFunction.GoboWheel, value);
        }

        /// <summary>Stops the gobo wheel where it is.</summary>
        public void StopGoboCycle(byte[] universe) => Set(universe, Spot260XFunction.GoboWheel, GoboCycleStop);

        /// <summary>Rotates the gobo itself.</summary>
        public void SetGoboRotation(byte[] universe, GoboRotation rotation, byte speed = 128)
        {
            Set(universe, Spot260XFunction.GoboRotation, RotationValue(rotation, speed));
        }

        private static int RotationValue(GoboRotation rotation, byte speed)
        {
            switch (rotation)
            {
                case GoboRotation.Clockwise: return FixtureMath.ScaleIntoRange(speed, 8, 119);
                case GoboRotation.CounterClockwise: return FixtureMath.ScaleIntoRange(speed, 120, 231);
                case GoboRotation.Bounce: return FixtureMath.ScaleIntoRange(speed, 232, 255);
                default: return 0; // no rotation
            }
        }

        // ------------------------------------------------------------ prism / focus

        /// <summary>3-facet prism in or out of the beam.</summary>
        public void SetPrism(byte[] universe, bool on) => Set(universe, Spot260XFunction.Prism, on ? PrismOn : PrismOff);

        /// <summary>Focus 0..255.</summary>
        public void SetFocus(byte[] universe, byte value) => Set(universe, Spot260XFunction.Focus, value);

        // --------------------------------------------------------- dimmer / shutter

        /// <summary>Dimmer 0..255 (0..100 %). 14-channel mode only.</summary>
        public void SetDimmer(byte[] universe, byte level) => Set(universe, Spot260XFunction.Dimmer, level);

        /// <summary>Shutter open, no strobe.</summary>
        public void OpenShutter(byte[] universe) => Set(universe, Spot260XFunction.Shutter, ShutterOpen);

        /// <summary>Shutter closed: no light at all.</summary>
        public void CloseShutter(byte[] universe) => Set(universe, Spot260XFunction.Shutter, ShutterClosed);

        /// <summary>Strobe; use <see cref="OpenShutter"/> to stop it.</summary>
        public void SetStrobe(byte[] universe, byte speed, StrobeEffect effect = StrobeEffect.Normal)
        {
            Set(universe, Spot260XFunction.Shutter, StrobeValue(effect, speed));
        }

        private static int StrobeValue(StrobeEffect effect, byte speed)
        {
            switch (effect)
            {
                case StrobeEffect.Pulse: return FixtureMath.ScaleIntoRange(speed, 77, 145);
                case StrobeEffect.Random: return FixtureMath.ScaleIntoRange(speed, 146, 215);
                default: return FixtureMath.ScaleIntoRange(speed, 8, 76);
            }
        }

        /// <summary>Makes the fixture emit light: dimmer at <paramref name="level"/> (14-channel mode) and shutter open.</summary>
        public void LightOn(byte[] universe, byte level = 255)
        {
            if (Has(Spot260XFunction.Dimmer))
            {
                SetDimmer(universe, level);
            }
            OpenShutter(universe);
        }

        /// <summary>No light: dimmer at 0 (14-channel mode) and shutter closed.</summary>
        public void Blackout(byte[] universe)
        {
            if (Has(Spot260XFunction.Dimmer))
            {
                SetDimmer(universe, 0);
            }
            CloseShutter(universe);
        }

        // ------------------------------------------------------------------ control

        /// <summary>Blacks out the beam while pan/tilt or a wheel moves. 14-channel mode only.</summary>
        public void SetBlackoutOnMove(byte[] universe, BlackoutOnMove option) => Set(universe, Spot260XFunction.Control, (byte)option);

        /// <summary>Starts a reset; call <see cref="ClearControl"/> a few seconds later. 14-channel mode only.</summary>
        public void Reset(byte[] universe, Spot260XReset target = Spot260XReset.All) => Set(universe, Spot260XFunction.Control, (byte)target);

        /// <summary>Control channel back to "no function".</summary>
        public void ClearControl(byte[] universe) => Set(universe, Spot260XFunction.Control, 0);

        // ---------------------------------------------------------------- internals

        /// <summary>Writes a 16-bit position; the fine byte is dropped in 8-channel mode.</summary>
        private void Set16Bit(byte[] universe, Spot260XFunction coarse, Spot260XFunction fine, ushort position)
        {
            Set(universe, coarse, position >> 8);
            if (Has(fine))
            {
                Set(universe, fine, position & 0xFF);
            }
        }

        /// <summary>Angle 0..fullRange -> 16-bit position, rounded to the nearest step.</summary>
        private static ushort DegreesTo16Bit(double degrees, double fullRange)
        {
            double clamped = Math.Max(0.0, Math.Min(fullRange, degrees));
            return (ushort)(clamped * 65535.0 / fullRange + 0.5);
        }
    }
}
