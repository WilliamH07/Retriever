/* No hardware access here: a single ESP task owns all output writes. Apache-2.0. */
#include "motor_control.h"
#include <math.h>
#include <string.h>

bool rt_motor_control_init(rt_motor_control_t *c, const rt_motor_control_config_t *cfg)
{
    if (!c || !cfg || !cfg->configured_mask || (cfg->configured_mask & 0xF0u) ||
        !cfg->timeout_ms || !cfg->reverse_ms || !isfinite(cfg->slew_per_s) ||
        cfg->slew_per_s <= 0 || !isfinite(cfg->duty_limit) ||
        cfg->duty_limit <= 0 || cfg->duty_limit > 1) return false;
    memset(c, 0, sizeof(*c));
    c->cfg = *cfg;
    c->cmd_age_ms = 65535;
    c->flags = RT_MOTOR_FLAG_NEVER_ARMED | RT_MOTOR_FLAG_CMD_TIMEOUT |
               RT_MOTOR_FLAG_PROTOCOL_BLOCKED;
    return true;
}

bool rt_motor_control_command(rt_motor_control_t *c, const float duty[4], uint64_t now_us)
{
    if (!duty) { c->rejected++; return false; }
    for (int i = 0; i < 4; ++i) {
        if (!isfinite(duty[i]) || fabsf(duty[i]) > 1) {
            c->rejected++;
            return false; /* Whole frame rejected; invalid data never refreshes watchdog. */
        }
    }
    /* Observe expiry BEFORE refreshing the timestamp: a late frame must not
     * hide an interruption between two control ticks. */
    if (c->have_command && now_us - c->last_cmd_us > (uint64_t)c->cfg.timeout_ms * 1000)
        c->enable_mask = 0;
    memcpy(c->target, duty, sizeof(c->target));
    c->last_cmd_us = now_us;
    c->have_command = true;
    return true;
}

bool rt_motor_control_enable(rt_motor_control_t *c, uint8_t mask, uint64_t now_us)
{
    if (mask & 0xF0u) { c->rejected++; return false; }
    const uint8_t local = mask & c->cfg.configured_mask;
    if (local) {
        if (c->fault || !c->protocol_ok || !c->have_command ||
            now_us - c->last_cmd_us > (uint64_t)c->cfg.timeout_ms * 1000) {
            c->rejected++;
            return false;
        }
        for (int i = 0; i < 4; ++i) {
            if ((c->cfg.configured_mask & (1u << i)) &&
                (c->target[i] != 0 || c->applied[i] != 0)) {
                c->rejected++;
                return false;
            }
        }
        c->estop = false;
        c->ever_armed = true;
    }
    c->enable_mask = local;
    return true;
}

bool rt_motor_control_session(rt_motor_control_t *c, uint32_t hash)
{
    c->protocol_ok = hash == RT_PROTOCOL_HASH;
    if (!c->protocol_ok) {
        c->enable_mask = 0;
        c->rejected++;
    }
    return c->protocol_ok;
}

void rt_motor_control_stop(rt_motor_control_t *c, bool fault)
{
    c->enable_mask = 0;
    memset(c->target, 0, sizeof(c->target));
    c->estop = true;
    c->fault |= fault; /* Peripheral faults can only be cleared by reboot. */
}

void rt_motor_control_step(rt_motor_control_t *c, uint64_t now_us)
{
    const uint64_t age = c->have_command ? (now_us - c->last_cmd_us) / 1000 : 65535;
    c->cmd_age_ms = age > 65535 ? 65535 : (uint32_t)age;
    const bool timeout = !c->have_command ||
        now_us - c->last_cmd_us > (uint64_t)c->cfg.timeout_ms * 1000;
    if (timeout || c->fault || c->estop || !c->protocol_ok) c->enable_mask = 0;
    c->flags = (c->enable_mask ? RT_MOTOR_FLAG_ENABLED : 0) |
        (timeout ? RT_MOTOR_FLAG_CMD_TIMEOUT : 0) |
        (c->estop ? RT_MOTOR_FLAG_ESTOP : 0) |
        (!c->ever_armed ? RT_MOTOR_FLAG_NEVER_ARMED : 0) |
        (c->fault ? RT_MOTOR_FLAG_OUTPUT_FAULT : 0) |
        (!c->protocol_ok ? RT_MOTOR_FLAG_PROTOCOL_BLOCKED : 0);

    /* Cap elapsed time: after a delayed task, no jump straight to full duty. */
    uint64_t elapsed = c->last_step_us ? now_us - c->last_step_us : 5000;
    if (elapsed > 10000) elapsed = 10000;
    const float step = c->cfg.slew_per_s * (float)elapsed / 1000000.0f;
    c->last_step_us = now_us;
    for (int i = 0; i < 4; ++i) {
        float goal = (c->enable_mask & (1u << i)) ? c->target[i] : 0;
        if (fabsf(goal) > c->cfg.duty_limit) {
            goal = copysignf(c->cfg.duty_limit, goal);
            c->flags |= RT_MOTOR_FLAG_LIMITED;
        }
        const int sign = goal > 0 ? 1 : (goal < 0 ? -1 : 0);
        const float previous = c->applied[i];
        if (sign && c->direction[i] && sign != c->direction[i]) {
            if (previous != 0 || now_us - c->stopped_us[i] < (uint64_t)c->cfg.reverse_ms * 1000) {
                goal = 0;
                c->flags |= RT_MOTOR_FLAG_REVERSING;
            }
        }
        if (goal == 0) {
            c->applied[i] = 0;
        } else if (fabsf(goal) <= fabsf(previous) && sign == c->direction[i]) {
            c->applied[i] = goal;
        } else {
            c->applied[i] = copysignf(fminf(fabsf(goal), fabsf(previous) + step), goal);
        }
        if (previous != 0 && c->applied[i] == 0) c->stopped_us[i] = now_us;
        if (c->applied[i] != 0) c->direction[i] = sign;
    }
}
