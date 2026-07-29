"""OS별 프로세스 RSS 측정과 명시적 Python 객체 회수."""

from __future__ import annotations

import ctypes
import gc
import logging
import os
import sys
import threading
from typing import Any

log = logging.getLogger(__name__)

PRESSURE_WARNING_MB = 800.0
PRESSURE_CRITICAL_MB = 1500.0
PRESSURE_FATAL_MB = 2000.0
PRESSURE_EMERGENCY_MB = 2500.0

_WINDOWS_READER_UNAVAILABLE = object()
_winMemoryLock = threading.Lock()
_winMemoryReader: tuple[Any, Any, Any] | object | None = None


def _buildWindowsMemoryReader() -> tuple[Any, Any, Any] | None:
    """프로세스 전용 Win32 RSS reader를 한 번 조립한다."""
    try:
        import ctypes.wintypes

        class _WindowsMemoryCounters(ctypes.Structure):
            _fields_ = [
                ("cb", ctypes.wintypes.DWORD),
                ("PageFaultCount", ctypes.wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        getCurrentProcess = kernel32.GetCurrentProcess
        getCurrentProcess.argtypes = []
        getCurrentProcess.restype = ctypes.wintypes.HANDLE
        getProcessMemoryInfo = psapi.GetProcessMemoryInfo
        getProcessMemoryInfo.argtypes = [
            ctypes.wintypes.HANDLE,
            ctypes.POINTER(_WindowsMemoryCounters),
            ctypes.wintypes.DWORD,
        ]
        getProcessMemoryInfo.restype = ctypes.wintypes.BOOL
    except (AttributeError, OSError, ImportError):
        return None
    return getCurrentProcess, getProcessMemoryInfo, _WindowsMemoryCounters


def _windowsCounters() -> Any | None:
    """Windows RSS counter를 읽고 지원·관측 실패는 None으로 표현한다."""
    global _winMemoryReader

    if sys.platform != "win32":
        return None
    with _winMemoryLock:
        if _winMemoryReader is None:
            _winMemoryReader = _buildWindowsMemoryReader() or _WINDOWS_READER_UNAVAILABLE
        reader = _winMemoryReader
    if reader is _WINDOWS_READER_UNAVAILABLE or not isinstance(reader, tuple):
        return None
    getCurrentProcess, getProcessMemoryInfo, counterType = reader
    try:
        counters = counterType()
        counters.cb = ctypes.sizeof(counterType)
        if getProcessMemoryInfo(getCurrentProcess(), ctypes.byref(counters), counters.cb):
            return counters
    except (ctypes.ArgumentError, OSError, ValueError):
        return None
    return None


def _procStatusKb(field: str) -> float:
    """Linux ``/proc/self/status`` 필드를 MB로 읽는다."""
    try:
        with open(f"/proc/{os.getpid()}/status") as handle:
            for line in handle:
                if line.startswith(field):
                    return int(line.split()[1]) / 1024
    except (OSError, ValueError, IndexError):
        return -1.0
    return -1.0


def getMemoryMb() -> float:
    """현재 프로세스 RSS를 MB로 반환한다.

    Capabilities:
        Windows working set과 Linux VmRSS를 같은 MB 단위로 투영한다.
    AIContext:
        cache pressure와 OOM 감시가 사용하는 현재 메모리 근거다.
    Guide:
        음수는 0MB가 아니라 현재 플랫폼에서 측정할 수 없다는 뜻이다.
    When:
        대형 DataFrame 작업 전후 또는 background OOM 감시에서 호출한다.
    How:
        Windows는 private psapi handle, Linux는 procfs를 직접 읽는다.
    Requires:
        Windows psapi 또는 Linux procfs 중 하나가 필요하다.
    Raises:
        없음. 지원·관측 실패는 -1.0으로 명시한다.
    Returns:
        현재 RSS MB. 측정할 수 없으면 -1.0.
    Example:
        >>> isinstance(getMemoryMb(), float)
        True
    SeeAlso:
        getPeakRssMb, checkMemoryAndGc
    """
    counters = _windowsCounters()
    if counters is not None:
        return counters.WorkingSetSize / (1024 * 1024)
    return _procStatusKb("VmRSS:")


def getPeakRssMb() -> float:
    """프로세스 수명 중 peak RSS를 MB로 반환한다.

    Capabilities:
        Windows PeakWorkingSetSize와 Linux VmHWM을 같은 단위로 투영한다.
    AIContext:
        성능 회귀에서 시점 RSS가 놓치는 최고 수위를 증거로 남긴다.
    Guide:
        음수는 peak가 0이라는 뜻이 아니라 측정 불가 상태다.
    When:
        대형 분석이나 실데이터 RSS gate가 끝난 뒤 호출한다.
    How:
        현재 RSS reader의 peak 필드 또는 procfs VmHWM을 읽는다.
    Requires:
        Windows psapi 또는 Linux procfs 중 하나가 필요하다.
    Raises:
        없음. 지원·관측 실패는 -1.0으로 명시한다.
    Returns:
        peak RSS MB. 측정할 수 없으면 -1.0.
    Example:
        >>> isinstance(getPeakRssMb(), float)
        True
    SeeAlso:
        getMemoryMb
    """
    counters = _windowsCounters()
    if counters is not None:
        return counters.PeakWorkingSetSize / (1024 * 1024)
    return _procStatusKb("VmHWM:")


def checkMemoryAndGc(label: str = "") -> float:
    """현재 RSS를 확인하고 critical 이상에서 Python GC를 실행한다.

    Capabilities:
        측정, pressure 로그, Python cyclic garbage 회수를 한 경로로 묶는다.
    AIContext:
        dataLoader와 panel read 전후의 OOM 방어 근거를 제공한다.
    Guide:
        Polars allocator가 보유한 native page를 강제 반환한다고 해석하지 않는다.
    When:
        대형 artifact를 열기 직전 또는 직후 호출한다.
    How:
        전역 pressure tier와 현재 RSS를 비교하고 critical 이상에서 gc.collect한다.
    Requires:
        getMemoryMb가 지원되는 OS에서만 pressure 판단이 가능하다.
    Raises:
        gc.collect에서 발생한 예외를 그대로 전달한다.
    Args:
        label: pressure 로그의 호출 지점 식별자.
    Returns:
        GC 후 다시 측정한 현재 RSS MB. 측정 불가면 음수.
    Example:
        >>> isinstance(checkMemoryAndGc("before-load"), float)
        True
    SeeAlso:
        cleanupBetweenCompanies, OomTripwire
    """
    mem = getMemoryMb()
    if mem <= 0:
        return mem
    if mem > PRESSURE_FATAL_MB:
        log.warning("[memory] FATAL %s: %.0fMB > %.0fMB — full GC", label, mem, PRESSURE_FATAL_MB)
        gc.collect()
        return getMemoryMb()
    if mem > PRESSURE_CRITICAL_MB:
        log.warning("[memory] CRITICAL %s: %.0fMB > %.0fMB — GC", label, mem, PRESSURE_CRITICAL_MB)
        gc.collect()
        return getMemoryMb()
    if mem > PRESSURE_WARNING_MB:
        log.debug("[memory] WARNING %s: %.0fMB > %.0fMB", label, mem, PRESSURE_WARNING_MB)
    return mem


def cleanupBetweenCompanies(label: str = "") -> tuple[float, float]:
    """회사 경계에서 Python 참조 순환을 회수하고 전후 RSS를 측정한다.

    Capabilities:
        호출 전후 RSS와 명시적 Python GC를 하나의 회사 경계 작업으로 제공한다.
    AIContext:
        다종목 loop가 각 Company cache를 clear한 뒤 남은 Python 참조를 회수한다.
    Guide:
        Polars 1.41의 string-cache API는 no-op이므로 native cache 회수로 과장하지 않는다.
    When:
        Company.cleanupCache 또는 다종목 CLI가 한 회사를 끝냈을 때 호출한다.
    How:
        현재 RSS 측정, gc.collect, 재측정과 구조화 로그 순서로 실행한다.
    Requires:
        호출자가 먼저 자신이 소유한 BoundedCache.clear를 실행해야 한다.
    Raises:
        gc.collect에서 발생한 예외를 그대로 전달한다.
    Args:
        label: 회사 코드나 분석 단계 등 로그 식별자.
    Returns:
        호출 전과 후의 RSS MB tuple. 측정할 수 없으면 해당 값은 음수다.
    Example:
        >>> before, after = cleanupBetweenCompanies("005930")
        >>> isinstance(before, float) and isinstance(after, float)
        True
    SeeAlso:
        BoundedCache.clear, checkMemoryAndGc
    """
    before = getMemoryMb()
    gc.collect()
    after = getMemoryMb()
    if before > 0 and after > 0:
        log.info(
            "[memory] cleanupBetweenCompanies %s: %.0f → %.0f MB (-%.0f)",
            label,
            before,
            after,
            before - after,
        )
    return before, after


__all__ = [
    "PRESSURE_CRITICAL_MB",
    "PRESSURE_EMERGENCY_MB",
    "PRESSURE_FATAL_MB",
    "PRESSURE_WARNING_MB",
    "checkMemoryAndGc",
    "cleanupBetweenCompanies",
    "getMemoryMb",
    "getPeakRssMb",
]
