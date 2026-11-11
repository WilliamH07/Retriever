# motor_interface

Sits between a MOTION ESP32 and two ZS-X11H drivers. One reference, two boards
in service (front and rear), three spares from a lot of five. The role is read
from two strap pins at boot.

**State: redesign from a clean sheet.** Design brief, with what must be fixed
before the schematic: [`cahier-des-charges.md`](cahier-des-charges.md). The specification of record is
[`10-spec-motor-interface.md`](../../../docs/architecture/10-spec-motor-interface.md).
The earlier four-motor board is archived in
[`docs/archive/pcb-v1/`](../../../docs/archive/pcb-v1/).

## Scope

| Function | Decision | Source |
|---|---|---|
| Hall feedback | Three lines per motor, `SN74LVC3G17` non-inverting buffer | `11` C7 |
| Hall conditioning | 2.2 kΩ pull-up to `+5V_MOT` on board, 2.2 kΩ series + 10 nF / 100 V, `BAT54S` clamp | `11` C7 |
| Command path | `VR`, `DIR`, `EL`, `STOP` and NTC per driver, polarity-agnostic output stage | `11` C2, M4 |
| Speed command | DAC + amplifier on `VR` (option B), jumper J1 irrelevant | `11` M5 |
| Low-side switches | `DMG1012T`, not `2N7002` | `11` C6 |
| CAN | `TCAN1042HVDR` | `11` C5 |
| GPIO | `GPIO12` never used; `GPIO16`/`17` depend on PSRAM variant | `11` C14, P3 |

## Blocking measurements

M7 (Hall output level and impedance, no published source), HALL_OC, HALL_COL,
and P1 to P3 on the ESP32 module. See
[`docs/measurements/`](../../../docs/measurements/).

Pinout: `boards.motor_interface` in [`hardware/icd.yaml`](../../icd.yaml).
