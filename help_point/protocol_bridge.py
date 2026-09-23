"""Single import point for service_protocol/, which uses flat imports."""

import sys
from pathlib import Path

from .config import PROJECT_ROOT

SERVICE_PROTOCOL_DIR = PROJECT_ROOT / "service_protocol"

if str(SERVICE_PROTOCOL_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICE_PROTOCOL_DIR))

from counter import SequenceCounter  # noqa: E402
from queue_drainer import QueueDrainer  # noqa: E402
from schema import MsgType, decode_message, encode_message  # noqa: E402
from store_and_forward import StoreAndForwardQueue  # noqa: E402

__all__ = [
    "SequenceCounter",
    "QueueDrainer",
    "MsgType",
    "decode_message",
    "encode_message",
    "StoreAndForwardQueue",
]
