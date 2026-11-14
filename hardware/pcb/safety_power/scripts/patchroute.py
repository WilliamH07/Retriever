"""patchroute — finish the few connections Freerouting leaves open.

Reads the unconnected pairs of a KiCad DRC report, and for each one runs a small A* search
on a 0.1 mm grid, on F.Cu and B.Cu with vias, around the two items. Obstacles are every
copper item of another net, inflated by the larger of the two net-class clearances plus half
the track width. GND_LOGIC pours (refilled afterwards) are ignored. Deterministic.
"""

from __future__ import annotations

import heapq
import math
import re

import pcbnew as P

STEP = 0.1
TRACK = 0.2
VIA_D, VIA_DRILL = 0.6, 0.3
LAYERS = (P.F_Cu, P.In2_Cu, P.B_Cu)  # In1 holds the ground planes and is never used


def mm(v):
    return P.ToMM(v)


def pairs_from_report(path):
    out = []
    for blk in re.split(r"\n(?=\[)", open(path).read()):
        if not blk.startswith("[unconnected_items"):
            continue
        items = re.findall(r"@\(([-\d.]+) mm, ([-\d.]+) mm\): (Pad|Piste|Via|Pad métallisé|Zone)[^\[]*\[([^\]]+)\]", blk)
        if len(items) == 2 and items[0][3] == items[1][3] and "Zone" not in (items[0][2], items[1][2]):
            out.append([(float(x), float(y), k) for x, y, k, n in items] + [items[0][3]])
    return out


class Router:
    def __init__(self, b, clr_of, ignore_nets=(), y_min=None):
        self.b = b
        self.clr_of = clr_of
        self.ignore = set(ignore_nets)
        self.y_min = y_min

    def anchors(self, x, y, kind, net):
        """Candidate start/goal points (x, y, layers) for one reported item."""
        pts = []
        for t in self.b.GetTracks():
            if t.GetNetname() != net:
                continue
            if t.GetClass() == "PCB_VIA":
                p = t.GetPosition()
                if math.hypot(mm(p.x) - x, mm(p.y) - y) < 0.05:
                    pts.append((mm(p.x), mm(p.y), LAYERS))
            elif kind == "Piste":
                for e in (t.GetStart(), t.GetEnd()):
                    pass
                s0, s1 = t.GetStart(), t.GetEnd()
                if min(math.hypot(mm(s0.x) - x, mm(s0.y) - y), math.hypot(mm(s1.x) - x, mm(s1.y) - y)) < 0.05 or \
                        self._on_seg(x, y, s0, s1):
                    for e in (s0, s1):
                        pts.append((mm(e.x), mm(e.y), (t.GetLayer(),)))
        if kind.startswith("Pad"):
            for fp in self.b.GetFootprints():
                for p in fp.Pads():
                    c = p.GetPosition()
                    if p.GetNetname() == net and math.hypot(mm(c.x) - x, mm(c.y) - y) < 0.05:
                        lay = LAYERS if p.GetAttribute() == P.PAD_ATTRIB_PTH else (P.F_Cu,)
                        pts.append((mm(c.x), mm(c.y), lay))
        return pts

    @staticmethod
    def _on_seg(x, y, s0, s1):
        ax, ay, bx, by = mm(s0.x), mm(s0.y), mm(s1.x), mm(s1.y)
        L2 = (bx - ax) ** 2 + (by - ay) ** 2
        u = 0 if L2 == 0 else max(0, min(1, ((x - ax) * (bx - ax) + (y - ay) * (by - ay)) / L2))
        return math.hypot(ax + u * (bx - ax) - x, ay + u * (by - ay) - y) < 0.05

    def grid(self, net, box):
        x0, y0, x1, y1 = box
        nx, ny = int((x1 - x0) / STEP) + 1, int((y1 - y0) / STEP) + 1
        my = self.clr_of(net)
        blocked = {L: bytearray(nx * ny) for L in LAYERS}
        vblock = bytearray(nx * ny)

        def mark(layer, shape, infl, via_infl):
            # shape: ("seg", ax, ay, bx, by, w) | ("box", x0, y0, x1, y1) | ("circ", cx, cy, r)
            if shape[0] == "seg":
                _, ax, ay, bx, by, w = shape
                ext = w / 2 + max(infl, via_infl)
                bx0, by0, bx1, by1 = min(ax, bx) - ext, min(ay, by) - ext, max(ax, bx) + ext, max(ay, by) + ext
            elif shape[0] == "box":
                _, bx0, by0, bx1, by1 = shape
                ext = max(infl, via_infl)
                bx0, by0, bx1, by1 = bx0 - ext, by0 - ext, bx1 + ext, by1 + ext
            else:
                _, cx, cy, r = shape
                ext = r + max(infl, via_infl)
                bx0, by0, bx1, by1 = cx - ext, cy - ext, cx + ext, cy + ext
            i0, i1 = max(0, int((bx0 - x0) / STEP)), min(nx - 1, int((bx1 - x0) / STEP) + 1)
            j0, j1 = max(0, int((by0 - y0) / STEP)), min(ny - 1, int((by1 - y0) / STEP) + 1)
            for j in range(j0, j1 + 1):
                py = y0 + j * STEP
                for i in range(i0, i1 + 1):
                    px = x0 + i * STEP
                    if shape[0] == "seg":
                        _, ax, ay, bx, by, w = shape
                        L2 = (bx - ax) ** 2 + (by - ay) ** 2
                        u = 0 if L2 == 0 else max(0, min(1, ((px - ax) * (bx - ax) + (py - ay) * (by - ay)) / L2))
                        d = math.hypot(ax + u * (bx - ax) - px, ay + u * (by - ay) - py) - w / 2
                    elif shape[0] == "box":
                        _, a0, b0, a1, b1 = shape
                        d = math.hypot(max(a0 - px, 0, px - a1), max(b0 - py, 0, py - b1))
                    else:
                        _, cx, cy, r = shape
                        d = math.hypot(px - cx, py - cy) - r
                    k = j * nx + i
                    if layer is not None and d < infl:
                        blocked[layer][k] = 1
                    if d < via_infl:
                        vblock[k] = 1

        def infl_for(other):
            c = max(my, self.clr_of(other)) + 0.01
            return c + TRACK / 2, c + VIA_D / 2

        for t in self.b.GetTracks():
            n = t.GetNetname()
            if t.GetClass() == "PCB_VIA":
                p = t.GetPosition()
                cx, cy, r = mm(p.x), mm(p.y), mm(t.GetWidth(P.F_Cu)) / 2
                if not (x0 - 2 < cx < x1 + 2 and y0 - 2 < cy < y1 + 2):
                    continue
                if n == net:
                    continue
                ti, tv = infl_for(n)
                tv = max(tv, VIA_DRILL / 2 + 0.5 + r)  # hole to hole
                for L in LAYERS:
                    mark(L, ("circ", cx, cy, r), ti, tv)
            else:
                s0, s1 = t.GetStart(), t.GetEnd()
                ax, ay, bx, by = mm(s0.x), mm(s0.y), mm(s1.x), mm(s1.y)
                if max(ax, bx) < x0 - 2 or min(ax, bx) > x1 + 2 or max(ay, by) < y0 - 2 or min(ay, by) > y1 + 2:
                    continue
                if n == net:
                    continue
                ti, tv = infl_for(n)
                L = t.GetLayer()
                w = mm(t.GetWidth())
                if L in blocked:
                    mark(L, ("seg", ax, ay, bx, by, w), ti, tv)
                else:  # inner layer: only vias care
                    mark(None, ("seg", ax, ay, bx, by, w), 0, tv)
        for fp in self.b.GetFootprints():
            for p in fp.Pads():
                bb = p.GetBoundingBox()
                a0, b0, a1, b1 = mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom())
                if a1 < x0 - 2 or a0 > x1 + 2 or b1 < y0 - 2 or b0 > y1 + 2:
                    continue
                n = p.GetNetname()
                same = n == net and n != ""
                ti, tv = infl_for(n)
                if p.GetDrillSize().x > 0:
                    tv = max(tv, mm(p.GetDrillSize().x) / 2 + VIA_DRILL / 2 + 0.5 - 0.0)
                    if same:
                        mark(None, ("box", a0, b0, a1, b1), 0, tv)
                        continue
                    for L in LAYERS:
                        mark(L, ("box", a0, b0, a1, b1), ti, tv)
                else:
                    if same:
                        mark(None, ("box", a0, b0, a1, b1), 0, VIA_D / 2 + 0.2)
                        continue
                    for L in LAYERS:
                        if p.IsOnLayer(L):
                            mark(L, ("box", a0, b0, a1, b1), ti, tv)
                        else:
                            mark(None, ("box", a0, b0, a1, b1), 0, 0)
        for z in self.b.Zones():
            zb = z.GetBoundingBox()
            if mm(zb.GetRight()) < x0 - 1 or mm(zb.GetLeft()) > x1 + 1 or mm(zb.GetBottom()) < y0 - 1 or \
                    mm(zb.GetTop()) > y1 + 1:
                continue
            if not any(z.GetLayerSet().Contains(L) for L in LAYERS):
                continue
            if z.GetIsRuleArea():
                ol = z.Outline()
                bb = ol.BBox()
                if z.GetDoNotAllowTracks() and z.GetLayerSet().Contains(P.F_Cu) and z.GetLayerSet().Contains(P.B_Cu):
                    self._mark_poly(z, blocked, vblock, (x0, y0, nx, ny), 0.0, True)
                continue
            if z.GetNetname() == net or z.GetNetname() in self.ignore:
                continue
            ti, tv = infl_for(z.GetNetname())
            self._mark_poly(z, blocked, vblock, (x0, y0, nx, ny), ti, False, tv)
        # board edge and the logic-zone limit
        for j in range(ny):
            for i in range(nx):
                px, py = x0 + i * STEP, y0 + j * STEP
                if px < 0.6 or py < 0.6 or px > self.W - 0.6 or py > self.H - 0.6 or \
                        (self.y_min is not None and py < self.y_min):
                    k = j * nx + i
                    for L in LAYERS:
                        blocked[L][k] = 1
                    vblock[k] = 1
        return blocked, vblock, nx, ny

    def _mark_poly(self, z, blocked, vblock, g, infl, all_layers, vinfl=0.0):
        x0, y0, nx, ny = g
        layers = [L for L in LAYERS if z.GetLayerSet().Contains(L)] if not all_layers else list(LAYERS)
        inner = not layers
        for j in range(ny):
            for i in range(nx):
                px, py = x0 + i * STEP, y0 + j * STEP
                q = P.VECTOR2I(P.FromMM(px), P.FromMM(py))
                ol = z.Outline()
                if ol.Contains(q) or ol.SquaredDistance(q) < P.FromMM(max(infl, vinfl)) ** 2:
                    d = math.sqrt(ol.SquaredDistance(q)) / 1e6 if not ol.Contains(q) else 0
                    k = j * nx + i
                    for L in layers:
                        if d < infl:
                            blocked[L][k] = 1
                    if all_layers or (d < vinfl and not inner and False):
                        vblock[k] = 1

    def route(self, net, a_pts, b_pts):
        xs = [p[0] for p in a_pts + b_pts]
        ys = [p[1] for p in a_pts + b_pts]
        pad = 6.0
        box = (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)
        blocked, vblock, nx, ny = self.grid(net, box)
        x0, y0 = box[0], box[1]

        def cell(x, y):
            return int(round((x - x0) / STEP)), int(round((y - y0) / STEP))
        layers = LAYERS
        goal = set()
        for x, y, ls in b_pts:
            i, j = cell(x, y)
            for L in ls:
                if L in layers:
                    goal.add((i, j, L))
        gx = sum(g[0] for g in goal) / max(1, len(goal))
        gy = sum(g[1] for g in goal) / max(1, len(goal))
        openq, came, cost = [], {}, {}
        for x, y, ls in a_pts:
            i, j = cell(x, y)
            for L in ls:
                if L in layers:
                    s = (i, j, L)
                    cost[s] = 0
                    heapq.heappush(openq, (math.hypot(i - gx, j - gy), s))
        moves = [(1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)]
        end = None
        n_exp = 0
        while openq and n_exp < 400000:
            _, s = heapq.heappop(openq)
            n_exp += 1
            if s in goal:
                end = s
                break
            i, j, L = s
            c0 = cost[s]
            nbrs = []
            for di, dj, w in moves:
                ii, jj = i + di, j + dj
                if 0 <= ii < nx and 0 <= jj < ny:
                    nbrs.append(((ii, jj, L), w))
            for other in LAYERS:
                if other != L:
                    nbrs.append(((i, j, other), 25))
            for n2, w in nbrs:
                ii, jj, L2 = n2
                k = jj * nx + ii
                free = (blocked[L2][k] == 0) or n2 in goal
                if L2 != L:
                    free = free and vblock[k] == 0
                if not free:
                    continue
                c = c0 + w
                if c < cost.get(n2, 1e18):
                    cost[n2] = c
                    came[n2] = s
                    heapq.heappush(openq, (c + math.hypot(ii - gx, jj - gy), n2))
        if end is None:
            return None
        path = [end]
        while path[-1] in came:
            path.append(came[path[-1]])
        path.reverse()
        # emit: merge straight runs, vias at layer changes
        pts = [(x0 + i * STEP, y0 + j * STEP, L) for i, j, L in path]
        seg_start = pts[0]
        prev = pts[0]
        direction = None
        for p in pts[1:] + [None]:
            if p is not None and p[2] == prev[2]:
                d = (round(p[0] - prev[0], 3), round(p[1] - prev[1], 3))
                if direction is None or d == direction:
                    direction = d
                    prev = p
                    continue
            if (seg_start[0], seg_start[1]) != (prev[0], prev[1]):
                self._track(net, seg_start, prev)
            if p is None:
                break
            if p[2] != prev[2]:
                self._via(net, prev[0], prev[1])
                seg_start, prev, direction = p, p, None
            else:
                seg_start, direction = prev, (round(p[0] - prev[0], 3), round(p[1] - prev[1], 3))
                prev = p
        return pts[0], pts[-1]

    def _track(self, net, a, b):
        t = P.PCB_TRACK(self.b)
        t.SetStart(P.VECTOR2I(P.FromMM(a[0]), P.FromMM(a[1])))
        t.SetEnd(P.VECTOR2I(P.FromMM(b[0]), P.FromMM(b[1])))
        t.SetWidth(P.FromMM(TRACK))
        t.SetLayer(a[2])
        t.SetNet(self.b.FindNet(net))
        self.b.Add(t)

    def _via(self, net, x, y):
        v = P.PCB_VIA(self.b)
        v.SetPosition(P.VECTOR2I(P.FromMM(x), P.FromMM(y)))
        v.SetWidth(P.FromMM(VIA_D))
        v.SetDrill(P.FromMM(VIA_DRILL))
        v.SetNet(self.b.FindNet(net))
        self.b.Add(v)


def finish(b, report, clr_of, W, H, ignore_nets=(), log=print):
    r = Router(b, clr_of, ignore_nets)
    r.W, r.H = W, H
    done = 0
    for (xa, ya, ka), (xb, yb, kb), net in pairs_from_report(report):
        a = r.anchors(xa, ya, ka, net)
        bb = r.anchors(xb, yb, kb, net)
        if not a or not bb:
            log("  skip %s: anchors %d/%d" % (net, len(a), len(bb)))
            continue
        # snap anchors to the grid with a short stub from the true point
        global TRACK
        ends = r.route(net, a, bb)
        if not ends:  # retry with the fab minimum width
            TRACK = 0.15
            ends = r.route(net, a, bb)
            TRACK = 0.2
        if ends:
            for e, cands in ((ends[0], a), (ends[1], bb)):
                best = min((c for c in cands if e[2] in c[2]), key=lambda c: math.hypot(c[0] - e[0], c[1] - e[1]))
                if math.hypot(best[0] - e[0], best[1] - e[1]) > 1e-4:
                    r._track(net, (best[0], best[1], e[2]), e)
        log("  %s (%.1f,%.1f)->(%.1f,%.1f): %s" % (net, xa, ya, xb, yb, "routed" if ends else "FAILED"))
        done += bool(ends)
    return done
