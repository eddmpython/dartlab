from __future__ import annotations

import json
from copy import deepcopy

import pytest

from dartlab.story import Story
from dartlab.story.lensProducts import (
    collectLensProducts,
    enginesForReportType,
    lensSummary,
    publicLensBundle,
)

pytestmark = pytest.mark.unit


def _product(engine: str) -> dict:
    return {
        "schemaVersion": 1,
        "identity": {
            "target": "005930",
            "market": "KR",
            "engine": engine,
            "axis": "대표",
            "version": "1",
        },
        "time": {
            "asOf": "2026-07-18",
            "dataAsOf": "2025-12-31",
            "period": "2025",
            "knowledgeBoundary": "2026-07-18",
        },
        "status": "usable",
        "conclusion": {"label": f"{engine} 판단", "summary": f"{engine} 직접 결론"},
        "confidence": {"level": "high", "score": 80.0, "method": "test"},
        "drivers": [],
        "evidence": [
            {
                "id": f"{engine}.representative",
                "kind": "fixture",
                "sourceRef": f"fixture://{engine}/representative",
                "status": "derived",
            }
        ],
        "assumptions": [],
        "gaps": [],
        "scenarios": [],
        "falsifiers": [],
        "payload": {},
    }


class _FakeCompany:
    stockCode = "005930"
    market = "KR"

    def __init__(self):
        self._cache = {}
        self.calls = {engine: 0 for engine in ("analysis", "credit", "industry", "quant", "macro")}

    def analysis(self, *args, **kwargs):
        self.calls["analysis"] += 1
        return {"product": _product("analysis"), "representative": {}}

    def credit(self, *args, **kwargs):
        self.calls["credit"] += 1
        return {"product": _product("credit"), "grade": "dCR-AA"}

    def industry(self):
        self.calls["industry"] += 1
        return {"product": _product("industry"), "industry": "반도체"}

    def quant(self, *args, **kwargs):
        self.calls["quant"] += 1
        return {"product": _product("quant"), "classification": "confirmation"}

    def macro(self, *args, **kwargs):
        self.calls["macro"] += 1
        return {"product": _product("macro"), "edges": []}


def test_collects_five_products_without_composite_and_reuses_company_session() -> None:
    company = _FakeCompany()

    first = collectLensProducts(company)
    second = collectLensProducts(company)

    assert list(first["products"]) == ["analysis", "credit", "industry", "quant", "macro"]
    assert first["noComposite"] is True
    assert first["tensions"]["noComposite"] is True
    assert "score" not in first and "conclusion" not in first
    assert first["statusCounts"] == {"usable": 5}
    assert first["results"]["credit"]["grade"] == "dCR-AA"
    assert all(count == 1 for count in company.calls.values())
    assert second["products"] == first["products"]


def test_report_type_selects_only_relevant_products() -> None:
    assert enginesForReportType("credit") == ("analysis", "credit")
    assert enginesForReportType("valuation") == ("analysis", "quant")
    assert enginesForReportType("macro") == ("analysis", "industry", "macro")

    company = _FakeCompany()
    bundle = collectLensProducts(company, engines=enginesForReportType("credit"))
    assert list(bundle["products"]) == ["analysis", "credit"]
    assert company.calls["industry"] == company.calls["quant"] == company.calls["macro"] == 0


def test_missing_contract_becomes_collection_gap_not_fake_product() -> None:
    company = _FakeCompany()
    company.quant = lambda *args, **kwargs: {"classification": "inconclusive"}

    bundle = collectLensProducts(company, engines=("quant",))

    assert bundle["products"] == {}
    assert bundle["gaps"][0]["engine"] == "quant"
    assert bundle["gaps"][0]["status"] == "missing"


def test_market_without_industry_facade_gets_honest_blocked_product() -> None:
    class CompanyWithoutIndustry:
        stockCode = "AAPL"
        market = "US"

    bundle = collectLensProducts(CompanyWithoutIndustry(), engines=("industry",))
    product = bundle["products"]["industry"]

    assert product["status"] == "blocked"
    assert product["identity"]["target"] == "AAPL"
    assert product["identity"]["market"] == "US"
    assert product["gaps"]


def test_partial_product_keeps_gap_but_does_not_publish_conclusion() -> None:
    company = _FakeCompany()
    product = _product("credit")
    product["status"] = "partial"
    product["gaps"] = [
        {
            "id": "credit.coverage",
            "status": "partial",
            "reason": "신용 근거 일부 결손",
            "sourceRef": "fixture://credit/coverage",
        }
    ]
    company.credit = lambda *args, **kwargs: {
        "product": product,
        "grade": "dCR-AA",
        "gradeRaw": "AA",
    }

    bundle = collectLensProducts(company, engines=("credit",))
    rows = lensSummary(bundle["products"])

    assert bundle["products"]["credit"]["status"] == "partial"
    assert bundle["gaps"] == [
        {
            "id": "credit.coverage",
            "status": "partial",
            "reason": "신용 근거 일부 결손",
            "sourceRef": "fixture://credit/coverage",
            "engine": "credit",
        }
    ]
    assert rows[0]["status"] == "partial"
    assert rows[0]["label"] is None and rows[0]["summary"] is None


def test_unsupported_top_level_product_is_rejected_as_contract_gap() -> None:
    company = _FakeCompany()
    product = _product("quant")
    product["status"] = "unsupported"
    product["gaps"] = [{"id": "quant.axis", "status": "unsupported", "reason": "축 미지원"}]
    company.quant = lambda *args, **kwargs: {"product": product}

    bundle = collectLensProducts(company, engines=("quant",))

    assert bundle["products"] == {}
    assert bundle["gaps"][0]["status"] == "blocked"
    assert "계약 검증 실패" in bundle["gaps"][0]["reason"]


def test_base_period_is_forwarded_to_supported_lenses() -> None:
    company = _FakeCompany()
    received: dict[str, dict] = {}

    def analysis(*args, **kwargs):
        received["analysis"] = kwargs
        return {"product": _product("analysis")}

    def credit(*args, **kwargs):
        received["credit"] = kwargs
        return {"product": _product("credit")}

    def industry(**kwargs):
        received["industry"] = kwargs
        return {"product": _product("industry")}

    def quant(*args, **kwargs):
        received["quant"] = kwargs
        return {"product": _product("quant")}

    def macro(*args, **kwargs):
        received["macro"] = kwargs
        return {"product": _product("macro")}

    company.analysis = analysis
    company.credit = credit
    company.industry = industry
    company.quant = quant
    company.macro = macro

    collectLensProducts(company, basePeriod="2024Q2")

    assert received["analysis"]["basePeriod"] == "2024Q2"
    assert received["credit"]["basePeriod"] == "2024Q2"
    assert received["industry"]["basePeriod"] == "2024Q2"
    assert received["quant"]["asOf"] == "2024-06-30"
    assert received["macro"]["asOf"] == "2024-06-30"


def test_historical_industry_without_cutoff_contract_is_a_gap() -> None:
    company = _FakeCompany()

    bundle = collectLensProducts(company, engines=("industry",), basePeriod="2024")

    assert bundle["products"] == {}
    assert bundle["gaps"][0]["engine"] == "industry"
    assert bundle["gaps"][0]["status"] == "blocked"


def test_public_bundle_and_story_json_exclude_legacy_results() -> None:
    bundle = collectLensProducts(_FakeCompany(), engines=("analysis",))
    public = publicLensBundle(bundle)
    assert public is not None
    assert "results" not in public
    assert public["tensions"] == bundle["tensions"]

    story = Story(stockCode="005930", corpName="삼성전자", reportType="audit")
    story.lensProducts = bundle["products"]
    story._lensBundle = bundle
    rendered = json.loads(story.render("json"))

    assert rendered["reportType"] == "audit"
    assert rendered["lensProducts"]["noComposite"] is True
    assert "results" not in rendered["lensProducts"]


def test_story_gaps_are_visible_in_all_public_formats() -> None:
    story = Story(stockCode="005930", corpName="삼성전자", reportType="audit")
    story.lensGaps = [
        {
            "code": "BLOCK_BUILD_FAILED",
            "builder": "revenue",
            "error": "ValueError",
            "message": "공시 표 결손",
        }
    ]

    markdown = story.render("markdown")
    html = story.render("html")
    rendered = json.loads(story.render("json"))

    assert "BLOCK_BUILD_FAILED" in markdown
    assert "BLOCK_BUILD_FAILED" in html
    assert rendered["lensGaps"] == story.lensGaps


def test_public_bundle_recomputes_canonical_tensions_from_products() -> None:
    bundle = collectLensProducts(_FakeCompany())
    forged = deepcopy(bundle)
    forged["tensions"] = {
        "schemaVersion": 1,
        "items": [{"id": "invented-active-tension"}],
        "evaluations": [],
        "noComposite": True,
    }

    public = publicLensBundle(forged)

    assert public is not None
    assert public["tensions"] == bundle["tensions"]
    assert all(row.get("id") != "invented-active-tension" for row in public["tensions"]["items"])


def test_absent_and_legacy_bundles_are_not_published() -> None:
    assert publicLensBundle(None) is None
    assert publicLensBundle({}) is None
    assert publicLensBundle({"results": {}, "products": {}, "gaps": [], "noComposite": True}) is None

    story = Story(stockCode="005930", corpName="삼성전자", reportType="audit")
    rendered = json.loads(story.render("json"))
    assert "lensProducts" not in rendered
