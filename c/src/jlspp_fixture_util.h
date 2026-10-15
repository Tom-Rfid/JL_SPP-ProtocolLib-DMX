/*
 * jlspp_fixture_util.h - small helpers shared by the fixture files (internal header).
 * Integer maths only, so that every language of the project gives the same values.
 */
#ifndef JLSPP_FIXTURE_UTIL_H
#define JLSPP_FIXTURE_UTIL_H

#include <stdint.h>

#include "jlspp_dmx.h"

/* Clamps any int into a DMX value 0..255. */
static inline uint8_t jlspp_clamp_byte(int value)
{
    return (uint8_t)(value < 0 ? 0 : (value > 255 ? 255 : value));
}

/* Maps amount 0..255 linearly onto the DMX range low..high (0 -> low, 255 -> high). */
static inline uint8_t jlspp_scale_into_range(int amount, int low, int high)
{
    return (uint8_t)(low + jlspp_clamp_byte(amount) * (high - low) / 255);
}

/* Middle of a DMX range: the safest value to select a slot (color, gobo...). */
static inline uint8_t jlspp_middle(int low, int high)
{
    return (uint8_t)((low + high) / 2);
}

/* 1 if a fixture of `footprint` channels fits at `address` in a 512-channel universe. */
static inline int jlspp_address_fits(int address, int footprint)
{
    return address >= 1 && address + footprint - 1 <= JLSPP_UNIVERSE_SIZE;
}

#endif /* JLSPP_FIXTURE_UTIL_H */
