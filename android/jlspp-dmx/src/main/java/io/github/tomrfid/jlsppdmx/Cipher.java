package io.github.tomrfid.jlsppdmx;

/**
 * Brouillage JL_SPP (portage de {@code Code.java}, appli Android RY-AI).
 * {@code table = PASSWORD[SIN[code] % 5]} ; {@code sortie = table[(octet + code) % 256]}.
 * Les tables ({@link CipherTables}) sont generees depuis spec/cipher_tables.json.
 */
public final class Cipher {
    private Cipher() {}

    /** Equivalent de Code.Encryption1, EN PLACE ; ecrit la cle en buf[marker] et buf[marker + 1]. */
    public static void encrypt(byte[] buf, int start, int length, int codeNum, int marker) {
        int code = codeNum & 0xFF;
        int[] table = CipherTables.PASSWORD[CipherTables.SIN[code] % 5];
        for (int i = start; i < start + length; i++) {
            buf[i] = (byte) table[((buf[i] & 0xFF) + code) & 0xFF];
        }
        buf[marker] = (byte) CipherTables.SIN[code];
        buf[marker + 1] = (byte) code;
    }

    /** Equivalent de Code.Decode, EN PLACE, en relisant la cle ecrite dans buf. */
    public static void decrypt(byte[] buf, int start, int length, int marker) {
        int[] table = CipherTables.DECODE[(buf[marker] & 0xFF) % 5];
        int key = buf[marker + 1] & 0xFF;
        for (int i = start; i < start + length; i++) {
            buf[i] = (byte) ((table[buf[i] & 0xFF] - key) & 0xFF);
        }
    }
}
