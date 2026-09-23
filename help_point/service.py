import threading
from pathlib import Path

from .codebook import Codebook
from .config import Config
from .protocol_bridge import (
    MsgType,
    QueueDrainer,
    SequenceCounter,
    StoreAndForwardQueue,
    encode_message,
)
from .radio import RadioBase


# Queue implementation sorts ascending, so lower number = higher queue priority.
QUEUE_PRIORITY = {
    MsgType.MEDICAL_URGENT: 0,
    MsgType.RESOURCE_REQUEST: 1,
    MsgType.CHECKIN: 2,
}


class HelpPointService:
    def __init__(
        self,
        config: Config,
        radio: RadioBase,
        drain_interval: float = 2.0
    ):
        self.config = config
        self.radio = radio or make_radio(
            config.radio,
            gateway_url=config.gateway_dev_url,
        )

        config.data_dir.mkdir(parents=True, exist_ok=True)

        self.codebook = Codebook(config.codes_path)
        self.counter = SequenceCounter(str(config.counter_path))
        self.queue = StoreAndForwardQueue(str(config.queue_path))
        self.key = self._load_key(config.key_path)

        self.drainer = QueueDrainer(
            self.queue,
            self.radio,
            check_interval=drain_interval
        )   
        self.drainer.start()

        self._send_lock = threading.Lock()

    @staticmethod
    def _load_key(path: Path) -> bytes | None:
        path = Path(path)
        if not path.exists():
            return None
        return path.read_bytes()

    def close(self):
        self.drainer.stop()
        self.radio.close()

    def status(self) -> dict:
        self.codebook.reload()
        return {
            "help_point_id": self.config.help_point_id,
            "radio": self.radio.describe(),
            "mesh_connected": self.radio.is_connected(),
            "queue_depth": len(self.queue.get_pending()),
            "codebook_available": self.codebook.available,
            "codes_path": str(self.config.codes_path),
            "key_available": self.key is not None,
            "key_path": str(self.config.key_path),
        }

    def submit_browser_request(self, request: dict) -> dict:
        if self.key is None:
            raise RuntimeError(
                f"Help Point key is missing: {self.config.key_path}. "
                "Run provision_keys.py or set MESHAID_HELP_POINT_KEY."
            )

        msg_type, values = self._translate_request(request)
        return self._encode_and_submit(msg_type, values)

    def queue_status(self) -> dict:
                pending = self.queue.get_pending()
    
                return {
                    "queue_depth": len(pending),
                    "items": [
                        {
                            "index": index,
                            "size_bytes": len(wire),
                        }
                        for index, wire in enumerate(pending, start=1)
                    ],
                }

    def _translate_request(self, request: dict):
        request_type = str(request.get("type", "")).strip().lower()

        if request_type in {"safety_checkin", "checkin", "check-in"}:
            status = self.codebook.code_for("checkin_status", request.get("status", "safe"))
            people = self._positive_int(request.get("people"), "people", max_value=255)
            return MsgType.CHECKIN, {
                "status": status,
                "name": str(request.get("name", ""))[:20],
                "group_size": people,
            }

        if request_type in {"resource_request", "resource", "resources"}:
            resource = self.codebook.code_for("resource_type", request.get("resource"))
            urgency = self.codebook.code_for("urgency", request.get("urgency"))

            # Current frontend asks for "number of people", while the wire schema calls
            # this field "quantity". Until the team confirms semantics, quantity can be
            # supplied explicitly; otherwise we preserve current UI behavior.
            quantity_source = request.get("quantity", request.get("people"))
            quantity = self._positive_int(quantity_source, "quantity", max_value=65535)

            return MsgType.RESOURCE_REQUEST, {
                "resource_type": resource,
                "quantity": quantity,
                "urgency": urgency,
                "notes": str(request.get("notes", ""))[:20],
            }

        if request_type in {"medical", "medical_urgent", "medical_request"}:
            # Do not guess a condition_code from "conscious"/"breathing".
            # Current frontend and protocol contract disagree here, so require
            # protocol-supported values until the team confirms the mapping.
            severity = self.codebook.code_for("severity", request.get("severity"))
            condition = request.get("condition_code", request.get("condition"))

            if condition in (None, ""):
                raise ValueError(
                    "Medical request needs condition or condition_code. "
                    "The current Medical UI and service_protocol schema do not yet agree "
                    "on how conscious/breathing/location map to condition_code."
                )

            condition_code = self.codebook.code_for("condition_code", condition)
            patient_age = self._nonnegative_int(
                request.get("patient_age", 0), "patient_age", max_value=255
            )

            return MsgType.MEDICAL_URGENT, {
                "severity": severity,
                "condition_code": condition_code,
                "patient_name": str(request.get("patient_name", ""))[:20],
                "patient_age": patient_age,
            }

        raise ValueError(f"Unsupported request type: {request.get('type')!r}")

    def _encode_and_submit(self, msg_type: MsgType, values: dict) -> dict:
        seq = self.counter.next()

        wire = encode_message(
            msg_type,
            seq=seq,
            help_point_id=self.config.help_point_id,
            values=values,
            key=self.key,
        )

        result = self.queue.submit(
            wire,
            priority=QUEUE_PRIORITY[msg_type],
            mesh_available=self.radio.is_connected(),
        )

        wire_to_send = result.get("wire_to_send")

        if wire_to_send is not None:
            # Serialize immediate writes so two browser submissions do not write to
            # the radio at the same time.
            with self._send_lock:
                try:
                    self.radio.send(wire_to_send)
                except Exception:
                    # If the radio dropped between the connectivity check and send,
                    # persist the already-encoded frame rather than losing it.
                    fallback = self.queue.submit(
                        wire_to_send,
                        priority=QUEUE_PRIORITY[msg_type],
                        mesh_available=False,
                    )
                    return {
                        "status": "queued",
                        "sequence": seq,
                        "queue_depth": fallback["queue_depth"],
                        "message_type": msg_type.name,
                    }

            return {
                "status": "sent",
                "sequence": seq,
                "queue_depth": len(self.queue.get_pending()),
                "message_type": msg_type.name,
            }

        return {
            "status": "queued",
            "sequence": seq,
            "queue_depth": result["queue_depth"],
            "message_type": msg_type.name,
        }

    @staticmethod
    def _positive_int(value, name: str, max_value: int) -> int:
        try:
            value = int(value)
        except (TypeError, ValueError):
            raise ValueError(f"{name} must be an integer")
        if not 1 <= value <= max_value:
            raise ValueError(f"{name} must be between 1 and {max_value}")
        return value

    @staticmethod
    def _nonnegative_int(value, name: str, max_value: int) -> int:
        try:
            value = int(value)
        except (TypeError, ValueError):
            raise ValueError(f"{name} must be an integer")
        if not 0 <= value <= max_value:
            raise ValueError(f"{name} must be between 0 and {max_value}")
        return value
