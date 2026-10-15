/*
 * jlspp_chauvet_spot260x.c - DMX messages of the Chauvet Intimidator Spot 260X
 * (see jlspp_chauvet_spot260x.h and docs/fixtures/chauvet-intimidator-spot-260x.md).
 */
#include "jlspp_chauvet_spot260x.h"

#include "jlspp_fixture_util.h"

/* ------------------------------------------------------------------- chart ranges */

#define COLOR_INDEXING_LOW         65  /* continuous wheel position: 65..189 */
#define COLOR_INDEXING_HIGH        189
#define COLOR_RAINBOW_LOW          190 /* rainbow: 190 = fast .. 221 = slow */
#define COLOR_RAINBOW_HIGH         221
#define COLOR_RAINBOW_STOP         222
#define COLOR_RAINBOW_REVERSE_LOW  224 /* reverse rainbow: slow .. fast */
#define COLOR_RAINBOW_REVERSE_HIGH 255

#define GOBO_SHAKE_FIRST           64  /* gobo 7 shake = 64..71, ..., gobo 1 shake = 112..119 */
#define GOBO_SHAKE_WIDTH           8
#define GOBO_CYCLE_LOW             128 /* cycle effect, slow to fast */
#define GOBO_CYCLE_HIGH            189
#define GOBO_CYCLE_STOP            191
#define GOBO_CYCLE_REVERSE_LOW     194
#define GOBO_CYCLE_REVERSE_HIGH    255

#define PRISM_OFF                  0   /* 0..15 */
#define PRISM_ON                   255 /* 16..255: 3-facet prism */

#define SHUTTER_CLOSED             0   /* 0..3: no light */
#define SHUTTER_OPEN               255 /* 216..255 */

#define MACRO_COUNT                8
#define MOVEMENT_MACRO_FIRST       8   /* macro 1 = 8..23, macro 2 = 24..39... */
#define SOUND_MACRO_FIRST          136 /* sound-active macro 1 = 136..151... */
#define MACRO_WIDTH                16

/* low..high DMX range of a "slow to fast" effect */
typedef struct {
    int low;
    int high;
} dmx_range;

static const dmx_range ROTATION_RANGES[] = {
    {0, 0},       /* JLSPP_SPOT260X_ROTATION_NONE */
    {8, 119},     /* JLSPP_SPOT260X_ROTATION_CLOCKWISE */
    {120, 231},   /* JLSPP_SPOT260X_ROTATION_COUNTER_CLOCKWISE */
    {232, 255},   /* JLSPP_SPOT260X_ROTATION_BOUNCE */
};

static const dmx_range STROBE_RANGES[] = {
    {8, 76},      /* JLSPP_SPOT260X_STROBE_NORMAL */
    {77, 145},    /* JLSPP_SPOT260X_STROBE_PULSE */
    {146, 215},   /* JLSPP_SPOT260X_STROBE_RANDOM */
};

/* Channel (1-based, relative to the address) of each function, per mode. 0 = absent. */
static const uint8_t CHANNELS_14CH[JLSPP_SPOT260X_FUNCTION_COUNT] = {
    1,  /* pan */
    2,  /* pan fine */
    3,  /* tilt */
    4,  /* tilt fine */
    5,  /* pan/tilt speed */
    6,  /* color wheel */
    7,  /* gobo wheel */
    8,  /* gobo rotation */
    9,  /* prism */
    10, /* focus */
    11, /* dimmer */
    12, /* shutter */
    13, /* control */
    14, /* movement macros */
};

static const uint8_t CHANNELS_8CH[JLSPP_SPOT260X_FUNCTION_COUNT] = {
    1, /* pan */
    0, /* pan fine: absent */
    2, /* tilt */
    0, /* tilt fine: absent */
    0, /* pan/tilt speed: absent */
    3, /* color wheel */
    4, /* gobo wheel */
    5, /* gobo rotation */
    6, /* prism */
    7, /* focus */
    0, /* dimmer: absent */
    8, /* shutter */
    0, /* control: absent */
    0, /* movement macros: absent */
};

/* ------------------------------------------------------------------------ channels */

int jlspp_spot260x_init(jlspp_spot260x *spot, int address, jlspp_spot260x_mode mode)
{
    spot->address = address;
    spot->mode = mode;
    if (mode != JLSPP_SPOT260X_MODE_8CH && mode != JLSPP_SPOT260X_MODE_14CH) {
        return JLSPP_ERROR;
    }
    return jlspp_address_fits(address, (int)mode) ? JLSPP_OK : JLSPP_ERROR;
}

int jlspp_spot260x_relative_channel(jlspp_spot260x_mode mode, jlspp_spot260x_function function)
{
    if ((int)function < 0 || function >= JLSPP_SPOT260X_FUNCTION_COUNT) {
        return 0;
    }
    return mode == JLSPP_SPOT260X_MODE_8CH ? CHANNELS_8CH[function] : CHANNELS_14CH[function];
}

int jlspp_spot260x_has(const jlspp_spot260x *spot, jlspp_spot260x_function function)
{
    return jlspp_spot260x_relative_channel(spot->mode, function) != 0;
}

int jlspp_spot260x_dmx_channel(const jlspp_spot260x *spot, jlspp_spot260x_function function)
{
    int relative = jlspp_spot260x_relative_channel(spot->mode, function);
    return relative == 0 ? 0 : spot->address + relative - 1;
}

int jlspp_spot260x_set(const jlspp_spot260x *spot, uint8_t *universe,
                       jlspp_spot260x_function function, int value)
{
    int channel = jlspp_spot260x_dmx_channel(spot, function);
    if (channel == 0) {
        return JLSPP_ERROR;
    }
    universe[channel - 1] = jlspp_clamp_byte(value);
    return JLSPP_OK;
}

/* Value of a function when nothing is asked: centered head, sharp focus, shutter open. */
static int default_value(jlspp_spot260x_function function)
{
    switch (function) {
    case JLSPP_SPOT260X_PAN:
    case JLSPP_SPOT260X_TILT:
    case JLSPP_SPOT260X_FOCUS:
        return 128;
    case JLSPP_SPOT260X_SHUTTER:
        return SHUTTER_OPEN;
    default:
        return 0;
    }
}

void jlspp_spot260x_apply_defaults(const jlspp_spot260x *spot, uint8_t *universe)
{
    int f;
    for (f = 0; f < JLSPP_SPOT260X_FUNCTION_COUNT; f++) {
        /* functions absent from the mode are skipped by jlspp_spot260x_set */
        jlspp_spot260x_set(spot, universe, (jlspp_spot260x_function)f, default_value((jlspp_spot260x_function)f));
    }
}

/* ------------------------------------------------------------------------ movement */

/* Writes a 16-bit position: high byte on `coarse`, low byte on `fine` when the mode has it. */
static void set_16bit(const jlspp_spot260x *spot, uint8_t *universe, jlspp_spot260x_function coarse,
                      jlspp_spot260x_function fine, uint16_t position)
{
    jlspp_spot260x_set(spot, universe, coarse, position >> 8);
    jlspp_spot260x_set(spot, universe, fine, position & 0xFF); /* ignored in 8-channel mode */
}

/* Angle 0..full_range -> 16-bit position, rounded to the nearest step. */
static uint16_t degrees_to_16bit(double degrees, double full_range)
{
    if (degrees < 0.0) {
        degrees = 0.0;
    }
    if (degrees > full_range) {
        degrees = full_range;
    }
    return (uint16_t)(degrees * 65535.0 / full_range + 0.5);
}

void jlspp_spot260x_set_pan(const jlspp_spot260x *spot, uint8_t *universe, uint16_t position)
{
    set_16bit(spot, universe, JLSPP_SPOT260X_PAN, JLSPP_SPOT260X_PAN_FINE, position);
}

void jlspp_spot260x_set_tilt(const jlspp_spot260x *spot, uint8_t *universe, uint16_t position)
{
    set_16bit(spot, universe, JLSPP_SPOT260X_TILT, JLSPP_SPOT260X_TILT_FINE, position);
}

void jlspp_spot260x_set_pan_degrees(const jlspp_spot260x *spot, uint8_t *universe, double degrees)
{
    jlspp_spot260x_set_pan(spot, universe, degrees_to_16bit(degrees, JLSPP_SPOT260X_PAN_RANGE_DEGREES));
}

void jlspp_spot260x_set_tilt_degrees(const jlspp_spot260x *spot, uint8_t *universe, double degrees)
{
    jlspp_spot260x_set_tilt(spot, universe, degrees_to_16bit(degrees, JLSPP_SPOT260X_TILT_RANGE_DEGREES));
}

int jlspp_spot260x_set_pan_tilt_speed(const jlspp_spot260x *spot, uint8_t *universe, uint8_t value)
{
    return jlspp_spot260x_set(spot, universe, JLSPP_SPOT260X_PAN_TILT_SPEED, value);
}

int jlspp_spot260x_set_movement_macro(const jlspp_spot260x *spot, uint8_t *universe, int number, int sound_active)
{
    int low, high;

    if (number < 1 || number > MACRO_COUNT) {
        return JLSPP_ERROR;
    }
    low = (sound_active ? SOUND_MACRO_FIRST : MOVEMENT_MACRO_FIRST) + (number - 1) * MACRO_WIDTH;
    high = low + MACRO_WIDTH - 1;
    if (high > 255) {
        high = 255; /* the last sound-active macro is only 248..255 */
    }
    return jlspp_spot260x_set(spot, universe, JLSPP_SPOT260X_MOVEMENT_MACRO, jlspp_middle(low, high));
}

int jlspp_spot260x_stop_movement_macro(const jlspp_spot260x *spot, uint8_t *universe)
{
    return jlspp_spot260x_set(spot, universe, JLSPP_SPOT260X_MOVEMENT_MACRO, 0);
}

/* --------------------------------------------------------------------------- color */

void jlspp_spot260x_set_color(const jlspp_spot260x *spot, uint8_t *universe, jlspp_spot260x_color color)
{
    jlspp_spot260x_set(spot, universe, JLSPP_SPOT260X_COLOR_WHEEL, (int)color);
}

void jlspp_spot260x_set_color_wheel_position(const jlspp_spot260x *spot, uint8_t *universe, uint8_t position)
{
    jlspp_spot260x_set(spot, universe, JLSPP_SPOT260X_COLOR_WHEEL,
                       jlspp_scale_into_range(position, COLOR_INDEXING_LOW, COLOR_INDEXING_HIGH));
}

void jlspp_spot260x_set_color_rainbow(const jlspp_spot260x *spot, uint8_t *universe, uint8_t speed, int reverse)
{
    int value;

    if (reverse) {
        value = jlspp_scale_into_range(speed, COLOR_RAINBOW_REVERSE_LOW, COLOR_RAINBOW_REVERSE_HIGH);
    } else {
        /* this range goes from fast to slow: flip it so that 255 is always the fastest */
        int scaled = jlspp_scale_into_range(speed, COLOR_RAINBOW_LOW, COLOR_RAINBOW_HIGH);
        value = COLOR_RAINBOW_HIGH - (scaled - COLOR_RAINBOW_LOW);
    }
    jlspp_spot260x_set(spot, universe, JLSPP_SPOT260X_COLOR_WHEEL, value);
}

void jlspp_spot260x_stop_color_rainbow(const jlspp_spot260x *spot, uint8_t *universe)
{
    jlspp_spot260x_set(spot, universe, JLSPP_SPOT260X_COLOR_WHEEL, COLOR_RAINBOW_STOP);
}

/* ---------------------------------------------------------------------------- gobo */

void jlspp_spot260x_set_gobo(const jlspp_spot260x *spot, uint8_t *universe, jlspp_spot260x_gobo gobo)
{
    jlspp_spot260x_set(spot, universe, JLSPP_SPOT260X_GOBO_WHEEL, (int)gobo);
}

int jlspp_spot260x_set_gobo_shake(const jlspp_spot260x *spot, uint8_t *universe, int gobo, uint8_t speed)
{
    int low;

    if (gobo < 1 || gobo > 7) {
        return JLSPP_ERROR;
    }
    low = GOBO_SHAKE_FIRST + (7 - gobo) * GOBO_SHAKE_WIDTH; /* gobo 7 comes first on the wheel */
    return jlspp_spot260x_set(spot, universe, JLSPP_SPOT260X_GOBO_WHEEL,
                              jlspp_scale_into_range(speed, low, low + GOBO_SHAKE_WIDTH - 1));
}

void jlspp_spot260x_set_gobo_cycle(const jlspp_spot260x *spot, uint8_t *universe, uint8_t speed, int reverse)
{
    int value = reverse
        ? jlspp_scale_into_range(speed, GOBO_CYCLE_REVERSE_LOW, GOBO_CYCLE_REVERSE_HIGH)
        : jlspp_scale_into_range(speed, GOBO_CYCLE_LOW, GOBO_CYCLE_HIGH);
    jlspp_spot260x_set(spot, universe, JLSPP_SPOT260X_GOBO_WHEEL, value);
}

void jlspp_spot260x_stop_gobo_cycle(const jlspp_spot260x *spot, uint8_t *universe)
{
    jlspp_spot260x_set(spot, universe, JLSPP_SPOT260X_GOBO_WHEEL, GOBO_CYCLE_STOP);
}

void jlspp_spot260x_set_gobo_rotation(const jlspp_spot260x *spot, uint8_t *universe,
                                      jlspp_spot260x_rotation rotation, uint8_t speed)
{
    int value = 0; /* no rotation */

    if (rotation != JLSPP_SPOT260X_ROTATION_NONE) {
        dmx_range range = ROTATION_RANGES[rotation];
        value = jlspp_scale_into_range(speed, range.low, range.high);
    }
    jlspp_spot260x_set(spot, universe, JLSPP_SPOT260X_GOBO_ROTATION, value);
}

/* ------------------------------------------------------------------- prism / focus */

void jlspp_spot260x_set_prism(const jlspp_spot260x *spot, uint8_t *universe, int on)
{
    jlspp_spot260x_set(spot, universe, JLSPP_SPOT260X_PRISM, on ? PRISM_ON : PRISM_OFF);
}

void jlspp_spot260x_set_focus(const jlspp_spot260x *spot, uint8_t *universe, uint8_t value)
{
    jlspp_spot260x_set(spot, universe, JLSPP_SPOT260X_FOCUS, value);
}

/* ---------------------------------------------------------------- dimmer / shutter */

int jlspp_spot260x_set_dimmer(const jlspp_spot260x *spot, uint8_t *universe, uint8_t level)
{
    return jlspp_spot260x_set(spot, universe, JLSPP_SPOT260X_DIMMER, level);
}

void jlspp_spot260x_open_shutter(const jlspp_spot260x *spot, uint8_t *universe)
{
    jlspp_spot260x_set(spot, universe, JLSPP_SPOT260X_SHUTTER, SHUTTER_OPEN);
}

void jlspp_spot260x_close_shutter(const jlspp_spot260x *spot, uint8_t *universe)
{
    jlspp_spot260x_set(spot, universe, JLSPP_SPOT260X_SHUTTER, SHUTTER_CLOSED);
}

void jlspp_spot260x_set_strobe(const jlspp_spot260x *spot, uint8_t *universe, uint8_t speed,
                               jlspp_spot260x_strobe effect)
{
    dmx_range range = STROBE_RANGES[effect];
    jlspp_spot260x_set(spot, universe, JLSPP_SPOT260X_SHUTTER,
                       jlspp_scale_into_range(speed, range.low, range.high));
}

void jlspp_spot260x_light_on(const jlspp_spot260x *spot, uint8_t *universe, uint8_t level)
{
    jlspp_spot260x_set_dimmer(spot, universe, level); /* no-op in 8-channel mode */
    jlspp_spot260x_open_shutter(spot, universe);
}

void jlspp_spot260x_blackout(const jlspp_spot260x *spot, uint8_t *universe)
{
    jlspp_spot260x_set_dimmer(spot, universe, 0);     /* no-op in 8-channel mode */
    jlspp_spot260x_close_shutter(spot, universe);
}

/* ------------------------------------------------------------------------- control */

int jlspp_spot260x_set_blackout_on_move(const jlspp_spot260x *spot, uint8_t *universe,
                                        jlspp_spot260x_blackout_option option)
{
    return jlspp_spot260x_set(spot, universe, JLSPP_SPOT260X_CONTROL, (int)option);
}

int jlspp_spot260x_reset(const jlspp_spot260x *spot, uint8_t *universe, jlspp_spot260x_reset_target target)
{
    return jlspp_spot260x_set(spot, universe, JLSPP_SPOT260X_CONTROL, (int)target);
}

int jlspp_spot260x_clear_control(const jlspp_spot260x *spot, uint8_t *universe)
{
    return jlspp_spot260x_set(spot, universe, JLSPP_SPOT260X_CONTROL, 0);
}
