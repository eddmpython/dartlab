"""재무제표 완전 분석 통합 진입점.

scan()이 시장 전체를 횡단하듯, analysis()는 단일 종목을 심층 분석한다.

사용법::

    import dartlab

    dartlab.analysis()                              # 전체 가이드
    dartlab.analysis("financial", "수익구조")         # 수익구조 분석 항목 목록
    dartlab.analysis("financial", "수익구조", c)      # 삼성전자 수익구조 분석 실행
    dartlab.analysis("financial", "이익품질", c)      # 삼성전자 이익의 질 분석

    c.analysis()                                    # 가이드
    c.analysis("financial", "수익성")                 # 수익성 분석
"""

from __future__ import annotations

import importlib
import inspect
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


# ── 15축 레지스트리 ──
# catalog.py SECTIONS + _BLOCKS + registry.py buildBlocks()에서 매핑.

_AXIS_REGISTRY: dict[str, _AxisEntry] = {
    "수익구조": _AxisEntry(
        section="수익구조",
        partId="1-1",
        description="이 회사는 무엇으로 돈을 버는가",
        example='analysis("financial", "수익구조")',
        calcs=(
            _CalcEntry("calcCompanyProfile", "dartlab.analysis.financial.revenue", "profile", "기업 개요"),
            _CalcEntry(
                "calcSegmentComposition", "dartlab.analysis.financial.revenue", "segmentComposition", "부문별 매출 구성"
            ),
            _CalcEntry("calcSegmentTrend", "dartlab.analysis.financial.revenue", "segmentTrend", "부문별 매출 추이"),
            _CalcEntry("calcRevenueGrowth", "dartlab.analysis.financial.revenue", "growth", "매출 성장률"),
            _CalcEntry(
                "calcGrowthContribution", "dartlab.analysis.financial.revenue", "growthContribution", "성장 기여 분해"
            ),
            _CalcEntry("calcConcentration", "dartlab.analysis.financial.revenue", "concentration", "매출 집중도"),
            _CalcEntry("calcRevenueQuality", "dartlab.analysis.financial.revenue", "revenueQuality", "매출 품질"),
            _CalcEntry("calcFlags", "dartlab.analysis.financial.revenue", "revenueFlags", "수익구조 플래그"),
        ),
    ),
    "자금조달": _AxisEntry(
        section="자금조달",
        partId="1-2",
        description="돈을 어디서 조달하는가",
        example='analysis("financial", "자금조달")',
        calcs=(
            _CalcEntry("calcFundingSources", "dartlab.analysis.financial.capital", "fundingSources", "자금 원천 구성"),
            _CalcEntry(
                "calcCapitalOverview", "dartlab.analysis.financial.capital", "capitalOverview", "자본 구조 개요"
            ),
            _CalcEntry(
                "calcCapitalTimeline", "dartlab.analysis.financial.capital", "capitalTimeline", "자본 구조 추이"
            ),
            _CalcEntry("calcDebtTimeline", "dartlab.analysis.financial.capital", "debtTimeline", "부채 추이"),
            _CalcEntry("calcInterestBurden", "dartlab.analysis.financial.capital", "interestBurden", "이자 부담"),
            _CalcEntry("calcLiquidity", "dartlab.analysis.financial.capital", "liquidity", "유동성"),
            _CalcEntry(
                "calcCashFlowStructure", "dartlab.analysis.financial.capital", "cashFlowStructure", "자금흐름 구조"
            ),
            _CalcEntry(
                "calcDistressIndicators", "dartlab.analysis.financial.capital", "distressIndicators", "재무 위험 지표"
            ),
            _CalcEntry("calcCapitalFlags", "dartlab.analysis.financial.capital", "capitalFlags", "자금조달 플래그"),
        ),
    ),
    "자산구조": _AxisEntry(
        section="자산구조",
        partId="1-3",
        description="조달한 돈으로 뭘 준비했는가",
        example='analysis("financial", "자산구조")',
        calcs=(
            _CalcEntry("calcAssetStructure", "dartlab.analysis.financial.asset", "assetStructure", "자산 재분류"),
            _CalcEntry("calcWorkingCapital", "dartlab.analysis.financial.asset", "workingCapital", "운전자본 순환"),
            _CalcEntry("calcCapexPattern", "dartlab.analysis.financial.asset", "capexPattern", "CAPEX 패턴"),
            _CalcEntry("calcAssetFlags", "dartlab.analysis.financial.asset", "assetFlags", "자산구조 플래그"),
        ),
    ),
    "현금흐름": _AxisEntry(
        section="현금흐름",
        partId="1-4",
        description="실제로 현금은 어떻게 흘렀는가",
        example='analysis("financial", "현금흐름")',
        calcs=(
            _CalcEntry(
                "calcCashFlowOverview", "dartlab.analysis.financial.cashflow", "cashFlowOverview", "현금흐름 종합"
            ),
            _CalcEntry("calcCashQuality", "dartlab.analysis.financial.cashflow", "cashQuality", "이익의 현금 전환"),
            _CalcEntry("calcCashFlowFlags", "dartlab.analysis.financial.cashflow", "cashFlowFlags", "현금흐름 플래그"),
            _CalcEntry(
                "calcOcfDecomposition",
                "dartlab.analysis.financial.cashflow",
                "ocfDecomposition",
                "영업CF 분해 (NI+감가+운전자본)",
            ),
        ),
    ),
    "수익성": _AxisEntry(
        section="수익성",
        partId="2-1",
        description="이 회사는 얼마나 잘 벌고 있는가",
        example='analysis("financial", "수익성")',
        calcs=(
            _CalcEntry("calcMarginTrend", "dartlab.analysis.financial.profitability", "marginTrend", "마진 추이"),
            _CalcEntry(
                "calcReturnTrend", "dartlab.analysis.financial.profitability", "returnTrend", "ROE 분해 (듀퐁 5요소)"
            ),
            _CalcEntry(
                "calcMarginWaterfall", "dartlab.analysis.financial.profitability", "marginWaterfall", "마진 워터폴"
            ),
            _CalcEntry(
                "calcProfitabilityFlags",
                "dartlab.analysis.financial.profitability",
                "profitabilityFlags",
                "수익성 플래그",
            ),
            _CalcEntry(
                "calcPenmanDecomposition",
                "dartlab.analysis.financial.profitability",
                "penmanDecomposition",
                "Penman 분해 (RNOA vs 레버리지)",
            ),
            _CalcEntry(
                "calcRoicTree",
                "dartlab.analysis.financial.profitability",
                "roicTree",
                "ROIC Tree (마진×회전 분해)",
            ),
        ),
    ),
    "성장성": _AxisEntry(
        section="성장성",
        partId="2-2",
        description="이 회사는 얼마나 빨리 성장하는가",
        example='analysis("financial", "성장성")',
        calcs=(
            _CalcEntry("calcGrowthTrend", "dartlab.analysis.financial.growthAnalysis", "growthTrend", "성장률 추이"),
            _CalcEntry("calcGrowthQuality", "dartlab.analysis.financial.growthAnalysis", "growthQuality", "성장 품질"),
            _CalcEntry(
                "calcSustainableGrowthRate",
                "dartlab.analysis.financial.growthAnalysis",
                "sustainableGrowthRate",
                "지속가능성장률",
            ),
            _CalcEntry("calcGrowthFlags", "dartlab.analysis.financial.growthAnalysis", "growthFlags", "성장성 플래그"),
            _CalcEntry(
                "calcCagrComparison",
                "dartlab.analysis.financial.growthAnalysis",
                "cagrComparison",
                "CAGR 비교 (구조적 변화 감지)",
            ),
        ),
    ),
    "안정성": _AxisEntry(
        section="안정성",
        partId="2-3",
        description="이 회사는 망하지 않는가",
        example='analysis("financial", "안정성")',
        calcs=(
            _CalcEntry("calcLeverageTrend", "dartlab.analysis.financial.stability", "leverageTrend", "레버리지 추이"),
            _CalcEntry("calcCoverageTrend", "dartlab.analysis.financial.stability", "coverageTrend", "이자보상 추이"),
            _CalcEntry("calcDistressScore", "dartlab.analysis.financial.stability", "distressScore", "부실 판별"),
            _CalcEntry(
                "calcDistressEnsemble", "dartlab.analysis.financial.stability", "distressEnsemble", "부실예측 앙상블"
            ),
            _CalcEntry("calcDebtMaturity", "dartlab.analysis.financial.stability", "debtMaturity", "부채 만기 구조"),
            _CalcEntry("calcStabilityFlags", "dartlab.analysis.financial.stability", "stabilityFlags", "안정성 플래그"),
        ),
    ),
    "효율성": _AxisEntry(
        section="효율성",
        partId="2-4",
        description="이 회사는 자산을 잘 굴리는가",
        example='analysis("financial", "효율성")',
        calcs=(
            _CalcEntry(
                "calcTurnoverTrend", "dartlab.analysis.financial.efficiency", "turnoverTrend", "회전율 + CCC 추이"
            ),
            _CalcEntry(
                "calcEfficiencyFlags", "dartlab.analysis.financial.efficiency", "efficiencyFlags", "효율성 플래그"
            ),
        ),
    ),
    "종합평가": _AxisEntry(
        section="종합평가",
        partId="2-5",
        description="재무 상태를 한마디로",
        example='analysis("financial", "종합평가")',
        calcs=(
            _CalcEntry("calcScorecard", "dartlab.analysis.financial.scorecard", "scorecard", "재무 스코어카드"),
            _CalcEntry("calcPiotroskiDetail", "dartlab.analysis.financial.scorecard", "piotroski", "Piotroski F-Score"),
            _CalcEntry("calcSummaryFlags", "dartlab.analysis.financial.scorecard", "summaryFlags", "종합 플래그"),
        ),
    ),
    "이익품질": _AxisEntry(
        section="이익품질",
        partId="3-1",
        description="이익이 진짜인가",
        example='analysis("financial", "이익품질")',
        calcs=(
            _CalcEntry(
                "calcAccrualAnalysis", "dartlab.analysis.financial.earningsQuality", "accrualAnalysis", "발생액 분석"
            ),
            _CalcEntry(
                "calcEarningsPersistence",
                "dartlab.analysis.financial.earningsQuality",
                "earningsPersistence",
                "이익 지속성",
            ),
            _CalcEntry(
                "calcBeneishTimeline", "dartlab.analysis.financial.earningsQuality", "beneishMScore", "Beneish M-Score"
            ),
            _CalcEntry(
                "calcEarningsQualityFlags",
                "dartlab.analysis.financial.earningsQuality",
                "earningsQualityFlags",
                "이익품질 플래그",
            ),
            _CalcEntry(
                "calcRichardsonAccrual",
                "dartlab.analysis.financial.earningsQuality",
                "richardsonAccrual",
                "Richardson 3계층 발생액",
            ),
            _CalcEntry(
                "calcNonOperatingBreakdown",
                "dartlab.analysis.financial.earningsQuality",
                "nonOperatingBreakdown",
                "영업외손익 분해",
            ),
        ),
    ),
    "비용구조": _AxisEntry(
        section="비용구조",
        partId="3-2",
        description="비용이 어떻게 움직이는가",
        example='analysis("financial", "비용구조")',
        calcs=(
            _CalcEntry(
                "calcCostBreakdown", "dartlab.analysis.financial.costStructure", "costBreakdown", "비용 비중 분해"
            ),
            _CalcEntry(
                "calcOperatingLeverage", "dartlab.analysis.financial.costStructure", "operatingLeverage", "영업레버리지"
            ),
            _CalcEntry(
                "calcBreakevenEstimate", "dartlab.analysis.financial.costStructure", "breakevenEstimate", "손익분기점"
            ),
            _CalcEntry(
                "calcRawMaterialBreakdown",
                "dartlab.analysis.financial.costStructure",
                "rawMaterialBreakdown",
                "원재료 매입 비중",
            ),
            _CalcEntry(
                "calcCostStructureFlags",
                "dartlab.analysis.financial.costStructure",
                "costStructureFlags",
                "비용구조 플래그",
            ),
        ),
    ),
    "자본배분": _AxisEntry(
        section="자본배분",
        partId="3-3",
        description="번 돈을 어디에 쓰는가",
        example='analysis("financial", "자본배분")',
        calcs=(
            _CalcEntry(
                "calcDividendPolicy", "dartlab.analysis.financial.capitalAllocation", "dividendPolicy", "배당 정책"
            ),
            _CalcEntry(
                "calcShareholderReturn", "dartlab.analysis.financial.capitalAllocation", "shareholderReturn", "주주환원"
            ),
            _CalcEntry("calcReinvestment", "dartlab.analysis.financial.capitalAllocation", "reinvestment", "재투자"),
            _CalcEntry("calcFcfUsage", "dartlab.analysis.financial.capitalAllocation", "fcfUsage", "FCF 사용처"),
            _CalcEntry(
                "calcDividendDocs", "dartlab.analysis.financial.capitalAllocation", "dividendDocs", "배당 서술 (docs)"
            ),
            _CalcEntry(
                "calcTreasuryStockStatus",
                "dartlab.analysis.financial.capitalAllocation",
                "treasuryStockStatus",
                "자사주 현황",
            ),
            _CalcEntry(
                "calcCapitalAllocationFlags",
                "dartlab.analysis.financial.capitalAllocation",
                "capitalAllocationFlags",
                "자본배분 플래그",
            ),
        ),
    ),
    "투자효율": _AxisEntry(
        section="투자효율",
        partId="3-4",
        description="투자가 가치를 만드는가",
        example='analysis("financial", "투자효율")',
        calcs=(
            _CalcEntry(
                "calcRoicTimeline", "dartlab.analysis.financial.investmentAnalysis", "roicTimeline", "ROIC 시계열"
            ),
            _CalcEntry(
                "calcInvestmentIntensity",
                "dartlab.analysis.financial.investmentAnalysis",
                "investmentIntensity",
                "투자 강도",
            ),
            _CalcEntry(
                "calcEvaTimeline", "dartlab.analysis.financial.investmentAnalysis", "evaTimeline", "NOPAT + 투하자본"
            ),
            _CalcEntry(
                "calcInvestmentInOther",
                "dartlab.analysis.financial.investmentAnalysis",
                "investmentInOther",
                "타법인 출자 현황",
            ),
            _CalcEntry(
                "calcInvestmentFlags",
                "dartlab.analysis.financial.investmentAnalysis",
                "investmentFlags",
                "투자효율 플래그",
            ),
        ),
    ),
    "재무정합성": _AxisEntry(
        section="재무정합성",
        partId="3-5",
        description="재무제표가 서로 맞는가",
        example='analysis("financial", "재무정합성")',
        calcs=(
            _CalcEntry(
                "calcIsCfDivergence", "dartlab.analysis.financial.crossStatement", "isCfDivergence", "IS-CF 괴리"
            ),
            _CalcEntry(
                "calcIsBsDivergence", "dartlab.analysis.financial.crossStatement", "isBsDivergence", "IS-BS 괴리"
            ),
            _CalcEntry("calcAnomalyScore", "dartlab.analysis.financial.crossStatement", "anomalyScore", "이상 점수"),
            _CalcEntry(
                "calcEffectiveTaxRate", "dartlab.analysis.financial.taxAnalysis", "effectiveTaxRate", "유효세율"
            ),
            _CalcEntry("calcDeferredTax", "dartlab.analysis.financial.taxAnalysis", "deferredTax", "이연법인세"),
            _CalcEntry(
                "calcArticulationCheck",
                "dartlab.analysis.financial.crossStatement",
                "articulationCheck",
                "BS-CF 정합성 검증",
            ),
        ),
    ),
    # 신용평가는 독립 엔진 (c.credit()) — analysis 축에서 제거
    # ── 4부: 가치평가 ──
    "가치평가": _AxisEntry(
        section="가치평가",
        partId="4-1",
        description="이 회사의 적정 가치는 얼마인가",
        example='analysis("valuation", "가치평가")',
        calcs=(
            _CalcEntry("calcDcf", "dartlab.analysis.financial.valuation", "dcfValuation", "DCF 밸류에이션"),
            _CalcEntry("calcDdm", "dartlab.analysis.financial.valuation", "ddmValuation", "DDM 밸류에이션"),
            _CalcEntry(
                "calcRelativeValuation",
                "dartlab.analysis.financial.valuation",
                "relativeValuation",
                "상대가치 (PER/PBR/EV-EBITDA/PSR/PEG)",
            ),
            _CalcEntry(
                "calcResidualIncome", "dartlab.analysis.financial.valuation", "residualIncome", "RIM (잔여이익모델)"
            ),
            _CalcEntry("calcPriceTarget", "dartlab.analysis.financial.valuation", "priceTarget", "확률 가중 목표주가"),
            _CalcEntry("calcReverseImplied", "dartlab.analysis.financial.valuation", "reverseImplied", "역내재성장률"),
            _CalcEntry("calcSensitivity", "dartlab.analysis.financial.valuation", "sensitivity", "민감도 분석"),
            _CalcEntry(
                "calcValuationSynthesis",
                "dartlab.analysis.financial.valuation",
                "valuationSynthesis",
                "종합 적정가치",
            ),
            _CalcEntry(
                "calcValuationFlags", "dartlab.analysis.financial.valuation", "valuationFlags", "가치평가 플래그"
            ),
        ),
    ),
    # ── 5부: 비재무 심화 ──
    "지배구조": _AxisEntry(
        section="지배구조",
        partId="5-1",
        description="이 회사의 주인은 누구이며 감시는 작동하는가",
        example='analysis("governance", "지배구조")',
        calcs=(
            _CalcEntry(
                "calcOwnershipTrend", "dartlab.analysis.financial.governance", "ownershipTrend", "최대주주 지분 추이"
            ),
            _CalcEntry(
                "calcBoardComposition", "dartlab.analysis.financial.governance", "boardComposition", "이사회 구성"
            ),
            _CalcEntry(
                "calcAuditOpinionTrend",
                "dartlab.analysis.financial.governance",
                "auditOpinionTrend",
                "감사의견 시계열",
            ),
            _CalcEntry(
                "calcGovernanceFlags", "dartlab.analysis.financial.governance", "governanceFlags", "지배구조 플래그"
            ),
        ),
    ),
    "공시변화": _AxisEntry(
        section="공시변화",
        partId="5-2",
        description="이 회사의 공시가 뭐가 달라졌는가",
        example='analysis("governance", "공시변화")',
        calcs=(
            _CalcEntry(
                "calcDisclosureChangeSummary",
                "dartlab.analysis.financial.disclosureDelta",
                "disclosureChangeSummary",
                "공시변화 종합",
            ),
            _CalcEntry(
                "calcKeyTopicChanges",
                "dartlab.analysis.financial.disclosureDelta",
                "keyTopicChanges",
                "핵심 공시 변화",
            ),
            _CalcEntry(
                "calcChangeIntensity",
                "dartlab.analysis.financial.disclosureDelta",
                "changeIntensity",
                "변화 크기 분석",
            ),
            _CalcEntry(
                "calcDisclosureDeltaFlags",
                "dartlab.analysis.financial.disclosureDelta",
                "disclosureDeltaFlags",
                "공시변화 플래그",
            ),
        ),
    ),
    "비교분석": _AxisEntry(
        section="비교분석",
        partId="5-3",
        description="이 회사는 시장에서 어디에 서 있는가",
        example='analysis("governance", "비교분석")',
        calcs=(
            _CalcEntry(
                "calcPeerRanking", "dartlab.analysis.financial.peerBenchmark", "peerRanking", "시장 내 백분위 순위"
            ),
            _CalcEntry(
                "calcRiskReturnPosition",
                "dartlab.analysis.financial.peerBenchmark",
                "riskReturnPosition",
                "수익-위험 포지션",
            ),
            _CalcEntry(
                "calcPeerBenchmarkFlags",
                "dartlab.analysis.financial.peerBenchmark",
                "peerBenchmarkFlags",
                "비교분석 플래그",
            ),
        ),
    ),
    # ── 6부: 전망분석 ──
    "매출전망": _AxisEntry(
        section="매출전망",
        partId="6-1",
        description="이 회사의 매출은 어디로 가며 재무는 어떻게 변하는가",
        example='analysis("forecast", "매출전망")',
        calcs=(
            _CalcEntry(
                "calcRevenueForecast", "dartlab.analysis.financial.forecastCalcs", "revenueForecast", "매출 예측"
            ),
            _CalcEntry(
                "calcSegmentForecast", "dartlab.analysis.financial.forecastCalcs", "segmentForecast", "세그먼트별 전망"
            ),
            _CalcEntry(
                "calcProFormaHighlights",
                "dartlab.analysis.financial.forecastCalcs",
                "proFormaHighlights",
                "Pro-Forma 전망",
            ),
            _CalcEntry(
                "calcScenarioImpact", "dartlab.analysis.financial.forecastCalcs", "scenarioImpact", "시나리오 영향"
            ),
            _CalcEntry(
                "calcForecastMethodology",
                "dartlab.analysis.financial.forecastCalcs",
                "forecastMethodology",
                "예측 방법론",
            ),
            _CalcEntry(
                "calcHistoricalRatios", "dartlab.analysis.financial.forecastCalcs", "historicalRatios", "과거 구조 비율"
            ),
            _CalcEntry(
                "calcForecastFlags", "dartlab.analysis.financial.forecastCalcs", "forecastFlags", "매출전망 플래그"
            ),
            _CalcEntry(
                "calcScenarioSimulation",
                "dartlab.analysis.financial.forecastCalcs",
                "scenarioSimulation",
                "시나리오 시뮬레이션",
            ),
        ),
    ),
    "예측신호": _AxisEntry(
        section="예측신호",
        partId="6-2",
        description="이 회사의 실적은 어디로 향하는가",
        example='analysis("forecast", "예측신호")',
        calcs=(
            _CalcEntry(
                "calcEarningsMomentum",
                "dartlab.analysis.financial.predictionSignals",
                "earningsMomentum",
                "이익 모멘텀",
            ),
            _CalcEntry(
                "calcPeerPrediction",
                "dartlab.analysis.financial.predictionSignals",
                "peerPrediction",
                "횡단면 피어 예측",
            ),
            _CalcEntry(
                "calcStructuralBreak",
                "dartlab.analysis.financial.predictionSignals",
                "structuralBreak",
                "구조변화 감지",
            ),
            _CalcEntry(
                "calcMacroSensitivity",
                "dartlab.analysis.financial.predictionSignals",
                "macroSensitivity",
                "거시경제 민감도",
            ),
            _CalcEntry(
                "calcMacroRegression",
                "dartlab.analysis.financial.predictionSignals",
                "macroRegression",
                "거시-재무 동적 회귀",
            ),
            _CalcEntry(
                "calcEventImpact",
                "dartlab.analysis.financial.predictionSignals",
                "eventImpact",
                "이벤트 충격 분석",
            ),
            _CalcEntry(
                "calcDisclosureDelta",
                "dartlab.analysis.financial.predictionSignals",
                "disclosureDelta",
                "공시 변화 신호",
            ),
            _CalcEntry(
                "calcInventoryDivergence",
                "dartlab.analysis.financial.predictionSignals",
                "inventoryDivergence",
                "재고/매출채권 괴리",
            ),
            _CalcEntry(
                "calcAnnouncementTiming",
                "dartlab.analysis.financial.predictionSignals",
                "announcementTiming",
                "동종업계 공시 타이밍",
            ),
            _CalcEntry(
                "calcSupplyChainSignal",
                "dartlab.analysis.financial.predictionSignals",
                "supplyChainSignal",
                "공급망 모멘텀",
            ),
            _CalcEntry(
                "calcConsensusDirection",
                "dartlab.analysis.financial.predictionSignals",
                "consensusDirection",
                "컨센서스 매출 방향",
            ),
            _CalcEntry(
                "calcFlowDirection",
                "dartlab.analysis.financial.predictionSignals",
                "flowDirection",
                "수급 누적 방향",
            ),
            _CalcEntry(
                "calcRevenueDirection",
                "dartlab.analysis.financial.predictionSignals",
                "revenueDirection",
                "매출 모멘텀 방향",
            ),
            _CalcEntry(
                "calcPredictionSynthesis",
                "dartlab.analysis.financial.predictionSignals",
                "predictionSynthesis",
                "예측 신호 종합",
            ),
            _CalcEntry(
                "calcPredictionFlags",
                "dartlab.analysis.financial.predictionSignals",
                "predictionFlags",
                "예측신호 플래그",
            ),
        ),
    ),
    # ── 7부: 기술적 분석 ──
    "기술적분석": _AxisEntry(
        section="기술적분석",
        partId="7-1",
        description="주가 기술적 지표와 매매 신호로 타이밍을 판단한다",
        example='analysis("quant", "기술적분석")',
        calcs=(
            _CalcEntry(
                "calcTechnicalVerdict",
                "dartlab.analysis.financial.quantCalcs",
                "technicalVerdict",
                "종합 판단 (강세/중립/약세)",
            ),
            _CalcEntry(
                "calcTechnicalIndicators",
                "dartlab.analysis.financial.quantCalcs",
                "technicalIndicators",
                "25개 기술적 지표",
            ),
            _CalcEntry("calcBeta", "dartlab.analysis.financial.quantCalcs", "beta", "시장 베타 + CAPM"),
        ),
    ),
}


# ── Alias ──

# ── 그룹 정의 — analysis("그룹", "하위") 2단계 호출 ──

_GROUPS: dict[str, list[str]] = {
    "financial": [
        "수익구조",
        "자금조달",
        "자산구조",
        "현금흐름",
        "수익성",
        "성장성",
        "안정성",
        "효율성",
        "종합평가",
        "이익품질",
        "비용구조",
        "자본배분",
        "투자효율",
        "재무정합성",
    ],
    "valuation": ["가치평가"],
    "governance": ["지배구조", "공시변화", "비교분석"],
    "forecast": ["매출전망", "예측신호"],
    "quant": ["기술적분석"],
}

# 역매핑: 축 → 소속 그룹
_AXIS_TO_GROUP: dict[str, str] = {}
for _g, _axes in _GROUPS.items():
    for _a in _axes:
        _AXIS_TO_GROUP[_a] = _g

# ── alias — 한글↔영문 양방향 ──

_ALIASES: dict[str, str] = {
    # 영문 → 한글 (축 이름)
    "revenue": "수익구조",
    "revenueStructure": "수익구조",
    "capital": "자금조달",
    "funding": "자금조달",
    "asset": "자산구조",
    "assetStructure": "자산구조",
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
    "investmentEfficiency": "투자효율",
    "crossStatement": "재무정합성",
    "financialConsistency": "재무정합성",
    "valuation": "가치평가",
    "governance": "지배구조",
    "disclosureDelta": "공시변화",
    "disclosureChange": "공시변화",
    "peerBenchmark": "비교분석",
    "peerComparison": "비교분석",
    "forecast": "매출전망",
    "전망": "매출전망",
    "prediction": "예측신호",
    "predictionSignals": "예측신호",
    "전망신호": "예측신호",
    # 그룹 alias (한글)
    "재무": "financial",
    "재무분석": "financial",
    "가치": "valuation",
    "지배": "governance",
    "전망분석": "forecast",
    "기술적": "quant",
    "기술적분석": "quant",
    "technical": "quant",
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


# ── basePeriod 지원 여부 검사 (캐싱) ──

_BP_CACHE: dict[str, bool] = {}


def _acceptsBasePeriod(fn) -> bool:
    """calc 함수가 basePeriod 파라미터를 받는지 확인 (결과 캐싱)."""
    key = f"{fn.__module__}.{fn.__qualname__}"
    cached = _BP_CACHE.get(key)
    if cached is not None:
        return cached
    try:
        sig = inspect.signature(fn)
        result = "basePeriod" in sig.parameters
    except (ValueError, TypeError):
        result = False
    _BP_CACHE[key] = result
    return result


# ── Group Accessor ──


class _GroupAccessor:
    """analysis.financial, analysis.valuation 등 그룹 accessor."""

    def __init__(self, analysis_instance: "Analysis", group: str):
        self._analysis = analysis_instance
        self._group = group

    def __call__(self, company=None, *, basePeriod=None):
        """그룹 가이드 또는 그룹 전체 실행."""
        return self._analysis(self._group, company=company, basePeriod=basePeriod)

    def __getattr__(self, name):
        """analysis.financial.profitability() 패턴."""
        try:
            resolved = _resolveAxis(name)
        except ValueError:
            raise AttributeError(f"'{self._group}' 그룹에 '{name}' 축이 없습니다")

        if resolved not in _GROUPS.get(self._group, []):
            raise AttributeError(f"'{name}' 축은 '{self._group}' 그룹에 속하지 않습니다")

        def _bound_axis(company=None, *, basePeriod=None):
            return self._analysis(self._group, resolved, company=company, basePeriod=basePeriod)

        _bound_axis.__name__ = name
        _bound_axis.__doc__ = f'analysis("{self._group}", "{resolved}")'
        return _bound_axis

    def __repr__(self) -> str:
        axes = _GROUPS.get(self._group, [])
        lines = [f"Analysis.{self._group} -- {len(axes)}축"]
        for key in axes:
            entry = _AXIS_REGISTRY.get(key)
            if entry:
                lines.append(f"  {key:8s} {entry.description}")
        return "\n".join(lines)


# ── Analysis Class ──


class Analysis:
    """재무제표 완전 분석 — 20축, 단일 종목 심층.

    Capabilities:
        Part 1 — 사업구조: 수익구조, 자금조달, 자산구조, 현금흐름
        Part 2 — 핵심비율: 수익성, 성장성, 안정성, 효율성, 종합평가
        Part 3 — 심화분석: 이익품질, 비용구조, 자본배분, 투자효율, 재무정합성
        Part 4 — 가치평가: DCF, DDM, 상대가치, RIM, 목표주가, 역내재성장률, 민감도
        Part 5 — 비재무 심화: 지배구조, 공시변화감지, 비교분석
        Part 6 — 전망분석: 매출전망, 예측신호
        - 각 축은 Company를 받아 dict를 반환하는 순수 함수 집합
        - review()가 이 결과를 소비하여 구조화 보고서 생성

    Requires:
        데이터: finance (자동 다운로드)

    AIContext:
        - reviewer()가 analysis 결과를 소비하여 AI 해석 생성
        - ask()에서 재무분석 컨텍스트로 활용
        - 70개 calc* 함수의 개별 결과를 LLM에 주입 가능

    Guide:
        - "이 회사 수익구조?" -> analysis("financial", "수익구조") — 매출원가율, 판관비율 등
        - "재무 건전한가?" -> analysis("financial", "안정성") — 부채비율, 유동비율, ICR
        - "이익이 진짜야?" -> analysis("financial", "이익품질") — 발생주의 비율, OCF/NI
        - "적정가치?" -> analysis("valuation", "가치평가") — DCF/DDM/상대/RIM/목표가
        - "전체 종합?" -> analysis("financial", "종합평가") — 15축 통합 스코어
        - 15축 전부 보고 싶으면 review() 사용 권장

    SeeAlso:
        - review: analysis 결과를 구조화 보고서로 렌더링
        - scan: 전종목 비교 (analysis는 단일 종목 심층)
        - Company.insights: 7영역 인사이트 등급 (빠른 요약)

    Args:
        axis: 축 이름 ("수익구조", "수익성" 등). None이면 15축 가이드.
        company: Company 객체. None이면 해당 축의 분석 항목 목록.
        **kwargs: 축별 옵션.

    Returns:
        axis=None → pl.DataFrame (15축 가이드)
        company=None → pl.DataFrame (해당 축 calc 목록)
        둘 다 있으면 → dict (분석 결과)

    Example::

        import dartlab
        dartlab.analysis()                              # 전체 가이드
        dartlab.analysis("financial", "수익구조")         # 항목 목록
        c = dartlab.Company("005930")
        dartlab.analysis("financial", "수익구조", c)      # 삼성전자 수익구조
        c.analysis("financial", "수익성")                 # Company 바인딩
    """

    def __call__(
        self,
        axis: str | None = None,
        sub: Any | None = None,
        *,
        company: Any | None = None,
        basePeriod: str | None = None,
        **kwargs: Any,
    ) -> pl.DataFrame | dict:
        """엔진("그룹", "하위") 2단계 호출 패턴.

        호출::

            c.analysis("financial", "수익성")   # 그룹 + 하위
            c.analysis("valuation", "가치평가")  # 그룹 + 하위
            c.analysis("forecast", "매출전망")   # 그룹 + 하위
        """
        if axis is None:
            return self._guide()

        # sub가 Company 객체면 legacy 호환: analysis("financial", "수익성", company)
        if sub is not None and hasattr(sub, "stockCode"):
            company = sub
            sub = None

        # 그룹 해석 — 직접 그룹명 또는 한글 그룹 alias
        group = axis if axis in _GROUPS else _ALIASES.get(axis) if _ALIASES.get(axis) in _GROUPS else None

        if group is not None:
            # 2단계: analysis("financial", "수익성")
            if sub is None:
                return self._groupGuide(group)
            resolved = _resolveAxis(sub)
            entry = _AXIS_REGISTRY[resolved]
            if company is None:
                return self._listCalcs(resolved, entry)
            return self._run(company, entry, basePeriod=basePeriod)

        # 그룹 없이 축만 전달된 경우 → 자동 추론
        resolved = _resolveAxis(axis)
        entry = _AXIS_REGISTRY[resolved]

        if company is None:
            return self._listCalcs(resolved, entry)

        return self._run(company, entry, basePeriod=basePeriod)

    def _groupGuide(self, group: str) -> pl.DataFrame:
        """그룹 내 축 목록."""
        axes = _GROUPS.get(group, [])
        rows = []
        for key in axes:
            entry = _AXIS_REGISTRY.get(key)
            if entry:
                rows.append({"축": key, "파트": entry.partId, "설명": entry.description})
        if not rows:
            return pl.DataFrame()
        return pl.DataFrame(rows)

    def _guide(self) -> pl.DataFrame:
        """15축 가이드."""
        rows = []
        for key, entry in _AXIS_REGISTRY.items():
            rows.append(
                {
                    "축": key,
                    "partId": entry.partId,
                    "설명": entry.description,
                    "항목수": len(entry.calcs),
                    "예시": entry.example,
                }
            )
        return pl.DataFrame(rows)

    def _listCalcs(self, axis: str, entry: _AxisEntry) -> pl.DataFrame:
        """해당 축의 분석 항목 목록."""
        rows = []
        for calc in entry.calcs:
            rows.append(
                {
                    "blockKey": calc.blockKey,
                    "함수": calc.fn,
                    "label": calc.label,
                }
            )
        return pl.DataFrame(rows)

    def _run(self, company: Any, entry: _AxisEntry, *, basePeriod: str | None = None) -> dict:
        """해당 축의 calc* 함수 전부 실행."""
        results: dict[str, Any] = {}
        for calc in entry.calcs:
            try:
                mod = importlib.import_module(calc.module)
                fn = getattr(mod, calc.fn)
                if _acceptsBasePeriod(fn):
                    results[calc.blockKey] = fn(company, basePeriod=basePeriod)
                else:
                    results[calc.blockKey] = fn(company)
            except (KeyError, ValueError, TypeError, AttributeError, ArithmeticError, ImportError):
                results[calc.blockKey] = None
        return results

    def __getattr__(self, name):
        """accessor 패턴: analysis.financial, analysis.valuation 등."""
        group = name if name in _GROUPS else _ALIASES.get(name) if _ALIASES.get(name) in _GROUPS else None
        if group is not None:
            return _GroupAccessor(self, group)
        raise AttributeError(f"Analysis에 '{name}' 속성이 없습니다")

    def __repr__(self) -> str:
        lines = [f"Analysis -- {len(_AXIS_REGISTRY)}축 종합 분석", ""]
        for key, entry in _AXIS_REGISTRY.items():
            lines.append(f"  {entry.partId}  {key:8s} {entry.description} ({len(entry.calcs)}항목)")
        lines.append("")
        lines.append("사용법: analysis(), analysis('그룹', '축'), analysis('그룹', '축', company)")
        return "\n".join(lines)
