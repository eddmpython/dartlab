"""예측신호(6-2) 축 unit 테스트 — 순수 로직, 데이터 로드 없음."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


# ── import 테스트 ──


def test_predictionSignals_import():
    from dartlab.analysis.financial.predictionSignals import (
        calcDisclosureDelta,
        calcEarningsMomentum,
        calcMacroSensitivity,
        calcPeerPrediction,
        calcPredictionFlags,
        calcPredictionSynthesis,
        calcStructuralBreak,
    )

    assert callable(calcEarningsMomentum)
    assert callable(calcPeerPrediction)
    assert callable(calcStructuralBreak)
    assert callable(calcMacroSensitivity)
    assert callable(calcDisclosureDelta)
    assert callable(calcPredictionSynthesis)
    assert callable(calcPredictionFlags)


# ── 레지스트리 등록 확인 ──


def test_axis_registered():
    from dartlab.analysis.financial import _ALIASES, _AXIS_REGISTRY

    assert "예측신호" in _AXIS_REGISTRY
    entry = _AXIS_REGISTRY["예측신호"]
    assert entry.partId == "6-2"
    assert len(entry.calcs) == 7

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
