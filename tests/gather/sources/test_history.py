"""dartlab.gather.sources.history real unit test (A 트랙 T4).

history.fetch — fallback chain 동작 + 빈 결과 처리 + limit slice.
"""

from __future__ import annotations

import asyncio
import importlib
import types

import pytest

pytestmark = pytest.mark.unit


def test_smoke_import() -> None:
    """``dartlab.gather.sources.history`` 모듈 import 가능 — 모듈 구조 회귀 차단."""
    importlib.import_module("dartlab.gather.sources.history")


def test_history_fallback_first_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """fallback chain 첫 성공 결과에 실제 source와 수집 시각을 붙인다."""
    from dartlab.gather.sources import history as historyMod

    fakeRows = [
        {"date": "2026-01-01", "close": 70000},
        {"date": "2026-01-02", "close": 71000},
    ]

    async def fakeFetchHistory(stockCode, client, *, start, end, market):
        return fakeRows

    fakeModule = types.SimpleNamespace(fetchHistory=fakeFetchHistory)
    monkeypatch.setattr(historyMod, "HISTORY_FALLBACK", ["naver"])
    monkeypatch.setattr(historyMod, "loadDomain", lambda name: fakeModule)
    fakeCircuit = types.SimpleNamespace(
        isOpen=lambda src: False,
        recordFailure=lambda src: None,
        recordSuccess=lambda src: None,
    )
    monkeypatch.setattr(historyMod, "circuitBreaker", fakeCircuit)

    result = asyncio.run(historyMod.fetch("005930", start="2026-01-01", end="2026-01-02"))
    assert [row["date"] for row in result] == ["2026-01-01", "2026-01-02"]
    assert {row["source"] for row in result} == {"naver"}
    assert all(isinstance(row["fetchedAt"], str) and row["fetchedAt"] for row in result)
    assert result[0] is not fakeRows[0]
    assert "source" not in fakeRows[0]


def test_history_all_fail_preserves_causes(monkeypatch: pytest.MonkeyPatch) -> None:
    """모든 fallback 실패 시 source별 원인을 보존한 typed aggregate를 raise한다."""
    from dartlab.gather.sources import history as historyMod
    from dartlab.gather.types import GatherError, SourceAttemptsExhaustedError

    async def boom(stockCode, client, *, start, end, market):
        raise GatherError("source down")

    fakeModule = types.SimpleNamespace(fetchHistory=boom)
    monkeypatch.setattr(historyMod, "HISTORY_FALLBACK", ["naver", "fdr"])
    monkeypatch.setattr(historyMod, "loadDomain", lambda name: fakeModule)
    failures = []
    fakeCircuit = types.SimpleNamespace(
        isOpen=lambda src: False,
        recordFailure=lambda src: failures.append(src),
        recordSuccess=lambda src: None,
    )
    monkeypatch.setattr(historyMod, "circuitBreaker", fakeCircuit)

    with pytest.raises(SourceAttemptsExhaustedError) as excInfo:
        asyncio.run(historyMod.fetch("005930", start="2026-01-01", end="2026-01-02"))

    assert tuple(excInfo.value.failures) == ("naver", "fdr", "fmp")
    assert all(isinstance(cause, GatherError) for cause in excInfo.value.failures.values())
    assert failures == ["naver", "fdr", "fmp"]
    assert isinstance(excInfo.value.__cause__, GatherError)


def test_history_successful_empty_is_not_provider_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """정상 빈 응답이 하나라도 있으면 provider 전멸 예외 대신 빈 list를 반환한다."""
    from dartlab.gather.sources import history as historyMod
    from dartlab.gather.types import GatherError

    async def failFetchHistory(stockCode, client, *, start, end, market):
        raise GatherError("source down")

    async def emptyFetchHistory(stockCode, client, *, start, end, market):
        return []

    modules = {
        "naver": types.SimpleNamespace(fetchHistory=failFetchHistory),
        "fdr": types.SimpleNamespace(fetchHistory=emptyFetchHistory),
        "fmp": types.SimpleNamespace(fetchHistory=emptyFetchHistory),
    }
    monkeypatch.setattr(historyMod, "HISTORY_FALLBACK", ["naver", "fdr"])
    monkeypatch.setattr(historyMod, "loadDomain", modules.__getitem__)
    fakeCircuit = types.SimpleNamespace(
        isOpen=lambda src: False,
        recordFailure=lambda src: None,
        recordSuccess=lambda src: None,
    )
    monkeypatch.setattr(historyMod, "circuitBreaker", fakeCircuit)

    result = asyncio.run(historyMod.fetch("EMPTY", start="2026-01-01", end="2026-01-02"))
    assert result == []


def test_history_domain_load_failure_is_preserved(monkeypatch: pytest.MonkeyPatch) -> None:
    """도메인 로드 실패도 source별 aggregate 원인에서 유실하지 않는다."""
    from dartlab.gather.sources import history as historyMod
    from dartlab.gather.types import SourceAttemptsExhaustedError

    monkeypatch.setattr(historyMod, "HISTORY_FALLBACK", ["missing"])

    def failLoadDomain(name: str):
        raise ImportError(f"{name} module unavailable")

    monkeypatch.setattr(historyMod, "loadDomain", failLoadDomain)
    monkeypatch.setattr(
        historyMod,
        "circuitBreaker",
        types.SimpleNamespace(isOpen=lambda src: False, recordFailure=lambda src: None, recordSuccess=lambda src: None),
    )

    with pytest.raises(SourceAttemptsExhaustedError) as excInfo:
        asyncio.run(historyMod.fetch("005930", start="2026-01-01", end="2026-01-02", market="US"))

    assert tuple(excInfo.value.failures) == ("missing", "fmp")
    assert all(isinstance(cause, ImportError) for cause in excInfo.value.failures.values())


def test_history_circuit_open_is_preserved(monkeypatch: pytest.MonkeyPatch) -> None:
    """모든 source circuit이 open이면 각 차단 원인을 aggregate에 보존한다."""
    from dartlab.gather.sources import history as historyMod
    from dartlab.gather.types import CircuitOpenError, SourceAttemptsExhaustedError

    monkeypatch.setattr(historyMod, "HISTORY_FALLBACK", ["naver"])
    monkeypatch.setattr(
        historyMod,
        "circuitBreaker",
        types.SimpleNamespace(isOpen=lambda src: True, recordFailure=lambda src: None, recordSuccess=lambda src: None),
    )

    with pytest.raises(SourceAttemptsExhaustedError) as excInfo:
        asyncio.run(historyMod.fetch("005930", start="2026-01-01", end="2026-01-02"))

    assert all(isinstance(cause, CircuitOpenError) for cause in excInfo.value.failures.values())


def test_history_invalid_input_is_not_fallback_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """호출자 입력 ValueError는 다른 source 장애로 오인하지 않고 즉시 전달한다."""
    from dartlab.gather.sources import history as historyMod

    calls: list[str] = []

    async def invalid(*args, **kwargs):
        raise ValueError("invalid stock code")

    monkeypatch.setattr(historyMod, "HISTORY_FALLBACK", ["naver", "fdr"])
    monkeypatch.setattr(
        historyMod,
        "loadDomain",
        lambda name: calls.append(name) or types.SimpleNamespace(fetchHistory=invalid),
    )
    monkeypatch.setattr(
        historyMod,
        "circuitBreaker",
        types.SimpleNamespace(isOpen=lambda src: False, recordFailure=lambda src: None, recordSuccess=lambda src: None),
    )

    with pytest.raises(ValueError, match="invalid stock code"):
        asyncio.run(historyMod.fetch("bad", start="2026-01-01", end="2026-01-02"))

    assert calls == ["naver"]
