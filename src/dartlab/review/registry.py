"""review 레지스트리 — 템플릿 기반 Review 생성."""

from __future__ import annotations

from dartlab.review.layout import DEFAULT_LAYOUT, ReviewLayout
from dartlab.review.section import Section
from dartlab.review.templates import TEMPLATE_ORDER, TEMPLATES
from dartlab.review.utils import isTerminal


def buildBlocks(company):
    """블록 사전 -- analysis calc* 결과를 블록으로 변환."""
    from dartlab.analysis.strategy.asset import (
        calcAssetFlags,
        calcAssetStructure,
        calcCapexPattern,
        calcWorkingCapital,
    )
    from dartlab.analysis.strategy.capital import (
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
    from dartlab.analysis.strategy.cashflow import (
        calcCashFlowFlags,
        calcCashFlowOverview,
        calcCashQuality,
    )
    from dartlab.analysis.strategy.revenue import (
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
        accrualAnalysisBlock,
        anomalyScoreBlock,
        assetFlagsBlock,
        assetStructureBlock,
        beneishMScoreBlock,
        breakdownBlock,
        breakevenEstimateBlock,
        capexBlock,
        capitalAllocationFlagsBlock,
        capitalFlagsBlock,
        capitalOverviewBlock,
        capitalTimelineBlock,
        cashFlowBlock,
        cashFlowFlagsBlock,
        cashFlowOverviewBlock,
        cashQualityBlock,
        cccTrendBlock,
        concentrationBlock,
        costBreakdownBlock,
        costStructureFlagsBlock,
        coverageTrendBlock,
        crossStatementFlagsBlock,
        debtTimelineBlock,
        deferredTaxBlock,
        distressBlock,
        distressScoreBlock,
        dividendPolicyBlock,
        dupontBlock,
        earningsPersistenceBlock,
        earningsQualityFlagsBlock,
        effectiveTaxRateBlock,
        efficiencyFlagsBlock,
        evaTimelineBlock,
        fcfUsageBlock,
        fundingSourcesBlock,
        growthContributionBlock,
        growthFlagsBlock,
        growthQualityBlock,
        growthTrendBlock,
        interestBurdenBlock,
        investmentFlagsBlock,
        investmentIntensityBlock,
        isBsDivergenceBlock,
        isCfDivergenceBlock,
        leverageTrendBlock,
        liquidityBlock,
        marginTrendBlock,
        operatingLeverageBlock,
        piotroskiBlock,
        profileBlock,
        profitabilityFlagsBlock,
        reinvestmentBlock,
        returnTrendBlock,
        revenueFlagsBlock,
        revenueGrowthBlock,
        revenueQualityBlock,
        roicTimelineBlock,
        scorecardBlock,
        segmentCompositionBlock,
        segmentTrendBlock,
        shareholderReturnBlock,
        stabilityFlagsBlock,
        summaryFlagsBlock,
        turnoverTrendBlock,
        workingCapitalBlock,
    )

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

    b: dict = {}

    # ── 수익구조 ──
    b["profile"] = _safe(lambda: profileBlock(calcCompanyProfile(company)))
    b["segmentComposition"] = _safe(lambda: segmentCompositionBlock(calcSegmentComposition(company)))
    b["segmentTrend"] = _safe(lambda: segmentTrendBlock(calcSegmentTrend(company)))
    b["region"] = _safe(lambda: breakdownBlock(calcBreakdown(company, "region"), "region"))
    b["product"] = _safe(lambda: breakdownBlock(calcBreakdown(company, "product"), "product"))
    b["growth"] = _safe(lambda: revenueGrowthBlock(calcRevenueGrowth(company)))
    b["concentration"] = _safe(lambda: concentrationBlock(calcConcentration(company)))
    b["revenueQuality"] = _safe(lambda: revenueQualityBlock(calcRevenueQuality(company)))
    b["growthContribution"] = _safe(lambda: growthContributionBlock(calcGrowthContribution(company)))
    b["revenueFlags"] = _safe(lambda: revenueFlagsBlock(calcFlags(company)))

    # ── 자금구조 ──
    b["fundingSources"] = _safe(lambda: fundingSourcesBlock(calcFundingSources(company)))
    b["capitalOverview"] = _safe(lambda: capitalOverviewBlock(calcCapitalOverview(company)))
    b["capitalTimeline"] = _safe(lambda: capitalTimelineBlock(calcCapitalTimeline(company)))
    b["debtTimeline"] = _safe(lambda: debtTimelineBlock(calcDebtTimeline(company)))
    b["interestBurden"] = _safe(lambda: interestBurdenBlock(calcInterestBurden(company)))
    b["liquidity"] = _safe(lambda: liquidityBlock(calcLiquidity(company)))
    b["cashFlowStructure"] = _safe(lambda: cashFlowBlock(calcCashFlowStructure(company)))
    b["distressIndicators"] = _safe(lambda: distressBlock(calcDistressIndicators(company)))
    b["capitalFlags"] = _safe(lambda: capitalFlagsBlock(calcCapitalFlags(company)))

    # ── 자산구조 ──
    b["assetStructure"] = _safe(lambda: assetStructureBlock(calcAssetStructure(company)))
    b["workingCapital"] = _safe(lambda: workingCapitalBlock(calcWorkingCapital(company)))
    b["capexPattern"] = _safe(lambda: capexBlock(calcCapexPattern(company)))
    b["assetFlags"] = _safe(lambda: assetFlagsBlock(calcAssetFlags(company)))

    # ── 현금흐름 ──
    b["cashFlowOverview"] = _safe(lambda: cashFlowOverviewBlock(calcCashFlowOverview(company)))
    b["cashQuality"] = _safe(lambda: cashQualityBlock(calcCashQuality(company)))
    b["cashFlowFlags"] = _safe(lambda: cashFlowFlagsBlock(calcCashFlowFlags(company)))

    # ── 2부: 재무비율 분석 ──
    from dartlab.analysis.strategy.efficiency import (
        calcCccTrend,
        calcEfficiencyFlags,
        calcTurnoverTrend,
    )
    from dartlab.analysis.strategy.growthAnalysis import (
        calcGrowthFlags,
        calcGrowthQuality,
        calcGrowthTrend,
    )
    from dartlab.analysis.strategy.profitability import (
        calcDupont,
        calcMarginTrend,
        calcProfitabilityFlags,
        calcReturnTrend,
    )
    from dartlab.analysis.strategy.scorecard import (
        calcPiotroskiDetail,
        calcScorecard,
        calcSummaryFlags,
    )
    from dartlab.analysis.strategy.stability import (
        calcCoverageTrend,
        calcDistressScore,
        calcLeverageTrend,
        calcStabilityFlags,
    )

    # ── 수익성 ──
    b["marginTrend"] = _safe(lambda: marginTrendBlock(calcMarginTrend(company)))
    b["returnTrend"] = _safe(lambda: returnTrendBlock(calcReturnTrend(company)))
    b["dupont"] = _safe(lambda: dupontBlock(calcDupont(company)))
    b["profitabilityFlags"] = _safe(lambda: profitabilityFlagsBlock(calcProfitabilityFlags(company)))

    # ── 성장성 ──
    b["growthTrend"] = _safe(lambda: growthTrendBlock(calcGrowthTrend(company)))
    b["growthQuality"] = _safe(lambda: growthQualityBlock(calcGrowthQuality(company)))
    b["growthFlags"] = _safe(lambda: growthFlagsBlock(calcGrowthFlags(company)))

    # ── 안정성 ──
    b["leverageTrend"] = _safe(lambda: leverageTrendBlock(calcLeverageTrend(company)))
    b["coverageTrend"] = _safe(lambda: coverageTrendBlock(calcCoverageTrend(company)))
    b["distressScore"] = _safe(lambda: distressScoreBlock(calcDistressScore(company)))
    b["stabilityFlags"] = _safe(lambda: stabilityFlagsBlock(calcStabilityFlags(company)))

    # ── 효율성 ──
    b["turnoverTrend"] = _safe(lambda: turnoverTrendBlock(calcTurnoverTrend(company)))
    b["cccTrend"] = _safe(lambda: cccTrendBlock(calcCccTrend(company)))
    b["efficiencyFlags"] = _safe(lambda: efficiencyFlagsBlock(calcEfficiencyFlags(company)))

    # ── 종합 평가 ──
    b["scorecard"] = _safe(lambda: scorecardBlock(calcScorecard(company)))
    b["piotroski"] = _safe(lambda: piotroskiBlock(calcPiotroskiDetail(company)))
    b["summaryFlags"] = _safe(lambda: summaryFlagsBlock(calcSummaryFlags(company)))

    # ── 3부: 심화 분석 ──
    from dartlab.analysis.strategy.capitalAllocation import (
        calcCapitalAllocationFlags,
        calcDividendPolicy,
        calcFcfUsage,
        calcReinvestment,
        calcShareholderReturn,
    )
    from dartlab.analysis.strategy.costStructure import (
        calcBreakevenEstimate,
        calcCostBreakdown,
        calcCostStructureFlags,
        calcOperatingLeverage,
    )
    from dartlab.analysis.strategy.crossStatement import (
        calcAnomalyScore,
        calcCrossStatementFlags,
        calcIsBsDivergence,
        calcIsCfDivergence,
    )
    from dartlab.analysis.strategy.earningsQuality import (
        calcAccrualAnalysis,
        calcBeneishTimeline,
        calcEarningsPersistence,
        calcEarningsQualityFlags,
    )
    from dartlab.analysis.strategy.investmentAnalysis import (
        calcEvaTimeline,
        calcInvestmentFlags,
        calcInvestmentIntensity,
        calcRoicTimeline,
    )
    from dartlab.analysis.strategy.taxAnalysis import (
        calcDeferredTax,
        calcEffectiveTaxRate,
        calcTaxFlags,
    )

    # ── 이익품질 ──
    b["accrualAnalysis"] = _safe(lambda: accrualAnalysisBlock(calcAccrualAnalysis(company)))
    b["earningsPersistence"] = _safe(lambda: earningsPersistenceBlock(calcEarningsPersistence(company)))
    b["beneishMScore"] = _safe(lambda: beneishMScoreBlock(calcBeneishTimeline(company)))
    b["earningsQualityFlags"] = _safe(lambda: earningsQualityFlagsBlock(calcEarningsQualityFlags(company)))

    # ── 비용구조 ──
    b["costBreakdown"] = _safe(lambda: costBreakdownBlock(calcCostBreakdown(company)))
    b["operatingLeverage"] = _safe(lambda: operatingLeverageBlock(calcOperatingLeverage(company)))
    b["breakevenEstimate"] = _safe(lambda: breakevenEstimateBlock(calcBreakevenEstimate(company)))
    b["costStructureFlags"] = _safe(lambda: costStructureFlagsBlock(calcCostStructureFlags(company)))

    # ── 자본배분 ──
    b["dividendPolicy"] = _safe(lambda: dividendPolicyBlock(calcDividendPolicy(company)))
    b["shareholderReturn"] = _safe(lambda: shareholderReturnBlock(calcShareholderReturn(company)))
    b["reinvestment"] = _safe(lambda: reinvestmentBlock(calcReinvestment(company)))
    b["fcfUsage"] = _safe(lambda: fcfUsageBlock(calcFcfUsage(company)))
    b["capitalAllocationFlags"] = _safe(lambda: capitalAllocationFlagsBlock(calcCapitalAllocationFlags(company)))

    # ── 투자효율 ──
    b["roicTimeline"] = _safe(lambda: roicTimelineBlock(calcRoicTimeline(company)))
    b["investmentIntensity"] = _safe(lambda: investmentIntensityBlock(calcInvestmentIntensity(company)))
    b["evaTimeline"] = _safe(lambda: evaTimelineBlock(calcEvaTimeline(company)))
    b["investmentFlags"] = _safe(lambda: investmentFlagsBlock(calcInvestmentFlags(company)))

    # ── 재무정합성 ──
    b["isCfDivergence"] = _safe(lambda: isCfDivergenceBlock(calcIsCfDivergence(company)))
    b["isBsDivergence"] = _safe(lambda: isBsDivergenceBlock(calcIsBsDivergence(company)))
    b["anomalyScore"] = _safe(lambda: anomalyScoreBlock(calcAnomalyScore(company)))
    b["effectiveTaxRate"] = _safe(lambda: effectiveTaxRateBlock(calcEffectiveTaxRate(company)))
    b["deferredTax"] = _safe(lambda: deferredTaxBlock(calcDeferredTax(company)))
    b["crossStatementFlags"] = _safe(
        lambda: crossStatementFlagsBlock(calcCrossStatementFlags(company) + calcTaxFlags(company))
    )

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

        b = buildBlocks(company)

        # 템플릿 순서 결정
        if section is not None:
            templateKeys = [section] if section in TEMPLATES else []
        elif ly.sectionOrder is not None:
            templateKeys = [k for k in ly.sectionOrder if k in TEMPLATES]
        else:
            templateKeys = list(TEMPLATE_ORDER)

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

        threads = detectThreads(company, b)
        for thread in threads:
            for sec in review.sections:
                if sec.key in thread.involvedSections:
                    sec.threads.append(thread)
        review.circulationSummary = buildCirculationSummary(threads) if threads else ""

    return review
