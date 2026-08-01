"""story 레지스트리 - 템플릿 기반 Story 생성.

buildBlocks 는 분석 calc* 결과를 블록으로 변환해 BlockMap 으로 반환한다. 100+ 블록을
26+ 그룹으로 묶어 그룹별 빌더 함수로 분리 - 새 블록 추가 시 해당 그룹만 수정.
buildBlocks 본체는 preset 처리 + currency setup + 그룹 loop 만 담당.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from dartlab.story.blocks import Block
from dartlab.story.layout import StoryLayout
from dartlab.story.section import Section
from dartlab.story.templates import TEMPLATE_ORDER, TEMPLATES
from dartlab.story.utils import isTerminal

try:
    import polars as _pl_lib

    _POLARS_ERR: type[Exception] = _pl_lib.exceptions.PolarsError
except ImportError:
    _POLARS_ERR = RuntimeError

_SAFE_BUILD_ERRORS: tuple[type[Exception], ...] = (
    KeyError,
    ValueError,
    TypeError,
    AttributeError,
    ArithmeticError,
    ImportError,
    RuntimeError,
    IndexError,
    _POLARS_ERR,
)

_LOG = logging.getLogger("dartlab.story")

# Phase 4 G15a: buildBlocks preset - 전체 호출 113초/7.9GB 회피
_MINIMAL_KEYS: frozenset[str] = frozenset(
    {
        "profile",
        "segmentComposition",
        "revenueGrowth",
        "marginTrend",
        "cashFlowOverview",
        "cashQuality",
        "leverageTrend",
        "assetStructure",
        "dFV",
        "lifeCycleStage",
        "valuationSins",
    }
)

_STANDARD_KEYS: frozenset[str] = _MINIMAL_KEYS | frozenset(
    {
        "concentration",
        "growthTrend",
        "roicTimeline",
        "distressScore",
        "valuationSynthesis",
        "plausibilityBand",
        # storyPrecedents 제외 (scan 271MB 다운로드 회피 - preset="full" 에서만)
    }
)


def _makeSafeCall(failures: list[dict]):
    """블록 빌드 실패를 기록하면서 빈 list 를 돌려주는 호출기를 만든다.

    한 그룹의 실패가 다른 그룹을 무너뜨리지 않게 막는 것이 이 장치의 목적이고 그것은 옳다.
    다만 예전에는 실패를 debug 로그로만 흘려서, 데이터가 없어 비어 있는 블록과 빌더가 터져서
    비어 있는 블록이 결과만 봐서는 같아 보였다. 보고서는 멀쩡히 완성된 얼굴로 나갔다.
    실패를 목록에 남겨 `Story.lensGaps` 로 올려 보낸다.

    잡는 예외 카테고리:
        KeyError/ValueError/TypeError/AttributeError - 데이터 누락 + 타입 mismatch
        ArithmeticError/IndexError - 계산식 + 인덱싱 실패
        ImportError/RuntimeError - 외부 모듈 + 런타임 의존성 실패
        polars.exceptions.PolarsError - DataFrame 연산 실패
    """

    def _safeCall(fn: Callable):
        try:
            return fn()
        except _SAFE_BUILD_ERRORS as exc:
            name = getattr(fn, "__name__", "?")
            _LOG.debug("story block build 실패: %s - %s: %s", name, type(exc).__name__, exc)
            failures.append(
                {
                    "code": "BLOCK_BUILD_FAILED",
                    "builder": name,
                    "error": type(exc).__name__,
                    "message": str(exc),
                }
            )
            return []

    return _safeCall


def _safeCall(fn: Callable):
    """기록 없이 실패를 흡수한다. 실패를 남길 곳이 없는 호출자용 얇은 래퍼."""
    return _makeSafeCall([])(fn)


def _resolvePresetKeys(keys: set[str] | None, preset: str) -> set[str] | None:
    """preset → keys 변환. keys 명시되면 preset 무시.

    minimal (~30초): 6막 골격 블록 ~11개
    standard (기본, ~60초): minimal + 주요 분석 블록 (storyPrecedents 제외)
    full (~113초): 전체 블록 - keys=None 유지
    """
    if keys is not None:
        return keys
    if preset == "minimal":
        return set(_MINIMAL_KEYS)
    if preset == "standard":
        return set(_STANDARD_KEYS)
    return None  # full


def _setupCurrency(company) -> None:
    """story builders + analysis 의 금액 포맷을 company.currency 로 설정.

    contextvars - 스레드 안전. analysis.financial.capital 의 _analysis_currency
    가 없으면 (구버전) silent skip.
    """
    from dartlab.story.builders import _storyCurrency

    _currency = getattr(company, "currency", "KRW")
    _storyCurrency.set(_currency)
    try:
        from dartlab.analysis.financial import capital as capital_module

        getattr(capital_module, "_analysis_currency").set(_currency)
    except (ImportError, AttributeError):
        pass


def _makeNeed(keys: set[str] | None) -> Callable[[str], bool]:
    """need(key) - 그룹 빌더가 사용할 키 게이트 헬퍼."""

    def _need(key: str) -> bool:
        return keys is None or key in keys

    return _need


# ──────────────────────────────────────────────────────────────────
# 그룹 빌더 함수 - buildBlocks 가 호출하는 그룹 단위 책임 분해.
# 각 함수: (company, keys, basePeriod, safe, need, out) -> None.
# 그룹 게이트 (keys 매칭) + lazy import (calc + builder) + 블록 등록.
# ──────────────────────────────────────────────────────────────────


def _buildRevenueBlocks(company, keys, basePeriod, safe: Callable, need: Callable, out: dict) -> None:
    """1 부 - 사업구조 (10 블록)."""
    if keys is not None and not (
        keys
        & {
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
        }
    ):
        return
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
    from dartlab.story.builders import (
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

    if need("profile"):
        out["profile"] = safe(lambda: profileBlock(calcCompanyProfile(company, basePeriod=basePeriod)))
    if need("segmentComposition"):
        out["segmentComposition"] = safe(
            lambda: segmentCompositionBlock(calcSegmentComposition(company, basePeriod=basePeriod))
        )
    if need("segmentTrend"):
        out["segmentTrend"] = safe(lambda: segmentTrendBlock(calcSegmentTrend(company, basePeriod=basePeriod)))
    if need("region"):
        out["region"] = safe(lambda: breakdownBlock(calcBreakdown(company, "region", basePeriod=basePeriod), "region"))
    if need("product"):
        out["product"] = safe(
            lambda: breakdownBlock(calcBreakdown(company, "product", basePeriod=basePeriod), "product")
        )
    if need("growth"):
        out["growth"] = safe(lambda: revenueGrowthBlock(calcRevenueGrowth(company, basePeriod=basePeriod)))
    if need("concentration"):
        out["concentration"] = safe(lambda: concentrationBlock(calcConcentration(company, basePeriod=basePeriod)))
    if need("revenueQuality"):
        out["revenueQuality"] = safe(lambda: revenueQualityBlock(calcRevenueQuality(company, basePeriod=basePeriod)))
    if need("growthContribution"):
        out["growthContribution"] = safe(
            lambda: growthContributionBlock(calcGrowthContribution(company, basePeriod=basePeriod))
        )
    if need("revenueFlags"):
        out["revenueFlags"] = safe(lambda: revenueFlagsBlock(calcFlags(company, basePeriod=basePeriod)))


def _buildCapitalBlocks(company, keys, basePeriod, safe: Callable, need: Callable, out: dict) -> None:
    """1 부 - 자본구조 (9 블록)."""
    if keys is not None and not (
        keys
        & {
            "fundingSources",
            "capitalOverview",
            "capitalTimeline",
            "debtTimeline",
            "interestBurden",
            "liquidity",
            "cashFlowStructure",
            "distressIndicators",
            "capitalFlags",
        }
    ):
        return
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
    from dartlab.story.builders import (
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

    if need("fundingSources"):
        out["fundingSources"] = safe(
            lambda: fundingSourcesBlock(calcFundingSources(company, basePeriod=basePeriod) or {})
        )
    if need("capitalOverview"):
        out["capitalOverview"] = safe(lambda: capitalOverviewBlock(calcCapitalOverview(company, basePeriod=basePeriod)))
    if need("capitalTimeline"):
        out["capitalTimeline"] = safe(lambda: capitalTimelineBlock(calcCapitalTimeline(company, basePeriod=basePeriod)))
    if need("debtTimeline"):
        out["debtTimeline"] = safe(lambda: debtTimelineBlock(calcDebtTimeline(company, basePeriod=basePeriod)))
    if need("interestBurden"):
        out["interestBurden"] = safe(lambda: interestBurdenBlock(calcInterestBurden(company, basePeriod=basePeriod)))
    if need("liquidity"):
        out["liquidity"] = safe(lambda: liquidityBlock(calcLiquidity(company, basePeriod=basePeriod)))
    if need("cashFlowStructure"):
        out["cashFlowStructure"] = safe(lambda: cashFlowBlock(calcCashFlowStructure(company, basePeriod=basePeriod)))
    if need("distressIndicators"):
        out["distressIndicators"] = safe(lambda: distressBlock(calcDistressIndicators(company, basePeriod=basePeriod)))
    if need("capitalFlags"):
        out["capitalFlags"] = safe(lambda: capitalFlagsBlock(calcCapitalFlags(company, basePeriod=basePeriod)))


def _buildAssetBlocks(company, keys, basePeriod, safe: Callable, need: Callable, out: dict) -> None:
    """1 부 - 자산구조 (4 블록)."""
    if keys is not None and not (keys & {"assetStructure", "workingCapital", "capexPattern", "assetFlags"}):
        return
    from dartlab.analysis.financial.asset import (
        calcAssetFlags,
        calcAssetStructure,
        calcCapexPattern,
        calcWorkingCapital,
    )
    from dartlab.story.builders import (
        assetFlagsBlock,
        assetStructureBlock,
        capexBlock,
        workingCapitalBlock,
    )

    if need("assetStructure"):
        out["assetStructure"] = safe(lambda: assetStructureBlock(calcAssetStructure(company, basePeriod=basePeriod)))
    if need("workingCapital"):
        out["workingCapital"] = safe(lambda: workingCapitalBlock(calcWorkingCapital(company, basePeriod=basePeriod)))
    if need("capexPattern"):
        out["capexPattern"] = safe(lambda: capexBlock(calcCapexPattern(company, basePeriod=basePeriod)))
    if need("assetFlags"):
        out["assetFlags"] = safe(lambda: assetFlagsBlock(calcAssetFlags(company, basePeriod=basePeriod)))


def _buildCashflowBlocks(company, keys, basePeriod, safe: Callable, need: Callable, out: dict) -> None:
    """1 부 - 현금흐름 (4 블록)."""
    if keys is not None and not (keys & {"cashFlowOverview", "cashQuality", "ocfDecomposition", "cashFlowFlags"}):
        return
    from dartlab.analysis.financial.cashflow import (
        calcCashFlowFlags,
        calcCashFlowOverview,
        calcCashQuality,
        calcOcfDecomposition,
    )
    from dartlab.story.builders import (
        cashFlowFlagsBlock,
        cashFlowOverviewBlock,
        cashQualityBlock,
        ocfDecompositionBlock,
    )

    if need("cashFlowOverview"):
        out["cashFlowOverview"] = safe(
            lambda: cashFlowOverviewBlock(calcCashFlowOverview(company, basePeriod=basePeriod))
        )
    if need("cashQuality"):
        out["cashQuality"] = safe(lambda: cashQualityBlock(calcCashQuality(company, basePeriod=basePeriod)))
    if need("ocfDecomposition"):
        out["ocfDecomposition"] = safe(
            lambda: ocfDecompositionBlock(calcOcfDecomposition(company, basePeriod=basePeriod))
        )
    if need("cashFlowFlags"):
        out["cashFlowFlags"] = safe(lambda: cashFlowFlagsBlock(calcCashFlowFlags(company, basePeriod=basePeriod)))


def _buildProfitabilityBlocks(company, keys, basePeriod, safe: Callable, need: Callable, out: dict) -> None:
    """2 부 - 수익성 (6 블록)."""
    if keys is not None and not (
        keys & {"marginTrend", "returnTrend", "dupont", "penmanDecomposition", "roicTree", "profitabilityFlags"}
    ):
        return
    from dartlab.analysis.financial.profitability import (
        calcMarginTrend,
        calcPenmanDecomposition,
        calcProfitabilityFlags,
        calcReturnTrend,
        calcRoicTree,
    )
    from dartlab.story.builders import (
        dupontBlock,
        marginTrendBlock,
        penmanDecompositionBlock,
        profitabilityFlagsBlock,
        returnTrendBlock,
        roicTreeBlock,
    )

    if need("marginTrend"):
        out["marginTrend"] = safe(lambda: marginTrendBlock(calcMarginTrend(company, basePeriod=basePeriod)))
    if need("returnTrend"):
        out["returnTrend"] = safe(lambda: returnTrendBlock(calcReturnTrend(company, basePeriod=basePeriod)))
    if need("dupont"):
        out["dupont"] = safe(lambda: dupontBlock(calcReturnTrend(company, basePeriod=basePeriod)))
    if need("penmanDecomposition"):
        out["penmanDecomposition"] = safe(
            lambda: penmanDecompositionBlock(calcPenmanDecomposition(company, basePeriod=basePeriod))
        )
    if need("roicTree"):
        out["roicTree"] = safe(lambda: roicTreeBlock(calcRoicTree(company, basePeriod=basePeriod)))
    if need("profitabilityFlags"):
        out["profitabilityFlags"] = safe(
            lambda: profitabilityFlagsBlock(calcProfitabilityFlags(company, basePeriod=basePeriod))
        )


def _buildGrowthBlocks(company, keys, basePeriod, safe: Callable, need: Callable, out: dict) -> None:
    """2 부 - 성장 (4 블록)."""
    if keys is not None and not (keys & {"growthTrend", "growthQuality", "cagrComparison", "growthFlags"}):
        return
    from dartlab.analysis.financial.growthAnalysis import (
        calcCagrComparison,
        calcGrowthFlags,
        calcGrowthQuality,
        calcGrowthTrend,
    )
    from dartlab.story.builders import (
        cagrComparisonBlock,
        growthFlagsBlock,
        growthQualityBlock,
        growthTrendBlock,
    )

    if need("growthTrend"):
        out["growthTrend"] = safe(lambda: growthTrendBlock(calcGrowthTrend(company, basePeriod=basePeriod)))
    if need("growthQuality"):
        out["growthQuality"] = safe(lambda: growthQualityBlock(calcGrowthQuality(company, basePeriod=basePeriod)))
    if need("cagrComparison"):
        out["cagrComparison"] = safe(lambda: cagrComparisonBlock(calcCagrComparison(company, basePeriod=basePeriod)))
    if need("growthFlags"):
        out["growthFlags"] = safe(lambda: growthFlagsBlock(calcGrowthFlags(company, basePeriod=basePeriod)))


def _buildStabilityBlocks(company, keys, basePeriod, safe: Callable, need: Callable, out: dict) -> None:
    """2 부 - 안정성 (5+ 블록 - scenarioSensitivity/criticalAssumptions/improvementLevers/marketRisk 공유)."""
    if keys is not None and not (
        keys
        & {
            "leverageTrend",
            "coverageTrend",
            "distressScore",
            "stabilityFlags",
            "marketRisk",
            "scenarioSensitivity",
            "criticalAssumptions",
            "improvementLevers",
        }
    ):
        return
    from dartlab.analysis.financial.stability import (
        calcCoverageTrend,
        calcDistressScore,
        calcLeverageTrend,
        calcStabilityFlags,
    )
    from dartlab.story.builders import (
        coverageTrendBlock,
        distressScoreBlock,
        leverageTrendBlock,
        stabilityFlagsBlock,
    )

    if need("leverageTrend"):
        out["leverageTrend"] = safe(lambda: leverageTrendBlock(calcLeverageTrend(company, basePeriod=basePeriod)))
    if need("coverageTrend"):
        out["coverageTrend"] = safe(lambda: coverageTrendBlock(calcCoverageTrend(company, basePeriod=basePeriod)))
    if need("distressScore"):
        out["distressScore"] = safe(lambda: distressScoreBlock(calcDistressScore(company, basePeriod=basePeriod)))
    if need("stabilityFlags"):
        out["stabilityFlags"] = safe(lambda: stabilityFlagsBlock(calcStabilityFlags(company, basePeriod=basePeriod)))
    if need("scenarioSensitivity") or need("criticalAssumptions"):
        from dartlab.analysis.financial.scenarioSensitivity import calcScenarioSensitivity
        from dartlab.story.builders import criticalAssumptionsBlock, scenarioSensitivityBlock

        _ss = safe(lambda: calcScenarioSensitivity(company, basePeriod=basePeriod))
        if need("scenarioSensitivity"):
            out["scenarioSensitivity"] = safe(lambda: scenarioSensitivityBlock(_ss))
        if need("criticalAssumptions"):
            out["criticalAssumptions"] = safe(lambda: criticalAssumptionsBlock(_ss))
        # improvementLevers - 같은 SS 캐시 시점, 메모리 압박 전
        if need("improvementLevers") and _ss:
            from dartlab.analysis.financial.scenarioSensitivity import calcImprovementLevers
            from dartlab.story.builders import improvementLeversBlock

            try:
                _il_data = calcImprovementLevers(company, basePeriod=basePeriod)
                out["improvementLevers"] = improvementLeversBlock(_il_data) if _il_data else []
            except Exception as _e:
                _LOG.debug("improvementLevers: %s", _e)
                out["improvementLevers"] = []
    if need("marketRisk"):
        from dartlab.quant.screen.extended import calcMarketRisk
        from dartlab.story.builders import marketRiskBlock

        out["marketRisk"] = safe(lambda: marketRiskBlock(calcMarketRisk(company)))


def _buildEfficiencyBlocks(company, keys, basePeriod, safe: Callable, need: Callable, out: dict) -> None:
    """2 부 - 효율성 (3 블록)."""
    if keys is not None and not (keys & {"turnoverTrend", "cccTrend", "efficiencyFlags"}):
        return
    from dartlab.analysis.financial.efficiency import (
        calcEfficiencyFlags,
        calcTurnoverTrend,
    )
    from dartlab.story.builders import (
        cccTrendBlock,
        efficiencyFlagsBlock,
        turnoverTrendBlock,
    )

    if need("turnoverTrend"):
        out["turnoverTrend"] = safe(lambda: turnoverTrendBlock(calcTurnoverTrend(company, basePeriod=basePeriod)))
    if need("cccTrend"):
        out["cccTrend"] = safe(lambda: cccTrendBlock(calcTurnoverTrend(company, basePeriod=basePeriod)))
    if need("efficiencyFlags"):
        out["efficiencyFlags"] = safe(lambda: efficiencyFlagsBlock(calcEfficiencyFlags(company, basePeriod=basePeriod)))


def _buildScorecardBlocks(company, keys, basePeriod, safe: Callable, need: Callable, out: dict) -> None:
    """2 부 - 종합 (3 블록)."""
    if keys is not None and not (keys & {"scorecard", "piotroski", "summaryFlags"}):
        return
    from dartlab.analysis.financial.scorecard import (
        calcPiotroskiDetail,
        calcScorecard,
        calcSummaryFlags,
    )
    from dartlab.story.builders import (
        piotroskiBlock,
        scorecardBlock,
        summaryFlagsBlock,
    )

    if need("scorecard"):
        out["scorecard"] = safe(lambda: scorecardBlock(calcScorecard(company, basePeriod=basePeriod)))
    if need("piotroski"):
        out["piotroski"] = safe(lambda: piotroskiBlock(calcPiotroskiDetail(company, basePeriod=basePeriod)))
    if need("summaryFlags"):
        out["summaryFlags"] = safe(lambda: summaryFlagsBlock(calcSummaryFlags(company, basePeriod=basePeriod)))


def _buildIndustryBlocks(company, keys, basePeriod, safe: Callable, need: Callable, out: dict) -> None:
    """업종별 KPI + 산업 밸류체인 (4 블록)."""
    if keys is not None and not (keys & {"sectorKpi", "chainPosition", "sectorMetrics", "sectorOutlook"}):
        return
    if need("sectorKpi"):
        from dartlab.analysis.financial.sectorKpi import sectorKpi as _sectorKpi
        from dartlab.story.builders import sectorKpiBlock

        out["sectorKpi"] = safe(lambda: sectorKpiBlock(_sectorKpi(company)))

    if keys is None or keys & {"chainPosition", "sectorMetrics", "sectorOutlook"}:
        from dartlab.industry.calcs.companyCalcs import (
            calcChainPosition,
            calcSectorCycle,
            calcSectorDynamics,
            calcSectorMetrics,
        )
        from dartlab.story.builders import chainPositionBlock, sectorMetricsBlock, sectorOutlookBlock

        if need("chainPosition"):
            out["chainPosition"] = safe(lambda: chainPositionBlock(calcChainPosition(company)))
        if need("sectorMetrics"):
            out["sectorMetrics"] = safe(lambda: sectorMetricsBlock(calcSectorMetrics(company)))
        if need("sectorOutlook"):
            out["sectorOutlook"] = safe(
                lambda: sectorOutlookBlock(calcSectorCycle(company), calcSectorDynamics(company))
            )


def _buildEarningsQualityBlocks(company, keys, basePeriod, safe: Callable, need: Callable, out: dict) -> None:
    """3 부 - 이익품질 (6 블록)."""
    if keys is not None and not (
        keys
        & {
            "accrualAnalysis",
            "earningsPersistence",
            "beneishMScore",
            "richardsonAccrual",
            "nonOperatingBreakdown",
            "earningsQualityFlags",
        }
    ):
        return
    from dartlab.analysis.financial.earningsQuality import (
        calcAccrualAnalysis,
        calcBeneishTimeline,
        calcEarningsPersistence,
        calcEarningsQualityFlags,
        calcNonOperatingBreakdown,
        calcRichardsonAccrual,
    )
    from dartlab.story.builders import (
        accrualAnalysisBlock,
        beneishMScoreBlock,
        earningsPersistenceBlock,
        earningsQualityFlagsBlock,
        nonOperatingBreakdownBlock,
        richardsonAccrualBlock,
    )

    if need("accrualAnalysis"):
        out["accrualAnalysis"] = safe(
            lambda: accrualAnalysisBlock(calcAccrualAnalysis(company, basePeriod=basePeriod) or {})
        )
    if need("earningsPersistence"):
        out["earningsPersistence"] = safe(
            lambda: earningsPersistenceBlock(calcEarningsPersistence(company, basePeriod=basePeriod))
        )
    if need("beneishMScore"):
        out["beneishMScore"] = safe(lambda: beneishMScoreBlock(calcBeneishTimeline(company, basePeriod=basePeriod)))
    if need("richardsonAccrual"):
        out["richardsonAccrual"] = safe(
            lambda: richardsonAccrualBlock(calcRichardsonAccrual(company, basePeriod=basePeriod))
        )
    if need("nonOperatingBreakdown"):
        out["nonOperatingBreakdown"] = safe(
            lambda: nonOperatingBreakdownBlock(calcNonOperatingBreakdown(company, basePeriod=basePeriod))
        )
    if need("earningsQualityFlags"):
        out["earningsQualityFlags"] = safe(
            lambda: earningsQualityFlagsBlock(calcEarningsQualityFlags(company, basePeriod=basePeriod))
        )


def _buildCostStructureBlocks(company, keys, basePeriod, safe: Callable, need: Callable, out: dict) -> None:
    """3 부 - 비용구조 (4 블록)."""
    if keys is not None and not (
        keys & {"costBreakdown", "operatingLeverage", "breakevenEstimate", "costStructureFlags"}
    ):
        return
    from dartlab.analysis.financial.costStructure import (
        calcBreakevenEstimate,
        calcCostBreakdown,
        calcCostStructureFlags,
        calcOperatingLeverage,
    )
    from dartlab.story.builders import (
        breakevenEstimateBlock,
        costBreakdownBlock,
        costStructureFlagsBlock,
        operatingLeverageBlock,
    )

    if need("costBreakdown"):
        out["costBreakdown"] = safe(lambda: costBreakdownBlock(calcCostBreakdown(company, basePeriod=basePeriod)))
    if need("operatingLeverage"):
        out["operatingLeverage"] = safe(
            lambda: operatingLeverageBlock(calcOperatingLeverage(company, basePeriod=basePeriod))
        )
    if need("breakevenEstimate"):
        out["breakevenEstimate"] = safe(
            lambda: breakevenEstimateBlock(calcBreakevenEstimate(company, basePeriod=basePeriod))
        )
    if need("costStructureFlags"):
        out["costStructureFlags"] = safe(
            lambda: costStructureFlagsBlock(calcCostStructureFlags(company, basePeriod=basePeriod))
        )


def _buildCapitalAllocationBlocks(company, keys, basePeriod, safe: Callable, need: Callable, out: dict) -> None:
    """3 부 - 자본배분 (8 블록 - div/sh 결과 캐시 공유)."""
    if keys is not None and not (
        keys
        & {
            "dividendPolicy",
            "shareholderReturn",
            "reinvestment",
            "fcfUsage",
            "dividendSustainability",
            "totalShareholderReturn",
            "treasuryStockStatus",
            "capitalAllocationFlags",
        }
    ):
        return
    from dartlab.analysis.financial.capitalAllocation import (
        calcCapitalAllocationFlags,
        calcDividendPolicy,
        calcFcfUsage,
        calcReinvestment,
        calcShareholderReturn,
        calcTreasuryStockStatus,
    )
    from dartlab.story.builders import (
        capitalAllocationFlagsBlock,
        dividendPolicyBlock,
        dividendSustainabilityBlock,
        fcfUsageBlock,
        reinvestmentBlock,
        shareholderReturnBlock,
        totalShareholderReturnBlock,
        treasuryStockStatusBlock,
    )

    _divCache: dict = {}
    _shCache: dict = {}

    def _getDiv():
        if "v" not in _divCache:
            _divCache["v"] = calcDividendPolicy(company, basePeriod=basePeriod)
        return _divCache["v"]

    def _getSh():
        if "v" not in _shCache:
            _shCache["v"] = calcShareholderReturn(company, basePeriod=basePeriod)
        return _shCache["v"]

    if need("dividendPolicy"):
        out["dividendPolicy"] = safe(lambda: dividendPolicyBlock(_getDiv()))
    if need("shareholderReturn"):
        out["shareholderReturn"] = safe(lambda: shareholderReturnBlock(_getSh()))
    if need("reinvestment"):
        out["reinvestment"] = safe(lambda: reinvestmentBlock(calcReinvestment(company, basePeriod=basePeriod)))
    if need("fcfUsage"):
        out["fcfUsage"] = safe(lambda: fcfUsageBlock(calcFcfUsage(company, basePeriod=basePeriod)))
    if need("dividendSustainability"):
        out["dividendSustainability"] = safe(lambda: dividendSustainabilityBlock(_getDiv(), _getSh()))
    if need("totalShareholderReturn"):
        out["totalShareholderReturn"] = safe(lambda: totalShareholderReturnBlock(_getSh()))
    if need("treasuryStockStatus"):
        out["treasuryStockStatus"] = safe(
            lambda: treasuryStockStatusBlock(calcTreasuryStockStatus(company, basePeriod=basePeriod))
        )
    if need("capitalAllocationFlags"):
        out["capitalAllocationFlags"] = safe(
            lambda: capitalAllocationFlagsBlock(calcCapitalAllocationFlags(company, basePeriod=basePeriod))
        )


def _buildInvestmentBlocks(company, keys, basePeriod, safe: Callable, need: Callable, out: dict) -> None:
    """3 부 - 투자효율 (4 블록)."""
    if keys is not None and not (keys & {"roicTimeline", "investmentIntensity", "evaTimeline", "investmentFlags"}):
        return
    from dartlab.analysis.financial.investmentAnalysis import (
        calcEvaTimeline,
        calcInvestmentFlags,
        calcInvestmentIntensity,
        calcRoicTimeline,
    )
    from dartlab.story.builders import (
        evaTimelineBlock,
        investmentFlagsBlock,
        investmentIntensityBlock,
        roicTimelineBlock,
    )

    if need("roicTimeline"):
        out["roicTimeline"] = safe(lambda: roicTimelineBlock(calcRoicTimeline(company, basePeriod=basePeriod)))
    if need("investmentIntensity"):
        out["investmentIntensity"] = safe(
            lambda: investmentIntensityBlock(calcInvestmentIntensity(company, basePeriod=basePeriod))
        )
    if need("evaTimeline"):
        out["evaTimeline"] = safe(lambda: evaTimelineBlock(calcEvaTimeline(company, basePeriod=basePeriod)))
    if need("investmentFlags"):
        out["investmentFlags"] = safe(lambda: investmentFlagsBlock(calcInvestmentFlags(company, basePeriod=basePeriod)))


def _buildCrossStatementBlocks(company, keys, basePeriod, safe: Callable, need: Callable, out: dict) -> None:
    """3 부 - 재무정합성 + 세무 (7 블록)."""
    if keys is not None and not (
        keys
        & {
            "isCfDivergence",
            "isBsDivergence",
            "anomalyScore",
            "articulationCheck",
            "effectiveTaxRate",
            "deferredTax",
            "crossStatementFlags",
        }
    ):
        return
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
    from dartlab.story.builders import (
        anomalyScoreBlock,
        articulationCheckBlock,
        crossStatementFlagsBlock,
        deferredTaxBlock,
        effectiveTaxRateBlock,
        isBsDivergenceBlock,
        isCfDivergenceBlock,
    )

    if need("isCfDivergence"):
        out["isCfDivergence"] = safe(lambda: isCfDivergenceBlock(calcIsCfDivergence(company, basePeriod=basePeriod)))
    if need("isBsDivergence"):
        out["isBsDivergence"] = safe(lambda: isBsDivergenceBlock(calcIsBsDivergence(company, basePeriod=basePeriod)))
    if need("anomalyScore"):
        out["anomalyScore"] = safe(lambda: anomalyScoreBlock(calcAnomalyScore(company, basePeriod=basePeriod)))
    if need("articulationCheck"):
        out["articulationCheck"] = safe(
            lambda: articulationCheckBlock(calcArticulationCheck(company, basePeriod=basePeriod))
        )
    if need("effectiveTaxRate"):
        out["effectiveTaxRate"] = safe(
            lambda: effectiveTaxRateBlock(calcEffectiveTaxRate(company, basePeriod=basePeriod))
        )
    if need("deferredTax"):
        out["deferredTax"] = safe(lambda: deferredTaxBlock(calcDeferredTax(company, basePeriod=basePeriod)))
    if need("crossStatementFlags"):
        out["crossStatementFlags"] = safe(
            lambda: crossStatementFlagsBlock(
                calcCrossStatementFlags(company, basePeriod=basePeriod) + calcTaxFlags(company, basePeriod=basePeriod)
            )
        )


def _buildCreditBlocks(company, keys, basePeriod, safe: Callable, need: Callable, out: dict) -> None:
    """3-6 - 신용평가 (8+ 블록)."""
    if keys is not None and not (
        keys
        & {
            "creditMetrics",
            "creditScore",
            "creditHistory",
            "cashFlowGrade",
            "creditPeerPosition",
            "creditFlags",
            "creditNarrative",
            "creditAudit",
            "creditScenario",
        }
    ):
        return
    from dartlab.credit.scoring.calcs import (
        calcCashFlowGrade,
        calcCreditAudit,
        calcCreditFlags,
        calcCreditHistory,
        calcCreditMetrics,
        calcCreditNarrative,
        calcCreditPeerPosition,
        calcCreditScore,
    )
    from dartlab.story.builders import (
        cashFlowGradeBlock,
        creditAuditBlock,
        creditFlagsBlock,
        creditHistoryBlock,
        creditMetricsBlock,
        creditNarrativeBlock,
        creditPeerPositionBlock,
        creditScoreBlock,
    )

    if need("creditMetrics"):
        out["creditMetrics"] = safe(lambda: creditMetricsBlock(calcCreditMetrics(company, basePeriod=basePeriod)))
    if need("creditScore"):
        out["creditScore"] = safe(lambda: creditScoreBlock(calcCreditScore(company, basePeriod=basePeriod)))
    if need("creditHistory"):
        out["creditHistory"] = safe(lambda: creditHistoryBlock(calcCreditHistory(company, basePeriod=basePeriod)))
    if need("cashFlowGrade"):
        out["cashFlowGrade"] = safe(lambda: cashFlowGradeBlock(calcCashFlowGrade(company, basePeriod=basePeriod)))
    if need("creditPeerPosition"):
        out["creditPeerPosition"] = safe(
            lambda: creditPeerPositionBlock(calcCreditPeerPosition(company, basePeriod=basePeriod))
        )
    if need("creditFlags"):
        out["creditFlags"] = safe(lambda: creditFlagsBlock(calcCreditFlags(company, basePeriod=basePeriod)))
    if need("creditNarrative"):
        out["creditNarrative"] = safe(lambda: creditNarrativeBlock(calcCreditNarrative(company, basePeriod=basePeriod)))
    if need("creditAudit"):
        out["creditAudit"] = safe(lambda: creditAuditBlock(calcCreditAudit(company, basePeriod=basePeriod)))
    if need("creditScenario"):
        from dartlab.story.builders import creditScenarioBlock

        _base_credit = out.get("creditScore")
        _stress_overrides = {"debtRatio": 80.0, "interestCoverage": 2.0}
        _stress_credit = safe(lambda: calcCreditScore(company, basePeriod=basePeriod, overrides=_stress_overrides))
        if _base_credit and _stress_credit:
            _base_data = calcCreditScore(company, basePeriod=basePeriod)
            _stress_data = calcCreditScore(company, basePeriod=basePeriod, overrides=_stress_overrides)
            out["creditScenario"] = safe(lambda: creditScenarioBlock(_base_data, _stress_data, _stress_overrides))


def _buildValuationBlocks(company, keys, basePeriod, safe: Callable, need: Callable, out: dict) -> None:
    """4 부 - 가치평가 (Damodaran 흡수 포함 storyPrecedents/plausibilityBand)."""
    _CORE_KEYS = {
        "dcfValuation",
        "ddmValuation",
        "relativeValuation",
        "residualIncome",
        "priceTarget",
        "reverseImplied",
        "sensitivity",
        "valuationSynthesis",
        "valuationFlags",
        "lifeCycleStage",
        "valuationSins",
        "dFV",
        "methodFitness",
        "qualityFactors",
    }
    _DAMODARAN_KEYS = {"storyPrecedents", "plausibilityBand"}
    if keys is not None and not (keys & (_CORE_KEYS | _DAMODARAN_KEYS)):
        return

    if keys is None or keys & _CORE_KEYS:
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
        from dartlab.story.builders import (
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

        if need("dcfValuation"):
            out["dcfValuation"] = safe(lambda: dcfValuationBlock(calcDcf(company, basePeriod=basePeriod)))
        if need("ddmValuation"):
            out["ddmValuation"] = safe(lambda: ddmValuationBlock(calcDdm(company, basePeriod=basePeriod)))
        if need("relativeValuation"):
            out["relativeValuation"] = safe(lambda: relativeValuationBlock(calcRelVal(company, basePeriod=basePeriod)))
        if need("residualIncome"):
            out["residualIncome"] = safe(lambda: residualIncomeBlock(calcRim(company, basePeriod=basePeriod)))
        # priceTarget 결과를 valuationSynthesis 에 전달 - 두 모델 차이 narration 자동 추가
        _ptCache: dict = {}

        def _getPt():
            if "v" not in _ptCache:
                _ptCache["v"] = calcPriceTarget(company, basePeriod=basePeriod)
            return _ptCache["v"]

        if need("priceTarget"):
            out["priceTarget"] = safe(lambda: priceTargetBlock(_getPt()))
        if need("reverseImplied"):
            out["reverseImplied"] = safe(
                lambda: reverseImpliedBlock(calcReverseImplied(company, basePeriod=basePeriod))
            )
        if need("sensitivity"):
            out["sensitivity"] = safe(lambda: sensitivityBlock(calcSensitivity(company, basePeriod=basePeriod)))
        if need("valuationSynthesis"):
            out["valuationSynthesis"] = safe(
                lambda: valuationSynthesisBlock(
                    calcValuationSynthesis(company, basePeriod=basePeriod),
                    priceTargetData=_getPt(),
                )
            )
        if need("valuationFlags"):
            out["valuationFlags"] = safe(
                lambda: valuationFlagsBlock(calcValuationFlags(company, basePeriod=basePeriod))
            )
        # dFV (dartlab Fair Value) - 4엔진 통합 적정주가
        if need("dFV") or need("methodFitness") or need("qualityFactors"):
            from dartlab.analysis.valuation.dFV import calcDFV
            from dartlab.story.builders import dFVBlock, methodFitnessBlock, qualityFactorsBlock

            _dfv_data = safe(lambda: calcDFV(company, basePeriod=basePeriod))
            if need("dFV"):
                out["dFV"] = dFVBlock(_dfv_data) if _dfv_data else []
            if need("methodFitness"):
                out["methodFitness"] = methodFitnessBlock(_dfv_data) if _dfv_data else []
            if need("qualityFactors"):
                out["qualityFactors"] = qualityFactorsBlock(_dfv_data) if _dfv_data else []
        # Damodaran 흡수 - lifeCycle / valuationSins
        if need("lifeCycleStage"):
            from dartlab.analysis.financial.lifeCycle import calcLifeCycle
            from dartlab.story.builders import lifeCycleStageBlock

            out["lifeCycleStage"] = safe(
                lambda: lifeCycleStageBlock(calcLifeCycle(company, basePeriod=basePeriod) or {})
            )
        if need("valuationSins"):
            from dartlab.analysis.financial.storyValidation import calcValuationSins
            from dartlab.story.builders import valuationSinsBlock

            out["valuationSins"] = safe(lambda: valuationSinsBlock(calcValuationSins(company, basePeriod=basePeriod)))

    # Damodaran 흡수 - storyPrecedents / plausibilityBand (별도 calc 모듈)
    if need("storyPrecedents"):
        from dartlab.analysis.financial.storyValidation import calcStoryPrecedents
        from dartlab.story.builders import storyPrecedentsBlock

        out["storyPrecedents"] = safe(lambda: storyPrecedentsBlock(calcStoryPrecedents(company, basePeriod=basePeriod)))
    if need("plausibilityBand"):
        from dartlab.analysis.financial.storyValidation import calcPlausibilityBand
        from dartlab.story.builders import plausibilityBandBlock

        out["plausibilityBand"] = safe(
            lambda: plausibilityBandBlock(calcPlausibilityBand(company, basePeriod=basePeriod))
        )


def _buildGovernanceBlocks(company, keys, basePeriod, safe: Callable, need: Callable, out: dict) -> None:
    """5 부 - 비재무 심화 거버넌스 (6 블록)."""
    if keys is not None and not (
        keys
        & {
            "ownershipTrend",
            "boardComposition",
            "auditOpinionTrend",
            "governanceFlags",
            "executivePayDivergence",
            "independentDirectorQuality",
        }
    ):
        return
    from dartlab.analysis.financial.governance import (
        calcAuditOpinionTrend,
        calcBoardComposition,
        calcExecutivePayDivergence,
        calcGovernanceFlags,
        calcIndependentDirectorQuality,
        calcOwnershipTrend,
    )
    from dartlab.story.builders import (
        auditOpinionTrendBlock,
        boardCompositionBlock,
        executivePayDivergenceBlock,
        governanceFlagsBlock,
        independentDirectorQualityBlock,
        ownershipTrendBlock,
    )

    if need("ownershipTrend"):
        out["ownershipTrend"] = safe(lambda: ownershipTrendBlock(calcOwnershipTrend(company, basePeriod=basePeriod)))
    if need("boardComposition"):
        out["boardComposition"] = safe(
            lambda: boardCompositionBlock(calcBoardComposition(company, basePeriod=basePeriod))
        )
    if need("auditOpinionTrend"):
        out["auditOpinionTrend"] = safe(
            lambda: auditOpinionTrendBlock(calcAuditOpinionTrend(company, basePeriod=basePeriod))
        )
    if need("executivePayDivergence"):
        out["executivePayDivergence"] = safe(
            lambda: executivePayDivergenceBlock(calcExecutivePayDivergence(company, basePeriod=basePeriod))
        )
    if need("independentDirectorQuality"):
        out["independentDirectorQuality"] = safe(
            lambda: independentDirectorQualityBlock(calcIndependentDirectorQuality(company, basePeriod=basePeriod))
        )
    if need("governanceFlags"):
        out["governanceFlags"] = safe(lambda: governanceFlagsBlock(calcGovernanceFlags(company, basePeriod=basePeriod)))


def _buildDisclosureDeltaBlocks(company, keys, basePeriod, safe: Callable, need: Callable, out: dict) -> None:
    """5 부 - 공시변화 (4 블록)."""
    if keys is not None and not (
        keys & {"disclosureChangeSummary", "keyTopicChanges", "changeIntensity", "disclosureDeltaFlags"}
    ):
        return
    from dartlab.analysis.financial.disclosureDelta import (
        calcChangeIntensity,
        calcDisclosureChangeSummary,
        calcDisclosureDeltaFlags,
        calcKeyTopicChanges,
    )
    from dartlab.story.builders import (
        changeIntensityBlock,
        disclosureChangeSummaryBlock,
        disclosureDeltaFlagsBlock,
        keyTopicChangesBlock,
    )

    if need("disclosureChangeSummary"):
        out["disclosureChangeSummary"] = safe(
            lambda: disclosureChangeSummaryBlock(calcDisclosureChangeSummary(company, basePeriod=basePeriod))
        )
    if need("keyTopicChanges"):
        out["keyTopicChanges"] = safe(lambda: keyTopicChangesBlock(calcKeyTopicChanges(company, basePeriod=basePeriod)))
    if need("changeIntensity"):
        out["changeIntensity"] = safe(lambda: changeIntensityBlock(calcChangeIntensity(company, basePeriod=basePeriod)))
    if need("disclosureDeltaFlags"):
        out["disclosureDeltaFlags"] = safe(
            lambda: disclosureDeltaFlagsBlock(calcDisclosureDeltaFlags(company, basePeriod=basePeriod))
        )


def _buildPeerBenchmarkBlocks(company, keys, basePeriod, safe: Callable, need: Callable, out: dict) -> None:
    """5 부 - 비교분석 peer benchmark (3 블록)."""
    if keys is not None and not (keys & {"peerRanking", "riskReturnPosition", "peerBenchmarkFlags"}):
        return
    from dartlab.analysis.financial.peerBenchmark import (
        calcPeerBenchmarkFlags,
        calcPeerRanking,
        calcRiskReturnPosition,
    )
    from dartlab.story.builders import (
        peerBenchmarkFlagsBlock,
        peerRankingBlock,
        riskReturnPositionBlock,
    )

    if need("peerRanking"):
        out["peerRanking"] = safe(lambda: peerRankingBlock(calcPeerRanking(company, basePeriod=basePeriod)))
    if need("riskReturnPosition"):
        out["riskReturnPosition"] = safe(
            lambda: riskReturnPositionBlock(calcRiskReturnPosition(company, basePeriod=basePeriod))
        )
    if need("peerBenchmarkFlags"):
        out["peerBenchmarkFlags"] = safe(
            lambda: peerBenchmarkFlagsBlock(calcPeerBenchmarkFlags(company, basePeriod=basePeriod))
        )


def _buildForecastBlocks(company, keys, basePeriod, safe: Callable, need: Callable, out: dict) -> None:
    """6 부 - 전망분석 (8 블록)."""
    if keys is not None and not (
        keys
        & {
            "revenueForecast",
            "segmentForecast",
            "proFormaHighlights",
            "scenarioImpact",
            "forecastMethodology",
            "historicalRatios",
            "forecastFlags",
            "calibrationReport",
        }
    ):
        return
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
    from dartlab.story.builders import (
        calibrationReportBlock,
        forecastFlagsBlock,
        forecastMethodologyBlock,
        historicalRatiosBlock,
        proFormaHighlightsBlock,
        revenueForecastBlock,
        scenarioImpactBlock,
        segmentForecastBlock,
    )

    if need("revenueForecast"):
        out["revenueForecast"] = safe(lambda: revenueForecastBlock(calcRevenueForecast(company, basePeriod=basePeriod)))
    if need("segmentForecast"):
        out["segmentForecast"] = safe(lambda: segmentForecastBlock(calcSegmentForecast(company, basePeriod=basePeriod)))
    if need("proFormaHighlights"):
        out["proFormaHighlights"] = safe(
            lambda: proFormaHighlightsBlock(calcProFormaHighlights(company, basePeriod=basePeriod))
        )
    if need("scenarioImpact"):
        out["scenarioImpact"] = safe(lambda: scenarioImpactBlock(calcScenarioImpact(company, basePeriod=basePeriod)))
    if need("forecastMethodology"):
        out["forecastMethodology"] = safe(
            lambda: forecastMethodologyBlock(calcForecastMethodology(company, basePeriod=basePeriod))
        )
    if need("historicalRatios"):
        out["historicalRatios"] = safe(
            lambda: historicalRatiosBlock(calcHistoricalRatios(company, basePeriod=basePeriod))
        )
    if need("forecastFlags"):
        out["forecastFlags"] = safe(lambda: forecastFlagsBlock(calcForecastFlags(company, basePeriod=basePeriod)))
    if need("calibrationReport"):
        out["calibrationReport"] = safe(
            lambda: calibrationReportBlock(calcCalibrationReport(company, basePeriod=basePeriod))
        )


def _buildPeerPositionBlocks(company, keys, basePeriod, safe: Callable, need: Callable, out: dict) -> None:
    """비교분석 - scan 교차 조합 (peerPosition/governanceSummary)."""
    if keys is not None and not (keys & {"peerPosition", "governanceSummary"}):
        return
    import importlib

    _ext = importlib.import_module("dartlab.scan.builders.kr.extended")
    calcGovernanceSummary = _ext.calcGovernanceSummary
    calcPeerPosition = _ext.calcPeerPosition
    from dartlab.story.builders import peerPositionBlock
    from dartlab.story.builders import quantModuleBlock as _scanBlock

    if need("peerPosition"):
        out["peerPosition"] = safe(lambda: peerPositionBlock(calcPeerPosition(company)))
    if need("governanceSummary"):
        out["governanceSummary"] = safe(lambda: _scanBlock("governanceSummary", calcGovernanceSummary(company)))


def _buildQuantTechnicalBlocks(company, keys, basePeriod, safe: Callable, need: Callable, out: dict) -> None:
    """시장분석 - quant 기술적 + 알파 12 (story 통합)."""
    _CORE_KEYS = {
        "technicalVerdict",
        "technicalSignals",
        "strategySnapshot",
        "marketBeta",
        "fundamentalDivergence",
        "marketAnalysisFlags",
    }
    _NARRATIVE_KEYS = {
        "trendNarrative",
        "riskNarrative",
        "signalNarrative",
        "strategyNarrative",
        "crosscheckNarrative",
        "quantConclusion",
    }
    _ALPHA_KEYS = {
        "altmanFactor",
        "piotroskiFactor",
        "beneishFactor",
        "accrualsFactor",
        "qFactor",
        "qmj",
        "bab",
        "earningsSurprise",
        "fundMomentum",
        "factorTearSheet",
        "factorIC",
        "riskDecomposition",
    }
    if keys is not None and not (keys & (_CORE_KEYS | _NARRATIVE_KEYS | _ALPHA_KEYS)):
        return

    from dartlab.quant.screen.extended import (
        calcCrosscheckData,
        calcFundamentalDivergence,
        calcMarketAnalysisFlags,
        calcMarketBeta,
        calcQuantConclusionData,
        calcRiskData,
        calcSignalData,
        calcStrategyData,
        calcStrategySnapshot,
        calcTechnicalSignals,
        calcTechnicalVerdict,
        calcTrendData,
    )
    from dartlab.story.builders import (
        fundamentalDivergenceBlock,
        marketAnalysisFlagsBlock,
        marketBetaBlock,
        quantModuleBlock,
        strategySnapshotBlock,
        technicalSignalsBlock,
        technicalVerdictBlock,
    )
    from dartlab.story.narrate import (
        narrateCrosscheck,
        narrateQuantConclusion,
        narrateQuantRisk,
        narrateSignals,
        narrateStrategyVerdict,
        narrateTrend,
    )

    if need("technicalVerdict"):
        out["technicalVerdict"] = safe(lambda: technicalVerdictBlock(calcTechnicalVerdict(company)))
    if need("technicalSignals"):
        out["technicalSignals"] = safe(lambda: technicalSignalsBlock(calcTechnicalSignals(company)))
    # quant 서사 모듈 5+1 - review 가 서사를 생성 (엔진=숫자만, story=이야기꾼)
    _narrate_map = {
        "trendNarrative": (calcTrendData, lambda d: narrateTrend(d.get("verdict", {})) if d else ""),
        "riskNarrative": (calcRiskData, lambda d: narrateQuantRisk(d.get("data"), d.get("verdict")) if d else ""),
        "signalNarrative": (calcSignalData, lambda d: narrateSignals(d.get("data")) if d else ""),
        "strategyNarrative": (calcStrategyData, lambda d: narrateStrategyVerdict(d.get("data")) if d else ""),
        "crosscheckNarrative": (calcCrosscheckData, lambda d: narrateCrosscheck(d.get("data")) if d else ""),
        "quantConclusion": (
            calcQuantConclusionData,
            lambda d: narrateQuantConclusion(
                d.get("trend_label", ""),
                d.get("bullish", 0),
                d.get("bearish", 0),
                d.get("active_styles", []),
                d.get("diagnosis", ""),
            )
            if d
            else "",
        ),
    }
    for qkey, (qcalc, qnarrate) in _narrate_map.items():
        if need(qkey):

            def _build(c=qcalc, n=qnarrate, k=qkey):
                data = c(company)
                narrative = n(data) if data else ""
                return quantModuleBlock(k, {"narrative": narrative, "data": data})

            out[qkey] = safe(_build)
    if need("strategySnapshot"):
        out["strategySnapshot"] = safe(lambda: strategySnapshotBlock(calcStrategySnapshot(company)))
    if need("marketBeta"):
        out["marketBeta"] = safe(lambda: marketBetaBlock(calcMarketBeta(company)))
    if need("fundamentalDivergence"):
        out["fundamentalDivergence"] = safe(
            lambda: fundamentalDivergenceBlock(calcFundamentalDivergence(company, basePeriod=basePeriod))
        )
    if need("marketAnalysisFlags"):
        out["marketAnalysisFlags"] = safe(lambda: marketAnalysisFlagsBlock(calcMarketAnalysisFlags(company)))

    # Sprint 2~7 신규 12 alpha - 동일 narrative map 패턴.
    _alpha_market = "US" if getattr(company, "currency", "KRW") == "USD" else "KR"
    _stockCode = getattr(company, "stockCode", None)

    from dartlab.quant.alphas.accruals import calcAccrualsFactor
    from dartlab.quant.alphas.altman import calcAltmanFactor
    from dartlab.quant.alphas.bab import calcBAB
    from dartlab.quant.alphas.beneish import calcBeneishFactor
    from dartlab.quant.alphas.earningsSurprise import calcEarningsSurprise
    from dartlab.quant.alphas.fundamentalMomentum import calcFundamentalMomentum
    from dartlab.quant.alphas.piotroski import calcPiotroskiFactor
    from dartlab.quant.alphas.qFactor import calcQFactor
    from dartlab.quant.alphas.qmj import calcQMJ
    from dartlab.quant.factor._factorIC import calcFactorICAll
    from dartlab.quant.factor.calc import calcFactorTearSheetAll, calcMultiFactorRisk
    from dartlab.story.narrate import (
        narrateAccruals,
        narrateAltman,
        narrateBAB,
        narrateBeneish,
        narrateEarningsSurprise,
        narrateFactorIC,
        narrateFactorTearSheet,
        narrateFundMomentum,
        narratePiotroski,
        narrateQFactor,
        narrateQMJ,
        narrateRiskDecomposition,
    )

    _alpha_map: dict[str, tuple] = {
        "altmanFactor": (lambda: calcAltmanFactor(market=_alpha_market), narrateAltman),
        "piotroskiFactor": (lambda: calcPiotroskiFactor(market=_alpha_market), narratePiotroski),
        "beneishFactor": (lambda: calcBeneishFactor(market=_alpha_market), narrateBeneish),
        "accrualsFactor": (lambda: calcAccrualsFactor(market=_alpha_market), narrateAccruals),
        "qFactor": (lambda: calcQFactor(market=_alpha_market), narrateQFactor),
        "qmj": (lambda: calcQMJ(market=_alpha_market), narrateQMJ),
        "bab": (lambda: calcBAB(market=_alpha_market), narrateBAB),
        "earningsSurprise": (lambda: calcEarningsSurprise(market=_alpha_market), narrateEarningsSurprise),
        "fundMomentum": (lambda: calcFundamentalMomentum(market=_alpha_market), narrateFundMomentum),
        "factorTearSheet": (lambda: calcFactorTearSheetAll(market=_alpha_market), narrateFactorTearSheet),
        "factorIC": (lambda: calcFactorICAll(market=_alpha_market, horizon=5), narrateFactorIC),
    }
    if _stockCode:
        _alpha_map["riskDecomposition"] = (lambda: calcMultiFactorRisk(_stockCode), narrateRiskDecomposition)

    for akey, (acalc, anarrate) in _alpha_map.items():
        if need(akey):

            def _build(c=acalc, n=anarrate, k=akey):
                data = c()
                narrative = n(data) if data else ""
                return quantModuleBlock(k, {"narrative": narrative, "data": data})

            out[akey] = safe(_build)


def _buildMacroBlocks(company, keys, basePeriod, safe: Callable, need: Callable, out: dict) -> None:
    """매크로 - 시장 환경 + 기업-매크로 연결 (12 블록)."""
    _MACRO_KEYS = {
        "macroEnvironment",
        "macroCycle",
        "macroRates",
        "macroLiquidity",
        "macroSentiment",
        "macroForecast",
        "macroCorporate",
        "macroTrade",
        "macroFlags",
        "valuationBand",
        "companyCyclePosition",
        "macroSensitivity",
    }
    if keys is not None and not (keys & _MACRO_KEYS):
        return
    from dartlab.analysis.financial.macroExposure import calcValuationBand
    from dartlab.story.builders import (
        macroCorporateBlock,
        macroCycleBlock,
        macroEnvironmentBlock,
        macroFlagsBlock,
        macroForecastBlock,
        macroLiquidityBlock,
        macroRatesBlock,
        macroSensitivityBlock,
        macroSentimentBlock,
        macroTradeBlock,
        valuationBandBlock,
    )

    # macro("종합") 1회 호출 + 캐시 - 11축 전부 포함
    _macro_summary: list = [None]
    _macro_market = getattr(company, "market", "KR")

    def _ensureSummary():
        if _macro_summary[0] is None:
            # F6: dartlab root facade 우회 → macro.summary 직접 (정공법 D)
            try:
                from dartlab.macro.summary import analyzeSummary

                _macro_summary[0] = analyzeSummary(market=_macro_market)
            except (ValueError, TypeError, KeyError, OSError, ImportError) as e:
                _LOG.debug("macro 종합 실패 (market=%s): %s", _macro_market, e)
                _macro_summary[0] = {}
        return _macro_summary[0]

    if need("macroEnvironment"):
        out["macroEnvironment"] = safe(lambda: macroEnvironmentBlock(_ensureSummary()))
    if need("macroCycle"):
        out["macroCycle"] = safe(lambda: macroCycleBlock(_ensureSummary().get("cycle", {})))
    if need("macroRates"):
        out["macroRates"] = safe(lambda: macroRatesBlock(_ensureSummary().get("rates", {})))
    if need("macroLiquidity"):
        out["macroLiquidity"] = safe(lambda: macroLiquidityBlock(_ensureSummary().get("liquidity", {})))
    if need("macroSentiment"):
        out["macroSentiment"] = safe(lambda: macroSentimentBlock(_ensureSummary().get("sentiment", {})))
    if need("macroForecast"):
        out["macroForecast"] = safe(lambda: macroForecastBlock(_ensureSummary().get("forecast")))
    if need("macroCorporate"):
        out["macroCorporate"] = safe(lambda: macroCorporateBlock(_ensureSummary().get("corporate")))
    if need("macroTrade"):
        _market = getattr(company, "market", "KR")
        if _market == "KR":
            out["macroTrade"] = safe(lambda: macroTradeBlock(_ensureSummary().get("trade")))
    if need("macroFlags"):
        out["macroFlags"] = safe(lambda: macroFlagsBlock(_ensureSummary()))
    if need("macroSensitivity"):
        from dartlab.analysis.financial.macroExposure import calcMacroSensitivity

        out["macroSensitivity"] = safe(
            lambda: macroSensitivityBlock(calcMacroSensitivity(company, basePeriod=basePeriod))
        )
    if need("valuationBand"):
        out["valuationBand"] = safe(lambda: valuationBandBlock(calcValuationBand(company, basePeriod=basePeriod)))
    if need("companyCyclePosition"):
        from dartlab.story.builders import companyCyclePositionBlock

        out["companyCyclePosition"] = safe(lambda: companyCyclePositionBlock(_ensureSummary().get("crisis", {})))


def _buildScenarioBlocks(company, keys, basePeriod, safe: Callable, need: Callable, out: dict) -> None:
    """개선 시나리오 (How축) + Damodaran 3-test."""
    if keys is not None and not (
        keys & {"gradeUpgradePath", "technicalActionTargets", "cyclicalActionPlan", "damodaran3test"}
    ):
        return

    if keys is None or keys & {"gradeUpgradePath", "technicalActionTargets", "cyclicalActionPlan"}:
        from dartlab.story.builders import (
            cyclicalActionPlanBlock,
            gradeUpgradePathBlock,
            technicalActionTargetsBlock,
        )

        if need("gradeUpgradePath"):
            from dartlab.credit.scoring.calcs import calcGradeImprovement

            out["gradeUpgradePath"] = safe(
                lambda: gradeUpgradePathBlock(calcGradeImprovement(company, basePeriod=basePeriod))
            )
        if need("technicalActionTargets"):
            from dartlab.quant.screen.extended import calcActionableTargets

            out["technicalActionTargets"] = safe(lambda: technicalActionTargetsBlock(calcActionableTargets(company)))
        if need("cyclicalActionPlan"):
            from dartlab.macro.crisis.crisis import calcCyclicalAction

            _market = getattr(company, "market", "KR")
            out["cyclicalActionPlan"] = safe(lambda: cyclicalActionPlanBlock(calcCyclicalAction(market=_market)))

    if need("damodaran3test"):
        from dartlab.story.builders import damodaran3testBlock

        out["damodaran3test"] = safe(lambda: damodaran3testBlock(company))


def buildBlocks(
    company,
    keys: set[str] | None = None,
    *,
    basePeriod: str | None = None,
    preset: str = "standard",
):
    """블록 사전 - analysis calc* 결과를 블록으로 변환.

    keys 가 지정되면 해당 블록만 빌드한다 (선택적 빌드, preset 무시).
    keys=None 이면 preset 에 따라 빌드 범위 결정 - 자세한 정책은
    ``_resolvePresetKeys`` 참조.

    내부적으로 ``_GROUP_BUILDERS`` (그룹별 빌더 list) 를 순회. 새 블록 추가 시
    해당 그룹 빌더 함수만 수정 + (필요 시) 새 그룹 빌더 등록.
    """
    keys = _resolvePresetKeys(keys, preset)
    _setupCurrency(company)
    # buildBlocks 본체에서 사용하는 헬퍼 - 그룹 빌더 추출 시 인자로 전달.
    # 이전 inline 정의 (_safe/_need) 와 같은 이름 유지해 본체 호출 그대로.
    buildFailures: list[dict] = []
    _safe = _makeSafeCall(buildFailures)
    _need = _makeNeed(keys)
    b: dict = {}

    # ── 1부: 사업구조 + 자본구조 + 자산구조 + 현금흐름 ──
    _buildRevenueBlocks(company, keys, basePeriod, _safe, _need, b)
    _buildCapitalBlocks(company, keys, basePeriod, _safe, _need, b)
    _buildAssetBlocks(company, keys, basePeriod, _safe, _need, b)
    _buildCashflowBlocks(company, keys, basePeriod, _safe, _need, b)

    # ── 2부: 재무비율 분석 (수익성 + 성장 + 안정성 + 효율성 + 종합) ──
    _buildProfitabilityBlocks(company, keys, basePeriod, _safe, _need, b)
    _buildGrowthBlocks(company, keys, basePeriod, _safe, _need, b)
    _buildStabilityBlocks(company, keys, basePeriod, _safe, _need, b)
    _buildEfficiencyBlocks(company, keys, basePeriod, _safe, _need, b)
    _buildScorecardBlocks(company, keys, basePeriod, _safe, _need, b)

    # ── 3부: 산업 + 심화 분석 ──
    _buildIndustryBlocks(company, keys, basePeriod, _safe, _need, b)
    _buildEarningsQualityBlocks(company, keys, basePeriod, _safe, _need, b)
    _buildCostStructureBlocks(company, keys, basePeriod, _safe, _need, b)
    _buildCapitalAllocationBlocks(company, keys, basePeriod, _safe, _need, b)
    _buildInvestmentBlocks(company, keys, basePeriod, _safe, _need, b)
    _buildCrossStatementBlocks(company, keys, basePeriod, _safe, _need, b)

    # ── 3-6 신용평가 + 4부 가치평가 (Damodaran 흡수 storyPrecedents/plausibilityBand 포함) ──
    _buildCreditBlocks(company, keys, basePeriod, _safe, _need, b)
    _buildValuationBlocks(company, keys, basePeriod, _safe, _need, b)

    # ── 5부: 비재무 심화 (governance + disclosureDelta + peerBenchmark) ──
    _buildGovernanceBlocks(company, keys, basePeriod, _safe, _need, b)
    _buildDisclosureDeltaBlocks(company, keys, basePeriod, _safe, _need, b)
    _buildPeerBenchmarkBlocks(company, keys, basePeriod, _safe, _need, b)

    # ── 6부: 전망분석 + 비교분석 + 시장분석 + 매크로 + 시나리오 ──
    _buildForecastBlocks(company, keys, basePeriod, _safe, _need, b)
    _buildPeerPositionBlocks(company, keys, basePeriod, _safe, _need, b)
    _buildQuantTechnicalBlocks(company, keys, basePeriod, _safe, _need, b)
    _buildMacroBlocks(company, keys, basePeriod, _safe, _need, b)
    _buildScenarioBlocks(company, keys, basePeriod, _safe, _need, b)

    # ── 종료 - BlockMap 변환 + 메모리 해제 힌트 ──
    import gc

    from dartlab.story.blockMap import BlockMap

    gc.collect()
    return BlockMap(b, buildFailures=buildFailures)


def buildStory(
    company,
    section: str | None = None,
    layout: StoryLayout | None = None,
    helper: bool | None = None,
    *,
    type: str | None = None,
    template: str | None = None,
    detail: bool | None = None,
    basePeriod: str | None = None,
    hypothesis: str | None = None,  # thesis 타입 전용
    # ── deprecated (한 릴리즈 경고 후 제거) ──
    preset: str | None = None,
    perspective: str | None = None,
):
    """Company에서 Review를 생성.

    Parameters
    ----------
    type : str, optional
        보고서 타입. full/executive/credit/valuation/growth/crisis/audit/
        dividend/governance/macro/thesis. 기본 full.
    template : str, optional
        기업유형 감지 (독립 축). "auto" 또는 사이클/프랜차이즈/턴어라운드/...
    preset, perspective : deprecated
        type= 로 이전. 임시로 매핑 지원.
    """
    import warnings

    from dartlab.story import Story
    from dartlab.story.reportTypes import resolveReportType

    ly = layout or StoryLayout()

    # ── deprecated 파라미터 매핑 ──
    if perspective is not None and type is None:
        warnings.warn(
            "story(perspective=...) 는 deprecated. story(type=...) 를 사용하세요.",
            DeprecationWarning,
            stacklevel=3,
        )
        type = perspective
    if preset is not None and type is None:
        warnings.warn(
            "story(preset=...) 는 deprecated. story(type=...) 를 사용하세요.",
            DeprecationWarning,
            stacklevel=3,
        )
        type = preset

    # ── ReportType 해석 ──
    reportType = resolveReportType(type)

    blockBuildFailures: list[dict] = []

    def _attachLensProducts(story):
        from dartlab.story.lensProducts import collectLensProducts, enginesForReportType

        bundle = collectLensProducts(
            company,
            engines=enginesForReportType(reportType.key),
            basePeriod=basePeriod,
        )
        story.reportType = reportType.key
        story.lensProducts = bundle["products"]
        # 블록 빌더가 터진 것도 결손이다. 렌즈 결손과 같은 자리에 실어야 보고서가
        # 완전한 얼굴로 나가지 않는다.
        story.lensGaps = list(bundle["gaps"]) + blockBuildFailures
        story._lensBundle = bundle
        return story

    # ── thesis 타입: 서사 주도 특수 경로 (블록화 예외) ──
    if reportType.key == "thesis":
        corpName = getattr(company, "corpName", "")
        stockCode = getattr(company, "stockCode", "")
        story = Story(stockCode=stockCode, corpName=corpName, layout=ly)
        if basePeriod is not None:
            from dartlab.story.blocks import FlagBlock, HeadingBlock, TextBlock

            thesis_blocks: list[Block] = [HeadingBlock("논제 검증", level=2)]
            if hypothesis:
                thesis_blocks.append(TextBlock(f"가설: {hypothesis}"))
            thesis_blocks.append(
                FlagBlock(
                    flags=["과거 시점에 고정된 AI 논제 검증 경로가 없어 서사 판정을 차단했습니다."],
                    kind="warning",
                )
            )
            blockBuildFailures.append(
                {
                    "code": "HISTORICAL_THESIS_UNSUPPORTED",
                    "status": "unsupported",
                    "reason": f"{basePeriod} 시점에 고정된 AI 근거 계약이 없습니다.",
                }
            )
        else:
            from dartlab.story.builders import thesisReportBlocks

            thesis_blocks = thesisReportBlocks(company, hypothesis)
        story.sections = [Section(key="thesisReport", partId="T", title="논제 검증", blocks=thesis_blocks)]
        return _attachLensProducts(story)

    # ── lifeCycle 기반 강조 블록 자동 설정 ──
    # lifeCycle phase 에 따라 어떤 분석 관점이 중요한지 자동 결정
    _LIFECYCLE_EMPHASIZE: dict[str, set[str]] = {
        "earlyGrowth": {"revenueGrowth", "segmentComposition", "cashFlowOverview", "lifeCycleStage"},
        "highGrowth": {"revenueGrowth", "marginTrend", "capitalAllocation", "lifeCycleStage"},
        "matureGrowth": {"returnTrend", "capitalAllocation", "cashQuality", "lifeCycleStage"},
        "matureStable": {"dividendPolicy", "cashFlowOverview", "capitalAllocation", "lifeCycleStage"},
        "decline": {"leverageTrend", "distressSignals", "cashFlowOverview", "lifeCycleStage"},
        "turnaround": {"marginTrend", "cashFlowOverview", "leverageTrend", "lifeCycleStage"},
    }
    try:
        from dartlab.analysis.financial.lifeCycle import calcLifeCycle as _calcLC

        _lcResult = _calcLC(company, basePeriod=basePeriod)
        _lcPhase = _lcResult.get("phase") if _lcResult else None
    except (ImportError, AttributeError, TypeError, ValueError):
        _lcPhase = None

    # ── 스토리 템플릿 판별 (기업유형, ReportType과 독립) ──
    detectedTemplate: str | None = None
    detectedTemplates: list[str] = []
    emphasizedKeys: set[str] = set(reportType.emphasize)
    # lifeCycle 기반 강조 합산
    if _lcPhase and _lcPhase in _LIFECYCLE_EMPHASIZE:
        emphasizedKeys |= _LIFECYCLE_EMPHASIZE[_lcPhase]
    if template is not None:
        from dartlab.story.templates import STORY_TEMPLATES
        from dartlab.story.templates import detectTemplate as _detect

        if template == "auto":
            detectedTemplate = _detect(company)
            from dartlab.story.templates import detectTemplates as _detectMulti

            try:
                detectedTemplates = _detectMulti(company)
            except (AttributeError, ValueError, TypeError):
                detectedTemplates = []
        elif template in STORY_TEMPLATES:
            detectedTemplate = template
            detectedTemplates = [template]
        else:
            detectedTemplates = []

        if detectedTemplate and detectedTemplate in STORY_TEMPLATES:
            for tmplName in detectedTemplates:
                if tmplName in STORY_TEMPLATES:
                    emphasizedKeys |= STORY_TEMPLATES[tmplName].get("emphasize", set())

    # ── ReportType의 섹션 순서 적용 ──
    # (section 단일 지정이 아니고, layout.sectionOrder가 명시되지 않은 경우만)
    if section is None and ly.sectionOrder is None and type is not None:
        ly.sectionOrder = list(reportType.sectionOrder)
    if detail is None:
        ly.detail = reportType.detail

    # detail 명시 오버라이드
    if detail is not None:
        ly.detail = detail

    showHelper = helper if helper is not None else ly.helper

    corpName = getattr(company, "corpName", "")
    stockCode = getattr(company, "stockCode", "")

    story = Story(stockCode=stockCode, corpName=corpName, layout=ly)
    story.template = detectedTemplate
    story.templates = detectedTemplates if detectedTemplates else ([detectedTemplate] if detectedTemplate else [])

    useSpinner = isTerminal()
    if useSpinner:
        from rich.live import Live
        from rich.spinner import Spinner

        from dartlab.core.logger import getErrConsole

        console = getErrConsole()
        spinner = Spinner("dots", text="분석 준비 중...")
        ctx = Live(spinner, console=console, transient=True)
    else:
        from contextlib import nullcontext

        ctx = nullcontext()

    with ctx as live:
        if live is not None:
            from rich.spinner import Spinner

            live.update(Spinner("dots", text="블록 사전 생성 중..."))

        # 템플릿 순서 결정 (블록 빌드 전에 필요한 keys 산출).
        # section 이 빈 문자열 / None 이면 전체 보고서 (AI dispatch 가 default 로 ""
        # 보내는 경우 ValueError 대신 무인자 호출과 동등 처리).
        if section:
            if section not in TEMPLATES:
                available = ", ".join(sorted(TEMPLATES.keys()))
                raise ValueError(
                    f"'{section}' 섹션을 찾을 수 없습니다.\n"
                    f"  사용 가능한 섹션: {available}\n"
                    f"  사용법: c.story('수익구조') 또는 c.story() 로 전체 보고서"
                )
            templateKeys = [section]
        elif ly.sectionOrder is not None:
            templateKeys = [k for k in ly.sectionOrder if k in TEMPLATES]
        else:
            templateKeys = list(TEMPLATE_ORDER)

        # 필요한 블록 keys만 산출 → 선택적 빌드
        if templateKeys and set(templateKeys) != set(TEMPLATE_ORDER):
            neededKeys: set[str] | None = set()
            for tk in templateKeys:
                neededKeys.update(TEMPLATES[tk]["keys"])
        else:
            neededKeys = None  # 전체 빌드

        b = buildBlocks(company, keys=neededKeys, basePeriod=basePeriod)
        blockBuildFailures.extend(getattr(b, "buildFailures", []))

        for tmplKey in templateKeys:
            tmpl = TEMPLATES[tmplKey]
            if live is not None:
                from rich.spinner import Spinner

                live.update(Spinner("dots", text=f"{tmplKey} 조립 중..."))

            sectionBlocks: list[Block] = []
            for blockKey in tmpl["keys"]:
                blockList = b.get(blockKey)
                if blockList:
                    if blockKey in emphasizedKeys:
                        for blk in blockList:
                            if hasattr(blk, "emphasized"):
                                blk.emphasized = True
                    sectionBlocks.extend(blockList)

            if sectionBlocks:
                story.sections.append(
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

        from dartlab.story.narrative import buildCirculationSummary, detectThreads

        _sectionSet = set(templateKeys) if section is not None else None
        threads = detectThreads(company, b, sections=_sectionSet, basePeriod=basePeriod)
        if not getattr(b, "verifiedNarrativeInputs", None):
            blockBuildFailures.append(
                {
                    "code": "NARRATIVE_VALUE_PROVENANCE_UNAVAILABLE",
                    "status": "unsupported",
                    "reason": "값 단위 ref를 가진 하위 엔진 Narrative Product가 없어 인과 서사를 차단했습니다.",
                }
            )
        for thread in threads:
            for sec in story.sections:
                if sec.key in thread.involvedSections:
                    sec.threads.append(thread)
        story.circulationSummary = buildCirculationSummary(threads) if threads else ""

        # ── 6막 전환 인과 문장 ──
        from dartlab.story.narrative import buildActTransitions

        story.actTransitions = buildActTransitions(company, basePeriod=basePeriod)
        if basePeriod is not None:
            blockBuildFailures.append(
                {
                    "code": "HISTORICAL_ACT_TRANSITIONS_UNSUPPORTED",
                    "status": "unsupported",
                    "reason": "과거 시점 ratio 계약이 없어 최신 비율 기반 막 전환 문장을 차단했습니다.",
                }
            )

        # ── 요약 카드 생성 ──
        from dartlab.story.summary import buildSectionSummary, buildSummaryCard

        scorecardData = None
        try:
            from dartlab.analysis.financial.scorecard import calcScorecard

            scorecardData = calcScorecard(company, basePeriod=basePeriod)
        except (ImportError, KeyError, ValueError, TypeError, AttributeError):
            pass

        story.summaryCard = buildSummaryCard(threads, scorecardData, story.sections)

        # ── 섹션별 요약 생성 ──
        for sec in story.sections:
            sec.summary = buildSectionSummary(sec)

    # ── type=None(기본)일 때 보고서 상단에 타입 가이드 삽입 ──
    if type is None and section is None:
        from dartlab.story.blocks import TextBlock

        guide = (
            "보고서 타입 안내: "
            "c.story(type='executive') 경영 3분컷 / "
            "type='credit' 신용분석 / "
            "type='dividend' 배당 / "
            "type='governance' 지배구조 / "
            "type='macro' 매크로 / "
            "type='thesis' 가설 검증"
        )
        if story.sections:
            story.sections[0].blocks.insert(0, TextBlock(guide, style="dim"))

    return _attachLensProducts(story)


# [Phase 3 워밍업 함수는 제거됨 - 위 buildBlocks 주석 참조]
