"""fab_pcbway — PCBWay BOM and centroid files from a KiCad board.

Run with KiCad's bundled Python:
    <KiCad python> fab_pcbway.py board.kicad_pcb out_dir

Writes:
    bom_pcbway.csv       Item, Designator, Quantity, Manufacturer, MPN, Description, Package, Type,
                         Placed by, LCSC (reference only)
    centroid_pcbway.csv  Designator, Mid X, Mid Y, Layer, Rotation   (SMD parts only, mm)

Type comes from the footprint attribute: SMD footprints are placed by PCBWay;
through-hole footprints (connectors, sockets, modules, fuse holders, big
capacitors, terminals) are soldered by hand and listed as "Placed by: hand".
Footprints marked DNP are listed once with "DNP" and left out of the centroid
file. Board-only footprints and those excluded from the BOM (test pads, mounting
holes) are left out of both.

With --fine-only, PCBWay places only the parts that cannot reasonably be
soldered with an iron (FINE_PACKAGES below: 0603 and smaller, SOT-23-5/6,
0.65 mm pitch and finer, packages with a thermal pad underneath, JST GH).
Every other SMD part (0805 and up, SOT-23, SOIC, SOD-123, SMA/SMC, DPAK,
power inductors, shunts) moves to "hand (William)". Files get a "_fine" suffix.

Leaves the JLCPCB helper (fab.py) untouched.
"""

import csv
import os
import re
import sys
from collections import OrderedDict

import pcbnew as P


FINE_PACKAGES = re.compile(
    r"_0603_|_0402_|_0201_|SOD-523|SOD-323|SOT-23-5|SOT-23-6|SOT-363|SOT-563|SSOP|TSSOP|VSSOP|MSOP"
    r"|PowerPAD|-1EP|QFN|DFN|SON-|JST_GH")


def field(fp, name):
    return fp.GetFieldText(name) if fp.HasField(name) else ""


def main(pcb_path: str, out: str, fine_only: bool = False):
    b = P.LoadBoard(pcb_path)
    os.makedirs(out, exist_ok=True)
    origin = b.GetDesignSettings().GetAuxOrigin()
    groups = OrderedDict()
    cpl = []
    for fp in sorted(b.GetFootprints(), key=lambda f: (f.GetReference()[0], len(f.GetReference()), f.GetReference())):
        ref = fp.GetReference()
        if fp.IsBoardOnly() or fp.IsExcludedFromBOM():
            continue
        attr = fp.GetAttributes()
        kind = "SMD" if attr & P.FP_SMD else ("THT" if attr & P.FP_THROUGH_HOLE else "OTHER")
        dnp = fp.IsDNP()
        mpn = field(fp, "MPN")
        pkg = fp.GetFPID().GetLibItemName().wx_str()
        machine = kind == "SMD" and (not fine_only or bool(FINE_PACKAGES.search(pkg)))
        key = (fp.GetValue(), mpn, pkg, dnp)
        g = groups.setdefault(key, {"refs": [], "kind": kind, "mfr": field(fp, "Manufacturer"),
                                    "lcsc": field(fp, "LCSC"), "dnp": dnp, "machine": machine})
        g["refs"].append(ref)
        if machine and not dnp:
            pos = fp.GetPosition()
            cpl.append([ref, "%.3f" % P.ToMM(pos.x - origin.x), "%.3f" % (-P.ToMM(pos.y - origin.y)),
                        "Top" if fp.GetLayer() == P.F_Cu else "Bottom", "%.1f" % fp.GetOrientationDegrees()])
    n_smd = n_tht = 0
    sfx = "_fine" if fine_only else ""
    with open(os.path.join(out, "bom_pcbway%s.csv" % sfx), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Item", "Designator", "Quantity", "Manufacturer", "MPN", "Description", "Package", "Type",
                    "Placed by", "LCSC (reference)"])
        for i, ((value, mpn, pkg, dnp), g) in enumerate(groups.items(), 1):
            placed = "DNP (do not place)" if dnp else ("PCBWay" if g["machine"] else "hand (William)")
            w.writerow([i, ",".join(g["refs"]), len(g["refs"]), g["mfr"], mpn, value, pkg, g["kind"], placed,
                        g["lcsc"]])
            if not dnp:
                if g["machine"]:
                    n_smd += len(g["refs"])
                else:
                    n_tht += len(g["refs"])
    with open(os.path.join(out, "centroid_pcbway%s.csv" % sfx), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Mid X(mm)", "Mid Y(mm)", "Layer", "Rotation"])
        w.writerows(cpl)
    print("bom lines:", len(groups), "placed by PCBWay:", n_smd, "by hand:", n_tht,
          "centroid rows:", len(cpl))


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--fine-only"]
    main(args[0], args[1], fine_only="--fine-only" in sys.argv)
