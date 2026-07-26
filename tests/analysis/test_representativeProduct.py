"""Analysis 종합평가 대표 제품 회귀."""

from __future__ import annotations

from typing import Any

import pytest

from dartlab.analysis.financial import representative

pytestmark = pytest.mark.unit


class _Company:
    stockCode = "005930"
    market = "KR"


def _componentValue(functionName: str) -> Any:
    values = {
        "calcCompanyProfile": {"company": "테스트"},
        "calcMarginTrend": {"history": [{"period": "2025", "operatingMargin": 18.0}]},
        "calcGrowthTrend": {"cagr": {"revenue": 7.0, "operatingIncome": 9.0, "periods": 4}},
        "calcGrowthQuality": {"quality": "이익 동반"},
        "calcCashFlowOverview": {"history": [{"period": "2025", "ocf": 120.0, "fcf": 80.0}]},
        "calcCashQuality": {"history": [{"period": "2025", "ocf": 120.0, "netIncome": 100.0, "ocfToNi": 120.0}]},
        "calcLeverageTrend": {"history": [{"period": "2025", "debtRatio": 45.0}]},
        "calcCoverageTrend": {"history": [{"period": "2025", "interestCoverage": 8.0}]},
        "calcDebtMaturity": {"history": [{"period": "2025", "shortTermRatio": 30.0}]},
        "calcValuationSynthesis": {"verdict": "저평가", "weightedFairValue": 100.0},
        "calcSensitivity": {"baseValue": 100.0},
        "calcEarningsQualityFlags": {"flags": []},
        "calcCrossStatementFlags": ["매출채권 확인"],
        "calcScenarioSensitivity": {"shocks": {"opm_minus_5pp": {"opm": 13.0}}},
    }
    return values.get(functionName)


def _runner(company, moduleName, functionName, *, basePeriod):
    del company, moduleName, basePeriod
    return _componentValue(functionName), None


def testRepresentativeBuildsFourDecisionDomains(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(representative, "_runComponent", _runner)

    result = representative.calcRepresentativeAnalysis.__wrapped__(_Company())

    assert result["coverage"]["observedRequiredDomains"] == 4
    assert result["assessment"]["label"] == "재무 기반 우수"
    assert result["assessment"]["positiveDrivers"]
    assert result["blocks"]["quality"]["earningsQualityFlags"] == {"flags": []}


def testRepresentativeUsesMinimumSufficientAnalysisPath() -> None:
    componentNames = {row[3] for row in representative._COMPONENTS}

    assert componentNames == {
        "calcMarginTrend",
        "calcGrowthTrend",
        "calcCashQuality",
        "calcLeverageTrend",
        "calcCoverageTrend",
        "calcEarningsQualityFlags",
    }
    assert {row[0] for row in representative._COMPONENTS} == {"earnings", "cash", "resilience", "quality"}


def testProductKeepsLegacyBlocksAndAddsContract(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(representative, "_runComponent", _runner)
    rep = representative.calcRepresentativeAnalysis.__wrapped__(_Company())
    legacy = {
        "stockCode": "005930",
        "scorecard": {"items": []},
        "piotroski": {"score": 7},
        "summaryFlags": [],
        "representative": rep,
        "dataAsOf": {"latestPeriod": "2025", "retrievedAt": "2026-07-18"},
    }

    product = representative.buildAnalysisProduct(_Company(), legacy)

    assert product["status"] == "usable"
    assert product["identity"]["axis"] == "종합평가"
    assert product["payload"]["blockRefs"] == ["scorecard", "piotroski", "summaryFlags", "representative"]
    assert product["scenarios"][0]["id"] == "marginCompression"
    assert {row["id"] for row in product["claims"]} == {
        "analysis.cashConversion",
        "analysis.operatingIncomeCagr",
        "analysis.operatingMargin",
        "analysis.revenueCagr",
    }
    assert all(row["evidenceRefs"] and row["falsifierRefs"] for row in product["claims"])
    assert legacy["scorecard"] == {"items": []}


def testMissingRequiredDomainIsPartialAndVisible(monkeypatch: pytest.MonkeyPatch) -> None:
    def withoutQuality(company, moduleName, functionName, *, basePeriod):
        if functionName == "calcEarningsQualityFlags":
            return None, None
        return _runner(company, moduleName, functionName, basePeriod=basePeriod)

    monkeypatch.setattr(representative, "_runComponent", withoutQuality)
    rep = representative.calcRepresentativeAnalysis.__wrapped__(_Company())
    legacy = {
        "scorecard": {},
        "piotroski": {},
        "summaryFlags": [],
        "representative": rep,
    }

    product = representative.buildAnalysisProduct(_Company(), legacy)

    assert product["status"] == "partial"
    assert product["confidence"]["score"] == 75.0
    assert any(gap["id"] == "analysis.quality.earningsQualityFlags" for gap in product["gaps"])


def testCashZeroFillCannotBecomeObservedEvidence(monkeypatch: pytest.MonkeyPatch) -> None:
    def zeroCash(company, moduleName, functionName, *, basePeriod):
        if functionName == "calcCashQuality":
            return {"history": [{"period": "2025", "ocf": 0, "netIncome": 100.0, "ocfToNi": 0.0}]}, None
        if functionName == "calcCashFlowOverview":
            return {"history": [{"period": "2025", "ocf": 0, "fcf": 0, "revenue": 500.0}]}, None
        return _runner(company, moduleName, functionName, basePeriod=basePeriod)

    monkeypatch.setattr(representative, "_runComponent", zeroCash)

    result = representative.calcRepresentativeAnalysis.__wrapped__(_Company())

    assert result["coverage"]["domainCoverage"]["cash"]["status"] == "missing"
    assert any(row["status"] == "partial" for row in result["coverage"]["components"] if row["domain"] == "cash")
    assert all(row["id"] != "cashConversion" for row in result["assessment"]["drivers"])
