from dataclasses import dataclass
from typing import Optional
from schema import decode_message, peek_help_point_id
from replay_guard import ReplayGuard, ReplayResult
from rate_limiter import RateLimiter


@dataclass
class ProcessResult:
    status: str
    message: Optional[dict]


class Gateway:
    def __init__(self, key_store: dict, rate_limiter: RateLimiter = None, replay_guard: ReplayGuard = None):
        self.key_store = key_store
        self.rate_limiter = rate_limiter or RateLimiter()
        self.replay_guard = replay_guard or ReplayGuard()

    def process(self, wire: bytes) -> ProcessResult:
        help_point_id = peek_help_point_id(wire)

        key = self.key_store.get(help_point_id)
        if key is None:
            return ProcessResult("unknown_node", None)

        if not self.rate_limiter.allow(str(help_point_id)):
            return ProcessResult("rate_limited", None)

        decoded = decode_message(wire, key)
        if not decoded["authentic"]:
            return ProcessResult("unauthentic", None)

        result = self.replay_guard.evaluate(str(help_point_id), decoded["seq"])
        if result == ReplayResult.DUPLICATE:
            return ProcessResult("duplicate", None)

        status = "accepted" if result == ReplayResult.ACCEPTED else "flagged_stale"
        return ProcessResult(status, decoded)
