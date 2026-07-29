"""함수 RSS 사후조건과 단일 background OOM tripwire."""

from __future__ import annotations

import functools
import os
import sys
import threading
import traceback
from collections.abc import Callable
from typing import Any, TypeVar

from dartlab.core.memory.metrics import PRESSURE_EMERGENCY_MB, getMemoryMb

F = TypeVar("F", bound=Callable[..., Any])


class MemoryBudgetExceeded(RuntimeError):
    """함수 반환 시점 RSS delta가 선언한 예산을 초과했다."""


def withMemoryBudget(
    limitMb: int,
    *,
    sampler: Callable[[], float] | None = None,
) -> Callable[[F], F]:
    """함수의 반환 시점 retained RSS delta를 검증한다.

    Capabilities:
        함수 진입과 정상 반환 시점 RSS 차이를 typed error로 강제한다.
    AIContext:
        대형 수집·분석 함수가 호출 뒤 과도한 native heap을 남겼는지 검증한다.
    Guide:
        mid-call abort나 순간 peak guard가 아니다. 실행 중 절대 RSS 방어는 OomTripwire다.
    When:
        정상 반환 뒤에도 큰 RSS 증가가 남으면 결과를 발행하지 않아야 할 때 적용한다.
    How:
        주입 sampler를 진입·반환에 한 번씩 호출하고 delta가 limit보다 크면 예외를 낸다.
    Requires:
        sampler는 같은 MB 단위의 현재 RSS를 반환해야 한다.
    Raises:
        ValueError: limitMb가 음수일 때.
    Args:
        limitMb: 허용할 반환 시점 RSS 증가량 MB.
        sampler: 테스트 또는 플랫폼별 RSS sampler.
    Returns:
        원본 metadata를 보존하는 decorator.
    Example:
        >>> @withMemoryBudget(500)
        ... def build():
        ...     return {}
    SeeAlso:
        OomTripwire, MemoryBudgetExceeded
    """
    if limitMb < 0:
        raise ValueError("limitMb는 0 이상이어야 합니다")
    sample = sampler if sampler is not None else getMemoryMb

    def _decorator(fn: F) -> F:
        @functools.wraps(fn)
        def _wrapper(*args: Any, **kwargs: Any) -> Any:
            before = sample()
            result = fn(*args, **kwargs)
            after = sample()
            if before >= 0 and after >= 0:
                delta = after - before
                if delta > limitMb:
                    raise MemoryBudgetExceeded(
                        f"{fn.__qualname__}: RSS delta {delta:.0f}MB > budget {limitMb}MB "
                        f"(before={before:.0f}MB after={after:.0f}MB)"
                    )
            return result

        return _wrapper  # type: ignore[return-value]

    return _decorator


class OomTripwire:
    """절대 RSS 임계 초과를 background thread에서 감시한다."""

    def __init__(
        self,
        *,
        thresholdMb: float = PRESSURE_EMERGENCY_MB,
        intervalSec: float = 0.5,
        sampler: Callable[[], float] | None = None,
        exiter: Callable[[float], None] | None = None,
    ) -> None:
        if thresholdMb <= 0:
            raise ValueError("thresholdMb는 0보다 커야 합니다")
        if intervalSec <= 0:
            raise ValueError("intervalSec는 0보다 커야 합니다")
        self._thresholdMb = thresholdMb
        self._intervalSec = intervalSec
        self._sampler = sampler if sampler is not None else getMemoryMb
        self._exiter = exiter if exiter is not None else self._defaultExiter
        self._stop = threading.Event()
        self._stateLock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._failure: BaseException | None = None
        self._failureStage: str | None = None

    @staticmethod
    def _defaultExiter(rss: float) -> None:
        sys.stderr.write(f"\n[OomTripwire] RSS {rss:.0f}MB > EMERGENCY threshold — exit 137.\n")
        traceback.print_stack(file=sys.stderr)
        os._exit(137)

    def start(self) -> None:
        """살아 있는 watcher가 없을 때 단일 daemon thread를 시작한다.

        Requires:
            생성자에서 유효한 sampler와 exiter가 설정되어 있어야 한다.
        Raises:
            RuntimeError: 이전 background 실패를 stop으로 아직 확인하지 않았을 때.
        Example:
            >>> watcher = OomTripwire(sampler=lambda: 0.0)
            >>> watcher.start()
            >>> watcher.stop()
        """
        with self._stateLock:
            if self._thread is not None and self._thread.is_alive():
                return
            if self._failure is not None:
                stage = self._failureStage or "background"
                raise RuntimeError(f"이전 OomTripwire {stage} 실패를 stop()으로 확인해야 합니다") from self._failure
            self._stop.clear()
            self._thread = threading.Thread(target=self._loop, daemon=True, name="OomTripwire")
            self._thread.start()

    def stop(self, *, timeout: float = 2.0) -> None:
        """watcher를 정지하고 sampler 실패 또는 join timeout을 호출자에게 전달한다.

        Capabilities:
            단일 watcher의 종료 여부를 확인하고 거짓 성공 상태를 만들지 않는다.
        AIContext:
            Company context 종료가 OOM 보호 thread를 확실히 회수했는지 보장한다.
        Guide:
            timeout 뒤 thread가 살아 있으면 같은 객체를 다시 start하지 말고 재정지한다.
        When:
            Company context 또는 명시적 대형 작업 범위가 끝났을 때 호출한다.
        How:
            stop Event를 설정하고 join한 뒤 실제 생존 상태와 background failure를 검사한다.
        Requires:
            timeout은 0 이상이어야 한다.
        Raises:
            ValueError: timeout이 음수일 때.
            TimeoutError: timeout 안에 watcher가 끝나지 않았을 때.
            RuntimeError: sampler 또는 exiter가 background에서 실패했을 때.
        Args:
            timeout: watcher 종료를 기다릴 최대 초.
        Returns:
            None.
        Example:
            >>> watcher = OomTripwire(sampler=lambda: 0.0)
            >>> watcher.start(); watcher.stop()
        SeeAlso:
            start, withMemoryBudget
        """
        if timeout < 0:
            raise ValueError("timeout은 0 이상이어야 합니다")
        with self._stateLock:
            thread = self._thread
            if thread is None:
                return
            self._stop.set()
        thread.join(timeout=timeout)
        with self._stateLock:
            if thread.is_alive():
                raise TimeoutError(f"OomTripwire thread가 {timeout:g}초 안에 종료되지 않았습니다")
            if self._thread is thread:
                self._thread = None
            failure = self._failure
            failureStage = self._failureStage
            self._failure = None
            self._failureStage = None
        if failure is not None:
            raise RuntimeError(f"OomTripwire {failureStage or 'background'}가 실패했습니다") from failure

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                rss = self._sampler()
            except BaseException as exc:  # background failure를 stop()에서 명시 전파
                with self._stateLock:
                    self._failure = exc
                    self._failureStage = "sampler"
                self._stop.set()
                return
            if rss > self._thresholdMb:
                try:
                    self._exiter(rss)
                except BaseException as exc:
                    with self._stateLock:
                        self._failure = exc
                        self._failureStage = "exiter"
                    self._stop.set()
                return
            self._stop.wait(self._intervalSec)


def finalizeMemoryScope(
    *,
    tripwire: OomTripwire | None,
    cleanup: Callable[[], Any],
    bodyError: BaseException | None,
) -> None:
    """context 본문과 메모리 정리 실패를 잃지 않고 범위를 종료한다.

    Capabilities:
        tripwire 정지와 cache 정리를 모두 시도하고 발생한 모든 예외를 보존한다.
    AIContext:
        DART·EDGAR·EDINET Company context가 같은 오류 전파 계약을 공유한다.
    Guide:
        본문이 정상이라면 단일 정리 실패를 그대로 재발생시킨다.
    When:
        OomTripwire를 시작한 context manager의 ``__exit__``에서 호출한다.
    How:
        종료 작업 실패를 모은 뒤 본문 예외가 있으면 하나의 BaseExceptionGroup으로 묶는다.
    Requires:
        cleanup은 현재 context가 소유한 cache만 정리해야 한다.
    Raises:
        정리 단계의 단일 예외 또는 본문·정리 실패를 보존한 예외 그룹.
    Args:
        tripwire: 시작했을 수 있는 watcher. 없으면 None.
        cleanup: cache와 RSS 경계를 정리할 callable.
        bodyError: context 본문에서 발생한 예외. 정상 종료면 None.
    Returns:
        정리 실패가 없으면 None.
    Example:
        >>> finalizeMemoryScope(tripwire=None, cleanup=lambda: None, bodyError=None)
    SeeAlso:
        OomTripwire.stop
    """
    failures: list[BaseException] = []
    if tripwire is not None:
        try:
            tripwire.stop()
        except BaseException as exc:  # 두 종료 작업을 모두 시도한 뒤 함께 전파한다.
            failures.append(exc)
    try:
        cleanup()
    except BaseException as exc:  # 본문 예외와 정리 실패를 모두 보존한다.
        failures.append(exc)

    if not failures:
        return
    if bodyError is not None:
        raise BaseExceptionGroup(
            "Company context 본문과 메모리 정리가 함께 실패했습니다",
            [bodyError, *failures],
        ) from None
    if len(failures) == 1:
        raise failures[0]
    raise BaseExceptionGroup("Company context 메모리 정리가 실패했습니다", failures) from None


class MemoryScope:
    """Company context의 단일 OomTripwire와 활성 상태를 소유한다."""

    __slots__ = ("_tripwire", "_active", "_lock")

    def __init__(self, tripwire: OomTripwire | None = None) -> None:
        self._tripwire = tripwire if tripwire is not None else OomTripwire()
        self._active = False
        self._lock = threading.Lock()

    @property
    def active(self) -> bool:
        """현재 scope가 enter 뒤 정상 exit 전인지 반환한다."""
        with self._lock:
            return self._active

    def enter(self) -> None:
        """단일 tripwire를 시작하고 같은 scope의 중첩 진입을 거부한다.

        Capabilities:
            순차 context에서는 watcher를 재사용하고 중첩 context에서는 참조 유실을 막는다.
        AIContext:
            DART·EDGAR·EDINET Company가 같은 메모리 감시 수명주기를 공유한다.
        Guide:
            Company ``__enter__``에서만 호출하고 성공한 진입마다 exit를 한 번 호출한다.
        When:
            Company context manager가 사용자 본문 실행 직전에 진입할 때.
        How:
            활성 상태를 lock으로 확인한 뒤 기존 OomTripwire를 시작하고 active로 전환한다.
        Requires:
            이전 exit가 성공했거나 아직 한 번도 enter하지 않은 scope여야 한다.
        Raises:
            RuntimeError: 같은 scope가 이미 활성 상태일 때.
            OomTripwire.start가 낸 예외를 그대로 전달한다.
        Returns:
            None.
        Example:
            >>> scope = MemoryScope(OomTripwire(sampler=lambda: 0.0))
            >>> scope.enter()
            >>> scope.exit(cleanup=lambda: None, bodyError=None)
        SeeAlso:
            exit, OomTripwire.start
        """
        with self._lock:
            if self._active:
                raise RuntimeError("같은 Company memory scope는 중첩 진입할 수 없습니다")
            self._tripwire.start()
            self._active = True

    def exit(
        self,
        *,
        cleanup: Callable[[], Any],
        bodyError: BaseException | None,
    ) -> None:
        """tripwire와 cache를 정리하고 성공한 경우에만 scope를 재사용 가능하게 한다.

        Capabilities:
            종료 오류를 보존하고 실패한 scope가 새 watcher로 덮이는 일을 차단한다.
        AIContext:
            provider Company ``__exit__``의 재진입·정리 실패 계약을 한 곳에서 강제한다.
        Guide:
            context 본문 예외는 bodyError로 넘긴다. 정리가 성공하면 Python이 원래 예외를 전파한다.
        When:
            Company context manager가 정상 또는 예외 본문을 마친 직후.
        How:
            활성 상태를 lock으로 확인하고 finalizeMemoryScope가 성공한 뒤 active를 해제한다.
        Requires:
            enter가 성공한 활성 scope여야 하며 cleanup은 해당 Company cache만 정리해야 한다.
        Raises:
            RuntimeError: 활성화되지 않은 scope를 종료하려 할 때.
            finalizeMemoryScope가 보존한 정리 예외 또는 BaseExceptionGroup.
        Args:
            cleanup: provider가 소유한 cache 정리 callable.
            bodyError: context 본문 예외. 정상 종료면 None.
        Returns:
            None.
        Example:
            >>> scope = MemoryScope(OomTripwire(sampler=lambda: 0.0))
            >>> scope.enter()
            >>> scope.exit(cleanup=lambda: None, bodyError=None)
        SeeAlso:
            enter, finalizeMemoryScope
        """
        with self._lock:
            if not self._active:
                raise RuntimeError("활성화되지 않은 Company memory scope는 종료할 수 없습니다")
            finalizeMemoryScope(
                tripwire=self._tripwire,
                cleanup=cleanup,
                bodyError=bodyError,
            )
            self._active = False


__all__ = [
    "MemoryScope",
    "MemoryBudgetExceeded",
    "OomTripwire",
    "finalizeMemoryScope",
    "withMemoryBudget",
]
