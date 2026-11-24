#!/usr/bin/env python3
"""mainboard v1.0-draft — the whole board, schematic and layout, in one file.

    python3 build.py sch            # libraries + schematic + project (any Python 3)
    <KiCad python> build.py pcb     # board: placement, power copper, keepouts
    <KiCad python> build.py route   # Freerouting for the signals, then GND pours
    <KiCad python> build.py drop|patch   # clean-up driven by build/drc.rpt

One board replaces the three v2 boards (safety_power, motor_interface x2,
safety_bus_distribution) for a first, cheap build: battery input (XT30),
external mechanical contactor (out/return terminals), precharge, brake
chopper, 4 fused driver outputs, hotel rails, and three ESP32-DevKitC V4
(SAFETY, MOTION_AVANT, MOTION_ARRIERE) on sockets with CAN on traces.

The circuit is described once, in `circuit()`; `sch` and `pcb` both read it.
Decisions and computed values: ../decisions.md (French).

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
sys.path.insert(0, os.path.join(PCB_DIR, "safety_power", "scripts"))      # splib via mblib (read only)
sys.path.insert(0, HERE)

import kicadgen as K  # noqa: E402
import mblib  # noqa: E402

PROJECT = "mainboard"
REV = "1.0-draft"
DATE = "2026-11-23"
DRAFT = ("v1.0-draft — ne pas fabriquer avant P1, coil voltage, BMS level, "
         "and a review by an electronics engineer")

W, H = 180.0, 150.0
STRIP = 40.5            # power strip: y < STRIP

# ---------------------------------------------------------------------------
#  Parts: (lib_id, footprint, value, LCSC, MPN, manufacturer)
#  LCSC numbers are given where they were already used on the v2 boards or found
#  on lcsc.com; "" = to be sourced by PCBWay from the MPN. Re-check stock before ordering.
# ---------------------------------------------------------------------------
P = {
    # --- power path (through-hole, hand soldered) ---
    "XT30": ("Connector_Generic:Conn_01x02", "Connector_AMASS:AMASS_XT30PW-M_1x02_P2.50mm_Horizontal", "XT30PW-M",
             "C431092", "XT30PW-M30.G.Y", "Changzhou Amass"),
    "LUG5": ("Connector_Generic:Conn_01x02", "mb:RingLug_M5_2P_P26", "M5 lug x2", "", "plated holes, M5 bolt + ring lug",
             "-"),
    "LUG4": ("Connector_Generic:Conn_01x02", "mb:RingLug_M4_2P_P13", "M4 lug x2", "", "plated holes, M4 bolt + ring lug",
             "-"),
    "FUSE25": ("Device:Fuse", "Fuse:Fuseholder_Blade_Mini_Keystone_3568", "MINI 58V 25A", "",
               "3568 holder + 0997025.WXN fuse", "Keystone / Littelfuse"),
    "RPRE": ("Device:R", "Resistor_THT:R_Axial_Power_L25.0mm_W9.0mm_P30.48mm", "10Ω 5W", "", "SQP500JB-10R", "Yageo"),
    "FET_THT": ("Transistor_FET:IRF540N", "Package_TO_SOT_THT:TO-220-3_Vertical", "IRL540N", "", "IRL540NPBF",
                "Infineon"),
    "URB": ("mb:URB_YMD", "mb:Mornsun_URB_YMD-30WR3_1x1in", "URB4812YMD-30WR3", "C22458769", "URB4812YMD-30WR3",
            "Mornsun"),
    "CP2200": ("Device:C_Polarized", "Capacitor_THT:CP_Radial_D10.0mm_P5.00mm", "2200µF 10V", "C49256788",
               "ERA10V2200M10X16", "Lelon"),
    "ESP32": ("mb:ESP32-DevKitC-V4", "mb:ESP32-DevKitC-V4_Sockets_OpenCenter", "ESP32-DevKitC-V4", "",
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
    "MKDS2": ("Connector_Generic:Conn_01x02", "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal",
              "12V PC", "", "1715721 (MKDS 1,5/2-5,08)", "Phoenix Contact"),
    # --- SMD (placed by PCBWay) ---
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
    "SH1m": ("Device:R_Shunt", "Resistor_SMD:R_Shunt_Vishay_WSK2512_6332Metric_T1.19mm", "1mΩ WSK2512", "C4248455",
             "WSK25121L000FEA", "Vishay"),
    "INA228": ("Sensor_Energy:INA228", "Package_SO:TSSOP-10_3x3mm_P0.5mm", "INA228", "C2887910", "INA228AIDGSR", "TI"),
    "TPS54360B": ("Regulator_Switching:TPS54360DDA", "Package_SO:TI_SO-PowerPAD-8_ThermalVias", "TPS54360BDDAR",
                  "C524806", "TPS54360BDDAR", "TI"),
    "L15": ("Device:L", "Inductor_SMD:L_TaiTech_TMPC1265_13.5x12.5mm", "15µH", "C189912", "SRP1265A-150M", "Bourns"),
    "L33": ("Device:L", "Inductor_SMD:L_TaiTech_TMPC1265_13.5x12.5mm", "33µH", "C2847586", "MDA1365-330M", "Cyntec"),
    "FUSE5": ("Device:Fuse", "Fuse:Fuse_Littelfuse-NANO2-451_453", "5A 125V", "C66503", "0452005.MRL", "Littelfuse"),
    "TCAN": ("mb:TCAN1042HV", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", "TCAN1042HVDR", "C127869", "TCAN1042HVDR", "TI"),
    "NUP2105": ("Power_Protection:NUP2105L", "Package_TO_SOT_SMD:SOT-23", "NUP2105L", "C14486", "NUP2105LT1G", "onsemi"),
    "ESD33": ("Diode:ESD5Zxx", "Diode_SMD:D_SOD-523", "ESD5Z3.3", "C397781", "ESD5Z3.3T1G", "onsemi"),
    "TPL5010": ("Timer:TPL5010", "Package_TO_SOT_SMD:SOT-23-6", "TPL5010", "C473912", "TPL5010DDCR", "TI"),
    "LVC1G74": ("mb:74LVC1G74", "Package_SO:SSOP-8_2.95x2.8mm_P0.65mm", "SN74LVC1G74DCT", "", "SN74LVC1G74DCTR", "TI"),
    "LVC1G08": ("74xGxx:74LVC1G08", "Package_TO_SOT_SMD:SOT-23-5", "SN74LVC1G08DBV", "C7666", "SN74LVC1G08DBVR", "TI"),
    "AHCT1G08": ("74xGxx:74AHCT1G08", "Package_TO_SOT_SMD:SOT-23-5", "SN74AHCT1G08DBV", "", "SN74AHCT1G08DBVR", "TI"),
    "LVC3G17": ("74xGxx:74LVC3G17", "Package_SO:SSOP-8_2.95x2.8mm_P0.65mm", "SN74LVC3G17DCT", "", "SN74LVC3G17DCTR",
                "TI"),
    "TLV9062": ("Amplifier_Operational:TLV9062xD", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", "TLV9062IDR", "C398355",
                "TLV9062IDR", "TI"),
    "TLV1701": ("mb:TLV1701", "Package_TO_SOT_SMD:SOT-23-5", "TLV1701", "C130035", "TLV1701AIDBVR", "TI"),
    "UCC27517": ("mb:UCC27517", "Package_TO_SOT_SMD:SOT-23-5", "UCC27517", "C99395", "UCC27517DBVR", "TI"),
    "TPS7A4001": ("mb:TPS7A4001", "mb:HVSSOP-8-1EP_3x3mm_P0.65mm_EP1.57x1.89mm_Pad0.42", "TPS7A4001", "C5144143",
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
BAT, BUSP, BUS = "BAT_P", "BUS_P", "BUS"

# Lug pairs on the top edge: x of pin 1 (pin 2 at +13 mm).
LUG_X = (52.0, 77.0, 102.0, 127.0)
CHOP_LUG_X = 152.0
# DevKitC sockets (rot 180): x of the J2 row (pins 1..19), J3 row at -25.40; pin 1 at y = MOD_Y.
MOD = {"S": 70.4, "AV": 115.4, "AR": 160.4}
MOD_Y = 147.0
# Motor blocks (x origin), y of the motor Hall connector and of the driver connectors.
MOTOR_BX = {"M1": 8.0, "M2": 51.0, "M3": 94.0, "M4": 137.0}
Y_JM, Y_JD = 79.0, 93.0
MOTORS = (("M1", "AV", "1", "AV_G"), ("M2", "AV", "2", "AV_D"), ("M3", "AR", "1", "AR_G"), ("M4", "AR", "2", "AR_D"))
# Parts packed with their group, then moved (keeps the rest of the group where it was routed):
# R29/R30 next to the chopper FET gate so that CH_G does not cross the crowded chopper group.
MOVED_AFTER_PACK = {"R29": (165.3, 41.2, 0), "R30": (168.8, 41.2, 0)}
REMOVED = ("R58",)     # no longer in circuit(): LATCH_QN is driven push-pull by U15 (decisions M23)
HOLES = [(3.5, 147.5), (176.5, 146.5), (3.5, 46.5), (176.5, 66.0)]


def circuit() -> Circuit:
    c = Circuit()
    R, C, A = c.R, c.C, c.add

    # =====================================================================
    #  1. Battery input (XT30), terminals to/from the external contactor, bus shunt
    # =====================================================================
    c.block("1. ENTRÉE BATTERIE (XT30) — bornes VERS / RETOUR CONTACTEUR externe — shunt du bus + INA228", 40, 38)
    # XT30PW-M: pad 2 is "+" and pad 1 is "-" on the KiCad footprint silkscreen (Amass drawing).
    A("J1", P["XT30"], {"1": G, "2": BAT}, (13.5, 24.0), 90, value="BATTERIE XT30")
    A("D1", P["TVS48CA"], {"1": BAT, "2": G}, (6.0, 37.2), 0)
    C("C1", "2.2u/100V", BAT, G, (14.5, 37.2), 0)
    C("C2", "2.2u/100V", BAT, G, (19.3, 37.2), 0)
    A("J2", P["LUG5"], {"1": BAT, "2": BUSP}, (12.0, 9.0), 0, value="VERS / RETOUR CONTACTEUR (M5)")
    # 1 mΩ 4-terminal shunt on the battery side of the bus: measures the XT30 current (minus hotel).
    A("RS1", P["SH1m"], {"1": BUSP, "2": "SNS_P", "3": "SNS_N", "4": BUS}, (38.0, 22.0), 0)
    A("U1", P["INA228"], {"1": G, "2": G, "3": None, "4": "I2C_SDA", "5": "I2C_SCL", "6": "3V3_S", "7": G,
                          "8": "INA_N", "9": "INA_N", "10": "INA_P"}, (26.17, 26.8), 0)
    # Sense filter resistors placed by hand next to the shunt; tracks drawn by ina_tracks().
    R("R1", "10", "SNS_P", "INA_P", (31.6, 24.3), 180)
    R("R2", "10", "SNS_N", "INA_N", (32.6, 26.6), 180)
    C("C3", "100n", "3V3_S", G, (24.525, 29.61), 0)
    # VBAT (upstream of the contactor) for the SAFETY ADC: 243k / 10k -> 42 V = 1.66 V, 60 V = 2.37 V.
    # Taken after the 5 A hotel fuse (HOTEL_F): same voltage, and reachable from the logic area.
    R("R48", "243k", "HOTEL_F", "VBAT_ADC", (77.0, 49.0), 90)
    R("R49", "10k", "VBAT_ADC", G, (77.0, 46.0), 90)
    C("C22", "100n", "VBAT_ADC", G, (77.0, 43.0), 90)

    # =====================================================================
    #  2. Precharge: P-FET driven by the SAFETY ESP32, resistor on board (THT)
    # =====================================================================
    c.block("2. PRÉCHARGE — FET P SUD50P10-43L, NPN MMBT5551, 10 Ω 5 W sur la carte, diode série SS510C", 40, 0)
    A("Q3", P["PFET"], {"1": "PRE_G", "2": "PRE_P", "3": BAT}, (30.0, 47.0), 0)
    R("R3", "10k", "PRE_G", BAT, (16.75, 41.0), 0)
    A("D2", P["Z12"], {"1": BAT, "2": "PRE_G"}, "pre")
    R("R4", "22k", "PRE_G", "PRE_C", "pre")
    A("Q4", P["NPN"], {"1": "PRE_B", "2": G, "3": "PRE_C"}, "pre")
    R("R5", "4.7k", "PRECH_EN", "PRE_B", "pre")
    R("R6", "100k", "PRE_B", G, "pre")
    A("R7", P["RPRE"], {"1": "PRE_P", "2": "PRE_N"}, (36.5, 47.0), 0)
    A("D3", P["SS510C"], {"1": BUS, "2": "PRE_N"}, (72.0, 42.0), 270)

    # =====================================================================
    #  3. Brake chopper — safety_power v2.1, unchanged values and references
    # =====================================================================
    c.block("3. HACHEUR DE FREINAGE (safety_power v2.1) — analogique, alimenté par le bus, ON 43,0 V / OFF 42,3 V", 40, 0)
    A("J12", P["LUG4"], {"1": BUS, "2": "CHOP_N"}, (CHOP_LUG_X, 7.0), 0, value="HACHEUR 22R 100W (M4)")
    A("Q5", P["FET_THT"], {"1": "CH_G", "2": "CHOP_N", "3": G}, (167.0, 19.0), 0)
    A("D8", P["SS510C"], {"1": BUS, "2": "CHOP_N"}, (156.0, 20.0), 0)
    R("R19", "10", BUS, "CH_VIN", (176.0, 41.6), 270)     # pin 1 sits on the BUS bar
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
    #  4. Driver outputs: MINI 58 V fuse + M4 lug pair (BUS+ / GND), x4
    # =====================================================================
    c.block("4. SORTIES VARIATEURS — fusible MINI 58 V 25 A (Keystone 3568) + bornes M4 BUS+ / GND, x4", 40, 0)
    for k, (m, node, i, name) in enumerate(MOTORS):
        cx = LUG_X[k]
        A("F%d" % (k + 1), P["FUSE25"], {"1": BUS, "2": "BR_" + m}, (cx - 1.7, 30.0), 90)
        A("J%d" % (3 + k), P["LUG4"], {"1": "BR_" + m, "2": G}, (cx, 7.0), 0, value="ZS-X11H %s (M4)" % name)

    # =====================================================================
    #  5. Hotel rails, upstream of the contactor
    # =====================================================================
    c.block("5. RAILS HÔTEL (amont contacteur) — fusible 5 A, anti-inversion, 5 V et 12 V AUX (TPS54360B), "
            "12 V PC isolé (URB4812YMD-30WR3), 5V_BRAKE", 40, 0)
    A("F5", P["FUSE5"], {"1": BAT, "2": "HOTEL_F"}, (10.0, 46.5), 270)
    A("Q6", P["PFET"], {"1": "REV_G", "2": "HOTEL_F", "3": "HOTEL_IN"}, "hot1")
    R("R35", "100k", "REV_G", G, "hot1")
    A("D12", P["Z12"], {"1": "HOTEL_IN", "2": "REV_G"}, "hot1")
    C("C15", "47u/100V", "HOTEL_IN", G, "hot1")
    C("C16", "2.2u/100V", "HOTEL_IN", G, "hot1")

    def buck(p, x, y, out, l_part, rfb_top, rc, cc, cout):
        """TPS54360B, 400 kHz (RT 243 k), UVLO 24 V on / 20 V off: safety_power decisions §5.1-5.2."""
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

    buck("B5", 12.0, 62.0, V5, "L15", "53.6k", "10.7k", "8.2n", "47u/10V")            # 5.00 V
    buck("B12", 51.0, 62.0, "12V_AUX", "L33", "143k", "10.5k", "15n", "22u/25V")      # 12.0 V
    A("D13", P["LED_G"], {"1": G, "2": "LED_5V"}, "hot1", value="5V")
    R("R36", "1k", V5, "LED_5V", "hot1")

    # 12 V for the PC (Youyeetoo X1), isolated. Ctrl open = on (no GPIO left for it).
    A("PS1", P["URB"], {"3": "HOTEL_IN", "1": None, "2": G, "4": "12V_PC", "5": None, "6": "GND_PC"}, (98.0, 50.0), 0,
      big=True)
    C("C19", "100u/25V", "12V_PC", "GND_PC", "pc")
    C("C20", "10u", "12V_PC", "GND_PC", "pc")
    A("J7", P["MKDS2"], {"1": "12V_PC", "2": "GND_PC"}, (127.0, 68.0), 0, value="12V PC (isolé)")
    A("D15", P["LED_G"], {"1": "GND_PC", "2": "LED_PC"}, "pc", value="12V PC")
    R("R41", "4.7k", "12V_PC", "LED_PC", "pc")

    # 12 V AUX: fan, and the contactor coil when the selector is on 12 V.
    A("J8", P["XH2"], {"1": "12V_AUX", "2": G}, "brk", value="FAN 12V")
    # Coil supply selector: jumper 1-2 = 12 V AUX, 2-3 = battery (after the 5 A fuse). No jumper = coil
    # unpowered: the contactor cannot close until the coil voltage is known.
    A("JP1", P["HDR3"], {"1": "12V_AUX", "2": "COIL_SUP", "3": "HOTEL_IN"}, "brk", value="BOBINE 12V|BAT")

    # 5V_BRAKE (D5): diode-fed 2200 µF reservoir, one 220 Ω per driver harness (short-circuit limit 23 mA).
    A("D14", P["SS34"], {"1": "BRK_RES", "2": V5}, "brk")
    A("C17", P["CP2200"], {"1": "BRK_RES", "2": G}, "brk")
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
             "20": G, "21": "IMU_MOSI", "22": "IMU_CS", "23": None, "24": None, "25": "SAFE_REARM", "26": None,
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
               "20": G, "21": n("STOP2"), "22": n("BRAKE_REL"), "23": None, "24": None, "25": None, "26": None,
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
        bx = MOTOR_BX[m]
        v5m, hall = "5V_MOT_" + m, ["H%s_%s" % (m, x) for x in "ABC"]
        pins = {"1": v5m, "2": G, "3": hall[0], "4": hall[1], "5": hall[2]}
        A("JM%d" % (k + 1), P["XH5"], dict(pins), (bx + 2.0, Y_JM), 0, value="HALL MOTEUR " + name)
        A("JD%d" % (k + 1), P["XH5"], dict(pins), (bx + 2.0, Y_JD), 0, value="HALL VARIATEUR " + name)
        A("JC%d" % (k + 1), P["XH6"], {"1": "VR_" + m, "2": "DIR_" + m, "3": "EL_" + m, "4": "STOP_" + m, "5": G,
                                       "6": "5V_BRAKE_" + m}, (bx + 20.0, Y_JD), 0, value="COMMANDE " + name)
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
    return c


# ---------------------------------------------------------------------------
#  Schematic
# ---------------------------------------------------------------------------
PWR_NETS = (G, BAT, BUS, V5, "HOTEL_IN", "3V3_S", "3V3_AV", "3V3_AR", "12V_AUX", "12V_PC", "GND_PC", "CH_12V",
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
    mblib.write_all(LIB_DIR)
    s = K.Schematic(PROJECT, "Retriever — mainboard (carte unique)", paper="A0", rev=REV, date=DATE,
                    company="Retriever, open hardware (CERN-OHL-S-2.0)",
                    comments=(DRAFT, "Batterie 42 V / 30 A, contacteur mécanique externe : relecture experte obligatoire",
                              "Généré par scripts/build.py — ne pas éditer à la main",
                              "Décisions et calculs : hardware/pcb/mainboard/decisions.md"),
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
            f.write('(%s_lib_table\n\t(version 7)\n\t(lib (name "mb") (type "KiCad") '
                    '(uri "${KIPRJMOD}/lib/mb.%s") (options "") (descr "mainboard, généré par mblib.py"))\n)\n'
                    % (kind, ext))
    return s


# ---------------------------------------------------------------------------
#  Board
# ---------------------------------------------------------------------------
HV_PWR = ["/BAT_P", "/BUS_P", "/BUS", "/BR_*", "/PRE_P", "/PRE_N", "/CHOP_N"]
HV_SIG = ["/SNS_*", "/INA_P", "/INA_N", "/PRE_G", "/PRE_C", "/REV_G", "/CH_VIN", "/CH_T", "/B5_*", "/B12_*",
          "/LED_BUS"]
NETCLASSES = [
    {"name": "Default", "track": 0.2, "clearance": 0.2, "via": 0.6, "drill": 0.3},
    # 42 V power copper (zones in practice): 0.5 mm, as safety_power (IPC-2221B B2 asks 0.6 mm uncoated).
    {"name": "HV_PWR", "track": 1.0, "clearance": 0.5, "via": 0.8, "drill": 0.4, "patterns": HV_PWR},
    # 42 V small signals: 0.2 mm (IPC-2221B B4, coated external, 31-50 V: 0.13 mm).
    {"name": "HV_SIG", "track": 0.25, "clearance": 0.2, "via": 0.6, "drill": 0.3, "patterns": HV_SIG},
    # Hotel feed (<= 2 A at 42 V) and the contactor coil (<= 1 A): 0.8 mm, 0.3 mm clearance.
    {"name": "HV_RAIL", "track": 0.8, "clearance": 0.3, "via": 0.8, "drill": 0.4,
     "patterns": ["/HOTEL_*", "/COIL_SUP", "/COIL_P", "/COIL_N"]},
    # Logic rails (<= 1.5 A): 0.6 mm on 2 oz ≈ 3 A at ΔT 20 °C (IPC-2152, external).
    {"name": "RAIL", "track": 0.6, "clearance": 0.2, "via": 0.8, "drill": 0.4,
     "patterns": ["/5V", "/5V_*", "/12V_*", "/BRK_RES", "/GND_PC"]},
    {"name": "RAIL_LO", "track": 0.3, "clearance": 0.2, "via": 0.6, "drill": 0.3,
     "patterns": ["/3V3_*", "/CH_12V", "/GND"]},
]
# PCBWay 2 layers, 2 oz: 6/6 mil (0.15 mm) minimum track/space; we keep 0.2 mm except inside fine-pitch pads.
RULES = dict(track=0.15, clearance=0.15, via=0.6, drill=0.3, annular=0.13, edge_clearance=0.4)

# Same limits in the project file (kicad-cli reads them from there).
PRO_RULES = {"min_clearance": 0.15, "min_copper_edge_clearance": 0.4, "min_track_width": 0.15,
             "min_via_diameter": 0.6, "min_via_annular_width": 0.13, "min_through_hole_diameter": 0.3,
             "min_hole_clearance": 0.25, "min_hole_to_hole": 0.5, "min_text_height": 0.8,
             "min_text_thickness": 0.12, "min_silk_clearance": 0.0}

# Packing groups: (x0, y0, x1, y1) on the board.
GROUPS = {
    "ina": (23.0, 25.0, 38.4, 39.5),
    "pre": (13.8, 42.0, 23.6, 53.0),
    "chop": (139.0, 42.0, 172.0, 60.0),
    "hot1": (79.0, 51.5, 93.5, 75.5),
    "pc": (122.5, 42.0, 138.5, 62.0),
    "brk": (139.0, 60.5, 172.0, 75.5),
    "safe": (47.6, 102.5, 67.8, 146.0),
    "left": (9.0, 131.0, 42.0, 142.5),
    "coil": (9.0, 103.0, 42.0, 120.0),
    "av": (92.6, 102.5, 112.8, 146.0),
    "ar": (137.6, 102.5, 157.8, 146.0),
    "av_cmd": (72.4, 99.0, 88.0, 146.0),
    "ar_cmd": (162.4, 99.0, 179.4, 142.5),
}
for _m, _bx in MOTOR_BX.items():
    GROUPS["tap_" + _m] = (_bx + 16.6, 75.8, _bx + 42.6, 89.6)


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
    """Row packing of every grouped part into its rectangle (courtyards 0.25 mm apart)."""
    import kicadpcb as KP
    groups = {}
    for p in c.parts:
        if "ref" in p and isinstance(p["pcb"], str):
            groups.setdefault(p["pcb"], []).append(p)
    for g, parts in groups.items():
        x0, y0, x1, y1 = GROUPS[g]
        # spread the parts where the router ran short of room on the first boards
        gap = 0.8 if g.startswith("tap_") else (0.45 if g in ("safe", "pre") else 0.25)
        cx, cy, rowh = x0, y0, 0.0
        # tallest first gives denser rows
        for p in sorted(parts, key=lambda q: -(footprint_box(b.fps[q["ref"]])[3] - footprint_box(b.fps[q["ref"]])[1])):
            fp = b.fps[p["ref"]]
            fp.SetPosition(KP.pt(0, 0))
            bx0, by0, bx1, by1 = footprint_box(fp)
            w, h = bx1 - bx0, by1 - by0
            if cx + w > x1 + 1e-6:
                cx, cy, rowh = x0, cy + rowh + gap, 0.0
            if cy + h > y1 + 1e-6:
                raise RuntimeError("group %s full at %s" % (g, p["ref"]))
            fp.SetPosition(KP.pt(cx - bx0, cy - by0))
            cx += w + gap
            rowh = max(rowh, h)
            for pad in fp.Pads():
                pass


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
        x, y = p["pcb"] if not isinstance(p["pcb"], str) else (0.0, 0.0)
        b.place(p["ref"], info, x, y, p["rot"])
    pack(b, c)
    import kicadpcb as KP
    for ref, (x, y, rot) in MOVED_AFTER_PACK.items():
        b.fps[ref].SetOrientationDegrees(rot)
        b.fps[ref].SetPosition(KP.pt(x, y))
    b.outline(0, 0, W, H, r=3.0)
    for i, (x, y) in enumerate(HOLES):
        b.hole("H%d" % (i + 1), x, y, name="MountingHole_3.2mm_M3", net=None)
        keepout(b, circle(x, y, 4.0), tracks=True)
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


class Copper:
    """Rectangles per (net, layer), united, one zone per outline."""

    def __init__(self, b):
        self.b = b
        self.parts = {}

    def add(self, net, layer, pts, prio=2, clr=0.5):
        self.parts.setdefault((net, layer, prio, clr), []).append(pts)

    def emit(self):
        import pcbnew as Pn
        for (net, layer, prio, clr), polys in self.parts.items():
            ps = polyset(polys[0])
            for p in polys[1:]:
                ps.BooleanAdd(polyset(p))
            for i in range(ps.OutlineCount()):
                z = Pn.ZONE(self.b.b)
                z.SetLayer(layer)
                z.SetNet(self.b.net(net))
                z.SetAssignedPriority(prio)
                z.SetLocalClearance(Pn.FromMM(clr))
                z.SetMinThickness(Pn.FromMM(0.3))
                z.SetPadConnection(Pn.ZONE_CONNECTION_FULL)
                z.SetIslandRemovalMode(Pn.ISLAND_REMOVAL_MODE_ALWAYS)
                z.SetZoneName("PWR_%s_%d" % (net, i))
                ol = ps.Outline(i)
                set_outline(z, [(ol.CPoint(j).x, ol.CPoint(j).y) for j in range(ol.PointCount())], raw=True)
                self.b.b.Add(z)


def power_copper(b):
    """30 A copper, drawn before routing (decisions.md §Cuivre). F.Cu carries BAT_P, BUS_P, BUS and the
    branches; B.Cu under the whole power strip is one GND plane (the 30 A return)."""
    import pcbnew as Pn
    F, B = Pn.F_Cu, Pn.B_Cu
    cu = Copper(b)
    # BAT_P: XT30 "+", input TVS/caps, contactor "out" lug. 21.5 mm wide.
    cu.add(BAT, F, rect(0.5, 0.5, 22.0, STRIP))
    # BUS_P: contactor "return" lug down to shunt pin 1 (from above: the sense pin 2 leaves below).
    cu.add(BUSP, F, rect(28.0, 0.5, 46.0, 17.0))
    cu.add(BUSP, F, rect(31.5, 17.0, 37.0, 21.6))
    # BUS bar: shunt pin 4 (from below: the sense pin 3 leaves above), fuses, chopper, precharge diode.
    cu.add(BUS, F, rect(39.4, 23.5, W - 0.5, 40.0))
    cu.add(BUS, F, rect(174.6, 40.0, 177.4, 41.2))            # tongue onto R19 pin 1
    cu.add(BUS, F, rect(CHOP_LUG_X - 5.0, 0.5, CHOP_LUG_X + 5.0, 23.5))
    # Branches: fuse pin 2 up to the lug.
    for k, (m, *_r) in enumerate(MOTORS):
        cx = LUG_X[k]
        cu.add("BR_" + m, F, rect(cx - 4.2, 0.5, cx + 4.2, 22.6))
    # Chopper resistor return: lug pin 2 to the FET drain and the freewheel diode.
    cu.add("CHOP_N", F, rect(CHOP_LUG_X + 6.6, 0.5, W - 0.5, 22.6))
    cu.emit()
    # GND plane, B.Cu, whole power strip; no tracks may cut it.
    b.zone(G, B, rect(0.5, 0.5, W - 0.5, STRIP), priority=1, clearance=0.5, name="GND_STRIP_B")
    keepout(b, rect(0.5, 0.5, W - 0.5, STRIP - 0.5), tracks=True, layers=(B,), fills=False, vias=False)
    # No routed track between the BUS_P tongue and the shunt: it would cut the 30 A copper.
    keepout(b, rect(28.0, 0.5, 37.6, 22.6), tracks=True, layers=(F, B), fills=False)


def power_vias(b):
    """GND vias next to the SMD ground pads of the power strip (TVS, caps, INA228 area), and stitching of
    the B.Cu plane under the lug GND pads is done by the lug footprints themselves (8 plated holes)."""
    n = 0
    for ref, num, dx, dy in (("D1", "2", 0, 2.6), ("C1", "2", 0, 2.2), ("C2", "2", 0, 2.2)):
        x, y = pad_xy(b, ref, num)
        via(b, G, x + dx, y + dy)
        b.track(G, [(x, y), (x + dx, y + dy)], 1.0)
        n += 1
    return n


def ina_tracks(b):
    """Sense filter and INA228 inputs, by hand (0.25 mm): SNS_P -> R1 -> INA_P -> IN+,
    SNS_N -> R2 -> INA_N -> IN- and VBUS (pins 9 and 8)."""
    import pcbnew as Pn
    F = Pn.F_Cu
    w = 0.25
    x2, y2 = pad_xy(b, "RS1", "2")
    r1a, r1b = pad_xy(b, "R1", "1"), pad_xy(b, "R1", "2")
    r2a, r2b = pad_xy(b, "R2", "1"), pad_xy(b, "R2", "2")
    u10, u9, u8 = pad_xy(b, "U1", "10"), pad_xy(b, "U1", "9"), pad_xy(b, "U1", "8")
    lt(b, "SNS_P", [(x2, y2), (r1a[0] + 1.2, r1a[1]), r1a], w, F)
    lt(b, "INA_P", [r1b, (29.6, r1b[1]), (29.6, u10[1]), u10], w, F)
    lt(b, "INA_N", [r2b, (30.0, r2b[1]), (29.7, u9[1]), u9], w, F)
    lt(b, "INA_N", [u8, (29.2, u8[1]), (29.7, u9[1])], w, F)
    lt(b, "SNS_N", [(38.25, 24.9), (36.55, r2a[1]), r2a], w, F)


def local_tracks(b):
    """Short connections of the hand-placed parts (R3, R19, VBAT divider) that the router cannot
    reach in the packed precharge group."""
    import pcbnew as Pn
    F, B = Pn.F_Cu, Pn.B_Cu
    r3a, r3b = pad_xy(b, "R3", "1"), pad_xy(b, "R3", "2")
    lt(b, BAT, [r3b, (r3b[0], STRIP - 0.4)], 0.4, F)                 # into the BAT_P polygon
    v1 = (r3a[0], r3a[1] + 1.05)
    lt(b, "PRE_G", [r3a, v1], 0.25, F)
    via(b, "PRE_G", v1[0], v1[1], 0.6, 0.3)
    lt(b, "PRE_G", [v1, (17.66, 45.39)], 0.25, B)
    via(b, "PRE_G", 17.66, 45.39, 0.6, 0.3)
    f5 = pad_xy(b, "F5", "1")
    lt(b, BAT, [f5, (11.6, f5[1] - 1.5), (11.6, STRIP - 0.4)], 0.8, F)
    r19 = pad_xy(b, "R19", "1")
    lt(b, BUS, [r19, (r19[0], 39.5)], 0.5, F)
    r48a, r48b = pad_xy(b, "R48", "1"), pad_xy(b, "R48", "2")
    r49a, c22a = pad_xy(b, "R49", "1"), pad_xy(b, "C22", "1")
    lt(b, "HOTEL_F", [r48a, (r48a[0] + 0.19, 51.406)], 0.5, F)
    lt(b, "VBAT_ADC", [r48b, r49a, (r49a[0] + 1.4, r49a[1]), (c22a[0] + 1.4, c22a[1]), c22a], 0.25, F)


def kelvin(b):
    """Sense traces of the shunt, drawn by the script so they leave each sense pad away from the current
    copper: pin 2 straight down, pin 3 up then left through the gap between BUS_P and the BUS bar."""
    import pcbnew as Pn
    x2, y2 = pad_xy(b, "RS1", "2")
    x3, y3 = pad_xy(b, "RS1", "3")
    lt(b, "SNS_N", [(x3, y3), (x3, 18.6), (38.25, 18.6), (38.25, 24.9)], 0.3, Pn.F_Cu)


def silkscreen(b):
    import pcbnew as Pn
    t = b.text

    def back(s, x, y, size=1.0):
        tx = t(s, x, y, size, layer=Pn.B_SilkS)
        tx.SetMirrored(True)

    # Banner on the bottom face, under the power strip (only the lug pads are there).
    back("RETRIEVER mainboard " + REV, 100.0, 14.3, 1.2)
    back("v1.0-draft - ne pas fabriquer avant P1, coil voltage, BMS level, and a review", 100.0, 16.4, 0.9)
    back("by an electronics engineer", 100.0, 18.0, 0.9)
    t("v1.0-draft - NE PAS FABRIQUER (voir decisions.md)", 100.0, 41.3, 0.8)
    t("BAT+", 5.0, 3.0, 1.2)
    t("XT30", 9.0, 33.0, 1.0)
    t("VERS CONTACTEUR", 12.0, 15.5, 0.9)
    t("RETOUR CONTACTEUR", 38.0, 15.5, 0.9)
    t("BUS+ (apres contacteur)", 110.0, 37.5, 1.0)
    for k, (m, node, j, name) in enumerate(MOTORS):
        t("%s  BUS+   GND" % name, LUG_X[k] + 6.5, 13.2, 0.8)
        t("MINI 58V 25A", LUG_X[k] - 6.3, 28.0, 0.8, rot=90)
        bx = MOTOR_BX[m]
        t("HALL MOT " + name, bx + 7.0, Y_JM + 4.9, 0.8)
        t("HALL VAR " + name, bx + 7.0, Y_JD - 3.6, 0.8)
        t("VR DIR EL STOP GND 5VB", bx + 25.2, Y_JD + 4.8, 0.8)
    t("HACHEUR 22R", CHOP_LUG_X + 6.5, 13.2, 0.8)
    t("PRECHARGE 10R 5W", 52.0, 52.6, 0.8)
    t("12V PC ISOLE", 130.0, 74.5, 0.8)
    jp = b.b.FindFootprintByReference("JP1")
    if jp is not None and hasattr(jp, "GetPosition"):
        x, y = Pn.ToMM(jp.GetPosition().x), Pn.ToMM(jp.GetPosition().y)
        tx = t("1-2:12V 2-3:BAT", x - 2.3, y + 2.54, 0.8, layer=Pn.B_SilkS, rot=90)
        tx.SetMirrored(True)
    for node, x in MOD.items():
        lab = {"S": "SAFETY", "AV": "MOTION AVANT", "AR": "MOTION ARRIERE"}[node]
        t("ESP32 " + lab + "  (USB ici)", x - 12.7, 99.1, 0.8)
        t("ANTENNE", x - 12.7, MOD_Y + 1.8, 0.8)
    t("IMU", 3.5, 77.2, 0.8)
    for lab, y in (("ARU /SAFE", 109.75), ("ARU BOBINE", 118.75), ("BOBINE", 127.75), ("CAN PC", 138.0)):
        tx = t(lab, 6.3, y, 0.8, layer=Pn.B_SilkS, rot=90)
        tx.SetMirrored(True)
    t("BMS", 14.0, 141.6, 0.8)


def main():
    what = sys.argv[1] if len(sys.argv) > 1 else "sch"
    os.makedirs(KICAD_DIR, exist_ok=True)
    pcb_path = os.path.join(KICAD_DIR, PROJECT + ".kicad_pcb")
    if what in ("drop", "patch"):
        import kicadpcb as KP
        import pcbnew as Pn
        import patchroute_mb as patchroute
        b = KP.Board(pcb_path, load=True, extra_fp_dirs=(LIB_DIR,))
        rpt = os.path.join(BOARD_DIR, "build", "drc.rpt")
        if what == "drop":
            print("dropped:", drop_violations(b, rpt))
        else:
            print("patched:", patchroute.finish(b.b, rpt, net_clearance, W, H, ignore_nets=("/" + G,)))
        b.save()
        return
    if what == "fix":
        # Repair tool for the 23/11 routing (40 Freerouting passes, build/routed_backup.kicad_pcb), kept
        # because it routed better than later runs: applies the placement corrections of circuit()
        # to the routed board. Run fix2 next, in a new process (pcbnew's SWIG proxies go stale after
        # removing items in the same process).
        import kicadpcb as KP
        import pcbnew as Pn
        b = KP.Board(pcb_path, load=True, extra_fp_dirs=(LIB_DIR,))
        load_nets(b)
        c = circuit()
        refs = {p["ref"]: p for p in c.parts if "ref" in p}
        for ref in ("U1", "R48"):
            for pad in b.b.FindFootprintByReference(ref).Pads():
                net = refs[ref]["nets"].get(pad.GetNumber())
                if net:
                    pad.SetNet(b.net(net))
        for ref in ("R1", "R2", "R3", "R19", "R48", "R49", "C22"):
            fp = b.b.FindFootprintByReference(ref)
            fp.SetOrientationDegrees(refs[ref]["rot"])
            fp.SetPosition(KP.pt(*refs[ref]["pcb"]))
        n = 0
        for t in list(b.b.GetTracks()):
            net = t.GetNetname()[1:]
            ys = [Pn.ToMM(t.GetStart().y), Pn.ToMM(t.GetEnd().y)]
            if net in ("SNS_P", "SNS_N", "INA_P", "INA_N", "VBAT_ADC") or \
                    (t.GetLayer() == Pn.B_Cu and t.GetClass() == "PCB_TRACK" and min(ys) < STRIP - 0.5):
                b.b.Remove(t)
                n += 1
        print("removed", n, "tracks")
        b.save()
        print("ok: fix")
        return
    if what == "fix2":
        import kicadpcb as KP
        b = KP.Board(pcb_path, load=True, extra_fp_dirs=(LIB_DIR,))
        load_nets(b)
        import pcbnew as Pn
        stub = any(t.GetNetname() == "/" + BUS and t.GetLayer() == Pn.B_Cu and
                   any(abs(Pn.ToMM(q.x) - 132.6) < 0.05 and abs(Pn.ToMM(q.y) - 41.2) < 0.05
                       for q in (t.GetStart(), t.GetEnd())) for t in b.b.GetTracks())
        cu = Copper(b)
        cu.add(BUS, Pn.F_Cu, rect(171.9, 23.5, W - 0.5, 40.0), prio=3)
        cu.add(BUS, Pn.F_Cu, rect(174.6, 40.0, 177.4, 41.2), prio=3)
        cu.emit()
        keepout(b, rect(28.0, 0.5, 37.6, 22.6), tracks=True, layers=(Pn.F_Cu, Pn.B_Cu), fills=False)
        if stub:
            via(b, BUS, 132.6, 41.2)
            lt(b, BUS, [(132.6, 41.2), (132.6, 39.4)], 0.5, Pn.F_Cu)
        kelvin(b)
        ina_tracks(b)
        local_tracks(b)
        for ref in REMOVED:                           # parts dropped from circuit() since that routing
            fp = b.b.FindFootprintByReference(ref)
            if fp is not None and hasattr(fp, "GetReference"):
                b.b.Remove(fp)
        b.save()
        print("ok: fix2")
        return
    if what == "reroute":
        # Freerouting on the routed board, GND pours kept (they count as planes): only the open
        # connections are routed. Save straight after the import (SWIG proxies go stale after it).
        import kicadpcb as KP
        b = KP.Board(pcb_path, load=True, extra_fp_dirs=(LIB_DIR,))
        work = os.path.join(BOARD_DIR, "build")
        print(autoroute(b, work, passes=int(os.environ.get("PASSES", "4")), threads=0))
        b.save()
        print("ok: reroute")
        return
    if what == "tidy":
        import kicadpcb as KP
        b = KP.Board(pcb_path, load=True, extra_fp_dirs=(LIB_DIR,))
        print("removed from B.Cu under the power strip:", strip_bottom_tracks(b))
        b.save()
        return
    if what == "move":
        import kicadpcb as KP
        b = KP.Board(pcb_path, load=True, extra_fp_dirs=(LIB_DIR,))
        for ref, (x, y, rot) in MOVED_AFTER_PACK.items():
            fp = b.b.FindFootprintByReference(ref)
            fp.SetOrientationDegrees(rot)
            fp.SetPosition(KP.pt(x, y))
        b.save()
        print("ok: move")
        return
    if what == "silk":
        import kicadpcb as KP
        import pcbnew as Pn
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
        print("removed from B.Cu under the power strip:", strip_bottom_tracks(b))
        gnd_pours(b)
        b.save()
        print("ok: route")
        return
    c = circuit()
    s = build_sch(c)
    uuids = {ref: info["uuid"] for ref, info in s.symbols.items()}
    nc = {ref: info["nc"] for ref, info in s.symbols.items()}
    K.write_project(os.path.join(KICAD_DIR, PROJECT + ".kicad_pro"), NETCLASSES, PRO_RULES)
    if what == "pcb":
        b = build_pcb(c, uuids, nc)
        power_copper(b)
        print("power vias:", power_vias(b))
        kelvin(b)
        ina_tracks(b)
        local_tracks(b)
        silkscreen(b)
        b.save()
    print("ok:", what, len([p for p in c.parts if "ref" in p]), "parts")


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
    open(dsn, "w").write(txt)
    cmd = [KP.JAVA, "-jar", KP.FREEROUTING, "-de", dsn, "-do", ses, "-mp", str(passes), "-mt", str(threads),
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
                                         "hole_to_hole", "holes_co_located", "track_dangling", "hole_clearance"):
            continue
        for x, y, kind, net in re.findall(r"@\(([-\d.]+) mm, ([-\d.]+) mm\): (Piste|Via|Track) \[([^\]]+)\]", blk):
            bad.append((float(x), float(y), kind, net))
    n = 0
    for t in list(b.b.GetTracks()):
        if t.IsLocked():
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


def strip_bottom_tracks(b):
    """Freerouting does not honour the single-layer keepout: remove any non-GND track it put on
    B.Cu inside the power strip (the GND plane there carries the 30 A return)."""
    import pcbnew as Pn
    n = 0
    for t in list(b.b.GetTracks()):
        if t.GetClass() == "PCB_TRACK" and t.GetLayer() == Pn.B_Cu and \
                min(Pn.ToMM(t.GetStart().y), Pn.ToMM(t.GetEnd().y)) < STRIP - 0.5:
            b.b.Remove(t)
            n += 1
    return n


def stitch(b, pitch=float(os.environ.get("STITCH", "4.0"))):
    """GND vias wherever both GND pours are present with room to spare, so that no copper island of
    either face is left floating. Run on a filled board; refill afterwards."""
    import pcbnew as Pn
    b.fill()
    zf = [z for z in b.b.Zones() if z.GetZoneName() == "GND_F"]
    zb = [z for z in b.b.Zones() if z.GetZoneName() in ("GND_B", "GND_STRIP_B")]

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
            if not (27.5 <= x <= 38.1 and y <= 23.1) and \
                    inside(zf, Pn.F_Cu, x, y, 0.65) and inside(zb, Pn.B_Cu, x, y, 0.65) and \
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


def gnd_pours(b):
    """GND on both layers over the whole board, added after routing (lowest priority); the isolated
    12 V PC output gets its own island on B.Cu around its terminal and capacitors."""
    import pcbnew as Pn
    for layer, name in ((Pn.F_Cu, "GND_F"), (Pn.B_Cu, "GND_B")):
        b.zone(G, layer, rect(0.4, 0.4, W - 0.4, H - 0.4), priority=0, clearance=0.25, name=name)


if __name__ == "__main__":
    main()
