# Printed circuit boards

Three boards, **all three redesigned from a clean sheet and drawn in KiCad 10**.
Status of all three, what blocks each, what must be reviewed:
[`etat-des-lieux.md`](etat-des-lieux.md) (French). The first
pass (August–September 2026, EasyEDA) is archived in
[`docs/archive/pcb-v1/`](../../docs/archive/pcb-v1/): its schematic was never
functional, and parts of its specification contradicted the v1.2 corrections.

**Start here:** [`conception-v2.md`](conception-v2.md) — the cross-board brief
(French): why v1 failed, design principles, decisions D1–D9 to settle, the
braking-chain defect to fix, ICD v1.3 corrections. Toolchain:
[`outils.md`](outils.md) (KiCad 10, driven from the command line).

| Board | Role | Copies | Blocked by | Design brief |
|---|---|---|---|---|
| `safety_bus_distribution` | Passive CAN + `/SAFE` trunk, protected 5 V per node, no MCU | 1 of 5 | nothing — **v2.0**, ready to order | [decisions](safety_bus_distribution/decisions.md) · [brief](safety_bus_distribution/cahier-des-charges.md) |
| `motor_interface` | Hall tap to the ESP32, command path VR / DIR / EL / STOP to two ZS-X11H | 2 of 5 | **v2.0-draft**; M7, HALL_OC, P1–P3 | [decisions](motor_interface/decisions.md) · [brief](motor_interface/cahier-des-charges.md) |
| `safety_power` | Battery input, static contactor, precharge, brake chopper, INA228, DC/DC rails, SAFETY ESP32 | 1 of 5 | **v2.0-draft**; M1, M2, M10, M12, PACK_ID, P1–P3, expert review | [decisions](safety_power/decisions.md) · [brief](safety_power/cahier-des-charges.md) |

Build order, from [`11-corrections-v1.2.md`](../../docs/architecture/11-corrections-v1.2.md)
part 6:

```
1  safety_bus_distribution   no blocking measurement, unlocks the CAN bench
2  M4, M5, M7 on one motor and one ZS-X11H, current-limited lab supply
3  Hall tap prototype on perfboard, one channel
4  motor_interface
5  PACK_ID, M1, M2, M10, M12 on the pack
6  safety_power
```

## Inputs for the redesign

| Source | What it fixes |
|---|---|
| [`../icd.yaml`](../icd.yaml) | Connectors, pinouts, wire colours, GPIO allocation |
| [`09-validation-composants.md`](../../docs/architecture/09-validation-composants.md) | Every part checked against its datasheet |
| [`10-spec-motor-interface.md`](../../docs/architecture/10-spec-motor-interface.md) | The two-motor board |
| [`11-corrections-v1.2.md`](../../docs/architecture/11-corrections-v1.2.md) | Safety-critical corrections C-S1 to C-S3, parts C5 to C17 |
| [`12-contacteur-statique.md`](../../docs/architecture/12-contacteur-statique.md) | Static contactor and precharge |

Corrections that a new schematic must carry, whatever the tool:

- `/SAFE` does not brake: ZS-X11H `STOP` is active low and coasts. Braking
  comes from `EL`, pulled up to `5V_BRAKE` on the loom (C-S1).
- The brake chopper is mandatory, 22 Ω / 100 W, on at 42.5 V, off at 41.8 V
  (C-S2).
- Every fuse on the 42 V side is rated 58 V DC: `BF1 58V` in MIDI 498 holders,
  MRBF at the battery (C-S3).
- CAN transceiver `TCAN1042HVDR`, not `SN65HVD230` (C5).
- Three Hall lines per motor through `SN74LVC3G17`, 2.2 kΩ pull-up and
  2.2 kΩ + 10 nF filter (C7).
- `INA228` current and energy monitor (C8). eFuses chosen per voltage class
  (C10). `GPIO12` never used (C14).

## What each board folder will hold

```
README.md            role, connectors, status, render
decisions.md         every design choice and its reason (French)
build.sh, fab.sh     regenerate the KiCad project, then the fabrication files
scripts/build.py     the board, described once in Python
kicad/               generated KiCad 10 project
fab/                 Gerber zip, JLCPCB BOM and placement, schematic PDF, renders
```

Fabrication output is committed so anyone can order the boards without opening
a design tool.
