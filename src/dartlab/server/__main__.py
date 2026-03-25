"""``python -m dartlab.server`` 진입점."""

from __future__ import annotations

import argparse
import os

from .runtime import default_host, ensure_port, run_server


def main() -> None:
    parser = argparse.ArgumentParser(description="DartLab web server")
    parser.add_argument("--host", default=None, help="bind host (default: 127.0.0.1, HF Spaces: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=None, help="bind port (default: 8400, HF Spaces: 7860)")
    args = parser.parse_args()

    # HuggingFace Spaces 자동 감지
    isHfSpace = os.environ.get("SPACE_ID") is not None
    host = args.host or ("0.0.0.0" if isHfSpace else default_host())
    port = args.port or (7860 if isHfSpace else 8400)

    status = ensure_port(port)
    if status == "failed":
        raise SystemExit(1)

    run_server(host=host, port=port)


if __name__ == "__main__":
    main()
