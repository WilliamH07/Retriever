/* Retriever MOTION bench, common front/rear/four-wheel image source. Apache-2.0. */
#include <inttypes.h>
#include <string.h>
#include "esp_err.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "board_config.h"
#include "motors.h"
#include "retriever_link/link.h"
#include "retriever_link/link_log.h"

static const char *TAG = "motion";
static uint8_t s_app_passed, s_app_failed;

static bool on_frame(const rt_frame_t *f, void *user)
{
    (void)user;
    switch (f->id) {
    case RT_ID_MOTOR_CMD: {
        rt_motor_cmd_t c;
        if (!rt_motor_cmd_unpack(f, &c)) { rt_motors_reject(); return true; }
        const float duty[4] = {c.m0, c.m1, c.m2, c.m3};
        (void)rt_motors_command(duty);
        return true;
    }
    case RT_ID_MOTOR_ENABLE: {
        rt_motor_enable_t e;
        if (!rt_motor_enable_unpack(f, &e) || e.magic != 0xEBu) {
            rt_motors_reject(); return true;
        }
        (void)rt_motors_enable(e.enable_mask);
        return true;
    }
    case RT_ID_MOTOR_SESSION: {
        rt_motor_session_t s;
        if (!rt_motor_session_unpack(f, &s) || s.magic != 0xB2u) {
            rt_motors_reject(); return true;
        }
        if (s.target == BOARD_NODE_ID) (void)rt_motors_session(s.protocol_hash);
        return true;
    }
    case RT_ID_ESTOP_REQUEST: {
        rt_estop_request_t e;
        if (rt_estop_request_unpack(f, &e) && e.magic == 0xE5u) rt_motors_estop();
        else rt_motors_reject();
        return true;
    }
    case RT_ID_LINK_PING: {
        rt_link_ping_t p;
        if (!rt_link_ping_unpack(f, &p) || p.target != BOARD_NODE_ID) return true;
        const rt_link_pong_t pong = {.source = BOARD_NODE_ID, .seq = p.seq, .t_tx_us = p.t_tx_us};
        rt_frame_t out;
        rt_link_pong_pack(&pong, &out);
        rt_link_send_urgent(&out);
        return true;
    }
    default: return false;
    }
}

static uint16_t sat16(uint32_t v) { return v > 65535 ? 65535 : (uint16_t)v; }

static void housekeeping_task(void *arg)
{
    (void)arg;
    /* Publishing READY before installing the RX hook lets the host send its
     * session to a receiver that still drops commands during startup. */
    ulTaskNotifyTake(pdTRUE, portMAX_DELAY);
    TickType_t wake = xTaskGetTickCount();
    unsigned ticks = 0;
    for (;;) {
        rt_frame_t f;
        /* Bound draining so traffic from other nodes cannot starve diagnostics. */
        for (int i = 0; i < 32 && rt_link_recv(&f, 0) == ESP_OK; ++i) {}
        rt_link_stats_t st;
        rt_link_get_stats(&st);
        if (st.bus_off) rt_motors_estop(); /* Recovery never re-arms outputs. */
        rt_motors_state_t m;
        rt_motors_get_state(&m);
        rt_motor_state_t state = {
            .applied_m0 = m.applied[0], .applied_m1 = m.applied[1],
            .applied_m2 = m.applied[2], .applied_m3 = m.applied[3],
            .enable_mask = m.enable_mask, .flags = m.flags, .cmd_age_ms = sat16(m.cmd_age_ms),
        };
        rt_motor_state_pack(&state, &f);
#if CONFIG_RETRIEVER_ROLE_REAR
        f.id = RT_ID_MOTOR_STATE_REAR; /* Identical layout, distinct CAN arbitration ID. */
#endif
        rt_link_send(&f, 0);
        const rt_motor_diag_front_t diag = {
            .passed = m.selftest_passed | s_app_passed,
            .failed = m.selftest_failed | s_app_failed,
            .configured_mask = m.configured_mask, .flags = m.flags,
            .rejected = sat16(m.rejected), .output_errors = sat16(m.output_errors),
        };
        rt_motor_diag_front_pack(&diag, &f);
#if CONFIG_RETRIEVER_ROLE_REAR
        f.id = RT_ID_MOTOR_DIAG_REAR;
#endif
        rt_link_send(&f, 0);
        const uint64_t errors = (uint64_t)st.framing.crc_errors + st.framing.format_errors +
            st.framing.overflows + st.rx_dropped + st.tx_dropped + st.bus_errors +
            m.rejected + m.output_errors;
        const bool fault = diag.failed || (m.flags & RT_MOTOR_FLAG_OUTPUT_FAULT);
        const bool degraded = st.bus_off || (m.flags & RT_MOTOR_FLAG_ESTOP) ||
            ((m.flags & RT_MOTOR_FLAG_CMD_TIMEOUT) && !(m.flags & RT_MOTOR_FLAG_NEVER_ARMED));
        const rt_heartbeat_motion_front_t hb = {
            .state = fault ? RT_NODE_STATE_FAULT : (degraded ? RT_NODE_STATE_DEGRADED :
                ((m.flags & RT_MOTOR_FLAG_ENABLED) ? RT_NODE_STATE_ACTIVE : RT_NODE_STATE_READY)),
            .uptime_s = (uint16_t)(esp_timer_get_time() / 1000000),
            .err_count = errors > 255 ? 255 : (uint8_t)errors, .protocol_hash = RT_PROTOCOL_HASH,
        };
        rt_heartbeat_motion_front_pack(&hb, &f);
#if CONFIG_RETRIEVER_ROLE_REAR
        f.id = RT_ID_HEARTBEAT_MOTION_REAR;
#endif
        rt_link_send(&f, 0);
        if (++ticks % 10 == 0) {
            ESP_LOGI(TAG, "%s roues=0x%02x selftest=%02x/%02x masque=%02x flags=%02x age=%" PRIu32
                     "ms rejetees=%" PRIu32 " erreurs-sortie=%" PRIu32,
                     BOARD_ROLE_NAME, m.configured_mask, diag.passed, diag.failed,
                     m.enable_mask, m.flags, m.cmd_age_ms, m.rejected, m.output_errors);
            ESP_LOGI(TAG, "readback pwm=[%u,%u,%u,%u] stop_gpio_high=0x%02x",
                     m.pwm_readback[0], m.pwm_readback[1], m.pwm_readback[2], m.pwm_readback[3],
                     m.stop_gpio_high);
        }
        vTaskDelayUntil(&wake, pdMS_TO_TICKS(100));
    }
}

void app_main(void)
{
    const rt_motor_pins_t pins[4] = BOARD_MOTOR_TABLE;
    rt_motors_config_t cfg = {
        .count = CONFIG_RETRIEVER_MOTOR_COUNT, .first_motor = BOARD_FIRST_MOTOR,
        .pwm_freq_hz = BOARD_PWM_FREQ_HZ, .pwm_resolution_bits = BOARD_PWM_RESOLUTION_BITS,
#if CONFIG_RETRIEVER_MOTOR_LOGIC_INVERTED
        .logic_inverted = true,
#endif
        .cmd_timeout_ms = CONFIG_RETRIEVER_MOTOR_CMD_TIMEOUT_MS,
        .reverse_deadtime_ms = CONFIG_RETRIEVER_MOTOR_REVERSE_DEADTIME_MS,
        .slew_per_s = CONFIG_RETRIEVER_MOTOR_SLEW_PER_S / 1000.0f,
        .duty_limit = CONFIG_RETRIEVER_MOTOR_DUTY_LIMIT_MILLI / 1000.0f,
    };
    memcpy(cfg.pins, pins, sizeof(pins));
    const esp_err_t motor_err = rt_motors_init(&cfg); /* Zero outputs before communications. */
    rt_link_config_t link = RT_LINK_CONFIG_BENCH_DEFAULT();
    link.node_id = BOARD_NODE_ID;
#if CONFIG_RETRIEVER_LINK_BACKEND_TWAI
    link.backend = RT_LINK_BACKEND_TWAI;
#endif
    const esp_err_t link_err = rt_link_init(&link);
    if (link_err != ESP_OK) {
        rt_motors_estop();
        ESP_LOGE(TAG, "liaison: %s; aucun armement possible", esp_err_to_name(link_err));
        return;
    }
    s_app_passed |= RT_MOTOR_SELFTEST_LINK;
#if CONFIG_RETRIEVER_LINK_CONSOLE_TUNNEL && !CONFIG_RETRIEVER_LINK_BACKEND_TWAI
    rt_link_log_install(); /* Shared LOG ID is only appropriate on a point-to-point bench. */
#endif
    ESP_LOGI(TAG, "motion %s: protocole %s 0x%08" PRIX32 "; init=%s",
             BOARD_ROLE_NAME, RT_PROTOCOL_VERSION, (uint32_t)RT_PROTOCOL_HASH, esp_err_to_name(motor_err));
    /* Start diagnostics even if the motor self-test failed. Never accept enable
     * until both output and housekeeping tasks have been created. */
    TaskHandle_t house_task = NULL;
    if (xTaskCreate(housekeeping_task, "house", 4096, NULL, 5, &house_task) != pdPASS) {
        s_app_failed |= RT_MOTOR_SELFTEST_TASK;
        rt_motors_estop();
        ESP_LOGE(TAG, "tache diagnostic absente: armement interdit");
        return;
    }
    if (motor_err == ESP_OK) rt_link_set_rx_hook(on_frame, NULL);
    xTaskNotifyGive(house_task);
}
