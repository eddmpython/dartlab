"""Universe 성능 receipt에 결박할 process와 host 환경 측정."""

from __future__ import annotations

import os
import platform
from typing import Final

_UNKNOWN: Final = "UNKNOWN"


def _windowsMemory() -> tuple[int | None, int | None]:
    """Windows total physical memory와 현재 process peak working set을 읽는다."""
    try:
        import ctypes
        from ctypes import wintypes

        class MemoryStatusEx(ctypes.Structure):
            _fields_ = (
                ("length", wintypes.DWORD),
                ("memoryLoad", wintypes.DWORD),
                ("totalPhysical", ctypes.c_ulonglong),
                ("availablePhysical", ctypes.c_ulonglong),
                ("totalPageFile", ctypes.c_ulonglong),
                ("availablePageFile", ctypes.c_ulonglong),
                ("totalVirtual", ctypes.c_ulonglong),
                ("availableVirtual", ctypes.c_ulonglong),
                ("availableExtendedVirtual", ctypes.c_ulonglong),
            )

        class ProcessMemoryCounters(ctypes.Structure):
            _fields_ = (
                ("cb", wintypes.DWORD),
                ("pageFaultCount", wintypes.DWORD),
                ("peakWorkingSetSize", ctypes.c_size_t),
                ("workingSetSize", ctypes.c_size_t),
                ("quotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("quotaPagedPoolUsage", ctypes.c_size_t),
                ("quotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("quotaNonPagedPoolUsage", ctypes.c_size_t),
                ("pagefileUsage", ctypes.c_size_t),
                ("peakPagefileUsage", ctypes.c_size_t),
            )

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        kernel32.GlobalMemoryStatusEx.argtypes = (ctypes.POINTER(MemoryStatusEx),)
        kernel32.GlobalMemoryStatusEx.restype = wintypes.BOOL
        kernel32.GetCurrentProcess.argtypes = ()
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        psapi.GetProcessMemoryInfo.argtypes = (
            wintypes.HANDLE,
            ctypes.POINTER(ProcessMemoryCounters),
            wintypes.DWORD,
        )
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        memory = MemoryStatusEx()
        memory.length = ctypes.sizeof(memory)
        totalPhysical = int(memory.totalPhysical) if kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)) else None
        counters = ProcessMemoryCounters()
        counters.cb = ctypes.sizeof(counters)
        process = kernel32.GetCurrentProcess()
        peak = (
            int(counters.peakWorkingSetSize)
            if psapi.GetProcessMemoryInfo(process, ctypes.byref(counters), counters.cb)
            else None
        )
        return totalPhysical, peak
    except (AttributeError, OSError, TypeError, ValueError):
        return None, None


def _posixMemory() -> tuple[int | None, int | None]:
    """POSIX total physical memory와 ru_maxrss를 byte로 정규화한다."""
    total = None
    peak = None
    try:
        pageSize = int(os.sysconf("SC_PAGE_SIZE"))
        pageCount = int(os.sysconf("SC_PHYS_PAGES"))
        total = pageSize * pageCount
    except (AttributeError, OSError, TypeError, ValueError):
        pass
    try:
        import resource

        rawPeak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        peak = rawPeak if platform.system() == "Darwin" else rawPeak * 1024
    except (ImportError, OSError, TypeError, ValueError):
        pass
    return total, peak


def memoryEnvironment() -> tuple[int | None, int | None]:
    """Host total memory와 현재 process peak RSS 계열 값을 반환한다."""
    return _windowsMemory() if os.name == "nt" else _posixMemory()


def runtimeEnvironment(
    *,
    cacheProfile: str,
    networkProfile: str,
) -> tuple[tuple[str, str], ...]:
    """성능 숫자를 해석하는 데 필요한 host와 실행 profile을 결정론 정렬한다."""
    totalMemory, _peak = memoryEnvironment()
    processor = platform.processor() or os.getenv("PROCESSOR_IDENTIFIER") or _UNKNOWN
    values = {
        "cacheProfile": cacheProfile,
        "logicalCpuCount": str(os.cpu_count() or _UNKNOWN),
        "machine": platform.machine() or _UNKNOWN,
        "networkProfile": networkProfile,
        "platform": platform.platform(),
        "processor": processor,
        "python": platform.python_version(),
        "totalPhysicalMemoryBytes": str(totalMemory) if totalMemory is not None else _UNKNOWN,
    }
    return tuple(sorted(values.items()))
