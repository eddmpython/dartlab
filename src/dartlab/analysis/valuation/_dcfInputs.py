"""DCF helpers — 12 데이터 추출/정규화/프로젝션 헬퍼.

_getFcfFromSeries / _getNetDebt / _fcfHistory — series → FCF/순차입금 추출.
_normalizeBaseFcf / _fallbackOcfBasedFcf / _fallbackNormalizedEarningsFcf / _resolveBaseFcf — base FCF 정규화.
_projectFcf / _computeExitMultipleTv — DCF 프로젝션.
_normalizedEarnings — 정상화 이익.
_estimateSectorPsr / _epsGrowth3Y — 가치 헬퍼.

dcf.py 의 god module 분리 일환. public 7 valuation 함수가 import 로 호출.
"""

from __future__ import annotations

from typing import Optional

from dartlab.core.utils.calc import cagr as _cagr
from dartlab.core.utils.extract import getAnnualValues, getLatest, getRevenueGrowth3Y, getTTM
from dartlab.frame.sector import SectorParams


def _getFcfFromSeries(series: dict, annual: bool = False) -> Optional[float]:
    """FCF = 영업CF - CAPEX."""
    flow = getLatest if annual else getTTM
    ocf = flow(series, "CF", "operating_cashflow")
    capex = flow(series, "CF", "purchase_of_property_plant_and_equipment")
    if ocf is None:
        return None
    return ocf - abs(capex or 0)


def _getNetDebt(series: dict) -> float:
    """순차입금 = 총차입금 - 현금."""
    stb = getLatest(series, "BS", "shortterm_borrowings") or 0
    ltb = getLatest(series, "BS", "longterm_borrowings") or 0
    bonds = getLatest(series, "BS", "debentures") or 0
    cash = getLatest(series, "BS", "cash_and_cash_equivalents") or 0
    return stb + ltb + bonds - cash


def _fcfHistory(series: dict) -> list[Optional[float]]:
    """연간 FCF 시계열 (영업CF - CAPEX)."""
    ocfVals = getAnnualValues(series, "CF", "operating_cashflow")
    capexVals = getAnnualValues(series, "CF", "purchase_of_property_plant_and_equipment")
    if not ocfVals:
        return []
    result: list[Optional[float]] = []
    for i in range(len(ocfVals)):
        o = ocfVals[i]
        c = capexVals[i] if i < len(capexVals) else None
        if o is None:
            result.append(None)
        else:
            result.append(o - abs(c or 0))
    return result


def _normalizeBaseFcf(series: dict, fcfCurrent: float | None, fcfHist: list, warnings: list[str]) -> float | None:
    """사이클 기업 mid-cycle FCF 정규화. 최근 FCF 가 극단 왜곡이면 중앙값 채택."""
    positiveFcfs = [f for f in fcfHist if f is not None and f > 0]
    if len(positiveFcfs) < 3:
        return fcfCurrent
    midCycleFcf = sorted(positiveFcfs)[len(positiveFcfs) // 2]
    if fcfCurrent is not None and fcfCurrent > 0:
        ratio = fcfCurrent / midCycleFcf if midCycleFcf > 0 else 1
        if ratio > 1.8 or ratio < 0.5:
            warnings.append(f"사이클 정규화: mid-cycle FCF 적용 (최근 대비 {ratio:.1f}배 괴리)")
            return midCycleFcf
        return fcfCurrent
    warnings.append("FCF 음수 → mid-cycle 양수 FCF 중앙값으로 대체")
    return midCycleFcf


def _fallbackOcfBasedFcf(series: dict, warnings: list[str]) -> float | None:
    """FCF 부재 시 영업CF × 할인률 fallback (호황기 과대 방지)."""
    ocfHist = getAnnualValues(series, "CF", "operating_cashflow")
    positiveOcfs = [v for v in ocfHist if v is not None and v > 0]
    allOcfs = [v for v in ocfHist if v is not None]
    if len(positiveOcfs) >= 3:
        midOcf = sorted(positiveOcfs)[len(positiveOcfs) // 2]
        lossRatio = 1 - len(positiveOcfs) / max(len(allOcfs), 1) if allOcfs else 0
        discount = 0.5 if lossRatio >= 0.5 else 0.7
        warnings.append(f"FCF 음수 → mid-cycle 영업CF × {discount * 100:.0f}%로 대체 (적자비율 {lossRatio * 100:.0f}%)")
        return midOcf * discount
    ocf = getTTM(series, "CF", "operating_cashflow")
    if ocf is not None and ocf > 0:
        warnings.append("FCF 음수/미확인 → 영업CF × 70%로 대체 추정")
        return ocf * 0.7
    return None


def _fallbackNormalizedEarningsFcf(series: dict, warnings: list[str]) -> float | None:
    """Damodaran normalized earnings — 정상 OPM × 현재 매출 → FCF proxy."""
    oiHist = getAnnualValues(series, "IS", "operating_profit")
    revHist = getAnnualValues(series, "IS", "sales")
    if not (oiHist and revHist):
        return None
    margins = [
        oi / rev for oi, rev in zip(oiHist, revHist) if oi is not None and rev is not None and rev > 0 and oi > 0
    ]
    if not margins:
        return None
    normalMargin = sorted(margins)[len(margins) // 2]
    latestRev = next((v for v in reversed(revHist) if v is not None and v > 0), None)
    if not (latestRev and normalMargin > 0):
        return None
    warnings.append(f"Normalized earnings: 정상 OPM {normalMargin * 100:.1f}% × 현재 매출 → FCF proxy")
    return latestRev * normalMargin * 0.65


def _resolveBaseFcf(series: dict, warnings: list[str]) -> tuple[float | None, list]:
    """기준 FCF 결정: series → mid-cycle → OCF fallback → normalized earnings."""
    fcfCurrent = _getFcfFromSeries(series)
    fcfHist = _fcfHistory(series)
    fcfCurrent = _normalizeBaseFcf(series, fcfCurrent, fcfHist, warnings)
    if fcfCurrent is None or fcfCurrent <= 0:
        fcfCurrent = _fallbackOcfBasedFcf(series, warnings)
    if fcfCurrent is None or fcfCurrent <= 0:
        fcfCurrent = _fallbackNormalizedEarningsFcf(series, warnings)
    return fcfCurrent, fcfHist


def _projectFcf(
    fcfCurrent: float,
    initialGrowth: float,
    tg: float,
    projectionYears: int,
    proformaFCF: list[float] | None,
    warnings: list[str],
) -> list[float]:
    """Pro Forma 우선 → 아니면 (initialGrowth → tg) blend 로 FCF 시계열 예측."""
    if proformaFCF and len(proformaFCF) > 0:
        pf = [float(f) for f in proformaFCF if f is not None and float(f) != 0]
        if pf:
            while len(pf) < projectionYears:
                pf.append(pf[-1] * (1 + tg / 100))
            warnings.append(f"추정재무제표(Pro Forma) 기반 FCF 사용 ({len(proformaFCF)}년 원본 + 연장)")
            return pf[:projectionYears]

    projections: list[float] = []
    prevFcf = fcfCurrent
    for yr in range(1, projectionYears + 1):
        blend = (yr - 1) / max(projectionYears - 1, 1)
        growth = initialGrowth * (1 - blend) + tg * blend
        proj = prevFcf * (1 + growth / 100)
        projections.append(proj)
        prevFcf = proj
    return projections


def _computeExitMultipleTv(
    series: dict,
    sectorParams: SectorParams | None,
    initialGrowth: float,
    tg: float,
    projectionYears: int,
    wacc: float,
    pvFcfs: float,
    netDebt: float,
    shares: int | None,
) -> tuple[float | None, float | None, float | None, float | None]:
    """Exit Multiple TV 교차검증 — EBITDA × 섹터 exit multiple. (tv, ev, perShare, mult)."""
    exitMult = sectorParams.exitMultiple if sectorParams and sectorParams.exitMultiple else None
    if not (exitMult and exitMult > 0):
        return None, None, None, None
    oi = getTTM(series, "IS", "operating_profit") or getTTM(series, "IS", "operating_income")
    if oi is None or oi <= 0:
        return None, None, None, exitMult
    dep = getTTM(series, "CF", "depreciation_and_amortization")
    if dep is None:
        ta = getLatest(series, "BS", "tangible_assets") or 0
        ia = getLatest(series, "BS", "intangible_assets") or 0
        dep = ta * 0.05 + ia * 0.1
    ebitda = oi + (dep or 0)
    if ebitda <= 0:
        return None, None, None, exitMult
    projEbitda = ebitda
    for yr in range(1, projectionYears + 1):
        blend = (yr - 1) / max(projectionYears - 1, 1)
        g = initialGrowth * (1 - blend) + tg * blend
        projEbitda *= 1 + g / 100
    exitTv = projEbitda * exitMult
    pvExitTv = exitTv / (1 + wacc / 100) ** projectionYears
    exitEv = pvFcfs + pvExitTv
    exitEqValue = exitEv - netDebt
    exitPerShare = exitEqValue / shares if shares and shares > 0 else None
    return exitTv, exitEv, exitPerShare, exitMult


def _normalizedEarnings(series: dict, shares: int | None) -> tuple[float | None, float | None, bool]:
    """경기순환 조정 정규화 수익 -- Damodaran/CFA 표준.

    방법: 과거 3-5년 평균 ROE x 현재 BPS (mid-cycle earnings)
    Returns: (normalizedNI, normalizedEps, wasNormalized)
    """
    niVals = getAnnualValues(series, "IS", "net_profit")
    if not niVals:
        niVals = getAnnualValues(series, "IS", "net_income")
    eqVals = getAnnualValues(series, "BS", "total_stockholders_equity")
    if not eqVals:
        eqVals = getAnnualValues(series, "BS", "owners_of_parent_equity")

    if not niVals or not eqVals or len(niVals) < 3 or len(eqVals) < 3:
        return None, None, False

    # 최근 3-5년 ROE 평균
    n = min(len(niVals), len(eqVals), 5)
    roes: list[float] = []
    for i in range(-n, 0):
        ni = niVals[i] if abs(i) <= len(niVals) else None
        eq = eqVals[i] if abs(i) <= len(eqVals) else None
        if ni is not None and eq is not None and eq > 0:
            roes.append(ni / eq)

    if len(roes) < 2:
        return None, None, False

    avgRoe = sum(roes) / len(roes)
    currentEquity = eqVals[-1]
    if currentEquity is None or currentEquity <= 0:
        return None, None, False

    normalizedNi = currentEquity * avgRoe
    normalizedEps = normalizedNi / shares if shares and shares > 0 else None

    # TTM 대비 30% 이상 차이나면 정규화 적용
    ttmNi = getTTM(series, "IS", "net_profit") or getTTM(series, "IS", "net_income")
    if ttmNi and ttmNi > 0 and normalizedNi > 0:
        divergence = abs(ttmNi - normalizedNi) / max(ttmNi, normalizedNi)
        return normalizedNi, normalizedEps, divergence > 0.3

    return normalizedNi, normalizedEps, True


def _estimateSectorPsr(sp: SectorParams) -> float:
    """섹터 PSR 추정 -- PER × 순이익률 가정으로 역산."""
    # 일반적으로 PSR = PER × 순이익률
    # 순이익률 모르면 섹터 평균 5% 가정
    estimatedMargin = 0.05
    psr = sp.perMultiple * estimatedMargin
    return round(max(psr, 0.3), 2)


def _epsGrowth3Y(series: dict, shares: int) -> Optional[float]:
    """EPS 3년 CAGR (%)."""
    niVals = getAnnualValues(series, "IS", "net_profit")
    if not niVals:
        niVals = getAnnualValues(series, "IS", "net_income")
    if not niVals or len(niVals) < 4 or shares <= 0:
        return None

    recent = niVals[-4:]
    validNi = [v for v in recent if v is not None and v > 0]
    if len(validNi) < 2:
        return None

    epsStart = validNi[0] / shares
    epsEnd = validNi[-1] / shares
    if epsStart <= 0 or epsEnd <= 0:
        return None

    years = len(validNi) - 1
    cagr = _cagr(epsStart, epsEnd, years)
    # PEG 산출용 상한: 50% (사이클 기업 적자→흑전 시 수천% 방지)
    return min(cagr, 50.0) if cagr is not None else None


# ── 민감도 분석 ──────────────────────────────────────────────


__all__ = [
    "_computeExitMultipleTv",
    "_epsGrowth3Y",
    "_estimateSectorPsr",
    "_fallbackNormalizedEarningsFcf",
    "_fallbackOcfBasedFcf",
    "_fcfHistory",
    "_getFcfFromSeries",
    "_getNetDebt",
    "_normalizedEarnings",
    "_normalizeBaseFcf",
    "_projectFcf",
    "_resolveBaseFcf",
]
