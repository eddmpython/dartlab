"""금융 Track B가 회계 프록시를 등급으로 가장하지 않는 회귀."""

from __future__ import annotations

import importlib
from types import SimpleNamespace

import pytest

pytestmark = pytest.mark.unit


def _auditEvidence(*_args, **_kwargs) -> dict:
    return {
        "status": "observed",
        "opinion": "적정의견",
        "rawOpinion": "적정의견",
        "fiscalPeriod": "2025",
        "source": {"market": "KR", "method": "structured", "rceptNo": "20260301000001"},
    }


def _history() -> list[dict]:
    return [
        {
            "period": "2026",
            "totalAssets": 120e12,
            "equityRatio": 8.0,
            "roa": None,
            "incomeToAsset": None,
            "provisionRatio": None,
            "cashToAsset": 2.0,
            "currentRatio": None,
        },
        {
            "period": "2025",
            "totalAssets": 100e12,
            "equityRatio": 7.5,
            "roa": 0.7,
            "incomeToAsset": 2.4,
            "provisionRatio": 0.0,
            "cashToAsset": 3.0,
            "currentRatio": None,
        },
    ]


def testFinancialDiagnosticSelectsLatestCommonPeriodAndBlocksGrade(monkeypatch: pytest.MonkeyPatch) -> None:
    """BS-only 최신행과 규모 대체점수로 금융 등급을 만들지 않는다."""
    from dartlab.credit import _engineFinancial as engine
    from dartlab.credit.scoring import _metricsFetchers, metrics

    monkeypatch.setattr(
        metrics,
        "calcFinancialMetrics",
        lambda *_args, **_kwargs: {
            "history": _history(),
            "businessStability": {"operatingIncomeCV": None},
            "track": "B",
        },
    )
    monkeypatch.setattr(_metricsFetchers, "_fetchAuditOpinionEvidence", _auditEvidence)
    company = SimpleNamespace(market="KOSPI", corpName="테스트은행", stockCode="000001")

    result = engine._evaluateFinancial(
        company,
        detail=True,
        industryGroup=SimpleNamespace(name="BANK"),
    )

    assert result is not None
    assert result["assessmentStatus"] == "diagnostic_only"
    assert result["requestedAsOf"] == "2026"
    assert result["assessmentAsOf"] == "2025"
    assert result["freshnessGap"] is True
    assert result["grade"] is None
    assert result["pdEstimate"] is None
    assert result["investmentGrade"] is None
    assert result["outlook"] == "N/A"
    assert result["coverage"]["gradeCoveragePct"] == 0.0
    assert all(axis["score"] is None for axis in result["axes"])
    assert all(axis["weight"] is None for axis in result["axes"])
    assert all(axis["contribution"] is None for axis in result["axes"])

    assetAxis = next(axis for axis in result["axes"] if axis["name"] == "회계자산위험 프록시")
    assert assetAxis["metrics"][0]["value"] == 0.0  # 관측 0은 결측이나 규모 12점이 아니다
    assert assetAxis["metrics"][0]["status"] == "observed"


def testTotalAssetsOnlyCannotBecomeAaProxyScore(monkeypatch: pytest.MonkeyPatch) -> None:
    """총자산만 큰 회사가 자산건전성 우량 대체점수를 얻지 않는다."""
    from dartlab.credit import _engineFinancial as engine
    from dartlab.credit.scoring import _metricsFetchers, metrics

    onlyAssets = {
        "period": "2025",
        "totalAssets": 200e12,
        "equityRatio": None,
        "roa": None,
        "incomeToAsset": None,
        "provisionRatio": None,
        "cashToAsset": None,
        "currentRatio": None,
    }
    monkeypatch.setattr(
        metrics,
        "calcFinancialMetrics",
        lambda *_args, **_kwargs: {
            "history": [onlyAssets],
            "businessStability": {"operatingIncomeCV": None},
            "track": "B",
        },
    )
    monkeypatch.setattr(_metricsFetchers, "_fetchAuditOpinionEvidence", _auditEvidence)

    result = engine._evaluateFinancial(
        SimpleNamespace(market="KOSPI", corpName="대형금융", stockCode="000002"),
        industryGroup=SimpleNamespace(name="DIVERSIFIED_FINANCIALS"),
    )

    assert result is not None
    assert result["grade"] is None
    assert result["currentScore"] is None
    assert result["financialSubtypeStatus"] == "ambiguous"
    assert all(axis["score"] is None for axis in result["axes"])


def testFinancialDiagnosticBuildsBlockedProduct(monkeypatch: pytest.MonkeyPatch) -> None:
    """공개 product·AI badge도 진단값을 등급으로 승격하지 않는다."""
    from dartlab.ai.tools import creditBadge
    from dartlab.credit.product import attachCreditProduct

    creditEngine = importlib.import_module("dartlab.credit.engine")

    company = SimpleNamespace(market="KR", corpName="금융사", stockCode="000003")
    diagnostic = {
        "assessmentStatus": "diagnostic_only",
        "blockedReason": "유형별 calibration 없음",
        "grade": None,
        "score": None,
        "pdEstimate": None,
        "outlook": "N/A",
        "latestPeriod": "2025",
        "axes": [{"name": "유동성", "score": None, "weight": None, "metrics": []}],
    }

    productResult = attachCreditProduct(company, dict(diagnostic))
    assert productResult["product"]["status"] == "blocked"
    assert productResult["product"]["payload"]["pdEstimate"] is None

    monkeypatch.setattr(creditEngine, "evaluateCompany", lambda *_args, **_kwargs: dict(diagnostic))
    assert creditBadge.getDcrBadge(company) is None
