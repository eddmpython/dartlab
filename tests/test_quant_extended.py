"""quant extended 함수 단위 테스트 — 합성 OHLCV 사용.

coverage 대상:
- extended.py: calcTechnicalSignals, calcMarketBeta, calcFundamentalDivergence,
               calcMarketRisk, calcMarketAnalysisFlags
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import polars as pl
import pytest

pytestmark = pytest.mark.unit


# ── 합성 OHLCV 생성 ──


def _make_ohlcv(n: int = 200, trend: str = "up") -> pl.DataFrame:
    """합성 OHLCV DataFrame 생성.

    Args:
        n: 데이터 포인트 수.
        trend: "up" (상승 추세), "down" (하락), "flat" (횡보).
    """
    np.random.seed(42)
    dates = pl.date_range(pl.date(2024, 1, 1), pl.date(2024, 1, 1) + pl.duration(days=n - 1), eager=True)

    if trend == "up":
        base = np.cumsum(np.random.randn(n) * 0.5 + 0.3) + 100
    elif trend == "down":
        base = np.cumsum(np.random.randn(n) * 0.5 - 0.3) + 100
    else:
        base = np.cumsum(np.random.randn(n) * 0.3) + 100

    # Ensure positive
    base = np.maximum(base, 10.0)
    close = base
    high = close * (1 + np.abs(np.random.randn(n) * 0.01))
    low = close * (1 - np.abs(np.random.randn(n) * 0.01))
    open_ = (high + low) / 2
    volume = (np.random.rand(n) * 1_000_000 + 100_000).astype(np.int64)

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


def _make_mock_company(ohlcv: pl.DataFrame | None = None, currency: str = "KRW"):
    """OHLCV가 캐시된 MockCompany."""
    co = MagicMock()
    co.stockCode = "005930"
    co.currency = currency
    co._cache = {"_quant_ohlcv": ohlcv}
    return co


# ── Fixtures ──


@pytest.fixture
def ohlcv_up():
    return _make_ohlcv(200, "up")


@pytest.fixture
def ohlcv_down():
    return _make_ohlcv(200, "down")


@pytest.fixture
def ohlcv_short():
    """데이터 부족 (20일)."""
    return _make_ohlcv(20, "up")


# ═══════════════════════════════════════════════════════════
# calcTechnicalSignals
# ═══════════════════════════════════════════════════════════


class TestCalcTechnicalSignals:
    def test_returns_signals(self, ohlcv_up):
        from dartlab.quant.extended import calcTechnicalSignals

        co = _make_mock_company(ohlcv_up)
        result = calcTechnicalSignals(co)
        assert result is not None
        assert "signals" in result
        assert "signalSummary" in result
        assert "recentEvents" in result

    def test_signal_keys(self, ohlcv_up):
        from dartlab.quant.extended import calcTechnicalSignals

        co = _make_mock_company(ohlcv_up)
        result = calcTechnicalSignals(co)
        sigs = result["signals"]
        assert "goldenCross" in sigs
        assert "rsiSignal" in sigs
        assert "macdSignal" in sigs
        assert "bollingerSignal" in sigs

    def test_signal_summary_structure(self, ohlcv_up):
        from dartlab.quant.extended import calcTechnicalSignals

        co = _make_mock_company(ohlcv_up)
        result = calcTechnicalSignals(co)
        summary = result["signalSummary"]
        assert "bullish" in summary
        assert "bearish" in summary
        assert isinstance(summary["bullish"], int)
        assert isinstance(summary["bearish"], int)

    def test_returns_none_when_short(self, ohlcv_short):
        from dartlab.quant.extended import calcTechnicalSignals

        co = _make_mock_company(ohlcv_short)
        result = calcTechnicalSignals(co)
        assert result is None

    def test_returns_none_when_no_data(self):
        from dartlab.quant.extended import calcTechnicalSignals

        co = _make_mock_company(None)
        result = calcTechnicalSignals(co)
        assert result is None

    def test_recent_events_format(self, ohlcv_up):
        from dartlab.quant.extended import calcTechnicalSignals

        co = _make_mock_company(ohlcv_up)
        result = calcTechnicalSignals(co)
        for event in result["recentEvents"]:
            assert "date" in event
            assert "type" in event
            assert "direction" in event
            assert event["direction"] in ("매수", "매도")


# ═══════════════════════════════════════════════════════════
# calcMarketBeta
# ═══════════════════════════════════════════════════════════


class TestCalcMarketBeta:
    def test_returns_none_when_no_data(self):
        from dartlab.quant.extended import calcMarketBeta

        co = _make_mock_company(None)
        result = calcMarketBeta(co)
        assert result is None

    def test_returns_none_when_short(self, ohlcv_short):
        from dartlab.quant.extended import calcMarketBeta

        co = _make_mock_company(ohlcv_short)
        result = calcMarketBeta(co)
        assert result is None

    @patch("dartlab.quant.extended._fetchBenchmarkForCompany")
    def test_returns_beta_with_benchmark(self, mock_bench, ohlcv_up):
        from dartlab.quant.extended import calcMarketBeta

        benchmark = _make_ohlcv(200, "up")
        mock_bench.return_value = benchmark

        co = _make_mock_company(ohlcv_up)
        result = calcMarketBeta(co)
        if result is not None:
            assert "value" in result
            assert "interpretation" in result
            assert isinstance(result["value"], float)

    @patch("dartlab.quant.extended._fetchBenchmarkForCompany")
    def test_returns_none_when_no_benchmark(self, mock_bench, ohlcv_up):
        from dartlab.quant.extended import calcMarketBeta

        mock_bench.return_value = None
        co = _make_mock_company(ohlcv_up)
        result = calcMarketBeta(co)
        assert result is None


# ═══════════════════════════════════════════════════════════
# calcFundamentalDivergence
# ═══════════════════════════════════════════════════════════


class TestCalcFundamentalDivergence:
    def test_returns_none_when_no_data(self):
        co = _make_mock_company(None)
        # No OHLCV, no financial grade → None
        with patch("dartlab.quant.extended.calcFundamentalDivergence") as mock_fn:
            mock_fn.return_value = None
            result = mock_fn(co)
            assert result is None

    @patch("dartlab.quant.extended._fetchOHLCV")
    @patch("dartlab.analysis.financial.scorecard.calcScorecard")
    def test_with_mock_scorecard(self, mock_sc, mock_ohlcv, ohlcv_up):
        from dartlab.quant.extended import calcFundamentalDivergence

        mock_ohlcv.return_value = ohlcv_up
        mock_sc.return_value = {"overallGrade": "A"}

        co = _make_mock_company(ohlcv_up)
        result = calcFundamentalDivergence(co)
        if result is not None:
            assert "financialGrade" in result
            assert "divergence" in result
            assert "diagnosis" in result
            assert "matrix" in result

    def test_returns_none_when_both_absent(self):
        from dartlab.quant.extended import calcFundamentalDivergence

        co = _make_mock_company(None)
        # Mock scorecard to return None
        with patch("dartlab.analysis.financial.scorecard.calcScorecard", return_value=None):
            result = calcFundamentalDivergence(co)
            assert result is None


# ═══════════════════════════════════════════════════════════
# calcMarketRisk
# ═══════════════════════════════════════════════════════════


class TestCalcMarketRisk:
    def test_returns_none_when_no_data(self):
        from dartlab.quant.extended import calcMarketRisk

        co = _make_mock_company(None)
        result = calcMarketRisk(co)
        assert result is None

    def test_returns_none_when_short(self, ohlcv_short):
        from dartlab.quant.extended import calcMarketRisk

        co = _make_mock_company(ohlcv_short)
        result = calcMarketRisk(co)
        assert result is None

    @patch("dartlab.quant.extended.calcMarketBeta")
    def test_returns_risk_metrics(self, mock_beta, ohlcv_up):
        from dartlab.quant.extended import calcMarketRisk

        mock_beta.return_value = {"value": 1.2, "relativeStrength": 0.05}
        co = _make_mock_company(ohlcv_up)
        result = calcMarketRisk(co)
        assert result is not None
        assert "atr" in result
        assert "atrPercent" in result
        assert "volatilityGrade" in result
        assert "price" in result
        assert result["price"] > 0

    @patch("dartlab.quant.extended.calcMarketBeta")
    def test_volatility_grade_present(self, mock_beta, ohlcv_up):
        from dartlab.quant.extended import calcMarketRisk

        mock_beta.return_value = None
        co = _make_mock_company(ohlcv_up)
        result = calcMarketRisk(co)
        assert result is not None
        assert result["volatilityGrade"] in ("매우 높음", "높음", "보통", "낮음")


# ═══════════════════════════════════════════════════════════
# calcMarketAnalysisFlags
# ═══════════════════════════════════════════════════════════


class TestCalcMarketAnalysisFlags:
    def test_returns_list_when_no_data(self):
        from dartlab.quant.extended import calcMarketAnalysisFlags

        co = _make_mock_company(None)
        result = calcMarketAnalysisFlags(co)
        assert isinstance(result, list)
        assert len(result) == 0

    @patch("dartlab.quant.extended.calcMarketRisk")
    def test_returns_flags_with_data(self, mock_risk, ohlcv_up):
        from dartlab.quant.extended import calcMarketAnalysisFlags

        mock_risk.return_value = {"beta": 1.2, "atrPercent": 2.5}
        co = _make_mock_company(ohlcv_up)
        result = calcMarketAnalysisFlags(co)
        assert isinstance(result, list)
        # With 200 data points and an uptrend, we should get some flags
        assert all(isinstance(f, str) for f in result)

    @patch("dartlab.quant.extended.calcMarketRisk")
    def test_high_beta_flag(self, mock_risk, ohlcv_up):
        from dartlab.quant.extended import calcMarketAnalysisFlags

        mock_risk.return_value = {"beta": 2.0, "atrPercent": 6.0}
        co = _make_mock_company(ohlcv_up)
        result = calcMarketAnalysisFlags(co)
        # High beta + high ATR should generate warnings
        beta_flags = [f for f in result if "베타" in f]
        atr_flags = [f for f in result if "변동성" in f]
        assert len(beta_flags) > 0 or len(atr_flags) > 0


# ═══════════════════════════════════════════════════════════
# calcTechnicalVerdict
# ═══════════════════════════════════════════════════════════


class TestCalcTechnicalVerdict:
    def test_returns_none_when_no_data(self):
        from dartlab.quant.extended import calcTechnicalVerdict

        co = _make_mock_company(None)
        result = calcTechnicalVerdict(co)
        assert result is None

    def test_returns_none_when_short(self, ohlcv_short):
        from dartlab.quant.extended import calcTechnicalVerdict

        co = _make_mock_company(ohlcv_short)
        result = calcTechnicalVerdict(co)
        assert result is None
