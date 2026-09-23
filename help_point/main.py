import argparse
import logging

import uvicorn

from .api import create_app
from .config import Config


def main(argv=None):
    parser = argparse.ArgumentParser(description="MeshAid Help Point backend")
    parser.add_argument("--host")
    parser.add_argument("--port", type=int)
    parser.add_argument("--radio", help="sim | offline | serial | serial:PORT")
    parser.add_argument("--help-point-id", type=int)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    config = Config()

    if args.host:
        config.host = args.host
    if args.port:
        config.port = args.port
    if args.radio:
        config.radio = args.radio
    if args.help_point_id:
        config.help_point_id = args.help_point_id

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )

    app = create_app(config)
    logging.getLogger(__name__).info(
        "Help Point API: http://%s:%d", config.host, config.port
    )
    uvicorn.run(app, host=config.host, port=config.port, log_level="warning")


if __name__ == "__main__":
    main()
