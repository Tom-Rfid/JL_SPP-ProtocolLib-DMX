namespace JlSpp.Dmx.Fixtures
{
    // Value types of the Chauvet Intimidator Spot 260X (see ChauvetSpot260X.cs).
    // Source: Intimidator Spot 260X Quick Reference Guide Rev. 1 (Chauvet).

    /// <summary>DMX mode chosen in the fixture menu (Run Mode &gt; DMX). The value is the number of channels.</summary>
    public enum Spot260XMode
    {
        /// <summary>Pan, tilt, color, gobo, gobo rotation, prism, focus, shutter.</summary>
        Channels8 = 8,
        /// <summary>Everything, with 16-bit pan/tilt and a dimmer.</summary>
        Channels14 = 14,
    }

    /// <summary>Everything the fixture can do over DMX.</summary>
    public enum Spot260XFunction
    {
        Pan,
        PanFine,
        Tilt,
        TiltFine,
        PanTiltSpeed,
        ColorWheel,
        GoboWheel,
        GoboRotation,
        Prism,
        Focus,
        Dimmer,
        Shutter,
        Control,
        MovementMacro,
    }

    /// <summary>Color wheel slots. The value is the middle of the slot range.</summary>
    public enum Spot260XColor : byte
    {
        /// <summary>0..6</summary>
        White = 3,
        /// <summary>7..13</summary>
        Red = 10,
        /// <summary>14..20</summary>
        Orange = 17,
        /// <summary>21..27</summary>
        Yellow = 24,
        /// <summary>28..34</summary>
        Green = 31,
        /// <summary>35..41</summary>
        Blue = 38,
        /// <summary>42..48, warm white filter.</summary>
        Cto = 45,
        /// <summary>49..55</summary>
        Cyan = 52,
        /// <summary>56..62</summary>
        Magenta = 59,
    }

    /// <summary>Gobo wheel slots. The value is the middle of the slot range.</summary>
    public enum Spot260XGobo : byte
    {
        /// <summary>0..7, no gobo.</summary>
        Open = 3,
        /// <summary>8..15</summary>
        Gobo1 = 11,
        /// <summary>16..23</summary>
        Gobo2 = 19,
        /// <summary>24..31</summary>
        Gobo3 = 27,
        /// <summary>32..39</summary>
        Gobo4 = 35,
        /// <summary>40..47</summary>
        Gobo5 = 43,
        /// <summary>48..55</summary>
        Gobo6 = 51,
        /// <summary>56..63</summary>
        Gobo7 = 59,
    }

    /// <summary>Gobo rotation direction (the speed is given separately).</summary>
    public enum GoboRotation
    {
        /// <summary>0..7</summary>
        None,
        /// <summary>8..119, slow to fast.</summary>
        Clockwise,
        /// <summary>120..231, slow to fast.</summary>
        CounterClockwise,
        /// <summary>232..255, slow to fast.</summary>
        Bounce,
    }

    /// <summary>Kinds of strobe on the shutter channel.</summary>
    public enum StrobeEffect
    {
        /// <summary>8..76, slow to fast.</summary>
        Normal,
        /// <summary>77..145, slow to fast.</summary>
        Pulse,
        /// <summary>146..215, slow to fast.</summary>
        Random,
    }

    /// <summary>Resets on the control channel (14-channel mode only).</summary>
    public enum Spot260XReset : byte
    {
        /// <summary>96..103</summary>
        Pan = 99,
        /// <summary>104..111</summary>
        Tilt = 107,
        /// <summary>112..119</summary>
        ColorWheel = 115,
        /// <summary>120..127</summary>
        GoboWheel = 123,
        /// <summary>136..143</summary>
        Prism = 139,
        /// <summary>144..151</summary>
        Focus = 147,
        /// <summary>152..159</summary>
        All = 155,
    }

    /// <summary>Beam blacked out while something moves (control channel, 14-channel mode only).</summary>
    public enum BlackoutOnMove : byte
    {
        /// <summary>0..7</summary>
        None = 0,
        /// <summary>8..15</summary>
        PanTilt = 11,
        /// <summary>16..23</summary>
        ColorWheel = 19,
        /// <summary>24..31</summary>
        GoboWheel = 27,
        /// <summary>32..39</summary>
        PanTiltColor = 35,
        /// <summary>40..47</summary>
        PanTiltGobo = 43,
        /// <summary>48..55</summary>
        All = 51,
    }
}
