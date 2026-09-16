"""
Per-Help-Point rate limiting (token bucket).

Independent of replay protection - caps how fast any one node can push
messages through, protecting shared mesh airtime and Gateway processing
time regardless of whether the messages are otherwise valid.
"""

import time


class RateLimiter:
    def __init__(self, capacity: int = 20, refill_seconds: float = 300.0):
        self.capacity = capacity
        self.refill_seconds = refill_seconds
        self._buckets = {}  # node_id -> {"tokens", "last_check"}

    def _refill(self, bucket: dict, now: float) -> None:
        elapsed = now - bucket["last_check"]
        rate = self.capacity / self.refill_seconds
        bucket["tokens"] = min(self.capacity, bucket["tokens"] + elapsed * rate)
        bucket["last_check"] = now

    def allow(self, node_id: str, now: float = None) -> bool:
        now = now if now is not None else time.monotonic()
        bucket = self._buckets.setdefault(node_id, {"tokens": float(self.capacity), "last_check": now})
        self._refill(bucket, now)

        if bucket["tokens"] >= 1:
            bucket["tokens"] -= 1
            return True
        return False
