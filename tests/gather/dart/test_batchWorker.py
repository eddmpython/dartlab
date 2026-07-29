"""mirror smoke — dart/openapi/batchWorker.py (split helper).

분할 helper 모듈의 임포트 가능성 + 룰 7 mirror 슬롯 충족.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def test_import() -> None:
    """clean-interpreter import smoke — pytest 세션 import-order 순환 면역."""
    import subprocess
    import sys

    code = "import dartlab.gather.dart.batchWorker"
    r = subprocess.run([sys.executable, "-X", "utf8", "-c", code], capture_output=True, text=True, timeout=180)
    assert r.returncode == 0, r.stderr


def test_quota_failure_requeues_current_stock(monkeypatch) -> None:
    """키가 소진된 요청의 현재 종목도 pending 큐에서 사라지지 않는다."""
    import asyncio

    from dartlab.core.dartClient import DartApiError
    from dartlab.gather.dart import batchWorker

    class FakeClient:
        exhausted = False

    client = FakeClient()

    async def failFinance(*args, **kwargs):
        client.exhausted = True
        raise DartApiError("020", "요청 제한 초과")

    monkeypatch.setattr(batchWorker, "_collectFinance", failFinance)
    queue = asyncio.Queue()
    queue.put_nowait("005930")
    failures: dict[str, dict[str, str]] = {}

    asyncio.run(
        batchWorker._workerLoop(
            0,
            client,
            queue,
            ["finance"],
            {},
            {"005930": ("00126380", "삼성전자")},
            True,
            None,
            None,
            None,
            failures,
        )
    )

    assert queue.get_nowait() == "005930"
    assert failures["005930"]["finance"].startswith("DartApiError:")
