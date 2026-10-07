#!/usr/bin/env python3
"""Build an isolated front/rear/bench4 ESP-IDF configuration, optionally flash it.

    python3 tools/flash_motion.py front
    python3 tools/flash_motion.py rear --transport can
    python3 tools/flash_motion.py bench4 --count 3 --flash --port /dev/cu.usbserial-XXXX

Source ESP-IDF export.sh first. No flash without --flash and an explicit port.
Apache-2.0.
"""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

PROJECT = Path(__file__).resolve().parent.parent / "firmware" / "esp32_motion"

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("role", choices=("front", "rear", "bench4"))
    ap.add_argument("--transport", choices=("serial", "can"), default="serial")
    ap.add_argument("--count", type=int, help="sorties locales cablees (1..2 par essieu, 1..4 sur banc)")
    ap.add_argument("--inverted", action="store_true", help="DIR/STOP via NMOS externe inversant")
    ap.add_argument("--flash", action="store_true")
    ap.add_argument("--port")
    args = ap.parse_args()
    if args.flash and not args.port:
        ap.error("--flash exige --port : identifier physiquement l'ESP avant/arriere")
    if args.port and not args.flash:
        ap.error("--port s'utilise avec --flash")
    count = args.count if args.count is not None else (3 if args.role == "bench4" else 2)
    if not 1 <= count <= (4 if args.role == "bench4" else 2):
        ap.error("nombre de sorties incompatible avec le profil")
    idf_root = os.environ.get("IDF_PATH")
    idf = shutil.which("idf.py")
    if not idf and idf_root and (Path(idf_root) / "tools" / "idf.py").is_file():
        idf = str(Path(idf_root) / "tools" / "idf.py")
    if not idf or not idf_root:
        ap.error("environnement ESP-IDF absent : charger export.sh d'ESP-IDF v5.5")
    # Separate build and sdkconfig for EVERY effective configuration. Cached
    # Kconfig values must never silently turn a rear image into a front image.
    build = PROJECT / "build" / f"{args.role}-{args.transport}-{count}-{'nmos' if args.inverted else 'translator'}"
    build.mkdir(parents=True, exist_ok=True)
    overrides = build / "bench.defaults"
    overrides.write_text(f"CONFIG_RETRIEVER_MOTOR_COUNT={count}\nCONFIG_RETRIEVER_MOTOR_LOGIC_INVERTED={'y' if args.inverted else 'n'}\n")
    defaults = ";".join(str(p) for p in (PROJECT / "sdkconfig.defaults", PROJECT / f"sdkconfig.{args.role}",
                                        PROJECT / f"sdkconfig.{args.transport}", overrides))
    # SDKCONFIG is generated exclusively by this tool. Recreate it on every
    # invocation so a changed committed default cannot be shadowed by cache.
    (build / "sdkconfig").unlink(missing_ok=True)
    cmd = [sys.executable, idf, "-B", str(build), "-D", f"SDKCONFIG={build / 'sdkconfig'}",
           "-D", f"SDKCONFIG_DEFAULTS={defaults}", "reconfigure", "build"]
    if args.flash:
        cmd[2:2] = ["-p", args.port]
        cmd.append("flash")
    print(f"MOTION {args.role} · {args.transport} · {count} sorties · {build}", flush=True)
    return subprocess.run(cmd, cwd=PROJECT).returncode

if __name__ == "__main__":
    raise SystemExit(main())
