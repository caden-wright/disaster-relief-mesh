"""
Radio sources feeding the gateway (IF-10: mesh message arriving at the uplink).

MeshtasticSource talks to a real node over USB serial or TCP (meshtasticd on a
Pi, or a WiFi-enabled node). The meshtastic library delivers packets through
pubsub topics, not an `onReceive` attribute, so we subscribe to the
PRIVATE_APP topic only. Help Points send with `sendData()`, whose default
portnum is PRIVATE_APP; text, position and telemetry traffic never reaches the
parser.

SimSource has no hardware. Frames are injected through the dev API
(sim.py uses it), and it can emit fake node heartbeats for the mesh-health panel.

Callbacks run on the radio library's thread. The app hands in thread-safe
callbacks (see api.py) that bounce onto the asyncio loop.
"""

import logging
import threading
import time
from dataclasses import dataclass
from typing import Callable, Optional

log = logging.getLogger(__name__)

PRIVATE_APP_TOPIC = "meshtastic.receive.data.PRIVATE_APP"


@dataclass
class RadioFrame:
    wire: bytes
    received_at: float            # wall clock, when the gateway got it off the radio
    from_node: Optional[int] = None
    snr: Optional[float] = None
    hops: Optional[int] = None


@dataclass
class NodeUpdate:
    node_num: int
    node_id: Optional[str] = None
    long_name: Optional[str] = None
    short_name: Optional[str] = None
    last_heard: Optional[float] = None
    snr: Optional[float] = None
    hops_away: Optional[int] = None
    battery: Optional[int] = None


FrameCallback = Callable[[RadioFrame], None]
NodeCallback = Callable[[NodeUpdate], None]


class RadioSource:
    kind = "base"

    def start(self, on_frame: FrameCallback, on_node: NodeCallback) -> None:
        raise NotImplementedError

    def stop(self) -> None:
        pass

    @property
    def connected(self) -> bool:
        return False

    def describe(self) -> str:
        return self.kind


def node_update_from_meshtastic(node: dict) -> NodeUpdate:
    user = node.get("user") or {}
    metrics = node.get("deviceMetrics") or {}
    return NodeUpdate(
        node_num=node["num"],
        node_id=user.get("id"),
        long_name=user.get("longName"),
        short_name=user.get("shortName"),
        last_heard=node.get("lastHeard"),
        snr=node.get("snr"),
        hops_away=node.get("hopsAway"),
        battery=metrics.get("batteryLevel"),
    )


def frame_from_packet(packet: dict, received_at: Optional[float] = None) -> Optional[RadioFrame]:
    decoded = packet.get("decoded") or {}
    payload = decoded.get("payload")
    if not isinstance(payload, (bytes, bytearray)):
        return None
    hops = None
    if packet.get("hopStart") is not None and packet.get("hopLimit") is not None:
        hops = packet["hopStart"] - packet["hopLimit"]
    return RadioFrame(
        wire=bytes(payload),
        received_at=received_at or time.time(),
        from_node=packet.get("from"),
        snr=packet.get("rxSnr"),
        hops=hops,
    )


class MeshtasticSource(RadioSource):
    kind = "meshtastic"

    def __init__(self, spec: str):
        # "serial", "serial:COM5", "tcp:10.0.0.2", "tcp:10.0.0.2:4403"
        mode, _, target = spec.partition(":")
        if mode not in ("serial", "tcp"):
            raise ValueError(f"Unsupported radio spec {spec!r}")
        self.mode, self.target = mode, target or None
        self.interface = None
        self._on_frame: Optional[FrameCallback] = None
        self._on_node: Optional[NodeCallback] = None

    def describe(self) -> str:
        return f"{self.mode}:{self.target or 'auto'}"

    def start(self, on_frame, on_node):
        from pubsub import pub

        self._on_frame, self._on_node = on_frame, on_node
        # Subscribe before connecting so the initial node DB dump is not missed.
        pub.subscribe(self._handle_packet, PRIVATE_APP_TOPIC)
        pub.subscribe(self._handle_node, "meshtastic.node.updated")

        if self.mode == "serial":
            from meshtastic.serial_interface import SerialInterface
            self.interface = SerialInterface(devPath=self.target)
        else:
            from meshtastic.tcp_interface import TCPInterface
            host, _, port = (self.target or "localhost").partition(":")
            self.interface = TCPInterface(hostname=host, portNumber=int(port or 4403))

        for node in (self.interface.nodes or {}).values():
            self._handle_node(node, self.interface)
        log.info("Meshtastic connected via %s", self.describe())

    def stop(self):
        from pubsub import pub

        for listener, topic in ((self._handle_packet, PRIVATE_APP_TOPIC),
                                (self._handle_node, "meshtastic.node.updated")):
            try:
                pub.unsubscribe(listener, topic)
            except Exception:
                pass
        if self.interface is not None:
            self.interface.close()
            self.interface = None

    @property
    def connected(self) -> bool:
        return self.interface is not None and bool(getattr(self.interface, "isConnected", None)
                                                   and self.interface.isConnected.is_set())

    def _handle_packet(self, packet, interface):
        if interface is not self.interface or self._on_frame is None:
            return
        frame = frame_from_packet(packet)
        if frame is not None:
            self._on_frame(frame)

    def _handle_node(self, node, interface):
        if interface is not self.interface or self._on_node is None or "num" not in node:
            return
        self._on_node(node_update_from_meshtastic(node))


# Fixed demo topology for the simulator. node_num -> (node_id, long_name, short_name, hops_away)
SIM_NODES = {
    0x0A000001: ("!0a000001", "Gateway (Incident Command)", "GW", 0),
    0x0A000011: ("!0a000011", "Relay 1 (solar)", "R1", 1),
    0x0A000012: ("!0a000012", "Relay 2 (battery)", "R2", 1),
    0x0A000101: ("!0a000101", "Help Point 1", "HP1", 2),
    0x0A000102: ("!0a000102", "Help Point 2", "HP2", 3),
}
SIM_HP_NODE = {1: 0x0A000101, 2: 0x0A000102}


class SimSource(RadioSource):
    kind = "sim"

    def __init__(self, heartbeat_seconds: float = 20.0, emit_heartbeats: bool = True):
        self.heartbeat_seconds = heartbeat_seconds
        self.emit_heartbeats = emit_heartbeats
        self.offline: set = set()
        self._on_frame: Optional[FrameCallback] = None
        self._on_node: Optional[NodeCallback] = None
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self, on_frame, on_node):
        self._on_frame, self._on_node = on_frame, on_node
        self._heartbeat_all()
        if self.emit_heartbeats:
            self._thread = threading.Thread(target=self._loop, name="sim-heartbeat", daemon=True)
            self._thread.start()

    def stop(self):
        self._stop.set()

    @property
    def connected(self) -> bool:
        return self._on_frame is not None and not self._stop.is_set()

    def inject(self, wire: bytes, from_node=None, hops=None, snr=None):
        if self._on_frame is None:
            raise RuntimeError("SimSource not started")
        self._on_frame(RadioFrame(wire=wire, received_at=time.time(), from_node=from_node, snr=snr, hops=hops))

    def set_online(self, node_num: int, online: bool):
        (self.offline.discard if online else self.offline.add)(node_num)
        if online:
            self._heartbeat(node_num)

    def _loop(self):
        while not self._stop.wait(self.heartbeat_seconds):
            self._heartbeat_all()

    def _heartbeat_all(self):
        for node_num in SIM_NODES:
            if node_num not in self.offline:
                self._heartbeat(node_num)

    def _heartbeat(self, node_num: int):
        node_id, long_name, short_name, hops = SIM_NODES.get(node_num, (None, None, None, None))
        self._on_node(NodeUpdate(node_num=node_num, node_id=node_id, long_name=long_name, short_name=short_name,
                                 last_heard=time.time(), snr=9.5 - 2 * (hops or 0), hops_away=hops,
                                 battery=None if hops == 0 else 80))


def make_source(spec: str, *, sim_heartbeats: bool = True) -> RadioSource:
    if spec == "sim":
        return SimSource(emit_heartbeats=sim_heartbeats)
    return MeshtasticSource(spec)
