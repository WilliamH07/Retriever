/* ===========================================================================
 *  motors.h — pilotage de banc de N variateurs ZS-X11H
 *
 *  Une consigne par moteur en rapport cyclique signé [-1, +1], un masque
 *  d'autorisation, un chien de garde, une pente. Rien de plus : pas
 *  d'asservissement (la carte variateur a le sien), pas de retour Hall (à
 *  venir), pas de freinage (affaire de la carte motor_interface, §Z.1).
 *
 *  Copyright (c) 2026 William Hanczyk — Apache License 2.0
 * =========================================================================== */

#ifndef RT_MOTORS_H
#define RT_MOTORS_H

#include <stdbool.h>
#include <stdint.h>

#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

#define RT_MOTORS_MAX 4

typedef struct {
    int pwm;            /**< GPIO de la PWM filtrée → VR */
    int dir;            /**< GPIO DIR, drain ouvert */
    int stop;           /**< GPIO STOP, drain ouvert, actif bas côté variateur */
    const char *name;
} rt_motor_pins_t;

typedef struct {
    rt_motor_pins_t pins[RT_MOTORS_MAX];
    int count;              /**< moteurs réellement pilotés, ≤ RT_MOTORS_MAX */
    int pwm_freq_hz;
    int pwm_resolution_bits;
    uint32_t cmd_timeout_ms;
    float slew_per_s;       /**< pente max de la consigne, en unité/s */
} rt_motors_config_t;

typedef struct {
    float applied[RT_MOTORS_MAX];   /**< consigne effectivement en sortie */
    uint8_t enable_mask;
    uint8_t flags;                  /**< RT_MOTOR_FLAG_* */
    uint32_t cmd_age_ms;
} rt_motors_state_t;

/** Configure les GPIO et la PWM, tout à l'état sûr, et démarre la tâche 200 Hz. */
esp_err_t rt_motors_init(const rt_motors_config_t *cfg);

/** Dépose une consigne. Appelable depuis n'importe quelle tâche. */
void rt_motors_command(const float duty[RT_MOTORS_MAX]);

/** Dépose un masque d'autorisation. */
void rt_motors_enable(uint8_t mask);

/** Arrêt logiciel : tout à zéro, tout interdit, il faudra ré-armer. */
void rt_motors_estop(void);

/** Photo de l'état. */
void rt_motors_get_state(rt_motors_state_t *out);

#ifdef __cplusplus
}
#endif

#endif /* RT_MOTORS_H */
