#!/usr/bin/env python3
"""Observer, valider ou commander le banc MOTION (roues en l'air).

    python3 tools/motor_bench.py --device /dev/cu.usbserial-XXXX --self-test
    python3 tools/motor_bench.py --device /dev/cu.usbserial-XXXX --node rear --enable 12 --duty 0 0 .1 0
    python3 tools/motor_bench.py --transport can --interface can0 --node front --self-test

Les quatre valeurs sont toujours [avant gauche, avant droite, arriere gauche,
arriere droite]. Sans --enable, aucune autorisation n'est envoyee. --self-test
observe sans mouvement pendant --seconds (defaut 3 s). Apache-2.0.
"""
from __future__ import annotations
import argparse
from collections import deque
import json
import math
import sys
import time
from pathlib import Path
from retriever_wire import Decoder, Protocol, open_port

MAGIC_ENABLE, MAGIC_ESTOP, MAGIC_SESSION = 0xEB, 0xE5, 0xB2
ZERO = [0.0] * 4

class Transport:
    def __init__(self, args, proto):
        self.proto = proto
        self.decoder = Decoder()
        self.can = args.transport == "can"
        if self.can:
            import can
            self.api = can
            self.port = can.Bus(interface="socketcan", channel=args.interface)
        else:
            self.port = open_port(args.device, args.baud, reset=not args.no_reset)

    def send(self, name, **values):
        fd = self.proto.by_name[name]
        if self.can:
            self.port.send(self.api.Message(arbitration_id=fd.id, is_extended_id=False,
                                           data=fd.encode(values)), timeout=0.02)
        else:
            self.port.write(self.proto.encode_named(name, **values))
            self.port.flush()

    def receive(self):
        if self.can:
            msg = self.port.recv(timeout=0.005)
            if msg and not (msg.is_extended_id or msg.is_remote_frame or msg.is_error_frame):
                return [(msg.arbitration_id, bytes(msg.data))]
            return []
        return self.decoder.feed(self.port.read(self.port.in_waiting or 1))

    def close(self):
        self.port.shutdown() if self.can else self.port.close()

class Bench:
    def __init__(self, proto, transport, node):
        self.proto, self.transport = proto, transport
        self.target = proto.enums["node_id"]["values"][f"MOTION_{node.upper()}"]
        self.names = {"state": "MOTOR_STATE_REAR" if node == "rear" else "MOTOR_STATE",
                      "diag": f"MOTOR_DIAG_{node.upper()}",
                      "hb": f"HEARTBEAT_MOTION_{node.upper()}"}
        self.values = {}
        self.seen_at = {}
        self.started = time.monotonic()
        self.invalid = 0
        self.decoder_acquisition = None
        self.log_line = bytearray()
        self.logs = deque(maxlen=20)
        self.show_logs = False
        self.requested = None
        self.peak_applied = [0.0] * 4

    def poll(self):
        for fid, payload in self.transport.receive():
            fd = self.proto.frames.get(fid)
            if not fd:
                continue
            if len(payload) != fd.dlc:
                self.invalid += 1
                continue
            if fd.name == "LOG" and not getattr(self.transport, "can", False):
                values = fd.decode(payload)
                length = min(values["header"] & 0x0F, 7)
                self.log_line.extend(values[f"c{i}"] for i in range(length))
                if values["header"] & 0x10 or len(self.log_line) > 400:
                    line = self.log_line.decode("utf-8", errors="replace")
                    self.logs.append(line)
                    if self.show_logs:
                        print(f"ESP: {line}", file=sys.stderr)
                    self.log_line.clear()
            for kind, name in self.names.items():
                if fd.name == name:
                    self.values[kind] = fd.decode(payload)
                    self.seen_at[kind] = time.monotonic()
                    if kind == "state" and self.requested is not None:
                        for i in range(4):
                            self.peak_applied[i] = max(self.peak_applied[i], abs(self.values[kind][f"applied_m{i}"]))

    def healthy(self):
        now = time.monotonic()
        if any(k not in self.values or now - self.seen_at[k] > .5 for k in self.names):
            return False
        hb, diag = self.values["hb"], self.values["diag"]
        bits = self.proto.enums["motor_selftest"]["values"]
        expected = sum(bits.values())
        return (hb["protocol_hash"] == self.proto.hash and diag["passed"] == expected and
                diag["failed"] == 0 and diag["output_errors"] == 0 and
                not (diag["flags"] & self.proto.enums["motor_flag"]["values"]["OUTPUT_FAULT"]))

    def command(self, duty):
        self.transport.send("MOTOR_CMD", **{f"m{i}": duty[i] for i in range(4)})

    def session_ready(self):
        if not self.healthy():
            return False
        flags = self.proto.enums["motor_flag"]["values"]
        blocked = flags["PROTOCOL_BLOCKED"] | flags["CMD_TIMEOUT"] | flags["OUTPUT_FAULT"]
        # A matching heartbeat hash is not acknowledgement of MOTOR_SESSION.
        # Require BOTH status frames to confirm the session and fresh command.
        return not ((self.values["state"]["flags"] | self.values["diag"]["flags"]) & blocked)

    def session(self):
        self.transport.send("MOTOR_SESSION", target=self.target,
                            protocol_hash=self.proto.hash, magic=MAGIC_SESSION)

    def wait_disarmed(self, timeout=1.0):
        requested_at = time.monotonic()
        deadline = requested_at + timeout
        while time.monotonic() < deadline:
            self.poll()
            state = self.values.get("state", {})
            if (self.healthy() and self.seen_at.get("state", 0) >= requested_at and
                    state.get("enable_mask") == 0 and
                    all(state.get(f"applied_m{i}") == 0 for i in range(4))):
                return True
        return False

    def snapshot(self):
        decoder = dict(vars(self.transport.decoder.stats))
        observation = ({k: v - self.decoder_acquisition[k] for k, v in decoder.items()}
                       if self.decoder_acquisition is not None else None)
        return {"node_id": self.target, "protocol_hash_host": self.proto.hash,
                "healthy": self.healthy(), "frames": self.values,
                "session_ready": self.session_ready(),
                "ages_s": {k: time.monotonic() - t for k, t in self.seen_at.items()},
                "decoder": decoder, "decoder_acquisition": self.decoder_acquisition,
                "decoder_observation": observation, "invalid_dlc": self.invalid,
                "requested": self.requested, "peak_applied": self.peak_applied,
                "esp_logs": list(self.logs)}

    def check_selection(self, mask, duty):
        state = self.values["state"]
        if state["enable_mask"] != mask:
            raise RuntimeError("masque d'armement inattendu : arret, aucun rearmement automatique")
        for i, wanted in enumerate(duty):
            actual = state[f"applied_m{i}"]
            if (not (mask & (1 << i)) or wanted == 0) and actual != 0:
                raise RuntimeError(f"sortie inattendue m{i}={actual} : arret")
            if actual * wanted < 0:
                raise RuntimeError(f"sens inattendu m{i}={actual} : arret")

    def validate(self, args):
        # Acquire matching telemetry first. ROM/bootloader text is emitted at
        # another baud rate on UART0; retain its counters separately, then
        # require a full clean observation window after synchronization.
        end = time.monotonic() + 3
        self.decoder_acquisition = None
        next_tx = 0
        while time.monotonic() < end:
            now = time.monotonic()
            if now >= next_tx:
                if not args.self_test:
                    self.session()
                    self.command(ZERO)
                next_tx = now + .02
            self.poll()
            if args.self_test:
                state = self.values.get("state", {})
                if state.get("enable_mask", 0) or any(state.get(f"applied_m{i}", 0) for i in range(4)):
                    return False
                if self.decoder_acquisition is None:
                    if self.healthy():
                        self.decoder_acquisition = dict(vars(self.transport.decoder.stats))
                        end = time.monotonic() + args.seconds
                elif (not self.healthy() or self.invalid or any(
                        getattr(self.transport.decoder.stats, k) != self.decoder_acquisition[k]
                        for k in ("crc_errors", "format_errors", "overflows"))):
                    return False
            if not args.self_test and self.session_ready():
                state = self.values["state"]
                if state["enable_mask"] == 0 and all(state[f"applied_m{i}"] == 0 for i in range(4)):
                    return True
        if args.self_test:
            state = self.values.get("state", {})
            decoder = self.snapshot()["decoder_observation"]
            return (decoder is not None and self.healthy() and state.get("enable_mask") == 0 and
                    all(state.get(f"applied_m{i}") == 0 for i in range(4)) and
                    not (decoder["crc_errors"] or decoder["format_errors"] or decoder["overflows"] or self.invalid))
        return False

    def run(self, args):
        # Only arm after fresh, zero output telemetry and a matching self-test.
        if not self.validate(args):
            raise RuntimeError("validation echouee : identite, hash, self-test ou telemetrie absente/perimee")
        if args.self_test:
            return
        mask = args.enable if args.enable is not None else 0
        if mask & ~self.values["diag"]["configured_mask"]:
            raise RuntimeError("le masque demande inclut une roue non configuree sur ce noeud")
        if mask:
            arm_requested_at = time.monotonic()
            self.transport.send("MOTOR_ENABLE", enable_mask=mask, magic=MAGIC_ENABLE)
            # Wait for acknowledgement while maintaining a zero command.
            deadline = time.monotonic() + 1
            while time.monotonic() < deadline:
                self.command(ZERO)
                self.poll()
                if (self.session_ready() and self.seen_at["state"] >= arm_requested_at and
                        self.values["state"]["enable_mask"] == mask):
                    break
                time.sleep(.02)
            else:
                raise RuntimeError("armement refuse par le firmware")
        duty = args.duty or ZERO
        self.requested = {"enable_mask": mask, "duty": list(duty)}
        start = time.monotonic()
        next_tx = next_session = next_render = 0
        while not args.duty or args.seconds == 0 or time.monotonic() - start < args.seconds:
            now = time.monotonic()
            if now >= next_session:
                self.session()
                next_session = now + 1
            if now >= next_tx:
                self.command(duty)
                next_tx = now + .02
            self.poll()
            if not self.session_ready():
                raise RuntimeError("telemetrie perdue, hash divergent ou defaut sortie : arret")
            self.check_selection(mask, duty)
            if now >= next_render:
                next_render = now + .25
                print(json.dumps(self.snapshot(), ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--device", default="/dev/ttyUSB1")
    ap.add_argument("--baud", type=int, default=921600)
    ap.add_argument("--node", choices=("front", "rear"), default="front",
                    help="le profil bench4 utilise l'identite front")
    ap.add_argument("--transport", choices=("serial", "can"), default="serial")
    ap.add_argument("--interface", default="can0")
    reset = ap.add_mutually_exclusive_group()
    reset.add_argument("--reset", dest="no_reset", action="store_false",
                       help="demander un reset de l'ESP a l'ouverture (puissance moteur coupee)")
    reset.add_argument("--no-reset", dest="no_reset", action="store_true",
                       help="ne pas demander de reset a l'ouverture (defaut)")
    ap.set_defaults(no_reset=True)
    ap.add_argument("--logs", action="store_true", help="afficher les diagnostics emis par l'ESP")
    ap.add_argument("--enable", type=lambda v: int(v, 0))
    ap.add_argument("--duty", type=float, nargs=4)
    ap.add_argument("--seconds", type=float, default=3)
    ap.add_argument("--estop", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--report", type=Path, help="sauvegarder le resultat JSON")
    args = ap.parse_args()
    if args.enable is not None and not 0 <= args.enable <= 15:
        ap.error("--enable doit etre un masque 0..15")
    if not math.isfinite(args.seconds) or args.seconds < 0 or (args.self_test and args.seconds == 0):
        ap.error("--seconds doit etre fini, positif pour --self-test")
    if args.duty and any(not math.isfinite(v) or abs(v) > 1 for v in args.duty):
        ap.error("consignes finies dans [-1,1] requises")
    if args.duty and any(args.duty) and not args.enable:
        ap.error("une consigne non nulle exige --enable")
    if args.duty and any(v and not (args.enable & (1 << i)) for i, v in enumerate(args.duty)):
        ap.error("une consigne non nulle vise une roue non autorisee")
    if args.self_test and (args.enable is not None or args.duty or args.estop):
        ap.error("--self-test observe uniquement : incompatible avec --enable/--duty/--estop")
    proto = Protocol()
    transport = None
    bench = None
    status = 0
    shutdown_confirmed = None
    try:
        transport = Transport(args, proto)
        bench = Bench(proto, transport, args.node)
        bench.show_logs = args.logs
        if args.estop:
            transport.send("ESTOP_REQUEST", magic=MAGIC_ESTOP)
        else:
            bench.run(args)
    except KeyboardInterrupt:
        status = 130
    except Exception as exc:
        print(f"ECHEC : {exc}", file=sys.stderr)
        status = 1
    finally:
        if transport:
            if not args.self_test:
                try:
                    # Disarm ALL bench wheels. Best effort if the cable is gone;
                    # the firmware watchdog remains responsible for the timeout.
                    for _ in range(3):
                        transport.send("MOTOR_ENABLE", enable_mask=0, magic=MAGIC_ENABLE)
                        if bench:
                            bench.command(ZERO)
                        time.sleep(.02)
                    shutdown_confirmed = bench.wait_disarmed() if bench else False
                    if not shutdown_confirmed:
                        print("Desarmement non confirme par une telemetrie fraiche", file=sys.stderr)
                        status = status or 1
                except Exception as exc:
                    print(f"Arret non confirme sur liaison : {exc}", file=sys.stderr)
                    status = status or 1
            if bench:
                result = bench.snapshot()
                result["exit_code"] = status
                result["shutdown_confirmed"] = shutdown_confirmed
                print(json.dumps(result, ensure_ascii=False, indent=2))
                try:
                    if args.report:
                        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
                finally:
                    transport.close()
            else:
                transport.close()
    return status

if __name__ == "__main__":
    raise SystemExit(main())
