"""expectationSpec 계약·채점 순수수학 단위 테스트 (순수 unit, 네트워크·Company 무접촉).

검증:
- 계약 가드: 분위 결손/비단조 raise, direction prob 범위 raise, 미지 kind raise.
- 채점 골든값: pinball(독립 손계산 0.14) · PIT(중앙 0.5, 클램프 0.01/0.99) · Brier 0.09.
- scoreExpectation: coverage/skill(가장 센 baseline 대비)·실패 봉인(error 행).
- aggregateCalibration: minN 미달 verified=False 강제, error 행 분모 정직성.
"""

from __future__ import annotations

import pytest

from dartlab.synth.expectationSpec import (
    ExpectationSpec,
    aggregateCalibration,
    buildExpectationId,
    pinballLoss,
    pitValue,
    scoreExpectation,
)

Q = {5: 1.0, 25: 2.0, 50: 3.0, 75: 4.0, 95: 5.0}


def makeSpec(**kw) -> ExpectationSpec:
    base = dict(
        expectationId="macro.KR.TEST.M1@20260703T0900",
        domain="macro",
        variable="KR.TEST",
        unit="level",
        freq="M",
        horizon=1,
        targetPeriod="2026-08",
        issuedAt="2026-07-03T09:00",
        issuedLive=False,
        asOf="2026-07-03",
        engine="macro.simulate.simulateMacro",
        engineVersion="bvar-v1",
        kind="quantiles",
        quantiles=dict(Q),
    )
    base.update(kw)
    return ExpectationSpec(**base)


class TestContractGuards:
    def test_missing_quantile_raises(self):
        with pytest.raises(ValueError, match="5점"):
            makeSpec(quantiles={5: 1.0, 25: 2.0, 50: 3.0, 75: 4.0})

    def test_non_monotone_quantiles_raise(self):
        with pytest.raises(ValueError, match="비단조"):
            makeSpec(quantiles={5: 5.0, 25: 4.0, 50: 3.0, 75: 2.0, 95: 1.0})

    def test_direction_prob_out_of_range_raises(self):
        with pytest.raises(ValueError, match="0~1"):
            makeSpec(kind="direction", quantiles=None, direction={"prob": 1.7, "predicted": "up"})

    def test_unknown_kind_raises(self):
        with pytest.raises(ValueError, match="kind"):
            makeSpec(kind="point")

    def test_frozen_immutable(self):
        spec = makeSpec()
        with pytest.raises(AttributeError):
            spec.quantiles = {}  # type: ignore[misc]


class TestScoringGolden:
    def test_pinball_hand_computed(self):
        # 손계산: (0.05*2 + 0.25*1 + 0 + 0.25*1 + 0.05*2)/5 = 0.14
        assert pinballLoss(Q, 3.0) == pytest.approx(0.14)

    def test_pit_median_and_clamps(self):
        assert pitValue(Q, 3.0) == pytest.approx(0.5)
        assert pitValue(Q, 0.0) == 0.01
        assert pitValue(Q, 9.0) == 0.99

    def test_direction_brier(self):
        spec = makeSpec(kind="direction", quantiles=None, direction={"prob": 0.7, "predicted": "up"})
        s = scoreExpectation(spec, "up", scoredAt="2026-10-01T00:00", actualAsOf="2026-10-01")
        assert s.brier == pytest.approx(0.09)

    def test_expectation_id_format(self):
        eid = buildExpectationId("macro", "KR.CPI", "M", 3, "2026-07-03T09:00")
        assert eid == "macro.KR.CPI.M3@20260703T0900"


class TestScoreExpectation:
    def test_coverage_and_skill_vs_strongest_baseline(self):
        spec = makeSpec(
            baselines={
                "randomWalk": {5: -1.0, 25: 1.0, 50: 3.0, 75: 5.0, 95: 7.0},  # 넓은 분포
                "seasonalNaive": 3.5,  # 점 baseline (더 셈)
            }
        )
        s = scoreExpectation(spec, 3.0, scoredAt="t", actualAsOf="d")
        assert s.coverageHit90 is True and s.coverageHit50 is True
        strongest = min(s.crpsBaseline.values())
        # 손계산: randomWalk pinball = (0.05*4+0.25*2+0+0.25*2+0.05*4)/5 = 0.28 < seasonal 0.5
        assert strongest == pytest.approx(0.28)
        assert s.skill == pytest.approx(1.0 - s.crps / strongest)

    def test_actual_none_seals_error_row(self):
        s = scoreExpectation(makeSpec(), None, scoredAt="t", actualAsOf="d")
        assert s.error is not None and s.crps is None and s.actual is None


class TestAggregate:
    def test_min_n_forces_unverified(self):
        spec = makeSpec()
        scores = [scoreExpectation(spec, 3.0, scoredAt="t", actualAsOf="d") for _ in range(5)]
        agg = aggregateCalibration(scores, minN=24)
        assert agg["n"] == 5 and agg["verified"] is False

    def test_error_rows_counted_not_dropped_silently(self):
        spec = makeSpec()
        scores = [
            scoreExpectation(spec, 3.0, scoredAt="t", actualAsOf="d"),
            scoreExpectation(spec, None, scoredAt="t", actualAsOf="d"),
        ]
        agg = aggregateCalibration(scores, minN=1)
        assert agg["n"] == 1 and agg["errorRows"] == 1 and agg["verified"] is True

    def test_empty_returns_unverified(self):
        assert aggregateCalibration([])["verified"] is False
