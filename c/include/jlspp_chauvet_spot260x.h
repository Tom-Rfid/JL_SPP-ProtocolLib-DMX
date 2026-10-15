/*
 * jlspp_chauvet_spot260x.h - DMX messages of the Chauvet DJ Intimidator Spot 260X.
 * Source: Intimidator Spot 260X Quick Reference Guide Rev. 1 (Chauvet).
 * See docs/fixtures/chauvet-intimidator-spot-260x.md.
 *
 * The fixture has two DMX modes, chosen in its menu (Run Mode > DMX):
 *   14 channels: everything, with 16-bit pan/tilt and a dimmer
 *    8 channels: pan, tilt, color, gobo, gobo rotation, prism, focus, shutter
 *
 *     jlspp_spot260x spot;
 *     jlspp_spot260x_init(&spot, 17, JLSPP_SPOT260X_MODE_14CH);
 *     jlspp_spot260x_light_on(&spot, universe, 255);
 *     jlspp_spot260x_set_pan_degrees(&spot, universe, 270.0);
 *     jlspp_spot260x_set_color(&spot, universe, JLSPP_SPOT260X_RED);
 *
 * Functions returning int give JLSPP_OK, or JLSPP_ERROR when the current mode lacks
 * the function (no dimmer in 8-channel mode...) or an argument is out of range.
 * "speed" arguments are always 0 = slowest, 255 = fastest.
 */
#ifndef JLSPP_CHAUVET_SPOT260X_H
#define JLSPP_CHAUVET_SPOT260X_H

#include <stdint.h>

#include "jlspp_dmx.h"

#ifdef __cplusplus
extern "C" {
#endif

#define JLSPP_SPOT260X_PAN_RANGE_DEGREES  540.0 /* menu "Pan Angle" default */
#define JLSPP_SPOT260X_TILT_RANGE_DEGREES 234.0 /* menu "Tilt Angle" default */

/* DMX mode chosen in the fixture menu. The value is the number of channels. */
typedef enum {
    JLSPP_SPOT260X_MODE_8CH = 8,
    JLSPP_SPOT260X_MODE_14CH = 14
} jlspp_spot260x_mode;

/* Everything the fixture can do over DMX. */
typedef enum {
    JLSPP_SPOT260X_PAN,
    JLSPP_SPOT260X_PAN_FINE,
    JLSPP_SPOT260X_TILT,
    JLSPP_SPOT260X_TILT_FINE,
    JLSPP_SPOT260X_PAN_TILT_SPEED,
    JLSPP_SPOT260X_COLOR_WHEEL,
    JLSPP_SPOT260X_GOBO_WHEEL,
    JLSPP_SPOT260X_GOBO_ROTATION,
    JLSPP_SPOT260X_PRISM,
    JLSPP_SPOT260X_FOCUS,
    JLSPP_SPOT260X_DIMMER,
    JLSPP_SPOT260X_SHUTTER,
    JLSPP_SPOT260X_CONTROL,
    JLSPP_SPOT260X_MOVEMENT_MACRO,
    JLSPP_SPOT260X_FUNCTION_COUNT
} jlspp_spot260x_function;

/* Color wheel slots. The value is the middle of the slot range. */
typedef enum {
    JLSPP_SPOT260X_WHITE = 3,    /* 0..6 */
    JLSPP_SPOT260X_RED = 10,     /* 7..13 */
    JLSPP_SPOT260X_ORANGE = 17,  /* 14..20 */
    JLSPP_SPOT260X_YELLOW = 24,  /* 21..27 */
    JLSPP_SPOT260X_GREEN = 31,   /* 28..34 */
    JLSPP_SPOT260X_BLUE = 38,    /* 35..41 */
    JLSPP_SPOT260X_CTO = 45,     /* 42..48, warm white filter */
    JLSPP_SPOT260X_CYAN = 52,    /* 49..55 */
    JLSPP_SPOT260X_MAGENTA = 59  /* 56..62 */
} jlspp_spot260x_color;

/* Gobo wheel slots. The value is the middle of the slot range. */
typedef enum {
    JLSPP_SPOT260X_GOBO_OPEN = 3, /* 0..7, no gobo */
    JLSPP_SPOT260X_GOBO_1 = 11,   /* 8..15 */
    JLSPP_SPOT260X_GOBO_2 = 19,   /* 16..23 */
    JLSPP_SPOT260X_GOBO_3 = 27,   /* 24..31 */
    JLSPP_SPOT260X_GOBO_4 = 35,   /* 32..39 */
    JLSPP_SPOT260X_GOBO_5 = 43,   /* 40..47 */
    JLSPP_SPOT260X_GOBO_6 = 51,   /* 48..55 */
    JLSPP_SPOT260X_GOBO_7 = 59    /* 56..63 */
} jlspp_spot260x_gobo;

/* Gobo rotation direction. */
typedef enum {
    JLSPP_SPOT260X_ROTATION_NONE,
    JLSPP_SPOT260X_ROTATION_CLOCKWISE,         /* 8..119 */
    JLSPP_SPOT260X_ROTATION_COUNTER_CLOCKWISE, /* 120..231 */
    JLSPP_SPOT260X_ROTATION_BOUNCE             /* 232..255 */
} jlspp_spot260x_rotation;

/* Kinds of strobe on the shutter channel. */
typedef enum {
    JLSPP_SPOT260X_STROBE_NORMAL, /* 8..76 */
    JLSPP_SPOT260X_STROBE_PULSE,  /* 77..145 */
    JLSPP_SPOT260X_STROBE_RANDOM  /* 146..215 */
} jlspp_spot260x_strobe;

/* Resets on the control channel (14-channel mode only). */
typedef enum {
    JLSPP_SPOT260X_RESET_PAN = 99,          /* 96..103 */
    JLSPP_SPOT260X_RESET_TILT = 107,        /* 104..111 */
    JLSPP_SPOT260X_RESET_COLOR_WHEEL = 115, /* 112..119 */
    JLSPP_SPOT260X_RESET_GOBO_WHEEL = 123,  /* 120..127 */
    JLSPP_SPOT260X_RESET_PRISM = 139,       /* 136..143 */
    JLSPP_SPOT260X_RESET_FOCUS = 147,       /* 144..151 */
    JLSPP_SPOT260X_RESET_ALL = 155          /* 152..159 */
} jlspp_spot260x_reset_target;

/* Beam blacked out while something moves (control channel, 14-channel mode only). */
typedef enum {
    JLSPP_SPOT260X_BLACKOUT_NONE = 0,            /* 0..7 */
    JLSPP_SPOT260X_BLACKOUT_PAN_TILT = 11,       /* 8..15 */
    JLSPP_SPOT260X_BLACKOUT_COLOR_WHEEL = 19,    /* 16..23 */
    JLSPP_SPOT260X_BLACKOUT_GOBO_WHEEL = 27,     /* 24..31 */
    JLSPP_SPOT260X_BLACKOUT_PAN_TILT_COLOR = 35, /* 32..39 */
    JLSPP_SPOT260X_BLACKOUT_PAN_TILT_GOBO = 43,  /* 40..47 */
    JLSPP_SPOT260X_BLACKOUT_ALL = 51             /* 48..55 */
} jlspp_spot260x_blackout_option;

/* One Intimidator Spot 260X in the universe. */
typedef struct {
    int address;              /* DMX address set in the fixture menu */
    jlspp_spot260x_mode mode; /* DMX mode set in the fixture menu */
} jlspp_spot260x;

/* ------------------------------------------------------------------------- channels */

/* Fills `spot`. JLSPP_ERROR if the fixture does not fit at that address. */
int jlspp_spot260x_init(jlspp_spot260x *spot, int address, jlspp_spot260x_mode mode);

/* Channel of a function relative to the fixture (1..14), or 0 if the mode lacks it. */
int jlspp_spot260x_relative_channel(jlspp_spot260x_mode mode, jlspp_spot260x_function function);

/* 1 if the current mode has this function. */
int jlspp_spot260x_has(const jlspp_spot260x *spot, jlspp_spot260x_function function);

/* Absolute DMX channel (1..512) of a function, or 0 if the mode lacks it. */
int jlspp_spot260x_dmx_channel(const jlspp_spot260x *spot, jlspp_spot260x_function function);

/* Writes the raw value of one function into the universe. */
int jlspp_spot260x_set(const jlspp_spot260x *spot, uint8_t *universe,
                       jlspp_spot260x_function function, int value);

/* Centered head, sharp focus, shutter open, everything else at 0. */
void jlspp_spot260x_apply_defaults(const jlspp_spot260x *spot, uint8_t *universe);

/* ------------------------------------------------------------------------- movement */

/* Pan / tilt as 16-bit positions 0..65535 (0x8000 = middle). Fine byte dropped in 8-channel mode. */
void jlspp_spot260x_set_pan(const jlspp_spot260x *spot, uint8_t *universe, uint16_t position);
void jlspp_spot260x_set_tilt(const jlspp_spot260x *spot, uint8_t *universe, uint16_t position);

/* Pan 0..540 degrees / tilt 0..234 degrees (menu default angle ranges). */
void jlspp_spot260x_set_pan_degrees(const jlspp_spot260x *spot, uint8_t *universe, double degrees);
void jlspp_spot260x_set_tilt_degrees(const jlspp_spot260x *spot, uint8_t *universe, double degrees);

/* Movement speed, FIXTURE convention: 0 = fastest, 255 = slowest. 14-channel mode only. */
int jlspp_spot260x_set_pan_tilt_speed(const jlspp_spot260x *spot, uint8_t *universe, uint8_t value);

/* Built-in movement macro 1..8 (sound_active != 0: its sound-active version). 14-channel mode only. */
int jlspp_spot260x_set_movement_macro(const jlspp_spot260x *spot, uint8_t *universe, int number, int sound_active);
int jlspp_spot260x_stop_movement_macro(const jlspp_spot260x *spot, uint8_t *universe);

/* ---------------------------------------------------------------------------- color */

void jlspp_spot260x_set_color(const jlspp_spot260x *spot, uint8_t *universe, jlspp_spot260x_color color);

/* Continuous wheel position 0..255 (stops between two colors). */
void jlspp_spot260x_set_color_wheel_position(const jlspp_spot260x *spot, uint8_t *universe, uint8_t position);

/* Turns the color wheel continuously. */
void jlspp_spot260x_set_color_rainbow(const jlspp_spot260x *spot, uint8_t *universe, uint8_t speed, int reverse);
void jlspp_spot260x_stop_color_rainbow(const jlspp_spot260x *spot, uint8_t *universe);

/* ----------------------------------------------------------------------------- gobo */

void jlspp_spot260x_set_gobo(const jlspp_spot260x *spot, uint8_t *universe, jlspp_spot260x_gobo gobo);

/* Shakes gobo 1..7. */
int jlspp_spot260x_set_gobo_shake(const jlspp_spot260x *spot, uint8_t *universe, int gobo, uint8_t speed);

/* Turns the gobo wheel continuously. */
void jlspp_spot260x_set_gobo_cycle(const jlspp_spot260x *spot, uint8_t *universe, uint8_t speed, int reverse);
void jlspp_spot260x_stop_gobo_cycle(const jlspp_spot260x *spot, uint8_t *universe);

/* Rotates the gobo itself. */
void jlspp_spot260x_set_gobo_rotation(const jlspp_spot260x *spot, uint8_t *universe,
                                      jlspp_spot260x_rotation rotation, uint8_t speed);

/* -------------------------------------------------------------------- prism / focus */

void jlspp_spot260x_set_prism(const jlspp_spot260x *spot, uint8_t *universe, int on);
void jlspp_spot260x_set_focus(const jlspp_spot260x *spot, uint8_t *universe, uint8_t value);

/* ----------------------------------------------------------------- dimmer / shutter */

/* Dimmer 0..255. 14-channel mode only. */
int jlspp_spot260x_set_dimmer(const jlspp_spot260x *spot, uint8_t *universe, uint8_t level);

void jlspp_spot260x_open_shutter(const jlspp_spot260x *spot, uint8_t *universe);
void jlspp_spot260x_close_shutter(const jlspp_spot260x *spot, uint8_t *universe);
void jlspp_spot260x_set_strobe(const jlspp_spot260x *spot, uint8_t *universe, uint8_t speed,
                               jlspp_spot260x_strobe effect);

/* Light on: dimmer at `level` (14-channel mode) + shutter open. Blackout: the opposite. */
void jlspp_spot260x_light_on(const jlspp_spot260x *spot, uint8_t *universe, uint8_t level);
void jlspp_spot260x_blackout(const jlspp_spot260x *spot, uint8_t *universe);

/* -------------------------------------------------------------------------- control */

int jlspp_spot260x_set_blackout_on_move(const jlspp_spot260x *spot, uint8_t *universe,
                                        jlspp_spot260x_blackout_option option);

/* Starts a reset; call jlspp_spot260x_clear_control() a few seconds later. */
int jlspp_spot260x_reset(const jlspp_spot260x *spot, uint8_t *universe, jlspp_spot260x_reset_target target);
int jlspp_spot260x_clear_control(const jlspp_spot260x *spot, uint8_t *universe);

#ifdef __cplusplus
}
#endif

#endif /* JLSPP_CHAUVET_SPOT260X_H */
