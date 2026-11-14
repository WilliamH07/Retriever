"""Pire cas des seuils du hacheur : résistances ±1 %, LM4040A ±0,1 %, offset TLV1701 ±2,5 mV.

Usage : python3 corners.py hacheur.cir [tolérance diviseur, défaut 0.01]
"""
import itertools, re, subprocess, sys

src = open(sys.argv[1]).read()
base = dict(re.findall(r"(\w+)=([\d.]+(?:k|Meg)?)", re.search(r"^\.param (.*)$", src, re.M).group(1)))
unit = {"k": 1e3, "Meg": 1e6, "": 1}
num = {k: float(re.match(r"[\d.]+", v).group()) * unit[re.sub(r"[\d.]+", "", v)] for k, v in base.items()}

def run(p):
    line = ".param " + " ".join("%s=%g" % kv for kv in p.items())
    net = re.sub(r"^\.param .*$", line, src, flags=re.M)
    out = subprocess.run(["ngspice", "-b", "/dev/stdin"], input=net, capture_output=True, text=True).stdout
    get = lambda k: float(re.search(r"^%s\s+=\s+(\S+)" % k, out, re.M).group(1))
    return get("von"), get("voff")

tol = float(sys.argv[2]) if len(sys.argv) > 2 else 0.01
res = []
for s in itertools.product((-1, 1), repeat=4):  # Rt, Rb, Rh, Vref(+offset)
    p = dict(num)
    p["RT1"] *= 1 + tol * s[0]; p["RT2"] *= 1 + tol * s[0]
    p["RB1"] *= 1 + tol * s[1]; p["RB2"] *= 1 + tol * s[1]
    p["RH"] *= 1 + 0.01 * s[2]
    p["VREF"] = 2.5 * (1 + 0.001 * s[3]) + 0.0025 * s[3]
    res.append(run(p))
von, voff = zip(*res)
print("nominal  ON %.2f V  OFF %.2f V" % run(num))
print("tol %.1f %%" % (tol * 100)); print("pire cas ON %.2f à %.2f V  OFF %.2f à %.2f V" % (min(von), max(von), min(voff), max(voff)))
