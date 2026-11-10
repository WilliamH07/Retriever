# Bench measurements

Each of these blocks a design decision. Nothing that depends on a measurement
gets wired, or routed, before the measurement exists.

Results go here, one file per measurement, named `<id>-<short-name>.md`.
Consolidated status from
[`11-corrections-v1.2.md`](../architecture/11-corrections-v1.2.md) part 5; the
same list, with the reasons, is under `blocking_measurements` in
[`hardware/icd.yaml`](../../hardware/icd.yaml).

## Status

| ID | Measurement | Blocks | Status |
|---|---|---|---|
| PACK_ID | Photograph the pack label **and** the BMS label | `safety_power` | to do |
| M1 | BMS current cut-off threshold | `safety_power`, main fuse | to do, **safety protocol below** |
| M2 | Pack voltage at rest and under load, internal resistance | `safety_power`, fuse breaking capacity | to do |
| M3 | BMS connector logic level and pinout | — | worked around: isolator in any case |
| M4 | ZS-X11H `EL` and `STOP` polarity | firmware, population | strong consensus, to confirm; PCB no longer blocked |
| M5 | ZS-X11H jumper J1 | — | not applicable: DAC option chosen |
| M6 | Motor pole pairs | — | **answered: 15**, strong consensus |
| M7 | Hall and `SC` output level and impedance | `motor_interface` | to do, **no published source** |
| M8 | No-load and loaded current per motor | current budget, cable sizing | to do |
| M9 | X1 USB 3.0 controller model | depth camera | to do |
| M10 | Total bus input capacitance | precharge sizing | to do |
| M11 | GNSS supply voltage and protocol | power rail, ROS 2 driver | to do |
| M12 | ZS-X11H input capacitor voltage rating | `safety_power` | to do |
| P1 | ESP32 module row pitch, with calipers | all PCBs | to do |
| P2 | ESP32 module pin order, with a multimeter | GPIO allocation | to do |
| P3 | ESP32 module variant, PSRAM or not | `GPIO16` / `GPIO17` | to do |
| HALL_OC | Are the Hall outputs really open collector? | pull-up value | to do |
| HALL_COL | Hall wire colours, wire by wire | silkscreen | to do |
| TEMP_ID | Type of the 3-pin temperature sensor | — | worked around: dual footprint |

## Safety protocol for M1

40 A fuse in series, pack at 50 % state of charge or less, outdoors, dry sand
or a class D extinguisher within reach.

## Result file template

```markdown
# <id> — <name>

**Date:**
**Method:**
**Instruments:**
**Protection in place:**

## Raw data

## Result

## Decision unblocked
```
