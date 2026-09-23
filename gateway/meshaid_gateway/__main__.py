"""
Run the gateway:

    python -m meshaid_gateway                          # simulator, no hardware
    python -m meshaid_gateway --radio serial:COM5      # node on USB (Windows)
    python -m meshaid_gateway --radio serial           # auto-detect USB node
    python -m meshaid_gateway --radio tcp:127.0.0.1    # meshtasticd on the Pi
    python -m meshaid_gateway --config gateway/config.json
"""

import argparse
import logging

import uvicorn

from .api import create_app
from .config import load_config


def main(argv=None):
    p = argparse.ArgumentParser(prog="meshaid_gateway", description="MeshAid Gateway + Incident Command backend")
    p.add_argument("--config", help="JSON config file (see config.example.json)")
    p.add_argument("--radio", help="sim | serial[:PORT] | tcp:HOST[:PORT]")
    p.add_argument("--keys", dest="key_store_path", help="gateway_key_store.json from provision_keys.py")
    p.add_argument("--db", dest="db_path", help="SQLite database path")
    p.add_argument("--host", help="bind address (use 0.0.0.0 to serve other laptops on the LAN)")
    p.add_argument("--port", type=int)
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s")

    overrides = {k: v for k, v in vars(args).items() if k not in ("config", "verbose")}
    config = load_config(args.config, **overrides)
    if config.is_sim and not args.config:
        # Sim heartbeats every 20 s, so let dropped nodes show up quickly in the demo.
        config.node_degraded_after, config.node_down_after = 60.0, 120.0

    app = create_app(config)
    logging.getLogger(__name__).info("Dashboard: http://%s:%d", config.host, config.port)
    uvicorn.run(app, host=config.host, port=config.port, log_level="warning")


if __name__ == "__main__":
    main()
