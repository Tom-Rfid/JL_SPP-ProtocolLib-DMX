package io.github.tomrfid.jlsppdmx;

import java.util.Arrays;

/**
 * JL_SPP DMX frames (521 bytes) and handshakes.
 * Convention: a universe is 512 bytes, index 0 = DMX channel 1.
 *
 * <pre>
 * [0]        0x00
 * [1][2]     'K' 'T'        start marker (clear)
 * [3]        scene          0 = direct control
 * [4]        speed          0 in direct control
 * [5..516]   512 channels   scrambled (channel 1 -> byte 5)
 * [517]      SIN[code]      ) key
 * [518]      code           )
 * [519][520] 'T' 'K'        end marker (clear)
 * </pre>
 */
public final class DmxFrame {
    /** Bytes in one DMX frame. */
    public static final int FRAME_LENGTH = 521;
    /** DMX channels in one universe. */
    public static final int UNIVERSE_SIZE = 512;
    /** Frame byte holding DMX channel 1. */
    public static final int PAYLOAD_START = 5;
    /** Frame bytes 517 and 518 hold the key. */
    public static final int MARKER_OFFSET = 517;
    /** Sending rate of the original app: one frame every 100 ms. */
    public static final int DEFAULT_SEND_INTERVAL_MS = 100;

    private static final int END_MARKER_OFFSET = 519;

    private DmxFrame() {}

    /** To send right after connecting. */
    public static byte[] handshakeConnect() {
        return new byte[] {(byte) 0xBB, (byte) 0x99, 0x77, 0x01, 0x77, (byte) 0x99};
    }

    /** To send right before disconnecting. */
    public static byte[] handshakeDisconnect() {
        return new byte[] {(byte) 0xBB, 0x77, (byte) 0x99, 0x10, (byte) 0x99, 0x77, 0x00, 0x55};
    }

    /** Builds a complete frame for direct control (scene = 0, speed = 0). */
    public static byte[] build(byte[] universe, int codeNum) {
        return build(universe, codeNum, 0, 0);
    }

    /**
     * Builds a complete frame, ready to be written to the socket.
     *
     * @param universe 512 bytes, index 0 = DMX channel 1
     * @param codeNum  counter 0..255, normally incremented for every frame
     * @param scene    byte 3 (0 = direct control)
     * @param speed    byte 4 (0 in direct control)
     */
    public static byte[] build(byte[] universe, int codeNum, int scene, int speed) {
        checkUniverse(universe);
        byte[] frame = buildClearFrame(universe, scene, speed);
        Cipher.encrypt(frame, PAYLOAD_START, UNIVERSE_SIZE, codeNum, MARKER_OFFSET);
        return frame;
    }

    /** True if the frame has the right length and the KT / TK markers. */
    public static boolean isFrame(byte[] frame) {
        return frame != null && frame.length == FRAME_LENGTH
                && frame[1] == 'K' && frame[2] == 'T'
                && frame[END_MARKER_OFFSET] == 'T' && frame[END_MARKER_OFFSET + 1] == 'K';
    }

    /** Gets the clear universe (512 bytes) back from a frame. */
    public static byte[] decodeUniverse(byte[] frame) {
        if (!isFrame(frame)) {
            throw new IllegalArgumentException("Not a valid JL_SPP DMX frame");
        }
        byte[] copy = Arrays.copyOf(frame, FRAME_LENGTH);
        Cipher.decrypt(copy, PAYLOAD_START, UNIVERSE_SIZE, MARKER_OFFSET);
        return Arrays.copyOfRange(copy, PAYLOAD_START, PAYLOAD_START + UNIVERSE_SIZE);
    }

    /** Counter written in the frame (0..255). */
    public static int codeNumOf(byte[] frame) {
        return frame[MARKER_OFFSET + 1] & 0xFF;
    }

    /** Throws unless the universe has exactly 512 bytes. */
    static void checkUniverse(byte[] universe) {
        if (universe == null || universe.length != UNIVERSE_SIZE) {
            throw new IllegalArgumentException("A universe must hold " + UNIVERSE_SIZE + " bytes");
        }
    }

    /** Frame whose channels are still in clear (before scrambling). */
    private static byte[] buildClearFrame(byte[] universe, int scene, int speed) {
        byte[] frame = new byte[FRAME_LENGTH];
        frame[1] = 'K';
        frame[2] = 'T';
        frame[3] = (byte) scene;
        frame[4] = (byte) speed;
        System.arraycopy(universe, 0, frame, PAYLOAD_START, UNIVERSE_SIZE);
        frame[END_MARKER_OFFSET] = 'T';
        frame[END_MARKER_OFFSET + 1] = 'K';
        return frame;
    }
}
