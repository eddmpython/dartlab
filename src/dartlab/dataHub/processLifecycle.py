"""Owner 와 eager 자식 프로세스가 공유하는 POSIX process group 봉쇄.

Windows 는 Job Object 가 kill-on-close 로 손자 프로세스까지 회수한다. POSIX 에는
대응물이 없으므로 자식이 `os.setsid()` 로 새 session leader 가 되고 부모가 그 group
전체에 신호를 보낸다. 그래야 자식이 남긴 손자까지 zero-live 로 판정할 수 있다.

이 봉쇄가 없으면 자식이 손자를 남겨도 `multiprocessing.active_children()` 이 직속
자식만 훑기 때문에 zero-live 가 참으로 보고된다.
"""

from __future__ import annotations

import os
import signal
import time


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
    "processGroupAlive",
    "stopProcessGroup",
    "waitProcessGroupZero",
]
