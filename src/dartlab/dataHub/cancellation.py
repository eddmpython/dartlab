"""실행 중인 DataHub query 에 취소 신호를 전달하는 협조적 토큰.

취소는 page 경계에서만 관측한다. bounded page 계약이 이미 자연스러운 중단 지점을
만들어 두었으므로, 별도 인터럽트 없이 다음 page 로 넘어가기 직전에 확인하면 된다.
최대 대기는 page 하나의 실행 시간이다.

토큰이 없으면 확인은 무비용이다. 취소를 쓰지 않는 경로는 아무 영향도 받지 않는다.
"""

from __future__ import annotations

import threading
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

from dartlab.dataHub.continuation import ContinuationError

_active: ContextVar[CancellationToken | None] = ContextVar("dataHubCancellation", default=None)


class CancellationToken:
    """스레드 안전한 1 회성 취소 신호.

    Args:
        reason: 취소 사유를 남길 짧은 라벨.

    Example:
        ``token = CancellationToken("leaseLost")``.

    AI Context:
        한 번 취소되면 되돌릴 수 없다. 재실행은 새 토큰으로 시작한다.
    """

    __slots__ = ("_event", "reason")

    def __init__(self, reason: str = "cancelled") -> None:
        self._event = threading.Event()
        self.reason = reason

    def cancel(self) -> None:
        """취소를 표시한다. 이미 취소됐으면 아무 일도 하지 않는다."""

        self._event.set()

    @property
    def cancelled(self) -> bool:
        """취소 여부를 반환한다."""

        return self._event.is_set()


@contextmanager
def activeCancellation(token: CancellationToken | None) -> Iterator[None]:
    """호출 구간에 취소 토큰을 결박한다.

    Capabilities:
        같은 실행 문맥의 page 루프가 별도 인자 전달 없이 토큰을 관측하게 한다.

    Args:
        token: 결박할 토큰. ``None`` 이면 취소를 쓰지 않는다.

    Yields:
        없음.

    Example:
        ``with activeCancellation(token): runQuery()``.

    Guide:
        worker 처럼 외부에서 취소를 받을 수 있는 실행 진입점에서만 감싼다.

    When:
        원격 job 실행이나 장시간 build 를 시작하기 직전에 사용한다.

    How:
        `ContextVar` 로 결박하고 구간을 벗어나면 이전 값으로 되돌린다.

    See Also:
        ``raiseIfCancelled``.

    Requires:
        토큰은 다른 스레드에서 취소될 수 있어야 한다.

    AI Context:
        `ContextVar` 라 같은 스레드의 중첩 실행도 서로 간섭하지 않는다.
    """

    reset = _active.set(token)
    try:
        yield
    finally:
        _active.reset(reset)


def currentCancellation() -> CancellationToken | None:
    """현재 구간에 결박된 취소 토큰을 반환한다."""

    return _active.get()


def raiseIfCancelled() -> None:
    """취소됐으면 page 경계에서 실행을 중단한다.

    Capabilities:
        장시간 build 가 취소 후에도 계속 CPU 를 태우는 것을 막는다.

    Raises:
        ContinuationError: 취소됐을 때 ``CONTINUATION_TIMEOUT``.

    Example:
        ``raiseIfCancelled()``.

    Guide:
        page 경계처럼 중단해도 부분 결과가 commit 되지 않는 지점에서만 호출한다.

    When:
        다음 page 계산을 시작하기 직전에 호출한다.

    How:
        결박된 토큰이 없으면 즉시 반환한다.

    See Also:
        ``activeCancellation``.

    Requires:
        중단은 이미 commit 된 page 를 되돌리지 않는다.

    AI Context:
        취소를 별도 code 로 노출하지 않고 기존 budget 초과와 같은 등급으로 처리한다.
        소비자 입장에서 둘 다 "이 실행은 끝까지 가지 못했다" 로 동일하다.
    """

    token = _active.get()
    if token is not None and token.cancelled:
        raise ContinuationError("CONTINUATION_TIMEOUT")


__all__ = [
    "CancellationToken",
    "activeCancellation",
    "currentCancellation",
    "raiseIfCancelled",
]
