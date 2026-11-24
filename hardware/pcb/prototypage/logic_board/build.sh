#!/bin/sh
# Regenerate schematic and board, route, fill, check.
#   ./build.sh            full build (Freerouting, about an hour; one Java process, 3 GB heap)
#   ./build.sh --no-route placement only
set -e
cd "$(dirname "$0")"
KP=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
PCB=kicad/logic_board.kicad_pcb
mkdir -p build
quiet() { grep -v -i -e swig -e "assert" -e fontconfig || true; }
python3 scripts/build.py sch
"$KP" scripts/build.py pcb 2>&1 | quiet
kicad-cli pcb drc --refill-zones --save-board -o build/drc-fill.rpt "$PCB" >/dev/null 2>&1 || true
if [ "$1" != "--no-route" ]; then
  "$KP" scripts/build.py route 2>&1 | quiet | { grep -v INFO || true; }
  # clean-up: drop what KiCad's DRC rejects, then finish the open connections (patchroute)
  for step in drop patch patch drop patch; do
    kicad-cli pcb drc -o build/drc.rpt --severity-all "$PCB" >/dev/null 2>&1 || true
    "$KP" scripts/build.py $step 2>&1 | quiet
    kicad-cli pcb drc --refill-zones --save-board -o build/drc-fill.rpt "$PCB" >/dev/null 2>&1 || true
  done
  # GND is not autorouted (fan-out vias placed with the parts, pours on both faces): stitch, merge the
  # pour groups with vias, then give a via to every GND pad still reported unconnected.
  for step in stitch join join islands; do
    "$KP" scripts/build.py $step 2>&1 | quiet
    kicad-cli pcb drc --refill-zones --save-board -o build/drc-fill.rpt "$PCB" >/dev/null 2>&1 || true
  done
  kicad-cli pcb drc -o build/drc.rpt --severity-all "$PCB" >/dev/null 2>&1 || true
  "$KP" scripts/build.py gndvias 2>&1 | quiet
  kicad-cli pcb drc --refill-zones --save-board -o build/drc-fill.rpt "$PCB" >/dev/null 2>&1 || true
fi
kicad-cli sch erc -o build/erc.rpt --severity-all kicad/logic_board.kicad_sch 2>/dev/null | tail -1
kicad-cli pcb drc -o build/drc.rpt --schematic-parity --severity-all "$PCB" 2>/dev/null | tail -3
grep -E "^\[" build/drc.rpt | sed 's/:.*//' | sort | uniq -c || true
