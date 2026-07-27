"""Corporate Life Cycle 판별. Damodaran (2024).

기업의 시간적 위치(생애주기 단계)를 매출 CAGR / 영업마진 추세 / ROIC-WACC spread /
FCF 전환 여부 / 배당성향 조합으로 자동 판별.

storyTemplate (사업 특성) 과 **직교**하는 축. 삼성전자 는 `사이클 × matureStable`.
밸류에이션 모델 선택은 이 생애주기 단계에 따라 dispatch (dFV.py).

근거: Damodaran, *The Corporate Life Cycle* (Wiley 2024).
"""

from __future__ import annotations

from statistics import mean, pstdev
from typing import Any, NamedTuple

from dartlab.synth.overrides import applyOverride

_KR_GROWTH_ADJ = -5.0  # KR 상장사 mid-cycle 정체 → 성장 threshold -5%p

_PHASES = (
    "earlyGrowth",
    "highGrowth",
    "matureGrowth",
    "matureStable",
    "decline",
    "turnaround",
)

_MODEL_HINT = {
    "earlyGrowth": "relativeSurvival",
    "highGrowth": "dcf2stage",
    "matureGrowth": "dcf",
    "matureStable": "dcf",
    "decline": "liquidation",
    "turnaround": "relative",
}


def calcLifeCycle(
    company: Any,
    *,
    basePeriod: str | None = None,
    overrides: dict | None = None,
) -> dict | None:
    """기업 생애주기 단계 판별.

    Capabilities:
        - 매출 CAGR · 마진 CV · ROIC-WACC · FCF streak 신호로 phase 판정.

    Guide:
        earlyGrowth/highGrowth/matureGrowth/matureStable/decline/turnaround 6 라벨.

    When:
        밸류에이션 모델 선택 직전 또는 회사 성격 분류 시.

    How:
        _gatherSignals → KR 조정 → _classify → inflection 보강 → modelHint.

    Requires:
        IS/CF 시계열 ≥ 3 년 + ROIC 계산 가능.

    Raises:
        없음 (신호 부재 시 None).

    Example:
        >>> calcLifeCycle(c)["phase"]
        "matureGrowth"

    See Also:
        - needsNormalized : decline/turnaround 게이트
        - dFV : modelHint 소비

    AIContext:
        AI 답변 "이 회사 성격" + 적합 valuation 모델 라우팅에 사용.

    Returns
    -------
    dict | None
        phase : str. 단계 키 (_PHASES 중 하나)
        phaseConfidence : float. 0.0~1.0
        signals : dict
            revenueCAGR : float. 매출 CAGR (%)
            operatingMarginCV : float. 영업이익률 변동계수
            roicWACCSpread : float. ROIC - WACC 평균 (%p)
            fcfPositiveStreak : int. FCF 양수 연속 기간
            dividendPayout : float. 평균 배당성향 (%)
            marginDirection : str. "expanding" | "stable" | "contracting"
        inflection : dict. {"towards": str | None, "score": float}
        history : list[dict]. 기간별 단계 이력 (최대 5)
        modelHint : str. dFV fitness 가 참조할 밸류에이션 모델 힌트
        source : str. "auto" | "override"
    """
    overrides = overrides or {}

    # override 로 직접 지정된 경우 즉시 반환
    forced = applyOverride(None, "lifeCyclePhase", overrides)
    if forced in _PHASES:
        return {
            "phase": forced,
            "phaseConfidence": 1.0,
            "signals": {},
            "inflection": {"towards": None, "score": 0.0},
            "history": [],
            "modelHint": _MODEL_HINT[forced],
            "source": "override",
        }

    # 신호 수집. 기존 calc 재사용 (신규 계산 금지)
    signals = _gatherSignals(company, basePeriod=basePeriod)
    if signals is None:
        return None

    # KR 조정
    currency = (getattr(company, "currency", "KRW") or "KRW").upper()
    growthAdj = _KR_GROWTH_ADJ if currency == "KRW" else 0.0

    phase, confidence, history = _classify(signals, growthAdj=growthAdj)
    inflection = _detectInflection(signals, phase)

    return {
        "phase": phase,
        "phaseConfidence": round(confidence, 2),
        "signals": signals,
        "inflection": inflection,
        "history": history,
        "modelHint": _MODEL_HINT.get(phase, "dcf"),
        "source": "auto",
    }


def _gatherSignals(company: Any, *, basePeriod: str | None) -> dict | None:
    """기존 calc 재사용. lifeCycle 판별 입력 수집."""
    revenue_cagr: float | None = None
    op_margins: list[float] = []
    roic_spreads: list[float] = []
    fcf_streak = 0
    dividend_payout: float | None = None
    margin_direction = "stable"
    revenue_yoys: list[float] = []

    try:
        from dartlab.analysis.financial.growthAnalysis import calcGrowthTrend

        growth = calcGrowthTrend(company, basePeriod=basePeriod)
        if growth:
            revenue_cagr = (growth.get("cagr") or {}).get("revenue")
            _collectHistoryFloats(growth, "revenueYoy", revenue_yoys)
    except (ImportError, AttributeError, ValueError, TypeError):
        pass

    try:
        from dartlab.analysis.financial.profitability import calcMarginTrend

        margin = calcMarginTrend(company, basePeriod=basePeriod)
        if margin:
            _collectHistoryFloats(margin, "operatingMargin", op_margins)
    except (ImportError, AttributeError, ValueError, TypeError):
        pass

    try:
        from dartlab.analysis.financial.investmentAnalysis import calcRoicTimeline

        roic = calcRoicTimeline(company, basePeriod=basePeriod)
        if roic:
            _collectHistoryFloats(roic, "spread", roic_spreads)
    except (ImportError, AttributeError, ValueError, TypeError):
        pass

    try:
        from dartlab.analysis.financial.cashflow import calcCashFlowOverview

        cf = calcCashFlowOverview(company, basePeriod=basePeriod)
        if cf:
            # FCF 양수 연속 기간 (최신부터)
            for h in cf.get("history", []):
                fcf = h.get("fcf")
                if isinstance(fcf, (int, float)) and fcf > 0:
                    fcf_streak += 1
                else:
                    break
    except (ImportError, AttributeError, ValueError, TypeError):
        pass

    try:
        from dartlab.analysis.financial.capitalAllocation import calcDividendPolicy

        div = calcDividendPolicy(company, basePeriod=basePeriod)
        if div:
            payouts: list[float] = []
            _collectHistoryFloats(div, "payoutRatio", payouts)
            if payouts:
                dividend_payout = float(mean(payouts))
    except (ImportError, AttributeError, ValueError, TypeError):
        pass

    return {
        "revenueCAGR": revenue_cagr,
        "operatingMarginCV": _coefficientOfVariation(op_margins),
        "roicWACCSpread": round(mean(roic_spreads), 2) if roic_spreads else None,
        "fcfPositiveStreak": fcf_streak,
        "dividendPayout": round(dividend_payout, 2) if dividend_payout is not None else None,
        "marginDirection": _marginDirection(op_margins),
        "operatingMarginSeries": op_margins,
        "revenueYoySeries": revenue_yoys,
    }


def _collectHistoryFloats(result: dict, field: str, into: list[float]) -> None:
    """calc 결과의 ``history`` 에서 한 필드만 뽑아 ``into`` 에 누적한다.

    growth/margin/roic/dividend 네 곳이 같은 "history 순회 + 숫자면 채택" 을 필드명만
    바꿔 반복하고 있었다. 새 리스트를 만들지 않고 누적하는 이유는 호출자의
    try/except 가 순회 도중 예외에서 부분 수집분을 그대로 안고 가기 때문이다.
    """
    for h in result.get("history", []):
        v = h.get(field)
        if isinstance(v, (int, float)):
            into.append(float(v))


def _marginDirection(opMargins: list[float]) -> str:
    """마진 방향: 최근 3 기간 평균과 오래된 3 기간 평균의 차이로 확장/축소 판정."""
    if len(opMargins) < 3:
        return "stable"
    delta = mean(opMargins[:3]) - mean(opMargins[-3:])
    if delta > 2.0:
        return "expanding"
    if delta < -2.0:
        return "contracting"
    return "stable"


def _coefficientOfVariation(opMargins: list[float]) -> float | None:
    """영업이익률 변동계수 (표준편차 / |평균|). 평균 0 이면 None."""
    if len(opMargins) < 3:
        return None
    mu = mean(opMargins)
    if mu == 0:
        return None
    return round(pstdev(opMargins) / abs(mu), 3)


class _PhaseInputs(NamedTuple):
    """G20 룰 6 개가 공유하는 파생 입력. 룰마다 재추출하지 않으려고 한 번만 만든다."""

    cagr: float | None
    spread: float | None
    fcfStreak: int
    payout: float
    margins: list
    yoys: list
    recentMargin: float | None
    growthAdj: float


def _phaseInputs(signals: dict, growthAdj: float) -> _PhaseInputs:
    """signals dict 를 룰이 바로 읽을 수 있는 파생 입력으로 정규화한다."""
    margins = signals.get("operatingMarginSeries") or []
    return _PhaseInputs(
        cagr=signals.get("revenueCAGR"),
        spread=signals.get("roicWACCSpread"),
        fcfStreak=signals.get("fcfPositiveStreak", 0),
        payout=signals.get("dividendPayout") or 0.0,
        margins=margins,
        yoys=signals.get("revenueYoySeries") or [],
        # 최근 마진 평균 (음수 여부 판단)
        recentMargin=mean(margins[:3]) if len(margins) >= 2 else (margins[0] if margins else None),
        growthAdj=growthAdj,
    )


def _ruleTurnaround(inputs: _PhaseInputs) -> tuple[str, float] | None:
    """G20.1: turnaround 우선 강화. 최근 3년 중 음수 1회 + 최신 양수 (창 확대)."""
    margins = inputs.margins
    if len(margins) < 3:
        return None
    recent3 = margins[:3]
    if recent3[0] > 0 and any(m < 0 for m in recent3[1:]) and (inputs.cagr is None or inputs.cagr > -10):
        return "turnaround", 0.85
    return None


def _ruleDecline(inputs: _PhaseInputs) -> tuple[str, float] | None:
    """G20.2: decline. 성장이 꺾이고 spread 음수가 이어지거나 3년 연속 역성장."""
    cagr = inputs.cagr
    spread = inputs.spread
    if isinstance(cagr, (int, float)) and cagr < 0 and (spread is None or spread < -1.0):
        if inputs.recentMargin is not None and inputs.recentMargin < 5:
            return "decline", 0.75
    yoys = inputs.yoys
    if len(yoys) >= 3 and all(y < 0 for y in yoys[:3]):
        return "decline", 0.7
    return None


def _ruleMatureStable(inputs: _PhaseInputs) -> tuple[str, float] | None:
    """G20.3: matureStable 엄격화. CAGR<5, payout>=40, fcf streak>=3, spread 작음 전부 충족.

    이전에는 일부 충족도 흡수해서 matureGrowth/turnaround 사각지대를 만들었다.
    """
    cagr = inputs.cagr
    spread = inputs.spread
    if (
        isinstance(cagr, (int, float))
        and cagr <= 5 + inputs.growthAdj
        and inputs.payout >= 40
        and inputs.fcfStreak >= 3
        and (spread is None or abs(spread) < 3.0)
    ):
        return "matureStable", 0.85
    return None


def _ruleEarlyGrowth(inputs: _PhaseInputs) -> tuple[str, float] | None:
    """G20.4: earlyGrowth. 고성장 + 음수 마진 + FCF 음수."""
    cagr = inputs.cagr
    if isinstance(cagr, (int, float)) and cagr >= 30 + inputs.growthAdj:
        if inputs.recentMargin is not None and inputs.recentMargin < 0 and inputs.fcfStreak == 0:
            return "earlyGrowth", 0.75
    return None


def _ruleHighGrowth(inputs: _PhaseInputs) -> tuple[str, float] | None:
    """G20.5: highGrowth. 빠른 성장 + spread 양수.

    Damodaran: 고성장기에는 R&D 확대로 마진이 흔들려도 단계 판정을 바꾸지 않는다.
    """
    cagr = inputs.cagr
    if isinstance(cagr, (int, float)) and 15 + inputs.growthAdj <= cagr < 35 + inputs.growthAdj:
        if inputs.spread is None or inputs.spread > 0:
            return "highGrowth", 0.75
    return None


def _ruleMatureGrowth(inputs: _PhaseInputs) -> tuple[str, float] | None:
    """G20.6: matureGrowth 활성화. CAGR 5~18% + spread 양수 (fcf streak 의무 제거)."""
    cagr = inputs.cagr
    if isinstance(cagr, (int, float)) and 5 + inputs.growthAdj <= cagr < 18 + inputs.growthAdj:
        if inputs.spread is None or inputs.spread > 0:
            return "matureGrowth", 0.7
    return None


# G20 룰은 우선순위 순서가 곧 판정 순서다. 앞 룰이 잡으면 뒤 룰은 보지 않는다.
_PHASE_RULES = (
    _ruleTurnaround,
    _ruleDecline,
    _ruleMatureStable,
    _ruleEarlyGrowth,
    _ruleHighGrowth,
    _ruleMatureGrowth,
)


def _classify(signals: dict, *, growthAdj: float = 0.0) -> tuple[str, float, list[dict]]:
    """신호 → 단계 판별. 보수적 confidence 로 반환."""
    inputs = _phaseInputs(signals, growthAdj)
    for rule in _PHASE_RULES:
        verdict = rule(inputs)
        if verdict is not None:
            phase, confidence = verdict
            return phase, confidence, _buildHistory(signals)

    # G20.7: 잔여분은 보수적 fallback 으로 matureStable.
    return "matureStable", 0.4, _buildHistory(signals)


def _buildHistory(signals: dict) -> list[dict]:
    """간단한 히스토리. 판별에 쓴 핵심 신호만 기록."""
    return [
        {
            "signal": "revenueCAGR",
            "value": signals.get("revenueCAGR"),
        },
        {
            "signal": "roicWACCSpread",
            "value": signals.get("roicWACCSpread"),
        },
        {
            "signal": "fcfPositiveStreak",
            "value": signals.get("fcfPositiveStreak"),
        },
        {
            "signal": "dividendPayout",
            "value": signals.get("dividendPayout"),
        },
    ]


def _detectInflection(signals: dict, currentPhase: str) -> dict:
    """단계 전환 신호 감지. 최근 지표 방향성으로."""
    direction = signals.get("marginDirection")
    cagr = signals.get("revenueCAGR")
    margins = signals.get("operatingMarginSeries") or []
    fcf_streak = signals.get("fcfPositiveStreak", 0)

    # matureGrowth → matureStable: 성장 둔화
    if currentPhase == "matureGrowth" and isinstance(cagr, (int, float)) and cagr < 8:
        return {"towards": "matureStable", "score": 0.6}
    # matureStable → decline: 마진 하락 + FCF 약화
    if currentPhase == "matureStable" and direction == "contracting" and fcf_streak <= 1:
        return {"towards": "decline", "score": 0.55}
    # highGrowth → matureGrowth: CAGR 하락
    if currentPhase == "highGrowth" and isinstance(cagr, (int, float)) and cagr < 15:
        return {"towards": "matureGrowth", "score": 0.5}
    # turnaround → highGrowth/matureGrowth: 지속 흑자
    if currentPhase == "turnaround" and len(margins) >= 3 and all(m > 0 for m in margins[:3]):
        return {"towards": "matureGrowth", "score": 0.6}
    return {"towards": None, "score": 0.0}
