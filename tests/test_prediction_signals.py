"""예측신호(6-2) 축 unit 테스트 — 순수 로직, 데이터 로드 없음."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


# ── import 테스트 ──


def test_predictionSignals_import():
    from dartlab.analysis.financial.predictionSignals import (
        calcAnnouncementTiming,
        calcDisclosureDelta,
        calcEarningsMomentum,
        calcEventImpact,
        calcInventoryDivergence,
        calcMacroRegression,
        calcMacroSensitivity,
        calcPeerPrediction,
        calcPredictionFlags,
        calcPredictionSynthesis,
        calcStructuralBreak,
        calcSupplyChainSignal,
    )

    assert callable(calcEarningsMomentum)
    assert callable(calcPeerPrediction)
    assert callable(calcStructuralBreak)
    assert callable(calcMacroSensitivity)
    assert callable(calcMacroRegression)
    assert callable(calcEventImpact)
    assert callable(calcDisclosureDelta)
    assert callable(calcInventoryDivergence)
    assert callable(calcAnnouncementTiming)
    assert callable(calcSupplyChainSignal)
    assert callable(calcPredictionSynthesis)
    assert callable(calcPredictionFlags)


# ── 레지스트리 등록 확인 ──


def test_axis_registered():
    from dartlab.analysis.financial import _ALIASES, _AXIS_REGISTRY

    assert "예측신호" in _AXIS_REGISTRY
    entry = _AXIS_REGISTRY["예측신호"]
    assert entry.partId == "6-2"
    assert len(entry.calcs) == 12

    # alias
    assert _ALIASES["prediction"] == "예측신호"
    assert _ALIASES["predictionSignals"] == "예측신호"
    assert _ALIASES["전망신호"] == "예측신호"


def test_axis_resolve():
    from dartlab.analysis.financial import _resolveAxis

    assert _resolveAxis("예측신호") == "예측신호"
    assert _resolveAxis("prediction") == "예측신호"
    assert _resolveAxis("전망신호") == "예측신호"


# ── 방향 점수 상수 ──


def test_direction_scores():
    from dartlab.analysis.financial.predictionSignals import _DIRECTION_SCORES

    assert _DIRECTION_SCORES["up"] == 1.0
    assert _DIRECTION_SCORES["down"] == -1.0
    assert _DIRECTION_SCORES["neutral"] == 0.0
    assert _DIRECTION_SCORES["stable"] == 0.0


# ── 매크로 민감도 테이블 ──


def test_sector_macro_map():
    from dartlab.analysis.financial.predictionSignals import _SECTOR_MACRO_MAP

    assert "high" in _SECTOR_MACRO_MAP
    assert "defensive" in _SECTOR_MACRO_MAP
    assert "moderate" in _SECTOR_MACRO_MAP

    # 각 항목에 필수 키가 있는지
    for cyclicality, drivers in _SECTOR_MACRO_MAP.items():
        for d in drivers:
            assert "indicator" in d
            assert "source" in d
            assert "direction" in d


# ── 헬퍼 함수 순수 테스트 ──


def test_avgGrowth():
    from dartlab.analysis.financial.predictionSignals import _avgGrowth

    assert _avgGrowth([100, 110, 121]) == pytest.approx(10.0, abs=0.5)
    assert _avgGrowth([100, 50]) == pytest.approx(-50.0, abs=0.1)
    assert _avgGrowth([100]) is None
    assert _avgGrowth([]) is None


def test_safe():
    from dartlab.analysis.financial.predictionSignals import _safe

    assert _safe(10, 5) == 2.0
    assert _safe(10, 0) is None
    assert _safe(0, 10) == 0.0


# ── forecast/prediction.py 브릿지 ──


def test_collectSignals_accepts_usePredictionAxis():
    """collectSignals가 usePredictionAxis 파라미터를 받는지 확인."""
    import inspect

    from dartlab.analysis.forecast.prediction import collectSignals

    sig = inspect.signature(collectSignals)
    assert "usePredictionAxis" in sig.parameters


def test_contextSignals_fields():
    """ContextSignals에 disclosure 관련 필드가 있는지 확인."""
    from dartlab.analysis.forecast.prediction import ContextSignals

    signals = ContextSignals()
    assert hasattr(signals, "disclosureTone")
    assert hasattr(signals, "disclosureChangeIntensity")
    assert hasattr(signals, "disclosureGrowthAdj")
    assert hasattr(signals, "disclosureConfidence")


# ── Prediction Space ──


def test_predictionSpace_import():
    from dartlab.analysis.forecast.predictionSpace import (
        getPredictionSpace,
    )

    assert callable(getPredictionSpace)


def test_axisState_dataclass():
    from dartlab.analysis.forecast.predictionSpace import AxisState

    ax = AxisState(name="test", label="테스트", level=0.5, direction="improving", momentum=0.3, confidence="high")
    assert ax.level == 0.5
    assert ax.direction == "improving"


def test_predictionSpace_impactOn():
    from dartlab.analysis.forecast.predictionSpace import AxisState, PredictionSpace

    space = PredictionSpace(
        axes={
            "businessCycle": AxisState("businessCycle", "경기축", 0.5, "improving", 0.3, "high"),
            "fxRate": AxisState("fxRate", "환율축", -0.3, "deteriorating", -0.2, "medium"),
        },
        timestamp="2026-03-30",
        dataFreshness="fresh",
    )
    impact = space.impactOn("반도체")
    assert "businessCycle" in impact
    assert "fxRate" in impact
    # 반도체: revenueToGdp=1.8, level=0.5 → 0.5*1.8*3.0=2.7
    assert impact["businessCycle"] == pytest.approx(2.7, abs=0.1)


def test_predictionSpace_summary():
    from dartlab.analysis.forecast.predictionSpace import AxisState, PredictionSpace

    space = PredictionSpace(
        axes={"businessCycle": AxisState("businessCycle", "경기축", 0.5, "improving", 0.3, "high")},
        timestamp="2026-03-30",
        dataFreshness="fresh",
    )
    s = space.summary()
    assert "axes" in s
    assert s["axes"]["businessCycle"]["state"] == "expansion"
    assert s["axes"]["businessCycle"]["level"] == 0.5


def test_normalize_functions():
    from dartlab.analysis.forecast.predictionSpace import (
        _clamp,
        _normalizeIndex,
        _normalizeZscore,
    )

    assert _clamp(2.0) == 1.0
    assert _clamp(-2.0) == -1.0
    assert _clamp(0.5) == 0.5

    # CLI=110 → (110-100)/20 = 0.5
    assert _normalizeIndex([110]) == pytest.approx(0.5, abs=0.01)
    # CLI=80 → (80-100)/20 = -1.0
    assert _normalizeIndex([80]) == pytest.approx(-1.0, abs=0.01)

    # zscore: 값이 부족하면 0
    assert _normalizeZscore([1, 2, 3]) == 0.0


def test_computeDirection():
    from dartlab.analysis.forecast.predictionSpace import _computeDirection

    # 상승 추세
    direction, momentum = _computeDirection([100, 102, 105])
    assert direction == "improving"
    assert momentum > 0

    # 하락 추세
    direction, momentum = _computeDirection([105, 102, 100])
    assert direction == "deteriorating"
    assert momentum < 0
