/* ===========================================================================
 *  motors.c — voir motors.h
 *
 *  Structure : la réception (tâche de la liaison) DÉPOSE ; la tâche de commande
 *  à 200 Hz APPLIQUE. Même découpage que l'étalonnage de l'IMU, et pour la même
 *  raison : les périphériques ne sont touchés que par une seule tâche.
 *
 *  L'ordre des sécurités dans la boucle n'est pas arbitraire :
 *    1. chien de garde  → si le PC s'est tu, consigne nulle, quoi qu'on ait déposé
 *    2. autorisation    → un moteur non autorisé reste à zéro, STOP asserté
 *    3. pente           → la consigne autorisée est rapprochée de la cible sans
 *                         dépasser la pente, SAUF vers zéro : une coupure est
 *                         immédiate
 *
 *  Copyright (c) 2026 William Hanczyk — Apache License 2.0
 * =========================================================================== */

#include "motors.h"

#include <inttypes.h>
#include <math.h>
#include <string.h>

#include "driver/gpio.h"
#include "driver/ledc.h"
#include "esp_check.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "retriever_protocol.h"

static const char *TAG = "motors";

#define CTRL_HZ         200
#define CTRL_TASK_PRIO  18
#define CTRL_TASK_STACK 3072

static rt_motors_config_t s_cfg;
static portMUX_TYPE s_lock = portMUX_INITIALIZER_UNLOCKED;

/* --- déposé par la réception, lu par la commande ------------------------- */
static float    s_target[RT_MOTORS_MAX];
static uint8_t  s_enable_mask;
static bool     s_estop;
static bool     s_ever_armed;
static int64_t  s_last_cmd_us;      /* 0 = jamais reçu */

/* --- écrit par la tâche de commande, lu partout : sous verrou ------------- */
static float    s_applied[RT_MOTORS_MAX];
static uint8_t  s_flags;
static uint32_t s_cmd_age_ms;

static inline float clampf(float v, float lo, float hi)
{
    return v < lo ? lo : (v > hi ? hi : v);
}

/* --------------------------------------------------------------------------
 *  Sorties
 * ----------------------------------------------------------------------- */

static void output_set(int i, float duty)
{
    const rt_motor_pins_t *p = &s_cfg.pins[i];
    const bool run = fabsf(duty) > 0.0005f;

    /* STOP d'abord quand on coupe, en dernier quand on démarre : il ne doit
     * jamais y avoir de consigne non nulle sur VR avec STOP relâché par erreur
     * dans le mauvais ordre. */
    if (!run) {
        gpio_set_level((gpio_num_t)p->stop, 0);   /* tiré bas = roue libre */
    }

    /* DIR : 1 = relâché = tiré à 5 V par le variateur. Quel sens est « avant »
     * dépend du câblage de chaque moteur ; c'est au banc de le dire, et ça se
     * corrige par le signe de la consigne côté ROS, pas ici. */
    gpio_set_level((gpio_num_t)p->dir, duty >= 0.0f ? 1 : 0);

    const uint32_t full = (1u << s_cfg.pwm_resolution_bits) - 1u;
    const uint32_t d = (uint32_t)lroundf(fabsf(duty) * (float)full);
    ledc_set_duty(LEDC_LOW_SPEED_MODE, (ledc_channel_t)i, d);
    ledc_update_duty(LEDC_LOW_SPEED_MODE, (ledc_channel_t)i);

    if (run) {
        gpio_set_level((gpio_num_t)p->stop, 1);   /* relâché = marche */
    }
}

static void outputs_all_safe(void)
{
    for (int i = 0; i < s_cfg.count; ++i) {
        output_set(i, 0.0f);
    }
    portENTER_CRITICAL(&s_lock);
    memset(s_applied, 0, sizeof(s_applied));
    portEXIT_CRITICAL(&s_lock);
}

/* --------------------------------------------------------------------------
 *  Boucle de commande
 * ----------------------------------------------------------------------- */

static void ctrl_task(void *arg)
{
    (void)arg;
    const float dt = 1.0f / (float)CTRL_HZ;
    const float step = s_cfg.slew_per_s * dt;
    TickType_t wake = xTaskGetTickCount();
    float applied[RT_MOTORS_MAX] = {0};   /* copie locale : les sorties suivent celle-ci */

    for (;;) {
        vTaskDelayUntil(&wake, pdMS_TO_TICKS(1000 / CTRL_HZ));

        /* Photo atomique de ce qui a été déposé. */
        float target[RT_MOTORS_MAX];
        uint8_t mask;
        bool estop, armed;
        int64_t last_us;
        portENTER_CRITICAL(&s_lock);
        memcpy(target, s_target, sizeof(target));
        mask = s_enable_mask;
        estop = s_estop;
        armed = s_ever_armed;
        last_us = s_last_cmd_us;
        portEXIT_CRITICAL(&s_lock);

        const int64_t now = esp_timer_get_time();
        const int64_t age_us = last_us ? (now - last_us) : INT64_MAX / 2;
        const bool timeout = age_us > (int64_t)s_cfg.cmd_timeout_ms * 1000;

        uint8_t flags = 0;
        if (!armed) flags |= RT_MOTOR_FLAG_NEVER_ARMED;
        if (estop)  flags |= RT_MOTOR_FLAG_ESTOP;
        if (timeout) flags |= RT_MOTOR_FLAG_CMD_TIMEOUT;
        if (mask & ((1u << s_cfg.count) - 1u)) flags |= RT_MOTOR_FLAG_ENABLED;

        for (int i = 0; i < s_cfg.count; ++i) {
            const bool allowed = !estop && !timeout && ((mask >> i) & 1u);
            const float goal = allowed ? clampf(target[i], -1.0f, 1.0f) : 0.0f;

            float next;
            if (goal == 0.0f || (goal > 0.0f) != (applied[i] > 0.0f)) {
                /* Coupure, ou changement de sens : on passe par zéro tout de
                 * suite. La pente ne s'applique qu'à la montée. */
                next = 0.0f;
                if (goal != 0.0f && applied[i] == 0.0f) {
                    next = clampf(goal, -step, step);
                }
            } else if (fabsf(goal) < fabsf(applied[i])) {
                next = goal;                          /* ralentir : immédiat */
            } else {
                const float delta = clampf(goal - applied[i], -step, step);
                next = applied[i] + delta;            /* accélérer : en pente */
            }

            if (next != applied[i]) {
                applied[i] = next;
                output_set(i, next);
            }
        }

        portENTER_CRITICAL(&s_lock);
        memcpy(s_applied, applied, sizeof(s_applied));
        s_flags = flags;
        s_cmd_age_ms = (age_us / 1000 > 65535) ? 65535u : (uint32_t)(age_us / 1000);
        portEXIT_CRITICAL(&s_lock);
    }
}

/* --------------------------------------------------------------------------
 *  Interface
 * ----------------------------------------------------------------------- */

esp_err_t rt_motors_init(const rt_motors_config_t *cfg)
{
    if (cfg == NULL || cfg->count < 1 || cfg->count > RT_MOTORS_MAX) {
        return ESP_ERR_INVALID_ARG;
    }
    s_cfg = *cfg;

    /* GPIO logiques en DRAIN OUVERT, à 0 (= tirés bas) AVANT toute PWM :
     * STOP bas = roue libre, c'est l'état sûr. */
    uint64_t mask = 0;
    for (int i = 0; i < s_cfg.count; ++i) {
        mask |= (1ULL << s_cfg.pins[i].dir) | (1ULL << s_cfg.pins[i].stop);
    }
    const gpio_config_t od = {
        .pin_bit_mask = mask,
        .mode = GPIO_MODE_OUTPUT_OD,
        .pull_up_en = GPIO_PULLUP_DISABLE,     /* le tirage est côté variateur, en 5 V */
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    ESP_RETURN_ON_ERROR(gpio_config(&od), TAG, "gpio drain ouvert");
    for (int i = 0; i < s_cfg.count; ++i) {
        gpio_set_level((gpio_num_t)s_cfg.pins[i].stop, 0);
        gpio_set_level((gpio_num_t)s_cfg.pins[i].dir, 0);
    }

    const ledc_timer_config_t timer = {
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .duty_resolution = (ledc_timer_bit_t)s_cfg.pwm_resolution_bits,
        .timer_num = LEDC_TIMER_0,
        .freq_hz = (uint32_t)s_cfg.pwm_freq_hz,
        .clk_cfg = LEDC_AUTO_CLK,
    };
    ESP_RETURN_ON_ERROR(ledc_timer_config(&timer), TAG, "ledc timer");

    for (int i = 0; i < s_cfg.count; ++i) {
        const ledc_channel_config_t ch = {
            .gpio_num = s_cfg.pins[i].pwm,
            .speed_mode = LEDC_LOW_SPEED_MODE,
            .channel = (ledc_channel_t)i,
            .intr_type = LEDC_INTR_DISABLE,
            .timer_sel = LEDC_TIMER_0,
            .duty = 0,
            .hpoint = 0,
        };
        ESP_RETURN_ON_ERROR(ledc_channel_config(&ch), TAG, "ledc canal %d", i);
    }

    memset(s_target, 0, sizeof(s_target));
    memset(s_applied, 0, sizeof(s_applied));
    s_enable_mask = 0;
    s_estop = false;
    s_ever_armed = false;
    s_last_cmd_us = 0;
    outputs_all_safe();

    if (xTaskCreate(ctrl_task, "motors", CTRL_TASK_STACK, NULL, CTRL_TASK_PRIO, NULL) != pdPASS) {
        return ESP_ERR_NO_MEM;
    }

    for (int i = 0; i < s_cfg.count; ++i) {
        ESP_LOGI(TAG, "%s : pwm=%d dir=%d stop=%d", s_cfg.pins[i].name,
                 s_cfg.pins[i].pwm, s_cfg.pins[i].dir, s_cfg.pins[i].stop);
    }
    ESP_LOGI(TAG, "%d moteur(s), pwm %d Hz / %d bits, chien de garde %" PRIu32 " ms, pente %.1f/s",
             s_cfg.count, s_cfg.pwm_freq_hz, s_cfg.pwm_resolution_bits,
             s_cfg.cmd_timeout_ms, (double)s_cfg.slew_per_s);
    return ESP_OK;
}

void rt_motors_command(const float duty[RT_MOTORS_MAX])
{
    portENTER_CRITICAL(&s_lock);
    memcpy(s_target, duty, sizeof(s_target));
    s_last_cmd_us = esp_timer_get_time();
    portEXIT_CRITICAL(&s_lock);
}

void rt_motors_enable(uint8_t mask)
{
    portENTER_CRITICAL(&s_lock);
    s_enable_mask = mask;
    s_ever_armed = true;
    if (mask != 0u) {
        s_estop = false;      /* ré-armer explicitement lève l'arrêt logiciel */
    }
    portEXIT_CRITICAL(&s_lock);
    ESP_LOGI(TAG, "autorisation : masque 0x%02x", (unsigned)mask);
}

void rt_motors_estop(void)
{
    portENTER_CRITICAL(&s_lock);
    s_estop = true;
    s_enable_mask = 0;
    memset(s_target, 0, sizeof(s_target));
    portEXIT_CRITICAL(&s_lock);
    ESP_LOGW(TAG, "arret logiciel : tout a zero, re-armer par MOTOR_ENABLE");
}

void rt_motors_get_state(rt_motors_state_t *out)
{
    if (out == NULL) return;
    portENTER_CRITICAL(&s_lock);
    memcpy(out->applied, s_applied, sizeof(out->applied));
    out->enable_mask = s_enable_mask;
    out->flags = s_flags;
    out->cmd_age_ms = s_cmd_age_ms;
    portEXIT_CRITICAL(&s_lock);
}
