from __future__ import annotations

from types import SimpleNamespace

import polars as pl
import pytest

from dartlab.ai.context import build_compact_context, build_context_by_module
from dartlab.ai.context.builder import _resolve_context_route
from dartlab.ai.context.finance_context import _detect_year_hint
from dartlab.ai.runtime.core import (
    _resolve_context_tier,
    _resolve_follow_up_include,
    _resolve_snapshot_policy,
    _should_run_validation,
    _should_use_light_mode,
)
from dartlab.core.memory import BoundedCache
from dartlab.providers.dart._docs_accessor import _DocsAccessor
from dartlab.providers.dart.company import Company

pytestmark = pytest.mark.unit


class _FakeRatioResult:
    def __init__(self):
        self.roe = 11.2
        self.debtRatio = 58.4
        self.currentRatio = 142.0
        self.operatingMargin = 16.8
        self.fcf = 9000
        self.revenueGrowth3Y = 7.5


def _bare_company(*, has_docs: bool = True, has_finance: bool = False, has_report: bool = False) -> Company:
    company = Company.__new__(Company)
    company.stockCode = "000000"
    company.corpName = "테스트기업"
    company._cache = BoundedCache(max_entries=30)
    company._hasDocs = has_docs
    company._hasFinanceParquet = has_finance
    company._hasReport = has_report
    company._financeChecked = True
    company._notesAccessor = None
    company.docs = _DocsAccessor(company)
    company.finance = SimpleNamespace()
    company.report = SimpleNamespace()
    company._profileAccessor = None
    return company


def _project(df: pl.DataFrame, columns: list[str] | None) -> pl.DataFrame:
    if not columns:
        return df
    available = [column for column in columns if column in df.columns]
    return df.select(available) if available else pl.DataFrame()


def test_sections_topics_and_outline_use_lightweight_manifest(monkeypatch):
    docs_df = pl.DataFrame(
        {
            "year": ["2024", "2024", "2023", "2023"],
            "report_type": [
                "사업보고서 (2024.12)",
                "사업보고서 (2024.12)",
                "사업보고서 (2023.12)",
                "사업보고서 (2023.12)",
            ],
            "rcept_date": ["2025-03-01", "2025-03-01", "2024-03-01", "2024-03-01"],
            "section_order": [10, 20, 10, 20],
            "section_title": ["II. 사업 개요", "IV. 리스크 요약", "II. 사업 개요", "IV. 리스크 요약"],
            "content": [
                "가. 사업 내용\n반도체와 배터리",
                "시장 리스크와 환율 변동",
                "가. 사업 내용\n메모리와 소재",
                "전년 리스크",
            ],
        }
    )

    def fake_load_data(stockCode: str, category: str = "docs", **kwargs):
        assert stockCode == "000000"
        if category == "docs":
            return _project(docs_df, kwargs.get("columns"))
        raise AssertionError(f"unexpected category: {category}")

    def fake_map_section_title(title: str) -> str:
        if "사업" in title:
            return "businessOverview"
        if "리스크" in title:
            return "riskDerivative"
        return title

    monkeypatch.setattr("dartlab.providers.dart.company.loadData", fake_load_data)
    monkeypatch.setattr("dartlab.core.dataLoader.loadData", fake_load_data)
    monkeypatch.setattr("dartlab.providers.dart.docs.sections.mapper.mapSectionTitle", fake_map_section_title)

    company = _bare_company(has_docs=True)

    topics = company.docs.sections.topics()
    manifest = company.docs.sections.outline()
    outline = company.docs.sections.outline("businessOverview")

    assert topics == ["businessOverview", "riskDerivative"]
    assert isinstance(manifest, pl.DataFrame)
    assert {"order", "chapter", "topic", "blocks", "periods", "latestPeriod"}.issubset(set(manifest.columns))
    assert isinstance(outline, pl.DataFrame)
    assert {"period", "sectionOrder", "block", "type", "title", "preview"}.issubset(set(outline.columns))
    assert outline["period"].to_list() == ["2024", "2023"]
    assert "sections" not in company._cache._store
    assert "_sections" not in company._cache._store


def test_company_topics_combines_docs_manifest_and_finance_summary_without_sections(monkeypatch):
    docs_df = pl.DataFrame(
        {
            "year": ["2024"],
            "report_type": ["사업보고서 (2024.12)"],
            "rcept_date": ["2025-03-01"],
            "section_order": [10],
            "section_title": ["II. 사업 개요"],
            "content": ["반도체와 배터리"],
        }
    )
    finance_df = pl.DataFrame({"bsns_year": ["2022", "2023", "2024"]})

    def fake_load_data(stockCode: str, category: str = "docs", **kwargs):
        assert stockCode == "000000"
        if category == "docs":
            return _project(docs_df, kwargs.get("columns"))
        if category == "finance":
            return _project(finance_df, kwargs.get("columns"))
        raise AssertionError(f"unexpected category: {category}")

    monkeypatch.setattr("dartlab.providers.dart.company.loadData", fake_load_data)
    monkeypatch.setattr("dartlab.core.dataLoader.loadData", fake_load_data)
    monkeypatch.setattr("dartlab.providers.dart.docs.sections.mapper.mapSectionTitle", lambda title: "businessOverview")

    company = _bare_company(has_docs=True, has_finance=True)

    topics = company.topics

    assert isinstance(topics, pl.DataFrame)
    assert "businessOverview" in topics["topic"].to_list()
    assert "BS" in topics["topic"].to_list()
    assert "ratios" in topics["topic"].to_list()
    assert "sections" not in company._cache._store
    assert "_sections" not in company._cache._store


def test_get_finance_build_reuses_quarter_series(monkeypatch):
    calls = {"q": 0, "y": 0, "cum": 0}

    def fake_build_timeseries(stockCode: str, fsDivPref: str = "CFS"):
        assert stockCode == "000000"
        assert fsDivPref == "CFS"
        calls["q"] += 1
        return ({"IS": {}, "BS": {}, "CF": {}}, ["2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4"])

    def fake_aggregate_annual(series: dict, periods: list[str]):
        calls["y"] += 1
        return (series, ["2024"])

    def fake_aggregate_cumulative(series: dict, periods: list[str]):
        calls["cum"] += 1
        return (series, periods)

    monkeypatch.setattr("dartlab.providers.dart.finance.pivot.buildTimeseries", fake_build_timeseries)
    monkeypatch.setattr("dartlab.providers.dart.finance.pivot._aggregateAnnual", fake_aggregate_annual)
    monkeypatch.setattr("dartlab.providers.dart.finance.pivot._aggregateCumulative", fake_aggregate_cumulative)

    company = _bare_company(has_docs=False, has_finance=True)

    assert company._getFinanceBuild("y") is not None
    assert company._getFinanceBuild("cum") is not None
    assert company._getFinanceBuild("q") is not None
    assert calls == {"q": 1, "y": 1, "cum": 1}


def test_insights_uses_prebuilt_finance_series(monkeypatch):
    q_pair = ({"IS": {}, "BS": {}, "CF": {}}, ["2024-Q4"])
    a_pair = ({"IS": {}, "BS": {}, "CF": {}}, ["2024"])
    captured: dict[str, object] = {}

    def fake_analyze(stockCode: str, **kwargs):
        captured["stockCode"] = stockCode
        captured.update(kwargs)
        return "analysis-ok"

    monkeypatch.setattr("dartlab.analysis.financial.insight.analyze", fake_analyze)

    company = _bare_company(has_docs=False, has_finance=True)
    company.finance = SimpleNamespace(timeseries=q_pair, annual=a_pair)

    assert company.insights == "analysis-ok"
    assert captured["stockCode"] == "000000"
    assert captured["qSeriesPair"] == q_pair
    assert captured["aSeriesPair"] == a_pair


def test_finance_question_avoids_docs_and_report_paths():
    class FinanceOnlyCompany:
        corpName = "테스트기업"
        stockCode = "000000"
        _hasDocs = False
        sector = SimpleNamespace(sector=None)
        annual = (
            {
                "IS": {"sales": [100.0, 110.0, 120.0], "operating_profit": [10.0, 15.0, 18.0]},
                "BS": {"total_assets": [200.0, 210.0, 220.0]},
                "CF": {"operating_cashflow": [5.0, 7.0, 9.0]},
            },
            ["2022", "2023", "2024"],
        )
        timeseries = (
            {"IS": {}, "BS": {}, "CF": {}},
            ["2022-Q1", "2022-Q2", "2022-Q3", "2022-Q4", "2023-Q1", "2023-Q2", "2023-Q3", "2023-Q4"],
        )

        @property
        def docs(self):
            raise AssertionError("finance route should not access docs")

        @property
        def report(self):
            raise AssertionError("finance route should not access report")

        def getRatios(self):
            return _FakeRatioResult()

    modules, included, _ = build_context_by_module(FinanceOnlyCompany(), "영업이익률 추세를 분석해줘", compact=True)

    assert "IS" in included
    assert "ratios" in included
    assert "businessOverview" not in included
    assert "_insights" not in included
    assert "IS" in modules


def test_sections_question_avoids_finance_and_report_paths():
    class FakeSectionsAccessor:
        def outline(self, topic: str | None = None):
            if topic is None:
                return pl.DataFrame(
                    {
                        "order": [10, 20],
                        "chapter": ["II", "IV"],
                        "topic": ["businessOverview", "riskDerivative"],
                        "source": ["docs", "docs"],
                        "blocks": [1, 1],
                        "periods": [2, 2],
                        "latestPeriod": ["2024", "2024"],
                    }
                )
            if topic == "businessOverview":
                return pl.DataFrame(
                    {
                        "period": ["2024", "2023"],
                        "sectionOrder": [10, 10],
                        "block": [0, 0],
                        "type": ["text", "text"],
                        "title": ["사업 개요", "사업 개요"],
                        "preview": ["반도체와 배터리", "메모리와 소재"],
                    }
                )
            return pl.DataFrame()

        def topics(self):
            return ["businessOverview", "riskDerivative"]

    class SectionsOnlyCompany:
        corpName = "테스트기업"
        stockCode = "000000"
        _hasDocs = True
        docs = SimpleNamespace(sections=FakeSectionsAccessor())

        @property
        def annual(self):
            raise AssertionError("sections route should not access annual finance")

        @property
        def report(self):
            raise AssertionError("sections route should not access report")

        def getRatios(self):
            raise AssertionError("sections route should not access ratios")

        def _topicLabel(self, topic: str) -> str:
            return {"businessOverview": "사업의 개요", "riskDerivative": "리스크"}.get(topic, topic)

        def show(self, topic: str, block: int | None = None):
            if block is None:
                return pl.DataFrame(
                    {
                        "block": [0],
                        "type": ["text"],
                        "source": ["docs"],
                        "preview": ["반도체와 배터리"],
                    }
                )
            return pl.DataFrame({"내용": ["반도체와 배터리"]})

    modules, included, _ = build_context_by_module(SectionsOnlyCompany(), "무슨 사업 하는 회사냐", compact=True)

    assert "businessOverview" in included
    assert "ratios" not in included
    assert "section_businessOverview" in modules


def test_sections_question_compact_mode_uses_outline_preview_without_raw():
    class FakeSectionsAccessor:
        def outline(self, topic: str | None = None):
            if topic is None:
                return pl.DataFrame(
                    {
                        "order": [10],
                        "chapter": ["II"],
                        "topic": ["businessOverview"],
                        "source": ["docs"],
                        "blocks": [1],
                        "periods": [2],
                        "latestPeriod": ["2024"],
                    }
                )
            return pl.DataFrame(
                {
                    "period": ["2024", "2023"],
                    "sectionOrder": [10, 10],
                    "block": [0, 0],
                    "type": ["text", "text"],
                    "title": ["사업 개요", "사업 개요"],
                    "preview": ["반도체와 배터리", "메모리와 소재"],
                }
            )

        def topics(self):
            return ["businessOverview"]

        @property
        def raw(self):
            raise AssertionError("compact sections route should not access raw sections")

    class SectionsOnlyCompany:
        corpName = "테스트기업"
        stockCode = "000000"
        _hasDocs = True
        docs = SimpleNamespace(sections=FakeSectionsAccessor())

        @property
        def annual(self):
            raise AssertionError("sections route should not access annual finance")

        def getRatios(self):
            raise AssertionError("sections route should not access ratios")

        def _topicLabel(self, topic: str) -> str:
            return {"businessOverview": "사업의 개요"}.get(topic, topic)

    modules, included, _ = build_context_by_module(SectionsOnlyCompany(), "무슨 사업 하는 회사냐", compact=True)

    assert "businessOverview" in included
    assert "핵심 preview" in modules["section_businessOverview"]


def test_build_compact_context_includes_section_and_report_prefixed_modules():
    class FakeSectionsAccessor:
        def outline(self, topic: str | None = None):
            if topic is None:
                return pl.DataFrame(
                    {
                        "order": [10],
                        "chapter": ["II"],
                        "topic": ["businessOverview"],
                        "source": ["docs"],
                        "blocks": [1],
                        "periods": [1],
                        "latestPeriod": ["2024"],
                    }
                )
            return pl.DataFrame(
                {
                    "period": ["2024"],
                    "sectionOrder": [10],
                    "block": [0],
                    "type": ["text"],
                    "title": ["사업 개요"],
                    "preview": ["반도체와 배터리"],
                }
            )

        def topics(self):
            return ["businessOverview"]

    class FakeDividend:
        years = [2023, 2024]
        dps = [1444.0, 1446.0]
        dividendYield = [1.9, 2.7]

    class CompactContextCompany:
        corpName = "테스트기업"
        stockCode = "000000"
        _hasDocs = True
        docs = SimpleNamespace(sections=FakeSectionsAccessor())
        report = SimpleNamespace(dividend=FakeDividend())

        @property
        def annual(self):
            raise AssertionError("compact section/report context should not access annual finance")

        def _topicLabel(self, topic: str) -> str:
            return "사업의 개요"

    section_text, section_included = build_compact_context(CompactContextCompany(), "무슨 사업 하는 회사냐")
    dividend_text, dividend_included = build_compact_context(CompactContextCompany(), "배당 추세 알려줘")

    assert "businessOverview" in section_included
    assert "반도체와 배터리" in section_text
    assert "dividend" in dividend_included
    assert "DPS(원)" in dividend_text


def test_direct_cost_question_prefers_cost_by_nature_without_summary_module():
    class DirectCostCompany:
        corpName = "테스트기업"
        stockCode = "000000"
        _hasDocs = False
        sector = SimpleNamespace(sector=None)

        @property
        def annual(self):
            raise AssertionError("direct cost question should not access annual finance")

        @property
        def report(self):
            raise AssertionError("direct cost question should not access report")

        def getRatios(self):
            raise AssertionError("direct cost question should not access ratios")

        def _get_primary(self, name: str):
            if name == "costByNature":
                return pl.DataFrame({"account": ["급여", "감가상각비"], "2024": [100.0, 80.0]})
            if name == "fsSummary":
                raise AssertionError("specific module question should not pull fsSummary by default")
            return None

    modules, included, _ = build_context_by_module(
        DirectCostCompany(),
        "성격별 비용 분류를 보여줘",
        compact=True,
    )

    assert included == ["costByNature"]
    assert "costByNature" in modules
    assert "_response_contract" in modules


def test_sections_evidence_contract_requires_exact_period_and_no_tool_narration():
    class FakeSectionsAccessor:
        def outline(self, topic: str | None = None):
            if topic is None:
                return pl.DataFrame(
                    {
                        "order": [10],
                        "chapter": ["II"],
                        "topic": ["businessOverview"],
                        "source": ["docs"],
                        "blocks": [1],
                        "periods": [2],
                        "latestPeriod": ["2024"],
                    }
                )
            return pl.DataFrame(
                {
                    "period": ["2024", "2023"],
                    "sectionOrder": [10, 10],
                    "block": [0, 0],
                    "type": ["text", "text"],
                    "title": ["사업 개요", "사업 개요"],
                    "preview": ["반도체와 배터리", "메모리와 소재"],
                }
            )

        def topics(self):
            return ["businessOverview"]

    class EvidenceCompany:
        corpName = "테스트기업"
        stockCode = "000000"
        _hasDocs = True
        docs = SimpleNamespace(sections=FakeSectionsAccessor())

        @property
        def annual(self):
            raise AssertionError("sections evidence question should not access annual finance")

        def getRatios(self):
            raise AssertionError("sections evidence question should not access ratios")

        def _topicLabel(self, topic: str) -> str:
            return "사업의 개요"

    modules, included, _ = build_context_by_module(
        EvidenceCompany(),
        "최근 공시 기준으로 사업구조 설명 근거를 2개만 짚어줘",
        compact=True,
    )

    assert included == ["businessOverview"]
    assert "period: 2024" in modules["section_businessOverview"]
    assert "_response_contract" in modules
    assert "도구 호출 계획" in modules["_response_contract"]
    assert "실제 값을 쓰세요" in modules["_response_contract"]


def test_ambiguous_cost_question_emits_single_clarification_without_loading_summary():
    class AmbiguousCostCompany:
        corpName = "테스트기업"
        stockCode = "000000"
        _hasDocs = False
        sector = SimpleNamespace(sector=None)

        @property
        def annual(self):
            raise AssertionError("ambiguous clarification should not access annual finance")

        def _get_primary(self, name: str):
            if name == "costByNature":
                return pl.DataFrame({"account": ["급여"], "2024": [100.0]})
            if name == "fsSummary":
                raise AssertionError("ambiguous clarification should not pull fsSummary")
            return None

    modules, included, _ = build_context_by_module(
        AmbiguousCostCompany(),
        "비용 구조를 설명해줘",
        compact=True,
    )

    assert included == []
    assert "_clarify" in modules
    assert "한 문장만" in modules["_clarify"]


def test_distress_question_forces_finance_route():
    route = _resolve_context_route("삼성SDI의 부실 징후를 지금 시점에서 점검해줘", include=None, q_types=[])
    assert route == "finance"


def test_margin_driver_question_forces_hybrid_without_clarification():
    class MarginSectionsAccessor:
        def outline(self, topic: str | None = None):
            if topic is None:
                return pl.DataFrame(
                    {
                        "order": [10, 20],
                        "chapter": ["II", "II"],
                        "topic": ["businessOverview", "productService"],
                        "source": ["docs", "docs"],
                        "blocks": [1, 1],
                        "periods": [2, 2],
                        "latestPeriod": ["2024", "2024"],
                    }
                )
            return pl.DataFrame(
                {
                    "period": ["2024", "2023"],
                    "sectionOrder": [10, 10],
                    "block": [0, 0],
                    "type": ["text", "text"],
                    "title": ["사업 개요", "사업 개요"],
                    "preview": ["반도체 비중 확대", "메모리 중심"],
                }
            )

        def topics(self):
            return ["businessOverview", "productService"]

    class MarginDriverCompany:
        corpName = "테스트기업"
        stockCode = "000000"
        _hasDocs = True
        docs = SimpleNamespace(sections=MarginSectionsAccessor())
        sector = SimpleNamespace(sector=None)

        @property
        def annual(self):
            series = {
                "IS": {
                    "sales": [1000.0, 1200.0],
                    "cost_of_sales": [700.0, 820.0],
                    "gross_profit": [300.0, 380.0],
                    "selling_and_administrative_expenses": [120.0, 150.0],
                    "operating_profit": [180.0, 230.0],
                    "net_profit": [150.0, 190.0],
                }
            }
            return series, ["2023", "2024"]

        @property
        def timeseries(self):
            return ({}, ["2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4"])

        def getRatios(self):
            return _FakeRatioResult()

        def _get_primary(self, name: str):
            if name == "costByNature":
                return pl.DataFrame({"account": ["급여", "감가상각비"], "2024": [100.0, 80.0]})
            return None

        def _topicLabel(self, topic: str) -> str:
            return {"businessOverview": "사업의 개요", "productService": "제품·서비스"}.get(topic, topic)

    modules, included, _ = build_context_by_module(
        MarginDriverCompany(),
        "삼성전자 영업이익률 변동을 비용 구조와 사업 변화까지 묶어서 설명해줘",
        compact=True,
    )

    assert "IS" in included
    assert "costByNature" in included
    assert "businessOverview" in included
    assert "_clarify" not in modules
    assert "손익계산서/재무상태표/현금흐름표/재무비율" in modules["_response_contract"]


def test_recent_disclosure_business_change_adds_business_overview_context():
    class RecentSectionsAccessor:
        def outline(self, topic: str | None = None):
            if topic is None:
                return pl.DataFrame(
                    {
                        "order": [10, 20, 30],
                        "chapter": ["II", "III", "III"],
                        "topic": ["businessOverview", "disclosureChanges", "productService"],
                        "source": ["docs", "docs", "docs"],
                        "blocks": [1, 1, 1],
                        "periods": [2, 2, 2],
                        "latestPeriod": ["2024", "2024", "2024"],
                    }
                )
            return pl.DataFrame(
                {
                    "period": ["2024", "2023"],
                    "sectionOrder": [10, 10],
                    "block": [0, 0],
                    "type": ["text", "text"],
                    "title": ["변화 요약", "변화 요약"],
                    "preview": ["사업 구조 일부 조정", "전년 구조 유지"],
                }
            )

        def topics(self):
            return ["businessOverview", "disclosureChanges", "productService"]

    class RecentBusinessChangeCompany:
        corpName = "테스트기업"
        stockCode = "000000"
        _hasDocs = True
        docs = SimpleNamespace(sections=RecentSectionsAccessor())

        @property
        def annual(self):
            raise AssertionError("recent disclosure structure question should not access annual finance")

        @property
        def report(self):
            raise AssertionError("recent disclosure structure question should not access report")

        def getRatios(self):
            raise AssertionError("recent disclosure structure question should not access ratios")

        def _topicLabel(self, topic: str) -> str:
            return {
                "businessOverview": "사업의 개요",
                "disclosureChanges": "공시 변화",
                "productService": "제품·서비스",
            }.get(topic, topic)

    modules, included, _ = build_context_by_module(
        RecentBusinessChangeCompany(),
        "최근 공시 기준으로 삼성전자 사업 구조가 바뀐 부분이 있나",
        compact=True,
    )

    assert included[:2] == ["disclosureChanges", "businessOverview"]
    assert "_clarify" not in modules


def test_sections_context_uses_context_slices_as_primary_evidence():
    class SliceSectionsAccessor:
        def outline(self, topic: str | None = None):
            if topic is None:
                return pl.DataFrame(
                    {
                        "order": [10, 20],
                        "chapter": ["II", "III"],
                        "topic": ["businessOverview", "disclosureChanges"],
                        "source": ["docs", "docs"],
                        "blocks": [1, 1],
                        "periods": [2, 2],
                        "latestPeriod": ["2024", "2024"],
                    }
                )
            return pl.DataFrame(
                {
                    "period": ["2024", "2023"],
                    "sectionOrder": [10, 10],
                    "block": [0, 0],
                    "type": ["text", "text"],
                    "title": ["사업 개요", "사업 개요"],
                    "preview": ["preview fallback", "older preview"],
                }
            )

        def topics(self):
            return ["businessOverview", "disclosureChanges"]

    class SliceEvidenceCompany:
        corpName = "테스트기업"
        stockCode = "000000"
        _hasDocs = True
        sector = SimpleNamespace(sector=None)
        docs = SimpleNamespace(
            sections=SliceSectionsAccessor(),
            contextSlices=pl.DataFrame(
                {
                    "topic": ["businessOverview", "disclosureChanges"],
                    "sourceTopic": ["사업의 개요", "공시 변화"],
                    "semanticTopic": [None, None],
                    "detailTopic": [None, None],
                    "period": ["2024", "2024"],
                    "periodOrder": [2024, 2024],
                    "blockType": ["text", "text"],
                    "sliceIdx": [0, 0],
                    "sliceText": ["낸드 사업부 재편과 AI 메모리 확대를 명시", "HBM 중심 투자 확대를 공시에서 언급"],
                    "blockPriority": [5, 5],
                    "isTable": [False, False],
                }
            ),
        )

        def _topicLabel(self, topic: str) -> str:
            return {
                "businessOverview": "사업의 개요",
                "disclosureChanges": "공시 변화",
            }.get(topic, topic)

    modules, included, _ = build_context_by_module(
        SliceEvidenceCompany(),
        "최근 공시 기준으로 사업 구조 변화 근거를 보여줘",
        compact=True,
    )

    assert included[:2] == ["disclosureChanges", "businessOverview"]
    assert "HBM 중심 투자 확대" in modules["section_disclosureChanges"]
    assert "낸드 사업부 재편" in modules["section_businessOverview"]
    assert "시점: 2024" in modules["section_businessOverview"]


def test_direct_module_context_limits_recent_periods_for_cost_by_nature():
    class CostCompany:
        corpName = "테스트기업"
        stockCode = "000000"
        _hasDocs = False
        sector = SimpleNamespace(sector=None)

        def _get_primary(self, name: str):
            if name == "costByNature":
                return pl.DataFrame(
                    {
                        "account": ["원재료사용", "종업원급여"],
                        "2024": [10.0, 5.0],
                        "2023": [9.0, 4.0],
                        "2022": [8.0, 3.0],
                        "2021": [7.0, 2.0],
                        "2020": [6.0, 1.0],
                        "2019": [5.0, 0.5],
                    }
                )
            return None

    modules, included, _ = build_context_by_module(
        CostCompany(),
        "하이닉스 비용의 성격별분류 현황좀줘",
        compact=True,
    )

    assert included == ["costByNature"]
    assert "2024" in modules["costByNature"]
    assert "2020" in modules["costByNature"]
    assert "2019" not in modules["costByNature"]
    assert "연도 기준을 다시 묻지 마세요" in modules["_response_contract"]


def test_follow_up_period_question_inherits_previous_modules():
    state = SimpleNamespace(dialogue_mode="follow_up", modules=("costByNature",))

    assert _resolve_follow_up_include(None, "최근 5개년", state) == ["costByNature"]
    assert _resolve_follow_up_include(None, "애플은 어떤 회사야?", state) is None


def test_detect_year_hint_prefers_explicit_range_over_recent_keyword():
    assert _detect_year_hint("최근 5개년") == 5
    assert _detect_year_hint("최근 10년 추세") == 10


def test_resolve_context_tier_defaults_to_focused_for_default_ask():
    assert _resolve_context_tier("oauth-codex", use_tools=False) == "focused"
    assert _resolve_context_tier("openai", use_tools=False) == "focused"
    assert _resolve_context_tier("openai", use_tools=True) == "skeleton"


def test_resolve_snapshot_policy_skips_sections_and_report_routes():
    finance_policy = _resolve_snapshot_policy("영업이익률 추세를 분석해줘", (), False)
    sections_policy = _resolve_snapshot_policy("무슨 사업 하는 회사냐", (), False)
    report_policy = _resolve_snapshot_policy("배당 추세 알려줘", (), False)

    assert finance_policy["route"] == "finance"
    assert finance_policy["enabled"] is True
    assert finance_policy["includeInsights"] is False
    assert finance_policy["includeDataDate"] is False

    assert sections_policy["route"] == "sections"
    assert sections_policy["enabled"] is False
    assert sections_policy["includeDataDate"] is False

    assert report_policy["route"] == "report"
    assert report_policy["enabled"] is False
    assert report_policy["includeDataDate"] is False


def test_should_run_validation_only_for_finance_modules():
    assert _should_run_validation(["IS", "ratios"]) is True
    assert _should_run_validation(["section_businessOverview", "businessOverview"]) is False
    assert _should_run_validation(["dividend"]) is False


def test_should_use_light_mode_only_for_pure_conversation_or_meta():
    assert _should_use_light_mode(object(), "ㅋㅋ", None, False) is True
    assert _should_use_light_mode(object(), "이 회사 어떤 데이터가 있어?", None, False) is True
    assert _should_use_light_mode(object(), "배당이 실적과 현금흐름으로 지속 가능한지 판단해줘", None, False) is False
    assert (
        _should_use_light_mode(object(), "최근 공시 기준으로 사업구조 설명 근거를 2개만 짚어줘", None, False) is False
    )
    follow_up_state = SimpleNamespace(question="최근 5개년", dialogue_mode="follow_up", modules=("costByNature",))
    assert _should_use_light_mode(object(), "최근 5개년", follow_up_state, False) is False


# ── Route Hint 테스트 ──────────────────────────────────────


def test_route_hint_matches_keywords():
    from dartlab.ai.tools.routeHint import buildToolRouteHint

    hint = buildToolRouteHint("삼성전자 경영진 분석 의견에서 올해 핵심 이슈가 뭔지 정리해줘")
    assert "show_topic" in hint
    assert "mdnaOverview" in hint


def test_route_hint_empty_for_no_match():
    from dartlab.ai.tools.routeHint import buildToolRouteHint

    hint = buildToolRouteHint("안녕하세요")
    assert hint == ""


def test_route_hint_multiple_keywords():
    from dartlab.ai.tools.routeHint import buildToolRouteHint

    hint = buildToolRouteHint("삼성전자 재무제표와 배당 현황 알려줘")
    assert "get_data" in hint
    assert "get_report_data" in hint
    assert "IS" in hint
    assert "dividend" in hint


def test_route_hint_deduplicates():
    from dartlab.ai.tools.routeHint import buildToolRouteHint

    hint = buildToolRouteHint("임원 보수 현황 알려줘")
    assert hint.count("executive") == 1
