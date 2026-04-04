"""경제 사이클 판별 + 자산 해석 + 멀티플 밴드 + 전환 시퀀스 + 금리 분해.

순수 데이터 + 판정 함수. 외부 의존성 없음.
core/ 계층 소속 — gather(수집), macro(시장 해석), analysis(기업 해석) 에서 사용.

사이클 4국면: contraction(침체) → recovery(회복) → expansion(확장) → slowdown(둔화)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

# ══════════════════════════════════════
# 데이터 구조
# ══════════════════════════════════════


@dataclass(frozen=True)
class CyclePhase:
    """경제 사이클 판별 결과."""

    phase: str  # "contraction" | "recovery" | "expansion" | "slowdown"
    label: str  # "침체" | "회복" | "확장" | "둔화"
    confidence: str  # "high" | "medium" | "low"
    signals: tuple[str, ...]  # 판정 근거 문장
    sectorStrategy: dict[str, str] = field(default_factory=dict)
    # cyclicality → "overweight" | "neutral" | "underweight"

    def __repr__(self) -> str:
        return f"{self.label} ({self.confidence}) — {', '.join(self.signals[:3])}"


@dataclass(frozen=True)
class TransitionSignal:
    """사이클 전환 시퀀스 감지 결과."""

    fromPhase: str  # 현재 국면
    toPhase: str  # 전환 목표 국면
    progress: int  # 0-100 (발현된 신호 비율)
    triggered: tuple[str, ...]  # 이미 발현된 신호
    pending: tuple[str, ...]  # 아직 발현 안 된 신호

    def __repr__(self) -> str:
        return f"{PHASE_LABELS.get(self.fromPhase, self.fromPhase)}→{PHASE_LABELS.get(self.toPhase, self.toPhase)} {self.progress}%"


@dataclass(frozen=True)
class RateDecomposition:
    """장기금리 3요소 분해 (DKW 근사)."""

    nominal: float  # 명목 금리 (%)
    expectedInflation: float  # 기대인플레이션 — BEI (%)
    realRate: float  # 실질금리 — TIPS (%)
    termPremium: float  # 기간프리미엄 — 잔차 (%)


@dataclass(frozen=True)
class GoldDrivers:
    """금 가격 3요인 해석."""

    realRateEffect: str  # "상승압력" | "하락압력" | "중립"
    dollarEffect: str  # "상승압력" | "하락압력" | "중립"
    safeHavenEffect: str  # "상승압력" | "중립"
    dominant: str  # 지배적 요인


@dataclass(frozen=True)
class VixRegime:
    """VIX 구간 판정."""

    level: float
    zone: str  # "complacent" | "normal" | "anxious" | "fear" | "extreme_fear" | "panic"
    zoneLabel: str  # "낙관" | "정상" | "불안" | "공포" | "극단공포" | "패닉"
    buySignal: int  # 0 = 없음, 1-3 = 분할매수 1~3차


@dataclass(frozen=True)
class AssetSignal:
    """개별 자산의 현재 신호."""

    asset: str  # "shortRate" | "longRate" | "fx" | "gold" | "vix"
    label: str  # "단기금리" | "장기금리" | "환율" | "금" | "VIX"
    level: float | None
    change: float | None  # 전기대비 변화 (%, bp 등)
    interpretation: str  # 해석 문장
    implication: str  # "성장기대↑" | "긴축기대" | "위험회피" 등


@dataclass(frozen=True)
class MultipleBand:
    """멀티플 정규분포 밴드."""

    metric: str  # "PER" | "PBR"
    current: float
    mean: float
    std: float
    percentile: float  # 0-100
    zone: str  # "cheap" | "fair" | "expensive"
    zLabel: str  # "저평가" | "적정" | "고평가"


# ══════════════════════════════════════
# 사이클 판별
# ══════════════════════════════════════

PHASE_LABELS = {
    "contraction": "침체",
    "recovery": "회복",
    "expansion": "확장",
    "slowdown": "둔화",
}

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
    """매크로 지표로 경제 사이클 4국면 판별.

    Args:
        indicators: 키-값 dict. 지원 키:
            - hy_spread: 하이일드 스프레드 (bp)
            - term_spread: 장단기 스프레드 (10Y-2Y, %)
            - vix: CBOE VIX
            - gold_yoy: 금 가격 YoY 변화율 (%)
            - cli_mom: 경기선행지수 전월비 변화
            - hy_spread_3m_change: HY 스프레드 3개월 변화 (bp)
            - cpi_yoy: CPI YoY (%)
            - bei_10y: 10년 BEI 기대인플레이션 (%)

    Returns:
        CyclePhase 판별 결과
    """
    signals: list[str] = []
    scores = {"contraction": 0, "recovery": 0, "expansion": 0, "slowdown": 0}

    hy = indicators.get("hy_spread")
    hy_chg = indicators.get("hy_spread_3m_change")
    ts = indicators.get("term_spread")
    vix = indicators.get("vix")
    gold_yoy = indicators.get("gold_yoy")
    cli_mom = indicators.get("cli_mom")
    cpi_yoy = indicators.get("cpi_yoy")
    bei_10y = indicators.get("bei_10y")

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
    if gold_yoy is not None:
        if gold_yoy > 15:
            scores["contraction"] += 1
            scores["slowdown"] += 1
            signals.append(f"금 급등 (YoY {gold_yoy:+.1f}%)")
        elif gold_yoy < -5:
            scores["recovery"] += 1
            scores["expansion"] += 1
            signals.append(f"금 하락 (YoY {gold_yoy:+.1f}%)")

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
    if cpi_yoy is not None:
        if cpi_yoy > 4.0:
            scores["slowdown"] += 2
            signals.append(f"CPI {cpi_yoy:.1f}% — 물가 과열, 둔화 전조")
        elif cpi_yoy > 3.0:
            scores["expansion"] += 1
            signals.append(f"CPI {cpi_yoy:.1f}% — 인플레 동반 확장")
        elif cpi_yoy < 1.5:
            scores["contraction"] += 1
            signals.append(f"CPI {cpi_yoy:.1f}% — 디플레 우려")

    if bei_10y is not None:
        if bei_10y > 2.8:
            scores["slowdown"] += 1
            signals.append(f"BEI {bei_10y:.2f}% — 기대인플레 상승, 긴축 압력")
        elif bei_10y < 1.8:
            scores["contraction"] += 1
            scores["recovery"] += 1
            signals.append(f"BEI {bei_10y:.2f}% — 기대인플레 하락")

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


# ══════════════════════════════════════
# 5대 자산 해석
# ══════════════════════════════════════


def interpretAssets(indicators: dict[str, float | None]) -> list[AssetSignal]:
    """5대 자산의 현재 상태를 해석.

    Args:
        indicators: 키-값 dict. 지원 키:
            - short_rate / short_rate_change: 단기금리 (%, %p)
            - long_rate / long_rate_change: 장기금리 (%, %p)
            - bei_change: BEI 변화 (%p) — 장기금리 "왜" 해석용
            - real_rate_change: 실질금리 변화 (%p) — 장기금리 "왜" 해석용
            - fx_usdkrw / fx_change_pct: 원/달러 환율 (원, %)
            - rate_diff: 한미 금리차 (%p) — 환율 교차 해석용
            - rate_diff_change: 금리차 변화 (%p) — 환율 교차 해석용
            - gold / gold_yoy: 금 가격 ($/oz, %)
            - vix / vix_change: VIX (index, pts)
    """
    results: list[AssetSignal] = []

    # 1. 단기금리 (2년물 / 기준금리)
    sr = indicators.get("short_rate")
    sr_chg = indicators.get("short_rate_change")
    if sr is not None:
        if sr_chg is not None and sr_chg > 0.25:
            interp = f"단기금리 상승 ({sr:.2f}%, {sr_chg:+.2f}%p) — 긴축 기대"
            impl = "긴축기대"
        elif sr_chg is not None and sr_chg < -0.25:
            interp = f"단기금리 하락 ({sr:.2f}%, {sr_chg:+.2f}%p) — 완화 기대"
            impl = "완화기대"
        else:
            interp = f"단기금리 안정 ({sr:.2f}%)"
            impl = "중립"
        results.append(AssetSignal("shortRate", "단기금리", sr, sr_chg, interp, impl))

    # 2. 장기금리 (10년물) — DKW 분해로 "왜" 해석
    lr = indicators.get("long_rate")
    lr_chg = indicators.get("long_rate_change")
    bei_chg = indicators.get("bei_change")
    rr_chg = indicators.get("real_rate_change")
    if lr is not None:
        if lr_chg is not None and abs(lr_chg) > 0.3:
            # DKW 분해: BEI 변화 vs 실질금리 변화로 주도 요인 판별
            driver = ""
            if bei_chg is not None and rr_chg is not None:
                if abs(bei_chg) > abs(rr_chg):
                    driver = f" (BEI {bei_chg:+.2f}%p 주도 → 인플레 기대 변화)"
                else:
                    driver = f" (실질금리 {rr_chg:+.2f}%p 주도 → 성장 기대 변화)"
            if lr_chg > 0.3:
                impl = "인플레기대↑" if (bei_chg and bei_chg > rr_chg if rr_chg else True) else "성장기대↑"
                interp = f"장기금리 상승 ({lr:.2f}%, {lr_chg:+.2f}%p){driver}"
            else:
                impl = "인플레기대↓" if (bei_chg and bei_chg < rr_chg if rr_chg else True) else "경기둔화"
                interp = f"장기금리 하락 ({lr:.2f}%, {lr_chg:+.2f}%p){driver}"
        else:
            interp = f"장기금리 안정 ({lr:.2f}%)"
            impl = "중립"
        results.append(AssetSignal("longRate", "장기금리", lr, lr_chg, interp, impl))

    # 3. 환율 (원/달러) — 금리차 교차 해석
    fx = indicators.get("fx_usdkrw")
    fx_chg = indicators.get("fx_change_pct")
    rate_diff = indicators.get("rate_diff")  # US금리 - KR금리
    rate_diff_chg = indicators.get("rate_diff_change")
    if fx is not None:
        # 기본 방향 해석
        if fx_chg is not None and fx_chg > 3:
            base = f"원화 약세 ({fx:,.0f}원, {fx_chg:+.1f}%)"
            impl = "위험회피"
        elif fx_chg is not None and fx_chg < -3:
            base = f"원화 강세 ({fx:,.0f}원, {fx_chg:+.1f}%)"
            impl = "위험선호"
        else:
            base = f"환율 안정 ({fx:,.0f}원)"
            impl = "중립"

        # 금리차 교차 해석: 금리차 확대→자본유출→원화약세, 축소→유입→강세
        rate_context = ""
        if rate_diff_chg is not None:
            if rate_diff_chg > 0.2:
                rate_context = f" — 한미 금리차 확대({rate_diff_chg:+.2f}%p), 자본유출 압력"
            elif rate_diff_chg < -0.2:
                rate_context = f" — 한미 금리차 축소({rate_diff_chg:+.2f}%p), 자본유입 기대"

        interp = base + rate_context
        results.append(AssetSignal("fx", "환율", fx, fx_chg, interp, impl))

    # 4. 금
    gold = indicators.get("gold")
    gold_yoy = indicators.get("gold_yoy")
    if gold is not None:
        if gold_yoy is not None and gold_yoy > 15:
            interp = f"금 급등 (${gold:,.0f}, YoY {gold_yoy:+.1f}%) — 인플레·불안심리"
            impl = "위험회피"
        elif gold_yoy is not None and gold_yoy < -5:
            interp = f"금 하락 (${gold:,.0f}, YoY {gold_yoy:+.1f}%) — 위험자산 선호"
            impl = "위험선호"
        else:
            interp = f"금 안정 (${gold:,.0f})"
            impl = "중립"
        results.append(AssetSignal("gold", "금", gold, gold_yoy, interp, impl))

    # 5. VIX
    vix = indicators.get("vix")
    vix_chg = indicators.get("vix_change")
    if vix is not None:
        if vix > 30:
            interp = f"VIX 급등 ({vix:.1f}) — 극단적 공포"
            impl = "공포"
        elif vix > 20:
            interp = f"VIX 상승 ({vix:.1f}) — 불확실성 확대"
            impl = "불확실성"
        elif vix < 15:
            interp = f"VIX 안정 ({vix:.1f}) — 시장 낙관"
            impl = "낙관"
        else:
            interp = f"VIX 보통 ({vix:.1f})"
            impl = "중립"
        results.append(AssetSignal("vix", "VIX", vix, vix_chg, interp, impl))

    return results


# ══════════════════════════════════════
# 멀티플 밴드
# ══════════════════════════════════════


def calcMultipleBand(
    values: list[float],
    current: float,
    metric: str = "PER",
) -> MultipleBand | None:
    """과거 멀티플 시계열에서 정규분포 밴드 계산.

    Args:
        values: 과거 멀티플 값 리스트 (최소 5개)
        current: 현재 멀티플
        metric: "PER" | "PBR" | "EV/EBITDA" 등

    Returns:
        MultipleBand 또는 데이터 부족 시 None
    """
    # 유효값 필터 (0 이하, 극단값 제거)
    valid = [v for v in values if v is not None and 0 < v < 200]
    if len(valid) < 5:
        return None

    mean = sum(valid) / len(valid)
    variance = sum((v - mean) ** 2 for v in valid) / len(valid)
    std = math.sqrt(variance) if variance > 0 else 0.01

    if std == 0:
        return None

    # z-score
    z = (current - mean) / std

    # 정규분포 CDF 근사 (Abramowitz & Stegun)
    percentile = _norm_cdf(z) * 100

    # zone 판정 (+-1 표준편차)
    if z < -1:
        zone, zLabel = "cheap", "저평가"
    elif z > 1:
        zone, zLabel = "expensive", "고평가"
    else:
        zone, zLabel = "fair", "적정"

    return MultipleBand(
        metric=metric,
        current=current,
        mean=round(mean, 2),
        std=round(std, 2),
        percentile=round(percentile, 1),
        zone=zone,
        zLabel=zLabel,
    )


def _norm_cdf(z: float) -> float:
    """표준정규분포 CDF 근사 (|오차| < 7.5e-8)."""
    # Abramowitz & Stegun 26.2.17
    if z < -6:
        return 0.0
    if z > 6:
        return 1.0
    a1, a2, a3, a4, a5 = 0.254829592, -0.284496736, 1.421413741, -1.453152027, 1.061405429
    p = 0.3275911
    sign = 1.0
    if z < 0:
        sign = -1.0
        z = -z
    t = 1.0 / (1.0 + p * z)
    y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * math.exp(-z * z / 2)
    return 0.5 * (1.0 + sign * y)


# ══════════════════════════════════════
# 금리 전망
# ══════════════════════════════════════


def rateOutlook(indicators: dict[str, float | None]) -> dict:
    """금리·물가·고용 조합으로 금리 방향 전망.

    Args:
        indicators:
            - fed_funds / base_rate: 현재 정책금리 (%)
            - cpi_yoy: CPI YoY (%)
            - core_cpi_yoy: Core CPI YoY (%)
            - unemployment: 실업률 (%)
            - payrolls_change: 비농업고용 변화 (천명)

    Returns:
        dict: direction, confidence, reasoning
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
) -> TransitionSignal | None:
    """현재 국면에서 다음 국면으로의 전환 시퀀스를 감지.

    Args:
        currentPhase: 현재 사이클 국면
        indicators: 매크로 지표 dict (classifyCycle과 동일 키 + 추가)
            - hy_spread_3m_change: HY 스프레드 3개월 변화 (bp)
            - gold_yoy: 금 가격 YoY (%)
            - long_rate_change: 장기금리 3개월 변화 (%p)
            - vix: VIX 수준
            - term_spread: 장단기 스프레드 (%)

    Returns:
        TransitionSignal 또는 전환 징후 없으면 None
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
    gold_yoy = indicators.get("gold_yoy")
    lr_chg = indicators.get("long_rate_change")
    vix = indicators.get("vix")
    ts = indicators.get("term_spread")
    bei = indicators.get("bei_10y")

    signal_checks: dict[str, bool] = {
        "hy_spread_declining": hy_chg is not None and hy_chg < -30,
        "hy_spread_widening": hy_chg is not None and hy_chg > 50,
        "hy_spread_stable": hy_chg is not None and abs(hy_chg) < 30,
        "gold_declining": gold_yoy is not None and gold_yoy < -3,
        "gold_surging": gold_yoy is not None and gold_yoy > 15,
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
        if signal_checks.get(signal_name, False):
            triggered.append(signal_name)
        else:
            pending.append(signal_name)

    if not triggered:
        return None

    progress = round(len(triggered) / len(sequence) * 100)
    return TransitionSignal(
        fromPhase=currentPhase,
        toPhase=nextPhase,
        progress=progress,
        triggered=tuple(triggered),
        pending=tuple(pending),
    )


# ══════════════════════════════════════
# 장기금리 DKW 근사 분해
# ══════════════════════════════════════


def decomposeLongRate(
    nominal: float,
    bei: float,
    tips: float,
    fed_funds: float | None = None,
) -> RateDecomposition:
    """10년 명목금리를 3요소로 분해 (DKW 모델 근사).

    Args:
        nominal: 10년 명목금리 DGS10 (%)
        bei: 10년 BEI T10YIE (%)  — 기대인플레이션
        tips: 10년 TIPS DFII10 (%) — 실질금리
        fed_funds: 정책금리 (%) — 기간프리미엄 보정용 (optional)

    Returns:
        RateDecomposition
    """
    # 기간프리미엄 = 명목 - BEI - TIPS 실질금리의 잔차 근사
    term_premium = nominal - bei - tips
    return RateDecomposition(
        nominal=round(nominal, 3),
        expectedInflation=round(bei, 3),
        realRate=round(tips, 3),
        termPremium=round(term_premium, 3),
    )


# ══════════════════════════════════════
# 금 3요인 해석
# ══════════════════════════════════════


def interpretGoldDrivers(
    gold_yoy: float,
    real_rate_change: float,
    dxy_change_pct: float,
    vix: float,
) -> GoldDrivers:
    """금 가격의 3요인 분해 해석.

    Args:
        gold_yoy: 금 YoY 변화율 (%)
        real_rate_change: 실질금리(DFII10) 변화 (%p, 양수=상승)
        dxy_change_pct: 달러인덱스 변화율 (%, 양수=달러강세)
        vix: VIX 수준

    Returns:
        GoldDrivers
    """
    # 실질금리 역상관: 실질금리 하락 → 금 상승압력
    if real_rate_change < -0.3:
        rr = "상승압력"
    elif real_rate_change > 0.3:
        rr = "하락압력"
    else:
        rr = "중립"

    # 달러 역상관: 달러 약세 → 금 상승압력
    if dxy_change_pct < -2:
        dx = "상승압력"
    elif dxy_change_pct > 2:
        dx = "하락압력"
    else:
        dx = "중립"

    # 안전자산 수요: VIX 급등 → 금 상승
    sh = "상승압력" if vix > 25 else "중립"

    # 지배적 요인 판별
    effects = {"실질금리": rr, "달러": dx, "안전자산": sh}
    up_count = sum(1 for v in effects.values() if v == "상승압력")
    down_count = sum(1 for v in effects.values() if v == "하락압력")

    if up_count > down_count:
        dominant = next(k for k, v in effects.items() if v == "상승압력")
    elif down_count > up_count:
        dominant = next(k for k, v in effects.items() if v == "하락압력")
    else:
        dominant = "복합"

    return GoldDrivers(
        realRateEffect=rr,
        dollarEffect=dx,
        safeHavenEffect=sh,
        dominant=dominant,
    )


# ══════════════════════════════════════
# VIX 구간 판정
# ══════════════════════════════════════


def classifyVixRegime(vix: float) -> VixRegime:
    """VIX 수준으로 시장 공포 구간 판정 + 분할매수 신호.

    Args:
        vix: CBOE VIX 수준

    Returns:
        VixRegime
    """
    if vix >= 40:
        return VixRegime(vix, "panic", "패닉", 3)
    if vix >= 30:
        return VixRegime(vix, "extreme_fear", "극단공포", 2)
    if vix >= 25:
        return VixRegime(vix, "fear", "공포", 1)
    if vix >= 20:
        return VixRegime(vix, "anxious", "불안", 0)
    if vix >= 15:
        return VixRegime(vix, "normal", "정상", 0)
    return VixRegime(vix, "complacent", "낙관", 0)


# ══════════════════════════════════════
# Copper/Gold Ratio (경기 선행)
# ══════════════════════════════════════


@dataclass(frozen=True)
class CopperGoldSignal:
    """구리/금 비율 경기 선행 신호."""

    ratio: float
    direction: str  # "rising" | "stable" | "falling"
    directionLabel: str  # "상승" | "안정" | "하락"
    implication: str  # "expansion" | "neutral" | "contraction"
    description: str


def copperGoldRatio(
    copper: float,
    gold: float,
    prevCopper: float | None = None,
    prevGold: float | None = None,
) -> CopperGoldSignal:
    """Copper/Gold Ratio → 경기 선행.

    구리 = 산업수요, 금 = 안전자산. 비율 상승 = 경기 낙관.
    10Y 국채 수익률과 강한 상관.
    """
    if gold <= 0:
        return CopperGoldSignal(0, "stable", "판별불가", "neutral", "금 가격 데이터 없음")

    ratio = copper / gold
    prev_ratio = (prevCopper / prevGold) if prevCopper and prevGold and prevGold > 0 else None

    if prev_ratio is not None:
        change_pct = ((ratio - prev_ratio) / prev_ratio) * 100
    else:
        change_pct = 0.0

    if change_pct > 3:
        return CopperGoldSignal(round(ratio, 4), "rising", "상승", "expansion",
                                f"Cu/Au {ratio:.4f} ({change_pct:+.1f}%) — 산업수요 확대, 경기 낙관")
    elif change_pct < -3:
        return CopperGoldSignal(round(ratio, 4), "falling", "하락", "contraction",
                                f"Cu/Au {ratio:.4f} ({change_pct:+.1f}%) — 안전자산 선호, 경기 비관")
    else:
        return CopperGoldSignal(round(ratio, 4), "stable", "안정", "neutral",
                                f"Cu/Au {ratio:.4f} ({change_pct:+.1f}%) — 안정")


# ══════════════════════════════════════
# BEI / Real Rate 분해
# ══════════════════════════════════════


@dataclass(frozen=True)
class RealRateRegimeResult:
    """실질금리 + 기대인플레이션 분해 결과."""

    realRate: float  # TIPS 실질금리 (%)
    bei: float  # Breakeven Inflation (%)
    regime: str  # "tightening" | "reflation" | "goldilocks" | "deflation"
    regimeLabel: str  # "긴축" | "리플레이션" | "골디락스" | "디플레"
    description: str


def realRateRegime(realRate: float, bei: float) -> RealRateRegimeResult:
    """실질금리 + BEI → 금융환경 4분면.

    | | BEI 상승 | BEI 하락 |
    |실질금리 상승| 긴축 | 디플레 위험 |
    |실질금리 하락| 리플레이션 | 골디락스 |

    (방향 판별은 호출자가 전기 대비 제공)
    여기서는 수준 기반으로 판별.
    """
    if realRate > 2.0 and bei < 2.0:
        return RealRateRegimeResult(round(realRate, 2), round(bei, 2), "deflation", "디플레위험",
                                    f"실질금리 {realRate:.2f}% 높음 + BEI {bei:.2f}% 낮음 — 디플레이션 위험")
    elif realRate > 1.5 and bei > 2.5:
        return RealRateRegimeResult(round(realRate, 2), round(bei, 2), "tightening", "긴축",
                                    f"실질금리 {realRate:.2f}% + BEI {bei:.2f}% 동반 상승 — 금융 긴축")
    elif realRate < 0.5 and bei > 2.5:
        return RealRateRegimeResult(round(realRate, 2), round(bei, 2), "reflation", "리플레이션",
                                    f"실질금리 {realRate:.2f}% 낮음 + BEI {bei:.2f}% 높음 — 리플레이션")
    elif realRate < 1.0 and bei < 2.0:
        return RealRateRegimeResult(round(realRate, 2), round(bei, 2), "goldilocks", "골디락스",
                                    f"실질금리 {realRate:.2f}% + BEI {bei:.2f}% 모두 안정 — 골디락스")
    else:
        return RealRateRegimeResult(round(realRate, 2), round(bei, 2), "neutral", "중립",
                                    f"실질금리 {realRate:.2f}%, BEI {bei:.2f}% — 뚜렷한 방향 없음")
