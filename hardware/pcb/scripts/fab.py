"""fab — JLCPCB BOM and placement (CPL) files from a KiCad board.

Run with KiCad's bundled Python:
    <KiCad python> fab.py board.kicad_pcb out_dir

Writes:
    bom_jlcpcb.csv   Comment, Designator, Footprint, LCSC Part #
    cpl_jlcpcb.csv   Designator, Mid X, Mid Y, Layer, Rotation

Footprints flagged DNP, excluded from BOM, or without an LCSC number are left
out of both files (through-hole connectors are listed: JLCPCB can solder them).
Rotation offsets between KiCad and JLCPCB's library differ for some packages;
check the placement preview on the JLCPCB order page before paying.
"""

import csv
import os
import sys
from collections import OrderedDict

import pcbnew as P


def main(pcb_path: str, out: str):
    b = P.LoadBoard(pcb_path)
    os.makedirs(out, exist_ok=True)
    origin = b.GetDesignSettings().GetAuxOrigin()
    groups = OrderedDict()
    cpl = []
    skipped = []
    for fp in sorted(b.GetFootprints(), key=lambda f: f.GetReference()):
        ref = fp.GetReference()
        lcsc = fp.GetFieldText("LCSC") if fp.HasField("LCSC") else ""
        if fp.IsDNP() or fp.IsExcludedFromBOM() or not lcsc:
            skipped.append(ref)
            continue
        key = (lcsc, fp.GetFPID().GetLibItemName().wx_str())
        g = groups.setdefault(key, {"refs": [], "values": set(), "mpn": ""})
        g["refs"].append(ref)
        g["values"].add(fp.GetValue())
        if fp.HasField("MPN"):
            g["mpn"] = fp.GetFieldText("MPN")
        pos = fp.GetPosition()
        cpl.append([ref, "%.3fmm" % P.ToMM(pos.x - origin.x), "%.3fmm" % (-P.ToMM(pos.y - origin.y)),
                    "Top" if fp.GetLayer() == P.F_Cu else "Bottom", "%.1f" % fp.GetOrientationDegrees()])
    with open(os.path.join(out, "bom_jlcpcb.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
        for (lcsc, fpn), g in groups.items():
            comment = g["values"].pop() if len(g["values"]) == 1 else g["mpn"]
            w.writerow([comment, ",".join(g["refs"]), fpn, lcsc])
    with open(os.path.join(out, "cpl_jlcpcb.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        w.writerows(cpl)
    print("bom lines:", len(groups), "placed parts:", len(cpl), "skipped:", " ".join(skipped))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
