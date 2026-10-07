/* Portable bench control policy, also exercised on the host. Apache-2.0. */
#ifndef RT_MOTOR_CONTROL_H
#define RT_MOTOR_CONTROL_H
#include <stdbool.h>
#include <stdint.h>
#include "retriever_protocol.h"

#define RT_MOTORS_MAX 4
typedef struct {
    uint8_t configured_mask;
    uint32_t timeout_ms;
    uint32_t reverse_ms;
    float slew_per_s;
    float duty_limit;
} rt_motor_control_config_t;

typedef struct {
    rt_motor_control_config_t cfg;
    float target[RT_MOTORS_MAX];
    float applied[RT_MOTORS_MAX];
    int direction[RT_MOTORS_MAX];
    uint64_t stopped_us[RT_MOTORS_MAX];
    uint64_t last_cmd_us;
    uint64_t last_step_us;
    uint8_t enable_mask;
    uint8_t flags;
    uint32_t cmd_age_ms;
    uint32_t rejected;
    bool have_command;
    bool ever_armed;
    bool estop;
    bool fault;
    bool protocol_ok;
} rt_motor_control_t;

bool rt_motor_control_init(rt_motor_control_t *c, const rt_motor_control_config_t *cfg);
bool rt_motor_control_command(rt_motor_control_t *c, const float duty[4], uint64_t now_us);
bool rt_motor_control_enable(rt_motor_control_t *c, uint8_t mask, uint64_t now_us);
bool rt_motor_control_session(rt_motor_control_t *c, uint32_t hash);
void rt_motor_control_stop(rt_motor_control_t *c, bool fault);
void rt_motor_control_step(rt_motor_control_t *c, uint64_t now_us);
#endif
