"""Bench tooling tests without serial devices or CAN adapters."""
import argparse
from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import motor_bench
import flash_motion
from retriever_wire import Decoder, Protocol

class Clock:
    now = 100.0
    def monotonic(self): return self.now

class FakeTransport:
    def __init__(self, proto, clock):
        self.proto, self.clock = proto, clock
        self.decoder = Decoder()
        self.sent = []
        self.frames = []
    def send(self, name, **values): self.sent.append((name, values))
    def receive(self):
        self.clock.now += .005
        return self.frames
    def telemetry(self, node="front", mask=0, hash_value=None, failed=0, flags=0, configured=None):
        names = ("MOTOR_STATE_REAR" if node == "rear" else "MOTOR_STATE",
                 f"MOTOR_DIAG_{node.upper()}", f"HEARTBEAT_MOTION_{node.upper()}")
        vals = ({"enable_mask": mask, "flags": flags}, {"passed": 31, "failed": failed, "flags": flags,
                    "configured_mask": configured if configured is not None else (12 if node == "rear" else 7)},
                {"protocol_hash": self.proto.hash if hash_value is None else hash_value})
        self.frames = [(self.proto.by_name[n].id, self.proto.by_name[n].encode(v)) for n, v in zip(names, vals)]

class BenchTests(unittest.TestCase):
    def setUp(self):
        self.proto, self.clock = Protocol(), Clock()
        self.transport = FakeTransport(self.proto, self.clock)
        self.bench = motor_bench.Bench(self.proto, self.transport, "front")
    def validate(self):
        args = argparse.Namespace(seconds=.03, self_test=True)
        with patch.object(motor_bench.time, "monotonic", self.clock.monotonic):
            return self.bench.validate(args)
    def test_selftest_never_sends_command_or_arm(self):
        self.transport.telemetry()
        self.assertTrue(self.validate())
        self.assertEqual(self.transport.sent, [])

    def test_protocol_blocked_healthy_node_cannot_pass_command_validation(self):
        self.transport.telemetry(flags=40, configured=15)  # Exact reported startup state.
        with patch.object(motor_bench.time, 'monotonic', self.clock.monotonic):
            self.assertFalse(self.bench.validate(argparse.Namespace(self_test=False)))
            self.assertTrue(self.bench.healthy())
            self.assertFalse(self.bench.session_ready())
        self.assertTrue(self.transport.sent)
        self.assertTrue(all(name in ('MOTOR_SESSION', 'MOTOR_CMD') for name, _ in self.transport.sent))
        self.assertTrue(all(not any(values.values()) for name, values in self.transport.sent if name == 'MOTOR_CMD'))

    def test_session_must_be_confirmed_in_both_status_frames(self):
        self.transport.telemetry()
        self.bench.poll()
        flags = self.proto.enums['motor_flag']['values']
        for kind in ('state', 'diag'):
            for blocked in ('PROTOCOL_BLOCKED', 'CMD_TIMEOUT', 'OUTPUT_FAULT'):
                with self.subTest(kind=kind, flag=blocked), patch.dict(self.bench.values[kind], flags=flags[blocked]):
                    self.assertFalse(self.bench.session_ready())
        self.assertTrue(self.bench.session_ready())

    def test_startup_drops_sessions_until_receiver_ready_without_early_arm(self):
        self.transport.telemetry(flags=40, configured=15)
        send = self.transport.send
        sessions = 0
        mask = 0
        def receiver_starting(name, **values):
            nonlocal sessions, mask
            send(name, **values)
            if name == 'MOTOR_SESSION':
                sessions += 1
            if name == 'MOTOR_ENABLE':
                self.assertGreaterEqual(sessions, 3)
                self.assertTrue(self.bench.session_ready())
                mask = values['enable_mask']
            if name == 'MOTOR_CMD' and any(values.values()):
                self.assertEqual(mask, 8)
            self.transport.telemetry(mask=mask, flags=40 if sessions < 3 else 0, configured=15)
        args = argparse.Namespace(self_test=False, enable=8, duty=[0, 0, 0, .1], seconds=.03)
        with patch.object(self.transport, 'send', receiver_starting), \
             patch.object(motor_bench.time, 'monotonic', self.clock.monotonic), redirect_stdout(io.StringIO()):
            self.bench.run(args)
        arms = [values['enable_mask'] for name, values in self.transport.sent if name == 'MOTOR_ENABLE']
        self.assertEqual(arms, [8])
    def test_boot_noise_is_reported_separately_from_clean_observation(self):
        self.transport.telemetry()
        self.transport.decoder.stats.format_errors = 1860
        self.transport.decoder.stats.overflows = 1
        started = self.clock.now
        self.assertTrue(self.validate())
        report = self.bench.snapshot()
        self.assertEqual(report["decoder_acquisition"]["format_errors"], 1860)
        self.assertEqual(report["decoder_observation"]["format_errors"], 0)
        self.assertEqual(report["decoder_observation"]["overflows"], 0)
        self.assertGreaterEqual(self.clock.now - started, .03)
    def test_corruption_after_synchronization_fails(self):
        self.transport.telemetry()
        receive = self.transport.receive
        calls = 0
        def corrupt_later():
            nonlocal calls
            calls += 1
            if calls == 2:
                self.transport.decoder.stats.crc_errors += 1
            return receive()
        with patch.object(self.transport, "receive", corrupt_later):
            self.assertFalse(self.validate())
        self.assertEqual(self.transport.sent, [])
    def test_absent_or_wrong_peer_fails(self):
        self.assertFalse(self.validate())
        self.transport.telemetry(node="rear")
        self.assertFalse(self.validate())
    def test_hash_and_failed_selftest_block(self):
        self.transport.telemetry(hash_value=0)
        self.assertFalse(self.validate())
        self.transport.telemetry(failed=4)
        self.assertFalse(self.validate())
    def test_active_outputs_fail_observational_validation(self):
        self.transport.telemetry(mask=1)
        self.assertFalse(self.validate())
        fd = self.proto.by_name["MOTOR_STATE"]
        self.transport.telemetry()
        self.transport.frames[0] = (fd.id, fd.encode({"applied_m0": .1}))
        self.assertFalse(self.validate())
    def test_truncated_frame_is_rejected(self):
        self.transport.telemetry()
        fid, payload = self.transport.frames[0]
        self.transport.frames[0] = (fid, payload[:-1])
        self.assertFalse(self.validate())
        self.assertGreater(self.bench.invalid, 0)
    def test_stale_data_cannot_stay_healthy(self):
        self.transport.telemetry()
        with patch.object(motor_bench.time, "monotonic", self.clock.monotonic):
            self.bench.poll()
            self.assertTrue(self.bench.healthy())
            self.clock.now += .51
            self.assertFalse(self.bench.healthy())
    def test_rear_data_is_addressed_correctly(self):
        self.bench = motor_bench.Bench(self.proto, self.transport, "rear")
        self.transport.telemetry(node="rear")
        self.assertTrue(self.validate())
        self.assertEqual(self.bench.target, 3)
    def test_shutdown_requires_fresh_zero_output_acknowledgement(self):
        with patch.object(motor_bench.time, "monotonic", self.clock.monotonic):
            self.transport.telemetry(mask=1)
            self.assertFalse(self.bench.wait_disarmed(timeout=.03))
            self.transport.telemetry(mask=0)
            self.assertTrue(self.bench.wait_disarmed(timeout=.03))

    def test_movement_rejects_unselected_output_wrong_mask_and_wrong_direction(self):
        self.bench.values['state'] = dict(enable_mask=8, applied_m0=0, applied_m1=0,
                                         applied_m2=0, applied_m3=.05)
        self.bench.check_selection(8, [0, 0, 0, .1])  # Ramp need not have reached target.
        for changes in ({'applied_m0': .01}, {'enable_mask': 4}, {'applied_m3': -.01}):
            with self.subTest(changes=changes), patch.dict(self.bench.values['state'], changes):
                with self.assertRaises(RuntimeError):
                    self.bench.check_selection(8, [0, 0, 0, .1])

    def test_report_keeps_movement_peak_after_shutdown(self):
        self.bench.requested = {'enable_mask': 8, 'duty': [0, 0, 0, .1]}
        fd = self.proto.by_name['MOTOR_STATE']
        self.transport.frames = [(fd.id, fd.encode(dict(enable_mask=8, applied_m3=.1)))]
        self.bench.poll()
        self.transport.frames = [(fd.id, fd.encode(dict(enable_mask=0)))]
        self.bench.poll()
        self.assertEqual(self.bench.snapshot()['peak_applied'], [0, 0, 0, .1])

    def test_firmware_logs_are_reassembled_for_diagnostics(self):
        message = 'readback pwm=[0,0,0,102] stop_gpio_high=0x08'
        data = message.encode()
        fd = self.proto.by_name['LOG']
        for offset in range(0, len(data), 7):
            chunk = data[offset:offset+7]
            values = {f'c{i}': value for i, value in enumerate(chunk)}
            values['header'] = (2 << 5) | len(chunk) | (0x10 if offset+7 >= len(data) else 0)
            self.transport.frames.append((fd.id, fd.encode(values)))
        self.bench.poll()
        self.assertEqual(self.bench.snapshot()['esp_logs'], [message])

    def test_reset_is_only_requested_explicitly(self):
        for options, no_reset in (([], True), (['--no-reset'], True), (['--reset'], False)):
            with self.subTest(options=options), \
                 patch.object(sys, 'argv', ['motor_bench', '--self-test', *options]), \
                 patch.object(motor_bench, 'Transport', side_effect=RuntimeError('no hardware')) as hardware, \
                 redirect_stderr(io.StringIO()):
                self.assertEqual(motor_bench.main(), 1)
                self.assertEqual(hardware.call_args.args[0].no_reset, no_reset)

    def test_bad_cli_values_do_not_open_hardware(self):
        for args in (("--enable", "16"), ("--duty", "nan", "0", "0", "0"),
                     ("--duty", ".1", "0", "0", "0"), ("--self-test", "--enable", "1"),
                     ("--seconds", "nan"), ("--duty", "0", ".1", "0", "0", "--enable", "1")):
            with self.subTest(args=args), patch.object(sys, "argv", ["motor_bench", *args]), \
                 patch.object(motor_bench, "Transport") as hardware, redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit): motor_bench.main()
                hardware.assert_not_called()

class FlashTests(unittest.TestCase):
    def test_build_roles_are_isolated_and_flash_port_is_explicit(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(flash_motion, "PROJECT", Path(tmp)), \
             patch.object(flash_motion.shutil, "which", return_value="/idf/tools/idf.py"), \
             patch.dict(flash_motion.os.environ, {"IDF_PATH": "/idf"}), \
             patch.object(flash_motion.subprocess, "run") as run, redirect_stdout(io.StringIO()):
            run.return_value.returncode = 0
            for role in ("front", "rear", "bench4"):
                with patch.object(sys, "argv", ["flash_motion", role]):
                    self.assertEqual(flash_motion.main(), 0)
                cmd = run.call_args.args[0]
                self.assertIn(f"SDKCONFIG={tmp}/build/{role}-serial-{3 if role == 'bench4' else 2}-translator/sdkconfig", cmd)
                self.assertNotIn("flash", cmd)
            with patch.object(sys, "argv", ["flash_motion", "rear", "--transport", "can", "--inverted", "--flash", "--port", "/dev/test"]):
                self.assertEqual(flash_motion.main(), 0)
                self.assertEqual(run.call_args.args[0][-2:], ["build", "flash"])
                self.assertIn("/dev/test", run.call_args.args[0])
    def test_no_flash_without_explicit_port(self):
        with patch.object(sys, "argv", ["flash_motion", "front", "--flash"]), \
             patch.object(flash_motion.subprocess, "run") as run, redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit): flash_motion.main()
            run.assert_not_called()

if __name__ == "__main__": unittest.main()
