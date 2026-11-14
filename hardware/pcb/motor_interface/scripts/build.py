#!/usr/bin/env python3
"""motor_interface v2.0-draft — the whole board, schematic and layout, in one file.

    python3 build.py sch            # schematic + project (any Python 3)
    <KiCad python> build.py pcb     # board: placement, fixed passthrough tracks
    <KiCad python> build.py route   # autoroute, then copper zones

The circuit is described once, in `circuit()`. `sch` and `pcb` both read it,
so the board can only contain what the schematic contains.

Every design decision is recorded in ../decisions.md (French); the numbers
below quote the datasheet line they come from.

Board: one ESP32-DevKitC V4 (MOTION node) on sockets, two ZS-X11H drivers,
two hub motors. Ground domains (decision D4 of conception-v2.md):
    GND        logic ground, = GND_LOGIC of the trunk
    GND_MOT_A  BUS_N of driver A, as seen through its Hall/command harness
    GND_MOT_B  BUS_N of driver B
They are NOT joined on this board. They meet only at the star point on
safety_power. R_GT_A / R_GT_B (not fitted) exist for bench use only.
"""

from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD_DIR = os.path.dirname(HERE)
KICAD_DIR = os.path.join(BOARD_DIR, "kicad")
LIB_DIR = os.path.join(KICAD_DIR, "lib")
sys.path.insert(0, os.path.join(BOARD_DIR, "..", "scripts"))
sys.path.insert(0, HERE)

import kicadgen as K  # noqa: E402
import mi_gen as G  # noqa: E402

PROJECT = "motor_interface"
REV = "2.0-draft"
DATE = "2026-11-13"
STATUS = "v2.0-draft — ne pas fabriquer avant M7, HALL_OC, P1, P2, P3"

# ---------------------------------------------------------------------------
#  Parts: (lib_id, footprint, value, LCSC, MPN)
#  LCSC numbers: stock snapshot 13/11/2026 by web search — re-check before ordering.
# ---------------------------------------------------------------------------
P_MF6 = ("Connector_Generic:Conn_01x06", "Connector_Molex:Molex_Micro-Fit_3.0_43650-0615_1x06_P3.00mm_Vertical",
         "Micro-Fit 6p", "C505231", "Molex 43650-0615")
# 8-way vertical Micro-Fit: not stocked by LCSC -> bought from Mouser, hand soldered.
P_MF8 = ("Connector_Generic:Conn_01x08", "Connector_Molex:Molex_Micro-Fit_3.0_43650-0815_1x08_P3.00mm_Vertical",
         "Micro-Fit 8p", "", "Molex 43650-0815 (Mouser 538-43650-0815)")
# DevKitC sockets: turned-pin, must accept 0.64 mm square pins (Mill-Max 310, not 315).
P_SOCK = ("Connector_Generic:Conn_01x19", "Connector_PinSocket_2.54mm:PinSocket_1x19_P2.54mm_Vertical",
          "socket 1x19", "", "Mill-Max 310-43-119-41-001000 (Mouser)")
P_BUF3 = ("74xGxx:74LVC3G17", "Package_SO:VSSOP-8_2.3x2mm_P0.5mm", "SN74LVC3G17DCUR", "C68245",
          "TI SN74LVC3G17DCUR")
P_AND = ("74xGxx:74LVC1G08", "Package_TO_SOT_SMD:SOT-23-5", "SN74LVC1G08DBVR", "C7666", "TI SN74LVC1G08DBVR")
P_NFET = ("Transistor_FET:AO3400A", "Package_TO_SOT_SMD:SOT-23", "AO3400A", "C20917", "AOS AO3400A")
P_PFET = ("Transistor_FET:AO3401A", "Package_TO_SOT_SMD:SOT-23", "AO3401A", "C15127", "AOS AO3401A")
P_CLAMP = ("Diode:BAT54S", "Package_TO_SOT_SMD:SOT-23", "BAT54S", "C47546", "Nexperia BAT54S,215")
P_DAC = ("Analog_DAC:MCP4728", "Package_SO:MSOP-10_3x3mm_P0.5mm", "MCP4728-E/UN", "C108207", "Microchip MCP4728-E/UN")
P_ADC = ("Analog_ADC:ADS1115IDGS", "Package_SO:TSSOP-10_3x3mm_P0.5mm", "ADS1115IDGSR", "C37593", "TI ADS1115IDGSR")
P_OPA = ("Amplifier_Operational:TLV9062xD", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", "TLV9062IDR", "C398355",
         "TI TLV9062IDR")
P_CAN = ("Interface_CAN_LIN:TJA1042T-3", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", "TCAN1042HVDR", "C127869",
         "TI TCAN1042HVDR")   # pin-compatible symbol: TXD GND VCC RXD VIO CANL CANH STB
P_CMC = ("Filter:Choke_CommonMode_FerriteCore_1423", "lcsc:IND-SMD_4P-L4.5-W3.2-TL",
         "ACT45B-510", "C76584", "TDK ACT45B-510-2P-TL003")
P_CANESD = ("Power_Protection:NUP2105L", "Package_TO_SOT_SMD:SOT-23", "NUP2105L", "C14486", "onsemi NUP2105LT1G")
P_IDEAL = ("Power_Management:LM66100DCK", "Package_TO_SOT_SMD:SOT-363_SC-70-6", "LM66100DCKR", "C2869734",
           "TI LM66100DCKR")
P_WDT = ("Timer:TPL5010", "Package_TO_SOT_SMD:SOT-23-6", "TPL5010DDCR", "C473912", "TI TPL5010DDCR")
P_TVS = ("Device:D_Zener", "Diode_SMD:D_SMA", "SMAJ6.0A", "C223993", "Littelfuse SMAJ6.0A")
P_LED_G = ("Device:LED", "LED_SMD:LED_0603_1608Metric", "green", "C72043", "Everlight 19-217/GHC")
P_LED_R = ("Device:LED", "LED_SMD:LED_0603_1608Metric", "red", "C2286", "Hubei KENTO KT-0603R")
P_LED_B = ("Device:LED", "LED_SMD:LED_0603_1608Metric", "blue", "C72041", "Everlight 19-217/BHC")
P_SJ = ("Jumper:SolderJumper_2_Open", "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm", "SJ", "", "")
P_TP = ("Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", "TP", "", "")

R0603 = "Resistor_SMD:R_0603_1608Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
C0805 = "Capacitor_SMD:C_0805_2012Metric"
RES = {  # value -> (LCSC, MPN); all JLCPCB basic parts, 1 %
    "0R": ("C21189", "0603WAF0000T5E"),
    "100": ("C22775", "0603WAF1000T5E"),
    "1k": ("C21190", "0603WAF1001T5E"),
    "2.2k": ("C4190", "0603WAF2201T5E"),
    "3.3k": ("C22978", "0603WAF3301T5E"),
    "4.7k": ("C23162", "0603WAF4701T5E"),
    "6.8k": ("C23212", "0603WAF6801T5E"),
    "10k": ("C25804", "0603WAF1002T5E"),
    "15k": ("C22809", "0603WAF1502T5E"),
    "20k": ("C4184", "0603WAF2002T5E"),
    "47k": ("C25819", "0603WAF4702T5E"),
    "100k": ("C25803", "0603WAF1003T5E"),
    "1M": ("C22935", "0603WAF1004T5E"),
}
CAP = {  # value -> (footprint, LCSC, MPN)
    "100p": (C0603, "C14858", "CC0603JRNPO9BN101"),
    "10n/100V": (C0603, "C43253", "FH 0603B103K101NT"),
    "100n": (C0603, "C14663", "CC0603KRX7R9BB104"),
    "1u": (C0603, "C15849", "CL10A105KB8NNNC"),
    "4.7u": (C0805, "C1779", "CL21A475KAQNNNE"),
    "10u": (C0805, "C15850", "CL21A106KAYNNNE"),
}


# ---------------------------------------------------------------------------
#  Circuit container with automatic schematic placement
# ---------------------------------------------------------------------------

class Circuit:
    """Collects parts with schematic slot and board placement."""

    def __init__(self):
        self.parts = []
        self.blocks = []          # (title, x, y) for schematic headings
        self.notes = []           # (text, x, y)
        self._cur = None

    # -- schematic cursor: parts flow left to right inside a block ------------
    def block(self, title, x, y, width):
        self.blocks.append((title, x, y - 12))
        self._cur = {"x0": x, "x": x, "y": y, "w": width, "row_h": 0}

    def _slot(self, w, h):
        cur = self._cur
        if cur["x"] + w > cur["x0"] + cur["w"] and cur["x"] > cur["x0"]:
            cur["x"] = cur["x0"]
            cur["y"] += cur["row_h"]
            cur["row_h"] = 0
        at = (cur["x"] + w / 2.0, cur["y"] + h / 2.0)
        cur["x"] += w
        cur["row_h"] = max(cur["row_h"], h)
        return at

    def add(self, ref, part, nets, pcb, rot=0, dnp=False, value=None, in_bom=True, size=None, units=None,
            sch_rot=0):
        lib_id, fp, val, lcsc, mpn = part
        n = len(nets)
        if units:      # multi-unit symbol: one slot per unit
            placements = [(u, self._slot(*(size or (38, 30))), 0) for u in units]
            sch = None
        else:
            w, h = size or ((20, 22) if n <= 3 else (50, 36))
            sch = self._slot(w, h)
            placements = None
        self.parts.append(dict(ref=ref, lib_id=lib_id, footprint=fp, value=value or val, lcsc=lcsc, mpn=mpn,
                               nets=nets, sch=sch, sch_rot=sch_rot, units=placements, pcb=pcb, rot=rot,
                               dnp=dnp, in_bom=in_bom))

    def R(self, ref, value, a, b, pcb, rot=0, dnp=False):
        lcsc, mpn = RES[value]
        self.add(ref, ("Device:R", R0603, value + ("Ω" if value[-1].isdigit() else ""), lcsc, mpn),
                 {"1": a, "2": b}, pcb, rot, dnp=dnp, sch_rot=90)

    def C(self, ref, value, a, b, pcb, rot=0, dnp=False):
        fp, lcsc, mpn = CAP[value]
        self.add(ref, ("Device:C", fp, value.replace("/", "F/") if "/" in value else value + "F", lcsc, mpn),
                 {"1": a, "2": b}, pcb, rot, dnp=dnp, sch_rot=90)

    def TP(self, ref, net, pcb, label=None):
        self.add(ref, P_TP, {"1": net}, pcb, value=label or net, in_bom=False, size=(16, 16))

    def note(self, text, x, y):
        self.notes.append((text, x, y))


# ---------------------------------------------------------------------------
#  Board geometry (mm). Origin top-left, y down. Motor A on top, B mirrored below.
# ---------------------------------------------------------------------------
W, H = 100.0, 100.0
HOLES = ((3.5, 3.5), (W - 3.5, 3.5), (3.5, H - 3.5), (W - 3.5, H - 3.5))

# Hall connectors: J1 (motor) and J3 (driver) face each other, pins running down
# from the top edge, so the five passthrough conductors are straight parallel tracks.
X_MOT, X_DRV = 12.0, 36.0        # x of J1/J2 and J3/J4 pin rows
Y_HALL1 = 9.5                    # y of pin 1 (motor A); pins at +3 mm
PT_WIDTH = 0.8                   # passthrough track width (ICD: >= 0.5 mm)
X_CMD = 45.0                     # x of pin 1 of J5 along the top edge
Y_CMD = 4.6

# ESP32-DevKitC V4: rows 25.40 mm apart (P1 to confirm), antenna end at the right edge.
MOD_PIN1_X = 97.2                # pin 1 of both rows (antenna end)
MOD_ROW_TOP = 50.0 - 12.7        # Espressif J2 row (3V3 ... 5V)
MOD_ROW_BOT = 50.0 + 12.7        # Espressif J3 row (GND ... CLK)
NOTCH = (90.5, 40.6, 59.4)       # antenna cut-out: x start, y top, y bottom

# Trunk connectors J8/J9 on the left edge, pins running down.
X_TRUNK = (5.0, 12.5)
Y_TRUNK1 = 42.5


def my(y, m):
    """Mirror a y coordinate for motor B."""
    return y if m == "A" else H - y


def mrot(rot, m):
    return rot if m == "A" else (rot + 180) % 360


# ---------------------------------------------------------------------------
#  Circuit
# ---------------------------------------------------------------------------

def circuit() -> Circuit:
    c = Circuit()

    # ===================== ESP32 module (two socket rows) ====================
    c.block("MODULE ESP32-DevKitC V4 (MOTION) — supports 2 × 19, entraxe 25,40 mm (P1)", 30, 40, 200)
    # Espressif DevKitC V4 schematic (ESP32_DevKitc_V4, 2017-12-06) and user guide.
    # J2 (Espressif): 1 3V3 · 2 EN · 3 VP/IO36 · 4 VN/IO39 · 5 IO34 · 6 IO35 · 7 IO32 · 8 IO33 ·
    #                 9 IO25 · 10 IO26 · 11 IO27 · 12 IO14 · 13 IO12 · 14 GND · 15 IO13 ·
    #                 16 SD2/IO9 · 17 SD3/IO10 · 18 CMD/IO11 · 19 5V (EXT_5V, behind the module's BAT760)
    j2 = {"1": "+3V3", "2": "ESP_EN", "3": "HALL_C1", "4": "HALL_A2", "5": "HALL_A1", "6": "HALL_B1",
          "7": "HALL_B2", "8": "HALL_C2", "9": "DIR_1", "10": "BRAKE_RELEASE", "11": "STOP_1", "12": "DIR_2",
          "13": None,           # IO12 = MTDI strapping: never connected (C14)
          "14": "GND", "15": "WD_WAKE",
          "16": None, "17": None, "18": None,     # flash SPI: NC — FLASH
          "19": "+5V_MOD"}
    # J3 (Espressif): 1 GND · 2 IO23 · 3 IO22 · 4 TX/IO1 · 5 RX/IO3 · 6 IO21 · 7 GND (docs) / NC
    #                 (schematic) · 8 IO19 · 9 IO18 · 10 IO5 · 11 IO17 · 12 IO16 · 13 IO4 · 14 IO0 ·
    #                 15 IO2 · 16 IO15 · 17 SD1/IO8 · 18 SD0/IO7 · 19 CLK/IO6
    j3 = {"1": "GND", "2": "STOP_2", "3": "I2C_SCL", "4": None, "5": None, "6": "I2C_SDA",
          "7": None,            # GND in the user guide, unlabeled in the schematic: left open (P2)
          "8": "SAFE_N_IN", "9": "WD_DONE", "10": "CAN_TX",
          "11": None, "12": None,                 # IO17/IO16: reserve, PSRAM variant (P3)
          "13": "CAN_RX", "14": None, "15": None,  # IO0/IO2 strapping: NC
          "16": "LED_STATUS", "17": None, "18": None, "19": None}
    c.add("J10", P_SOCK, j2, pcb=(MOD_PIN1_X, MOD_ROW_TOP), rot=270, value="DevKitC J2 (3V3…5V)", size=(60, 60))
    c.add("J11", P_SOCK, j3, pcb=(MOD_PIN1_X, MOD_ROW_BOT), rot=270, value="DevKitC J3 (GND…CLK)", size=(60, 60))

    # ===================== Trunk: power and CAN ============================
    c.block("DORSALE — J8/J9 en parallèle, anti-inversion, TVS, diode idéale vers le module", 30, 120, 260)
    for ref, x in (("J8", X_TRUNK[0]), ("J9", X_TRUNK[1])):
        c.add(ref, P_MF6, {"1": "+5V_IN", "2": "CANH", "3": "CANL", "4": "SAFE_N", "5": "GND", "6": "SHIELD"},
              pcb=(x, Y_TRUNK1), rot=270, value="CAN_SAFE_" + ("A" if ref == "J8" else "B"), size=(40, 36))
    # Reverse polarity: P-MOSFET, drain on the input, source on the protected rail.
    c.add("Q1", P_PFET, {"1": "PFET_G", "2": "+5V", "3": "+5V_IN"}, pcb=(20.0, 41.0), rot=90)
    c.R("R1", "10k", "PFET_G", "GND", pcb=(20.0, 44.6), rot=0)
    c.add("D1", P_TVS, {"1": "+5V", "2": "GND"}, pcb=(25.6, 41.6), rot=90, sch_rot=90)
    c.C("C1", "10u", "+5V", "GND", pcb=(30.0, 40.2), rot=0)
    c.C("C2", "100n", "+5V", "GND", pcb=(30.0, 42.6), rot=0)
    c.R("R2", "1k", "+5V", "LED_5V", pcb=(33.6, 40.2), rot=0)
    c.add("D2", P_LED_G, {"1": "GND", "2": "LED_5V"}, pcb=(33.6, 42.6), rot=180, value="5V")
    # Ideal diode: trunk 5 V -> module 5 V pin. Blocks USB VBUS (through the DevKitC's
    # BAT760) from back-feeding the trunk and the board's 5 V loads. CE low = on.
    c.add("U1", P_IDEAL, {"1": "+5V", "2": "GND", "3": "GND", "4": None, "5": None, "6": "+5V_MOD"},
          pcb=(38.6, 41.2), rot=0)
    c.C("C3", "1u", "+5V", "GND", pcb=(38.6, 44.2), rot=0)
    c.C("C4", "10u", "+5V_MOD", "GND", pcb=(43.2, 40.2), rot=0)
    # 3.3 V comes from the DevKitC regulator (AMS1117 class, 1 A): board logic < 20 mA.
    c.C("C5", "10u", "+3V3", "GND", pcb=(43.2, 42.8), rot=0)
    c.R("R3", "1k", "+3V3", "LED_3V3", pcb=(47.0, 40.2), rot=0)
    c.add("D3", P_LED_G, {"1": "GND", "2": "LED_3V3"}, pcb=(47.0, 42.6), rot=180, value="3V3")

    c.block("CAN — TCAN1042HVDR, STB à la masse, VIO 3,3 V, pas de terminaison sur cette carte", 30, 200, 260)
    c.add("U2", P_CAN, {"1": "CAN_TX", "2": "GND", "3": "+5V", "4": "CAN_RX", "5": "+3V3", "6": "CANL_T",
                        "7": "CANH_T", "8": "GND"}, pcb=(27.0, 53.0), rot=90)
    c.R("R4", "10k", "+3V3", "CAN_TX", pcb=(33.2, 48.4), rot=0)     # GPIO5 strapping: high at boot
    c.C("C6", "4.7u", "+5V", "GND", pcb=(21.0, 49.0), rot=90)
    c.C("C7", "100n", "+5V", "GND", pcb=(23.4, 48.4), rot=90)
    c.C("C8", "100n", "+3V3", "GND", pcb=(30.6, 48.4), rot=90)
    # Choke: bus side 1/2, transceiver side 4/3 (TDK windings 1-4, 2-3).
    c.add("L1", P_CMC, {"1": "CANH", "2": "CANL", "4": "CANH_T", "3": "CANL_T"}, pcb=(20.2, 57.4), rot=90)
    c.add("D4", P_CANESD, {"1": "CANH", "2": "CANL", "3": "GND"}, pcb=(24.4, 60.2), rot=90)

    # ===================== /SAFE input ======================================
    c.block("/SAFE — résistance série (nœud éteint non rétro-alimenté), 1 MΩ local (ICD SAFE_N_spec)", 300, 120, 260)
    c.R("R5", "47k", "SAFE_N", "SAFE_N_IN", pcb=(33.8, 52.0), rot=90)
    c.R("R6", "1M", "SAFE_N_IN", "GND", pcb=(36.0, 52.0), rot=90)
    c.C("C9", "100p", "SAFE_N_IN", "GND", pcb=(38.2, 52.0), rot=90)
    # GPIO26 pull-down: GPIO26 floats during reset (TPL5010, D7) and when the module is out.
    c.R("R7", "100k", "BRAKE_RELEASE", "GND", pcb=(40.4, 52.0), rot=90)

    # ===================== Watchdog TPL5010 ================================
    c.block("WATCHDOG — TPL5010 : RSTn sur EN de l'ESP32 (D7), intervalle 2 s", 300, 200, 260)
    c.add("U3", P_WDT, {"1": "+3V3", "2": "GND", "3": "WD_DELAY", "4": "WD_DONE", "5": "WD_WAKE", "6": "ESP_EN"},
          pcb=(62.0, 57.0), rot=0)
    # TPL5010 SNAS651A table 3: 6.788 kΩ -> 2 s. 6.8 kΩ 1 % gives ~2.0 s.
    c.R("R8", "6.8k", "WD_DELAY", "GND", pcb=(58.0, 57.0), rot=90)
    c.R("R9", "100k", "WD_DONE", "GND", pcb=(65.8, 60.0), rot=0)   # no DONE edge while GPIO18 floats
    c.R("R10", "100k", "+3V3", "ESP_EN", pcb=(62.0, 60.0), rot=0)    # RSTn open drain: TI recommends 100k
    c.C("C10", "100n", "+3V3", "GND", pcb=(62.0, 54.0), rot=0)

    # ===================== I2C: DAC, op-amp, ADC ===========================
    c.block("CONSIGNE VR — MCP4728 en 3,3 V (VIH = 0,7 VDD), réf. interne 2,048 V, TLV9062 gain 2,5", 30, 280, 400)
    c.R("R11", "4.7k", "+3V3", "I2C_SDA", pcb=(56.0, 43.0), rot=90)
    c.R("R12", "4.7k", "+3V3", "I2C_SCL", pcb=(58.2, 43.0), rot=90)
    c.add("U4", P_DAC, {"1": "+3V3", "2": "I2C_SCL", "3": "I2C_SDA", "4": "GND", "5": None, "6": "DAC_A",
                        "7": "DAC_B", "8": None, "9": None, "10": "GND"}, pcb=(63.0, 44.0), rot=0)
    c.C("C11", "100n", "+3V3", "GND", pcb=(63.0, 47.4), rot=0)
    c.add("U5", P_OPA, {"1": "VR_A_O", "2": "VR_A_FB", "3": "DAC_A", "5": "DAC_B", "6": "VR_B_FB",
                        "7": "VR_B_O", "4": "GND", "8": "+5V"}, pcb=(72.0, 50.0), rot=0, units=(1, 2, 3))
    c.C("C12", "100n", "+5V", "GND", pcb=(72.0, 45.0), rot=0)
    for m, fb, o, dac, y in (("A", "VR_A_FB", "VR_A_O", "DAC_A", 43.6), ("B", "VR_B_FB", "VR_B_O", "DAC_B", 56.4)):
        i = 0 if m == "A" else 3
        # VR = 2.048 V x (1 + 15k/10k) = 5.12 V -> clips at ~4.98 V (TLV9062 20 mV from rail at 10 kΩ):
        # codes 0..~3980 are linear, which is all the PI loop needs.
        c.R("R%d" % (13 + i), "15k", o, fb, pcb=(77.0, y), rot=90)
        c.R("R%d" % (14 + i), "10k", fb, "GND", pcb=(79.2, y), rot=90)
        # Module out (DAC unpowered): non-inverting input held at 0 V -> VR = 0.
        c.R("R%d" % (15 + i), "100k", dac, "GND", pcb=(67.0, y), rot=90)

    c.block("MESURES — ADS1115 (0x48) : NTC A, NTC B, rôle, révision matérielle", 450, 280, 260)
    c.add("U6", P_ADC, {"1": "GND", "2": None, "3": "GND", "4": "NTC_A_ADC", "5": "NTC_B_ADC", "6": "ROLE",
                        "7": "HW_REV", "8": "+3V3", "9": "I2C_SDA", "10": "I2C_SCL"}, pcb=(84.0, 50.0), rot=0)
    c.C("C13", "100n", "+3V3", "GND", pcb=(84.0, 46.4), rot=0)
    c.C("C14", "100n", "NTC_A_ADC", "GND", pcb=(84.0, 43.0), rot=0)
    c.C("C15", "100n", "NTC_B_ADC", "GND", pcb=(84.0, 57.0), rot=0)
    # Role: SJ1 open = AVANT (0 V), SJ1 closed = ARRIÈRE (1/3), SJ2 closed = BANC (3V3).
    c.R("R19", "20k", "+3V3", "ROLE_X", pcb=(43.0, 61.2), rot=0)
    c.add("SJ1", P_SJ, {"1": "ROLE_X", "2": "ROLE"}, pcb=(43.0, 63.6), rot=0, value="ARRIERE", in_bom=False)
    c.R("R20", "10k", "ROLE", "GND", pcb=(46.6, 61.2), rot=0)
    c.add("SJ2", P_SJ, {"1": "ROLE", "2": "+3V3"}, pcb=(46.6, 63.6), rot=0, value="BANC", in_bom=False)
    c.C("C16", "100n", "ROLE", "GND", pcb=(80.0, 59.0), rot=0)
    # Hardware revision: ratio 1/2 = motor_interface v2.0 (table in decisions.md).
    c.R("R21", "10k", "+3V3", "HW_REV", pcb=(88.0, 43.0), rot=90)
    c.R("R22", "10k", "HW_REV", "GND", pcb=(88.0, 46.4), rot=90)
    c.C("C17", "100n", "HW_REV", "GND", pcb=(88.0, 57.0), rot=90)

    # ===================== Indicators =====================================
    c.block("VOYANTS — tampon tolérant 5 V : frein serré A/B (sur EL), /SAFE actif ; LED d'état GPIO15", 450, 360, 260)
    c.add("U7", P_BUF3, {"1": "EL_A_S", "7": "LED_EL_A", "6": "EL_B_S", "2": "LED_EL_B", "3": "SAFE_N_IN",
                         "5": "LED_SAFE", "4": "GND", "8": "+3V3"}, pcb=(42.0, 56.4), rot=0, units=(1, 2, 3, 4))
    c.C("C18", "100n", "+3V3", "GND", pcb=(42.0, 59.0), rot=0)
    c.R("R23", "1k", "LED_EL_A", "LED_EL_A_K", pcb=(46.4, 47.0), rot=0)
    c.add("D5", P_LED_R, {"1": "GND", "2": "LED_EL_A_K"}, pcb=(46.4, 49.0), rot=180, value="FREIN A")
    c.R("R24", "1k", "LED_EL_B", "LED_EL_B_K", pcb=(46.4, 51.4), rot=0)
    c.add("D6", P_LED_R, {"1": "GND", "2": "LED_EL_B_K"}, pcb=(46.4, 53.4), rot=180, value="FREIN B")
    c.R("R25", "1k", "+3V3", "LED_SAFE_A", pcb=(46.4, 55.8), rot=0)
    c.add("D7", P_LED_R, {"1": "LED_SAFE", "2": "LED_SAFE_A"}, pcb=(46.4, 57.8), rot=180, value="/SAFE")
    c.R("R26", "1k", "+3V3", "LED_STAT_A", pcb=(38.0, 61.2), rot=0)
    c.add("D8", P_LED_B, {"1": "LED_STATUS", "2": "LED_STAT_A"}, pcb=(38.0, 63.6), rot=180, value="ETAT")

    # ===================== Trunk test points ==============================
    for i, (net, lab) in enumerate((("+5V", "5V"), ("+3V3", "3V3"), ("GND", "GND"), ("CANH", "CANH"),
                                    ("CANL", "CANL"), ("SAFE_N", "/SAFE"))):
        c.TP("TP%d" % (1 + i), net, pcb=(73.0 + i * 3.6, 25.0), label=lab)

    # ===================== Per motor ======================================
    tp = 7
    for m in ("A", "B"):
        idx = "1" if m == "A" else "2"
        X = lambda v: v  # noqa: E731
        V5, GM = "+5V_MOT_" + m, "GND_MOT_" + m
        hall = ["M%s_H%s" % (m, k) for k in "ABC"]
        y1 = my(Y_HALL1, m)
        pin_rot = mrot(270, m)
        c.block("MOTEUR %s — passage Hall J%s→J%s métallique, prélèvement, commande J%s" %
                (m, "1" if m == "A" else "2", "3" if m == "A" else "4", "5" if m == "A" else "6"),
                30 if m == "A" else 300, 440, 260)
        jm, jd, jc = (("J1", "J3", "J5") if m == "A" else ("J2", "J4", "J6"))
        hall_pins = {"1": V5, "2": GM, "3": hall[0], "4": hall[1], "5": hall[2], "6": None}
        c.add(jm, P_MF6, hall_pins, pcb=(X_MOT, y1), rot=pin_rot, value="MOT_HALL_" + m, size=(40, 36))
        c.add(jd, P_MF6, dict(hall_pins), pcb=(X_DRV, y1), rot=pin_rot, value="CTRL_HALL_" + m, size=(40, 36))
        el, dr, st, vr, ntc = ("EL_" + m, "DIR_" + m, "STOP_" + m, "VR_" + m, "NTC_" + m)
        c.add(jc, P_MF8, {"1": vr, "2": dr, "3": el, "4": st, "5": GM, "6": ntc,
                          "7": None,   # was 5V_BRAKE: NC since D5 (13/11/2026)
                          "8": GM},
              pcb=(X_CMD, my(Y_CMD, m)) if m == "A" else (X_CMD + 21.0, my(Y_CMD, m)),
              rot=0 if m == "A" else 180, value="CTRL_CMD_" + m, size=(40, 40))

        # --- Hall tap, 3 lines ---------------------------------------------
        base = 0 if m == "A" else 50
        for k in range(3):
            n = base + k * 4
            bx = 3.6 + k * 7.4
            line, filt = hall[k], hall[k] + "_F"
            # (1) on-board pull-up: fitted by default, remove if HALL_OC shows push-pull outputs
            c.R("R%d" % (101 + n), "2.2k", V5, line, pcb=(bx, my(31.0, m)), rot=90)
            # (3) series resistor then the 10 nF: a shorted capacitor cannot kill the Hall line
            c.R("R%d" % (102 + n), "2.2k", line, filt, pcb=(bx + 2.4, my(31.0, m)), rot=90)
            c.C("C%d" % (101 + n), "10n/100V", filt, GM, pcb=(bx + 4.8, my(31.0, m)), rot=90)
            # (4) BAT54S: A1 (pin 1) to GND_MOT, K2 (pin 2) to 5V_MOT, common (pin 3) on the node
            c.add("D%d" % (101 + n), P_CLAMP, {"1": GM, "2": V5, "3": filt},
                  pcb=(bx + 2.4, my(35.0, m)), rot=mrot(0, m))
        # (5) Schmitt buffer, 3.3 V, Ioff: passthrough unaffected when unpowered
        o = ["HALL_A" + idx, "HALL_B" + idx, "HALL_C" + idx]
        c.add("U%d" % (10 if m == "A" else 11), P_BUF3,
              {"1": hall[0] + "_F", "7": o[0], "6": hall[1] + "_F", "2": o[1], "3": hall[2] + "_F", "5": o[2],
               "4": "GND", "8": "+3V3"}, pcb=(26.8, my(32.6, m)), rot=mrot(90, m), units=(1, 2, 3, 4))
        c.C("C%d" % (113 + (0 if m == "A" else 30)), "100n", "+3V3", "GND", pcb=(29.6, my(32.6, m)), rot=90)

        # --- Command stage -------------------------------------------------
        base = 0 if m == "A" else 30
        y0 = 14.0
        # DIR and STOP: open drain AO3400A + polarity options (not fitted):
        #   R_PU to the driver's 5 V if its input has no internal pull-up,
        #   R_DIRECT + R_PD (with Q removed) for a non-inverting 3.3 V push-pull drive.
        for j, (sig, gpio) in enumerate(((dr, "DIR_" + idx), (st, "STOP_" + idx))):
            n = base + j * 5
            x = 42.5 + j * 9.0
            c.add("Q%d" % (101 + n), P_NFET, {"1": gpio, "2": "GND", "3": sig}, pcb=(x, my(y0, m)),
                  rot=mrot(0, m))
            c.R("R%d" % (131 + n), "100k", gpio, "GND", pcb=(x, my(y0 + 3.6, m)), rot=0)
            c.R("R%d" % (132 + n), "4.7k", sig, V5, pcb=(x + 3.4, my(y0 - 1.0, m)), rot=90, dnp=True)
            c.R("R%d" % (133 + n), "10k", sig, GM, pcb=(x + 5.6, my(y0 - 1.0, m)), rot=90, dnp=True)
            c.R("R%d" % (134 + n), "1k", gpio, sig, pcb=(x + 4.5, my(y0 + 3.6, m)), rot=0, dnp=True)
        # EL: AND(GPIO26, /SAFE) -> AO3400A pulling EL low = brake released.
        # No option of any kind on EL: the pull-up is on the harness (D5).
        n = base
        c.add("U%d" % (12 if m == "A" else 13), P_AND,
              {"1": "BRAKE_RELEASE", "2": "SAFE_N_IN", "3": "GND", "4": "EL_%s_G" % m, "5": "+3V3"},
              pcb=(60.6, my(y0, m)), rot=mrot(0, m))
        c.C("C%d" % (115 + base), "100n", "+3V3", "GND", pcb=(60.6, my(y0 + 3.4, m)), rot=0)
        c.R("R%d" % (141 + n), "100k", "EL_%s_G" % m, "GND", pcb=(65.2, my(y0 + 3.4, m)), rot=0)
        c.add("Q%d" % (111 + base), P_NFET, {"1": "EL_%s_G" % m, "2": "GND", "3": el}, pcb=(65.2, my(y0, m)),
              rot=mrot(0, m))
        # Brake indicator input: 10k series, 1M to 3V3 (unplugged harness reads "brake applied",
        # which is what the driver does with its harness pull-up).
        c.R("R%d" % (142 + n), "10k", el, "EL_%s_S" % m, pcb=(68.4, my(y0 - 1.0, m)), rot=90)
        c.R("R%d" % (143 + n), "1M", "EL_%s_S" % m, "+3V3", pcb=(70.6, my(y0 - 1.0, m)), rot=90)
        # VR output: 100 Ω isolates the cable capacitance; 10k defines VR when the op-amp is off.
        c.R("R%d" % (144 + n), "100", "VR_%s_O" % m, vr, pcb=(74.0, my(y0 - 1.0, m)), rot=90)
        c.R("R%d" % (145 + n), "10k", vr, "GND", pcb=(76.2, my(y0 - 1.0, m)), rot=90)
        # NTC 10k B3950 on the driver heatsink, returned on GND_MOT: 3.3k pull-up centres the
        # divider near 60 °C; 1k + 100 nF filter and protect the ADS1115 input.
        c.R("R%d" % (146 + n), "3.3k", "+3V3", ntc, pcb=(79.6, my(y0 - 1.0, m)), rot=90)
        c.R("R%d" % (147 + n), "1k", ntc, "NTC_%s_ADC" % m, pcb=(81.8, my(y0 - 1.0, m)), rot=90)
        # Bench-only ground tie (NOT FITTED on the robot: D4).
        c.R("R%d" % (148 + n), "0R", GM, "GND", pcb=(86.0, my(y0 - 1.0, m)), rot=90, dnp=True)

        # --- Test points -----------------------------------------------------
        for net, lab, (x, y) in ((hall[0], "H%sA" % m, (17.6, 25.6)), (hall[1], "H%sB" % m, (20.8, 25.6)),
                                 (hall[2], "H%sC" % m, (24.0, 25.6)), (V5, "5VM" + m, (27.2, 25.6)),
                                 (GM, "GM" + m, (30.4, 25.6)), (el, "EL" + m, (68.0, 19.0)),
                                 (vr, "VR" + m, (72.0, 19.0))):
            c.TP("TP%d" % tp, net, pcb=(x, my(y, m)), label=lab)
            tp += 1
    return c


# ---------------------------------------------------------------------------
#  Schematic
# ---------------------------------------------------------------------------

def fields_of(p):
    f = {}
    if p["lcsc"]:
        f["LCSC"] = p["lcsc"]
    if p["mpn"]:
        f["MPN"] = p["mpn"]
    return f


def build_sch(c: Circuit):
    s = K.Schematic(PROJECT, "Retriever — motor_interface (2 moteurs)", paper="A1", rev=REV, date=DATE,
                    company="Retriever, open hardware (CERN-OHL-S-2.0)",
                    comments=(STATUS,
                              "Généré par scripts/build.py — ne pas éditer à la main",
                              "Décisions : hardware/pcb/motor_interface/decisions.md",
                              "Masses : GND (logique), GND_MOT_A, GND_MOT_B — jamais reliées sur cette carte (D4)"),
                    extra_lib_dirs=(LIB_DIR,))
    for p in c.parts:
        if p["units"]:
            G.add_units(s, p["ref"], p["lib_id"], p["value"], p["footprint"], p["units"], p["nets"],
                        fields=fields_of(p), dnp=p["dnp"], in_bom=p["in_bom"])
        else:
            s.add(p["ref"], p["lib_id"], p["value"], p["footprint"], p["sch"], rot=p["sch_rot"],
                  nets=p["nets"], fields=fields_of(p), dnp=p["dnp"], in_bom=p["in_bom"])
    for i, net in enumerate(("+5V", "GND", "+3V3")):
        s.power_flag(net, (300 + i * 15, 40))
    for title, x, y in c.blocks:
        s.text(title, (x, y), 2.2, True)
    notes = [
        STATUS,
        "J7 (alimentation séparée) supprimé : 5 V par la dorsale uniquement (broche 1 de J8/J9).",
        "J5/J6 broche 7 : NC (D5). Le pull-up 2,2 kΩ de EL vers 5V_BRAKE est SUR LE FAISCEAU, côté variateur.",
        "Aucune option de peuplement sur EL. Options DIR/STOP non montées : R_PU (4,7k), R_PD (10k), R_DIRECT (1k).",
        "R148/R178 (0 Ω GND_MOT–GND) : NON MONTÉES. Banc seulement, jamais sur le robot (D4).",
        "Tampons Hall : SN74LVC3G17 uniquement (Ioff). Interdits : 74HC14, 74HCT14, SN74LVC14A.",
        "MCP4728 : programmer l'EEPROM à 0 en production (VR = 0 V dès la mise sous tension).",
        "Rôle (ADS1115 AIN2) : SJ1 ouvert = AVANT, SJ1 fermé = ARRIÈRE, SJ2 fermé = BANC.",
    ]
    for i, t in enumerate(notes):
        s.text(t, (580, 40 + i * 6), 2.0)
    s.write(os.path.join(KICAD_DIR, PROJECT + ".kicad_sch"))
    with open(os.path.join(KICAD_DIR, "sym-lib-table"), "w") as f:
        f.write("(sym_lib_table\n\t(version 7)\n)\n")
    with open(os.path.join(KICAD_DIR, "fp-lib-table"), "w") as f:
        f.write('(fp_lib_table\n\t(version 7)\n\t(lib (name "lcsc") (type "KiCad") '
                '(uri "${KIPRJMOD}/lib/lcsc.pretty") (options "") (descr "Pièces LCSC importées"))\n)\n')
    return s


# ---------------------------------------------------------------------------
#  Board
# ---------------------------------------------------------------------------

NETCLASSES = [
    # 0.15 mm clearance: VSSOP-8 / MSOP-10 / TSSOP-10 at 0.5 mm pitch.
    {"name": "Default", "track": 0.25, "clearance": 0.15, "via": 0.7},
    # Supplies and returns. 0.4 mm on 1 oz carries ~1.2 A (IPC-2152), above the 0.95 A
    # branch limit of safety_bus_distribution.
    {"name": "Power", "track": 0.4, "clearance": 0.15, "via": 0.7, "patterns": ["/+5V*", "/GND*", "/+3V3"]},
    # Hall lines: the passthrough itself is drawn at 0.8 mm by this script; stubs at 0.3 mm.
    {"name": "Hall", "track": 0.3, "clearance": 0.15, "via": 0.7, "patterns": ["/MA_H*", "/MB_H*"]},
    {"name": "CAN", "track": 0.25, "clearance": 0.15, "via": 0.7, "patterns": ["/CAN*", "/SAFE_N*"]},
]


def board_outline():
    """Rectangle with chamfered corners and the antenna notch on the right edge."""
    ch = 2.0
    x0, y0 = NOTCH[0], NOTCH[1]
    y1 = NOTCH[2]
    return [(ch, 0), (W - ch, 0), (W, ch), (W, y0), (x0, y0), (x0, y1), (W, y1), (W, H - ch),
            (W - ch, H), (ch, H), (0, H - ch), (0, ch)]


def build_pcb(c: Circuit, sch_uuids: dict, nc_pins: dict):
    import pcbnew as Pn
    import kicadpcb as KP

    b = KP.Board(os.path.join(KICAD_DIR, PROJECT + ".kicad_pcb"), copper_layers=2, extra_fp_dirs=(LIB_DIR,))
    # Placed and routed as a 2-layer board; the two inner planes are added after routing
    # (add_zones), so Freerouting keeps every signal on F.Cu and B.Cu.
    # JLCPCB 4-layer capabilities with margin: 0.09 mm track/space min, 0.2 mm drill.
    b.rules(track=0.15, clearance=0.15, via=0.6, drill=0.3, annular=0.13, edge_clearance=0.3)
    for nc in NETCLASSES:
        b.netclass(nc["name"], nc["track"], nc["clearance"], nc.get("via", 0.6), nc.get("drill", 0.3),
                   nc.get("patterns", []))

    for p in c.parts:
        info = {"footprint": p["footprint"], "value": p["value"], "uuid": sch_uuids[p["ref"]],
                "fields": fields_of(p), "dnp": p["dnp"], "in_bom": p["in_bom"], "nets": p["nets"],
                "nc": nc_pins[p["ref"]]}
        b.place(p["ref"], info, p["pcb"][0], p["pcb"][1], p["rot"])

    G.outline_poly(b, board_outline())
    for i, (x, y) in enumerate(HOLES):
        b.hole("H%d" % (i + 1), x, y, name="MountingHole_3.2mm_M3", net=None)

    # Hall passthrough, fixed before routing: pin k of the motor connector straight to pin k
    # of the driver connector, one layer, no via, no component in series.
    for m in ("A", "B"):
        nets = ["+5V_MOT_" + m, "GND_MOT_" + m] + ["M%s_H%s" % (m, k) for k in "ABC"]
        for k, net in enumerate(nets):
            y = my(Y_HALL1, m) + (3.0 * k if m == "A" else -3.0 * k)
            b.track(net, [(X_MOT, y), (X_DRV, y)], PT_WIDTH, Pn.F_Cu)
    for t in b.b.GetTracks():
        t.SetLocked(True)

    # Keep tracks and vias 0.5 mm away from the antenna notch (Freerouting only sees the
    # outline itself, not the 0.3 mm edge clearance on inner corners).
    ka = Pn.ZONE(b.b)
    ka.SetIsRuleArea(True)
    ka.SetDoNotAllowTracks(True)
    ka.SetDoNotAllowVias(True)
    ka.SetDoNotAllowPads(False)
    ka.SetDoNotAllowFootprints(False)
    ka.SetDoNotAllowZoneFills(False)
    ls = Pn.LSET()
    ls.AddLayer(Pn.F_Cu)
    ls.AddLayer(Pn.B_Cu)
    ka.SetLayerSet(ls)
    ka.SetZoneName("antenna_notch_keepout")
    o = ka.Outline()
    o.NewOutline()
    for x, y in ((NOTCH[0] - 0.6, NOTCH[1] - 0.6), (W, NOTCH[1] - 0.6), (W, NOTCH[2] + 0.6),
                 (NOTCH[0] - 0.6, NOTCH[2] + 0.6)):
        o.Append(KP.mm(x), KP.mm(y))
    b.b.Add(ka)
    silk(b, c)
    return b


def silk(b, c=None):
    t = b.text
    t("RETRIEVER motor_interface v%s" % REV, 70.0, 30.0, 1.1)
    t("NE PAS FABRIQUER avant M7, HALL_OC, P1, P2, P3", 70.0, 32.2, 0.8)
    t("ROLE AVANT/ARRIERE : SJ1 ouvert = AVANT, SJ1 ferme = ARRIERE, SJ2 = BANC", 33.0, 67.6, 0.8,
      justify="left")
    # module orientation
    t("DevKitC V4 - USB ici", 53.6, 50.0, 0.9, rot=90)
    t("ANTENNE", 95.0, 50.0, 0.9, rot=90)
    t("1", MOD_PIN1_X + 2.0, MOD_ROW_TOP - 2.0, 0.9)
    t("1", MOD_PIN1_X + 2.0, MOD_ROW_BOT + 2.0, 0.9)
    t("NC - FLASH", MOD_PIN1_X - 45.72 + 6.35, MOD_ROW_TOP - 2.6, 0.8)
    t("NC - FLASH", MOD_PIN1_X - 45.72 + 2.54, MOD_ROW_BOT + 2.6, 0.8)
    for m in ("A", "B"):
        jm, jd, jc = (("J1", "J3", "J5") if m == "A" else ("J2", "J4", "J6"))
        t("%s MOTEUR %s" % (jm, m), X_MOT, my(2.4, m), 0.9)
        t("%s VARIATEUR %s" % (jd, m), X_DRV, my(2.4, m), 0.9)
        t("%s COMMANDE %s : 1 VR 2 DIR 3 EL 4 STOP 5 GND 6 NTC 7 NC 8 GND" % (jc, m), X_CMD - 4.0,
          my(9.9, m), 0.8, justify="left")
        for k, lab in enumerate(("5V", "GND", "HA", "HB", "HC")):
            y = my(Y_HALL1, m) + (3.0 * k + 1.5 if m == "A" else -3.0 * k - 1.5)
            t(lab, (X_MOT + X_DRV) / 2, y, 0.8)
        t("BANC SEUL", 86.0, my(16.6, m), 0.8)
    t("J8   J9", 8.8, 37.9, 0.8)
    t("DORSALE 1 5V 2 CANH 3 CANL 4 /SAFE 5 GND 6 SHLD", 3.0, 62.4, 0.8, justify="left")
    # test point names, never numbers (spec Z.6)
    for p in (c.parts if c else []):
        if p["lib_id"] == "Connector:TestPoint":
            x, y = p["pcb"]
            t(p["value"], x, y + (2.0 if y < H / 2 else -2.0), 0.8)
    for x, y, lab in ((33.6, 44.5, "5V"), (47.0, 44.5, "3V3"), (38.0, 65.4, "ETAT")):
        t(lab, x, y, 0.8)
    for y, lab in ((49.0, "FREIN A"), (53.4, "FREIN B"), (57.8, "/SAFE")):
        t(lab, 47.9, y, 0.8, justify="left")


def add_zones(b):
    """Planes, added AFTER routing so the router draws every connection."""
    import pcbnew as Pn
    full = board_outline()
    band_a = [(0, 0), (39.0, 0), (39.0, 38.0), (0, 38.0)]
    band_b = [(x, H - y) for x, y in band_a]
    left_logic = [(0, 38.0), (51.0, 38.0), (51.0, 62.0), (0, 62.0)]
    for layer, name in ((Pn.F_Cu, "F"), (Pn.In1_Cu, "In1"), (Pn.B_Cu, "B")):
        b.zone("GND", layer, full, priority=0, name="GND_" + name)
        b.zone("GND_MOT_A", layer, band_a, priority=1, name="GMA_" + name)
        b.zone("GND_MOT_B", layer, band_b, priority=1, name="GMB_" + name)
    b.zone("+3V3", Pn.In2_Cu, full, priority=0, name="3V3_In2")
    b.zone("+5V", Pn.In2_Cu, left_logic, priority=1, name="5V_In2")
    b.zone("GND_MOT_A", Pn.In2_Cu, band_a, priority=1, name="GMA_In2")
    b.zone("GND_MOT_B", Pn.In2_Cu, band_b, priority=1, name="GMB_In2")


def main():
    what = sys.argv[1] if len(sys.argv) > 1 else "sch"
    os.makedirs(KICAD_DIR, exist_ok=True)
    pcb_path = os.path.join(KICAD_DIR, PROJECT + ".kicad_pcb")
    if what == "route":
        import pcbnew as Pn
        import kicadpcb as KP
        b = KP.Board(pcb_path, load=True, extra_fp_dirs=(LIB_DIR,))
        work = os.path.join(BOARD_DIR, "build")
        os.makedirs(work, exist_ok=True)
        print(b.autoroute(work, passes=int(os.environ.get("PASSES", "40"))))
        print("widened", b.widen_tracks(0.15), "necked tracks")
        b.b.SetCopperLayerCount(4)
        b.b.SetLayerType(Pn.In1_Cu, Pn.LT_POWER)
        b.b.SetLayerType(Pn.In2_Cu, Pn.LT_POWER)
        add_zones(b)
        b.save()
        print("ok: route")
        return
    c = circuit()
    s = build_sch(c)
    uuids = {ref: info["uuid"] for ref, info in s.symbols.items()}
    # KiCad escapes "/" in pin names of unconnected nets as "{slash}".
    nc = {ref: {k: v.replace("/", "{slash}") for k, v in info["nc"].items()} for ref, info in s.symbols.items()}
    K.write_project(os.path.join(KICAD_DIR, PROJECT + ".kicad_pro"), NETCLASSES, {})
    if what == "pcb":
        b = build_pcb(c, uuids, nc)
        b.save()
    print("ok:", what, len(c.parts), "parts")


if __name__ == "__main__":
    main()
