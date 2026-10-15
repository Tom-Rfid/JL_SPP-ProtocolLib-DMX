package io.github.tomrfid.jlsppdmx;

import java.util.Arrays;

/**
 * Trames DMX JL_SPP (521 octets) et poignees de main.
 * Convention : un univers = 512 octets, index 0 = canal DMX 1.
 *
 * <pre>
 * [0]        0x00
 * [1][2]     'K' 'T'        marqueurs de debut (en clair)
 * [3]        scene          0 = pilotage direct
 * [4]        vitesse        0 en pilotage direct
 * [5..516]   512 canaux     brouilles (canal 1 -> octet 5)
 * [517]      SIN[code]      ) cle
 * [518]      code           )
 * [519][520] 'T' 'K'        marqueurs de fin (en clair)
 * </pre>
 */
public final class DmxFrame {
    public static final int FRAME_LENGTH = 521;
    public static final int UNIVERSE_SIZE = 512;
    public static final int PAYLOAD_START = 5;
    public static final int MARKER_OFFSET = 517;
    /** Cadence de l'appli d'origine : une trame toutes les 100 ms. */
    public static final int DEFAULT_SEND_INTERVAL_MS = 100;

    private DmxFrame() {}

    /** A envoyer juste apres la connexion. */
    public static byte[] handshakeConnect() {
        return new byte[] {(byte) 0xBB, (byte) 0x99, 0x77, 0x01, 0x77, (byte) 0x99};
    }

    /** A envoyer juste avant la deconnexion. */
    public static byte[] handshakeDisconnect() {
        return new byte[] {(byte) 0xBB, 0x77, (byte) 0x99, 0x10, (byte) 0x99, 0x77, 0x00, 0x55};
    }

    /** Construit une trame complete (pilotage direct : scene = 0, vitesse = 0). */
    public static byte[] build(byte[] universe, int codeNum) {
        return build(universe, codeNum, 0, 0);
    }

    public static byte[] build(byte[] universe, int codeNum, int scene, int speed) {
        if (universe == null || universe.length != UNIVERSE_SIZE) {
            throw new IllegalArgumentException("L'univers doit faire " + UNIVERSE_SIZE + " octets");
        }
        byte[] frame = new byte[FRAME_LENGTH];
        frame[1] = 'K';
        frame[2] = 'T';
        frame[3] = (byte) scene;
        frame[4] = (byte) speed;
        System.arraycopy(universe, 0, frame, PAYLOAD_START, UNIVERSE_SIZE);
        frame[519] = 'T';
        frame[520] = 'K';
        Cipher.encrypt(frame, PAYLOAD_START, UNIVERSE_SIZE, codeNum, MARKER_OFFSET);
        return frame;
    }

    /** true si la trame a la bonne longueur et les marqueurs KT / TK. */
    public static boolean isFrame(byte[] frame) {
        return frame != null && frame.length == FRAME_LENGTH
                && frame[1] == 'K' && frame[2] == 'T' && frame[519] == 'T' && frame[520] == 'K';
    }

    /** Retrouve l'univers (512 octets) d'une trame. */
    public static byte[] decodeUniverse(byte[] frame) {
        if (!isFrame(frame)) {
            throw new IllegalArgumentException("Ce n'est pas une trame DMX JL_SPP valide");
        }
        byte[] copy = Arrays.copyOf(frame, FRAME_LENGTH);
        Cipher.decrypt(copy, PAYLOAD_START, UNIVERSE_SIZE, MARKER_OFFSET);
        return Arrays.copyOfRange(copy, PAYLOAD_START, PAYLOAD_START + UNIVERSE_SIZE);
    }

    /** Compteur ecrit dans la trame (0..255). */
    public static int codeNumOf(byte[] frame) {
        return frame[MARKER_OFFSET + 1] & 0xFF;
    }
}
