"""splib — project-local symbols and footprints for safety_power.

Everything KiCad's standard library does not provide is generated here, from
the datasheet pinouts, so the symbol in the schematic and the file in
kicad/lib are always the same object (no lib_symbol_mismatch).

    symbols   -> kicad/lib/sp.kicad_sym
    footprints-> kicad/lib/sp.pretty/*.kicad_mod

Pins of generated symbols are typed "passive" (or "no_connect"): ERC then
checks connectivity, not drive strength. Power nets are flagged explicitly.
"""

from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scripts"))

import kicadgen as K  # noqa: E402
from kicadgen import S, Q, dump, uid  # noqa: E402

FP_SRC = K.FP_DIR

# ---------------------------------------------------------------------------
#  Symbols: name -> (reference prefix, left pins, right pins, description)
#  A pin is (number, name) or (number, name, "nc").
# ---------------------------------------------------------------------------
SYMBOLS = {
    # TI SLUSEW1C, table 4-1. DGX package: 20 positions, pin 16 absent.
    "TPS48100-Q1": ("U", [("1", "EN/UVLO"), ("2", "INP2"), ("3", "INP1"), ("4", "NC", "nc"), ("5", "~{FLT}"),
                          ("6", "GND"), ("7", "CS_SEL"), ("8", "ISCP"), ("9", "TMR"), ("10", "SCP_TEST")],
                    [("20", "VS"), ("19", "NC", "nc"), ("18", "CS+"), ("17", "CS-"), ("15", "G1PU"), ("14", "G1PD"),
                     ("13", "SRC"), ("12", "BST"), ("11", "G2")],
                    "100 V back-to-back MOSFET smart high-side driver, two gate drives, INP1/INP2"),
    # Infineon IPB017N10N5(LF) D2PAK-7: 1 gate, 2/3/5/6/7 source, 4 = tab = drain.
    "NMOS_D2PAK7": ("Q", [("1", "G")], [("4", "D"), ("2", "S"), ("3", "S"), ("5", "S"), ("6", "S"), ("7", "S")],
                    "N-MOSFET, D2PAK-7 (TO-263-7), tab = drain"),
    # TI SLLSEV0 table 6-1, V suffix: pin 5 = VIO.
    "TCAN1042HV": ("U", [("1", "TXD"), ("4", "RXD"), ("8", "STB"), ("5", "VIO")],
                   [("3", "VCC"), ("7", "CANH"), ("6", "CANL"), ("2", "GND")], "CAN transceiver, +/-70 V bus fault, VIO"),
    # TI SBOS589D, DBV: 1 IN+, 2 V-, 3 IN-, 4 OUT (open collector), 5 V+.
    "TLV1701": ("U", [("1", "IN+"), ("3", "IN-")], [("5", "V+"), ("4", "OUT"), ("2", "V-")],
                "Comparator, 36 V, open-collector output"),
    # TI UCC27517 DBV: 1 VDD, 2 GND, 3 IN+, 4 IN-, 5 OUT.
    "UCC27517": ("U", [("3", "IN+"), ("4", "IN-")], [("1", "VDD"), ("5", "OUT"), ("2", "GND")],
                 "Low-side gate driver 4 A, inputs 20 V independent of VDD"),
    # TI TPS7A4001 DGN: 1 OUT, 2 FB, 3/6/7 NC, 4 GND, 5 EN, 8 IN, 9 pad.
    "TPS7A4001": ("U", [("8", "IN"), ("5", "EN"), ("3", "NC", "nc"), ("6", "NC", "nc"), ("7", "NC", "nc")],
                  [("1", "OUT"), ("2", "FB"), ("4", "GND"), ("9", "PAD")], "100 V LDO, 50 mA, adjustable"),
    # TI SLVSE57C: 1 dVdt, 2 EN, 3/4 IN, 5 OUT, 6 FLT, 7 ILM, 8 GND, 9 pad.
    "TPS2595x": ("U", [("3", "IN"), ("4", "IN"), ("2", "EN"), ("1", "dVdt")],
                 [("5", "OUT"), ("6", "~{FLT}"), ("7", "ILM"), ("8", "GND"), ("9", "PAD")], "eFuse 2.7-18 V, 4 A"),
    # Dual comparator, standard LM393 pinout, single unit.
    "LM2903": ("U", [("3", "+A"), ("2", "-A"), ("5", "+B"), ("6", "-B")], [("8", "VCC"), ("1", "OUTA"), ("7", "OUTB"), ("4", "GND")],
               "Dual comparator, open collector"),
    # TI SCES220, DCU: 1 CLK, 2 D, 3 ~Q, 4 GND, 5 Q, 6 ~CLR, 7 ~PRE, 8 VCC.
    "74LVC1G74": ("U", [("2", "D"), ("1", "CLK"), ("6", "~{CLR}"), ("7", "~{PRE}")],
                  [("8", "VCC"), ("5", "Q"), ("3", "~{Q}"), ("4", "GND")], "Single D flip-flop, set/reset"),
    # Espressif ESP32-DevKitC V4, 38 pins. 1-19 = J2 (3V3 ... 5V), 20-38 = J3 (GND ... CLK).
    "ESP32-DevKitC-V4": ("U", [("1", "3V3"), ("2", "EN"), ("3", "IO36"), ("4", "IO39"), ("5", "IO34"), ("6", "IO35"),
                               ("7", "IO32"), ("8", "IO33"), ("9", "IO25"), ("10", "IO26"), ("11", "IO27"), ("12", "IO14"),
                               ("13", "IO12"), ("14", "GND"), ("15", "IO13"), ("16", "SD2"), ("17", "SD3"), ("18", "CMD"),
                               ("19", "5V")],
                         [("20", "GND"), ("21", "IO23"), ("22", "IO22"), ("23", "TXD0"), ("24", "RXD0"), ("25", "IO21"),
                          ("26", "GND"), ("27", "IO19"), ("28", "IO18"), ("29", "IO5"), ("30", "IO17"), ("31", "IO16"),
                          ("32", "IO4"), ("33", "IO0"), ("34", "IO2"), ("35", "IO15"), ("36", "SD1"), ("37", "SD0"),
                          ("38", "CLK")],
                         "ESP32-DevKitC V4 on 2 x 19 sockets"),
    # Mornsun URB_YMD-30WR3: 1 Ctrl, 2 GND (input), 3 Vin, 4 +Vo, 5 Trim, 6 0V.
    "URB_YMD": ("PS", [("3", "Vin"), ("1", "Ctrl"), ("2", "GND")], [("4", "+Vo"), ("5", "Trim"), ("6", "0V")],
                "Isolated DC/DC 30 W, 18-75 V in"),
    # Mornsun B_S-1WR3: 1 GND (input), 2 Vin, 3 0V, 4 +Vo.
    "B0503S": ("PS", [("2", "Vin"), ("1", "GND")], [("4", "+Vo"), ("3", "0V")], "Isolated DC/DC 1 W, 5 V to 3.3 V"),
}


def _pin(num, name, x, y, ang, kind):
    return S("pin", kind, "line", S("at", x, y, ang), S("length", 2.54),
             S("name", Q(name), S("effects", S("font", S("size", 1.016, 1.016)))),
             S("number", Q(num), S("effects", S("font", S("size", 1.016, 1.016)))))


def _prop(k, v, x, y, hide=False):
    p = S("property", Q(k), Q(v), S("at", x, y, 0))
    eff = S("effects", S("font", S("size", 1.27, 1.27)))
    if hide:
        eff.append(S("hide", "yes"))
    p.append(eff)
    return p


def symbol(name, spec):
    ref, left, right, descr = spec
    n = max(len(left), len(right))
    h = (n + 1) * 2.54
    w = 15.24 if name != "ESP32-DevKitC-V4" else 20.32
    top = h / 2
    sym = S("symbol", Q(name), S("exclude_from_sim", "no"), S("in_bom", "yes"), S("on_board", "yes"),
            _prop("Reference", ref, -w / 2, top + 1.27), _prop("Value", name, -w / 2, -top - 1.27),
            _prop("Footprint", "", 0, 0, True), _prop("Datasheet", "", 0, 0, True),
            _prop("Description", descr, 0, 0, True))
    body = S("symbol", Q(name + "_0_1"),
             S("rectangle", S("start", -w / 2, top), S("end", w / 2, -top),
               S("stroke", S("width", 0.254), S("type", "default")), S("fill", S("type", "background"))))
    pins = S("symbol", Q(name + "_1_1"))
    for side, lst in ((-1, left), (1, right)):
        for i, p in enumerate(lst):
            num, pname = p[0], p[1]
            kind = "no_connect" if len(p) > 2 else "passive"
            y = round(top - 2.54 * (i + 1), 2)
            x = side * (w / 2 + 2.54)
            pins.append(_pin(num, pname, x, y, 0 if side < 0 else 180, kind))
    sym.append(body)
    sym.append(pins)
    sym.append(S("embedded_fonts", "no"))
    return sym


def write_symbols(path):
    lib = S("kicad_symbol_lib", S("version", 20251024), S("generator", Q("splib")), S("generator_version", Q("10.0")))
    for name, spec in SYMBOLS.items():
        lib.append(symbol(name, spec))
    with open(path, "w", encoding="utf-8") as f:
        f.write(dump(lib) + "\n")


# ---------------------------------------------------------------------------
#  Footprints
# ---------------------------------------------------------------------------

def _fp_head(name, descr, attr="smd"):
    return S("footprint", Q(name), S("version", 20260206), S("generator", Q("pcbnew")),
             S("generator_version", Q("10.0")), S("layer", Q("F.Cu")), S("descr", Q(descr)),
             S("property", Q("Reference"), Q("REF**"), S("at", 0, 0, 0), S("layer", Q("F.SilkS")),
               S("uuid", Q(uid("fpref:" + name))), S("effects", S("font", S("size", 1, 1), S("thickness", 0.15)))),
             S("property", Q("Value"), Q(name), S("at", 0, 0, 0), S("layer", Q("F.Fab")), S("hide", "yes"),
               S("uuid", Q(uid("fpval:" + name))), S("effects", S("font", S("size", 1, 1), S("thickness", 0.15)))),
             S("attr", attr))


def _rect(x0, y0, x1, y1, layer, width=0.05, seed=""):
    return S("fp_rect", S("start", x0, y0), S("end", x1, y1), S("stroke", S("width", width), S("type", "solid")),
             S("fill", "no"), S("layer", Q(layer)), S("uuid", Q(uid("r:%s:%s:%s:%s:%s" % (seed, x0, y0, layer, x1)))))


def _circle(cx, cy, r, layer, width=0.05, seed=""):
    return S("fp_circle", S("center", cx, cy), S("end", cx + r, cy), S("stroke", S("width", width), S("type", "solid")),
             S("fill", "no"), S("layer", Q(layer)), S("uuid", Q(uid("c:%s:%s:%s:%s" % (seed, cx, cy, layer)))))


def _smd(num, x, y, w, h, seed, shape="roundrect", paste=True):
    layers = ["F.Cu", "F.Mask"] + (["F.Paste"] if paste else [])
    p = S("pad", Q(num), "smd", shape, S("at", x, y), S("size", w, h), S("layers", *[Q(l) for l in layers]))
    if shape == "roundrect":
        p.append(S("roundrect_rratio", 0.15))
    p.append(S("uuid", Q(uid("p:%s:%s:%s:%s" % (seed, num, x, y)))))
    return p


def _tht(num, x, y, size, drill, seed, shape="circle"):
    return S("pad", Q(num), "thru_hole", shape, S("at", x, y), S("size", size, size), S("drill", drill),
             S("layers", Q("*.Cu"), Q("*.Mask")), S("remove_unused_layers", "no"),
             S("uuid", Q(uid("p:%s:%s:%s:%s" % (seed, num, x, y)))))


def fp_dgx(name="TI_DGX0019A_VSSOP-19"):
    """TI DGX0019A land pattern (SLUSEW1C p. 'example board layout'): 20 x 0.3 x 1.45 mm,
    pitch 0.5, row centres 4.4 mm apart. Position 16 is depopulated."""
    fp = _fp_head(name, "TI DGX0019A VSSOP-19 (20 positions, pin 16 removed), 0.5 mm pitch")
    for i in range(10):
        y = -2.25 + 0.5 * i
        fp.append(_smd(str(i + 1), -2.2, y, 1.45, 0.3, name))
        num = 20 - i
        if num != 16:
            fp.append(_smd(str(num), 2.2, y, 1.45, 0.3, name))
    fp.append(_rect(-1.5, -2.55, 1.5, 2.55, "F.Fab", 0.1, name))
    fp.append(_rect(-3.2, -2.8, 3.2, 2.8, "F.CrtYd", 0.05, name))
    fp.append(_circle(-1.05, -2.0, 0.2, "F.Fab", 0.1, name))
    fp.append(S("embedded_fonts", "no"))
    return fp


def fp_lug(name, pitch, hole, pad, n_stitch=8):
    """Ring-lug terminal pair: two plated holes for an M4/M5 bolt or press-in stud,
    with a ring of plated stitching holes so current reaches every copper layer."""
    import math
    fp = _fp_head(name, "Ring-lug terminal pair, %.1f mm holes, pitch %.1f mm" % (hole, pitch), "through_hole")
    for k, x in ((1, 0.0), (2, pitch)):
        fp.append(_tht(str(k), x, 0, pad, hole, name))
        r = pad / 2 - 0.9
        for i in range(n_stitch):
            a = 2 * math.pi * i / n_stitch
            fp.append(_tht(str(k), round(x + r * math.cos(a), 3), round(r * math.sin(a), 3), 1.0, 0.5, name + "s"))
        fp.append(_circle(x, 0, pad / 2 + 0.6, "F.CrtYd", 0.05, name + str(k)))
        fp.append(_circle(x, 0, pad / 2 + 0.3, "F.SilkS", 0.15, name + str(k)))
    fp.append(S("embedded_fonts", "no"))
    return fp


def fp_star(name="NetTie_GND_STAR_4mm"):
    """Single GND_LOGIC-BUS_N bond (decision D4): 4 mm wide copper bridge."""
    fp = _fp_head(name, "Net tie, star ground point, 4 mm copper")
    fp.append(S("net_tie_pad_groups", Q("1, 2")))
    fp[fp.index(S("attr", "smd"))] = S("attr", "smd", "exclude_from_pos_files", "exclude_from_bom", "allow_missing_courtyard")
    fp.append(S("fp_poly", S("pts", S("xy", -2.5, -2), S("xy", 2.5, -2), S("xy", 2.5, 2), S("xy", -2.5, 2)),
                S("stroke", S("width", 0), S("type", "solid")), S("fill", "yes"), S("layer", Q("F.Cu")),
                S("uuid", Q(uid("star-poly")))))
    fp.append(_smd("1", -2.5, 0, 3, 4, name, "rect", paste=False))
    fp.append(_smd("2", 2.5, 0, 3, 4, name, "rect", paste=False))
    fp.append(S("embedded_fonts", "no"))
    return fp


def fp_devkitc(name="ESP32-DevKitC-V4_Sockets"):
    """Two 1x19 sockets, 2.54 mm pitch, rows 25.40 mm apart (to confirm by P1).
    Origin = J2 pin 1 (3V3). J3 pin 1 (GND) is pad 20 at x = +25.40."""
    fp = _fp_head(name, "ESP32-DevKitC V4 on two 1x19 2.54 mm sockets (Mill-Max 310), row spacing 25.40 mm", "through_hole")
    for i in range(19):
        fp.append(_tht(str(i + 1), 0, 2.54 * i, 1.7, 1.0, name, "rect" if i == 0 else "circle"))
        fp.append(_tht(str(20 + i), 25.4, 2.54 * i, 1.7, 1.0, name))
    # module outline 27.9 x 54.4 mm (antenna end at -y)
    fp.append(_rect(-1.25, -6.0, 26.65, 48.4, "F.Fab", 0.1, name))
    fp.append(_rect(-1.5, -6.3, 26.9, 48.7, "F.CrtYd", 0.05, name))
    fp.append(_rect(-1.3, -1.3, 1.3, 47.0, "F.SilkS", 0.15, name))
    fp.append(_rect(24.1, -1.3, 26.7, 47.0, "F.SilkS", 0.15, name + "b"))
    fp.append(S("embedded_fonts", "no"))
    return fp


def fp_urb(name="Mornsun_URB_YMD-30WR3_1x1in"):
    """Mornsun URB_YMD-30WR3, 25.4 x 25.4 mm, recommended layout (top view):
    pins 1-3 left column (1 top), 6-4 right column (6 top); pin 1 at origin."""
    fp = _fp_head(name, "Mornsun URB_YMD-30WR3 1x1 inch DC/DC, pin dia 1.0 mm", "through_hole")
    pins = {"1": (0, 0), "2": (0, 7.62), "3": (0, 12.7), "6": (20.32, 0), "5": (20.32, 10.16), "4": (20.32, 20.32)}
    for n, (x, y) in pins.items():
        fp.append(_tht(n, x, y, 2.4, 1.4, name, "rect" if n == "1" else "circle"))
    fp.append(_rect(-2.54, -2.54, 22.86, 22.86, "F.Fab", 0.1, name))
    fp.append(_rect(-2.64, -2.64, 22.96, 22.96, "F.SilkS", 0.15, name))
    fp.append(_rect(-2.9, -2.9, 23.2, 23.2, "F.CrtYd", 0.05, name))
    fp.append(S("embedded_fonts", "no"))
    return fp


def fp_to263_nopin4(name="TO-263-7_TabPin4_NoPin4"):
    """KiCad TO-263-7_TabPin4 with the short centre leg removed: on the D2PAK-7 that
    leg is cut, and its pad sat 0.47 mm from two source pads at drain potential."""
    with open(os.path.join(FP_SRC, "Package_TO_SOT_SMD.pretty", "TO-263-7_TabPin4.kicad_mod")) as f:
        node = K.parse(f.read())
    node[1] = Q(name)
    out = []
    for c in node:
        if isinstance(c, list) and c and c[0] == "pad" and c[1] == "4":
            at = K.find(c, "at")
            if float(at[1]) < 0:  # the leg, not the tab
                continue
        out.append(c)
    return out


def write_footprints(d):
    os.makedirs(d, exist_ok=True)
    fps = [fp_dgx(), fp_lug("RingLug_M5_2P_P26", 26.0, 5.3, 10.0), fp_lug("RingLug_M4_2P_P13", 13.0, 4.3, 8.0),
           fp_star(), fp_devkitc(), fp_urb(), fp_to263_nopin4()]
    for fp in fps:
        with open(os.path.join(d, str(fp[1]) + ".kicad_mod"), "w", encoding="utf-8") as f:
            f.write(dump(fp) + "\n")


def write_all(lib_dir):
    os.makedirs(lib_dir, exist_ok=True)
    write_symbols(os.path.join(lib_dir, "sp.kicad_sym"))
    write_footprints(os.path.join(lib_dir, "sp.pretty"))


if __name__ == "__main__":
    write_all(os.path.join(HERE, "..", "kicad", "lib"))
    print("ok")
