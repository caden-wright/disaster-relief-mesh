import unittest
import time
from schema import MsgType, encode_message, decode_message, BYTE_CEILING
from replay_guard import ReplayGuard, ReplayResult
from rate_limiter import RateLimiter
from gateway import Gateway

class TestSchema(unittest.TestCase):
    def setUp(self):
        self.key = b"test_secret_key_1234567890123456"
        self.hp_id = 1

    def test_roundtrip_checkin(self):
        values = {"status": 1, "name": "Alice", "group_size": 4}
        wire = encode_message(MsgType.CHECKIN, seq=1, help_point_id=self.hp_id, values=values, key=self.key)
        self.assertLessEqual(len(wire), BYTE_CEILING)
        decoded = decode_message(wire, self.key)
        self.assertTrue(decoded["authentic"])
        self.assertEqual(decoded["fields"]["name"], "Alice")
        self.assertEqual(decoded["help_point_id"], self.hp_id)

    def test_tamper_detection(self):
        values = {"severity": 3, "condition_code": 1, "patient_name": "Bob", "patient_age": 30}
        wire = encode_message(MsgType.MEDICAL_URGENT, seq=5, help_point_id=self.hp_id, values=values, key=self.key)
        tampered_wire = wire[:-1] + bytes([wire[-1] ^ 0xFF])
        decoded = decode_message(tampered_wire, self.key)
        self.assertFalse(decoded["authentic"])

    def test_wrong_key_rejection(self):
        values = {"status": 1, "name": "Eve", "group_size": 2}
        wire = encode_message(MsgType.CHECKIN, seq=10, help_point_id=self.hp_id, values=values, key=self.key)
        decoded = decode_message(wire, b"wrong_key_wrong_key_wrong_key_123")
        self.assertFalse(decoded["authentic"])

class TestReplayGuard(unittest.TestCase):
    def setUp(self):
        self.guard = ReplayGuard(window_size=4)

    def test_accept_and_duplicate(self):
        self.assertEqual(self.guard.evaluate("node1", 1), ReplayResult.ACCEPTED)
        self.assertEqual(self.guard.evaluate("node1", 1), ReplayResult.DUPLICATE)

    def test_out_of_order_window(self):
        self.assertEqual(self.guard.evaluate("node1", 5), ReplayResult.ACCEPTED)
        self.assertEqual(self.guard.evaluate("node1", 3), ReplayResult.ACCEPTED)
        self.assertEqual(self.guard.evaluate("node1", 3), ReplayResult.DUPLICATE)

    def test_stale_flagging(self):
        self.assertEqual(self.guard.evaluate("node1", 10), ReplayResult.ACCEPTED)
        self.assertEqual(self.guard.evaluate("node1", 1), ReplayResult.FLAGGED_STALE)
        self.assertEqual(self.guard.evaluate("node1", 1), ReplayResult.DUPLICATE)

class TestGatewayPipeline(unittest.TestCase):
    def setUp(self):
        self.key_store = {1: b"hp1_key_1234567890123456789012"}
        self.gw = Gateway(key_store=self.key_store, rate_limiter=RateLimiter(capacity=2, refill_seconds=10))

    def test_full_accept_pipeline(self):
        wire = encode_message(MsgType.CHECKIN, seq=1, help_point_id=1, values={"status": 1, "name": "Test", "group_size": 1}, key=self.key_store[1])
        result = self.gw.process(wire)
        self.assertEqual(result.status, "accepted")

    def test_rate_limit_blocks(self):
        wire = encode_message(MsgType.CHECKIN, seq=1, help_point_id=1, values={"status": 1, "name": "Test", "group_size": 1}, key=self.key_store[1])
        self.gw.process(wire)
        self.gw.process(wire)
        result = self.gw.process(wire)
        self.assertEqual(result.status, "rate_limited")

if __name__ == "__main__":
    unittest.main()
