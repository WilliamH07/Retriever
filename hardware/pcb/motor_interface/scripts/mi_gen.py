"""mi_gen — board-local helpers on top of the shared generator (kicadgen / kicadpcb).

The shared modules in hardware/pcb/scripts are not modified by this board.
What lives here:

* `add_units()`: place every unit of a multi-unit symbol (74LVC3G17, TLV9062).
  `kicadgen.Schematic.add` only instantiates unit 1, which would leave the
  other gates and the power unit out of the netlist.
* `outline_poly()`: board outline from an arbitrary polygon (the antenna notch
  under the ESP32 module is not a rectangle).
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

import kicadgen as K


def unit_pins(sym: list, unit: int) -> Dict[str, dict]:
    """Pins drawn in `unit` (plus pins common to all units, unit 0)."""
    pins = {}
    for u in K.find_all(sym, "symbol"):
        m = re.search(r"_(\d+)_(\d+)$", u[1])
        if not m or int(m.group(1)) not in (0, unit):
            continue
        for p in K.find_all(u, "pin"):
            at = K.find(p, "at")
            pins[str(K.find(p, "number")[1])] = {
                "x": float(at[1]), "y": float(at[2]),
                "angle": float(at[3]) if len(at) > 3 else 0.0,
                "type": p[1], "name": str(K.find(p, "name")[1]),
            }
    return pins


def unit_count(sym: list) -> int:
    n = 1
    for u in K.find_all(sym, "symbol"):
        m = re.search(r"_(\d+)_(\d+)$", u[1])
        if m:
            n = max(n, int(m.group(1)))
    return n


def add_units(s: "K.Schematic", ref: str, lib_id: str, value: str, footprint: str,
              placements: List[Tuple[int, Tuple[float, float], float]],
              nets: Dict[str, Optional[str]], fields: Optional[Dict[str, str]] = None,
              dnp: bool = False, in_bom: bool = True) -> dict:
    """Like Schematic.add, for a symbol with several units.

    placements: [(unit, (x, y), rot), ...] — every unit must be listed once.
    nets: pin number -> net for the whole package.
    """
    if lib_id not in s.libs:
        s.libs[lib_id] = K.library_symbol(lib_id, s.extra)
    sym = s.libs[lib_id]
    n_units = unit_count(sym)
    if sorted(u for u, _, _ in placements) != list(range(1, n_units + 1)):
        raise ValueError("%s: place units 1..%d exactly once" % (ref, n_units))
    seen = set()
    nc_names: Dict[str, str] = {}
    first_uuid = None
    for unit, at, rot in placements:
        pins = unit_pins(sym, unit)
        x, y = K._snap(at[0]), K._snap(at[1])
        su = K.uid("sym:%s:%s:u%d" % (s.project, ref, unit)) if unit > 1 else K.uid("sym:%s:%s" % (s.project, ref))
        first_uuid = first_uuid or su
        node = K.S("symbol", K.S("lib_id", K.Q(lib_id)), K.S("at", x, y, rot), K.S("unit", unit),
                   K.S("exclude_from_sim", "no"), K.S("in_bom", "yes" if in_bom else "no"),
                   K.S("on_board", "yes"), K.S("dnp", "yes" if dnp else "no"), K.S("uuid", K.Q(su)))
        props = [("Reference", ref, (x + 2.54, y - 3.81), False),
                 ("Value", value, (x + 2.54, y + 3.81), False),
                 ("Footprint", footprint, (x, y), True),
                 ("Datasheet", (fields or {}).get("Datasheet", ""), (x, y), True),
                 ("Description", "", (x, y), True)]
        for k, v in (fields or {}).items():
            if k != "Datasheet":
                props.append((k, v, (x, y), True))
        for k, v, pos, hide in props:
            node.append(K.S("property", K.Q(k), K.Q(v), K.S("at", pos[0], pos[1], 0),
                            K._effects(hide=hide, justify=["left"] if k in ("Reference", "Value") else None)))
        for num in pins:
            node.append(K.S("pin", K.Q(num), K.S("uuid", K.Q(K.uid("pin:%s:%s:%s" % (s.project, ref, num))))))
        node.append(K.S("instances", K.S("project", K.Q(s.project),
                    K.S("path", K.Q("/" + s.uuid), K.S("reference", K.Q(ref)), K.S("unit", unit)))))
        s.items.append(node)
        for num, p in pins.items():
            if num in seen:
                continue
            seen.add(num)
            if num not in nets:
                if p["type"] == "no_connect":
                    continue
                raise ValueError("%s pin %s has no net" % (ref, num))
            px, py = K._rot(p["x"], p["y"], rot)
            sx, sy = round(x + px, 4), round(y - py, 4)
            net = nets[num]
            if net is None:
                s.items.append(K.S("no_connect", K.S("at", sx, sy), K.S("uuid", K.Q(K.uid()))))
                nc_names[num] = "unconnected-(%s-%s-Pad%s)" % (ref, p["name"] or "Pad", num)
                continue
            ang = (p["angle"] + rot + 180) % 360
            lab_ang, just = {180: (0, ["right", "bottom"]), 0: (0, ["left", "bottom"]),
                             90: (90, ["left", "bottom"])}.get(ang, (90, ["right", "bottom"]))
            s.items.append(K.S("label", K.Q(net), K.S("at", sx, sy, lab_ang),
                               K._effects(justify=just), K.S("uuid", K.Q(K.uid()))))
    extra = set(nets) - seen
    if extra:
        raise ValueError("%s: unknown pins %s" % (ref, sorted(extra)))
    info = {"uuid": first_uuid, "lib_id": lib_id, "value": value, "footprint": footprint,
            "nets": dict(nets), "fields": dict(fields or {}), "dnp": dnp, "in_bom": in_bom,
            "on_board": True, "nc": nc_names}
    s.symbols[ref] = info
    return info


def outline_poly(board, pts: List[Tuple[float, float]], width: float = 0.1):
    """Closed Edge.Cuts polygon made of straight segments."""
    import pcbnew as P
    for a, b in zip(pts, pts[1:] + pts[:1]):
        board._seg(a, b, P.Edge_Cuts, width)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    board.bbox = (min(xs), min(ys), max(xs), max(ys))
