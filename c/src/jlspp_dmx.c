/*
 * jlspp_dmx.c - builds and decodes JL_SPP DMX frames.
 * The tables live in jlspp_tables.c (generated from spec/cipher_tables.json).
 */
#include "jlspp_dmx.h"

#include <string.h>

extern const uint8_t jlspp_password[5][256];
extern const uint8_t jlspp_decode[5][256];
extern const uint8_t jlspp_sin[256];

#define TABLE_COUNT 5          /* number of substitution tables */
#define END_MARKER_OFFSET 519  /* frame bytes 519..520 = 'T' 'K' */

const uint8_t JLSPP_HANDSHAKE_CONNECT[6] = {0xBB, 0x99, 0x77, 0x01, 0x77, 0x99};
const uint8_t JLSPP_HANDSHAKE_DISCONNECT[8] = {0xBB, 0x77, 0x99, 0x10, 0x99, 0x77, 0x00, 0x55};

/* ------------------------------------------------------------------------- scrambling */

/* Substitution table used for a given counter value. */
static const uint8_t *scramble_table(uint8_t code_num)
{
    return jlspp_password[jlspp_sin[code_num] % TABLE_COUNT];
}

/* Inverse table, found from the sin value written in the frame. */
static const uint8_t *unscramble_table(uint8_t sin_value)
{
    return jlspp_decode[sin_value % TABLE_COUNT];
}

void jlspp_encrypt(uint8_t *buf, size_t start, size_t length, uint8_t code_num, size_t marker)
{
    const uint8_t *table = scramble_table(code_num);
    size_t i;

    /* each byte is shifted by the counter, then substituted */
    for (i = start; i < start + length; i++) {
        buf[i] = table[(uint8_t)(buf[i] + code_num)];
    }
    buf[marker] = jlspp_sin[code_num];
    buf[marker + 1] = code_num;
}

void jlspp_decrypt(uint8_t *buf, size_t start, size_t length, size_t marker)
{
    const uint8_t *table = unscramble_table(buf[marker]);
    uint8_t key = buf[marker + 1];
    size_t i;

    /* substitute back, then remove the counter shift */
    for (i = start; i < start + length; i++) {
        buf[i] = (uint8_t)(table[buf[i]] - key);
    }
}

/* ----------------------------------------------------------------------------- frames */

/* Writes the clear parts of a frame: byte 0, KT marker, scene, speed, TK marker. */
static void write_frame_envelope(uint8_t out[JLSPP_FRAME_LEN], uint8_t scene, uint8_t speed)
{
    memset(out, 0, JLSPP_FRAME_LEN);
    out[1] = 'K';
    out[2] = 'T';
    out[3] = scene;
    out[4] = speed;
    out[END_MARKER_OFFSET] = 'T';
    out[END_MARKER_OFFSET + 1] = 'K';
}

void jlspp_build_frame(const uint8_t universe[JLSPP_UNIVERSE_SIZE], uint8_t code_num,
                       uint8_t scene, uint8_t speed, uint8_t out[JLSPP_FRAME_LEN])
{
    write_frame_envelope(out, scene, speed);
    memcpy(out + JLSPP_PAYLOAD_START, universe, JLSPP_UNIVERSE_SIZE);
    jlspp_encrypt(out, JLSPP_PAYLOAD_START, JLSPP_UNIVERSE_SIZE, code_num, JLSPP_MARKER_OFFSET);
}

int jlspp_is_frame(const uint8_t frame[JLSPP_FRAME_LEN])
{
    return frame[1] == 'K' && frame[2] == 'T'
        && frame[END_MARKER_OFFSET] == 'T' && frame[END_MARKER_OFFSET + 1] == 'K';
}

int jlspp_decode_frame(const uint8_t frame[JLSPP_FRAME_LEN],
                       uint8_t universe_out[JLSPP_UNIVERSE_SIZE], uint8_t *code_num)
{
    uint8_t copy[JLSPP_FRAME_LEN];

    if (!jlspp_is_frame(frame)) {
        return JLSPP_ERROR;
    }
    memcpy(copy, frame, JLSPP_FRAME_LEN);
    jlspp_decrypt(copy, JLSPP_PAYLOAD_START, JLSPP_UNIVERSE_SIZE, JLSPP_MARKER_OFFSET);
    memcpy(universe_out, copy + JLSPP_PAYLOAD_START, JLSPP_UNIVERSE_SIZE);
    if (code_num != NULL) {
        *code_num = frame[JLSPP_MARKER_OFFSET + 1];
    }
    return JLSPP_OK;
}
