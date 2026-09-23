"""
Single import point for Evan's Layer-3 code in service_protocol/.

service_protocol/ uses flat imports (`from schema import ...`) and has no
__init__.py, so it is put on sys.path here rather than imported as a package.
Nothing in service_protocol/ is modified; gaps are handled in ingest.py and
documented in gateway/docs/service_protocol_notes.md.
"""

import json
import sys
from pathlib import Path

from .config import REPO_ROOT

SERVICE_PROTOCOL_DIR = REPO_ROOT / "service_protocol"
if str(SERVICE_PROTOCOL_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICE_PROTOCOL_DIR))

from schema import (  # noqa: E402
    HEADER_LEN,
    MAC_LEN,
    SCHEMA_VERSION,
    MsgType,
    decode_message,
    encode_message,
    peek_help_point_id,
)
from gateway import Gateway, ProcessResult  # noqa: E402
from replay_guard import ReplayGuard, ReplayResult  # noqa: E402
from rate_limiter import RateLimiter  # noqa: E402

MIN_FRAME_LEN = HEADER_LEN + MAC_LEN


class AllowAllRateLimiter:
    """Passed into Gateway so its pre-auth rate check never fires; ingest.py rate-limits after auth."""

    def allow(self, node_id: str, now: float = None) -> bool:
        return True


def load_key_store(path: Path) -> dict:
    """
    Convert provision_keys.py output ({"1": "<hex>"}) into what Gateway expects ({1: bytes}).
    """
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return {int(hp_id): bytes.fromhex(key_hex) for hp_id, key_hex in raw.items()}


def write_dev_key_store(path: Path, num_help_points: int) -> dict:
    """Create a development key store in provision_keys.py's format. Never use for a real deployment."""
    import secrets

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = {i: secrets.token_bytes(32) for i in range(1, num_help_points + 1)}
    path.write_text(json.dumps({str(i): k.hex() for i, k in keys.items()}, indent=2), encoding="utf-8")
    return keys


__all__ = [
    "HEADER_LEN", "MAC_LEN", "MIN_FRAME_LEN", "SCHEMA_VERSION", "MsgType",
    "decode_message", "encode_message", "peek_help_point_id",
    "Gateway", "ProcessResult", "ReplayGuard", "ReplayResult", "RateLimiter",
    "AllowAllRateLimiter", "load_key_store", "write_dev_key_store",
]
