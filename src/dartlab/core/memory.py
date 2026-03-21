"""프로세스 메모리 모니터링 — Polars 네이티브 메모리 포함."""

from __future__ import annotations

import functools
import gc
import os
from typing import TypeVar, Callable

F = TypeVar("F", bound=Callable)


def get_memory_mb() -> float:
    """현재 프로세스 RSS(Resident Set Size)를 MB로 반환.

    Polars Rust 힙을 포함한 실제 물리 메모리 사용량.
    psutil 없이 OS API 직접 사용.
    """
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        # PROCESS_MEMORY_COUNTERS_EX
        class PMC(ctypes.Structure):
            _fields_ = [
                ("cb", ctypes.c_uint32),
                ("PageFaultCount", ctypes.c_uint32),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        psapi = ctypes.windll.psapi  # type: ignore[attr-defined]
        pmc = PMC()
        pmc.cb = ctypes.sizeof(PMC)
        handle = kernel32.GetCurrentProcess()
        if psapi.GetProcessMemoryInfo(handle, ctypes.byref(pmc), pmc.cb):
            return pmc.WorkingSetSize / (1024 * 1024)
    except (AttributeError, OSError):
        pass

    # Linux/macOS fallback
    try:
        with open(f"/proc/{os.getpid()}/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) / 1024  # kB → MB
    except (FileNotFoundError, PermissionError):
        pass

    return -1.0


def _get_total_memory_mb() -> float:
    """시스템 전체 물리 메모리(MB)."""
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]

        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_uint32),
                ("dwMemoryLoad", ctypes.c_uint32),
                ("ullTotalPhys", ctypes.c_uint64),
                ("ullAvailPhys", ctypes.c_uint64),
                ("ullTotalPageFile", ctypes.c_uint64),
                ("ullAvailPageFile", ctypes.c_uint64),
                ("ullTotalVirtual", ctypes.c_uint64),
                ("ullAvailVirtual", ctypes.c_uint64),
                ("ullAvailExtendedVirtual", ctypes.c_uint64),
            ]

        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        return stat.ullTotalPhys / (1024 * 1024)
    except (AttributeError, OSError):
        pass

    # Linux fallback
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    return int(line.split()[1]) / 1024
    except (FileNotFoundError, PermissionError):
        pass

    return -1.0


def memory_guard(threshold_pct: float = 60) -> Callable[[F], F]:
    """메모리 사용률이 threshold_pct 초과 시 GC 강제 실행하는 데코레이터.

    Usage::

        @memory_guard(threshold_pct=60)
        def heavy_computation():
            ...
    """
    total = _get_total_memory_mb()

    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            if total > 0:
                current = get_memory_mb()
                if current > 0 and (current / total * 100) > threshold_pct:
                    gc.collect()
            return fn(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator
