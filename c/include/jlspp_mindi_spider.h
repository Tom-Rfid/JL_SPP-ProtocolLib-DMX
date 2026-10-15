/*
 * jlspp_mindi_spider.h - DMX messages of the Mindi Mini Spider 8x3W RGBW (15-channel mode).
 * See docs/fixtures/mindi-mini-spider.md.
 *
 * ADDRESS QUIRK (observed on the fixture): when set to address N, the Spider ignores
 * channel N and listens from N+1. jlspp_spider_init() applies that shift: give it the
 * address SHOWN on the fixture. Set quirk_offset to 0 for a unit that behaves normally.
 *
 *     jlspp_spider spider;
 *     jlspp_spider_init(&spider, 1);
 *     jlspp_spider_set_dimmer(&spider, universe, 255);
 *     jlspp_spider_set_wings(&spider, universe, 200, 1);
 */
#ifndef JLSPP_MINDI_SPIDER_H
#define JLSPP_MINDI_SPIDER_H

#include <stdint.h>

#include "jlspp_dmx.h"

#ifdef __cplusplus
extern "C" {
#endif

#define JLSPP_SPIDER_CHANNEL_COUNT 15
#define JLSPP_SPIDER_LED_COUNT     8

/* Channels of the Spider (1..15), from its manual. */
typedef enum {
    JLSPP_SPIDER_MOTOR_1 = 1,       /* wing 1 position: 0..255 = 0..135 degrees */
    JLSPP_SPIDER_MOTOR_2 = 2,       /* wing 2 position */
    JLSPP_SPIDER_DIMMER = 3,        /* master dimmer */
    JLSPP_SPIDER_STROBE = 4,        /* 0 = no strobe, then flash speed */
    JLSPP_SPIDER_LED_1 = 5,         /* LED 1..8 = channels 5..12 (color ASSUMED: R, G, B, W twice) */
    JLSPP_SPIDER_MACRO = 13,        /* built-in effect programs */
    JLSPP_SPIDER_EFFECT_SPEED = 14, /* effect speed, slow -> fast */
    JLSPP_SPIDER_RESET = 15         /* keep at 0 */
} jlspp_spider_channel;

/* One Spider in the universe. */
typedef struct {
    int address;      /* address shown on the fixture */
    int quirk_offset; /* 1 = ignores its first channel (observed on our unit), 0 = normal */
} jlspp_spider;

/* Fills `spider` (quirk_offset = 1). JLSPP_ERROR if the 16 channels do not fit. */
int jlspp_spider_init(jlspp_spider *spider, int address);

/* Absolute DMX channel (1..512) of a Spider channel. */
int jlspp_spider_dmx_channel(const jlspp_spider *spider, int spider_channel);

/* Writes one Spider channel (1..15) into the universe. */
void jlspp_spider_set(const jlspp_spider *spider, uint8_t *universe, int spider_channel, uint8_t value);

/* Master dimmer. Must be open, otherwise the LEDs stay dark. */
void jlspp_spider_set_dimmer(const jlspp_spider *spider, uint8_t *universe, uint8_t level);

/* Strobe speed; 0 = no strobe. */
void jlspp_spider_set_strobe(const jlspp_spider *spider, uint8_t *universe, uint8_t speed);

/* Intensity of one LED (1..8). JLSPP_ERROR if led is out of range. */
int jlspp_spider_set_led(const jlspp_spider *spider, uint8_t *universe, int led, uint8_t level);

/* Both wings. mirror != 0: wing 2 takes the symmetric position (255 - position), so the
 * wings start from opposite sides and meet in the middle. */
void jlspp_spider_set_wings(const jlspp_spider *spider, uint8_t *universe, uint8_t position, int mirror);

#ifdef __cplusplus
}
#endif

#endif /* JLSPP_MINDI_SPIDER_H */
