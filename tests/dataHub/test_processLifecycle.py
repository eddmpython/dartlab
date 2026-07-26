"""Owner 와 eager 자식이 공유하는 POSIX process group 봉쇄 tests."""

from __future__ import annotations

import os
import time

import pytest

from dartlab.dataHub.isolation.processLifecycle import (
    becomeProcessGroupLeader,
    processGroupAlive,
    stopProcessGroup,
    waitProcessGroupZero,
)

_isWindows = os.name == "nt"


def testWindowsIsNoOpBecauseJobObjectCoversTheSameRole() -> None:
    """Windows 는 Job Object 가 kill-on-close 로 손자까지 회수하므로 개입하지 않는다."""

    if not _isWindows:
        pytest.skip("Windows 전용 계약")
    assert becomeProcessGroupLeader() is False
    assert processGroupAlive(os.getpid()) is False
    assert stopProcessGroup(os.getpid(), time.perf_counter() + 1) == ()


def testNonePidIsAlwaysTreatedAsReleased() -> None:
    """pid 가 없으면 살아 있는 group 도 없다. 무관한 프로세스를 건드리지 않는다."""

    assert processGroupAlive(None) is False
    assert stopProcessGroup(None, time.perf_counter() + 1) == ()
    assert waitProcessGroupZero(None, time.perf_counter() + 1) is True


def testStopIsSilentWhenGroupIsAlreadyEmpty() -> None:
    """이미 비어 있는 group 에는 신호를 보내지 않는다."""

    if _isWindows:
        pytest.skip("POSIX 전용 계약")
    # 존재할 수 없는 큰 pid. 신호를 보내지 않고 빈 trace 로 끝나야 한다.
    assert stopProcessGroup(4_000_000, time.perf_counter() + 1) == ()


def testWaitReturnsImmediatelyForReleasedGroup() -> None:
    """비어 있는 group 대기는 기한을 소모하지 않는다."""

    startedAt = time.perf_counter()
    assert waitProcessGroupZero(None, startedAt + 5) is True
    assert time.perf_counter() - startedAt < 1.0


def testStalledThreadDescriptionPointsAtTheBlockingFrame() -> None:
    """멈춘 thread 요약은 그 thread 가 실제로 서 있는 파일과 줄을 가리킨다."""

    import threading

    from dartlab.dataHub.isolation.processLifecycle import describeStalledThread

    release = threading.Event()

    def blocked() -> None:
        release.wait(timeout=5.0)

    worker = threading.Thread(target=blocked, daemon=True)
    worker.start()
    try:
        deadline = time.perf_counter() + 2.0
        summary = ""
        while time.perf_counter() < deadline:
            summary = describeStalledThread(worker.ident)
            if "blocked" in summary:
                break
        assert "blocked" in summary
        assert "test_processLifecycle.py" in summary
    finally:
        release.set()
        worker.join(timeout=5.0)


def testStalledThreadDescriptionNeverRaisesOnUnknownThread() -> None:
    """진단 경로가 진단 대상보다 먼저 죽으면 안 된다."""

    from dartlab.dataHub.isolation.processLifecycle import describeStalledThread

    assert describeStalledThread(None) == "thread-ident-unavailable"
    assert describeStalledThread(-1) == "thread-gone"
