"""kicadgen — build KiCad schematics and boards from one Python description.

One circuit description (components, footprints, pin-to-net map, placement)
produces both the schematic and the board, so the two cannot drift apart.
The schematic part runs on any Python 3; the board part needs KiCad's
`pcbnew` module, so run board scripts with KiCad's bundled Python.

Schematic style: every pin gets a short net label at its connection point
instead of drawn wires. It reads like a netlist laid out in blocks — correct
and checkable by ERC, less elegant than a hand-drawn sheet.

Written for KiCad 10. Python 3.9 compatible (KiCad's bundled interpreter).
"""

from __future__ import annotations

import math
import os
import re
import uuid as _uuid
from typing import Dict, List, Optional, Tuple

KICAD_SHARE = os.environ.get(
    "KICAD_SHARE", "/Applications/KiCad/KiCad.app/Contents/SharedSupport"
)
SYM_DIR = os.path.join(KICAD_SHARE, "symbols")
FP_DIR = os.path.join(KICAD_SHARE, "footprints")


# --------------------------------------------------------------------------
#  S-expressions
# --------------------------------------------------------------------------

class QStr(str):
    """A quoted string atom (as opposed to a bare symbol)."""


_TOKEN = re.compile(r'\s*(?:(\()|(\))|"((?:[^"\\]|\\.)*)"|([^\s()"]+))', re.S)


def parse(text: str):
    stack: List[list] = [[]]
    for m in _TOKEN.finditer(text):
        lp, rp, qs, atom = m.groups()
        if lp:
            stack.append([])
        elif rp:
            node = stack.pop()
            stack[-1].append(node)
        elif qs is not None:
            stack[-1].append(QStr(qs.replace('\\"', '"').replace("\\\\", "\\")))
        elif atom is not None:
            stack[-1].append(atom)
    return stack[0][0]


def _atom(a) -> str:
    if isinstance(a, QStr):
        return '"' + a.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if isinstance(a, float):
        s = ("%.4f" % a).rstrip("0").rstrip(".")
        return "0" if s in ("-0", "") else s
    return str(a)


def dump(node, depth: int = 0) -> str:
    if not isinstance(node, list):
        return _atom(node)
    if all(not isinstance(c, list) for c in node):
        return "(" + " ".join(_atom(c) for c in node) + ")"
    tab = "\t" * (depth + 1)
    head = [c for c in node if not isinstance(c, list)]
    out = "(" + " ".join(_atom(c) for c in head)
    for c in node:
        if isinstance(c, list):
            out += "\n" + tab + dump(c, depth + 1)
    return out + "\n" + "\t" * depth + ")"


def find(node, key):
    for c in node:
        if isinstance(c, list) and c and c[0] == key:
            return c
    return None


def find_all(node, key):
    return [c for c in node if isinstance(c, list) and c and c[0] == key]


_NS = _uuid.UUID("6f1c3c2e-7c55-4a0b-9e7e-52657472696e")  # "Retriever" namespace


def uid(seed: Optional[str] = None) -> str:
    """Deterministic UUID when seeded, so regenerating keeps schematic/board links."""
    return str(_uuid.uuid5(_NS, seed)) if seed else str(_uuid.uuid4())


def S(*items):
    return list(items)


def Q(s) -> QStr:
    return QStr(str(s))


# --------------------------------------------------------------------------
#  Symbol libraries
# --------------------------------------------------------------------------

_lib_cache: Dict[str, list] = {}


def _load_lib(path: str) -> list:
    if path not in _lib_cache:
        with open(path, encoding="utf-8") as f:
            _lib_cache[path] = parse(f.read())
    return _lib_cache[path]


def _lib_path(lib: str, extra_dirs: Tuple[str, ...]) -> str:
    for d in extra_dirs + (SYM_DIR,):
        p = os.path.join(d, lib + ".kicad_sym")
        if os.path.exists(p):
            return p
    raise FileNotFoundError("symbol library %s.kicad_sym not found" % lib)


def _raw_symbol(lib_node, name):
    for s in find_all(lib_node, "symbol"):
        if s[1] == name:
            return s
    raise KeyError(name)


def _rename_units(node, old: str, new: str):
    for c in node:
        if isinstance(c, list) and c and c[0] == "symbol" and isinstance(c[1], str):
            if c[1].startswith(old + "_"):
                c[1] = QStr(new + c[1][len(old):])


def library_symbol(lib_id: str, extra_dirs: Tuple[str, ...] = ()) -> list:
    """Return a flattened copy of a library symbol, named `Lib:Name`."""
    import copy

    lib, name = lib_id.split(":", 1)
    lib_node = _load_lib(_lib_path(lib, extra_dirs))
    raw = _raw_symbol(lib_node, name)
    ext = find(raw, "extends")
    if ext:
        parent = copy.deepcopy(_raw_symbol(lib_node, ext[1]))
        _rename_units(parent, ext[1], name)
        props = {p[1]: p for p in find_all(raw, "property")}
        merged = []
        for c in parent:
            if isinstance(c, list) and c and c[0] == "property" and c[1] in props:
                merged.append(copy.deepcopy(props.pop(c[1])))
            else:
                merged.append(c)
        # properties only present on the child
        insert_at = max(i for i, c in enumerate(merged) if isinstance(c, list) and c[:1] == ["property"]) + 1
        for p in props.values():
            merged.insert(insert_at, copy.deepcopy(p))
        sym = merged
    else:
        sym = copy.deepcopy(raw)
    sym[1] = QStr(lib_id)
    return sym


def symbol_pins(sym: list) -> Dict[str, dict]:
    """Pins of unit 1 (plus common unit 0): number -> geometry."""
    pins = {}
    for unit in find_all(sym, "symbol"):
        m = re.search(r"_(\d+)_(\d+)$", unit[1])
        if m and m.group(1) not in ("0", "1"):
            continue
        for p in find_all(unit, "pin"):
            at = find(p, "at")
            num = find(p, "number")[1]
            name = find(p, "name")[1]
            pins[str(num)] = {
                "x": float(at[1]), "y": float(at[2]),
                "angle": float(at[3]) if len(at) > 3 else 0.0,
                "type": p[1], "name": str(name),
            }
    return pins


# --------------------------------------------------------------------------
#  Schematic
# --------------------------------------------------------------------------

def _rot(x: float, y: float, deg: float) -> Tuple[float, float]:
    r = math.radians(deg)
    return (x * math.cos(r) - y * math.sin(r), x * math.sin(r) + y * math.cos(r))


def _snap(v: float) -> float:
    return round(v / 1.27) * 1.27


def _effects(size=1.27, hide=False, justify=None):
    e = S("effects", S("font", S("size", size, size)))
    if justify:
        e.append(S("justify", *justify))
    if hide:
        e.append(S("hide", "yes"))
    return e


class Schematic:
    def __init__(self, project: str, title: str, paper: str = "A2",
                 rev: str = "", date: str = "", company: str = "",
                 comments: Tuple[str, ...] = (), extra_lib_dirs: Tuple[str, ...] = ()):
        self.project = project
        self.uuid = uid("sheet:" + project)
        self.paper = paper
        self.title = (title, rev, date, company, comments)
        self.extra = extra_lib_dirs
        self.libs: Dict[str, list] = {}
        self.items: List[list] = []
        self.symbols: Dict[str, dict] = {}   # ref -> info (uuid, nets, footprint...)
        self._flags = 0

    # -- symbols -----------------------------------------------------------
    def add(self, ref: str, lib_id: str, value: str, footprint: str,
            at: Tuple[float, float], rot: float = 0, nets: Optional[Dict[str, Optional[str]]] = None,
            fields: Optional[Dict[str, str]] = None, dnp: bool = False,
            in_bom: bool = True, on_board: bool = True) -> dict:
        if lib_id not in self.libs:
            self.libs[lib_id] = library_symbol(lib_id, self.extra)
        sym = self.libs[lib_id]
        pins = symbol_pins(sym)
        nets = dict(nets or {})
        x, y = _snap(at[0]), _snap(at[1])
        su = uid("sym:%s:%s" % (self.project, ref))
        node = S("symbol", S("lib_id", Q(lib_id)), S("at", x, y, rot), S("unit", 1),
                 S("exclude_from_sim", "no"), S("in_bom", "yes" if in_bom else "no"),
                 S("on_board", "yes" if on_board else "no"), S("dnp", "yes" if dnp else "no"),
                 S("uuid", Q(su)))
        hidden_ref = ref.startswith("#")
        props = [("Reference", ref, (x + 2.54, y - 3.81), hidden_ref),
                 ("Value", value, (x + 2.54, y + 3.81), hidden_ref),
                 ("Footprint", footprint, (x, y), True),
                 ("Datasheet", (fields or {}).get("Datasheet", ""), (x, y), True),
                 ("Description", "", (x, y), True)]
        for k, v in (fields or {}).items():
            if k != "Datasheet":
                props.append((k, v, (x, y), True))
        for k, v, pos, hide in props:
            node.append(S("property", Q(k), Q(v), S("at", pos[0], pos[1], 0),
                          _effects(hide=hide, justify=["left"] if k in ("Reference", "Value") else None)))
        for num in pins:
            node.append(S("pin", Q(num), S("uuid", Q(uid("pin:%s:%s:%s" % (self.project, ref, num))))))
        node.append(S("instances", S("project", Q(self.project),
                      S("path", Q("/" + self.uuid), S("reference", Q(ref)), S("unit", 1)))))
        self.items.append(node)

        nc_names: Dict[str, str] = {}
        for num, p in pins.items():
            if num not in nets:
                if p["type"] in ("no_connect",):
                    continue
                raise ValueError("%s pin %s (%s) has no net; pass None for no-connect" % (ref, num, p["name"]))
            px, py = _rot(p["x"], p["y"], rot)
            sx, sy = round(x + px, 4), round(y - py, 4)
            net = nets[num]
            if net is None:
                self.items.append(S("no_connect", S("at", sx, sy), S("uuid", Q(uid()))))
                nc_names[num] = "unconnected-(%s-%s-Pad%s)" % (ref, p["name"], num)
                continue
            ang = (p["angle"] + rot + 180) % 360
            just = ["right", "bottom"] if ang in (180.0,) else ["left", "bottom"]
            if ang == 180:
                lab_ang = 0
                just = ["right", "bottom"]
            elif ang == 0:
                lab_ang = 0
                just = ["left", "bottom"]
            elif ang == 90:
                lab_ang = 90
                just = ["left", "bottom"]
            else:
                lab_ang = 90
                just = ["right", "bottom"]
            self.items.append(S("label", Q(net), S("at", sx, sy, lab_ang),
                                _effects(justify=just), S("uuid", Q(uid()))))
        extra = set(nets) - set(pins)
        if extra:
            raise ValueError("%s: unknown pins %s" % (ref, sorted(extra)))
        info = {"uuid": su, "lib_id": lib_id, "value": value, "footprint": footprint,
                "nets": {k: v for k, v in nets.items()}, "fields": dict(fields or {}),
                "dnp": dnp, "in_bom": in_bom, "on_board": on_board, "nc": nc_names}
        self.symbols[ref] = info
        return info

    def power_flag(self, net: str, at: Tuple[float, float]):
        self._flags += 1
        self.add("#FLG%02d" % self._flags, "power:PWR_FLAG", "PWR_FLAG", "", at,
                 nets={"1": net}, in_bom=False, on_board=False)

    # -- annotations -------------------------------------------------------
    def text(self, s: str, at: Tuple[float, float], size: float = 1.27, bold: bool = False):
        font = S("font", S("size", size, size))
        if bold:
            font.append(S("bold", "yes"))
        self.items.append(S("text", Q(s), S("exclude_from_sim", "no"), S("at", at[0], at[1], 0),
                            S("effects", font, S("justify", "left", "bottom")), S("uuid", Q(uid()))))

    def box(self, x0, y0, x1, y1):
        self.items.append(S("rectangle", S("start", x0, y0), S("end", x1, y1),
                            S("stroke", S("width", 0.2), S("type", "dash")),
                            S("fill", S("type", "none")), S("uuid", Q(uid()))))

    # -- output ------------------------------------------------------------
    def write(self, path: str):
        title, rev, date, company, comments = self.title
        tb = S("title_block", S("title", Q(title)))
        if date:
            tb.append(S("date", Q(date)))
        if rev:
            tb.append(S("rev", Q(rev)))
        if company:
            tb.append(S("company", Q(company)))
        for i, c in enumerate(comments, 1):
            tb.append(S("comment", i, Q(c)))
        root = S("kicad_sch", S("version", 20250114), S("generator", Q("kicadgen")),
                 S("generator_version", Q("10.0")), S("uuid", Q(self.uuid)),
                 S("paper", Q(self.paper)), tb,
                 S("lib_symbols", *self.libs.values()))
        root.extend(self.items)
        root.append(S("sheet_instances", S("path", Q("/"), S("page", Q("1")))))
        root.append(S("embedded_fonts", "no"))
        with open(path, "w", encoding="utf-8") as f:
            f.write(dump(root) + "\n")

    def nets(self) -> Dict[str, List[Tuple[str, str]]]:
        out: Dict[str, List[Tuple[str, str]]] = {}
        for ref, info in self.symbols.items():
            if not info["on_board"]:
                continue
            for pin, net in info["nets"].items():
                if net:
                    out.setdefault(net, []).append((ref, pin))
        return out


def write_project(path: str, netclasses: List[dict], rules: dict):
    """Minimal .kicad_pro with net classes and design rules."""
    import json

    classes = []
    for nc in netclasses:
        d = {
            "name": nc["name"], "clearance": nc.get("clearance", 0.2),
            "track_width": nc.get("track", 0.25), "via_diameter": nc.get("via", 0.6),
            "via_drill": nc.get("drill", 0.3), "microvia_diameter": 0.3, "microvia_drill": 0.1,
            "diff_pair_width": 0.2, "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25,
            "wire_width": 6, "bus_width": 12, "line_style": 0, "schematic_color": "rgba(0, 0, 0, 0.000)",
            "pcb_color": "rgba(0, 0, 0, 0.000)", "priority": nc.get("priority", 2147483647),
        }
        classes.append(d)
    patterns = []
    for nc in netclasses:
        for pat in nc.get("patterns", []):
            patterns.append({"netclass": nc["name"], "pattern": pat})
    pro = {
        "board": {"design_settings": {"rules": rules, "defaults": {}}},
        "meta": {"filename": os.path.basename(path), "version": 3},
        "net_settings": {"classes": classes, "meta": {"version": 4}, "netclass_patterns": patterns},
        "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},
        "sheets": [], "text_variables": {},
    }
    with open(path, "w") as f:
        json.dump(pro, f, indent=2)
