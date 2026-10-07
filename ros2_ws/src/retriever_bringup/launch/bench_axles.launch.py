"""Deux ESP MOTION sur deux ports USB : commande commune, retours par essieu.

ros2 launch retriever_bringup bench_axles.launch.py front_device:=<port> rear_device:=<port>

ROUES EN L'AIR. Cette launch utilise deux liaisons serie point a point.
Copyright (c) 2026 William Hanczyk — Apache License 2.0
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    nodes = []
    for role in ("front", "rear"):
        nodes.append(Node(
            package="retriever_link",
            executable="link_bridge",
            name=f"retriever_motion_{role}",
            output="screen",
            parameters=[{
                "transport": "serial",
                "serial.device": LaunchConfiguration(f"{role}_device"),
                "serial.baudrate": 921600,
                "serial.reset_on_open": True,
                "link.peer": f"motion_{role}",
                "imu.enabled": False,
                "motors.enabled": True,
                "motors.command_timeout_s": 0.5,
                "bench.publish_tf": False,
                "bench.publish_marker": False,
            }],
            remappings=[
                (f"retriever/{topic}", f"retriever/{role}/{topic}")
                for topic in ("link_status", "node_status", "motor_state", "motor_diagnostics")
            ],
        ))
    return LaunchDescription([
        DeclareLaunchArgument("front_device", description="Port USB identifie de l'ESP avant"),
        DeclareLaunchArgument("rear_device", description="Port USB identifie de l'ESP arriere"),
        DeclareLaunchArgument("foxglove", default_value="true"),
        *nodes,
        Node(
            package="foxglove_bridge", executable="foxglove_bridge", name="foxglove_bridge",
            condition=IfCondition(LaunchConfiguration("foxglove")),
            parameters=[{"port": 8765, "address": "0.0.0.0"}],
        ),
    ])
