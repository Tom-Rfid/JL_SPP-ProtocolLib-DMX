/*
 * blink.c - fait clignoter les canaux 1..N une fois par seconde (test de liaison).
 *
 *   Windows : blink.exe COM6 44
 *   Linux   : ./blink /dev/rfcomm0 44
 *
 * La librairie ne fait que construire les trames : ce fichier montre l'envoi sur le
 * port serie (Win32 ou POSIX) au rythme de l'appli d'origine (une trame / 100 ms).
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "jlspp_dmx.h"

#ifdef _WIN32
#include <windows.h>
typedef HANDLE port_t;

static port_t port_open(const char *name)
{
    char path[64];
    snprintf(path, sizeof path, "\\\\.\\%s", name); /* necessaire au-dela de COM9 */
    return CreateFileA(path, GENERIC_WRITE, 0, NULL, OPEN_EXISTING, 0, NULL);
}
static int port_ok(port_t p) { return p != INVALID_HANDLE_VALUE; }
static int port_write(port_t p, const uint8_t *data, size_t len)
{
    DWORD written = 0;
    return WriteFile(p, data, (DWORD)len, &written, NULL) && written == len;
}
static void port_close(port_t p) { CloseHandle(p); }
static void sleep_ms(int ms) { Sleep((DWORD)ms); }
#else
#include <fcntl.h>
#include <termios.h>
#include <unistd.h>
typedef int port_t;

static port_t port_open(const char *name)
{
    int fd = open(name, O_WRONLY | O_NOCTTY);
    if (fd >= 0) {
        struct termios tio;
        tcgetattr(fd, &tio);
        cfmakeraw(&tio); /* octets bruts, pas de traduction de fin de ligne */
        tcsetattr(fd, TCSANOW, &tio);
    }
    return fd;
}
static int port_ok(port_t p) { return p >= 0; }
static int port_write(port_t p, const uint8_t *data, size_t len) { return write(p, data, len) == (ssize_t)len; }
static void port_close(port_t p) { close(p); }
static void sleep_ms(int ms) { usleep((useconds_t)ms * 1000); }
#endif

int main(int argc, char **argv)
{
    const char *name = argc > 1 ? argv[1] : "COM6";
    int last = argc > 2 ? atoi(argv[2]) : 44;
    uint8_t universe[JLSPP_UNIVERSE_SIZE] = {0};
    uint8_t frame[JLSPP_FRAME_LEN];
    uint8_t code = 0;
    int tick;

    port_t port = port_open(name);
    if (!port_ok(port)) {
        fprintf(stderr, "Impossible d'ouvrir %s\n", name);
        return 1;
    }
    port_write(port, JLSPP_HANDSHAKE_CONNECT, sizeof JLSPP_HANDSHAKE_CONNECT);
    printf("Clignotement des canaux 1 a %d sur %s pendant 20 s...\n", last, name);

    for (tick = 0; tick < 200; tick++) {         /* 200 x 100 ms = 20 s */
        if (tick % 10 == 0) {                    /* bascule une fois par seconde */
            memset(universe, (tick / 10) % 2 ? 0 : 255, (size_t)last);
        }
        jlspp_build_frame(universe, ++code, 0, 0, frame);
        if (!port_write(port, frame, sizeof frame)) {
            fprintf(stderr, "Ecriture impossible (liaison perdue ?)\n");
            break;
        }
        sleep_ms(JLSPP_SEND_INTERVAL_MS);
    }

    memset(universe, 0, sizeof universe);
    jlspp_build_frame(universe, ++code, 0, 0, frame);
    port_write(port, frame, sizeof frame);
    port_write(port, JLSPP_HANDSHAKE_DISCONNECT, sizeof JLSPP_HANDSHAKE_DISCONNECT);
    port_close(port);
    return 0;
}
