"""
Replay protection: accept / flag-for-review / duplicate.

Never silently drops a message outright. Anything too old to verify with
confidence is flagged for a human to review instead of being discarded,
since a false rejection here could mean a real emergency goes unseen.
Duplicates of an already-flagged message are suppressed so a replayed
message can't spam the dashboard.
"""

from collections import OrderedDict
from enum import Enum


class ReplayResult(Enum):
    ACCEPTED = "accepted"
    FLAGGED_STALE = "flagged_stale"
    DUPLICATE = "duplicate"


class ReplayGuard:
    def __init__(self, window_size: int = 32, stale_cache_size: int = 128):
        self.window_size = window_size
        self.stale_cache_size = stale_cache_size
        self._state = {}  # node_id -> {"highest_seq", "window", "stale_seen"}

    def _new_state(self, seq: int) -> dict:
        return {"highest_seq": seq, "window": 1, "stale_seen": OrderedDict()}

    def _remember_stale(self, state: dict, seq: int) -> None:
        stale_seen = state["stale_seen"]
        stale_seen[seq] = True
        if len(stale_seen) > self.stale_cache_size:
            stale_seen.popitem(last=False)  # evict oldest, keeps memory bounded

    def evaluate(self, node_id: str, seq: int) -> ReplayResult:
        state = self._state.get(node_id)

        # first message from this node
        if state is None:
            self._state[node_id] = self._new_state(seq)
            return ReplayResult.ACCEPTED

        highest_seq = state["highest_seq"]
        window = state["window"]

        # new high sequence number
        if seq > highest_seq:
            shift = seq - highest_seq
            window = 0 if shift >= self.window_size else (window << shift)
            window |= 1
            state["highest_seq"] = seq
            state["window"] = window
            return ReplayResult.ACCEPTED

        # exact repeat of the latest message
        if seq == highest_seq:
            return ReplayResult.DUPLICATE

        # older message: still within the tracked window?
        distance = highest_seq - seq
        if distance < self.window_size:
            bit = 1 << distance
            if window & bit:
                return ReplayResult.DUPLICATE
            state["window"] = window | bit
            return ReplayResult.ACCEPTED

        # outside the window: flag once, suppress repeats
        if seq in state["stale_seen"]:
            return ReplayResult.DUPLICATE

        self._remember_stale(state, seq)
        return ReplayResult.FLAGGED_STALE
