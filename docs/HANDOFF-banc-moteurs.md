# HANDOFF — banc moteurs, trois ZS-X11H depuis Foxglove

**État au 21 septembre 2026.** Branche `feat/link-layer-and-imu-bench`. Troisième
banc après [l'IMU](HANDOFF-banc-imu.md) et [le lidar](HANDOFF-banc-lidar.md).
⚠️ **Écrit avant le premier essai matériel** : tout est codé, vérifié par les
tests hôte et la génération du protocole, mais **rien n'a encore fait tourner
une roue**. La section 3 dit exactement ce qu'il reste à constater.

---

## 1. Ce qui a été construit

Un **second ESP32 DevKitC** dédié, identité `MOTION_FRONT`, sur un second port
série. Il ne touche pas au nœud SAFETY ni à l'IMU.

```
Foxglove ──ws──▶ foxglove_bridge ──▶ retriever_motion_bridge ──série──▶ esp32_motion ──PWM+RC/DIR/STOP──▶ 3× ZS-X11H
   Publish /retriever/motor_enable        MOTOR_ENABLE 0x111 (magic 0xEB)
   Publish /retriever/motor_command       MOTOR_CMD    0x110 à 50 Hz
   Publish /retriever/estop               ESTOP_REQUEST 0x020 (magic 0xE5)
   Plot    /retriever/motor_state   ◀──   MOTOR_STATE  0x1A0 à 10 Hz
                                          HEARTBEAT_MOTION_FRONT 0x702 à 10 Hz
```

| Couche | Fichiers | Notes |
|---|---|---|
| Protocole | `firmware/protocol/protocol.yaml` — `MOTOR_CMD`, `MOTOR_ENABLE`, `MOTOR_STATE`, enum `motor_flag` | hash `0x670192A7`, 33 trames. `MOTOR_CMD` porte **quatre** consignes i16 ×0,001 |
| Firmware | `firmware/esp32_motion/` — `board_config.h` (table de 4 moteurs), `motors.c` (tâche 200 Hz, chien de garde, pente, masque), `main.c` | `CONFIG_RETRIEVER_MOTOR_COUNT` = 3, passer à 4 quand m3 est câblé |
| Messages | `retriever_msgs/msg/MotorCommand` (`duty[4]`), `MotorEnable`, `MotorState` | |
| Pont | `retriever_link/src/bridge_node.cpp` — paramètres `link.peer`, `imu.enabled`, `motors.*` | **un seul exécutable** pour les deux bancs ; c'est le YAML qui fait la différence |
| Lancement | `bench_motors.launch.py`, `config/motors_bench.yaml` | états de liaison remappés sous `/retriever/motion/` pour cohabiter avec le banc IMU |
| Foxglove | `docs/foxglove/bench_motors.json` | ARMER / consigne / STOP / ESTOP, tracés `applied[0..3]` |
| Sans ROS | `tools/motor_bench.py` | pour valider le firmware depuis le Mac, avant Ubuntu |
| Doc | `docs/DEMARRAGE.md` §4 quater | câblage RC, ajout du 4ᵉ moteur, les trois chiens de garde |

### Décisions prises, et pourquoi

- **Consigne VR = PWM 20 kHz + RC 1 kΩ / 2,2 µF**, pas de CNA externe (choix de
  William). Pleine échelle ≈ 3,0 V donc ~60 % de la vitesse max : suffisant
  pour le banc, à corriger sur le PCB.
- **DIR / STOP en open-drain** : aucun 5 V de la carte ne peut remonter.
- **L'encodeur reste géré par la carte** pour l'instant ; les trames
  `FB_WHEELS_*` du protocole sont prêtes pour quand on récupérera les Hall.
- **Rien ne tourne sans `MOTOR_ENABLE` explicite** (drapeau `NEVER_ARMED` au
  démarrage). Un reset de l'ESP32 désarme tout.
- **Pente à l'accélération seulement** (`RETRIEVER_MOTOR_SLEW_PER_S` = 2,0/s) ;
  un arrêt ou une inversion est immédiat.
- **Deux chiens de garde** : firmware 500 ms sans `MOTOR_CMD` ; pont 10 s sans
  message ROS (le panneau Publish n'émet qu'au clic, il faut le temps de
  regarder la roue). Ne pas confondre les deux : le premier est la sécurité,
  le second un confort de banc.

---

## 2. Ce qui a été vérifié

- `python3 firmware/protocol/generate.py --check` : OK, les trois cibles
  (C, C++, tables markdown) sont à jour.
- `make -C firmware/test` : les tests hôte passent sur les 33 trames, vecteurs
  croisés C ↔ Python inclus (`tools/check_protocol_sync.py`).
- Tous les identifiants générés utilisés par `motors.c`, `main.c` et
  `bridge_node.cpp` (`rt_motor_*`, `kMotorStateId`, `RT_MOTOR_FLAG_*`,
  `unpack_heartbeat_motion_front`…) existent dans les en-têtes générés.
- ⚠️ **Non vérifié** : la compilation ESP-IDF de `esp32_motion` et la
  compilation `colcon` du pont modifié — ni ESP-IDF ni ROS ne sont
  disponibles dans l'environnement où ce code a été écrit. C'est la première
  chose à faire (section 3).

---

## 3. Ce qui reste, dans l'ordre

1. **Compiler.** `idf.py build` dans `firmware/esp32_motion` (Mac), puis
   `colcon build --symlink-install` sur Ubuntu. Les erreurs éventuelles seront
   de typographie, pas de conception.
2. **Flasher le second DevKitC** et lancer `tools/motor_bench.py` **sans
   variateur branché** : battement, hash, `NEVER_ARMED` → `ENABLED`.
3. **Un variateur, une roue en l'air.** `--enable 1 --duty 0.2 0 0 0` : sens,
   pente, arrêt au bout de 3 s. Mesurer VR au voltmètre : ~0,6 V à 0,2 de
   consigne. Si la roue ne tourne pas : vérifier STOP (doit être **haut** pour
   tourner) et la masse commune.
4. **Le test du câble arraché** : la roue doit s'arrêter sous 500 ms.
5. **Les trois**, puis Foxglove via `bench_motors.launch.py`.
6. **Le quatrième moteur** : câbler m3, `CONFIG_RETRIEVER_MOTOR_COUNT=4`,
   `enable_mask: 15`.

### Plus tard, hors banc

- Retour Hall → `FB_WHEELS_*`, puis consigne en rad/s et `ros2_control`.
- VR à 5 V pleine échelle sur le PCB.
- EL / BRAKE.
- Un téléop qui republie en continu (le délai de 10 s du pont redescend alors
  à 0,5 s).
- Le nœud `MOTION_REAR` du dossier, quand il y aura deux cartes.
