"""dartlab.gather.sources.insider real unit test (A 트랙 I2 + T2).

iterFetchInsiderTrading / iterFetchMajorShareholders generator 검증.
"""

from __future__ import annotations

import importlib
from typing import Any

import pytest

pytestmark = pytest.mark.unit


def test_smoke_import() -> None:
    """``dartlab.gather.sources.insider`` 모듈 import 가능 — 모듈 구조 회귀 차단."""
    importlib.import_module("dartlab.gather.sources.insider")


def test_iterFetchInsiderTrading_yields(monkeypatch: pytest.MonkeyPatch) -> None:
    """iterFetchInsiderTrading — runAsync(fetchInsiderTrading) 결과 mock 후 batch yield."""
    from dartlab.gather.sources import insider as insiderMod

    fakeRows = list(range(15))  # InsiderTrade 대신 단순 int (구조만 검증)

    async def fakeFetch(stockCode, *, market="KR"):
        return fakeRows

    monkeypatch.setattr(insiderMod, "fetchInsiderTrading", fakeFetch)

    batches = list(insiderMod.iterFetchInsiderTrading("005930", batchSize=7))
    assert len(batches) == 3  # 15 / 7 = 3 batches (7, 7, 1)
    assert len(batches[0]) == 7
    assert len(batches[-1]) == 1


def test_iterFetchMajorShareholders_yields(monkeypatch: pytest.MonkeyPatch) -> None:
    """iterFetchMajorShareholders — list batch yield."""
    from dartlab.gather.sources import insider as insiderMod

    fakeHolders = list(range(8))

    async def fakeFetch(stockCode, *, market="KR"):
        return fakeHolders

    monkeypatch.setattr(insiderMod, "fetchMajorShareholders", fakeFetch)

    batches = list(insiderMod.iterFetchMajorShareholders("005930", batchSize=3))
    assert len(batches) == 3  # 8 / 3 = 3 batches (3, 3, 2)
    assert len(batches[-1]) == 2


def test_iter_empty_returns_no_batches(monkeypatch: pytest.MonkeyPatch) -> None:
    """fetch 결과가 빈 list 면 iter 도 빈 yield."""
    from dartlab.gather.sources import insider as insiderMod

    async def fakeFetch(stockCode, *, market="KR"):
        return []

    monkeypatch.setattr(insiderMod, "fetchInsiderTrading", fakeFetch)
    monkeypatch.setattr(insiderMod, "fetchMajorShareholders", fakeFetch)

    assert list(insiderMod.iterFetchInsiderTrading("005930")) == []
    assert list(insiderMod.iterFetchMajorShareholders("005930")) == []


class _FakeInsiderProvider:
    def __init__(
        self,
        *,
        insiderRows: list[dict[str, Any]] | None = None,
        holderRows: list[dict[str, Any]] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.insiderRows = insiderRows or []
        self.holderRows = holderRows or []
        self.error = error
        self.insiderLimit: int | None = None
        self.holderLimit: int | None = None

    async def fetchInsiderTradingRaw(self, _stockCode: str, *, limit: int | None = None) -> list[dict[str, Any]]:
        self.insiderLimit = limit
        if self.error is not None:
            raise self.error
        return self.insiderRows

    async def fetchMajorShareholdersRaw(
        self,
        _stockCode: str,
        *,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        self.holderLimit = limit
        if self.error is not None:
            raise self.error
        return self.holderRows


@pytest.mark.asyncio
async def test_fetch_insider_rejects_unsupported_market(monkeypatch: pytest.MonkeyPatch) -> None:
    """지원하지 않는 시장을 데이터 0건으로 표현하지 않는다."""
    from dartlab.gather.sources import insider as insiderMod

    monkeypatch.setattr(insiderMod, "getInsiderRawProvider", lambda: pytest.fail("provider lookup must not run"))

    with pytest.raises(ValueError, match="KR만 지원"):
        await insiderMod.fetchInsiderTrading("AAPL", market="US")


@pytest.mark.asyncio
async def test_fetch_insider_reports_missing_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    """composition 누락을 정상 빈 응답과 구분한다."""
    from dartlab.gather.sources import insider as insiderMod

    monkeypatch.setattr(insiderMod, "getInsiderRawProvider", lambda: None)

    with pytest.raises(RuntimeError, match="등록되지 않았습니다"):
        await insiderMod.fetchInsiderTrading("005930")


@pytest.mark.asyncio
async def test_fetch_insider_preserves_raw_provider_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """provider 예외 타입과 메시지를 gather 경계에서 보존한다."""
    from dartlab.gather.sources import insider as insiderMod

    provider = _FakeInsiderProvider(error=OSError("OpenDART disconnected"))
    monkeypatch.setattr(insiderMod, "getInsiderRawProvider", lambda: provider)

    with pytest.raises(OSError, match="OpenDART disconnected"):
        await insiderMod.fetchInsiderTrading("005930")


@pytest.mark.asyncio
async def test_fetch_major_shareholders_normal_empty_and_limit_passthrough(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """정상 빈 결과는 []이고 상한은 raw provider 호출자까지 명확히 전달한다."""
    from dartlab.gather.sources import insider as insiderMod

    provider = _FakeInsiderProvider()
    monkeypatch.setattr(insiderMod, "getInsiderRawProvider", lambda: provider)

    assert await insiderMod.fetchMajorShareholders("005930", limit=0) == []
    assert provider.holderLimit == 0


@pytest.mark.asyncio
async def test_fetch_insider_preserves_schema_conversion_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """잘못된 raw schema를 빈 목록으로 삼키지 않는다."""
    from dartlab.gather.sources import insider as insiderMod

    provider = _FakeInsiderProvider(insiderRows=[{"unknownField": "bad"}])
    monkeypatch.setattr(insiderMod, "getInsiderRawProvider", lambda: provider)

    with pytest.raises(TypeError, match="unknownField"):
        await insiderMod.fetchInsiderTrading("005930")
