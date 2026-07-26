"""_AXIS_REGISTRY 부분 A - 1~3 부 (수익구조 ~ 재무정합성)."""

from __future__ import annotations

from dartlab.analysis.financial._registryTypes import _AxisEntry, _CalcEntry

_AXES_A: dict[str, _AxisEntry] = {
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
            _CalcEntry(
                "calcRepresentativeAnalysis",
                "dartlab.analysis.financial.representative",
                "representative",
                "대표 재무 판단",
            ),
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
                "calcQualityAnomalies",
                "dartlab.analysis.financial.earningsQuality",
                "qualityAnomalies",
                "Phase 7 - Damodaran Ch.4 회계 품질 이상치 (Beneish + Sloan + 5 카테고리 + 감사보고서 docs)",
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
            _CalcEntry("calcRndExpense", "dartlab.analysis.financial.costStructure", "rndExpense", "연구개발비"),
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
    # 신용평가는 독립 엔진 (c.credit()) - analysis 축에서 제거
}
