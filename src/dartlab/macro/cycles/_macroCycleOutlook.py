"""macroCycle 금리 전망 + 전환 시퀀스 감지 — macroCycle.py 에서 분리."""

from __future__ import annotations

from dartlab.macro.cycles._macroCycleStats import _findFirstTriggerDates
from dartlab.macro.cycles._macroCycleTypes import TransitionSignal

# ══════════════════════════════════════
# 금리 전망
# ══════════════════════════════════════


def rateOutlook(indicators: dict[str, float | None]) -> dict:
    """금리·물가·고용 → Fed/BOK 정책 금리 방향 전망 (인상/동결/인하).

    Capabilities:
        Taylor rule 단순화 — CPI/Core CPI + 실업률 + payrolls 변화로 인플레
        압력과 고용 강도를 합산하여 정책금리 방향 (hike/hold/cut) 과 신뢰도
        산출. macro/summary 의 rates 축이 직접 호출.

    Args:
        indicators: 매크로 dict. 지원 키:
            - ``fed_funds`` 또는 ``base_rate`` (%): 현 정책금리
            - ``cpi_yoy`` (%): CPI YoY
            - ``core_cpi_yoy`` (%): Core CPI YoY
            - ``unemployment`` (%): 실업률
            - ``payrolls_change`` (천명): 비농업고용 변화

    Returns:
        dict:
            - ``direction`` (str): ``"hike"``/``"hold"``/``"cut"``
            - ``directionLabel`` (str): 한국어
            - ``confidence`` (str): high/medium/low
            - ``reasoning`` (list[str]): 판정 근거 라인
            - ``bias`` (int): 양수=인상 / 음수=인하

    Raises:
        없음.

    Example:
        >>> r = rateOutlook({"fed_funds": 5.5, "cpi_yoy": 3.2,
        ...                  "unemployment": 3.7, "payrolls_change": 200})
        >>> r["direction"]
        'hold'

    Guide:
        Taylor rule: r* = neutral + 1.5(π - 2) + 0.5(u_natural - u). 본 함수는
        간소화 — 인상 bias 누적 (CPI>3, payrolls 강세 등) - 인하 bias (CPI<2,
        unemp 상승). bias > +2 = hike, < -2 = cut, 그 외 hold.

    See Also:
        - ``classifyCycle``: 사이클 4 국면 (rateOutlook 와 함께 종합)
        - ``decomposeLongRate``: 장기금리 BEI/real rate 분해

    When:
        ``analyzeRates`` + ``analyzeSummary`` 의 rates 축 진입점.

    How:
        CPI/Core CPI/실업률/payrolls 별 bias 누적 (±1~2) → 합산 → ±2 임계로
        direction (hike/cut/hold) + |bias|≥3 = high confidence.

    Requires:
        없음 (순수 함수). indicators 일부 키만 있어도 동작.

    AIContext:
        direction + reasoning 함께 인용. confidence=low 시 다음 분기 재호출
        권장 (전환기). bias 절댓값 작으면 (|bias|<2) hold 가 default.

    LLM Specifications:
        AntiPatterns:
            - 단일 지표 (CPI 만) 로 direction 판정 — Taylor rule 은 인플레 +
              고용 동시 고려.
            - 한국 base_rate 호출에 미국 fed_funds 표준 적용 — KR/US 별
              neutral rate 다름 (한국 ~2.5%, 미국 ~3%).
        OutputSchema:
            ``{direction, directionLabel, confidence, reasoning, bias}``.
        Prerequisites:
            indicators 에 (fed_funds 또는 base_rate) + cpi_yoy 권장.
        Freshness:
            CPI 월간 (10 일 발표), 고용 월간 (첫 금요일).
        Dataflow:
            indicators → CPI bias + 고용 bias + 실업 bias 누적 → 합산 →
            direction 분류 + confidence.
        TargetMarkets: US (Fed funds + CPI + payrolls), KR (BOK base + KOSIS).
    """
    ff = indicators.get("fed_funds") or indicators.get("base_rate")
    cpi = indicators.get("cpi_yoy")
    core_cpi = indicators.get("core_cpi_yoy")
    unemp = indicators.get("unemployment")
    payrolls = indicators.get("payrolls_change")

    reasoning: list[str] = []
    bias = 0  # 양수 = 인상 방향, 음수 = 인하 방향

    if cpi is not None:
        if cpi > 3.0:
            bias += 2
            reasoning.append(f"CPI {cpi:.1f}% > 3% — 인상 압력")
        elif cpi < 2.0:
            bias -= 1
            reasoning.append(f"CPI {cpi:.1f}% < 2% — 인하 여지")
        else:
            reasoning.append(f"CPI {cpi:.1f}% — 목표 부근")

    if core_cpi is not None:
        if core_cpi > 3.0:
            bias += 1
            reasoning.append(f"Core CPI {core_cpi:.1f}% — 기조적 인플레")

    if unemp is not None:
        if unemp > 5.0:
            bias -= 2
            reasoning.append(f"실업률 {unemp:.1f}% > 5% — 고용 약화, 인하 압력")
        elif unemp < 4.0:
            bias += 1
            reasoning.append(f"실업률 {unemp:.1f}% < 4% — 고용 강함")

    if payrolls is not None:
        if payrolls < 100:
            bias -= 1
            reasoning.append(f"비농업고용 +{payrolls:.0f}K — 둔화")
        elif payrolls > 250:
            bias += 1
            reasoning.append(f"비농업고용 +{payrolls:.0f}K — 강함")

    if bias >= 2:
        direction = "hike"
        dLabel = "인상 가능"
    elif bias <= -2:
        direction = "cut"
        dLabel = "인하 가능"
    else:
        direction = "hold"
        dLabel = "동결 유지"

    confidence = "high" if abs(bias) >= 3 else "medium" if abs(bias) >= 2 else "low"

    return {
        "currentRate": ff,
        "direction": direction,
        "directionLabel": dLabel,
        "confidence": confidence,
        "reasoning": reasoning,
        "biasScore": bias,
    }


# ══════════════════════════════════════
# 전환 시퀀스 감지
# ══════════════════════════════════════

# 각 전환에 대한 자산 신호 시퀀스 (발현 순서대로)
_TRANSITION_SEQUENCES: dict[tuple[str, str], tuple[str, ...]] = {
    # 침체→회복: HY스프레드 축소 → 금 하락 → 장기금리 상승
    ("contraction", "recovery"): (
        "hy_spread_declining",
        "gold_declining",
        "long_rate_rising",
    ),
    # 회복→확장: VIX 안정 → 수익률곡선 정상화 → BEI 상승(인플레 동반) → HY 안정
    ("recovery", "expansion"): (
        "vix_stable",
        "term_spread_normalizing",
        "bei_rising",
        "hy_spread_stable",
    ),
    # 확장→둔화: HY스프레드 확대 → BEI 급등(물가 과열) → 수익률곡선 평탄화 → VIX 상승
    ("expansion", "slowdown"): (
        "hy_spread_widening",
        "bei_overheating",
        "term_spread_flattening",
        "vix_rising",
    ),
    # 둔화→침체: VIX 급등 → 수익률곡선 역전 → 금 급등
    ("slowdown", "contraction"): (
        "vix_spiking",
        "term_spread_inverted",
        "gold_surging",
    ),
}


def detectTransitionSequence(
    currentPhase: str,
    indicators: dict[str, float | None],
    history: dict[str, list[tuple[str, float]]] | None = None,
) -> TransitionSignal | None:
    """현재 국면에서 다음 국면으로의 전환 시퀀스를 감지.

    Capabilities:
        4 국면 cycle 의 순환 전이 (contraction→recovery→expansion→slowdown→
        contraction) 마다 정해진 자산 신호 시퀀스를 확인 — 발현된 신호 수 ÷ 전체
        = progress (0~1). history 가 있으면 신호별 최초 발현일까지 추적해
        sequenceOrder + orderValid 검증.

    Args:
        currentPhase: 현재 사이클 국면 (contraction/recovery/expansion/slowdown).
        indicators: 매크로 지표 dict. 키 — hy_spread_3m_change/gold_yoy/
            long_rate_change/vix/term_spread/bei_10y.
        history: 신호별 시계열 ``{시리즈: [(date, val), ...]}``. None 이면 순서
            검증 생략.

    Returns:
        TransitionSignal (fromPhase/toPhase/progress/triggered/pending/
        sequenceOrder/orderValid) 또는 None (지원 외 phase, 시퀀스 미정의).

    Example:
        >>> r = detectTransitionSequence("expansion", {"hy_spread_3m_change": 60,
        ...     "bei_10y": 2.8, "vix": 22, "term_spread": 0.1})
        >>> r.toPhase, r.progress > 0.5
        ('slowdown', True)

    Guide:
        progress ≥ 0.7 = "다음 국면 임박" 메시지. orderValid=False 면 순서 어긋남
        — 시퀀스 정의 재검토 또는 전환 신뢰 약화.

    When:
        ``analyzeCycle`` 내부 — phase 판정 직후 호출.

    How:
        _TRANSITION_SEQUENCES 룩업 → indicator 임계 매칭 → triggered/pending 분리
        → history 가 있으면 _findFirstTriggerDates → orderValid.

    Requires:
        - currentPhase 가 4 국면 중 하나
        - indicators 에 최소 hy_spread_3m_change 또는 vix
        - (선택) history 12 개월 신뢰 baseline

    Raises:
        없음 (지원 외 phase 면 None 반환).

    See Also:
        - classifyCycle : 4 국면 판정 (이 함수의 진입 phase)
        - analyzeCycle : transition 결과 합성

    AIContext:
        progress + toPhase 두 필드만으로 "X 단계로 진행 중 (70%)" 1 문장 답변
        가능.

    LLM Specifications:
        AntiPatterns:
            - history 없이 sequenceOrder 인용 (None 일 수 있음)
            - 시퀀스 정의 외 phase 입력 후 None 무시
            - progress 30% 미만에서 전환 강조 (premature signal)
        OutputSchema:
            TransitionSignal ``{fromPhase, toPhase, progress, triggered, pending,
            sequenceOrder, orderValid}``.
        Prerequisites: classifyCycle phase 출력 + indicators.
        Freshness: 일간 (HY/VIX) ~ 월간 (BEI).
        Dataflow: phase → sequence 룩업 → indicator 임계 → progress + history 검증.
        TargetMarkets: US (FRED 풀세트). KR 미지원 (시퀀스 미정의).
    """
    phases = ["contraction", "recovery", "expansion", "slowdown"]
    if currentPhase not in phases:
        return None

    idx = phases.index(currentPhase)
    nextPhase = phases[(idx + 1) % len(phases)]
    key = (currentPhase, nextPhase)
    sequence = _TRANSITION_SEQUENCES.get(key)
    if sequence is None:
        return None

    # 각 신호의 발현 여부 판정
    triggered: list[str] = []
    pending: list[str] = []

    hy_chg = indicators.get("hy_spread_3m_change")
    goldYoy = indicators.get("gold_yoy")
    lr_chg = indicators.get("long_rate_change")
    vix = indicators.get("vix")
    ts = indicators.get("term_spread")
    bei = indicators.get("bei_10y")

    signalChecks: dict[str, bool] = {
        "hy_spread_declining": hy_chg is not None and hy_chg < -30,
        "hy_spread_widening": hy_chg is not None and hy_chg > 50,
        "hy_spread_stable": hy_chg is not None and abs(hy_chg) < 30,
        "gold_declining": goldYoy is not None and goldYoy < -3,
        "gold_surging": goldYoy is not None and goldYoy > 15,
        "long_rate_rising": lr_chg is not None and lr_chg > 0.2,
        "vix_stable": vix is not None and vix < 18,
        "vix_rising": vix is not None and vix > 22,
        "vix_spiking": vix is not None and vix > 30,
        "term_spread_normalizing": ts is not None and ts > 0.5,
        "term_spread_flattening": ts is not None and 0 < ts < 0.5,
        "term_spread_inverted": ts is not None and ts < 0,
        # 인플레이션 전환 신호
        "bei_rising": bei is not None and bei > 2.3,  # 회복→확장: 인플레 동반
        "bei_overheating": bei is not None and bei > 2.8,  # 확장→둔화: 물가 과열
    }

    for signal_name in sequence:
        if signalChecks.get(signal_name, False):
            triggered.append(signal_name)
        else:
            pending.append(signal_name)

    if not triggered:
        return None

    progress = round(len(triggered) / len(sequence) * 100)

    # 시계열 이력이 있으면 각 신호의 최초 발현 시점 추적 + 순서 검증
    sequence_order: list[tuple[str, str | None]] = []
    order_valid: bool | None = None

    if history and len(triggered) >= 2:
        first_dates = _findFirstTriggerDates(sequence, signalChecks, history)
        sequence_order = [(sig, first_dates.get(sig)) for sig in triggered]
        # 발현 시점이 있는 신호들만 순서 검증
        dated = [(sig, d) for sig, d in sequence_order if d is not None]
        if len(dated) >= 2:
            order_valid = all(dated[i][1] <= dated[i + 1][1] for i in range(len(dated) - 1))

    return TransitionSignal(
        fromPhase=currentPhase,
        toPhase=nextPhase,
        progress=progress,
        triggered=tuple(triggered),
        pending=tuple(pending),
        sequenceOrder=tuple(sequence_order),
        orderValid=order_valid,
    )
