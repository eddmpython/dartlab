"""핵심 수치 스냅샷 빌드 — server 의존성 없는 순수 로직.

server/chat.py의 build_snapshot()에서 추출.
"""

from __future__ import annotations

from typing import Any

from dartlab.engines.ai.context.company_adapter import get_headline_ratios


def _fmt(val: float | int | None, suffix: str = "") -> str | None:
    if val is None:
        return None
    abs_v = abs(val)
    sign = "-" if val < 0 else ""
    if abs_v >= 1e12:
        return f"{sign}{abs_v / 1e12:,.1f}조{suffix}"
    if abs_v >= 1e8:
        return f"{sign}{abs_v / 1e8:,.0f}억{suffix}"
    if abs_v >= 1e4:
        return f"{sign}{abs_v / 1e4:,.0f}만{suffix}"
    if abs_v >= 1:
        return f"{sign}{abs_v:,.0f}{suffix}"
    return f"0{suffix}"


def _pct(val: float | None) -> str | None:
    return f"{val:.1f}%" if val is not None else None


def _judge_pct(val: float | None, good: float, caution: float) -> str | None:
    if val is None:
        return None
    if val >= good:
        return "good"
    if val >= caution:
        return "caution"
    return "danger"


def _judge_pct_inv(val: float | None, good: float, caution: float) -> str | None:
    if val is None:
        return None
    if val <= good:
        return "good"
    if val <= caution:
        return "caution"
    return "danger"


def build_snapshot(company: Any, *, includeInsights: bool = True) -> dict | None:
    """ratios + 핵심 시계열에서 즉시 표시할 스냅샷 데이터 추출."""
    ratios = get_headline_ratios(company)
    if ratios is None:
        return None
    if not hasattr(ratios, "revenueTTM"):
        return None

    isFinancial = False
    sectorInfo = getattr(company, "sector", None)
    if sectorInfo is not None:
        try:
            from dartlab.engines.analysis.sector.types import Sector

            isFinancial = sectorInfo.sector == Sector.FINANCIALS
        except (ImportError, AttributeError):
            isFinancial = False

    items: list[dict[str, Any]] = []
    roeGood, roeCaution = (8, 5) if isFinancial else (10, 5)
    roaGood, roaCaution = (0.5, 0.2) if isFinancial else (5, 2)

    if ratios.revenueTTM is not None:
        items.append({"label": "매출(TTM)", "value": _fmt(ratios.revenueTTM), "status": None})
    if ratios.operatingIncomeTTM is not None:
        items.append(
            {
                "label": "영업이익(TTM)",
                "value": _fmt(ratios.operatingIncomeTTM),
                "status": "good" if ratios.operatingIncomeTTM > 0 else "danger",
            }
        )
    if ratios.netIncomeTTM is not None:
        items.append(
            {
                "label": "순이익(TTM)",
                "value": _fmt(ratios.netIncomeTTM),
                "status": "good" if ratios.netIncomeTTM > 0 else "danger",
            }
        )
    if ratios.operatingMargin is not None:
        items.append(
            {
                "label": "영업이익률",
                "value": _pct(ratios.operatingMargin),
                "status": _judge_pct(ratios.operatingMargin, 10, 5),
            }
        )
    if ratios.roe is not None:
        items.append({"label": "ROE", "value": _pct(ratios.roe), "status": _judge_pct(ratios.roe, roeGood, roeCaution)})
    if ratios.roa is not None:
        items.append({"label": "ROA", "value": _pct(ratios.roa), "status": _judge_pct(ratios.roa, roaGood, roaCaution)})
    if ratios.debtRatio is not None:
        items.append(
            {
                "label": "부채비율",
                "value": _pct(ratios.debtRatio),
                "status": _judge_pct_inv(ratios.debtRatio, 100, 200),
            }
        )
    if ratios.currentRatio is not None:
        items.append(
            {
                "label": "유동비율",
                "value": _pct(ratios.currentRatio),
                "status": _judge_pct(ratios.currentRatio, 150, 100),
            }
        )
    if ratios.fcf is not None:
        items.append({"label": "FCF", "value": _fmt(ratios.fcf), "status": "good" if ratios.fcf > 0 else "danger"})
    if ratios.revenueGrowth3Y is not None:
        items.append(
            {
                "label": "매출 3Y CAGR",
                "value": _pct(ratios.revenueGrowth3Y),
                "status": _judge_pct(ratios.revenueGrowth3Y, 5, 0),
            }
        )
    if ratios.roic is not None:
        items.append(
            {
                "label": "ROIC",
                "value": _pct(ratios.roic),
                "status": _judge_pct(ratios.roic, 15, 8),
            }
        )
    if ratios.interestCoverage is not None:
        items.append(
            {
                "label": "이자보상배율",
                "value": f"{ratios.interestCoverage:.1f}x",
                "status": _judge_pct(ratios.interestCoverage, 5, 1),
            }
        )
    pf = getattr(ratios, "piotroskiFScore", None)
    if pf is not None:
        items.append(
            {
                "label": "Piotroski F",
                "value": f"{pf}/9",
                "status": "good" if pf >= 7 else ("caution" if pf >= 4 else "danger"),
            }
        )
    az = getattr(ratios, "altmanZScore", None)
    if az is not None:
        items.append(
            {
                "label": "Altman Z",
                "value": f"{az:.2f}",
                "status": "good" if az > 2.99 else ("caution" if az >= 1.81 else "danger"),
            }
        )

    annual = getattr(company, "annual", None)
    trend = None
    if annual is not None:
        series, years = annual
        if years and len(years) >= 2:
            rev_list = series.get("IS", {}).get("sales")
            if rev_list:
                n = min(5, len(rev_list))
                recent_years = years[-n:]
                recent_vals = rev_list[-n:]
                trend = {"years": recent_years, "values": list(recent_vals)}

    if not items:
        return None

    snapshot: dict[str, Any] = {"items": items}
    if trend:
        snapshot["trend"] = trend
    if ratios.warnings:
        snapshot["warnings"] = ratios.warnings[:3]

    if includeInsights:
        try:
            from dartlab.engines.analysis.insight.pipeline import analyze as insight_analyze

            insight_result = insight_analyze(company.stockCode, company=company)
            if insight_result is not None:
                snapshot["grades"] = insight_result.grades()
                snapshot["anomalyCount"] = len(insight_result.anomalies)
        except (ImportError, AttributeError, FileNotFoundError, OSError, RuntimeError, TypeError, ValueError):
            pass

    return snapshot
