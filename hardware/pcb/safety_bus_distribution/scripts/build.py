#!/usr/bin/env python3
"""safety_bus_distribution v2 — the whole board, schematic and layout, in one file.

    python3 build.py sch            # schematic + project (any Python 3)
    <KiCad python> build.py pcb     # board: placement, zones, autoroute, fill

The circuit is described once, in `circuit()`. `sch` and `pcb` both read it,
so the board can only contain what the schematic contains.

Design decisions are recorded in ../decisions.md. Values below cite the
datasheet line they come from.
"""

from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD_DIR = os.path.dirname(HERE)
KICAD_DIR = os.path.join(BOARD_DIR, "kicad")
LIB_DIR = os.path.join(KICAD_DIR, "lib")
sys.path.insert(0, os.path.join(BOARD_DIR, "..", "scripts"))

import kicadgen as K  # noqa: E402

PROJECT = "safety_bus_distribution"
REV = "2.0"
DATE = "2026-11-11"

N_BRANCH = 8
BRANCH_NAMES = ["SAFETY", "MOTION AV", "MOTION AR", "X1 USB-CAN", "LIBRE 5", "LIBRE 6", "LIBRE 7", "BANC"]

# ---------------------------------------------------------------------------
#  Parts: (lib_id, footprint, value, LCSC, MPN)
# ---------------------------------------------------------------------------
P_CONN = ("Connector_Generic:Conn_01x06", "Connector_Molex:Molex_Micro-Fit_3.0_43650-0615_1x06_P3.00mm_Vertical",
          "Micro-Fit 6p", "C505231", "Molex 43650-0615")
P_EFUSE = ("lcsc:TPS259531DSGR", "Package_SON:Texas_DSG0008A_WSON-8-1EP_2x2mm_P0.5mm_EP0.9x1.6mm",
           "TPS259531", "C2155674", "TI TPS259531DSGR")
P_CMC = ("Filter:Choke_CommonMode_FerriteCore_1423", "lcsc:IND-SMD_4P-L4.5-W3.2-TL",
         "ACT45B-510", "C76584", "TDK ACT45B-510-2P-TL003")
P_PPTC = ("Device:Polyfuse", "lcsc:F1812", "1.1A/48V", "C19723490", "LUTE 1812L110/48QR")
P_CANESD = ("Power_Protection:NUP2105L", "Package_TO_SOT_SMD:SOT-23", "NUP2105L", "C14486", "onsemi NUP2105LT1G")
P_SAFEESD = ("Diode:ESD5Zxx", "Diode_SMD:D_SOD-523", "ESD5Z3.3", "C5252448", "ESD5Z3.3T1G")
P_PFET = ("Transistor_FET:AO3401A", "Package_TO_SOT_SMD:SOT-23", "AO3401A", "C15127", "AOS AO3401A")
P_TVS = ("Device:D_Zener", "Diode_SMD:D_SMA", "SMAJ6.0A", "C223993", "Littelfuse SMAJ6.0A")
P_LED_G = ("Device:LED", "LED_SMD:LED_0603_1608Metric", "green", "C72043", "Everlight 19-217/GHC")
P_JUMP = ("Connector_Generic:Conn_01x02", "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
          "TERM", "C492401", "2.54 mm 1x2 header")
P_TP = ("Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", "TP", "", "")

R0603 = "Resistor_SMD:R_0603_1608Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
C0805 = "Capacitor_SMD:C_0805_2012Metric"
RES = {  # value -> (LCSC, MPN)
    "1k": ("C21190", "0603WAF1001T5E"),
    "2.2k": ("C4190", "0603WAF2201T5E"),
    "10k": ("C25804", "0603WAF1002T5E"),
    "47k": ("C25819", "0603WAF4702T5E"),
    "100k": ("C25803", "0603WAF1003T5E"),
    "1M": ("C22935", "0603WAF1004T5E"),
    "60.4": ("C4099359", "RM06F60R4CT"),
    "0R": ("C21189", "0603WAF0000T5E"),
    "1.8k": ("C4177", "0603WAF1801T5E"),
}
CAP = {  # value -> (footprint, LCSC, MPN)
    "100n": (C0603, "C14663", "CC0603KRX7R9BB104"),
    "1u": (C0603, "C15849", "CL10A105KB8NNNC"),
    "1n": (C0603, "C1588", "0603B102K500NT"),
    "4.7n C0G": (C0603, "C85980", "GRM1885C1H472JA01D"),
    "10u": (C0805, "C15850", "CL21A106KAYNNNE"),
}


class Circuit:
    """Collects parts with both schematic and board placement."""

    def __init__(self):
        self.parts = []  # dicts

    def add(self, ref, part, nets, sch, pcb, rot=0, sch_rot=0, dnp=False, value=None, back=False, in_bom=True):
        lib_id, fp, val, lcsc, mpn = part
        self.parts.append(dict(ref=ref, lib_id=lib_id, footprint=fp, value=value or val,
                               lcsc=lcsc, mpn=mpn, nets=nets, sch=sch, sch_rot=sch_rot,
                               pcb=pcb, rot=rot, dnp=dnp, back=back, in_bom=in_bom))

    def R(self, ref, value, a, b, sch, pcb, rot=0, dnp=False, sch_rot=90):
        lcsc, mpn = RES[value]
        self.add(ref, ("Device:R", R0603, value + ("Ω" if value[-1].isdigit() else ""), lcsc, mpn),
                 {"1": a, "2": b}, sch, pcb, rot, sch_rot, dnp)

    def C(self, ref, value, a, b, sch, pcb, rot=0, dnp=False, sch_rot=90):
        fp, lcsc, mpn = CAP[value]
        self.add(ref, ("Device:C", fp, value.split()[0] + "F" + (" C0G" if "C0G" in value else ""), lcsc, mpn),
                 {"1": a, "2": b}, sch, pcb, rot, sch_rot, dnp)


# ---------------------------------------------------------------------------
#  Board geometry (mm). Origin top-left, y down.
# ---------------------------------------------------------------------------
W, H = 110.0, 72.0
PITCH = 23.5
X0 = 13.0          # pin 1 of the first top connector
Y_TOP = 5.0        # top connector pin row
Y_BOT = H - 5.0    # bottom connector pin row


def branch_frame(k):
    """Return (cx, flip) for branch k: cx = x of pin 1 for top, mirrored for bottom."""
    col = k % 4
    top = k < 4
    return X0 + col * PITCH, top


def circuit() -> Circuit:
    c = Circuit()

    # ---------------- trunk input -----------------------------------------
    # J1 on the left edge, rotated so its pins run vertically.
    c.add("J1", P_CONN, {"1": "+5V_IN", "2": "CANH", "3": "CANL", "4": "SAFE_N", "5": "GND", "6": "SHIELD"},
          sch=(40, 60), pcb=(5.0, 43.5), rot=90)
    # Reverse polarity: P-MOSFET, drain on the input, source on the protected rail.
    c.add("Q1", P_PFET, {"1": "PFET_G", "2": "+5V", "3": "+5V_IN"}, sch=(80, 55), pcb=(6.8, 10.5), rot=0)
    c.R("R1", "10k", "PFET_G", "GND", sch=(80, 75), pcb=(6.8, 13.6), rot=0)
    # Transients and ESD on the protected rail (after the MOSFET, so reverse polarity
    # does not forward-bias the TVS).
    c.add("D1", P_TVS, {"1": "+5V", "2": "GND"}, sch=(100, 65), pcb=(2.6, 19.0), rot=90, sch_rot=90)
    c.C("C1", "10u", "+5V", "GND", sch=(115, 65), pcb=(6.8, 16.2), rot=0)
    c.C("C2", "10u", "+5V", "GND", sch=(125, 65), pcb=(6.8, 18.8), rot=0)
    c.C("C3", "100n", "+5V", "GND", sch=(135, 65), pcb=(6.8, 21.3), rot=0)
    c.R("R2", "1k", "+5V", "LED_PWR", sch=(150, 55), pcb=(2.4, 9.6), rot=90)
    c.add("D2", P_LED_G, {"1": "GND", "2": "LED_PWR"}, sch=(150, 75), pcb=(2.4, 12.8), rot=270, sch_rot=90,
          value="PWR")

    # ---------------- bus services ---------------------------------------
    # Split termination A and B: 2 x 60.4 Ω, centre tap to GND through 4.7 nF C0G.
    for i, (jp, ra, rb, cs, x) in enumerate((("JP1", "R3", "R4", "C4", 26.0), ("JP2", "R5", "R6", "C5", 36.0))):
        tag = "AB"[i]
        sx = 40 + i * 70
        c.add(jp, P_JUMP, {"1": "CANH", "2": "TERM%s_H" % tag}, sch=(sx, 130), pcb=(x, 33.0), rot=90)
        c.R(ra, "60.4", "TERM%s_H" % tag, "TERM%s_M" % tag, sch=(sx + 15, 125), pcb=(x + 1.0, 38.5), rot=0)
        c.R(rb, "60.4", "TERM%s_M" % tag, "CANL", sch=(sx + 15, 145), pcb=(x + 4.5, 38.5), rot=0)
        c.C(cs, "4.7n C0G", "TERM%s_M" % tag, "GND", sch=(sx + 30, 135), pcb=(x + 2.75, 41.0), rot=0)
    # /SAFE: one ESD diode on the common net.
    c.add("D3", P_SAFEESD, {"1": "SAFE_N", "2": "GND"}, sch=(190, 130), pcb=(50.0, 36.0), rot=0, sch_rot=90)
    # Shield bonding option (not fitted: the shield is bonded at one end, X1 side).
    c.R("R7", "0R", "SHIELD", "GND", sch=(210, 125), pcb=(60.0, 34.0), rot=0, dnp=True)
    c.C("C6", "4.7n C0G", "SHIELD", "GND", sch=(210, 145), pcb=(60.0, 38.0), rot=0, dnp=True)
    # Bench-only /SAFE pull-up from 5 V, divided to 3.2 V (not fitted on the robot).
    c.R("R8", "1k", "+5V", "SAFE_N", sch=(230, 125), pcb=(70.0, 34.0), rot=0, dnp=True)
    c.R("R9", "1.8k", "SAFE_N", "GND", sch=(230, 145), pcb=(70.0, 38.0), rot=0, dnp=True)
    # Test points.
    for i, (ref, net) in enumerate((("TP1", "+5V"), ("TP2", "CANH"), ("TP3", "CANL"),
                                    ("TP4", "SAFE_N"), ("TP5", "GND"), ("TP6", "GND"))):
        c.add(ref, P_TP, {"1": net}, sch=(260 + i * 10, 130), pcb=(80.0 + i * 3.5, 36.0), value=net, in_bom=False)

    # ---------------- branches ---------------------------------------------
    for k in range(N_BRANCH):
        n = k + 1
        cx, top = branch_frame(k)
        s = "_N%d" % n
        # schematic block origin
        bx = 40 + (k % 4) * 135
        by = 200 + (k // 4) * 100

        def P(dx, dy):
            """Board point relative to the branch: dx along the connector, dy into the board."""
            if top:
                return (cx + dx, Y_TOP + dy)
            return (cx + 15.0 - dx, Y_BOT - dy)

        r0 = 0 if top else 180
        jref = "J%d" % (n + 1)
        c.add(jref, P_CONN, {"1": "+5V" + s, "2": "CANH" + s, "3": "CANL" + s, "4": "SAFE_N",
                             "5": "GND" + s, "6": "SHIELD"},
              sch=(bx, by), pcb=P(0, 0), rot=r0)

        # eFuse TPS259531: ILIM ≈ 0.95 A with R_ILM = 2.2 kΩ (datasheet table:
        # 1780 Ω -> 1.17 A, 4420 Ω -> 0.49 A). UVLO = 1.2 V x (100k+47k)/47k = 3.75 V.
        # dVdt 1 nF: soft start into the node's bulk capacitance. FLT unused.
        u = "U%d" % n
        c.add(u, P_EFUSE, {"1": "DVDT" + s, "2": "EN" + s, "3": "+5V", "4": "+5V", "5": "+5V" + s,
                           "6": None, "7": "ILM" + s, "8": "GND", "9": "GND"},
              sch=(bx + 40, by), pcb=P(2.0, 9.6), rot=r0 + 90)
        c.R("R%d" % (10 + n * 10), "100k", "+5V", "EN" + s, sch=(bx + 20, by + 25), pcb=P(-1.8, 6.5), rot=r0)
        c.R("R%d" % (11 + n * 10), "47k", "EN" + s, "GND", sch=(bx + 20, by + 45), pcb=P(-1.8, 8.2), rot=r0)
        c.R("R%d" % (12 + n * 10), "2.2k", "ILM" + s, "GND", sch=(bx + 60, by + 25), pcb=P(-1.8, 11.6), rot=r0)
        c.C("C%d" % (10 + n * 10), "1n", "DVDT" + s, "GND", sch=(bx + 60, by + 45), pcb=P(-1.8, 9.9), rot=r0)
        c.C("C%d" % (11 + n * 10), "100n", "+5V", "GND", sch=(bx + 30, by + 60), pcb=P(2.0, 6.5), rot=r0)
        c.C("C%d" % (12 + n * 10), "1u", "+5V" + s, "GND", sch=(bx + 50, by + 60), pcb=P(2.0, 12.6), rot=r0)
        # Branch presence LED, on the protected branch rail.
        c.R("R%d" % (13 + n * 10), "1k", "+5V" + s, "LED" + s, sch=(bx + 80, by + 25), pcb=P(-1.8, 13.3), rot=r0)
        c.add("D%d" % (10 + n), P_LED_G, {"1": "GND", "2": "LED" + s},
              sch=(bx + 80, by + 45), pcb=P(2.0, 14.6), rot=r0, sch_rot=90, value="N%d" % n)
        # CAN: common-mode choke, bus side 1/2, branch side 4/3 (TDK: windings 1-4, 2-3).
        c.add("L%d" % n, P_CMC, {"1": "CANH", "2": "CANL", "4": "CANH" + s, "3": "CANL" + s},
              sch=(bx + 100, by), pcb=P(6.5, 14.0), rot=r0 + 90)
        c.add("D%d" % (20 + n), P_CANESD, {"1": "CANH" + s, "2": "CANL" + s, "3": "GND"},
              sch=(bx + 100, by + 35), pcb=P(6.5, 7.5), rot=r0 + 90)
        # Ground return fuse: hold 1.1 A > eFuse limit, rated 48 V for a 42 V fault.
        c.add("F%d" % n, P_PPTC, {"1": "GND", "2": "GND" + s},
              sch=(bx + 115, by + 35), pcb=P(12.0, 9.5), rot=r0 + 90, sch_rot=0)
    return c


# ---------------------------------------------------------------------------
#  Schematic
# ---------------------------------------------------------------------------

def build_sch(c: Circuit):
    s = K.Schematic(PROJECT, "Retriever — safety_bus_distribution", paper="A2", rev=REV, date=DATE,
                    company="Retriever, open hardware (CERN-OHL-S-2.0)",
                    comments=("Carte passive : CAN + /SAFE + 5 V protégé vers 8 nœuds",
                              "Généré par scripts/build.py — ne pas éditer à la main",
                              "Décisions : hardware/pcb/safety_bus_distribution/decisions.md"),
                    extra_lib_dirs=(LIB_DIR,))
    for p in c.parts:
        fields = {"LCSC": p["lcsc"], "MPN": p["mpn"]} if p["lcsc"] else {}
        s.add(p["ref"], p["lib_id"], p["value"], p["footprint"], p["sch"], rot=p["sch_rot"],
              nets=p["nets"], fields=fields, dnp=p["dnp"], in_bom=p["in_bom"])
    for i, net in enumerate(("+5V_IN", "GND", "+5V")):
        s.power_flag(net, (40 + i * 15, 95))

    s.text("ENTRÉE DORSALE — anti-inversion, TVS, réservoir", (30, 35), 2.5, True)
    s.text("SERVICES DU BUS — terminaisons fendues, ESD /SAFE, options blindage et banc, points de test", (30, 110), 2.5, True)
    s.text("JP1, JP2 : terminaisons 120 Ω. Hors tension, TP2–TP3 = 60 Ω avec les deux posées.", (30, 165), 1.8)
    s.text("R7, C6, R8, R9 : NON MONTÉS (DNP). R8/R9 = pull-up de banc seulement.", (30, 172), 1.8)
    for k in range(N_BRANCH):
        bx = 40 + (k % 4) * 135
        by = 200 + (k // 4) * 100
        s.text("BRANCHE N%d — %s" % (k + 1, BRANCH_NAMES[k]), (bx - 10, by - 15), 2.2, True)
    s.write(os.path.join(KICAD_DIR, PROJECT + ".kicad_sch"))

    # library tables local to the project, so it opens anywhere
    with open(os.path.join(KICAD_DIR, "sym-lib-table"), "w") as f:
        f.write('(sym_lib_table\n\t(version 7)\n\t(lib (name "lcsc") (type "KiCad") '
                '(uri "${KIPRJMOD}/lib/lcsc.kicad_sym") (options "") (descr "Pièces LCSC importées"))\n)\n')
    with open(os.path.join(KICAD_DIR, "fp-lib-table"), "w") as f:
        f.write('(fp_lib_table\n\t(version 7)\n\t(lib (name "lcsc") (type "KiCad") '
                '(uri "${KIPRJMOD}/lib/lcsc.pretty") (options "") (descr "Pièces LCSC importées"))\n)\n')
    return s


# ---------------------------------------------------------------------------
#  Board
# ---------------------------------------------------------------------------

NETCLASSES = [
    # 0.15 mm clearance everywhere: the TPS2595 WSON has 0.5 mm pitch and a 0.2 mm
    # gap between the exposed pad and its pins.
    {"name": "Default", "track": 0.25, "clearance": 0.15, "via": 0.7},
    # 0.4 mm on 1 oz copper carries ~1.2 A for a 10 °C rise (IPC-2152), above the
    # 0.95 A branch limit. The trunk 5 V also gets a B.Cu copper band (see zones).
    {"name": "Power", "track": 0.4, "clearance": 0.15, "via": 0.7, "drill": 0.3, "patterns": ["/+5V*", "/GND*"]},
    {"name": "CAN", "track": 0.25, "clearance": 0.15, "via": 0.7, "patterns": ["/CAN*", "/SAFE_N"]},
]


def build_pcb(c: Circuit, sch_uuids: dict, nc_pins: dict):
    import pcbnew as Pn
    import kicadpcb as KP

    b = KP.Board(os.path.join(KICAD_DIR, PROJECT + ".kicad_pcb"), copper_layers=2, extra_fp_dirs=(LIB_DIR,))
    # JLCPCB 2-layer capabilities, with margin: 0.127 mm track/space min, 0.3 mm drill.
    b.rules(track=0.15, clearance=0.15, via=0.6, drill=0.3, annular=0.13, edge_clearance=0.3)
    for nc in NETCLASSES:
        b.netclass(nc["name"], nc["track"], nc["clearance"], nc.get("via", 0.6), nc.get("drill", 0.3),
                   nc.get("patterns", []))

    for p in c.parts:
        info = {"footprint": p["footprint"], "value": p["value"], "uuid": sch_uuids[p["ref"]],
                "fields": {"LCSC": p["lcsc"], "MPN": p["mpn"]} if p["lcsc"] else {},
                "dnp": p["dnp"], "in_bom": p["in_bom"], "nets": p["nets"], "nc": nc_pins[p["ref"]]}
        b.place(p["ref"], info, p["pcb"][0], p["pcb"][1], p["rot"], back=p["back"])

    b.outline(0, 0, W, H, r=3.0)
    for i, (x, y) in enumerate(((3.5, 3.5), (W - 3.5, 3.5), (3.5, H - 3.5), (W - 3.5, H - 3.5))):
        b.hole("H%d" % (i + 1), x, y, name="MountingHole_3.2mm_M3", net=None)

    # silkscreen
    b.text("RETRIEVER", 88.75, 29.6, 1.6)
    b.text("safety_bus_distribution v%s" % REV, 88.75, 32.0, 1.0)
    b.text("STUB MAX 30 cm", 22.0, 45.2, 1.1, justify="left")
    b.text("CANH-CANL hors tension : 60R OK / 120R = 1 term. / 40R = 3 term.", 62.0, 44.6, 0.8)
    b.text("TERM A", 27.0, 30.6, 0.8)
    b.text("TERM B", 37.0, 30.6, 0.8)
    b.text("BLINDAGE", 60.0, 31.9, 0.8)
    b.text("(non monte)", 60.0, 40.2, 0.8)
    b.text("BANC", 70.0, 31.9, 0.8)
    b.text("(non monte)", 70.0, 40.2, 0.8)
    for i, lab in enumerate(("5V", "CANH", "CANL", "SAFE", "GND", "GND")):
        b.text(lab, 80.0 + i * 3.5, 38.4, 0.8)
    for k in range(N_BRANCH):
        cx, top = branch_frame(k)
        # free row under the choke and the LED, across the whole branch
        y = Y_TOP + 18.6 if top else Y_BOT - 18.6
        b.text("N%d %s" % (k + 1, BRANCH_NAMES[k]), cx + 6.0 if top else cx + 9.0, y, 0.9)
    b.text("1 5V  2 CANH  3 CANL  4 /SAFE  5 GND  6 SHLD", 26.0, 26.6, 0.8)
    b.text("J1 DORSALE", 9.0, 36.0, 0.9, rot=90)

    return b


def add_zones(b):
    """Copper pours, added AFTER routing so the router draws every connection."""
    import pcbnew as Pn
    poly = [(0.0, 0.0), (W, 0.0), (W, H), (0.0, H)]
    b.zone("GND", Pn.F_Cu, poly, priority=0, name="GND_F")
    b.zone("GND", Pn.B_Cu, poly, priority=0, name="GND_B")
    # Extra copper for the trunk 5 V on B.Cu, along the bus band.
    band = [(12.0, 25.5), (W - 4.0, 25.5), (W - 4.0, 46.5), (12.0, 46.5)]
    b.zone("+5V", Pn.B_Cu, band, priority=1, name="5V_BUS")


def main():
    what = sys.argv[1] if len(sys.argv) > 1 else "sch"
    os.makedirs(KICAD_DIR, exist_ok=True)
    pcb_path = os.path.join(KICAD_DIR, PROJECT + ".kicad_pcb")
    if what == "route":
        # Second stage: the board exists and its zones were filled by kicad-cli.
        import kicadpcb as KP
        b = KP.Board(pcb_path, load=True, extra_fp_dirs=(LIB_DIR,))
        work = os.path.join(BOARD_DIR, "build")
        os.makedirs(work, exist_ok=True)
        print(b.autoroute(work, passes=40))
        print("widened", b.widen_tracks(0.15), "necked tracks")
        add_zones(b)
        b.save()
        print("ok: route")
        return
    c = circuit()
    s = build_sch(c)
    uuids = {ref: info["uuid"] for ref, info in s.symbols.items()}
    nc = {ref: info["nc"] for ref, info in s.symbols.items()}
    K.write_project(os.path.join(KICAD_DIR, PROJECT + ".kicad_pro"), NETCLASSES, {})
    if what == "pcb":
        b = build_pcb(c, uuids, nc)
        b.save()
    print("ok:", what, len(c.parts), "parts")


if __name__ == "__main__":
    main()
