"""Owner 와 eager 자식 프로세스가 공유하는 수명 주기 봉쇄.

Windows 는 Job Object 가 kill-on-close 로 손자 프로세스까지 회수한다. POSIX 에는
대응물이 없으므로 자식이 `os.setsid()` 로 새 session leader 가 되고 부모가 그 group
전체에 신호를 보낸다. 그래야 자식이 남긴 손자까지 zero-live 로 판정할 수 있다.

이 봉쇄가 없으면 자식이 손자를 남겨도 `multiprocessing.active_children()` 이 직속
자식만 훑기 때문에 zero-live 가 참으로 보고된다.

자식이 태어난 직후 무거운 C 확장을 main thread 에서 먼저 여는 것(`warmChildImports`)도
같은 수명 주기의 일부라 여기 둔다. owner lane 과 eager lane 이 그 목록까지 같았다.
"""

from __future__ import annotations

import importlib
import logging
import os
import signal
import sys
import time
import traceback
from pathlib import Path

from dartlab.dataHub.telemetry import recordFailure

_STALL_FRAME_LIMIT = 6

# 자식이 main thread 에서 먼저 열어 두는 무거운 모듈. worker thread 최초 import 교착 회피.
_WARM_MODULES = (
    "polars",
    "pyarrow",
    "dartlab.dataHub.paging.owner",
    "dartlab.dataHub.paging.composite",
    "dartlab.dataHub.execution",
)


def warmChildImports(log: logging.Logger) -> None:
    """무거운 모듈을 main thread 에서 먼저 import 한다.

    worker 는 별도 thread 에서 돌고, 자식은 fresh spawn 이라 polars 와 pyarrow 같은
    C 확장을 그 thread 에서 최초로 import 하게 된다. POSIX 에서 비-main thread 의
    C 확장 최초 import 는 확장이 설치하는 thread pool 이나 lock 때문에 교착할 수 있고,
    그러면 자식이 자기 기한을 꽉 채우고도 끝나지 않는다.

    sandbox 를 이미 설치한 뒤 호출하므로 write 와 network 차단은 그대로 유지된다.
    실패는 삼키지 않고 worker 가 같은 import 를 다시 시도해 typed 오류로 보고하게 둔다.

    Args:
        log: 부르는 lane 의 logger. 실패 기록이 어느 lane 에서 났는지 남긴다.

    Returns:
        None.

    Raises:
        없음. 개별 import 실패는 ``CHILD_WARM_IMPORT_FAILED`` 로 기록만 한다.

    Example:
        ``warmChildImports(_log)``
    """

    for moduleName in _WARM_MODULES:
        try:
            importlib.import_module(moduleName)
        except Exception:
            recordFailure(log, "CHILD_WARM_IMPORT_FAILED", context={"module": moduleName})


def describeStalledThread(threadIdent: int | None) -> str:
    """기한을 넘긴 worker thread 가 서 있는 지점을 한 줄로 요약한다.

    Capabilities:
        살아 있는 thread 의 현재 frame 을 잡아 파일명, 줄번호, 함수명으로 압축한다.

    AIContext:
        자식이 기한을 다 쓰고도 끝나지 않을 때 부모가 받는 것은 평평한 실패 코드뿐이라
        어디서 멈췄는지 알 수 없다. 이 요약이 그 공백을 메운다.

    Guide:
        반환값은 진단용이라 자식 stderr 로 내보내고 공개 payload 에는 싣지 않는다.

    When:
        `Thread.join(timeout=...)` 이 만료됐는데 thread 가 여전히 살아 있을 때.

    How:
        `sys._current_frames()` 에서 해당 ident 의 frame 을 찾아 안쪽 몇 개만 남긴다.

    Requires:
        `threading.Thread.ident`. `native_id` 는 frame 표의 키가 아니라 쓸 수 없다.

    Raises:
        올리지 않는다. 진단 경로가 진단 대상보다 먼저 죽으면 안 된다.

    Example:
        ``describeStalledThread(worker.ident)``.

    See Also:
        ``waitProcessGroupZero``.
    """

    if threadIdent is None:
        return "thread-ident-unavailable"
    try:
        frame = sys._current_frames().get(threadIdent)
    except Exception:
        return "thread-frames-unavailable"
    if frame is None:
        return "thread-gone"
    try:
        stack = traceback.extract_stack(frame)
    except Exception:
        return "thread-stack-unavailable"
    tail = stack[-_STALL_FRAME_LIMIT:]
    return " <- ".join(f"{Path(item.filename).name}:{item.lineno}:{item.name}" for item in reversed(tail))


def becomeProcessGroupLeader() -> bool:
    """POSIX 자식이 새 session 을 열어 손자까지 한 group 에 묶는다.

    Capabilities:
        부모가 group 단위로 신호를 보낼 수 있는 봉쇄 경계를 만든다.

    Returns:
        새 group leader 가 됐으면 ``True``. Windows 이거나 이미 leader 면 ``False``.

    Example:
        ``becomeProcessGroupLeader()``.

    Guide:
        자식 진입점에서 다른 작업보다 먼저 호출한다.

    When:
        spawn 된 owner 또는 eager 자식이 시작하자마자 호출한다.

    How:
        POSIX 에서만 `os.setsid()` 를 시도하고 실패는 무시한다.

    See Also:
        ``stopProcessGroup``.

    Requires:
        Windows 에서는 아무 일도 하지 않는다. Job Object 가 같은 역할을 한다.

    AI Context:
        이미 group leader 인 프로세스에서 `setsid` 는 PermissionError 다. 정상 상황이다.
    """

    if os.name == "nt":
        return False
    try:
        os.setsid()
    except (AttributeError, OSError):
        return False
    return True


def processGroupAlive(pid: int | None) -> bool:
    """POSIX process group 에 살아 있는 구성원이 있는지 확인한다."""

    if os.name == "nt" or pid is None:
        return False
    try:
        os.killpg(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def waitProcessGroupZero(pid: int | None, deadline: float) -> bool:
    """Group 이 비워질 때까지 기한 안에서 기다린다."""

    while processGroupAlive(pid) and time.perf_counter() < deadline:
        time.sleep(min(0.01, max(0.0, deadline - time.perf_counter())))
    return not processGroupAlive(pid)


def stopProcessGroup(pid: int | None, deadline: float) -> tuple[str, ...]:
    """POSIX process group 전체를 SIGTERM 뒤 SIGKILL 로 회수한다.

    Capabilities:
        자식이 남긴 손자 프로세스까지 한 번에 정리한다.

    Args:
        pid: 자식 pid. 자식이 group leader 이므로 pgid 와 같다.
        deadline: `time.perf_counter()` 기준 절대 기한.

    Returns:
        실제 수행한 단계 trace. Windows 에서는 빈 tuple.

    Example:
        ``trace = stopProcessGroup(process.pid, deadline)``.

    Guide:
        Windows 는 Job Object close 가 같은 역할을 하므로 호출해도 무해하다.

    When:
        자식 종료 절차에서 terminate 와 kill 사이 또는 직후에 호출한다.

    How:
        group 이 살아 있는 동안만 신호를 보내고 각 단계마다 비워지길 기다린다.

    See Also:
        ``becomeProcessGroupLeader`` 와 ``waitProcessGroupZero``.

    Requires:
        자식이 `becomeProcessGroupLeader` 로 leader 가 돼 있어야 효과가 있다.

    AI Context:
        group 이 이미 비었으면 신호를 보내지 않는다. 무관한 프로세스를 건드리지 않는다.
    """

    if os.name == "nt" or pid is None:
        return ()
    trace: list[str] = []
    for activeSignal, label, waitSeconds in (
        (signal.SIGTERM, "groupTerminate", 0.05),
        (signal.SIGKILL, "groupKill", None),
    ):
        if not processGroupAlive(pid):
            break
        try:
            os.killpg(pid, activeSignal)
            trace.append(label)
        except ProcessLookupError:
            break
        except OSError:
            break
        waitDeadline = deadline if waitSeconds is None else min(deadline, time.perf_counter() + waitSeconds)
        waitProcessGroupZero(pid, waitDeadline)
    return tuple(trace)


__all__ = [
    "becomeProcessGroupLeader",
    "describeStalledThread",
    "processGroupAlive",
    "stopProcessGroup",
    "waitProcessGroupZero",
]
