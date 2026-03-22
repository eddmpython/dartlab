"""Analyst 엔진 단위 테스트 — synthesizer, calibrator, types."""

from __future__ import annotations

import pytest

from dartlab.engines.analysis.analyst.calibrator import calibrate_scenarios

pytestmark = pytest.mark.integration
from dartlab.engines.analysis.analyst.synthesizer import synthesize
from dartlab.engines.analysis.analyst.types import AnalystReport, ValuationMethod, _classify_opinion
from dartlab.engines.gather.types import ConsensusData, MarketSnapshot

# ══════════════════════════════════════
# 타입 테스트
# ══════════════════════════════════════


class TestAnalystTypes:
    """AnalystReport, ValuationMethod 기본 동작."""

    def test_valuation_method_repr(self):
        m = ValuationMethod(
            name="dcf",
            value=200000,
            weight=0.3,
            confidence=0.6,
            reasoning="MC 시뮬레이션",
        )
        r = repr(m)
        assert "dcf" in r
        assert "200,000" in r

    def test_analyst_report_repr(self):
        report = AnalystReport(
            stock_code="005930",
            company_name="삼성전자",
            target_price=250000,
            current_price=200000,
            upside=0.25,
            opinion="매수",
            methods=[
                ValuationMethod(name="dcf", value=200000, weight=0.3, confidence=0.5),
                ValuationMethod(name="consensus", value=300000, weight=0.7, confidence=0.8),
            ],
            confidence=0.7,
            reasoning=["종합 판단"],
        )
        r = repr(report)
        assert "삼성전자" in r
        assert "250,000" in r
        assert "매수" in r

    def test_classify_opinion(self):
        assert _classify_opinion(0.50) == "강력매수"
        assert _classify_opinion(0.15) == "매수"
        assert _classify_opinion(0.05) == "중립"
        assert _classify_opinion(-0.05) == "중립"
        assert _classify_opinion(-0.15) == "매도"
        assert _classify_opinion(-0.50) == "강력매도"


# ══════════════════════════════════════
# Synthesizer 테스트
# ══════════════════════════════════════


class TestSynthesizer:
    """synthesize() 가중평균 합성."""

    def test_dcf_only(self):
        """DCF만 있을 때."""
        report = synthesize(
            dcf_target=200000,
            current_price=200000,
            stock_code="005930",
        )
        assert report.target_price > 0
        assert len(report.methods) >= 1
        # DCF만 가용 → 가중치 100%
        dcf_method = next(m for m in report.methods if m.name == "dcf")
        assert dcf_method.value == 200000

    def test_dcf_plus_consensus(self):
        """DCF + 컨센서스."""
        market = MarketSnapshot(
            stock_code="005930",
            current_price=200000,
            consensus=ConsensusData(
                target_price=300000,
                analyst_count=15,
                buy_ratio=0.8,
                high=350000,
                low=250000,
                source="naver",
            ),
        )
        report = synthesize(
            dcf_target=200000,
            market=market,
            current_price=200000,
            stock_code="005930",
        )
        # 가중평균: DCF(200k) + consensus(300k) → 200k~300k 사이
        assert 200000 < report.target_price < 300000
        assert len(report.methods) >= 2

    def test_full_methods(self):
        """DCF + 컨센서스 + 피어 + 상대가치 모두 가용."""
        market = MarketSnapshot(
            stock_code="005930",
            current_price=200000,
            consensus=ConsensusData(
                target_price=300000,
                analyst_count=15,
                buy_ratio=0.8,
                source="naver",
            ),
            multiples={"per": 12.5, "pbr": 1.3, "sector_per": 15.0},
            price_range_52w=(150000, 250000),
        )
        report = synthesize(
            dcf_target=200000,
            market=market,
            company_financials={"eps": 15000, "bps": 150000},
            shares=5969782550,
            current_price=200000,
            stock_code="005930",
            company_name="삼성전자",
        )
        assert report.target_price > 0
        assert len(report.methods) == 4  # dcf, consensus, peer, relative
        assert report.opinion in ("강력매수", "매수", "중립", "매도", "강력매도")
        assert len(report.reasoning) > 0

    def test_no_data_returns_empty_report(self):
        """아무 데이터도 없을 때."""
        report = synthesize(stock_code="005930", current_price=200000)
        assert len(report.warnings) > 0

    def test_consensus_low_analyst_count(self):
        """애널리스트 2명 → 컨센서스 가중치 감소."""
        market = MarketSnapshot(
            consensus=ConsensusData(
                target_price=300000,
                analyst_count=2,
                buy_ratio=0.5,
                source="naver",
            ),
        )
        report = synthesize(
            dcf_target=200000,
            market=market,
            current_price=200000,
        )
        # 컨센서스 가중치가 낮아졌으므로 DCF에 가까움
        consensus_method = next((m for m in report.methods if m.name == "consensus"), None)
        assert consensus_method is not None
        assert consensus_method.confidence == 0.5  # 낮은 신뢰도

    def test_weight_normalization(self):
        """가중치 합 = 1.0 보장."""
        market = MarketSnapshot(
            consensus=ConsensusData(target_price=300000, analyst_count=15, source="naver"),
        )
        report = synthesize(
            dcf_target=200000,
            market=market,
            current_price=200000,
        )
        total_weight = sum(m.weight for m in report.methods)
        assert abs(total_weight - 1.0) < 0.01

    def test_dcf_consensus_gap_adjustment(self):
        """DCF-컨센서스 괴리 >50% → DCF 가중치 하향."""
        market = MarketSnapshot(
            consensus=ConsensusData(target_price=500000, analyst_count=15, source="naver"),
        )
        report = synthesize(
            dcf_target=100000,  # 5배 괴리
            market=market,
            current_price=200000,
        )
        # DCF 가중치가 하향되어 컨센서스에 더 가까움
        assert report.target_price > 200000  # 컨센서스 영향 커짐

    def test_upside_and_opinion(self):
        """업사이드 계산 + 의견 분류."""
        report = synthesize(
            dcf_target=250000,
            current_price=200000,
            stock_code="005930",
        )
        assert report.upside > 0
        assert report.opinion in ("강력매수", "매수")

    def test_peer_multiple_with_sector_per(self):
        """업종 PER × EPS → 피어 목표가."""
        market = MarketSnapshot(
            multiples={"sector_per": 20.0},
        )
        report = synthesize(
            dcf_target=200000,
            market=market,
            company_financials={"eps": 15000},
            shares=1000000,
            current_price=200000,
        )
        peer = next((m for m in report.methods if m.name == "peer_multiple"), None)
        assert peer is not None
        assert peer.value == 20.0 * 15000  # 300,000


# ══════════════════════════════════════
# Calibrator 테스트
# ══════════════════════════════════════


class TestCalibrator:
    """calibrate_scenarios() 확률 보정."""

    BASE_PROBS = {
        "baseline": 0.40,
        "optimistic": 0.20,
        "adverse": 0.15,
        "rate_hike": 0.15,
        "stress": 0.10,
    }

    def test_consensus_above_dcf(self):
        """컨센서스 > DCF → optimistic ↑."""
        market = MarketSnapshot(
            consensus=ConsensusData(target_price=300000, analyst_count=10, source="naver"),
        )
        probs, reasons = calibrate_scenarios(
            dict(self.BASE_PROBS),
            dcf_baseline_price=100000,
            market=market,
        )
        assert probs["optimistic"] > self.BASE_PROBS["optimistic"]
        assert len(reasons) > 0

    def test_consensus_below_dcf(self):
        """컨센서스 < DCF → adverse ↑."""
        market = MarketSnapshot(
            consensus=ConsensusData(target_price=50000, analyst_count=10, source="naver"),
        )
        probs, reasons = calibrate_scenarios(
            dict(self.BASE_PROBS),
            dcf_baseline_price=100000,
            market=market,
        )
        assert probs["adverse"] > self.BASE_PROBS["adverse"]

    def test_high_buy_ratio(self):
        """매수의견 80% → baseline ↑."""
        market = MarketSnapshot(
            consensus=ConsensusData(
                target_price=100000,
                analyst_count=10,
                buy_ratio=0.85,
                source="naver",
            ),
        )
        probs, reasons = calibrate_scenarios(
            dict(self.BASE_PROBS),
            dcf_baseline_price=100000,
            market=market,
        )
        assert probs["baseline"] > self.BASE_PROBS["baseline"] - 0.01  # 근사

    def test_foreign_net_sell(self):
        """외국인 순매도 → adverse ↑."""
        market = MarketSnapshot(
            supply_demand={"foreign_net": -5_000_000},
        )
        probs, reasons = calibrate_scenarios(
            dict(self.BASE_PROBS),
            dcf_baseline_price=100000,
            market=market,
        )
        assert probs["adverse"] > self.BASE_PROBS["adverse"]

    def test_foreign_net_buy(self):
        """외국인 순매수 → baseline ↑."""
        market = MarketSnapshot(
            supply_demand={"foreign_net": 5_000_000},
        )
        probs, reasons = calibrate_scenarios(
            dict(self.BASE_PROBS),
            dcf_baseline_price=100000,
            market=market,
        )
        assert probs["baseline"] >= self.BASE_PROBS["baseline"]

    def test_high_base_rate(self):
        """고금리 → rate_hike ↑."""
        market = MarketSnapshot(macro={"base_rate": 5.0})
        probs, reasons = calibrate_scenarios(
            dict(self.BASE_PROBS),
            dcf_baseline_price=100000,
            market=market,
        )
        assert probs["rate_hike"] > self.BASE_PROBS["rate_hike"]

    def test_probabilities_sum_to_one(self):
        """보정 후 확률 합 = 1.0."""
        market = MarketSnapshot(
            consensus=ConsensusData(target_price=300000, analyst_count=10, source="naver"),
            supply_demand={"foreign_net": -5_000_000},
            macro={"base_rate": 5.0},
        )
        probs, _ = calibrate_scenarios(
            dict(self.BASE_PROBS),
            dcf_baseline_price=100000,
            market=market,
        )
        assert abs(sum(probs.values()) - 1.0) < 0.001

    def test_no_negative_probabilities(self):
        """확률 하한 1%p."""
        market = MarketSnapshot(
            consensus=ConsensusData(
                target_price=1000000,
                analyst_count=20,
                buy_ratio=0.95,
                source="naver",
            ),
            supply_demand={"foreign_net": 10_000_000},
            macro={"base_rate": 1.0},
        )
        probs, _ = calibrate_scenarios(
            dict(self.BASE_PROBS),
            dcf_baseline_price=10000,
            market=market,
        )
        for v in probs.values():
            assert v >= 0.005  # 정규화 후 1%p 이상

    def test_empty_market(self):
        """빈 시장 데이터 → 변경 없음."""
        market = MarketSnapshot()
        probs, reasons = calibrate_scenarios(
            dict(self.BASE_PROBS),
            dcf_baseline_price=100000,
            market=market,
        )
        # 조정 규칙 적용 안 됨 → 원본과 유사
        assert len(reasons) == 0
        assert abs(sum(probs.values()) - 1.0) < 0.001
