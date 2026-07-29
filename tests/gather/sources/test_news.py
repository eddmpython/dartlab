"""dartlab.gather.sources.news real unit test (A 트랙 I2 + T2).

iterFetchNews generator + fetchNews 본문 검증.
"""

from __future__ import annotations

import asyncio
import importlib
import types

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def test_smoke_import() -> None:
    """``dartlab.gather.sources.news`` 모듈 import 가능 — 모듈 구조 회귀 차단."""
    importlib.import_module("dartlab.gather.sources.news")


def test_iterFetchNews_yields(monkeypatch: pytest.MonkeyPatch) -> None:
    """iterFetchNews — fetchNews 결과 mock 후 batch yield (A 트랙 I2)."""
    from dartlab.gather.sources import news as newsMod

    df = pl.DataFrame({"title": [f"t{i}" for i in range(12)], "url": ["x"] * 12})
    monkeypatch.setattr(newsMod, "fetchNews", lambda *a, **kw: df)

    batches = list(newsMod.iterFetchNews("test", batchSize=5))
    assert len(batches) == 3
    assert batches[0].height == 5
    assert batches[-1].height == 2


def test_iterFetchNews_empty_df(monkeypatch: pytest.MonkeyPatch) -> None:
    """fetchNews 가 빈 DataFrame 이면 iter generator 도 빈 yield."""
    from dartlab.gather.sources import news as newsMod

    monkeypatch.setattr(newsMod, "fetchNews", lambda *a, **kw: pl.DataFrame())
    batches = list(newsMod.iterFetchNews("nothing"))
    assert batches == []


def test_toDataFrame_preserves_provider_and_fetch_time() -> None:
    """뉴스 매체 source와 수집 provider를 구분하고 수집 시각을 동행한다."""
    from dartlab.gather.sources import news as newsMod
    from dartlab.gather.types import NewsItem

    df = newsMod.toDataFrame(
        [NewsItem(date="2026-07-01", title="t", source="publisher", url="https://example.com")],
        provider="google_news",
    )

    assert df.row(0, named=True)["source"] == "publisher"
    assert df.row(0, named=True)["provider"] == "google_news"
    assert df.row(0, named=True)["fetchedAt"]


def test_google_news_failure_and_invalid_input_are_not_empty_results(monkeypatch: pytest.MonkeyPatch) -> None:
    """입력 오류와 provider 장애를 기사 0건으로 바꾸지 않는다."""
    from dartlab.gather.sources import news as newsMod
    from dartlab.gather.types import CircuitOpenError, SourceUnavailableError

    with pytest.raises(ValueError, match="KR/US"):
        asyncio.run(newsMod._fetchAsync("query", market="XX"))
    with pytest.raises(ValueError, match="1 이상"):
        asyncio.run(newsMod._fetchAsync("query", days=0))

    monkeypatch.setattr(
        newsMod,
        "_circuit_breaker",
        types.SimpleNamespace(isOpen=lambda source: True),
    )
    with pytest.raises(CircuitOpenError):
        asyncio.run(newsMod._fetchAsync("query"))

    class BadClient:
        @staticmethod
        async def get(url, timeout):
            raise OSError("network down")

    monkeypatch.setattr(
        newsMod,
        "_circuit_breaker",
        types.SimpleNamespace(
            isOpen=lambda source: False,
            recordSuccess=lambda source: None,
            recordFailure=lambda source: None,
        ),
    )
    monkeypatch.setattr(
        newsMod,
        "_health_tracker",
        types.SimpleNamespace(record=lambda *args, **kwargs: None),
    )
    with pytest.raises(SourceUnavailableError, match="조회 실패"):
        asyncio.run(newsMod._fetchAsync("query", client=BadClient()))
