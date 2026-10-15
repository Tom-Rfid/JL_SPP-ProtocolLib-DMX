/*
 * jlspp_dmx.h - DMX protocol of the "USB-RDM-DMX" Bluetooth interfaces (Jieli chip,
 * JL_SPP service, RY-AI Android app).
 *
 * C99 library with NO dependency, NO allocation and NO input/output: it builds and
 * decodes frames. Writing them to the serial port (Windows COM port, /dev/rfcomm0 on
 * Linux...) is up to the caller: see examples/blink.c.
 *
 * Convention: a "universe" is 512 bytes, index 0 = DMX channel 1.
 * Specification: docs/protocol.md
 *
 * Typical use:
 *
 *     uint8_t universe[JLSPP_UNIVERSE_SIZE] = {0};
 *     uint8_t frame[JLSPP_FRAME_LEN];
 *     uint8_t code = 0;
 *
 *     write_port(JLSPP_HANDSHAKE_CONNECT, sizeof JLSPP_HANDSHAKE_CONNECT);
 *     every JLSPP_SEND_INTERVAL_MS:
 *         jlspp_build_frame(universe, code++, 0, 0, frame);
 *         write_port(frame, JLSPP_FRAME_LEN);
 *     write_port(JLSPP_HANDSHAKE_DISCONNECT, sizeof JLSPP_HANDSHAKE_DISCONNECT);
 */
#ifndef JLSPP_DMX_H
#define JLSPP_DMX_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define JLSPP_FRAME_LEN        521 /* bytes in one DMX frame */
#define JLSPP_UNIVERSE_SIZE    512 /* DMX channels in one universe */
#define JLSPP_PAYLOAD_START    5   /* frame byte holding DMX channel 1 */
#define JLSPP_MARKER_OFFSET    517 /* key bytes: [517] = sin[code], [518] = code */
#define JLSPP_SEND_INTERVAL_MS 100 /* sending rate of the original app */

/* Return codes of the functions that can fail. */
#define JLSPP_OK    0
#define JLSPP_ERROR (-1)

/* Handshakes, sent in clear: right after opening the port / right before closing it. */
extern const uint8_t JLSPP_HANDSHAKE_CONNECT[6];
extern const uint8_t JLSPP_HANDSHAKE_DISCONNECT[8];

/*
 * Scrambling (Code.Encryption1), IN PLACE: scrambles buf[start .. start+length-1] and
 * writes the 2 key bytes at buf[marker] and buf[marker+1].
 */
void jlspp_encrypt(uint8_t *buf, size_t start, size_t length, uint8_t code_num, size_t marker);

/* Inverse operation (Code.Decode), IN PLACE, reading the key back from buf. */
void jlspp_decrypt(uint8_t *buf, size_t start, size_t length, size_t marker);

/*
 * Builds a complete frame into out (JLSPP_FRAME_LEN bytes).
 *   universe : 512 channel values, index 0 = channel 1
 *   code_num : counter 0..255, normally incremented for every frame
 *   scene    : byte 3 (0 = direct control)
 *   speed    : byte 4 (0 in direct control)
 */
void jlspp_build_frame(const uint8_t universe[JLSPP_UNIVERSE_SIZE], uint8_t code_num,
                       uint8_t scene, uint8_t speed, uint8_t out[JLSPP_FRAME_LEN]);

/* 1 if the frame has the clear KT / TK markers, 0 otherwise. */
int jlspp_is_frame(const uint8_t frame[JLSPP_FRAME_LEN]);

/*
 * Gets the clear universe back from a frame. Returns JLSPP_OK, or JLSPP_ERROR if this
 * is not a valid frame. code_num may be NULL.
 */
int jlspp_decode_frame(const uint8_t frame[JLSPP_FRAME_LEN],
                       uint8_t universe_out[JLSPP_UNIVERSE_SIZE], uint8_t *code_num);

#ifdef __cplusplus
}
#endif

#endif /* JLSPP_DMX_H */
