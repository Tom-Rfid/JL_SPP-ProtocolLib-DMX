/* Tests contre spec/test_vectors.json (via test_vectors.h genere par tools/generate_tables.py). */
#include <stdio.h>
#include <string.h>

#include "jlspp_dmx.h"
#include "jlspp_mindi_spider.h"
#include "test_vectors.h"

static int failures = 0;

static void check(int ok, const char *what, const char *name)
{
    printf("%s  %-32s %s\n", ok ? "OK  " : "ECHEC", name, what);
    if (!ok) {
        failures++;
    }
}

int main(void)
{
    uint8_t frame[JLSPP_FRAME_LEN];
    uint8_t universe[JLSPP_UNIVERSE_SIZE];
    uint8_t code = 0;
    int i;

    for (i = 0; i < JLSPP_TEST_VECTOR_COUNT; i++) {
        const jlspp_test_vector *v = &JLSPP_TEST_VECTORS[i];

        jlspp_build_frame(v->universe, v->code_num, 0, 0, frame);
        check(memcmp(frame, v->frame, JLSPP_FRAME_LEN) == 0, "build_frame == vecteur", v->name);

        check(jlspp_decode_frame(v->frame, universe, &code) == 0
                  && memcmp(universe, v->universe, JLSPP_UNIVERSE_SIZE) == 0
                  && code == v->code_num,
              "decode_frame == univers", v->name);
    }

    /* Le vecteur "Spider" se reconstruit avec les aides du Spider (adresse affichee 1). */
    memset(universe, 0, sizeof universe);
    jlspp_spider_set_wings(universe, 1, 200, 1);
    universe[jlspp_spider_index(1, JLSPP_SPIDER_DIMMER)] = 255;
    jlspp_spider_set_led(universe, 1, 1, 255);
    jlspp_spider_set_led(universe, 1, 5, 255);
    for (i = 0; i < JLSPP_TEST_VECTOR_COUNT; i++) {
        if (strcmp(JLSPP_TEST_VECTORS[i].name, "mindi_spider_adresse1_code7") == 0) {
            check(memcmp(universe, JLSPP_TEST_VECTORS[i].universe, JLSPP_UNIVERSE_SIZE) == 0,
                  "aides Spider == vecteur", "mindi_spider");
        }
    }

    frame[1] = 'X';
    check(jlspp_decode_frame(frame, universe, NULL) == -1, "trame invalide refusee", "is_frame");

    printf("\n%s (%d echec(s))\n", failures == 0 ? "TOUS LES TESTS PASSENT" : "DES TESTS ECHOUENT", failures);
    return failures == 0 ? 0 : 1;
}
