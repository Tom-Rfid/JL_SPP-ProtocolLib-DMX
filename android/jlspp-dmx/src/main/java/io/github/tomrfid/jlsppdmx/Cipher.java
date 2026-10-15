package io.github.tomrfid.jlsppdmx;

/**
 * Channel scrambling of the JL_SPP DMX protocol (port of {@code Code.java}, RY-AI Android app).
 *
 * <p>This is NOT cryptography: a byte substitution chosen by a counter:
 * {@code table = PASSWORD[SIN[code] % 5]}, {@code output = table[(byte + code) % 256]}.
 * The tables ({@link CipherTables}) are generated from spec/cipher_tables.json.
 */
public final class Cipher {
    private static final int TABLE_COUNT = 5;

    private Cipher() {}

    /** Same as Code.Encryption1, IN PLACE; writes the key at buf[marker] and buf[marker + 1]. */
    public static void encrypt(byte[] buf, int start, int length, int codeNum, int marker) {
        int code = codeNum & 0xFF;
        int[] table = scrambleTable(code);
        for (int i = start; i < start + length; i++) {
            buf[i] = (byte) scrambleByte(buf[i] & 0xFF, code, table);
        }
        buf[marker] = (byte) CipherTables.SIN[code];
        buf[marker + 1] = (byte) code;
    }

    /** Same as Code.Decode, IN PLACE, reading the key back from buf. */
    public static void decrypt(byte[] buf, int start, int length, int marker) {
        int[] table = unscrambleTable(buf[marker] & 0xFF);
        int key = buf[marker + 1] & 0xFF;
        for (int i = start; i < start + length; i++) {
            buf[i] = (byte) unscrambleByte(buf[i] & 0xFF, key, table);
        }
    }

    /** Substitution table used for a given counter value. */
    private static int[] scrambleTable(int code) {
        return CipherTables.PASSWORD[CipherTables.SIN[code] % TABLE_COUNT];
    }

    /** Inverse table, found from the SIN value written in the frame. */
    private static int[] unscrambleTable(int sinValue) {
        return CipherTables.DECODE[sinValue % TABLE_COUNT];
    }

    /** Shift the value by the counter, then substitute it. */
    private static int scrambleByte(int value, int code, int[] table) {
        return table[(value + code) & 0xFF];
    }

    /** Substitute back, then remove the counter shift. */
    private static int unscrambleByte(int value, int key, int[] table) {
        return (table[value] - key) & 0xFF;
    }
}
