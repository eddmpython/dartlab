"""detectors 헬퍼 — HP 필터 + Dalio Deleveraging sub-phase + regime variant.

macro/crisis/detectors.py 가 884 줄이라 isolate 헬퍼 분리.
identity 보존을 위해 detectors.py 가 본 모듈에서 re-export 한다.

함수:
- _oneSidedHpTrend — BIS 단측 HP 필터 (Kalman EMA 근사)
- _beautifulDeleveragingSubPhase — Dalio 4 단계 (austerity/default/printing/wealth)
- _dalioRegimeVariant — Deflationary vs Inflationary regime 판정
"""

from __future__ import annotations


def _oneSidedHpTrend(series: list[float], lamb: float = 400_000.0) -> list[float]:
    """단측 HP 필터 (재귀적, numpy 불필요).

    BIS 기준 lambda=400,000 (분기 데이터). Kalman 필터 재귀 방식.
    BIS WP 878: one-sided HP ≈ EMA with appropriate smoothing.
    alpha = 1 / (1 + sqrt(lambda)) (근사).
    """
    n = len(series)
    if n < 4:
        return list(series)
    alpha = 1.0 / (1.0 + (lamb**0.5))
    trend = [series[0]]
    for i in range(1, n):
        trend.append(alpha * series[i] + (1 - alpha) * trend[-1])
    return trend


def _beautifulDeleveragingSubPhase(
    *,
    realRate: float | None = None,
    m2GrowthYoy: float | None = None,
    debtServiceYoY: float | None = None,
    npl: float | None = None,
    hySpread: float | None = None,
    fiscalDeficitPctGdp: float | None = None,
) -> str | None:
    """Beautiful Deleveraging 내부 4단계 판정."""
    available = sum(x is not None for x in [realRate, m2GrowthYoy, debtServiceYoY, npl, hySpread, fiscalDeficitPctGdp])
    if available < 3:
        return None
    if (hySpread is not None and hySpread > 800) or (npl is not None and npl > 5.0):
        return "defaultRestructuring"
    if m2GrowthYoy is not None and m2GrowthYoy > 8.0 and (realRate is None or realRate < 0):
        return "moneyPrinting"
    if fiscalDeficitPctGdp is not None and fiscalDeficitPctGdp > 6.0:
        return "wealthTransfer"
    if realRate is not None and realRate > 1.0 and debtServiceYoY is not None and debtServiceYoY >= 0:
        return "austerity"
    return None


def _dalioRegimeVariant(
    *,
    fxFlexibility: str | None = None,
    reserveCurrency: bool | None = None,
    realRate: float | None = None,
    foreignDebtPct: float | None = None,
) -> str | None:
    """Deflationary vs Inflationary regime 판정 (Dalio Part 1)."""
    if fxFlexibility is None and reserveCurrency is None and realRate is None:
        return None
    score_deflation = 0
    score_inflation = 0
    if fxFlexibility == "pegged":
        score_deflation += 2
    elif fxFlexibility == "managed":
        score_deflation += 1
    elif fxFlexibility == "flexible":
        score_inflation += 1
    if reserveCurrency is True:
        score_inflation += 2
    elif reserveCurrency is False:
        score_deflation += 1
    if foreignDebtPct is not None:
        if foreignDebtPct > 30:
            score_deflation += 2
        elif foreignDebtPct > 15:
            score_deflation += 1
    if realRate is not None:
        if realRate < -2.0:
            score_inflation += 1
        elif realRate > 2.0:
            score_deflation += 1
    if score_deflation > score_inflation:
        return "deflationary"
    if score_inflation > score_deflation:
        return "inflationary"
    return None


__all__ = ["_beautifulDeleveragingSubPhase", "_dalioRegimeVariant", "_oneSidedHpTrend"]
