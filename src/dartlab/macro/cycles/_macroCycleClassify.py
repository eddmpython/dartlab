"""매크로 사이클 판별 — classifyCycle + CYCLE_SECTOR_MAP.

8 지표 (HY/Term/VIX/Gold/CLI/CPI/BEI/CPI_yoy) 가중 투표로 사이클 4 국면 판정 + 국면별
섹터 전략 매핑. macroCycle.py god module 분리.
"""

from __future__ import annotations

import math

from dartlab.macro.cycles._macroCycleStats import _normCdf
from dartlab.macro.cycles._macroCycleTypes import PHASE_LABELS, CyclePhase

# ══════════════════════════════════════
# 사이클 판별
# ══════════════════════════════════════

# 사이클별 섹터 전략 (SectorElasticity.cyclicality 기반)
# 실험 109-02 결과: 회복기/둔화기에서 실효성 확인
CYCLE_SECTOR_MAP: dict[str, dict[str, str]] = {
    "contraction": {
        "defensive": "neutral",  # 침체기엔 전부 하락, 차이 미미
        "moderate": "neutral",
        "high": "underweight",
        "low": "neutral",
    },
    "recovery": {
        "high": "overweight",  # +51%p 초과수익 (실험 검증)
        "moderate": "overweight",
        "defensive": "neutral",
        "low": "neutral",
    },
    "expansion": {
        "high": "overweight",
        "moderate": "overweight",
        "defensive": "neutral",
        "low": "neutral",
    },
    "slowdown": {
        "defensive": "overweight",  # -7.4%p 방어 (실험 검증)
        "moderate": "neutral",
        "high": "underweight",
        "low": "neutral",
    },
}


def classifyCycle(indicators: dict[str, float | None]) -> CyclePhase:
    """매크로 8 지표 → 경제 사이클 4국면 판별 (가중 투표).

    Capabilities:
        HY 스프레드 + Term 스프레드 + VIX + 금 YoY + CLI 모멘텀 + CPI/BEI 등
        8 지표를 가중치로 합산하여 4 국면 (contraction/recovery/expansion/
        slowdown) 중 하나를 선택. macro/summary 의 cycle 축이 직접 호출.

    Args:
        indicators: 매크로 지표 dict. 지원 키:
            - ``hy_spread``: HY 스프레드 (bp)
            - ``term_spread``: 10Y-2Y 스프레드 (%)
            - ``vix``: CBOE VIX
            - ``gold_yoy``: 금 YoY (%)
            - ``cli_mom``: 경기선행지수 전월비
            - ``hy_spread_3m_change``: HY 3M 변화 (bp)
            - ``cpi_yoy``: CPI YoY (%)
            - ``bei_10y``: 10Y BEI (%)
            모든 키 옵션. None 값은 해당 지표 무시.

    Returns:
        CyclePhase dataclass:
            - ``phase`` (str): ``"contraction"``/``"recovery"``/``"expansion"``/``"slowdown"``
            - ``phaseLabel`` (str): 한국어
            - ``confidence`` (str): ``"high"``/``"medium"``/``"low"`` (top - 2nd 차이)
            - ``signals`` (list[str]): 판정 근거 라인 리스트
            - ``scores`` (dict[str, int]): 4 국면 누적 점수

    Raises:
        없음.

    Example:
        >>> r = classifyCycle({"hy_spread": 450, "term_spread": -0.3, "vix": 28})
        >>> r.phase
        'slowdown'

    Guide:
        4 국면 정의: contraction (침체, HY 급등+VIX>30), recovery (회복, HY
        하락+CLI 반등), expansion (확장, HY 안정+CLI 양수), slowdown (둔화,
        Term spread 역전+CPI 가속). 점수 모두 0 이면 ``"expansion"`` 기본값.

    See Also:
        - ``interpretAssets``: 사이클 → 자산 추천
        - ``CYCLE_SECTOR_MAP``: 사이클별 섹터 전략

    When:
        ``analyzeCycle`` 내부 1 차 분류기 — phase 판정 결과를 transition/quadrant
        가 받아 확장.

    How:
        8 지표 룰 매칭 → scores dict 누적 → argmax → top-2nd 차이로 confidence.

    Requires:
        없음 (순수 함수).

    AIContext:
        confidence="low" 결과는 전환기 가능성 — 동일 indicators 1~2 분기 후
        재호출 권장. signals 리스트는 라벨 인용 시 함께 노출하여 근거 투명화.

    LLM Specifications:
        AntiPatterns:
            - 단일 지표만으로 phase 추론 금지. 본 함수는 8 지표 가중 합산.
            - signals 리스트가 비어 있을 때 phase 신뢰 금지 — 입력 부족 신호.
        OutputSchema:
            CyclePhase ``{phase, phaseLabel, confidence, signals, scores}``.
        Prerequisites:
            최소 1 개 지표 값 (None 아님). 모두 None 이면 기본 expansion.
        Freshness:
            지표별 갱신 주기 (HY/VIX 일, CLI 월, CPI/BEI 월).
        Dataflow:
            지표별 룰 → scores dict 누적 → max → phase + confidence 계산
            (top - 2nd 차이로).
        TargetMarkets: US (FRED), KR (BOK ECOS).
    """
    signals: list[str] = []
    scores = {"contraction": 0, "recovery": 0, "expansion": 0, "slowdown": 0}

    hy = indicators.get("hy_spread")
    hy_chg = indicators.get("hy_spread_3m_change")
    ts = indicators.get("term_spread")
    vix = indicators.get("vix")
    goldYoy = indicators.get("gold_yoy")
    cli_mom = indicators.get("cli_mom")
    cpiYoy = indicators.get("cpi_yoy")
    bei10y = indicators.get("bei_10y")

    # 1. 하이일드 스프레드 — 레벨 + 변화 속도
    if hy is not None:
        if hy > 500:
            scores["contraction"] += 3
            signals.append(f"HY 스프레드 급등 ({hy:.0f}bp)")
        elif hy > 400:
            scores["contraction"] += 1
            scores["slowdown"] += 2
            signals.append(f"HY 스프레드 경고 ({hy:.0f}bp)")
        elif hy < 350:
            scores["expansion"] += 1
            scores["recovery"] += 1
            signals.append(f"HY 스프레드 안정 ({hy:.0f}bp)")

    # HY 변화 속도 — 회복 전환 핵심 신호 (실험 01 피드백)
    if hy_chg is not None:
        if hy_chg < -50:
            scores["recovery"] += 2
            signals.append(f"HY 스프레드 급감 (3M {hy_chg:+.0f}bp)")
        elif hy_chg > 100:
            scores["contraction"] += 2
            signals.append(f"HY 스프레드 급등 (3M {hy_chg:+.0f}bp)")

    # 2. 장단기 스프레드
    if ts is not None:
        if ts < 0:
            scores["contraction"] += 2
            scores["slowdown"] += 1
            signals.append(f"수익률곡선 역전 ({ts:+.2f}%)")
        elif ts < 0.5:
            scores["slowdown"] += 2
            signals.append(f"수익률곡선 평탄화 ({ts:+.2f}%)")
        elif ts > 1.5:
            scores["recovery"] += 2
            signals.append(f"수익률곡선 가파름 ({ts:+.2f}%)")
        else:
            scores["expansion"] += 1
            signals.append(f"수익률곡선 정상 ({ts:+.2f}%)")

    # 3. VIX
    if vix is not None:
        if vix > 30:
            scores["contraction"] += 2
            signals.append(f"VIX 급등 ({vix:.1f})")
        elif vix > 20:
            scores["slowdown"] += 1
            signals.append(f"VIX 상승 ({vix:.1f})")
        elif vix < 15:
            scores["expansion"] += 2
            signals.append(f"VIX 안정 ({vix:.1f})")
        else:
            scores["recovery"] += 1
            scores["expansion"] += 1

    # 4. 금 YoY
    if goldYoy is not None:
        if goldYoy > 15:
            scores["contraction"] += 1
            scores["slowdown"] += 1
            signals.append(f"금 급등 (YoY {goldYoy:+.1f}%)")
        elif goldYoy < -5:
            scores["recovery"] += 1
            scores["expansion"] += 1
            signals.append(f"금 하락 (YoY {goldYoy:+.1f}%)")

    # 5. CLI 모멘텀 — 반전 강화 (실험 01 피드백)
    if cli_mom is not None:
        if cli_mom < -0.5:
            scores["contraction"] += 2
            signals.append(f"CLI 급락 ({cli_mom:+.2f})")
        elif cli_mom < -0.1:
            scores["slowdown"] += 2
            signals.append(f"CLI 하락 ({cli_mom:+.2f})")
        elif cli_mom > 0.5:
            scores["recovery"] += 2
            signals.append(f"CLI 급등 ({cli_mom:+.2f})")
        elif cli_mom > 0.1:
            scores["expansion"] += 1
            scores["recovery"] += 1
            signals.append(f"CLI 상승 ({cli_mom:+.2f})")

    # 6. 인플레이션 — 사이클 3대 힘 중 하나 (통화/재정/물가)
    if cpiYoy is not None:
        if cpiYoy > 4.0:
            scores["slowdown"] += 2
            signals.append(f"CPI {cpiYoy:.1f}% — 물가 과열, 둔화 전조")
        elif cpiYoy > 3.0:
            scores["expansion"] += 1
            signals.append(f"CPI {cpiYoy:.1f}% — 인플레 동반 확장")
        elif cpiYoy < 1.5:
            scores["contraction"] += 1
            signals.append(f"CPI {cpiYoy:.1f}% — 디플레 우려")

    if bei10y is not None:
        if bei10y > 2.8:
            scores["slowdown"] += 1
            signals.append(f"BEI {bei10y:.2f}% — 기대인플레 상승, 긴축 압력")
        elif bei10y < 1.8:
            scores["contraction"] += 1
            scores["recovery"] += 1
            signals.append(f"BEI {bei10y:.2f}% — 기대인플레 하락")

    # 최고 점수 국면 선택
    phase = max(scores, key=lambda k: scores[k])
    max_score = scores[phase]
    total = sum(scores.values())

    if total == 0:
        return CyclePhase(
            "expansion",
            "확장",
            "low",
            ("신호 데이터 부족",),
            CYCLE_SECTOR_MAP["expansion"],
        )

    ratio = max_score / total if total > 0 else 0
    if ratio > 0.5:
        confidence = "high"
    elif ratio > 0.35:
        confidence = "medium"
    else:
        confidence = "low"

    return CyclePhase(
        phase=phase,
        label=PHASE_LABELS[phase],
        confidence=confidence,
        signals=tuple(signals),
        sectorStrategy=CYCLE_SECTOR_MAP[phase],
    )


__all__ = ["CYCLE_SECTOR_MAP", "classifyCycle"]
