"""역사적 매크로 — bullishSignalFlags + hyCompressionToExpansion (회복기/강세 통계).

_monthsSinceRecessionEnd + hyCompressionToExpansion + bullishSignalFlags + signature 매핑 테이블.
"""

from __future__ import annotations

import numpy as np

from dartlab.macro.corporate._historicalContextSeries import (
    _NBER_RECESSIONS,
    _deltaN,
    _isRecession,
    _monthsToNextRecession,
)
from dartlab.macro.corporate._historicalContextTypes import (
    BullishSignals,
    HistoricalEvent,
    HYCompressionHistory,
)


def _monthsSinceRecessionEnd(month: str) -> int | None:
    """마지막 침체 종료 이후 경과 개월. 침체 중이면 None."""
    if _isRecession(month):
        return None
    for _, end in reversed(_NBER_RECESSIONS):
        if month > end:
            y1, m1 = int(end[:4]), int(end[5:7])
            y2, m2 = int(month[:4]), int(month[5:7])
            return (y2 - y1) * 12 + (m2 - m1)
    return None


def hyCompressionToExpansion(
    hyMonthly: dict[str, float],
    *,
    thresholdBp: float = -1.0,
) -> HYCompressionHistory:
    """HY 스프레드 3개월 급락 (신용 완화) → 확장 통계.

    Capabilities:
        HY OAS 월별 시리즈에서 3 개월 변화 ≤ thresholdBp (기본 -1.0 %p = -100bp)
        구간을 추출 → NBER 침체 종료 12 개월 이내 발생한 케이스 (회복 초기
        신용 완화) 의 평균 확장 지속 개월 계산. 매크로 회복 통계 진단.

    Args:
        hyMonthly: ``{"YYYY-MM": HY OAS %}`` 월별 dict.
        thresholdBp: 급락 임계 (%p). 기본 -1.0 = -100bp 이하.

    Returns:
        HYCompressionHistory — totalCompressions/avgExpansionMonths/currentDelta/
        description.

    Example:
        >>> r = hyCompressionToExpansion({"2009-04": 12.0, "2009-07": 9.5, ...})
        >>> r.avgExpansionMonths
        62.0

    Guide:
        avg expansion 60~80 개월 = 큰 신용 완화 직후 장기 확장. currentDelta 가
        threshold 이하면 "현재 신용 완화 진행 중" 인용.

    When:
        ``buildHistoricalContext`` 내부 + AI "신용 완화 이후 확장 가능성" 답변.

    How:
        _deltaN(3M) → threshold 매칭 → _monthsSinceRecessionEnd ≤ 12 필터 →
        _monthsToNextRecession 평균.

    Requires:
        FRED BAMLH0A0HYM2 월별 + NBER 침체 일자 정적 테이블.

    Raises:
        없음.

    See Also:
        - bullishSignalFlags : 8 신호 동시 점등 통계
        - buildHistoricalContext : 본 함수 호출 진입점

    AIContext:
        avgExpansionMonths + totalCompressions 두 필드 인용으로 "신용 완화 후
        평균 N 개월 확장" 답변 완성.

    LLM Specifications:
        AntiPatterns:
            - 침체 기간 내 압축은 제외 (회복 초기 압축만 카운트)
            - thresholdBp 양수 입력 (음수가 정상)
        OutputSchema:
            HYCompressionHistory ``(totalCompressions, avgExpansionMonths,
            currentDelta, description)``.
        Prerequisites: HY OAS 월별 시리즈 ≥ 1980 이상.
        Freshness: 월말 단순화.
        Dataflow: hyMonthly → deltaN → 회복기 필터 → 평균.
        TargetMarkets: US (HY OAS 풀세트). KR 미지원.
    """
    d3 = _deltaN(hyMonthly, 3)
    compressions: list[tuple[str, float, int | None]] = []

    for m in sorted(d3.keys()):
        if d3[m] < thresholdBp:
            since = _monthsSinceRecessionEnd(m)
            compressions.append((m, d3[m], since))

    # 침체 직후 급락인 경우 (회복 초기) — 이후 확장 기간
    recovery_compressions = [c for c in compressions if c[2] is not None and c[2] <= 12]
    expansion_durations = []
    for m, _, _ in recovery_compressions:
        mtr = _monthsToNextRecession(m)
        if mtr < 999:
            expansion_durations.append(mtr)

    avg_exp = float(np.mean(expansion_durations)) if expansion_durations else None

    latest = max(d3.keys()) if d3 else None
    currentDelta = d3.get(latest) if latest else None

    desc_parts = [
        f"HY 스프레드 3개월 -{abs(thresholdBp) * 100:.0f}bp 이상 급락 (신용 완화): 과거 {len(compressions)}회"
    ]
    if avg_exp:
        desc_parts.append(f"회복 초기 급락 후 평균 {avg_exp:.0f}개월 확장 지속")
    if currentDelta is not None and currentDelta < thresholdBp:
        desc_parts.append(f"현재 3개월 {currentDelta * 100:+.0f}bp — 신용 완화 진행 중")

    return HYCompressionHistory(
        totalCompressions=len(compressions),
        avgExpansionMonths=round(avg_exp, 1) if avg_exp else None,
        currentDelta=round(currentDelta, 2) if currentDelta is not None else None,
        description=". ".join(desc_parts),
    )


def bullishSignalFlags(
    data: dict[str, dict[str, float] | None],
) -> BullishSignals:
    """호황/회복 신호 감지 — 위기 경고등의 반대.

    Capabilities:
        8 긍정 신호 (HY<4%/HY축소/YC양수/실업↓/VIX<18/NFCI완화/산업생산↑/
        CPI안정) 의 현재 점등 수 + 과거 4 개+ 동시 점등 횟수 + 이후 평균 확장
        지속 개월 + 유사 시기 list. 위기 경고등의 반대.

    Args:
        data: ``{"hy_spread"/"hy_spread_d3"/"spread_10y2y"/"ur_d6"/"vix"/"nfci"/
            "ip_yoy"/"cpi_yoy": {"YYYY-MM": value}}`` 월별 dict 모음.

    Returns:
        BullishSignals — activeSignals/signalCount/historicalOccurrences/
        avgExpansionMonths/similarPeriods(list[dict])/description.

    Example:
        >>> r = bullishSignalFlags({"hy_spread": {...}, ...})
        >>> r.signalCount, r.avgExpansionMonths
        (5, 48.0)

    Guide:
        signalCount ≥ 4 = 호황 진행, ≥ 6 = 강한 호황. similarPeriods 와 매칭하면
        과거 사례 인용 가능.

    When:
        ``buildHistoricalContext`` 내부 + AI "지금 호황 신호 몇 개" 답변.

    How:
        각 신호 임계 매칭 → active 리스트 + 4+ 동시 점등 월 → 이후 확장 지속
        평균 → 현재 active 와 ≥ 3 overlap 인 과거 5 케이스.

    Requires:
        FRED HY/yield curve/UNRATE/VIX/NFCI/IP/CPI 월별 + NBER 침체 일자.

    Raises:
        없음.

    See Also:
        - hyCompressionToExpansion : 신용 완화 단일 신호 통계
        - simultaneousWarningFlags : 반대 (위기 경고등)
        - buildHistoricalContext : 본 함수 호출 진입점

    AIContext:
        activeSignals + similarPeriods 1 건 인용으로 "지금 (2008-02 와 유사) 4 개
        호황 신호 점등" 1 문장 답변.

    LLM Specifications:
        AntiPatterns:
            - signalCount 만 인용 + similarPeriods 미노출
            - 침체 중 (mtr=999) 케이스도 expansion 평균에 포함 (필터링 필요)
            - 8 신호 임계 임의 변경 (재현성 손실)
        OutputSchema:
            BullishSignals ``(activeSignals, signalCount, historicalOccurrences,
            avgExpansionMonths, similarPeriods, description)``.
        Prerequisites: 8 시리즈 월별 cache.
        Freshness: 월간.
        Dataflow: data → 8 신호 임계 → active + 과거 카운트 → 평균.
        TargetMarkets: US (NFCI 등 US 한정). KR 미지원.
    """
    hy = data.get("hy_spread") or {}
    hyD3 = data.get("hy_spread_d3") or {}
    yc = data.get("spread_10y2y") or {}
    urD6 = data.get("ur_d6") or {}
    vixD = data.get("vix") or {}
    nfciD = data.get("nfci") or {}
    ipYoy = data.get("ip_yoy") or {}
    cpiYoy = data.get("cpi_yoy") or {}

    all_months = sorted(set(hy.keys()) & set(yc.keys())) if hy and yc else []
    latest = all_months[-1] if all_months else None

    active: list[str] = []
    if latest:
        if hy.get(latest, 10) < 4:
            active.append("HY<4%")
        if hyD3.get(latest, 0) < -0.3:
            active.append("HY축소")
        if yc.get(latest, 0) > 1.0:
            active.append("YC양수")
        if urD6.get(latest, 0) < 0:
            active.append("실업↓")
        if vixD.get(latest, 30) < 18:
            active.append("VIX안정")
        if nfciD.get(latest, 0) < -0.5:
            active.append("NFCI완화")
        if ipYoy.get(latest, 0) > 2:
            active.append("산업생산↑")
        cpi = cpiYoy.get(latest, 5)
        if 1 <= cpi <= 3:
            active.append("CPI안정")

    # 역사적 4개+ 동시 점등 통계
    multi_bull: list[tuple[str, list[str]]] = []
    for m in all_months:
        signals: list[str] = []
        if hy.get(m, 10) < 4:
            signals.append("HY<4%")
        if hyD3.get(m, 0) < -0.3:
            signals.append("HY축소")
        if yc.get(m, 0) > 1.0:
            signals.append("YC양수")
        if urD6.get(m, 0) < 0:
            signals.append("실업↓")
        if vixD.get(m, 30) < 18:
            signals.append("VIX안정")
        if nfciD.get(m, 0) < -0.5:
            signals.append("NFCI완화")
        if ipYoy.get(m, 0) > 2:
            signals.append("산업생산↑")
        cpi_v = cpiYoy.get(m, 5)
        if 1 <= cpi_v <= 3:
            signals.append("CPI안정")
        if len(signals) >= 4:
            multi_bull.append((m, signals))

    # 4개+ 호황 신호 후 확장 지속 기간
    expansion_months = []
    for m, _ in multi_bull:
        mtr = _monthsToNextRecession(m)
        if mtr < 999 and not _isRecession(m):
            expansion_months.append(mtr)
    avg_exp = float(np.mean(expansion_months)) if expansion_months else None

    # 유사 시기
    similar: list[dict] = []
    if active:
        active_set = set(active)
        for m, signals in reversed(multi_bull):
            if m == latest:
                continue
            overlap = set(signals) & active_set
            if len(overlap) >= 3:
                mtr = _monthsToNextRecession(m)
                outcome = f"{mtr}개월 확장 지속" if mtr < 999 and not _isRecession(m) else "확장 중"
                similar.append({"month": m, "signals": signals, "outcome": outcome, "overlap": list(overlap)})
            if len(similar) >= 5:
                break

    desc = f"호황 신호 {len(active)}개"
    if active:
        desc += f" ({', '.join(active)})"
    desc += f". 과거 4개+ 동시 {len(multi_bull)}회"
    if avg_exp:
        desc += f", 이후 평균 {avg_exp:.0f}개월 확장"

    return BullishSignals(
        activeSignals=active,
        signalCount=len(active),
        historicalOccurrences=len(multi_bull),
        avgExpansionMonths=round(avg_exp, 1) if avg_exp else None,
        similarPeriods=similar,
        description=desc,
    )


# ══════════════════════════════════════
# 역사적 사건 매칭
# ══════════════════════════════════════

_HISTORICAL_EPOCHS: list[dict] = [
    {
        "name": "볼커 긴축 (1980-81)",
        "period": ("1980-01", "1982-11"),
        "signature": {"cpi_yoy_high": 8, "ff_high": 10, "ur_high": 7},
        "outcome": "인플레 진압 → 1983~89 장기 확장",
        "nextRisk": "골디락스",
        "nextEvent": "1983~89 장기 확장",
    },
    {
        "name": "골디락스 (1995-98)",
        "period": ("1995-01", "1998-06"),
        "signature": {"cpi_yoy_low": 3, "ur_low": 5.5, "vix_low": 20, "yc_positive": True},
        "outcome": "저인플레 + 완전고용 + 주식 강세 42개월",
        "nextRisk": "자산 버블 붕괴",
        "nextEvent": "IT 버블 정점 (2000) → NASDAQ -78%",
    },
    {
        "name": "IT 버블 정점 (2000)",
        "period": ("1999-06", "2000-09"),
        "signature": {"vix_low": 25, "yc_inverted": True, "ip_strong": True},
        "outcome": "NASDAQ -78%, 2001-03 침체 시작",
        "nextRisk": "신용 충격",
        "nextEvent": "2001 침체 → 2001-03~2001-11",
    },
    {
        "name": "금융위기 (2008)",
        "period": ("2007-12", "2009-03"),
        "signature": {"hy_high": 8, "nfci_tight": True, "ur_rising": True, "ip_falling": True},
        "outcome": "S&P -57%, 실업률 10%, 2009-03 저점 후 V자 반등",
        "nextRisk": "연착륙",
        "nextEvent": "2009 대반등 → 112개월 확장",
    },
    {
        "name": "2009 대반등",
        "period": ("2009-03", "2010-06"),
        "signature": {"hy_falling": True, "nfci_easing": True, "vix_falling": True},
        "outcome": "S&P +80% (12개월), 112개월 확장 시작",
        "nextRisk": "신용 충격",
        "nextEvent": "유럽 재정위기 (2011) → S&P -19%",
    },
    {
        "name": "유럽 재정위기 (2011)",
        "period": ("2011-07", "2011-12"),
        "signature": {"hy_high": 6, "vix_high": 30, "yc_positive": True},
        "outcome": "V자 반등, 위기는 유럽에 국한",
        "nextRisk": "골디락스",
        "nextEvent": "2012~2018 장기 확장",
    },
    {
        "name": "연준 긴축 쇼크 (2018말)",
        "period": ("2018-10", "2019-01"),
        "signature": {"hy_rising": True, "vix_high": 25, "yc_flat": True, "ff_rising": True},
        "outcome": "연준 피벗(금리 동결) → 2019 강세장",
        "nextRisk": "지정학/팬데믹",
        "nextEvent": "COVID 충격 (2020-03)",
    },
    {
        "name": "COVID 충격 (2020-03)",
        "period": ("2020-02", "2020-04"),
        "signature": {"vix_high": 40, "hy_high": 8, "nfci_tight": True, "ip_falling": True},
        "outcome": "역사상 최단 침체(2개월), V자 반등, 양적완화",
        "nextRisk": "인플레이션 충격",
        "nextEvent": "인플레 긴축 (2022) → CPI 9.1%",
    },
    {
        "name": "인플레 긴축 (2022)",
        "period": ("2022-01", "2022-12"),
        "signature": {"cpi_yoy_high": 5, "ff_rising": True, "yc_inverted": True},
        "outcome": "NASDAQ -33%, 하지만 침체 회피",
        "nextRisk": "골디락스",
        "nextEvent": "AI 강세장 (2023-24) → 연착륙",
    },
    {
        "name": "AI 강세장 (2023-24)",
        "period": ("2023-01", "2024-12"),
        "signature": {"vix_low": 20, "ur_low": 4.5, "ip_stable": True, "hy_low": 4},
        "outcome": "NASDAQ +85%, 연착륙 기대",
        "nextRisk": "AI 버블 붕괴",
        "nextEvent": "??? (진행 중)",
    },
]


# signature 조건 → (curr 키, 비교 함수 (값, 임계값) → bool)
# 임계값 없는 키는 sig 내 boolean flag 만 검사 (두 번째 인자 무시).
_SIGNATURE_CHECKS: list[tuple[str, str, object]] = [
    ("cpi_yoy_high", "cpi_yoy", lambda v, t: v >= t),
    ("cpi_yoy_low", "cpi_yoy", lambda v, t: v <= t),
    ("ff_high", "ff", lambda v, t: v >= t),
    ("ff_rising", "ff", lambda v, _t: v > 3),
    ("ur_high", "ur", lambda v, t: v >= t),
    ("ur_low", "ur", lambda v, t: v <= t),
    ("ur_rising", "ur_d6", lambda v, _t: v > 0.3),
    ("vix_high", "vix", lambda v, t: v >= t),
    ("vix_low", "vix", lambda v, t: v <= t),
    ("vix_falling", "vix", lambda v, _t: v < 20),
    ("hy_high", "hy", lambda v, t: v >= t),
    ("hy_low", "hy", lambda v, t: v <= t),
    ("hy_rising", "hy_d3", lambda v, _t: v > 0.5),
    ("hy_falling", "hy_d3", lambda v, _t: v < -0.5),
    ("yc_inverted", "yc", lambda v, _t: v < 0),
    ("yc_positive", "yc", lambda v, _t: v > 0.5),
    ("yc_flat", "yc", lambda v, _t: -0.3 <= v <= 0.3),
    ("nfci_tight", "nfci", lambda v, _t: v > 0),
    ("nfci_easing", "nfci", lambda v, _t: v < -0.3),
    ("ip_falling", "ip_yoy", lambda v, _t: v < 0),
    ("ip_strong", "ip_yoy", lambda v, _t: v > 3),
    ("ip_stable", "ip_yoy", lambda v, _t: v > -1),
]


__all__ = ["bullishSignalFlags", "hyCompressionToExpansion"]
