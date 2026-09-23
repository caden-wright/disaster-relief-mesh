# MeshAid Help Point Integration Handoff

# QUICK START

Use this section if you only need to run the project.

## Local simulator / development

Open 3 terminals.

### Terminal 1 — Civilian UI
From the project root:

```powershell
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

### Terminal 2 — Help Point backend
From the project root:

```powershell
$env:MESHAID_HELP_POINT_RADIO="gateway-dev"
py -m help_point
```

Check:

```text
http://127.0.0.1:8001/api/status
```

### Terminal 3 — Gateway + Incident Command
From the `gateway` folder:

```powershell
py -m meshaid_gateway --radio sim --port 8000 --keys ..\keys\gateway_key_store.json -v
```

Open:

```text
http://127.0.0.1:8000
```

## Raspberry Pi / physical radio

For the Pi, do **not** use `gateway-dev`.

Set the physical Meshtastic serial device and start the Help Point:

```bash
export MESHAID_HELP_POINT_RADIO="serial:/dev/ttyACM0"
python3 -m help_point
```

The device may instead be something like:

```text
/dev/ttyUSB0
```

## What may need to be changed

Prefer environment variables instead of editing Python source.

| Setting | Where/default | What to change |
|---|---|---|
| Help Point ID | `help_point/config.py` / `MESHAID_HELP_POINT_ID` | Change only if this Pi is a different Help Point |
| Radio mode/device | `help_point/config.py` / `MESHAID_HELP_POINT_RADIO` | Use `gateway-dev` for local testing; `serial:/dev/...` for hardware |
| Help Point key | `keys/help_point_1.key` or `MESHAID_HELP_POINT_KEY` | Must match the Gateway key store |
| Gateway key store | `keys/gateway_key_store.json` | Must contain the matching Help Point key |
| Shared codes | `shared/codes.json` | Must be the same contract used by Help Point + Gateway |
| Sequence counter | `help_point/data/counter.txt` | Preserve if reusing the same Help Point ID + key |
| Offline queue | `help_point/data/queue.json` | Persistent queued messages |

### Important
If the Pi reuses the same **Help Point ID + key**, keep the existing:

```text
help_point/data/counter.txt
```

Do not reset the sequence counter, or Gateway replay protection may reject messages.

## Current verified state

- 14/14 Help Point tests pass
- Check-In works end-to-end
- Resource Request works end-to-end
- Medical Urgent works end-to-end
- HMAC verification works
- Offline queue + automatic resend works
- Incident Command dashboard receives messages
- Frontend production build succeeds with `npm run build`

Physical Meshtastic transport is the remaining hardware validation step.

---

## Current Status

The Civilian Help Point integration has been completed and validated in simulator mode.

Validated functionality:

- Safety Check-In submission
- Resource Request submission
- Medical Urgent submission
- Shared message codebook
- HMAC authenticated messages
- Sequence numbering
- Persistent store-and-forward queue
- Automatic queue draining after connectivity returns
- Gateway message verification
- Gateway database persistence
- Incident Command dashboard display
- Rejected/invalid HMAC security events
- Civilian frontend production build

Automated Help Point tests:

14 passed.

Frontend production build:

Successful with Vite.

---

# Architecture

## Development integration

Civilian React PWA
    ↓
Help Point API
    ↓
Service Protocol encoder
    ↓
HMAC + sequence number
    ↓
GatewayDevRadio
    ↓
Gateway /api/dev/inject
    ↓
Gateway ingest/security pipeline
    ↓
SQLite
    ↓
Incident Command dashboard

The gateway-dev adapter is DEVELOPMENT ONLY.

It exists to test the Help Point against the existing gateway without
requiring physical Meshtastic radios.

---

# Intended Hardware Architecture

Civilian device
    ↓
Raspberry Pi Wi-Fi / Help Point
    ↓
Built Civilian PWA
    ↓
Help Point backend
    ↓
MeshtasticSerialRadio
    ↓
Meshtastic radio
    ↓
LoRa mesh
    ↓
Gateway Meshtastic radio
    ↓
Existing Gateway backend
    ↓
Incident Command dashboard

The Help Point integration should not replace or duplicate the existing
Gateway implementation.

---

# Important Files

## Civilian frontend

src/

Primary pages:

- src/pages/Home.jsx
- src/pages/CheckIn.jsx
- src/pages/Resources.jsx
- src/pages/Medical.jsx
- src/pages/Messages.jsx

Help Point API client:

- src/api/helpPoint.js

Shared Help Point connectivity state:

- src/context/HelpPointStatusContext.jsx

Production frontend build:

- dist/

---

## Help Point integration backend

help_point/

Important modules:

- api.py
- service.py
- radio.py
- config.py
- codebook.py
- protocol_bridge.py

Persistent runtime data:

- help_point/data/counter.txt
- help_point/data/queue.json

---

## Shared protocol code

service_protocol/

The Help Point integration uses the existing service protocol rather than
reimplementing it.

---

## Codebook

shared/codes.json

This is the shared message-code contract used by both Help Point and Gateway.

---

# Supported Civilian Messages

## Safety Check-In

Protocol type:

CHECKIN

Fields:

- status
- name
- group_size

Known status values:

1 - Safe
2 - Safe, needs assistance
3 - Not safe

---

## Resource Request

Protocol type:

RESOURCE_REQUEST

Fields:

- resource_type
- quantity
- urgency
- notes

Resource types:

1 - Water
2 - Food
3 - Medicine
4 - Shelter
5 - Other

Urgency:

1 - Low
2 - Medium
3 - High

---

## Medical Urgent

Protocol type:

MEDICAL_URGENT

Fields:

- severity
- condition_code
- patient_name
- patient_age

Severity:

1 - Minor
2 - Serious
3 - Critical

Condition:

1 - Injury or bleeding
2 - Breathing difficulty
3 - Unconscious or unresponsive
4 - Chest pain
5 - Other or unknown

NOTE:

The current protocol does NOT contain fields for:

- patient location
- number of injured people
- age ranges

Do not silently encode these into unrelated fields.

Any change requires a coordinated protocol/schema change.

---

# Help Point Radio Modes

The Help Point supports the following radio configurations.

## sim

Development-only local simulator.

MESHAID_HELP_POINT_RADIO=sim

Frames are accepted locally but are not sent to the real Gateway.

---

## offline

Used to test persistent store-and-forward behavior.

MESHAID_HELP_POINT_RADIO=offline

Messages are queued locally.

---

## gateway-dev

Development integration mode.

MESHAID_HELP_POINT_RADIO=gateway-dev

Encoded frames are forwarded to the existing Gateway simulator through:

POST /api/dev/inject

Default Gateway address:

http://127.0.0.1:8000

This mode should NOT be used for hardware deployment.

---

## serial

Physical Meshtastic serial interface.

Example:

MESHAID_HELP_POINT_RADIO=serial

or:

MESHAID_HELP_POINT_RADIO=serial:/dev/ttyACM0

Exact Linux device path must be verified on the Raspberry Pi.

---

# Important Environment Variables

Help Point ID:

MESHAID_HELP_POINT_ID

Default:

1

Help Point backend host:

MESHAID_HELP_POINT_HOST

Default:

127.0.0.1

Help Point backend port:

MESHAID_HELP_POINT_PORT

Default:

8001

Radio configuration:

MESHAID_HELP_POINT_RADIO

Codebook:

MESHAID_CODES_PATH

Help Point key:

MESHAID_HELP_POINT_KEY

Gateway development URL:

MESHAID_GATEWAY_DEV_URL

Default:

http://127.0.0.1:8000

---

# Keys

Current development keys are stored separately from source code.

The Help Point key and Gateway key store MUST correspond.

Example:

keys/help_point_1.key

and:

keys/gateway_key_store.json

Do not commit deployment keys to Git.

Do not repeatedly regenerate keys during deployment.

Regenerating one side without updating the other will cause:

HMAC verification failed

The Gateway correctly records this as an unauthentic security event.

---

# CRITICAL: Sequence Counter / Replay Protection

The Gateway implements replay protection.

The Help Point sequence counter is persisted in:

help_point/data/counter.txt

If the same Help Point ID and HMAC key are reused, do NOT reset the sequence
counter to zero.

For example:

If the Gateway has already accepted HP1 sequence 11 and the Raspberry Pi starts
HP1 again at sequence 1 using the same key, those messages may be rejected as
replays.

For deployment either:

1. Transfer the existing sequence-counter state to the Pi, OR
2. Provision a fresh Help Point identity/key and corresponding Gateway key
   store.

Treat:

Help Point ID + key + sequence history

as one security identity.

---

# Persistent Queue

Queued messages are stored in:

help_point/data/queue.json

Messages survive Help Point process restarts.

When connectivity returns, the queue drainer sends pending messages
automatically.

Priority currently behaves as:

Medical
Resource
Check-In

within the integration adapter.

---

# Delivery Semantics

"Sent to Mesh Network" means the local send operation was accepted.

It does NOT necessarily mean Incident Command has acknowledged or acted on
the message.

Gateway operator acknowledgement is a separate state.

The UI intentionally communicates this distinction.

---

# Development Startup

Three processes are used for the complete simulator environment.

## 1. Gateway

From gateway/:

py -m meshaid_gateway --radio sim --port 8000 --keys ..\keys\gateway_key_store.json -v

Gateway / Incident Command:

http://127.0.0.1:8000

---

## 2. Help Point

From project root:

$env:MESHAID_HELP_POINT_RADIO="gateway-dev"
py -m help_point

Help Point API:

http://127.0.0.1:8001/api/status

---

## 3. Civilian frontend

From project root:

npm run dev

Typical development URL:

http://127.0.0.1:5173

---

# Automated Tests

From repository root:

py -m pytest help_point\tests -v

Current expected result:

14 passed

The current Starlette/httpx deprecation warning does not represent a failed
test.

---

# Frontend Production Build

From repository root:

npm run build

Output:

dist/

The Raspberry Pi deployment should serve the built production assets rather
than running the Vite development server.

---

# Raspberry Pi Web Hosting Requirement

The production PWA uses /api requests.

The Pi's web configuration must therefore route browser requests appropriately.

Recommended topology:

Browser
    ↓
Pi web server
    ├── /        -> frontend dist/
    └── /api/*   -> Help Point backend on port 8001

A reverse proxy such as nginx can provide this configuration.

The existing Vite proxy is DEVELOPMENT ONLY and does not provide production
routing after `npm run build`.

---

# Raspberry Pi Process Management

For permanent deployment, do not rely on manually opened terminals.

Recommended production configuration:

- Help Point backend managed by systemd
- web server managed by systemd
- services automatically start on boot
- services automatically restart after failure

Physical radio mode should be configured through environment variables or a
systemd environment file.

---

# Integration Tests Already Completed

## Normal delivery

Civilian Check-In
→ accepted by Gateway

Civilian Resource Request
→ accepted by Gateway

Civilian Medical Request
→ accepted by Gateway

---

## Authentication

Message signed with mismatched key
→ rejected by Gateway
→ security event created

Expected result.

---

## Store-and-forward

Gateway stopped
→ civilian message accepted locally
→ message queued

Gateway restarted
→ Help Point detected connectivity
→ queued message automatically transmitted
→ Gateway accepted message
→ dashboard displayed message

Successful.

---


## Windows Development Note

During local Windows testing, the Gateway may occasionally log:

```text
ConnectionResetError: [WinError 10054]
```

This has occurred when a browser/dashboard connection disconnects or reconnects.
If the Gateway is still responding at:

```text
http://127.0.0.1:8000/api/health
```

and messages still process normally, no restart is required.

# Known Limitations / Follow-Up Work

1. Physical Meshtastic serial transport still needs hardware validation.

2. Raspberry Pi Wi-Fi/AP configuration belongs to the Pi/platform deployment.

3. Production static-file hosting / reverse proxy must be configured on Pi.

4. Medical protocol currently has no location or number-of-injured field.

5. Patient age is a single unsigned integer. Age ranges cannot currently be
   represented.

6. The queue considers the local send successful when the radio/send adapter
   accepts the frame. This is not equivalent to an Incident Command operator ACK.

7. Real LoRa range, radio reconnect behavior, antenna behavior, and hardware
   power recovery require physical testing.

---

# Hardware Team First-Boot Checklist

Before sending real traffic:

1. Verify Python dependencies are installed.
2. Verify shared/codes.json exists.
3. Verify Help Point ID.
4. Verify Help Point key.
5. Verify Gateway contains matching key.
6. Verify sequence-counter strategy.
7. Connect Meshtastic radio.
8. Identify Linux serial device.
9. Start Help Point using serial mode.
10. Confirm /api/status shows mesh connected.
11. Submit one Check-In.
12. Confirm Gateway accepts it.
13. Confirm Incident Command dashboard displays it.
14. Disconnect the mesh/radio.
15. Submit another message.
16. Confirm message queues.
17. Restore radio connectivity.
18. Confirm queued message drains automatically.

Only after this should the deployment be treated as hardware validated.