/*
 * jlspp_mindi_spider.c - DMX messages of the Mindi Mini Spider (see jlspp_mindi_spider.h).
 */
#include "jlspp_mindi_spider.h"

#include "jlspp_fixture_util.h"

int jlspp_spider_init(jlspp_spider *spider, int address)
{
    spider->address = address;
    spider->quirk_offset = 1;
    return jlspp_address_fits(address, JLSPP_SPIDER_CHANNEL_COUNT + 1) ? JLSPP_OK : JLSPP_ERROR;
}

int jlspp_spider_dmx_channel(const jlspp_spider *spider, int spider_channel)
{
    return spider->address + spider->quirk_offset + spider_channel - 1;
}

void jlspp_spider_set(const jlspp_spider *spider, uint8_t *universe, int spider_channel, uint8_t value)
{
    universe[jlspp_spider_dmx_channel(spider, spider_channel) - 1] = value;
}

void jlspp_spider_set_dimmer(const jlspp_spider *spider, uint8_t *universe, uint8_t level)
{
    jlspp_spider_set(spider, universe, JLSPP_SPIDER_DIMMER, level);
}

void jlspp_spider_set_strobe(const jlspp_spider *spider, uint8_t *universe, uint8_t speed)
{
    jlspp_spider_set(spider, universe, JLSPP_SPIDER_STROBE, speed);
}

int jlspp_spider_set_led(const jlspp_spider *spider, uint8_t *universe, int led, uint8_t level)
{
    if (led < 1 || led > JLSPP_SPIDER_LED_COUNT) {
        return JLSPP_ERROR;
    }
    jlspp_spider_set(spider, universe, JLSPP_SPIDER_LED_1 + led - 1, level);
    return JLSPP_OK;
}

void jlspp_spider_set_wings(const jlspp_spider *spider, uint8_t *universe, uint8_t position, int mirror)
{
    uint8_t wing_2 = mirror ? (uint8_t)(255 - position) : position;

    jlspp_spider_set(spider, universe, JLSPP_SPIDER_MOTOR_1, position);
    jlspp_spider_set(spider, universe, JLSPP_SPIDER_MOTOR_2, wing_2);
}
