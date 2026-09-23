import json
import os
import time

import pytest
from fastapi.testclient import TestClient

from conftest import KEYS, wire
from meshaid_gateway.api import create_app
from meshaid_gateway.config import Config
from meshaid_gateway.protocol_bridge import MsgType
from meshaid_gateway.radio import SimSource


@pytest.fixture
def client(tmp_path):
    keys = tmp_path / "keys.json"
    keys.write_text(json.dumps({str(k): v.hex() for k, v in KEYS.items()}))
    config = Config(radio="sim", key_store_path=keys, db_path=tmp_path / "api.db",
                    dashboard_dist=tmp_path / "no-dist", shelters={"1": "Shelter A"})
    app = create_app(config, radio=SimSource(emit_heartbeats=False))
    with TestClient(app) as c:
        yield c


def inject(client, w, from_node=0x0A000101):
    r = client.post("/api/dev/inject", json={"wire_hex": w.hex(), "from_node": from_node, "hops": 2, "snr": 4.0})
    assert r.status_code == 200


def receive_until(ws, kind, limit=20):
    for _ in range(limit):
        msg = ws.receive_json()
        if msg["type"] == kind:
            return msg
    raise AssertionError(f"no {kind} event")


def test_message_pushed_over_websocket_within_5s(client):
    with client.websocket_connect("/ws") as ws:
        t0 = time.time()
        inject(client, wire(MsgType.MEDICAL_URGENT, seq=1))
        msg = receive_until(ws, "message")
    data = msg["data"]
    assert data["msg_type"] == "MEDICAL_URGENT"
    assert data["shelter"] == "Shelter A"
    assert data["summary"] == "Critical: Breathing difficulty"
    assert msg["sent_at"] - data["received_at"] < 5  # SRS 5.6: uplink arrival -> dashboard
    assert time.time() - t0 < 5


def test_rejections_go_to_security_feed_not_messages(client):
    with client.websocket_connect("/ws") as ws:
        inject(client, wire(key=os.urandom(32)))
        ev = receive_until(ws, "security_event")
    assert ev["data"]["kind"] == "unauthentic"
    assert client.get("/api/messages").json() == []
    assert client.get("/api/security-events").json()[0]["kind"] == "unauthentic"


def test_filters_sort_and_ack(client):
    with client.websocket_connect("/ws") as ws:
        inject(client, wire(MsgType.CHECKIN, seq=1))
        inject(client, wire(MsgType.MEDICAL_URGENT, seq=2))
        inject(client, wire(MsgType.RESOURCE_REQUEST, hp_id=2, seq=1))
        for _ in range(3):
            receive_until(ws, "message")

        msgs = client.get("/api/messages").json()
        assert [m["msg_type"] for m in msgs] == ["MEDICAL_URGENT", "RESOURCE_REQUEST", "CHECKIN"]
        assert [m["hp_id"] for m in client.get("/api/messages", params={"hp_id": 2}).json()] == [2]
        assert len(client.get("/api/messages", params={"type": "CHECKIN"}).json()) == 1

        mid = msgs[0]["id"]
        r = client.post(f"/api/messages/{mid}/ack", json={"state": "acknowledged", "note": "team dispatched"})
        assert r.status_code == 200 and r.json()["ack_state"] == "acknowledged"
        upd = receive_until(ws, "message_update")
        assert upd["data"]["id"] == mid

    assert client.post(f"/api/messages/{mid}/ack", json={"state": "bogus"}).status_code == 422
    assert client.post("/api/messages/9999/ack", json={"state": "resolved"}).status_code == 404
    assert client.get("/api/stats").json()["open_medical"] == 1


def test_nodes_reported_with_health(client):
    nodes = client.get("/api/nodes").json()
    by_short = {n["short_name"]: n for n in nodes}
    assert by_short["GW"]["role"] == "gateway"
    assert by_short["HP1"]["status"] == "up"


def test_meta_exposes_code_tables(client):
    meta = client.get("/api/meta").json()
    assert meta["codes"]["msg_type"]["3"]["key"] == "MEDICAL_URGENT"
    assert meta["help_points"] == [1, 2]
