/* ===========================================================================
 *  main.c — nœud MOTION de Retriever, version BANC
 *
 *  Ce que fait ce firmware :
 *    - reçoit MOTOR_CMD (50 Hz) et MOTOR_ENABLE depuis le calculateur
 *    - pilote jusqu'à quatre variateurs ZS-X11H : VR par PWM filtrée,
 *      DIR et STOP en drain ouvert
 *    - ramène tout à zéro si le calculateur se tait 500 ms
 *    - publie MOTOR_STATE (10 Hz) et son heartbeat
 *
 *  Ce qu'il ne fait PAS, et pourquoi :
 *    - aucun asservissement de vitesse : la carte variateur a le sien, et le
 *      retour Hall vers l'ESP32 est une étape à part (§Z.3)
 *    - aucun freinage : le frein est actif haut sur EL et n'est pas câblé au
 *      banc. Le freinage de sécurité est l'affaire de la carte motor_interface
 *      (§Z.1.2), pas d'un GPIO d'ESP32
 *    - aucune fonction de sécurité au sens du dossier : la liaison série n'a
 *      ni arbitrage ni confinement de faute (§AB.5). Le chien de garde de
 *      consigne est une commodité de banc, pas un niveau d'arrêt.
 *
 *  ⚠️ ROUES EN L'AIR. Tant que ce firmware tourne sur le banc, le châssis est
 *  sur cales. Un curseur Foxglove lâché au mauvais moment envoie 60 % de la
 *  vitesse maximale à un moteur-roue de 35 kg.
 *
 *  Copyright (c) 2026 William Hanczyk — Apache License 2.0
 * =========================================================================== */

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
#include "retriever_protocol.h"

static const char *TAG = "motion";

#define HOUSE_TASK_PRIO 5

static uint32_t s_cmd_frames;
static uint32_t s_cmd_rejected;

/* --------------------------------------------------------------------------
 *  Réception — on DÉPOSE, la tâche moteur applique
 * ----------------------------------------------------------------------- */

static bool on_frame(const rt_frame_t *f, void *user)
{
    (void)user;

    switch (f->id) {
    case RT_ID_MOTOR_CMD: {
        rt_motor_cmd_t c;
        if (!rt_motor_cmd_unpack(f, &c)) {
            s_cmd_rejected++;
            return true;
        }
        const float duty[RT_MOTORS_MAX] = {c.m0, c.m1, c.m2, c.m3};
        rt_motors_command(duty);
        s_cmd_frames++;
        return true;
    }

    case RT_ID_MOTOR_ENABLE: {
        rt_motor_enable_t e;
        if (!rt_motor_enable_unpack(f, &e) || e.magic != 0xEBu) {
            /* Le garde n'est pas décoratif : une trame corrompue dont le CRC
             * passe ne doit pas pouvoir mettre une roue en marche. */
            s_cmd_rejected++;
            ESP_LOGW(TAG, "MOTOR_ENABLE sans garde, ignoree");
            return true;
        }
        rt_motors_enable(e.enable_mask);
        return true;
    }

    case RT_ID_ESTOP_REQUEST: {
        rt_estop_request_t r;
        if (rt_estop_request_unpack(f, &r) && r.magic == 0xE5u) {
            rt_motors_estop();
        }
        return true;
    }

    case RT_ID_LINK_PING: {
        rt_link_ping_t ping;
        if (!rt_link_ping_unpack(f, &ping) || ping.target != BOARD_NODE_ID) {
            return true;
        }
        rt_link_pong_t pong = {
            .source = BOARD_NODE_ID, .seq = ping.seq, .t_tx_us = ping.t_tx_us,
        };
        rt_frame_t out;
        rt_link_pong_pack(&pong, &out);
        rt_link_send_urgent(&out);
        return true;
    }

    default:
        return false;   /* file de réception, vidée par l'entretien */
    }
}

/* --------------------------------------------------------------------------
 *  Entretien : état moteur à 10 Hz, heartbeat, journal
 * ----------------------------------------------------------------------- */

static void housekeeping_task(void *arg)
{
    (void)arg;
    const int64_t t0 = esp_timer_get_time();
    int ticks = 0;

    for (;;) {
        rt_frame_t f;
        while (rt_link_recv(&f, 0) == ESP_OK) {
            /* TIME_SYNC est absorbée par la liaison ; le reste ne nous concerne pas. */
        }

        rt_motors_state_t m;
        rt_motors_get_state(&m);
        const rt_motor_state_t ms = {
            .applied_m0 = m.applied[0],
            .applied_m1 = m.applied[1],
            .applied_m2 = m.applied[2],
            .applied_m3 = m.applied[3],
            .enable_mask = m.enable_mask,
            .flags = m.flags,
            .cmd_age_ms = (uint16_t)m.cmd_age_ms,
        };
        rt_frame_t msf;
        rt_motor_state_pack(&ms, &msf);
        rt_link_send(&msf, 0);

        rt_link_stats_t st;
        rt_link_get_stats(&st);
        const uint32_t errs = st.framing.crc_errors + st.framing.format_errors + st.tx_dropped;
        const rt_heartbeat_motion_front_t hb = {
            .state = (m.flags & RT_MOTOR_FLAG_ENABLED) ? RT_NODE_STATE_ACTIVE : RT_NODE_STATE_READY,
            .uptime_s = (uint16_t)((esp_timer_get_time() - t0) / 1000000),
            .err_count = (uint8_t)(errs > 255u ? 255u : errs),
            .protocol_hash = RT_PROTOCOL_HASH,
        };
        rt_frame_t hbf;
        rt_heartbeat_motion_front_pack(&hb, &hbf);
        rt_link_send(&hbf, 0);

        if (++ticks % 100 == 0) {   /* toutes les 10 s */
            ESP_LOGI(TAG,
                     "cmd=%" PRIu32 " rejetees=%" PRIu32 " masque=0x%02x flags=0x%02x age=%" PRIu32
                     "ms  applique=[%.2f %.2f %.2f %.2f]  rx=%" PRIu32 " crc=%" PRIu32,
                     s_cmd_frames, s_cmd_rejected, (unsigned)m.enable_mask,
                     (unsigned)m.flags, m.cmd_age_ms, (double)m.applied[0],
                     (double)m.applied[1], (double)m.applied[2], (double)m.applied[3],
                     st.rx_frames, st.framing.crc_errors);
        }

        vTaskDelay(pdMS_TO_TICKS(100));
    }
}

/* --------------------------------------------------------------------------
 *  Démarrage
 * ----------------------------------------------------------------------- */

void app_main(void)
{
    /* Les moteurs D'ABORD, à l'état sûr, avant même que la liaison n'existe :
     * STOP tiré bas, PWM à zéro, rien d'autorisé. Si tout le reste échoue,
     * les roues sont libres et immobiles. */
    const rt_motor_pins_t table[BOARD_MOTOR_TABLE_SIZE] = BOARD_MOTOR_TABLE;
    rt_motors_config_t motors = {
        .count = CONFIG_RETRIEVER_MOTOR_COUNT,
        .pwm_freq_hz = BOARD_PWM_FREQ_HZ,
        .pwm_resolution_bits = BOARD_PWM_RESOLUTION_BITS,
        .cmd_timeout_ms = CONFIG_RETRIEVER_MOTOR_CMD_TIMEOUT_MS,
        .slew_per_s = (float)CONFIG_RETRIEVER_MOTOR_SLEW_PER_S / 1000.0f,
    };
    memcpy(motors.pins, table, sizeof(motors.pins));
    ESP_ERROR_CHECK(rt_motors_init(&motors));

    rt_link_config_t link = RT_LINK_CONFIG_BENCH_DEFAULT();
    link.uart_num = BOARD_LINK_UART_NUM;
    link.uart_tx_gpio = BOARD_LINK_UART_TX;
    link.uart_rx_gpio = BOARD_LINK_UART_RX;
    link.uart_baud = BOARD_LINK_BAUD;
    link.twai_tx_gpio = BOARD_CAN_TX;
    link.twai_rx_gpio = BOARD_CAN_RX;
    link.node_id = BOARD_NODE_ID;
#if CONFIG_RETRIEVER_LINK_BACKEND_TWAI
    link.backend = RT_LINK_BACKEND_TWAI;
#else
    link.backend = RT_LINK_BACKEND_UART;
#endif
    ESP_ERROR_CHECK(rt_link_init(&link));
    rt_link_set_rx_hook(on_frame, NULL);

#if CONFIG_RETRIEVER_LINK_CONSOLE_TUNNEL
    rt_link_log_install();
#endif

    ESP_LOGI(TAG, "retriever motion (banc) — protocole %s (0x%08" PRIX32 "), %d moteur(s)",
             RT_PROTOCOL_VERSION, (uint32_t)RT_PROTOCOL_HASH, CONFIG_RETRIEVER_MOTOR_COUNT);
    ESP_LOGW(TAG, "ROUES EN L'AIR. Rien ne tourne avant une MOTOR_ENABLE.");

    xTaskCreate(housekeeping_task, "house", 4096, NULL, HOUSE_TASK_PRIO, NULL);
}
