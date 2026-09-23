import os

from conftest import KEYS, frame, wire
from meshaid_gateway.codes import Codes
from meshaid_gateway.config import Config
from meshaid_gateway.ingest import IngestPipeline
from meshaid_gateway.protocol_bridge import MsgType, RateLimiter
from meshaid_gateway.store import Store


def test_accepts_valid_frame_and_stores_it(pipeline, store):
    out = pipeline.process(frame(wire(MsgType.RESOURCE_REQUEST, seq=7), from_node=0xAB, hops=2))
    assert out.status == "accepted"
    assert out.security_event is None
    m = out.message
    assert (m["hp_id"], m["seq"], m["msg_type"]) == (1, 7, "RESOURCE_REQUEST")
    assert m["fields"]["quantity"] == 10
    assert (m["from_node"], m["hops"], m["ack_state"]) == (0xAB, 2, "new")
    assert store.list_messages()[0]["id"] == m["id"]


def test_duplicate_retransmission_is_suppressed(pipeline, store):
    w = wire(seq=1)
    assert pipeline.process(frame(w)).status == "accepted"
    out = pipeline.process(frame(w))
    assert out.status == "duplicate"
    assert out.message is None
    assert out.security_event["kind"] == "duplicate"
    assert len(store.list_messages()) == 1


def test_out_of_order_within_window_is_accepted(pipeline):
    assert pipeline.process(frame(wire(seq=10))).status == "accepted"
    assert pipeline.process(frame(wire(seq=8))).status == "accepted"


def test_spoofed_frame_with_wrong_key_is_rejected(pipeline, store):
    out = pipeline.process(frame(wire(MsgType.MEDICAL_URGENT, key=os.urandom(32))))
    assert out.status == "unauthentic"
    assert out.security_event["severity"] == "alert"
    assert store.list_messages() == []


def test_unprovisioned_help_point_is_rejected(pipeline):
    w = wire(hp_id=1, key=os.urandom(32))
    w = w[:2] + bytes([99]) + w[3:]
    out = pipeline.process(frame(w))
    assert out.status == "unknown_node"
    assert out.security_event["hp_id"] == 99


def test_malformed_frames_never_crash(pipeline, store):
    good = wire(seq=1)
    cases = [b"", os.urandom(5), good[:20], bytes([1, 9, 1]) + os.urandom(16), os.urandom(200)]
    for w in cases:
        out = pipeline.process(frame(w))
        assert out.message is None, w
        assert out.security_event is not None
    assert store.list_messages() == []
    assert {e["kind"] for e in store.list_security_events()} <= {"malformed", "unknown_node", "unauthentic"}


def test_stale_frame_is_delivered_flagged(pipeline):
    assert pipeline.process(frame(wire(seq=500))).status == "accepted"
    out = pipeline.process(frame(wire(seq=100)))
    assert out.status == "flagged_stale"
    assert out.message["verify_status"] == "flagged_stale"
    assert out.security_event["kind"] == "stale"


def test_rate_limit_applies_after_authentication(pipeline, store):
    for seq in range(1, 6):
        assert pipeline.process(frame(wire(seq=seq))).status == "accepted"
    out = pipeline.process(frame(wire(seq=6)))
    assert out.status == "rate_limited"
    assert "CHECKIN" in out.security_event["detail"]
    assert len(store.list_messages()) == 5


def test_spoofs_do_not_drain_real_help_point_budget(pipeline):
    for _ in range(50):
        assert pipeline.process(frame(wire(seq=1, key=os.urandom(32)))).status == "unauthentic"
    assert pipeline.process(frame(wire(seq=1))).status == "accepted"


def test_replay_rejected_after_gateway_restart(tmp_path):
    codes = Codes(Config().codes_path)
    db = tmp_path / "restart.db"
    first = Store(db)
    w_old, w_new = wire(seq=1), wire(seq=200)
    p1 = IngestPipeline(KEYS, first, codes)
    assert p1.process(frame(w_old)).status == "accepted"
    assert p1.process(frame(w_new)).status == "accepted"
    first.close()

    second = Store(db)
    p2 = IngestPipeline(KEYS, second, codes)  # fresh ReplayGuard, re-seeded from the DB
    assert p2.process(frame(w_new)).status == "duplicate"
    assert p2.process(frame(w_old)).status == "duplicate"  # outside the window: caught by the DB backstop
    assert p2.process(frame(wire(seq=201))).status == "accepted"
    second.close()


def test_priority_orders_medical_then_resources_then_checkins(pipeline, store):
    pipeline.process(frame(wire(MsgType.CHECKIN, seq=1)))
    pipeline.process(frame(wire(MsgType.RESOURCE_REQUEST, values={**_res(urgency=1)}, seq=2)))
    pipeline.process(frame(wire(MsgType.MEDICAL_URGENT, values={**_med(severity=1)}, seq=3)))
    pipeline.process(frame(wire(MsgType.RESOURCE_REQUEST, values={**_res(urgency=3)}, seq=4)))
    order = [(m["msg_type"], m["seq"]) for m in store.list_messages(sort="priority")]
    assert order == [("MEDICAL_URGENT", 3), ("RESOURCE_REQUEST", 4), ("RESOURCE_REQUEST", 2), ("CHECKIN", 1)]


def _res(urgency):
    return {"resource_type": 2, "quantity": 1, "urgency": urgency, "notes": ""}


def _med(severity):
    return {"severity": severity, "condition_code": 1, "patient_name": "", "patient_age": 5}


def test_rate_limits_are_per_help_point(store, codes):
    p = IngestPipeline(KEYS, store, codes, rate_limiter=RateLimiter(capacity=1, refill_seconds=3600))
    assert p.process(frame(wire(hp_id=1, seq=1))).status == "accepted"
    assert p.process(frame(wire(hp_id=1, seq=2))).status == "rate_limited"
    assert p.process(frame(wire(hp_id=2, seq=1))).status == "accepted"
