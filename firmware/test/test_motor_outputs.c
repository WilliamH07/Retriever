/* Exercise the production GPIO/LEDC writer, with peripheral faults injected. */
#include <assert.h>
#include <stdio.h>
#include "fake_idf.h"
#include "../esp32_motion/main/motors.c"

static uint32_t pwm[4], pending[4], frequency;
static int pins[4], pad[40], forced[40], fail_update;
static uint64_t now;
static int active_write_slot, inactive_writes;

esp_err_t gpio_set_level(gpio_num_t pin, int level) { pad[pin] = level; return ESP_OK; }
int gpio_get_level(gpio_num_t pin) { return forced[pin] < 0 ? pad[pin] : forced[pin]; }
esp_err_t gpio_config(const gpio_config_t *cfg) { (void)cfg; return ESP_OK; }
esp_err_t ledc_set_duty(int mode, ledc_channel_t channel, uint32_t duty)
{
    assert(mode == LEDC_LOW_SPEED_MODE && channel >= 0 && channel < 4);
    if (active_write_slot >= 0 && duty) {
        assert(channel == active_write_slot);
        assert(inactive_writes == s_cfg.count - 1); /* Inactive outputs were written first. */
    } else if (active_write_slot >= 0) {
        inactive_writes++;
    }
    pending[channel] = duty;
    return ESP_OK;
}
esp_err_t ledc_update_duty(int mode, ledc_channel_t channel)
{
    (void)mode;
    if (fail_update == channel) { fail_update = -1; return ESP_FAIL; }
    pwm[channel] = pending[channel];
    return ESP_OK;
}
uint32_t ledc_get_duty(int mode, ledc_channel_t channel) { (void)mode; return pwm[channel]; }
esp_err_t ledc_timer_config(const ledc_timer_config_t *cfg) { frequency = cfg->freq_hz; return ESP_OK; }
esp_err_t ledc_channel_config(const ledc_channel_config_t *cfg)
{
    assert(cfg->channel >= 0 && cfg->channel < 4);
    pins[cfg->channel] = cfg->gpio_num;
    pwm[cfg->channel] = pending[cfg->channel] = cfg->duty;
    return ESP_OK;
}
uint32_t ledc_get_freq(int mode, int timer) { (void)mode; (void)timer; return frequency; }
int64_t esp_timer_get_time(void) { return now; }
esp_err_t esp_task_wdt_add(void *task) { (void)task; return ESP_OK; }
esp_err_t esp_task_wdt_reset(void) { return ESP_OK; }
TickType_t xTaskGetTickCount(void) { return now / 1000; }
void vTaskDelay(TickType_t ticks) { now += ticks * 1000; }
void vTaskDelayUntil(TickType_t *wake, TickType_t ticks) { *wake += ticks; now += ticks * 1000; }
void vTaskDelete(void *task) { (void)task; }
int xTaskCreate(void (*task)(void *), const char *name, int stack, void *arg, int priority, void *handle)
{
    (void)task; (void)name; (void)stack; (void)arg; (void)priority; (void)handle;
    return pdPASS; /* The test advances ctrl_cycle deterministically. */
}

static void initialize(bool inverted, bool rear)
{
    memset(pwm, 0, sizeof(pwm)); memset(pending, 0, sizeof(pending));
    memset(pad, 0, sizeof(pad)); memset(pins, 0, sizeof(pins));
    for (int i = 0; i < 40; ++i) forced[i] = -1;
    s_initialized = false; s_pwm_channels = 0; s_passed = s_failed = 0;
    s_output_errors = 0; s_stop_levels = 0;
    memset(s_written, 0, sizeof(s_written)); memset(s_confirmed, 0, sizeof(s_confirmed));
    memset(s_pwm_readback, 0, sizeof(s_pwm_readback));
    active_write_slot = fail_update = -1; inactive_writes = 0; now = 10000;
    const rt_motors_config_t cfg = {
        .pins = {{25, 26, 27, "m0"}, {32, 33, 14, "m1"},
                 {18, 19, 21, "m2"}, {22, 23, 13, "m3"}},
        .count = rear ? 2 : 4, .first_motor = rear ? 2 : 0,
        .pwm_freq_hz = 20000, .pwm_resolution_bits = 10, .logic_inverted = inverted,
        .cmd_timeout_ms = 500, .reverse_deadtime_ms = 250, .slew_per_s = 2, .duty_limit = .25f,
    };
    assert(rt_motors_init(&cfg) == ESP_OK);
    for (int i = 0; i < cfg.count; ++i) assert(pins[i] == cfg.pins[i].pwm && pwm[i] == 0);
}
static void cycle(void) { now += 5000; inactive_writes = 0; ctrl_cycle(); }
static void start(int global)
{
    const float zero[4] = {0};
    assert(rt_motors_session(RT_PROTOCOL_HASH));
    assert(rt_motors_command(zero));
    assert(rt_motors_enable((uint8_t)(1u << global)));
    float duty[4] = {0}; duty[global] = .1f;
    assert(rt_motors_command(duty));
    active_write_slot = global - s_cfg.first_motor;
    for (int i = 0; i < 15; ++i) cycle();
    active_write_slot = -1;
}
static void assert_stopped(void)
{
    for (int i = 0; i < s_cfg.count; ++i) {
        assert(pwm[i] == 0);
        assert(pad[s_cfg.pins[i].stop] == (s_cfg.logic_inverted ? 1 : 0));
    }
}
int main(void)
{
    for (int inverted = 0; inverted <= 1; ++inverted) {
        initialize(inverted, false);
        for (int selected = 0; selected < 4; ++selected) {
            start(selected);
            rt_motors_state_t state;
            rt_motors_get_state(&state);
            for (int i = 0; i < 4; ++i) {
                assert(pwm[i] == (i == selected ? 102u : 0u));
                assert(state.pwm_readback[i] == pwm[i]);
                assert(fabsf(state.applied[i] - (i == selected ? 102.0f / 1023 : 0)) < 1e-6f);
                assert(pad[s_cfg.pins[i].stop] == (inverted ? i != selected : i == selected));
            }
            assert(rt_motors_enable(0));
            cycle(); assert_stopped(); cycle();
            rt_motors_get_state(&state);
            for (int i = 0; i < 4; ++i) assert(state.applied[i] == 0);
        }
    }
    initialize(false, true); start(3); /* Rear m3 uses local channel 1 / GPIO32. */
    assert(pwm[0] == 0 && pwm[1] == 102 && pins[1] == 32);
    now += 600000; cycle(); assert_stopped();

    initialize(false, false); start(3);
    pwm[0] = 80; /* Non-selected hardware channel unexpectedly active. */
    cycle(); assert_stopped();
    assert(s_failed & RT_MOTOR_SELFTEST_PWM);
    assert(!rt_motors_enable(8)); cycle(); assert_stopped();

    initialize(false, false);
    forced[27] = 1; /* STOP pad unexpectedly high on an inactive wheel. */
    cycle(); assert_stopped();
    assert(s_failed & RT_MOTOR_SELFTEST_GPIO);

    initialize(false, false); start(3);
    fail_update = 2; /* Write failure must stop every channel. */
    cycle(); assert_stopped(); assert(s_output_errors == 1);
    puts("motor outputs: GPIO/channel mapping, sequential selection, polarity, readback and faults OK");
    return 0;
}
