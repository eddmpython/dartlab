"""시장 심리 판정 + 금리 기대 추정 + 고용/물가 해석.

순수 데이터 + 판정 함수. 외부 의존성 없음.
core/ 계층 소속 — macro(시장 해석) 엔진에서 소비.
"""

from __future__ import annotations

from dataclasses import dataclass


# ══════════════════════════════════════
# 데이터 구조
# ══════════════════════════════════════


@dataclass(frozen=True)
class SentimentScore:
    """시장 심리 지수 (CNN Fear & Greed 근사)."""

    score: float  # 0-100 (0=극단공포, 100=극단탐욕)
    zone: str  # "extreme_fear" | "fear" | "neutral" | "greed" | "extreme_greed"
    zoneLabel: str  # "극단공포" | "공포" | "중립" | "탐욕" | "극단탐욕"
    components: dict[str, float]  # 개별 요소 점수


@dataclass(frozen=True)
class RateExpectation:
    """시장 금리 기대 방향 (FedWatch 근사)."""

    spread2yFf: float  # 2Y - Fed Funds 스프레드 (%p)
    spread10y2y: float | None  # 10Y - 2Y 스프레드 (%p)
    direction: str  # "cut_expected" | "hike_expected" | "hold_expected"
    directionLabel: str  # "인하 기대" | "인상 기대" | "동결 기대"
    strength: str  # "strong" | "moderate" | "mild"


@dataclass(frozen=True)
class EmploymentSignal:
    """고용 상태 해석."""

    state: str  # "strong" | "moderate" | "weakening" | "weak"
    stateLabel: str  # "강함" | "보통" | "약화" | "약함"
    reasoning: tuple[str, ...]


@dataclass(frozen=True)
class InflationSignal:
    """물가 상태 해석."""

    state: str  # "hot" | "warm" | "target" | "cool" | "cold"
    stateLabel: str  # "과열" | "높음" | "목표부근" | "둔화" | "디플레우려"
    reasoning: tuple[str, ...]


# ══════════════════════════════════════
# 공포탐욕 근사
# ══════════════════════════════════════


def _normalize(value: float, low: float, high: float) -> float:
    """value를 [low, high] 범위에서 0-100으로 정규화."""
    if high <= low:
        return 50.0
    clamped = max(low, min(high, value))
    return (clamped - low) / (high - low) * 100


def calcFearGreedProxy(
    vix: float,
    sp500_vs_ma125: float,
    hy_spread: float,
    gold_equity_ratio: float | None = None,
) -> SentimentScore:
    """FRED 4요소로 CNN Fear & Greed Index 근사.

    Args:
        vix: CBOE VIX (낮을수록 탐욕)
        sp500_vs_ma125: S&P500 현재가 / 125일 이동평균 비율 (1.0 = 평균, >1 = 탐욕)
        hy_spread: HY 스프레드 bps (낮을수록 탐욕)
        gold_equity_ratio: 금/S&P500 비율 (높을수록 공포). None이면 제외.

    Returns:
        SentimentScore (0=극단공포, 100=극단탐욕)
    """
    components: dict[str, float] = {}

    # VIX: 10(극단탐욕) ~ 40(극단공포) → 반전
    components["vix"] = 100 - _normalize(vix, 10, 40)

    # S&P500 모멘텀: 0.9(공포) ~ 1.1(탐욕)
    components["momentum"] = _normalize(sp500_vs_ma125, 0.90, 1.10)

    # HY 스프레드: 300(탐욕) ~ 700(공포) → 반전
    components["credit"] = 100 - _normalize(hy_spread, 300, 700)

    # 금/주식 비율 (선택): 높으면 공포
    if gold_equity_ratio is not None:
        components["safe_haven"] = 100 - _normalize(gold_equity_ratio, 0.3, 0.6)

    score = sum(components.values()) / len(components)
    score = max(0, min(100, score))

    if score < 25:
        zone, label = "extreme_fear", "극단공포"
    elif score < 45:
        zone, label = "fear", "공포"
    elif score < 55:
        zone, label = "neutral", "중립"
    elif score < 75:
        zone, label = "greed", "탐욕"
    else:
        zone, label = "extreme_greed", "극단탐욕"

    return SentimentScore(
        score=round(score, 1),
        zone=zone,
        zoneLabel=label,
        components={k: round(v, 1) for k, v in components.items()},
    )


# ══════════════════════════════════════
# 금리 기대 (FedWatch 근사)
# ══════════════════════════════════════


def estimateRateExpectation(
    ff_rate: float,
    dgs2: float,
    dgs10: float | None = None,
) -> RateExpectation:
    """2Y-FF 스프레드로 시장 금리 기대 방향 근사.

    2Y 국채는 향후 2년간 정책금리 경로 기대를 반영.
    2Y < FF → 시장은 인하를 기대.
    2Y > FF → 시장은 인상을 기대.

    Args:
        ff_rate: Fed Funds Rate (%)
        dgs2: 2년 국채 수익률 (%)
        dgs10: 10년 국채 수익률 (%) — optional, 기울기 정보용

    Returns:
        RateExpectation
    """
    spread = dgs2 - ff_rate
    spread_10y2y = (dgs10 - dgs2) if dgs10 is not None else None

    if spread < -0.50:
        direction, label, strength = "cut_expected", "인하 기대", "strong"
    elif spread < -0.25:
        direction, label, strength = "cut_expected", "인하 기대", "moderate"
    elif spread < -0.10:
        direction, label, strength = "cut_expected", "인하 기대", "mild"
    elif spread > 0.50:
        direction, label, strength = "hike_expected", "인상 기대", "strong"
    elif spread > 0.25:
        direction, label, strength = "hike_expected", "인상 기대", "moderate"
    elif spread > 0.10:
        direction, label, strength = "hike_expected", "인상 기대", "mild"
    else:
        direction, label, strength = "hold_expected", "동결 기대", "moderate"

    return RateExpectation(
        spread2yFf=round(spread, 3),
        spread10y2y=round(spread_10y2y, 3) if spread_10y2y is not None else None,
        direction=direction,
        directionLabel=label,
        strength=strength,
    )


# ══════════════════════════════════════
# 고용 해석
# ══════════════════════════════════════


def interpretEmployment(
    unrate: float,
    payrolls_3m_avg: float | None = None,
) -> EmploymentSignal:
    """고용 지표 해석.

    Args:
        unrate: 실업률 (%)
        payrolls_3m_avg: 비농업고용 3개월 평균 변화 (천명)

    Returns:
        EmploymentSignal
    """
    reasons: list[str] = []
    score = 0  # 양수=강함, 음수=약함

    if unrate < 4.0:
        score += 2
        reasons.append(f"실업률 {unrate:.1f}% — 완전고용 수준")
    elif unrate < 5.0:
        score += 1
        reasons.append(f"실업률 {unrate:.1f}% — 양호")
    elif unrate < 6.0:
        score -= 1
        reasons.append(f"실업률 {unrate:.1f}% — 약화")
    else:
        score -= 2
        reasons.append(f"실업률 {unrate:.1f}% — 고용 악화")

    if payrolls_3m_avg is not None:
        if payrolls_3m_avg > 200:
            score += 2
            reasons.append(f"고용 증가 3M평균 +{payrolls_3m_avg:.0f}K — 강함")
        elif payrolls_3m_avg > 100:
            score += 1
            reasons.append(f"고용 증가 3M평균 +{payrolls_3m_avg:.0f}K — 적정")
        elif payrolls_3m_avg > 0:
            reasons.append(f"고용 증가 3M평균 +{payrolls_3m_avg:.0f}K — 둔화")
        else:
            score -= 2
            reasons.append(f"고용 감소 3M평균 {payrolls_3m_avg:.0f}K — 경고")

    if score >= 3:
        state, label = "strong", "강함"
    elif score >= 1:
        state, label = "moderate", "보통"
    elif score >= -1:
        state, label = "weakening", "약화"
    else:
        state, label = "weak", "약함"

    return EmploymentSignal(state=state, stateLabel=label, reasoning=tuple(reasons))


# ══════════════════════════════════════
# 물가 해석
# ══════════════════════════════════════


def interpretInflation(
    cpi_yoy: float,
    core_cpi_yoy: float | None = None,
    bei_5y: float | None = None,
    bei_10y: float | None = None,
) -> InflationSignal:
    """물가 지표 해석.

    Args:
        cpi_yoy: CPI YoY (%)
        core_cpi_yoy: Core CPI YoY (%)
        bei_5y: 5년 BEI (%) — 기대인플레이션
        bei_10y: 10년 BEI (%) — 기대인플레이션

    Returns:
        InflationSignal
    """
    reasons: list[str] = []
    heat = 0  # 양수=과열, 음수=냉각

    if cpi_yoy > 4.0:
        heat += 3
        reasons.append(f"CPI {cpi_yoy:.1f}% — 인플레이션 과열")
    elif cpi_yoy > 3.0:
        heat += 2
        reasons.append(f"CPI {cpi_yoy:.1f}% — 목표 상회")
    elif cpi_yoy > 1.5:
        reasons.append(f"CPI {cpi_yoy:.1f}% — 목표 부근")
    elif cpi_yoy > 0:
        heat -= 1
        reasons.append(f"CPI {cpi_yoy:.1f}% — 둔화")
    else:
        heat -= 2
        reasons.append(f"CPI {cpi_yoy:.1f}% — 디플레이션 우려")

    if core_cpi_yoy is not None:
        if core_cpi_yoy > 3.5:
            heat += 1
            reasons.append(f"Core CPI {core_cpi_yoy:.1f}% — 기조적 인플레")
        elif core_cpi_yoy < 2.0:
            heat -= 1
            reasons.append(f"Core CPI {core_cpi_yoy:.1f}% — 기조 둔화")

    if bei_5y is not None:
        if bei_5y > 2.8:
            heat += 1
            reasons.append(f"5Y BEI {bei_5y:.2f}% — 기대인플레 상승")
        elif bei_5y < 1.8:
            heat -= 1
            reasons.append(f"5Y BEI {bei_5y:.2f}% — 기대인플레 하락")

    if heat >= 3:
        state, label = "hot", "과열"
    elif heat >= 1:
        state, label = "warm", "높음"
    elif heat >= -1:
        state, label = "target", "목표부근"
    elif heat >= -2:
        state, label = "cool", "둔화"
    else:
        state, label = "cold", "디플레우려"

    return InflationSignal(state=state, stateLabel=label, reasoning=tuple(reasons))
