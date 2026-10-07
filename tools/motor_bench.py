#!/usr/bin/env python3
"""Banc moteurs sans ROS : arme, commande et observe le nœud MOTION.

    python3 tools/motor_bench.py --device /dev/cu.usbserial-XXXX
    python3 tools/motor_bench.py --device /dev/ttyUSB1 --enable 7 --duty 0.2 0 0 0
    python3 tools/motor_bench.py --device /dev/ttyUSB1 --estop

Sans --duty, le script arme (si --enable) puis envoie des zéros à 50 Hz et
affiche MOTOR_STATE : c'est le mode « je vérifie que la carte répond ».
Avec --duty, la consigne est tenue pendant --seconds (défaut 3 s), puis
remise à zéro AVANT de quitter — jamais de moteur laissé en marche par un
Ctrl-C.

⚠️ ROUES EN L'AIR.

Copyright (c) 2026 William Hanczyk — Apache License 2.0
"""

from __future__ import annotations

import argparse
import sys
import time

from retriever_wire import Decoder, Protocol, open_port

MAGIC_ENABLE = 0xEB
MAGIC_ESTOP = 0xE5
FLAGS = (("ENABLED", 0x01), ("CMD_TIMEOUT", 0x02), ("ESTOP", 0x04), ("NEVER_ARMED", 0x08))


def flags_str(v: int) -> str:
    noms = [n for n, b in FLAGS if v & b]
    return "+".join(noms) if noms else "-"


def render(state: dict | None, hb: dict | None, duty: list[float], vues: dict[int, int],
           proto: Protocol) -> str:
    lignes = []
    if hb:
        lignes.append(f"  MOTION_FRONT  etat={hb['state']}  uptime={hb['uptime_s']} s  "
                      f"err={hb['err_count']}  hash=0x{hb['protocol_hash']:08X}")
    else:
        lignes.append("  MOTION_FRONT  (aucun battement de coeur)")
    lignes.append("")
    if state:
        lignes.append(f"  masque=0x{state['enable_mask']:02X}  drapeaux={flags_str(state['flags'])}"
                      f"  age cmd={state['cmd_age_ms']} ms")
        for i in range(4):
            on = "ON " if state["enable_mask"] & (1 << i) else "off"
            lignes.append(f"    m{i} [{on}]  consigne {duty[i]:+.2f}  "
                          f"appliquee {state[f'applied_m{i}']:+.2f}")
    else:
        lignes.append("  (aucun MOTOR_STATE)")
    lignes.append("")
    lignes.append("  trames vues : " + ", ".join(
        f"{proto.name(k)}×{v}" for k, v in sorted(vues.items())))
    return "\n".join(lignes)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--device", default="/dev/ttyUSB1")
    ap.add_argument("--baud", type=int, default=921600)
    ap.add_argument("--enable", type=lambda s: int(s, 0), default=None,
                    help="masque d'activation à envoyer (7 = m0..m2, 15 = les quatre)")
    ap.add_argument("--duty", type=float, nargs=4, metavar=("M0", "M1", "M2", "M3"),
                    help="rapport cyclique signé par moteur, dans [-1, 1]")
    ap.add_argument("--seconds", type=float, default=3.0,
                    help="durée de la consigne --duty (défaut 3 s) ; 0 = jusqu'à Ctrl-C")
    ap.add_argument("--estop", action="store_true", help="envoyer ESTOP_REQUEST et sortir")
    args = ap.parse_args()

    proto = Protocol()
    port = open_port(args.device, args.baud)
    decoder = Decoder()
    id_state = proto.by_name["MOTOR_STATE"].id
    id_hb = proto.by_name["HEARTBEAT_MOTION_FRONT"].id

    if args.estop:
        port.write(proto.encode_named("ESTOP_REQUEST", magic=MAGIC_ESTOP))
        port.flush()
        print("ESTOP_REQUEST envoyé. Ré-armer avec --enable.")
        return 0

    if args.enable is not None:
        port.write(proto.encode_named("MOTOR_ENABLE", enable_mask=args.enable,
                                      magic=MAGIC_ENABLE))
        port.flush()

    duty = [max(-1.0, min(1.0, d)) for d in (args.duty or [0.0] * 4)]
    hold = args.seconds if args.duty else 0.0

    state = hb = None
    vues: dict[int, int] = {}
    debut = time.monotonic()
    prochain_cmd = 0.0
    prochain_rendu = 0.0

    def send(vals: list[float]) -> None:
        port.write(proto.encode_named("MOTOR_CMD", m0=vals[0], m1=vals[1],
                                      m2=vals[2], m3=vals[3]))
        port.flush()

    try:
        while True:
            maintenant = time.monotonic()
            if hold and maintenant - debut >= hold:
                break
            if maintenant >= prochain_cmd:
                prochain_cmd = maintenant + 0.02
                send(duty)
            data = port.read(port.in_waiting or 1)
            for frame_id, payload in decoder.feed(data):
                vues[frame_id] = vues.get(frame_id, 0) + 1
                fd = proto.frames.get(frame_id)
                if fd is None:
                    continue
                if frame_id == id_state:
                    state = fd.decode(payload)
                elif frame_id == id_hb:
                    hb = fd.decode(payload)
            if maintenant >= prochain_rendu:
                prochain_rendu = maintenant + 0.25
                sys.stdout.write("\033[2J\033[H")
                sys.stdout.write(f"  {args.device}   ·   {maintenant - debut:6.1f} s   ·   "
                                 f"crc={decoder.stats.crc_errors} fmt={decoder.stats.format_errors}\n\n")
                sys.stdout.write(render(state, hb, duty, vues, proto) + "\n")
                sys.stdout.flush()
    except KeyboardInterrupt:
        pass
    finally:
        # Trois zéros de suite : une trame perdue ne doit pas laisser une roue tourner.
        for _ in range(3):
            send([0.0] * 4)
            time.sleep(0.02)
        print("\nconsignes remises à zéro.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
