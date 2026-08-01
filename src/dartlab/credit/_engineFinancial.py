"""금융업 회계 프록시 진단.

은행·보험·증권의 규제자본과 funding/liquidity 지표가 없는 공통 재무제표만으로
신용등급이나 PD를 만들지 않는다. 기존 Track B 숫자는 관측 회계값을 확인하는
진단으로만 남긴다.
"""

from __future__ import annotations

import math

from dartlab.credit.features.sectorThresholds import getSectorLabel


def _finite(value) -> float | None:
    """유한한 숫자만 진단값으로 보존한다."""
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _metric(name: str, value, *, unit: str, isProxy: bool = True) -> dict:
    """점수와 분리된 관측 metric 계약."""
    observed = _finite(value)
    return {
        "name": name,
        "value": observed,
        "unit": unit,
        "status": "observed" if observed is not None else "missing",
        "isProxy": isProxy,
    }


def _selectAssessmentRow(history: list[dict]) -> dict | None:
    """BS와 최소 한 수익성 지표가 함께 있는 최신 공통기간을 선택한다."""
    for row in history:
        if _finite(row.get("equityRatio")) is None:
            continue
        if _finite(row.get("roa")) is None and _finite(row.get("incomeToAsset")) is None:
            continue
        return row
    return None


def _financialSubtype(company, industryGroup) -> tuple[str, str]:
    """현재 공개 분류가 확정할 수 있는 최소 금융 하위유형과 상태."""
    group = str(getattr(industryGroup, "name", "") or "").upper()
    corpName = str(getattr(company, "corpName", "") or "")
    if "금융지주" in corpName or "FINANCIAL HOLDING" in corpName.upper():
        return "financial_holding", "resolved"
    if group == "BANK":
        if "은행" in corpName or "BANK" in corpName.upper():
            return "bank", "resolved"
        return "bank_or_financial_holding", "ambiguous"
    if group == "INSURANCE":
        return "insurance", "resolved"
    if group == "DIVERSIFIED_FINANCIALS":
        return "other_finance", "ambiguous"
    return "unknown", "ambiguous"


def _axis(name: str, metrics: list[dict], *, reason: str) -> dict:
    """회계 프록시 축을 비채점 진단으로 공개한다."""
    return {
        "name": name,
        "score": None,
        "weight": None,
        "contribution": None,
        "status": "diagnostic_only",
        "reason": reason,
        "metrics": metrics,
    }


def _evaluateFinancial(
    company,
    *,
    detail: bool = False,
    basePeriod: str | None = None,
    sector=None,
    industryGroup=None,
) -> dict | None:
    """금융업 공시 회계값을 진단하되 dCR 등급과 PD는 발행하지 않는다."""
    from dartlab.credit.scoring._metricsFetchers import _fetchAuditOpinionEvidence
    from dartlab.credit.scoring.metrics import calcFinancialMetrics

    metrics = calcFinancialMetrics(company, basePeriod=basePeriod)
    if metrics is None or not metrics.get("history"):
        return None

    history = metrics["history"]
    requestedAsOf = history[0].get("period")
    latest = _selectAssessmentRow(history)
    if latest is None:
        latest = history[0]
    assessmentAsOf = latest.get("period")

    subtype, subtypeStatus = _financialSubtype(company, industryGroup)
    auditEvidence = _fetchAuditOpinionEvidence(
        company, basePeriod=str(assessmentAsOf) if assessmentAsOf else basePeriod
    )

    capital = [
        _metric("장부자본/총자산", latest.get("equityRatio"), unit="%"),
    ]
    profitability = [
        _metric("당기순이익/기말총자산", latest.get("roa"), unit="%"),
        _metric("금융수익/기말총자산", latest.get("incomeToAsset"), unit="%"),
    ]
    assetRisk = [
        _metric("대손상각비/총자산", latest.get("provisionRatio"), unit="%"),
    ]
    fundingLiquidity = [
        _metric("현금성자산/총자산", latest.get("cashToAsset"), unit="%"),
        _metric("회계 유동자산/유동부채", latest.get("currentRatio"), unit="%"),
    ]
    business = metrics.get("businessStability", {}) or {}
    stability = [
        _metric("영업이익 변동계수", business.get("operatingIncomeCV"), unit="%"),
        _metric("총자산", latest.get("totalAssets"), unit="KRW"),
    ]

    axes = [
        _axis(
            "회계자본 프록시",
            capital,
            reason="규제자본비율(CET1·K-ICS·NCR 등)이 아니므로 자본적정성 점수로 쓰지 않습니다.",
        ),
        _axis(
            "회계수익성 프록시",
            profitability,
            reason="유형별 수익성 calibration이 없어 점수와 등급에 쓰지 않습니다.",
        ),
        _axis(
            "회계자산위험 프록시",
            assetRisk,
            reason="NPL·Stage 3·보험위험·시장/PF 위험을 대체하지 못합니다.",
        ),
        _axis(
            "유동성",
            fundingLiquidity,
            reason="LCR·NSFR·ALM·haircut·우발유출을 반영하지 못해 비채점 진단으로만 제공합니다.",
        ),
        _axis(
            "규모·변동성 진단",
            stability,
            reason="규모는 누락된 건전성 지표의 대체점수가 아니며 진단값으로만 제공합니다.",
        ),
    ]

    observedProxyMetrics = sum(1 for axis in axes for item in axis["metrics"] if item.get("status") == "observed")
    totalProxyMetrics = sum(len(axis["metrics"]) for axis in axes)
    blockedReason = (
        "금융업 공통 재무제표 프록시는 유형별 규제자본·자산위험·자금조달/유동성 calibration을 "
        "대체할 수 없어 dCR 등급과 PD를 발행하지 않습니다."
    )
    sectorLabel = f"{getSectorLabel(sector)} (금융 회계프록시 진단)"

    result = {
        "assessmentStatus": "diagnostic_only",
        "blockedReason": blockedReason,
        "grade": None,
        "gradeRaw": None,
        "gradeDescription": None,
        "gradeCategory": None,
        "investmentGrade": None,
        "score": None,
        "healthScore": None,
        "currentScore": None,
        "pdEstimate": None,
        "eCR": None,
        "outlook": "N/A",
        "sector": sectorLabel,
        "financialSubtype": subtype,
        "financialSubtypeStatus": subtypeStatus,
        "requestedAsOf": requestedAsOf,
        "assessmentAsOf": assessmentAsOf,
        "freshnessGap": requestedAsOf != assessmentAsOf,
        "latestPeriod": assessmentAsOf,
        "auditOpinion": auditEvidence.get("opinion") if auditEvidence.get("status") == "observed" else None,
        "auditOpinionEvidence": auditEvidence,
        "methodologyVersion": "v4.1-TrackB-diagnostic",
        "axes": axes,
        "coverage": {
            "status": "diagnostic_only",
            "observedProxyMetrics": observedProxyMetrics,
            "totalProxyMetrics": totalProxyMetrics,
            "gradeCoveragePct": 0.0,
            "criticalGaps": [
                "유형별 규제자본",
                "유형별 자산/보험/시장위험",
                "유형별 funding/liquidity",
                "유형별 out-of-time calibration",
            ],
        },
    }

    if detail:
        result["metricsHistory"] = history
        result["businessStability"] = business

    return result


__all__ = ["_evaluateFinancial", "_financialSubtype", "_selectAssessmentRow"]
