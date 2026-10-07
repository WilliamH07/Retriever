/* One task owns GPIO/LEDC. The portable policy is shared with host tests. Apache-2.0. */
#include "motors.h"
#include <inttypes.h>
#include <math.h>
#include <string.h>
#include "driver/gpio.h"
#include "driver/ledc.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "esp_task_wdt.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "motors";
static portMUX_TYPE s_lock = portMUX_INITIALIZER_UNLOCKED;
static rt_motors_config_t s_cfg;
static rt_motor_control_t s_control;
static uint8_t s_passed, s_failed;
static uint32_t s_output_errors;
static bool s_initialized;
static int s_pwm_channels;
/* Last writes and next-cycle peripheral readback. Only ctrl_task writes these. */
static float s_written[4], s_confirmed[4];
static uint16_t s_pwm_readback[4];
static uint8_t s_stop_levels;

static uint32_t duty_ticks(float duty)
{
    return (uint32_t)lroundf(fabsf(duty) * (float)((1u << s_cfg.pwm_resolution_bits) - 1u));
}

static esp_err_t logic_set(int pin, int driver_level)
{
    return gpio_set_level((gpio_num_t)pin, s_cfg.logic_inverted ? !driver_level : driver_level);
}

static esp_err_t output_set(int slot, float duty)
{
    const rt_motor_pins_t *p = &s_cfg.pins[slot];
    const bool run = duty != 0;
    esp_err_t err;
    if (!run && (err = logic_set(p->stop, 0)) != ESP_OK) return err;
    /* Keep DIR unchanged at zero, including throughout reversal dead time. */
    if (run && (err = logic_set(p->dir, duty > 0)) != ESP_OK) return err;
    err = ledc_set_duty(LEDC_LOW_SPEED_MODE, (ledc_channel_t)slot,
                        duty_ticks(duty));
    if (err != ESP_OK) return err;
    err = ledc_update_duty(LEDC_LOW_SPEED_MODE, (ledc_channel_t)slot);
    if (err != ESP_OK) return err;
    return run ? logic_set(p->stop, 1) : ESP_OK;
}

/* Best effort even after a peripheral failure. STOP first on every slot. */
static void outputs_safe(void)
{
    for (int i = 0; i < s_cfg.count; ++i) (void)logic_set(s_cfg.pins[i].stop, 0);
    for (int i = 0; i < s_pwm_channels; ++i) {
        (void)ledc_set_duty(LEDC_LOW_SPEED_MODE, (ledc_channel_t)i, 0);
        (void)ledc_update_duty(LEDC_LOW_SPEED_MODE, (ledc_channel_t)i);
    }
    memset(s_written, 0, sizeof(s_written));
}

static esp_err_t fail(uint8_t test, esp_err_t err)
{
    outputs_safe();
    portENTER_CRITICAL(&s_lock);
    s_failed |= test;
    s_output_errors++;
    rt_motor_control_stop(&s_control, true);
    rt_motor_control_step(&s_control, esp_timer_get_time());
    portEXIT_CRITICAL(&s_lock);
    ESP_LOGE(TAG, "self-test 0x%02x: %s; sorties interdites", test, esp_err_to_name(err));
    return err;
}

static void ctrl_cycle(void)
{
    /* Read AFTER the previous PWM update has had a full control period to
     * reach the hardware. A successful API call alone is not output feedback.
     * This measures peripheral registers and STOP pads, not wheel rotation. */
    uint16_t raw[4] = {0};
    float confirmed[4] = {0};
    uint8_t stop_levels = 0, bad = 0;
    for (int slot = 0; slot < s_cfg.count; ++slot) {
        const int global = s_cfg.first_motor + slot;
        raw[global] = ledc_get_duty(LEDC_LOW_SPEED_MODE, (ledc_channel_t)slot);
        const int stop = gpio_get_level((gpio_num_t)s_cfg.pins[slot].stop);
        const int expected_stop = s_cfg.logic_inverted ? s_written[global] == 0 : s_written[global] != 0;
        stop_levels |= (uint8_t)(stop << global);
        confirmed[global] = copysignf((float)raw[global] /
            (float)((1u << s_cfg.pwm_resolution_bits) - 1u), s_written[global]);
        if (raw[global] != duty_ticks(s_written[global])) bad |= RT_MOTOR_SELFTEST_PWM;
        if (stop != expected_stop) bad |= RT_MOTOR_SELFTEST_GPIO;
        if (raw[global] != duty_ticks(s_written[global]) || stop != expected_stop)
            ESP_LOGE(TAG, "readback m%d pwm=%u/%" PRIu32 " stop=%d/%d", global,
                     raw[global], duty_ticks(s_written[global]), stop, expected_stop);
    }
    portENTER_CRITICAL(&s_lock);
    memcpy(s_confirmed, confirmed, sizeof(confirmed));
    memcpy(s_pwm_readback, raw, sizeof(raw));
    s_stop_levels = stop_levels;
    portEXIT_CRITICAL(&s_lock);
    if (bad) { (void)fail(bad, ESP_FAIL); return; }

    float applied[4];
    portENTER_CRITICAL(&s_lock);
    rt_motor_control_step(&s_control, esp_timer_get_time());
    memcpy(applied, s_control.applied, sizeof(applied));
    portEXIT_CRITICAL(&s_lock);
    /* Inhibit every inactive output first, including ones that were already
     * zero. Only then update active outputs. All writes share this one owner. */
    for (int phase = 0; phase < 2; ++phase) {
        for (int slot = 0; slot < s_cfg.count; ++slot) {
            const int global = s_cfg.first_motor + slot;
            if ((applied[global] != 0) != (phase != 0)) continue;
            const esp_err_t err = output_set(slot, applied[global]);
            if (err != ESP_OK) { (void)fail(RT_MOTOR_SELFTEST_PWM, err); return; }
            s_written[global] = applied[global];
        }
    }
}

static void ctrl_task(void *arg)
{
    (void)arg;
    if (esp_task_wdt_add(NULL) != ESP_OK) {
        (void)fail(RT_MOTOR_SELFTEST_TASK, ESP_FAIL);
        vTaskDelete(NULL);
        return;
    }
    portENTER_CRITICAL(&s_lock);
    s_passed |= RT_MOTOR_SELFTEST_TASK;
    portEXIT_CRITICAL(&s_lock);
    TickType_t wake = xTaskGetTickCount();
    for (;;) {
        vTaskDelayUntil(&wake, pdMS_TO_TICKS(5));
        if (esp_task_wdt_reset() != ESP_OK) {
            (void)fail(RT_MOTOR_SELFTEST_TASK, ESP_FAIL);
            vTaskDelete(NULL);
            return;
        }
        ctrl_cycle();
    }
}

static bool pins_valid(const rt_motors_config_t *cfg)
{
    uint64_t used = (1ULL << 1) | (1ULL << 3) | (1ULL << 4) | (1ULL << 5);
    for (int i = 0; i < cfg->count; ++i) {
        const int pins[] = {cfg->pins[i].pwm, cfg->pins[i].dir, cfg->pins[i].stop};
        for (int k = 0; k < 3; ++k) {
            const int p = pins[k];
            if (!GPIO_IS_VALID_OUTPUT_GPIO(p) || p < 0 || p > 33 ||
                p == 0 || p == 2 || (p >= 6 && p <= 12) ||
                p == 15 || p == 16 || p == 17 || (used & (1ULL << p))) return false;
            used |= 1ULL << p;
        }
    }
    return true;
}

esp_err_t rt_motors_init(const rt_motors_config_t *cfg)
{
    if (s_initialized) return ESP_ERR_INVALID_STATE;
    /* Never shift by an unchecked GPIO or array index. */
    if (!cfg || cfg->count < 1 || cfg->count > 4 || cfg->first_motor < 0 ||
        cfg->first_motor + cfg->count > 4 || cfg->pwm_resolution_bits < 1 ||
        cfg->pwm_resolution_bits > 14 || cfg->pwm_freq_hz <= 0 || !pins_valid(cfg)) {
        s_failed = RT_MOTOR_SELFTEST_CONFIG;
        s_control.fault = true;
        return ESP_ERR_INVALID_ARG;
    }
    const rt_motor_control_config_t policy = {
        .configured_mask = (uint8_t)(((1u << cfg->count) - 1u) << cfg->first_motor),
        .timeout_ms = cfg->cmd_timeout_ms, .reverse_ms = cfg->reverse_deadtime_ms,
        .slew_per_s = cfg->slew_per_s, .duty_limit = cfg->duty_limit,
    };
    if (!rt_motor_control_init(&s_control, &policy)) {
        s_failed = RT_MOTOR_SELFTEST_CONFIG;
        s_control.fault = true;
        return ESP_ERR_INVALID_ARG;
    }
    s_initialized = true;
    s_cfg = *cfg;
    s_passed = RT_MOTOR_SELFTEST_CONFIG;

    uint64_t mask = 0;
    /* Preload output latches before enabling GPIO drivers. */
    for (int i = 0; i < cfg->count; ++i) {
        logic_set(cfg->pins[i].stop, 0);
        logic_set(cfg->pins[i].dir, 0);
        mask |= (1ULL << cfg->pins[i].dir) | (1ULL << cfg->pins[i].stop);
    }
    const gpio_config_t gpio = {
        .pin_bit_mask = mask,
        .mode = cfg->logic_inverted ? GPIO_MODE_INPUT_OUTPUT : GPIO_MODE_INPUT_OUTPUT_OD,
        .pull_up_en = GPIO_PULLUP_DISABLE, .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    esp_err_t err = gpio_config(&gpio);
    if (err != ESP_OK) return fail(RT_MOTOR_SELFTEST_GPIO, err);
    for (int i = 0; i < cfg->count; ++i) {
        if (logic_set(cfg->pins[i].stop, 0) != ESP_OK ||
            logic_set(cfg->pins[i].dir, 0) != ESP_OK ||
            gpio_get_level((gpio_num_t)cfg->pins[i].stop) != (cfg->logic_inverted ? 1 : 0) ||
            gpio_get_level((gpio_num_t)cfg->pins[i].dir) != (cfg->logic_inverted ? 1 : 0)) return fail(RT_MOTOR_SELFTEST_GPIO, ESP_FAIL);
    }
    s_passed |= RT_MOTOR_SELFTEST_GPIO;

    const ledc_timer_config_t timer = {
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .duty_resolution = (ledc_timer_bit_t)cfg->pwm_resolution_bits,
        .timer_num = LEDC_TIMER_0, .freq_hz = (uint32_t)cfg->pwm_freq_hz,
        .clk_cfg = LEDC_AUTO_CLK,
    };
    err = ledc_timer_config(&timer);
    if (err != ESP_OK) return fail(RT_MOTOR_SELFTEST_PWM, err);
    for (int i = 0; i < cfg->count; ++i) {
        const ledc_channel_config_t ch = {
            .gpio_num = cfg->pins[i].pwm, .speed_mode = LEDC_LOW_SPEED_MODE,
            .channel = (ledc_channel_t)i, .intr_type = LEDC_INTR_DISABLE,
            .timer_sel = LEDC_TIMER_0, .duty = 0, .hpoint = 0,
        };
        err = ledc_channel_config(&ch);
        if (err != ESP_OK) return fail(RT_MOTOR_SELFTEST_PWM, err);
        s_pwm_channels++;
    }
    vTaskDelay(pdMS_TO_TICKS(1)); /* Duty readback is valid after the next PWM cycle. */
    if (ledc_get_freq(LEDC_LOW_SPEED_MODE, LEDC_TIMER_0) != (uint32_t)cfg->pwm_freq_hz)
        return fail(RT_MOTOR_SELFTEST_PWM, ESP_FAIL);
    for (int i = 0; i < cfg->count; ++i) {
        if (ledc_get_duty(LEDC_LOW_SPEED_MODE, (ledc_channel_t)i) != 0)
            return fail(RT_MOTOR_SELFTEST_PWM, ESP_FAIL);
    }
    s_passed |= RT_MOTOR_SELFTEST_PWM;
    if (pdMS_TO_TICKS(5) == 0 ||
        xTaskCreate(ctrl_task, "motors", 3072, NULL, 18, NULL) != pdPASS)
        return fail(RT_MOTOR_SELFTEST_TASK, ESP_ERR_NO_MEM);
    ESP_LOGI(TAG, "self-test sans mouvement: 0x%02x; roues=0x%02x; limite=%.2f",
             s_passed, policy.configured_mask, (double)cfg->duty_limit);
    return ESP_OK;
}

bool rt_motors_command(const float duty[4])
{
    portENTER_CRITICAL(&s_lock);
    const bool ok = s_initialized && rt_motor_control_command(&s_control, duty, esp_timer_get_time());
    portEXIT_CRITICAL(&s_lock);
    return ok;
}
bool rt_motors_enable(uint8_t mask)
{
    portENTER_CRITICAL(&s_lock);
    const bool ok = s_initialized && rt_motor_control_enable(&s_control, mask, esp_timer_get_time());
    portEXIT_CRITICAL(&s_lock);
    return ok;
}
bool rt_motors_session(uint32_t hash)
{
    portENTER_CRITICAL(&s_lock);
    const bool ok = rt_motor_control_session(&s_control, hash);
    portEXIT_CRITICAL(&s_lock);
    return ok;
}
void rt_motors_estop(void)
{
    portENTER_CRITICAL(&s_lock);
    rt_motor_control_stop(&s_control, false);
    portEXIT_CRITICAL(&s_lock);
}
void rt_motors_reject(void)
{
    portENTER_CRITICAL(&s_lock);
    s_control.rejected++;
    portEXIT_CRITICAL(&s_lock);
}
void rt_motors_get_state(rt_motors_state_t *out)
{
    portENTER_CRITICAL(&s_lock);
    memcpy(out->applied, s_confirmed, sizeof(out->applied));
    memcpy(out->pwm_readback, s_pwm_readback, sizeof(out->pwm_readback));
    out->stop_gpio_high = s_stop_levels;
    out->enable_mask = s_control.enable_mask;
    out->flags = s_control.flags |
        (s_control.fault ? RT_MOTOR_FLAG_OUTPUT_FAULT : 0) |
        (s_control.estop ? RT_MOTOR_FLAG_ESTOP : 0) |
        (!s_control.protocol_ok ? RT_MOTOR_FLAG_PROTOCOL_BLOCKED : 0) |
        (!s_control.ever_armed ? RT_MOTOR_FLAG_NEVER_ARMED : 0);
    if (!s_control.enable_mask) out->flags &= ~RT_MOTOR_FLAG_ENABLED;
    out->cmd_age_ms = s_control.have_command ? s_control.cmd_age_ms : 65535;
    out->configured_mask = s_control.cfg.configured_mask;
    out->selftest_passed = s_passed;
    out->selftest_failed = s_failed;
    out->rejected = s_control.rejected;
    out->output_errors = s_output_errors;
    portEXIT_CRITICAL(&s_lock);
}
