/* ZS-X11H bench outputs. No Hall feedback or hardware safety claim. Apache-2.0. */
#ifndef RT_MOTORS_H
#define RT_MOTORS_H
#include "esp_err.h"
#include "motor_control.h"

typedef struct {
    int pwm;
    int dir;
    int stop;
    const char *name;
} rt_motor_pins_t;

typedef struct {
    rt_motor_pins_t pins[RT_MOTORS_MAX]; /* Local output slots, independent of role. */
    int count;
    int first_motor;                    /* Global index: front=0, rear=2, bench=0. */
    int pwm_freq_hz;
    int pwm_resolution_bits;
    bool logic_inverted;               /* External NMOS: GPIO high pulls driver input low. */
    uint32_t cmd_timeout_ms;
    uint32_t reverse_deadtime_ms;
    float slew_per_s;
    float duty_limit;
} rt_motors_config_t;

typedef struct {
    float applied[RT_MOTORS_MAX];
    uint16_t pwm_readback[RT_MOTORS_MAX]; /* LEDC registers, global wheel indices. */
    uint8_t stop_gpio_high;             /* Physical ESP pad levels, before interface. */
    uint8_t enable_mask;
    uint8_t flags;
    uint32_t cmd_age_ms;
    uint8_t configured_mask;
    uint8_t selftest_passed;
    uint8_t selftest_failed;
    uint32_t rejected;
    uint32_t output_errors;
} rt_motors_state_t;

esp_err_t rt_motors_init(const rt_motors_config_t *cfg);
bool rt_motors_command(const float duty[RT_MOTORS_MAX]);
bool rt_motors_enable(uint8_t mask);
bool rt_motors_session(uint32_t hash);
void rt_motors_estop(void);
void rt_motors_reject(void);
void rt_motors_get_state(rt_motors_state_t *out);
#endif
