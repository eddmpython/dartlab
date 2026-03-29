"""review 레지스트리 — 템플릿 기반 Review 생성."""

from __future__ import annotations

from dartlab.review.layout import DEFAULT_LAYOUT, ReviewLayout
from dartlab.review.section import Section
from dartlab.review.templates import TEMPLATE_ORDER, TEMPLATES
from dartlab.review.utils import isTerminal


def buildBlocks(company, keys: set[str] | None = None):
    """블록 사전 -- analysis calc* 결과를 블록으로 변환.

    keys가 지정되면 해당 블록만 빌드한다 (선택적 빌드).
    keys=None이면 전체 블록을 빌드한다 (기존 동작).
    """

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
        ):
            return []

    def _need(key: str) -> bool:
        return keys is None or key in keys

    b: dict = {}

    # ── 1부: 사업구조 ──
    # import는 해당 블록이 필요할 때만 (그룹 단위)
    if keys is None or keys & {
        "profile", "segmentComposition", "segmentTrend", "region", "product",
        "growth", "concentration", "revenueQuality", "growthContribution", "revenueFlags",
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
            b["profile"] = _safe(lambda: profileBlock(calcCompanyProfile(company)))
        if _need("segmentComposition"):
            b["segmentComposition"] = _safe(lambda: segmentCompositionBlock(calcSegmentComposition(company)))
        if _need("segmentTrend"):
            b["segmentTrend"] = _safe(lambda: segmentTrendBlock(calcSegmentTrend(company)))
        if _need("region"):
            b["region"] = _safe(lambda: breakdownBlock(calcBreakdown(company, "region"), "region"))
        if _need("product"):
            b["product"] = _safe(lambda: breakdownBlock(calcBreakdown(company, "product"), "product"))
        if _need("growth"):
            b["growth"] = _safe(lambda: revenueGrowthBlock(calcRevenueGrowth(company)))
        if _need("concentration"):
            b["concentration"] = _safe(lambda: concentrationBlock(calcConcentration(company)))
        if _need("revenueQuality"):
            b["revenueQuality"] = _safe(lambda: revenueQualityBlock(calcRevenueQuality(company)))
        if _need("growthContribution"):
            b["growthContribution"] = _safe(lambda: growthContributionBlock(calcGrowthContribution(company)))
        if _need("revenueFlags"):
            b["revenueFlags"] = _safe(lambda: revenueFlagsBlock(calcFlags(company)))

    if keys is None or keys & {
        "fundingSources", "capitalOverview", "capitalTimeline", "debtTimeline",
        "interestBurden", "liquidity", "cashFlowStructure", "distressIndicators", "capitalFlags",
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
            b["fundingSources"] = _safe(lambda: fundingSourcesBlock(calcFundingSources(company)))
        if _need("capitalOverview"):
            b["capitalOverview"] = _safe(lambda: capitalOverviewBlock(calcCapitalOverview(company)))
        if _need("capitalTimeline"):
            b["capitalTimeline"] = _safe(lambda: capitalTimelineBlock(calcCapitalTimeline(company)))
        if _need("debtTimeline"):
            b["debtTimeline"] = _safe(lambda: debtTimelineBlock(calcDebtTimeline(company)))
        if _need("interestBurden"):
            b["interestBurden"] = _safe(lambda: interestBurdenBlock(calcInterestBurden(company)))
        if _need("liquidity"):
            b["liquidity"] = _safe(lambda: liquidityBlock(calcLiquidity(company)))
        if _need("cashFlowStructure"):
            b["cashFlowStructure"] = _safe(lambda: cashFlowBlock(calcCashFlowStructure(company)))
        if _need("distressIndicators"):
            b["distressIndicators"] = _safe(lambda: distressBlock(calcDistressIndicators(company)))
        if _need("capitalFlags"):
            b["capitalFlags"] = _safe(lambda: capitalFlagsBlock(calcCapitalFlags(company)))

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
            b["assetStructure"] = _safe(lambda: assetStructureBlock(calcAssetStructure(company)))
        if _need("workingCapital"):
            b["workingCapital"] = _safe(lambda: workingCapitalBlock(calcWorkingCapital(company)))
        if _need("capexPattern"):
            b["capexPattern"] = _safe(lambda: capexBlock(calcCapexPattern(company)))
        if _need("assetFlags"):
            b["assetFlags"] = _safe(lambda: assetFlagsBlock(calcAssetFlags(company)))

    if keys is None or keys & {"cashFlowOverview", "cashQuality", "cashFlowFlags"}:
        from dartlab.analysis.financial.cashflow import (
            calcCashFlowFlags,
            calcCashFlowOverview,
            calcCashQuality,
        )
        from dartlab.review.builders import (
            cashFlowFlagsBlock,
            cashFlowOverviewBlock,
            cashQualityBlock,
        )

        if _need("cashFlowOverview"):
            b["cashFlowOverview"] = _safe(lambda: cashFlowOverviewBlock(calcCashFlowOverview(company)))
        if _need("cashQuality"):
            b["cashQuality"] = _safe(lambda: cashQualityBlock(calcCashQuality(company)))
        if _need("cashFlowFlags"):
            b["cashFlowFlags"] = _safe(lambda: cashFlowFlagsBlock(calcCashFlowFlags(company)))

    # ── 2부: 재무비율 분석 ──
    if keys is None or keys & {"marginTrend", "returnTrend", "dupont", "profitabilityFlags"}:
        from dartlab.analysis.financial.profitability import (
            calcDupont,
            calcMarginTrend,
            calcProfitabilityFlags,
            calcReturnTrend,
        )
        from dartlab.review.builders import (
            dupontBlock,
            marginTrendBlock,
            profitabilityFlagsBlock,
            returnTrendBlock,
        )

        if _need("marginTrend"):
            b["marginTrend"] = _safe(lambda: marginTrendBlock(calcMarginTrend(company)))
        if _need("returnTrend"):
            b["returnTrend"] = _safe(lambda: returnTrendBlock(calcReturnTrend(company)))
        if _need("dupont"):
            b["dupont"] = _safe(lambda: dupontBlock(calcDupont(company)))
        if _need("profitabilityFlags"):
            b["profitabilityFlags"] = _safe(lambda: profitabilityFlagsBlock(calcProfitabilityFlags(company)))

    if keys is None or keys & {"growthTrend", "growthQuality", "growthFlags"}:
        from dartlab.analysis.financial.growthAnalysis import (
            calcGrowthFlags,
            calcGrowthQuality,
            calcGrowthTrend,
        )
        from dartlab.review.builders import (
            growthFlagsBlock,
            growthQualityBlock,
            growthTrendBlock,
        )

        if _need("growthTrend"):
            b["growthTrend"] = _safe(lambda: growthTrendBlock(calcGrowthTrend(company)))
        if _need("growthQuality"):
            b["growthQuality"] = _safe(lambda: growthQualityBlock(calcGrowthQuality(company)))
        if _need("growthFlags"):
            b["growthFlags"] = _safe(lambda: growthFlagsBlock(calcGrowthFlags(company)))

    if keys is None or keys & {"leverageTrend", "coverageTrend", "distressScore", "stabilityFlags"}:
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
            b["leverageTrend"] = _safe(lambda: leverageTrendBlock(calcLeverageTrend(company)))
        if _need("coverageTrend"):
            b["coverageTrend"] = _safe(lambda: coverageTrendBlock(calcCoverageTrend(company)))
        if _need("distressScore"):
            b["distressScore"] = _safe(lambda: distressScoreBlock(calcDistressScore(company)))
        if _need("stabilityFlags"):
            b["stabilityFlags"] = _safe(lambda: stabilityFlagsBlock(calcStabilityFlags(company)))

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
            b["turnoverTrend"] = _safe(lambda: turnoverTrendBlock(calcTurnoverTrend(company)))
        if _need("cccTrend"):
            b["cccTrend"] = _safe(lambda: cccTrendBlock(calcCccTrend(company)))
        if _need("efficiencyFlags"):
            b["efficiencyFlags"] = _safe(lambda: efficiencyFlagsBlock(calcEfficiencyFlags(company)))

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
            b["scorecard"] = _safe(lambda: scorecardBlock(calcScorecard(company)))
        if _need("piotroski"):
            b["piotroski"] = _safe(lambda: piotroskiBlock(calcPiotroskiDetail(company)))
        if _need("summaryFlags"):
            b["summaryFlags"] = _safe(lambda: summaryFlagsBlock(calcSummaryFlags(company)))

    # ── 3부: 심화 분석 ──
    if keys is None or keys & {"accrualAnalysis", "earningsPersistence", "beneishMScore", "earningsQualityFlags"}:
        from dartlab.analysis.financial.earningsQuality import (
            calcAccrualAnalysis,
            calcBeneishTimeline,
            calcEarningsPersistence,
            calcEarningsQualityFlags,
        )
        from dartlab.review.builders import (
            accrualAnalysisBlock,
            beneishMScoreBlock,
            earningsPersistenceBlock,
            earningsQualityFlagsBlock,
        )

        if _need("accrualAnalysis"):
            b["accrualAnalysis"] = _safe(lambda: accrualAnalysisBlock(calcAccrualAnalysis(company)))
        if _need("earningsPersistence"):
            b["earningsPersistence"] = _safe(lambda: earningsPersistenceBlock(calcEarningsPersistence(company)))
        if _need("beneishMScore"):
            b["beneishMScore"] = _safe(lambda: beneishMScoreBlock(calcBeneishTimeline(company)))
        if _need("earningsQualityFlags"):
            b["earningsQualityFlags"] = _safe(lambda: earningsQualityFlagsBlock(calcEarningsQualityFlags(company)))

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
            b["costBreakdown"] = _safe(lambda: costBreakdownBlock(calcCostBreakdown(company)))
        if _need("operatingLeverage"):
            b["operatingLeverage"] = _safe(lambda: operatingLeverageBlock(calcOperatingLeverage(company)))
        if _need("breakevenEstimate"):
            b["breakevenEstimate"] = _safe(lambda: breakevenEstimateBlock(calcBreakevenEstimate(company)))
        if _need("costStructureFlags"):
            b["costStructureFlags"] = _safe(lambda: costStructureFlagsBlock(calcCostStructureFlags(company)))

    if keys is None or keys & {
        "dividendPolicy", "shareholderReturn", "reinvestment", "fcfUsage", "capitalAllocationFlags",
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
            b["dividendPolicy"] = _safe(lambda: dividendPolicyBlock(calcDividendPolicy(company)))
        if _need("shareholderReturn"):
            b["shareholderReturn"] = _safe(lambda: shareholderReturnBlock(calcShareholderReturn(company)))
        if _need("reinvestment"):
            b["reinvestment"] = _safe(lambda: reinvestmentBlock(calcReinvestment(company)))
        if _need("fcfUsage"):
            b["fcfUsage"] = _safe(lambda: fcfUsageBlock(calcFcfUsage(company)))
        if _need("capitalAllocationFlags"):
            b["capitalAllocationFlags"] = _safe(lambda: capitalAllocationFlagsBlock(calcCapitalAllocationFlags(company)))

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
            b["roicTimeline"] = _safe(lambda: roicTimelineBlock(calcRoicTimeline(company)))
        if _need("investmentIntensity"):
            b["investmentIntensity"] = _safe(lambda: investmentIntensityBlock(calcInvestmentIntensity(company)))
        if _need("evaTimeline"):
            b["evaTimeline"] = _safe(lambda: evaTimelineBlock(calcEvaTimeline(company)))
        if _need("investmentFlags"):
            b["investmentFlags"] = _safe(lambda: investmentFlagsBlock(calcInvestmentFlags(company)))

    if keys is None or keys & {
        "isCfDivergence", "isBsDivergence", "anomalyScore",
        "effectiveTaxRate", "deferredTax", "crossStatementFlags",
    }:
        from dartlab.analysis.financial.crossStatement import (
            calcAnomalyScore,
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
            crossStatementFlagsBlock,
            deferredTaxBlock,
            effectiveTaxRateBlock,
            isBsDivergenceBlock,
            isCfDivergenceBlock,
        )

        if _need("isCfDivergence"):
            b["isCfDivergence"] = _safe(lambda: isCfDivergenceBlock(calcIsCfDivergence(company)))
        if _need("isBsDivergence"):
            b["isBsDivergence"] = _safe(lambda: isBsDivergenceBlock(calcIsBsDivergence(company)))
        if _need("anomalyScore"):
            b["anomalyScore"] = _safe(lambda: anomalyScoreBlock(calcAnomalyScore(company)))
        if _need("effectiveTaxRate"):
            b["effectiveTaxRate"] = _safe(lambda: effectiveTaxRateBlock(calcEffectiveTaxRate(company)))
        if _need("deferredTax"):
            b["deferredTax"] = _safe(lambda: deferredTaxBlock(calcDeferredTax(company)))
        if _need("crossStatementFlags"):
            b["crossStatementFlags"] = _safe(
                lambda: crossStatementFlagsBlock(calcCrossStatementFlags(company) + calcTaxFlags(company))
            )

    # ── 4부: 가치평가 ──
    if keys is None or keys & {
        "dcfValuation", "ddmValuation", "relativeValuation", "residualIncome",
        "priceTarget", "reverseImplied", "sensitivity", "valuationSynthesis", "valuationFlags",
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
            b["dcfValuation"] = _safe(lambda: dcfValuationBlock(calcDcf(company)))
        if _need("ddmValuation"):
            b["ddmValuation"] = _safe(lambda: ddmValuationBlock(calcDdm(company)))
        if _need("relativeValuation"):
            b["relativeValuation"] = _safe(lambda: relativeValuationBlock(calcRelVal(company)))
        if _need("residualIncome"):
            b["residualIncome"] = _safe(lambda: residualIncomeBlock(calcRim(company)))
        if _need("priceTarget"):
            b["priceTarget"] = _safe(lambda: priceTargetBlock(calcPriceTarget(company)))
        if _need("reverseImplied"):
            b["reverseImplied"] = _safe(lambda: reverseImpliedBlock(calcReverseImplied(company)))
        if _need("sensitivity"):
            b["sensitivity"] = _safe(lambda: sensitivityBlock(calcSensitivity(company)))
        if _need("valuationSynthesis"):
            b["valuationSynthesis"] = _safe(lambda: valuationSynthesisBlock(calcValuationSynthesis(company)))
        if _need("valuationFlags"):
            b["valuationFlags"] = _safe(lambda: valuationFlagsBlock(calcValuationFlags(company)))

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
            b["ownershipTrend"] = _safe(lambda: ownershipTrendBlock(calcOwnershipTrend(company)))
        if _need("boardComposition"):
            b["boardComposition"] = _safe(lambda: boardCompositionBlock(calcBoardComposition(company)))
        if _need("auditOpinionTrend"):
            b["auditOpinionTrend"] = _safe(lambda: auditOpinionTrendBlock(calcAuditOpinionTrend(company)))
        if _need("governanceFlags"):
            b["governanceFlags"] = _safe(lambda: governanceFlagsBlock(calcGovernanceFlags(company)))

    if keys is None or keys & {
        "disclosureChangeSummary", "keyTopicChanges", "changeIntensity", "disclosureDeltaFlags",
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
                lambda: disclosureChangeSummaryBlock(calcDisclosureChangeSummary(company))
            )
        if _need("keyTopicChanges"):
            b["keyTopicChanges"] = _safe(lambda: keyTopicChangesBlock(calcKeyTopicChanges(company)))
        if _need("changeIntensity"):
            b["changeIntensity"] = _safe(lambda: changeIntensityBlock(calcChangeIntensity(company)))
        if _need("disclosureDeltaFlags"):
            b["disclosureDeltaFlags"] = _safe(lambda: disclosureDeltaFlagsBlock(calcDisclosureDeltaFlags(company)))

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
            b["peerRanking"] = _safe(lambda: peerRankingBlock(calcPeerRanking(company)))
        if _need("riskReturnPosition"):
            b["riskReturnPosition"] = _safe(lambda: riskReturnPositionBlock(calcRiskReturnPosition(company)))
        if _need("peerBenchmarkFlags"):
            b["peerBenchmarkFlags"] = _safe(lambda: peerBenchmarkFlagsBlock(calcPeerBenchmarkFlags(company)))

    # ── 6부: 전망분석 ──
    if keys is None or keys & {
        "revenueForecast", "segmentForecast", "proFormaHighlights",
        "scenarioImpact", "forecastMethodology", "historicalRatios", "forecastFlags",
    }:
        from dartlab.analysis.financial.forecastCalcs import (
            calcForecastFlags,
            calcForecastMethodology,
            calcHistoricalRatios,
            calcProFormaHighlights,
            calcRevenueForecast,
            calcScenarioImpact,
            calcSegmentForecast,
        )
        from dartlab.review.builders import (
            forecastFlagsBlock,
            forecastMethodologyBlock,
            historicalRatiosBlock,
            proFormaHighlightsBlock,
            revenueForecastBlock,
            scenarioImpactBlock,
            segmentForecastBlock,
        )

        if _need("revenueForecast"):
            b["revenueForecast"] = _safe(lambda: revenueForecastBlock(calcRevenueForecast(company)))
        if _need("segmentForecast"):
            b["segmentForecast"] = _safe(lambda: segmentForecastBlock(calcSegmentForecast(company)))
        if _need("proFormaHighlights"):
            b["proFormaHighlights"] = _safe(lambda: proFormaHighlightsBlock(calcProFormaHighlights(company)))
        if _need("scenarioImpact"):
            b["scenarioImpact"] = _safe(lambda: scenarioImpactBlock(calcScenarioImpact(company)))
        if _need("forecastMethodology"):
            b["forecastMethodology"] = _safe(lambda: forecastMethodologyBlock(calcForecastMethodology(company)))
        if _need("historicalRatios"):
            b["historicalRatios"] = _safe(lambda: historicalRatiosBlock(calcHistoricalRatios(company)))
        if _need("forecastFlags"):
            b["forecastFlags"] = _safe(lambda: forecastFlagsBlock(calcForecastFlags(company)))

    from dartlab.review.blockMap import BlockMap

    return BlockMap(b)


def buildReview(
    company,
    section: str | None = None,
    layout: ReviewLayout | None = None,
    helper: bool | None = None,
):
    """Company에서 Review를 생성."""
    from dartlab.review import Review

    ly = layout or DEFAULT_LAYOUT
    showHelper = helper if helper is not None else ly.helper

    corpName = getattr(company, "corpName", "")
    stockCode = getattr(company, "stockCode", "")

    review = Review(stockCode=stockCode, corpName=corpName, layout=ly)

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

        b = buildBlocks(company, keys=neededKeys)

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

    return review
