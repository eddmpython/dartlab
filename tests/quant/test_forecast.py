"""quant.forecastReturns 단위 테스트.

합성 시계열 (uptrend, downtrend, sideways) 으로 4 모델 (Naive · AR(1) · ETS-Holt · Theta)
+ ADF + Conformal interval + dispatch 룰을 검증한다.

fetchOhlcv 는 monkeypatch 로 mocking — 외부 네트워크 의존 0.
"""

from __future__ import annotations

import numpy as np
import polars as pl
import pytest

pytestmark = pytest.mark.unit


# ── helpers: 합성 OHLCV ─────────────────────────────────────


def _uptrend_close(n: int = 250, drift: float = 0.0008, vol: float = 0.005, seed: int = 42) -> np.ndarray:
    """drift +0.08% / day · noise σ=0.5% — 명확한 trend."""
    rng = np.random.default_rng(seed)
    log_ret = drift + vol * rng.standard_normal(n - 1)
    return 100.0 * np.exp(np.concatenate([[0.0], np.cumsum(log_ret)]))


def _downtrend_close(n: int = 250, drift: float = -0.0008, vol: float = 0.005, seed: int = 43) -> np.ndarray:
    """drift -0.08% / day."""
    rng = np.random.default_rng(seed)
    log_ret = drift + vol * rng.standard_normal(n - 1)
    return 100.0 * np.exp(np.concatenate([[0.0], np.cumsum(log_ret)]))


def _sideways_close(n: int = 250, vol: float = 0.005, seed: int = 44) -> np.ndarray:
    """평균 회귀 OU 프로세스 — drift 0, ρ=0.7."""
    rng = np.random.default_rng(seed)
    rho = 0.7
    log_ret = np.zeros(n - 1)
    for i in range(1, n - 1):
        log_ret[i] = rho * log_ret[i - 1] + vol * rng.standard_normal()
    return 100.0 * np.exp(np.concatenate([[0.0], np.cumsum(log_ret)]))


def _make_ohlcv_df(close: np.ndarray) -> pl.DataFrame:
    """close numpy → Polars OHLCV DataFrame (date 는 영업일 sequence)."""
    n = len(close)
    spread = 0.5
    high = close + spread
    low = close - spread
    open_ = close
    volume = np.full(n, 1_000_000, dtype=np.float64)
    from datetime import date, timedelta

    base = date(2024, 1, 2)
    dates = [base + timedelta(days=i) for i in range(n)]
    return pl.DataFrame(
        {
            "date": dates,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        }
    )


@pytest.fixture
def patch_fetch_ohlcv(monkeypatch):
    """fetchOhlcv 를 합성 시계열로 대체하는 fixture factory."""

    def _patcher(close: np.ndarray):
        df = _make_ohlcv_df(close)

        def _fake_fetch(stockCode, **kwargs):
            return df

        monkeypatch.setattr("dartlab.quant.benchmark.forecast.fetchOhlcv", _fake_fetch)
        return df

    return _patcher


# ═══════════════════════════════════════════════════════════
# ADF + dispatch
# ═══════════════════════════════════════════════════════════


class TestAdf:
    def test_random_walk_high_pvalue(self):
        from dartlab.quant.benchmark.forecast import _pAdfStationary

        rng = np.random.default_rng(123)
        rw = np.cumsum(rng.standard_normal(300))
        p = _pAdfStationary(rw)
        assert 0.0 <= p <= 1.0
        # random walk 는 정상이 아니다 → p > 0.05 기대
        assert p > 0.05

    def test_short_series_returns_one(self):
        from dartlab.quant.benchmark.forecast import _pAdfStationary

        p = _pAdfStationary(np.array([1.0, 2.0, 3.0]))
        assert p == 1.0


class TestDispatch:
    def test_short_series_picks_naive(self):
        from dartlab.quant.benchmark.forecast import _pickModel

        y = np.zeros(30)
        assert _pickModel(y) == "naive"

    def test_long_random_walk_picks_etsholt(self):
        from dartlab.quant.benchmark.forecast import _pickModel

        rng = np.random.default_rng(7)
        # log-return 시계열은 대개 stationary 라 _pickModel 에 직접 random-walk 의 log-return 줘도 theta 가능.
        # 여기서는 long trend 시계열 (non-stationary log) 로 etsHolt 를 강제하기 위해 cumsum 사용.
        y = np.cumsum(rng.standard_normal(300))  # random walk → ADF p > 0.05
        chosen = _pickModel(y)
        assert chosen in ("etsHolt", "theta")  # 둘 다 유효 (휴리스틱)


# ═══════════════════════════════════════════════════════════
# 4 model fit
# ═══════════════════════════════════════════════════════════


class TestModels:
    def test_naive_constant_drift(self):
        from dartlab.quant.benchmark.forecast import _modelNaive

        y = np.array([0.001, 0.002, 0.003, -0.001, 0.002])
        forecasts, inSample = _modelNaive(y, horizon=3)
        expected_drift = float(np.mean(y))
        assert forecasts.shape == (3,)
        np.testing.assert_allclose(forecasts, [expected_drift] * 3, atol=1e-12)
        assert inSample.shape == (5,)

    def test_ar1_recovers_persistence(self):
        from dartlab.quant.benchmark.forecast import _modelAr1

        # AR(1) 진짜 데이터 — ρ=0.5
        rng = np.random.default_rng(99)
        n = 500
        y = np.zeros(n)
        for i in range(1, n):
            y[i] = 0.5 * y[i - 1] + 0.01 * rng.standard_normal()
        forecasts, inSample = _modelAr1(y, horizon=5)
        # forecast 는 점차 0 으로 수렴 (장기평균)
        assert abs(forecasts[-1]) < abs(forecasts[0]) + 1e-3
        assert inSample.shape == (n,)

    def test_ets_holt_extrapolates_trend(self):
        from dartlab.quant.benchmark.forecast import _modelEtsHolt

        # 명확한 선형 trend
        y = 0.001 + 0.0001 * np.arange(100, dtype=np.float64)
        forecasts, inSample = _modelEtsHolt(y, horizon=10)
        # 마지막 trend 가 양수 → 양수 forecast
        assert forecasts[-1] > forecasts[0]
        assert np.all(np.isfinite(forecasts))

    def test_theta_handles_constant(self):
        from dartlab.quant.benchmark.forecast import _modelTheta

        y = np.full(100, 0.001)
        forecasts, inSample = _modelTheta(y, horizon=5)
        # 상수 시계열 → forecast 도 거의 같은 값
        np.testing.assert_allclose(forecasts, [0.001] * 5, atol=1e-3)

    def test_short_series_falls_back_to_naive(self):
        from dartlab.quant.benchmark.forecast import _modelAr1, _modelEtsHolt, _modelTheta

        y = np.array([0.001, 0.002])
        for fn in (_modelAr1, _modelEtsHolt, _modelTheta):
            f, _ = fn(y, horizon=3)
            assert f.shape == (3,)
            assert np.all(np.isfinite(f))


# ═══════════════════════════════════════════════════════════
# Conformal
# ═══════════════════════════════════════════════════════════


class TestConformal:
    def test_half_width_nonneg(self):
        from dartlab.quant.benchmark.forecast import _conformalHalfWidth

        residuals = np.array([0.01, -0.02, 0.005, -0.015, 0.008])
        q = _conformalHalfWidth(residuals, alpha=0.10)
        assert q >= 0
        assert q == pytest.approx(0.02, rel=0.5)  # 가장 큰 |residual| 근처

    def test_zero_residuals(self):
        from dartlab.quant.benchmark.forecast import _conformalHalfWidth

        q = _conformalHalfWidth(np.zeros(10))
        assert q == 0.0

    def test_handles_nan(self):
        from dartlab.quant.benchmark.forecast import _conformalHalfWidth

        residuals = np.array([0.01, np.nan, -0.02, np.inf])
        q = _conformalHalfWidth(residuals)
        assert np.isfinite(q)


# ═══════════════════════════════════════════════════════════
# 메인 진입점 — forecastReturns
# ═══════════════════════════════════════════════════════════


class TestForecastReturns:
    def test_uptrend_positive_cumulative(self, patch_fetch_ohlcv):
        from dartlab.quant.benchmark.forecast import forecastReturns

        patch_fetch_ohlcv(_uptrend_close(n=250))
        r = forecastReturns("TEST1", market="KR", horizon=5)
        assert "error" not in r
        # 합성 uptrend 의 log-return 시계열은 stationary (mean drift) 라 ar1 또는 etsHolt 가능
        assert r["modelChosen"] in ("etsHolt", "ar1", "theta", "naive")
        assert r["horizon"] == 5
        assert len(r["forecastTable"]) == 5
        # Trend uptrend → cumLogReturn 양수 또는 작은 음수 (calib noise 허용 범위)
        assert r["forecastTable"][-1]["cumLogReturn"] > -0.05

    def test_downtrend_negative_or_neutral(self, patch_fetch_ohlcv):
        from dartlab.quant.benchmark.forecast import forecastReturns

        patch_fetch_ohlcv(_downtrend_close(n=250))
        r = forecastReturns("TEST2", market="KR", horizon=5)
        assert "error" not in r
        assert r["forecastTable"][-1]["cumLogReturn"] < 0.05

    def test_sideways_small_forecast(self, patch_fetch_ohlcv):
        from dartlab.quant.benchmark.forecast import forecastReturns

        patch_fetch_ohlcv(_sideways_close(n=250))
        r = forecastReturns("TEST3", market="KR", horizon=5)
        assert "error" not in r
        # Sideways → |pointForecast| 작음 (절대값 0.5σ 이내)
        for row in r["forecastTable"]:
            assert abs(row["pointForecast"]) < 0.05

    def test_interval_monotone(self, patch_fetch_ohlcv):
        from dartlab.quant.benchmark.forecast import forecastReturns

        patch_fetch_ohlcv(_uptrend_close(n=250))
        r = forecastReturns("TEST4", market="KR", horizon=5)
        for row in r["forecastTable"]:
            assert row["lowerBound"] <= row["pointForecast"] <= row["upperBound"]
            assert row["cumLowerBound"] <= row["cumLogReturn"] <= row["cumUpperBound"]
            assert row["priceLower"] <= row["pricePoint"] <= row["priceUpper"]

    def test_no_nan_in_output(self, patch_fetch_ohlcv):
        from dartlab.quant.benchmark.forecast import forecastReturns

        patch_fetch_ohlcv(_uptrend_close(n=250))
        r = forecastReturns("TEST5", market="KR", horizon=10)
        for row in r["forecastTable"]:
            for k, v in row.items():
                if isinstance(v, float):
                    assert np.isfinite(v), f"{k} NaN/inf detected: {v}"

    def test_explicit_models_ensemble(self, patch_fetch_ohlcv):
        from dartlab.quant.benchmark.forecast import forecastReturns

        patch_fetch_ohlcv(_uptrend_close(n=250))
        r = forecastReturns("TEST6", market="KR", horizon=5, models=["etsHolt", "theta"])
        assert "error" not in r
        assert r["modelChosen"] == "etsHolt+theta"
        assert r["modelsConsidered"] == ["etsHolt", "theta"]

    def test_invalid_model_returns_error(self, patch_fetch_ohlcv):
        from dartlab.quant.benchmark.forecast import forecastReturns

        patch_fetch_ohlcv(_uptrend_close(n=250))
        r = forecastReturns("TEST7", market="KR", horizon=5, models=["xgboost"])
        assert "error" in r

    def test_short_series_returns_error(self, patch_fetch_ohlcv):
        from dartlab.quant.benchmark.forecast import forecastReturns

        patch_fetch_ohlcv(_uptrend_close(n=20))
        r = forecastReturns("TEST8", market="KR", horizon=5)
        assert "error" in r

    def test_no_data_returns_error(self, monkeypatch):
        from dartlab.quant.benchmark.forecast import forecastReturns

        monkeypatch.setattr("dartlab.quant.benchmark.forecast.fetchOhlcv", lambda code, **kw: None)
        r = forecastReturns("FAIL", market="KR", horizon=5)
        assert "error" in r

    def test_horizon_clamp_to_min_1(self, patch_fetch_ohlcv):
        from dartlab.quant.benchmark.forecast import forecastReturns

        patch_fetch_ohlcv(_uptrend_close(n=250))
        r = forecastReturns("TEST9", market="KR", horizon=0)
        assert "error" not in r
        assert r["horizon"] == 1
        assert len(r["forecastTable"]) == 1

    def test_evidence_fields_present(self, patch_fetch_ohlcv):
        from dartlab.quant.benchmark.forecast import forecastReturns

        patch_fetch_ohlcv(_uptrend_close(n=250))
        r = forecastReturns("TEST10", market="KR", horizon=5)
        # SKILL.md 의 requiredEvidence 충실도
        for k in (
            "stockCode",
            "lastDate",
            "modelChosen",
            "nObs",
            "calibSize",
            "pAdfStationary",
            "conformalHalfWidth",
            "summary",
        ):
            assert k in r, f"evidence 필드 누락: {k}"

    def test_summary_format(self, patch_fetch_ohlcv):
        from dartlab.quant.benchmark.forecast import forecastReturns

        patch_fetch_ohlcv(_uptrend_close(n=250))
        r = forecastReturns("TEST11", market="KR", horizon=5)
        assert "%" in r["summary"]
        assert "90% empirical band" in r["summary"]
        assert r["coverageGuaranteed"] is False
        assert r["intervalMethod"] == "expandingWindowHeldoutResidualQuantile"


# ═══════════════════════════════════════════════════════════
# Axis registry 통합 (정식 dispatch 경유)
# ═══════════════════════════════════════════════════════════


class TestAxisRegistry:
    def test_forecast_axis_registered(self):
        from dartlab.quant import _AXIS_REGISTRY

        assert "forecast" in _AXIS_REGISTRY
        entry = _AXIS_REGISTRY["forecast"]
        assert entry.fn == "forecastReturns"
        assert entry.module == "dartlab.quant.benchmark.forecast"
        assert entry.stockRequired is True

    def test_korean_alias(self):
        from dartlab.quant import _ALIASES

        assert _ALIASES.get("예측") == "forecast"
        assert _ALIASES.get("수익률예측") == "forecast"

    def test_dispatch_via_quant_call(self, patch_fetch_ohlcv):
        import dartlab

        patch_fetch_ohlcv(_uptrend_close(n=250))
        r = dartlab.quant("forecast", "TEST_DISPATCH", horizon=3)
        assert "error" not in r
        assert r["horizon"] == 3
        # 한글 alias 도 동일 결과
        r2 = dartlab.quant("예측", "TEST_DISPATCH", horizon=3)
        assert r2["modelChosen"] == r["modelChosen"]


# ═══════════════════════════════════════════════════════════
# forecastRuleFactory + walkForward(rule_factory=...) 결합
# ═══════════════════════════════════════════════════════════


class TestForecastRuleFactory:
    def test_factory_returns_rule_of_correct_length(self):
        from dartlab.quant.benchmark.forecast import forecastRuleFactory
        from dartlab.quant.strategy.rule import Rule

        factory = forecastRuleFactory(threshold=0.002)
        isClose = _uptrend_close(n=200)
        rule = factory(isClose, oosLen=20)
        assert isinstance(rule, Rule)
        assert len(rule.entry_expr) == 200 + 20
        assert len(rule.exit_expr) == 200 + 20

    def test_is_region_all_false(self):
        """IS 구간 (학습) 은 entry/exit 모두 False — 학습용."""
        from dartlab.quant.benchmark.forecast import forecastRuleFactory

        factory = forecastRuleFactory(threshold=0.002)
        isClose = _uptrend_close(n=200)
        rule = factory(isClose, oosLen=20)
        assert not rule.entry_expr[:200].any()
        assert not rule.exit_expr[:200].any()

    def test_short_is_returns_empty_rule(self):
        from dartlab.quant.benchmark.forecast import forecastRuleFactory

        factory = forecastRuleFactory()
        rule = factory(np.array([100.0, 101.0, 99.0]), oosLen=10)
        # IS < 30 → 모두 False
        assert not rule.entry_expr.any()
        assert not rule.exit_expr.any()

    def test_walk_forward_with_factory(self):
        from dartlab.quant.benchmark.forecast import forecastRuleFactory
        from dartlab.quant.strategy.backtest import walkForward

        close = _uptrend_close(n=400)
        factory = forecastRuleFactory(threshold=0.0005, models=["ar1"])
        bt = walkForward(close, rule=None, ruleFactory=factory, train=200, test=50, step=50)
        assert bt.status == "ok"
        assert bt.oos is True
        assert bt.cpcv is not None
        assert bt.cpcv.get("refit_count", 0) >= 2
        assert "n_folds" in bt.cpcv
        # PBO 는 refit path 에서 None (IS region all-False 설계 때문에 가짜 PBO 회피)
        assert bt.pbo is None

    def test_walk_forward_factory_loose_mode_entry_active(self):
        """loose mode (default) — 강한 trend 합성 데이터에서 entry 활성화 (쓸만함 검증)."""
        from dartlab.quant.benchmark.forecast import forecastRuleFactory
        from dartlab.quant.strategy.backtest import walkForward

        # 강한 drift +0.3%/day
        rng = np.random.default_rng(11)
        n = 600
        close = 100.0 * np.exp(np.concatenate([[0.0], np.cumsum(0.003 + 0.005 * rng.standard_normal(n - 1))]))
        factory = forecastRuleFactory(threshold=0.0005, models=["ar1"])
        bt = walkForward(close, rule=None, ruleFactory=factory, train=200, test=40, step=40)
        assert bt.status == "ok"
        # 강한 trend → entry 일자 비율 > 50% (loose mode 검증)
        active_ratio = float(np.mean(bt.returns != 0))
        assert active_ratio > 0.5, f"loose mode 에서 active_ratio={active_ratio:.2f} 너무 낮음"
        # forecast 가 trend 잡으면 sharpe > 1 기대
        assert bt.sharpe > 1.0, f"trend forecast sharpe={bt.sharpe:.2f} 너무 낮음"

    def test_walk_forward_factory_strict_mode(self):
        """strict mode — interval 검증 추가. 일별 conformal width 가 커서 entry 적음."""
        from dartlab.quant.benchmark.forecast import forecastRuleFactory
        from dartlab.quant.strategy.backtest import walkForward

        close = _uptrend_close(n=400)
        factory = forecastRuleFactory(threshold=0.0005, models=["ar1"], requireConfidence=True)
        bt = walkForward(close, rule=None, ruleFactory=factory, train=200, test=50, step=50)
        assert bt.status == "ok"
        # strict 는 entry 가 매우 적거나 0 (예상된 동작)
        active_ratio = float(np.mean(bt.returns != 0))
        loose_factory = forecastRuleFactory(threshold=0.0005, models=["ar1"], requireConfidence=False)
        bt_loose = walkForward(close, rule=None, ruleFactory=loose_factory, train=200, test=50, step=50)
        loose_active = float(np.mean(bt_loose.returns != 0))
        # strict 는 loose 보다 entry 적거나 같다
        assert active_ratio <= loose_active

    def test_walk_forward_static_rule_still_works(self):
        """rule_factory 없이 정적 Rule 도 그대로 동작 (backward compat)."""
        from dartlab.quant.strategy.backtest import walkForward
        from dartlab.quant.strategy.rule import Rule

        close = _uptrend_close(n=400)
        n = len(close)
        # 단순 정적 entry/exit (절반 holding)
        entry = np.zeros(n, dtype=bool)
        exit_ = np.zeros(n, dtype=bool)
        entry[10] = True
        exit_[100] = True
        rule = Rule(entry_expr=entry, exit_expr=exit_)
        bt = walkForward(close, rule, train=200, test=50, step=50)
        # 정적 rule path 도 ok 상태
        assert bt.status == "ok"
        assert bt.oos is False
        assert bt.cpcv.get("evaluation_mode") == "fixed_rule_rolling_stress"
        assert bt.cpcv.get("refit_count", 0) == 0

    def test_walk_forward_missing_both_returns_error(self):
        from dartlab.quant.strategy.backtest import walkForward

        close = _uptrend_close(n=400)
        bt = walkForward(close, rule=None, train=200, test=50, step=50)
        assert bt.status == "error"
        assert "rule" in (bt.reason or "")

    def test_walk_forward_factory_wrong_length_returns_error(self):
        from dartlab.quant.strategy.backtest import walkForward
        from dartlab.quant.strategy.rule import Rule

        def bad_factory(isClose, oosLen):
            # 잘못된 길이 (train + test 아닌 len(is_close) 만)
            return Rule(
                entry_expr=np.zeros(len(isClose), dtype=bool),
                exit_expr=np.zeros(len(isClose), dtype=bool),
            )

        close = _uptrend_close(n=400)
        bt = walkForward(close, rule=None, ruleFactory=bad_factory, train=200, test=50, step=50)
        assert bt.status == "error"
        assert "length" in (bt.reason or "")
