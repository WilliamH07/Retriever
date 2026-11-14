#!/usr/bin/env python3
"""safety_power v2.0-draft — the whole board, schematic and layout, in one file.

    python3 build.py sch            # libraries + schematic + project (any Python 3)
    <KiCad python> build.py pcb     # board: placement, power copper, planes
    <KiCad python> build.py route   # autoroute signals, then logic pours

The circuit is described once, in `circuit()`. `sch` and `pcb` both read it,
so the board can only contain what the schematic contains.

Design decisions and every computed value: ../decisions.md.
DRAFT — do not manufacture before M1, M2, M10, M12, PACK_ID, P1-P3 and a review
by an electronics engineer.
"""

from __future__ import annotations

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD_DIR = os.path.dirname(HERE)
KICAD_DIR = os.path.join(BOARD_DIR, "kicad")
LIB_DIR = os.path.join(KICAD_DIR, "lib")
sys.path.insert(0, os.path.join(BOARD_DIR, "..", "scripts"))
sys.path.insert(0, HERE)

import kicadgen as K  # noqa: E402
import splib  # noqa: E402

PROJECT = "safety_power"
REV = "2.0-draft"
DATE = "2026-11-13"
DRAFT = "v2.0-draft — NE PAS FABRIQUER avant M1, M2, M10, M12, PACK_ID, P1-P3 et relecture par un électronicien"

W, H = 210.0, 160.0
Y_SPLIT = 66.0          # power zone above, logic zone below

# ---------------------------------------------------------------------------
#  Parts: (lib_id, footprint, value, LCSC, MPN). LCSC "" = hand-soldered / user supplied.
# ---------------------------------------------------------------------------
P = {
    "TPS48100": ("sp:TPS48100-Q1", "sp:TI_DGX0019A_VSSOP-19", "TPS48100QDGXRQ1", "C43131316", "TI TPS48100QDGXRQ1"),
    "FET": ("sp:NMOS_D2PAK7", "sp:TO-263-7_TabPin4_NoPin4", "IPB017N10N5LF", "C3289286", "Infineon IPB017N10N5LFATMA1"),
    "PFET": ("Transistor_FET:SUD50P10-43L", "Package_TO_SOT_SMD:TO-252-2", "SUD50P10-43L", "C41408040", "SUD50P10-43L-TP"),
    # Vishay WSK2512: true 4-terminal shunt (1, 4 current; 2, 3 Kelvin sense), 1 W.
    "SH1m": ("Device:R_Shunt", "Resistor_SMD:R_Shunt_Vishay_WSK2512_6332Metric_T1.19mm", "1mΩ WSK2512", "C4248455",
             "Vishay WSK25121L000FEA"),
    "SH2m": ("Device:R_Shunt", "Resistor_SMD:R_Shunt_Vishay_WSK2512_6332Metric_T1.19mm", "2mΩ WSK2512", "C3997408",
             "Vishay WSK25122L000FEA"),
    "TVS48CA": ("Device:D_TVS", "Diode_SMD:D_SMC", "SMCJ48CA", "C151287", "SMCJ48CA bidirectional"),
    "SS510C": ("Device:D_Schottky", "Diode_SMD:D_SMC", "SS510C", "C19229", "SS510C 100 V 5 A"),
    "B560C": ("Device:D_Schottky", "Diode_SMD:D_SMC", "B560C", "C85100", "Diodes B560C-13-F"),
    "SS34": ("Device:D_Schottky", "Diode_SMD:D_SMA", "SS34", "C8678", "SS34"),
    "B5819W": ("Device:D_Schottky", "Diode_SMD:D_SOD-123", "B5819W", "C8598", "B5819W"),
    "Z12": ("Device:D_Zener", "Diode_SMD:D_SOD-123", "BZT52C12", "C43491", "BZT52C12"),
    "Z15": ("Device:D_Zener", "Diode_SMD:D_SOD-123", "BZT52C15", "C173427", "BZT52C15"),
    "NPN": ("Transistor_BJT:MMBT5551L", "Package_TO_SOT_SMD:SOT-23", "MMBT5551", "C2145", "MMBT5551"),
    "NFET": ("Transistor_FET:DMG1012T", "Package_TO_SOT_SMD:SOT-523", "DMG1012T", "C20512", "Diodes DMG1012T-7"),
    "TPS54360B": ("Regulator_Switching:TPS54360DDA", "Package_SO:TI_SO-PowerPAD-8_ThermalVias", "TPS54360BDDAR",
                  "C524806", "TI TPS54360BDDAR"),
    "L15": ("Device:L", "Inductor_SMD:L_TaiTech_TMPC1265_13.5x12.5mm", "15µH", "C189912", "Bourns SRP1265A-150M"),
    "L33": ("Device:L", "Inductor_SMD:L_TaiTech_TMPC1265_13.5x12.5mm", "33µH", "C2847586", "MDA1365-330M"),
    "URB": ("sp:URB_YMD", "sp:Mornsun_URB_YMD-30WR3_1x1in", "URB4812YMD-30WR3", "C22458769", "Mornsun URB4812YMD-30WR3"),
    "AP2112": ("Regulator_Linear:AP2112K-3.3", "Package_TO_SOT_SMD:SOT-23-5", "AP2112K-3.3", "C51118", "AP2112K-3.3TRG1"),
    "EF5": ("sp:TPS2595x", "Package_SON:Texas_DSG0008A_WSON-8-1EP_2x2mm_P0.5mm_EP0.9x1.6mm", "TPS259531",
            "C2155674", "TI TPS259531DSGR"),
    "EF12": ("sp:TPS2595x", "Package_SON:Texas_DSG0008A_WSON-8-1EP_2x2mm_P0.5mm_EP0.9x1.6mm", "TPS259573",
             "C2653844", "TI TPS259573DSGR"),
    "TCAN": ("sp:TCAN1042HV", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", "TCAN1042HVDRQ1", "C485807", "TI TCAN1042HVDRQ1"),
    "NUP2105": ("Power_Protection:NUP2105L", "Package_TO_SOT_SMD:SOT-23", "NUP2105L", "C14486", "onsemi NUP2105LT1G"),
    "ESD33": ("Diode:ESD5Zxx", "Diode_SMD:D_SOD-523", "ESD5Z3.3", "C397781", "ESD5Z3.3"),
    "INA228": ("Sensor_Energy:INA228", "Package_SO:TSSOP-10_3x3mm_P0.5mm", "INA228", "C2887910", "TI INA228AIDGSR"),
    "ADS1115": ("Analog_ADC:ADS1115IDGS", "Package_SO:TSSOP-10_3x3mm_P0.5mm", "ADS1115", "C37593", "TI ADS1115IDGSR"),
    "TCA9555": ("Interface_Expansion:TCA9555PWR", "Package_SO:TSSOP-24_4.4x7.8mm_P0.65mm", "TCA9555", "C465732",
                "TI TCA9555PWR"),
    "TPL5010": ("Timer:TPL5010", "Package_TO_SOT_SMD:SOT-23-6", "TPL5010", "C473912", "TI TPL5010DDCR"),
    "LVC1G74": ("sp:74LVC1G74", "Package_SO:VSSOP-8_2.3x2mm_P0.5mm", "SN74LVC1G74", "C70285", "TI SN74LVC1G74DCUR"),
    "LVC1G08": ("74xGxx:74LVC1G08", "Package_TO_SOT_SMD:SOT-353_SC-70-5", "74LVC1G08", "C12512", "Nexperia 74LVC1G08GW"),
    "AHCT125": ("74xGxx:74AHCT1G125", "Package_TO_SOT_SMD:SOT-23-5", "74AHCT1G125", "C7484", "TI SN74AHCT1G125DBVR"),
    "LM2903": ("sp:LM2903", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", "LM2903", "C7549", "TI LM2903DR"),
    "TLV1701": ("sp:TLV1701", "Package_TO_SOT_SMD:SOT-23-5", "TLV1701", "C130035", "TI TLV1701AIDBVR"),
    "UCC27517": ("sp:UCC27517", "Package_TO_SOT_SMD:SOT-23-5", "UCC27517", "C99395", "TI UCC27517DBVR"),
    "TPS7A4001": ("sp:TPS7A4001", "Package_SO:HVSSOP-8-1EP_3x3mm_P0.65mm_EP1.57x1.89mm", "TPS7A4001", "C5144143",
                  "TI TPS7A4001DGNT"),
    "LM4040": ("Reference_Voltage:LM4040DBZ-2.5", "Package_TO_SOT_SMD:SOT-23", "LM4040A25", "C9421", "TI LM4040A25IDBZR"),
    "ADUM1201": ("Isolator:ADuM1201AR", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", "ADuM1201", "C9669", "ADI ADUM1201ARZ-RL7"),
    "B0503S": ("sp:B0503S", "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical", "B0503S-1WR3", "C5369462",
               "Mornsun B0503S-1WR3"),
    "BAT54S": ("Diode:BAT54S", "Package_TO_SOT_SMD:SOT-23", "BAT54S", "C19726", "onsemi BAT54SLT1G"),
    "ESP32": ("sp:ESP32-DevKitC-V4", "sp:ESP32-DevKitC-V4_Sockets", "ESP32-DevKitC-V4", "", "Espressif ESP32-DevKitC-V4 + 2x Mill-Max 310-43-119"),
    "LUG5": ("Connector_Generic:Conn_01x02", "sp:RingLug_M5_2P_P26", "M5 lug x2", "", "plated holes, ring lugs M5"),
    "LUG4": ("Connector_Generic:Conn_01x02", "sp:RingLug_M4_2P_P13", "M4 lug x2", "", "plated holes, ring lugs M4"),
    "FUSE25": ("Device:Fuse", "Fuse:Fuseholder_Blade_Mini_Keystone_3568", "MINI 58V 25A", "",
               "Keystone 3568-20 holder + Littelfuse 0997025.WXN (MINI 58V)"),
    "FUSE5": ("Device:Fuse", "Fuse:Fuse_Littelfuse-NANO2-451_453", "5A 125V slo", "C66503", "Littelfuse 0452005.MRL"),
    "STAR": ("Device:NetTie_2", "sp:NetTie_GND_STAR_4mm", "★ GND STAR", "", ""),
    "MF2": ("Connector_Generic:Conn_01x02", "Connector_Molex:Molex_Micro-Fit_3.0_43650-0215_1x02_P3.00mm_Vertical",
            "Micro-Fit 2p", "C293740", "Molex 43650-0215"),
    "MF3": ("Connector_Generic:Conn_01x03", "Connector_Molex:Molex_Micro-Fit_3.0_43650-0315_1x03_P3.00mm_Vertical",
            "Micro-Fit 3p", "C293546", "Molex 43650-0315"),
    "MF4": ("Connector_Generic:Conn_01x04", "Connector_Molex:Molex_Micro-Fit_3.0_43650-0415_1x04_P3.00mm_Vertical",
            "Micro-Fit 4p", "C293547", "Molex 43650-0415"),
    "MF6": ("Connector_Generic:Conn_01x06", "Connector_Molex:Molex_Micro-Fit_3.0_43650-0615_1x06_P3.00mm_Vertical",
            "Micro-Fit 6p", "C505231", "Molex 43650-0615"),
    "XH2": ("Connector_Generic:Conn_01x02", "Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical", "XH 2p",
            "C265283", "JST B2B-XH-A"),
    "GH4": ("Connector_Generic:Conn_01x04", "Connector_JST:JST_GH_SM04B-GHS-TB_1x04-1MP_P1.25mm_Horizontal",
            "GH 4p", "C189895", "JST SM04B-GHS-TB"),
    "GH8": ("Connector_Generic:Conn_01x08", "Connector_JST:JST_GH_SM08B-GHS-TB_1x08-1MP_P1.25mm_Horizontal",
            "GH 8p", "C265111", "JST SM08B-GHS-TB"),
    "FAN": ("Connector_Generic:Conn_01x04", "Connector:FanPinHeader_1x04_P2.54mm_Vertical", "FAN 4p", "C240840",
            "Molex 47053-1000"),
    "HDR2": ("Connector_Generic:Conn_01x02", "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
             "RADIO E-STOP", "C492401", "2.54 mm 1x2 header + jumper"),
    "LED_G": ("Device:LED", "LED_SMD:LED_0603_1608Metric", "green", "C72043", "Everlight 19-217/GHC"),
    "LED_R": ("Device:LED", "LED_SMD:LED_0603_1608Metric", "red", "C2286", "KT-0603R"),
    "TP": ("Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", "TP", "", ""),
    "TPP": ("Connector:TestPoint", "TestPoint:TestPoint_Pad_D2.0mm", "TP", "", ""),
}

R0603 = "Resistor_SMD:R_0603_1608Metric"
R1206 = "Resistor_SMD:R_1206_3216Metric"
RES = {  # value -> (LCSC, MPN), all 0603 1 % 75 V unless noted
    "0R": ("C21189", "0603WAF0000T5E"), "10": ("C22859", "0603WAF100JT5E"), "33": ("C23140", "0603WAF330JT5E"),
    "100": ("C22775", "0603WAF1000T5E"), "150": ("C22808", "0603WAF1500T5E"), "221": ("C23342", "0603WAF2210T5E"),
    "330": ("C23138", "0603WAF3300T5E"), "470": ("C23179", "0603WAF4700T5E"), "1k": ("C21190", "0603WAF1001T5E"),
    "1.05k": ("C858882", "RC0603DR-071K05L"), "1.4k": ("C25957", "0603WAF1401T5E"), "2.2k": ("C4190", "0603WAF2201T5E"),
    "4.42k": ("C23043", "0603WAF4421T5E"), "4.7k": ("C23162", "0603WAF4701T5E"), "5.23k": ("C23068", "0603WAF5231T5E"),
    "6.04k": ("C25977", "0603WAF6041T5E"), "10k": ("C25804", "0603WAF1002T5E"), "10.2k": ("C22772", "0603WAF1022T5E"),
    "10.5k": ("C22855", "0603WAF1052T5E"), "10.7k": ("C22857", "0603WAF1072T5E"), "18.7k": ("C22893", "0603WAF1872T5E"),
    "20k": ("C4184", "0603WAF2002T5E"), "22k": ("C31850", "0603WAF2202T5E"), "24.3k": ("C23348", "0603WAF2432T5E"),
    "33k": ("C4216", "0603WAF3302T5E"), "40.2k": ("C12447", "0603WAF4022T5E"), "47k": ("C25819", "0603WAF4702T5E"),
    "49.9k": ("C23184", "0603WAF4992T5E"), "51k": ("C23196", "0603WAF5102T5E"), "53.6k": ("C23074", "0603WAF5362T5E"),
    "57.6k": ("C23082", "0603WAF5762T5E"), "59k": ("C23085", "0603WAF5902T5E"), "93.1k": ("C228101", "AC0603FR-0793K1L"),
    "100k": ("C25803", "0603WAF1003T5E"), "124k": ("C22788", "0603WAF1243T5E"), "143k": ("C304703", "RS-03K1433FT"),
    "150k": ("C22807", "0603WAF1503T5E"), "243k": ("C23351", "0603WAF2433T5E"), "1M": ("C22935", "0603WAF1004T5E"),
    "1.18M": ("C4072929", "AA0603FR-071M18L"), "1.69M": ("C247054", "0603WAF1694T5E"),
    "22k-1206": ("C114942", "RC1206FR-0722KL"),
}
C0603, C0805, C1210 = "Capacitor_SMD:C_0603_1608Metric", "Capacitor_SMD:C_0805_2012Metric", "Capacitor_SMD:C_1210_3225Metric"
CAP = {  # value -> (symbol, footprint, LCSC, MPN, label)
    "82p": ("Device:C", C0603, "C107056", "CC0603JRNPO9BN820", "82pF C0G"),
    "1n": ("Device:C", C0603, "C1588", "CL10B102KB8NNNC", "1nF"),
    "6.8n": ("Device:C", C0603, "C1631", "0603B682K500NT", "6.8nF"),
    "8.2n": ("Device:C", C0603, "C1322360", "0603B822K500NT", "8.2nF"),
    "10n": ("Device:C", C0603, "C57112", "0603B103K500NT", "10nF"),
    "15n": ("Device:C", C0603, "C107076", "CC0603KRX7R9BB153", "15nF"),
    "100n": ("Device:C", C0603, "C14663", "CC0603KRX7R9BB104", "100nF"),
    "100n/100V": ("Device:C", C0603, "C88219", "0603B104K101NT", "100nF 100V"),
    "1u": ("Device:C", C0603, "C5673", "CL10A105KA8NNNC", "1µF 25V"),
    "1u/100V": ("Device:C", C0805, "C385977", "HMK212BC7105KGHTE", "1µF 100V"),
    "4.7u": ("Device:C", C0805, "C1779", "CL21A475KAQNNNE", "4.7µF 25V"),
    "10u": ("Device:C", C0805, "C15850", "CL21A106KAYNNNE", "10µF 25V"),
    "2.2u/100V": ("Device:C", C1210, "C153036", "FS32X225K101EGG", "2.2µF 100V"),
    "22u/25V": ("Device:C", C1210, "C52306", "CL32A226KAJNNNE", "22µF 25V"),
    "47u/10V": ("Device:C", C1210, "C84494", "GRM32ER71A476KE15L", "47µF 10V"),
    "47u/100V": ("Device:C_Polarized", "Capacitor_SMD:CP_Elec_8x10", "C48935391", "RV100V47M8X10", "47µF 100V"),
    "100u/25V": ("Device:C_Polarized", "Capacitor_SMD:CP_Elec_6.3x7.7", "C2836443", "RVT100UF25V67RV0011", "100µF 25V"),
    "2200u/10V": ("Device:C_Polarized", "Capacitor_THT:CP_Radial_D10.0mm_P5.00mm", "C49256788", "ERA10V2200M10X16",
                  "2200µF 10V"),
}


class Circuit:
    """Collects parts with both schematic and board placement."""

    def __init__(self):
        self.parts = []
        self.sx, self.sy, self.sx0, self.rowh = 0.0, 0.0, 0.0, 0.0

    def block(self, title, x, y, cols=44):
        # Blocks flow down the sheet: each starts below the previous one.
        y = max(y, self.sy + self.rowh + (14 if self.parts else 0))
        self.sx0, self.sx, self.sy, self.rowh, self.xmax = x, x, y, 0.0, x + cols * 25
        self.parts.append(dict(text=title, at=(x - 10, y - 14)))

    def _sch(self, w, h):
        """Row-major packing: a part w wide and h tall; rows are as tall as their tallest part."""
        if self.sx + w > self.xmax:
            self.sx, self.sy, self.rowh = self.sx0, self.sy + self.rowh, 0.0
        p = (self.sx + (w - 25) / 2, self.sy + h / 2)
        self.sx += w
        self.rowh = max(self.rowh, h)
        return p

    def add(self, ref, part, nets, pcb, rot=0, dnp=False, value=None, back=False, in_bom=True, big=False, sch_rot=0):
        lib_id, fp, val, lcsc, mpn = part
        npins = max(len(nets), 2)
        h = max(24.0, 2.54 * (npins / 2 + 3)) if (big or npins > 4) else 24.0
        w = 60 if big else (40 if npins > 4 else 25)
        sch = self._sch(w, h)
        self.parts.append(dict(ref=ref, lib_id=lib_id, footprint=fp, value=value or val, lcsc=lcsc, mpn=mpn,
                               nets=nets, sch=sch, sch_rot=sch_rot, pcb=pcb, rot=rot, dnp=dnp, back=back,
                               in_bom=in_bom and not ref.startswith("TP")))

    def R(self, ref, value, a, b, pcb, rot=0, dnp=False):
        lcsc, mpn = RES[value]
        fp = R1206 if value.endswith("-1206") else R0603
        v = value.replace("-1206", "")
        self.add(ref, ("Device:R", fp, v + ("Ω" if v[-1].isdigit() else ""), lcsc, mpn), {"1": a, "2": b},
                 pcb, rot, dnp, sch_rot=90)

    def C(self, ref, value, a, b, pcb, rot=0, dnp=False):
        sym, fp, lcsc, mpn, label = CAP[value]
        self.add(ref, (sym, fp, label, lcsc, mpn), {"1": a, "2": b}, pcb, rot, dnp, sch_rot=90)


G = "GND_LOGIC"
N = "BUS_N"
V3 = "3V3_HOTEL"
V5 = "5V_HOTEL"
XR = 10.0  # everything right of the branches is shifted by the 210 mm board width


def circuit() -> Circuit:
    c = Circuit()
    R, C, A = c.R, c.C, c.add

    # =====================================================================
    #  1. Battery input, static contactor (TPS48100-Q1 + 2 x IPB017N10N5LF)
    # =====================================================================
    c.block("1. ENTRÉE BATTERIE ET CONTACTEUR STATIQUE — TPS48100-Q1, 2 x IPB017N10N5LF tête-bêche", 40, 38)
    A("J1", P["LUG5"], {"1": "BAT_P", "2": N}, (9, 18), 270, value="BAT_IN (M5)")
    A("D1", P["TVS48CA"], {"1": N, "2": "BAT_P"}, (4.0, 33.0), 90)
    C("C1", "2.2u/100V", "BAT_P", N, (9.8, 33.0), 270)
    C("C2", "2.2u/100V", "BAT_P", N, (13.0, 33.0), 270)
    # 1 mΩ 4-terminal shunt shared by the TPS48100 short-circuit comparator and the bus INA228.
    A("RS1", P["SH1m"], {"1": "BAT_P", "2": "SNS_BAT_P", "3": "SNS_BAT_N", "4": "BAT_SH"}, (19.5, 25.5), 0)
    A("Q1", P["FET"], {"1": "Q1_G", "4": "BAT_SH", "2": "MID", "3": "MID", "5": "MID", "6": "MID", "7": "MID"},
      (35, 31), 180)
    A("Q2", P["FET"], {"1": "Q2_G", "4": "BUS_P", "2": "MID", "3": "MID", "5": "MID", "6": "MID", "7": "MID"},
      (57, 31), 0)
    # Bidirectional TVS across the whole switch: clamps the turn-off spike in both directions
    # and does not conduct on a reversed battery (48 V standoff > 42 V).
    A("D2", P["TVS48CA"], {"1": "BAT_SH", "2": "BUS_P"}, (46, 42), 0)
    # Freewheel: the load-side harness drives BUS_P below ground at turn-off.
    A("D3", P["SS510C"], {"1": "BUS_P", "2": N}, (72, 50.2), 270)
    # Controller. High-side sense: CS_SEL to GND. Latch-off: R_TMR 100 k across C_TMR.
    A("U1", P["TPS48100"], {"1": "TPS_EN", "2": "CTR_INP2", "3": "CTR_INP1", "4": None, "5": "TPS_FLT_N", "6": N,
                            "7": N, "8": "TPS_ISCP", "9": "TPS_TMR", "10": "SCP_TEST", "20": "TPS_VS", "19": None,
                            "18": "SNS_BAT_P", "17": "SNS_BAT_N", "15": "G1PU", "14": "G1PD", "13": "MID",
                            "12": "TPS_BST", "11": "G2_O"}, (44, 56), 0, big=True)
    R("R1", "10", "SNS_BAT_P", "TPS_VS", (37.5, 50.5), 0)
    C("C4", "100n/100V", "TPS_VS", N, (37.5, 52.5), 0)
    R("R2", "1M", "TPS_VS", "TPS_EN", (37.5, 54.5), 0)       # UVLO 1.23 V x 1051/51 = 25.3 V rising
    R("R3", "51k", "TPS_EN", N, (37.5, 56.5), 0)
    R("R4", "40.2k", "TPS_ISCP", N, (37.5, 58.5), 0)         # I_SC = (19 mV + 2 µA x 40.2 k) / 1 mΩ = 99 A
    C("C5", "6.8n", "TPS_TMR", N, (37.5, 60.5), 0)           # t_SC ≈ 100 µs (latch-off, eq. 9)
    R("R5", "100k", "TPS_TMR", N, (37.5, 62.5), 0)           # latch-off resistor
    C("C6", "1n", "SNS_BAT_P", "SNS_BAT_N", (50.5, 49.5), 0, dnp=True)  # TI placeholder, tune on the bench
    R("R6", "10", "G1PU", "Q1_G", (50.5, 52.5), 0)           # turn-on
    R("R7", "150", "G1PD", "Q1_G", (50.5, 54.5), 0)          # Rg_off, 100-220 Ω window (study 12 §AA.4)
    R("R8", "150", "G2_O", "Q2_G", (50.5, 56.5), 0)          # Q2: one pin, same resistor both ways
    C("C7", "1u", "TPS_BST", "MID", (50.5, 58.5), 0)         # ≥ 2 x Qg(IPB017) / 1 V
    R("R9", "100k", "Q1_G", "MID", (54, 50.5), 90)
    A("D4", P["Z15"], {"1": "Q1_G", "2": "MID"}, (57.2, 51.5), 90)
    R("R10", "100k", "Q2_G", "MID", (54, 57.0), 90)
    A("D5", P["Z15"], {"1": "Q2_G", "2": "MID"}, (57.2, 58.0), 90)
    R("R11", "100k", "MID", N, (33.5, 50.5), 90)              # DIAG pull-down (ICD stuck_fet_diagnostic)
    R("R12", "150k", "MID", "DIAG_ADC", (33.5, 54.0), 90)     # DIAG divider top, bottom at the ADS1115
    # Bus current/energy: INA228 at 0x40 on the contactor shunt (GND = BUS_N, power domain).
    A("U2", P["INA228"], {"1": N, "2": N, "3": "INA_ALERT_N", "4": "I2C_SDA", "5": "I2C_SCL", "6": V3, "7": N,
                          "8": "SNS_BAT_N", "9": "INA0_N", "10": "INA0_P"}, (20.6, 17.5), 0)
    R("R13", "10", "SNS_BAT_P", "INA0_P", (19.0, 21.4), 0)
    R("R14", "10", "SNS_BAT_N", "INA0_N", (22.2, 21.4), 0)
    C("C8", "100n", V3, N, (20.6, 14.4), 0)

    # =====================================================================
    #  2. Precharge: P-FET driven by the ESP32 (not by the TPS48100, study 12 §AA.2.3)
    # =====================================================================
    c.block("2. PRÉCHARGE — FET P piloté par l'ESP32, résistance 10 Ω / 25 W hors carte (J13)", 40, 0)
    A("Q3", P["PFET"], {"1": "PRE_G", "2": "PRE_P", "3": "BAT_P"}, (35, 7), 0)
    R("R15", "10k", "PRE_G", "BAT_P", (17.5, 3.6), 180)
    A("D6", P["Z12"], {"1": "BAT_P", "2": "PRE_G"}, (17.9, 6.3), 0)
    R("R16", "22k", "PRE_G", "PRE_C", (21.6, 3.6), 0)
    A("Q4", P["NPN"], {"1": "PRE_B", "2": N, "3": "PRE_C"}, (25.6, 4.6), 0)
    R("R17", "4.7k", "PRECH_EN", "PRE_B", (25.6, 1.3), 0)
    R("R18", "100k", "PRE_B", N, (22.1, 6.4), 0)
    A("J13", P["LUG4"], {"1": "PRE_P", "2": "PRE_N"}, (45, 7), 0, value="PRECHARGE_R (M4)")
    A("D7", P["SS510C"], {"1": "BUS_P", "2": "PRE_N"}, (67.8, 7), 180)

    # =====================================================================
    #  3. Brake chopper: analog, bus-powered, downstream of the contactor
    # =====================================================================
    c.block("3. HACHEUR DE FREINAGE — comparateur analogique alimenté par le bus, ON 42,5 V / OFF 41,8 V", 40, 0)
    A("J12", P["LUG4"], {"1": "BUS_P", "2": "CHOP_N"}, (194.5 + XR, 36), 270, value="BRAKE_CHOPPER (M4)")
    A("Q5", P["FET"], {"1": "CH_G", "4": "CHOP_N", "2": N, "3": N, "5": N, "6": N, "7": N}, (176 + XR, 56), 0)
    A("D8", P["SS510C"], {"1": "BUS_P", "2": "CHOP_N"}, (186 + XR, 46.4), 270)
    x0 = XR
    R("R19", "10", "BUS_P", "CH_VIN", (150 + x0, 46.6), 270)
    C("C9", "1u/100V", "CH_VIN", N, (150 + x0, 50.0), 270)
    A("U3", P["TPS7A4001"], {"8": "CH_VIN", "5": "CH_VIN", "1": "CH_12V", "2": "CH_FB", "4": N, "9": N, "3": None,
                             "6": None, "7": None}, (154.5 + x0, 53.5), 0)
    R("R20", "93.1k", "CH_12V", "CH_FB", (159.5 + x0, 51.5), 0)  # 1.173 V x (1 + 93.1/10) = 12.1 V
    R("R21", "10k", "CH_FB", N, (159.5 + x0, 53.5), 0)
    C("C10", "10u", "CH_12V", N, (159.5 + x0, 56.0), 0)
    A("U4", P["TLV1701"], {"1": "CH_SNS", "3": "CH_REF", "4": "CH_CMD", "5": "CH_12V", "2": N}, (145 + x0, 51.0), 0)
    R("R22", "10k", "CH_12V", "CH_REF", (148.0 + x0, 55.5), 90)
    A("D9", P["LM4040"], {"1": "CH_REF", "2": N, "3": None}, (145 + x0, 57.5), 0)
    C("C11", "100n", "CH_REF", N, (141.6 + x0, 57.5), 90)
    # Positive-feedback divider: V_on = 2.5 x (1 + Rt/Rb + Rt/Rh) = 42.50 V, ΔV = V_oh x Rt/Rh = 0.70 V.
    R("R23", "49.9k", "BUS_P", "CH_T", (140 + x0, 46.6), 270)
    R("R24", "49.9k", "CH_T", "CH_SNS", (140 + x0, 49.8), 270)
    R("R25", "6.04k", "CH_SNS", "CH_B", (137.5 + x0, 53.0), 270)
    R("R26", "221", "CH_B", N, (137.5 + x0, 56.2), 270)
    R("R27", "1.69M", "CH_SNS", "CH_CMD", (141 + x0, 53.4), 0)
    C("C12", "1n", "CH_SNS", N, (140 + x0, 56.6), 90)
    R("R28", "10k", "CH_12V", "CH_CMD", (148.0 + x0, 51.0), 90)
    C("C13", "100n", "CH_12V", N, (148.0 + x0, 59.0), 90)
    A("U5", P["UCC27517"], {"3": "CH_CMD", "4": N, "1": "CH_12V", "5": "CH_DRV", "2": N}, (162.5 + x0, 59.5), 0)
    C("C14", "1u", "CH_12V", N, (159.0 + x0, 59.5), 90)
    R("R29", "10", "CH_DRV", "CH_G", (163.0 + x0, 62.8), 0)
    R("R30", "100k", "CH_G", N, (159.5 + x0, 62.8), 0)
    R("R31", "100k", "CH_CMD", "CHOP_ACT", (154.5 + x0, 62.8), 0)
    R("R32", "33k", "CHOP_ACT", G, (154.5 + x0, 72), 90)
    R("R33", "4.7k", "CH_CMD", "CH_LED", (144.5 + x0, 62.8), 0)
    A("D10", P["LED_R"], {"1": N, "2": "CH_LED"}, (148.0 + x0, 62.8), 180, value="CHOP")
    # Active bus discharge (cahier #8): the expander may force the comparator on (OR input).
    # Node impedance ≈ 5.9 kΩ: 3.05 V through 330 Ω lifts CH_SNS to ≈ 2.9 V > 2.5 V.
    A("D26", P["B5819W"], {"1": "DISCH_K", "2": "DISCH_REQ"}, (134.0 + x0, 55.5), 90)
    R("R34", "330", "DISCH_K", "CH_SNS", (134.0 + x0, 59.5), 90)

    # =====================================================================
    #  4. Motor branches: MINI 58 V 25 A fuse, 2 mΩ shunt + INA228 (blown-fuse detection)
    # =====================================================================
    c.block("4. BRANCHES MOTEUR — fusible MINI 58 V 25 A, shunt 2 mΩ + INA228 (0x41-0x44)", 40, 0)
    addr = [("GND", "VS"), ("GND", "SDA"), ("GND", "SCL"), ("VS", "GND")]
    strap = {"GND": N, "VS": V3, "SDA": "I2C_SDA", "SCL": "I2C_SCL"}
    names = ["AV_G", "AV_D", "AR_G", "AR_D"]
    for k in range(4):
        n = k + 1
        cx = 82 + 28 * k
        s = "_B%d" % n
        A("J%d" % (3 + k), P["LUG4"], {"1": "BR_OUT" + s, "2": N}, (cx, 7), 0, value="MOT_%s (M4)" % names[k])
        A("F%d" % n, P["FUSE25"], {"1": "BUS_P", "2": "BR_F" + s}, (cx - 1.7, 37.5), 90)
        A("RS%d" % (n + 1), P["SH2m"], {"1": "BR_F" + s, "2": "SNS" + s + "_P", "3": "SNS" + s + "_N",
                                         "4": "BR_OUT" + s}, (cx, 19.5), 90)
        a1, a0 = addr[k]
        A("U%d" % (5 + n), P["INA228"], {"1": strap[a1], "2": strap[a0], "3": "INA_ALERT_N", "4": "I2C_SDA",
                                         "5": "I2C_SCL", "6": V3, "7": N, "8": "SNS" + s + "_N",
                                         "9": "INA" + s + "_N", "10": "INA" + s + "_P"}, (cx + 9.5, 21.0), 0)
        R("R%d" % (40 + 4 * k), "10", "SNS" + s + "_P", "INA" + s + "_P", (cx + 5.6, 24.4), 0)
        R("R%d" % (41 + 4 * k), "10", "SNS" + s + "_N", "INA" + s + "_N", (cx + 5.6, 17.8), 0)
        C("C%d" % (40 + k), "100n", V3, N, (cx + 13.6, 21.0), 90)

    # Bus voltage (precharge complete?) and bus-live LED, tapped on BUS_P.
    R("R60", "150k", "BUS_P", "BUSV_ADC", (100, 46.6), 270)
    R("R61", "22k-1206", "BUS_P", "LED_BUS", (114, 47.2), 270)
    A("D11", P["LED_R"], {"1": N, "2": "LED_BUS"}, (114, 51.5), 90, value="BUS LIVE")

    # =====================================================================
    #  5. Hotel rails, upstream of the contactor (D2)
    # =====================================================================
    c.block("5. RAILS HÔTEL (amont contacteur, D2) — fusible, anti-inversion, 5 V 3,5 A, 12 V AUX 2 A, "
            "12 V calculateur isolé, 3,3 V", 40, 0)
    A("F5", P["FUSE5"], {"1": "BAT_SH", "2": "HOTEL_F"}, (25.5, 48.6), 270)
    A("Q6", P["PFET"], {"1": "REV_G", "2": "HOTEL_F", "3": "HOTEL_IN"}, (25.5, 58.5), 90)
    R("R62", "100k", "REV_G", N, (19.5, 55.5), 90)
    A("D12", P["Z12"], {"1": "HOTEL_IN", "2": "REV_G"}, (19.5, 60.0), 90)
    C("C50", "47u/100V", "HOTEL_IN", G, (40.5, 76), 270)
    C("C55", "47u/100V", "HOTEL_IN", G, (50.0, 76), 270)
    C("C51", "2.2u/100V", "HOTEL_IN", G, (57.5, 71.5), 0)

    def buck(p, x, y, out, l_part, rfb_top, rc, cc, cout):
        """TPS54360B, 400 kHz (RT 243 k), UVLO 24 V on / 20 V off. Values: decisions.md §Rails."""
        A("U" + p, P["TPS54360B"], {"1": p + "_BOOT", "2": "HOTEL_IN", "3": p + "_EN", "4": p + "_RT", "5": p + "_FB",
                                    "6": p + "_COMP", "7": G, "8": p + "_SW", "9": G}, (x, y), 0, big=True)
        C("C" + p + "1", "2.2u/100V", "HOTEL_IN", G, (x - 6.5, y - 6), 90)
        C("C" + p + "2", "2.2u/100V", "HOTEL_IN", G, (x - 3.2, y - 6), 90)
        C("C" + p + "3", "100n/100V", "HOTEL_IN", G, (x - 0.4, y - 6), 90)
        C("C" + p + "4", "100n", p + "_BOOT", p + "_SW", (x + 3.5, y - 4.6), 0)
        R("R" + p + "1", "1.18M", "HOTEL_IN", p + "_EN", (x - 6.5, y - 1.5), 0)
        R("R" + p + "2", "59k", p + "_EN", G, (x - 6.5, y + 0.5), 0)
        R("R" + p + "3", "243k", p + "_RT", G, (x - 6.5, y + 2.5), 0)
        R("R" + p + "4", rfb_top, out, p + "_FB", (x - 6.5, y + 4.5), 0)
        R("R" + p + "5", "10.2k", p + "_FB", G, (x - 6.5, y + 6.5), 0)
        R("R" + p + "6", rc, p + "_COMP", p + "_CZ", (x - 2.5, y + 4.6), 0)
        C("C" + p + "5", cc, p + "_CZ", G, (x - 2.5, y + 6.5), 0)
        C("C" + p + "6", "82p", p + "_COMP", G, (x - 6.5, y + 8.5), 0)
        A("D" + p, P["B560C"], {"1": p + "_SW", "2": G}, (x + 7.5, y + 1.6), 270)
        A("L" + p, P[l_part], {"1": p + "_SW", "2": out}, (x + 9, y + 14), 0)
        for i in range(3):
            C("C%s%d" % (p, 7 + i), cout, out, G, (x + 15.0 + 3.4 * i, y + 2.5), 90)

    buck("B5", 14, 110, V5, "L15", "53.6k", "10.7k", "8.2n", "47u/10V")              # 5.00 V
    buck("B12", 48, 110, "12V_AUX_RAW", "L33", "143k", "10.5k", "15n", "22u/25V")      # 12.0 V
    A("D13", P["LED_G"], {"1": G, "2": "LED_5V"}, (4, 134), 0, value="5V")
    R("R63", "1k", V5, "LED_5V", (7.5, 134), 0)
    C("C52", "10u", V5, G, (11, 134), 0)

    # 3V3_HOTEL: LDO from 5V_HOTEL. Feeds the /SAFE pull-up, logic, INA228s.
    A("U26", P["AP2112"], {"1": V5, "2": G, "3": V5, "4": None, "5": V3}, (63, 84), 0)
    C("C53", "1u", V5, G, (59.2, 84), 90)
    C("C54", "10u", V3, G, (67, 84), 90)
    A("D14", P["LED_G"], {"1": G, "2": "LED_3V3"}, (63, 89), 0, value="3V3")
    R("R64", "1k", V3, "LED_3V3", (66.5, 89), 0)

    # 12V_COMPUTE: isolated module. Ctrl open = on; NPN pulls it low on COMPUTE_OFF.
    A("PS1", P["URB"], {"3": "HOTEL_IN", "1": "COMP_CTRL", "2": G, "4": "12V_COMPUTE", "5": None, "6": "GND_COMPUTE"},
      (33, 92), 180, big=True)
    A("Q7", P["NPN"], {"1": "COMP_B", "2": G, "3": "COMP_CTRL"}, (38, 97.5), 0)
    R("R65", "10k", "COMPUTE_OFF", "COMP_B", (42, 97), 0)
    R("R66", "100k", "COMP_B", G, (42, 99), 0)
    C("C56", "100u/25V", "12V_COMPUTE", "GND_COMPUTE", (5.5, 82), 270)
    C("C57", "10u", "12V_COMPUTE", "GND_COMPUTE", (5.5, 89.5), 270)
    A("J7", P["XH2"], {"1": "12V_COMPUTE", "2": "GND_COMPUTE"}, (4.5, 70.5), 270, value="PWR_12V_COMPUTE")
    A("D15", P["LED_G"], {"1": "GND_COMPUTE", "2": "LED_CMP"}, (5, 99.5), 0, value="12V CMP")
    R("R67", "4.7k", "12V_COMPUTE", "LED_CMP", (5, 97.5), 0)

    # =====================================================================
    #  6. Protected outputs (eFuses, C10)
    # =====================================================================
    c.block("6. SORTIES PROTÉGÉES — eFuses TPS2595x (C10), 5V_BRAKE dédié (D5) avec réservoir 2200 µF", 40, 0)

    def efuse(ref, part, vin, vout, ilm, en_top, en_bot, x, y, rbase):
        A(ref, P[part], {"3": vin, "4": vin, "2": ref + "_EN", "1": ref + "_DV", "5": vout, "6": "EFUSE_FLT_N",
                         "7": ref + "_ILM", "8": G, "9": G}, (x, y), 0)
        R("R%d" % rbase, en_top, vin, ref + "_EN", (x - 3.5, y - 1), 0)
        R("R%d" % (rbase + 1), en_bot, ref + "_EN", G, (x - 3.5, y + 1), 0)
        # ILM resistor level with pin 7 (upper right) so its track does not wall in pin 6 (FLT).
        R("R%d" % (rbase + 2), ilm, ref + "_ILM", G, (x + 3.5, y - 1), 0)
        C("C%d" % (rbase + 100), "10n", ref + "_DV", G, (x + 3.5, y + 1), 0)
        C("C%d" % (rbase + 101), "10u", vout, G, (x, y + 3.5), 0)

    # 12V_AUX: TPS259573 (OVLO 1.2 V x 134/10 = 16.1 V, active-low EN/OVLO), 2.0 A.
    efuse("U10", "EF12", "12V_AUX_RAW", "12V_AUX", "1.05k", "124k", "10k", 64, 140, 70)
    A("D16", P["LED_G"], {"1": G, "2": "LED_12A"}, (71, 136), 0, value="12V AUX")
    R("R75", "4.7k", "12V_AUX", "LED_12A", (74.5, 136), 0)
    # 5V_LOGIC to the CAN trunk (J15/J16 pin 1), J9 and the ACS758: 1.5 A, UVLO 3.75 V.
    efuse("U11", "EF5", V5, "5V_LOGIC", "1.4k", "100k", "47k", 138, 144, 80)
    A("D17", P["LED_G"], {"1": G, "2": "LED_5VL"}, (130, 148), 0, value="5V LOG")
    R("R85", "1k", "5V_LOGIC", "LED_5VL", (126.5, 148), 0)
    # 5V_LED to the WS2812B strips: 0.95 A.
    efuse("U12", "EF5", V5, "5V_LED", "2.2k", "100k", "47k", 184.5 + XR, 80, 90)
    # 5V_BRAKE: diode-isolated 2200 µF reservoir, then one eFuse per harness (front, rear), 0.49 A.
    A("D18", P["SS34"], {"1": "BRK_RES", "2": V5}, (19, 141), 90)
    C("C99", "2200u/10V", "BRK_RES", G, (7, 142), 0)
    C("C98", "10u", "BRK_RES", G, (22.6, 141), 90)
    efuse("U13", "EF5", "BRK_RES", "5V_BRAKE_F", "4.42k", "100k", "47k", 31, 142, 100)
    efuse("U14", "EF5", "BRK_RES", "5V_BRAKE_R", "4.42k", "100k", "47k", 44, 142, 110)
    A("J22", P["MF2"], {"1": "5V_BRAKE_F", "2": None}, (31, 156), 0, value="5V_BRAKE_AV")
    A("J23", P["MF2"], {"1": "5V_BRAKE_R", "2": None}, (42, 156), 0, value="5V_BRAKE_AR")

    # =====================================================================
    #  7. SAFETY ESP32, CAN, /SAFE, watchdog latch
    # =====================================================================
    c.block("7. ESP32 SAFETY, CAN, /SAFE (pull-up unique 1 kΩ + NF champignon, pull-down 10 kΩ), "
            "watchdog verrouillé (D7)", 40, 0)
    esp = {"1": None, "2": None, "13": None, "16": None, "17": None, "18": None, "23": None, "24": None, "33": None,
           "36": None, "37": None, "38": None, "14": G, "20": G, "26": G, "19": V5,
           "29": "CAN_TX", "5": "CAN_RX", "25": "I2C_SDA", "22": "I2C_SCL", "28": "SPI_SCK", "21": "SPI_MOSI",
           "27": "SPI_MISO", "35": "SPI_CS", "3": "IMU_INT", "9": "CTR_INP1", "10": "CTR_INP2", "11": "PRECH_EN",
           "7": "SAFE_HOLD", "8": "SAFE_REARM", "4": "SAFE_N_IN", "12": "WD_DONE", "6": "BMS_RX", "30": "BMS_TX",
           "32": "FAN_PWM", "34": "LED_DATA_F", "15": "LED_DATA_R", "31": "GPIO16_1W"}
    A("U15", P["ESP32"], esp, (151.5 + XR, 108), 0, big=True)
    C("C60", "10u", V5, G, (157.5, 146), 90)
    # Fail-safe defaults while the ESP32 boots or is absent.
    bank = [("R120", "100k", "CTR_INP1", G), ("R121", "100k", "CTR_INP2", G), ("R122", "100k", "PRECH_EN", G),
            ("R123", "100k", "WD_DONE", G), ("R124", "100k", "SAFE_REARM", G), ("R125", "100k", "LED_DATA_F", G),
            ("R126", "100k", "LED_DATA_R", G), ("R127", "100k", "FAN_PWM", G), ("R128", "10k", "CAN_TX", V3),
            ("R129", "10k", "SPI_CS", V3), ("R130", "10k", "IMU_INT", V3), ("R131", "10k", "TPS_FLT_N", V3),
            ("R132", "100k", "SCP_TEST", G), ("R133", "2.2k", "I2C_SDA", V3), ("R134", "2.2k", "I2C_SCL", V3),
            ("R135", "10k", "INA_ALERT_N", V3), ("R136", "10k", "EFUSE_FLT_N", V3), ("R119", "100k", "DISCH_REQ", G)]
    for i, (ref, v, a, b) in enumerate(bank):
        R(ref, v, a, b, (124, 74 + 2 * i), 0)

    # CAN
    A("U16", P["TCAN"], {"1": "CAN_TX", "4": "CAN_RX", "8": G, "5": V3, "3": V5, "7": "CANH", "6": "CANL", "2": G},
      (112, 134), 0)
    C("C61", "4.7u", V5, G, (107, 129), 90)
    C("C62", "100n", V5, G, (110, 129), 90)
    C("C63", "100n", V3, G, (115, 129), 90)
    A("D19", P["NUP2105"], {"1": "CANH", "2": "CANL", "3": G}, (112, 141), 0)
    A("J15", P["MF6"], {"1": "5V_LOGIC", "2": "CANH", "3": "CANL", "4": "SAFE_N", "5": G, "6": "SHIELD"},
      (100.5, 156), 0, value="CAN_SAFE_A")
    A("J16", P["MF6"], {"1": "5V_LOGIC", "2": "CANH", "3": "CANL", "4": "SAFE_N", "5": G, "6": "SHIELD"},
      (123.5, 156), 0, value="CAN_SAFE_B")
    A("J9", P["MF4"], {"1": "5V_LOGIC", "2": "5V_LOGIC", "3": G, "4": G}, (146.6, 156), 0, value="PWR_5V_LOGIC")

    # /SAFE: the single pull-up through the mushroom NC contact (J11 CH1), the single pull-down.
    xa, xb, xj = 182 + XR, 187.5 + XR, 194 + XR
    R("R137", "1k", V3, "ESTOP_CH1_A", (xa, 70.5), 0)
    R("R139", "1k", V3, "ESTOP_CH2_A", (xa, 72.5), 0)
    R("R140", "10k", "ESTOP_CH2_B", G, (xa, 74.5), 0)
    A("JP1", P["HDR2"], {"1": "ESTOP_CH1_B", "2": "SAFE_N"}, (xb, 70.5), 0)
    A("J11", P["MF4"], {"1": "ESTOP_CH1_A", "2": "ESTOP_CH1_B", "3": "ESTOP_CH2_A", "4": "ESTOP_CH2_B"},
      (xj, 82), 90, value="ESTOP_LOOP")
    R("R138", "10k", "SAFE_N", G, (138, 74), 90)
    A("D20", P["ESD33"], {"1": "SAFE_N", "2": G}, (135, 74), 90)
    A("Q8", P["NFET"], {"1": "SAFE_HOLD", "2": G, "3": "SAFE_N"}, (132, 77.5), 0)
    R("R141", "10k", "SAFE_HOLD", V3, (132, 80.5), 0)
    A("Q9", P["NFET"], {"1": "LATCH_QN", "2": G, "3": "SAFE_N"}, (136.5, 77.5), 0)
    R("R142", "100k", "LATCH_QN", V3, (136.5, 80.5), 0)
    R("R143", "1k", "SAFE_N", "SAFE_N_IN", (140.5, 77.5), 90)

    # Watchdog -> latch -> /SAFE (D7). Trip sources ANDed (active low): TPL5010 RSTn, overcurrent.
    A("U17", P["TPL5010"], {"1": V3, "2": G, "3": "WD_DELAY", "4": "WD_DONE", "5": "WD_WAKE", "6": "WD_RST_N"},
      (132, 88), 0)
    R("R144", "5.23k", "WD_DELAY", G, (128.5, 88), 90)           # 1.0 s (TPL5010 table)
    R("R145", "10k", "WD_RST_N", V3, (135.8, 86), 0)
    C("C64", "100n", V3, G, (135.8, 90), 0)
    A("U18", P["LVC1G08"], {"1": "WD_RST_N", "2": "OC_N", "4": "TRIP_N", "5": V3, "3": G}, (132, 95), 0)
    C("C65", "100n", V3, G, (135.8, 95), 0)
    R("R146", "10k", "OC_N", V3, (128.5, 95), 90)
    C("C66", "1u", "OC_N", G, (132, 98.5), 0)                    # power-on clear: OC_N low ~10 ms
    A("U19", P["LVC1G74"], {"2": V3, "1": "SAFE_REARM", "6": "TRIP_N", "7": V3, "8": V3, "5": "LATCH_Q",
                            "3": "LATCH_QN", "4": G}, (132, 103), 0)
    C("C67", "100n", V3, G, (135.8, 103), 0)

    # Hardware overcurrent: ACS758 (J14) window comparator, ±35 A, ratiometric to 5V_LOGIC.
    A("J14", P["MF3"], {"1": "5V_LOGIC", "2": "ACS_OUT", "3": G}, (xj, 96), 90, value="ACS758")
    R("R147", "10k", "ACS_OUT", "ACS_DIV", (xa, 90), 0)
    R("R148", "20k", "ACS_DIV", G, (xa, 92), 0)
    C("C68", "1n", "ACS_DIV", G, (xa, 94), 0)
    A("U20", P["LM2903"], {"3": "OC_VH", "2": "ACS_DIV", "5": "ACS_DIV", "6": "OC_VL", "8": "5V_LOGIC", "1": "OC_N",
                           "7": "OC_N", "4": G}, (142, 94), 0)
    C("C69", "100n", "5V_LOGIC", G, (147.5, 94), 90)
    R("R149", "57.6k", "5V_LOGIC", "OC_VH", (142, 89), 0)
    R("R150", "18.7k", "OC_VH", "OC_VL", (142, 99), 0)
    R("R151", "24.3k", "OC_VL", G, (142, 101), 0)
    R("R152", "1k", "ACS_DIV", "ACS_ADC", (106, 76), 0)
    C("C70", "10n", "ACS_ADC", G, (109.5, 76), 0)

    # ADC: ACS758, DIAG, bus voltage, temperature.
    A("U21", P["ADS1115"], {"1": G, "2": None, "3": G, "4": "ACS_ADC", "5": "DIAG_ADC", "6": "BUSV_ADC",
                            "7": "TEMP_ADC", "8": V3, "9": "I2C_SDA", "10": "I2C_SCL"}, (106, 80), 0)
    C("C71", "100n", V3, G, (110.8, 80), 90)
    R("R153", "10k", "DIAG_ADC", G, (99.5, 76.5), 0)
    C("C72", "100n", "DIAG_ADC", G, (99.5, 78.5), 0)
    R("R154", "10k", "BUSV_ADC", G, (99.5, 80.5), 0)
    C("C73", "100n", "BUSV_ADC", G, (99.5, 82.5), 0)

    # Expander (D3): slow signals.
    exp = {"1": None, "2": G, "3": G, "21": G, "12": G, "24": V3, "22": "I2C_SCL", "23": "I2C_SDA",
           "4": "WD_WAKE", "5": "TPS_FLT_N", "6": "SCP_TEST", "7": "LATCH_Q", "8": "OC_N", "9": "CHOP_ACT",
           "10": "ESTOP_CH2_B", "11": "IMU_WAKE", "13": "FAN1_TACH", "14": "FAN2_TACH", "15": "EFUSE_FLT_N",
           "16": "INA_ALERT_N", "17": "LED_OK_K", "18": "LED_FLT_K", "19": "COMPUTE_OFF", "20": "DISCH_REQ"}
    A("U22", P["TCA9555"], exp, (110, 100), 0)
    C("C74", "100n", V3, G, (115.5, 95), 90)
    A("D21", P["LED_G"], {"1": "LED_OK_K", "2": "LED_OK_A"}, (101, 108), 0, value="OK")
    R("R155", "1k", V3, "LED_OK_A", (97.5, 108), 0)
    A("D22", P["LED_R"], {"1": "LED_FLT_K", "2": "LED_FLT_A"}, (101, 110), 0, value="FAULT")
    R("R156", "1k", V3, "LED_FLT_A", (97.5, 110), 0)

    # Temperature J21: triple footprint, analog fitted (R158), 1-Wire / NTC options DNP.
    A("J21", P["MF3"], {"1": V3, "2": "TEMP_DATA", "3": G}, (xj, 110), 90, value="TEMP_SENSOR")
    R("R157", "4.7k", V3, "TEMP_DATA", (xa, 102), 0, dnp=True)
    R("R158", "0R", "TEMP_DATA", "TEMP_ADC", (xa, 104), 0)
    R("R159", "0R", "TEMP_DATA", "GPIO16_1W", (xa, 106), 0, dnp=True)
    R("R160", "10k", V3, "TEMP_DATA", (xa, 108), 0, dnp=True)

    # BNO085 remote (J17, SPI): series 33 Ω, WAKE pulled high before reset (C15).
    A("J17", P["GH8"], {"1": V3, "2": G, "3": "IMU_SCK", "4": "IMU_MISO", "5": "IMU_MOSI", "6": "IMU_CS",
                        "7": "IMU_INT", "8": "IMU_WAKE"}, (195 + XR, 151), 90, value="IMU_BNO085")
    for i, (ref, v, a, b) in enumerate((("R161", "33", "SPI_SCK", "IMU_SCK"), ("R162", "33", "IMU_MISO", "SPI_MISO"),
                                        ("R163", "33", "SPI_MOSI", "IMU_MOSI"), ("R164", "33", "SPI_CS", "IMU_CS"),
                                        ("R165", "10k", "IMU_WAKE", V3))):
        R(ref, v, a, b, (xa, 137 + 2 * i), 0)

    # WS2812B front/rear: AHCT buffer (VIH 2.0 V at 5 V), 470 Ω series.
    for i, (ref, data, j, y, yj) in enumerate((("U23", "LED_DATA_F", "J19", 116, 124),
                                               ("U24", "LED_DATA_R", "J20", 127, 138))):
        A(ref, P["AHCT125"], {"1": G, "2": data, "3": G, "4": data + "_B", "5": V5}, (xa + 1.5, y), 0)
        C("C%d" % (75 + i), "100n", V5, G, (xa + 1.5, y + 3.5), 0)
        R("R%d" % (166 + i), "470", data + "_B", data + "_O", (xb + 0.5, y + 3.5), 0)
        A(j, P["MF3"], {"1": "5V_LED", "2": data + "_O", "3": G}, (xj, yj), 90,
          value="WS2812B_" + ("AV" if i == 0 else "AR"))

    # BMS UART, isolated (J2): ADuM1201 + B0503S, read-only firmware.
    A("J2", P["GH4"], {"1": "BMS_R", "2": "BMS_T", "3": "GND_BMS", "4": None}, (90, 154.5), 0, value="BMS_UART (iso)")
    A("U25", P["ADUM1201"], {"1": V3, "2": "BMS_RX", "3": "BMS_TX", "4": G, "5": "GND_BMS", "6": "BMS_TO",
                             "7": "BMS_RI", "8": "BMS_3V3"}, (84, 140), 0)
    A("PS2", P["B0503S"], {"2": V5, "1": G, "4": "BMS_3V3", "3": "GND_BMS"}, (80, 124), 0)
    C("C77", "4.7u", V5, G, (77, 125), 90)
    C("C78", "10u", "BMS_3V3", "GND_BMS", (91, 130), 0)
    C("C79", "100n", V3, G, (78.5, 140), 90)
    R("R168", "330", "BMS_3V3", "GND_BMS", (91, 132), 0)    # minimum load for the unregulated B0503S
    R("R171", "10k", "BMS_RI", "BMS_3V3", (91, 134), 0)
    R("R169", "100", "BMS_R", "BMS_RI", (91, 138), 0)
    R("R170", "100", "BMS_TO", "BMS_T", (91, 140), 0)

    # Fans (J18): open-drain PWM shared, tach to 3.3 V with series 4.7 k + BAT54S clamp.
    A("Q10", P["NFET"], {"1": "FAN_PWM", "2": G, "3": "FAN_PWM_OD"}, (49, 147.5), 0)
    for i, bx in enumerate((52, 64)):
        n = i + 1
        A("J18%s" % "AB"[i], P["FAN"], {"1": G, "2": "12V_AUX", "3": "FAN%d_TK" % n, "4": "FAN_PWM_OD"},
          (bx, 156), 0, value="FAN%d" % n)
        R("R%d" % (172 + 2 * i), "4.7k", "FAN%d_TK" % n, "FAN%d_TACH" % n, (bx + 3, 149.5), 0)
        R("R%d" % (173 + 2 * i), "10k", "FAN%d_TACH" % n, V3, (bx + 3, 147.5), 0)
        A("D%d" % (23 + i), P["BAT54S"], {"1": G, "2": V3, "3": "FAN%d_TACH" % n}, (bx + 7.5, 148.5), 0)
    A("J8", P["MF4"], {"1": "12V_AUX", "2": "12V_AUX", "3": G, "4": G}, (12, 156), 0, value="PWR_12V_AUX")

    # ★ GND STAR (D4): the only GND_LOGIC-BUS_N bond.
    A("NT1", P["STAR"], {"1": N, "2": G}, (12, 63.0), 270, in_bom=False)

    # Test points.
    tps = [("BAT_P", 4.5, 24, 1), ("BUS_P", 110, 43, 1), (N, 75.2, 57.6, 1), ("MID", 44, 49.0, 0),
           ("Q1_G", 40.8, 49.0, 0), ("Q2_G", 47.4, 49.0, 0), ("CH_G", 167 + XR, 63.2, 0), ("CH_12V", 162.5 + XR, 51.0, 0),
           ("CH_CMD", 151.5 + XR, 62.8, 0), ("HOTEL_IN", 31.5, 66.2, 1), (V5, 14.5, 134, 0), (V3, 70, 89, 0),
           ("12V_AUX", 76, 140, 0), ("12V_COMPUTE", 12.5, 97.5, 0), ("GND_COMPUTE", 12.5, 100.3, 0),
           ("5V_LOGIC", 145, 148, 0), ("5V_LED", 184.5 + XR, 86.5, 0), ("5V_BRAKE_F", 31, 148.5, 0),
           ("5V_BRAKE_R", 44, 148.5, 0), ("SAFE_N", 143, 74, 0), ("CANH", 117, 141, 0), ("CANL", 120, 141, 0),
           ("TRIP_N", 128.5, 100.5, 0), ("LATCH_Q", 128.5, 105.5, 0), ("TPS_FLT_N", 33.5, 58.0, 0),
           ("DIAG_ADC", 96, 79, 0), (G, 96, 83, 0), (G, 123, 141, 0), (G, 56, 98, 0)]
    for i, (net, x, y, big) in enumerate(tps):
        A("TP%d" % (i + 1), P["TPP" if big else "TP"], {"1": net}, (x, y), 0, value=net.replace("_HOTEL", ""))
    return c


# ---------------------------------------------------------------------------
#  Schematic
# ---------------------------------------------------------------------------
PWR_NETS = (G, N, V5, "HOTEL_IN", "BUS_P", "BAT_P", "5V_LOGIC", "12V_AUX", "GND_COMPUTE", "5V_LED", "BMS_3V3",
            "GND_BMS")


def build_sch(c: Circuit):
    splib.write_all(LIB_DIR)
    s = K.Schematic(PROJECT, "Retriever — safety_power", paper="A0", rev=REV, date=DATE,
                    company="Retriever, open hardware (CERN-OHL-S-2.0)",
                    comments=(DRAFT, "Contacteur statique 42 V / 30 A sur pack lithium : relecture experte obligatoire",
                              "Généré par scripts/build.py — ne pas éditer à la main",
                              "Décisions et calculs : hardware/pcb/safety_power/decisions.md"),
                    extra_lib_dirs=(LIB_DIR,))
    for p in c.parts:
        if "text" in p:
            s.text(p["text"], p["at"], 2.5, True)
            continue
        fields = {"LCSC": p["lcsc"], "MPN": p["mpn"]} if p["lcsc"] else ({"MPN": p["mpn"]} if p["mpn"] else {})
        s.add(p["ref"], p["lib_id"], p["value"], p["footprint"], p["sch"], rot=p["sch_rot"], nets=p["nets"],
              fields=fields, dnp=p["dnp"], in_bom=p["in_bom"])
    for i, net in enumerate(PWR_NETS):
        s.power_flag(net, (40 + i * 15, 20))
    s.text(DRAFT, (40, 10), 3.0, True)
    s.write(os.path.join(KICAD_DIR, PROJECT + ".kicad_sch"))
    for kind, ext in (("sym", "kicad_sym"), ("fp", "pretty")):
        with open(os.path.join(KICAD_DIR, kind + "-lib-table"), "w") as f:
            f.write('(%s_lib_table\n\t(version 7)\n\t(lib (name "sp") (type "KiCad") '
                    '(uri "${KIPRJMOD}/lib/sp.%s") (options "") (descr "safety_power, généré par splib.py"))\n)\n'
                    % (kind, ext))
    return s


# ---------------------------------------------------------------------------
#  Board
# ---------------------------------------------------------------------------
HV_SIG = ["/SNS_*", "/INA0_*", "/INA_B*", "/TPS_VS", "/TPS_EN", "/G1PU", "/G1PD", "/G2_O", "/Q1_G", "/Q2_G",
          "/TPS_BST", "/MID", "/PRE_G", "/PRE_C", "/REV_G", "/CH_T", "/CH_G", "/B5_*", "/B12_*"]
NETCLASSES = [
    # 0.15 mm everywhere in the logic zone (0.5 mm pitch packages).
    {"name": "Default", "track": 0.15, "clearance": 0.15, "via": 0.7, "drill": 0.3},
    # 42 V-level small signals. 0.19 mm: imposed by the 0.5 mm pitch of TPS48100 and INA228
    # (both rated 85-100 V by TI in that package). See decisions.md §Isolation.
    {"name": "HV_SIG", "track": 0.15, "clearance": 0.19, "via": 0.7, "drill": 0.3, "patterns": HV_SIG},
    # 42 V power copper: 0.5 mm. IPC-2221B asks 0.6 mm for 31-50 V on bare external copper (B2);
    # 0.5 mm is what a 4-terminal 2512 shunt allows between its sense and current pads.
    # Solder mask everywhere + conformal coating of the power zone recommended (decisions.md).
    {"name": "HV_PWR", "track": 1.5, "clearance": 0.5, "via": 0.8, "drill": 0.3,
     "patterns": ["/BAT_*", "/BUS_P", "/BR_*", "/PRE_P", "/PRE_N", "/CHOP_N"]},
    # Hotel input (42 V, ≤ 3 A): wide, but it lands on 1.27 mm pitch regulator pins.
    {"name": "HV_RAIL", "track": 1.0, "clearance": 0.25, "via": 0.8, "drill": 0.3, "patterns": ["/HOTEL_*"]},
    # Power ground: wide tracks, small clearance (it is 0 V; 42 V nets keep their own 0.6 mm).
    {"name": "PWR_GND", "track": 0.4, "clearance": 0.15, "via": 0.7, "drill": 0.3, "patterns": ["/BUS_N"]},
    # Logic rails carrying amps: 0.6 mm on 2 oz outer ≈ 3.2 A, on 1 oz inner ≈ 1.7 A (IPC-2152, ΔT 20 °C).
    {"name": "RAIL", "track": 0.6, "clearance": 0.2, "via": 0.8, "drill": 0.3,
     "patterns": ["/5V_*", "/12V_*", "/BRK_RES", "/GND_COMPUTE", "/FAN_PWM_OD"]},
    {"name": "RAIL_LO", "track": 0.3, "clearance": 0.15, "via": 0.7, "drill": 0.3,
     "patterns": ["/3V3_HOTEL", "/CH_12V", "/BMS_3V3", "/GND_BMS"]},
]
# JLCPCB 4-layer: 0.09 mm track/space min; we keep 0.15. Vias 0.6/0.3 min. Copper to edge 0.4 mm.
RULES = dict(track=0.15, clearance=0.15, via=0.6, drill=0.3, annular=0.13, edge_clearance=0.4)
HOLES = [(4, 4), (206, 4), (4, 156), (194.5, 156), (78, 66), (126, 66)]
LOGIC_TOP = 64.5
COMPUTE = (0.0, 67.0, 16.0, 101.5)
ISO = [(76.0, 127.8), (97.0, 127.8), (97.0, 159.5), (83.6, 159.5), (83.6, 136.0), (76.0, 136.0)]
ISO_GAP = [(75.0, 126.8), (98.0, 126.8), (98.0, 160.0), (82.6, 160.0), (82.6, 137.0), (75.0, 137.0)]  # ISO + 1 mm


def build_pcb(c: Circuit, sch_uuids: dict, nc_pins: dict):
    import pcbnew as Pn
    import kicadpcb as KP

    b = KP.Board(os.path.join(KICAD_DIR, PROJECT + ".kicad_pcb"), copper_layers=4, extra_fp_dirs=(LIB_DIR,))
    # JLCPCB 4-layer: 0.09 mm track/space min; we keep 0.15. Vias 0.7/0.3.
    b.rules(**RULES)
    for nc in NETCLASSES:
        b.netclass(nc["name"], nc["track"], nc["clearance"], nc.get("via", 0.6), nc.get("drill", 0.3),
                   nc.get("patterns", []))
    for p in c.parts:
        if "text" in p:
            continue
        fields = {"LCSC": p["lcsc"], "MPN": p["mpn"]} if p["lcsc"] else ({"MPN": p["mpn"]} if p["mpn"] else {})
        nc = {k: v.replace("/", "{slash}") for k, v in nc_pins[p["ref"]].items()}
        info = {"footprint": p["footprint"], "value": p["value"], "uuid": sch_uuids[p["ref"]], "fields": fields,
                "dnp": p["dnp"], "in_bom": p["in_bom"], "nets": p["nets"], "nc": nc}
        b.place(p["ref"], info, p["pcb"][0], p["pcb"][1], p["rot"], back=p["back"])
    b.outline(0, 0, W, H, r=3.0)
    for i, (x, y) in enumerate(HOLES):
        b.hole("H%d" % (i + 1), x, y, name="MountingHole_3.2mm_M3", net=None)
        keepout(b, circle(x, y, 4.5), tracks=True)
    # No copper under the ESP32 antenna (module on sockets above the board).
    keepout(b, rect(150 + XR, 96.0, 179.5 + XR, 101.6), tracks=True)
    return b


# ---- copper helpers ---------------------------------------------------------

def pad_box(b, ref, num, margin=0.0):
    import pcbnew as Pn
    fp = b.fps[ref]
    boxes = [p.GetBoundingBox() for p in fp.Pads() if p.GetNumber() == num]
    return (min(Pn.ToMM(bb.GetLeft()) for bb in boxes) - margin, min(Pn.ToMM(bb.GetTop()) for bb in boxes) - margin,
            max(Pn.ToMM(bb.GetRight()) for bb in boxes) + margin, max(Pn.ToMM(bb.GetBottom()) for bb in boxes) + margin)


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


def track_keepout(b, layer, pts):
    """Rule area that forbids tracks (vias and zone fill allowed) on one layer: keeps the
    autorouter off the inner planes so they are not cut."""
    import pcbnew as Pn
    z = Pn.ZONE(b.b)
    z.SetIsRuleArea(True)
    ls = Pn.LSET()
    ls.AddLayer(layer)
    z.SetLayerSet(ls)
    z.SetDoNotAllowZoneFills(False)
    z.SetDoNotAllowTracks(True)
    z.SetDoNotAllowVias(False)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowFootprints(False)
    o = z.Outline()
    o.NewOutline()
    for x, y in pts:
        o.Append(Pn.FromMM(x), Pn.FromMM(y))
    b.b.Add(z)


def keepout(b, pts, tracks=False):
    import pcbnew as Pn
    z = Pn.ZONE(b.b)
    z.SetIsRuleArea(True)
    z.SetLayerSet(Pn.LSET.AllCuMask())
    z.SetDoNotAllowZoneFills(True)
    z.SetDoNotAllowTracks(tracks)
    z.SetDoNotAllowVias(tracks)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowFootprints(False)
    o = z.Outline()
    o.NewOutline()
    for x, y in pts:
        o.Append(Pn.FromMM(x), Pn.FromMM(y))
    b.b.Add(z)


def via(b, net, x, y, size=0.8, drill=0.4):
    import pcbnew as Pn
    import kicadpcb as KP
    v = Pn.PCB_VIA(b.b)
    v.SetPosition(KP.pt(x, y))
    v.SetWidth(KP.mm(size))
    v.SetDrill(KP.mm(drill))
    v.SetNet(b.net(net))
    b.b.Add(v)


class Copper:
    """Collects rectangles per (net, layer), unions them, emits one zone per outline."""

    def __init__(self, b):
        self.b = b
        self.parts = {}

    def add(self, net, layer, pts, prio=2, clr=0.6):
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
                z.SetZoneName("%s_%s_%d" % (net, Pn.LayerName(layer) if hasattr(Pn, "LayerName") else layer, i))
                o = z.Outline()
                ol = ps.Outline(i)
                o.NewOutline()
                for j in range(ol.PointCount()):
                    pt = ol.CPoint(j)
                    o.Append(pt.x, pt.y)
                for h in range(ps.HoleCount(i)):
                    hl = ps.Hole(i, h)
                    o.NewHole()
                    for j in range(hl.PointCount()):
                        pt = hl.CPoint(j)
                        o.Append(pt.x, pt.y, -1, 0)
                self.b.b.Add(z)


def logic_area():
    """The logic zone minus the isolated compute island and the BMS isolation island."""
    import pcbnew as Pn
    ps = polyset(rect(0.4, LOGIC_TOP, W - 0.4, H - 0.4))
    ps.BooleanSubtract(polyset(rect(COMPUTE[0], COMPUTE[1] - 1.0, COMPUTE[2] + 1.0, COMPUTE[3] + 1.0)))
    ps.BooleanSubtract(polyset(ISO_GAP))
    return ps


def power_copper(b):
    """High-current copper as zones, drawn before routing. Freerouting receives them as planes
    and keeps signals out. Widths and checks: decisions.md §Cuivre (IPC-2152)."""
    import pcbnew as Pn
    F, B, I1 = Pn.F_Cu, Pn.B_Cu, Pn.In1_Cu
    cu = Copper(b)
    pb = lambda r, n, m=0.0: pad_box(b, r, n, m)  # noqa: E731

    # --- BAT_P: J1 lug, input caps/TVS, RS1 pin 1 (approached from above, away from sense pin 2),
    #     Q3 source, R15/D6. Mounting hole H1 is cut out by its keepout.
    p1, s2 = pb("RS1", "1"), pb("RS1", "2")
    cu.add("BAT_P", F, rect(0.4, 0.4, p1[0] - 1.0, 32.6))
    cu.add("BAT_P", F, rect(0.4, 0.4, 17.0, p1[1] + 0.6))
    q3s = pb("Q3", "3", 0.3)
    cu.add("BAT_P", F, rect(14.0, 7.6, q3s[2], 13.0))
    # --- BAT_SH: RS1 pin 4 (approached from below, away from sense pin 3) -> Q1 tab, D2, F5.
    p4, s3 = pb("RS1", "4"), pb("RS1", "3")
    q1t = pb("Q1", "4")
    cu.add("BAT_SH", F, rect(p4[0], p4[3] - 0.6, q1t[2] + 0.4, 46.0))
    cu.add("BAT_SH", F, rect(s3[2] + 0.8, 19.5, q1t[2] + 0.4, 46.0))
    cu.add("BAT_SH", F, rect(q1t[2], 38.0, 44.0, 46.0))
    cu.add("BAT_SH", B, rect(s3[2] + 0.8, 19.5, q1t[2] + 0.4, 46.0))
    # --- MID (common source): both source pin rows.
    q1p, q2p = pb("Q1", "2"), pb("Q2", "2")
    cu.add("MID", F, rect(q1t[2] + 1.2, 24.3, q2p[2] + 0.4, 37.6), clr=0.4)
    # --- BUS_P: Q2 tab, band, strip to the precharge diode, chopper terminal.
    q2t = pb("Q2", "4")
    d7k = pb("D7", "1", 0.4)
    cu.add("BUS_P", F, rect(q2t[0] - 0.4, 19.5, 75.5, 46.0))
    cu.add("BUS_P", F, rect(47.5, 38.0, q2t[0], 46.0))
    cu.add("BUS_P", F, rect(d7k[0], 0.4, 75.5, 19.5))
    cu.add("BUS_P", F, rect(75.5, 33.0, 186.0 + XR, 46.0))
    cu.add("BUS_P", F, rect(186.0 + XR, 31.0, W - 0.4, 40.4))
    cu.add("BUS_P", B, rect(q2t[0] - 0.4, 19.5, 66.0, 40.0))
    # --- Precharge path
    q3t = pb("Q3", "2", 0.4)
    j13a, j13b = pb("J13", "1", 0.9), pb("J13", "2", 0.9)
    cu.add("PRE_P", F, rect(q3t[0], 0.4, j13a[2], 13.0))
    d7a = pb("D7", "2", 0.4)
    cu.add("PRE_N", F, rect(j13b[0], 0.4, d7a[2], 13.0))
    # --- Branches: pin 1 of the shunt approached from the left (sense pin 2 exits right, to the
    #     INA228), pin 4 approached from the right (sense pin 3 exits left).
    for k in range(4):
        n = k + 1
        s = "_B%d" % n
        cx = 82 + 28 * k
        f2 = pb("F%d" % n, "2", 0.9)
        r1, r2 = pb("RS%d" % (n + 1), "1"), pb("RS%d" % (n + 1), "2")
        r4, r3 = pb("RS%d" % (n + 1), "4"), pb("RS%d" % (n + 1), "3")
        cu.add("BR_F" + s, F, rect(cx - 5.0, r1[1], r1[0] + 0.6, f2[3]))
        cu.add("BR_F" + s, F, rect(cx - 5.0, r2[3] + 0.8, f2[2], f2[3]))
        lug = pb("J%d" % (3 + k), "1", 0.9)
        cu.add("BR_OUT" + s, F, rect(lug[0], 0.4, lug[2], r3[1] - 1.6))
        cu.add("BR_OUT" + s, F, rect(r3[2] + 0.8, 0.4, cx + 3.0, r4[3]))
        lugn = pb("J%d" % (3 + k), "2", 0.9)
        cu.add(N, F, rect(lugn[0], 0.4, lugn[2], lugn[3]), clr=0.6)
    # --- Chopper
    q5t, q5s, q5g = pb("Q5", "4", 0.4), pb("Q5", "2"), pb("Q5", "1")
    cu.add("CHOP_N", F, rect(q5t[0], 48.6, W - 0.4, 64.0))
    cu.add("CHOP_N", F, rect(188.5 + XR, 41.0, W - 0.4, 48.6))
    cu.add(N, F, rect(q5s[0] - 2.0, q5g[3] + 0.3, q5t[0] - 0.8, 64.0), clr=0.6)
    # --- BUS_N islands on F.Cu: J1 lug, input caps/TVS, star pad 1, D3 anode.
    cu.add(N, F, rect(0.4, 33.4, 17.4, 56.5), clr=0.6)
    cu.add(N, F, rect(0.4, 56.5, 11.0, 62.6), clr=0.6)
    nt = pb("NT1", "1", 0.2)
    cu.add(N, F, rect(nt[0], 56.5, nt[2], nt[3]), clr=0.6)
    d3a = pb("D3", "2", 1.5)
    cu.add(N, F, rect(d3a[0], d3a[1], d3a[2], 58.0), clr=0.6)
    # --- Hotel feed
    f5b, q6t, q6s = pb("F5", "2", 0.8), pb("Q6", "2", 0.6), pb("Q6", "3", 0.6)
    cu.add("HOTEL_F", F, rect(min(f5b[0], q6t[0]), f5b[1], max(f5b[2], q6t[2]), q6t[3]), clr=0.6)
    cu.add("HOTEL_IN", F, rect(q6s[0], q6s[1], 36.0, 81.0), clr=0.4)
    cu.add("HOTEL_IN", F, rect(36.0, 68.5, 54.6, 74.5), clr=0.4)

    # --- Planes. Power zone: BUS_N on B.Cu and In1. Logic zone: GND_LOGIC on In1, with islands
    #     for the isolated 12 V output and the BMS isolator.
    cu.add(N, B, rect(0.4, 0.4, W - 0.4, Y_SPLIT - 2.6), prio=1, clr=0.6)
    cu.add(N, I1, rect(0.4, 0.4, W - 0.4, Y_SPLIT - 2.6), prio=1, clr=0.6)
    cu.emit()
    la = logic_area()
    for i in range(la.OutlineCount()):
        add_polyset_zone(b, G, I1, la, i, prio=1, clr=0.2)
        # In2 under the logic zone is the 3V3_HOTEL plane (sig / GND / PWR / sig stack-up);
        # In2 under the power zone stays a routing layer.
        add_polyset_zone(b, V3, Pn.In2_Cu, la, i, prio=1, clr=0.2)
    b.zone("GND_COMPUTE", I1, rect(*COMPUTE), priority=1, clearance=0.6, name="GND_CMP_IN1")
    b.zone("GND_BMS", I1, ISO, priority=1, clearance=0.6, name="GND_BMS_IN1")


def add_polyset_zone(b, net, layer, ps, i, prio=0, clr=0.3):
    import pcbnew as Pn
    z = Pn.ZONE(b.b)
    z.SetLayer(layer)
    z.SetNet(b.net(net))
    z.SetAssignedPriority(prio)
    z.SetLocalClearance(Pn.FromMM(clr))
    z.SetMinThickness(Pn.FromMM(0.2))
    z.SetPadConnection(Pn.ZONE_CONNECTION_FULL)
    z.SetIslandRemovalMode(Pn.ISLAND_REMOVAL_MODE_ALWAYS)
    o = z.Outline()
    ol = ps.Outline(i)
    o.NewOutline()
    for j in range(ol.PointCount()):
        o.Append(ol.CPoint(j).x, ol.CPoint(j).y)
    b.b.Add(z)


def power_vias(b):
    """Stitching vias: F.Cu power copper down to the B.Cu/In1 BUS_N planes and to the B.Cu drain
    islands under Q1/Q2. Skips any point within 1 mm of a pad (holes and solder mask)."""
    import pcbnew as Pn
    boxes = []
    for fp in b.b.GetFootprints():
        for p in fp.Pads():
            bb = p.GetBoundingBox()
            boxes.append((Pn.ToMM(bb.GetLeft()), Pn.ToMM(bb.GetTop()), Pn.ToMM(bb.GetRight()), Pn.ToMM(bb.GetBottom())))
    holes = HOLES

    def grid(net, x0, y0, x1, y1, pitch):
        n = 0
        y = y0
        while y <= y1 + 1e-6:
            x = x0
            while x <= x1 + 1e-6:
                ok = not any(a[0] - 1.0 < x < a[2] + 1.0 and a[1] - 1.0 < y < a[3] + 1.0 for a in boxes)
                ok = ok and all(math.hypot(x - hx, y - hy) > 5.5 for hx, hy in holes)
                if ok:
                    via(b, net, x, y)
                    n += 1
                x += pitch
            y += pitch
        return n

    n = grid(N, 2.0, 38.5, 16.0, 55.5, 2.5)
    n += grid(N, 2.0, 57.0, 10.0, 61.5, 2.0)
    d3a = pad_box(b, "D3", "2")
    n += grid(N, d3a[0] - 0.8, d3a[3] + 1.2, d3a[2] + 0.8, 57.4, 1.6)
    q5s = pad_box(b, "Q5", "2")
    n += grid(N, q5s[0] - 1.5, 53.0, q5s[0] + 2.5, 63.0, 1.6)
    for k in range(4):
        lugn = pad_box(b, "J%d" % (3 + k), "2")
        n += grid(N, lugn[0] + 0.2, lugn[3] + 0.0, lugn[2] - 0.2, lugn[3] + 0.0, 2.5)
    q1t = pad_box(b, "Q1", "4")
    n += grid("BAT_SH", 25.5, 20.5, q1t[2] - 0.8, 45.0, 2.2)
    q2t = pad_box(b, "Q2", "4")
    n += grid("BUS_P", q2t[0] + 0.8, 20.5, 65.0, 39.0, 2.2)
    return n


def fanout(b, net, y_max, y_min=0.0, size=0.6, drill=0.3, stub=False, min_pad=99.0):
    """One via next to every SMD pad of `net` that its F.Cu copper does not already reach.
    The power-zone planes (In1, B.Cu) are BUS_N, so a via is a complete connection."""
    import pcbnew as Pn
    full = "/" + net
    zones_f = [z for z in b.b.Zones() if not z.GetIsRuleArea() and z.GetLayer() == Pn.F_Cu]
    pads = [p for fp in b.b.GetFootprints() for p in fp.Pads()]
    obst = []
    for p in pads:
        bb = p.GetBoundingBox()
        hv = p.GetNetname().startswith(("/BAT_", "/BUS_P", "/BR_", "/PRE_", "/CHOP_N", "/HOTEL"))
        obst.append((Pn.ToMM(bb.GetLeft()), Pn.ToMM(bb.GetTop()), Pn.ToMM(bb.GetRight()), Pn.ToMM(bb.GetBottom()),
                     p.GetNetname(), 0.55 if hv else 0.22))
    vias = [(Pn.ToMM(t.GetPosition().x), Pn.ToMM(t.GetPosition().y)) for t in b.b.GetTracks() if t.GetClass() == "PCB_VIA"]

    def inside_other_zone(x, y, r):
        for z in zones_f:
            if z.GetNetname() == full:
                continue
            for a in range(8):
                q = Pn.VECTOR2I(Pn.FromMM(x + r * math.cos(a * math.pi / 4)), Pn.FromMM(y + r * math.sin(a * math.pi / 4)))
                if z.Outline().Contains(q):
                    return True
        return False

    def own_zone(x, y):
        return any(z.GetNetname() == full and z.Outline().Contains(Pn.VECTOR2I(Pn.FromMM(x), Pn.FromMM(y)))
                   for z in zones_f)

    def seg_clear(cx, cy, x, y, own):
        L = math.hypot(x - cx, y - cy)
        for i in range(int(L / 0.1) + 1):
            t = i * 0.1 / L if L else 0
            px, py = cx + (x - cx) * t, cy + (y - cy) * t
            if own[0] <= px <= own[2] and own[1] <= py <= own[3]:
                continue
            for (x0, y0, x1, y1, nn, clr) in obst:
                if nn == full:
                    continue
                dx = max(x0 - px, 0, px - x1)
                dy = max(y0 - py, 0, py - y1)
                if math.hypot(dx, dy) < 0.15 + max(clr, 0.16):
                    return False
        return True

    def ok(x, y, pad):
        if x < 1.0 or y < y_min or x > W - 1.0 or y > y_max or inside_other_zone(x, y, 1.0):
            return False
        if y_min > 0 and (in_poly(x, y, ISO_GAP) or (x < COMPUTE[2] + 1.5 and y < COMPUTE[3] + 1.5)):
            return False
        for (x0, y0, x1, y1, nn, clr) in obst:
            if nn == full and (x0 <= x <= x1 and y0 <= y <= y1):
                continue
            dx = max(x0 - x, 0, x - x1)
            dy = max(y0 - y, 0, y - y1)
            if math.hypot(dx, dy) < 0.3 + (clr if nn != full else 0.0):
                return False
        return all(math.hypot(x - vx, y - vy) > 0.9 for vx, vy in vias)

    n = 0
    done_pads = []
    failed = []
    for p in pads:
        if p.GetNetname() != full or p.GetAttribute() != Pn.PAD_ATTRIB_SMD:
            continue
        c = p.GetPosition()
        cx, cy = Pn.ToMM(c.x), Pn.ToMM(c.y)
        if cy > y_max or cy < y_min or own_zone(cx, cy):
            continue
        bb = p.GetBoundingBox()
        hw, hh = Pn.ToMM(bb.GetWidth()) / 2, Pn.ToMM(bb.GetHeight()) / 2
        if stub and 2 * min(hw, hh) >= min_pad:
            continue
        if not stub and hw * hh * 4 > 1.4 and p.GetNumber() not in ("1", "2") and p.GetAttribute() == Pn.PAD_ATTRIB_SMD:
            if any(math.hypot(cx - vx, cy - vy) < 1.0 for vx, vy in vias) or any(
                    q.GetAttribute() == Pn.PAD_ATTRIB_PTH and q.GetNumber() == p.GetNumber() for q in p.GetParentFootprint().Pads()):
                done_pads.append(p)
                continue
            # exposed pad: thermal via in the pad
            via(b, net, cx, cy, size, drill)
            vias.append((cx, cy))
            done_pads.append(p)
            n += 1
            continue
        fc = p.GetParent().GetPosition()
        away = math.atan2(cy - Pn.ToMM(fc.y), cx - Pn.ToMM(fc.x))
        done = False
        for extra in ((1.0, 1.4, 0.8) if stub else (0.55, 0.9, 1.3)):
            for k in range(17):
                a = away + (k // 2) * (math.pi / 8) * (1 if k % 2 else -1)
                r = abs(hw * math.cos(a)) + abs(hh * math.sin(a)) + extra
                x, y = cx + r * math.cos(a), cy + r * math.sin(a)
                own = (cx - hw, cy - hh, cx + hw, cy + hh)
                if ok(x, y, p) and seg_clear(cx, cy, x, y, own):
                    b.track(net, [(cx, cy), (x, y)], 0.25 if stub else 0.3)
                    if not stub:
                        via(b, net, x, y, size, drill)
                    vias.append((x, y))
                    n += 1
                    done = True
                    break
            if done:
                break
        (done_pads if done else failed).append(p)
    # A pad that found no room is tied to an adjacent pad of the same net and footprint
    # that did (e.g. INA228 A0/A1 straps next to GND).
    for p in failed:
        c = p.GetPosition()
        for q in done_pads:
            if q.GetParentFootprint().GetReference() != p.GetParentFootprint().GetReference():
                continue
            d = q.GetPosition()
            if math.hypot(Pn.ToMM(c.x - d.x), Pn.ToMM(c.y - d.y)) < 0.6:
                b.track(net, [(Pn.ToMM(c.x), Pn.ToMM(c.y)), (Pn.ToMM(d.x), Pn.ToMM(d.y))], 0.2)
                n += 1
                break
    return n


def efuse_ilm(b):
    """ILM (pin 7, 0.5 mm pitch) to its resistor: drawn by the script, the router could not
    enter the pin past FLT (pin 6)."""
    for ref in ("U10", "U11", "U12", "U13", "U14"):
        x7, y7 = pad_xy(b, ref, "7")
        rref = [r for r, f in ILM_R.items() if f == ref][0]
        xr, yr = pad_xy(b, rref, "1")
        xm = x7 + 0.9
        b.track(ref + "_ILM", [(x7, y7), (xm, y7), (xm, yr), (xr, yr)], 0.2)


ILM_R = {"R72": "U10", "R82": "U11", "R92": "U12", "R102": "U13", "R112": "U14"}


def ina_ground_bridges(b):
    """INA228 GND (pin 7) sits between VS and VBUS at 0.5 mm pitch, with no room for a via:
    tie it under the package to the BUS_N pad of its decoupling capacitor (or for U2 to C8),
    and the A0 strap of U9 across the package to pin 7."""
    pairs = [("U2", "C8")] + [("U%d" % (5 + n), "C%d" % (39 + n)) for n in range(1, 5)]
    for u, cref in pairs:
        x7, y7 = pad_xy(b, u, "7")
        xc, yc = pad_xy(b, cref, "2")
        xe = x7 + 1.1
        b.track(N, [(x7, y7), (xe, y7), (xe, yc), (xc, yc)], 0.2)
    x2, y2 = pad_xy(b, "U9", "2")
    x7, y7 = pad_xy(b, "U9", "7")
    xm = x2 + 1.25
    b.track(N, [(x2, y2), (xm, y2), (xm, y7), (x7, y7)], 0.2)


def pad_xy(b, ref, num):
    import pcbnew as Pn
    for p in b.fps[ref].Pads():
        if p.GetNumber() == num:
            v = p.GetPosition()
            return Pn.ToMM(v.x), Pn.ToMM(v.y)
    raise KeyError((ref, num))


def in_poly(x, y, pts):
    inside = False
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            inside = not inside
    return inside


def silkscreen(b):
    t = b.text
    t("RETRIEVER  safety_power  %s" % REV, 105, 153.0, 1.4) if False else None
    t("RETRIEVER safety_power " + REV, 125, 116.0, 1.5)
    t("NE PAS FABRIQUER avant M1 M2 M10 M12 PACK_ID P1-P3", 125, 118.6, 1.0)
    t("et relecture par un electronicien", 125, 120.4, 1.0)
    t("ZONE PUISSANCE 42 V", 104, 61.5, 1.5)
    t("ZONE SIGNAL", 104, 69.0, 1.5)
    t("* GND STAR *", 21.0, 66.0, 1.1)
    t("seule liaison GND_LOGIC-BUS_N", 21.0, 67.8, 0.8)
    t("BAT+", 15.5, 9.5, 1.2)
    t("BAT-", 15.0, 52.0, 1.2)
    t("PRECHARGE 10R", 51.5, 13.8, 0.9)
    t("HACHEUR 22R", 202 + XR - 10, 58.5, 0.9, rot=90)
    for k, nm in enumerate(["AV G", "AV D", "AR G", "AR D"]):
        cx = 82 + 28 * k
        t("MOT %s   +   -" % nm, cx + 6.5, 13.0, 0.9)
        t("MINI 58V 25A", cx - 6.2, 30.0, 0.8, rot=90)
    t("CONTACTEUR Q1/Q2", 46, 18.5, 0.9)
    t("12V ISOLE", 4.6, 65.9, 0.8)
    t("BUS LIVE", 117.5, 51.5, 0.8, justify="left")
    t("BMS ISOLE", 90, 147.0, 0.8)


def main():
    what = sys.argv[1] if len(sys.argv) > 1 else "sch"
    os.makedirs(KICAD_DIR, exist_ok=True)
    pcb_path = os.path.join(KICAD_DIR, PROJECT + ".kicad_pcb")
    if what in ("drop", "patch"):
        # Post-routing clean-up, driven by the last DRC report (build/drc.rpt):
        #   drop  — delete the few routed items KiCad flags (clearance rounding, edge);
        #   patch — route the connections still open with patchroute (A*, F/B + vias).
        import kicadpcb as KP
        import patchroute
        b = KP.Board(pcb_path, load=True, extra_fp_dirs=(LIB_DIR,))
        rpt = os.path.join(BOARD_DIR, "build", "drc.rpt")
        if what == "drop":
            print("dropped:", drop_violations(b, rpt))
        else:
            print("patched:", patchroute.finish(b.b, rpt, net_clearance, W, H, ignore_nets=("/" + G,)))
        b.save()
        return
    if what == "reroute":
        # Second Freerouting pass on the routed board: existing wiring is kept, only the
        # connections left open by the first pass are attempted (pours removed first).
        import kicadpcb as KP
        import pcbnew as Pn
        b = KP.Board(pcb_path, load=True, extra_fp_dirs=(LIB_DIR,))
        b.rules(**RULES)
        for z in list(b.b.Zones()):
            if z.GetZoneName() in ("GND_CMP_B", "GND_BMS_B") or (z.GetAssignedPriority() == 0 and not z.GetIsRuleArea()):
                b.b.Remove(z)
        work = os.path.join(BOARD_DIR, "build")
        print("removed after DRC:", drop_violations(b, os.path.join(work, "drc.rpt")))
        print(b.autoroute(work, passes=int(os.environ.get("PASSES", "20")), threads=6))
        logic_pours(b)
        b.save()
        print("ok: reroute")
        return
    if what == "route":
        import kicadpcb as KP
        b = KP.Board(pcb_path, load=True, extra_fp_dirs=(LIB_DIR,))
        work = os.path.join(BOARD_DIR, "build")
        os.makedirs(work, exist_ok=True)
        print(autoroute(b, work, passes=int(os.environ.get("PASSES", "40"))))
        # Freerouting necks tracks down by the DSN margin near pads; restoring 0.15 mm uses up
        # exactly that margin.
        print("widened", b.widen_tracks(0.15), "necked tracks")
        logic_pours(b)
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
        power_copper(b)
        print("stitching vias:", power_vias(b))
        ina_ground_bridges(b)
        print("BUS_N fan-out vias:", fanout(b, N, y_max=Y_SPLIT - 3.0))
        # The router does not fan out to planes: every logic-zone pad of the plane nets gets
        # its via here (GND_LOGIC on In1, 3V3_HOTEL on In2).
        print("GND_LOGIC fan-out vias:", fanout(b, G, y_max=H - 1.0, y_min=LOGIC_TOP + 1.0))
        print("3V3 fan-out vias:", fanout(b, V3, y_max=H - 1.0, y_min=LOGIC_TOP + 1.0))
        # Wide rail tracks (0.6-1.0 mm) cannot enter 0.25-0.3 mm pins: each narrow pin of a rail
        # gets a 0.25 mm stub that ends outside the package, where the router lands.
        nst = 0
        for net in (V5, "5V_LOGIC", "5V_LED", "5V_BRAKE_F", "5V_BRAKE_R", "BRK_RES", "12V_AUX_RAW", "12V_AUX",
                    "HOTEL_IN", "12V_COMPUTE", "GND_COMPUTE", "BMS_3V3", "GND_BMS", "CH_12V"):
            nst += fanout(b, net, y_max=H - 1.0, stub=True, min_pad=0.6)
        print("rail stubs:", nst)
        silkscreen(b)
        b.save()
    print("ok:", what, len([p for p in c.parts if "ref" in p]), "parts")


def autoroute(b, workdir, passes=40, threads=6, margin_um=20):
    """kicadpcb.Board.autoroute with one change: every clearance in the DSN is raised by
    `margin_um` before Freerouting runs. Freerouting and KiCad round clearances differently;
    without the margin a handful of KiCad DRC clearance errors survive routing."""
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
    return "\n".join(l for l in log if "unrouted" in l and ("Net '" in l or "completed:" in l))[-3000:]


def net_clearance(net):
    """Clearance of a board net name, from NETCLASSES (fnmatch on the patterns)."""
    import fnmatch
    for nc in NETCLASSES[1:]:
        if any(fnmatch.fnmatch(net, pat) for pat in nc.get("patterns", [])):
            return nc["clearance"]
    return NETCLASSES[0]["clearance"]


def drop_violations(b, report):
    """Delete the routed tracks and vias that the previous DRC flagged (Freerouting and KiCad
    disagree by a few µm on clearances, and on the board-edge clearance), so the next
    Freerouting pass redraws those connections."""
    import re
    import pcbnew as Pn
    if not os.path.exists(report):
        return 0
    bad = []
    for blk in re.split(r"\n(?=\[)", open(report).read()):
        m = re.match(r"\[(\w+)\]", blk)
        if not m or m.group(1) not in ("clearance", "copper_edge_clearance", "annular_width", "shorting_items",
                                         "hole_to_hole", "holes_co_located", "track_dangling"):
            continue
        for x, y, kind, net in re.findall(r"@\(([-\d.]+) mm, ([-\d.]+) mm\): (Piste|Via) \[([^\]]+)\]", blk):
            bad.append((float(x), float(y), kind, net))
    keep = set()  # never remove the vias placed by the script (power stitching, fan-out)
    n = 0
    for t in list(b.b.GetTracks()):
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


def logic_pours(b):
    """GND_LOGIC on F.Cu and B.Cu in the logic zone, added after routing; GND_COMPUTE and
    GND_BMS islands on B.Cu."""
    import pcbnew as Pn
    la = logic_area()
    for layer in (Pn.F_Cu, Pn.B_Cu):
        for i in range(la.OutlineCount()):
            add_polyset_zone(b, G, layer, la, i, prio=0, clr=0.25)
    b.zone("GND_COMPUTE", Pn.B_Cu, rect(*COMPUTE), priority=1, clearance=0.6, name="GND_CMP_B")
    b.zone("GND_BMS", Pn.B_Cu, ISO, priority=1, clearance=0.6, name="GND_BMS_B")


if __name__ == "__main__":
    main()
