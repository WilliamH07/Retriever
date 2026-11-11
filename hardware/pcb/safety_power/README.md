# safety_power

The board that decides whether the robot may move. It takes the battery,
switches it onto the DC bus through a static contactor, and hosts the SAFETY
ESP32 that grants or refuses arming.

**State: redesign from a clean sheet.** Design brief, with what must be fixed
before the schematic: [`cahier-des-charges.md`](cahier-des-charges.md). No schematic in this folder yet. The
first attempt is archived in
[`docs/archive/pcb-v1/`](../../../docs/archive/pcb-v1/).

## Scope

| Function | Decision | Source |
|---|---|---|
| Battery input | 30 to 42 V, every part on the rail rated 60 V | `11` C1 |
| Main switch | Static contactor: `TPS4810-Q1`, 2 × `IPB017N10N5` back-to-back, `SMCJ48A` drain to drain | `12`, `11` C17 |
| Precharge | 10 Ω / 25 W, τ 0.1 s, FET driven by the ESP32, not by the `TPS4810` | `11` C17 |
| Regeneration | Brake chopper, 22 Ω / 100 W, on 42.5 V, off 41.8 V, mandatory | `11` C-S2 |
| Fusing | `BF1 58V` in MIDI 498 holders; MRBF 80 A at the battery | `11` C-S3 |
| Measurement | `INA228`: bus voltage, current, energy | `11` C8 |
| Branch protection | `TPS26630` / `TPS26620` on 42 V, `TPS259573` on 12 V and 5 V | `11` C10 |
| Rails | 12 V for the X1, 5 V logic, from the 42 V bus | `11` C3 |
| Hosted peripherals | BNO085 on a remote mast, two PWM fans, front and rear WS2812B, 3-pin temperature sensor | `11` C3 |
| Layout rule | Strict power and signal zones, single `★ GND STAR` | `11` C3 |

## Blocking measurements

M1 (BMS cut-off), M2 (pack resistance), M10 (bus capacitance), M12 (driver
input capacitor rating) and PACK_ID (pack and BMS labels). See
[`docs/measurements/`](../../../docs/measurements/).

Pinout: `boards.safety_power` in [`hardware/icd.yaml`](../../icd.yaml).

<p align="center">
  <img src="../../../docs/images/diagrams/power-chain.svg" width="100%" alt="Power chain">
</p>
