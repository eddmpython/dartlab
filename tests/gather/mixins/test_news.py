"""dartlab.gather.mixins.news real unit test (A 트랙 O3).

_GatherNewsMixin 의 news/dartDoc 2 메서드 emit wrap 검증.
"""

from __future__ import annotations

import importlib

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def test_smoke_import() -> None:
    """``dartlab.gather.mixins.news`` 모듈 import 가능 — 모듈 구조 회귀 차단."""
    importlib.import_module("dartlab.gather.mixins.news")


def test_news_emits_gather_fetch(monkeypatch: pytest.MonkeyPatch) -> None:
    """news() 가 fetch 완료 시 emitGatherFetch 신호."""
    from dartlab.gather.engine import Gather
    from dartlab.gather.infra import telemetry as telemetryMod
    from dartlab.gather.sources import naverNews as naverMod
    from dartlab.gather.sources import news as newsMod

    captured: list = []
    monkeypatch.setattr(telemetryMod, "_coreEmit", lambda k, **kw: captured.append((k, kw)))

    # KR=네이버 우선 → 네트워크 격리 위해 naver stub([])로 google 폴백 경로 강제.
    async def fakeNaver(query, *, market="KR", client=None, **kw):
        return []

    async def fakeFetchAsync(query, *, market, days, client):
        return []

    monkeypatch.setattr(naverMod, "_fetchAsync", fakeNaver)
    monkeypatch.setattr(newsMod, "_fetchAsync", fakeFetchAsync)
    monkeypatch.setattr(newsMod, "toDataFrame", lambda items, **kwargs: pl.DataFrame())

    g = Gather()
    g.news("삼성전자", market="KR", days=7)

    fetchEmits = [c for c in captured if c[0] == "gather:fetch:done"]
    assert any(kw["axis"] == "news" for _, kw in fetchEmits)


def test_news_cache_isolated_by_days(monkeypatch: pytest.MonkeyPatch) -> None:
    from dartlab.gather.engine import Gather
    from dartlab.gather.sources import news as newsMod

    calls: list[int] = []

    async def fakeFetchAsync(query, *, market, days, client):
        calls.append(days)
        return [{"days": days}]

    monkeypatch.setattr(newsMod, "_fetchAsync", fakeFetchAsync)
    monkeypatch.setattr(newsMod, "toDataFrame", lambda items, **kwargs: pl.DataFrame(items))
    gather = Gather()

    thirty = gather.news("Apple", market="US", days=30)
    one = gather.news("Apple", market="US", days=1)
    thirtyAgain = gather.news("Apple", market="US", days=30)

    assert calls == [30, 1]
    assert thirty["days"][0] == thirtyAgain["days"][0] == 30
    assert one["days"][0] == 1
