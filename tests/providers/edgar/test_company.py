"""providers/edgar/company.py mirror smoke — P6."""

from datetime import date

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def test_imports():
    try:
        import dartlab.providers.edgar.company  # noqa: F401
    except ImportError as e:
        pytest.skip(f"module import requires data/env: {e}")


def test_ask_callable() -> None:
    """ask() callable smoke."""
    from dartlab.providers.edgar.company import Company

    assert hasattr(Company, "ask")


def test_audit_callable() -> None:
    """audit() callable smoke."""
    from dartlab.providers.edgar.company import Company

    assert hasattr(Company, "audit")


def test_calendar_callable() -> None:
    """calendar() callable smoke."""
    from dartlab.providers.edgar.company import Company

    assert hasattr(Company, "calendar")


def test_can_handle_callable() -> None:
    """canHandle() callable smoke."""
    from dartlab.providers.edgar.company import Company

    assert hasattr(Company, "canHandle")


def test_panel_property_exists() -> None:
    """panel property smoke — DART c.panel 의 EDGAR 미러 진입점."""
    from dartlab.providers.edgar.company import Company

    assert isinstance(getattr(Company, "panel", None), property)


def test_capital_callable() -> None:
    """capital() callable smoke."""
    from dartlab.providers.edgar.company import Company

    assert hasattr(Company, "capital")


def test_causal_weights_callable() -> None:
    """causalWeights() callable smoke."""
    from dartlab.providers.edgar.company import Company

    assert hasattr(Company, "causalWeights")


def test_cleanup_cache_callable() -> None:
    """cleanupCache() callable smoke."""
    from dartlab.providers.edgar.company import Company

    assert hasattr(Company, "cleanupCache")


def test_debt_callable() -> None:
    """debt() callable smoke."""
    from dartlab.providers.edgar.company import Company

    assert hasattr(Company, "debt")


def test_diff_callable() -> None:
    """diff() callable smoke."""
    from dartlab.providers.edgar.company import Company

    assert hasattr(Company, "diff")


def test_disclosure_callable() -> None:
    """disclosure() callable smoke."""
    from dartlab.providers.edgar.company import Company

    assert hasattr(Company, "disclosure")


def test_filings_callable() -> None:
    """filings() callable smoke."""
    from dartlab.providers.edgar.company import Company

    assert hasattr(Company, "filings")


def test_gather_callable() -> None:
    """gather() callable smoke."""
    from dartlab.providers.edgar.company import Company

    assert hasattr(Company, "gather")


def test_governance_callable() -> None:
    """governance() callable smoke."""
    from dartlab.providers.edgar.company import Company

    assert hasattr(Company, "governance")


def test_keyword_trend_callable() -> None:
    """keywordTrend() callable smoke."""
    from dartlab.providers.edgar.company import Company

    assert hasattr(Company, "keywordTrend")


def test_listing_callable() -> None:
    """listing() callable smoke."""
    from dartlab.providers.edgar.company import Company

    assert hasattr(Company, "listing")


def test_live_filings_callable() -> None:
    """liveFilings() callable smoke."""
    from dartlab.providers.edgar.company import Company

    assert hasattr(Company, "liveFilings")


def test_macro_callable() -> None:
    """macro() callable smoke."""
    from dartlab.providers.edgar.company import Company

    assert hasattr(Company, "macro")


def test_memory_snapshot_callable() -> None:
    """memorySnapshot() callable smoke."""
    from dartlab.providers.edgar.company import Company

    assert hasattr(Company, "memorySnapshot")


def test_narrative_diff_callable() -> None:
    """narrativeDiff() callable smoke."""
    from dartlab.providers.edgar.company import Company

    assert hasattr(Company, "narrativeDiff")


def test_news_callable() -> None:
    """news() callable smoke."""
    from dartlab.providers.edgar.company import Company

    assert hasattr(Company, "news")


def test_priority_callable() -> None:
    """priority() callable smoke."""
    from dartlab.providers.edgar.company import Company

    assert hasattr(Company, "priority")


def test_read_filing_callable() -> None:
    """readFiling() callable smoke."""
    from dartlab.providers.edgar.company import Company

    assert hasattr(Company, "readFiling")


def test_refresh_from_api_callable() -> None:
    """refreshFromApi() callable smoke."""
    from dartlab.providers.edgar.company import Company

    assert hasattr(Company, "refreshFromApi")


def test_search_callable() -> None:
    """search() callable smoke."""
    from dartlab.providers.edgar.company import Company

    assert hasattr(Company, "search")


def test_story_tree_callable() -> None:
    """storyTree() callable smoke."""
    from dartlab.providers.edgar.company import Company

    assert hasattr(Company, "storyTree")


def test_table_callable() -> None:
    """table() callable smoke."""
    from dartlab.providers.edgar.company import Company

    assert hasattr(Company, "table")


def test_trace_callable() -> None:
    """trace() callable smoke."""
    from dartlab.providers.edgar.company import Company

    assert hasattr(Company, "trace")


def test_validate_story_callable() -> None:
    """validateStory() callable smoke."""
    from dartlab.providers.edgar.company import Company

    assert hasattr(Company, "validateStory")


def test_valuation_impact_callable() -> None:
    """valuationImpact() callable smoke."""
    from dartlab.providers.edgar.company import Company

    assert hasattr(Company, "valuationImpact")


def test_view_callable() -> None:
    """view() callable smoke."""
    from dartlab.providers.edgar.company import Company

    assert hasattr(Company, "view")


def test_watch_callable() -> None:
    """watch() callable smoke."""
    from dartlab.providers.edgar.company import Company

    assert hasattr(Company, "watch")


def test_workforce_callable() -> None:
    """workforce() callable smoke."""
    from dartlab.providers.edgar.company import Company

    assert hasattr(Company, "workforce")


def test_network_callable() -> None:
    """Company.network() callable smoke."""
    from dartlab.providers.edgar.company import Company

    assert hasattr(Company, "network")


def test_topic_summaries_callable() -> None:
    """Company.topicSummaries() callable smoke."""
    from dartlab.providers.edgar.company import Company

    assert hasattr(Company, "topicSummaries")


def test_update_callable() -> None:
    """Company.update() callable smoke."""
    from dartlab.providers.edgar.company import Company

    assert hasattr(Company, "update")


def test_notes_keys_kr_maps_known_categories_and_preserves_unknown() -> None:
    """표시 라벨은 알려진 카테고리만 번역하고 확장 카테고리는 원본 ID를 보존한다."""
    from types import SimpleNamespace

    from dartlab.providers.edgar.company import _EdgarNotesWrapper
    from dartlab.providers.edgar.docs.notesParsers import CATEGORY_LABELS

    known = next(iter(CATEGORY_LABELS))
    docs = SimpleNamespace(noteCategories=lambda: [known, "future_category"])
    wrapper = _EdgarNotesWrapper(SimpleNamespace(docs=docs))

    assert wrapper.keysKr() == [CATEGORY_LABELS[known], "future_category"]


def test_fiscal_year_end_uses_configured_edgar_directory(tmp_path, monkeypatch) -> None:
    from dartlab.core import dataLoader
    from dartlab.providers.edgar.company import Company

    cik = "0000000001"
    pl.DataFrame(
        {
            "fp": ["FY", "FY", "FY"],
            "fy": [2022, 2023, 2024],
            "end": [date(2022, 9, 24), date(2023, 9, 30), date(2024, 9, 28)],
        }
    ).write_parquet(tmp_path / f"{cik}.parquet")
    monkeypatch.setattr(dataLoader, "_dataDir", lambda category: tmp_path)

    company = Company.__new__(Company)
    company.cik = cik
    company._cache = {}

    assert company.fiscalYearEnd == "09-28"


def test_refresh_from_api_preserves_collection_failure(monkeypatch) -> None:
    from dartlab.core import edgarClient
    from dartlab.providers.edgar.company import Company

    def _failSave(cik, *, client):
        raise OSError("disk full")

    monkeypatch.setattr(edgarClient, "saveFinance", _failSave)
    company = Company.__new__(Company)
    company.cik = "0000000001"
    company._cache = {}

    with pytest.raises(RuntimeError, match=r"cik=0000000001, error=OSError") as excInfo:
        company.refreshFromApi()

    assert isinstance(excInfo.value.__cause__, OSError)


def test_pyodide_ticker_artifact_failure_is_not_unknown_ticker(monkeypatch) -> None:
    """브라우저 ticker artifact 고장을 정상적인 미등록 ticker None으로 위장하지 않는다."""
    from dartlab.core import dataLoader
    from dartlab.providers.edgar import company as companyModule
    from dartlab.providers.edgar.company import Company

    def _failLoad(*_args, **_kwargs):
        raise OSError("ticker artifact corrupt")

    company = Company.__new__(Company)
    monkeypatch.setattr(company, "_getTickerPath", lambda: None)
    monkeypatch.setattr(companyModule.sys, "platform", "emscripten")
    monkeypatch.setattr(dataLoader, "loadData", _failLoad)

    with pytest.raises(OSError, match="ticker artifact corrupt"):
        company._resolveTickerRow("AAPL")


def test_public_company_panel_builds_ifrs_full_finance(tmp_path, monkeypatch) -> None:
    from dartlab.core import dataLoader
    from dartlab.providers.edgar import panel as panelModule
    from dartlab.providers.edgar.company import Company

    cik = "0000000001"
    pl.DataFrame(
        {
            "cik": [cik],
            "entityName": ["Foreign Issuer"],
            "namespace": ["ifrs-full"],
            "tag": ["ProfitLoss"],
            "label": ["Profit loss"],
            "unit": ["USD"],
            "val": [25.0],
            "fy": [2024],
            "fp": ["Q1"],
            "form": ["6-K"],
            "filed": [date(2024, 5, 1)],
            "frame": [None],
            "start": [date(2024, 1, 1)],
            "end": [date(2024, 3, 31)],
            "accn": ["0000000001-24-000001"],
        }
    ).write_parquet(tmp_path / f"{cik}.parquet")
    monkeypatch.setattr(dataLoader, "_dataDir", lambda category: tmp_path)
    monkeypatch.setattr(
        Company,
        "_resolveTickerRow",
        lambda self, ticker: {"ticker": ticker, "cik": cik, "title": "Foreign Issuer"},
    )

    class _PublicPanel:
        def __init__(self, ticker):
            self.ticker = ticker

        def __call__(self, topic, *args, **kwargs):
            return self._showFn(topic, *args, **kwargs)

    monkeypatch.setattr(panelModule, "Panel", _PublicPanel)

    company = Company("TEST")
    result = company.panel("IS")

    assert result is not None
    row = result.filter(pl.col("snakeId") == "net_income")
    assert row.height == 1
    assert row["2024Q1"][0] == pytest.approx(25.0)
