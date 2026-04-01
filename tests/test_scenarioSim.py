"""scenarioSim 단위 테스트.

시나리오 시뮬레이터의 핵심 로직을 검증한다.
Company 로드 필요 → requires_data 마커.
"""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.requires_data]


@pytest.fixture(scope="module")
def samsung():
    from dartlab import Company

    return Company("005930")


class TestCreateSimulation:
    """시뮬레이션 생성 테스트."""

    def test_basic_creation(self, samsung):
        from dartlab.analysis.forecast.scenarioSim import createSimulation

        sim = createSimulation(
            samsung,
            "테스트",
            revenueGrowth=10.0,
            baseYear="2023",
            targetYear="2024",
        )
        assert sim.stockCode == "005930"
        assert sim.scenarioName == "테스트"
        assert "base" in sim.proformaResults
        assert "bull" in sim.proformaResults
        assert "bear" in sim.proformaResults

    def test_quarterly_targets_sum_to_annual(self, samsung):
        from dartlab.analysis.forecast.scenarioSim import createSimulation

        sim = createSimulation(
            samsung,
            "합산검증",
            revenueGrowth=15.0,
            baseYear="2023",
            targetYear="2024",
        )
        baseP = sim.proformaResults["base"].projections[0]
        qSum = sum(sim.quarterlyRevTargets["base"])
        # 분기 합산 = 연간 ProForma (소수점 오차 허용)
        assert abs(qSum - baseP.revenue) / baseP.revenue < 0.001

    def test_seasonality_sums_to_one(self, samsung):
        from dartlab.analysis.forecast.scenarioSim import createSimulation

        sim = createSimulation(
            samsung,
            "계절성",
            revenueGrowth=10.0,
            baseYear="2023",
            targetYear="2024",
        )
        assert abs(sum(sim.revSeasonality) - 1.0) < 0.01
        assert abs(sum(sim.oiSeasonality) - 1.0) < 0.01

    def test_dcf_no_reversal(self, samsung):
        """Bull ≥ Base ≥ Bear DCF 적정가."""
        from dartlab.analysis.forecast.scenarioSim import createSimulation

        sim = createSimulation(
            samsung,
            "DCF검증",
            revenueGrowth=15.0,
            baseYear="2023",
            targetYear="2024",
            shares=5969782550,
        )
        if sim.dcfPerShare:
            assert sim.dcfPerShare.get("bull", 0) >= sim.dcfPerShare.get("base", 0)
            assert sim.dcfPerShare.get("base", 0) >= sim.dcfPerShare.get("bear", 0)

    def test_growth_path_from_float(self, samsung):
        """float 입력 → 3년 수렴 경로 자동 생성."""
        from dartlab.analysis.forecast.scenarioSim import createSimulation

        sim = createSimulation(
            samsung,
            "수렴",
            revenueGrowth=20.0,
            baseYear="2023",
            targetYear="2024",
        )
        assert len(sim.revenueGrowthPath) == 3
        # 수렴: [20, 14, 10]
        assert sim.revenueGrowthPath[0] > sim.revenueGrowthPath[1] > sim.revenueGrowthPath[2]


class TestJudgeQuarter:
    """분기 판정 테스트."""

    def test_on_track_judgment(self, samsung):
        from dartlab.analysis.forecast.scenarioSim import createSimulation, judgeQuarter

        sim = createSimulation(
            samsung,
            "판정",
            revenueGrowth=15.0,
            baseYear="2023",
            targetYear="2024",
        )
        baseQ1 = sim.quarterlyRevTargets["base"][0]
        baseOIQ1 = sim.quarterlyOITargets["base"][0]

        # base 목표와 동일한 실적 → on_track
        j = judgeQuarter(sim, "2024Q1", baseQ1, baseOIQ1)
        assert j.revPath == "on_track"
        assert j.oiPath == "on_track"
        assert "보유" in j.action

    def test_outperform_judgment(self, samsung):
        from dartlab.analysis.forecast.scenarioSim import createSimulation, judgeQuarter

        sim = createSimulation(
            samsung,
            "상회",
            revenueGrowth=15.0,
            baseYear="2023",
            targetYear="2024",
        )
        bullQ1 = sim.quarterlyRevTargets["bull"][0]
        bullOIQ1 = sim.quarterlyOITargets["bull"][0]

        j = judgeQuarter(sim, "2024Q1", bullQ1 * 1.1, bullOIQ1 * 1.1)
        assert j.revPath == "outperform"

    def test_reforecast_included(self, samsung):
        from dartlab.analysis.forecast.scenarioSim import createSimulation, judgeQuarter

        sim = createSimulation(
            samsung,
            "재예측",
            revenueGrowth=15.0,
            baseYear="2023",
            targetYear="2024",
        )
        baseQ1 = sim.quarterlyRevTargets["base"][0]
        baseOIQ1 = sim.quarterlyOITargets["base"][0]

        j = judgeQuarter(sim, "2024Q1", baseQ1, baseOIQ1)
        assert j.reforecastRevenue > 0
        assert j.reforecastOI != 0  # 양수 또는 음수 가능

    def test_consecutive_underperform_action(self, samsung):
        """2분기 연속 하회 → 비중축소 검토."""
        from dartlab.analysis.forecast.scenarioSim import createSimulation, judgeQuarter

        sim = createSimulation(
            samsung,
            "연속하회",
            revenueGrowth=15.0,
            baseYear="2023",
            targetYear="2024",
        )
        bearQ = sim.quarterlyRevTargets.get("bear", [0] * 4)
        bearOI = sim.quarterlyOITargets.get("bear", [0] * 4)

        # Q1, Q2 모두 bear 이하
        judgeQuarter(sim, "2024Q1", bearQ[0] * 0.8, bearOI[0] * 0.8)
        j2 = judgeQuarter(sim, "2024Q2", bearQ[1] * 0.8, bearOI[1] * 0.8)
        assert "축소" in j2.action
