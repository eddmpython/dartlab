"""재무제표 완전 분석 통합 진입점.

scan()이 시장 전체를 횡단하듯, analysis()는 단일 종목을 심층 분석한다.

사용법::

    import dartlab

    dartlab.analysis()                      # 14축 가이드
    dartlab.analysis("수익구조")             # 수익구조 축의 분석 항목 목록
    dartlab.analysis("수익구조", c)          # 삼성전자 수익구조 분석 실행
    dartlab.analysis("이익품질", c)          # 삼성전자 이익의 질 분석

    c.analysis()                            # 가이드
    c.analysis("수익성")                     # 수익성 분석
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from typing import Any

import polars as pl

# ── 분석 항목 레지스트리 ──


@dataclass(frozen=True)
class _CalcEntry:
    """개별 calc* 함수 메타."""

    fn: str
    module: str
    blockKey: str
    label: str


@dataclass(frozen=True)
class _AxisEntry:
    """분석 축 메타."""

    section: str
    partId: str
    description: str
    example: str
    calcs: tuple[_CalcEntry, ...] = field(default_factory=tuple)


# ── 14축 레지스트리 ──
# catalog.py SECTIONS + _BLOCKS + registry.py buildBlocks()에서 매핑.

_AXIS_REGISTRY: dict[str, _AxisEntry] = {
    "수익구조": _AxisEntry(
        section="수익구조",
        partId="1-1",
        description="이 회사는 무엇으로 돈을 버는가",
        example='analysis("수익구조", c)',
        calcs=(
            _CalcEntry("calcCompanyProfile", "dartlab.analysis.strategy.revenue", "profile", "기업 개요"),
            _CalcEntry("calcSegmentComposition", "dartlab.analysis.strategy.revenue", "segmentComposition", "부문별 매출 구성"),
            _CalcEntry("calcSegmentTrend", "dartlab.analysis.strategy.revenue", "segmentTrend", "부문별 매출 추이"),
            _CalcEntry("calcRevenueGrowth", "dartlab.analysis.strategy.revenue", "growth", "매출 성장률"),
            _CalcEntry("calcGrowthContribution", "dartlab.analysis.strategy.revenue", "growthContribution", "성장 기여 분해"),
            _CalcEntry("calcConcentration", "dartlab.analysis.strategy.revenue", "concentration", "매출 집중도"),
            _CalcEntry("calcRevenueQuality", "dartlab.analysis.strategy.revenue", "revenueQuality", "매출 품질"),
            _CalcEntry("calcFlags", "dartlab.analysis.strategy.revenue", "revenueFlags", "수익구조 플래그"),
        ),
    ),
    "자금조달": _AxisEntry(
        section="자금조달",
        partId="1-2",
        description="돈을 어디서 조달하는가",
        example='analysis("자금조달", c)',
        calcs=(
            _CalcEntry("calcFundingSources", "dartlab.analysis.strategy.capital", "fundingSources", "자금 원천 구성"),
            _CalcEntry("calcCapitalOverview", "dartlab.analysis.strategy.capital", "capitalOverview", "자본 구조 개요"),
            _CalcEntry("calcCapitalTimeline", "dartlab.analysis.strategy.capital", "capitalTimeline", "자본 구조 추이"),
            _CalcEntry("calcDebtTimeline", "dartlab.analysis.strategy.capital", "debtTimeline", "부채 추이"),
            _CalcEntry("calcInterestBurden", "dartlab.analysis.strategy.capital", "interestBurden", "이자 부담"),
            _CalcEntry("calcLiquidity", "dartlab.analysis.strategy.capital", "liquidity", "유동성"),
            _CalcEntry("calcCashFlowStructure", "dartlab.analysis.strategy.capital", "cashFlowStructure", "자금흐름 구조"),
            _CalcEntry("calcDistressIndicators", "dartlab.analysis.strategy.capital", "distressIndicators", "재무 위험 지표"),
            _CalcEntry("calcCapitalFlags", "dartlab.analysis.strategy.capital", "capitalFlags", "자금조달 플래그"),
        ),
    ),
    "자산구조": _AxisEntry(
        section="자산구조",
        partId="1-3",
        description="조달한 돈으로 뭘 준비했는가",
        example='analysis("자산구조", c)',
        calcs=(
            _CalcEntry("calcAssetStructure", "dartlab.analysis.strategy.asset", "assetStructure", "자산 재분류"),
            _CalcEntry("calcWorkingCapital", "dartlab.analysis.strategy.asset", "workingCapital", "운전자본 순환"),
            _CalcEntry("calcCapexPattern", "dartlab.analysis.strategy.asset", "capexPattern", "CAPEX 패턴"),
            _CalcEntry("calcAssetFlags", "dartlab.analysis.strategy.asset", "assetFlags", "자산구조 플래그"),
        ),
    ),
    "현금흐름": _AxisEntry(
        section="현금흐름",
        partId="1-4",
        description="실제로 현금은 어떻게 흘렀는가",
        example='analysis("현금흐름", c)',
        calcs=(
            _CalcEntry("calcCashFlowOverview", "dartlab.analysis.strategy.cashflow", "cashFlowOverview", "현금흐름 종합"),
            _CalcEntry("calcCashQuality", "dartlab.analysis.strategy.cashflow", "cashQuality", "이익의 현금 전환"),
            _CalcEntry("calcCashFlowFlags", "dartlab.analysis.strategy.cashflow", "cashFlowFlags", "현금흐름 플래그"),
        ),
    ),
    "수익성": _AxisEntry(
        section="수익성",
        partId="2-1",
        description="이 회사는 얼마나 잘 벌고 있는가",
        example='analysis("수익성", c)',
        calcs=(
            _CalcEntry("calcMarginTrend", "dartlab.analysis.strategy.profitability", "marginTrend", "마진 추이"),
            _CalcEntry("calcReturnTrend", "dartlab.analysis.strategy.profitability", "returnTrend", "수익률 추이"),
            _CalcEntry("calcDupont", "dartlab.analysis.strategy.profitability", "dupont", "듀퐁 분해"),
            _CalcEntry("calcProfitabilityFlags", "dartlab.analysis.strategy.profitability", "profitabilityFlags", "수익성 플래그"),
        ),
    ),
    "성장성": _AxisEntry(
        section="성장성",
        partId="2-2",
        description="이 회사는 얼마나 빨리 성장하는가",
        example='analysis("성장성", c)',
        calcs=(
            _CalcEntry("calcGrowthTrend", "dartlab.analysis.strategy.growthAnalysis", "growthTrend", "성장률 추이"),
            _CalcEntry("calcGrowthQuality", "dartlab.analysis.strategy.growthAnalysis", "growthQuality", "성장 품질"),
            _CalcEntry("calcGrowthFlags", "dartlab.analysis.strategy.growthAnalysis", "growthFlags", "성장성 플래그"),
        ),
    ),
    "안정성": _AxisEntry(
        section="안정성",
        partId="2-3",
        description="이 회사는 망하지 않는가",
        example='analysis("안정성", c)',
        calcs=(
            _CalcEntry("calcLeverageTrend", "dartlab.analysis.strategy.stability", "leverageTrend", "레버리지 추이"),
            _CalcEntry("calcCoverageTrend", "dartlab.analysis.strategy.stability", "coverageTrend", "이자보상 추이"),
            _CalcEntry("calcDistressScore", "dartlab.analysis.strategy.stability", "distressScore", "부실 판별"),
            _CalcEntry("calcStabilityFlags", "dartlab.analysis.strategy.stability", "stabilityFlags", "안정성 플래그"),
        ),
    ),
    "효율성": _AxisEntry(
        section="효율성",
        partId="2-4",
        description="이 회사는 자산을 잘 굴리는가",
        example='analysis("효율성", c)',
        calcs=(
            _CalcEntry("calcTurnoverTrend", "dartlab.analysis.strategy.efficiency", "turnoverTrend", "회전율 추이"),
            _CalcEntry("calcCccTrend", "dartlab.analysis.strategy.efficiency", "cccTrend", "CCC 추이"),
            _CalcEntry("calcEfficiencyFlags", "dartlab.analysis.strategy.efficiency", "efficiencyFlags", "효율성 플래그"),
        ),
    ),
    "종합평가": _AxisEntry(
        section="종합평가",
        partId="2-5",
        description="재무 상태를 한마디로",
        example='analysis("종합평가", c)',
        calcs=(
            _CalcEntry("calcScorecard", "dartlab.analysis.strategy.scorecard", "scorecard", "재무 스코어카드"),
            _CalcEntry("calcPiotroskiDetail", "dartlab.analysis.strategy.scorecard", "piotroski", "Piotroski F-Score"),
            _CalcEntry("calcSummaryFlags", "dartlab.analysis.strategy.scorecard", "summaryFlags", "종합 플래그"),
        ),
    ),
    "이익품질": _AxisEntry(
        section="이익품질",
        partId="3-1",
        description="이익이 진짜인가",
        example='analysis("이익품질", c)',
        calcs=(
            _CalcEntry("calcAccrualAnalysis", "dartlab.analysis.strategy.earningsQuality", "accrualAnalysis", "발생액 분석"),
            _CalcEntry("calcEarningsPersistence", "dartlab.analysis.strategy.earningsQuality", "earningsPersistence", "이익 지속성"),
            _CalcEntry("calcBeneishTimeline", "dartlab.analysis.strategy.earningsQuality", "beneishMScore", "Beneish M-Score"),
            _CalcEntry("calcEarningsQualityFlags", "dartlab.analysis.strategy.earningsQuality", "earningsQualityFlags", "이익품질 플래그"),
        ),
    ),
    "비용구조": _AxisEntry(
        section="비용구조",
        partId="3-2",
        description="비용이 어떻게 움직이는가",
        example='analysis("비용구조", c)',
        calcs=(
            _CalcEntry("calcCostBreakdown", "dartlab.analysis.strategy.costStructure", "costBreakdown", "비용 비중 분해"),
            _CalcEntry("calcOperatingLeverage", "dartlab.analysis.strategy.costStructure", "operatingLeverage", "영업레버리지"),
            _CalcEntry("calcBreakevenEstimate", "dartlab.analysis.strategy.costStructure", "breakevenEstimate", "손익분기점"),
            _CalcEntry("calcCostStructureFlags", "dartlab.analysis.strategy.costStructure", "costStructureFlags", "비용구조 플래그"),
        ),
    ),
    "자본배분": _AxisEntry(
        section="자본배분",
        partId="3-3",
        description="번 돈을 어디에 쓰는가",
        example='analysis("자본배분", c)',
        calcs=(
            _CalcEntry("calcDividendPolicy", "dartlab.analysis.strategy.capitalAllocation", "dividendPolicy", "배당 정책"),
            _CalcEntry("calcShareholderReturn", "dartlab.analysis.strategy.capitalAllocation", "shareholderReturn", "주주환원"),
            _CalcEntry("calcReinvestment", "dartlab.analysis.strategy.capitalAllocation", "reinvestment", "재투자"),
            _CalcEntry("calcFcfUsage", "dartlab.analysis.strategy.capitalAllocation", "fcfUsage", "FCF 사용처"),
            _CalcEntry("calcCapitalAllocationFlags", "dartlab.analysis.strategy.capitalAllocation", "capitalAllocationFlags", "자본배분 플래그"),
        ),
    ),
    "투자효율": _AxisEntry(
        section="투자효율",
        partId="3-4",
        description="투자가 가치를 만드는가",
        example='analysis("투자효율", c)',
        calcs=(
            _CalcEntry("calcRoicTimeline", "dartlab.analysis.strategy.investmentAnalysis", "roicTimeline", "ROIC 시계열"),
            _CalcEntry("calcInvestmentIntensity", "dartlab.analysis.strategy.investmentAnalysis", "investmentIntensity", "투자 강도"),
            _CalcEntry("calcEvaTimeline", "dartlab.analysis.strategy.investmentAnalysis", "evaTimeline", "EVA 시계열"),
            _CalcEntry("calcInvestmentFlags", "dartlab.analysis.strategy.investmentAnalysis", "investmentFlags", "투자효율 플래그"),
        ),
    ),
    "재무정합성": _AxisEntry(
        section="재무정합성",
        partId="3-5",
        description="재무제표가 서로 맞는가",
        example='analysis("재무정합성", c)',
        calcs=(
            _CalcEntry("calcIsCfDivergence", "dartlab.analysis.strategy.crossStatement", "isCfDivergence", "IS-CF 괴리"),
            _CalcEntry("calcIsBsDivergence", "dartlab.analysis.strategy.crossStatement", "isBsDivergence", "IS-BS 괴리"),
            _CalcEntry("calcAnomalyScore", "dartlab.analysis.strategy.crossStatement", "anomalyScore", "이상 점수"),
            _CalcEntry("calcEffectiveTaxRate", "dartlab.analysis.strategy.taxAnalysis", "effectiveTaxRate", "유효세율"),
            _CalcEntry("calcDeferredTax", "dartlab.analysis.strategy.taxAnalysis", "deferredTax", "이연법인세"),
        ),
    ),
}


# ── Alias ──

_ALIASES: dict[str, str] = {
    "revenue": "수익구조",
    "capital": "자금조달",
    "asset": "자산구조",
    "cashflow": "현금흐름",
    "profitability": "수익성",
    "growth": "성장성",
    "stability": "안정성",
    "efficiency": "효율성",
    "scorecard": "종합평가",
    "earningsQuality": "이익품질",
    "costStructure": "비용구조",
    "capitalAllocation": "자본배분",
    "investment": "투자효율",
    "crossStatement": "재무정합성",
}


def _resolveAxis(axis: str) -> str:
    """축 이름 또는 alias -> 정규 축 이름."""
    if axis in _AXIS_REGISTRY:
        return axis
    if axis in _ALIASES:
        return _ALIASES[axis]
    lower = axis.lower()
    if lower in _ALIASES:
        return _ALIASES[lower]
    available = ", ".join(sorted(_AXIS_REGISTRY))
    raise ValueError(f"알 수 없는 분석 축: '{axis}'. 가용 축: {available}")


# ── Analysis Class ──


class Analysis:
    """재무제표 완전 분석 통합 진입점.

    analysis()                      -> 14축 가이드
    analysis("수익구조")             -> 수익구조 항목 목록
    analysis("수익구조", c)          -> 삼성전자 수익구조 분석
    """

    def __call__(
        self,
        axis: str | None = None,
        company: Any | None = None,
        **kwargs: Any,
    ) -> pl.DataFrame | dict:
        """축(axis)별 단일 종목 재무분석."""
        if axis is None:
            return self._guide()

        resolved = _resolveAxis(axis)
        entry = _AXIS_REGISTRY[resolved]

        if company is None:
            return self._listCalcs(resolved, entry)

        return self._run(company, entry)

    def _guide(self) -> pl.DataFrame:
        """14축 가이드."""
        rows = []
        for key, entry in _AXIS_REGISTRY.items():
            rows.append({
                "축": key,
                "partId": entry.partId,
                "설명": entry.description,
                "항목수": len(entry.calcs),
                "예시": entry.example,
            })
        return pl.DataFrame(rows)

    def _listCalcs(self, axis: str, entry: _AxisEntry) -> pl.DataFrame:
        """해당 축의 분석 항목 목록."""
        rows = []
        for calc in entry.calcs:
            rows.append({
                "blockKey": calc.blockKey,
                "함수": calc.fn,
                "label": calc.label,
            })
        return pl.DataFrame(rows)

    def _run(self, company: Any, entry: _AxisEntry) -> dict:
        """해당 축의 calc* 함수 전부 실행."""
        results: dict[str, Any] = {}
        for calc in entry.calcs:
            try:
                mod = importlib.import_module(calc.module)
                fn = getattr(mod, calc.fn)
                results[calc.blockKey] = fn(company)
            except (KeyError, ValueError, TypeError, AttributeError, ArithmeticError, ImportError):
                results[calc.blockKey] = None
        return results

    def __repr__(self) -> str:
        lines = [f"Analysis -- {len(_AXIS_REGISTRY)}축 재무제표 완전 분석", ""]
        for key, entry in _AXIS_REGISTRY.items():
            lines.append(f"  {entry.partId}  {key:8s} {entry.description} ({len(entry.calcs)}항목)")
        lines.append("")
        lines.append("사용법: analysis(), analysis('축'), analysis('축', company)")
        return "\n".join(lines)
