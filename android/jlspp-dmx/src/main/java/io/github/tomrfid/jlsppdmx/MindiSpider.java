package io.github.tomrfid.jlsppdmx;

/**
 * Messagerie DMX du Mindi Mini Spider 8x3W RGBW (mode 15 canaux), voir
 * docs/fixtures/mindi-mini-spider.md.
 *
 * BIZARRERIE CONSTATEE : regle sur l'adresse N, le Spider ignore le canal N et ecoute a
 * partir de N+1 ; avec addressQuirk = true (defaut), on donne l'adresse AFFICHEE.
 */
public final class MindiSpider {
    public static final int MOTOR_1 = 1;       // position aile 1 : 0..255 = 0..135 degres
    public static final int MOTOR_2 = 2;       // position aile 2
    public static final int DIMMER = 3;        // dimmer general
    public static final int STROBE = 4;        // 0 = pas de strobe
    public static final int LED_1 = 5;         // LED 1..8 = canaux 5..12 (couleur supposee R,V,B,Blanc x2)
    public static final int MACRO = 13;        // programmes integres
    public static final int EFFECT_SPEED = 14; // vitesse des effets
    public static final int RESET = 15;        // laisser a 0

    private final int address;
    private final boolean addressQuirk;

    public MindiSpider(int address) {
        this(address, true);
    }

    public MindiSpider(int address, boolean addressQuirk) {
        if (address < 1 || address > 512) {
            throw new IllegalArgumentException("Adresse DMX 1..512");
        }
        this.address = address;
        this.addressQuirk = addressQuirk;
    }

    /** Numero de canal DMX absolu (1..512) d'une fonction du Spider (1..15). */
    public int dmxChannel(int spiderChannel) {
        return address + spiderChannel - 1 + (addressQuirk ? 1 : 0);
    }

    private void set(byte[] universe, int spiderChannel, int value) {
        universe[dmxChannel(spiderChannel) - 1] = (byte) Math.max(0, Math.min(255, value));
    }

    public void setDimmer(byte[] universe, int level) {
        set(universe, DIMMER, level);
    }

    /** 0 = pas de strobe. */
    public void setStrobe(byte[] universe, int speed) {
        set(universe, STROBE, speed);
    }

    /** led : 1..8. */
    public void setLed(byte[] universe, int led, int level) {
        if (led < 1 || led > 8) {
            throw new IllegalArgumentException("LED 1 a 8");
        }
        set(universe, LED_1 + led - 1, level);
    }

    /** mirror : l'aile 2 prend la position symetrique (255 - position). */
    public void setWings(byte[] universe, int position, boolean mirror) {
        int p = Math.max(0, Math.min(255, position));
        set(universe, MOTOR_1, p);
        set(universe, MOTOR_2, mirror ? 255 - p : p);
    }
}
