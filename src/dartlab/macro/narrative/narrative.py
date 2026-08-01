"""macro 12 번째 축 — news narrative pulse 분석 (Phase C).

newsHeadlines archive → narrativePulse → narrative score (-4~+4) + label + topic
pulse + regime shift + similar past periods. analyzeSummary 의 12 축 통합 입력 +
scenarios.runScenario 의 narrative_signal 계산 base.
"""

from __future__ import annotations

import logging
from datetime import date as _date
from datetime import timedelta

log = logging.getLogger(__name__)


def _scoreFromMean(mean: float, volume: int) -> tuple[float, str]:
    """sentiment 평균 + volume → narrative score(-4~+4) + label.

    Sig: ``_scoreFromMean(mean, volume) -> (score, label)``

    Capabilities: 평균 sentiment 구간별 정규화 + volume 부족 시 신호 약화.
    AIContext: analyzeNarrative 의 score 정규화 헬퍼.
    Guide: volume < 50 이면 score 50% 감쇠 (작은 표본 신호 신뢰성 ↓).
    When: analyzeNarrative.
    How: mean 구간 매칭 + volume 가중.

    Args:
        mean: sentiment 평균 (-1~+1).
        volume: lookback 기간 총 headline 수.

    Returns:
        (score: -4~+4, label: 극단공포/비관/중립/낙관/극단탐욕).

    Raises:
        없음.

    Example::

        _scoreFromMean(-0.6, 200)  # → (-2.5, "비관")

    Requires:
        없음.

    See Also:
        ``analyzeNarrative``: caller.
    """
    score = mean * 4.0  # mean ∈ [-1, +1] → score ∈ [-4, +4]
    if volume < 50:
        score *= 0.5
    if score <= -3:
        label = "극단공포"
    elif score <= -1:
        label = "비관"
    elif score >= 3:
        label = "극단탐욕"
    elif score >= 1:
        label = "낙관"
    else:
        label = "중립"
    return round(score, 2), label


def analyzeNarrative(
    market: str = "KR",
    asOf: str | _date | None = None,
    *,
    lookbackDays: int = 30,
    overrides: dict | None = None,
    sentimentModel: str = "auto",
) -> dict:
    """news narrative 분석 — 12 번째 macro 축 (Phase C).

    Capabilities:
        - lookback 30 일 news headline pulse 계산
        - 평균 sentiment + topic 분포 + regime shift (7d vs 30d) + similar past period
        - 결과 dict 표준 — score(-4~+4) + label + topicPulse top5 + regimeShift + contributions
        - asOf 관측/수집일 cutoff (원천 revision vintage를 재현하는 PIT 계약은 아님)
        - archive 0 일 또는 enrichment 미실행 시 unavailable 결과

    AIContext:
        analyzeSummary 11 → 12 축 통합 단일 진입점. scenarios.runScenario 의
        narrative_signal 계산 baseline 도 본 함수 호출 후 similarPastPeriods 활용.

    Guide:
        lookback 7~30 일이 narrative 의 의미 단위. 90 일 이상은 regime 평균화로 신호 약화.
        overrides 는 macro 변수 강제용 — narrative 는 *과거 데이터 기반*이라 override 무시
        (overrides=None 동일 결과). 시나리오에선 similarPastPeriods 인용으로 우회.

    When:
        - dartlab.macro("내러티브") 진입점
        - analyzeSummary for-loop 의 12 번째 entry
        - scenarios runScenario baseline 계산

    How:
        buildNarrativePulse → group_by topic → top 5 + sentiment mean + std
        → _scoreFromMean 정규화 → regime shift 비교 → similar past periods
        embedding NN (Phase B 누적 ≥ 90 일 시 실효, 그 전엔 빈 리스트).

    Args:
        market: "KR" | "US".
        asOf: 분석 기준일. None 이면 오늘.
        lookbackDays: 30 일 (기본).
        overrides: scenarios 호환 (현재 narrative 는 무시).
        sentimentModel: "auto" 또는 "lm_dict".

    Returns:
        dict — market/asOf/lookbackDays/score/label/topicPulse/regimeShift/
        similarPastPeriods/contributions.

    Raises:
        없음.

    Example::

        r = analyzeNarrative(market="KR")
        # → {"score": -1.2, "label": "비관", "topicPulse": [...top5], ...}

    Requires:
        Phase A archive (newsHeadlines) + Phase B enrichment (narrativePulse).
        archive 미존재 시 status="unavailable" + score/label=None + empty pulse 반환.

    See Also:
        ``dartlab.synth.narrativePulse.buildNarrativePulse``: 입력 SSOT.
        ``dartlab.macro.summary.analyzeSummary``: 12 축 통합 caller.
        ``dartlab.macro.scenarios.engine._computeDelta``: narrative_signal 계산.

    LLM Specifications:
        Inputs: market(str), asOf(str|None), lookbackDays(int), sentimentModel(str).
        Outputs: dict 9 키 (위 Returns).
        Errors: 없음 (graceful empty).
        Side effects: 없음 (read-only).
        Cost: O(lookback_days × archive_per_day) ≈ 1 초 (mmap parquet).
        Determinism: same inputs → same outputs (asOf 고정 시).
    """
    from dartlab.synth.narrativePulse import buildNarrativePulse

    # asOf 가 명시되면 관측/수집일 cutoff. 원천 revision vintage를 재현하는 PIT 필터는 아니다.
    asof_explicit = asOf is not None
    asof_date = _date.fromisoformat(asOf) if isinstance(asOf, str) else (asOf or _date.today())
    start = (asof_date - timedelta(days=lookbackDays)).isoformat()
    end = asof_date.isoformat()

    empty_result = {
        "market": market.upper(),
        "asOf": end,
        "lookbackDays": lookbackDays,
        "score": None,
        "label": None,
        "topicPulse": [],
        "regimeShift": {"sentiment_7d": None, "sentiment_30d": None, "delta": None, "label": None},
        "similarPastPeriods": [],
        "contributions": {"regimeShift": None, "topicTone": None, "volumeAnomaly": None},
        "status": "unavailable",
        "observationCount": 0,
    }

    try:
        pulse = buildNarrativePulse(
            start,
            end,
            market,
            asof=asof_date if asof_explicit else None,
            sentimentModel=sentimentModel,
        )
    except Exception as exc:
        log.warning("buildNarrativePulse 실패: %s — narrative 빈 결과", exc)
        return empty_result

    if pulse.is_empty():
        return empty_result

    # 전체 평균 + volume
    import polars as pl

    overall_mean = float(pulse["sentiment_mean"].mean() or 0.0)
    total_volume = int(pulse["volume"].sum() or 0)
    score, label = _scoreFromMean(overall_mean, total_volume)

    # top 5 topic by volume
    top_topics = (
        pulse.group_by(["topic_id", "topic_label"])
        .agg(
            pl.col("sentiment_mean").mean().alias("sentiment_mean"),
            pl.col("volume").sum().alias("volume"),
        )
        .sort("volume", descending=True)
        .head(5)
    )
    topic_pulse = []
    for row in top_topics.iter_rows(named=True):
        topic_pulse.append(
            {
                "topic_label": row["topic_label"],
                "sentiment_mean": round(float(row["sentiment_mean"]), 3),
                "volume": int(row["volume"]),
                "weight": round(float(row["volume"]) / max(total_volume, 1), 3),
            }
        )

    # regime shift — 7d vs 30d
    asof_iso = asof_date.isoformat()
    cutoff_7d = (asof_date - timedelta(days=7)).isoformat()
    pulse_30 = pulse.filter(pl.col("date") <= pl.lit(asof_iso).str.to_date())
    pulse_7 = pulse.filter(pl.col("date") >= pl.lit(cutoff_7d).str.to_date())
    mean_30 = float(pulse_30["sentiment_mean"].mean() or 0.0)
    mean_7 = float(pulse_7["sentiment_mean"].mean() or 0.0)
    delta = mean_7 - mean_30
    if delta <= -0.2:
        regime_label = "악화"
    elif delta >= 0.2:
        regime_label = "개선"
    else:
        regime_label = "안정"

    # contributions
    regime_contrib = round(delta * 1.5, 3)  # |0.4| → ±0.6
    tone_contrib = round(overall_mean * 1.5, 3)
    volume_contrib = 0.0 if total_volume >= 300 else round((300 - total_volume) / 300 * -0.3, 3)

    return {
        "market": market.upper(),
        "asOf": end,
        "lookbackDays": lookbackDays,
        "score": score,
        "label": label,
        "topicPulse": topic_pulse,
        "regimeShift": {
            "sentiment_7d": round(mean_7, 3),
            "sentiment_30d": round(mean_30, 3),
            "delta": round(delta, 3),
            "label": regime_label,
        },
        "similarPastPeriods": [],  # Phase B archive ≥ 90 일 후 embedding NN 활성
        "contributions": {
            "regimeShift": regime_contrib,
            "topicTone": tone_contrib,
            "volumeAnomaly": volume_contrib,
        },
        "status": "usable",
        "observationCount": total_volume,
    }
