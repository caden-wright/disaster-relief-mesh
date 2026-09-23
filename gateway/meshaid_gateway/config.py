"""
Gateway configuration.

Values come from an optional JSON file (see config.example.json) and can be
overridden on the command line. Everything has a default so the gateway runs
in simulator mode with no config at all.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

GATEWAY_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = GATEWAY_DIR.parent


@dataclass
class Config:
    # "sim", "serial" (auto-detect), "serial:COM5", "serial:/dev/ttyUSB0", "tcp:10.0.0.2", "tcp:host:4403"
    radio: str = "sim"
    key_store_path: Path = GATEWAY_DIR / "dev_keys" / "gateway_key_store.json"
    db_path: Path = GATEWAY_DIR / "meshaid_gateway.db"
    codes_path: Path = REPO_ROOT / "shared" / "codes.json"
    dashboard_dist: Path = REPO_ROOT / "dashboard" / "dist"
    host: str = "127.0.0.1"
    port: int = 8000

    # Help Point id -> shelter display name
    shelters: dict = field(default_factory=dict)
    # Meshtastic node id ("!a1b2c3d4") -> {"role": "help_point"|"relay"|"gateway", "hp_id": int, "label": str}
    nodes: dict = field(default_factory=dict)

    # Post-authentication rate limit (Evan's RateLimiter defaults: 20 per 5 min)
    rate_capacity: int = 20
    rate_refill_seconds: float = 300.0

    # Data retention (SRS 8.7). 0 disables purging.
    retention_hours: float = 72.0

    # Node health thresholds, seconds since last heard
    node_degraded_after: float = 900.0
    node_down_after: float = 3600.0

    # Sim mode: auto-create dev keys for this many Help Points if the key store is missing
    sim_help_points: int = 2

    @property
    def is_sim(self) -> bool:
        return self.radio == "sim"

    def shelter_name(self, hp_id: Optional[int]) -> str:
        if hp_id is None:
            return "Unknown"
        return self.shelters.get(str(hp_id)) or self.shelters.get(hp_id) or f"Help Point {hp_id}"


_PATH_FIELDS = {"key_store_path", "db_path", "codes_path", "dashboard_dist"}


def load_config(path: Optional[Path] = None, **overrides) -> Config:
    data = {}
    if path is not None:
        path = Path(path)
        data = json.loads(path.read_text(encoding="utf-8"))
        base = path.parent
        for key in _PATH_FIELDS & data.keys():
            p = Path(data[key])
            data[key] = p if p.is_absolute() else (base / p).resolve()

    data.update({k: v for k, v in overrides.items() if v is not None})
    for key in _PATH_FIELDS & data.keys():
        data[key] = Path(data[key])

    known = Config.__dataclass_fields__.keys()
    unknown = set(data) - set(known)
    if unknown:
        raise ValueError(f"Unknown config keys: {sorted(unknown)}")
    return Config(**data)
