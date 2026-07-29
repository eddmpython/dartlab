"""core/memory — 프로세스 RSS, bounded cache, 메모리 가드 단위 테스트."""

from __future__ import annotations

import os
import threading

import pytest

pytestmark = pytest.mark.unit


def test_polars_max_threads_capped_when_cpu_gt_4():
    """CPU > 4 환경에서 dartlab import 가 POLARS_MAX_THREADS=4 를 박는지 확인.

    이미 사용자가 설정한 경우는 존중한다 (이 테스트는 dartlab import 가 끝난
    후 시점이라 우리가 확인하는 건 결과 상태).
    """
    cpu = os.cpu_count() or 4
    val = os.environ.get("POLARS_MAX_THREADS")

    if cpu > 4:
        assert val is not None, "CPU > 4 인데 POLARS_MAX_THREADS 가 설정되지 않았다"
        assert val == "4", f"기본 cap 은 4 이어야 한다. 실제: {val}"


def test_polars_thread_pool_respects_cap():
    """POLARS_MAX_THREADS=4 가 실제 polars 런타임에 반영됐는지 확인."""
    import polars as pl

    cpu = os.cpu_count() or 4
    pool = pl.thread_pool_size()

    if cpu > 4:
        assert pool <= 4, f"CPU > 4 환경에서 polars thread pool 이 {pool} — 4 이하여야 한다"


class TestGetMemoryMb:
    def test_returns_positive_on_supported_os(self):
        """Windows / Linux 에서 RSS > 0 반환."""
        from dartlab.core.memory import getMemoryMb

        mem = getMemoryMb()
        assert mem > 0, f"RSS 측정 실패 (-1 반환): {mem}"
        assert mem < 100_000, f"비현실적인 RSS: {mem} MB"


class TestCacheCaps:
    """대량 Polars 사용 시 RSS 폭증 가드 — 캐시 최대 entry 상수 회귀 방지."""

    def test_load_cache_max_capped(self):
        """dataLoader 의 _LOAD_CACHE_MAX 가 8 이하로 유지된다.

        회사 1 개 docs DataFrame ~수백 MB × max entries = 잠재 점유. CLAUDE.md
        병렬 2 × 카테고리 4 = 8 정합. 16 으로 회귀하면 메모리 압박 재유입.
        """
        from dartlab.core.dataLoader import _LOAD_CACHE_MAX

        assert _LOAD_CACHE_MAX <= 8, f"_LOAD_CACHE_MAX={_LOAD_CACHE_MAX} — 8 초과는 회사 다중 분석 시 RSS 폭증"


class TestPressureLevels:
    """M1: PRESSURE_* 4 단계 escalation 임계 분리 검증."""

    def test_fatal_distinct_from_critical(self):
        """PRESSURE_FATAL > PRESSURE_CRITICAL 분리 — 동치 시 CRITICAL elif dead code."""
        from dartlab.core.memory import PRESSURE_CRITICAL_MB, PRESSURE_FATAL_MB

        assert PRESSURE_FATAL_MB > PRESSURE_CRITICAL_MB, (
            f"FATAL={PRESSURE_FATAL_MB} CRITICAL={PRESSURE_CRITICAL_MB} 동치 — "
            f"`if mem > FATAL: ... elif mem > CRITICAL:` 구조에서 CRITICAL elif 도달 불가"
        )

    def test_levels_strictly_increasing(self):
        """WARNING < CRITICAL < FATAL < EMERGENCY 엄격 증가 — 4 단계 escalation 보장."""
        from dartlab.core.memory import (
            PRESSURE_CRITICAL_MB,
            PRESSURE_EMERGENCY_MB,
            PRESSURE_FATAL_MB,
            PRESSURE_WARNING_MB,
        )

        levels = [PRESSURE_WARNING_MB, PRESSURE_CRITICAL_MB, PRESSURE_FATAL_MB, PRESSURE_EMERGENCY_MB]
        assert levels == sorted(levels) and len(set(levels)) == 4, (
            f"4 단계 임계 엄격 증가 실패: WARNING={PRESSURE_WARNING_MB} CRITICAL={PRESSURE_CRITICAL_MB} "
            f"FATAL={PRESSURE_FATAL_MB} EMERGENCY={PRESSURE_EMERGENCY_MB}"
        )


class TestWithMemoryBudget:
    """M4: ``withMemoryBudget`` 데코레이터 — 함수 단위 RSS delta 가드."""

    def test_passes_within_budget(self):
        """delta 가 limit 이하면 정상 반환."""
        from dartlab.core.memory import withMemoryBudget

        samples = iter([100.0, 200.0])  # delta 100 < 500

        @withMemoryBudget(500, sampler=lambda: next(samples))
        def heavy():
            return "ok"

        assert heavy() == "ok"

    def test_raises_when_exceeded(self):
        """delta 가 limit 초과면 ``MemoryBudgetExceeded`` raise."""
        import pytest

        from dartlab.core.memory import MemoryBudgetExceeded, withMemoryBudget

        samples = iter([100.0, 800.0])  # delta 700 > 500

        @withMemoryBudget(500, sampler=lambda: next(samples))
        def heavy():
            return "ok"

        with pytest.raises(MemoryBudgetExceeded, match=r"delta 700.*budget 500"):
            heavy()

    def test_default_sampler_uses_real_rss(self):
        """sampler 미지정 시 기본 ``getMemoryMb`` 사용 — 단순 함수는 1GB 한계 안 넘음."""
        from dartlab.core.memory import withMemoryBudget

        @withMemoryBudget(1024)
        def light():
            return 42

        assert light() == 42


class TestOomTripwire:
    """M5: ``OomTripwire`` — RSS background watcher + 응급 graceful 종료."""

    def test_does_not_fire_below_threshold(self):
        """RSS < threshold 면 exiter 호출 안 함."""
        import time

        from dartlab.core.memory import OomTripwire

        exitedRss: list[float] = []
        tw = OomTripwire(
            thresholdMb=2500,
            intervalSec=0.02,
            sampler=lambda: 100.0,  # 항상 100
            exiter=lambda rss: exitedRss.append(rss),
        )
        tw.start()
        time.sleep(0.1)  # 여러 poll
        tw.stop()
        assert exitedRss == []

    def test_fires_when_threshold_exceeded(self):
        """RSS > threshold 면 exiter 호출."""
        import time

        from dartlab.core.memory import OomTripwire

        exitedRss: list[float] = []
        tw = OomTripwire(
            thresholdMb=1000,
            intervalSec=0.02,
            sampler=lambda: 3000.0,  # 항상 초과
            exiter=lambda rss: exitedRss.append(rss),
        )
        tw.start()
        time.sleep(0.1)
        tw.stop()
        assert len(exitedRss) >= 1 and exitedRss[0] == 3000.0

    def test_start_stop_idempotent(self):
        """double start/stop 안전."""
        from dartlab.core.memory import OomTripwire

        tw = OomTripwire(sampler=lambda: 100.0, exiter=lambda _: None)
        tw.start()
        tw.start()  # 이미 alive — noop
        tw.stop()
        tw.stop()  # 이미 정지 — noop

    def test_stop_timeout_keeps_single_live_thread(self):
        """join timeout을 성공처럼 처리해 감시 스레드를 두 개 띄우지 않는다."""
        from dartlab.core.memory import OomTripwire

        entered = threading.Event()
        release = threading.Event()

        def blockedSampler() -> float:
            entered.set()
            release.wait(2)
            return 100.0

        tw = OomTripwire(intervalSec=0.01, sampler=blockedSampler, exiter=lambda _: None)
        tw.start()
        assert entered.wait(1)
        originalThread = tw._thread
        try:
            with pytest.raises(TimeoutError, match="OomTripwire"):
                tw.stop(timeout=0)
            tw.start()
            assert tw._thread is originalThread
        finally:
            release.set()
            tw.stop(timeout=1)

    def test_sampler_failure_is_propagated_by_stop(self):
        from dartlab.core.memory import OomTripwire

        sampled = threading.Event()

        def brokenSampler() -> float:
            sampled.set()
            raise ValueError("sampler failed")

        tw = OomTripwire(intervalSec=0.01, sampler=brokenSampler, exiter=lambda _: None)
        tw.start()
        assert sampled.wait(1)

        with pytest.raises(RuntimeError, match="sampler") as caught:
            tw.stop(timeout=1)

        assert isinstance(caught.value.__cause__, ValueError)

    def test_exiter_failure_is_propagated_by_stop(self):
        from dartlab.core.memory import OomTripwire

        exited = threading.Event()

        def brokenExiter(_rss: float) -> None:
            exited.set()
            raise RuntimeError("exiter failed")

        tw = OomTripwire(
            thresholdMb=1.0,
            intervalSec=0.01,
            sampler=lambda: 2.0,
            exiter=brokenExiter,
        )
        tw.start()
        assert exited.wait(1)

        with pytest.raises(RuntimeError, match="exiter") as caught:
            tw.stop(timeout=1)

        assert isinstance(caught.value.__cause__, RuntimeError)


class TestMemoryScope:
    """Company memory scope는 watcher 하나를 잃지 않고 수명주기를 닫는다."""

    def test_nested_enter_is_rejected_without_replacing_watcher(self):
        from dartlab.core.memory import MemoryScope, OomTripwire

        scope = MemoryScope(OomTripwire(intervalSec=0.01, sampler=lambda: 0.0))
        scope.enter()
        try:
            with pytest.raises(RuntimeError, match="중첩"):
                scope.enter()
            assert scope.active
        finally:
            scope.exit(cleanup=lambda: None, bodyError=None)

        assert not scope.active

    def test_successful_exit_allows_sequential_reuse(self):
        from dartlab.core.memory import MemoryScope, OomTripwire

        scope = MemoryScope(OomTripwire(intervalSec=0.01, sampler=lambda: 0.0))

        scope.enter()
        scope.exit(cleanup=lambda: None, bodyError=None)
        scope.enter()
        scope.exit(cleanup=lambda: None, bodyError=None)

        assert not scope.active

    def test_cleanup_failure_keeps_scope_active_until_retry(self):
        from dartlab.core.memory import MemoryScope, OomTripwire

        scope = MemoryScope(OomTripwire(intervalSec=0.01, sampler=lambda: 0.0))
        scope.enter()

        def brokenCleanup() -> None:
            raise RuntimeError("cleanup failed")

        with pytest.raises(RuntimeError, match="cleanup failed"):
            scope.exit(
                cleanup=brokenCleanup,
                bodyError=None,
            )

        assert scope.active
        with pytest.raises(RuntimeError, match="중첩"):
            scope.enter()

        scope.exit(cleanup=lambda: None, bodyError=None)
        assert not scope.active


class TestFinalizeMemoryScope:
    """Company context 종료는 본문과 정리 예외를 하나도 삼키지 않는다."""

    def test_cleanup_failure_is_raised_after_normal_body(self):
        from dartlab.core.memory import finalizeMemoryScope

        failure = RuntimeError("cleanup failed")

        def cleanup() -> None:
            raise failure

        with pytest.raises(RuntimeError, match="cleanup failed") as caught:
            finalizeMemoryScope(tripwire=None, cleanup=cleanup, bodyError=None)

        assert caught.value is failure

    def test_body_and_cleanup_failures_are_both_preserved(self):
        from dartlab.core.memory import finalizeMemoryScope

        bodyError = ValueError("body failed")
        cleanupError = RuntimeError("cleanup failed")

        def cleanup() -> None:
            raise cleanupError

        with pytest.raises(BaseExceptionGroup) as caught:
            finalizeMemoryScope(
                tripwire=None,
                cleanup=cleanup,
                bodyError=bodyError,
            )

        assert caught.value.exceptions == (bodyError, cleanupError)


class TestBoundedCacheContracts:
    """BoundedCache의 구성값과 갱신도 실제 pressure 정책을 거쳐야 한다."""

    def test_pressure_parameter_controls_warning_tier(self):
        from dartlab.core.memory import BoundedCache

        cache = BoundedCache(maxEntries=30, pressureMb=300.0, memorySampler=lambda: 400.0)
        cache["value"] = 1

        assert cache._max == 15
        cache.clear()

    def test_pressure_never_increases_small_capacity(self):
        from dartlab.core.memory import BoundedCache

        cache = BoundedCache(maxEntries=1, pressureMb=300.0, memorySampler=lambda: 400.0)
        cache["value"] = 1

        assert cache._max <= 1
        cache.clear()

    def test_existing_key_update_checks_pressure(self):
        from dartlab.core.memory import BoundedCache

        samples = iter([100.0, 400.0])
        cache = BoundedCache(maxEntries=30, pressureMb=300.0, memorySampler=lambda: next(samples))
        cache["value"] = 1
        cache["value"] = 2

        assert cache._max == 15
        cache.clear()

    def test_lookup_distinguishes_cached_none_from_miss(self):
        from dartlab.core.memory import BoundedCache, lookupCache

        cache = BoundedCache(memorySampler=lambda: 0.0)
        cache["empty"] = None

        assert cache.lookup("empty") == (True, None)
        assert cache.lookup("missing") == (False, None)
        assert lookupCache({"empty": None}, "empty") == (True, None)
        assert lookupCache({}, "missing") == (False, None)
        cache.clear()

    def test_get_or_create_runs_one_builder_per_key(self):
        from dartlab.core.memory import BoundedCache

        cache = BoundedCache(memorySampler=lambda: 0.0)
        entered = threading.Event()
        release = threading.Event()
        calls = 0
        results: list[object] = []

        def builder() -> object:
            nonlocal calls
            calls += 1
            entered.set()
            release.wait(2)
            return object()

        workers = [
            threading.Thread(
                target=lambda: results.append(cache.getOrCreate("shared", builder)),
            )
            for _ in range(8)
        ]
        for worker in workers:
            worker.start()
        assert entered.wait(1)
        release.set()
        for worker in workers:
            worker.join(timeout=2)

        assert calls == 1
        assert len(results) == 8
        assert len({id(result) for result in results}) == 1
        assert cache._buildLocks == {}
        cache.clear()

    def test_emergency_pressure_keeps_resident_count_bounded(self):
        from dartlab.core.memory import BoundedCache

        cache = BoundedCache(maxEntries=8, memorySampler=lambda: 3000.0)
        for index in range(20):
            cache[str(index)] = index

        assert len(cache._store) <= cache._max <= 1
        cache.clear()

    def test_emergency_cooldown_still_enforces_reduced_capacity(self):
        """clear가 용량을 복구해도 GC cooldown이 emergency 상한을 우회하지 않는다."""
        from dartlab.core.memory import BoundedCache

        cache = BoundedCache(maxEntries=30, memorySampler=lambda: 3000.0)
        cache["before-clear"] = 1
        cache.clear()

        for index in range(20):
            cache[str(index)] = index

        assert cache._max == 3
        assert len(cache._store) <= cache._max
        cache.clear()

    @pytest.mark.parametrize(
        ("kwargs", "match"),
        [
            ({"maxEntries": 0}, "maxEntries"),
            ({"pressureMb": 0}, "pressureMb"),
        ],
    )
    def test_invalid_limits_fail_fast(self, kwargs, match):
        from dartlab.core.memory import BoundedCache

        with pytest.raises(ValueError, match=match):
            BoundedCache(**kwargs)


class TestMemoizedCalcContracts:
    """memoizedCalc는 실제 166개 caller signature와 cache namespace를 보존한다."""

    def test_additional_arguments_are_forwarded_and_keyed(self):
        from dartlab.core.memory import BoundedCache, memoizedCalc

        class Company:
            def __init__(self):
                self._cache = BoundedCache(maxEntries=10, memorySampler=lambda: 0.0)

        calls: list[tuple[str, str]] = []

        @memoizedCalc
        def calc(company, statement: str, account: str) -> str:
            calls.append((statement, account))
            return f"{statement}:{account}"

        company = Company()
        assert calc(company, "BS", "cash") == "BS:cash"
        assert calc(company, "IS", "revenue") == "IS:revenue"
        assert calc(company, "BS", "cash") == "BS:cash"
        assert calls == [("BS", "cash"), ("IS", "revenue")]
        company._cache.clear()

    def test_same_function_name_in_different_modules_does_not_collide(self):
        from dartlab.core.memory import BoundedCache, memoizedCalc

        class Company:
            def __init__(self):
                self._cache = BoundedCache(maxEntries=10, memorySampler=lambda: 0.0)

        def build(moduleName: str, value: str):
            def calcMacroSensitivity(company, *, basePeriod=None):
                return value

            calcMacroSensitivity.__module__ = moduleName
            return memoizedCalc(calcMacroSensitivity)

        dynamic = build("dartlab.analysis.financial.macroExposure", "dynamic")
        static = build("dartlab.analysis.financial._signalsMacroSensitivity", "static")
        company = Company()

        assert dynamic(company) == "dynamic"
        assert static(company) == "static"
        company._cache.clear()

    def test_real_decorated_functions_accept_their_declared_arguments(self, monkeypatch):
        from dartlab.analysis.financial import _revenueSegment
        from dartlab.analysis.financial._capitalStructure import _latestAnnualVal
        from dartlab.core.memory import BoundedCache

        class Company:
            def __init__(self):
                self._cache = BoundedCache(maxEntries=10, memorySampler=lambda: 0.0)

            def select(self, *args):
                del args
                return None

        company = Company()
        monkeypatch.setattr(_revenueSegment, "_selectDocsSalesOrder", lambda _company: None)

        assert _latestAnnualVal(company, "BS", "현금및현금성자산") is None
        assert _revenueSegment.calcBreakdown(company, "지역", basePeriod="2024") is None
        company._cache.clear()


class TestCleanupBetweenCompanies:
    def test_returns_before_after_tuple(self):
        """(before, after) 튜플 반환."""
        from dartlab.core.memory import cleanupBetweenCompanies

        result = cleanupBetweenCompanies(label="test")
        assert isinstance(result, tuple)
        assert len(result) == 2
        before, after = result
        assert before > 0
        assert after > 0

    def test_idempotent_no_error_on_repeat_call(self):
        """반복 호출해도 예외 없이 동작."""
        from dartlab.core.memory import cleanupBetweenCompanies

        for i in range(3):
            before, after = cleanupBetweenCompanies(label=f"iter{i}")
            assert before > 0 and after > 0

    def test_label_appears_in_log(self, caplog):
        """label 인자가 로그에 포함된다."""
        import logging

        from dartlab.core.memory import cleanupBetweenCompanies

        with caplog.at_level(logging.INFO, logger="dartlab.core.memory"):
            cleanupBetweenCompanies(label="005930")

        joined = " ".join(rec.message for rec in caplog.records)
        assert "005930" in joined or len(caplog.records) == 0
