"""매출액 예측 엔진 v4 — 4-소스 앙상블 + 세그먼트 Bottom-Up + 시나리오.

4-소스 앙상블:
1. 자체 시계열 (과거 매출 OLS/CAGR/평균회귀)
2. 시장 컨센서스 (네이버/Yahoo 금융 애널리스트 매출 추정치)
3. ROIC 기반 내재 성장 (Damodaran Value Driver: g = ROIC × Reinvestment Rate)
4. 세그먼트 Bottom-Up (부문별 개별 예측 → 합산)
+ 수주잔고 선행지표 (B/R ratio → 내재 성장률, 전 종목 적용)

v3→v4 변경 (실험 098 기반):
- 매크로 GDP β 제거 (기여도 0%, 오히려 악화)
- FX regex 제거 (29% 성공률)
- 주가내재 역산 제거 (순환논리)
- 횡단면 회귀 제거 (비활성)
- 공시 tone 제거 (미검증)

설계 원칙 (Engine-First, AI-Augmented):
- 엔진이 재현 가능하고 투명한 기본 예측을 생성
- ai_context 필드로 AI가 세계 지식으로 보정할 수 있는 브릿지 제공
- 결과 스키마는 도메인(DART/EDGAR/EDINET) 불문 동일
- 3-시나리오 출력 (Base/Bull/Bear)으로 불확실성 정량화
- CompanyDataBundle로 L1 데이터를 L0에 전달 (L0→L1 import 금지)

외부 의존성: gather 엔진 (optional — 없으면 시계열 only).
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    import polars as pl

from dartlab.analysis.forecast.forecast import (
    forecastMetric,
)
from dartlab.core.finance.extract import (
    getAnnualValues,
    getLatest,
    getTTM,
)
from dartlab.core.finance.fmt import fmtBig

log = logging.getLogger(__name__)

# ROIC 기반 성장 소스 가중치 (시계열에서 할당)
_ROIC_WEIGHT = 0.15


# ══════════════════════════════════════
# L1 → L0 데이터 브릿지
# ══════════════════════════════════════


@dataclass
class CompanyDataBundle:
    """L1(Company) → L0(forecast) 데이터 브릿지."""

    segmentRevenue: pl.DataFrame | None = None  # c.segments.revenue
    salesDf: pl.DataFrame | None = None  # c.salesOrder.salesDf
    orderDf: pl.DataFrame | None = None  # c.salesOrder.orderDf
    structuralBreak: dict | None = None  # calcStructuralBreak() 결과


@dataclass
class SegmentForecast:
    """개별 세그먼트 예측 결과."""

    name: str
    historical: list[Optional[float]]
    projected: list[float]
    growthRates: list[float]
    method: str
    shareOfRevenue: float  # 최근 매출 비중 (%, 0~100)
    lifecycle: str


@dataclass
class BacklogSignal:
    """수주잔고 기반 선행 시그널."""

    backlogRevenueRatio: float  # 현재 B/R ratio
    brRatioTrend: str  # "increasing" | "stable" | "declining"
    impliedRevenueGrowth: float  # 수주잔고 기반 내재 매출 성장률 (%)
    conversionRate: float  # 과거 평균 수주→매출 전환율
    sectorsApplicable: bool  # 건설/조선/방산만 강신호


@dataclass
class RevenueForecastAIOverlay:
    """AI 보정 결과 — 구조화된 스키마."""

    growthAdjustment: list[float]  # 연도별 %p 보정
    direction: str  # "up" | "down" | "neutral"
    magnitude: str  # "minor" (<2%p) | "moderate" (2-5%p) | "major" (>5%p)
    scenarioShift: dict[str, float] | None = None  # 시나리오 확률 이동
    reasoning: list[str] = field(default_factory=list)  # 보정 근거
    applied: bool = False


# ══════════════════════════════════════
# 결과 타입
# ══════════════════════════════════════


@dataclass
class RevenueForecastResult:
    """매출 예측 결과 — 소스별 기여도 투명 공개."""

    historical: list[Optional[float]]
    projected: list[float]
    horizon: int
    method: str  # "ensemble" | "timeseries_only" | "consensus_only" | "N/A"
    confidence: str  # "high" | "medium" | "low"
    growthRates: list[float]  # 연도별 YoY 성장률 (%)
    sources: list[str]  # ["timeseries", "consensus", "macro", "roic"]
    sourceWeights: dict[str, float]  # {"timeseries": 0.4, "consensus": 0.45, ...}
    consensusRevenue: list[float] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    aiContext: dict = field(default_factory=dict)

    # v3 확장 필드 (전부 default — 하위호환)
    scenarios: dict[str, list[float]] = field(default_factory=dict)  # base/bull/bear
    scenarioGrowthRates: dict[str, list[float]] = field(default_factory=dict)
    scenarioProbabilities: dict[str, float] = field(default_factory=dict)
    segmentForecasts: list[SegmentForecast] = field(default_factory=list)
    backlogSignal: BacklogSignal | None = None
    aiOverlay: RevenueForecastAIOverlay | None = None
    forwardTestKey: str | None = None
    currency: str = "KRW"

    # v4: 예측 불가능성 명시 (네이트 실버 — 예측할 수 없는 것을 예측하지 마라)
    forecastable: bool = True
    unforecastableReason: str = ""

    DISCLAIMER: str = "본 분석은 투자 참고용이며 투자 권유가 아닙니다."

    def __repr__(self) -> str:
        cur = self.currency
        lines = [f"[매출 예측 — {self.method}]"]
        lines.append(f"  신뢰도: {self.confidence}")
        lc = self.aiContext.get("lifecycle", "")
        if lc:
            lines.append(f"  라이프사이클: {lc}")
        lines.append(f"  소스: {', '.join(f'{k}({v:.0%})' for k, v in self.sourceWeights.items())}")

        validHist = [v for v in self.historical if v is not None]
        if self.projected and validHist:
            base = (
                self.projected[0] / (1 + self.growthRates[0] / 100)
                if self.growthRates and self.growthRates[0] != -100
                else validHist[-1]
            )
            lines.append(f"  기준 매출: {fmtBig(base, cur)}")
        elif validHist:
            lines.append(f"  최근 실적: {fmtBig(validHist[-1], cur)}")

        for i, (proj, gr) in enumerate(zip(self.projected, self.growthRates), 1):
            lines.append(f"  +{i}년: {fmtBig(proj, cur)} ({gr:+.1f}%)")

        # v3: 시나리오
        if self.scenarios:
            probs = self.scenarioProbabilities
            for label in ("bull", "bear"):
                sc = self.scenarios.get(label, [])
                sg = self.scenarioGrowthRates.get(label, [])
                prob = probs.get(label, 0)
                if sc:
                    lines.append(
                        f"  {label.title()}({prob:.0f}%): {fmtBig(sc[0], cur)} ({sg[0]:+.1f}%)"
                        if sg
                        else f"  {label.title()}: {fmtBig(sc[0], cur)}"
                    )

        # v3: 세그먼트
        if self.segmentForecasts:
            lines.append(f"  세그먼트: {len(self.segmentForecasts)}개 부문")
            for sf in self.segmentForecasts[:3]:  # 상위 3개만 표시
                if sf.projected:
                    lines.append(
                        f"    {sf.name}({sf.shareOfRevenue:.0f}%): {fmtBig(sf.projected[0], cur)} ({sf.growthRates[0]:+.1f}%)"
                        if sf.growthRates
                        else f"    {sf.name}: {fmtBig(sf.projected[0], cur)}"
                    )

        # v3: 수주잔고
        if self.backlogSignal:
            bs = self.backlogSignal
            lines.append(
                f"  수주잔고: B/R={bs.backlogRevenueRatio:.1f}x ({bs.brRatioTrend}), 내재 성장 {bs.impliedRevenueGrowth:+.1f}%"
            )

        if self.assumptions:
            for a in self.assumptions:
                lines.append(f"  · {a}")
        if self.warnings:
            for w in self.warnings:
                lines.append(f"  ⚠ {w}")
        lines.append(f"  ※ {self.DISCLAIMER}")
        return "\n".join(lines)


# ══════════════════════════════════════
# 컨센서스 매출 추출
# ══════════════════════════════════════


def _fetchConsensusRevenue(
    stockCode: str,
    market: str = "KR",
) -> list[tuple[int, float, str]]:
    """gather에서 매출 컨센서스를 가져온다."""
    try:
        from dartlab.gather import Gather

        g = Gather()
        items = g.revenue_consensus(stockCode, market=market)
        try:
            g.close()
        except RuntimeError:
            pass  # event loop already closed
        return [(item.fiscal_year, item.revenue_est, item.source) for item in items if item.revenue_est > 0]
    except (ImportError, OSError) as exc:
        log.debug("컨센서스 수집 실패: %s", exc)
        return []


# ══════════════════════════════════════
# ROIC 기반 내재 성장률 (Damodaran Value Driver)
# ══════════════════════════════════════


def _fundamentalGrowth(series: dict) -> tuple[float | None, dict]:
    """ROIC × Reinvestment Rate → 내재 성장률."""
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
    """기업 라이프사이클 단계 판별."""
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
    """라이프사이클에 따른 가중치 조정."""
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
    """소스별 가중치 계산.

    structuralBreak가 전달되면 구조변화 심각도에 따라
    시계열 가중치를 삭감하고 컨센서스로 이전한다.
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


# ══════════════════════════════════════
# 세그먼트 Bottom-Up 예측
# ══════════════════════════════════════

# 세그먼트 가중치: 시계열에서 할당
_SEGMENT_WEIGHT = 0.25

# 수주잔고 선행 시그널 가중치
_BACKLOG_WEIGHT = 0.15


def _extractSegmentForecasts(
    segmentRevenue: object,  # pl.DataFrame | None (TYPE_CHECKING 회피)
    horizon: int = 3,
) -> list[SegmentForecast]:
    """세그먼트별 개별 시계열 예측."""
    if segmentRevenue is None:
        return []

    import importlib.util

    if importlib.util.find_spec("polars") is None:
        return []

    df = segmentRevenue
    if not hasattr(df, "columns") or "부문" not in df.columns:
        return []

    # 연도 컬럼 추출 (숫자만)
    yearCols = sorted(
        [c for c in df.columns if c != "부문" and c.isdigit()],
        key=int,
    )
    if len(yearCols) < 3:
        return []

    totalLatest = 0.0
    segmentLatest: dict[str, float] = {}

    results: list[SegmentForecast] = []
    for row in df.iter_rows(named=True):
        name = row.get("부문", "")
        if not name:
            continue

        # 시계열 추출 (오래된 순서로)
        vals = [row.get(y) for y in yearCols]
        valid = [(i, v) for i, v in enumerate(vals) if v is not None and v > 0]
        if len(valid) < 3:
            continue

        # 최근 매출 (비중 계산용)
        latest = valid[-1][1]
        segmentLatest[name] = latest
        totalLatest += latest

        # forecastMetric에 넣기 위한 가짜 series dict 구성
        fakeSeries = {
            "IS": {"sales": [v for _, v in valid]},
        }
        fr = forecastMetric(fakeSeries, "revenue", horizon)
        if not fr.projected:
            continue

        # 라이프사이클 판정
        lc, _ = _classifyLifecycle(fakeSeries)

        # 성장률 계산
        growthRates: list[float] = []
        prevVal = latest
        for p in fr.projected:
            if prevVal > 0:
                growthRates.append(round((p / prevVal - 1) * 100, 1))
            else:
                growthRates.append(0.0)
            prevVal = p

        results.append(
            SegmentForecast(
                name=name,
                historical=[v for _, v in valid],
                projected=fr.projected,
                growthRates=growthRates,
                method=fr.method,
                shareOfRevenue=0.0,  # 후처리에서 계산
                lifecycle=lc,
            )
        )

    # 비중 계산
    if totalLatest > 0:
        for sf in results:
            latestRev = segmentLatest.get(sf.name, 0)
            sf.shareOfRevenue = round(latestRev / totalLatest * 100, 1)

    # 비중 내림차순 정렬
    results.sort(key=lambda x: x.shareOfRevenue, reverse=True)
    return results


def _segmentBottomUpGrowth(
    segmentForecasts: list[SegmentForecast],
    horizon: int,
    lastRevenue: float | None,
) -> list[float]:
    """세그먼트별 예측을 합산하여 Bottom-Up 성장률 시계열 생성."""
    if not segmentForecasts or not lastRevenue or lastRevenue <= 0:
        return []

    growthRates: list[float] = []
    # 세그먼트 합산: 각 연도별 세그먼트 projected 합
    prevTotal = sum(sf.historical[-1] for sf in segmentForecasts if sf.historical)
    if prevTotal <= 0:
        return []

    for yr in range(horizon):
        yrTotal = 0.0
        for sf in segmentForecasts:
            if yr < len(sf.projected):
                yrTotal += sf.projected[yr]
            elif sf.projected:
                yrTotal += sf.projected[-1]
        if prevTotal > 0:
            growthRates.append((yrTotal / prevTotal - 1) * 100)
        else:
            growthRates.append(0.0)
        prevTotal = yrTotal

    return growthRates


# ══════════════════════════════════════
# 수주잔고 선행지표 (Source 6)
# ══════════════════════════════════════


def _computeBacklogSignal(
    orderDf: object,  # pl.DataFrame | None
    salesDf: object,  # pl.DataFrame | None
    sectorKey: str | None = None,
) -> BacklogSignal | None:
    """수주잔고 기반 선행 시그널 계산."""
    if orderDf is None or salesDf is None:
        return None

    if not hasattr(orderDf, "columns") or not hasattr(salesDf, "columns"):
        return None

    try:
        # 수주잔고 합산 (모든 행의 마지막 value 컬럼 합)
        orderValCols = [c for c in orderDf.columns if c != "label"]
        salesValCols = [c for c in salesDf.columns if c != "label"]

        if not orderValCols or not salesValCols:
            return None

        # 최신 기간 수주잔고 합산
        latestOrderCol = orderValCols[0]  # 첫 컬럼이 최근
        latestSalesCol = salesValCols[0]

        orderTotal = 0.0
        for row in orderDf.iter_rows(named=True):
            v = row.get(latestOrderCol)
            if v is not None and isinstance(v, (int, float)):
                orderTotal += abs(v)

        salesTotal = 0.0
        for row in salesDf.iter_rows(named=True):
            v = row.get(latestSalesCol)
            if v is not None and isinstance(v, (int, float)):
                salesTotal += abs(v)

        if salesTotal <= 0 or orderTotal <= 0:
            return None

        brRatio = orderTotal / salesTotal

        # B/R ratio 추세 (2기간 이상 필요)
        brRatios: list[float] = []
        nPeriods = min(len(orderValCols), len(salesValCols))
        for i in range(min(nPeriods, 3)):
            oCol = orderValCols[i]
            sCol = salesValCols[i]
            oSum = sum(
                abs(row.get(oCol, 0) or 0)
                for row in orderDf.iter_rows(named=True)
                if isinstance(row.get(oCol), (int, float))
            )
            sSum = sum(
                abs(row.get(sCol, 0) or 0)
                for row in salesDf.iter_rows(named=True)
                if isinstance(row.get(sCol), (int, float))
            )
            if sSum > 0:
                brRatios.append(oSum / sSum)

        # 추세 판단
        if len(brRatios) >= 2:
            if brRatios[0] > brRatios[-1] * 1.05:
                trend = "increasing"
            elif brRatios[0] < brRatios[-1] * 0.95:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "stable"

        # 내재 매출 성장률: B/R ratio 변화 → 매출 성장 추정
        if len(brRatios) >= 2 and brRatios[-1] > 0:
            impliedGrowth = (brRatios[0] / brRatios[-1] - 1) * 100
        else:
            impliedGrowth = 0.0

        # 전환율: 역사적 평균 (매출/수주잔고)
        conversionRate = 1.0 / brRatio if brRatio > 0 else 0.0

        # 건설/조선/방산: 수주잔고가 특히 강한 선행지표인 섹터 (정보 목적)
        _strongSectors = {"건설", "조선", "방산", "건설/토목", "조선/기계"}
        isApplicable = bool(sectorKey and any(s in sectorKey for s in _strongSectors))

        return BacklogSignal(
            backlogRevenueRatio=round(brRatio, 2),
            brRatioTrend=trend,
            impliedRevenueGrowth=round(impliedGrowth, 1),
            conversionRate=round(conversionRate, 3),
            sectorsApplicable=isApplicable,
        )
    except (TypeError, ValueError, KeyError):
        return None


# ══════════════════════════════════════
# 3-시나리오 빌더 (Base/Bull/Bear)
# ══════════════════════════════════════

# 라이프사이클별 spread 배수 (1σ 대비)
_LIFECYCLE_SPREAD = {
    "high_growth": 1.5,
    "mature": 0.7,
    "transition": 2.0,
    "decline": 1.2,
    "unknown": 1.0,
}


def _buildScenarios(
    projected: list[float],
    growthRates: list[float],
    historical: list[Optional[float]],
    lifecycle: str,
    lastRevenue: float | None,
    structuralBreak: dict | None = None,
) -> tuple[dict[str, list[float]], dict[str, list[float]], dict[str, float]]:
    """Base/Bull/Bear 3-시나리오 생성."""
    if not projected or not lastRevenue or lastRevenue <= 0:
        return {}, {}, {}

    # 과거 성장률 변동성 (σ) 계산
    validHist = [v for v in historical if v is not None and v > 0]
    histGrowth: list[float] = []
    for i in range(1, len(validHist)):
        if validHist[i - 1] > 0:
            histGrowth.append((validHist[i] / validHist[i - 1] - 1) * 100)

    if histGrowth:
        meanG = sum(histGrowth) / len(histGrowth)
        variance = sum((g - meanG) ** 2 for g in histGrowth) / max(len(histGrowth) - 1, 1)
        sigma = math.sqrt(variance)
    else:
        sigma = 5.0  # 기본 5%p

    # 최소 sigma 보장 (너무 좁은 밴드 방지)
    sigma = max(sigma, 3.0)

    spread = _LIFECYCLE_SPREAD.get(lifecycle, 1.0)

    scenarios: dict[str, list[float]] = {"base": list(projected)}
    scenarioGrs: dict[str, list[float]] = {"base": list(growthRates)}

    # Bull / Bear
    for label, direction in [("bull", 1.0), ("bear", -1.0)]:
        scProjected: list[float] = []
        scGrs: list[float] = []
        prev = lastRevenue
        for i, gr in enumerate(growthRates):
            # 시간 감쇠: 멀수록 불확실성 증가
            timeFactor = 1.0 + i * 0.15
            adjGr = gr + direction * sigma * spread * timeFactor
            # Bull cap: 2× base growth, Bear floor: -base growth (mature 이상)
            if direction > 0:
                adjGr = min(adjGr, max(gr * 2, gr + 20))
            else:
                if lifecycle != "decline":
                    adjGr = max(adjGr, min(gr * 0.5, gr - 20))
            val = prev * (1 + adjGr / 100)
            scProjected.append(val)
            scGrs.append(round(adjGr, 1))
            prev = val
        scenarios[label] = scProjected
        scenarioGrs[label] = scGrs

    # 구조변화 감지 시 시나리오 확률 조정 (하방 리스크 확대)
    stability = structuralBreak.get("overallStability", "stable") if structuralBreak else "stable"
    if stability == "volatile":
        probabilities = {"base": 40.0, "bull": 20.0, "bear": 40.0}
    elif stability == "transitioning":
        probabilities = {"base": 45.0, "bull": 22.0, "bear": 33.0}
    else:
        probabilities = {"base": 50.0, "bull": 25.0, "bear": 25.0}

    return scenarios, scenarioGrs, probabilities


# ══════════════════════════════════════
# 메인 예측 함수
# ══════════════════════════════════════


def forecastRevenue(
    series: dict,
    stockCode: str | None = None,
    sectorKey: str | None = None,
    market: str = "KR",
    horizon: int = 3,
    companyData: CompanyDataBundle | None = None,
    currency: str = "KRW",
) -> RevenueForecastResult:
    """매출액 앙상블 예측."""
    warnings: list[str] = []
    assumptions: list[str] = []

    # ── 라이프사이클 판별 ──
    lifecycle, lifecycleDetail = _classifyLifecycle(series)

    # ── Source 1: 시계열 예측 (기존 forecast.py) ──
    tsResult = forecastMetric(series, "revenue", horizon)
    tsAvailable = len(tsResult.projected) > 0

    # 과거 매출 시계열 (revenue 키 조회)
    historical = tsResult.historical

    # 최근 매출 (앙상블 기준점)
    validHist = [v for v in historical if v is not None]
    lastRevenue = validHist[-1] if validHist else None

    # ── Source 2: 컨센서스 (KR: 네이버, US+: Yahoo) ──
    consensusItems: list[tuple[int, float, str]] = []
    if stockCode:
        consensusItems = _fetchConsensusRevenue(stockCode, market)
        if not consensusItems and market != "KR":
            warnings.append(f"컨센서스 수집 실패({market}) — 시계열 기반 예측")

    # ── Source 4: ROIC 기반 내재 성장 ──
    roicGrowth, roicDetail = _fundamentalGrowth(series)
    roicGrowthRate: float | None = roicGrowth  # % 단위

    # ── Source 5: 세그먼트 Bottom-Up ──
    segmentForecasts: list[SegmentForecast] = []
    segGrowthRates: list[float] = []
    if companyData and companyData.segmentRevenue is not None:
        segmentForecasts = _extractSegmentForecasts(
            companyData.segmentRevenue,
            horizon,
        )
        if segmentForecasts:
            segGrowthRates = _segmentBottomUpGrowth(
                segmentForecasts,
                horizon,
                lastRevenue,
            )

    # ── Source 6: 수주잔고 선행지표 ──
    backlogSignal: BacklogSignal | None = None
    if companyData and companyData.orderDf is not None:
        backlogSignal = _computeBacklogSignal(
            companyData.orderDf,
            companyData.salesDf,
            sectorKey,
        )

    # ── 가중치 계산 ──
    _sb = companyData.structuralBreak if companyData else None
    weights = _computeWeights(tsAvailable, consensusItems, roicGrowth, structuralBreak=_sb)

    # v3 소스 가중치 할당 (시계열에서 할당)
    if segGrowthRates and "timeseries" in weights:
        segShare = min(_SEGMENT_WEIGHT, weights["timeseries"])
        weights["segments"] = segShare
        weights["timeseries"] -= segShare

    if backlogSignal and "timeseries" in weights:
        blShare = min(_BACKLOG_WEIGHT, weights["timeseries"])
        weights["backlog"] = blShare
        weights["timeseries"] -= blShare

    # 시계열 최소 보장: 과도 희석 방지 (최소 0.10)
    _TS_FLOOR = 0.10
    if "timeseries" in weights and weights["timeseries"] < _TS_FLOOR:
        deficit = _TS_FLOOR - weights["timeseries"]
        weights["timeseries"] = _TS_FLOOR
        # 부족분을 다른 v3 소스에서 비례 차감
        v3Keys = [k for k in ("segments", "backlog") if k in weights and weights[k] > 0]
        if v3Keys:
            totalV3 = sum(weights[k] for k in v3Keys)
            for k in v3Keys:
                weights[k] -= deficit * (weights[k] / totalV3)
                weights[k] = max(weights[k], 0.0)

    # 라이프사이클 기반 가중치 조정
    weights = _lifecycleWeightAdjustments(lifecycle, weights)

    # 시계열 최소 보장 재확인 (라이프사이클 조정 후)
    if "timeseries" in weights and weights["timeseries"] < _TS_FLOOR:
        deficit = _TS_FLOOR - weights["timeseries"]
        weights["timeseries"] = _TS_FLOOR
        v3Keys2 = [k for k in ("segments", "backlog") if k in weights and weights[k] > 0]
        if v3Keys2:
            totalV3_2 = sum(weights[k] for k in v3Keys2)
            if totalV3_2 > 0:
                for k in v3Keys2:
                    weights[k] -= deficit * (weights[k] / totalV3_2)
                    weights[k] = max(weights[k], 0.0)

    # ── 앙상블 ──
    projected: list[float] = []
    consensusRevenue: list[float] = []

    # 컨센서스에서 전체 매출 시계열 (actual + estimate) 구축
    consensusByYear: dict[int, tuple[float, str]] = {}  # year → (revenue_원, source)
    if consensusItems:
        for fy, rev, src in consensusItems:
            if rev > 0:
                consensusByYear[fy] = (rev * 1e8, src)  # 억원 → 원

    # 컨센서스 estimate만 추출
    consensusProj: dict[int, float] = {}
    for fy, (revWon, src) in consensusByYear.items():
        if src.endswith("_consensus"):
            consensusProj[fy] = revWon
            consensusRevenue.append(revWon)

    # 기준 연도: 컨센서스 actual 중 가장 최근
    baseYear = 0
    lastActualRevenue: float | None = None
    actualsSorted = sorted(
        [(fy, rev) for fy, (rev, src) in consensusByYear.items() if src.endswith("_actual")],
        key=lambda x: x[0],
    )
    if actualsSorted:
        baseYear = actualsSorted[-1][0]
        lastActualRevenue = actualsSorted[-1][1]
    if baseYear == 0:
        baseYear = 2025

    # lastRevenue를 컨센서스 actual과 동기화 (더 신뢰할 수 있으므로)
    if lastActualRevenue:
        lastRevenue = lastActualRevenue

    # 시계열 성장률: projected 간 YoY 성장률 (분기 데이터이므로 자체 기준 비교)
    tsGrowthRates: list[float] = []
    if tsAvailable and tsResult.projected:
        prev = tsResult.historical[-1] if tsResult.historical and tsResult.historical[-1] else None
        for p in tsResult.projected:
            if prev and prev > 0 and p > 0:
                tsGrowthRates.append((p / prev - 1) * 100)
            else:
                tsGrowthRates.append(tsResult.growthRate)
            prev = p

    # 컨센서스 성장률 계산
    conGrowthRates: list[float] = []
    sortedConYears = sorted(consensusProj.keys())
    for i, fy in enumerate(sortedConYears):
        if i == 0:
            # 첫 컨센서스 연도: actual 대비 성장률
            if lastRevenue and lastRevenue > 0:
                conGrowthRates.append((consensusProj[fy] / lastRevenue - 1) * 100)
            else:
                conGrowthRates.append(0.0)
        else:
            prevFy = sortedConYears[i - 1]
            prevRev = consensusProj[prevFy]
            if prevRev > 0:
                conGrowthRates.append((consensusProj[fy] / prevRev - 1) * 100)
            else:
                conGrowthRates.append(0.0)

    # ROIC 성장률: horizon 동안 일정 (내재 성장은 구조적)
    roicG = roicGrowthRate if roicGrowthRate is not None else 0.0

    # ROIC vs 시계열 괴리 감지
    roicTsGap: float | None = None
    if roicGrowthRate is not None and tsGrowthRates:
        avgTsG = sum(tsGrowthRates) / len(tsGrowthRates)
        roicTsGap = roicGrowthRate - avgTsG
        if abs(roicTsGap) > 10:
            warnings.append(
                f"ROIC 내재 성장률({roicGrowthRate:.1f}%)과 시계열 성장률({avgTsG:.1f}%) 괴리 {roicTsGap:+.1f}%p"
            )

    # 앙상블: 성장률 기반 블렌딩 (스케일 불일치 방지)
    prevRevenue = lastRevenue or 0
    for yrOffset in range(1, horizon + 1):
        if prevRevenue <= 0:
            break

        # 시계열 성장률
        tsG = (
            tsGrowthRates[yrOffset - 1]
            if yrOffset <= len(tsGrowthRates)
            else (tsGrowthRates[-1] if tsGrowthRates else 0.0)
        )

        # 컨센서스 성장률
        conG = conGrowthRates[yrOffset - 1] if yrOffset <= len(conGrowthRates) else None

        # 가중 성장률 계산
        blendedGrowth = 0.0
        if conG is not None and "consensus" in weights:
            blendedGrowth += conG * weights.get("consensus", 0)
            blendedGrowth += tsG * weights.get("timeseries", 0)
        else:
            # 컨센서스 없는 연도 → 시계열이 컨센서스 몫도 흡수
            blendedGrowth += tsG * (weights.get("timeseries", 0) + weights.get("consensus", 0))

        blendedGrowth += roicG * weights.get("roic", 0)

        # 세그먼트 Bottom-Up 성장률
        if segGrowthRates and "segments" in weights:
            segG = (
                segGrowthRates[yrOffset - 1]
                if yrOffset <= len(segGrowthRates)
                else (segGrowthRates[-1] if segGrowthRates else 0.0)
            )
            blendedGrowth += segG * weights.get("segments", 0)

        # 수주잔고 내재 성장률
        if backlogSignal and "backlog" in weights:
            # 수주잔고 신호는 horizon 동안 감쇠
            decay = max(0.5, 1.0 - (yrOffset - 1) * 0.2)
            blendedGrowth += backlogSignal.impliedRevenueGrowth * decay * weights.get("backlog", 0)

        projVal = prevRevenue * (1 + blendedGrowth / 100)
        projected.append(projVal)
        prevRevenue = projVal

    # ── 스키마 보장: projected가 horizon보다 적으면 패딩 ──
    while len(projected) < horizon:
        if projected:
            projected.append(projected[-1])
        elif lastRevenue and lastRevenue > 0:
            projected.append(lastRevenue)
        else:
            projected.append(0.0)

    # ── 성장률 계산 ──
    growthRates: list[float] = []
    for i, proj in enumerate(projected):
        if i == 0 and lastRevenue and lastRevenue > 0:
            growthRates.append((proj / lastRevenue - 1) * 100)
        elif i > 0 and projected[i - 1] > 0:
            growthRates.append((proj / projected[i - 1] - 1) * 100)
        else:
            growthRates.append(0.0)

    while len(growthRates) < horizon:
        growthRates.append(0.0)

    # ── 메서드 & 신뢰도 결정 ──
    activeSources = [s for s in weights if weights[s] > 0]
    if not activeSources:
        activeSources = ["timeseries"]
    method = "ensemble" if len(activeSources) > 1 else f"{activeSources[0]}_only"

    # 신뢰도: 소스 수 + 시계열 R² + 컨센서스 유무 + 라이프사이클
    if len(activeSources) >= 3 and tsResult.rSquared > 0.5:
        confidence = "high"
    elif len(activeSources) >= 2 and (tsAvailable or consensusProj):
        confidence = "medium" if lifecycle != "transition" else "low"
    elif tsAvailable or consensusProj:
        confidence = "medium"
    else:
        confidence = "low"

    # transition → 최대 medium
    if lifecycle == "transition" and confidence == "high":
        confidence = "medium"

    # 비-KR 시장에서 컨센서스 없으면 → 최대 medium
    if market != "KR" and not consensusProj:
        if confidence == "high":
            confidence = "medium"

    # ── 예측 불가 판정 (2개 이상 조건 동시 충족 시 거부) ──
    _unfConditions: list[str] = []
    if confidence == "low" and lifecycle == "transition":
        _unfConditions.append("전환기 기업 + 낮은 신뢰도")
    if tsResult.rSquared < 0.1 and not consensusProj:
        _unfConditions.append("시계열 R²<0.1 + 컨센서스 없음")
    if _sb and _sb.get("overallStability") == "volatile" and confidence != "high":
        _unfConditions.append("다중 구조변화 + 높지 않은 신뢰도")

    _forecastable = len(_unfConditions) < 2
    _unfReason = "; ".join(_unfConditions) if not _forecastable else ""
    if not _forecastable:
        warnings.append(f"예측 불가 판정: {_unfReason}")

    # ── 스키마 보장: sourceWeights 합이 1.0 ──
    wSum = sum(v for v in weights.values() if v > 0)
    if wSum > 0 and abs(wSum - 1.0) > 0.01:
        for k in weights:
            if weights[k] > 0:
                weights[k] = weights[k] / wSum

    finalWeights = {k: round(v, 2) for k, v in weights.items() if v > 0}
    if not finalWeights:
        finalWeights = {"timeseries": 1.0}
    # 반올림 오차 보정: 가장 큰 가중치에 잔여분 할당
    wTotal = sum(finalWeights.values())
    if abs(wTotal - 1.0) > 0.001 and finalWeights:
        maxKey = max(finalWeights, key=finalWeights.get)  # type: ignore[arg-type]
        finalWeights[maxKey] = round(finalWeights[maxKey] + (1.0 - wTotal), 2)

    # ── 가정 설명 (정규화된 가중치 기준) ──
    for src, w in finalWeights.items():
        if w > 0:
            if src == "timeseries":
                assumptions.append(f"시계열({w:.0%}): {tsResult.method}, R²={tsResult.rSquared:.2f}")
            elif src == "consensus":
                nEst = len(consensusProj)
                assumptions.append(f"컨센서스({w:.0%}): 네이버 금융 {nEst}개년 추정치")
            elif src == "roic":
                assumptions.append(f"ROIC({w:.0%}): g=ROIC×재투자율={roicGrowthRate:.1f}%")

    if lifecycle != "unknown":
        assumptions.append(
            f"라이프사이클: {lifecycle} (CAGR {lifecycleDetail.get('cagr_3y', 'N/A')}%, CV {lifecycleDetail.get('cv', 'N/A')})"
        )

    # ── AI 컨텍스트 (Tier 2 브릿지) ──
    conTsGap: float | None = None
    if conGrowthRates and tsGrowthRates:
        avgCon = sum(conGrowthRates) / len(conGrowthRates)
        avgTs = sum(tsGrowthRates) / len(tsGrowthRates)
        conTsGap = avgCon - avgTs

    avgGrowth = sum(growthRates) / len(growthRates) if growthRates else 0.0
    aiContext: dict = {
        "base_growth": round(avgGrowth, 2),
        "lifecycle": lifecycle,
        "lifecycle_detail": lifecycleDetail,
        "market": market,
        "sources_used": list(finalWeights.keys()),
        "ts_method": tsResult.method,
        "ts_r_squared": tsResult.rSquared,
        "roic_growth": round(roicGrowthRate, 2) if roicGrowthRate is not None else None,
        "roic_detail": roicDetail if roicDetail else None,
        "roic_ts_gap": round(roicTsGap, 2) if roicTsGap is not None else None,
        "consensus_vs_ts_gap": round(conTsGap, 2) if conTsGap is not None else None,
        "sector_key": sectorKey,
        "key_assumptions": assumptions.copy(),
        "uncertainty_flags": [],
    }

    # 불확실성 플래그
    if lifecycle == "transition":
        aiContext["uncertainty_flags"].append("전환기 기업 — 과거 추세 신뢰도 낮음")
    if roicTsGap is not None and abs(roicTsGap) > 10:
        aiContext["uncertainty_flags"].append(f"ROIC-시계열 괴리 {roicTsGap:+.1f}%p")
    if conTsGap is not None and abs(conTsGap) > 15:
        aiContext["uncertainty_flags"].append(f"컨센서스-시계열 괴리 {conTsGap:+.1f}%p")
    if not consensusProj:
        aiContext["uncertainty_flags"].append("컨센서스 데이터 없음")

    # 구조변화 컨텍스트 (forecastCalcs.py dead code 활성화)
    if _sb:
        aiContext["structural_break"] = {
            "stability": _sb.get("overallStability", "stable"),
            "revenue_break": any(m.get("hasBreak") for m in _sb.get("metrics", []) if m.get("name") == "revenue"),
            "n_breaks": sum(1 for m in _sb.get("metrics", []) if m.get("hasBreak")),
        }
        if _sb.get("overallStability") in ("volatile", "transitioning"):
            aiContext["uncertainty_flags"].append(f"구조변화 감지 ({_sb['overallStability']}) — 과거 추세 신뢰도 제한")

    # ── v3: 3-시나리오 ──
    scenarios, scenarioGrs, scenarioProbs = _buildScenarios(
        projected,
        [round(g, 1) for g in growthRates],
        historical,
        lifecycle,
        lastRevenue,
        structuralBreak=_sb,
    )

    # v3: 세그먼트/수주잔고 AI 컨텍스트
    if segmentForecasts:
        aiContext["segment_count"] = len(segmentForecasts)
        aiContext["segments_top3"] = [
            {"name": sf.name, "share": sf.shareOfRevenue, "growth": sf.growthRates[0] if sf.growthRates else 0}
            for sf in segmentForecasts[:3]
        ]
    if backlogSignal:
        aiContext["backlog"] = {
            "br_ratio": backlogSignal.backlogRevenueRatio,
            "trend": backlogSignal.brRatioTrend,
            "implied_growth": backlogSignal.impliedRevenueGrowth,
            "applicable": backlogSignal.sectorsApplicable,
        }

    # Forward test 키 생성 (저장은 opt-in)
    ftKey = None
    if stockCode:
        from dartlab.analysis.forecast.forwardTest import generateKey

        ftKey = generateKey(stockCode, horizon)

    return RevenueForecastResult(
        historical=historical,
        projected=projected,
        horizon=horizon,
        method=method,
        confidence=confidence,
        growthRates=[round(g, 1) for g in growthRates],
        sources=list(finalWeights.keys()),
        sourceWeights=finalWeights,
        consensusRevenue=consensusRevenue,
        assumptions=assumptions,
        warnings=warnings + tsResult.warnings,
        aiContext=aiContext,
        scenarios=scenarios,
        scenarioGrowthRates=scenarioGrs,
        scenarioProbabilities=scenarioProbs,
        segmentForecasts=segmentForecasts,
        backlogSignal=backlogSignal,
        forwardTestKey=ftKey,
        currency=currency,
        forecastable=_forecastable,
        unforecastableReason=_unfReason,
    )


# ══════════════════════════════════════
# AI 오버레이 적용
# ══════════════════════════════════════


_MAX_ANNUAL_ADJ = 10.0  # 연간 보정 ±%p 캡
_MAX_TOTAL_ADJ = 20.0  # 총 보정 ±%p 캡


def applyAiOverlay(
    result: RevenueForecastResult,
    overlay: RevenueForecastAIOverlay,
) -> RevenueForecastResult:
    """AI 보정을 예측 결과에 적용."""
    if not overlay.reasoning:
        log.warning("AI overlay rejected: reasoning 비어있음")
        return result

    adj = overlay.growthAdjustment
    if not adj or len(adj) < result.horizon:
        adj = (adj or []) + [0.0] * result.horizon
        adj = adj[: result.horizon]

    # 가드레일: 연간 캡
    adj = [max(min(a, _MAX_ANNUAL_ADJ), -_MAX_ANNUAL_ADJ) for a in adj]

    # 가드레일: 총 캡
    total = sum(abs(a) for a in adj)
    if total > _MAX_TOTAL_ADJ:
        scale = _MAX_TOTAL_ADJ / total
        adj = [a * scale for a in adj]

    # 보정 적용
    newProjected: list[float] = []
    prev = (
        result.projected[0] / (1 + result.growthRates[0] / 100)
        if result.projected and result.growthRates and result.growthRates[0] != -100
        else 0
    )

    for i, (proj, gr) in enumerate(zip(result.projected, result.growthRates)):
        newGr = gr + adj[i]
        if prev > 0:
            newVal = prev * (1 + newGr / 100)
        else:
            newVal = proj * (1 + adj[i] / 100)
        newProjected.append(newVal)
        prev = newVal

    newGrowthRates = []
    for i, p in enumerate(newProjected):
        if i == 0:
            base = (
                result.projected[0] / (1 + result.growthRates[0] / 100)
                if result.projected and result.growthRates and result.growthRates[0] != -100
                else 0
            )
            if base > 0:
                newGrowthRates.append(round((p / base - 1) * 100, 1))
            else:
                newGrowthRates.append(0.0)
        elif newProjected[i - 1] > 0:
            newGrowthRates.append(round((p / newProjected[i - 1] - 1) * 100, 1))
        else:
            newGrowthRates.append(0.0)

    # 시나리오 확률 이동
    newProbs = dict(result.scenarioProbabilities)
    if overlay.scenarioShift and newProbs:
        for k, shift in overlay.scenarioShift.items():
            if k in newProbs:
                newProbs[k] = max(5, min(70, newProbs[k] + shift))
        # 정규화
        pSum = sum(newProbs.values())
        if pSum > 0:
            newProbs = {k: round(v / pSum * 100, 1) for k, v in newProbs.items()}

    appliedOverlay = RevenueForecastAIOverlay(
        growthAdjustment=adj,
        direction=overlay.direction,
        magnitude=overlay.magnitude,
        scenarioShift=overlay.scenarioShift,
        reasoning=overlay.reasoning,
        applied=True,
    )

    return RevenueForecastResult(
        historical=result.historical,
        projected=newProjected,
        horizon=result.horizon,
        method=result.method,
        confidence=overlay.confidence_override
        if hasattr(overlay, "confidence_override") and overlay.confidence_override
        else result.confidence,  # type: ignore[attr-defined]
        growthRates=newGrowthRates,
        sources=result.sources,
        sourceWeights=result.sourceWeights,
        consensusRevenue=result.consensusRevenue,
        assumptions=result.assumptions + [f"AI 보정: {overlay.direction} ({overlay.magnitude})"],
        warnings=result.warnings,
        aiContext=result.aiContext,
        scenarios=result.scenarios,
        scenarioGrowthRates=result.scenarioGrowthRates,
        scenarioProbabilities=newProbs,
        segmentForecasts=result.segmentForecasts,
        backlogSignal=result.backlogSignal,
        aiOverlay=appliedOverlay,
        forwardTestKey=result.forwardTestKey,
        currency=result.currency,
    )
