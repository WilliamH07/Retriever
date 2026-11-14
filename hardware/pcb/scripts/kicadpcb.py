"""kicadpcb — build a KiCad board from the same description as the schematic.

Run with KiCad's bundled Python (it provides `pcbnew`):
    /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3

Each footprint is linked to its schematic symbol by UUID, so KiCad's
"schematic parity" DRC check confirms the board matches the schematic.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from typing import Dict, Iterable, List, Optional, Tuple

import pcbnew as P

from kicadgen import FP_DIR

JAVA = os.environ.get("JAVA", "/opt/homebrew/opt/openjdk/bin/java")
FREEROUTING = os.environ.get(
    "FREEROUTING", os.path.expanduser("~/.local/share/freerouting/freerouting-2.5.0.jar")
)


def mm(v: float) -> int:
    return P.FromMM(v)


def pt(x: float, y: float):
    return P.VECTOR2I(mm(x), mm(y))


class Board:
    def __init__(self, path: str, copper_layers: int = 2, extra_fp_dirs: Tuple[str, ...] = (),
                 load: bool = False):
        self.path = path
        if load:
            self.b = P.LoadBoard(path)
        else:
            self.b = P.NewBoard(path)
            self.b.SetCopperLayerCount(copper_layers)
        self.extra = extra_fp_dirs
        self._nets: Dict[str, P.NETINFO_ITEM] = {}
        self.fps: Dict[str, P.FOOTPRINT] = {}

    # -- rules ---------------------------------------------------------------
    def rules(self, track=0.2, clearance=0.2, via=0.6, drill=0.3, annular=0.13,
              hole_clearance=0.25, edge_clearance=0.3, hole_to_hole=0.5,
              silk_text=0.8, silk_thickness=0.15):
        ds = self.b.GetDesignSettings()
        ds.m_TrackMinWidth = mm(track)
        ds.m_MinClearance = mm(clearance)
        ds.m_ViasMinSize = mm(via)
        ds.m_MinThroughDrill = mm(drill)
        ds.m_ViasMinAnnularWidth = mm(annular)
        ds.m_HoleClearance = mm(hole_clearance)
        ds.m_CopperEdgeClearance = mm(edge_clearance)
        ds.m_HoleToHoleMin = mm(hole_to_hole)
        ds.m_MinSilkTextHeight = mm(silk_text)
        ds.m_MinSilkTextThickness = mm(silk_thickness)

    def netclass(self, name: str, track: float, clearance: float, via: float = 0.6,
                 drill: float = 0.3, patterns: Iterable[str] = ()):
        ns = self.b.GetDesignSettings().m_NetSettings
        if name == "Default":
            nc = ns.GetDefaultNetclass()
        else:
            nc = P.NETCLASS(name)
        nc.SetTrackWidth(mm(track))
        nc.SetClearance(mm(clearance))
        nc.SetViaDiameter(mm(via))
        nc.SetViaDrill(mm(drill))
        if name != "Default":
            ns.SetNetclass(name, nc)
        for pat in patterns:
            ns.SetNetclassPatternAssignment(pat, name)

    # -- nets and footprints -------------------------------------------------
    def net(self, name: str, raw: bool = False) -> P.NETINFO_ITEM:
        # Local schematic labels on the root sheet are named "/<label>".
        if not raw and not name.startswith("/"):
            name = "/" + name
        if name not in self._nets:
            ni = P.NETINFO_ITEM(self.b, name)
            self.b.Add(ni)
            self._nets[name] = ni
        return self._nets[name]

    def _fp_lib(self, lib: str) -> str:
        for d in self.extra + (FP_DIR,):
            p = os.path.join(d, lib + ".pretty")
            if os.path.isdir(p):
                return p
        raise FileNotFoundError(lib + ".pretty")

    def place(self, ref: str, info: dict, x: float, y: float, rot: float = 0, back: bool = False):
        lib, name = info["footprint"].split(":", 1)
        fp = P.FootprintLoad(self._fp_lib(lib), name)
        if fp is None:
            raise FileNotFoundError(info["footprint"])
        fp.SetFPID(P.LIB_ID(lib, name))
        fp.SetReference(ref)
        fp.SetValue(info["value"])
        fp.SetPath(P.KIID_PATH("/" + info["uuid"]))
        fp.SetSheetname("")
        fp.SetSheetfile("")
        for k, v in info["fields"].items():
            if k not in ("Datasheet",) and v:
                fp.SetField(k, v)
                fld = fp.GetField(k)
                if fld is not None:
                    fld.SetVisible(False)
        fp.Value().SetVisible(False)
        # References go to the fabrication layer (assembly drawing), not the
        # silkscreen: on a dense board they would sit on pads and each other.
        ref_txt = fp.Reference()
        ref_txt.SetLayer(P.F_Fab if not back else P.B_Fab)
        ref_txt.SetTextSize(P.VECTOR2I(mm(0.8), mm(0.8)))
        ref_txt.SetTextThickness(mm(0.12))
        fp.SetDNP(bool(info["dnp"]))
        if not info["in_bom"]:
            fp.SetExcludedFromBOM(True)
        self.b.Add(fp)
        fp.SetPosition(pt(x, y))
        if back:
            fp.Flip(fp.GetPosition(), P.FLIP_DIRECTION_TOP_BOTTOM)
        fp.SetOrientationDegrees(rot)
        nets = info["nets"]
        for pad in fp.Pads():
            num = pad.GetNumber()
            if num in nets and nets[num]:
                pad.SetNet(self.net(nets[num]))
            elif num in info.get("nc", {}):
                pad.SetNet(self.net(info["nc"][num], raw=True))
        self.fps[ref] = fp
        return fp

    def hole(self, ref: str, x: float, y: float, name: str = "MountingHole_3.2mm_M3_Pad_Via",
             net: Optional[str] = None):
        fp = P.FootprintLoad(self._fp_lib("MountingHole"), name)
        fp.SetFPID(P.LIB_ID("MountingHole", name))
        fp.SetReference(ref)
        fp.SetValue("M3")
        fp.SetBoardOnly(True)
        fp.SetExcludedFromBOM(True)
        fp.SetExcludedFromPosFiles(True)
        self.b.Add(fp)
        fp.SetPosition(pt(x, y))
        if net:
            for pad in fp.Pads():
                pad.SetNet(self.net(net))
        fp.Reference().SetVisible(False)
        return fp

    # -- geometry -------------------------------------------------------------
    def _seg(self, a, b, layer, width):
        s = P.PCB_SHAPE(self.b)
        s.SetShape(P.SHAPE_T_SEGMENT)
        s.SetStart(pt(*a))
        s.SetEnd(pt(*b))
        s.SetLayer(layer)
        s.SetWidth(mm(width))
        self.b.Add(s)

    def _arc(self, center, start, end, layer, width):
        s = P.PCB_SHAPE(self.b)
        s.SetShape(P.SHAPE_T_ARC)
        s.SetCenter(pt(*center))
        s.SetStart(pt(*start))
        s.SetEnd(pt(*end))
        s.SetLayer(layer)
        s.SetWidth(mm(width))
        self.b.Add(s)

    def outline(self, x0, y0, x1, y1, r=3.0, width=0.1):
        L = P.Edge_Cuts
        self._seg((x0 + r, y0), (x1 - r, y0), L, width)
        self._seg((x1, y0 + r), (x1, y1 - r), L, width)
        self._seg((x1 - r, y1), (x0 + r, y1), L, width)
        self._seg((x0, y1 - r), (x0, y0 + r), L, width)
        self._arc((x1 - r, y0 + r), (x1 - r, y0), (x1, y0 + r), L, width)
        self._arc((x1 - r, y1 - r), (x1, y1 - r), (x1 - r, y1), L, width)
        self._arc((x0 + r, y1 - r), (x0 + r, y1), (x0, y1 - r), L, width)
        self._arc((x0 + r, y0 + r), (x0, y0 + r), (x0 + r, y0), L, width)
        self.bbox = (x0, y0, x1, y1)

    def zone(self, net: str, layer, poly: List[Tuple[float, float]], priority: int = 0,
             clearance: float = 0.3, min_width: float = 0.25, thermal_gap: float = 0.4,
             spoke: float = 0.5, name: str = ""):
        z = P.ZONE(self.b)
        z.SetLayer(layer)
        z.SetNet(self.net(net))
        z.SetAssignedPriority(priority)
        z.SetLocalClearance(mm(clearance))
        z.SetMinThickness(mm(min_width))
        z.SetThermalReliefGap(mm(thermal_gap))
        z.SetThermalReliefSpokeWidth(mm(spoke))
        z.SetPadConnection(P.ZONE_CONNECTION_FULL)
        if name:
            z.SetZoneName(name)
        o = z.Outline()
        o.NewOutline()
        for x, y in poly:
            o.Append(mm(x), mm(y))
        self.b.Add(z)
        return z

    def text(self, s: str, x: float, y: float, size: float = 1.0, layer=None,
             rot: float = 0, thickness: Optional[float] = None, justify: str = "center"):
        t = P.PCB_TEXT(self.b)
        t.SetText(s)
        t.SetLayer(P.F_SilkS if layer is None else layer)
        t.SetPosition(pt(x, y))
        t.SetTextSize(P.VECTOR2I(mm(size), mm(size)))
        t.SetTextThickness(mm(thickness if thickness else max(0.15, size * 0.15)))
        t.SetTextAngleDegrees(rot)
        if justify == "left":
            t.SetHorizJustify(P.GR_TEXT_H_ALIGN_LEFT)
        elif justify == "right":
            t.SetHorizJustify(P.GR_TEXT_H_ALIGN_RIGHT)
        self.b.Add(t)
        return t

    def track(self, net: str, points: List[Tuple[float, float]], width: float, layer=None):
        layer = P.F_Cu if layer is None else layer
        for a, b in zip(points, points[1:]):
            t = P.PCB_TRACK(self.b)
            t.SetStart(pt(*a))
            t.SetEnd(pt(*b))
            t.SetWidth(mm(width))
            t.SetLayer(layer)
            t.SetNet(self.net(net))
            self.b.Add(t)

    # -- output ---------------------------------------------------------------
    def fill(self):
        self.b.BuildConnectivity()
        P.ZONE_FILLER(self.b).Fill(self.b.Zones())

    def widen_tracks(self, minimum: float):
        """Freerouting necks tracks down near pads; bring them back to the fab minimum."""
        n = 0
        for t in self.b.GetTracks():
            if t.GetClass() == "PCB_TRACK" and t.GetWidth() < mm(minimum):
                t.SetWidth(mm(minimum))
                n += 1
        return n

    def save(self, path: Optional[str] = None):
        P.SaveBoard(path or self.path, self.b)

    def autoroute(self, workdir: str, passes: int = 30, threads: int = 4) -> str:
        """Specctra round trip through Freerouting. Returns the router log tail."""
        dsn = os.path.join(workdir, "board.dsn")
        ses = os.path.join(workdir, "board.ses")
        for f in (dsn, ses):
            if os.path.exists(f):
                os.remove(f)
        if not P.ExportSpecctraDSN(self.b, dsn):
            raise RuntimeError("DSN export failed")
        cmd = [JAVA, "-jar", FREEROUTING, "-de", dsn, "-do", ses, "-mp", str(passes),
               "-mt", str(threads), "--gui.enabled=false"]
        r = subprocess.run(cmd, capture_output=True, text=True)
        log = (r.stdout + r.stderr).splitlines()
        if not os.path.exists(ses):
            raise RuntimeError("Freerouting produced no session:\n" + "\n".join(log[-20:]))
        if not P.ImportSpecctraSES(self.b, ses):
            raise RuntimeError("SES import failed")
        return "\n".join(l for l in log if "unrouted" in l or "COMPLETED" in l or "score" in l)[-2000:]
