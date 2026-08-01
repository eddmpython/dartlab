"""Altman/Beneish 재무 alpha의 모델·결측·비발행 계약."""

from __future__ import annotations

import polars as pl
import pytest

from dartlab.analysis.financial._earningsQualityDeepBeneish import calcBeneishTimeline
from dartlab.quant.alphas import altman as altman_module
from dartlab.quant.alphas.altman import (
    _applicabilityReason,
    _scoreOne,
    _zoneZ,
    _zoneZpp,
    calcAltmanFactor,
)
from dartlab.quant.alphas.beneish import calcBeneishFactor
from dartlab.quant.factor.build import _latestYear
from dartlab.story.builders.market import altmanFactorBlock
from dartlab.story.builders.quality import beneishFactorBlock
from dartlab.story.narrate import narrateBeneish

pytestmark = [pytest.mark.unit]


def _financeRow(code: str = "A", **overrides) -> dict:
    row = {
        "stockCode": code,
        "fy": 2024,
        "sector": "manufacturing",
        "total_assets": 100.0,
        "total_liabilities": 40.0,
        "current_assets": 30.0,
        "current_liabilities": 20.0,
        "retained_earnings": 10.0,
        "operating_profit": 5.0,
        "total_stockholders_equity": 60.0,
        "sales": 100.0,
    }
    row.update(overrides)
    return row


def _patchSnapshot(monkeypatch: pytest.MonkeyPatch, rows: list[dict], marketCaps: dict[str, float] | None = None):
    snapshot = pl.DataFrame(rows)
    seen_markets: list[str] = []

    def _load(_name: str, market: str):
        seen_markets.append(market)
        return snapshot.lazy()

    monkeypatch.setattr(altman_module, "loadScanParquet", _load)
    monkeypatch.setattr(altman_module, "_latestYear", lambda _snap: "2024")
    monkeypatch.setattr(altman_module, "_fetchYearEndMarketcaps", lambda _market, _year: marketCaps or {})
    return seen_markets


def testAltmanModelOraclesAndBoundaryZones() -> None:
    stock = pl.DataFrame([_financeRow()])
    z, missing_z, _ = _scoreOne(stock, marketCap=100.0, variant="z")
    zpp, missing_zpp, _ = _scoreOne(stock, marketCap=None, variant="zpp")

    assert missing_z == []
    assert missing_zpp == []
    assert z == pytest.approx(2.925)
    assert zpp == pytest.approx(2.893)
    assert _zoneZ(1.81) == "grey"
    assert _zoneZ(2.99) == "grey"
    assert _zoneZpp(1.1) == "grey"
    assert _zoneZpp(2.6) == "grey"


@pytest.mark.parametrize(
    "column",
    [
        "total_assets",
        "total_liabilities",
        "current_assets",
        "current_liabilities",
        "retained_earnings",
        "operating_profit",
        "total_stockholders_equity",
    ],
)
def testZppRejectsEachMissingRequiredInput(column: str) -> None:
    stock = pl.DataFrame([_financeRow(**{column: None})])
    score, missing, components = _scoreOne(stock, marketCap=None, variant="zpp")

    assert score is None
    assert missing
    assert components == {}


def testZppKeepsObservedZeroAndNegativeEquity() -> None:
    stock = pl.DataFrame(
        [
            _financeRow(
                total_assets=100.0,
                total_liabilities=120.0,
                current_assets=30.0,
                current_liabilities=40.0,
                retained_earnings=-20.0,
                operating_profit=-5.0,
                total_stockholders_equity=-20.0,
            )
        ]
    )
    score, missing, _ = _scoreOne(stock, marketCap=None, variant="zpp")

    assert missing == []
    assert score == pytest.approx(-1.819)
    assert _zoneZpp(score) == "distress"


def testApplicabilitySeparatesFinancialAndManufacturing() -> None:
    assert _applicabilityReason("banks", market="US", variant="zpp") == "financial_company_unsupported"
    assert _applicabilityReason("services", market="US", variant="z") == "nonmanufacturing_company_unsupported_for_z"
    assert _applicabilityReason("manufacturing", market="US", variant="z") is None
    assert _applicabilityReason(None, market="KR", variant="zpp") == "company_type_missing"


def testAutoUsesOneZppModelAndRecordsFinancialExclusion(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [
        _financeRow("A", sector="manufacturing"),
        _financeRow("B", sector="services"),
        _financeRow("C", sector="banks"),
    ]
    _patchSnapshot(monkeypatch, rows, marketCaps={"A": 100.0})

    result = calcAltmanFactor(
        market="US",
        variant="auto",
        industryByCode={"A": "manufacturing", "B": "services", "C": "banks"},
    )

    assert result["status"] == "ok"
    assert result["variantRequested"] == "auto"
    assert result["variant"] == "zpp"
    assert result["scores"] == {"A": 2.89, "B": 2.89}
    assert result["zones"]["safe"]["count"] == 2
    assert result["coverage"]["excludedByReason"] == {"financial_company_unsupported": 1}
    assert result["methodology"]["thresholds"] == {"distressBelow": 1.1, "safeAbove": 2.6}
    metric_labels = [label for label, _value in altmanFactorBlock(result)[1].metrics]
    assert "safe zone (score > 2.6)" in metric_labels
    assert "distress zone (score < 1.1)" in metric_labels


def testExplicitZNeverFallsBackToZPrime(monkeypatch: pytest.MonkeyPatch) -> None:
    _patchSnapshot(monkeypatch, [_financeRow("A")], marketCaps={})

    result = calcAltmanFactor(
        market="US",
        variant="z",
        stockCode="A",
        industryByCode={"A": "manufacturing"},
    )

    assert result["status"] == "unavailable"
    assert result["reasonCode"] == "required_input_missing_or_invalid"
    assert result["missingInputs"] == ["marketEquity"]
    assert result["variant"] == "z"


def testAltmanInfersUsForTickerAndRejectsInvalidVariant(monkeypatch: pytest.MonkeyPatch) -> None:
    seen = _patchSnapshot(monkeypatch, [_financeRow("AAPL")])

    result = calcAltmanFactor(
        market="auto",
        stockCode="AAPL",
        industryByCode={"AAPL": "manufacturing"},
    )

    assert seen == ["US"]
    assert result["market"] == "US"
    with pytest.raises(ValueError, match="variant"):
        calcAltmanFactor(variant="mystery")


def testLatestYearCountsCompaniesNotLongFormRows() -> None:
    snap = pl.DataFrame(
        {
            "bsns_year": ["2025", "2025", "2025", "2024", "2024"],
            "stockCode": ["A", "A", "A", "A", "B"],
        }
    )

    assert _latestYear(snap, minCount=2) == "2024"


def testBeneishAllPublicPathsStayUnavailable() -> None:
    factor = calcBeneishFactor(market="KR", stockCode="005930")
    timeline = calcBeneishTimeline(object())

    assert factor["status"] == "unavailable"
    assert factor["score"] is None
    assert factor["scores"] is None
    assert factor["flags"] is None
    assert factor["reasonCode"] == "canonical_inputs_unavailable"
    assert timeline["status"] == "unavailable"
    assert timeline["history"] == []
    assert timeline["threshold"] is None
    assert beneishFactorBlock(factor) == []
    assert narrateBeneish(factor) is None
