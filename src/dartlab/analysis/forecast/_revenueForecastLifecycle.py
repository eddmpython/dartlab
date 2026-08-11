"""revenueForecast 헬퍼 — 컨센서스 수집 + ROIC 내재성장 + 라이프사이클 + 가중치.

revenueForecast.py 에서 분리. 비공개 (_) 헬퍼 5 종.
"""

from __future__ import annotations

import functools
import logging
import math

from dartlab.core.utils.extract import getAnnualValues, getLatest, getTTM
from dartlab.gather.types import isOptionalSourceError

log = logging.getLogger(__name__)

_ROIC_WEIGHT = 0.15


# 컨센서스 매출 추출
# ══════════════════════════════════════


@functools.lru_cache(maxsize=64)
def _fetchConsensusRevenue(
    stockCode: str,
    market: str = "KR",
) -> tuple[tuple[int, float, str], ...]:
    """gather에서 매출 컨센서스를 가져온다.

    [성능] @lru_cache — review에서 4번 호출되는데 매번 외부 API.
    같은 stockCode 입력은 첫 호출 후 즉시 반환.
    Return type은 tuple (lru_cache는 hashable result 권장).
    """
    try:
        from dartlab.core.di import getMacroProvider

        g = getMacroProvider().getDefaultGather()
        items = g.revenueConsensus(stockCode, market=market)
        # 싱글턴 차용: 닫지 않는다. 여기서 close 하면 이후 모든 gather 호출이
        # "client has been closed" 로 죽는다 (전상장사 sweep 2번째 회사부터 전멸).
        return tuple((item.fiscal_year, item.revenue_est, item.source) for item in items if item.revenue_est > 0)
    except Exception as exc:
        if not isOptionalSourceError(exc):
            raise
        log.debug("컨센서스 수집 실패: %s", exc)
        return ()


# ══════════════════════════════════════
# ROIC 기반 내재 성장률 (Damodaran Value Driver)
# ══════════════════════════════════════


def _fundamentalGrowth(series: dict) -> tuple[float | None, dict]:
    """ROIC x Reinvestment Rate → 내재 성장률 (Damodaran Value Driver).

    Parameters
    ----------
    series : dict
        finance.timeseries 시계열 dict.

    Returns
    -------
    tuple[float | None, dict]
        fundamentalGrowth : float | None — 내재 성장률 (%). 계산 불가 시 None.
        detail : dict
            roic : float — 투하자본수익률 (%)
            reinvestmentRate : float — 재투자율 (%)
            nopat : float — 세후영업이익 (원)
            investedCapital : float — 투하자본 (원)
            capex : float — 자본적지출 (원)
            depreciation : float — 감가상각비 (원)
            deltaNwc : float — 순운전자본 변동 (원)
            fundamentalGrowth : float — 내재 성장률 (%)
    """
    detail: dict = {}

    # NOPAT = 영업이익 × (1 - 유효세율)
    opIncome = getTTM(series, "IS", "operating_income") or getTTM(series, "IS", "operating_profit")
    if opIncome is None or opIncome <= 0:
        return None, detail

    pbt = getTTM(series, "IS", "profit_before_tax")
    taxExp = getTTM(series, "IS", "income_tax_expense")
    effectiveTax = 0.22  # 기본값: 한국 법인세 실효세율
    if pbt and pbt > 0 and taxExp is not None:
        et = taxExp / pbt
        if 0 <= et <= 0.5:
            effectiveTax = et

    nopat = opIncome * (1 - effectiveTax)

    # Invested Capital = 자기자본 + max(순차입금, 0)
    totalEquity = getLatest(series, "BS", "total_stockholders_equity") or getLatest(
        series, "BS", "owners_of_parent_equity"
    )
    cash = getLatest(series, "BS", "cash_and_cash_equivalents") or 0
    shortBorr = getLatest(series, "BS", "shortterm_borrowings") or 0
    longBorr = getLatest(series, "BS", "longterm_borrowings") or 0
    bonds = getLatest(series, "BS", "bonds_payable") or 0
    netDebt = shortBorr + longBorr + bonds - cash

    if totalEquity is None or totalEquity <= 0:
        return None, detail

    invested = totalEquity + max(netDebt, 0)
    if invested <= 0:
        return None, detail

    roic = (nopat / invested) * 100  # %

    # CAPEX (CF에서 음수로 기록됨)
    capexRaw = getTTM(series, "CF", "purchase_of_property_plant_and_equipment")
    capex = abs(capexRaw) if capexRaw else 0

    # Depreciation
    dep = getTTM(series, "CF", "depreciation_and_amortization")
    if dep is None:
        dep = getTTM(series, "CF", "depreciation_cf")
    if dep is None:
        dep = getTTM(series, "CF", "depreciation")
    if dep is None:
        # fallback: 유형자산 × 5% + 무형자산 × 10%
        tangible = getLatest(series, "BS", "tangible_assets") or 0
        intangible = getLatest(series, "BS", "intangible_assets") or 0
        dep = tangible * 0.05 + intangible * 0.1

    # ΔNWC (순운전자본 변동)
    caVals = getAnnualValues(series, "BS", "current_assets")
    clVals = getAnnualValues(series, "BS", "current_liabilities")
    cashVals = getAnnualValues(series, "BS", "cash_and_cash_equivalents")
    deltaNwc = 0.0
    if len(caVals) >= 2 and len(clVals) >= 2:

        def _nwcAt(idx: int) -> float | None:
            """특정 인덱스의 순운전자본(유동자산-현금-유동부채) 산출."""
            ca = caVals[idx] if idx < len(caVals) else None
            cl = clVals[idx] if idx < len(clVals) else None
            c = cashVals[idx] if idx < len(cashVals) and cashVals[idx] else 0
            if ca is not None and cl is not None:
                return (ca - (c or 0)) - cl
            return None

        nwcCurr = _nwcAt(-1)
        nwcPrev = _nwcAt(-2)
        if nwcCurr is not None and nwcPrev is not None:
            deltaNwc = nwcCurr - nwcPrev

    # Reinvestment = CAPEX - Depreciation + ΔNWC
    reinvestment = capex - dep + deltaNwc

    if nopat <= 0:
        return None, detail

    reinvestmentRate = reinvestment / nopat
    # 재투자율 범위 제한 (음수 = 자본 회수, >1.0 = 공격 투자)
    reinvestmentRate = max(min(reinvestmentRate, 1.5), -0.5)

    fundamentalG = roic * reinvestmentRate  # % 단위

    detail = {
        "roic": round(roic, 2),
        "reinvestmentRate": round(reinvestmentRate * 100, 1),
        "nopat": nopat,
        "investedCapital": invested,
        "capex": capex,
        "depreciation": dep,
        "deltaNwc": deltaNwc,
        "fundamentalGrowth": round(fundamentalG, 2),
    }

    return fundamentalG, detail


# ══════════════════════════════════════
# 기업 라이프사이클 판별
# ══════════════════════════════════════


def _classifyLifecycle(series: dict) -> tuple[str, dict]:
    """기업 라이프사이클 단계 판별.

    Parameters
    ----------
    series : dict
        finance.timeseries 시계열 dict.

    Returns
    -------
    tuple[str, dict]
        lifecycle : str — "high_growth" | "mature" | "transition" | "decline" | "unknown"
        detail : dict
            cagr_3y : float — 3년 CAGR (%)
            cv : float — 변동계수 (비율)
            signChanges : int — 성장률 부호 전환 횟수
            dataPoints : int — 유효 데이터 수
    """
    revVals = getAnnualValues(series, "IS", "revenue") or getAnnualValues(series, "IS", "sales")
    valid = [v for v in revVals if v is not None and v > 0]

    if len(valid) < 4:
        return "unknown", {"reason": "매출 데이터 4기간 미만"}

    # 3Y CAGR
    recent = valid[-4:]  # 최근 4개 = 3년 성장
    cagr = ((recent[-1] / recent[0]) ** (1 / 3) - 1) * 100 if recent[0] > 0 else 0

    # CV (Coefficient of Variation)
    meanRev = sum(recent) / len(recent)
    if meanRev > 0:
        variance = sum((v - meanRev) ** 2 for v in recent) / len(recent)
        cv = math.sqrt(variance) / meanRev
    else:
        cv = 0

    # 부호 변화 횟수 (성장률 방향 전환)
    growthSigns = []
    for i in range(1, len(recent)):
        if recent[i - 1] > 0:
            growthSigns.append(1 if recent[i] > recent[i - 1] else -1)
    signChanges = sum(1 for i in range(1, len(growthSigns)) if growthSigns[i] != growthSigns[i - 1])

    detail = {
        "cagr_3y": round(cagr, 1),
        "cv": round(cv, 3),
        "signChanges": signChanges,
        "dataPoints": len(valid),
    }

    # signChanges 임계: 분기 데이터(>8개)는 3회, 연간은 2회
    signThreshold = 3 if len(valid) > 8 else 2
    if cv > 0.4 or signChanges >= signThreshold:
        return "transition", detail
    if cagr > 15 and cv < 0.3:
        return "high_growth", detail
    if cagr < -5:
        return "decline", detail
    return "mature", detail


def _lifecycleWeightAdjustments(
    lifecycle: str,
    baseWeights: dict[str, float],
) -> dict[str, float]:
    """라이프사이클에 따른 앙상블 소스 가중치 조정.

    Parameters
    ----------
    lifecycle : str
        라이프사이클 단계.
    baseWeights : dict[str, float]
        기본 소스별 가중치.

    Returns
    -------
    dict[str, float]
        조정된 소스별 가중치 (합계 불변).
    """
    w = dict(baseWeights)

    if lifecycle == "high_growth":
        # 컨센서스 의존도 높임
        if "consensus" in w and "timeseries" in w:
            shift = min(0.1, w["timeseries"])
            w["consensus"] += shift
            w["timeseries"] -= shift
    elif lifecycle == "mature":
        # ROIC, 시계열에 더 의존
        if "roic" in w and "consensus" in w:
            shift = min(0.05, w["consensus"])
            w["roic"] += shift
            w["consensus"] -= shift
    elif lifecycle == "transition":
        # 넓은 신뢰구간 (여기서는 가중치보다 confidence에 반영)
        if "consensus" in w and "timeseries" in w:
            shift = min(0.1, w["timeseries"])
            w["consensus"] += shift
            w["timeseries"] -= shift
    # decline: 기본 가중치 유지 (시계열 mean_revert가 이미 보수적)

    return w


# ══════════════════════════════════════
# 앙상블 가중치 계산
# ══════════════════════════════════════


def _computeWeights(
    tsAvailable: bool,
    consensusItems: list[tuple[int, float, str]],
    roicGrowth: float | None,
    structuralBreak: dict | None = None,
) -> dict[str, float]:
    """앙상블 소스별 가중치 계산.

    structuralBreak가 전달되면 구조변화 심각도에 따라
    시계열 가중치를 삭감하고 컨센서스로 이전한다.

    Parameters
    ----------
    tsAvailable : bool
        시계열 예측 가용 여부.
    consensusItems : list[tuple[int, float, str]]
        (연도, 매출추정, 소스) 튜플 리스트.
    roicGrowth : float | None
        ROIC 기반 내재 성장률 (%).
    structuralBreak : dict, optional
        구조변화 분석 결과.

    Returns
    -------
    dict[str, float]
        소스명 → 가중치 매핑 ("timeseries", "consensus", "roic" 등).
    """
    weights: dict[str, float] = {}

    hasConsensusEst = any(src.endswith("_consensus") for _, _, src in consensusItems)

    if tsAvailable and hasConsensusEst:
        weights["timeseries"] = 0.40
        weights["consensus"] = 0.45
    elif hasConsensusEst:
        weights["consensus"] = 1.0
    else:
        weights["timeseries"] = 1.0

    # 구조변화 감지 시 시계열 가중치 삭감
    if structuralBreak and "timeseries" in weights:
        revenueBreak = any(m.get("hasBreak") for m in structuralBreak.get("metrics", []) if m.get("name") == "revenue")
        stability = structuralBreak.get("overallStability", "stable")

        if revenueBreak or stability == "volatile":
            # volatile(2+ breaks): 60% 삭감, transitioning(1 break): 40% 삭감
            penalty = 0.6 if stability == "volatile" else 0.4
            reduction = weights["timeseries"] * penalty
            weights["timeseries"] -= reduction
            if "consensus" in weights:
                weights["consensus"] += reduction
            # consensus 없으면 삭감만 (총 가중치 < 1.0 → 정규화에서 보정)

    # ROIC 소스: 시계열에서 할당
    if roicGrowth is not None and "timeseries" in weights:
        roicShare = min(_ROIC_WEIGHT, weights["timeseries"])
        weights["roic"] = roicShare
        weights["timeseries"] -= roicShare

    return weights
