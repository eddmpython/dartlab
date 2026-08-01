"""Phase C — macro narrative 12 번째 축 + scenarios delta narrative_signal 테스트.

archive 0 인 환경에서도 graceful empty + axis dispatch + summary 12 축 통합 회귀 가드.
"""

from __future__ import annotations

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def test_analyze_narrative_smoke_empty_archive(monkeypatch) -> None:
    """archive 0 일 (또는 enrichment 미실행) → unavailable + 빈 topicPulse.

    unit 결정성 — buildNarrativePulse 를 빈 결과로 mock 해 archive 부재 경로를 강제한다
    (실 archive auto-download 시 비결정적 score 회귀 가드).
    """
    from dartlab.macro.narrative.narrative import analyzeNarrative

    monkeypatch.setattr(
        "dartlab.synth.narrativePulse.buildNarrativePulse",
        lambda *a, **k: pl.DataFrame(),
    )
    r = analyzeNarrative(market="KR", lookbackDays=7)
    assert r["market"] == "KR"
    assert r["score"] is None
    assert r["label"] is None
    assert r["status"] == "unavailable"
    assert r["observationCount"] == 0
    assert r["topicPulse"] == []
    assert "regimeShift" in r
    assert "similarPastPeriods" in r
    assert set(r["contributions"].keys()) == {"regimeShift", "topicTone", "volumeAnomaly"}


def test_analyze_narrative_with_pulse(monkeypatch: pytest.MonkeyPatch) -> None:
    """pulse fixture → score 계산 + topic top5 + regime shift dict."""
    from datetime import date as _date

    from dartlab.macro.narrative import narrative as narr_mod
    from dartlab.synth import narrativePulse as np_mod

    # mock pulse: 2 토픽 (one bullish, one bearish), 140 헤드라인 — analyzeNarrative 가
    # lazy import 하므로 source 모듈에 patch.
    fake_pulse = pl.DataFrame(
        {
            "date": [_date(2026, 5, 28)] * 4,
            "topic_id": [1, 1, 2, 2],
            "topic_label": ["반도체", "반도체", "금리우려", "금리우려"],
            "sentiment_mean": [0.5, 0.5, -0.6, -0.6],
            "sentiment_std": [0.1, 0.1, 0.1, 0.1],
            "volume": [30, 30, 40, 40],
            "headlines_sample": [["t1"], ["t2"], ["t3"], ["t4"]],
        }
    ).with_columns(pl.col("volume").cast(pl.UInt32))

    monkeypatch.setattr(np_mod, "buildNarrativePulse", lambda *a, **kw: fake_pulse)

    r = narr_mod.analyzeNarrative(market="KR", asOf="2026-05-28", lookbackDays=30)
    assert r["score"] != 0.0
    assert r["status"] == "usable"
    assert r["observationCount"] == 140
    assert len(r["topicPulse"]) == 2
    top_labels = {t["topic_label"] for t in r["topicPulse"]}
    assert top_labels == {"반도체", "금리우려"}


def test_score_narrative_thresholds() -> None:
    """_scoreNarrative 5 분기 임계 검증."""
    from dartlab.macro.summary import _scoreNarrative

    assert _scoreNarrative({"score": -3.5, "label": "극단공포"}) == (-0.7, ["narrative 극단 비관 (극단공포)"])
    assert _scoreNarrative({"score": -1.5, "label": "비관"}) == (-0.4, ["narrative 비관"])
    assert _scoreNarrative({"score": 0.0, "label": "중립"}) == (0.0, [])
    assert _scoreNarrative({"score": 1.5, "label": "낙관"}) == (0.4, ["narrative 낙관"])
    assert _scoreNarrative({"score": 3.5, "label": "극단탐욕"})[0] == -0.2
    assert _scoreNarrative(None) == (0.0, [])


def test_axis_registry_narrative() -> None:
    """macro('내러티브') 한글 별칭 정상 dispatch — registry 등록 회귀 가드."""
    from dartlab.macro import _ALIASES, _AXIS_REGISTRY

    assert "narrative" in _AXIS_REGISTRY
    entry = _AXIS_REGISTRY["narrative"]
    assert entry.fn == "analyzeNarrative"
    assert entry.label == "내러티브"
    assert _ALIASES.get("내러티브") == "narrative"
    assert _ALIASES.get("뉴스내러티브") == "narrative"


def test_scenarios_delta_narrative_signal() -> None:
    """_computeDelta 가 narrative_signal 키 항상 생성 (b/s narrative 없어도 None 유지)."""
    from dartlab.macro.scenarios.engine import _computeDelta

    baseline = {
        "score": 1.0,
        "overall": "neutral",
        "cycle": {"phase": "expansion"},
        "crisis": {"zone": "safe"},
        "sentiment": {"fearGreed": {"score": 55}},
    }
    scenario = {
        "score": -2.0,
        "overall": "unfavorable",
        "cycle": {"phase": "contraction"},
        "crisis": {"zone": "warning"},
        "sentiment": {"fearGreed": {"score": 25}},
    }
    delta = _computeDelta(baseline, scenario)
    assert "narrative_signal" in delta
    ns = delta["narrative_signal"]
    assert set(ns.keys()) == {
        "baseline_score",
        "baseline_label",
        "regime_shift_delta",
        "scenario_score_from_similar",
        "similar_period_cited",
        "topic_pulse_top1",
        "scenario_score",
    }
    assert ns["baseline_score"] is None  # narrative 누락 시 None


def test_scenarios_delta_with_narrative() -> None:
    """baseline narrative 존재 시 narrative_signal 의 값들 채워짐."""
    from dartlab.macro.scenarios.engine import _computeDelta

    baseline = {
        "score": 0.0,
        "overall": "neutral",
        "cycle": {},
        "crisis": {},
        "sentiment": {"fearGreed": {"score": 50}},
        "narrative": {
            "score": -1.2,
            "label": "비관",
            "regimeShift": {"delta": -0.3},
            "topicPulse": [{"topic_label": "금리우려"}],
            "similarPastPeriods": [{"period": "2022-Q3", "score": -1.5, "cosine": 0.87}],
        },
    }
    scenario = {
        "score": -1.0,
        "overall": "neutral",
        "cycle": {},
        "crisis": {},
        "sentiment": {"fearGreed": {"score": 50}},
        "narrative": {"score": -1.2, "label": "비관"},
    }
    delta = _computeDelta(baseline, scenario)
    ns = delta["narrative_signal"]
    assert ns["baseline_score"] == -1.2
    assert ns["baseline_label"] == "비관"
    assert ns["regime_shift_delta"] == -0.3
    assert ns["similar_period_cited"] == "2022-Q3"
    assert ns["scenario_score_from_similar"] == -1.5
    assert ns["topic_pulse_top1"] == "금리우려"


def test_scenarios_delta_keeps_missing_inputs_missing() -> None:
    from dartlab.macro.scenarios.engine import _computeDelta

    delta = _computeDelta({"score": 0}, {"score": 0})

    assert delta["fear_greed"] == {"baseline": None, "scenario": None, "change": None}
    assert delta["historical_risk"] == {"baseline": None, "scenario": None, "changed": False}
