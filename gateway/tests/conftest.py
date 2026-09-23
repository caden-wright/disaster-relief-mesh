import time

import pytest

from meshaid_gateway.codes import Codes
from meshaid_gateway.config import Config
from meshaid_gateway.ingest import IngestPipeline
from meshaid_gateway.protocol_bridge import MsgType, RateLimiter, encode_message
from meshaid_gateway.radio import RadioFrame
from meshaid_gateway.store import Store

KEYS = {1: b"k1" * 16, 2: b"k2" * 16}
CHECKIN = {"status": 1, "name": "", "group_size": 3}
RESOURCE = {"resource_type": 1, "quantity": 10, "urgency": 3, "notes": ""}
MEDICAL = {"severity": 3, "condition_code": 2, "patient_name": "", "patient_age": 40}


@pytest.fixture
def codes():
    return Codes(Config().codes_path)


@pytest.fixture
def store(tmp_path):
    s = Store(tmp_path / "gw.db")
    yield s
    s.close()


@pytest.fixture
def pipeline(store, codes):
    return IngestPipeline(KEYS, store, codes, rate_limiter=RateLimiter(capacity=5, refill_seconds=3600))


def wire(msg_type=MsgType.CHECKIN, values=None, hp_id=1, seq=1, key=None):
    default = {MsgType.CHECKIN: CHECKIN, MsgType.RESOURCE_REQUEST: RESOURCE, MsgType.MEDICAL_URGENT: MEDICAL}
    return encode_message(msg_type, seq=seq, help_point_id=hp_id, values=values or default[msg_type],
                          key=key or KEYS[hp_id])


def frame(w, from_node=0x100, hops=1, snr=5.0):
    return RadioFrame(wire=w, received_at=time.time(), from_node=from_node, hops=hops, snr=snr)
