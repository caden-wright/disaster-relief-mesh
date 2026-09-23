import os
from dataclasses import dataclass
from pathlib import Path

HELP_POINT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = HELP_POINT_DIR.parent


@dataclass
class Config:
    help_point_id: int = int(os.getenv("MESHAID_HELP_POINT_ID", "1"))
    host: str = os.getenv("MESHAID_HELP_POINT_HOST", "127.0.0.1")
    port: int = int(os.getenv("MESHAID_HELP_POINT_PORT", "8001"))
    
    # sim | offline | gateway-dev | serial | serial:COM5 | serial:/dev/ttyUSB0
    radio: str = os.getenv("MESHAID_HELP_POINT_RADIO", "sim")

    gateway_dev_url: str = os.getenv(
        "MESHAID_GATEWAY_DEV_URL",
        "http://127.0.0.1:8000",
    )

    # sim | offline | serial | serial:COM5 | serial:/dev/ttyUSB0
    radio: str = os.getenv("MESHAID_HELP_POINT_RADIO", "sim")

    data_dir: Path = Path(
        os.getenv("MESHAID_HELP_POINT_DATA", str(HELP_POINT_DIR / "data"))
    )
    codes_path: Path = Path(
        os.getenv("MESHAID_CODES_PATH", str(PROJECT_ROOT / "shared" / "codes.json"))
    )
    key_path: Path | None = None

    def __post_init__(self):
        self.data_dir = Path(self.data_dir)
        self.codes_path = Path(self.codes_path)

        if self.key_path is None:
            env_key = os.getenv("MESHAID_HELP_POINT_KEY")
            if env_key:
                self.key_path = Path(env_key)
            else:
                # provision_keys.py defaults to an output directory named "keys".
                self.key_path = PROJECT_ROOT / "keys" / f"help_point_{self.help_point_id}.key"
        else:
            self.key_path = Path(self.key_path)

    @property
    def counter_path(self) -> Path:
        return self.data_dir / "counter.txt"

    @property
    def queue_path(self) -> Path:
        return self.data_dir / "queue.json"
    
    
