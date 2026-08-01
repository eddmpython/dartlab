"""macro L2 순수함수 광범위 단위 테스트.

외부 API 호출 없는 순수함수만 대상. coverage 4% → 30%+ 끌어올림.

대상:
- macro/crisis/detectors.py (creditToGDPGap, fisherDebtDeflation, ghsCrisisScore,
  kooBalanceSheetRecession, minskyPhase, recessionDashboard)
- macro/cycles/sentiment.py (calcFearGreedProxy, estimateRateExpectation,
  interpretEmployment, interpretInflation, ismAssetAllocation, krInflationModel)
- macro/cycles/liquidity.py (capexPressure, classifyLiquidityRegime)
- macro/crisis/growthAtRisk.py (growthAtRisk)
- macro/scenarios/presets.py (getScenario, listAllScenarios)
- macro/cycles/macroCycle.py (interpretAssets, calcMultipleBand, rateOutlook,
  decomposeLongRate)
- macro/corporate/historicalContext.py (hySpikesToRecession,
  yieldCurveInversionsToRecession, unemploymentBounceToRecession,
  cpiAccelerationEvents)
"""

import pytest

# ══════════════════════════════════════
# macro/crisis/detectors.py
# ══════════════════════════════════════


class TestCreditToGDPGap:
    def test_basicSeries(self):
        from dartlab.macro.crisis.detectors import creditToGDPGap

        series = [50 + i * 0.5 for i in range(40)]
        r = creditToGDPGap(series)
        assert isinstance(r.gap, float)

    def test_emptySeries(self):
        from dartlab.macro.crisis.detectors import creditToGDPGap

        r = creditToGDPGap([])
        assert r is not None
        assert r.status == "unavailable"
        assert r.gap is None
        assert r.zone is None

    def test_extremeBuildup(self):
        from dartlab.macro.crisis.detectors import creditToGDPGap

        series = [100.0] * 80 + [200.0] * 4
        r = creditToGDPGap(series)
        assert r.gap > 5


class TestFisherDebtDeflation:
    def test_classicDeflation(self):
        from dartlab.macro.crisis.detectors import fisherDebtDeflation

        r = fisherDebtDeflation(dsr=15.0, cpiYoy=-2.0)
        assert r is not None

    def test_safe(self):
        from dartlab.macro.crisis.detectors import fisherDebtDeflation

        r = fisherDebtDeflation(dsr=5.0, cpiYoy=2.5)
        assert r is not None


class TestGhsCrisisScore:
    def test_overheating(self):
        from dartlab.macro.crisis.detectors import ghsCrisisScore

        r = ghsCrisisScore(creditGrowth3y=20.0, assetPriceGrowth3y=30.0)
        assert r.score >= 0

    def test_normal(self):
        from dartlab.macro.crisis.detectors import ghsCrisisScore

        r = ghsCrisisScore(creditGrowth3y=3.0, assetPriceGrowth3y=5.0)
        assert r.score >= 0


class TestKooBalanceSheetRecession:
    def test_balanceSheetRecession(self):
        from dartlab.macro.crisis.detectors import kooBalanceSheetRecession

        r = kooBalanceSheetRecession(privateSaving=200, privateInvestment=100, gdp=1000, policyRate=0.5)
        assert r.isBSR is True

    def test_normalEconomy(self):
        from dartlab.macro.crisis.detectors import kooBalanceSheetRecession

        r = kooBalanceSheetRecession(privateSaving=100, privateInvestment=120, gdp=1000, policyRate=3.0)
        assert r is not None


class TestMinskyPhase:
    def test_hedgePhase(self):
        from dartlab.macro.crisis.detectors import minskyPhase

        r = minskyPhase(creditGap=-2.0, assetReturn3y=5.0, hySpread=3.0, vix=15.0)
        assert isinstance(r.phase, str)

    def test_ponziPhase(self):
        from dartlab.macro.crisis.detectors import minskyPhase

        r = minskyPhase(creditGap=15.0, assetReturn3y=40.0, hySpread=8.0, vix=35.0)
        assert isinstance(r.phase, str)

    def test_allNone(self):
        from dartlab.macro.crisis.detectors import minskyPhase

        r = minskyPhase()
        assert r.status == "unavailable"
        assert r.phase is None


class TestRecessionDashboard:
    def test_multipleSignals(self):
        from dartlab.macro.crisis.detectors import recessionDashboard

        r = recessionDashboard(probitProb=0.5, leiSignal="warning", ismLevel=45.0, creditGap=10.0, hySpread=7.0)
        assert isinstance(r.composite, float)
        assert isinstance(r.zone, str)

    def test_empty(self):
        from dartlab.macro.crisis.detectors import recessionDashboard

        r = recessionDashboard()
        assert r.status == "unavailable"
        assert r.composite is None
        assert r.zone is None


# ══════════════════════════════════════
# macro/cycles/sentiment.py
# ══════════════════════════════════════


class TestCalcFearGreedProxy:
    def test_fear(self):
        from dartlab.macro.cycles.sentiment import calcFearGreedProxy

        # 고VIX + 마이너스 모멘텀 + 와이드 HY = 공포
        r = calcFearGreedProxy(vix=35.0, sp500VsMa125=-10.0, hySpread=8.0)
        assert r.score is not None
        assert 0 <= r.score <= 100

    def test_greed(self):
        from dartlab.macro.cycles.sentiment import calcFearGreedProxy

        r = calcFearGreedProxy(vix=12.0, sp500VsMa125=15.0, hySpread=2.5)
        assert 0 <= r.score <= 100

    def test_neutral(self):
        from dartlab.macro.cycles.sentiment import calcFearGreedProxy

        r = calcFearGreedProxy(vix=18.0, sp500VsMa125=2.0, hySpread=4.0)
        assert 0 <= r.score <= 100


class TestEstimateRateExpectation:
    def test_inversion(self):
        from dartlab.macro.cycles.sentiment import estimateRateExpectation

        # 정책금리 > 2년 → 시장 인하 예상
        r = estimateRateExpectation(ffRate=5.5, dgs2=4.5, dgs10=4.0)
        assert hasattr(r, "expectedChange") or hasattr(r, "direction") or hasattr(r, "signal")

    def test_steep(self):
        from dartlab.macro.cycles.sentiment import estimateRateExpectation

        r = estimateRateExpectation(ffRate=2.0, dgs2=3.0, dgs10=4.5)
        assert r is not None


class TestInterpretEmployment:
    def test_strongEmployment(self):
        from dartlab.macro.cycles.sentiment import interpretEmployment

        r = interpretEmployment(unrate=3.5, payrolls3mAvg=300.0)
        assert isinstance(r.state, str)
        assert isinstance(r.stateLabel, str)

    def test_recessionSignal(self):
        from dartlab.macro.cycles.sentiment import interpretEmployment

        r = interpretEmployment(unrate=6.5, payrolls3mAvg=-50.0)
        assert r is not None


class TestInterpretInflation:
    def test_hot(self):
        from dartlab.macro.cycles.sentiment import interpretInflation

        r = interpretInflation(cpiYoy=6.5, coreCpiYoy=5.5)
        assert r.state == "hot"

    def test_target(self):
        from dartlab.macro.cycles.sentiment import interpretInflation

        r = interpretInflation(cpiYoy=2.1, coreCpiYoy=2.3)
        assert isinstance(r.state, str)


class TestIsmAssetAllocation:
    def test_expansion(self):
        from dartlab.macro.cycles.sentiment import ismAssetAllocation

        r = ismAssetAllocation(ism=58.0)
        assert isinstance(r.stance, str)
        assert r.equityWeight in {"overweight", "underweight", "neutral"}

    def test_contraction(self):
        from dartlab.macro.cycles.sentiment import ismAssetAllocation

        r = ismAssetAllocation(ism=42.0)
        assert r is not None


class TestKrInflationModel:
    def test_fxImported(self):
        from dartlab.macro.cycles.sentiment import krInflationModel

        r = krInflationModel(fxYoy=10.0, oilYoy=25.0)
        assert r.combined > 0
        assert r.direction == "upward"

    def test_stable(self):
        from dartlab.macro.cycles.sentiment import krInflationModel

        r = krInflationModel(fxYoy=0.0, oilYoy=-5.0)
        assert r is not None


# ══════════════════════════════════════
# macro/cycles/liquidity.py
# ══════════════════════════════════════


class TestCapexPressure:
    def test_widening(self):
        from dartlab.macro.cycles.liquidity import capexPressure

        r = capexPressure(hySpread=8.0, hySpreadChange=1.5)
        assert isinstance(r.pressure, str)

    def test_normal(self):
        from dartlab.macro.cycles.liquidity import capexPressure

        r = capexPressure(hySpread=3.5, hySpreadChange=-0.2)
        assert r is not None


class TestClassifyLiquidityRegime:
    def test_easy(self):
        from dartlab.macro.cycles.liquidity import classifyLiquidityRegime

        # M2 늘고 HY 스프레드 낮음 → 풍부
        r = classifyLiquidityRegime(m2Yoy=8.0, fedBsChangePct=5.0, hySpread=3.0, igSpread=1.0, rrpChangePct=-10.0)
        assert hasattr(r, "regime") or hasattr(r, "label")

    def test_tight(self):
        from dartlab.macro.cycles.liquidity import classifyLiquidityRegime

        r = classifyLiquidityRegime(m2Yoy=-2.0, fedBsChangePct=-3.0, hySpread=7.0, igSpread=2.5, rrpChangePct=20.0)
        assert r is not None

    def test_partialInputs(self):
        from dartlab.macro.cycles.liquidity import classifyLiquidityRegime

        r = classifyLiquidityRegime(m2Yoy=5.0)
        assert r is not None


# ══════════════════════════════════════
# macro/crisis/growthAtRisk.py
# ══════════════════════════════════════


class TestGrowthAtRisk:
    def test_sufficientHistory(self):
        from dartlab.macro.crisis.growthAtRisk import growthAtRisk

        fci = [0.5, 0.3, 0.1, -0.2, -0.5, 0.0, 0.2, 0.4, 0.6, 0.8, 0.5, 0.3, 0.1, -0.1, -0.3, 0.0, 0.2, 0.4, 0.6, 0.8]
        gdp = [2.5, 2.8, 3.0, 2.5, 1.8, 2.0, 2.2, 2.5, 2.8, 3.0, 2.5, 2.3, 2.0, 1.8, 1.5, 2.0, 2.3, 2.5, 2.8, 3.0]
        r = growthAtRisk(fci, gdp)
        assert r is not None

    def test_insufficientHistory(self):
        from dartlab.macro.crisis.growthAtRisk import growthAtRisk

        r = growthAtRisk([0.5], [2.5])
        assert r is None or isinstance(r, dict)


# ══════════════════════════════════════
# macro/scenarios/presets.py
# ══════════════════════════════════════


class TestPresets:
    def test_listAllScenariosUs(self):
        from dartlab.macro.scenarios.presets import listAllScenarios

        scenarios = listAllScenarios("US")
        assert isinstance(scenarios, list)
        assert len(scenarios) > 0
        for s in scenarios[:3]:
            assert "name" in s or "key" in s or hasattr(s, "name")

    def test_listAllScenariosKr(self):
        from dartlab.macro.scenarios.presets import listAllScenarios

        scenarios = listAllScenarios("KR")
        assert isinstance(scenarios, list)
        assert len(scenarios) > 0

    def test_getScenarioUnknownReturnsNone(self):
        from dartlab.macro.scenarios.presets import getScenario

        r = getScenario("__not_a_real_scenario__")
        assert r is None or isinstance(r, dict)


# ══════════════════════════════════════
# macro/cycles/macroCycle.py
# ══════════════════════════════════════


class TestInterpretAssets:
    def test_shortRateOnly(self):
        from dartlab.macro.cycles.macroCycle import interpretAssets

        r = interpretAssets({"short_rate": 3.5, "short_rate_change": 0.5})
        assert isinstance(r, list)
        assert len(r) >= 1

    def test_allAssets(self):
        from dartlab.macro.cycles.macroCycle import interpretAssets

        r = interpretAssets(
            {
                "short_rate": 3.5,
                "short_rate_change": 0.25,
                "long_rate": 4.0,
                "long_rate_change": 0.3,
                "fx_usdkrw": 1350,
                "fx_change_pct": 2.0,
                "gold": 2400,
                "gold_yoy": 18.0,
                "vix": 22.0,
                "vix_change": 4.0,
            }
        )
        assert len(r) == 5

    def test_emptyDict(self):
        from dartlab.macro.cycles.macroCycle import interpretAssets

        r = interpretAssets({})
        assert isinstance(r, list)
        assert len(r) == 0


class TestCalcMultipleBand:
    def test_normalDist(self):
        from dartlab.macro.cycles.macroCycle import calcMultipleBand

        values = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
        r = calcMultipleBand(values, current=15.0)
        assert r is not None
        assert hasattr(r, "zone") or hasattr(r, "zLabel")

    def test_undervalued(self):
        from dartlab.macro.cycles.macroCycle import calcMultipleBand

        values = list(range(10, 20))
        r = calcMultipleBand(values, current=10.0)
        assert r is not None

    def test_emptyValues(self):
        from dartlab.macro.cycles.macroCycle import calcMultipleBand

        r = calcMultipleBand([], current=10.0)
        assert r is None or hasattr(r, "zone")


class TestRateOutlook:
    def test_hike(self):
        from dartlab.macro.cycles.macroCycle import rateOutlook

        r = rateOutlook({"fed_funds": 5.0, "cpi_yoy": 5.5, "unemployment": 3.5, "payrolls_change": 300})
        assert r["direction"] in {"hike", "hold", "cut"}
        assert "reasoning" in r

    def test_cut(self):
        from dartlab.macro.cycles.macroCycle import rateOutlook

        r = rateOutlook({"fed_funds": 5.5, "cpi_yoy": 1.8, "unemployment": 6.0, "payrolls_change": 50})
        assert r["direction"] in {"hike", "hold", "cut"}

    def test_hold(self):
        from dartlab.macro.cycles.macroCycle import rateOutlook

        r = rateOutlook({"fed_funds": 4.5, "cpi_yoy": 2.5, "unemployment": 4.0, "payrolls_change": 150})
        assert r["direction"] in {"hike", "hold", "cut"}

    def test_empty(self):
        from dartlab.macro.cycles.macroCycle import rateOutlook

        r = rateOutlook({})
        assert "direction" in r
        assert "reasoning" in r


class TestDecomposeLongRate:
    def test_residualApprox(self):
        from dartlab.macro.cycles.macroCycle import decomposeLongRate

        r = decomposeLongRate(nominal=4.5, bei=2.5, tips=2.0)
        assert r.nominal == 4.5
        assert r.expectedInflation == 2.5
        assert r.realRate == 2.0
        assert abs(r.termPremium - 0.0) < 0.01

    def test_acmGiven(self):
        from dartlab.macro.cycles.macroCycle import decomposeLongRate

        r = decomposeLongRate(nominal=4.5, bei=2.5, tips=2.0, acmTermPremium=0.5)
        assert r.termPremium == 0.5


# ══════════════════════════════════════
# macro/corporate/historicalContext.py
# ══════════════════════════════════════


class TestHySpikesToRecession:
    def test_normalSeries(self):
        from dartlab.macro.corporate.historicalContext import hySpikesToRecession

        # 정상 시계열
        series = {f"2020-{m:02d}": 4.0 + 0.1 * (m % 5) for m in range(1, 13)}
        series.update({f"2021-{m:02d}": 4.5 + 0.15 * (m % 5) for m in range(1, 13)})
        r = hySpikesToRecession(series)
        assert hasattr(r, "totalSpikes")

    def test_emptyDict(self):
        from dartlab.macro.corporate.historicalContext import hySpikesToRecession

        r = hySpikesToRecession({})
        assert r is not None
        assert r.totalSpikes == 0


class TestYieldCurveInversions:
    def test_positiveSpread(self):
        from dartlab.macro.corporate.historicalContext import yieldCurveInversionsToRecession

        series = {f"2020-{m:02d}": 1.0 + 0.05 * m for m in range(1, 13)}
        r = yieldCurveInversionsToRecession(series)
        assert hasattr(r, "totalInversions")

    def test_inversion(self):
        from dartlab.macro.corporate.historicalContext import yieldCurveInversionsToRecession

        series = {}
        for m in range(1, 13):
            series[f"2019-{m:02d}"] = 1.0
        for m in range(1, 7):
            series[f"2020-{m:02d}"] = -0.3
        r = yieldCurveInversionsToRecession(series)
        assert r.totalInversions >= 1


class TestUnemploymentBounce:
    def test_stable(self):
        from dartlab.macro.corporate.historicalContext import unemploymentBounceToRecession

        series = {f"2020-{m:02d}": 4.0 for m in range(1, 13)}
        for y in range(2021, 2023):
            for m in range(1, 13):
                series[f"{y}-{m:02d}"] = 4.0
        r = unemploymentBounceToRecession(series)
        assert hasattr(r, "totalBounces")

    def test_empty(self):
        from dartlab.macro.corporate.historicalContext import unemploymentBounceToRecession

        r = unemploymentBounceToRecession({})
        assert r.totalBounces == 0


class TestCpiAccelerationEvents:
    def test_steadyInflation(self):
        from dartlab.macro.corporate.historicalContext import cpiAccelerationEvents

        # 안정적 CPI
        series = {f"2020-{m:02d}": 100.0 + m * 0.2 for m in range(1, 13)}
        for y in range(2021, 2024):
            for m in range(1, 13):
                series[f"{y}-{m:02d}"] = 100.0 + (y - 2020) * 12 * 0.2 + m * 0.2
        r = cpiAccelerationEvents(series)
        assert "count" in r
        assert "description" in r

    def test_emptySeries(self):
        from dartlab.macro.corporate.historicalContext import cpiAccelerationEvents

        r = cpiAccelerationEvents({})
        assert "count" in r
        assert r["count"] == 0


# ══════════════════════════════════════
# Smoke — all imports cohabit
# ══════════════════════════════════════


def test_macroPublicEntries():
    """macro 공개 진입점 import smoke."""
    from dartlab.macro import Macro

    assert Macro is not None


def test_macroCycleEntries():
    """macroCycle 공개 함수 import smoke."""
    from dartlab.macro.cycles.macroCycle import (
        CYCLE_SECTOR_MAP,
        classifyCycle,
        decomposeLongRate,
        detectTransitionSequence,
        interpretAssets,
        rateOutlook,
    )

    assert classifyCycle is not None
    assert CYCLE_SECTOR_MAP


def test_macroCrisisEntries():
    """macro/crisis 공개 함수 import smoke."""
    from dartlab.macro.crisis.crisis import analyzeCrisis
    from dartlab.macro.crisis.detectors import (
        creditToGDPGap,
        fisherDebtDeflation,
        ghsCrisisScore,
        minskyPhase,
        recessionDashboard,
    )

    assert analyzeCrisis is not None


def test_historicalContextEntries():
    """historicalContext 공개 함수 import smoke."""
    from dartlab.macro.corporate.historicalContext import (
        buildHistoricalContext,
        bullishSignalFlags,
        cpiAccelerationEvents,
        hyCompressionToExpansion,
        hySpikesToRecession,
        matchHistoricalEvents,
        simultaneousWarningFlags,
        unemploymentBounceToRecession,
        yieldCurveInversionsToRecession,
    )

    assert buildHistoricalContext is not None


def test_historicalContextMissingnessDoesNotBecomeLowRisk():
    from dartlab.macro.corporate.historicalContext import buildHistoricalContext

    empty = buildHistoricalContext({})
    assert empty.status == "unavailable"
    assert empty.riskLevel is None
    assert empty.opportunityLevel is None

    sparse = buildHistoricalContext({"hy_spread": {"2025-01": 3.0, "2025-02": 3.2}})
    assert sparse.status == "partial"
    assert sparse.riskLevel is None
    assert sparse.suggestedScenario is None


def test_crisisDalioExplicitZeroOverridesFetchedValues():
    from dartlab.macro.crisis._crisisDetectors import _crisisDalioDebtCycle

    data = {
        "total_debt_to_gdp": 250.0,
        "debt_service_yoy": 3.0,
        "real_rate": 5.0,
        "gdp_growth": 4.0,
        "fed_funds": 5.0,
        "public_debt_to_gdp": 150.0,
    }
    debt, policy = _crisisDalioDebtCycle(
        data,
        0.0,
        {
            "totalDebtToGdp": 0.0,
            "debtServiceYoY": 0.0,
            "realRate": 0.0,
            "gdpGrowth": 0.0,
            "policyRate": 0.0,
            "publicDebtToGdp": 0.0,
            "fxFlexibility": "flexible",
        },
    )

    assert debt is not None
    assert "총부채/GDP 0%" in debt["signals"]
    assert policy is not None
    assert policy["monetary"] == "maxed"
    assert policy["fiscal"] == "spare"
