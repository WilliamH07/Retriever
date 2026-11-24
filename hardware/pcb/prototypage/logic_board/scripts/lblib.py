"""lblib — project-local symbols and footprints for the logic_board (copy of mainboard/scripts/mblib.py).

Reuses the generators of safety_power/scripts/splib.py (imported, not modified),
and writes its own library so that this board never depends on the files of
another board:

    symbols    -> kicad/lib/lb.kicad_sym
    footprints -> kicad/lib/lb.pretty/*.kicad_mod

Only one footprint is new: the DevKitC socket pair with a courtyard limited to
the two socket rows. The module stands 8.5 mm above the board on its sockets,
so low SMD parts (< 3 mm) may sit between the rows, under the module.
"""

from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PCB_DIR = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(PCB_DIR, "scripts"))
sys.path.insert(0, os.path.join(PCB_DIR, "safety_power", "scripts"))

import kicadgen as K  # noqa: E402
from kicadgen import S, Q, dump  # noqa: E402
import splib  # noqa: E402  (safety_power generators, read only)

LIB = "lb"

# Symbols taken as-is from splib (datasheet pinouts already checked there).
SYMBOLS = {k: splib.SYMBOLS[k] for k in ("TCAN1042HV", "TLV1701", "UCC27517", "TPS7A4001", "74LVC1G74",
                                          "ESP32-DevKitC-V4")}


def write_symbols(path):
    lib = S("kicad_symbol_lib", S("version", 20251024), S("generator", Q("lblib")), S("generator_version", Q("10.0")))
    for name, spec in SYMBOLS.items():
        lib.append(splib.symbol(name, spec))
    with open(path, "w", encoding="utf-8") as f:
        f.write(dump(lib) + "\n")


def fp_devkitc_mb(name="ESP32-DevKitC-V4_Sockets_OpenCenter"):
    """Two 1x19 sockets, 2.54 mm pitch, rows 25.40 mm apart (P1 to confirm).
    Origin = J2 pin 1 (3V3); J3 pin 1 (GND) is pad 20 at x = +25.40; antenna end at -y.
    Courtyard: the two socket strips only (the module is 8.5 mm above the board)."""
    fp = splib._fp_head(name, "ESP32-DevKitC V4 on two 1x19 2.54 mm sockets, rows 25.40 mm apart; "
                              "courtyard on the socket rows only (low SMD parts allowed under the module)",
                        "through_hole")
    for i in range(19):
        fp.append(splib._tht(str(i + 1), 0, 2.54 * i, 1.7, 1.0, name, "rect" if i == 0 else "circle"))
        fp.append(splib._tht(str(20 + i), 25.4, 2.54 * i, 1.7, 1.0, name))
    # module outline 27.9 x 54.4 mm on the fabrication layer (antenna end at -y)
    fp.append(splib._rect(-1.25, -6.0, 26.65, 48.4, "F.Fab", 0.1, name))
    fp.append(splib._rect(-1.3, -1.3, 1.3, 47.0, "F.SilkS", 0.15, name))
    fp.append(splib._rect(24.1, -1.3, 26.7, 47.0, "F.SilkS", 0.15, name + "b"))
    fp.append(splib._rect(-1.5, -1.5, 1.5, 47.2, "F.CrtYd", 0.05, name))
    fp.append(splib._rect(23.9, -1.5, 26.9, 47.2, "F.CrtYd", 0.05, name + "b"))
    fp.append(S("embedded_fonts", "no"))
    return fp


def fp_hvssop_narrow(name="HVSSOP-8-1EP_3x3mm_P0.65mm_EP1.57x1.89mm_Pad0.42"):
    """KiCad HVSSOP-8 (TI DGN) with 0.42 mm wide leads pads instead of 0.5 mm: 0.23 mm between pads,
    above the 0.2 mm net-class clearances (TI DGN land pattern: 0.45 mm max lead width)."""
    with open(os.path.join(K.FP_DIR, "Package_SO.pretty", "HVSSOP-8-1EP_3x3mm_P0.65mm_EP1.57x1.89mm.kicad_mod")) as f:
        node = K.parse(f.read())
    node[1] = Q(name)
    for c in node:
        if isinstance(c, list) and c and c[0] == "pad" and c[1] in [str(i) for i in range(1, 9)]:
            sz = K.find(c, "size")
            if sz and abs(float(sz[2]) - 0.5) < 1e-6:
                sz[2] = 0.42
    return node


def write_footprints(d):
    os.makedirs(d, exist_ok=True)
    # No lugs and no URB module here: the 30 A path and the 12 V PC converter are off board.
    fps = [fp_devkitc_mb(), fp_hvssop_narrow()]
    for fp in fps:
        with open(os.path.join(d, str(fp[1]) + ".kicad_mod"), "w", encoding="utf-8") as f:
            f.write(dump(fp) + "\n")


def write_all(lib_dir):
    os.makedirs(lib_dir, exist_ok=True)
    write_symbols(os.path.join(lib_dir, LIB + ".kicad_sym"))
    write_footprints(os.path.join(lib_dir, LIB + ".pretty"))


if __name__ == "__main__":
    write_all(os.path.join(HERE, "..", "kicad", "lib"))
    print("ok")
