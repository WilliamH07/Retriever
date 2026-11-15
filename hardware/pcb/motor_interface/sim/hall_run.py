"""Fronts en sortie du tampon Hall : retards et fronts parasites, pour plusieurs bruits et seuils.

Usage : python3 hall_run.py
Le capteur conduit (ligne basse) de 1,00 à 4,46 ms, puis de 7,92 à 11,38 ms : 5 fronts attendus (1,00 F, 4,46 R, 7,92 F, 11,38 R, 14,84 F).
"""
import re, subprocess

src = open("hall.cir").read()

def run(vtp, vtm, vn):
    net = re.sub(r"^\.param .*$", ".param VTP=%g VTM=%g VN=%g" % (vtp, vtm, vn), src, flags=re.M)
    subprocess.run(["ngspice", "-b", "/dev/stdin"], input=net, capture_output=True, text=True)
    t, o = [], []
    for line in open("/tmp/hall_out.txt"):
        c = line.split()
        t.append(float(c[0])); o.append(float(c[1]))
    edges = [(t[i], "R" if o[i] > o[i - 1] else "F") for i in range(1, len(o)) if (o[i] > 1.65) != (o[i - 1] > 1.65)]
    return [x for x in edges if x[0] > 0.5e-3]

hall_edges = {1.00e-3: "F", 4.46e-3: "R", 7.92e-3: "F", 11.38e-3: "R"}
for vtp, vtm, tag in ((1.8, 1.0, "seuils typiques"), (2.2, 1.4, "seuils hauts"), (1.3, 0.6, "seuils bas")):
    for vn in (0.0, 1.0, 2.0):
        e = run(vtp, vtm, vn)
        delays = []
        for th, kind in hall_edges.items():
            nxt = [x for x in e if x[0] >= th and x[1] == kind]
            if nxt:
                delays.append("%s+%.0fus" % (kind, (nxt[0][0] - th) * 1e6))
        print("%-16s bruit %.0f V : %d fronts (5 attendus)  %s" % (tag, vn, len(e), " ".join(delays[:2])))
