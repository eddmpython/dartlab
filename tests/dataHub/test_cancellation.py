"""실행 중 DataHub query 취소 신호 tests."""

from __future__ import annotations

import threading

import pytest

from dartlab.dataHub.cancellation import (
    CancellationToken,
    activeCancellation,
    currentCancellation,
    raiseIfCancelled,
)
from dartlab.dataHub.continuation import ContinuationError


def testNoTokenMeansCheckIsFree() -> None:
    """취소를 쓰지 않는 경로는 아무 영향도 받지 않는다."""

    assert currentCancellation() is None
    raiseIfCancelled()


def testBoundTokenStopsExecutionAtCheckPoint() -> None:
    """결박된 토큰이 취소되면 확인 지점에서 중단한다."""

    token = CancellationToken("leaseLost")
    with activeCancellation(token):
        raiseIfCancelled()
        token.cancel()
        with pytest.raises(ContinuationError) as captured:
            raiseIfCancelled()
    assert captured.value.code == "CONTINUATION_TIMEOUT"


def testCancellationIsScopedToItsContext() -> None:
    """구간을 벗어나면 이전 결박으로 되돌아간다."""

    outer = CancellationToken("outer")
    inner = CancellationToken("inner")
    with activeCancellation(outer):
        assert currentCancellation() is outer
        with activeCancellation(inner):
            assert currentCancellation() is inner
        assert currentCancellation() is outer
    assert currentCancellation() is None


def testTokenCancelledFromAnotherThreadIsObserved() -> None:
    """heartbeat 처럼 다른 스레드가 취소해도 실행 스레드가 관측한다."""

    token = CancellationToken("leaseLost")
    started = threading.Event()

    def canceller() -> None:
        started.wait(timeout=5)
        token.cancel()

    worker = threading.Thread(target=canceller, daemon=True)
    worker.start()
    with activeCancellation(token):
        started.set()
        worker.join(timeout=5)
        with pytest.raises(ContinuationError):
            raiseIfCancelled()


def testCancellationIsOneWay() -> None:
    """한 번 취소되면 되돌릴 수 없다. 재실행은 새 토큰으로 시작한다."""

    token = CancellationToken()
    assert token.cancelled is False
    token.cancel()
    token.cancel()
    assert token.cancelled is True
