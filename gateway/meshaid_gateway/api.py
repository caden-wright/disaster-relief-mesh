"""
Gateway -> Dashboard delivery contract (IF-15): REST for state, WebSocket for live push.

WebSocket frames are JSON objects {"type": ..., "data": ...}:
  message         a new verified message (enriched, see enrich_message)
  message_update  an existing message changed (operator acknowledge)
  security_event  a rejected or suspicious frame
  node            a mesh node's health changed
"""

import asyncio
import contextlib
import logging
import time
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .codes import Codes
from .config import Config
from .ingest import IngestPipeline
from .protocol_bridge import RateLimiter, load_key_store, write_dev_key_store
from .radio import NodeUpdate, RadioFrame, RadioSource, SimSource, make_source
from .store import ACK_STATES, Store

log = logging.getLogger(__name__)

RADIO_RETRY_SECONDS = 10
PURGE_INTERVAL_SECONDS = 600


class Hub:
    """Fan-out of live events to every connected dashboard."""

    def __init__(self):
        self.clients: set = set()

    async def broadcast(self, kind: str, data: dict):
        payload = {"type": kind, "data": data, "sent_at": time.time()}
        dead = []
        for ws in list(self.clients):
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.clients.discard(ws)


class AckBody(BaseModel):
    state: str
    note: Optional[str] = None


class InjectBody(BaseModel):
    wire_hex: str
    from_node: Optional[int] = None
    hops: Optional[int] = None
    snr: Optional[float] = None


class NodeBody(BaseModel):
    node_num: int
    online: bool


def create_app(config: Config, *, radio: Optional[RadioSource] = None, store: Optional[Store] = None) -> FastAPI:
    codes = Codes(config.codes_path)
    store = store or Store(config.db_path)
    radio = radio or make_source(config.radio)
    hub = Hub()

    if config.is_sim and not config.key_store_path.exists():
        write_dev_key_store(config.key_store_path, config.sim_help_points)
        log.warning("Sim mode: generated DEV keys at %s (not for deployment)", config.key_store_path)
    pipeline = IngestPipeline(
        load_key_store(config.key_store_path), store, codes,
        rate_limiter=RateLimiter(capacity=config.rate_capacity, refill_seconds=config.rate_refill_seconds),
    )

    node_roles = {node_id: meta for node_id, meta in config.nodes.items()}

    def enrich_message(m: dict) -> dict:
        m = dict(m)
        m["type_label"] = codes.label("msg_type", _type_code(codes, m["msg_type"]))
        m["labels"] = codes.labels_for(m["msg_type"], m["fields"])
        m["summary"] = codes.summary(m["msg_type"], m["fields"])
        m["shelter"] = config.shelter_name(m["hp_id"])
        return m

    def enrich_event(e: dict) -> dict:
        e = dict(e)
        e["shelter"] = config.shelter_name(e["hp_id"]) if e.get("hp_id") is not None else None
        return e

    def enrich_node(n: dict, now: Optional[float] = None) -> dict:
        n = dict(n)
        now = now or time.time()
        meta = node_roles.get(n.get("node_id") or "", {})
        n["role"] = meta.get("role") or _guess_role(n)
        n["hp_id"] = meta.get("hp_id")
        n["label"] = meta.get("label") or n.get("long_name") or n.get("node_id") or str(n["node_num"])
        age = None if n.get("last_heard") is None else max(0.0, now - n["last_heard"])
        n["age_seconds"] = age
        if age is None or age > config.node_down_after:
            n["status"] = "down"
        elif age > config.node_degraded_after:
            n["status"] = "degraded"
        else:
            n["status"] = "up"
        return n

    async def handle_frame(frame: RadioFrame):
        outcome = pipeline.process(frame)
        if outcome.message:
            await hub.broadcast("message", enrich_message(outcome.message))
        if outcome.security_event:
            await hub.broadcast("security_event", enrich_event(outcome.security_event))
        if frame.from_node is not None:
            row = store.upsert_node(frame.from_node, last_heard=frame.received_at, snr=frame.snr)
            await hub.broadcast("node", enrich_node(row))

    async def handle_node(update: NodeUpdate):
        fields = {k: v for k, v in vars(update).items() if k != "node_num"}
        row = store.upsert_node(update.node_num, **fields)
        await hub.broadcast("node", enrich_node(row))

    async def worker(queue: asyncio.Queue):
        while True:
            kind, item = await queue.get()
            try:
                if kind == "frame":
                    await handle_frame(item)
                else:
                    await handle_node(item)
            except Exception:
                log.exception("Failed to handle %s", kind)

    async def run_radio(queue: asyncio.Queue):
        loop = asyncio.get_running_loop()

        def on_frame(frame):
            loop.call_soon_threadsafe(queue.put_nowait, ("frame", frame))

        def on_node(update):
            loop.call_soon_threadsafe(queue.put_nowait, ("node", update))

        while True:
            try:
                await asyncio.to_thread(radio.start, on_frame, on_node)
                log.info("Radio source started: %s", radio.describe())
                return
            except Exception as exc:
                log.error("Radio %s failed to start (%s); retrying in %ss", radio.describe(), exc, RADIO_RETRY_SECONDS)
                await asyncio.sleep(RADIO_RETRY_SECONDS)

    async def purge_loop():
        while True:
            if config.retention_hours > 0:
                n = store.purge_older_than(time.time() - config.retention_hours * 3600)
                if n:
                    log.info("Retention purge removed %d rows", n)
            await asyncio.sleep(PURGE_INTERVAL_SECONDS)

    @contextlib.asynccontextmanager
    async def lifespan(app: FastAPI):
        queue: asyncio.Queue = asyncio.Queue()
        tasks = [asyncio.create_task(worker(queue)), asyncio.create_task(run_radio(queue)),
                 asyncio.create_task(purge_loop())]
        try:
            yield
        finally:
            for t in tasks:
                t.cancel()
            radio.stop()

    app = FastAPI(title="MeshAid Gateway", lifespan=lifespan)
    app.state.store, app.state.pipeline, app.state.radio, app.state.hub = store, pipeline, radio, hub

    @app.get("/api/health")
    def health():
        return {"radio": radio.describe(), "radio_kind": radio.kind, "connected": radio.connected,
                "clients": len(hub.clients), "time": time.time()}

    @app.get("/api/meta")
    def meta():
        return {"codes": codes.tables, "shelters": {str(k): v for k, v in config.shelters.items()},
                "help_points": sorted(pipeline.gateway.key_store.keys()), "ack_states": ACK_STATES,
                "node_degraded_after": config.node_degraded_after, "node_down_after": config.node_down_after}

    @app.get("/api/messages")
    def list_messages(
        msg_type: Optional[str] = Query(None, alias="type"),
        hp_id: Optional[int] = None,
        ack_state: Optional[str] = None,
        verify_status: Optional[str] = None,
        min_priority: Optional[int] = None,
        sort: str = "priority",
        limit: int = Query(500, le=5000),
    ):
        rows = store.list_messages(msg_type=msg_type, hp_id=hp_id, ack_state=ack_state, verify_status=verify_status,
                                   min_priority=min_priority, sort=sort, limit=limit)
        return [enrich_message(r) for r in rows]

    @app.get("/api/messages/{message_id}")
    def get_message(message_id: int):
        row = store.get_message(message_id)
        if row is None:
            raise HTTPException(404, "message not found")
        return enrich_message(row)

    @app.post("/api/messages/{message_id}/ack")
    async def ack_message(message_id: int, body: AckBody):
        if body.state not in ACK_STATES:
            raise HTTPException(422, f"state must be one of {ACK_STATES}")
        row = store.set_ack_state(message_id, body.state, body.note)
        if row is None:
            raise HTTPException(404, "message not found")
        data = enrich_message(row)
        await hub.broadcast("message_update", data)
        return data

    @app.get("/api/security-events")
    def security_events(kind: Optional[str] = None, limit: int = Query(200, le=5000)):
        return [enrich_event(e) for e in store.list_security_events(kind=kind, limit=limit)]

    @app.get("/api/nodes")
    def nodes():
        now = time.time()
        return [enrich_node(n, now) for n in store.list_nodes()]

    @app.get("/api/stats")
    def stats():
        return store.stats()

    @app.websocket("/ws")
    async def ws(websocket: WebSocket):
        await websocket.accept()
        hub.clients.add(websocket)
        try:
            while True:
                await websocket.receive_text()  # clients don't send anything meaningful; keeps the socket open
        except WebSocketDisconnect:
            pass
        finally:
            hub.clients.discard(websocket)

    if isinstance(radio, SimSource):
        @app.post("/api/dev/inject")
        def dev_inject(body: InjectBody):
            radio.inject(bytes.fromhex(body.wire_hex), from_node=body.from_node, hops=body.hops, snr=body.snr)
            return {"ok": True}

        @app.post("/api/dev/node")
        def dev_node(body: NodeBody):
            radio.set_online(body.node_num, body.online)
            return {"ok": True}

    if config.dashboard_dist.is_dir():
        app.mount("/", StaticFiles(directory=config.dashboard_dist, html=True), name="dashboard")

    return app


def _type_code(codes: Codes, type_key: str) -> str:
    for code, entry in codes.tables["msg_type"].items():
        if entry["key"] == type_key:
            return code
    return type_key


def _guess_role(n: dict) -> str:
    if n.get("hops_away") == 0:
        return "gateway"
    name = (n.get("long_name") or "").lower()
    if "relay" in name:
        return "relay"
    if "help point" in name:
        return "help_point"
    return "node"
