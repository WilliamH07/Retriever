#!/bin/sh
# Fabrication outputs for JLCPCB, from the committed board. Run after ./build.sh.
# Everything in fab/ is generated: never edit it by hand.
set -e
cd "$(dirname "$0")"
KP=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
PCB=kicad/motor_interface.kicad_pcb
SCH=kicad/motor_interface.kicad_sch
OUT=fab
rm -rf "$OUT" && mkdir -p "$OUT/gerbers"
q() { grep -v -i -e fontconfig -e swig -e assert || true; }

kicad-cli pcb export gerbers -o "$OUT/gerbers/" \
  --layers F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts \
  --subtract-soldermask "$PCB" 2>&1 | q | tail -1
kicad-cli pcb export drill -o "$OUT/gerbers/" --format excellon --excellon-separate-th \
  --generate-map --map-format gerberx2 "$PCB" 2>&1 | q | tail -1
(cd "$OUT/gerbers" && zip -q -r ../motor_interface_gerbers.zip .)

"$KP" ../scripts/fab.py "$PCB" "$OUT" 2>&1 | q
kicad-cli sch export pdf -o "$OUT/schematic.pdf" "$SCH" 2>&1 | q | tail -1
kicad-cli pcb export pdf -o "$OUT/assembly_top.pdf" --layers F.Fab,F.Silkscreen,Edge.Cuts \
  --mode-single "$PCB" 2>&1 | q | tail -1
kicad-cli pcb render -o "$OUT/render_top.png" --width 2000 --height 1300 --side top \
  --background opaque --quality high "$PCB" 2>&1 | q | tail -1
kicad-cli pcb render -o "$OUT/render_bottom.png" --width 2000 --height 1300 --side bottom \
  --background opaque --quality high "$PCB" 2>&1 | q | tail -1
ls -1 "$OUT"
