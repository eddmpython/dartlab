"""드라이버 교란 DCF 시나리오와 reverse-DCF 전시 단위 가드."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit

from dartlab.analysis.valuation._dFVDrivers import buildDriverScenarios, reverseDcfExhibit

_ARGS = {
    "baseFcf": 1_000_000.0,
    "growthRates": [10.0, 8.0, 6.0],
    "terminalGrowth": 2.0,
    "wacc": 9.0,
    "netDebt": 0.0,
    "shares": 1_000.0,
}


class TestBuildDriverScenarios:
    def test_bull_above_base_above_bear(self):
        """WACC 를 낮추고 성장을 올린 쪽이 더 비싸야 한다. 이 순서가 깨지면 교란 방향이 뒤집힌 것이다."""
        out = buildDriverScenarios(**_ARGS)
        assert out is not None
        assert out["bear"] < out["base"] < out["bull"]

    def test_driver_record_matches_perturbation(self):
        out = buildDriverScenarios(**_ARGS, waccDelta=1.5, growthDelta=0.25)
        assert out["drivers"]["bull"]["wacc"] == pytest.approx(7.5)
        assert out["drivers"]["bear"]["wacc"] == pytest.approx(10.5)
        assert out["drivers"]["bull"]["growthMult"] == pytest.approx(1.25)
        assert out["drivers"]["bear"]["growthMult"] == pytest.approx(0.75)
        assert out["drivers"]["base"]["growthMult"] == 1.0

    def test_missing_shares_is_none(self):
        """주식수가 없으면 주당 값이 성립하지 않는다."""
        assert buildDriverScenarios(**{**_ARGS, "shares": None}) is None
        assert buildDriverScenarios(**{**_ARGS, "shares": 0.0}) is None

    def test_bull_wacc_never_sinks_to_terminal_growth(self):
        """WACC 가 영구성장률 이하로 내려가면 터미널 값이 발산한다. 바닥이 있어야 한다."""
        out = buildDriverScenarios(**{**_ARGS, "wacc": 2.6}, waccDelta=5.0)
        assert out is not None
        assert out["bull"] is not None


class _Company:
    """_finance.series 만 가진 최소 stub."""

    def __init__(self, series: dict | None) -> None:
        self._finance = type("Fin", (), {"series": series})()


class TestReverseDcfExhibit:
    def test_no_market_cap_is_none(self):
        c = _Company({"revenue": {"2024": 1.0}})
        assert reverseDcfExhibit(c, waccPct=9.0, fundamentalGrowth=5.0, marketCap=None) is None
        assert reverseDcfExhibit(c, waccPct=9.0, fundamentalGrowth=5.0, marketCap=0.0) is None

    def test_no_series_is_none(self):
        """예전에는 company._series 를 먼저 봤다. 그 이름은 Company 에 없어 늘 건너뛰었다."""
        assert reverseDcfExhibit(_Company(None), waccPct=9.0, fundamentalGrowth=5.0, marketCap=1e12) is None
        assert reverseDcfExhibit(object(), waccPct=9.0, fundamentalGrowth=5.0, marketCap=1e12) is None
