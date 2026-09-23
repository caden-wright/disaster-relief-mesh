# Notes on `service_protocol/` from the Gateway side

The gateway (`gateway/meshaid_gateway/`) uses `Gateway.process()`, `ReplayGuard`, `RateLimiter`, and the
schema encoder/decoder as they are. I have **not changed anything in `service_protocol/`**. The items below are
things I ran into while integrating. For each one I say how the gateway works around it today, so nothing is
blocked on you. Fixing them in `service_protocol/` would let me delete the workarounds.

Line references are to the files as of commit `4b476f5`.

---

## 1. Malformed frames raise instead of returning a status

**Where:** `schema.py` — `peek_help_point_id()` (line 75), `decode_message()` (line 89), `unpack_payload()` (line 60)

**What happens:** each of these frames raises an exception out of `Gateway.process()`:

| Frame | Exception |
|---|---|
| Fewer than 3 bytes | `struct.error` in `peek_help_point_id` |
| Payload length wrong for its type (for example, truncated) | `struct.error: unpack requires a buffer of N bytes` |
| Unknown `msg_type` (for example, 9) | `ValueError: 9 is not a valid MsgType` |

This matters even when the frame came from a real, correctly keyed Help Point. `decode_message` computes the
MAC first but parses the payload before returning, so a validly MACed frame with a bad layout still raises.

**Why it matters:** SRS 8.4 says to reject malformed messages at ingest and fail closed. Uncaught, one garbage
LoRa frame would crash the gateway loop.

**Gateway workaround:** `ingest.py` rejects anything shorter than `HEADER_LEN + MAC_LEN` (19 bytes). It also
catches `struct.error`, `ValueError` and `KeyError` around `Gateway.process()` and records a `malformed` security
event.

**Suggested fix:** add a `"malformed"` status to `ProcessResult`. Have `decode_message` check the length and
`msg_type` before unpacking, and verify the MAC before parsing the payload.

## 2. Rate limiting happens before authentication

**Where:** `gateway.py` lines 27–28. `rate_limiter.allow()` is called before `decode_message()` checks the HMAC.

**What happens:** the rate-limit bucket is keyed on the *claimed* Help Point id, which comes from the
unauthenticated header.
- **Spoofing starves a real Help Point.** An attacker sends 20 junk frames with `help_point_id = 1` in the
  header. Help Point 1's bucket is empty for the next 5 minutes, so its real medical flags come back
  `rate_limited` and are dropped.
- **Mesh retransmissions use up tokens.** Duplicate copies of the same frame each cost a token, even though
  `ReplayGuard` would suppress them anyway.

**Gateway workaround:** I pass a no-op limiter into `Gateway(...)`. After a frame is `accepted` or
`flagged_stale`, I apply your `RateLimiter` myself. That makes the order HMAC → replay → rate limit. Test
`test_spoofs_do_not_drain_real_help_point_budget` covers it.

**Suggested fix:** move the `rate_limiter.allow()` call below the authenticity and replay checks in
`Gateway.process()`.

**Open question:** the charter puts rate limiting at the Help Points ("rate limiting at the Help Points"). Should
the gateway rate-limit at all, or only the Help Point? Right now I log an authentic but over-limit message as a
security event, with its summary, so the operator can still see it. I didn't want to drop it silently.

## 3. Replay state is lost when the gateway restarts

**Where:** `replay_guard.py`. `_state` exists only in memory.

**What happens:** after a gateway restart, `ReplayGuard` starts empty. The first frame per Help Point is always
`ACCEPTED` (line 40), so any frame recorded before the restart can be replayed once.

**Gateway workaround:**
- The SQLite table has `UNIQUE(hp_id, seq)`, and every accepted frame is checked against it.
- On startup, `ingest.py` rebuilds `ReplayGuard` by calling `evaluate()` over the stored sequence numbers in
  ascending order.
- Test `test_replay_rejected_after_gateway_restart` covers it.

**Suggested fix (optional):** add a way to save and restore `ReplayGuard` state (for example, `to_dict()` /
`from_dict()`), which would be useful on the Help Point side too.

## 4. Key store format mismatch

**Where:** `provision_keys.py` writes `{"1": "<hex>"}`, but `Gateway(key_store=...)` expects `{1: b"..."}`.

**Gateway workaround:** `protocol_bridge.load_key_store()` converts between the two.

**Suggested fix:** add a `load_gateway_key_store(path)` function to `provision_keys.py`, so the conversion is
owned by the same file that writes the format.

## 5. `radio_interface.py` won't receive packets

**Where:** `radio_interface.py` lines 13–20.

- **The callback is never called.** It sets `self.interface.onReceive = ...`, but the meshtastic Python library
  never calls an attribute with that name. Received packets are published through pubsub
  (`pub.subscribe(fn, "meshtastic.receive...")`). I checked the source of `meshtastic` 2.x, where
  `mesh_interface.py` builds a topic and publishes to it.
- **There is no portnum filter.** Once subscribed to `meshtastic.receive`, the callback would also get
  telemetry, position, node-info and text packets, and each of those would reach the parser as a "frame".
- **It only supports serial.** There is no `TCPInterface` for meshtasticd running on a Pi.

**Gateway workaround:** I wrote my own adapter (`gateway/meshaid_gateway/radio.py`). It supports serial or TCP,
subscribes only to `meshtastic.receive.data.PRIVATE_APP`, ignores packets from other interfaces, and also reads
hops and SNR for the dashboard.

**Note for the Help Point side (Abraham too):** `sendData()` defaults to `PRIVATE_APP` (portnum 256), which is
what the gateway listens on. Please keep that default, or tell me if you change portnum.

## 6. `service_protocol/` isn't importable as a package

**Where:** the modules use flat imports (`from schema import ...`) and there is no `__init__.py`.

**Gateway workaround:** `protocol_bridge.py` puts `service_protocol/` on `sys.path`. This works, but it means a
module named `gateway` is importable globally, which is easy to confuse.

**Suggested fix:** add `__init__.py` and relative imports (`from .schema import ...`), then I'll import
`service_protocol.gateway` directly.

**Related:** `counter.py` imports `fcntl`, which doesn't exist on Windows. The gateway never imports it, but
anyone running the Help Point code on a Windows laptop will hit it.

## 7. The schema version isn't checked

**Where:** `decode_message()` returns `version` but nothing compares it to `SCHEMA_VERSION`.

**Why it matters:** SRS 8.6.3 says nodes running different builds must interoperate. Today a v2 frame would
either be parsed with the v1 layout or raise.

**Suggestion:** have `decode_message` reject unknown versions with a clear status (or dispatch per version). The
gateway already stores `schema_version` with each message.

## 8. Schema fields vs. SRS data minimization

- `CHECKIN` has `name` (str20), and `MEDICAL_URGENT` has `patient_name` and `patient_age`.
- SRS 6.5 says a safety check-in must not require sensitive personal identifiers, and SRS 8.7 asks for minimal
  metadata retention.
- The dashboard shows these fields only when they're non-empty, and the simulator sends them empty.
- **Question for you and Caden:** should they stay (reunification value) or be dropped? The civilian app
  currently collects neither.

## 9. Numeric code tables were undefined

**Where:** `schema.py` defines field *types* but not what the numbers mean. That covers `status`,
`resource_type`, `urgency`, `severity` and `condition_code`.

The civilian app and the schema also don't line up yet. For example, the Medical page sends `injured`,
`conscious`, `breathing` and a free-text `location`, none of which exist in `MEDICAL_URGENT`.

## 10. ACK message is not enough for two-way acks (Future item, SRS 3.9 / 9.1)

**Where:** `MESSAGE_FIELDS[MsgType.ACK]` = `orig_seq u32, status u8`.

**What's missing:**
- **A target Help Point.** The header's `help_point_id` identifies the *sender*, so a gateway-originated ACK has
  nowhere to say which Help Point it's for.
- **A gateway key.** The gateway has none, so Help Points can't authenticate an ACK.

**Proposal (for November, when we get there):**
- The gateway signs with its own key as `help_point_id = 0`, and every Help Point is provisioned with that key.
- A replay counter for the gateway, persisted the way `counter.py` does it.
- Sent with `sendData(..., destinationId=<hp node>)`.

The dashboard's acknowledge button is local-only until this is agreed.

---

### How to check the gateway against your changes

```
cd gateway
.venv/Scripts/python -m pytest              # gateway tests (use .venv/bin/python on Linux/macOS)
cd ../service_protocol && python test_protocol.py
```
If you change `Gateway.process()` status strings, update `ingest.py` (search for `result.status`).
