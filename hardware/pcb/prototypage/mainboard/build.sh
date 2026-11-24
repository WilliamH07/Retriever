#!/bin/sh
# Regenerate schematic and board, route, fill, check.
#   ./build.sh            full build (Freerouting, several minutes)
#   ./build.sh --no-route placement and power copper only
set -e
cd "$(dirname "$0")"
KP=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
PCB=kicad/mainboard.kicad_pcb
mkdir -p build
quiet() { grep -v -i -e swig -e "assert" -e fontconfig || true; }
"$KP" scripts/build.py pcb 2>&1 | quiet
kicad-cli pcb drc --refill-zones --save-board -o build/drc-fill.rpt "$PCB" >/dev/null 2>&1 || true
if [ "$1" != "--no-route" ]; then
  "$KP" scripts/build.py route 2>&1 | quiet | { grep -v INFO || true; }
  # clean-up: drop what KiCad's DRC rejects, then finish the open connections (patchroute), twice over
  for step in drop patch patch drop patch; do
    kicad-cli pcb drc -o build/drc.rpt --severity-all "$PCB" >/dev/null 2>&1 || true
    "$KP" scripts/build.py $step 2>&1 | quiet
    kicad-cli pcb drc --refill-zones --save-board -o build/drc-fill.rpt "$PCB" >/dev/null 2>&1 || true
  done
  "$KP" scripts/build.py stitch 2>&1 | quiet
  kicad-cli pcb drc --refill-zones --save-board -o build/drc-fill.rpt "$PCB" >/dev/null 2>&1 || true
  "$KP" scripts/build.py islands 2>&1 | quiet
  kicad-cli pcb drc --refill-zones --save-board -o build/drc-fill.rpt "$PCB" >/dev/null 2>&1 || true
  # What may remain open after this is finished by hand (decisions.md M36): the 23/11 board needed
  # about ten local repairs (vias put back, a few tracks redrawn, R29/R30 moved: MOVED_AFTER_PACK).
fi
kicad-cli sch erc -o build/erc.rpt --severity-all kicad/mainboard.kicad_sch 2>/dev/null | tail -1
kicad-cli pcb drc -o build/drc.rpt --schematic-parity --severity-all "$PCB" 2>/dev/null | tail -3
grep -E "^\[" build/drc.rpt | sed 's/:.*//' | sort | uniq -c || true
