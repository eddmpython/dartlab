"""review가 소비하는 calc 인터페이스 — credit 엔진 래퍼.

credit/ 독립 엔진이 계산의 단일 진실(source of truth)이다.
이 모듈은 review가 소비할 수 있는 calc 인터페이스를 제공하는 thin wrapper.

직접 접근: dartlab.credit("005930") 또는 c.credit()
review 경유: c.review("신용분석")

cross-dependency 방지: analysis ↛ credit, credit ↛ analysis.
이전에는 analysis/financial/creditRating.py에 있었으나
analysis-credit 간 순환 의존 제거를 위해 credit/ 내부로 이동.
"""

from __future__ import annotations

import functools
import inspect
from typing import Any, Callable

# ── memoized_calc 자체 구현 (analysis 의존 제거) ──


def _memoized_calc(fn: Callable[..., Any]) -> Callable[..., Any]:
    """calc 함수 결과를 Company._cache에 메모이제이션.

    analysis/_memoize.py와 동일 로직. credit 독립성을 위해 자체 구현.
    """
    _has_base_period = "basePeriod" in inspect.signature(fn).parameters

    @functools.wraps(fn)
    def wrapper(company: Any, *, basePeriod: str | None = None) -> Any:
        cache = getattr(company, "_cache", None)
        key = f"_{fn.__name__}:{basePeriod}"

        if cache is not None and key in cache:
            return cache[key]

        if _has_base_period:
            result = fn(company, basePeriod=basePeriod)
        else:
            result = fn(company)

        if cache is not None:
            cache[key] = result

        return result

    return wrapper


# ── credit 엔진 호출 ──


def _evaluate(company, basePeriod=None):
    """credit 엔진 호출 (캐시 공유를 위한 내부 함수)."""
    from dartlab.credit.engine import evaluateCompany

    return evaluateCompany(company, detail=True, basePeriod=basePeriod)


# ═══════════════════════════════════════════════════════════
# calc 함수들 — review가 소비하는 인터페이스
# credit/ 엔진의 결과를 review 형식으로 변환
# ═══════════════════════════════════════════════════════════


@_memoized_calc
def calcCreditMetrics(company, *, basePeriod: str | None = None) -> dict | None:
    """신용분석 핵심 지표 시계열."""
    result = _evaluate(company, basePeriod)
    if result is None:
        return None
    history = result.get("metricsHistory")
    if not history:
        return None
    return {
        "history": history,
        "businessStability": result.get("businessStability"),
    }


@_memoized_calc
def calcCreditScore(company, *, basePeriod: str | None = None) -> dict | None:
    """신용등급 종합 산출."""
    return _evaluate(company, basePeriod)


@_memoized_calc
def calcCreditHistory(company, *, basePeriod: str | None = None) -> dict | None:
    """신용등급 시계열."""
    result = _evaluate(company, basePeriod)
    if result is None:
        return None

    from dartlab.credit.scorecard import mapTo20Grade, scoreMetric
    from dartlab.credit.thresholds import getThresholds

    history_data = result.get("metricsHistory", [])
    if not history_data:
        return None

    sector, ig = None, None
    try:
        si = getattr(company, "sector", None)
        if si:
            sector, ig = si.sector, si.industryGroup
    except (AttributeError, ImportError):
        pass

    thresholds = getThresholds(sector, ig)
    history = []
    for h in history_data:
        scores = []
        for key, tKey in [
            ("ffoToDebt", "ffo_to_debt"),
            ("debtToEbitda", "debt_to_ebitda"),
            ("ebitdaInterestCoverage", "ebitda_interest_coverage"),
            ("debtRatio", "debt_ratio"),
            ("currentRatio", "current_ratio"),
        ]:
            s = scoreMetric(h.get(key), thresholds[tKey])
            if s is not None:
                scores.append(s)
        if scores:
            periodScore = round(sum(scores) / len(scores), 2)
            grade, _, pd = mapTo20Grade(periodScore)
            history.append(
                {
                    "period": h["period"],
                    "score": periodScore,
                    "grade": grade,
                    "pdEstimate": pd,
                }
            )

    if not history:
        return None

    grades = [h["grade"] for h in history]
    return {
        "history": history,
        "stable": len(set(grades)) <= 2,
        "latestGrade": history[0]["grade"] if history else None,
        "oldestGrade": history[-1]["grade"] if history else None,
    }


@_memoized_calc
def calcCashFlowGrade(company, *, basePeriod: str | None = None) -> dict | None:
    """현금흐름등급(eCR)."""
    result = _evaluate(company, basePeriod)
    if result is None:
        return None

    from dartlab.credit.scorecard import cashFlowGrade

    history_data = result.get("metricsHistory", [])
    if not history_data:
        return None

    history = []
    for h in history_data:
        eCR = cashFlowGrade(
            h.get("ocfToSales"),
            h.get("fcf") is not None and (h.get("fcf") or 0) > 0,
            h.get("ocfToDebt"),
        )
        history.append(
            {
                "period": h["period"],
                "eCR": eCR,
                "ocfToSales": h.get("ocfToSales"),
                "fcfPositive": h.get("fcf") is not None and (h.get("fcf") or 0) > 0,
                "ocfToDebt": h.get("ocfToDebt"),
            }
        )

    return {"history": history} if history else None


@_memoized_calc
def calcCreditPeerPosition(company, *, basePeriod: str | None = None) -> dict | None:
    """업종 내 신용 순위."""
    result = _evaluate(company, basePeriod)
    if result is None:
        return None

    history_data = result.get("metricsHistory", [])
    if not history_data:
        return None

    latest = history_data[0]
    return {
        "latestPeriod": latest.get("period"),
        "metrics": {
            "debtRatio": latest.get("debtRatio"),
            "ebitdaInterestCoverage": latest.get("ebitdaInterestCoverage"),
            "ffoToDebt": latest.get("ffoToDebt"),
            "currentRatio": latest.get("currentRatio"),
        },
        "peerAvailable": False,
    }


@_memoized_calc
def calcCreditFlags(company, *, basePeriod: str | None = None) -> dict | None:
    """신용 경고/개선 플래그."""
    result = _evaluate(company, basePeriod)
    if result is None:
        return None

    history_data = result.get("metricsHistory", [])
    if not history_data:
        return None

    latest = history_data[0]
    flags: list[dict] = []

    isFinancial = False
    try:
        si = getattr(company, "sector", None)
        if si:
            from dartlab.core.sector.types import Sector

            isFinancial = si.sector == Sector.FINANCIALS
    except (AttributeError, ImportError):
        pass

    icr = latest.get("ebitdaInterestCoverage")
    if icr is not None and icr < 1.5 and not isFinancial:
        flags.append(
            {
                "type": "warning",
                "signal": "이자보상배율 1.5배 미달",
                "detail": f"EBITDA/이자비용 = {icr}배",
                "impact": "등급 하방 1~2 notch",
            }
        )

    dr = latest.get("debtRatio")
    if dr is not None and dr > 300 and not isFinancial:
        flags.append(
            {"type": "warning", "signal": "부채비율 300% 초과", "detail": f"부채비율 {dr:.0f}%", "impact": "등급 하방"}
        )

    ocfVal = latest.get("ocf")
    if ocfVal is not None and ocfVal < 0:
        flags.append(
            {
                "type": "warning",
                "signal": "영업현금흐름 적자",
                "detail": "본업에서 현금 유출",
                "impact": "등급 하방 2+ notch",
            }
        )

    de = latest.get("debtToEbitda")
    if de is not None and de > 5 and not isFinancial:
        flags.append(
            {
                "type": "warning",
                "signal": "Debt/EBITDA 5배 초과",
                "detail": f"총차입금/EBITDA = {de}배",
                "impact": "B급 이하 위험",
            }
        )

    if icr is not None and icr > 10:
        flags.append(
            {
                "type": "opportunity",
                "signal": "이자보상배율 10배 초과",
                "detail": f"EBITDA/이자비용 = {icr}배",
                "impact": "등급 상방",
            }
        )

    ffoDebt = latest.get("ffoToDebt")
    if ffoDebt is not None and ffoDebt > 40:
        flags.append(
            {
                "type": "opportunity",
                "signal": "FFO/총차입금 40% 초과",
                "detail": f"FFO/Debt = {ffoDebt:.0f}%",
                "impact": "등급 상방",
            }
        )

    cr = latest.get("currentRatio")
    if cr is not None and cr > 200:
        flags.append(
            {
                "type": "opportunity",
                "signal": "유동비율 200% 초과",
                "detail": f"유동비율 {cr:.0f}%",
                "impact": "유동성 안전",
            }
        )

    return {"flags": flags}
