"""gather("macro") HF 벌크 기본 경로 회귀."""

from __future__ import annotations

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def _mockLoadData(stockCode: str, category: str, **_kwargs):
    if category == "macroFred" and stockCode == "manifest":
        return pl.DataFrame(
            {
                "source": ["fred", "fred"],
                "seriesId": ["FEDFUNDS", "GDP"],
                "label": ["연방기금금리", "GDP"],
                "group": ["rates", "growth"],
                "frequency": ["Monthly", "Quarterly"],
                "unit": ["Percent", "Billions"],
                "description": ["rate", "gdp"],
                "rowCount": [2, 1],
                "startDate": ["2024-01-01", "2024-01-01"],
                "latestDate": ["2024-02-01", "2024-01-01"],
                "updatedAtUtc": ["2026-04-28T00:00:00Z", "2026-04-28T00:00:00Z"],
                "status": ["ok", "ok"],
                "error": ["", ""],
            }
        )
    if category == "macroFred" and stockCode == "observations":
        return pl.DataFrame(
            {
                "seriesId": ["FEDFUNDS", "FEDFUNDS", "GDP"],
                "date": ["2024-01-01", "2024-02-01", "2024-01-01"],
                "value": [5.33, 5.33, 100.0],
            }
        ).with_columns(pl.col("date").cast(pl.Date))
    if category == "macroEcos" and stockCode == "manifest":
        return pl.DataFrame(
            {
                "source": ["ecos"],
                "seriesId": ["CPI"],
                "label": ["소비자물가"],
                "group": ["물가"],
                "frequency": ["M"],
                "unit": ["2020=100"],
                "description": ["cpi"],
                "rowCount": [1],
                "startDate": ["2024-01-01"],
                "latestDate": ["2024-01-01"],
                "updatedAtUtc": ["2026-04-28T00:00:00Z"],
                "status": ["ok"],
                "error": [""],
            }
        )
    if category == "macroEcos" and stockCode == "observations":
        return pl.DataFrame({"seriesId": ["CPI"], "date": ["2024-01-01"], "value": [110.0]}).with_columns(
            pl.col("date").cast(pl.Date)
        )
    raise AssertionError((stockCode, category))


def test_gather_macro_uses_hf_without_api_key(monkeypatch):
    """API 키 없이 FRED HF observations 에서 단일 지표 반환."""
    import dartlab.core.dataLoader as dataLoader
    from dartlab.gather import getDefaultGather

    monkeypatch.setattr(dataLoader, "loadData", _mockLoadData)
    df = getDefaultGather().macro("FEDFUNDS")

    assert df.columns == ["date", "value"]
    assert df.height == 2
    assert df["value"].to_list() == [5.33, 5.33]


def test_gather_macro_default_wide_keeps_existing_scope(monkeypatch):
    """기본 전체 호출은 기존 default 목록 기반 wide 형태를 유지."""
    import importlib

    import dartlab.core.dataLoader as dataLoader

    gather_mod = importlib.import_module("dartlab.gather")

    monkeypatch.setattr(dataLoader, "loadData", _mockLoadData)
    monkeypatch.setattr(gather_mod.Gather, "_MACRO_US", ["FEDFUNDS", "GDP"])
    df = gather_mod.getDefaultGather().macro("US")

    assert df.columns == ["date", "FEDFUNDS", "GDP"]
    assert df.height == 2


def test_gather_macro_unknown_hf_series_requires_explicit_api_key(monkeypatch):
    """HF 카탈로그 밖 지표는 apiKey 없이 자동 API fallback 하지 않음."""
    import dartlab.core.dataLoader as dataLoader
    from dartlab.gather import getDefaultGather

    monkeypatch.setattr(dataLoader, "loadData", _mockLoadData)

    with pytest.raises(ValueError, match="apiKey"):
        getDefaultGather().macro("NOT_IN_HF")


def test_gather_macro_api_key_uses_direct_fred_path(monkeypatch):
    """apiKey 명시 시 HF가 아니라 기존 FRED 직접 API facade 사용."""
    import importlib

    fred_mod = importlib.import_module("dartlab.gather.fred")
    from dartlab.gather import getDefaultGather

    class _FakeFred:
        def __init__(self, apiKey=None):
            self.apiKey = apiKey
            self.closed = False

        def series(self, seriesId, **kwargs):
            return pl.DataFrame({"date": ["2024-01-01"], "value": [1.0]}).with_columns(pl.col("date").cast(pl.Date))

        def compare(self, seriesIds, **kwargs):
            return pl.DataFrame({"date": ["2024-01-01"], seriesIds[0]: [1.0]}).with_columns(
                pl.col("date").cast(pl.Date)
            )

        def close(self):
            self.closed = True

    monkeypatch.setattr(fred_mod, "Fred", _FakeFred)
    df = getDefaultGather().macro("US", "FEDFUNDS", apiKey="direct-key")

    assert df["value"].to_list() == [1.0]


def test_fetchMulti_drops_series_with_duplicate_dates(monkeypatch):
    """한 날짜에 값이 여럿인 시리즈는 wide 조합에서 뺀다.

    실측(2026-08-06): CSI 는 하루에 6 값, TRADE 는 4 값이라 date 기준 full join 이 행을
    곱했고, 2026-08-01 한 날짜가 열두 행 넘게 나오면서 멀쩡한 BASE_RATE 와 USDKRW 까지
    같이 복제됐다. 값 하나를 임의로 고르면 조용히 틀린 값을 주므로 빼고 알린다.
    """
    from dartlab.gather.bulkData import macroHf

    def _fake(source, sid, *, start=None, end=None):
        if sid == "MULTI":
            return pl.DataFrame(
                {"date": ["2026-08-01", "2026-08-01", "2026-08-01"], "value": [80.0, 87.0, 96.5]}
            ).with_columns(pl.col("date").cast(pl.Date))
        return pl.DataFrame({"date": ["2026-08-01", "2026-08-02"], "value": [2.75, 2.75]}).with_columns(
            pl.col("date").cast(pl.Date)
        )

    monkeypatch.setattr(macroHf, "fetchSeries", _fake)
    out = macroHf.fetchMulti("ecos", ["BASE_RATE", "MULTI"])

    assert out.columns == ["date", "BASE_RATE"]
    assert out.height == out["date"].n_unique() == 2


def test_fetchMulti_keeps_clean_series_unchanged(monkeypatch):
    """중복이 없으면 옛 동작 그대로다. 정상 경로를 건드리지 않는다."""
    from dartlab.gather.bulkData import macroHf

    def _fake(source, sid, *, start=None, end=None):
        value = 2.75 if sid == "BASE_RATE" else 1424.0
        return pl.DataFrame({"date": ["2026-08-01", "2026-08-02"], "value": [value, value]}).with_columns(
            pl.col("date").cast(pl.Date)
        )

    monkeypatch.setattr(macroHf, "fetchSeries", _fake)
    out = macroHf.fetchMulti("ecos", ["BASE_RATE", "USDKRW"])

    assert out.columns == ["date", "BASE_RATE", "USDKRW"]
    assert out.height == 2


def test_fetchMulti_returns_empty_when_every_series_is_ambiguous(monkeypatch):
    """전부 빠지면 곱한 표 대신 빈 표를 준다. 가짜 행을 만들지 않는다."""
    from dartlab.gather.bulkData import macroHf

    def _fake(source, sid, *, start=None, end=None):
        return pl.DataFrame({"date": ["2026-08-01", "2026-08-01"], "value": [1.0, 2.0]}).with_columns(
            pl.col("date").cast(pl.Date)
        )

    monkeypatch.setattr(macroHf, "fetchSeries", _fake)

    assert macroHf.fetchMulti("ecos", ["CSI", "TRADE"]).is_empty()
