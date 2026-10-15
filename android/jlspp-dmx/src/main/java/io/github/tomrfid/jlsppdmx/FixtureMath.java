package io.github.tomrfid.jlsppdmx;

/**
 * Small helpers shared by the fixture classes. Integer maths only, so that every
 * language of the project gives the same values.
 */
final class FixtureMath {
    private FixtureMath() {}

    /** Clamps any int into a DMX value 0..255. */
    static int clampByte(int value) {
        return Math.max(0, Math.min(255, value));
    }

    /** Maps amount 0..255 linearly onto the DMX range low..high (0 -> low, 255 -> high). */
    static int scaleIntoRange(int amount, int low, int high) {
        return low + clampByte(amount) * (high - low) / 255;
    }

    /** Middle of a DMX range: the safest value to select a slot (color, gobo...). */
    static int middle(int low, int high) {
        return (low + high) / 2;
    }

    /** Throws unless a fixture of {@code footprint} channels fits at {@code address}. */
    static void checkAddress(int address, int footprint) {
        int lastStart = DmxFrame.UNIVERSE_SIZE - footprint + 1;
        if (address < 1 || address > lastStart) {
            throw new IllegalArgumentException(
                    "DMX address must be 1.." + lastStart + " for a " + footprint + "-channel fixture");
        }
    }
}
