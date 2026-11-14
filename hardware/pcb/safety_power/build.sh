#!/bin/sh
# Regenerate schematic and board, route, fill, check.
#   ./build.sh            full build (Freerouting, ~25 min)
#   ./build.sh --no-route placement and power copper only
set -e
cd "$(dirname "$0")"
KP=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
PCB=kicad/safety_power.kicad_pcb
mkdir -p build
quiet() { grep -v -i -e swig -e "assert" -e fontconfig || true; }
"$KP" scripts/build.py pcb 2>&1 | quiet
kicad-cli pcb drc --refill-zones --save-board -o build/drc-fill.rpt "$PCB" >/dev/null 2>&1 || true
if [ "$1" != "--no-route" ]; then
  "$KP" scripts/build.py route 2>&1 | quiet | { grep -v INFO || true; }
  kicad-cli pcb drc --refill-zones --save-board -o build/drc-fill.rpt "$PCB" >/dev/null 2>&1 || true
  # clean-up: drop what KiCad's DRC rejects, then finish the open connections, twice over
  for step in drop patch patch drop patch; do
    kicad-cli pcb drc -o build/drc.rpt --severity-all "$PCB" >/dev/null 2>&1 || true
    "$KP" scripts/build.py $step 2>&1 | quiet
    kicad-cli pcb drc --refill-zones --save-board -o build/drc-fill.rpt "$PCB" >/dev/null 2>&1 || true
  done
fi
kicad-cli sch erc -o build/erc.rpt --severity-all kicad/safety_power.kicad_sch 2>/dev/null | tail -1
kicad-cli pcb drc -o build/drc.rpt --schematic-parity --severity-all "$PCB" 2>/dev/null | tail -3
grep -E "^\[" build/drc.rpt | sed 's/:.*//' | sort | uniq -c || true
