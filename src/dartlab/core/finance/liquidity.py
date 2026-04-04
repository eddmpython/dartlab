"""유동성 환경 판정.

순수 데이터 + 판정 함수. 외부 의존성 없음.
core/ 계층 소속 — macro(시장 해석) 엔진에서 소비.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LiquidityRegime:
    """유동성 환경 판정 결과."""

    regime: str  # "abundant" | "normal" | "tight"
    regimeLabel: str  # "풍부" | "정상" | "긴축"
    score: float  # -3 ~ +3 (양수=풍부, 음수=긴축)
    signals: tuple[str, ...]


def classifyLiquidityRegime(
    m2_yoy: float | None = None,
    fed_bs_change_pct: float | None = None,
    hy_spread: float | None = None,
    ig_spread: float | None = None,
    rrp_change_pct: float | None = None,
) -> LiquidityRegime:
    """유동성 환경 종합 판정.

    Args:
        m2_yoy: M2 통화량 YoY 변화율 (%)
        fed_bs_change_pct: 연준 총자산 변화율 (%, 3개월)
        hy_spread: HY 스프레드 (bps)
        ig_spread: IG 스프레드 (bps)
        rrp_change_pct: 역레포 잔액 변화율 (%, 음수=유동성 방출)

    Returns:
        LiquidityRegime
    """
    signals: list[str] = []
    score = 0.0

    # M2 통화량
    if m2_yoy is not None:
        if m2_yoy > 6:
            score += 1.5
            signals.append(f"M2 YoY +{m2_yoy:.1f}% — 통화 팽창")
        elif m2_yoy > 2:
            score += 0.5
            signals.append(f"M2 YoY +{m2_yoy:.1f}% — 정상 성장")
        elif m2_yoy > -2:
            signals.append(f"M2 YoY {m2_yoy:+.1f}% — 정체")
        else:
            score -= 1.5
            signals.append(f"M2 YoY {m2_yoy:+.1f}% — 통화 수축")

    # 연준 B/S
    if fed_bs_change_pct is not None:
        if fed_bs_change_pct > 2:
            score += 1
            signals.append(f"연준 B/S 3M {fed_bs_change_pct:+.1f}% — QE/확대")
        elif fed_bs_change_pct < -2:
            score -= 1
            signals.append(f"연준 B/S 3M {fed_bs_change_pct:+.1f}% — QT/축소")

    # HY 스프레드 (신용 시장 유동성)
    if hy_spread is not None:
        if hy_spread < 350:
            score += 0.5
            signals.append(f"HY 스프레드 {hy_spread:.0f}bp — 신용 완화")
        elif hy_spread > 500:
            score -= 1
            signals.append(f"HY 스프레드 {hy_spread:.0f}bp — 신용 경색")

    # IG 스프레드
    if ig_spread is not None:
        if ig_spread < 100:
            score += 0.5
            signals.append(f"IG 스프레드 {ig_spread:.0f}bp — 투자등급 안정")
        elif ig_spread > 200:
            score -= 0.5
            signals.append(f"IG 스프레드 {ig_spread:.0f}bp — 투자등급 경고")

    # 역레포 (음수 변화 = 유동성이 시장으로 방출)
    if rrp_change_pct is not None:
        if rrp_change_pct < -10:
            score += 0.5
            signals.append(f"역레포 {rrp_change_pct:+.1f}% — 유동성 방출")
        elif rrp_change_pct > 10:
            score -= 0.5
            signals.append(f"역레포 {rrp_change_pct:+.1f}% — 유동성 흡수")

    if score >= 1.5:
        regime, label = "abundant", "풍부"
    elif score <= -1.5:
        regime, label = "tight", "긴축"
    else:
        regime, label = "normal", "정상"

    return LiquidityRegime(
        regime=regime,
        regimeLabel=label,
        score=round(score, 1),
        signals=tuple(signals),
    )


# ══════════════════════════════════════
# 설비투자 압력 (투자전략 32)
# ══════════════════════════════════════


@dataclass(frozen=True)
class CapexPressure:
    """신용스프레드 기반 설비투자 압력."""

    pressure: str  # "easing" | "neutral" | "tightening"
    pressureLabel: str  # "완화" | "중립" | "긴축"
    spreadLevel: float  # HY 스프레드 (bps)
    spreadChange: float  # 변화 (bps)
    description: str


def capexPressure(hySpread: float, hySpreadChange: float) -> CapexPressure:
    """신용스프레드 → 설비투자 압력.

    투자전략 32: 신용스프레드는 곧 설비투자 조정압력이다.
    HY 스프레드 상승 → 기업 자금조달 비용 증가 → 설비투자 축소.

    Args:
        hySpread: HY 스프레드 (bps)
        hySpreadChange: HY 스프레드 3개월 변화 (bps)
    """
    if hySpreadChange > 100 or hySpread > 500:
        return CapexPressure(
            pressure="tightening",
            pressureLabel="긴축",
            spreadLevel=round(hySpread, 0),
            spreadChange=round(hySpreadChange, 0),
            description=f"HY 스프레드 {hySpread:.0f}bp ({hySpreadChange:+.0f}bp) — 설비투자 축소 압력 강화",
        )
    elif hySpreadChange < -50 or hySpread < 350:
        return CapexPressure(
            pressure="easing",
            pressureLabel="완화",
            spreadLevel=round(hySpread, 0),
            spreadChange=round(hySpreadChange, 0),
            description=f"HY 스프레드 {hySpread:.0f}bp ({hySpreadChange:+.0f}bp) — 설비투자 환경 개선",
        )
    else:
        return CapexPressure(
            pressure="neutral",
            pressureLabel="중립",
            spreadLevel=round(hySpread, 0),
            spreadChange=round(hySpreadChange, 0),
            description=f"HY 스프레드 {hySpread:.0f}bp ({hySpreadChange:+.0f}bp) — 설비투자 중립",
        )
