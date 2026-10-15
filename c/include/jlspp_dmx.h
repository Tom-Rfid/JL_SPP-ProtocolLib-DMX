/*
 * jlspp_dmx.h - protocole DMX des boitiers Bluetooth "USB-RDM-DMX" (puce Jieli,
 * service JL_SPP, appli Android RY-AI).
 *
 * Bibliotheque C99 SANS dependance ni entree/sortie : elle construit et decode les
 * trames. L'ecriture sur le port serie (COM Windows, /dev/rfcomm0 Linux...) est a la
 * charge de l'appelant : voir examples/blink.c.
 *
 * Convention : un "univers" = 512 octets, index 0 = canal DMX 1.
 * Specification : docs/protocol.md
 */
#ifndef JLSPP_DMX_H
#define JLSPP_DMX_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define JLSPP_FRAME_LEN     521  /* taille d'une trame DMX */
#define JLSPP_UNIVERSE_SIZE 512  /* nombre de canaux */
#define JLSPP_PAYLOAD_START 5    /* octet du canal 1 dans la trame */
#define JLSPP_MARKER_OFFSET 517  /* octets de cle : [517] = sin[code], [518] = code */
#define JLSPP_SEND_INTERVAL_MS 100 /* cadence de l'appli d'origine */

/* Handshakes en clair : connexion juste apres l'ouverture, deconnexion avant la fermeture. */
extern const uint8_t JLSPP_HANDSHAKE_CONNECT[6];
extern const uint8_t JLSPP_HANDSHAKE_DISCONNECT[8];

/*
 * Brouillage (Code.Encryption1) EN PLACE : brouille buf[start .. start+length-1] et ecrit
 * les 2 octets de cle a buf[marker] et buf[marker+1].
 */
void jlspp_encrypt(uint8_t *buf, size_t start, size_t length, uint8_t code_num, size_t marker);

/* Operation inverse (Code.Decode) EN PLACE, en relisant la cle ecrite dans buf. */
void jlspp_decrypt(uint8_t *buf, size_t start, size_t length, size_t marker);

/*
 * Construit une trame complete dans out (JLSPP_FRAME_LEN octets).
 * scene / speed : octets 3 et 4 (0 et 0 en pilotage direct).
 */
void jlspp_build_frame(const uint8_t universe[JLSPP_UNIVERSE_SIZE], uint8_t code_num,
                       uint8_t scene, uint8_t speed, uint8_t out[JLSPP_FRAME_LEN]);

/* 1 si la trame a la bonne longueur logique et les marqueurs KT / TK, 0 sinon. */
int jlspp_is_frame(const uint8_t frame[JLSPP_FRAME_LEN]);

/*
 * Retrouve l'univers en clair d'une trame. Retourne 0 si OK, -1 si ce n'est pas une
 * trame valide. code_num peut etre NULL.
 */
int jlspp_decode_frame(const uint8_t frame[JLSPP_FRAME_LEN],
                       uint8_t universe_out[JLSPP_UNIVERSE_SIZE], uint8_t *code_num);

#ifdef __cplusplus
}
#endif

#endif /* JLSPP_DMX_H */
