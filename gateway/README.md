# MeshAid Gateway & Incident Command Dashboard

This is Layer 4 of the MeshAid architecture (ADS §7):

- **Gateway** — receives frames from the mesh at the uplink node (IF-10), verifies and deduplicates them
  (IF-11 to IF-14) using `service_protocol/`, and delivers clean messages to the dashboard (IF-15).
- **Incident Command Dashboard** — a live, prioritized, filterable view for the operator (IF-16). It runs
  entirely on the command-post laptop with no internet.

```
Help Points ──LoRa mesh──► node at the command post
                             │ USB serial or TCP (meshtasticd)
                             ▼
                   meshaid_gateway (Python)
         radio.py ─► ingest.py ─► store.py (SQLite) ─► api.py
                        │                          REST + WebSocket
            service_protocol/ (Evan)                     │
      HMAC · replay guard · rate limiter                 ▼
                                               dashboard/ (React, served by the gateway)
```

## Quick start (no hardware)

**Requirements:** Python 3.11 or newer, and Node 20 or newer (Node is only needed to build the dashboard).

```bash
# one-time setup
cd gateway
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt      # Linux/macOS: .venv/bin/pip
cd ../dashboard && npm install && npm run build && cd ../gateway

# run the gateway with the built-in simulator
.venv/Scripts/python -m meshaid_gateway
```

Open **http://127.0.0.1:8000**. In a second terminal (from `gateway/`), send it some traffic:

```bash
.venv/Scripts/python -m meshaid_gateway.sim demo          # mixed traffic every few seconds, Ctrl-C to stop
```

In sim mode the gateway creates **development keys** in `gateway/dev_keys/` the first time it runs. Never use
them in a real deployment.

### Simulator scenarios

| Command | What happens | Where it shows up |
|---|---|---|
| `sim normal --count 10` | random check-ins, resource requests, medical flags | message log |
| `sim demo` | continuous mixed traffic | message log |
| `sim spoof` | medical flag signed with a forged key, plus a frame claiming an unprovisioned Help Point | Rejected panel: *Forged signature*, *Unknown Help Point* |
| `sim replay` | valid request, then the same bytes resent twice | 1 message; Rejected: *Duplicate or replay* ×2 |
| `sim malformed` | too short, truncated, and unknown-type frames | Rejected: *Unreadable frame* ×3 |
| `sim stale` | authentic frame 100 sequence numbers behind | message log flagged *Check with shelter* |
| `sim burst --count 25` | trips the 20-per-5-minute rate limit | Rejected: *Over rate limit* |
| `sim drop-node --node R2` / `restore-node --node R2` | a relay stops or resumes heartbeats | Mesh panel: Quiet → Down, then back to Up |

Nodes can be given as `GW`, `R1`, `R2`, `HP1`, `HP2`, or a node number. Every sim command is run as
`.venv/Scripts/python -m meshaid_gateway.sim <scenario>`.

## Running with a real radio

```bash
.venv/Scripts/python -m meshaid_gateway --radio serial:COM5 --keys path/to/gateway_key_store.json   # USB node (Windows)
.venv/bin/python     -m meshaid_gateway --radio serial --keys ...        # auto-detect a USB node
.venv/bin/python     -m meshaid_gateway --radio tcp:127.0.0.1 --keys ... # meshtasticd on the Pi
```

- **Keys:** the key store is the `gateway_key_store.json` written by `service_protocol/provision_keys.py`.
- **Packet type:** Help Points must send with `sendData()` on the default `PRIVATE_APP` portnum. The gateway
  ignores all other traffic (text, telemetry, position).
- **If the radio isn't reachable:** the dashboard still starts, shows the radio as disconnected, and retries every
  10 seconds.
- **Other laptops on the LAN:** add `--host 0.0.0.0` to let them open the dashboard.

### Config file

For a deployment, copy `config.example.json` to `config.json` and run
`python -m meshaid_gateway --config config.json`. The file sets:

- `shelters` — Help Point id → shelter name shown on the dashboard.
- `nodes` — Meshtastic node id → role and label for the Mesh panel.
- `rate_capacity` / `rate_refill_seconds` — the post-authentication rate limit.
- `retention_hours` — messages and security events older than this are deleted (SRS 8.7); 0 keeps everything.
- `node_degraded_after` / `node_down_after` — seconds of silence before a node shows as Quiet or Down.

Command-line flags override the file.

## How a frame is handled

`ingest.py` checks every frame in this order:

1. **Size** — shorter than header + MAC → `malformed`.
2. **`service_protocol` `Gateway.process()`** — key lookup (`unknown_node`), HMAC (`unauthentic`), replay window
   (`duplicate` / `flagged_stale`). A parse error → `malformed`.
3. **Durable dedup** — the Help Point + sequence number is already in SQLite → `duplicate`. This still works
   after a gateway restart.
4. **Rate limit** — applied only to authentic frames → `rate_limited`.
5. **Store and push** to the dashboard over WebSocket.

**Rejected frames** never reach the message log. Each one becomes a security event, shown in the
**Rejected at the gateway** panel (SRS 8.4).

**Stale frames** pass the signature check but have a very old sequence number. They go to the log with a warning
instead of being dropped, so a real emergency isn't lost.

**Priority** (SRS 3.4): medical flags are always above resource requests, which are above check-ins. Within each
group, higher severity, urgency, or a *not safe* status ranks higher. Labels and codes come from
`shared/codes.json`, which is **still a draft** that Evan and Caden need to approve.

## API (the gateway → dashboard contract, IF-15)

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/messages?type=&hp_id=&ack_state=&verify_status=&min_priority=&sort=priority\|newest\|oldest&limit=` | message log |
| GET | `/api/messages/{id}` | one message |
| POST | `/api/messages/{id}/ack` `{"state": "new\|acknowledged\|resolved", "note": "..."}` | operator acknowledge (dashboard only, not sent over the mesh) |
| GET | `/api/security-events?kind=&limit=` | rejected and suspicious frames |
| GET | `/api/nodes` | mesh health |
| GET | `/api/stats` | counts |
| GET | `/api/meta` | code tables, shelters, provisioned Help Points, node thresholds |
| GET | `/api/health` | radio link status |
| WS | `/ws` | pushes `{"type": "message" \| "message_update" \| "security_event" \| "node", "data": {...}, "sent_at": ...}` |
| POST | `/api/dev/inject`, `/api/dev/node` | **sim mode only**, used by `sim.py` |

## Dashboard development

```bash
cd dashboard
npm run dev        # http://localhost:5173, proxies /api and /ws to the gateway on :8000
npm run build      # writes dashboard/dist, which the gateway serves at /
```

Fonts (Barlow) are bundled through `@fontsource`, so the built dashboard makes no internet requests.

## Tests

```bash
cd gateway
.venv/Scripts/python -m pytest
```

The tests cover:

- every ingest outcome, including malformed input, spoofing, and replay after a restart;
- that spoofed frames can't use up a real Help Point's rate limit;
- priority ordering;
- the REST filters and acknowledge;
- WebSocket delivery within the 5-second target (SRS 5.6);
- the radio adapter's PRIVATE_APP filtering.

## Layout

```
gateway/
  meshaid_gateway/
    __main__.py        command line: python -m meshaid_gateway
    config.py          settings and config-file loading
    protocol_bridge.py the only import point for service_protocol/, plus the key-store loader
    radio.py           MeshtasticSource (serial|tcp) and SimSource
    ingest.py          verification pipeline
    store.py           SQLite: messages, security_events, nodes
    codes.py           labels and priority from shared/codes.json
    api.py             FastAPI app, WebSocket hub, static dashboard
    sim.py             traffic and attack simulator
  tests/
  docs/service_protocol_notes.md   integration issues for the service protocol (Evan)
dashboard/                         React + Vite operator UI
shared/codes.json                  DRAFT code tables shared with the civilian app
```

## Status and next steps

**Done:**
- the ingest pipeline, SQLite store, REST and WebSocket API, simulator, and serial/TCP radio adapter;
- the dashboard: log, filters, detail and acknowledge, mesh health, and the rejected-frames panel.

**Next:**
- a bench test with a real node and a Help Point frame;
- getting the code tables approved;
- ack-over-mesh (needs a schema change, see the notes for Evan §10);
- reroute visibility for the node-failure demo;
- an offline map (stretch goal);
- a gateway provisioning script (charter §14.3.9).

MeshAid is a research prototype. It is not a certified life-safety system and does not replace 911 or official
dispatch.
