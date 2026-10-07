#!/usr/bin/env bash
# Compile/flash MOTION from macOS with the installed ESP-IDF v5.5.
# Copyright 2026 William Hanczyk — Apache License 2.0
set -e
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" || $# -eq 0 ]]; then
    cat <<'HELP'
Compilation : ./tools/flash_motion_mac.sh bench4 --count 4
Televersement : ./tools/flash_motion_mac.sh bench4 --count 4 --flash --port <port-USB>
Profils : front, rear, bench4. Options supplementaires : --inverted, --transport can.
L'environnement ESP-IDF est active automatiquement. Aucun flash sans --flash.
HELP
    exit 0
fi
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
esp_idf_dir="${RETRIEVER_IDF_PATH:-$HOME/esp/esp-idf-v5.5}"
if [[ ! -f "$esp_idf_dir/export.sh" ]]; then
    printf 'ESP-IDF absent : %s\nDefinir RETRIEVER_IDF_PATH avec son emplacement.\n' "$esp_idf_dir" >&2
    exit 2
fi
source "$esp_idf_dir/export.sh"
exec python3 "$script_dir/flash_motion.py" "$@"
