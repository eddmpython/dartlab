"""경제 사이클 판별 + 자산 해석 + 멀티플 밴드.

순수 데이터 + 판정 함수. 외부 의존성 없음.
core/ 계층 소속 — gather(수집)와 analysis(소비) 양쪽에서 사용.

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
            - fx_usdkrw / fx_change_pct: 원/달러 환율 (원, %)
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

    # 2. 장기금리 (10년물)
    lr = indicators.get("long_rate")
    lr_chg = indicators.get("long_rate_change")
    if lr is not None:
        if lr_chg is not None and lr_chg > 0.3:
            interp = f"장기금리 상승 ({lr:.2f}%, {lr_chg:+.2f}%p) — 성장·물가 기대↑"
            impl = "성장기대↑"
        elif lr_chg is not None and lr_chg < -0.3:
            interp = f"장기금리 하락 ({lr:.2f}%, {lr_chg:+.2f}%p) — 경기둔화 우려"
            impl = "경기둔화"
        else:
            interp = f"장기금리 안정 ({lr:.2f}%)"
            impl = "중립"
        results.append(AssetSignal("longRate", "장기금리", lr, lr_chg, interp, impl))

    # 3. 환율 (원/달러)
    fx = indicators.get("fx_usdkrw")
    fx_chg = indicators.get("fx_change_pct")
    if fx is not None:
        if fx_chg is not None and fx_chg > 3:
            interp = f"원화 약세 ({fx:,.0f}원, {fx_chg:+.1f}%) — 자본 유출·위험회피"
            impl = "위험회피"
        elif fx_chg is not None and fx_chg < -3:
            interp = f"원화 강세 ({fx:,.0f}원, {fx_chg:+.1f}%) — 자본 유입·위험선호"
            impl = "위험선호"
        else:
            interp = f"환율 안정 ({fx:,.0f}원)"
            impl = "중립"
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
