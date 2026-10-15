package io.github.tomrfid.jlsppdmx;

/**
 * DMX messages of the Mindi Mini Spider 8x3W RGBW (15-channel mode), see
 * docs/fixtures/mindi-mini-spider.md.
 *
 * <p>ADDRESS QUIRK (observed on the fixture): when set to address N, the Spider ignores
 * channel N and listens from N+1. With addressQuirk = true (default), give the address
 * SHOWN on the fixture display.
 *
 * <pre>
 * byte[] universe = new byte[512];
 * MindiSpider spider = new MindiSpider(1);
 * spider.setDimmer(universe, 255);
 * spider.setWings(universe, 200, true);
 * </pre>
 */
public final class MindiSpider {
    // Channels of the Spider (1..15), from its manual.
    public static final int MOTOR_1 = 1;       // wing 1 position: 0..255 = 0..135 degrees
    public static final int MOTOR_2 = 2;       // wing 2 position
    public static final int DIMMER = 3;        // master dimmer
    public static final int STROBE = 4;        // 0 = no strobe, then flash speed
    public static final int LED_1 = 5;         // LED 1..8 = channels 5..12 (color ASSUMED: R, G, B, W twice)
    public static final int MACRO = 13;        // built-in effect programs
    public static final int EFFECT_SPEED = 14; // effect speed, slow -> fast
    public static final int RESET = 15;        // keep at 0

    public static final int CHANNEL_COUNT = 15;
    public static final int LED_COUNT = 8;

    /** LEDs of each wing (ASSUMED, to be checked on the fixture). */
    public static final int[] LEFT_WING_LEDS = {1, 2, 3, 4};
    public static final int[] RIGHT_WING_LEDS = {5, 6, 7, 8};

    private final int address;
    private final boolean addressQuirk;

    /** Spider with the address quirk applied (as observed on our unit). */
    public MindiSpider(int address) {
        this(address, true);
    }

    /**
     * @param address      DMX address shown on the fixture
     * @param addressQuirk true if the fixture ignores its first channel
     */
    public MindiSpider(int address, boolean addressQuirk) {
        this.address = address;
        this.addressQuirk = addressQuirk;
        FixtureMath.checkAddress(address, footprintSize());
    }

    /** Number of DMX channels used, the ignored one included (16 with the quirk). */
    public int footprintSize() {
        return CHANNEL_COUNT + quirkOffset();
    }

    private int quirkOffset() {
        return addressQuirk ? 1 : 0;
    }

    // ---------------------------------------------------------------- channels

    /** Absolute DMX channel (1..512) of a Spider channel (1..15). */
    public int dmxChannel(int spiderChannel) {
        return address + quirkOffset() + spiderChannel - 1;
    }

    private void set(byte[] universe, int spiderChannel, int value) {
        universe[dmxChannel(spiderChannel) - 1] = (byte) FixtureMath.clampByte(value);
    }

    // --------------------------------------------------------------- functions

    /** Master dimmer. Must be open, otherwise the LEDs stay dark. */
    public void setDimmer(byte[] universe, int level) {
        set(universe, DIMMER, level);
    }

    /** Strobe speed; 0 = no strobe. */
    public void setStrobe(byte[] universe, int speed) {
        set(universe, STROBE, speed);
    }

    /** Same as setStrobe(universe, 0). */
    public void stopStrobe(byte[] universe) {
        setStrobe(universe, 0);
    }

    /** Intensity of one LED (1..8). */
    public void setLed(byte[] universe, int led, int level) {
        if (led < 1 || led > LED_COUNT) {
            throw new IllegalArgumentException("LED number must be 1..8");
        }
        set(universe, LED_1 + led - 1, level);
    }

    /** Same intensity for a group of LEDs (e.g. LEFT_WING_LEDS). */
    public void setLeds(byte[] universe, int[] leds, int level) {
        for (int led : leds) {
            setLed(universe, led, level);
        }
    }

    /** Position of one wing (1 or 2), 0..255 = 0..135 degrees. */
    public void setWingMotor(byte[] universe, int wing, int position) {
        if (wing != 1 && wing != 2) {
            throw new IllegalArgumentException("Wing must be 1 or 2");
        }
        set(universe, wing == 1 ? MOTOR_1 : MOTOR_2, position);
    }

    /**
     * Moves both wings. With mirror, wing 2 takes the symmetric position (255 - position):
     * the wings start from opposite sides and meet in the middle.
     */
    public void setWings(byte[] universe, int position, boolean mirror) {
        int p = FixtureMath.clampByte(position);
        setWingMotor(universe, 1, p);
        setWingMotor(universe, 2, mirror ? 255 - p : p);
    }

    /** Built-in effect program (raw value, see the manual) and its speed. */
    public void setMacro(byte[] universe, int value, int speed) {
        set(universe, MACRO, value);
        set(universe, EFFECT_SPEED, speed);
    }
}
