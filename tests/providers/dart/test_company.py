"""providers/dart/company.py mirror smoke — P6."""

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def test_imports():
    try:
        import dartlab.providers.dart.company  # noqa: F401
    except ImportError as e:
        pytest.skip(f"module import requires data/env: {e}")


def test_ask_callable() -> None:
    """ask() callable smoke."""
    from dartlab.providers.dart.company import Company

    assert hasattr(Company, "ask")


def test_audit_callable() -> None:
    """audit() callable smoke."""
    from dartlab.providers.dart.company import Company

    assert hasattr(Company, "audit")


def test_calendar_callable() -> None:
    """calendar() callable smoke."""
    from dartlab.providers.dart.company import Company

    assert hasattr(Company, "calendar")


def test_can_handle_callable() -> None:
    """canHandle() callable smoke."""
    from dartlab.providers.dart.company import Company

    assert hasattr(Company, "canHandle")


def test_capital_callable() -> None:
    """capital() callable smoke."""
    from dartlab.providers.dart.company import Company

    assert hasattr(Company, "capital")


def test_causal_weights_callable() -> None:
    """causalWeights() callable smoke."""
    from dartlab.providers.dart.company import Company

    assert hasattr(Company, "causalWeights")


def test_cleanup_cache_callable() -> None:
    """cleanupCache() callable smoke."""
    from dartlab.providers.dart.company import Company

    assert hasattr(Company, "cleanupCache")


def test_code_name_callable() -> None:
    """codeName() callable smoke."""
    from dartlab.providers.dart.company import Company

    assert hasattr(Company, "codeName")


def test_debt_callable() -> None:
    """debt() callable smoke."""
    from dartlab.providers.dart.company import Company

    assert hasattr(Company, "debt")


def test_diff_callable() -> None:
    """diff() callable smoke."""
    from dartlab.providers.dart.company import Company

    assert hasattr(Company, "diff")


def test_disclosure_callable() -> None:
    """disclosure() callable smoke."""
    from dartlab.providers.dart.company import Company

    assert hasattr(Company, "disclosure")


def test_filings_callable() -> None:
    """filings() callable smoke."""
    from dartlab.providers.dart.company import Company

    assert hasattr(Company, "filings")


def test_gather_callable() -> None:
    """gather() callable smoke."""
    from dartlab.providers.dart.company import Company

    assert hasattr(Company, "gather")


def test_governance_callable() -> None:
    """governance() callable smoke."""
    from dartlab.providers.dart.company import Company

    assert hasattr(Company, "governance")


def test_industry_callable() -> None:
    """industry() callable smoke."""
    from dartlab.providers.dart.company import Company

    assert hasattr(Company, "industry")


def test_keyword_trend_callable() -> None:
    """keywordTrend() callable smoke."""
    from dartlab.providers.dart.company import Company

    assert hasattr(Company, "keywordTrend")


def test_listing_callable() -> None:
    """listing() callable smoke."""
    from dartlab.providers.dart.company import Company

    assert hasattr(Company, "listing")


def test_live_filings_callable() -> None:
    """liveFilings() callable smoke."""
    from dartlab.providers.dart.company import Company

    assert hasattr(Company, "liveFilings")


def test_macro_callable() -> None:
    """macro() callable smoke."""
    from dartlab.providers.dart.company import Company

    assert hasattr(Company, "macro")


def test_memory_snapshot_callable() -> None:
    """memorySnapshot() callable smoke."""
    from dartlab.providers.dart.company import Company

    assert hasattr(Company, "memorySnapshot")


def test_narrative_diff_callable() -> None:
    """narrativeDiff() callable smoke."""
    from dartlab.providers.dart.company import Company

    assert hasattr(Company, "narrativeDiff")


def test_network_callable() -> None:
    """network() callable smoke."""
    from dartlab.providers.dart.company import Company

    assert hasattr(Company, "network")


def test_news_callable() -> None:
    """news() callable smoke."""
    from dartlab.providers.dart.company import Company

    assert hasattr(Company, "news")


def test_panel_property() -> None:
    """panel property — 공시 수평화 보드 facade 연결 (c.panel → Panel)."""
    import inspect

    from dartlab.providers.dart.company import Company

    assert isinstance(inspect.getattr_static(Company, "panel"), property)


def test_panel_routes_structured_report_through_company_facade(monkeypatch: pytest.MonkeyPatch) -> None:
    """정형 report는 private accessor에 갇히지 않고 공개 panel에서 조회된다."""
    from types import SimpleNamespace

    from dartlab.core.memory import BoundedCache
    from dartlab.providers.dart import panel as panelModule
    from dartlab.providers.dart.accessor import reportAccessor
    from dartlab.providers.dart.company import Company

    seen: dict[str, object] = {}
    expected = pl.DataFrame({"항목": ["현금배당금"], "2024": [1446.0]})

    class PublicPanel:
        def __init__(self, code: str, *, marketNs: str):
            seen["code"] = code
            seen["marketNs"] = marketNs

        def __call__(self, topic: str, **kwargs):
            return self._showFn(topic, **kwargs) if self._strongFn(topic) else None

    def reportFrame(stockCode: str, apiType: str, topic: str, *, raw: bool = False):
        seen.update(stockCode=stockCode, apiType=apiType, topic=topic, raw=raw)
        return expected

    monkeypatch.setattr(panelModule, "Panel", PublicPanel)
    monkeypatch.setattr(reportAccessor, "reportFrameInner", reportFrame)

    company = Company.__new__(Company)
    company.stockCode = "005930"
    company._report = SimpleNamespace(apiTypes=["dividend"])
    company._cache = BoundedCache(memorySampler=lambda: 0.0)

    panel = company.panel
    result = panel("dividend", period="2024")

    assert result is not None and result.equals(expected)
    assert company.panel is panel
    assert seen == {
        "code": "005930",
        "marketNs": "kr",
        "stockCode": "005930",
        "apiType": "dividend",
        "topic": "dividend",
        "raw": False,
    }


def test_finance_artifact_failure_is_not_docs_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """finance 손상을 단순 미수집으로 바꿔 docs 수치에 조용히 폴백하지 않는다."""
    from dartlab.providers.dart.company import Company
    from dartlab.providers.dart.finance import pivot

    def failBuild(_stockCode):
        raise ValueError("finance parquet corrupt")

    monkeypatch.setattr(pivot, "buildTimeseries", failBuild)
    company = Company.__new__(Company)
    company.stockCode = "005930"
    company._financeChecked = False
    company._hasFinanceParquet = True

    with pytest.raises(RuntimeError, match="stockCode=005930") as excInfo:
        company._ensureFinanceLoaded()

    assert isinstance(excInfo.value.__cause__, ValueError)
    assert company._financeChecked is False
    assert company._hasFinanceParquet is True


def test_priority_callable() -> None:
    """priority() callable smoke."""
    from dartlab.providers.dart.company import Company

    assert hasattr(Company, "priority")


def test_read_filing_callable() -> None:
    """readFiling() callable smoke."""
    from dartlab.providers.dart.company import Company

    assert hasattr(Company, "readFiling")


def test_resolve_callable() -> None:
    """resolve() callable smoke."""
    from dartlab.providers.dart.company import Company

    assert hasattr(Company, "resolve")


def test_search_callable() -> None:
    """search() callable smoke."""
    from dartlab.providers.dart.company import Company

    assert hasattr(Company, "search")


def test_status_callable() -> None:
    """status() callable smoke."""
    from dartlab.providers.dart.company import Company

    assert hasattr(Company, "status")


def test_story_tree_callable() -> None:
    """storyTree() callable smoke."""
    from dartlab.providers.dart.company import Company

    assert hasattr(Company, "storyTree")


def test_table_callable() -> None:
    """table() callable smoke."""
    from dartlab.providers.dart.company import Company

    assert hasattr(Company, "table")


def test_topic_summaries_callable() -> None:
    """topicSummaries() callable smoke."""
    from dartlab.providers.dart.company import Company

    assert hasattr(Company, "topicSummaries")


def test_trace_callable() -> None:
    """trace() callable smoke."""
    from dartlab.providers.dart.company import Company

    assert hasattr(Company, "trace")


def test_update_callable() -> None:
    """update() callable smoke."""
    from dartlab.providers.dart.company import Company

    assert hasattr(Company, "update")


def test_validate_story_callable() -> None:
    """validateStory() callable smoke."""
    from dartlab.providers.dart.company import Company

    assert hasattr(Company, "validateStory")


def test_valuation_impact_callable() -> None:
    """valuationImpact() callable smoke."""
    from dartlab.providers.dart.company import Company

    assert hasattr(Company, "valuationImpact")


def test_view_callable() -> None:
    """view() callable smoke."""
    from dartlab.providers.dart.company import Company

    assert hasattr(Company, "view")


def test_watch_callable() -> None:
    """watch() callable smoke."""
    from dartlab.providers.dart.company import Company

    assert hasattr(Company, "watch")


def test_workforce_callable() -> None:
    """workforce() callable smoke."""
    from dartlab.providers.dart.company import Company

    assert hasattr(Company, "workforce")


def test_code_to_name_callable() -> None:
    """codeToName() callable smoke."""
    from dartlab.providers.dart.company import codeToName

    assert callable(codeToName)


def test_get_kind_list_callable() -> None:
    """getKindList() callable smoke."""
    from dartlab.providers.dart.company import getKindList

    assert callable(getKindList)


def test_iter_export_modules_callable() -> None:
    """iterExportModules() callable smoke."""
    from dartlab.providers.dart.company import iterExportModules

    assert callable(iterExportModules)


def test_iter_name_callable() -> None:
    """iterName() callable smoke."""
    from dartlab.providers.dart.company import iterName

    assert callable(iterName)


def test_list_export_modules_callable() -> None:
    """listExportModules() callable smoke."""
    from dartlab.providers.dart.company import listExportModules

    assert callable(listExportModules)


def test_name_to_code_callable() -> None:
    """nameToCode() callable smoke."""
    from dartlab.providers.dart.company import nameToCode

    assert callable(nameToCode)


def test_rebuild_module_registry_callable() -> None:
    """rebuildModuleRegistry() callable smoke."""
    from dartlab.providers.dart.company import rebuildModuleRegistry

    assert callable(rebuildModuleRegistry)


def test_search_name_callable() -> None:
    """searchName() callable smoke."""
    from dartlab.providers.dart.company import searchName

    assert callable(searchName)
