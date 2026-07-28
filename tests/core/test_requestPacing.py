"""core/requestPacing.py 미러 . 요청 사이 최소 간격 대기 규칙."""

from __future__ import annotations

import asyncio

import pytest

from dartlab.core.requestPacing import awaitMinInterval, waitMinInterval

pytestmark = pytest.mark.unit


def test_syncSkipsWhenIntervalNotPositive(monkeypatch: pytest.MonkeyPatch) -> None:
    """간격이 0 이하면 시계도 보지 않는다."""
    calls: list[float] = []
    monkeypatch.setattr("time.sleep", lambda seconds: calls.append(seconds))
    monkeypatch.setattr("time.monotonic", lambda: pytest.fail("시계를 보면 안 된다"))
    waitMinInterval(0.0, 0.0)
    waitMinInterval(0.0, -1.0)
    assert calls == []


def test_syncSleepsRemainderOnly(monkeypatch: pytest.MonkeyPatch) -> None:
    """이미 지난 만큼 빼고 남은 시간만 잔다."""
    calls: list[float] = []
    monkeypatch.setattr("time.sleep", lambda seconds: calls.append(seconds))
    monkeypatch.setattr("time.monotonic", lambda: 100.0)
    waitMinInterval(99.7, 1.0)
    assert calls == [pytest.approx(0.7)]


def test_syncDoesNotSleepWhenIntervalPassed(monkeypatch: pytest.MonkeyPatch) -> None:
    """간격이 이미 지났으면 자지 않는다."""
    calls: list[float] = []
    monkeypatch.setattr("time.sleep", lambda seconds: calls.append(seconds))
    monkeypatch.setattr("time.monotonic", lambda: 100.0)
    waitMinInterval(90.0, 1.0)
    assert calls == []


def test_asyncReturnsClockAfterWaiting() -> None:
    """대기 후 다시 읽은 루프 시각을 돌려준다."""

    async def run() -> tuple[float, float]:
        loop = asyncio.get_running_loop()
        before = loop.time()
        after = await awaitMinInterval(before, 0.05)
        return before, after

    before, after = asyncio.run(run())
    assert after >= before


def test_clientsShareOnePacer() -> None:
    """네 클라이언트가 같은 함수 객체를 본다."""
    from dartlab.gather.dart import batch as dartBatch
    from dartlab.gather.edgar import asyncClient as edgarAsync
    from dartlab.gather.edgar import client as edgarSync
    from dartlab.providers.edinet.openapi import client as edinetClient

    assert dartBatch.awaitMinInterval is awaitMinInterval
    assert edgarAsync.awaitMinInterval is awaitMinInterval
    assert edgarSync.waitMinInterval is waitMinInterval
    assert edinetClient.waitMinInterval is waitMinInterval
