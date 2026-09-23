import json
import time

from help_point.service import HelpPointService

from fastapi.testclient import TestClient

from help_point.api import create_app
from help_point.config import Config


TEST_CODES = {
    "msg_type": {
        "1": {"key": "CHECKIN", "label": "Check-in"},
        "2": {"key": "RESOURCE_REQUEST", "label": "Resource Request"},
        "3": {"key": "MEDICAL_URGENT", "label": "Medical"},
        "4": {"key": "ACK", "label": "Acknowledgement"},
    },

    "checkin_status": {
        "1": {"key": "SAFE", "label": "Safe"},
        "2": {"key": "NEEDS_HELP", "label": "Needs Help"},
    },

    "resource_type": {
        "1": {"key": "WATER", "label": "Water"},
        "2": {"key": "FOOD", "label": "Food"},
        "3": {"key": "MEDICINE", "label": "Medicine"},
        "4": {"key": "SHELTER", "label": "Shelter"},
    },

    "urgency": {
        "1": {"key": "NORMAL", "label": "Normal"},
        "2": {"key": "HIGH", "label": "High"},
    },

    "severity": {
        "1": {"key": "MINOR", "label": "Minor"},
        "2": {"key": "SERIOUS", "label": "Serious"},
        "3": {"key": "CRITICAL", "label": "Critical"},
    },

    "condition_code": {
        "1": {"key": "OTHER", "label": "Other"},
        "2": {"key": "BLEEDING", "label": "Bleeding"},
    },

    "ack_status": {
        "1": {"key": "RECEIVED", "label": "Received"}
    }
}

class ToggleRadio:
    kind = "test"

    def __init__(self, connected=False):
        self.connected = connected
        self.sent_frames = []

    def is_connected(self):
        return self.connected

    def send(self, wire):
        if not self.connected:
            raise ConnectionError("radio offline")

        self.sent_frames.append(bytes(wire))

    def close(self):
        pass

    def describe(self):
        return "test-toggle"


def make_config(tmp_path, radio="sim"):
    codes_path = tmp_path / "codes.json"
    codes_path.write_text(
        json.dumps(TEST_CODES),
        encoding="utf-8"
    )

    key_path = tmp_path / "help_point_1.key"
    key_path.write_bytes(b"test-key-" * 4)

    return Config(
        help_point_id=1,
        radio=radio,
        data_dir=tmp_path / "data",
        codes_path=codes_path,
        key_path=key_path,
    )


def test_status_reports_sim_connected(tmp_path):
    config = make_config(tmp_path, radio="sim")

    app = create_app(config)

    with TestClient(app) as client:
        response = client.get("/api/status")

        assert response.status_code == 200

        data = response.json()

        assert data["help_point_id"] == 1
        assert data["mesh_connected"] is True
        assert data["queue_depth"] == 0
        assert data["codebook_available"] is True
        assert data["key_available"] is True


def test_checkin_sends_in_sim_mode(tmp_path):
    config = make_config(tmp_path, radio="sim")

    app = create_app(config)

    with TestClient(app) as client:
        response = client.post(
            "/api/messages",
            json={
                "type": "safety_checkin",
                "status": "safe",
                "people": 3,
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["status"] == "sent"
        assert data["sequence"] == 1
        assert data["queue_depth"] == 0
        assert data["message_type"] == "CHECKIN"


def test_resource_sends_in_sim_mode(tmp_path):
    config = make_config(tmp_path, radio="sim")

    app = create_app(config)

    with TestClient(app) as client:
        response = client.post(
            "/api/messages",
            json={
                "type": "resource_request",
                "resource": "Water",
                "people": 4,
                "urgency": "High",
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["status"] == "sent"
        assert data["sequence"] == 1
        assert data["message_type"] == "RESOURCE_REQUEST"


def test_offline_request_is_queued(tmp_path):
    config = make_config(tmp_path, radio="offline")

    app = create_app(config)

    with TestClient(app) as client:
        response = client.post(
            "/api/messages",
            json={
                "type": "safety_checkin",
                "status": "safe",
                "people": 2,
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["status"] == "queued"
        assert data["queue_depth"] == 1

        status = client.get("/api/status").json()

        assert status["mesh_connected"] is False
        assert status["queue_depth"] == 1


def test_sequence_counter_increments(tmp_path):
    config = make_config(tmp_path, radio="sim")

    app = create_app(config)

    with TestClient(app) as client:
        first = client.post(
            "/api/messages",
            json={
                "type": "safety_checkin",
                "status": "safe",
                "people": 1,
            },
        ).json()

        second = client.post(
            "/api/messages",
            json={
                "type": "safety_checkin",
                "status": "safe",
                "people": 1,
            },
        ).json()

        assert first["sequence"] == 1
        assert second["sequence"] == 2


def test_missing_codebook_rejected_cleanly(tmp_path):
    key_path = tmp_path / "help_point_1.key"
    key_path.write_bytes(b"test-key-" * 4)

    config = Config(
        help_point_id=1,
        radio="sim",
        data_dir=tmp_path / "data",
        codes_path=tmp_path / "does-not-exist.json",
        key_path=key_path,
    )

    app = create_app(config)

    with TestClient(app) as client:
        response = client.post(
            "/api/messages",
            json={
                "type": "safety_checkin",
                "status": "safe",
                "people": 1,
            },
        )

        assert response.status_code == 503
        assert "Missing codebook" in response.json()["detail"]
        
        
def test_offline_queue_survives_restart(tmp_path):
    config = make_config(tmp_path, radio="offline")

    app1 = create_app(config)

    with TestClient(app1) as client:
        response = client.post(
            "/api/messages",
            json={
                "type": "safety_checkin",
                "status": "safe",
                "people": 2,
            },
        )

        assert response.status_code == 200
        assert response.json()["status"] == "queued"
        assert response.json()["queue_depth"] == 1

    # Simulate restarting the Help Point service.
    app2 = create_app(config)

    with TestClient(app2) as client:
        status = client.get("/api/status").json()

        assert status["mesh_connected"] is False
        assert status["queue_depth"] == 1
        

def test_queue_drains_when_mesh_returns(tmp_path):
    config = make_config(tmp_path, radio="offline")

    radio = ToggleRadio(connected=False)

    service = HelpPointService(
        config,
        radio,
        drain_interval=0.05
    )

    try:
        # Mesh is unavailable, so the message should be persisted.
        result = service.submit_browser_request(
            {
                "type": "safety_checkin",
                "status": "safe",
                "people": 3,
            }
        )

        assert result["status"] == "queued"
        assert result["queue_depth"] == 1
        assert len(service.queue.get_pending()) == 1
        assert radio.sent_frames == []

        # Simulate Meshtastic connectivity returning.
        radio.connected = True

        deadline = time.monotonic() + 2.0

        while (
            len(service.queue.get_pending()) > 0
            and time.monotonic() < deadline
        ):
            time.sleep(0.02)

        assert len(radio.sent_frames) == 1
        assert len(service.queue.get_pending()) == 0

    finally:
        service.close()
        
        
def test_multiple_offline_requests_increase_queue_depth(tmp_path):
    config = make_config(tmp_path, radio="offline")

    app = create_app(config)

    with TestClient(app) as client:
        for people in (1, 2, 3):
            response = client.post(
                "/api/messages",
                json={
                    "type": "safety_checkin",
                    "status": "safe",
                    "people": people,
                },
            )

            assert response.status_code == 200
            assert response.json()["status"] == "queued"

        status = client.get("/api/status").json()

        assert status["queue_depth"] == 3
        
def test_queue_endpoint_reports_pending_items(tmp_path):
    config = make_config(tmp_path, radio="offline")

    app = create_app(config)

    with TestClient(app) as client:
        client.post(
            "/api/messages",
            json={
                "type": "safety_checkin",
                "status": "safe",
                "people": 2,
            },
        )

        response = client.get("/api/queue")

        assert response.status_code == 200

        data = response.json()

        assert data["queue_depth"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["size_bytes"] > 0
        
class FailingRadio:
    kind = "test-failing"

    def is_connected(self):
        return True

    def send(self, wire):
        raise ConnectionError("simulated radio failure")

    def close(self):
        pass

    def describe(self):
        return "test-failing"
    
def test_send_failure_falls_back_to_queue(tmp_path):
    config = make_config(tmp_path, radio="sim")

    radio = FailingRadio()

    service = HelpPointService(
        config,
        radio,
        drain_interval=10.0
    )

    try:
        result = service.submit_browser_request(
            {
                "type": "safety_checkin",
                "status": "safe",
                "people": 1,
            }
        )

        assert result["status"] == "queued"
        assert result["queue_depth"] == 1
        assert len(service.queue.get_pending()) == 1

    finally:
        service.close()
        
def test_unsupported_request_type_returns_422(tmp_path):
    config = make_config(tmp_path, radio="sim")

    app = create_app(config)

    with TestClient(app) as client:
        response = client.post(
            "/api/messages",
            json={
                "type": "banana_emergency"
            },
        )

        assert response.status_code == 422
        assert "Unsupported request type" in response.json()["detail"]
        
def test_invalid_people_count_returns_422(tmp_path):
    config = make_config(tmp_path, radio="sim")

    app = create_app(config)

    with TestClient(app) as client:
        response = client.post(
            "/api/messages",
            json={
                "type": "safety_checkin",
                "status": "safe",
                "people": 0,
            },
        )

        assert response.status_code == 422
        assert "people must be between" in response.json()["detail"]
        
def test_queue_priority_places_resource_before_checkin(tmp_path):
    config = make_config(tmp_path, radio="offline")

    radio = ToggleRadio(connected=False)

    service = HelpPointService(
        config,
        radio,
        drain_interval=10.0
    )

    try:
        checkin = service.submit_browser_request(
            {
                "type": "safety_checkin",
                "status": "safe",
                "people": 1,
            }
        )

        resource = service.submit_browser_request(
            {
                "type": "resource_request",
                "resource": "Water",
                "people": 2,
                "urgency": "High",
            }
        )

        assert checkin["status"] == "queued"
        assert resource["status"] == "queued"

        pending = service.queue.get_pending()

        assert len(pending) == 2

        # The resource request has higher queue priority and should move
        # ahead of the earlier check-in.
        from help_point.protocol_bridge import decode_message

        first = decode_message(pending[0], service.key)
        second = decode_message(pending[1], service.key)

        assert first["msg_type"].name == "RESOURCE_REQUEST"
        assert second["msg_type"].name == "CHECKIN"

    finally:
        service.close()