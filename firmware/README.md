# Firmware

Three ESP32 nodes in the target architecture. The IMU bench runs on
`esp32_safety`; the motor bench now has front, rear and single-ESP profiles.
Setup and commissioning: [`esp32_motion/README.md`](esp32_motion/README.md).

| Node | Role | State |
|---|---|---|
| `esp32_safety/` | Safety state machine, current budget, watchdogs, precharge, contactor, BMS telemetry, and the BNO085 IMU. | **IMU chain only.** No safety function is implemented, and none can be validated on the serial bench. |
| `esp32_motion/` | Front/rear units, or one bench unit controlling up to four ZS-X11H drivers. | PWM/RC bench, software self-test, gated arming, watchdog and telemetry. Hall feedback and final PCB DAC/safety drivers remain to implement. |

## Layout

```
protocol/      protocol.yaml — the single source of truth — and its generator
components/    shared between every node
  retriever_protocol/   the generated header
  retriever_link/       transport-agnostic link layer
    portable/           C99, no ESP-IDF: compiled by the firmware AND by ROS 2
  retriever_imu/        BNO085 behind a four-function interface
esp32_safety/  the IMU ESP-IDF project
esp32_motion/  common front/rear/four-wheel ESP-IDF project
test/          host tests — no hardware, no ESP-IDF, no ROS
```

## The one idea worth knowing

Application code only ever sees `rt_frame_t`: an 11 bit identifier and at most
eight bytes. It does not know whether those frames travel over a CAN bus or a
USB cable. Today they travel over serial, because the CAN distribution board
does not exist yet. When it does, one Kconfig option switches the firmware and
one launch parameter switches the computer. Both CAN backends are already
written — `link_twai.c` and `socketcan_transport.cpp` — and their size is the
measure of whether the abstraction sits in the right place.

⚠️ Serial gives no arbitration, no acknowledgement, no retransmission and no
fault confinement. **No safety function is validated on it**, and stop levels
N4 and N5 stay in hardware where they belong. Section AB.5 of the architecture
document is the full list.

## Build

Full setup — toolchain, drivers, port, and how to check the result — is in
[`docs/DEMARRAGE.md`](../docs/DEMARRAGE.md). The short version:

```bash
git submodule update --init --recursive     # or tools/fetch_firmware_deps.sh
cd firmware/esp32_safety
idf.py set-target esp32
idf.py build flash
```

ESP-IDF v5.5. The SH-2 sensor hub stack is CEVA's, Apache 2.0, pinned as a
submodule and never modified; what belongs to this project is the port,
`sh2_hal_esp32_spi.c`.

## Host tests

```bash
make -C firmware/test          # protocol and framing, no hardware needed
python3 tools/check_protocol_sync.py
```
