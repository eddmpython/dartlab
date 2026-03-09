"""금융업 감지 + 불완전 연도 감지."""

from __future__ import annotations

from typing import Optional

from dartlab.engines.financeEngine.extract import getLatest, getAnnualValues
from dartlab.engines.financeEngine.ratios import RatioResult


def detectIncompleteYear(qPeriods: list[str]) -> tuple[str, int]:
    """최신 연도의 분기 수를 반환.

    Returns:
        (lastYear, quarterCount). quarterCount < 4면 불완전 연도.
    """
    lastPeriod = qPeriods[-1]
    lastYear = lastPeriod.split("_")[0]
    qCount = sum(1 for p in qPeriods if p.startswith(lastYear))
    return lastYear, qCount


def detectFinancialSector(
    series: dict,
    ratios: RatioResult,
) -> tuple[bool, list[str]]:
    """금융업 자동 감지 (신호 2개 이상이면 금융업).

    신호 후보 6개:
    1. revenue 없고 operating_income 있음
    2. 부채비율 500% 초과
    3. 유동자산/유동부채 데이터 없음
    4. 이자수익 계정 존재
    5. 순이자수익 계정 존재
    6. 보험수익 계정 존재
    """
    signals: list[str] = []

    revVals = getAnnualValues(series, "IS", "revenue")
    opVals = getAnnualValues(series, "IS", "operating_income")
    hasRevenue = any(v is not None for v in revVals)
    hasOpIncome = any(v is not None for v in opVals)
    if not hasRevenue and hasOpIncome:
        signals.append("revenue 없고 operating_income 있음")

    if ratios.debtRatio is not None and ratios.debtRatio > 500:
        signals.append(f"부채비율 {ratios.debtRatio:.0f}%")

    if ratios.currentRatio is None and getLatest(series, "BS", "current_assets") is None:
        signals.append("유동자산/유동부채 데이터 없음")

    if getLatest(series, "IS", "interest_income") is not None:
        signals.append("이자수익 계정 존재")

    if getLatest(series, "IS", "net_interest_income") is not None:
        signals.append("순이자수익 계정 존재")

    if getLatest(series, "IS", "insurance_revenue") is not None:
        signals.append("보험수익 계정 존재")

    return len(signals) >= 2, signals
