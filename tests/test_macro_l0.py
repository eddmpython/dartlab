"""macro L0 순수함수 단위 테스트.

외부 API 호출 없이 순수 함수만 테스트.
"""

import numpy as np
import pytest


# ══════════════════════════════════════
# regimeSwitching.py
# ══════════════════════════════════════


class TestClevelandProbit:
    def test_positive_spread_low_prob(self):
        from dartlab.core.finance.regimeSwitching import clevelandProbit

        r = clevelandProbit(2.0)
        assert r.probability < 0.1
        assert r.zone == "low"

    def test_negative_spread_high_prob(self):
        from dartlab.core.finance.regimeSwitching import clevelandProbit

        r = clevelandProbit(-0.5)
        assert r.probability > 0.3
        assert r.zone in ("moderate", "elevated")

    def test_zero_spread(self):
        from dartlab.core.finance.regimeSwitching import clevelandProbit

        r = clevelandProbit(0.0)
        assert 0.2 < r.probability < 0.4


class TestSahmRule:
    def test_stable_unemployment(self):
        from dartlab.core.finance.regimeSwitching import sahmRule

        r = sahmRule([4.0] * 15)
        assert not r.triggered
        assert r.value == 0.0

    def test_rising_unemployment(self):
        from dartlab.core.finance.regimeSwitching import sahmRule

        series = [3.5] * 12 + [4.0, 4.2, 4.5]
        r = sahmRule(series)
        assert r.triggered or r.value >= 0.3

    def test_insufficient_data(self):
        from dartlab.core.finance.regimeSwitching import sahmRule

        r = sahmRule([4.0] * 5)
        assert r.zone == "normal"


class TestConferenceBoardLEI:
    def test_basic_lei(self):
        from dartlab.core.finance.regimeSwitching import conferenceBoardLEI

        r = conferenceBoardLEI({"avg_weekly_hours": 0.2, "sp500": 1.5, "term_spread": 1.8})
        assert r.level != 0
        assert r.signal in ("expansion", "caution", "recession_warning")

    def test_empty_components(self):
        from dartlab.core.finance.regimeSwitching import conferenceBoardLEI

        r = conferenceBoardLEI({})
        assert r.signal == "caution"


class TestHamiltonRegime:
    def test_two_regime_separation(self):
        from dartlab.core.finance.regimeSwitching import hamiltonRegime

        np.random.seed(42)
        y = np.concatenate([np.random.normal(3, 1, 50), np.random.normal(-1, 2, 20), np.random.normal(3, 1, 30)])
        r = hamiltonRegime(y.tolist())
        assert r.converged
        # 침체 구간(50-70)에서 contraction 확률이 높아야 함
        assert r.smoothedProbs[60, 1] > 0.7

    def test_short_series(self):
        from dartlab.core.finance.regimeSwitching import hamiltonRegime

        r = hamiltonRegime([1.0, 2.0, 3.0])
        assert not r.converged


# ══════════════════════════════════════
# yieldCurve.py
# ══════════════════════════════════════


class TestNelsonSiegel:
    def test_normal_curve(self):
        from dartlab.core.finance.yieldCurve import nelsonSiegel

        ns = nelsonSiegel([1, 2, 5, 10, 30], [4.5, 4.2, 3.9, 3.8, 4.0])
        assert ns.rmse < 0.3
        assert ns.beta0 > 3.0

    def test_inverted_curve(self):
        from dartlab.core.finance.yieldCurve import nelsonSiegel

        ns = nelsonSiegel([0.25, 1, 2, 5, 10, 30], [5.3, 5.0, 4.8, 4.2, 3.8, 3.9])
        assert ns.interpretation in ("inverted", "flat")

    def test_insufficient_data(self):
        from dartlab.core.finance.yieldCurve import nelsonSiegel

        ns = nelsonSiegel([1, 2], [4.0, 3.9])
        assert ns.interpretation == "insufficient"


# ══════════════════════════════════════
# nowcast.py
# ══════════════════════════════════════


class TestGdpNowcast:
    def test_factor_extraction(self):
        from dartlab.core.finance.nowcast import gdpNowcast

        np.random.seed(42)
        T = 60
        factor_true = np.cumsum(np.random.normal(0, 0.3, T))
        loadings = np.array([0.8, 0.6, 0.5, 0.4, 1.0])
        indicators = np.outer(factor_true, loadings) + np.random.normal(0, 0.5, (T, 5))

        nc = gdpNowcast(indicators, nFactors=1, arOrder=1, maxIter=20)
        corr = abs(np.corrcoef(factor_true, nc.factor)[0, 1])
        assert corr > 0.8

    def test_missing_data(self):
        from dartlab.core.finance.nowcast import gdpNowcast

        np.random.seed(42)
        indicators = np.random.normal(0, 1, (40, 4))
        indicators[-3:, -2:] = np.nan
        nc = gdpNowcast(indicators)
        assert nc.factor is not None


# ══════════════════════════════════════
# crisisDetector.py
# ══════════════════════════════════════


class TestCreditToGDPGap:
    def test_rising_credit(self):
        from dartlab.core.finance.crisisDetector import creditToGDPGap

        series = list(range(100, 200, 5))
        r = creditToGDPGap(series)
        assert r.gap > 0

    def test_stable_credit(self):
        from dartlab.core.finance.crisisDetector import creditToGDPGap

        r = creditToGDPGap([150.0] * 20)
        assert abs(r.gap) < 5


class TestGHSCrisisScore:
    def test_high_risk(self):
        from dartlab.core.finance.crisisDetector import ghsCrisisScore

        r = ghsCrisisScore(creditGrowth3y=15, assetPriceGrowth3y=80)
        assert r.score >= 70
        assert r.crisisProb >= 0.3

    def test_normal(self):
        from dartlab.core.finance.crisisDetector import ghsCrisisScore

        r = ghsCrisisScore(creditGrowth3y=2, assetPriceGrowth3y=10)
        assert r.zone == "normal"


class TestMinskyPhase:
    def test_overtrading(self):
        from dartlab.core.finance.crisisDetector import minskyPhase

        r = minskyPhase(creditGap=12, assetReturn3y=70, hySpread=280, vix=14)
        assert r.phase == "overtrading"

    def test_discredit(self):
        from dartlab.core.finance.crisisDetector import minskyPhase

        r = minskyPhase(hySpread=700, vix=40, assetReturn3y=-30)
        assert r.phase == "discredit"


class TestKooRecession:
    def test_bsr_detected(self):
        from dartlab.core.finance.crisisDetector import kooBalanceSheetRecession

        r = kooBalanceSheetRecession(5000, 3000, 20000, 0.5)
        assert r.isBSR
        assert r.privateSurplus > 3


class TestFisherDeflation:
    def test_deflation_risk(self):
        from dartlab.core.finance.crisisDetector import fisherDebtDeflation

        r = fisherDebtDeflation(dsr=15, cpiYoy=-0.5, nplRate=6)
        assert r.risk == "high"


# ══════════════════════════════════════
# macroCycle.py
# ══════════════════════════════════════


class TestCopperGoldRatio:
    def test_rising(self):
        from dartlab.core.finance.macroCycle import copperGoldRatio

        r = copperGoldRatio(10000, 2000, 9000, 2000)
        assert r.direction == "rising"

    def test_stable(self):
        from dartlab.core.finance.macroCycle import copperGoldRatio

        r = copperGoldRatio(9000, 2000, 9000, 2000)
        assert r.direction == "stable"


class TestRealRateRegime:
    def test_tightening(self):
        from dartlab.core.finance.macroCycle import realRateRegime

        r = realRateRegime(2.5, 3.0)
        assert r.regime == "tightening"

    def test_goldilocks(self):
        from dartlab.core.finance.macroCycle import realRateRegime

        r = realRateRegime(0.5, 1.8)
        assert r.regime == "goldilocks"


# ══════════════════════════════════════
# fci.py
# ══════════════════════════════════════


class TestFCI:
    def test_tight(self):
        from dartlab.core.finance.fci import calcFCI

        # 점진적으로 상승하는 금리 + 스프레드 → 최신값이 평균 위 → 긴축
        r = calcFCI({
            "policy_rate": [1, 2, 3, 4, 5, 5.5],
            "credit_spread": [2, 3, 4, 5, 6, 7],
        }, market="US")
        assert r.value > 0

    def test_loose(self):
        from dartlab.core.finance.fci import calcFCI

        r = calcFCI({"policy_rate": [0.5] * 10, "credit_spread": [2.0] * 10, "equity": [20] * 10}, market="US")
        # 낮은 금리 + 낮은 스프레드 + 높은 주가 = 완화
        assert r.regime in ("loose", "neutral")


# ══════════════════════════════════════
# inventoryCycle.py
# ══════════════════════════════════════


class TestInventoryCycle:
    def test_active_restock(self):
        from dartlab.core.finance.inventoryCycle import classifyInventoryPhase

        r = classifyInventoryPhase(55, 48, 1.10)
        assert r.phase == "active_restock"

    def test_active_destock(self):
        from dartlab.core.finance.inventoryCycle import classifyInventoryPhase

        r = classifyInventoryPhase(45, 52, 0.90)
        assert r.phase == "active_destock"


class TestISMBarometer:
    def test_strong_expansion(self):
        from dartlab.core.finance.inventoryCycle import ismBarometer

        r = ismBarometer(57)
        assert r.zone == "strong_expansion"

    def test_hike_end(self):
        from dartlab.core.finance.inventoryCycle import ismBarometer

        r = ismBarometer(53, 56)
        assert r.rateImplication == "hike_end"


# ══════════════════════════════════════
# termsOfTrade.py
# ══════════════════════════════════════


class TestTermsOfTrade:
    def test_improving(self):
        from dartlab.core.finance.termsOfTrade import calcToT

        r = calcToT(110, 100, 105, 100)
        assert r.direction == "improving"

    def test_proxy(self):
        from dartlab.core.finance.termsOfTrade import totProxy

        r = totProxy(fxYoy=10, oilYoy=-5)
        assert r.value > 10
        assert r.direction == "improving"


# ══════════════════════════════════════
# portfolioMapping.py
# ══════════════════════════════════════


class TestPortfolioMapping:
    def test_favorable_expansion(self):
        from dartlab.core.finance.portfolioMapping import regimeToAllocation

        r = regimeToAllocation({"overall": "favorable", "cycle": {"phase": "expansion"}})
        assert r.equity >= 60
        assert r.equity + r.bond + r.gold + r.cash == 100

    def test_unfavorable_contraction(self):
        from dartlab.core.finance.portfolioMapping import regimeToAllocation

        r = regimeToAllocation({"overall": "unfavorable", "cycle": {"phase": "contraction"}})
        assert r.equity <= 30
        assert r.bond >= 30


# ══════════════════════════════════════
# strategyRules.py
# ══════════════════════════════════════


class TestStrategyRules:
    def test_40_strategies(self):
        from dartlab.core.finance.strategyRules import evaluateStrategies

        mock = {
            "cycle": {"phase": "expansion", "phaseLabel": "확장"},
            "rates": {"outlook": {"direction": "cut"}, "inflation": {"state": "warm", "stateLabel": "높음"}, "employment": {"state": "strong", "stateLabel": "강함"}, "expectation": {"spread2yFf": -0.3}},
            "forecast": {"recessionProb": {"probability": 0.12}, "lei": {"signal": "expansion", "description": "LEI", "lagMomentum": 0.3}, "nowcast": {"gdpEstimate": 2.5, "description": "GDP"}},
            "crisis": {"capexPressure": {"pressure": "easing", "pressureLabel": "완화", "description": "HY"}, "dollarSafeHaven": {"status": "inactive", "description": "V", "dxyChange3m": -1.5}},
            "inventory": {"inventoryPhase": {"phase": "active_restock", "phaseLabel": "적극보충", "ratio": 1.1, "equityImplication": "bullish", "description": ">"}, "ismBarometer": {"level": 53, "rateImplication": "hike_end"}, "ismAllocation": {"stance": "neutral", "description": "ISM"}},
            "trade": {"termsOfTrade": {"direction": "improving", "description": "개선"}, "totProxy": {"value": 3, "direction": "stable", "description": "안정", "components": {"fxYoy": 5, "oilYoy": 2}}, "exportProfit": {"signal": "positive", "description": "개선"}, "leadingRelativeStrength": {"fxDirection": "krw_strengthen", "description": "한국"}, "usConsumptionLink": {"usRetailYoy": 6, "implication": "미국"}},
            "assets": {"goldDrivers": {"dollarEffect": -0.3}, "copperGold": {"implication": "expansion", "description": "Cu/Au"}},
            "sentiment": {}, "liquidity": {"regime": "normal", "regimeLabel": "정상"},
        }
        signals = evaluateStrategies(mock)
        assert len(signals) == 40
        assert all(hasattr(s, "strength") for s in signals)
        assert all(hasattr(s, "confidence") for s in signals)
        assert sum(1 for s in signals if s.active is None) == 0
