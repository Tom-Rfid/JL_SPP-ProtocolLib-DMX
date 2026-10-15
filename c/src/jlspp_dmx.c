/*
 * jlspp_dmx.c - construction / decodage des trames DMX JL_SPP.
 * Les tables sont dans jlspp_tables.c (genere depuis spec/cipher_tables.json).
 */
#include "jlspp_dmx.h"

#include <string.h>

extern const uint8_t jlspp_password[5][256];
extern const uint8_t jlspp_decode[5][256];
extern const uint8_t jlspp_sin[256];

const uint8_t JLSPP_HANDSHAKE_CONNECT[6] = {0xBB, 0x99, 0x77, 0x01, 0x77, 0x99};
const uint8_t JLSPP_HANDSHAKE_DISCONNECT[8] = {0xBB, 0x77, 0x99, 0x10, 0x99, 0x77, 0x00, 0x55};

void jlspp_encrypt(uint8_t *buf, size_t start, size_t length, uint8_t code_num, size_t marker)
{
    /* La table est choisie par sin[code] % 5 ; chaque octet est decale de code puis substitue. */
    const uint8_t *table = jlspp_password[jlspp_sin[code_num] % 5];
    size_t i;
    for (i = start; i < start + length; i++) {
        buf[i] = table[(uint8_t)(buf[i] + code_num)];
    }
    buf[marker] = jlspp_sin[code_num];
    buf[marker + 1] = code_num;
}

void jlspp_decrypt(uint8_t *buf, size_t start, size_t length, size_t marker)
{
    const uint8_t *table = jlspp_decode[buf[marker] % 5];
    uint8_t key = buf[marker + 1];
    size_t i;
    for (i = start; i < start + length; i++) {
        buf[i] = (uint8_t)(table[buf[i]] - key);
    }
}

void jlspp_build_frame(const uint8_t universe[JLSPP_UNIVERSE_SIZE], uint8_t code_num,
                       uint8_t scene, uint8_t speed, uint8_t out[JLSPP_FRAME_LEN])
{
    memset(out, 0, JLSPP_FRAME_LEN);
    out[1] = 'K';
    out[2] = 'T';
    out[3] = scene;
    out[4] = speed;
    memcpy(out + JLSPP_PAYLOAD_START, universe, JLSPP_UNIVERSE_SIZE);
    out[519] = 'T';
    out[520] = 'K';
    jlspp_encrypt(out, JLSPP_PAYLOAD_START, JLSPP_UNIVERSE_SIZE, code_num, JLSPP_MARKER_OFFSET);
}

int jlspp_is_frame(const uint8_t frame[JLSPP_FRAME_LEN])
{
    return frame[1] == 'K' && frame[2] == 'T' && frame[519] == 'T' && frame[520] == 'K';
}

int jlspp_decode_frame(const uint8_t frame[JLSPP_FRAME_LEN],
                       uint8_t universe_out[JLSPP_UNIVERSE_SIZE], uint8_t *code_num)
{
    uint8_t copy[JLSPP_FRAME_LEN];
    if (!jlspp_is_frame(frame)) {
        return -1;
    }
    memcpy(copy, frame, JLSPP_FRAME_LEN);
    jlspp_decrypt(copy, JLSPP_PAYLOAD_START, JLSPP_UNIVERSE_SIZE, JLSPP_MARKER_OFFSET);
    memcpy(universe_out, copy + JLSPP_PAYLOAD_START, JLSPP_UNIVERSE_SIZE);
    if (code_num != NULL) {
        *code_num = frame[JLSPP_MARKER_OFFSET + 1];
    }
    return 0;
}
