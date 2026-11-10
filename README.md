<div align="center">

# Retriever

**Open source autonomous outdoor mobile robot**

[![CI](https://github.com/WilliamH07/retriever/actions/workflows/ci.yml/badge.svg)](https://github.com/WilliamH07/retriever/actions/workflows/ci.yml)
[![Licence: Apache 2.0](https://img.shields.io/badge/code-Apache--2.0-blue.svg)](LICENSE)
[![Hardware: CERN OHL S v2](https://img.shields.io/badge/hardware-CERN--OHL--S--v2-orange.svg)](LICENSE-HARDWARE.txt)
[![ROS 2](https://img.shields.io/badge/ROS%202-Jazzy-brightgreen.svg)](https://docs.ros.org/en/jazzy/)
[![ESP-IDF](https://img.shields.io/badge/firmware-ESP--IDF-red.svg)](firmware/)
[![Status](https://img.shields.io/badge/status-in%20construction-yellow.svg)](#status)

<img src="docs/images/01-hero-front-right.png" width="760" alt="Retriever, three quarter front view">

[Architecture](docs/architecture/) ·
[Getting started](docs/DEMARRAGE.md) ·
[Bench reports](docs/bancs/) ·
[Hardware](hardware/) ·
[Support the project](#supporting-the-project)

</div>

---

## What this is

Retriever is a four wheel drive outdoor robot, built by one person and released
as open hardware. Its single objective is autonomous outdoor navigation with
ROS 2 Jazzy and Nav2, on a chassis anyone can reproduce from documented,
commodity parts.

It is an open rebuild inspired by the [Clearpath
Husky](https://clearpathrobotics.com/husky-a300-unmanned-ground-vehicle-robot/),
a reference platform in mobile robotics labs. The Husky is an excellent machine,
priced as a commercial product. Retriever asks a different question: how much of
that capability can one person reach from recovered and off the shelf parts, if
the engineering is done properly rather than cheaply?

The hardware is deliberately ordinary. The discipline applied to it is not: an
architecture dossier written before the first part was cut, a failure mode
analysis, a hardware safety chain no software can override, and a measurable
exit criterion at every stage.

## Status

<div align="center">
<img src="docs/images/diagrams/roadmap.svg" width="100%" alt="Build stages: architecture, chassis and sensors done; motor bench current; PCBs and power next; then wheels raised and autonomy">
</div>

| Stage | Exit criterion | State |
|:-----:|----------------|-------|
| 1 | Architecture dossier and CAD complete | done |
| 2 | Chassis fabricated and assembled | done |
| 2b | First sensors published to ROS 2 over a transport agnostic link | done: [IMU](docs/bancs/imu.md) at 99.8 Hz, [lidar](docs/bancs/lidar.md) |
| 2c | Motor bench: hub motors driven from Foxglove | **current**: [coded, first spin due](docs/bancs/moteurs.md) |
| 3 | Three PCBs redesigned, power chain energised, no motor connected | next |
| 4 | Motors driven, wheels raised, all stop tests pass | planned |
| 5 | Autonomous outdoor navigation to a waypoint | planned |

Beyond stage 5, the plan is to mount a [Niryo
One](https://github.com/NiryoRobotics/niryo_one) arm and turn Retriever into a
mobile manipulator.

<div align="center">
<img src="docs/images/build/p1-rolling-chassis.jpg" width="49%" alt="Frame with battery and cooling fitted">
<img src="docs/images/build/p3-hub-motors.jpg" width="49%" alt="Hub motors mounted on the frame">
</div>

## System architecture

<div align="center">
<img src="docs/images/diagrams/architecture.svg" width="100%" alt="System architecture: X1 computer, CAN bus with /SAFE line, three ESP32 nodes, motor_interface and safety_power boards, DC bus">
</div>

Three decisions shape everything else.

**A CAN bus, not USB, carries every command.** Four BLDC drivers chopping tens
of amps within 30 cm of the signal wiring make USB the wrong choice for the
control path: it is master slave, dynamically enumerated, with no frame
priority. CAN 2.0A at 500 kbit/s links the computer to every microcontroller.
USB is kept for high bandwidth perception, whose loss degrades the mission but
cannot cause dangerous motion. On the bench today the same frames travel over
serial; one Kconfig option and one launch parameter switch to CAN.

**The main computer never does real time.** It runs perception, localisation,
Nav2 and the mission, and produces setpoints. A dedicated safety
microcontroller decides whether they may be executed: the computer requests
arming, the safety node grants or refuses it.

**Safety is hardware, and independent of software.** Six stop levels, from a
100 ms software collision monitor down to a latching emergency stop and a
manual battery isolator. The last two contain no code at all.

<div align="center">
<img src="docs/images/diagrams/safety-chain.svg" width="100%" alt="Stop chain: N1 to N4 in software, N5 latching emergency stop and N6 manual isolator with no code">
</div>

## Power

<div align="center">
<img src="docs/images/diagrams/power-chain.svg" width="100%" alt="Power chain: battery, isolator, MRBF fuse, INA228 shunt, static contactor with precharge, DC bus feeding four drivers, brake chopper and DC/DC rails">
</div>

The contactor is designed onto the power board rather than bought: a
`TPS4810-Q1` driving two opposed MOSFETs cuts a fault in 4.3 µs, draws 4 mW
instead of a coil's 2 to 8 W, and can test itself. The trade off is documented
in [`12-contacteur-statique.md`](docs/architecture/12-contacteur-statique.md).

## Hardware at a glance

| | |
|---|---|
| Configuration | 4WD skid steer, outdoor |
| Structure | Aluminium extrusion frame, laser cut panels, 3D printed mounts |
| Target mass | 35 kg in running order |
| Target speed | 1.5 m/s, slopes up to 10 % |
| Drivetrain | 4 × 6.5 inch hoverboard hub motors, 250 W each, 15 pole pairs |
| Motor drivers | 4 × ZS-X11H BLDC drivers, two per motor node |
| Battery | Xiaomi M365 Pro pack, 10S4P, 37 V nominal (30 to 42 V), 474 Wh |
| Endurance | about 2 h at 200 W average (estimate, 85 % depth of discharge) |
| Compute | Youyeetoo X1 (Celeron N5105), Ubuntu 24.04, ROS 2 Jazzy |
| Real time | 3 × ESP32 (SAFETY, MOTION front, MOTION rear) on CAN 2.0A, 500 kbit/s |
| Sensors | BNO085 IMU (SPI), YDLIDAR X4, GNSS; outdoor lidar and depth camera wanted |
| Localisation | GNSS, IMU and wheel odometry, dual EKF |
| Navigation | Nav2, collision monitor, twist mux |

## Repository layout

```
docs/
  architecture/   the design dossier: 00–07 base, 08–12 PCB and errata, 13 software
  bancs/          bench reports: IMU, lidar, motors (French)
  DEMARRAGE.md    getting started, from a blank machine to /imu/data (French)
  measurements/   bench measurements that gate the hardware design
  foxglove/       Foxglove Studio layouts for each bench
  images/         renders, build photos, diagrams
  sponsorship/    the sponsorship dossier
  archive/        superseded work, kept for history
hardware/
  icd.yaml        interface control document: every connector, every pin
  pcb/            the three boards, being redesigned
  cad/            laser cut DXF profiles, mechanical notes
  bom/            pointer to the costed bill of materials
firmware/
  protocol/       protocol.yaml, the single source of truth, and its generator
  components/     link layer, protocol header, BNO085 driver
  esp32_safety/   safety node (IMU bench today)
  esp32_motion/   motor node, front and rear
  test/           host tests, no hardware needed
ros2_ws/src/
  retriever_link/       transport agnostic bridge: serial today, SocketCAN later
  retriever_protocol/   generated protocol header for ROS 2
  retriever_msgs/       message definitions
  retriever_bringup/    launch files and bench configurations
  retriever_*           description, hardware, control, navigation, teleop: planned
tools/            bench scripts, flashing, protocol and link checks
```

## Documentation

The design documentation is in French; an English summary is planned. Every
claim carries a marker: verified against a datasheet, community consensus, to
be measured, or an explicit assumption.

| Start with | Why |
|---|---|
| [Documentation index](docs/README.md) | One page that says what each document is for and whether it is current |
| [Démarrage](docs/DEMARRAGE.md) | Install, flash an ESP32, build the workspace, verify the IMU chain stage by stage |
| [Bench reports](docs/bancs/) | What runs today, with measured numbers, and the silent defects found on the way |
| [Architecture dossier](docs/architecture/) | Power, communications, ROS 2, safety, network, BOM and FMEA, operator console |
| [Corrections v1.2](docs/architecture/11-corrections-v1.2.md) | Takes precedence over 00–07 wherever they disagree |

## Supporting the project

Retriever is self funded by a student. Four items stand between the current
platform and autonomous outdoor operation:

- **Printed circuit boards.** Three boards are being redesigned from a clean
  sheet: a motor interface, a safety and power board, and a passive CAN and
  safety bus distribution board.
- **Embedded AI compute.** The current x86 board runs the navigation stack, but
  not the perception outdoor autonomy asks for.
- **An outdoor lidar.** The blocking item. The 2D lidar on hand is specified for
  indoor use, and direct sunlight saturates its receiver.
- **A depth camera.** The Kinect v2 on hand is blind in daylight and its driver
  has been unmaintained since 2021.

Sponsors get a written and filmed integration tutorial for the sponsored part,
a field test video with honest performance data, attribution on the chassis and
here, and private feedback on how the part behaves on a real robot before
anything is published.

The full dossier is in [docs/sponsorship](docs/sponsorship/). Enquiries welcome:
see contact below.

## Credits

Inspired by the Clearpath Husky platform. The mechanical design was modelled
from scratch and the electrical and software architecture designed
independently. Some ROS 2 package conventions follow the open source
[husky/husky](https://github.com/husky/husky) repository, published under BSD 3
Clause. Clearpath Robotics is not affiliated with this project and does not
endorse it.

See [CREDITS.md](CREDITS.md) for the full attribution, and
[CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

## Licence

Software and firmware are released under the [Apache License 2.0](LICENSE).
Hardware designs, CAD and PCB files are released under the [CERN Open Hardware
Licence Version 2, Strongly Reciprocal](LICENSE-HARDWARE.txt).

## Contact

William Hanczyk, Bordeaux, France
wcontact33@gmail.com
