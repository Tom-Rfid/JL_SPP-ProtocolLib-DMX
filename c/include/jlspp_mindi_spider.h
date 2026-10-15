/*
 * jlspp_mindi_spider.h - messagerie DMX du Mindi Mini Spider 8x3W RGBW (15 canaux).
 * Voir docs/fixtures/mindi-mini-spider.md.
 *
 * BIZARRERIE CONSTATEE : regle sur l'adresse N, le Spider ignore le canal N et ecoute
 * a partir de N+1. JLSPP_SPIDER_QUIRK_OFFSET vaut 1 ; mettre 0 si un autre exemplaire
 * se comporte normalement.
 */
#ifndef JLSPP_MINDI_SPIDER_H
#define JLSPP_MINDI_SPIDER_H

#include <stdint.h>

#define JLSPP_SPIDER_QUIRK_OFFSET 1

/* Canaux du Spider (1..15), d'apres la notice. */
enum jlspp_spider_channel {
    JLSPP_SPIDER_MOTOR_1 = 1,      /* position aile 1 : 0..255 = 0..135 degres */
    JLSPP_SPIDER_MOTOR_2 = 2,      /* position aile 2 */
    JLSPP_SPIDER_DIMMER = 3,       /* dimmer general */
    JLSPP_SPIDER_STROBE = 4,       /* 0 = pas de strobe, puis vitesse */
    JLSPP_SPIDER_LED_1 = 5,        /* LED 1..8 = canaux 5..12 (couleur supposee R,V,B,Blanc x2) */
    JLSPP_SPIDER_MACRO = 13,       /* programmes integres */
    JLSPP_SPIDER_EFFECT_SPEED = 14,
    JLSPP_SPIDER_RESET = 15        /* laisser a 0 */
};

/* Index dans l'univers (0 = canal 1) d'une fonction du Spider dont l'adresse AFFICHEE est address. */
static inline int jlspp_spider_index(int address, int channel)
{
    return address - 1 + channel - 1 + JLSPP_SPIDER_QUIRK_OFFSET;
}

/* Ailes : mirror != 0 -> l'aile 2 prend la position symetrique (255 - position). */
static inline void jlspp_spider_set_wings(uint8_t *universe, int address, uint8_t position, int mirror)
{
    universe[jlspp_spider_index(address, JLSPP_SPIDER_MOTOR_1)] = position;
    universe[jlspp_spider_index(address, JLSPP_SPIDER_MOTOR_2)] = mirror ? (uint8_t)(255 - position) : position;
}

/* led : 1..8 */
static inline void jlspp_spider_set_led(uint8_t *universe, int address, int led, uint8_t level)
{
    universe[jlspp_spider_index(address, JLSPP_SPIDER_LED_1 + led - 1)] = level;
}

#endif /* JLSPP_MINDI_SPIDER_H */
