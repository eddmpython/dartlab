"""dartlab.gather.mixins.collect real unit test (A 트랙 O3).

_GatherCollectMixin 의 collect() emit wrap 검증.
"""

from __future__ import annotations

import asyncio
import importlib

import pytest

pytestmark = pytest.mark.unit


def test_smoke_import() -> None:
    """``dartlab.gather.mixins.collect`` 모듈 import 가능 — 모듈 구조 회귀 차단."""
    importlib.import_module("dartlab.gather.mixins.collect")


def test_collect_emits_gather_fetch(monkeypatch: pytest.MonkeyPatch) -> None:
    """collect() 가 fetch 완료 시 emitGatherFetch 신호."""
    from datetime import datetime, timezone

    from dartlab.gather.engine import Gather
    from dartlab.gather.infra import telemetry as telemetryMod
    from dartlab.gather.mixins import collect as collectMod
    from dartlab.gather.types import GatherSnapshot

    captured: list = []
    monkeypatch.setattr(telemetryMod, "_coreEmit", lambda k, **kw: captured.append((k, kw)))

    async def fakeCollect(self, stockCode, market):
        return GatherSnapshot(
            stockCode=stockCode,
            results={},
            collected_at=datetime.now(timezone.utc).isoformat(),
            _news=[],
            _sectorInfo=None,
            _insiderTrades=[],
        )

    monkeypatch.setattr(collectMod._GatherCollectMixin, "_collectAsync", fakeCollect)

    g = Gather()
    g.collect("005930", market="KR")

    fetchEmits = [c for c in captured if c[0] == "gather:fetch:done"]
    assert any(kw["axis"] == "collect" for _, kw in fetchEmits)


def test_collect_timeout_preserves_completed_results(monkeypatch: pytest.MonkeyPatch) -> None:
    from types import SimpleNamespace

    from dartlab.gather.engine import Gather
    from dartlab.gather.mixins import collect as collectMod
    from dartlab.gather.types import GatherResult, PriceSnapshot

    monkeypatch.setattr(collectMod, "_COLLECT_TIMEOUT_SECONDS", 0.01)
    monkeypatch.setattr(collectMod, "getMarketConfig", lambda market: SimpleNamespace(fallback_chain=["fast", "slow"]))

    async def fakeDomain(self, domainName, stockCode, market):
        if domainName == "slow":
            await asyncio.sleep(1)
        return GatherResult(domain=domainName, price=PriceSnapshot(current=100.0, source=domainName))

    async def emptyList(*args, **kwargs):
        return []

    async def emptySector(*args, **kwargs):
        return None

    monkeypatch.setattr(collectMod._GatherCollectMixin, "_fetchDomainAsync", fakeDomain)
    monkeypatch.setattr(collectMod._news, "_fetchAsync", emptyList)
    monkeypatch.setattr(collectMod._sector, "fetch", emptySector)
    monkeypatch.setattr(collectMod._insider, "fetchInsiderTrading", emptyList)

    snapshot = Gather().collect("005930", market="KR")

    assert snapshot.results["fast"].price is not None
    assert snapshot.results["slow"].error == "timeout"
    assert snapshot.sourcesAvailable == ["fast"]
    assert snapshot.sourcesFailed == ["slow"]


def test_collect_records_auxiliary_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    from types import SimpleNamespace

    from dartlab.gather.engine import Gather
    from dartlab.gather.mixins import collect as collectMod
    from dartlab.gather.types import GatherResult

    monkeypatch.setattr(collectMod, "getMarketConfig", lambda market: SimpleNamespace(fallback_chain=["only"]))

    async def domain(self, domainName, stockCode, market):
        return GatherResult(domain=domainName)

    async def fail(*args, **kwargs):
        raise RuntimeError("source down")

    monkeypatch.setattr(collectMod._GatherCollectMixin, "_fetchDomainAsync", domain)
    monkeypatch.setattr(collectMod._news, "_fetchAsync", fail)
    monkeypatch.setattr(collectMod._sector, "fetch", fail)
    monkeypatch.setattr(collectMod._insider, "fetchInsiderTrading", fail)

    snapshot = Gather().collect("005930", market="KR")

    assert snapshot.errors == {
        "news": "source down",
        "sector": "source down",
        "insider": "source down",
    }
    assert snapshot.sourcesAvailable == []
