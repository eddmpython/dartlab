"""dartlab.gather.sources.flow real unit test (A 트랙 T2).

flow.fetch 의 KR-only 분기 + fallback chain 동작 + limit slice 검증.
모든 케이스 monkeypatch — 네트워크 0.
"""

from __future__ import annotations

import asyncio
import importlib
import types

import pytest

pytestmark = pytest.mark.unit


def test_smoke_import() -> None:
    """``dartlab.gather.sources.flow`` 모듈 import 가능 — 모듈 구조 회귀 차단."""
    importlib.import_module("dartlab.gather.sources.flow")


def test_flow_non_kr_raises_value_error() -> None:
    """KR 외 시장은 지원하지 않음을 명시한다."""
    from dartlab.gather.sources import flow as flowMod

    with pytest.raises(ValueError, match="KR 시장만 지원"):
        asyncio.run(flowMod.fetch("AAPL", market="US"))


def test_flow_fallback_chain_first_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """fallback chain 첫 성공 결과에 실제 source와 수집 시각을 붙인다."""
    from dartlab.gather.sources import flow as flowMod

    fakeRows = [
        {"date": "2026-01-01", "foreignNet": 100.0, "institutionNet": 50.0, "individualNet": -150.0},
        {"date": "2026-01-02", "foreignNet": 200.0, "institutionNet": -50.0, "individualNet": -150.0},
    ]

    async def fakeFetchFlow(stockCode, client, **kwargs):
        return fakeRows

    fakeModule = types.SimpleNamespace(fetchFlow=fakeFetchFlow)
    monkeypatch.setattr(flowMod, "FLOW_FALLBACK", ["naver"])
    monkeypatch.setattr(flowMod, "loadDomain", lambda name: fakeModule)
    monkeypatch.setattr(
        flowMod,
        "circuitBreaker",
        types.SimpleNamespace(isOpen=lambda src: False, recordFailure=lambda src: None, recordSuccess=lambda src: None),
    )

    result = asyncio.run(flowMod.fetch("005930", market="KR"))
    assert [row["date"] for row in result] == ["2026-01-01", "2026-01-02"]
    assert {row["source"] for row in result} == {"naver"}
    assert all(isinstance(row["fetchedAt"], str) and row["fetchedAt"] for row in result)
    assert result[0] is not fakeRows[0]
    assert "source" not in fakeRows[0]


def test_flow_all_fail_preserves_causes(monkeypatch: pytest.MonkeyPatch) -> None:
    """모든 fallback 실패 시 source별 원인을 보존한 typed aggregate를 raise한다."""
    from dartlab.gather.sources import flow as flowMod
    from dartlab.gather.types import GatherError, SourceAttemptsExhaustedError

    async def boom(stockCode, client, **kwargs):
        raise GatherError("source down")

    fakeModule = types.SimpleNamespace(fetchFlow=boom)
    monkeypatch.setattr(flowMod, "FLOW_FALLBACK", ["naver", "anotherSource"])
    monkeypatch.setattr(flowMod, "loadDomain", lambda name: fakeModule)
    failures = []
    monkeypatch.setattr(
        flowMod,
        "circuitBreaker",
        types.SimpleNamespace(
            isOpen=lambda src: False,
            recordFailure=lambda src: failures.append(src),
            recordSuccess=lambda src: None,
        ),
    )

    with pytest.raises(SourceAttemptsExhaustedError) as excInfo:
        asyncio.run(flowMod.fetch("005930", market="KR"))

    assert tuple(excInfo.value.failures) == ("naver", "anotherSource")
    assert all(isinstance(cause, GatherError) for cause in excInfo.value.failures.values())
    assert failures == ["naver", "anotherSource"]
    assert isinstance(excInfo.value.__cause__, GatherError)


def test_flow_successful_empty_is_not_provider_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """정상 빈 응답이 하나라도 있으면 provider 전멸 예외 대신 빈 list를 반환한다."""
    from dartlab.gather.sources import flow as flowMod

    async def fakeFetchFlow(stockCode, client, **kwargs):
        return None

    fakeModule = types.SimpleNamespace(fetchFlow=fakeFetchFlow)
    monkeypatch.setattr(flowMod, "FLOW_FALLBACK", ["naver"])
    monkeypatch.setattr(flowMod, "loadDomain", lambda name: fakeModule)
    monkeypatch.setattr(
        flowMod,
        "circuitBreaker",
        types.SimpleNamespace(isOpen=lambda src: False, recordFailure=lambda src: None, recordSuccess=lambda src: None),
    )

    assert asyncio.run(flowMod.fetch("005930", market="KR")) == []


def test_flow_limit_slices(monkeypatch: pytest.MonkeyPatch) -> None:
    """limit 인자로 가장 최근 N건 slice."""
    from dartlab.gather.sources import flow as flowMod

    fakeRows = [{"date": f"2026-01-{i:02d}", "foreignNet": float(i)} for i in range(1, 11)]

    async def fakeFetchFlow(stockCode, client, **kwargs):
        return fakeRows

    fakeModule = types.SimpleNamespace(fetchFlow=fakeFetchFlow)
    monkeypatch.setattr(flowMod, "FLOW_FALLBACK", ["naver"])
    monkeypatch.setattr(flowMod, "loadDomain", lambda name: fakeModule)
    monkeypatch.setattr(
        flowMod,
        "circuitBreaker",
        types.SimpleNamespace(isOpen=lambda src: False, recordFailure=lambda src: None, recordSuccess=lambda src: None),
    )

    result = asyncio.run(flowMod.fetch("005930", market="KR", limit=3))
    assert len(result) == 3
    assert result[0]["date"] == "2026-01-01"
    assert result[0]["source"] == "naver"


def test_flow_passes_backfill_options(monkeypatch: pytest.MonkeyPatch) -> None:
    """start/end/full 옵션을 source domain 으로 전달한다."""
    from dartlab.gather.sources import flow as flowMod

    seen = {}

    async def fakeFetchFlow(stockCode, client, **kwargs):
        seen.update(kwargs)
        return [{"date": "20200131", "foreignNet": -1.0}]

    fakeModule = types.SimpleNamespace(fetchFlow=fakeFetchFlow)
    monkeypatch.setattr(flowMod, "FLOW_FALLBACK", ["naver"])
    monkeypatch.setattr(flowMod, "loadDomain", lambda name: fakeModule)
    monkeypatch.setattr(
        flowMod,
        "circuitBreaker",
        types.SimpleNamespace(isOpen=lambda src: False, recordFailure=lambda src: None, recordSuccess=lambda src: None),
    )

    result = asyncio.run(
        flowMod.fetch(
            "005930",
            market="KR",
            start="2020-01-01",
            end="2020-01-31",
            pageSize=50,
            sleepSec=1.0,
            marketType="KRX",
            maxPages=2,
            full=True,
            proxy="http://proxy.example:8080",
        )
    )

    assert result[0]["date"] == "20200131"
    assert result[0]["foreignNet"] == -1.0
    assert result[0]["source"] == "naver"
    assert result[0]["fetchedAt"]
    assert seen["start"] == "2020-01-01"
    assert seen["end"] == "2020-01-31"
    assert seen["pageSize"] == 50
    assert seen["sleepSec"] == 1.0
    assert seen["marketType"] == "KRX"
    assert seen["maxPages"] == 2
    assert seen["full"] is True
    assert seen["proxy"] == "http://proxy.example:8080"
