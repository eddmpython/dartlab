"""RSS 읽기가 다른 스레드 때문에 죽던 것에 대한 회귀.

`getMemoryMb` 와 `getPeakRssMb` 는 부를 때마다 구조체 class 를 **함수 안에서 새로 만들고**
그것으로 psapi 함수의 `argtypes` 를 덮어썼다. `ctypes.windll` 은 프로세스 전역 캐시라 그
`argtypes` 는 process 안 모두가 공유한다. 그래서 두 스레드가 겹치면 이렇게 된다.

    스레드 A: argtypes 를 자기 구조체로 설정
    스레드 B: argtypes 를 자기 구조체로 설정   <- A 것을 덮어씀
    스레드 A: 자기 구조체 포인터로 호출        <- ArgumentError

OomTripwire 가 배경 스레드로 RSS 를 폴링하고 BoundedCache 는 본 스레드에서 같은 값을 읽는다.
둘은 늘 함께 돈다. `Company.story` 가 실제로 이것 때문에 죽었다.

`ctypes.ArgumentError` 는 `ValueError` 라서 원래의 `except (AttributeError, OSError,
ImportError)` 에 안 걸렸다. 관측 실패가 그대로 사용자 호출을 무너뜨린 이유다.

여기 고정하는 것은 셋이다. 여러 스레드가 함께 불러도 안 죽는 것, 남이 같은 psapi 함수의
`argtypes` 를 건드려도 안 죽는 것, 그리고 못 읽었을 때 예외 대신 -1.0 을 주는 것.
"""

from __future__ import annotations

import ctypes
import sys
import threading

import pytest

from dartlab.core import memory
from dartlab.core.memory import metrics as memoryMetrics

pytestmark = [pytest.mark.unit]


def testConcurrentReadersDoNotRaise() -> None:
    """배경 폴링과 본 스레드 읽기가 겹쳐도 예외가 없어야 한다."""

    errors: list[BaseException] = []
    stop = threading.Event()

    def spin(fn) -> None:
        while not stop.is_set():
            try:
                fn()
            except BaseException as exc:  # noqa: BLE001
                errors.append(exc)
                return

    workers = [
        threading.Thread(target=spin, args=(fn,), daemon=True) for fn in (memory.getMemoryMb, memory.getPeakRssMb) * 4
    ]
    for worker in workers:
        worker.start()
    for _ in range(2000):
        try:
            memory.getMemoryMb()
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)
            break
    stop.set()
    for worker in workers:
        worker.join(timeout=5)

    assert not errors, f"동시 호출에서 예외: {errors[:3]}"


@pytest.mark.skipif(sys.platform != "win32", reason="psapi 는 Windows 전용")
def testForeignArgtypesDoNotBreakUs() -> None:
    """남이 전역 psapi 함수의 argtypes 를 바꿔도 우리 읽기는 살아야 한다.

    테스트 하니스와 프로파일러가 흔히 하는 일이다. 예전 구현은 그 전역을 같이 쓰고
    있어서, 남이 자기 구조체를 꽂는 순간 우리 호출이 ArgumentError 로 죽었다.
    """

    class _ForeignCounters(ctypes.Structure):
        _fields_ = [("cb", ctypes.c_uint32), ("PageFaultCount", ctypes.c_uint32)]

    foreign = ctypes.windll.psapi.GetProcessMemoryInfo  # type: ignore[attr-defined]
    foreign.argtypes = [ctypes.c_void_p, ctypes.POINTER(_ForeignCounters), ctypes.c_uint32]

    value = memory.getMemoryMb()

    assert value > 0


def testUnreadableCountersGiveMinusOneNotAnException(monkeypatch: pytest.MonkeyPatch) -> None:
    """관측 실패는 -1.0 이어야 한다. 예외면 부르는 쪽이 같이 죽는다."""

    monkeypatch.setattr(memoryMetrics, "_windowsCounters", lambda: None)
    monkeypatch.setattr(memoryMetrics, "_procStatusKb", lambda field: -1.0)

    assert memory.getMemoryMb() == -1.0
    assert memory.getPeakRssMb() == -1.0


def testCtypesArgumentErrorDoesNotEscapeMemoryObservation(monkeypatch: pytest.MonkeyPatch) -> None:
    """ctypes signature 오류도 관측 호출자를 죽이지 않고 측정 불가로 표현한다."""

    class _Counters(ctypes.Structure):
        _fields_ = [
            ("cb", ctypes.c_uint32),
            ("WorkingSetSize", ctypes.c_size_t),
            ("PeakWorkingSetSize", ctypes.c_size_t),
        ]

    def brokenReader(*_args) -> int:
        raise ctypes.ArgumentError("foreign signature")

    monkeypatch.setattr(memoryMetrics.sys, "platform", "win32")
    monkeypatch.setattr(memoryMetrics, "_winMemoryReader", (lambda: None, brokenReader, _Counters))

    assert memory.getMemoryMb() == -1.0
    assert memory.getPeakRssMb() == -1.0
