"""review 레지스트리 — 템플릿 기반 Review 생성."""

from __future__ import annotations

from dartlab.review.layout import ReviewLayout
from dartlab.review.section import Section
from dartlab.review.templates import TEMPLATE_ORDER, TEMPLATES
from dartlab.review.utils import isTerminal


def buildBlocks(company, keys: set[str] | None = None, *, basePeriod: str | None = None):
    """블록 사전 -- analysis calc* 결과를 블록으로 변환.

    keys가 지정되면 해당 블록만 빌드한다 (선택적 빌드).
    keys=None이면 전체 블록을 빌드한다 (기존 동작).
    """
    # builders와 analysis의 금액 포맷을 company.currency에 맞게 설정 (contextvars — 스레드 안전)
    from dartlab.review.builders import _review_currency

    _currency = getattr(company, "currency", "KRW")
    _review_currency.set(_currency)
    try:
        from dartlab.analysis.financial.capital import _analysis_currency

        _analysis_currency.set(_currency)
    except ImportError:
        pass

    def _safe(fn):
        try:
            import polars as pl

            _polarsErr = pl.exceptions.PolarsError
        except ImportError:
            _polarsErr = RuntimeError
        try:
            return fn()
        except (
            KeyError,
            ValueError,
            TypeError,
            AttributeError,
            ArithmeticError,
            ImportError,
            RuntimeError,
            IndexError,
            _polarsErr,
        ) as exc:
            import logging

            logging.getLogger("dartlab.review").debug(
                "review block build 실패: %s — %s: %s",
                getattr(fn, "__name__", "?"),
                type(exc).__name__,
                exc,
            )
            return []

    def _need(key: str) -> bool:
        return keys is None or key in keys

    b: dict = {}

    # ── 1부: 사업구조 ──
    # import는 해당 블록이 필요할 때만 (그룹 단위)
    if keys is None or keys & {
        "profile",
        "segmentComposition",
        "segmentTrend",
        "region",
        "product",
        "growth",
        "concentration",
        "revenueQuality",
        "growthContribution",
        "revenueFlags",
    }:
        from dartlab.analysis.financial.revenue import (
            calcBreakdown,
            calcCompanyProfile,
            calcConcentration,
            calcFlags,
            calcGrowthContribution,
            calcRevenueGrowth,
            calcRevenueQuality,
            calcSegmentComposition,
            calcSegmentTrend,
        )
        from dartlab.review.builders import (
            breakdownBlock,
            concentrationBlock,
            growthContributionBlock,
            profileBlock,
            revenueFlagsBlock,
            revenueGrowthBlock,
            revenueQualityBlock,
            segmentCompositionBlock,
            segmentTrendBlock,
        )

        if _need("profile"):
            b["profile"] = _safe(lambda: profileBlock(calcCompanyProfile(company, basePeriod=basePeriod)))
        if _need("segmentComposition"):
            b["segmentComposition"] = _safe(
                lambda: segmentCompositionBlock(calcSegmentComposition(company, basePeriod=basePeriod))
            )
        if _need("segmentTrend"):
            b["segmentTrend"] = _safe(lambda: segmentTrendBlock(calcSegmentTrend(company, basePeriod=basePeriod)))
        if _need("region"):
            b["region"] = _safe(
                lambda: breakdownBlock(calcBreakdown(company, "region", basePeriod=basePeriod), "region")
            )
        if _need("product"):
            b["product"] = _safe(
                lambda: breakdownBlock(calcBreakdown(company, "product", basePeriod=basePeriod), "product")
            )
        if _need("growth"):
            b["growth"] = _safe(lambda: revenueGrowthBlock(calcRevenueGrowth(company, basePeriod=basePeriod)))
        if _need("concentration"):
            b["concentration"] = _safe(lambda: concentrationBlock(calcConcentration(company, basePeriod=basePeriod)))
        if _need("revenueQuality"):
            b["revenueQuality"] = _safe(lambda: revenueQualityBlock(calcRevenueQuality(company, basePeriod=basePeriod)))
        if _need("growthContribution"):
            b["growthContribution"] = _safe(
                lambda: growthContributionBlock(calcGrowthContribution(company, basePeriod=basePeriod))
            )
        if _need("revenueFlags"):
            b["revenueFlags"] = _safe(lambda: revenueFlagsBlock(calcFlags(company, basePeriod=basePeriod)))

    if keys is None or keys & {
        "fundingSources",
        "capitalOverview",
        "capitalTimeline",
        "debtTimeline",
        "interestBurden",
        "liquidity",
        "cashFlowStructure",
        "distressIndicators",
        "capitalFlags",
    }:
        from dartlab.analysis.financial.capital import (
            calcCapitalFlags,
            calcCapitalOverview,
            calcCapitalTimeline,
            calcCashFlowStructure,
            calcDebtTimeline,
            calcDistressIndicators,
            calcFundingSources,
            calcInterestBurden,
            calcLiquidity,
        )
        from dartlab.review.builders import (
            capitalFlagsBlock,
            capitalOverviewBlock,
            capitalTimelineBlock,
            cashFlowBlock,
            debtTimelineBlock,
            distressBlock,
            fundingSourcesBlock,
            interestBurdenBlock,
            liquidityBlock,
        )

        if _need("fundingSources"):
            b["fundingSources"] = _safe(lambda: fundingSourcesBlock(calcFundingSources(company, basePeriod=basePeriod)))
        if _need("capitalOverview"):
            b["capitalOverview"] = _safe(
                lambda: capitalOverviewBlock(calcCapitalOverview(company, basePeriod=basePeriod))
            )
        if _need("capitalTimeline"):
            b["capitalTimeline"] = _safe(
                lambda: capitalTimelineBlock(calcCapitalTimeline(company, basePeriod=basePeriod))
            )
        if _need("debtTimeline"):
            b["debtTimeline"] = _safe(lambda: debtTimelineBlock(calcDebtTimeline(company, basePeriod=basePeriod)))
        if _need("interestBurden"):
            b["interestBurden"] = _safe(lambda: interestBurdenBlock(calcInterestBurden(company, basePeriod=basePeriod)))
        if _need("liquidity"):
            b["liquidity"] = _safe(lambda: liquidityBlock(calcLiquidity(company, basePeriod=basePeriod)))
        if _need("cashFlowStructure"):
            b["cashFlowStructure"] = _safe(lambda: cashFlowBlock(calcCashFlowStructure(company, basePeriod=basePeriod)))
        if _need("distressIndicators"):
            b["distressIndicators"] = _safe(
                lambda: distressBlock(calcDistressIndicators(company, basePeriod=basePeriod))
            )
        if _need("capitalFlags"):
            b["capitalFlags"] = _safe(lambda: capitalFlagsBlock(calcCapitalFlags(company, basePeriod=basePeriod)))

    if keys is None or keys & {"assetStructure", "workingCapital", "capexPattern", "assetFlags"}:
        from dartlab.analysis.financial.asset import (
            calcAssetFlags,
            calcAssetStructure,
            calcCapexPattern,
            calcWorkingCapital,
        )
        from dartlab.review.builders import (
            assetFlagsBlock,
            assetStructureBlock,
            capexBlock,
            workingCapitalBlock,
        )

        if _need("assetStructure"):
            b["assetStructure"] = _safe(lambda: assetStructureBlock(calcAssetStructure(company, basePeriod=basePeriod)))
        if _need("workingCapital"):
            b["workingCapital"] = _safe(lambda: workingCapitalBlock(calcWorkingCapital(company, basePeriod=basePeriod)))
        if _need("capexPattern"):
            b["capexPattern"] = _safe(lambda: capexBlock(calcCapexPattern(company, basePeriod=basePeriod)))
        if _need("assetFlags"):
            b["assetFlags"] = _safe(lambda: assetFlagsBlock(calcAssetFlags(company, basePeriod=basePeriod)))

    if keys is None or keys & {"cashFlowOverview", "cashQuality", "ocfDecomposition", "cashFlowFlags"}:
        from dartlab.analysis.financial.cashflow import (
            calcCashFlowFlags,
            calcCashFlowOverview,
            calcCashQuality,
            calcOcfDecomposition,
        )
        from dartlab.review.builders import (
            cashFlowFlagsBlock,
            cashFlowOverviewBlock,
            cashQualityBlock,
            ocfDecompositionBlock,
        )

        if _need("cashFlowOverview"):
            b["cashFlowOverview"] = _safe(
                lambda: cashFlowOverviewBlock(calcCashFlowOverview(company, basePeriod=basePeriod))
            )
        if _need("cashQuality"):
            b["cashQuality"] = _safe(lambda: cashQualityBlock(calcCashQuality(company, basePeriod=basePeriod)))
        if _need("ocfDecomposition"):
            b["ocfDecomposition"] = _safe(
                lambda: ocfDecompositionBlock(calcOcfDecomposition(company, basePeriod=basePeriod))
            )
        if _need("cashFlowFlags"):
            b["cashFlowFlags"] = _safe(lambda: cashFlowFlagsBlock(calcCashFlowFlags(company, basePeriod=basePeriod)))

    # ── 2부: 재무비율 분석 ──
    if keys is None or keys & {
        "marginTrend",
        "returnTrend",
        "dupont",
        "penmanDecomposition",
        "roicTree",
        "profitabilityFlags",
    }:
        from dartlab.analysis.financial.profitability import (
            calcDupont,
            calcMarginTrend,
            calcPenmanDecomposition,
            calcProfitabilityFlags,
            calcReturnTrend,
            calcRoicTree,
        )
        from dartlab.review.builders import (
            dupontBlock,
            marginTrendBlock,
            penmanDecompositionBlock,
            profitabilityFlagsBlock,
            returnTrendBlock,
            roicTreeBlock,
        )

        if _need("marginTrend"):
            b["marginTrend"] = _safe(lambda: marginTrendBlock(calcMarginTrend(company, basePeriod=basePeriod)))
        if _need("returnTrend"):
            b["returnTrend"] = _safe(lambda: returnTrendBlock(calcReturnTrend(company, basePeriod=basePeriod)))
        if _need("dupont"):
            b["dupont"] = _safe(lambda: dupontBlock(calcDupont(company, basePeriod=basePeriod)))
        if _need("penmanDecomposition"):
            b["penmanDecomposition"] = _safe(
                lambda: penmanDecompositionBlock(calcPenmanDecomposition(company, basePeriod=basePeriod))
            )
        if _need("roicTree"):
            b["roicTree"] = _safe(lambda: roicTreeBlock(calcRoicTree(company, basePeriod=basePeriod)))
        if _need("profitabilityFlags"):
            b["profitabilityFlags"] = _safe(
                lambda: profitabilityFlagsBlock(calcProfitabilityFlags(company, basePeriod=basePeriod))
            )

    if keys is None or keys & {"growthTrend", "growthQuality", "cagrComparison", "growthFlags"}:
        from dartlab.analysis.financial.growthAnalysis import (
            calcCagrComparison,
            calcGrowthFlags,
            calcGrowthQuality,
            calcGrowthTrend,
        )
        from dartlab.review.builders import (
            cagrComparisonBlock,
            growthFlagsBlock,
            growthQualityBlock,
            growthTrendBlock,
        )

        if _need("growthTrend"):
            b["growthTrend"] = _safe(lambda: growthTrendBlock(calcGrowthTrend(company, basePeriod=basePeriod)))
        if _need("growthQuality"):
            b["growthQuality"] = _safe(lambda: growthQualityBlock(calcGrowthQuality(company, basePeriod=basePeriod)))
        if _need("cagrComparison"):
            b["cagrComparison"] = _safe(lambda: cagrComparisonBlock(calcCagrComparison(company, basePeriod=basePeriod)))
        if _need("growthFlags"):
            b["growthFlags"] = _safe(lambda: growthFlagsBlock(calcGrowthFlags(company, basePeriod=basePeriod)))

    if keys is None or keys & {"leverageTrend", "coverageTrend", "distressScore", "stabilityFlags", "marketRisk"}:
        from dartlab.analysis.financial.stability import (
            calcCoverageTrend,
            calcDistressScore,
            calcLeverageTrend,
            calcStabilityFlags,
        )
        from dartlab.review.builders import (
            coverageTrendBlock,
            distressScoreBlock,
            leverageTrendBlock,
            stabilityFlagsBlock,
        )

        if _need("leverageTrend"):
            b["leverageTrend"] = _safe(lambda: leverageTrendBlock(calcLeverageTrend(company, basePeriod=basePeriod)))
        if _need("coverageTrend"):
            b["coverageTrend"] = _safe(lambda: coverageTrendBlock(calcCoverageTrend(company, basePeriod=basePeriod)))
        if _need("distressScore"):
            b["distressScore"] = _safe(lambda: distressScoreBlock(calcDistressScore(company, basePeriod=basePeriod)))
        if _need("stabilityFlags"):
            b["stabilityFlags"] = _safe(lambda: stabilityFlagsBlock(calcStabilityFlags(company, basePeriod=basePeriod)))
        if _need("marketRisk"):
            from dartlab.quant.extended import calcMarketRisk
            from dartlab.review.builders import marketRiskBlock

            b["marketRisk"] = _safe(lambda: marketRiskBlock(calcMarketRisk(company)))

    if keys is None or keys & {"turnoverTrend", "cccTrend", "efficiencyFlags"}:
        from dartlab.analysis.financial.efficiency import (
            calcCccTrend,
            calcEfficiencyFlags,
            calcTurnoverTrend,
        )
        from dartlab.review.builders import (
            cccTrendBlock,
            efficiencyFlagsBlock,
            turnoverTrendBlock,
        )

        if _need("turnoverTrend"):
            b["turnoverTrend"] = _safe(lambda: turnoverTrendBlock(calcTurnoverTrend(company, basePeriod=basePeriod)))
        if _need("cccTrend"):
            b["cccTrend"] = _safe(lambda: cccTrendBlock(calcCccTrend(company, basePeriod=basePeriod)))
        if _need("efficiencyFlags"):
            b["efficiencyFlags"] = _safe(
                lambda: efficiencyFlagsBlock(calcEfficiencyFlags(company, basePeriod=basePeriod))
            )

    if keys is None or keys & {"scorecard", "piotroski", "summaryFlags"}:
        from dartlab.analysis.financial.scorecard import (
            calcPiotroskiDetail,
            calcScorecard,
            calcSummaryFlags,
        )
        from dartlab.review.builders import (
            piotroskiBlock,
            scorecardBlock,
            summaryFlagsBlock,
        )

        if _need("scorecard"):
            b["scorecard"] = _safe(lambda: scorecardBlock(calcScorecard(company, basePeriod=basePeriod)))
        if _need("piotroski"):
            b["piotroski"] = _safe(lambda: piotroskiBlock(calcPiotroskiDetail(company, basePeriod=basePeriod)))
        if _need("summaryFlags"):
            b["summaryFlags"] = _safe(lambda: summaryFlagsBlock(calcSummaryFlags(company, basePeriod=basePeriod)))

    # ── 3부: 심화 분석 ──
    if keys is None or keys & {
        "accrualAnalysis",
        "earningsPersistence",
        "beneishMScore",
        "richardsonAccrual",
        "nonOperatingBreakdown",
        "earningsQualityFlags",
    }:
        from dartlab.analysis.financial.earningsQuality import (
            calcAccrualAnalysis,
            calcBeneishTimeline,
            calcEarningsPersistence,
            calcEarningsQualityFlags,
            calcNonOperatingBreakdown,
            calcRichardsonAccrual,
        )
        from dartlab.review.builders import (
            accrualAnalysisBlock,
            beneishMScoreBlock,
            earningsPersistenceBlock,
            earningsQualityFlagsBlock,
            nonOperatingBreakdownBlock,
            richardsonAccrualBlock,
        )

        if _need("accrualAnalysis"):
            b["accrualAnalysis"] = _safe(
                lambda: accrualAnalysisBlock(calcAccrualAnalysis(company, basePeriod=basePeriod))
            )
        if _need("earningsPersistence"):
            b["earningsPersistence"] = _safe(
                lambda: earningsPersistenceBlock(calcEarningsPersistence(company, basePeriod=basePeriod))
            )
        if _need("beneishMScore"):
            b["beneishMScore"] = _safe(lambda: beneishMScoreBlock(calcBeneishTimeline(company, basePeriod=basePeriod)))
        if _need("richardsonAccrual"):
            b["richardsonAccrual"] = _safe(
                lambda: richardsonAccrualBlock(calcRichardsonAccrual(company, basePeriod=basePeriod))
            )
        if _need("nonOperatingBreakdown"):
            b["nonOperatingBreakdown"] = _safe(
                lambda: nonOperatingBreakdownBlock(calcNonOperatingBreakdown(company, basePeriod=basePeriod))
            )
        if _need("earningsQualityFlags"):
            b["earningsQualityFlags"] = _safe(
                lambda: earningsQualityFlagsBlock(calcEarningsQualityFlags(company, basePeriod=basePeriod))
            )

    if keys is None or keys & {"costBreakdown", "operatingLeverage", "breakevenEstimate", "costStructureFlags"}:
        from dartlab.analysis.financial.costStructure import (
            calcBreakevenEstimate,
            calcCostBreakdown,
            calcCostStructureFlags,
            calcOperatingLeverage,
        )
        from dartlab.review.builders import (
            breakevenEstimateBlock,
            costBreakdownBlock,
            costStructureFlagsBlock,
            operatingLeverageBlock,
        )

        if _need("costBreakdown"):
            b["costBreakdown"] = _safe(lambda: costBreakdownBlock(calcCostBreakdown(company, basePeriod=basePeriod)))
        if _need("operatingLeverage"):
            b["operatingLeverage"] = _safe(
                lambda: operatingLeverageBlock(calcOperatingLeverage(company, basePeriod=basePeriod))
            )
        if _need("breakevenEstimate"):
            b["breakevenEstimate"] = _safe(
                lambda: breakevenEstimateBlock(calcBreakevenEstimate(company, basePeriod=basePeriod))
            )
        if _need("costStructureFlags"):
            b["costStructureFlags"] = _safe(
                lambda: costStructureFlagsBlock(calcCostStructureFlags(company, basePeriod=basePeriod))
            )

    if keys is None or keys & {
        "dividendPolicy",
        "shareholderReturn",
        "reinvestment",
        "fcfUsage",
        "capitalAllocationFlags",
    }:
        from dartlab.analysis.financial.capitalAllocation import (
            calcCapitalAllocationFlags,
            calcDividendPolicy,
            calcFcfUsage,
            calcReinvestment,
            calcShareholderReturn,
        )
        from dartlab.review.builders import (
            capitalAllocationFlagsBlock,
            dividendPolicyBlock,
            fcfUsageBlock,
            reinvestmentBlock,
            shareholderReturnBlock,
        )

        if _need("dividendPolicy"):
            b["dividendPolicy"] = _safe(lambda: dividendPolicyBlock(calcDividendPolicy(company, basePeriod=basePeriod)))
        if _need("shareholderReturn"):
            b["shareholderReturn"] = _safe(
                lambda: shareholderReturnBlock(calcShareholderReturn(company, basePeriod=basePeriod))
            )
        if _need("reinvestment"):
            b["reinvestment"] = _safe(lambda: reinvestmentBlock(calcReinvestment(company, basePeriod=basePeriod)))
        if _need("fcfUsage"):
            b["fcfUsage"] = _safe(lambda: fcfUsageBlock(calcFcfUsage(company, basePeriod=basePeriod)))
        if _need("capitalAllocationFlags"):
            b["capitalAllocationFlags"] = _safe(
                lambda: capitalAllocationFlagsBlock(calcCapitalAllocationFlags(company, basePeriod=basePeriod))
            )

    if keys is None or keys & {"roicTimeline", "investmentIntensity", "evaTimeline", "investmentFlags"}:
        from dartlab.analysis.financial.investmentAnalysis import (
            calcEvaTimeline,
            calcInvestmentFlags,
            calcInvestmentIntensity,
            calcRoicTimeline,
        )
        from dartlab.review.builders import (
            evaTimelineBlock,
            investmentFlagsBlock,
            investmentIntensityBlock,
            roicTimelineBlock,
        )

        if _need("roicTimeline"):
            b["roicTimeline"] = _safe(lambda: roicTimelineBlock(calcRoicTimeline(company, basePeriod=basePeriod)))
        if _need("investmentIntensity"):
            b["investmentIntensity"] = _safe(
                lambda: investmentIntensityBlock(calcInvestmentIntensity(company, basePeriod=basePeriod))
            )
        if _need("evaTimeline"):
            b["evaTimeline"] = _safe(lambda: evaTimelineBlock(calcEvaTimeline(company, basePeriod=basePeriod)))
        if _need("investmentFlags"):
            b["investmentFlags"] = _safe(
                lambda: investmentFlagsBlock(calcInvestmentFlags(company, basePeriod=basePeriod))
            )

    if keys is None or keys & {
        "isCfDivergence",
        "isBsDivergence",
        "anomalyScore",
        "articulationCheck",
        "effectiveTaxRate",
        "deferredTax",
        "crossStatementFlags",
    }:
        from dartlab.analysis.financial.crossStatement import (
            calcAnomalyScore,
            calcArticulationCheck,
            calcCrossStatementFlags,
            calcIsBsDivergence,
            calcIsCfDivergence,
        )
        from dartlab.analysis.financial.taxAnalysis import (
            calcDeferredTax,
            calcEffectiveTaxRate,
            calcTaxFlags,
        )
        from dartlab.review.builders import (
            anomalyScoreBlock,
            articulationCheckBlock,
            crossStatementFlagsBlock,
            deferredTaxBlock,
            effectiveTaxRateBlock,
            isBsDivergenceBlock,
            isCfDivergenceBlock,
        )

        if _need("isCfDivergence"):
            b["isCfDivergence"] = _safe(lambda: isCfDivergenceBlock(calcIsCfDivergence(company, basePeriod=basePeriod)))
        if _need("isBsDivergence"):
            b["isBsDivergence"] = _safe(lambda: isBsDivergenceBlock(calcIsBsDivergence(company, basePeriod=basePeriod)))
        if _need("anomalyScore"):
            b["anomalyScore"] = _safe(lambda: anomalyScoreBlock(calcAnomalyScore(company, basePeriod=basePeriod)))
        if _need("articulationCheck"):
            b["articulationCheck"] = _safe(
                lambda: articulationCheckBlock(calcArticulationCheck(company, basePeriod=basePeriod))
            )
        if _need("effectiveTaxRate"):
            b["effectiveTaxRate"] = _safe(
                lambda: effectiveTaxRateBlock(calcEffectiveTaxRate(company, basePeriod=basePeriod))
            )
        if _need("deferredTax"):
            b["deferredTax"] = _safe(lambda: deferredTaxBlock(calcDeferredTax(company, basePeriod=basePeriod)))
        if _need("crossStatementFlags"):
            b["crossStatementFlags"] = _safe(
                lambda: crossStatementFlagsBlock(
                    calcCrossStatementFlags(company, basePeriod=basePeriod)
                    + calcTaxFlags(company, basePeriod=basePeriod)
                )
            )

    # ── 3-6: 신용평가 ──
    if keys is None or keys & {
        "creditMetrics",
        "creditScore",
        "creditHistory",
        "cashFlowGrade",
        "creditPeerPosition",
        "creditFlags",
    }:
        from dartlab.credit.calcs import (
            calcCashFlowGrade,
            calcCreditFlags,
            calcCreditHistory,
            calcCreditMetrics,
            calcCreditPeerPosition,
            calcCreditScore,
        )
        from dartlab.review.builders import (
            cashFlowGradeBlock,
            creditFlagsBlock,
            creditHistoryBlock,
            creditMetricsBlock,
            creditPeerPositionBlock,
            creditScoreBlock,
        )

        if _need("creditMetrics"):
            b["creditMetrics"] = _safe(lambda: creditMetricsBlock(calcCreditMetrics(company, basePeriod=basePeriod)))
        if _need("creditScore"):
            b["creditScore"] = _safe(lambda: creditScoreBlock(calcCreditScore(company, basePeriod=basePeriod)))
        if _need("creditHistory"):
            b["creditHistory"] = _safe(lambda: creditHistoryBlock(calcCreditHistory(company, basePeriod=basePeriod)))
        if _need("cashFlowGrade"):
            b["cashFlowGrade"] = _safe(lambda: cashFlowGradeBlock(calcCashFlowGrade(company, basePeriod=basePeriod)))
        if _need("creditPeerPosition"):
            b["creditPeerPosition"] = _safe(
                lambda: creditPeerPositionBlock(calcCreditPeerPosition(company, basePeriod=basePeriod))
            )
        if _need("creditFlags"):
            b["creditFlags"] = _safe(lambda: creditFlagsBlock(calcCreditFlags(company, basePeriod=basePeriod)))

    # ── 4부: 가치평가 ──
    if keys is None or keys & {
        "dcfValuation",
        "ddmValuation",
        "relativeValuation",
        "residualIncome",
        "priceTarget",
        "reverseImplied",
        "sensitivity",
        "valuationSynthesis",
        "valuationFlags",
    }:
        from dartlab.analysis.financial.valuation import (
            calcDcf,
            calcDdm,
            calcPriceTarget,
            calcReverseImplied,
            calcSensitivity,
            calcValuationFlags,
            calcValuationSynthesis,
        )
        from dartlab.analysis.financial.valuation import (
            calcRelativeValuation as calcRelVal,
        )
        from dartlab.analysis.financial.valuation import (
            calcResidualIncome as calcRim,
        )
        from dartlab.review.builders import (
            dcfValuationBlock,
            ddmValuationBlock,
            priceTargetBlock,
            relativeValuationBlock,
            residualIncomeBlock,
            reverseImpliedBlock,
            sensitivityBlock,
            valuationFlagsBlock,
            valuationSynthesisBlock,
        )

        if _need("dcfValuation"):
            b["dcfValuation"] = _safe(lambda: dcfValuationBlock(calcDcf(company, basePeriod=basePeriod)))
        if _need("ddmValuation"):
            b["ddmValuation"] = _safe(lambda: ddmValuationBlock(calcDdm(company, basePeriod=basePeriod)))
        if _need("relativeValuation"):
            b["relativeValuation"] = _safe(lambda: relativeValuationBlock(calcRelVal(company, basePeriod=basePeriod)))
        if _need("residualIncome"):
            b["residualIncome"] = _safe(lambda: residualIncomeBlock(calcRim(company, basePeriod=basePeriod)))
        if _need("priceTarget"):
            b["priceTarget"] = _safe(lambda: priceTargetBlock(calcPriceTarget(company, basePeriod=basePeriod)))
        if _need("reverseImplied"):
            b["reverseImplied"] = _safe(lambda: reverseImpliedBlock(calcReverseImplied(company, basePeriod=basePeriod)))
        if _need("sensitivity"):
            b["sensitivity"] = _safe(lambda: sensitivityBlock(calcSensitivity(company, basePeriod=basePeriod)))
        if _need("valuationSynthesis"):
            b["valuationSynthesis"] = _safe(
                lambda: valuationSynthesisBlock(calcValuationSynthesis(company, basePeriod=basePeriod))
            )
        if _need("valuationFlags"):
            b["valuationFlags"] = _safe(lambda: valuationFlagsBlock(calcValuationFlags(company, basePeriod=basePeriod)))

    # ── 5부: 비재무 심화 ──
    if keys is None or keys & {"ownershipTrend", "boardComposition", "auditOpinionTrend", "governanceFlags"}:
        from dartlab.analysis.financial.governance import (
            calcAuditOpinionTrend,
            calcBoardComposition,
            calcGovernanceFlags,
            calcOwnershipTrend,
        )
        from dartlab.review.builders import (
            auditOpinionTrendBlock,
            boardCompositionBlock,
            governanceFlagsBlock,
            ownershipTrendBlock,
        )

        if _need("ownershipTrend"):
            b["ownershipTrend"] = _safe(lambda: ownershipTrendBlock(calcOwnershipTrend(company, basePeriod=basePeriod)))
        if _need("boardComposition"):
            b["boardComposition"] = _safe(
                lambda: boardCompositionBlock(calcBoardComposition(company, basePeriod=basePeriod))
            )
        if _need("auditOpinionTrend"):
            b["auditOpinionTrend"] = _safe(
                lambda: auditOpinionTrendBlock(calcAuditOpinionTrend(company, basePeriod=basePeriod))
            )
        if _need("governanceFlags"):
            b["governanceFlags"] = _safe(
                lambda: governanceFlagsBlock(calcGovernanceFlags(company, basePeriod=basePeriod))
            )

    if keys is None or keys & {
        "disclosureChangeSummary",
        "keyTopicChanges",
        "changeIntensity",
        "disclosureDeltaFlags",
    }:
        from dartlab.analysis.financial.disclosureDelta import (
            calcChangeIntensity,
            calcDisclosureChangeSummary,
            calcDisclosureDeltaFlags,
            calcKeyTopicChanges,
        )
        from dartlab.review.builders import (
            changeIntensityBlock,
            disclosureChangeSummaryBlock,
            disclosureDeltaFlagsBlock,
            keyTopicChangesBlock,
        )

        if _need("disclosureChangeSummary"):
            b["disclosureChangeSummary"] = _safe(
                lambda: disclosureChangeSummaryBlock(calcDisclosureChangeSummary(company, basePeriod=basePeriod))
            )
        if _need("keyTopicChanges"):
            b["keyTopicChanges"] = _safe(
                lambda: keyTopicChangesBlock(calcKeyTopicChanges(company, basePeriod=basePeriod))
            )
        if _need("changeIntensity"):
            b["changeIntensity"] = _safe(
                lambda: changeIntensityBlock(calcChangeIntensity(company, basePeriod=basePeriod))
            )
        if _need("disclosureDeltaFlags"):
            b["disclosureDeltaFlags"] = _safe(
                lambda: disclosureDeltaFlagsBlock(calcDisclosureDeltaFlags(company, basePeriod=basePeriod))
            )

    if keys is None or keys & {"peerRanking", "riskReturnPosition", "peerBenchmarkFlags"}:
        from dartlab.analysis.financial.peerBenchmark import (
            calcPeerBenchmarkFlags,
            calcPeerRanking,
            calcRiskReturnPosition,
        )
        from dartlab.review.builders import (
            peerBenchmarkFlagsBlock,
            peerRankingBlock,
            riskReturnPositionBlock,
        )

        if _need("peerRanking"):
            b["peerRanking"] = _safe(lambda: peerRankingBlock(calcPeerRanking(company, basePeriod=basePeriod)))
        if _need("riskReturnPosition"):
            b["riskReturnPosition"] = _safe(
                lambda: riskReturnPositionBlock(calcRiskReturnPosition(company, basePeriod=basePeriod))
            )
        if _need("peerBenchmarkFlags"):
            b["peerBenchmarkFlags"] = _safe(
                lambda: peerBenchmarkFlagsBlock(calcPeerBenchmarkFlags(company, basePeriod=basePeriod))
            )

    # ── 6부: 전망분석 ──
    if keys is None or keys & {
        "revenueForecast",
        "segmentForecast",
        "proFormaHighlights",
        "scenarioImpact",
        "forecastMethodology",
        "historicalRatios",
        "forecastFlags",
        "calibrationReport",
    }:
        from dartlab.analysis.financial.forecastCalcs import (
            calcCalibrationReport,
            calcForecastFlags,
            calcForecastMethodology,
            calcHistoricalRatios,
            calcProFormaHighlights,
            calcRevenueForecast,
            calcScenarioImpact,
            calcSegmentForecast,
        )
        from dartlab.review.builders import (
            calibrationReportBlock,
            forecastFlagsBlock,
            forecastMethodologyBlock,
            historicalRatiosBlock,
            proFormaHighlightsBlock,
            revenueForecastBlock,
            scenarioImpactBlock,
            segmentForecastBlock,
        )

        if _need("revenueForecast"):
            b["revenueForecast"] = _safe(
                lambda: revenueForecastBlock(calcRevenueForecast(company, basePeriod=basePeriod))
            )
        if _need("segmentForecast"):
            b["segmentForecast"] = _safe(
                lambda: segmentForecastBlock(calcSegmentForecast(company, basePeriod=basePeriod))
            )
        if _need("proFormaHighlights"):
            b["proFormaHighlights"] = _safe(
                lambda: proFormaHighlightsBlock(calcProFormaHighlights(company, basePeriod=basePeriod))
            )
        if _need("scenarioImpact"):
            b["scenarioImpact"] = _safe(lambda: scenarioImpactBlock(calcScenarioImpact(company, basePeriod=basePeriod)))
        if _need("forecastMethodology"):
            b["forecastMethodology"] = _safe(
                lambda: forecastMethodologyBlock(calcForecastMethodology(company, basePeriod=basePeriod))
            )
        if _need("historicalRatios"):
            b["historicalRatios"] = _safe(
                lambda: historicalRatiosBlock(calcHistoricalRatios(company, basePeriod=basePeriod))
            )
        if _need("forecastFlags"):
            b["forecastFlags"] = _safe(lambda: forecastFlagsBlock(calcForecastFlags(company, basePeriod=basePeriod)))
        if _need("calibrationReport"):
            b["calibrationReport"] = _safe(
                lambda: calibrationReportBlock(calcCalibrationReport(company, basePeriod=basePeriod))
            )

    # ── 시장분석 (quant 기술적 분석 → review 통합) ──
    if keys is None or keys & {
        "technicalVerdict",
        "technicalSignals",
        "marketBeta",
        "fundamentalDivergence",
        "marketAnalysisFlags",
    }:
        from dartlab.quant.extended import (
            calcFundamentalDivergence,
            calcMarketAnalysisFlags,
            calcMarketBeta,
            calcTechnicalSignals,
            calcTechnicalVerdict,
        )
        from dartlab.review.builders import (
            fundamentalDivergenceBlock,
            marketAnalysisFlagsBlock,
            marketBetaBlock,
            technicalSignalsBlock,
            technicalVerdictBlock,
        )

        if _need("technicalVerdict"):
            b["technicalVerdict"] = _safe(lambda: technicalVerdictBlock(calcTechnicalVerdict(company)))
        if _need("technicalSignals"):
            b["technicalSignals"] = _safe(lambda: technicalSignalsBlock(calcTechnicalSignals(company)))
        if _need("marketBeta"):
            b["marketBeta"] = _safe(lambda: marketBetaBlock(calcMarketBeta(company)))
        if _need("fundamentalDivergence"):
            b["fundamentalDivergence"] = _safe(
                lambda: fundamentalDivergenceBlock(calcFundamentalDivergence(company, basePeriod=basePeriod))
            )
        if _need("marketAnalysisFlags"):
            b["marketAnalysisFlags"] = _safe(lambda: marketAnalysisFlagsBlock(calcMarketAnalysisFlags(company)))

    # ── 매크로 (기업-매크로 연결만 — 시장 분석은 dartlab.macro()) ──
    if keys is None or keys & {"valuationBand"}:
        from dartlab.analysis.financial.macroExposure import calcValuationBand
        from dartlab.review.builders import valuationBandBlock

        if _need("valuationBand"):
            b["valuationBand"] = _safe(lambda: valuationBandBlock(calcValuationBand(company, basePeriod=basePeriod)))

    from dartlab.review.blockMap import BlockMap

    return BlockMap(b)


def buildReview(
    company,
    section: str | None = None,
    layout: ReviewLayout | None = None,
    helper: bool | None = None,
    *,
    preset: str | None = None,
    template: str | None = None,
    detail: bool | None = None,
    basePeriod: str | None = None,
):
    """Company에서 Review를 생성."""
    from dartlab.review import Review

    ly = layout or ReviewLayout()

    # ── 스토리 템플릿 판별 ──
    detectedTemplate: str | None = None
    if template is not None and preset is None:
        from dartlab.review.templates import STORY_TEMPLATES
        from dartlab.review.templates import detectTemplate as _detect

        if template == "auto":
            detectedTemplate = _detect(company)
        elif template in STORY_TEMPLATES:
            detectedTemplate = template

    # ── 프리셋 적용 ──
    if preset is not None:
        from dartlab.review.presets import PRESETS

        if preset not in PRESETS:
            raise ValueError(f"알 수 없는 프리셋: {preset}. 사용 가능: {', '.join(PRESETS)}")
        cfg = PRESETS[preset]
        ly.sectionOrder = cfg["sections"]
        if detail is None:
            ly.detail = cfg.get("detail", True)

    # detail 명시 오버라이드
    if detail is not None:
        ly.detail = detail

    showHelper = helper if helper is not None else ly.helper

    corpName = getattr(company, "corpName", "")
    stockCode = getattr(company, "stockCode", "")

    review = Review(stockCode=stockCode, corpName=corpName, layout=ly)
    review.template = detectedTemplate

    useSpinner = isTerminal()
    if useSpinner:
        from rich.console import Console
        from rich.live import Live
        from rich.spinner import Spinner

        console = Console(stderr=True)
        spinner = Spinner("dots", text="분석 준비 중...")
        ctx = Live(spinner, console=console, transient=True)
    else:
        from contextlib import nullcontext

        ctx = nullcontext()

    with ctx as live:
        if live is not None:
            from rich.spinner import Spinner

            live.update(Spinner("dots", text="블록 사전 생성 중..."))

        # 템플릿 순서 결정 (블록 빌드 전에 필요한 keys 산출)
        if section is not None:
            templateKeys = [section] if section in TEMPLATES else []
        elif ly.sectionOrder is not None:
            templateKeys = [k for k in ly.sectionOrder if k in TEMPLATES]
        else:
            templateKeys = list(TEMPLATE_ORDER)

        # 필요한 블록 keys만 산출 → 선택적 빌드
        if section is not None and templateKeys:
            neededKeys: set[str] | None = set()
            for tk in templateKeys:
                neededKeys.update(TEMPLATES[tk]["keys"])
        else:
            neededKeys = None  # 전체 빌드

        b = buildBlocks(company, keys=neededKeys, basePeriod=basePeriod)

        for tmplKey in templateKeys:
            tmpl = TEMPLATES[tmplKey]
            if live is not None:
                from rich.spinner import Spinner

                live.update(Spinner("dots", text=f"{tmplKey} 조립 중..."))

            sectionBlocks = []
            for blockKey in tmpl["keys"]:
                blockList = b.get(blockKey)
                if blockList:
                    sectionBlocks.extend(blockList)

            if sectionBlocks:
                review.sections.append(
                    Section(
                        key=tmplKey,
                        partId=tmpl.get("partId", ""),
                        title=tmpl["title"],
                        blocks=sectionBlocks,
                        helper=tmpl.get("helper", "") if showHelper else "",
                        aiGuide=tmpl.get("aiGuide", ""),
                    )
                )

        # ── 순환 서사 감지 + 주입 ──
        if live is not None:
            from rich.spinner import Spinner

            live.update(Spinner("dots", text="순환 서사 감지 중..."))

        from dartlab.review.narrative import buildCirculationSummary, detectThreads

        _sectionSet = set(templateKeys) if section is not None else None
        threads = detectThreads(company, b, sections=_sectionSet)
        for thread in threads:
            for sec in review.sections:
                if sec.key in thread.involvedSections:
                    sec.threads.append(thread)
        review.circulationSummary = buildCirculationSummary(threads) if threads else ""

        # ── 6막 전환 인과 문장 ──
        from dartlab.review.narrative import buildActTransitions

        review.actTransitions = buildActTransitions(company, b)

        # ── 요약 카드 생성 ──
        from dartlab.review.summary import buildSectionSummary, buildSummaryCard

        scorecardData = None
        try:
            from dartlab.analysis.financial.scorecard import calcScorecard

            scorecardData = calcScorecard(company, basePeriod=basePeriod)
        except (ImportError, KeyError, ValueError, TypeError, AttributeError):
            pass

        review.summaryCard = buildSummaryCard(threads, scorecardData, review.sections)

        # ── 섹션별 요약 생성 ──
        for sec in review.sections:
            sec.summary = buildSectionSummary(sec)

    return review
