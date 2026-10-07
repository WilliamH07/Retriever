/* Behavioural tests: commissioning gates, timeout, reversal, invalid data. */
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include "motor_control.h"

static rt_motor_control_t create(uint8_t mask)
{
    rt_motor_control_t c;
    const rt_motor_control_config_t cfg = {mask, 500, 250, 2.0f, 0.25f};
    assert(rt_motor_control_init(&c, &cfg));
    return c;
}
static void arm(rt_motor_control_t *c, uint8_t mask, uint64_t t)
{
    const float zero[4] = {0};
    assert(rt_motor_control_session(c, RT_PROTOCOL_HASH));
    assert(rt_motor_control_command(c, zero, t));
    rt_motor_control_step(c, t);
    assert(rt_motor_control_enable(c, mask, t));
}
int main(void)
{
    /* Current bench: front-right disconnected, keep all four fixed indices.
     * Each of the three commissioning commands must select exactly one wheel. */
    const int connected[] = {0, 2, 3};
    for (unsigned trial = 0; trial < sizeof(connected) / sizeof(connected[0]); ++trial) {
        const int selected = connected[trial];
        rt_motor_control_t isolated = create(15);
        const uint8_t mask = (uint8_t)(1u << selected);
        float duty[4] = {0};
        duty[selected] = .1f;
        arm(&isolated, mask, 10000);
        assert(rt_motor_control_command(&isolated, duty, 10000));
        for (int tick = 1; tick <= 20; ++tick) {
            rt_motor_control_step(&isolated, 10000 + tick * 5000);
            assert(isolated.enable_mask == mask);
            for (int wheel = 0; wheel < 4; ++wheel) {
                if (wheel != selected) assert(isolated.applied[wheel] == 0);
            }
        }
        assert(fabsf(isolated.applied[selected] - .1f) < 1e-6f);
        assert(rt_motor_control_enable(&isolated, 0, 115000));
        rt_motor_control_step(&isolated, 115000);
        for (int wheel = 0; wheel < 4; ++wheel) assert(isolated.applied[wheel] == 0);
    }
    rt_motor_control_t c = create(0x03);
    assert(!rt_motor_control_enable(&c, 3, 1000)); /* No session or command. */
    const float zero[4] = {0}, forward[4] = {.2f, .2f, .3f, .3f};
    assert(rt_motor_control_command(&c, zero, 1000));
    assert(!rt_motor_control_enable(&c, 3, 1000));
    assert(!rt_motor_control_session(&c, RT_PROTOCOL_HASH ^ 1));
    assert(rt_motor_control_session(&c, RT_PROTOCOL_HASH));
    assert(rt_motor_control_command(&c, forward, 2000));
    assert(!rt_motor_control_enable(&c, 3, 2000)); /* Cannot arm with nonzero target. */
    arm(&c, 15, 10000);
    assert(c.enable_mask == 3); /* Other axle bits never activate local outputs. */
    assert(rt_motor_control_command(&c, forward, 10000));
    rt_motor_control_step(&c, 15000);
    assert(fabsf(c.applied[0] - .01f) < 1e-6f);
    assert(c.applied[2] == 0 && c.applied[3] == 0);
    assert(c.flags & RT_MOTOR_FLAG_ENABLED);
    rt_motor_control_step(&c, 100000); /* Delayed task: ramp step remains bounded. */
    assert(c.applied[0] <= .031f);
    rt_motor_control_step(&c, 510001);
    assert(c.enable_mask == 0 && c.applied[0] == 0);
    assert(c.flags & RT_MOTOR_FLAG_CMD_TIMEOUT);
    assert(rt_motor_control_command(&c, forward, 520000));
    rt_motor_control_step(&c, 525000);
    assert(c.applied[0] == 0); /* No automatic restart on link recovery. */
    arm(&c, 3, 530000);
    assert(rt_motor_control_command(&c, forward, 530000));
    rt_motor_control_step(&c, 535000);
    /* A late RX frame before the next control tick cannot conceal expiry. */
    assert(rt_motor_control_command(&c, forward, 1100000));
    rt_motor_control_step(&c, 1105000);
    assert(c.enable_mask == 0 && c.applied[0] == 0);

    c = create(0x0C);
    arm(&c, 15, 10000);
    assert(c.enable_mask == 12);
    const float high[4] = {.1f, .1f, 1, 1};
    assert(rt_motor_control_command(&c, high, 10000));
    for (int i = 1; i <= 40; ++i) rt_motor_control_step(&c, 10000 + i * 5000);
    assert(c.applied[0] == 0 && c.applied[1] == 0);
    assert(fabsf(c.applied[2] - .25f) < 1e-6f && (c.flags & RT_MOTOR_FLAG_LIMITED));
    const float reverse[4] = {0, 0, -.2f, -.2f};
    assert(rt_motor_control_command(&c, reverse, 215000));
    rt_motor_control_step(&c, 215000);
    assert(c.applied[2] == 0 && c.direction[2] == 1);
    assert(c.flags & RT_MOTOR_FLAG_REVERSING);
    rt_motor_control_step(&c, 460000);
    assert(c.applied[2] == 0 && c.direction[2] == 1);
    rt_motor_control_step(&c, 465000);
    assert(c.applied[2] < 0 && c.direction[2] == -1);
    rt_motor_control_stop(&c, false);
    rt_motor_control_step(&c, 470000);
    assert(c.applied[2] == 0 && c.enable_mask == 0);
    assert(c.flags & RT_MOTOR_FLAG_ESTOP);
    arm(&c, 12, 475000);
    assert(!c.estop);
    rt_motor_control_stop(&c, true);
    assert(!rt_motor_control_enable(&c, 12, 475000));
    rt_motor_control_step(&c, 480000);
    assert(c.flags & RT_MOTOR_FLAG_OUTPUT_FAULT);

    c = create(7);
    arm(&c, 15, 10000);
    assert(c.enable_mask == 7); /* Fourth controller absent on current bench. */
    const float nan[4] = {NAN, 0, 0, 0}, inf[4] = {INFINITY, 0, 0, 0};
    const float invalid[4] = {1.001f, 0, 0, 0};
    assert(!rt_motor_control_command(&c, nan, 20000));
    assert(!rt_motor_control_command(&c, inf, 20000));
    assert(!rt_motor_control_command(&c, invalid, 20000));
    assert(c.last_cmd_us == 10000);
    assert(!rt_motor_control_enable(&c, 0x80, 10000));
    assert(rt_motor_control_enable(&c, 0, 10000));
    assert(c.enable_mask == 0);
    assert(!rt_motor_control_session(&c, 0));
    assert(!rt_motor_control_enable(&c, 7, 10000));
    rt_motor_control_step(&c, 100000000);
    assert(c.cmd_age_ms == 65535);
    const rt_motor_control_config_t bad = {0, 500, 250, 2, .25f};
    assert(!rt_motor_control_init(&c, &bad));
    puts("motor control: commissioning, axle mapping, watchdog, ramp, reversal and faults OK");
    return 0;
}
