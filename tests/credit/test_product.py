"""Credit 등급 대표 제품 계약 회귀."""

from __future__ import annotations

import pytest

from dartlab.credit.product import blockedCreditResult, buildCreditProduct

pytestmark = pytest.mark.unit


class _Company:
    stockCode = "005930"
    market = "KR"
    sector = None


def _result() -> dict:
    return {
        "grade": "dCR-AA",
        "score": 12.5,
        "healthScore": 87.5,
        "outlook": "안정적",
        "latestPeriod": "2025",
        "methodologyVersion": "v4.0",
        "eCR": "eCR-1",
        "pdEstimate": 0.2,
        "axes": [
            {"name": "채무상환능력", "score": 10.0, "weight": 40, "contribution": 4.0, "metrics": []},
            {"name": "자본구조", "score": 20.0, "weight": 30, "contribution": 6.0, "metrics": []},
            {"name": "유동성", "score": 15.0, "weight": 20, "contribution": 3.0, "metrics": []},
            {"name": "공시리스크", "score": None, "weight": 10, "contribution": None, "metrics": []},
        ],
        "metricsHistory": [
            {
                "period": "2025",
                "ffoToDebt": 40.0,
                "debtToEbitda": 1.0,
                "ebitdaInterestCoverage": 8.0,
                "debtRatio": 50.0,
                "currentRatio": 180.0,
            }
        ],
        "narratives": {
            "axes": [
                {"axis": "채무상환능력", "summary": "상환 부담", "details": [], "severity": "weak"},
                {"axis": "자본구조", "summary": "구조 양호", "details": [], "severity": "strong"},
                {"axis": "유동성", "summary": "유동성 보통", "details": [], "severity": "adequate"},
            ]
        },
    }


def testCreditProductPreservesGradeAndExposesCoverage() -> None:
    result = _result()
    stress = {
        "grade": "dCR-A+",
        "score": 24.0,
        "appliedOverrides": {"scenarioStress": "moderate"},
    }

    product = buildCreditProduct(_Company(), result, comparison=stress)

    assert product["status"] == "usable"
    assert product["conclusion"]["label"] == "dCR-AA"
    assert product["confidence"]["score"] == 90.0
    assert product["scenarios"][1]["id"] == "moderateStress"
    debtService = next(row for row in product["claims"] if row["id"] == "credit.debtService")
    assert debtService["direction"] == "adverse"
    assert debtService["basis"] == "creditNarrative"
    assert any(gap["id"] == "credit.axis.공시리스크" for gap in product["gaps"])
    assert result["grade"] == "dCR-AA"


def testRequestedScenarioAppearsAsAssumption() -> None:
    result = _result()
    result["appliedOverrides"] = {"debtRatio": 250.0}
    baseline = {"grade": "dCR-AA", "score": 12.5}

    product = buildCreditProduct(_Company(), result, comparison=baseline)

    assert product["scenarios"][0]["id"] == "baseline"
    assert product["scenarios"][1]["id"] == "requestedOverride"
    assert product["assumptions"] == [{"id": "debtRatio", "value": 250.0, "source": "userOrScenarioOverride"}]


def testBlockedMarketReturnsHonestProduct() -> None:
    class _UsCompany:
        stockCode = "AAPL"
        market = "US"

    result = blockedCreditResult(_UsCompany(), reason="US calibration 없음")

    assert result["grade"] is None
    assert result["product"]["status"] == "blocked"
    assert result["product"]["identity"]["market"] == "US"
    assert result["product"]["confidence"]["level"] == "blocked"
    assert result["product"]["gaps"][0]["status"] == "blocked"
