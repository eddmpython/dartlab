"""프로세스 메모리 모니터링 + 메모리 압박 감지 LRU 캐시.

⚠ Polars는 네이티브 Rust 힙을 사용하므로 Python gc.collect()로 회수 불가.
   Company 1개 로드 ≈ 200~500MB, 3개 이상 동시 로드 시 OOM 위험.
   BoundedCache + check_memory_and_gc()로 방어.
"""

from __future__ import annotations

import ctypes
import functools
import gc
import logging
import os
import sys
import threading
import time
from collections import OrderedDict
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable)

log = logging.getLogger(__name__)

# psapi 호출 준비를 프로세스당 한 번만 하고 붙들어 둔다. None 은 아직 안 해봤다는 뜻이고,
# 준비에 실패하면 그 자리에 다시 None 이 아니라 실패를 담은 값이 들어가지 않으므로
# `_buildWindowsMemoryReader` 가 None 을 돌려준 경우는 매번 다시 시도한다. 그 편이 낫다.
# 실패는 보통 Windows 가 아닌 곳이고 그때는 `sys.platform` 검사에서 이미 걸린다.
_winMemoryLock = threading.Lock()
_winMemoryReader: tuple[Any, Any, Any] | None = None

# ── 메모리 임계값 (MB) ──
# Polars 네이티브 메모리 포함, 단일 프로세스 기준
# 2026-04-22 AI audit 관찰: 현대차·삼성전자급 대기업 + 14축 analysis 호출 시
# peak 13GB 까지 폭증 → EMERGENCY 에서만 pinned 비움. 더 일찍 개입해야 한다.
# 2026-05-12 M1: PRESSURE_FATAL=CRITICAL=1500 동치였던 dead-code 분기 정정.
# `_checkPressure` (L362-) 의 `if mem > FATAL: ... elif mem > CRITICAL:` 구조에서
# 임계가 동치면 CRITICAL elif 가 절대 도달 못함. FATAL 을 2000 으로 분리하여
# 4 단계 escalation 활성화:
# - WARNING 800: 캐시 절반 축소
# - CRITICAL 1500: 캐시 1/4 축소 + GC (conftest.PYTEST_MEMORY_LIMIT_MB 기본값)
# - FATAL 2000: pinned 제외 전부 비우기 + GC (BoundedCache 공격적 정리)
# - EMERGENCY 2500: pinned 까지 비우기 + polars string cache 회수
PRESSURE_WARNING_MB = 800.0
PRESSURE_CRITICAL_MB = 1500.0
PRESSURE_FATAL_MB = 2000.0
PRESSURE_EMERGENCY_MB = 2500.0

# ── lazy-build atomic sentinel ──
# `if key not in cache: cache[key] = build(...); return cache[key]` 패턴은 atomic 이
# 아니다 — set 단계의 ``__setitem__`` 가 ``_check_pressure`` 를 호출해 FATAL 분기
# (line 318-325) 에서 just_set_key 보존 없이 unpinned 전부 evict 시키면 직후 read 가
# KeyError. atomic 패턴은 ``cache.get(key, _CACHE_MISSING)`` 으로 한 번만 cache 접근
# + 결과는 로컬 var 에 저장 → cache 에서 evict 되어도 영향 없음.
_CACHE_MISSING: Any = object()


def _windowsCounters() -> Any | None:
    """Windows 프로세스 메모리 카운터를 한 번 읽어 온다. 못 읽으면 None.

    준비를 프로세스당 한 번만 하고 그 결과를 붙들어 둔다. 예전에는 이 함수 둘이 부를 때마다
    구조체 class 를 **함수 안에서 새로 만들고** 그것으로 psapi 함수의 `argtypes` 를 덮어썼다.
    `ctypes.windll` 이 프로세스 전역 캐시라 그 `argtypes` 는 process 안 모두가 공유한다.
    그래서 이런 일이 났다.

        스레드 A: argtypes 를 자기 구조체로 설정
        스레드 B: argtypes 를 자기 구조체로 설정   <- A 것을 덮어씀
        스레드 A: 자기 구조체 포인터로 호출        <- ArgumentError

    OomTripwire 가 배경 스레드로 RSS 를 폴링하고 BoundedCache 는 본 스레드에서 같은 값을
    읽으므로 두 스레드가 늘 함께 돈다. 실제로 `Company.story` 가 이 경쟁으로 죽었다.
    `ArgumentError` 는 `ValueError` 라서 아래의 `except` 목록에도 안 걸려 그대로 새어 나갔다.

    Returns:
        `WorkingSetSize` 와 `PeakWorkingSetSize` 를 가진 구조체. Windows 가 아니거나
        호출이 실패하면 None.
    """
    global _winMemoryReader

    if sys.platform != "win32":
        return None
    with _winMemoryLock:
        if _winMemoryReader is None:
            _winMemoryReader = _buildWindowsMemoryReader()
        reader = _winMemoryReader
    if reader is None:
        return None
    getCurrentProcess, getProcessMemoryInfo, counterType = reader
    try:
        counters = counterType()
        counters.cb = ctypes.sizeof(counterType)
        if getProcessMemoryInfo(getCurrentProcess(), ctypes.byref(counters), counters.cb):
            return counters
    except (OSError, ValueError):
        # ValueError 로 ctypes.ArgumentError 까지 받는다. 다른 라이브러리가 같은 psapi
        # 함수의 argtypes 를 건드리면 여기로 온다. 메모리 관측 실패가 호출자를 죽이면 안 된다.
        return None
    return None


def _buildWindowsMemoryReader() -> tuple[Any, Any, Any] | None:
    """psapi 호출 준비. 실패하면 None 을 돌려 이후 시도를 접는다."""
    try:
        import ctypes.wintypes

        class _WindowsMemoryCounters(ctypes.Structure):
            """psapi 의 PROCESS_MEMORY_COUNTERS. 필드 순서가 곧 ABI 다."""

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

        # `ctypes.windll` 대신 자기 handle 을 연다. 그쪽은 전역 캐시라 거기 붙은 함수의
        # argtypes 를 우리가 정하면 process 안 다른 코드까지 같이 끌려간다. 새 handle 은
        # 우리 것이라 남과 부딪히지 않는다.
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


def _procStatusKb(field: str) -> float:
    """Linux `/proc/self/status` 의 한 줄을 MB 로 읽는다. 없으면 -1.0."""
    try:
        with open(f"/proc/{os.getpid()}/status") as handle:
            for line in handle:
                if line.startswith(field):
                    return int(line.split()[1]) / 1024
    except (FileNotFoundError, PermissionError):
        pass
    return -1.0


def getMemoryMb() -> float:
    """현재 프로세스 RSS(Resident Set Size)를 MB로 반환.

    Polars Rust 힙을 포함한 실제 물리 메모리 사용량.
    psutil 없이 OS API 직접 사용.
    """
    counters = _windowsCounters()
    if counters is not None:
        return counters.WorkingSetSize / (1024 * 1024)
    return _procStatusKb("VmRSS:")


def getPeakRssMb() -> float:
    """프로세스 시작 이후 *peak* RSS (Windows PMC.PeakWorkingSetSize) 를 MB 로 반환.

    매직처닝하스 처방 효과 검증 — 시점 RSS (getMemoryMb) 가 peak 를 놓치는
    문제 해결. Windows 의 PMC.PeakWorkingSetSize 가 *프로세스 수명 동안 최대*
    working set. Linux 는 VmHWM (high water mark).

    Returns -1.0 — 측정 불가 시 (지원 안 되는 OS / API fail).
    """
    counters = _windowsCounters()
    if counters is not None:
        return counters.PeakWorkingSetSize / (1024 * 1024)
    # Linux 대체 경로. VmHWM 이 프로세스 수명 동안의 최고 수위다.
    return _procStatusKb("VmHWM:")


def _getTotalMemoryMb() -> float:
    """시스템 전체 물리 메모리(MB)."""
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]

        class MEMORYSTATUSEX(ctypes.Structure):
            """MEMORYSTATUSEX — TODO 한국어 클래스 설명."""

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


def checkMemoryAndGc(label: str = "") -> float:
    """현재 메모리 확인 + 위험 시 GC 강제 실행. RSS(MB) 반환.

    테스트/데이터 로드 전후에 호출하여 OOM 사전 방지.
    """
    mem = getMemoryMb()
    if mem <= 0:
        return mem
    if mem > PRESSURE_FATAL_MB:
        log.warning("[memory] FATAL %s: %.0fMB > %.0fMB — full GC", label, mem, PRESSURE_FATAL_MB)
        gc.collect()
        mem = getMemoryMb()
    elif mem > PRESSURE_CRITICAL_MB:
        log.warning("[memory] CRITICAL %s: %.0fMB > %.0fMB — GC", label, mem, PRESSURE_CRITICAL_MB)
        gc.collect()
        mem = getMemoryMb()
    elif mem > PRESSURE_WARNING_MB:
        log.debug("[memory] WARNING %s: %.0fMB > %.0fMB", label, mem, PRESSURE_WARNING_MB)
    return mem


def cleanupBetweenCompanies(label: str = "") -> tuple[float, float]:
    """회사 다중 분석 워크플로우에서 회사 경계마다 호출하여 누적 메모리 회수.

    BoundedCache EMERGENCY tier 의 정리 동작 (dataLoader 디스크 캐시 비우기 +
    Polars string cache 회수 + GC) 을 명시 호출 가능하게 노출.

    한 프로세스 안에서 회사 여러 개를 순차 분석할 때 회사 사이에 호출하면
    누적 dataLoader 캐시 / Polars string interning 풀이 회수된다.
    BoundedCache 자체는 EMERGENCY 임계 (기본 2500 MB) 가 자동 처리한다.

    Polars Rust 힙은 allocator (mimalloc) 가 retained pages 를 보유해
    이 함수만으로 RSS 가 즉시 감소하지는 않는다. 그러나 다음 할당이 보유
    arena 를 재사용하므로 무한 누적은 막힌다.

    Args:
        label: 로그 식별자 (예: 회사 종목코드 / 분석 단계).

    Returns:
        (before_mb, after_mb): 호출 전 / 후 RSS (MB). 측정 실패 시 -1.0.

    Example::

        from dartlab.core.memory import cleanupBetweenCompanies
        for code in ["005930", "000660", "035420"]:
            company = Company(code)
            analyze(company)
            cleanupBetweenCompanies(label=code)
    """
    before = getMemoryMb()
    try:
        from dartlab.core.dataLoader import _clearLoadCache

        _clearLoadCache()
    except (ImportError, AttributeError):
        pass
    try:
        import polars as pl

        pl.disable_string_cache()
    except (ImportError, AttributeError):
        pass
    gc.collect()
    after = getMemoryMb()
    if before > 0 and after > 0:
        log.info(
            "[memory] cleanupBetweenCompanies %s: %.0f → %.0f MB (-%.0f)",
            label or "",
            before,
            after,
            before - after,
        )
    return before, after


class BoundedCache:
    """메모리 압박 감지 LRU 캐시 (thread-safe + pinned 키 보호).

    dict와 동일한 인터페이스(`in`, `[]`, `[]=`)를 제공하되,
    max_entries 초과 시 가장 오래된 항목을 제거하고
    주기적으로 프로세스 RSS를 체크하여 메모리 압박 시 용량을 축소한다.

    [thread-safety] threading.RLock으로 모든 mutation 보호.
    story/buildBlocks의 ThreadPoolExecutor 병렬 호출 안전.

    [pinned] 외부 API 결과(_quant_ohlcv, _quant_benchmark 등)는 evict 면제.
    작은 dict이고 재로드 비용이 크므로 메모리 압박 시에도 보존.

    ⚠ pressure_mb 기본값 800MB — Polars Company 2개 수준에서 이미 경고.
    """

    __slots__ = (
        "_store",
        "_max",
        "_default_max",
        "_pressure_mb",
        "_put_count",
        "_lock",
        "_pinned_prefixes",
        "_critical_prefixes",
        "_emergency_at",
        "_ipc_cache_dir",
        "_ipc_backed_prefixes",
    )

    def __init__(self, maxEntries: int = 30, pressureMb: float = 800.0):
        import tempfile
        import threading

        self._store: OrderedDict[str, Any] = OrderedDict()
        self._max = maxEntries
        self._default_max = maxEntries
        self._pressure_mb = pressureMb
        self._put_count = 0
        self._lock = threading.RLock()
        self._emergency_at = 0.0  # EMERGENCY 발생 시각 — cool-down 용
        # Phase C — IPC mmap backing. _sections 같은 무거운 DataFrame 결과를 IPC 파일로
        # 자동 저장. EMERGENCY clear 시에도 IPC 잔존 → 다음 호출 시 mmap reload (수 ms).
        # 인스턴스별 tmpdir — Company 다중 인스턴스 간 key 충돌 회피.
        from pathlib import Path

        self._ipc_cache_dir: Path = Path(tempfile.mkdtemp(prefix="dartlab-cache-"))
        self._ipc_backed_prefixes: tuple[str, ...] = ("_sections",)
        # critical: EMERGENCY에서도 절대 비우면 안 되는 키 (재생성 로직 없음 → KeyError).
        # 다른 pinned는 재로드 비용 크지만 가능. critical은 비우면 후속 호출 즉시 실패.
        # _pinned_prefixes 의 "Accessor" 그룹과 동기화 — pinned 의 첫 5 entries.
        self._critical_prefixes: tuple[str, ...] = (
            "_showAccessor",
            "_selectAccessor",
            "_storyAccessor",
            "_creditAccessor",
            "_analysisAccessor",
            # 2026-04-20: realdata-suite 에서 `c.quant` / `c.topics` KeyError 검출.
            # 동일한 CallableAccessor 패턴인데 critical_prefixes 에서 누락됐었음.
            "_quantAccessor",
            "_sectionsAnalyzer",
            # 2026-04-27: R9 인텔 audit 에서 `_docs_sections` KeyError 검출.
            # `_DocsAccessor.sections` (EDGAR) 의 lazy build 가 FATAL/EMERGENCY clear 와
            # race — pinned 도 critical 도 아니라 unpinned evict 에 휩쓸려 line `return
            # cache[key]` 가 KeyError. _docs prefix 는 _docs_sections · _docs_retrievalBlocks
            # · _docs_contextSlices · _docs_freq · _docs_coverage 공통 부모.
            "_docs",
            # _sections (DART) 도 동일 — _showDispatch 가 의존, evict 시 KeyError.
            "_sections",
        )
        # pinned: 이 prefix로 시작하는 키는 evict하지 않음 (외부 API + 무거운 계산 결과 보호)
        # review에서 여러 calc가 공유하는 핵심 캐시. 작은 dict이고 재로드 비용 큼.
        self._pinned_prefixes: tuple[str, ...] = (
            # Accessor (dualAccess wrapper — 재생성 로직이 없음, 반드시 보호) = critical
            # Phase 4 G11: 대형 기업 (한국전력 등) 에서 메모리 압박 시
            # _check_pressure() 가 accessor 까지 삭제 → 다음 select/show 에서 KeyError
            *self._critical_prefixes,
            # 외부 API / 데이터 로드
            "_quant_ohlcv",
            "_quant_benchmark",
            "_priceContext",
            "_diffResult",
            "_peerRanking",
            "_estimateWacc",
            "_estimateWacc_v2",
            "_fetchBeta",
            # finance series builders — 매우 무거운 parquet load + pivot
            # evict 시 14축 calc 가 매번 finance 를 다시 빌드해서 메모리 폭발.
            # Phase B 의 DuckDB pivot 으로 rebuild 비용 ~50% 감소, Phase D 의 IPC mmap
            # 으로 parquet 디코드 ~0 — 그래도 builder 자체 cost 보존 위해 pinned 유지.
            "_finance_",
            "_financeStmt_",
            "_financeCisQuarterly",
            "_sceDataFrame",
            "_ratios_",
            "_insights_analyze",
            # Phase D-2 — calc* 결과 13 prefix 제거.
            # 작은 dict / scalar / 짧은 list 결과 (재계산 비용 ≤ 50ms, finance pinned 가 있으면
            # rebuild thrashing 없음). pinned 유지 시 memory 압박 시에도 EMERGENCY 회수 안 됨.
            # 제거된 prefix: _calcMarketBeta · _calcTechnicalVerdict · _calcTechnicalSignals ·
            # _calcMarketRisk · _calcMarketAnalysisFlags · _calcFundamentalDivergence ·
            # _calcRoicTimeline · _calcCreditMetrics · _calcCreditScore · _calcScorecard ·
            # _calcPeerRanking · _calcDisclosureChangeSummary · _calcKeyTopicChanges.
        )

    def _isPinned(self, key: str) -> bool:
        return any(key.startswith(p) for p in self._pinned_prefixes)

    def _ipcBacked(self, key: str) -> bool:
        return any(key.startswith(p) for p in self._ipc_backed_prefixes)

    def _ipcPath(self, key: str):
        from pathlib import Path

        # key 가 underscore/alphanumeric 만 가정 — dartlab cache key 규약.
        safe = "".join(ch if ch.isalnum() or ch in "_-" else "_" for ch in key)
        return self._ipc_cache_dir / f"{safe}.arrow"

    def __contains__(self, key: str) -> bool:
        with self._lock:
            if key in self._store:
                return True
            if self._ipcBacked(key):
                return self._ipcPath(key).exists()
            return False

    def __getitem__(self, key: str) -> Any:
        with self._lock:
            if key in self._store:
                self._store.move_to_end(key)
                return self._store[key]
            # Phase C — IPC mmap reload (EMERGENCY clear 또는 evict 후).
            if self._ipcBacked(key):
                ipcPath = self._ipcPath(key)
                if ipcPath.exists():
                    try:
                        import polars as pl

                        df = pl.read_ipc(str(ipcPath), memory_map=True)
                        self._store[key] = df
                        return df
                    except (OSError, ImportError):
                        pass
            raise KeyError(key)

    def __setitem__(self, key: str, value: Any) -> None:
        with self._lock:
            # Phase C — IPC backing. _sections 류 + DataFrame 값 자동 저장 (caller 0 변경).
            # evict 시에도 디스크에 남아 다음 호출 mmap reload — thrashing 0.
            if self._ipcBacked(key):
                try:
                    import polars as pl

                    if isinstance(value, pl.DataFrame):
                        value.write_ipc(str(self._ipcPath(key)), compression="zstd")
                except (OSError, ImportError):
                    pass  # IPC 저장 실패 — heap 캐시만 유지 (fallback)

            if key in self._store:
                self._store.move_to_end(key)
                self._store[key] = value
                return
            self._store[key] = value
            self._put_count += 1
            # 매 put마다 압박 체크 — get_memory_mb는 ~µs 수준의 OS API라 overhead 무시 가능.
            # 이전 5번에 1번 체크는 burst write 중 8GB까지 폭증하는 케이스 못 잡음.
            # just_set_key 전달 — EMERGENCY 시 방금 넣은 key 가 clear 되어 직후 read 가 KeyError 나는 race 방지.
            self._checkPressure(justSetKey=key)
            # LRU evict — pinned 키는 건너뜀
            while len(self._store) > self._max:
                # 가장 오래된 unpinned 키 찾기
                evicted = False
                for k in list(self._store.keys()):
                    if not self._isPinned(k):
                        del self._store[k]
                        evicted = True
                        break
                if not evicted:
                    break  # 모두 pinned면 그냥 초과 허용

    def __len__(self) -> int:
        with self._lock:
            return len(self._store)

    def _checkPressure(self, justSetKey: str | None = None) -> None:
        # caller already holds _lock (called from __setitem__)
        mem = getMemoryMb()
        if mem <= 0:
            return
        if mem > PRESSURE_EMERGENCY_MB:
            # 응급: critical accessor + 방금 set 한 키만 보존하고 나머지 전부 비움.
            # 직전 EMERGENCY 후 1초 이내면 skip (반복 호출 방지 — gc 가 회수할 시간 필요).
            # 5초는 너무 길어 burst write 중 9GB 까지 폭증. 1초로 단축.
            now = time.monotonic()
            if now - self._emergency_at < 1.0:
                return
            self._emergency_at = now
            log.warning(
                "[BoundedCache] EMERGENCY: %.0fMB — clearing all except critical accessors + polars cache",
                mem,
            )
            for k in list(self._store.keys()):
                if k == justSetKey:
                    continue  # 방금 set 한 키는 보존 — 직후 read race 방지
                if not any(k.startswith(p) for p in self._critical_prefixes):
                    del self._store[k]
            self._max = max(self._default_max // 8, 1)
            try:
                from dartlab.core.dataLoader import _clearLoadCache

                _clearLoadCache()
            except (ImportError, AttributeError):
                pass
            try:
                import polars as pl

                pl.disable_string_cache()
            except (ImportError, AttributeError):
                pass
            gc.collect()
            return
        if mem > PRESSURE_FATAL_MB:
            # 치명: pinned 제외 모두 비우기
            log.warning("[BoundedCache] FATAL: %.0fMB — clearing unpinned entries", mem)
            for k in list(self._store.keys()):
                if not self._isPinned(k):
                    del self._store[k]
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
        # caller already holds _lock — pinned 키 건너뜀
        while len(self._store) > self._max:
            evicted = False
            for k in list(self._store.keys()):
                if not self._isPinned(k):
                    del self._store[k]
                    evicted = True
                    break
            if not evicted:
                break  # 모두 pinned면 초과 허용

    def keys(self) -> list[str]:
        """keys — TODO 한국어 동작 설명."""
        with self._lock:
            return list(self._store.keys())

    def pop(self, key: str, *args: Any) -> Any:
        """pop — TODO 한국어 동작 설명."""
        with self._lock:
            return self._store.pop(key, *args)

    def clear(self) -> None:
        """clear — TODO 한국어 동작 설명."""
        with self._lock:
            self._store.clear()
            self._max = self._default_max
            self._put_count = 0

    def get(self, key: str, default: Any = None) -> Any:
        """get — TODO 한국어 동작 설명."""
        with self._lock:
            if key in self._store:
                self._store.move_to_end(key)
                return self._store[key]
            return default

    def __del__(self) -> None:
        try:
            self._store.clear()
        except (AttributeError, TypeError):
            pass


def memoryGuard(thresholdPct: float = 60) -> Callable[[F], F]:
    """메모리 사용률이 threshold_pct 초과 시 GC 강제 실행하는 데코레이터.

    Usage::

        @memory_guard(threshold_pct=60)
        def heavy_computation():
            ...
    """
    total = _getTotalMemoryMb()

    def decorator(fn: F) -> F:
        """decorator — TODO 한국어 동작 설명."""

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            """wrapper — TODO 한국어 동작 설명."""
            if total > 0:
                current = getMemoryMb()
                if current > 0 and (current / total * 100) > thresholdPct:
                    gc.collect()
            return fn(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator


# ── calc 함수 메모이제이션 ──


def memoizedCalc(fn: Callable[..., Any]) -> Callable[..., Any]:
    """calc 함수 결과를 Company._cache에 메모이제이션.

    analysis/credit/quant의 calc 함수가 공통으로 사용.
    key: ``_{함수명}:{basePeriod}``
    Company._cache(BoundedCache)가 없으면 캐시 없이 실행.
    결과가 None이면 캐시하지 않는다.

    overrides 가 전달되면 **캐시 skip** + override 그대로 통과 — 같은 가정
    재실행 시 캐시가 오래된 값을 돌려주는 사고 방지.
    """
    import inspect

    params = inspect.signature(fn).parameters
    _has_base_period = "basePeriod" in params
    _has_overrides = "overrides" in params

    @functools.wraps(fn)
    def wrapper(
        company: Any,
        *,
        basePeriod: str | None = None,
        overrides: dict | None = None,
    ) -> Any:
        """wrapper — TODO 한국어 동작 설명."""
        kw: dict[str, Any] = {}
        if _has_base_period:
            kw["basePeriod"] = basePeriod
        if _has_overrides and overrides:
            kw["overrides"] = overrides

        # override 적용 시 캐시 우회 (값이 달라지므로)
        useCache = not overrides
        cache = getattr(company, "_cache", None) if useCache else None
        key = f"_{fn.__name__}:{basePeriod}"

        if cache is not None and key in cache:
            return cache[key]

        result = fn(company, **kw)

        if cache is not None and result is not None:
            cache[key] = result

        return result

    return wrapper


# ── M4: 함수 단위 메모리 예산 가드 ──


class MemoryBudgetExceeded(RuntimeError):
    """함수 단위 RSS delta 예산 초과 — M4.

    Polars Rust heap 누수 등 ``gc.collect()`` 로 회수 안 되는 메모리 폭증을
    함수 진입/이탈 RSS delta 로 감지. 호출자가 ``try/except`` 로 잡아
    fallback 또는 명확한 오류 메시지로 변환 가능.
    """


def withMemoryBudget(limitMb: int, *, sampler: Callable[[], float] | None = None) -> Callable[[F], F]:
    """함수 진입/이탈 RSS delta 가 ``limitMb`` 초과 시 ``MemoryBudgetExceeded`` raise.

    ``sampler`` 는 ``() -> RSS_in_MB`` 콜러블. 기본 ``getMemoryMb`` — 테스트 시
    fake sampler 주입으로 결정론적 검증 (정공법 B Protocol DIP).

    Args:
        limitMb: 진입-이탈 delta 한계 (MB).
        sampler: RSS 측정 함수 (테스트 주입용).

    Returns:
        데코레이터.

    Raises:
        없음 (raise 는 데코레이션 받은 함수의 wrapper 안에서).

    Example:
        >>> @withMemoryBudget(500)
        ... def buildHeavy() -> dict:
        ...     return load_lots_of_data()
    """
    sample = sampler if sampler is not None else getMemoryMb

    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            before = sample()
            result = fn(*args, **kwargs)
            after = sample()
            delta = after - before
            if delta > limitMb:
                raise MemoryBudgetExceeded(
                    f"{fn.__qualname__}: RSS delta {delta:.0f}MB > budget {limitMb}MB "
                    f"(before={before:.0f}MB after={after:.0f}MB)"
                )
            return result

        return wrapper  # type: ignore[return-value]

    return decorator


# ── M5: OomTripwire — background watcher + 응급 정지 ──


class OomTripwire:
    """RSS 가 임계 (기본 EMERGENCY=2500MB) 초과 시 kernel OOM-kill 전에
    Python 측에서 graceful 종료 — stack trace 덤프 + ``os._exit(137)``.

    Company ``__enter__`` 에서 자동 ``start()``, ``__exit__`` 에서 ``stop()``
    (정공법 C — Company 가 Tripwire 호출, Tripwire 는 Company 모름).

    Args:
        thresholdMb: 발화 임계 (기본 ``PRESSURE_EMERGENCY_MB`` = 2500).
        intervalSec: 폴링 간격 (기본 0.5 초).
        sampler: RSS 측정 함수 (기본 ``getMemoryMb``, 테스트 fake 주입용).
        exiter: 발화 시 호출 (기본 ``os._exit(137)``, 테스트 fake 주입용).

    Example:
        >>> tw = OomTripwire()
        >>> tw.start()
        >>> # ... heavy work
        >>> tw.stop()
    """

    def __init__(
        self,
        *,
        thresholdMb: float = PRESSURE_EMERGENCY_MB,
        intervalSec: float = 0.5,
        sampler: Callable[[], float] | None = None,
        exiter: Callable[[float], None] | None = None,
    ) -> None:
        import threading

        self._thresholdMb = thresholdMb
        self._intervalSec = intervalSec
        self._sampler = sampler if sampler is not None else getMemoryMb
        self._exiter = exiter if exiter is not None else self._defaultExiter
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    @staticmethod
    def _defaultExiter(rss: float) -> None:
        import os
        import sys
        import traceback

        sys.stderr.write(f"\n[OomTripwire] RSS {rss:.0f}MB > EMERGENCY threshold — graceful exit (137).\n")
        traceback.print_stack(file=sys.stderr)
        os._exit(137)

    def start(self) -> None:
        """daemon thread 시작."""
        import threading

        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="OomTripwire")
        self._thread.start()

    def stop(self, *, timeout: float = 2.0) -> None:
        """thread 정지 신호 + join."""
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)
            self._thread = None

    def _loop(self) -> None:
        while not self._stop.is_set():
            rss = self._sampler()
            if rss > self._thresholdMb:
                self._exiter(rss)
                return
            self._stop.wait(self._intervalSec)


# ── T3-4 — profileCall decorator ──


def profileCall(label: str, *, logEventFn: Callable[..., None] | None = None) -> Callable[[F], F]:
    """함수 호출의 *진입/이탈 RSS + 시간* 자동 측정 + logEvent 발급.

    T1-1 logEvent (구조화 로그) 와 통합. 6 facade API (Company.panel / scan.* /
    Story.compose / ask / EngineCall / MCP tool) 에 부착 → metrics workflow
    (T1-2) 가 grep 으로 P50/P95 latency + memory peak 추출.

    Args:
        label: event 식별자 (snake_case 권장, 예: "company_show", "scan_foreign_flow").
        logEventFn: 주입 가능한 이벤트 발급 함수. None 이면 core.logger.logEvent
            를 lazy import (순환 import 회피).

    Returns:
        데코레이터.

    Example:
        >>> from dartlab.core.memory import profileCall
        >>> @profileCall("company_show")
        ... def show(self, topic): ...

    Guide:
        본 decorator 는 *측정 only* — 임계값 초과 시 raise 하지 않는다. 그건
        ``withMemoryBudget`` 의 역할. 본 decorator 는 metrics 수집 진입점.

    SeeAlso:
        core.logger.logEvent — 구조화 이벤트 (T1-1)
        withMemoryBudget — 임계값 초과 raise (M4)

    Requires:
        ``time.monotonic`` + ``getMemoryMb``.

    AIContext:
        Observability KPI (T1) + 성능 KPI (T3-4) 의 단일 진입점. logEvent fields
        에 ``elapsed_ms`` / ``rss_delta_mb`` / ``rss_peak_mb`` 포함.
    """

    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # lazy import — 순환 import 회피 (logger → memory 호출 가능성)
            emit = logEventFn
            if emit is None:
                try:
                    from dartlab.core.logger import logEvent as _le  # noqa: PLC0415

                    emit = _le
                except ImportError:
                    emit = lambda *a, **kw: None  # type: ignore[assignment]  # noqa: E731

            rssBefore = getMemoryMb()
            tStart = time.monotonic()
            try:
                return fn(*args, **kwargs)
            finally:
                rssAfter = getMemoryMb()
                elapsedMs = round((time.monotonic() - tStart) * 1000, 2)
                rssDelta = round(rssAfter - rssBefore, 2)
                emit(
                    "info",
                    label,
                    elapsed_ms=elapsedMs,
                    rss_before_mb=round(rssBefore, 2),
                    rss_after_mb=round(rssAfter, 2),
                    rss_delta_mb=rssDelta,
                )

        return wrapper  # type: ignore[return-value]

    return decorator
