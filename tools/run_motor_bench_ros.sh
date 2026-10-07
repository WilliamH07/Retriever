#!/usr/bin/env bash
# Launch the serial motor bench on the Ubuntu ROS 2 control computer.
# Copyright 2026 William Hanczyk — Apache License 2.0
set -e
usage() {
    cat <<'HELP'
Un ESP pour quatre roues : ./tools/run_motor_bench_ros.sh bench4 <port-ESP> [foxglove:=false]
Essieu avant seul : ./tools/run_motor_bench_ros.sh front <port-ESP>
Essieu arriere seul : ./tools/run_motor_bench_ros.sh rear <port-ESP>
Deux ESP sur USB : ./tools/run_motor_bench_ros.sh axles <port-avant> <port-arriere>
Utiliser les chemins /dev/serial/by-id/... sur Ubuntu.
Ce script lance la liaison et les diagnostics ; il n'arme aucun moteur.
HELP
}
case "${1:-}" in
    -h|--help|"") usage; exit 0 ;;
    bench4|front|rear) [[ $# -ge 2 ]] || { usage >&2; exit 2; } ;;
    axles) [[ $# -ge 3 ]] || { usage >&2; exit 2; } ;;
    *) usage >&2; exit 2 ;;
esac
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_dir="$(cd -- "$script_dir/.." && pwd)"
if [[ ! -f /opt/ros/jazzy/setup.bash ]]; then
    printf 'ROS 2 Jazzy absent. Lancer ce script sur le calculateur Ubuntu ROS.\n' >&2
    exit 2
fi
if [[ ! -f "$repo_dir/ros2_ws/install/setup.bash" ]]; then
    printf 'Workspace a construire :\n  source /opt/ros/jazzy/setup.bash\n  cd %s/ros2_ws\n  colcon build --symlink-install --packages-up-to retriever_bringup\n' "$repo_dir" >&2
    exit 2
fi
source /opt/ros/jazzy/setup.bash
source "$repo_dir/ros2_ws/install/setup.bash"
profile="$1"
if [[ "$profile" == axles ]]; then
    front_device="$2"
    rear_device="$3"
    if [[ "$front_device" == "$rear_device" ]]; then
        printf 'Les deux ESP doivent utiliser deux ports distincts.\n' >&2
        exit 2
    fi
    shift 3
    exec ros2 launch retriever_bringup bench_axles.launch.py \
        "front_device:=$front_device" "rear_device:=$rear_device" "$@"
else
    device="$2"
    peer=motion_front
    [[ "$profile" == rear ]] && peer=motion_rear
    shift 2
    exec ros2 launch retriever_bringup bench_motors.launch.py "device:=$device" "peer:=$peer" "$@"
fi
