"""dartlab.gather.sources.ownership real unit test (A 트랙 I2).

iterFetch generator + _cleanFloat 헬퍼 검증.
"""

from __future__ import annotations

import asyncio
import importlib

import pytest

pytestmark = pytest.mark.unit


def test_smoke_import() -> None:
    """``dartlab.gather.sources.ownership`` 모듈 import 가능 — 모듈 구조 회귀 차단."""
    importlib.import_module("dartlab.gather.sources.ownership")


def test_iterFetch_yields(monkeypatch: pytest.MonkeyPatch) -> None:
    """iterFetch — fetch 결과 mock 후 batch yield (A 트랙 I2)."""
    from dartlab.gather.sources import ownership as ownerMod

    fakeOwners = list(range(10))

    async def fakeFetch(stockCode, *, market="KR", client, limit=None):
        return fakeOwners

    monkeypatch.setattr(ownerMod, "fetch", fakeFetch)

    batches = list(ownerMod.iterFetch("005930", client=object(), batchSize=4))
    assert len(batches) == 3  # 10 / 4 = 3 batches (4, 4, 2)
    assert len(batches[0]) == 4
    assert len(batches[-1]) == 2


def test_cleanFloat_parses_comma_and_pct() -> None:
    """_cleanFloat — 콤마·퍼센트·명시적 결측만 정규화한다."""
    from dartlab.gather.sources.ownership import _cleanFloat

    assert _cleanFloat("1,234.5") == 1234.5
    assert _cleanFloat("  42  ") == 42.0
    assert _cleanFloat("42%") == 42.0
    assert _cleanFloat("") == 0.0
    assert _cleanFloat(None) == 0.0
    assert _cleanFloat("-") == 0.0
    with pytest.raises(ValueError):
        _cleanFloat("invalid")


def test_iterFetch_empty_returns_no_batches(monkeypatch: pytest.MonkeyPatch) -> None:
    """fetch 가 빈 list 반환 시 iter 도 빈 yield."""
    from dartlab.gather.sources import ownership as ownerMod

    async def fakeFetch(stockCode, *, market="KR", client, limit=None):
        return []

    monkeypatch.setattr(ownerMod, "fetch", fakeFetch)
    assert list(ownerMod.iterFetch("005930", client=object())) == []


def test_fetch_rejects_market_and_propagates_invalid_schema() -> None:
    """지원하지 않는 시장과 malformed provider 응답을 빈 결과로 삼키지 않는다."""
    from dartlab.gather.sources import ownership as ownerMod
    from dartlab.gather.types import SourceUnavailableError

    with pytest.raises(ValueError, match="KR 시장만"):
        asyncio.run(ownerMod.fetch("AAPL", market="US", client=object()))

    class BadResponse:
        @staticmethod
        def json():
            return {"dealTrendInfos": "not-a-list"}

    class BadClient:
        @staticmethod
        async def get(url):
            return BadResponse()

    with pytest.raises(SourceUnavailableError, match="응답 해석 실패"):
        asyncio.run(ownerMod.fetch("005930", market="KR", client=BadClient()))
