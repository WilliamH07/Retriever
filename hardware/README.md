# Hardware

Everything needed to build the robot that is not code.

| Folder | Contents | State |
|---|---|---|
| [`icd.yaml`](icd.yaml) | Interface control document: every connector, every pin, every wire colour, the GPIO allocation and the measurements that block routing | v1.2, single source of truth |
| [`pcb/`](pcb/) | The three boards: `safety_power`, `motor_interface`, `safety_bus_distribution` | redesign from a clean sheet |
| [`cad/`](cad/) | Laser cut DXF profiles and mechanical notes | panels cut, STEP and native sources to publish |
| [`bom/`](bom/) | Pointer to the costed bill of materials | lives in the architecture dossier, section S |

## One rule

A pin, a connector or a wire colour is defined once, in `icd.yaml`. Board
READMEs, firmware `board_config.h` files and the harness list refer to it; they
never restate it. A change to the hardware interface is a commit to that file
first.

## How the boards fit together

<p align="center">
  <img src="../docs/images/diagrams/architecture.svg" width="100%" alt="System architecture">
</p>

`safety_bus_distribution` carries the CAN bus and the `/SAFE` line to every
node on one Micro-Fit 3.0 6-pin trunk. Each `motor_interface` sits between a
MOTION ESP32 and two ZS-X11H drivers. `safety_power` takes the battery, switches
it through a static contactor, and feeds everything else.
