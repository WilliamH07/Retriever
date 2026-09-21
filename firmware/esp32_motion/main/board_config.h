/* ===========================================================================
 *  board_config.h — nœud MOTION, affectation des broches du BANC
 *
 *  ⚠️ CECI EST LA CONFIGURATION DU BANC, pas celle de la carte `motor_interface`
 *  (§Z du dossier). La carte pilote VR par un DAC MCP4728 et les lignes
 *  logiques par des MOSFET DMG1012T ; le banc pilote VR par une PWM filtrée et
 *  les lignes logiques en drain ouvert directement depuis l'ESP32. Quand la
 *  carte existera, ce fichier sera mis en correspondance avec son ICD.
 *
 *  Règles de choix des broches (mêmes que le nœud SAFETY, voir son
 *  board_config.h) : jamais GPIO6-11 ni 12 ; on évite 0, 2, 15 (strapping),
 *  16, 17 (PSRAM), 34-39 (entrée seule). GPIO5 reste réservé à CAN_TX comme
 *  sur la carte finale, GPIO4 à CAN_RX.
 *
 *  ── LE VARIATEUR ZS-X11H, ce qu'il attend ✅ (§Z.1.1, mesuré à l'analyseur) ──
 *
 *      VR    0–5 V analogique     → vitesse. 10 kΩ vers GND AU PLUS PRÈS DU
 *                                   VARIATEUR, obligatoire (§F.5-L3) : un fil
 *                                   coupé donne alors consigne nulle, pas une
 *                                   entrée flottante.
 *      DIR   logique 5 V          → sens.
 *      STOP  logique 5 V          → ACTIF BAS = roue libre (« coast »).
 *                                   Haut = marche.
 *      EL    logique 5 V          → ACTIF HAUT = frein serré. Flottant ou bas
 *                                   = frein relâché. ⚠️ NON CÂBLÉ AU BANC : le
 *                                   frein reste relâché. Le freinage de
 *                                   sécurité est l'affaire de la carte (§Z.1.2),
 *                                   pas de ce firmware.
 *
 *  ── VR par PWM + RC, et ce que ça vaut ────────────────────────────────────
 *
 *      GPIO ──[ 1 kΩ ]──┬──► VR      + le 10 kΩ → GND côté variateur
 *                       │
 *                     2,2 µF
 *                       │
 *                      GND
 *
 *      PWM 20 kHz, 10 bits. Coupure RC ≈ 72 Hz : bien au-dessus des 50 Hz de
 *      la commande, bien en dessous des 20 kHz de la porteuse — ondulation
 *      résiduelle de l'ordre du millivolt.
 *
 *      ⚠️ Plein échelle ≈ 3,0 V, pas 5 : l'ESP32 sort 3,3 V, et le 10 kΩ du
 *      variateur forme un diviseur avec le 1 kΩ (10/11 = 91 %). Consigne +1
 *      = ~60 % de la vitesse maximale du moteur. C'est suffisant pour valider
 *      la chaîne de commande et faire tourner les roues ; ce n'est PAS le
 *      montage de mesure, qui attend le DAC 0–5 V de la carte.
 *
 *  ── DIR et STOP en DRAIN OUVERT ─────────────────────────────────────────────
 *
 *      Le variateur a ses propres tirages vers 5 V. En drain ouvert, l'ESP32
 *      ne fait que tirer à la masse : il ne source jamais 3,3 V dans un
 *      circuit 5 V, et la topologie est la même que celle de la carte finale
 *      (MOSFET drain ouvert). Niveau logique 1 = broche relâchée = tiré à 5 V
 *      par le variateur ; niveau 0 = tiré à la masse.
 *
 *      ⚠️ Conséquence pour STOP, actif bas : GPIO à 0 = STOP tiré bas = roue
 *      libre. C'est l'état de reset de l'ESP32 (tout à la masse ou flottant),
 *      donc l'état sûr est aussi l'état par défaut. C'est voulu.
 *
 *  Copyright (c) 2026 William Hanczyk — Apache License 2.0
 * =========================================================================== */

#ifndef RETRIEVER_BOARD_CONFIG_H
#define RETRIEVER_BOARD_CONFIG_H

#include "retriever_protocol.h"

/* --- Liaison : même chose que le nœud SAFETY ------------------------------ */
#define BOARD_LINK_UART_NUM  0
#define BOARD_LINK_UART_TX   1
#define BOARD_LINK_UART_RX   3
#define BOARD_LINK_BAUD      921600
#define BOARD_CAN_TX         5
#define BOARD_CAN_RX         4

/* Identité sur le bus. Le dossier prévoit MOTION_FRONT et MOTION_REAR à deux
 * roues chacun ; le banc n'a qu'un nœud pour tous les moteurs, il prend
 * l'identité FRONT. Le heartbeat 0x702 et le LINK_PONG le disent. */
#define BOARD_NODE_ID        RT_NODE_ID_MOTION_FRONT

/* --- Moteurs ---------------------------------------------------------------
 *
 *  Une ligne par moteur, QUATRE lignes. Le nombre de moteurs réellement
 *  pilotés est CONFIG_RETRIEVER_MOTOR_COUNT (menuconfig → Retriever →
 *  Moteurs) : 3 aujourd'hui. Câbler le quatrième = brancher les trois fils de
 *  la ligne 3 et passer l'option à 4. Rien d'autre ne change : ni le
 *  protocole, ni le nœud ROS, ni la mise en page Foxglove.
 *
 *       moteur   PWM→VR   DIR   STOP
 */
#define BOARD_MOTOR_TABLE                                                       \
    {                                                                          \
        {.pwm = 25, .dir = 26, .stop = 27, .name = "m0"},                      \
        {.pwm = 32, .dir = 33, .stop = 14, .name = "m1"},                      \
        {.pwm = 18, .dir = 19, .stop = 21, .name = "m2"},                      \
        {.pwm = 22, .dir = 23, .stop = 13, .name = "m3 (reserve)"},            \
    }

#define BOARD_MOTOR_TABLE_SIZE  4      /* la taille de la table, PAS le nombre pilotés */
#define BOARD_PWM_FREQ_HZ       20000
#define BOARD_PWM_RESOLUTION_BITS 10

#endif /* RETRIEVER_BOARD_CONFIG_H */
