"""
Gateway ingest pipeline: IF-10 frame in -> IF-15 verified message out.

Order of checks:
  1. structural sanity         - too short / unparseable     -> security event "malformed"
  2. service_protocol Gateway  - key lookup, HMAC, replay window (Evan's code, pre-auth rate limit disabled)
  3. durable dedup             - (hp_id, seq) already stored  -> "duplicate" (covers gateway restarts)
  4. post-auth rate limit      - Evan's RateLimiter, applied only to authentic frames, so a spoofed
                                 frame claiming a Help Point's id cannot drain that Help Point's budget
  5. store + return the message for the dashboard

Nothing is silently dropped. Every rejection becomes a security event (SRS 8.4)
and nothing rejected reaches the operator feed. Stale-but-authentic frames go to
the feed flagged for review, per ReplayGuard's design.
"""

import logging
import struct
from dataclasses import dataclass
from typing import Optional

from .codes import Codes
from .protocol_bridge import (
    MIN_FRAME_LEN,
    AllowAllRateLimiter,
    Gateway,
    RateLimiter,
    ReplayGuard,
    peek_help_point_id,
)
from .radio import RadioFrame
from .store import Store

log = logging.getLogger(__name__)

SEVERITY = {
    "malformed": "warning",
    "unknown_node": "alert",
    "unauthentic": "alert",
    "duplicate": "info",
    "stale": "warning",
    "rate_limited": "warning",
}


@dataclass
class IngestOutcome:
    status: str                         # accepted | flagged_stale | <security event kind>
    message: Optional[dict] = None      # stored message row (feed)
    security_event: Optional[dict] = None


class IngestPipeline:
    def __init__(self, key_store: dict, store: Store, codes: Codes, rate_limiter: RateLimiter = None,
                 replay_guard: ReplayGuard = None):
        self.store = store
        self.codes = codes
        self.replay_guard = replay_guard or ReplayGuard()
        self.rate_limiter = rate_limiter or RateLimiter()
        self.gateway = Gateway(key_store, rate_limiter=AllowAllRateLimiter(), replay_guard=self.replay_guard)
        self._reseed_replay_guard()

    def _reseed_replay_guard(self):
        """Rebuild ReplayGuard windows from stored messages so a restart doesn't reopen the replay window."""
        seen = self.store.seen_sequences()
        for hp_id, seqs in seen.items():
            for seq in seqs:
                self.replay_guard.evaluate(str(hp_id), seq)
        if seen:
            log.info("Replay guard re-seeded for %d Help Point(s)", len(seen))

    def process(self, frame: RadioFrame) -> IngestOutcome:
        wire = frame.wire

        if len(wire) < MIN_FRAME_LEN:
            return self._reject("malformed", frame, detail=f"frame too short ({len(wire)} bytes)")

        hp_id = peek_help_point_id(wire)
        try:
            result = self.gateway.process(wire)
        except (struct.error, ValueError, KeyError) as exc:
            # decode_message raises on a bad payload length or unknown msg_type
            return self._reject("malformed", frame, hp_id=hp_id, detail=f"unparseable frame: {exc}")

        if result.status == "unknown_node":
            return self._reject("unknown_node", frame, hp_id=hp_id, detail=f"no key provisioned for Help Point {hp_id}")
        if result.status == "unauthentic":
            return self._reject("unauthentic", frame, hp_id=hp_id, detail="HMAC verification failed (spoofed or corrupted)")
        if result.status == "duplicate":
            return self._reject("duplicate", frame, hp_id=hp_id, detail="duplicate or replayed frame suppressed")
        if result.status not in ("accepted", "flagged_stale"):
            return self._reject(result.status, frame, hp_id=hp_id, detail=f"gateway status {result.status}")

        msg = result.message
        seq = msg["seq"]
        if self.store.has_message(hp_id, seq):
            return self._reject("duplicate", frame, hp_id=hp_id, seq=seq,
                                detail="already delivered (seen before gateway restart)")

        type_key = self.codes.type_key(msg["msg_type"])
        if not self.rate_limiter.allow(str(hp_id)):
            summary = self.codes.summary(type_key, msg["fields"])
            return self._reject("rate_limited", frame, hp_id=hp_id, seq=seq,
                                detail=f"authentic but over rate limit: {type_key} - {summary}")

        stored = self.store.insert_message(
            hp_id=hp_id, seq=seq, msg_type=type_key, schema_version=msg["version"], fields=msg["fields"],
            hp_timestamp=msg["timestamp"], received_at=frame.received_at, verify_status=result.status,
            priority=self.codes.priority(type_key, msg["fields"]),
            from_node=frame.from_node, hops=frame.hops, snr=frame.snr,
        )
        if stored is None:  # lost a race with an identical frame
            return self._reject("duplicate", frame, hp_id=hp_id, seq=seq, detail="duplicate frame suppressed")

        event = None
        if result.status == "flagged_stale":
            event = self._event("stale", frame, hp_id=hp_id, seq=seq,
                                detail="sequence number outside replay window - shown in feed flagged for review")
        return IngestOutcome(status=result.status, message=stored, security_event=event)

    def _event(self, kind, frame, hp_id=None, seq=None, detail=None) -> dict:
        return self.store.insert_security_event(
            kind=kind, severity=SEVERITY.get(kind, "warning"), received_at=frame.received_at,
            hp_id=hp_id, seq=seq, from_node=frame.from_node, detail=detail, raw=frame.wire,
        )

    def _reject(self, kind, frame, **kw) -> IngestOutcome:
        event = self._event(kind, frame, **kw)
        log.info("Rejected frame: %s (%s)", kind, kw.get("detail"))
        return IngestOutcome(status=kind, security_event=event)
