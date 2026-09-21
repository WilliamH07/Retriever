"""Banc B2 — les variateurs ZS-X11H depuis Foxglove, via le second ESP32.

    ros2 launch retriever_bringup bench_motors.launch.py
    ros2 launch retriever_bringup bench_motors.launch.py device:=/dev/ttyUSB1
    ros2 launch retriever_bringup bench_motors.launch.py foxglove:=false

Ce que ça démarre :
  retriever_motion_bridge  la liaison série vers l'ESP32 MOTION et
                           /retriever/motor_command → MOTOR_CMD à 50 Hz
  foxglove_bridge          le pont WebSocket, port 8765

Dans Foxglove Studio (docs/foxglove/bench_motors.json) :
  - panneau Publish   /retriever/motor_enable   {enable_mask: 7}   → arme m0..m2
  - panneau Publish   /retriever/motor_command  {duty: [0.2, 0, 0, 0]}
  - panneau Publish   /retriever/estop          {}                 → tout coupe
  - panneau Plot      /retriever/motor_state.applied[0..3]
  - panneau Diagnostics  Moteurs / Liaison / Noeud MOTION_FRONT

⚠️ ROUES EN L'AIR. Un moteur brushless de trottinette à 20 % de consigne
suffit à faire partir un châssis posé au sol.

Pour lancer ce banc EN MÊME TEMPS que bench_imu : les deux pilotes publient
leurs états sous /retriever/motion/… et /retriever/… respectivement, et un seul
des deux doit démarrer foxglove_bridge (foxglove:=false sur le second).

Copyright (c) 2026 William Hanczyk — Apache License 2.0
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    device = LaunchConfiguration("device")
    baudrate = LaunchConfiguration("baudrate")
    foxglove = LaunchConfiguration("foxglove")
    port = LaunchConfiguration("foxglove_port")
    log_level = LaunchConfiguration("log_level")

    params = PathJoinSubstitution(
        [FindPackageShare("retriever_bringup"), "config", "motors_bench.yaml"]
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "device",
                default_value="/dev/ttyUSB1",
                description="Port serie de l'ESP32 MOTION. Avec deux DevKitC, "
                "`ls -l /dev/serial/by-id/` est le seul nom fiable.",
            ),
            DeclareLaunchArgument("baudrate", default_value="921600"),
            DeclareLaunchArgument("foxglove", default_value="true"),
            DeclareLaunchArgument("foxglove_port", default_value="8765"),
            DeclareLaunchArgument("log_level", default_value="info"),
            Node(
                package="retriever_link",
                executable="link_bridge",
                name="retriever_motion_bridge",
                output="screen",
                emulate_tty=True,
                parameters=[
                    params,
                    {"serial.device": device, "serial.baudrate": baudrate},
                ],
                # Les etats de liaison sont propres a CE pont ; on les range
                # sous /retriever/motion pour ne pas ecraser ceux du banc IMU
                # quand les deux tournent ensemble.
                remappings=[
                    ("retriever/link_status", "retriever/motion/link_status"),
                    ("retriever/node_status", "retriever/motion/node_status"),
                ],
                arguments=["--ros-args", "--log-level", log_level],
            ),
            Node(
                package="foxglove_bridge",
                executable="foxglove_bridge",
                name="foxglove_bridge",
                output="screen",
                condition=IfCondition(foxglove),
                parameters=[
                    {
                        "port": port,
                        "address": "0.0.0.0",
                        "use_compression": False,
                        "send_buffer_limit": 10000000,
                    }
                ],
            ),
        ]
    )
