"""프로세스 메모리 모니터링 + 메모리 압박 감지 LRU 캐시.

⚠ Polars는 네이티브 Rust 힙을 사용하므로 Python gc.collect()로 회수 불가.
   Company 1개 로드 ≈ 200~500MB, 3개 이상 동시 로드 시 OOM 위험.
   BoundedCache + check_memory_and_gc()로 방어.
"""

from __future__ import annotations

import functools
import gc
import logging
import os
from collections import OrderedDict
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable)

log = logging.getLogger(__name__)

# ── 메모리 임계값 (MB) ──
# Polars 네이티브 메모리 포함, 단일 프로세스 기준
PRESSURE_WARNING_MB = 800.0  # 경고: 캐시 절반 축소
PRESSURE_CRITICAL_MB = 1200.0  # 위험: 캐시 1/4 축소 + GC
PRESSURE_FATAL_MB = 1600.0  # 치명: 캐시 전체 비우기 + GC


def get_memory_mb() -> float:
    """현재 프로세스 RSS(Resident Set Size)를 MB로 반환.

    Polars Rust 힙을 포함한 실제 물리 메모리 사용량.
    psutil 없이 OS API 직접 사용.
    """
    try:
        import ctypes
        import ctypes.wintypes

        class PMC(ctypes.Structure):
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

        GetCurrentProcess = ctypes.windll.kernel32.GetCurrentProcess  # type: ignore[attr-defined]
        GetCurrentProcess.restype = ctypes.wintypes.HANDLE

        GetProcessMemoryInfo = ctypes.windll.psapi.GetProcessMemoryInfo  # type: ignore[attr-defined]
        GetProcessMemoryInfo.argtypes = [
            ctypes.wintypes.HANDLE,
            ctypes.POINTER(PMC),
            ctypes.wintypes.DWORD,
        ]
        GetProcessMemoryInfo.restype = ctypes.wintypes.BOOL

        pmc = PMC()
        pmc.cb = ctypes.sizeof(PMC)
        if GetProcessMemoryInfo(GetCurrentProcess(), ctypes.byref(pmc), pmc.cb):
            return pmc.WorkingSetSize / (1024 * 1024)
    except (AttributeError, OSError, ImportError):
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


def check_memory_and_gc(label: str = "") -> float:
    """현재 메모리 확인 + 위험 시 GC 강제 실행. RSS(MB) 반환.

    테스트/데이터 로드 전후에 호출하여 OOM 사전 방지.
    """
    mem = get_memory_mb()
    if mem <= 0:
        return mem
    if mem > PRESSURE_FATAL_MB:
        log.warning("[memory] FATAL %s: %.0fMB > %.0fMB — full GC", label, mem, PRESSURE_FATAL_MB)
        gc.collect()
        mem = get_memory_mb()
    elif mem > PRESSURE_CRITICAL_MB:
        log.warning("[memory] CRITICAL %s: %.0fMB > %.0fMB — GC", label, mem, PRESSURE_CRITICAL_MB)
        gc.collect()
        mem = get_memory_mb()
    elif mem > PRESSURE_WARNING_MB:
        log.debug("[memory] WARNING %s: %.0fMB > %.0fMB", label, mem, PRESSURE_WARNING_MB)
    return mem


class BoundedCache:
    """메모리 압박 감지 LRU 캐시.

    dict와 동일한 인터페이스(`in`, `[]`, `[]=`)를 제공하되,
    max_entries 초과 시 가장 오래된 항목을 제거하고
    주기적으로 프로세스 RSS를 체크하여 메모리 압박 시 용량을 축소한다.

    ⚠ pressure_mb 기본값 800MB — Polars Company 2개 수준에서 이미 경고.
    """

    __slots__ = ("_store", "_max", "_default_max", "_pressure_mb", "_put_count")

    def __init__(self, max_entries: int = 30, pressure_mb: float = 800.0):
        self._store: OrderedDict[str, Any] = OrderedDict()
        self._max = max_entries
        self._default_max = max_entries
        self._pressure_mb = pressure_mb
        self._put_count = 0

    def __contains__(self, key: str) -> bool:
        return key in self._store

    def __getitem__(self, key: str) -> Any:
        self._store.move_to_end(key)
        return self._store[key]

    def __setitem__(self, key: str, value: Any) -> None:
        if key in self._store:
            self._store.move_to_end(key)
            self._store[key] = value
            return
        self._store[key] = value
        self._put_count += 1
        if self._put_count % 5 == 0:
            self._check_pressure()
        while len(self._store) > self._max:
            self._store.popitem(last=False)

    def __len__(self) -> int:
        return len(self._store)

    def _check_pressure(self) -> None:
        mem = get_memory_mb()
        if mem <= 0:
            return
        if mem > PRESSURE_FATAL_MB:
            # 치명: 캐시 전체 비우기
            log.warning("[BoundedCache] FATAL: %.0fMB — clearing all entries", mem)
            self._store.clear()
            self._max = max(self._default_max // 4, 2)
            gc.collect()
        elif mem > PRESSURE_CRITICAL_MB:
            self._max = max(self._default_max // 4, 5)
            self._evict()
            gc.collect()
        elif mem > PRESSURE_WARNING_MB:
            self._max = max(self._default_max // 2, 10)
            self._evict()
        else:
            self._max = self._default_max

    def _evict(self) -> None:
        while len(self._store) > self._max:
            self._store.popitem(last=False)

    def clear(self) -> None:
        self._store.clear()
        self._max = self._default_max
        self._put_count = 0

    def get(self, key: str, default: Any = None) -> Any:
        if key in self._store:
            self._store.move_to_end(key)
            return self._store[key]
        return default

    def __del__(self) -> None:
        self._store.clear()


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
