# `motor_interface` — cahier des charges v2

**Statut** : spécifiée, bloquée par M7 et HALL_OC (niveaux Hall) et P1–P3 (module ESP32).
**Exemplaires** : 2 en service (avant, arrière), lot de 5, une seule référence.
**Spécification de référence** : [`10-spec-motor-interface.md`](../../../docs/architecture/10-spec-motor-interface.md).
**Brochage** : `boards.motor_interface`, `shared_pinouts`, `brake_chain`,
`gpio_allocation.motor_interface` dans [`hardware/icd.yaml`](../../icd.yaml).
**Cadre commun** : [`../conception-v2.md`](../conception-v2.md).

## 1. Rôle

Relier un ESP32 MOTION à deux variateurs ZS-X11H et à leurs deux moteurs-roues :

- **prélever** les trois signaux Hall de chaque moteur au passage, sans les
  couper : le variateur en a besoin pour commuter ;
- **commander** chaque variateur : consigne de vitesse `VR`, sens `DIR`,
  roue libre `STOP`, frein `EL` ; lire sa température `NTC` ;
- **porter** le nœud CAN et l'entrée `/SAFE`.

Le rôle avant ou arrière est lu au démarrage par l'ADS1115 sur un diviseur.
Les deux cartes sont identiques.

## 2. Connecteurs

| Repère | Rôle | Type |
|---|---|---|
| J1, J2 | Hall, côté moteur A, B | Micro-Fit 3.0, 6 pos |
| J3, J4 | Hall, côté variateur A, B (passage métallique direct de J1/J2) | Micro-Fit 3.0, 6 pos |
| J5, J6 | Commande variateur A, B : `VR`, `DIR`, `EL`, `STOP`, `NTC`, `5V_BRAKE` | Micro-Fit 3.0, 8 pos |
| J7 | Alimentation `5V_LOGIC` | Micro-Fit 3.0, 4 pos |
| J8, J9 | Dorsale CAN + `/SAFE`, entrée et sortie | Micro-Fit 3.0, 6 pos |

## 3. Blocs et composants

| Bloc | Composant | Valeur | Statut |
|---|---|---|---|
| Tap Hall, ×6 voies | pull-up vers `+5V_MOT` sur carte | 2,2 kΩ | 📐 dépend de M7, HALL_OC |
| | filtre série + condensateur | 2,2 kΩ + 10 nF / 100 V | 📐 τ 22 µs descendant, 40 µs montant |
| | clamp | `BAT54S` vers `5V_MOT` et GND | ✅ |
| | tampon non inverseur | `SN74LVC3G17`, alimenté 3,3 V | ✅ |
| Consigne `VR`, ×2 | DAC I²C 4 voies | `MCP4728`, `LDAC` à GND, EEPROM à 0 | ✅ ; ⚠️ niveau I²C à vérifier (§4) |
| | ampli | `TLV9062` | ✅ |
| | charge côté variateur | 10 kΩ vers GND, **non optionnelle** | ✅ |
| `DIR`, `STOP`, ×2 | drain ouvert | `DMG1012T` | ✅ ; polarité 🟡 (M4), étage agnostique JP1–JP3 |
| Frein `EL` | porte ET `GPIO26 · /SAFE` | `74LVC1G08` | ✅ |
| | interrupteur | `DMG1012T` tirant `EL` à la masse | ✅ |
| | pull-up | 2,2 kΩ vers `5V_BRAKE`, **sur le faisceau** | ⚠️ alimentation à corriger (§4) |
| `NTC` ×2, rôle | CAN 16 bits | `ADS1115` | ✅ ; valeurs des diviseurs à fixer |
| Watchdog | `TPL5010` | `DONE` GPIO18, `WAKE` GPIO13 | ✅ ; `DELAY` et routage de `RSTn` à fixer |
| CAN | transceiver | `TCAN1042HVDR`, `STB` à GND | ✅ |
| | protection | `NUP2105L` + `ACT45B` | ✅ |
| Alimentation | diode idéale | `LM66100` | ✅ |
| | réservoir `5V_BRAKE` | 2200 µF | ✅ |
| Module | ESP32-DevKitC V4 sur supports Mill-Max 310 | entraxe 25,40 mm | 📐 à confirmer par P1 |

Affectation GPIO : ICD `gpio_allocation.motor_interface`. Interdits : 0–3, 6–12.
16 et 17 en réserve, sous condition de P3.

## 4. À corriger avant schéma

### 🔴 Critiques

1. **Le frein se relâche si la carte est débranchée.** `5V_BRAKE` alimente le
   pull-up du faisceau par J5/J6 broche 7, donc par la carte. Carte débranchée,
   `EL` retombe. → décision D5 de [`conception-v2.md`](../conception-v2.md) :
   ligne `5V_BRAKE` dédiée, indépendante de cette carte.
2. **Aucune entrée `5V_BRAKE`** : ni J7 ni la dorsale ne la portent. À régler avec
   le point 1.
3. **L'étage agnostique ne doit pas toucher `EL`.** Les options pull-down et
   inverseur sur `EL` casseraient le fail-safe. Le limiter à `DIR` et `STOP`.

### 🟠 À compléter

4. **Liaison `GND_MOT`–`GND_LOGIC`** : les taps Hall imposent une référence
   commune. Elle doit suivre D4 (point unique sur `safety_power`) et ne pas créer
   de boucle par la dorsale.
5. **Double source 5 V** : `5V_LOGIC` arrive par J7 et par la broche 1 de la
   dorsale. Une seule source, ou une règle de priorité par diode.
6. **Pull-downs de grille** : un sur l'entrée `GPIO26` de la porte, un sur chaque
   grille `DIR`/`STOP`. Le schéma actuel n'en montre qu'un.
7. **`MCP4728` en 5 V** : son seuil haut I²C est probablement de 0,7 × VDD, au-dessus
   d'un bus 3,3 V. Vérifier sur datasheet ; sinon translateur, ou DAC en 3,3 V avec
   un gain de 1,515.
8. **ADS1115** : adresse, alimentation, pull-up et coefficient B des NTC, valeurs
   du diviseur de rôle.
9. **Origine des rails 3,3 V et 5 V** des circuits annexes (régulateur du module,
   amont ou aval du `LM66100`).
10. **LED « frein serré »** : tampon tolérant 5 V à compter.
11. **Révision matérielle** lisible par le firmware (diviseur ou straps), publiée
    dans le heartbeat.
12. **`DMG1012T` en SOT-523** : difficile à retoucher. Repli `BSS138` en SOT-23
    à évaluer.

## 5. Mesures bloquantes

| Mesure | Ce qu'elle change |
|---|---|
| **M7** niveau, impédance, type des sorties Hall | pull-up, rail du clamp |
| **HALL_OC** collecteur ouvert ou push-pull ? | si push-pull : pas de pull-up, conflit possible |
| **HALL_COL** couleurs des fils | sérigraphie |
| **P1** entraxe des rangées du DevKitC | empreinte du support : toute la carte |
| **P2** ordre des broches | affectation |
| **P3** variante PSRAM | GPIO16/17 |
| **M4** polarité `EL`/`STOP` | peuplement, polarité firmware (la carte n'est plus bloquée) |

## 6. Recette de mise en route (à détailler)

1. Hors module : continuité Hall J1→J3, J2→J4, aucune résistance série.
2. Module posé, sans variateur : `VR` 0 V au démarrage, `EL` haut tant que
   `GPIO26` et `/SAFE` ne sont pas tous deux hauts.
3. Retirer l'ESP32 de son support : frein serré.
4. Couper `/SAFE` : frein serré en moins de 10 ms.
5. Débrancher la carte entière : frein serré (vérifie la correction D5).
6. Un moteur tourné à la main : six fronts par pas électrique sur les trois voies,
   propres à l'oscilloscope.

## 7. Firmware associé

Le firmware de banc `esp32_motion` **ne doit pas être flashé sur la carte** : son
brochage entre en conflit sur huit GPIO (18 nourrirait le watchdog en continu,
19 piloterait `/SAFE`, 26 serait `DIR` au lieu du frein). `board_config.h` sera
réécrit depuis l'ICD en même temps que le schéma. Sur perte de consigne, la
carte doit **freiner**, pas passer en roue libre comme le banc actuel.
