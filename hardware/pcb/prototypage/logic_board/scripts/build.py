#!/usr/bin/env python3
"""logic_board v1.0-draft — the small-part half of the mainboard, schematic and layout, in one file.

    python3 build.py sch            # libraries + schematic + project (any Python 3)
    <KiCad python> build.py pcb     # board: placement, keepouts
    <KiCad python> build.py route   # Freerouting for every net, then GND pours
    <KiCad python> build.py drop|patch|stitch|islands   # clean-up driven by build/drc.rpt

Option B of the PCBWay comparison (option A = ../mainboard, unchanged): every circuit with
parts that cannot be soldered with an iron, assembled by PCBWay, on a small 1 oz board.
The 30 A path (battery connector, contactor terminals, motor fuses, bus shunt, driver
outputs) and the isolated 12 V PC converter are off board, on wires and bus bars
(README.md, wiring). The board keeps the three ESP32-DevKitC V4 (wiring hub), CAN, the
safety chain, precharge, chopper control and FET, coil driver, the two TPS54360B hotel
bucks fed by an off-board fused BAT+ wire, INA228 (Kelvin connector to the off-board
shunt), Hall taps, VR/DIR/STOP/EL, IMU and BMS connectors.

Circuits, values and references are those of ../mainboard/scripts/build.py; what changed
and why: ../decisions.md (French).

v1.0-draft — NE PAS FABRIQUER avant P1, la tension de bobine du contacteur,
le niveau logique du BMS et une relecture par un électronicien.
"""

from __future__ import annotations

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD_DIR = os.path.dirname(HERE)
KICAD_DIR = os.path.join(BOARD_DIR, "kicad")
LIB_DIR = os.path.join(KICAD_DIR, "lib")
PCB_DIR = os.path.dirname(os.path.dirname(BOARD_DIR))  # hardware/pcb (board lives in prototypage/)
sys.path.insert(0, os.path.join(PCB_DIR, "scripts"))
sys.path.insert(0, os.path.join(PCB_DIR, "motor_interface", "scripts"))   # mi_gen.add_units (read only)
sys.path.insert(0, os.path.join(PCB_DIR, "safety_power", "scripts"))      # splib via lblib (read only)
sys.path.insert(0, HERE)

import kicadgen as K  # noqa: E402
import lblib  # noqa: E402

PROJECT = "logic_board"
REV = "1.0-draft"
DATE = "2026-11-24"
DRAFT = ("v1.0-draft — ne pas fabriquer avant P1, coil voltage, BMS level, "
         "and a review by an electronics engineer")

W, H = float(os.environ.get("LB_W", "100")), float(os.environ.get("LB_H", "140"))

# ---------------------------------------------------------------------------
#  Parts: (lib_id, footprint, value, LCSC, MPN, manufacturer)
#  LCSC numbers are given where they were already used on the v2 boards or found
#  on lcsc.com; "" = to be sourced by PCBWay from the MPN. Re-check stock before ordering.
# ---------------------------------------------------------------------------
P = {
    # --- through-hole, hand soldered (the 30 A path is off board: README.md, wiring) ---
    # Power entry from the off-board distribution: BAT_F (fused), GND, BUS (fused), CHOP_N, GND.
    "VH5": ("Connector_Generic:Conn_01x05", "Connector_JST:JST_VH_B5P-VH_1x05_P3.96mm_Vertical", "VH 5p",
            "", "B5P-VH(LF)(SN)", "JST"),
    # Precharge resistor of the mainboard (SQP500JB-10R), standing up to save board area.
    "RPRE": ("Device:R", "Resistor_THT:R_Axial_Power_L25.0mm_W9.0mm_P10.16mm_Vertical", "10Ω 5W", "", "SQP500JB-10R",
             "Yageo"),
    "FET_THT": ("Transistor_FET:IRF540N", "Package_TO_SOT_THT:TO-220-3_Vertical", "IRL540N", "", "IRL540NPBF",
                "Infineon"),
    "CP2200": ("Device:C_Polarized", "Capacitor_THT:CP_Radial_D10.0mm_P5.00mm", "2200µF 10V", "C49256788",
               "ERA10V2200M10X16", "Lelon"),
    "ESP32": ("lb:ESP32-DevKitC-V4", "lb:ESP32-DevKitC-V4_Sockets_OpenCenter", "ESP32-DevKitC-V4", "",
              "2x 1x19 female socket 2.54 mm (e.g. Mill-Max 310-43-119-41-001000)", "Espressif (module) / Mill-Max"),
    "XH2": ("Connector_Generic:Conn_01x02", "Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical", "XH 2p", "C158012",
            "B2B-XH-A(LF)(SN)", "JST"),
    "XH3": ("Connector_Generic:Conn_01x03", "Connector_JST:JST_XH_B3B-XH-A_1x03_P2.50mm_Vertical", "XH 3p", "C144394",
            "B3B-XH-A(LF)(SN)", "JST"),
    "XH5": ("Connector_Generic:Conn_01x05", "Connector_JST:JST_XH_B5B-XH-A_1x05_P2.50mm_Vertical", "XH 5p", "C157991",
            "B5B-XH-A(LF)(SN)", "JST"),
    "XH6": ("Connector_Generic:Conn_01x06", "Connector_JST:JST_XH_B6B-XH-A_1x06_P2.50mm_Vertical", "XH 6p", "C157992",
            "B6B-XH-A(LF)(SN)", "JST"),
    "SOCK10": ("Connector_Generic:Conn_01x10", "Connector_PinSocket_2.54mm:PinSocket_1x10_P2.54mm_Vertical",
               "IMU 1x10", "", "1x10 female header 2.54 mm", "generic"),
    "HDR3": ("Connector_Generic:Conn_01x03", "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
             "COIL SEL", "", "1x3 pin header 2.54 mm + 1 jumper shunt", "generic"),
    "GH4": ("Connector_Generic:Conn_01x04", "Connector_JST:JST_GH_SM04B-GHS-TB_1x04-1MP_P1.25mm_Horizontal", "GH 4p",
            "C189895", "SM04B-GHS-TB(LF)(SN)", "JST"),
    "TVS48CA": ("Device:D_TVS", "Diode_SMD:D_SMC", "SMCJ48CA", "C151287", "SMCJ48CA", "Littelfuse"),
    "SS510C": ("Device:D_Schottky", "Diode_SMD:D_SMC", "SS510C", "C19229", "SS510C", "MDD"),
    "B560C": ("Device:D_Schottky", "Diode_SMD:D_SMC", "B560C", "C85100", "B560C-13-F", "Diodes Inc"),
    "SS34": ("Device:D_Schottky", "Diode_SMD:D_SMA", "SS34", "C8678", "SS34", "MDD"),
    "S1M": ("Device:D", "Diode_SMD:D_SMA", "S1M", "C2128", "S1M", "MDD"),
    "B5819W": ("Device:D_Schottky", "Diode_SMD:D_SOD-123", "B5819W", "C8598", "B5819W", "Changjiang"),
    "Z12": ("Device:D_Zener", "Diode_SMD:D_SOD-123", "BZT52C12", "C43491", "BZT52C12", "Changjiang"),
    "NPN": ("Transistor_BJT:MMBT5551L", "Package_TO_SOT_SMD:SOT-23", "MMBT5551", "C2145", "MMBT5551", "Changjiang"),
    "PFET": ("Transistor_FET:SUD50P10-43L", "Package_TO_SOT_SMD:TO-252-2", "SUD50P10-43L", "C41408040",
             "SUD50P10-43L-TP", "MCC"),
    "NFET": ("Transistor_FET:AO3400A", "Package_TO_SOT_SMD:SOT-23", "AO3400A", "C20917", "AO3400A", "AOS"),
    "INA228": ("Sensor_Energy:INA228", "Package_SO:TSSOP-10_3x3mm_P0.5mm", "INA228", "C2887910", "INA228AIDGSR", "TI"),
    "TPS54360B": ("Regulator_Switching:TPS54360DDA", "Package_SO:TI_SO-PowerPAD-8_ThermalVias", "TPS54360BDDAR",
                  "C524806", "TPS54360BDDAR", "TI"),
    "L15": ("Device:L", "Inductor_SMD:L_TaiTech_TMPC1265_13.5x12.5mm", "15µH", "C189912", "SRP1265A-150M", "Bourns"),
    "L33": ("Device:L", "Inductor_SMD:L_TaiTech_TMPC1265_13.5x12.5mm", "33µH", "C2847586", "MDA1365-330M", "Cyntec"),
    "TCAN": ("lb:TCAN1042HV", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", "TCAN1042HVDR", "C127869", "TCAN1042HVDR", "TI"),
    "NUP2105": ("Power_Protection:NUP2105L", "Package_TO_SOT_SMD:SOT-23", "NUP2105L", "C14486", "NUP2105LT1G", "onsemi"),
    "ESD33": ("Diode:ESD5Zxx", "Diode_SMD:D_SOD-523", "ESD5Z3.3", "C397781", "ESD5Z3.3T1G", "onsemi"),
    "TPL5010": ("Timer:TPL5010", "Package_TO_SOT_SMD:SOT-23-6", "TPL5010", "C473912", "TPL5010DDCR", "TI"),
    "LVC1G74": ("lb:74LVC1G74", "Package_SO:SSOP-8_2.95x2.8mm_P0.65mm", "SN74LVC1G74DCT", "", "SN74LVC1G74DCTR", "TI"),
    "LVC1G08": ("74xGxx:74LVC1G08", "Package_TO_SOT_SMD:SOT-23-5", "SN74LVC1G08DBV", "C7666", "SN74LVC1G08DBVR", "TI"),
    "AHCT1G08": ("74xGxx:74AHCT1G08", "Package_TO_SOT_SMD:SOT-23-5", "SN74AHCT1G08DBV", "", "SN74AHCT1G08DBVR", "TI"),
    "LVC3G17": ("74xGxx:74LVC3G17", "Package_SO:SSOP-8_2.95x2.8mm_P0.65mm", "SN74LVC3G17DCT", "", "SN74LVC3G17DCTR",
                "TI"),
    "TLV9062": ("Amplifier_Operational:TLV9062xD", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", "TLV9062IDR", "C398355",
                "TLV9062IDR", "TI"),
    "TLV1701": ("lb:TLV1701", "Package_TO_SOT_SMD:SOT-23-5", "TLV1701", "C130035", "TLV1701AIDBVR", "TI"),
    "UCC27517": ("lb:UCC27517", "Package_TO_SOT_SMD:SOT-23-5", "UCC27517", "C99395", "UCC27517DBVR", "TI"),
    "TPS7A4001": ("lb:TPS7A4001", "lb:HVSSOP-8-1EP_3x3mm_P0.65mm_EP1.57x1.89mm_Pad0.42", "TPS7A4001", "C5144143",
                  "TPS7A4001DGNT", "TI"),
    "LM4040": ("Reference_Voltage:LM4040DBZ-2.5", "Package_TO_SOT_SMD:SOT-23", "LM4040A25", "C9421", "LM4040A25IDBZR",
               "TI"),
    "BAT54S": ("Diode:BAT54S", "Package_TO_SOT_SMD:SOT-23", "BAT54S", "C47546", "BAT54S,215", "Nexperia"),
    "LED_G": ("Device:LED", "LED_SMD:LED_0603_1608Metric", "green", "C72043", "19-217/GHC-YR1S2/3T", "Everlight"),
    "LED_R": ("Device:LED", "LED_SMD:LED_0603_1608Metric", "red", "C2286", "KT-0603R", "Hubei KENTO"),
    "TP": ("Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", "TP", "", "", ""),
}

R0603, R1206 = "Resistor_SMD:R_0603_1608Metric", "Resistor_SMD:R_1206_3216Metric"
RES = {  # value -> (LCSC, MPN, manufacturer); 0603 1 % unless noted
    # 0.1 % thin film: chopper threshold divider, exactly as safety_power v2.1 (simulations.md §1)
    "49.9k-0.1%": ("C2828622", "AR03BTCX4992", "Viking"), "6.19k-0.1%": ("C667011", "TD03G6191BT", "Viking"),
    "0R": ("C21189", "0603WAF0000T5E", "UNI-ROYAL"), "10": ("C22859", "0603WAF100JT5E", "UNI-ROYAL"),
    "100": ("C22775", "0603WAF1000T5E", "UNI-ROYAL"), "120": ("C22787", "0603WAF1200T5E", "UNI-ROYAL"),
    "220-1206": ("C17958", "1206W4F2200T5E", "UNI-ROYAL"), "1k": ("C21190", "0603WAF1001T5E", "UNI-ROYAL"),
    "2.2k": ("C4190", "0603WAF2201T5E", "UNI-ROYAL"), "4.7k": ("C23162", "0603WAF4701T5E", "UNI-ROYAL"),
    "5.23k": ("C23068", "0603WAF5231T5E", "UNI-ROYAL"), "6.8k": ("C23212", "0603WAF6801T5E", "UNI-ROYAL"),
    "10k": ("C25804", "0603WAF1002T5E", "UNI-ROYAL"), "10.2k": ("C22772", "0603WAF1022T5E", "UNI-ROYAL"),
    "10.5k": ("C22855", "0603WAF1052T5E", "UNI-ROYAL"), "10.7k": ("C22857", "0603WAF1072T5E", "UNI-ROYAL"),
    "22k": ("C31850", "0603WAF2202T5E", "UNI-ROYAL"), "33k": ("C4216", "0603WAF3302T5E", "UNI-ROYAL"),
    "47k": ("C25819", "0603WAF4702T5E", "UNI-ROYAL"), "53.6k": ("C23074", "0603WAF5362T5E", "UNI-ROYAL"),
    "59k": ("C23085", "0603WAF5902T5E", "UNI-ROYAL"), "93.1k": ("C228101", "AC0603FR-0793K1L", "Yageo"),
    "100k": ("C25803", "0603WAF1003T5E", "UNI-ROYAL"), "143k": ("C304703", "RS-03K1433FT", "FOJAN"),
    "243k": ("C23351", "0603WAF2433T5E", "UNI-ROYAL"), "1.18M": ("C4072929", "AA0603FR-071M18L", "Yageo"),
    "1.69M": ("C247054", "0603WAF1694T5E", "UNI-ROYAL"), "22k-1206": ("C114942", "RC1206FR-0722KL", "Yageo"),
}
C0603, C0805, C1210 = ("Capacitor_SMD:C_0603_1608Metric", "Capacitor_SMD:C_0805_2012Metric",
                       "Capacitor_SMD:C_1210_3225Metric")
CAP = {  # value -> (symbol, footprint, LCSC, MPN, manufacturer, label)
    "82p": ("Device:C", C0603, "C107056", "CC0603JRNPO9BN820", "Yageo", "82pF C0G"),
    "1n": ("Device:C", C0603, "C1588", "CL10B102KB8NNNC", "Samsung", "1nF"),
    "8.2n": ("Device:C", C0603, "C1322360", "0603B822K500NT", "FH", "8.2nF"),
    "10n/100V": ("Device:C", C0603, "C43253", "0603B103K101NT", "FH", "10nF 100V"),
    "15n": ("Device:C", C0603, "C107076", "CC0603KRX7R9BB153", "Yageo", "15nF"),
    "100n": ("Device:C", C0603, "C14663", "CC0603KRX7R9BB104", "Yageo", "100nF"),
    "100n/100V": ("Device:C", C0603, "C88219", "0603B104K101NT", "FH", "100nF 100V"),
    "1u": ("Device:C", C0603, "C15849", "CL10A105KB8NNNC", "Samsung", "1µF 50V"),
    "1u/100V": ("Device:C", C0805, "C385977", "HMK212BC7105KGHTE", "Taiyo Yuden", "1µF 100V"),
    "10u": ("Device:C", C0805, "C15850", "CL21A106KAYNNNE", "Samsung", "10µF 25V"),
    "2.2u/100V": ("Device:C", C1210, "C153036", "FS32X225K101EGG", "FH", "2.2µF 100V"),
    "22u/25V": ("Device:C", C1210, "C52306", "CL32A226KAJNNNE", "Samsung", "22µF 25V"),
    "47u/10V": ("Device:C", C1210, "C84494", "GRM32ER71A476KE15L", "Murata", "47µF 10V"),
    "47u/100V": ("Device:C_Polarized", "Capacitor_SMD:CP_Elec_8x10", "C48935391", "RV100V47M8X10", "Lelon",
                 "47µF 100V"),
    "100u/25V": ("Device:C_Polarized", "Capacitor_SMD:CP_Elec_6.3x7.7", "C2836443", "RVT100UF25V67RV0011", "Lelon",
                 "100µF 25V"),
}


class Circuit:
    """Collects parts with schematic slot and board placement.

    pcb is either (x, y) — explicit — or a group name: the part is then packed
    into that group's rectangle by `pack()` at board build time."""

    def __init__(self):
        self.parts = []
        self.sx, self.sy, self.sx0, self.rowh = 0.0, 0.0, 0.0, 0.0

    def block(self, title, x, y, cols=40):
        y = max(y, self.sy + self.rowh + (14 if self.parts else 0))
        self.sx0, self.sx, self.sy, self.rowh, self.xmax = x, x, y, 0.0, x + cols * 25
        self.parts.append(dict(text=title, at=(x - 10, y - 14)))

    def _sch(self, w, h):
        if self.sx + w > self.xmax:
            self.sx, self.sy, self.rowh = self.sx0, self.sy + self.rowh, 0.0
        p = (self.sx + (w - 25) / 2, self.sy + h / 2)
        self.sx += w
        self.rowh = max(self.rowh, h)
        return p

    def add(self, ref, part, nets, pcb, rot=0, dnp=False, value=None, in_bom=True, big=False, sch_rot=0,
            units=None):
        lib_id, fp, val, lcsc, mpn, mfr = part
        npins = max(len(nets), 2)
        if units:
            placements = [(u, self._sch(40, 30), 0) for u in units]
            sch = None
        else:
            h = max(24.0, 2.54 * (npins / 2 + 3)) if (big or npins > 4) else 24.0
            w = 60 if big else (40 if npins > 4 else 25)
            sch = self._sch(w, h)
            placements = None
        self.parts.append(dict(ref=ref, lib_id=lib_id, footprint=fp, value=value or val, lcsc=lcsc, mpn=mpn, mfr=mfr,
                               nets=nets, sch=sch, sch_rot=sch_rot, units=placements, pcb=pcb, rot=rot, dnp=dnp,
                               in_bom=in_bom and not ref.startswith("TP")))

    def R(self, ref, value, a, b, pcb, rot=0, dnp=False):
        lcsc, mpn, mfr = RES[value]
        fp = R1206 if value.endswith("-1206") else R0603
        v = value.replace("-1206", "")
        if v.endswith("-0.1%"):
            v = v[:-5] + " 0.1%"
        self.add(ref, ("Device:R", fp, v + ("Ω" if v[-1].isdigit() else ""), lcsc, mpn, mfr), {"1": a, "2": b},
                 pcb, rot, dnp, sch_rot=90)

    def C(self, ref, value, a, b, pcb, rot=0, dnp=False):
        sym, fp, lcsc, mpn, mfr, label = CAP[value]
        self.add(ref, (sym, fp, label, lcsc, mpn, mfr), {"1": a, "2": b}, pcb, rot, dnp, sch_rot=90)


G = "GND"
V5 = "5V"
BAT, BUS = "BAT_F", "BUS"     # BAT_F: fused battery feed (off-board 7.5 A fuse, upstream of the contactor)

MOTORS = (("M1", "AV", "1", "AV_G"), ("M2", "AV", "2", "AV_D"), ("M3", "AR", "1", "AR_G"), ("M4", "AR", "2", "AR_D"))
REMOVED = ("R58",)     # as mainboard: LATCH_QN is driven push-pull by U15 (mainboard decisions M23)

# ---------------------------------------------------------------------------
#  Layout (mm, board origin top left). Top band (y < MOD_TOP): connectors, bucks, power parts.
#  Bottom: the three DevKitC side by side, antennas over the bottom edge; small SMD between
#  the socket rows (under each module). Right column: SAFETY connectors, IMU, INA228.
# ---------------------------------------------------------------------------
# DevKitC sockets (rot 180): x of the J2 row (pins 1..19), J3 row at -25.40; pin 1 at y = MOD_Y.
MOD = {"AV": 27.6, "AR": 56.3, "S": 85.0}
MOD_Y = H - 3.0
MOD_TOP = MOD_Y - 47.2                  # top of the socket courtyards
COL = 87.0                              # right column: x > COL
BUCK_AT = {"B5": (11.0, 31.5), "B12": (49.0, 31.5)}
HOLES = [(3.8, 3.8), (86.0, 4.0), (96.0, H - 4.0), (3.4, 55.6)]


def box(x0, y0, rot=0):
    """Placement by courtyard top-left corner."""
    return ("box", x0, y0), rot


POS = {"J1": box(89.6, 0.5, 90), "J2": box(92.6, 81.0, 90),
       "C17": box(76.6, 22.5), "C15": box(0.5, 41.8), "Q6": box(11.5, 41.8), "Q3": box(23.2, 41.8),
       "R7": box(34.9, 41.8), "D3": box(51.8, 41.8), "D8": box(62.2, 41.8),
       "Q5": box(72.6, 41.8), "Q10": box(87.2, 60.2, 90),
       "J14": box(87.4, 22.5), "J9": box(92.6, 22.5, 90), "J10": box(92.6, 34.0, 90), "J11": box(92.6, 43.0, 90),
       "J13": box(92.6, 52.0, 90), "J8": box(92.6, 61.0, 90), "J15": box(92.9, 70.0, 90),
       "JP1": box(87.6, 50.5), "D1": box(82.6, 8.6, 90), "C1": box(77.0, 34.2, 90), "C2": box(80.8, 34.2, 90),
       "U1": box(87.4, 71.6, 90)}
for _k, (_m, *_r) in enumerate(MOTORS):
    POS["JM%d" % (_k + 1)] = box(8.0 + 18.6 * _k, 0.5)
    POS["JD%d" % (_k + 1)] = box(8.0 + 18.6 * _k, 7.6)
    POS["JC%d" % (_k + 1)] = box(8.0 + 18.6 * _k, 14.7)


def _under(node, y0, y1):
    x = MOD[node]
    return (x - 22.8, MOD_Y - 44.5 + y0, x - 2.6, MOD_Y - 44.5 + y1)


# Packing groups: (x0, y0, x1, y1) on the board.
GROUPS = {
    "hot1": (7.6, 51.3, 22.7, 59.6),
    "pre": (23.2, 49.4, 34.4, 59.6),
    "chop": (34.9, 52.0, 86.5, 59.6),
    "ina": (COL, 78.6, 92.4, H - 9.0),
    # Two rows above the modules: the four Hall taps, then the CAN/VR blocks of both MOTION nodes and the
    # SAFETY connector-side parts. Under the modules only the command stages and the SAFETY logic stay:
    # densely packed parts between the socket rows cut the GND pours into islands (decisions.md L14).
    "tap_M1": (0.5, 60.2, 21.4, 72.0), "tap_M2": (21.9, 60.2, 42.8, 72.0),
    "tap_M3": (43.3, 60.2, 64.2, 72.0), "tap_M4": (64.7, 60.2, 86.5, 72.0),
    "av": (0.5, 72.6, 21.4, MOD_TOP - 0.3), "ar": (21.9, 72.6, 42.8, MOD_TOP - 0.3),
    "left": (43.3, 72.6, 64.2, MOD_TOP - 0.3), "coil": (64.7, 72.6, 86.5, 80.6),
    "brk": (64.7, 81.0, 86.5, MOD_TOP - 0.3),
    "av_cmd": _under("AV", 0.5, 43.0), "ar_cmd": _under("AR", 0.5, 43.0),
    "safe": _under("S", 0.5, 43.0),
}


def circuit() -> Circuit:
    c = Circuit()
    R, C, A = c.R, c.C, c.add

    # =====================================================================
    #  1. Power entry from the off-board distribution, input TVS, Kelvin input of the off-board shunt
    # =====================================================================
    c.block("1. ENTRÉE PUISSANCE (VH 5 broches depuis la distribution hors carte) — BAT_F fusible 7,5 A, BUS fusible "
            "7,5 A, CHOP_N — TVS SMCJ48CA — INA228 sur shunt hors carte (prise Kelvin)", 40, 38)
    # J1 pin currents: BAT_F <= 5.1 A peak (precharge 4.2 A + hotel 0.9 A), BUS <= 4.2 A peak (precharge),
    # CHOP_N <= 1.9 A, GND pins 2 and 5 together <= 3.5 A (hotel + chopper + coil). JST VH: 10 A per contact.
    A("J1", P["VH5"], {"1": BAT, "2": G, "3": BUS, "4": "CHOP_N", "5": G}, "pos", value="PUISSANCE")
    A("D1", P["TVS48CA"], {"1": BAT, "2": G}, "pos")
    C("C1", "2.2u/100V", BAT, G, "pos")
    C("C2", "2.2u/100V", BAT, G, "pos")
    # Kelvin pair from the off-board bus shunt (50 A / 75 mV, 1.5 mΩ), twisted, short: README.md.
    A("J2", P["XH2"], {"1": "SNS_P", "2": "SNS_N"}, "pos", value="SHUNT KELVIN")
    A("U1", P["INA228"], {"1": G, "2": G, "3": None, "4": "I2C_SDA", "5": "I2C_SCL", "6": "3V3_S", "7": G,
                          "8": "INA_N", "9": "INA_N", "10": "INA_P"}, "ina")
    R("R1", "10", "SNS_P", "INA_P", "ina")
    R("R2", "10", "SNS_N", "INA_N", "ina")
    C("C3", "100n", "3V3_S", G, "ina")
    # VBAT (upstream of the contactor) for the SAFETY ADC: 243k / 10k -> 42 V = 1.66 V, 60 V = 2.37 V.
    R("R48", "243k", BAT, "VBAT_ADC", "ina")
    R("R49", "10k", "VBAT_ADC", G, "ina")
    C("C22", "100n", "VBAT_ADC", G, "ina")

    # =====================================================================
    #  2. Precharge: P-FET driven by the SAFETY ESP32, resistor on board (THT, standing)
    # =====================================================================
    c.block("2. PRÉCHARGE — FET P SUD50P10-43L, NPN MMBT5551, 10 Ω 5 W debout sur la carte, diode série SS510C, "
            "sortie vers le bus par J1-3", 40, 0)
    A("Q3", P["PFET"], {"1": "PRE_G", "2": "PRE_P", "3": BAT}, "pos")
    R("R3", "10k", "PRE_G", BAT, "pre")
    A("D2", P["Z12"], {"1": BAT, "2": "PRE_G"}, "pre")
    R("R4", "22k", "PRE_G", "PRE_C", "pre")
    A("Q4", P["NPN"], {"1": "PRE_B", "2": G, "3": "PRE_C"}, "pre")
    R("R5", "4.7k", "PRECH_EN", "PRE_B", "pre")
    R("R6", "100k", "PRE_B", G, "pre")
    A("R7", P["RPRE"], {"1": "PRE_P", "2": "PRE_N"}, "pos")
    A("D3", P["SS510C"], {"1": BUS, "2": "PRE_N"}, "pos")

    # =====================================================================
    #  3. Brake chopper — safety_power v2.1, unchanged values and references
    # =====================================================================
    c.block("3. HACHEUR DE FREINAGE (safety_power v2.1) — analogique, alimenté par le bus (J1-3), ON 43,0 V / "
            "OFF 42,3 V ; résistance 22 Ω 100 W hors carte entre le bus et J1-4", 40, 0)
    A("Q5", P["FET_THT"], {"1": "CH_G", "2": "CHOP_N", "3": G}, "pos")
    A("D8", P["SS510C"], {"1": BUS, "2": "CHOP_N"}, "pos")
    R("R19", "10", BUS, "CH_VIN", "chop")
    C("C9", "1u/100V", "CH_VIN", G, "chop")
    A("U3", P["TPS7A4001"], {"8": "CH_VIN", "5": "CH_VIN", "1": "CH_12V", "2": "CH_FB", "4": G, "9": G, "3": None,
                             "6": None, "7": None}, "chop")
    R("R20", "93.1k", "CH_12V", "CH_FB", "chop")          # 1.173 V x (1 + 93.1/10) = 12.1 V
    R("R21", "10k", "CH_FB", G, "chop")
    C("C10", "10u", "CH_12V", G, "chop")
    A("U4", P["TLV1701"], {"1": "CH_SNS", "3": "CH_REF", "4": "CH_CMD", "5": "CH_12V", "2": G}, "chop")
    R("R22", "10k", "CH_12V", "CH_REF", "chop")
    A("D9", P["LM4040"], {"1": "CH_REF", "2": G, "3": None}, "chop")
    C("C11", "100n", "CH_REF", G, "chop")
    # V_on = 2.5 x (1 + Rt/Rb + Rt/Rh) = 42.95 V; V_off = V_on - V_oh x Rt/Rh = 42.29 V (simulations.md §1).
    R("R23", "49.9k-0.1%", BUS, "CH_T", "chop")
    R("R24", "49.9k-0.1%", "CH_T", "CH_SNS", "chop")
    R("R25", "6.19k-0.1%", "CH_SNS", "CH_B", "chop")
    R("R26", "0R", "CH_B", G, "chop")
    R("R27", "1.69M", "CH_SNS", "CH_CMD", "chop")
    C("C12", "1n", "CH_SNS", G, "chop")
    R("R28", "10k", "CH_12V", "CH_CMD", "chop")
    C("C13", "100n", "CH_12V", G, "chop")
    A("U5", P["UCC27517"], {"3": "CH_CMD", "4": G, "1": "CH_12V", "5": "CH_DRV", "2": G}, "chop")
    C("C14", "1u", "CH_12V", G, "chop")
    R("R29", "10", "CH_DRV", "CH_G", "chop")
    R("R30", "100k", "CH_G", G, "chop")
    R("R31", "100k", "CH_CMD", "CHOP_ACT", "chop")
    R("R32", "33k", "CHOP_ACT", G, "chop")
    # LED on the driver output (12 V), not on the comparator output (v2.1 correction).
    R("R33", "4.7k", "CH_DRV", "CH_LED", "chop")
    A("D10", P["LED_R"], {"1": G, "2": "CH_LED"}, "chop", value="CHOP")
    # Bus voltage after the contactor, for the SAFETY ADC, and the bus-live LED.
    R("R50", "243k", BUS, "VBUS_ADC", "chop")
    R("R51", "10k", "VBUS_ADC", G, "chop")
    C("C23", "100n", "VBUS_ADC", G, "chop")
    R("R34", "22k-1206", BUS, "LED_BUS", "chop")
    A("D11", P["LED_R"], {"1": G, "2": "LED_BUS"}, "chop", value="BUS LIVE")

    # =====================================================================
    #  5. Hotel rails, upstream of the contactor (the 12 V PC converter is off board)
    # =====================================================================
    c.block("5. RAILS HÔTEL (amont contacteur, BAT_F fusible hors carte) — anti-inversion, 5 V et 12 V AUX "
            "(TPS54360B), 5V_BRAKE ; le 12 V PC isolé est un module hors carte", 40, 0)
    A("Q6", P["PFET"], {"1": "REV_G", "2": BAT, "3": "HOTEL_IN"}, "pos")
    R("R35", "100k", "REV_G", G, "hot1")
    A("D12", P["Z12"], {"1": "HOTEL_IN", "2": "REV_G"}, "hot1")
    C("C15", "47u/100V", "HOTEL_IN", G, "pos")
    C("C16", "2.2u/100V", "HOTEL_IN", G, "hot1")

    def buck(p, x, y, out, l_part, rfb_top, rc, cc, cout):
        """TPS54360B, 400 kHz (RT 243 k), UVLO 24 V on / 20 V off: safety_power decisions §5.1-5.2.
        Same parts and relative placement as the mainboard bucks."""
        A("U" + p, P["TPS54360B"], {"1": p + "_BOOT", "2": "HOTEL_IN", "3": p + "_EN", "4": p + "_RT", "5": p + "_FB",
                                    "6": p + "_COMP", "7": G, "8": p + "_SW", "9": G}, (x, y), 0, big=True)
        C("C" + p + "1", "2.2u/100V", "HOTEL_IN", G, (x - 8.0, y - 6.8), 0)
        C("C" + p + "2", "2.2u/100V", "HOTEL_IN", G, (x - 3.2, y - 6.8), 0)
        C("C" + p + "3", "100n/100V", "HOTEL_IN", G, (x + 0.8, y - 6.8), 0)
        C("C" + p + "4", "100n", p + "_BOOT", p + "_SW", (x + 3.6, y - 4.9), 0)
        R("R" + p + "1", "1.18M", "HOTEL_IN", p + "_EN", (x - 7.0, y - 3.0), 0)
        R("R" + p + "2", "59k", p + "_EN", G, (x - 7.0, y - 1.3), 0)
        R("R" + p + "3", "243k", p + "_RT", G, (x - 7.0, y + 0.4), 0)
        R("R" + p + "4", rfb_top, out, p + "_FB", (x - 7.0, y + 2.1), 0)
        R("R" + p + "5", "10.2k", p + "_FB", G, (x - 7.0, y + 3.8), 0)
        R("R" + p + "6", rc, p + "_COMP", p + "_CZ", (x - 2.0, y + 4.6), 0)
        C("C" + p + "5", cc, p + "_CZ", G, (x - 2.0, y + 6.3), 0)
        C("C" + p + "6", "82p", p + "_COMP", G, (x + 1.6, y + 4.6), 0)
        A("D" + p, P["B560C"], {"1": p + "_SW", "2": G}, (x + 8.6, y + 1.0), 270)
        A("L" + p, P[l_part], {"1": p + "_SW", "2": out}, (x + 20.0, y - 1.0), 0)
        for j in range(3):
            C("C%s%d" % (p, 7 + j), cout, out, G, (x + 14.5 + 4.6 * j, y + 7.8), 0)

    buck("B5", *BUCK_AT["B5"], V5, "L15", "53.6k", "10.7k", "8.2n", "47u/10V")            # 5.00 V
    buck("B12", *BUCK_AT["B12"], "12V_AUX", "L33", "143k", "10.5k", "15n", "22u/25V")      # 12.0 V
    A("D13", P["LED_G"], {"1": G, "2": "LED_5V"}, "hot1", value="5V")
    R("R36", "1k", V5, "LED_5V", "hot1")

    # 12 V AUX: fan, and the contactor coil when the selector is on 12 V.
    A("J8", P["XH2"], {"1": "12V_AUX", "2": G}, "pos", value="FAN 12V")
    # Coil supply selector: jumper 1-2 = 12 V AUX, 2-3 = battery (HOTEL_IN). No jumper = coil
    # unpowered: the contactor cannot close until the coil voltage is known.
    A("JP1", P["HDR3"], {"1": "12V_AUX", "2": "COIL_SUP", "3": "HOTEL_IN"}, "pos", value="BOBINE 12V|BAT")

    # 5V_BRAKE (D5): diode-fed 2200 µF reservoir, one 220 Ω per driver harness (short-circuit limit 23 mA).
    A("D14", P["SS34"], {"1": "BRK_RES", "2": V5}, "brk")
    A("C17", P["CP2200"], {"1": "BRK_RES", "2": G}, "pos")
    C("C18", "10u", "BRK_RES", G, "brk")
    for k, (m, node, i, name) in enumerate(MOTORS):
        R("R%d" % (37 + k), "220-1206", "BRK_RES", "5V_BRAKE_" + m, "brk")

    # =====================================================================
    #  6. SAFETY ESP32: CAN, /SAFE, watchdog latch, contactor coil, IMU, BMS
    # =====================================================================
    c.block("6. ESP32 SAFETY — CAN, /SAFE (pull-up 1 kΩ via l'arrêt d'urgence, pull-down 10 kΩ), verrou watchdog (D7), "
            "bobine du contacteur, IMU BNO085, BMS", 40, 0)
    esp_s = {"1": "3V3_S", "2": None, "3": "SAFE_N_IN_S", "4": "VBAT_ADC", "5": "VBUS_ADC", "6": "BMS_RX",
             "7": "COIL_EN", "8": "IMU_RST", "9": "IMU_INT", "10": "IMU_PS0", "11": "PRECH_EN", "12": "BMS_TX",
             "13": None, "14": G, "15": "SAFE_HOLD", "16": None, "17": None, "18": None, "19": "5V_S",
             "20": G, "21": "IMU_MOSI", "22": "IMU_CS", "23": None, "24": None, "25": "SAFE_REARM", "26": G,
             "27": "IMU_MISO", "28": "IMU_SCK", "29": "CAN_TX_S", "30": None, "31": None, "32": "CAN_RX_S",
             "33": "I2C_SCL", "34": "WD_DONE", "35": "I2C_SDA", "36": None, "37": None, "38": None}
    A("U10", P["ESP32"], esp_s, (MOD["S"], MOD_Y), 180, big=True, value="ESP32 SAFETY")
    # 5 V to the module through a Schottky: a USB cable on one DevKitC cannot back-feed the board.
    A("D16", P["B5819W"], {"1": "5V_S", "2": V5}, "safe")
    C("C21", "10u", "5V_S", G, "safe")
    for ref, v, a, b in (("R42", "10k", "CAN_TX_S", "3V3_S"), ("R43", "2.2k", "I2C_SDA", "3V3_S"),
                         ("R44", "2.2k", "I2C_SCL", "3V3_S"), ("R45", "100k", "WD_DONE", G),
                         ("R46", "100k", "SAFE_REARM", G), ("R47", "100k", "COIL_EN", G)):
        R(ref, v, a, b, "safe")
    A("U11", P["TCAN"], {"1": "CAN_TX_S", "4": "CAN_RX_S", "8": G, "5": "3V3_S", "3": V5, "7": "CANH", "6": "CANL",
                         "2": G}, "safe")
    C("C24", "100n", V5, G, "safe")
    C("C25", "100n", "3V3_S", G, "safe")
    # PC link (CANable Pro 1.1, its own switchable termination) and the ESD clamp at the connector.
    A("J9", P["XH3"], {"1": "CANH", "2": "CANL", "3": G}, (4.0, 140.5), 90, value="CAN PC")
    A("D19", P["NUP2105"], {"1": "CANH", "2": "CANL", "3": G}, "left")

    # /SAFE: single pull-up 1 kΩ through the E-stop NC contact CH1 (J10), single pull-down 10 kΩ.
    R("R55", "1k", "3V3_S", "ESTOP1_A", "left")
    A("J10", P["XH2"], {"1": "ESTOP1_A", "2": "SAFE_N"}, (4.0, 111.0), 90, value="ARU /SAFE (NF)")
    R("R56", "10k", "SAFE_N", G, "safe")
    A("D20", P["ESD33"], {"1": "SAFE_N", "2": G}, "left")
    A("Q8", P["NFET"], {"1": "SAFE_HOLD", "2": G, "3": "SAFE_N"}, "safe")       # SAFETY holds /SAFE low
    R("R57", "10k", "SAFE_HOLD", "3V3_S", "safe")                                 # boot / absent: held low
    A("Q9", P["NFET"], {"1": "LATCH_QN", "2": G, "3": "SAFE_N"}, "safe")         # watchdog latch
    R("R59", "1k", "SAFE_N", "SAFE_N_IN_S", "safe")
    # Watchdog (D7): TPL5010 1.0 s; RSTn (open drain) and power-on RC both clear the latch.
    A("U14", P["TPL5010"], {"1": "3V3_S", "2": G, "3": "WD_DELAY", "4": "WD_DONE", "5": None, "6": "WD_RST_N"},
      "safe")
    R("R60", "5.23k", "WD_DELAY", G, "safe")
    R("R62", "100", "WD_RST_N", "TRIP_N", "safe")
    R("R61", "10k", "TRIP_N", "3V3_S", "safe")
    C("C30", "1u", "TRIP_N", G, "safe")                    # power-on clear: TRIP_N low for ~10 ms
    C("C31", "100n", "3V3_S", G, "safe")
    A("U15", P["LVC1G74"], {"2": "3V3_S", "1": "SAFE_REARM", "6": "TRIP_N", "7": "3V3_S", "8": "3V3_S",
                            "5": "LATCH_Q", "3": "LATCH_QN", "4": G}, "safe")
    C("C32", "100n", "3V3_S", G, "safe")

    # Contactor coil: COIL_EN AND LATCH_Q (5 V logic) -> IRL540N low side. The E-stop NC contact CH2
    # (J11) is in series with the coil: it opens the coil with no code at all.
    A("U16", P["AHCT1G08"], {"1": "COIL_EN", "2": "LATCH_Q", "3": G, "4": "COIL_GD", "5": V5}, "coil")
    C("C33", "100n", V5, G, "coil")
    R("R63", "100", "COIL_GD", "COIL_G", "coil")
    R("R64", "100k", "COIL_G", G, "coil")
    A("Q10", P["FET_THT"], {"1": "COIL_G", "2": "COIL_N", "3": G}, (30.0, 126.0), 0)
    A("D21", P["S1M"], {"1": "COIL_P", "2": "COIL_N"}, "coil")                 # flyback, across the coil
    A("J11", P["XH2"], {"1": "COIL_SUP", "2": "COIL_P"}, (4.0, 120.0), 90, value="ARU BOBINE (NF)")
    A("J13", P["XH2"], {"1": "COIL_P", "2": "COIL_N"}, (4.0, 129.0), 90, value="BOBINE CONTACTEUR")

    # IMU: BNO085 breakout plugged on a 1x10 socket, pin order of the breakout, SPI as board_config.h.
    A("J14", P["SOCK10"], {"1": "3V3_S", "2": G, "3": "IMU_SCK", "4": "IMU_MISO", "5": "IMU_MOSI", "6": "IMU_CS",
                           "7": "IMU_INT", "8": "IMU_RST", "9": "3V3_S", "10": "IMU_PS0"}, (3.5, 80.0), 0,
      value="IMU BNO085")
    C("C34", "100n", "3V3_S", G, "left")

    # BMS UART (Xiaomi M365 Pro): ground = battery negative now; series resistors and clamps at the connector.
    A("J15", P["GH4"], {"1": "BMS_R", "2": "BMS_T", "3": G, "4": None}, (14.0, 145.5), 0, value="BMS")
    R("R65", "1k", "BMS_R", "BMS_RX", "left")
    A("D22", P["BAT54S"], {"1": G, "2": "3V3_S", "3": "BMS_RX"}, "left")
    R("R66", "10k", "BMS_RX", "3V3_S", "left")
    R("R67", "22k", "BMS_RX", G, "left", dnp=True)         # 5 V BMS option: see decisions.md (PACK_ID / M3)
    R("R68", "100", "BMS_TX", "BMS_T", "left")
    A("D23", P["BAT54S"], {"1": G, "2": "3V3_S", "3": "BMS_TX"}, "left")

    # =====================================================================
    #  7. MOTION nodes (AVANT, ARRIÈRE): CAN, /SAFE input, VR (DAC + TLV9062), DIR/STOP/EL
    # =====================================================================
    for node, ru, cu in (("AV", 100, 100), ("AR", 200, 200)):
        c.block("7. ESP32 MOTION_%s — CAN, VR = DAC interne x 1,68 (TLV9062), DIR/STOP drain ouvert, "
                "EL = GPIO22 ET /SAFE" % ("AVANT" if node == "AV" else "ARRIÈRE"), 40, 0)
        v3, v5m = "3V3_" + node, "5V_" + node
        n = lambda s: s + "_" + node  # noqa: E731
        esp = {"1": v3, "2": None, "3": n("HALL1_A"), "4": n("HALL1_B"), "5": n("HALL1_C"), "6": n("HALL2_A"),
               "7": n("HALL2_B"), "8": n("HALL2_C"), "9": n("DAC1"), "10": n("DAC2"), "11": n("DIR1"),
               "12": n("DIR2"), "13": None, "14": G, "15": n("STOP1"), "16": None, "17": None, "18": None, "19": v5m,
               "20": G, "21": n("STOP2"), "22": n("BRAKE_REL"), "23": None, "24": None, "25": None, "26": G,
               "27": n("SAFE_N_IN"), "28": None, "29": n("CAN_TX"), "30": None, "31": None, "32": n("CAN_RX"),
               "33": None, "34": None, "35": None, "36": None, "37": None, "38": None}
        A("U%d" % (ru // 10 * 1 + 10), P["ESP32"], esp, (MOD[node], MOD_Y), 180, big=True,
          value="ESP32 MOTION_" + node)
        g = node.lower()
        A("D%d" % (cu + 1), P["B5819W"], {"1": v5m, "2": V5}, g)
        C("C%d" % (cu + 1), "10u", v5m, G, g)
        A("U%d" % (ru + 1), P["TCAN"], {"1": n("CAN_TX"), "4": n("CAN_RX"), "8": G, "5": v3, "3": V5, "7": "CANH",
                                         "6": "CANL", "2": G}, g)
        C("C%d" % (cu + 2), "100n", V5, G, g)
        C("C%d" % (cu + 3), "100n", v3, G, g)
        R("R%d" % (ru + 1), "10k", n("CAN_TX"), v3, g)          # GPIO5 strapping: high at boot
        R("R%d" % (ru + 2), "47k", "SAFE_N", n("SAFE_N_IN"), g)
        R("R%d" % (ru + 3), "100k", n("BRAKE_REL"), G, g)        # floats at reset -> brake applied
        # VR: ESP32 8-bit DAC (GPIO25/26) x (1 + 6.8k/10k) = 1.68 -> 0..~5 V; 100 k holds VR = 0 when unpowered.
        A("U%d" % (ru + 2), P["TLV9062"], {"3": n("DAC1"), "2": n("VR1_FB"), "1": n("VR1_O"), "5": n("DAC2"),
                                           "6": n("VR2_FB"), "7": n("VR2_O"), "4": G, "8": V5}, g, units=(1, 2, 3))
        C("C%d" % (cu + 4), "100n", V5, G, g)
        for j in ("1", "2"):
            base = ru + 4 + (0 if j == "1" else 4)
            R("R%d" % base, "6.8k", n("VR%s_O" % j), n("VR%s_FB" % j), g)
            R("R%d" % (base + 1), "10k", n("VR%s_FB" % j), G, g)
            R("R%d" % (base + 2), "100k", n("DAC" + j), G, g)
        # Command stage per driver (gap group): DIR, STOP open drain; EL = AND(BRAKE_REL, /SAFE) -> AO3400A.
        gg = g + "_cmd"
        for j in ("1", "2"):
            m = [mm for mm in MOTORS if mm[1] == node and mm[2] == j][0][0]
            q = ru + 20 + (0 if j == "1" else 10)
            for k, (sig, gpio) in enumerate((("DIR_" + m, n("DIR" + j)), ("STOP_" + m, n("STOP" + j)))):
                A("Q%d" % (q + k), P["NFET"], {"1": gpio, "2": G, "3": sig}, gg)
                R("R%d" % (q + k), "100k", gpio, G, gg)
            A("U%d" % (q), P["LVC1G08"], {"1": n("BRAKE_REL"), "2": "SAFE_N", "3": G, "4": "EL_%s_G" % m, "5": v3}, gg)
            C("C%d" % (q), "100n", v3, G, gg)
            R("R%d" % (q + 2), "100k", "EL_%s_G" % m, G, gg)
            A("Q%d" % (q + 2), P["NFET"], {"1": "EL_%s_G" % m, "2": G, "3": "EL_" + m}, gg)
            # VR output: 100 Ω against the cable capacitance, 10 k defines VR when the op-amp is off.
            R("R%d" % (q + 3), "100", n("VR%s_O" % j), "VR_" + m, gg)
            R("R%d" % (q + 4), "10k", "VR_" + m, G, gg)
    # Termination at the far end of the on-board bus (the CANable terminates the other end).
    R("R52", "120", "CANH", "CANL", "ar")

    # =====================================================================
    #  8. Motors: Hall passthrough motor -> driver, tap to the MOTION ESP32; command connector
    # =====================================================================
    for k, (m, node, j, name) in enumerate(MOTORS):
        c.block("8. MOTEUR %s (%s) — passage Hall moteur→variateur, prélèvement 2,2 kΩ / 2,2 kΩ + 10 nF / BAT54S / "
                "SN74LVC3G17, commande VR DIR EL STOP + 5V_BRAKE" % (m, name), 40, 0)
        v5m, hall = "5V_MOT_" + m, ["H%s_%s" % (m, x) for x in "ABC"]
        pins = {"1": v5m, "2": G, "3": hall[0], "4": hall[1], "5": hall[2]}
        A("JM%d" % (k + 1), P["XH5"], dict(pins), "pos", 0, value="HALL MOTEUR " + name)
        A("JD%d" % (k + 1), P["XH5"], dict(pins), "pos", 0, value="HALL VARIATEUR " + name)
        A("JC%d" % (k + 1), P["XH6"], {"1": "VR_" + m, "2": "DIR_" + m, "3": "EL_" + m, "4": "STOP_" + m, "5": G,
                                       "6": "5V_BRAKE_" + m}, "pos", 0, value="COMMANDE " + name)
        base = 300 + 20 * k
        gt = "tap_" + m
        for x in range(3):
            line, filt = hall[x], hall[x] + "_F"
            R("R%d" % (base + 3 * x), "2.2k", v5m, line, gt)
            R("R%d" % (base + 3 * x + 1), "2.2k", line, filt, gt)
            C("C%d" % (base + x), "10n/100V", filt, G, gt)
            A("D%d" % (base + x), P["BAT54S"], {"1": G, "2": v5m, "3": filt}, gt)
        o = ["HALL%s_%s_%s" % (j, x, node) for x in "ABC"]
        A("U%d" % base, P["LVC3G17"], {"1": hall[0] + "_F", "7": o[0], "6": hall[1] + "_F", "2": o[1],
                                       "3": hall[2] + "_F", "5": o[2], "4": G, "8": "3V3_" + node}, gt,
          units=(1, 2, 3, 4))
        C("C%d" % (base + 5), "100n", "3V3_" + node, G, gt)

    # Test points
    tps = [(V5, "safe"), ("3V3_S", "safe"), ("SAFE_N", "safe"), ("TRIP_N", "safe"), ("LATCH_Q", "safe"),
           ("CANH", "left"), ("CANL", "left"), (G, "left"), ("CH_12V", "chop"), ("CH_CMD", "chop"),
           ("CHOP_ACT", "chop"), (G, "chop"), ("12V_AUX", "brk"), ("3V3_AV", "av"), ("3V3_AR", "ar")]
    for i, (net, grp) in enumerate(tps):
        A("TP%d" % (i + 1), P["TP"], {"1": net}, grp, value=net)
    # Board placement of this board (overrides the mainboard coordinates kept in the code above).
    for p in c.parts:
        if "ref" in p and p["ref"] in POS:
            p["pcb"], p["rot"] = POS[p["ref"]]
    return c


# ---------------------------------------------------------------------------
#  Schematic
# ---------------------------------------------------------------------------
PWR_NETS = (G, BAT, BUS, V5, "HOTEL_IN", "3V3_S", "3V3_AV", "3V3_AR", "12V_AUX", "CH_12V",
            "CH_VIN", "5V_S", "5V_AV", "5V_AR", "BRK_RES", "5V_MOT_M1", "5V_MOT_M2", "5V_MOT_M3", "5V_MOT_M4")


def fields_of(p):
    f = {}
    if p["lcsc"]:
        f["LCSC"] = p["lcsc"]
    if p["mpn"]:
        f["MPN"] = p["mpn"]
    if p.get("mfr"):
        f["Manufacturer"] = p["mfr"]
    return f


def build_sch(c: Circuit):
    import mi_gen
    lblib.write_all(LIB_DIR)
    s = K.Schematic(PROJECT, "Retriever — logic_board (option B : petite carte logique)", paper="A0", rev=REV,
                    date=DATE, company="Retriever, open hardware (CERN-OHL-S-2.0)",
                    comments=(DRAFT, "Chemin 30 A hors carte (README.md) : relecture experte obligatoire",
                              "Généré par scripts/build.py — ne pas éditer à la main",
                              "Décisions et calculs : hardware/pcb/logic_board/decisions.md"),
                    extra_lib_dirs=(LIB_DIR,))
    for p in c.parts:
        if "text" in p:
            s.text(p["text"], p["at"], 2.5, True)
            continue
        if p["units"]:
            mi_gen.add_units(s, p["ref"], p["lib_id"], p["value"], p["footprint"], p["units"], p["nets"],
                             fields=fields_of(p), dnp=p["dnp"], in_bom=p["in_bom"])
        else:
            s.add(p["ref"], p["lib_id"], p["value"], p["footprint"], p["sch"], rot=p["sch_rot"], nets=p["nets"],
                  fields=fields_of(p), dnp=p["dnp"], in_bom=p["in_bom"])
    for i, net in enumerate(PWR_NETS):
        s.power_flag(net, (40 + i * 15, 20))
    s.text(DRAFT, (40, 10), 3.0, True)
    s.write(os.path.join(KICAD_DIR, PROJECT + ".kicad_sch"))
    for kind, ext in (("sym", "kicad_sym"), ("fp", "pretty")):
        with open(os.path.join(KICAD_DIR, kind + "-lib-table"), "w") as f:
            f.write('(%s_lib_table\n\t(version 7)\n\t(lib (name "lb") (type "KiCad") '
                    '(uri "${KIPRJMOD}/lib/lb.%s") (options "") (descr "logic_board, généré par lblib.py"))\n)\n'
                    % (kind, ext))
    return s


# ---------------------------------------------------------------------------
#  Board
# ---------------------------------------------------------------------------
# 1 oz (35 µm) external copper. Widths for ΔT = 20 °C, IPC-2221B external formula (decisions.md §4).
PWR42 = ["/BAT_F", "/BUS", "/PRE_P", "/PRE_N", "/CHOP_N"]
SW = ["/B5_SW", "/B12_SW"]
HV_SIG = ["/SNS_*", "/INA_P", "/INA_N", "/PRE_G", "/PRE_C", "/REV_G", "/CH_VIN", "/CH_T", "/LED_BUS"] + \
    ["/%s_%s" % (p, n) for p in ("B5", "B12") for n in ("BOOT", "EN", "RT", "FB", "COMP", "CZ")]
NETCLASSES = [
    {"name": "Default", "track": 0.2, "clearance": 0.2, "via": 0.6, "drill": 0.3},
    # 42 V wires of J1 (precharge 4.2 A peak for 0.3 s, chopper 1.9 A): 1.2 mm on 1 oz ≈ 3.7 A at ΔT 20 °C.
    # Clearance 0.5 mm, as the mainboard HV_PWR polygons.
    {"name": "PWR42", "track": 1.2, "clearance": 0.5, "via": 0.8, "drill": 0.4, "patterns": PWR42},
    # Buck switch nodes (peak inductor current <= 1.7 A at the loads of this board): 1.0 mm.
    {"name": "SW", "track": 1.0, "clearance": 0.3, "via": 0.8, "drill": 0.4, "patterns": SW},
    # 42 V small signals: 0.2 mm (IPC-2221B B4, coated external, 31-50 V: 0.13 mm).
    {"name": "HV_SIG", "track": 0.25, "clearance": 0.2, "via": 0.6, "drill": 0.3, "patterns": HV_SIG},
    # Hotel feed (<= 0.9 A at 30 V, no PC converter on this board) and the contactor coil (<= 1 A): 0.8 mm.
    {"name": "HV_RAIL", "track": 0.8, "clearance": 0.3, "via": 0.8, "drill": 0.4,
     "patterns": ["/HOTEL_*", "/COIL_SUP", "/COIL_P", "/COIL_N"]},
    # Logic rails (<= 1.3 A): 0.6 mm on 1 oz ≈ 2.2 A at ΔT 20 °C.
    {"name": "RAIL", "track": 0.6, "clearance": 0.2, "via": 0.8, "drill": 0.4,
     "patterns": ["/5V", "/5V_*", "/12V_*", "/BRK_RES"]},
    {"name": "RAIL_LO", "track": 0.3, "clearance": 0.2, "via": 0.6, "drill": 0.3,
     "patterns": ["/3V3_*", "/CH_12V", "/GND"]},
]
# PCBWay 2 layers, 1 oz: 5/5 mil possible; we keep 0.2 mm except inside fine-pitch pads (0.15 mm minimum).
RULES = dict(track=0.15, clearance=0.15, via=0.6, drill=0.3, annular=0.13, edge_clearance=0.4)

# Same limits in the project file (kicad-cli reads them from there).
PRO_RULES = {"min_clearance": 0.15, "min_copper_edge_clearance": 0.4, "min_track_width": 0.15,
             "min_via_diameter": 0.6, "min_via_annular_width": 0.13, "min_through_hole_diameter": 0.3,
             "min_hole_clearance": 0.25, "min_hole_to_hole": 0.5, "min_text_height": 0.8,
             "min_text_thickness": 0.12, "min_silk_clearance": 0.0}


def footprint_box(fp):
    """Courtyard box of a placed footprint (falls back to the full bounding box)."""
    import pcbnew as Pn
    try:
        cy = fp.GetCourtyard(Pn.F_CrtYd)
        if cy.OutlineCount():
            bb = cy.BBox()
            return (Pn.ToMM(bb.GetLeft()), Pn.ToMM(bb.GetTop()), Pn.ToMM(bb.GetRight()), Pn.ToMM(bb.GetBottom()))
    except Exception:
        pass
    bb = fp.GetBoundingBox(False)
    return (Pn.ToMM(bb.GetLeft()), Pn.ToMM(bb.GetTop()), Pn.ToMM(bb.GetRight()), Pn.ToMM(bb.GetBottom()))


def pack(b, c):
    """Row packing of every grouped part into its rectangle. Each group takes the largest gap between
    courtyards (2.0 mm down to 0.4 mm) with which it still fits: spread parts route better."""
    import kicadpcb as KP
    groups = {}
    for p in c.parts:
        if "ref" in p and isinstance(p["pcb"], str):
            groups.setdefault(p["pcb"], []).append(p)
    for g, parts in groups.items():
        x0, y0, x1, y1 = GROUPS[g]
        order = sorted(parts, key=lambda q: -(footprint_box(b.fps[q["ref"]])[3] - footprint_box(b.fps[q["ref"]])[1]))
        for gap in (2.0, 1.6, 1.3, 1.0, 0.8, 0.6, 0.45, 0.4):
            cx, cy, rowh, pos, ok = x0, y0, 0.0, {}, True
            for p in order:
                fp = b.fps[p["ref"]]
                fp.SetPosition(KP.pt(0, 0))
                bx0, by0, bx1, by1 = footprint_box(fp)
                w, h = bx1 - bx0, by1 - by0
                if cx + w > x1 + 1e-6:
                    cx, cy, rowh = x0, cy + rowh + gap, 0.0
                if cy + h > y1 + 1e-6:
                    ok = False
                    break
                pos[p["ref"]] = (cx - bx0, cy - by0)
                cx += w + gap
                rowh = max(rowh, h)
            if ok:
                break
        if not ok:
            raise RuntimeError("group %s full (%d parts)" % (g, len(parts)))
        for ref, (x, y) in pos.items():
            b.fps[ref].SetPosition(KP.pt(x, y))
        print("group %-7s %2d parts, gap %.2f, used %.1f of %.1f mm" % (g, len(parts), gap, cy + rowh - y0, y1 - y0))


def build_pcb(c: Circuit, sch_uuids: dict, nc_pins: dict):
    import kicadpcb as KP

    b = KP.Board(os.path.join(KICAD_DIR, PROJECT + ".kicad_pcb"), copper_layers=2, extra_fp_dirs=(LIB_DIR,))
    b.rules(**RULES)
    for nc in NETCLASSES:
        b.netclass(nc["name"], nc["track"], nc["clearance"], nc.get("via", 0.8), nc.get("drill", 0.3),
                   nc.get("patterns", []))
    for p in c.parts:
        if "text" in p:
            continue
        nc = {k: v.replace("/", "{slash}") for k, v in nc_pins[p["ref"]].items()}
        info = {"footprint": p["footprint"], "value": p["value"], "uuid": sch_uuids[p["ref"]], "fields": fields_of(p),
                "dnp": p["dnp"], "in_bom": p["in_bom"], "nets": p["nets"], "nc": nc}
        spec = p["pcb"]
        if spec == "pos":
            raise RuntimeError("no board position for " + p["ref"])
        if isinstance(spec, tuple) and spec[0] == "box":
            fp = b.place(p["ref"], info, 0.0, 0.0, p["rot"])
            bx0, by0, _, _ = footprint_box(fp)
            fp.SetPosition(KP.pt(spec[1] - bx0, spec[2] - by0))
            continue
        x, y = spec if not isinstance(spec, str) else (0.0, 0.0)
        b.place(p["ref"], info, x, y, p["rot"])
    pack(b, c)
    b.outline(0, 0, W, H, r=3.0)
    for i, (x, y) in enumerate(HOLES):
        b.hole("H%d" % (i + 1), x, y, name="MountingHole_3.2mm_M3", net=None)
        keepout(b, circle(x, y, 3.4), tracks=True)
    # No copper under the part of each DevKitC antenna that lies over the board.
    for node, x in MOD.items():
        keepout(b, rect(x - 26.9, MOD_Y + 1.3, x + 1.5, H - 0.2), tracks=True)
    return b


# ---- copper helpers ---------------------------------------------------------

def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def circle(x, y, r, n=24):
    return [(x + r * math.cos(2 * math.pi * i / n), y + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def polyset(pts):
    import pcbnew as Pn
    s = Pn.SHAPE_POLY_SET()
    s.NewOutline()
    for x, y in pts:
        s.Append(Pn.FromMM(x), Pn.FromMM(y))
    return s


def set_outline(z, pts, raw=False):
    """Zone outline. On a board that had items removed in the same process, ZONE.Outline() comes back
    as an untyped SWIG pointer: fall back to SetOutline() with a poly the zone owns."""
    import pcbnew as Pn
    cv = (lambda v: int(v)) if raw else Pn.FromMM
    o = z.Outline()
    if hasattr(o, "NewOutline"):
        o.NewOutline()
        for x, y in pts:
            o.Append(cv(x), cv(y))
        return
    ps = Pn.SHAPE_POLY_SET()
    ps.NewOutline()
    for x, y in pts:
        ps.Append(cv(x), cv(y))
    ps.thisown = False
    z.SetOutline(ps)


def keepout(b, pts, tracks=False, layers=None, fills=True, vias=None):
    import pcbnew as Pn
    z = Pn.ZONE(b.b)
    z.SetIsRuleArea(True)
    if layers is None:
        z.SetLayerSet(Pn.LSET.AllCuMask())
    else:
        ls = Pn.LSET()
        for L in layers:
            ls.AddLayer(L)
        z.SetLayerSet(ls)
    z.SetDoNotAllowZoneFills(fills)
    z.SetDoNotAllowTracks(tracks)
    z.SetDoNotAllowVias(tracks if vias is None else vias)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowFootprints(False)
    set_outline(z, pts)
    b.b.Add(z)


def lt(b, net, pts, width, layer):
    """Hand-drawn track, locked: the clean-up steps never remove it."""
    import pcbnew as Pn
    import kicadpcb as KP
    for a, c in zip(pts, pts[1:]):
        t = Pn.PCB_TRACK(b.b)
        t.SetStart(KP.pt(*a))
        t.SetEnd(KP.pt(*c))
        t.SetWidth(KP.mm(width))
        t.SetLayer(layer)
        t.SetNet(b.net(net))
        t.SetLocked(True)
        b.b.Add(t)


def via(b, net, x, y, size=0.8, drill=0.4):
    import pcbnew as Pn
    import kicadpcb as KP
    v = Pn.PCB_VIA(b.b)
    v.SetPosition(KP.pt(x, y))
    v.SetWidth(KP.mm(size))
    v.SetDrill(KP.mm(drill))
    v.SetNet(b.net(net))
    v.SetLocked(True)
    b.b.Add(v)


def pad_xy(b, ref, num):
    import pcbnew as Pn
    fp = b.b.FindFootprintByReference(ref)
    for p in fp.Pads():
        if p.GetNumber() == num:
            v = p.GetPosition()
            return Pn.ToMM(v.x), Pn.ToMM(v.y)
    raise KeyError((ref, num))


def silkscreen(b):
    import pcbnew as Pn
    t = b.text

    def back(s, x, y, size=1.0, rot=0):
        tx = t(s, x, y, size, layer=Pn.B_SilkS, rot=rot)
        tx.SetMirrored(True)

    # Banner on the bottom face (under the bucks: only SMD there) and a short one on the top face.
    for i, line in enumerate(("RETRIEVER logic_board " + REV,
                              "v1.0-draft - NE PAS FABRIQUER - ne pas fabriquer avant P1,",
                              "coil voltage, BMS level, and a review by an electronics engineer",
                              "option B : chemin 30 A hors carte, voir README.md",
                              "J1 : 1 BAT_F (fus. 7,5 A)  2 GND  3 BUS (fus. 7,5 A)  4 CHOP_N  5 GND",
                              "colonne droite : CAN PC, ARU /SAFE, ARU BOBINE, BOBINE,",
                              "FAN 12V, BMS, SHUNT KELVIN ; IMU BNO085 a gauche")):
        back(line, W / 2 - 6, 25.6 + 1.6 * i, 1.2 if i == 0 else 0.9)
    t("v1.0-draft - NE PAS FABRIQUER", 48.0, 22.5, 0.8)
    # Connector rows: one column per driver; row labels on the top face, driver names on the back,
    # between the pad rows.
    t("HALL MOT.", 81.3, 4.0, 0.8, rot=90)
    t("HALL VAR.", 6.0, 11.0, 0.8, rot=90)
    t("CMD VAR.", 6.0, 18.1, 0.8, rot=90)
    for k, (m, node, j, name) in enumerate(MOTORS):
        x = 8.0 + 18.6 * k
        back("%s (%s) HALL MOTEUR" % (name, m), x + 8.0, 5.5, 0.8)
        back("HALL VARIATEUR", x + 8.0, 8.3, 0.8)
        back("VR DIR EL STOP GND 5VB", x + 9.2, 20.2, 0.8)
    jp = b.b.FindFootprintByReference("JP1")
    if jp is not None and hasattr(jp, "GetPosition"):
        x, y = Pn.ToMM(jp.GetPosition().x), Pn.ToMM(jp.GetPosition().y)
        back("1-2:12V 2-3:BAT", x - 2.3, y + 2.54, 0.8, rot=90)
    for node, x in MOD.items():
        lab = {"S": "SAFETY", "AV": "MOTION AVANT", "AR": "MOTION ARRIERE"}[node]
        t("ESP32 " + lab, x - 12.7, MOD_TOP + 1.2, 0.8)
        t("ANTENNE", x - 12.7, MOD_Y + 1.8, 0.8)


def main():
    what = sys.argv[1] if len(sys.argv) > 1 else "sch"
    os.makedirs(KICAD_DIR, exist_ok=True)
    pcb_path = os.path.join(KICAD_DIR, PROJECT + ".kicad_pcb")
    if what in ("drop", "patch"):
        import kicadpcb as KP
        import patchroute_lb as patchroute
        b = KP.Board(pcb_path, load=True, extra_fp_dirs=(LIB_DIR,))
        rpt = os.path.join(BOARD_DIR, "build", "drc.rpt")
        if what == "drop":
            print("dropped:", drop_violations(b, rpt))
        else:
            # GND is not autorouted (see autoroute): with LB_PATCH_GND=1 the GND pads the pours missed are
            # joined to the nearest GND copper too.
            ign = () if os.environ.get("LB_PATCH_GND") == "1" else ("/" + G,)
            print("patched:", patchroute.finish(b.b, rpt, net_clearance, W, H, ignore_nets=ign))
        b.save()
        return
    if what == "reroute":
        # Second Freerouting run on the routed board. With LB_ROUTE_GND=1 the GND pours are taken out
        # first, so that GND is routed as an ordinary net through the room the signals left, and put
        # back afterwards (the pours alone split into islands between the signal tracks).
        import kicadpcb as KP
        import pcbnew as Pn
        b = KP.Board(pcb_path, load=True, extra_fp_dirs=(LIB_DIR,))
        pours = [z for z in b.b.Zones() if z.GetZoneName() in ("GND_F", "GND_B")]
        locked = []
        if os.environ.get("LB_ROUTE_GND") == "1":
            for z in pours:
                b.b.Remove(z)
            # keep the signal routing: Freerouting leaves "protected" (locked) wires alone
            for t in b.b.GetTracks():
                if not t.IsLocked():
                    t.SetLocked(True)
                    locked.append((t.GetClass(), Pn.ToMM(t.GetStart().x), Pn.ToMM(t.GetStart().y)))
            b.save()
            b = KP.Board(pcb_path, load=True, extra_fp_dirs=(LIB_DIR,))
        work = os.path.join(BOARD_DIR, "build")
        print(autoroute(b, work, passes=int(os.environ.get("PASSES", "4")), threads=0))
        b.save()
        if os.environ.get("LB_ROUTE_GND") == "1":
            b = KP.Board(pcb_path, load=True, extra_fp_dirs=(LIB_DIR,))
            load_nets(b)
            for t in b.b.GetTracks():          # nothing stays locked after this step
                t.SetLocked(False)
            print("widened", b.widen_tracks(0.2), "necked tracks")
            gnd_pours(b)
            b.save()
        print("ok: reroute")
        return
    if what == "silk":
        import kicadpcb as KP
        b = KP.Board(pcb_path, load=True, extra_fp_dirs=(LIB_DIR,))
        for d in list(b.b.GetDrawings()):
            if d.GetClass() == "PCB_TEXT":
                b.b.Remove(d)
        silkscreen(b)
        b.save()
        print("ok: silk")
        return
    if what == "stitch":
        import kicadpcb as KP
        b = KP.Board(pcb_path, load=True, extra_fp_dirs=(LIB_DIR,))
        load_nets(b)
        print("GND stitching vias:", stitch(b))
        b.save()
        return
    if what == "joinroute":
        import kicadpcb as KP
        b = KP.Board(pcb_path, load=True, extra_fp_dirs=(LIB_DIR,))
        load_nets(b)
        join_route(b)
        b.save()
        return
    if what == "join":
        import kicadpcb as KP
        b = KP.Board(pcb_path, load=True, extra_fp_dirs=(LIB_DIR,))
        load_nets(b)
        print("GND joining vias:", join_islands(b))
        b.save()
        return
    if what == "gndvias":
        import kicadpcb as KP
        b = KP.Board(pcb_path, load=True, extra_fp_dirs=(LIB_DIR,))
        load_nets(b)
        print("GND pad vias:", gnd_vias(b, os.path.join(BOARD_DIR, "build", "drc.rpt")))
        b.save()
        return
    if what == "islands":
        import kicadpcb as KP
        b = KP.Board(pcb_path, load=True, extra_fp_dirs=(LIB_DIR,))
        load_nets(b)
        print("GND island vias:", island_vias(b))
        b.save()
        return
    if what == "route":
        import kicadpcb as KP
        b = KP.Board(pcb_path, load=True, extra_fp_dirs=(LIB_DIR,))
        work = os.path.join(BOARD_DIR, "build")
        os.makedirs(work, exist_ok=True)
        print(autoroute(b, work, passes=int(os.environ.get("PASSES", "40")), threads=int(os.environ.get("THREADS", "6"))))
        print("widened", b.widen_tracks(0.2), "necked tracks")
        gnd_pours(b)
        b.save()
        print("ok: route")
        return
    c = circuit()
    s = build_sch(c)
    uuids = {ref: info["uuid"] for ref, info in s.symbols.items()}
    nc = {ref: info["nc"] for ref, info in s.symbols.items()}
    write_project(os.path.join(KICAD_DIR, PROJECT + ".kicad_pro"))
    if what == "pcb":
        b = build_pcb(c, uuids, nc)
        print("GND trunks:", gnd_trunks(b))
        print("GND fan-out vias:", gnd_fanout(b))
        silkscreen(b)
        b.save()
    print("ok:", what, len([p for p in c.parts if "ref" in p]), "parts")


def write_project(path):
    """K.write_project writes a minimal .kicad_pro; keep the design rules and net classes that DRC reads,
    and the rest of an existing project file (KiCad adds its own settings on save)."""
    import json
    K.write_project(path + ".new", NETCLASSES, PRO_RULES)
    new = json.load(open(path + ".new"))
    os.remove(path + ".new")
    if os.path.exists(path):
        try:
            old = json.load(open(path))
        except ValueError:
            old = {}
        old.setdefault("board", {}).setdefault("design_settings", {}).setdefault("rules", {}).update(
            new["board"]["design_settings"]["rules"])
        old["net_settings"] = new["net_settings"]
        old["meta"] = new["meta"]
        new = old
    with open(path, "w") as f:
        json.dump(new, f, indent=2)


def autoroute(b, workdir, passes=40, threads=6, margin_um=20):
    """As safety_power: every clearance in the DSN raised by `margin_um` before Freerouting runs."""
    import re
    import subprocess
    import pcbnew as Pn
    import kicadpcb as KP
    dsn, ses = os.path.join(workdir, "board.dsn"), os.path.join(workdir, "board.ses")
    for f in (dsn, ses):
        if os.path.exists(f):
            os.remove(f)
    if not Pn.ExportSpecctraDSN(b.b, dsn):
        raise RuntimeError("DSN export failed")
    txt = open(dsn).read()
    txt = re.sub(r"\(clearance ([\d.]+)\)", lambda m: "(clearance %g)" % (float(m.group(1)) + margin_um), txt)
    if os.environ.get("LB_ROUTE_GND", "0") != "1":
        # GND is not routed: both faces are poured with GND afterwards, plus stitching and island vias
        # (stitch, islands). Routing it only took room from the signals.
        txt = re.sub(r"\n    \(net /GND\n.*?(?=\n    \((?:net|class) )", "", txt, flags=re.S)
        txt = re.sub(r"(\(class [^\n]*?) /GND\b", r"\1", txt)
        txt = re.sub(r"(\n\s+[^(\n]*?) /GND\b", r"\1", txt)
    open(dsn, "w").write(txt)
    # One Freerouting at a time, 3 GB heap, one thread: the default heap and threads used ~14 GB of RAM.
    cmd = [KP.JAVA, "-Xmx3g", "-jar", KP.FREEROUTING, "-de", dsn, "-do", ses, "-mp", str(passes), "-mt", "1",
           "--gui.enabled=false"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    log = (r.stdout + r.stderr).splitlines()
    if not os.path.exists(ses) or not Pn.ImportSpecctraSES(b.b, ses):
        raise RuntimeError("Freerouting/SES failed:\n" + "\n".join(log[-20:]))
    return "\n".join(l for l in log if "unrouted" in l and ("completed:" in l))[-3000:]


def net_clearance(net):
    import fnmatch
    for nc in NETCLASSES[1:]:
        if any(fnmatch.fnmatch(net, pat) for pat in nc.get("patterns", [])):
            return nc["clearance"]
    return NETCLASSES[0]["clearance"]


def drop_violations(b, report):
    """Delete routed tracks/vias flagged by the last DRC (Freerouting/KiCad rounding), as safety_power."""
    import re
    import pcbnew as Pn
    if not os.path.exists(report):
        return 0
    bad = []
    for blk in re.split(r"\n(?=\[)", open(report).read()):
        m = re.match(r"\[(\w+)\]", blk)
        if not m or m.group(1) not in ("clearance", "copper_edge_clearance", "annular_width", "shorting_items",
                                         "hole_to_hole", "holes_co_located", "track_dangling", "hole_clearance",
                                         "via_dangling") + (("items_not_allowed",) if os.environ.get("LB_DROP_ALL") else ()):
            continue
        for x, y, kind, net in re.findall(r"@\(([-\d.]+) mm, ([-\d.]+) mm\): (Piste|Via|Track) \[([^\]]+)\]", blk):
            bad.append((float(x), float(y), kind, net))
    n = 0
    for t in list(b.b.GetTracks()):
        if t.IsLocked() and not os.environ.get("LB_DROP_ALL"):
            continue
        is_via = t.GetClass() == "PCB_VIA"
        for x, y, kind, net in bad:
            if t.GetNetname() != net or (kind == "Via") != is_via:
                continue
            if is_via:
                p = t.GetPosition()
                hit = math.hypot(Pn.ToMM(p.x) - x, Pn.ToMM(p.y) - y) < 0.02
            else:
                s0, s1 = t.GetStart(), t.GetEnd()
                ax, ay, bx, by = Pn.ToMM(s0.x), Pn.ToMM(s0.y), Pn.ToMM(s1.x), Pn.ToMM(s1.y)
                L2 = (bx - ax) ** 2 + (by - ay) ** 2
                u = 0 if L2 == 0 else max(0, min(1, ((x - ax) * (bx - ax) + (y - ay) * (by - ay)) / L2))
                hit = math.hypot(ax + u * (bx - ax) - x, ay + u * (by - ay) - y) < 0.02
            if hit:
                b.b.Remove(t)
                n += 1
                break
    return n


def load_nets(b):
    """kicadpcb.Board creates nets on demand; on a loaded board, reuse the existing ones."""
    for name, ni in b.b.GetNetsByName().items():
        b._nets[str(name)] = ni


def stitch(b, pitch=float(os.environ.get("STITCH", "4.0"))):
    """GND vias wherever both GND pours are present with room to spare, so that no copper island of
    either face is left floating. Run on a filled board; refill afterwards."""
    import pcbnew as Pn
    b.fill()
    zf = [z for z in b.b.Zones() if z.GetZoneName() == "GND_F"]
    zb = [z for z in b.b.Zones() if z.GetZoneName() in ("GND_B",)]

    def inside(zs, layer, x, y, r):
        for z in zs:
            fp = z.GetFilledPolysList(layer)
            pts = [(x, y)] + [(x + r * math.cos(a * math.pi / 4), y + r * math.sin(a * math.pi / 4)) for a in range(8)]
            if all(fp.Contains(Pn.VECTOR2I(Pn.FromMM(px), Pn.FromMM(py))) for px, py in pts):
                return True
        return False

    holes = [(Pn.ToMM(t.GetPosition().x), Pn.ToMM(t.GetPosition().y), Pn.ToMM(t.GetDrillValue()) / 2)
             for t in b.b.GetTracks() if t.GetClass() == "PCB_VIA"]
    for fp in b.b.GetFootprints():
        for p in fp.Pads():
            if p.GetDrillSize().x > 0:
                q = p.GetPosition()
                holes.append((Pn.ToMM(q.x), Pn.ToMM(q.y), Pn.ToMM(max(p.GetDrillSize().x, p.GetDrillSize().y)) / 2))
    import kicadpcb as KP
    n = 0
    y = 2.0
    while y < H - 1.0:
        x = 2.0
        while x < W - 1.0:
            if inside(zf, Pn.F_Cu, x, y, 0.65) and inside(zb, Pn.B_Cu, x, y, 0.65) and \
                    all(math.hypot(x - hx, y - hy) > hr + 0.15 + 0.6 for hx, hy, hr in holes):
                v = Pn.PCB_VIA(b.b)                   # not locked: the clean-up may remove it
                v.SetPosition(KP.pt(x, y))
                v.SetWidth(KP.mm(0.6))
                v.SetDrill(KP.mm(0.3))
                v.SetNet(b.net(G))
                b.b.Add(v)
                holes.append((x, y, 0.15))
                n += 1
            x += pitch
        y += pitch
    return n


def island_vias(b):
    """One GND via in every GND pour island that holds neither a via nor a plated hole (an island
    reached only by SMD pads is cut off from the rest of GND). Run on a filled board."""
    import pcbnew as Pn
    V = lambda x, y: Pn.VECTOR2I(Pn.FromMM(x), Pn.FromMM(y))  # noqa: E731
    zones = {Pn.F_Cu: [], Pn.B_Cu: []}
    for z in b.b.Zones():
        if z.GetNetname() == "/" + G and not z.GetIsRuleArea():
            for L in zones:
                if z.IsOnLayer(L):
                    zones[L].append(z.GetFilledPolysList(L))
    anchors = [t.GetPosition() for t in b.b.GetTracks() if t.GetNetname() == "/" + G and t.GetClass() == "PCB_VIA"]
    anchors += [p.GetPosition() for fp in b.b.GetFootprints() for p in fp.Pads()
                if p.GetNetname() == "/" + G and p.GetDrillSize().x > 0]
    holes = [(Pn.ToMM(t.GetPosition().x), Pn.ToMM(t.GetPosition().y)) for t in b.b.GetTracks() if t.GetClass() == "PCB_VIA"]
    holes += [(Pn.ToMM(p.GetPosition().x), Pn.ToMM(p.GetPosition().y)) for fp in b.b.GetFootprints()
              for p in fp.Pads() if p.GetDrillSize().x > 0]

    def infill(polys, x, y, r):
        pts = [(x, y)] + [(x + r * math.cos(a * math.pi / 4), y + r * math.sin(a * math.pi / 4)) for a in range(8)]
        return any(all(ps.Contains(V(px, py)) for px, py in pts) for ps in polys)

    import kicadpcb as KP
    added = 0
    for L, other in ((Pn.F_Cu, Pn.B_Cu), (Pn.B_Cu, Pn.F_Cu)):
        for ps in zones[L]:
            for i in range(ps.OutlineCount()):
                one = Pn.SHAPE_POLY_SET()
                one.AddOutline(ps.Outline(i))
                for h in range(ps.HoleCount(i)):
                    one.AddHole(ps.Hole(i, h))
                if any(one.Contains(a) for a in anchors):
                    continue
                bb = one.BBox()
                x0, y0, x1, y1 = Pn.ToMM(bb.GetLeft()), Pn.ToMM(bb.GetTop()), Pn.ToMM(bb.GetRight()), Pn.ToMM(bb.GetBottom())
                y, done = y0 + 0.4, False
                while y < y1 and not done:
                    x = x0 + 0.4
                    while x < x1 and not done:
                        if infill([one], x, y, 0.6) and infill(zones[other], x, y, 0.6) and \
                                all(math.hypot(x - hx, y - hy) > 1.1 for hx, hy in holes):
                            v = Pn.PCB_VIA(b.b)
                            v.SetPosition(KP.pt(x, y))
                            v.SetWidth(KP.mm(0.6))
                            v.SetDrill(KP.mm(0.3))
                            v.SetNet(b.net(G))
                            b.b.Add(v)
                            holes.append((x, y))
                            anchors.append(V(x, y))
                            added += 1
                            done = True
                        x += 0.2
                    y += 0.2
    return added


def gnd_trunks(b):
    """GND skeleton on B.Cu drawn before routing (locked, Freerouting routes around it): one track along
    the top band under the bucks, one above the modules, and one down the middle of each module. It
    keeps every region of the board on one ground once the signals have cut the pours up (decisions L14)."""
    import pcbnew as Pn
    B = Pn.B_Cu
    w = 0.8
    n = 0
    for y in (41.3, 89.6):
        lt(b, G, [(2.0, y), (86.0, y)], w, B)
        n += 1
    lt(b, G, [(86.0, 89.6), (98.6, 89.6)], w, B)
    for node, x in MOD.items():
        xc = x - 12.7 if node != "AR" else x - 12.8
        lt(b, G, [(xc, 41.3), (xc, MOD_Y - 2.0)], w, B)
        n += 1
    return n


def gnd_fanout(b):
    """Before routing: one GND via next to every SMD GND pad (short track, no via in pad). GND is not
    autorouted (autoroute) and the two GND pours are joined at every one of these vias, so the pours
    still form one ground once the signals have cut them up. Locked: the clean-up keeps them."""
    import pcbnew as Pn
    pts = []
    for fp in b.b.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname() == "/" + G and p.GetAttribute() == Pn.PAD_ATTRIB_SMD:
                q = p.GetPosition()
                pts.append((round(Pn.ToMM(q.x), 4), round(Pn.ToMM(q.y), 4)))
    return _gnd_vias_at(b, sorted(set(pts)), lock=True)


def gnd_vias(b, report):
    """GND is not autorouted: for every GND pad that the last DRC reports unconnected, add a short track
    and a via to the other face where nothing of another net is near (the GND pour of that face then
    takes it). Deterministic; run on a filled board, refill afterwards."""
    import re
    import pcbnew as Pn
    import kicadpcb as KP
    if not os.path.exists(report):
        return 0
    pts = set()
    for blk in re.split(r"\n(?=\[)", open(report).read()):
        if not blk.startswith("[unconnected_items"):
            continue
        for x, y, what in re.findall(r"@\(([-\d.]+) mm, ([-\d.]+) mm\): (Pad[^\[]*)\[/GND\]", blk):
            pts.add((round(float(x), 3), round(float(y), 3)))
    return _gnd_vias_at(b, sorted(pts))


def _gnd_vias_at(b, pts, lock=False):
    import pcbnew as Pn
    import kicadpcb as KP
    gnd = b.net(G)
    items = [t for t in b.b.GetTracks()] + [p for fp in b.b.GetFootprints() for p in fp.Pads()]
    rules = [z for z in b.b.Zones() if z.GetIsRuleArea() and z.GetDoNotAllowVias()]
    gvias = [(Pn.ToMM(t.GetPosition().x), Pn.ToMM(t.GetPosition().y)) for t in b.b.GetTracks()
             if t.GetClass() == "PCB_VIA"]
    VIA_D, TRK = 0.6, 0.3
    added = 0
    for (x, y) in pts:
        pad = None
        for fp in b.b.GetFootprints():
            for p in fp.Pads():
                q = p.GetPosition()
                if p.GetNetCode() == gnd.GetNetCode() and abs(Pn.ToMM(q.x) - x) < 0.01 and abs(Pn.ToMM(q.y) - y) < 0.01:
                    pad = p
        if pad is None:
            continue
        layer = Pn.F_Cu if pad.IsOnLayer(Pn.F_Cu) else Pn.B_Cu
        done = False
        for r in (0.8, 1.0, 1.2, 1.5, 1.8, 2.2, 2.7):
            for k in range(16):
                a = 2 * math.pi * k / 16
                vx, vy = x + r * math.cos(a), y + r * math.sin(a)
                if not (0.8 < vx < W - 0.8 and 0.8 < vy < H - 0.8):
                    continue
                if any(z.Outline().Contains(KP.pt(vx, vy)) for z in rules) or \
                        any(math.hypot(vx - gx, vy - gy) < VIA_D + 0.3 for gx, gy in gvias):
                    continue
                ok = True
                via_shape = Pn.SHAPE_CIRCLE(KP.pt(vx, vy), KP.mm(VIA_D / 2))
                seg = Pn.SHAPE_SEGMENT(KP.pt(x, y), KP.pt(vx, vy), KP.mm(TRK))
                for it in items:
                    if it.GetClass() == "PAD" and it.GetDrillSizeX() > 0 and \
                            math.hypot(Pn.ToMM(it.GetPosition().x) - vx, Pn.ToMM(it.GetPosition().y) - vy) < \
                            Pn.ToMM(it.GetDrillSizeX()) / 2 + 0.15 + 0.6:
                        ok = False
                        break
                    if it.GetNetCode() == gnd.GetNetCode():
                        continue
                    clr = KP.mm(max(net_clearance(it.GetNetname()), 0.2) + 0.02)
                    for L in (Pn.F_Cu, Pn.B_Cu):
                        if not it.IsOnLayer(L):
                            continue
                        sh = it.GetEffectiveShape(L)
                        if sh.Collide(via_shape, clr) or (L == layer and sh.Collide(seg, clr)):
                            ok = False
                            break
                        if it.GetClass() == "PAD" and it.GetDrillSizeX() > 0 and \
                                math.hypot(Pn.ToMM(it.GetPosition().x) - vx, Pn.ToMM(it.GetPosition().y) - vy) < \
                                Pn.ToMM(it.GetDrillSizeX()) / 2 + 0.15 + 0.6:
                            ok = False
                            break
                    if not ok:
                        break
                if ok:
                    t = Pn.PCB_TRACK(b.b)
                    t.SetStart(KP.pt(x, y))
                    t.SetEnd(KP.pt(vx, vy))
                    t.SetWidth(KP.mm(TRK))
                    t.SetLayer(layer)
                    t.SetNet(gnd)
                    t.SetLocked(lock)
                    b.b.Add(t)
                    v = Pn.PCB_VIA(b.b)
                    v.SetPosition(KP.pt(vx, vy))
                    v.SetWidth(KP.mm(VIA_D))
                    v.SetDrill(KP.mm(0.3))
                    v.SetNet(gnd)
                    v.SetLocked(lock)
                    b.b.Add(v)
                    items += [t, v]
                    gvias.append((vx, vy))
                    added += 1
                    done = True
                    break
            if done:
                break
    return added


def join_islands(b):
    """GND is not autorouted, so the GND pours split into groups of islands (an island joins the
    islands of the other face through GND vias and plated pads). Merge the groups: wherever an
    island of one group lies over an island of another group on the other face with room for a via,
    put a GND via there; repeat until no more merges are possible. Run on a filled board."""
    import pcbnew as Pn
    import kicadpcb as KP
    V = lambda x, y: Pn.VECTOR2I(Pn.FromMM(x), Pn.FromMM(y))  # noqa: E731
    isl, groups, main = gnd_groups(b)
    gid = {}
    for n, g in enumerate(groups):
        for k in g:
            gid[k] = n
    par = list(range(len(groups)))

    def find(i):
        while par[i] != i:
            par[i] = par[par[i]]
            i = par[i]
        return i

    holes = [(Pn.ToMM(t.GetPosition().x), Pn.ToMM(t.GetPosition().y), Pn.ToMM(t.GetWidth(Pn.F_Cu)) / 2)
             for t in b.b.GetTracks() if t.GetClass() == "PCB_VIA"]
    holes += [(Pn.ToMM(p.GetPosition().x), Pn.ToMM(p.GetPosition().y),
               Pn.ToMM(max(p.GetDrillSize().x, p.GetDrillSize().y)) / 2)
              for fp in b.b.GetFootprints() for p in fp.Pads() if p.GetDrillSize().x > 0]

    def infill(ps, x, y, r):
        return ps.Contains(V(x, y)) and all(
            ps.Contains(V(x + r * math.cos(a * math.pi / 4), y + r * math.sin(a * math.pi / 4))) for a in range(8))

    added = 0
    F = [k for k in range(len(isl)) if isl[k][0] == Pn.F_Cu]
    Bk = [k for k in range(len(isl)) if isl[k][0] == Pn.B_Cu]
    for kf in F:
        bbf = isl[kf][1].BBox()
        for kb in Bk:
            if find(gid[kf]) == find(gid[kb]):
                continue
            bbb = isl[kb][1].BBox()
            x0 = max(Pn.ToMM(bbf.GetLeft()), Pn.ToMM(bbb.GetLeft())) + 0.35
            x1 = min(Pn.ToMM(bbf.GetRight()), Pn.ToMM(bbb.GetRight())) - 0.35
            y0 = max(Pn.ToMM(bbf.GetTop()), Pn.ToMM(bbb.GetTop())) + 0.35
            y1 = min(Pn.ToMM(bbf.GetBottom()), Pn.ToMM(bbb.GetBottom())) - 0.35
            if x1 < x0 or y1 < y0:
                continue
            done = False
            y = y0
            while y <= y1 and not done:
                x = x0
                while x <= x1 and not done:
                    if infill(isl[kf][1], x, y, 0.32) and infill(isl[kb][1], x, y, 0.32) and \
                            all(math.hypot(x - hx, y - hy) > hr + 0.3 + 0.25 for hx, hy, hr in holes):
                        v = Pn.PCB_VIA(b.b)
                        v.SetPosition(KP.pt(x, y))
                        v.SetWidth(KP.mm(0.6))
                        v.SetDrill(KP.mm(0.3))
                        v.SetNet(b.net(G))
                        b.b.Add(v)
                        holes.append((x, y, 0.3))
                        par[find(gid[kf])] = find(gid[kb])
                        added += 1
                        done = True
                    x += 0.1
                y += 0.1
    left = len(set(find(i) for i in range(len(groups))))
    print("GND groups: %d before, %d after %d joining vias" % (len(groups), left, added))
    return added

def gnd_groups(b):
    """Filled GND islands of both faces grouped by what joins them (vias, plated pads, tracks, SMD pads).
    Returns (islands, groups, main) with islands = [(layer, SHAPE_POLY_SET)], groups = lists of indices."""
    import pcbnew as Pn
    isl = []
    for z in b.b.Zones():
        if z.GetNetname() != "/" + G or z.GetIsRuleArea():
            continue
        for L in (Pn.F_Cu, Pn.B_Cu):
            if not z.IsOnLayer(L):
                continue
            ps = z.GetFilledPolysList(L)
            for i in range(ps.OutlineCount()):
                one = Pn.SHAPE_POLY_SET()
                one.AddOutline(ps.Outline(i))
                for h in range(ps.HoleCount(i)):
                    one.AddHole(ps.Hole(i, h))
                isl.append((L, one))
    par = list(range(len(isl)))

    def find(i):
        while par[i] != i:
            par[i] = par[par[i]]
            i = par[i]
        return i

    def where(L, pt):
        return [k for k, (LL, ps) in enumerate(isl) if LL == L and ps.Contains(pt)]

    def join(ks):
        for k in ks[1:]:
            par[find(k)] = find(ks[0])

    for t in b.b.GetTracks():
        if t.GetNetname() != "/" + G:
            continue
        if t.GetClass() == "PCB_VIA":
            join(where(Pn.F_Cu, t.GetPosition()) + where(Pn.B_Cu, t.GetPosition()))
        else:
            join(where(t.GetLayer(), t.GetStart()) + where(t.GetLayer(), t.GetEnd()))
    for fp in b.b.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname() != "/" + G:
                continue
            join([k for L in (Pn.F_Cu, Pn.B_Cu) if p.IsOnLayer(L) for k in where(L, p.GetPosition())])
    groups = {}
    for k in range(len(isl)):
        groups.setdefault(find(k), []).append(k)
    groups = list(groups.values())
    main = max(groups, key=lambda g: sum(isl[k][1].Area() for k in g)) if groups else []
    return isl, groups, main


def join_route(b):
    """For every GND group cut off from the main one, route (patchroute A*, both faces, vias allowed)
    from one of its GND pads to the nearest copper of the main GND pours. Run on a filled board."""
    import pcbnew as Pn
    import patchroute_lb as PR
    V = lambda x, y: Pn.VECTOR2I(Pn.FromMM(x), Pn.FromMM(y))  # noqa: E731
    isl, groups, main = gnd_groups(b)
    r = PR.Router(b.b, net_clearance, ())
    r.W, r.H = W, H
    mainset = set(main)
    pads = [p for fp in b.b.GetFootprints() for p in fp.Pads() if p.GetNetname() == "/" + G]
    done = failed = 0
    for g in groups:
        if g is main:
            continue
        a = []
        for p in pads:
            c = p.GetPosition()
            lays = tuple(L for L in (Pn.F_Cu, Pn.B_Cu) if p.IsOnLayer(L))
            if any(isl[k][0] in lays and isl[k][1].Contains(c) for k in g):
                a.append((Pn.ToMM(c.x), Pn.ToMM(c.y), lays))
        if not a:
            continue
        ax, ay = a[0][0], a[0][1]
        cand = []
        for m in mainset:
            L, ps = isl[m]
            for d in (2.0, 4.0, 7.0):
                y = ay - d
                while y <= ay + d:
                    x = ax - d
                    while x <= ax + d:
                        if 0.8 < x < W - 0.8 and 0.8 < y < H - 0.8 and all(
                                ps.Contains(V(x + 0.3 * dx, y + 0.3 * dy)) for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1))):
                            cand.append((round(x, 1), round(y, 1), (L,)))
                        x += 0.4
                    y += 0.4
                if len(cand) > 20:
                    break
        cand = sorted(set(cand), key=lambda c: math.hypot(c[0] - ax, c[1] - ay))[:300]
        if not cand:
            failed += 1
            continue
        ends = r.route("/" + G, a, cand)
        if ends:
            for e, cands in ((ends[0], a), (ends[1], cand)):
                best = min((c for c in cands if e[2] in c[2]), key=lambda c: math.hypot(c[0] - e[0], c[1] - e[1]))
                if math.hypot(best[0] - e[0], best[1] - e[1]) > 1e-4:
                    r._track("/" + G, (best[0], best[1], e[2]), e)
            done += 1
        else:
            failed += 1
    print("GND groups cut off: %d, joined: %d, failed: %d" % (len(groups) - 1, done, failed))
    return done


def gnd_pours(b):
    """GND on both layers over the whole board, added after routing (lowest priority)."""
    import pcbnew as Pn
    for layer, name in ((Pn.F_Cu, "GND_F"), (Pn.B_Cu, "GND_B")):
        b.zone(G, layer, rect(0.4, 0.4, W - 0.4, H - 0.4), priority=0, clearance=0.25, name=name)


if __name__ == "__main__":
    main()
