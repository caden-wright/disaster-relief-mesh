import json
import logging
from typing import Optional
from urllib import error, request

log = logging.getLogger(__name__)


class RadioBase:
    kind = "base"

    def send(self, wire: bytes) -> None:
        raise NotImplementedError

    def is_connected(self) -> bool:
        return False

    def close(self) -> None:
        pass

    def describe(self) -> str:
        return self.kind


class SimRadio(RadioBase):
    """Development radio. Treats every send as successful and keeps the frame."""

    kind = "sim"

    def __init__(self):
        self.sent_frames: list[bytes] = []

    def send(self, wire: bytes) -> None:
        self.sent_frames.append(bytes(wire))
        log.info("SIM radio accepted %d-byte frame", len(wire))

    def is_connected(self) -> bool:
        return True


class OfflineRadio(RadioBase):
    """Development mode for testing store-and-forward behavior."""

    kind = "offline"

    def send(self, wire: bytes) -> None:
        raise ConnectionError("radio is offline")

    def is_connected(self) -> bool:
        return False


class GatewayDevRadio(RadioBase):
    """
    Development integration adapter.

    Sends an already-encoded MeshAid frame to the existing gateway simulator's
    /api/dev/inject endpoint. The gateway then processes it through its normal
    ingest pipeline.
    """

    kind = "gateway-dev"

    def __init__(self, gateway_url: str):
        self.gateway_url = gateway_url.rstrip("/")
        self.inject_url = f"{self.gateway_url}/api/dev/inject"

    def send(self, wire: bytes) -> None:
        payload = {
            "wire_hex": bytes(wire).hex(),
            "from_node": None,
            "hops": None,
            "snr": None,
        }

        body = json.dumps(payload).encode("utf-8")

        req = request.Request(
            self.inject_url,
            data=body,
            headers={
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=3.0) as response:
                if response.status < 200 or response.status >= 300:
                    raise ConnectionError(
                        f"Gateway returned HTTP {response.status}"
                    )

        except error.HTTPError as exc:
            raise ConnectionError(
                f"Gateway returned HTTP {exc.code}"
            ) from exc

        except error.URLError as exc:
            raise ConnectionError(
                f"Could not reach gateway at {self.gateway_url}: {exc.reason}"
            ) from exc

        log.info(
            "Forwarded %d-byte frame to gateway simulator",
            len(wire),
        )

    def is_connected(self) -> bool:
        health_url = f"{self.gateway_url}/api/health"

        try:
            with request.urlopen(health_url, timeout=1.0) as response:
                return 200 <= response.status < 300
        except Exception:
            return False

    def describe(self) -> str:
        return f"gateway-dev:{self.gateway_url}"


class MeshtasticSerialRadio(RadioBase):
    kind = "meshtastic-serial"

    def __init__(self, port: Optional[str] = None):
        from meshtastic.serial_interface import SerialInterface

        self.port = port
        self.interface = SerialInterface(devPath=port)

    def send(self, wire: bytes) -> None:
        if not self.is_connected():
            raise ConnectionError("Meshtastic radio is not connected")

        self.interface.sendData(bytes(wire))

    def is_connected(self) -> bool:
        if self.interface is None:
            return False

        state = getattr(self.interface, "isConnected", None)

        if state is None:
            return False

        if hasattr(state, "is_set"):
            return bool(state.is_set())

        return bool(state)

    def close(self) -> None:
        if self.interface is not None:
            self.interface.close()
            self.interface = None

    def describe(self) -> str:
        return f"serial:{self.port or 'auto'}"


def make_radio(
    spec: str,
    gateway_url: str = "http://127.0.0.1:8000",
) -> RadioBase:

    spec = (spec or "sim").strip()

    if spec == "sim":
        return SimRadio()

    if spec == "offline":
        return OfflineRadio()

    if spec == "gateway-dev":
        return GatewayDevRadio(gateway_url)

    mode, sep, target = spec.partition(":")

    if mode == "serial":
        return MeshtasticSerialRadio(
            target if sep else None
        )

    raise ValueError(
        f"Unsupported radio spec {spec!r}. "
        "Use sim, offline, gateway-dev, serial, or serial:PORT."
    )