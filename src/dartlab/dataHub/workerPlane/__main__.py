"""원격 DataHub pull worker 실행 진입점."""

from __future__ import annotations

import argparse
import os
import signal
import socket
import threading

from .worker import DataHubWorker


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="DartLab DataHub 분산 worker")
    parser.add_argument("--base-url", required=True, help="DataHub server base URL")
    parser.add_argument(
        "--worker-id",
        default=f"{socket.gethostname()}-{os.getpid()}",
        help="control plane에 기록할 고유 worker ID",
    )
    parser.add_argument("--lease-seconds", type=float, default=120)
    parser.add_argument("--idle-seconds", type=float, default=1)
    return parser


def main(argv: list[str] | None = None) -> int:
    """환경변수 token으로 worker를 시작하고 종료 신호를 정리한다."""

    args = _parser().parse_args(argv)
    token = os.environ.get("DARTLAB_DATA_HUB_WORKER_TOKEN")
    if not token:
        raise SystemExit("DARTLAB_DATA_HUB_WORKER_TOKEN이 필요합니다")
    stop = threading.Event()

    def requestStop(_signum: int, _frame: object) -> None:
        """운영체제 종료 신호를 worker 중단 이벤트로 변환한다."""

        stop.set()

    signal.signal(signal.SIGINT, requestStop)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, requestStop)

    worker = DataHubWorker(
        args.base_url,
        token,
        args.worker_id,
        leaseSeconds=args.lease_seconds,
    )
    try:
        worker.runForever(idleSeconds=args.idle_seconds, stop=stop)
    finally:
        worker.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
