package io.github.tomrfid.jlsppdmx;

import java.util.Collections;
import java.util.EnumMap;
import java.util.Map;

/**
 * DMX messages of the Chauvet DJ Intimidator Spot 260X moving head.
 * Source: Intimidator Spot 260X Quick Reference Guide Rev. 1 (Chauvet);
 * see docs/fixtures/chauvet-intimidator-spot-260x.md.
 *
 * <p>Every "speed" argument is 0 = slowest, 255 = fastest. Functions missing from the
 * current mode (no dimmer in 8-channel mode...) throw IllegalStateException; check
 * with {@link #has(Function)}.
 *
 * <pre>
 * byte[] universe = new byte[512];
 * ChauvetSpot260X spot = new ChauvetSpot260X(17, ChauvetSpot260X.Mode.CHANNELS_14);
 * spot.lightOn(universe, 255);                 // dimmer 100 % + shutter open
 * spot.setPanDegrees(universe, 270);
 * spot.setColor(universe, ChauvetSpot260X.Color.RED);
 * spot.setStrobe(universe, 200, ChauvetSpot260X.StrobeEffect.NORMAL);
 * </pre>
 */
public final class ChauvetSpot260X {

    /** Full pan travel with the default menu "Pan Angle" (540). */
    public static final double PAN_RANGE_DEGREES = 540.0;
    /** Full tilt travel with the default menu "Tilt Angle" (234). */
    public static final double TILT_RANGE_DEGREES = 234.0;

    // ================================================================== value types

    /** DMX mode chosen in the fixture menu (Run Mode > DMX). */
    public enum Mode {
        /** Pan, tilt, color, gobo, gobo rotation, prism, focus, shutter. */
        CHANNELS_8(8),
        /** Everything, with 16-bit pan/tilt and a dimmer. */
        CHANNELS_14(14);

        public final int channelCount;

        Mode(int channelCount) {
            this.channelCount = channelCount;
        }
    }

    /** Everything the fixture can do over DMX. */
    public enum Function {
        PAN, PAN_FINE, TILT, TILT_FINE, PAN_TILT_SPEED, COLOR_WHEEL, GOBO_WHEEL,
        GOBO_ROTATION, PRISM, FOCUS, DIMMER, SHUTTER, CONTROL, MOVEMENT_MACRO
    }

    /** Color wheel slots. dmxValue is the middle of the slot range. */
    public enum Color {
        WHITE(3),     // 0..6
        RED(10),      // 7..13
        ORANGE(17),   // 14..20
        YELLOW(24),   // 21..27
        GREEN(31),    // 28..34
        BLUE(38),     // 35..41
        CTO(45),      // 42..48, warm white filter
        CYAN(52),     // 49..55
        MAGENTA(59);  // 56..62

        public final int dmxValue;

        Color(int dmxValue) {
            this.dmxValue = dmxValue;
        }
    }

    /** Gobo wheel slots. dmxValue is the middle of the slot range. */
    public enum Gobo {
        OPEN(3),      // 0..7, no gobo
        GOBO_1(11),   // 8..15
        GOBO_2(19),   // 16..23
        GOBO_3(27),   // 24..31
        GOBO_4(35),   // 32..39
        GOBO_5(43),   // 40..47
        GOBO_6(51),   // 48..55
        GOBO_7(59);   // 56..63

        public final int dmxValue;

        Gobo(int dmxValue) {
            this.dmxValue = dmxValue;
        }
    }

    /** Gobo rotation direction, with its "slow to fast" DMX range. */
    public enum GoboRotation {
        NONE(0, 0),
        CLOCKWISE(8, 119),
        COUNTER_CLOCKWISE(120, 231),
        BOUNCE(232, 255);

        final int low;
        final int high;

        GoboRotation(int low, int high) {
            this.low = low;
            this.high = high;
        }
    }

    /** Kinds of strobe on the shutter channel, with their "slow to fast" DMX range. */
    public enum StrobeEffect {
        NORMAL(8, 76),
        PULSE(77, 145),
        RANDOM(146, 215);

        final int low;
        final int high;

        StrobeEffect(int low, int high) {
            this.low = low;
            this.high = high;
        }
    }

    /** Resets on the control channel (14-channel mode only). */
    public enum ResetTarget {
        PAN(99),          // 96..103
        TILT(107),        // 104..111
        COLOR_WHEEL(115), // 112..119
        GOBO_WHEEL(123),  // 120..127
        PRISM(139),       // 136..143
        FOCUS(147),       // 144..151
        ALL(155);         // 152..159

        public final int dmxValue;

        ResetTarget(int dmxValue) {
            this.dmxValue = dmxValue;
        }
    }

    /** Beam blacked out while something moves (control channel, 14-channel mode only). */
    public enum BlackoutOnMove {
        NONE(0),             // 0..7
        PAN_TILT(11),        // 8..15
        COLOR_WHEEL(19),     // 16..23
        GOBO_WHEEL(27),      // 24..31
        PAN_TILT_COLOR(35),  // 32..39
        PAN_TILT_GOBO(43),   // 40..47
        ALL(51);             // 48..55

        public final int dmxValue;

        BlackoutOnMove(int dmxValue) {
            this.dmxValue = dmxValue;
        }
    }

    // ================================================================= chart ranges

    private static final int COLOR_INDEXING_LOW = 65, COLOR_INDEXING_HIGH = 189;        // continuous position
    private static final int COLOR_RAINBOW_LOW = 190, COLOR_RAINBOW_HIGH = 221;         // fast (190) to slow (221)
    private static final int COLOR_RAINBOW_STOP = 222;
    private static final int COLOR_RAINBOW_REVERSE_LOW = 224, COLOR_RAINBOW_REVERSE_HIGH = 255;

    private static final int GOBO_SHAKE_FIRST = 64, GOBO_SHAKE_WIDTH = 8;               // gobo 7 shake = 64..71
    private static final int GOBO_CYCLE_LOW = 128, GOBO_CYCLE_HIGH = 189;
    private static final int GOBO_CYCLE_STOP = 191;
    private static final int GOBO_CYCLE_REVERSE_LOW = 194, GOBO_CYCLE_REVERSE_HIGH = 255;

    private static final int PRISM_OFF = 0, PRISM_ON = 255;                             // 16..255 = 3-facet prism
    private static final int SHUTTER_CLOSED = 0, SHUTTER_OPEN = 255;                    // 0..3 = no light

    private static final int MACRO_COUNT = 8, MACRO_WIDTH = 16;
    private static final int MOVEMENT_MACRO_FIRST = 8;                                  // macro 1 = 8..23
    private static final int SOUND_MACRO_FIRST = 136;                                   // sound macro 1 = 136..151

    private static final Map<Function, Integer> CHANNELS_14 = channels14();
    private static final Map<Function, Integer> CHANNELS_8 = channels8();

    /** Channel (1-based, relative to the address) of each function in 14-channel mode. */
    private static Map<Function, Integer> channels14() {
        Map<Function, Integer> map = new EnumMap<>(Function.class);
        Function[] order = {
            Function.PAN, Function.PAN_FINE, Function.TILT, Function.TILT_FINE, Function.PAN_TILT_SPEED,
            Function.COLOR_WHEEL, Function.GOBO_WHEEL, Function.GOBO_ROTATION, Function.PRISM, Function.FOCUS,
            Function.DIMMER, Function.SHUTTER, Function.CONTROL, Function.MOVEMENT_MACRO,
        };
        for (int i = 0; i < order.length; i++) {
            map.put(order[i], i + 1);
        }
        return Collections.unmodifiableMap(map);
    }

    /** Channel (1-based, relative to the address) of each function in 8-channel mode. */
    private static Map<Function, Integer> channels8() {
        Map<Function, Integer> map = new EnumMap<>(Function.class);
        Function[] order = {
            Function.PAN, Function.TILT, Function.COLOR_WHEEL, Function.GOBO_WHEEL,
            Function.GOBO_ROTATION, Function.PRISM, Function.FOCUS, Function.SHUTTER,
        };
        for (int i = 0; i < order.length; i++) {
            map.put(order[i], i + 1);
        }
        return Collections.unmodifiableMap(map);
    }

    // ===================================================================== fixture

    private final int address;
    private final Mode mode;

    /** Fixture in 14-channel mode. */
    public ChauvetSpot260X(int address) {
        this(address, Mode.CHANNELS_14);
    }

    /**
     * @param address DMX address set in the fixture menu (1..499 in 14-channel mode)
     * @param mode    DMX mode set in the fixture menu
     */
    public ChauvetSpot260X(int address, Mode mode) {
        this.address = address;
        this.mode = mode;
        FixtureMath.checkAddress(address, mode.channelCount);
    }

    public int getAddress() {
        return address;
    }

    public Mode getMode() {
        return mode;
    }

    private Map<Function, Integer> channelMap() {
        return mode == Mode.CHANNELS_8 ? CHANNELS_8 : CHANNELS_14;
    }

    // -------------------------------------------------------------------- channels

    /** True if the current mode has this function. */
    public boolean has(Function function) {
        return channelMap().containsKey(function);
    }

    /** Absolute DMX channel (1..512) of a function. */
    public int dmxChannel(Function function) {
        Integer relative = channelMap().get(function);
        if (relative == null) {
            throw new IllegalStateException(function + " is not available in " + mode.channelCount + "-channel mode");
        }
        return address + relative - 1;
    }

    /** Writes the raw value of one function into the universe. */
    public void set(byte[] universe, Function function, int value) {
        universe[dmxChannel(function) - 1] = (byte) FixtureMath.clampByte(value);
    }

    /** Centered head, sharp focus, shutter open, everything else at 0. */
    public void applyDefaults(byte[] universe) {
        for (Function function : channelMap().keySet()) {
            set(universe, function, defaultValue(function));
        }
    }

    private static int defaultValue(Function function) {
        switch (function) {
            case PAN:
            case TILT:
            case FOCUS:
                return 128;
            case SHUTTER:
                return SHUTTER_OPEN;
            default:
                return 0;
        }
    }

    // -------------------------------------------------------------------- movement

    /** Pan as a 16-bit position 0..65535 (0x8000 = middle). */
    public void setPan(byte[] universe, int position) {
        set16Bit(universe, Function.PAN, Function.PAN_FINE, position);
    }

    /** Tilt as a 16-bit position 0..65535 (0x8000 = middle). */
    public void setTilt(byte[] universe, int position) {
        set16Bit(universe, Function.TILT, Function.TILT_FINE, position);
    }

    /** Pan in degrees, 0..540 (menu "Pan Angle" default). */
    public void setPanDegrees(byte[] universe, double degrees) {
        setPan(universe, degreesTo16Bit(degrees, PAN_RANGE_DEGREES));
    }

    /** Tilt in degrees, 0..234 (menu "Tilt Angle" default). */
    public void setTiltDegrees(byte[] universe, double degrees) {
        setTilt(universe, degreesTo16Bit(degrees, TILT_RANGE_DEGREES));
    }

    /** Movement speed, FIXTURE convention: 0 = fastest, 255 = slowest. 14-channel mode only. */
    public void setPanTiltSpeed(byte[] universe, int value) {
        set(universe, Function.PAN_TILT_SPEED, value);
    }

    /** Runs built-in movement macro 1..8 (or its sound-active version). 14-channel mode only. */
    public void setMovementMacro(byte[] universe, int number, boolean soundActive) {
        if (number < 1 || number > MACRO_COUNT) {
            throw new IllegalArgumentException("Macro number must be 1..8");
        }
        int low = (soundActive ? SOUND_MACRO_FIRST : MOVEMENT_MACRO_FIRST) + (number - 1) * MACRO_WIDTH;
        int high = Math.min(low + MACRO_WIDTH - 1, 255); // the last sound-active macro is only 248..255
        set(universe, Function.MOVEMENT_MACRO, FixtureMath.middle(low, high));
    }

    public void stopMovementMacro(byte[] universe) {
        set(universe, Function.MOVEMENT_MACRO, 0);
    }

    // ----------------------------------------------------------------------- color

    /** Puts one color of the wheel in the beam. */
    public void setColor(byte[] universe, Color color) {
        set(universe, Function.COLOR_WHEEL, color.dmxValue);
    }

    /** Continuous wheel position 0..255 (lets you stop between two colors). */
    public void setColorWheelPosition(byte[] universe, int position) {
        set(universe, Function.COLOR_WHEEL,
                FixtureMath.scaleIntoRange(position, COLOR_INDEXING_LOW, COLOR_INDEXING_HIGH));
    }

    /** Turns the color wheel continuously. */
    public void setColorRainbow(byte[] universe, int speed, boolean reverse) {
        int value;
        if (reverse) {
            value = FixtureMath.scaleIntoRange(speed, COLOR_RAINBOW_REVERSE_LOW, COLOR_RAINBOW_REVERSE_HIGH);
        } else {
            // this range goes from fast to slow: flip it so that 255 is always the fastest
            int scaled = FixtureMath.scaleIntoRange(speed, COLOR_RAINBOW_LOW, COLOR_RAINBOW_HIGH);
            value = COLOR_RAINBOW_HIGH - (scaled - COLOR_RAINBOW_LOW);
        }
        set(universe, Function.COLOR_WHEEL, value);
    }

    public void stopColorRainbow(byte[] universe) {
        set(universe, Function.COLOR_WHEEL, COLOR_RAINBOW_STOP);
    }

    // ------------------------------------------------------------------------ gobo

    /** Puts one gobo in the beam (Gobo.OPEN = no gobo). */
    public void setGobo(byte[] universe, Gobo gobo) {
        set(universe, Function.GOBO_WHEEL, gobo.dmxValue);
    }

    /** Shakes gobo 1..7. */
    public void setGoboShake(byte[] universe, int gobo, int speed) {
        if (gobo < 1 || gobo > 7) {
            throw new IllegalArgumentException("Gobo number must be 1..7");
        }
        int low = GOBO_SHAKE_FIRST + (7 - gobo) * GOBO_SHAKE_WIDTH; // gobo 7 comes first on the wheel
        set(universe, Function.GOBO_WHEEL, FixtureMath.scaleIntoRange(speed, low, low + GOBO_SHAKE_WIDTH - 1));
    }

    /** Turns the gobo wheel continuously. */
    public void setGoboCycle(byte[] universe, int speed, boolean reverse) {
        int value = reverse
                ? FixtureMath.scaleIntoRange(speed, GOBO_CYCLE_REVERSE_LOW, GOBO_CYCLE_REVERSE_HIGH)
                : FixtureMath.scaleIntoRange(speed, GOBO_CYCLE_LOW, GOBO_CYCLE_HIGH);
        set(universe, Function.GOBO_WHEEL, value);
    }

    public void stopGoboCycle(byte[] universe) {
        set(universe, Function.GOBO_WHEEL, GOBO_CYCLE_STOP);
    }

    /** Rotates the gobo itself. */
    public void setGoboRotation(byte[] universe, GoboRotation rotation, int speed) {
        int value = rotation == GoboRotation.NONE
                ? 0
                : FixtureMath.scaleIntoRange(speed, rotation.low, rotation.high);
        set(universe, Function.GOBO_ROTATION, value);
    }

    // --------------------------------------------------------------- prism / focus

    /** 3-facet prism in or out of the beam. */
    public void setPrism(byte[] universe, boolean on) {
        set(universe, Function.PRISM, on ? PRISM_ON : PRISM_OFF);
    }

    /** Focus 0..255. */
    public void setFocus(byte[] universe, int value) {
        set(universe, Function.FOCUS, value);
    }

    // ------------------------------------------------------------ dimmer / shutter

    /** Dimmer 0..255 (0..100 %). 14-channel mode only. */
    public void setDimmer(byte[] universe, int level) {
        set(universe, Function.DIMMER, level);
    }

    /** Shutter open, no strobe. */
    public void openShutter(byte[] universe) {
        set(universe, Function.SHUTTER, SHUTTER_OPEN);
    }

    /** Shutter closed: no light at all. */
    public void closeShutter(byte[] universe) {
        set(universe, Function.SHUTTER, SHUTTER_CLOSED);
    }

    /** Strobe; use openShutter() to stop it. */
    public void setStrobe(byte[] universe, int speed, StrobeEffect effect) {
        set(universe, Function.SHUTTER, FixtureMath.scaleIntoRange(speed, effect.low, effect.high));
    }

    /** Makes the fixture emit light: dimmer at level (14-channel mode) and shutter open. */
    public void lightOn(byte[] universe, int level) {
        if (has(Function.DIMMER)) {
            setDimmer(universe, level);
        }
        openShutter(universe);
    }

    /** No light: dimmer at 0 (14-channel mode) and shutter closed. */
    public void blackout(byte[] universe) {
        if (has(Function.DIMMER)) {
            setDimmer(universe, 0);
        }
        closeShutter(universe);
    }

    // --------------------------------------------------------------------- control

    /** Blacks out the beam while pan/tilt or a wheel moves. 14-channel mode only. */
    public void setBlackoutOnMove(byte[] universe, BlackoutOnMove option) {
        set(universe, Function.CONTROL, option.dmxValue);
    }

    /** Starts a reset; call clearControl() a few seconds later. 14-channel mode only. */
    public void reset(byte[] universe, ResetTarget target) {
        set(universe, Function.CONTROL, target.dmxValue);
    }

    /** Control channel back to "no function". */
    public void clearControl(byte[] universe) {
        set(universe, Function.CONTROL, 0);
    }

    // ------------------------------------------------------------------- internals

    /** Writes a 16-bit position; the fine byte is dropped in 8-channel mode. */
    private void set16Bit(byte[] universe, Function coarse, Function fine, int position) {
        int p = Math.max(0, Math.min(0xFFFF, position));
        set(universe, coarse, p >> 8);
        if (has(fine)) {
            set(universe, fine, p & 0xFF);
        }
    }

    /** Angle 0..fullRange -> 16-bit position, rounded to the nearest step. */
    private static int degreesTo16Bit(double degrees, double fullRange) {
        double clamped = Math.max(0.0, Math.min(fullRange, degrees));
        return (int) (clamped * 65535.0 / fullRange + 0.5);
    }
}
