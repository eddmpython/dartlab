"""gather accessor가 공개 gather 옵션 계약을 정확히 번역하는지 검증한다."""

from __future__ import annotations

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def test_fetchMacroSeries_translates_source_to_public_market(monkeypatch: pytest.MonkeyPatch) -> None:
    """legacy source 이름은 공개 gather에 새지 않고 market 계약으로 변환한다."""
    from dartlab.gather import entry
    from dartlab.gather.accessors import DefaultFinanceAccessor

    calls: list[tuple[tuple, dict]] = []

    class FakeEntry:
        def __call__(self, *args, **kwargs):
            calls.append((args, kwargs))
            return pl.DataFrame({"date": [1, 2], "value": [10.0, 20.0]})

    monkeypatch.setattr(entry, "GatherEntry", FakeEntry)

    result = DefaultFinanceAccessor().fetchMacroSeries("GDP", source="fred", limit=1)

    assert calls == [(("macro", "GDP"), {"market": "US", "start": None})]
    assert result["value"].to_list() == [20.0]


def test_fetchMacroSeries_rejects_unknown_source() -> None:
    """알 수 없는 source를 None으로 삼키지 않는다."""
    from dartlab.gather.accessors import DefaultFinanceAccessor

    with pytest.raises(ValueError, match="source는"):
        DefaultFinanceAccessor().fetchMacroSeries("GDP", source="typo")


def test_fetchPriceSnapshot_does_not_swallow_provider_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """가격 공급자 오류는 None으로 바뀌지 않고 소비자에게 보존된다."""
    from dartlab.gather import entry
    from dartlab.gather.accessors import DefaultFinanceAccessor
    from dartlab.gather.types import SourceUnavailableError

    class FakeEntry:
        def __call__(self, *args, **kwargs):
            raise SourceUnavailableError("price providers unavailable")

    monkeypatch.setattr(entry, "GatherEntry", FakeEntry)

    with pytest.raises(SourceUnavailableError, match="providers unavailable"):
        DefaultFinanceAccessor().fetchPriceSnapshot("005930")


def test_fetchExogenousAxes_uses_indicator_mapping_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    """외생변수 dataclass를 Protocol의 (seriesId, source) 계약으로 변환한다."""
    from dartlab.gather.accessors import DefaultFinanceAccessor
    from dartlab.gather.mapping import exogenousAxes

    indicators = [
        exogenousAxes.ExogenousIndicator("GDP", "fred", "GDP", "demand"),
        exogenousAxes.ExogenousIndicator("BASE_RATE", "ecos", "기준금리", "financial"),
    ]
    monkeypatch.setattr(exogenousAxes, "getExogenousIndicators", lambda **kwargs: indicators)

    result = DefaultFinanceAccessor().fetchExogenousAxes("005930", limit=1)

    assert result == [("GDP", "fred")]


def test_fetchAlignedMacro_joins_available_series_by_period(monkeypatch: pytest.MonkeyPatch) -> None:
    """기업별 외생축 캐시를 period 기준 단일 패널로 결합한다."""
    from dartlab.gather.accessors import DefaultFinanceAccessor
    from dartlab.gather.transforms import macro

    accessor = DefaultFinanceAccessor()
    monkeypatch.setattr(accessor, "fetchExogenousAxes", lambda stockCode: [("GDP", "fred"), ("CPI", "ecos")])

    def fakeLoad(seriesId, *, source):
        if seriesId == "GDP":
            return pl.DataFrame({"date": ["2024-03-31"], "value": [10.0]})
        return pl.DataFrame({"date": ["2024-03-31"], "value": [20.0]})

    def fakeAlign(series, periods):
        return pl.DataFrame({"period": periods, "value": [series["value"][0]] * len(periods)})

    monkeypatch.setattr(macro, "loadMacroParquet", fakeLoad)
    monkeypatch.setattr(macro, "alignToFinancialPeriods", fakeAlign)

    result = accessor.fetchAlignedMacro("005930", ["2024Q1", "2024Q2"])

    assert result is not None
    assert result.to_dict(as_series=False) == {
        "period": ["2024Q1", "2024Q2"],
        "GDP": [10.0, 10.0],
        "CPI": [20.0, 20.0],
    }
