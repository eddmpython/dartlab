"""역사적 매크로 이벤트 통계 — historicalContext.py 에서 분리.

HY 스프레드 급등, 수익률곡선 역전, 실업률 반등, CPI 가속, 동시 경고등
5 종 이벤트 통계 함수.
"""

from __future__ import annotations

import numpy as np

from dartlab.macro.corporate._historicalContextSeries import (
    _deltaN,
    _isRecession,
    _monthsToNextRecession,
    _yoy,
)
from dartlab.macro.corporate._historicalContextTypes import (
    HYSpikeHistory,
    SimultaneousWarnings,
    URBounceHistory,
    YCInversionHistory,
)


def hySpikesToRecession(
    hyMonthly: dict[str, float],
    *,
    thresholdBp: float = 1.0,
    currentDelta: float | None = None,
) -> HYSpikeHistory:
    """HY 스프레드 3개월 급등 → 침체 선행 통계.

    Capabilities:
        HY OAS 3 개월 변화 ≥ thresholdBp (기본 1.0 %p = 100bp) 구간 추출 → 12 개월
        내 NBER 침체 발생률 + currentDelta 와 가장 유사한 과거 케이스 매칭.

    Args:
        hyMonthly: ``{"YYYY-MM": HY OAS %}`` 월별 dict.
        thresholdBp: 급등 임계 (%p). 기본 1.0.
        currentDelta: 현재 3M 변화 (%p). nearest 매칭에 사용.

    Returns:
        HYSpikeHistory — totalSpikes/recessionWithin12m/recessionRate12m/
        nearestMatch/nearestMatchDelta/nearestMatchOutcome/currentDelta/
        description.

    Example:
        >>> r = hySpikesToRecession({"2008-09": 8.0, ...}, currentDelta=2.5)
        >>> r.recessionRate12m
        0.67

    Guide:
        rate12m ≥ 0.6 = HY 급등 신호 강함. nearestMatchOutcome 인용으로 과거
        대조 가능.

    When:
        ``simultaneousWarningFlags`` + ``buildHistoricalContext`` 내부.

    How:
        _deltaN(3M) → threshold 매칭 → _monthsToNextRecession 12 개월 카운트 +
        currentDelta 와 |diff| 최소 매칭.

    Requires:
        FRED BAMLH0A0HYM2 월별 ≥ 1997 + NBER 침체 일자.

    Raises:
        없음.

    See Also:
        - hyCompressionToExpansion : 반대 (HY 급락 → 확장)
        - simultaneousWarningFlags : 8 신호 종합

    AIContext:
        rate12m + nearestMatch 두 필드 인용으로 "HY 급등 12 개월 내 침체 N%
        (2007-12 사례 비슷)" 한 문장 답변.

    LLM Specifications:
        AntiPatterns:
            - 침체 중 발생 케이스 (in_rec=True) 까지 rate 계산 (제외 필요)
            - currentDelta 없이 nearest 매칭 기대
        OutputSchema:
            HYSpikeHistory (8 필드).
        Prerequisites: HY OAS 월별 + NBER.
        Freshness: 월간.
        Dataflow: deltaN → 임계 → 침체 확률 + nearest.
        TargetMarkets: US. KR 미지원.
    """
    d3 = _deltaN(hyMonthly, 3)
    spikes: list[tuple[str, float, int, bool]] = []

    for m in sorted(d3.keys()):
        if d3[m] > thresholdBp:
            mtr = _monthsToNextRecession(m)
            spikes.append((m, d3[m], mtr, _isRecession(m)))

    pre_rec = [s for s in spikes if not s[3] and s[2] < 999]
    within_12 = sum(1 for s in pre_rec if s[2] <= 12)
    rate = within_12 / len(pre_rec) if pre_rec else 0.0

    nearest = None
    nearest_delta = None
    nearest_outcome = None
    if currentDelta is not None and spikes:
        best_diff = float("inf")
        for m, delta, mtr, in_rec in spikes:
            diff = abs(delta - currentDelta)
            if diff < best_diff:
                best_diff = diff
                nearest = m
                nearest_delta = delta
                if in_rec:
                    nearest_outcome = "침체 중"
                elif mtr < 999:
                    nearest_outcome = f"{mtr}개월 후 침체"
                else:
                    nearest_outcome = "침체 없음"

    desc_parts = [f"HY 스프레드 3개월 +{thresholdBp * 100:.0f}bp 이상 급등: 과거 {len(spikes)}회"]
    if pre_rec:
        desc_parts.append(f"12개월 내 침체 {within_12}/{len(pre_rec)} ({rate * 100:.0f}%)")
    if nearest:
        desc_parts.append(f"가장 유사: {nearest} ({nearest_outcome})")

    return HYSpikeHistory(
        totalSpikes=len(spikes),
        recessionWithin12m=within_12,
        recessionRate12m=round(rate, 3),
        nearestMatch=nearest,
        nearestMatchDelta=round(nearest_delta, 2) if nearest_delta else None,
        nearestMatchOutcome=nearest_outcome,
        currentDelta=round(currentDelta, 2) if currentDelta is not None else None,
        description=". ".join(desc_parts),
    )


def yieldCurveInversionsToRecession(
    spreadMonthly: dict[str, float],
) -> YCInversionHistory:
    """Yield Curve 역전 시작점 → 침체까지 통계.

    Capabilities:
        10Y-2Y (또는 10Y-3M) 스프레드 월별 시리즈에서 0 이상 → 음수 전이 시점
        추출 → 각 역전 시작점 → 다음 NBER 침체까지 평균/중위 lead 개월. 현재
        역전 중이면 시작일 + 경과 개월 노출.

    Args:
        spreadMonthly: ``{"YYYY-MM": Term spread %}`` 월별 dict.

    Returns:
        YCInversionHistory — totalInversions/avgLeadMonths/medianLeadMonths/
        rangeLeadMonths/currentInversionStart/currentDurationMonths/description.

    Example:
        >>> r = yieldCurveInversionsToRecession({"2019-08": -0.05, ...})
        >>> r.avgLeadMonths
        14.0

    Guide:
        avgLeadMonths 12~18 = 표준 (역사적 평균 ~14). currentInversionStart 가
        12 개월 초과면 "역전 장기화 → 침체 임박" 인용.

    When:
        ``simultaneousWarningFlags`` 보조 + AI 침체 시기 답변.

    How:
        spread 월별 시리즈 → 양→음 전이점 추출 → _monthsToNextRecession lead →
        평균/중위/범위 + 현재 역전 추적.

    Requires:
        FRED T10Y2Y (또는 T10Y3M) 월별 + NBER.

    Raises:
        없음.

    See Also:
        - hySpikesToRecession : HY 급등 시그널
        - buildHistoricalContext : 본 함수 호출 진입점

    AIContext:
        avgLeadMonths + currentDurationMonths 두 필드로 "역전 평균 14 개월 후
        침체, 현재 8 개월째" 답변.

    LLM Specifications:
        AntiPatterns:
            - lead = 999 (침체 없음) 케이스 포함 (제외 필요)
            - 단일 역전 시점 강조 + 평균/중위 미인용
        OutputSchema:
            YCInversionHistory (7 필드).
        Prerequisites: T10Y2Y 월별 ≥ 1977 + NBER.
        Freshness: 월간.
        Dataflow: spread → 전이점 추출 → lead 통계.
        TargetMarkets: US. KR 미지원.
    """
    months = sorted(spreadMonthly.keys())
    inversions: list[tuple[str, float, int]] = []
    prev_positive = True

    for m in months:
        val = spreadMonthly[m]
        if val < 0 and prev_positive:
            mtr = _monthsToNextRecession(m)
            inversions.append((m, val, mtr))
        prev_positive = val >= 0

    valid = [i for i in inversions if i[2] < 999]
    leads = [i[2] for i in valid] if valid else []

    current_start = None
    current_dur = None
    if months:
        latest = months[-1]
        if spreadMonthly[latest] < 0:
            for m in reversed(months):
                if spreadMonthly[m] >= 0:
                    break
                current_start = m
            if current_start:
                y1, m1 = int(current_start[:4]), int(current_start[5:7])
                y2, m2 = int(latest[:4]), int(latest[5:7])
                current_dur = (y2 - y1) * 12 + (m2 - m1)

    desc_parts = [f"Yield Curve 역전: 과거 {len(inversions)}회"]
    if leads:
        desc_parts.append(
            f"역전→침체 평균 {np.mean(leads):.0f}개월, 중위 {np.median(leads):.0f}개월 (범위 {min(leads)}~{max(leads)})"
        )
    if current_start:
        desc_parts.append(f"현재 {current_start}부터 역전 중 ({current_dur}개월째)")

    return YCInversionHistory(
        totalInversions=len(inversions),
        avgLeadMonths=round(float(np.mean(leads)), 1) if leads else None,
        medianLeadMonths=round(float(np.median(leads)), 1) if leads else None,
        rangeLeadMonths=(min(leads), max(leads)) if leads else None,
        currentInversionStart=current_start,
        currentDurationMonths=current_dur,
        description=". ".join(desc_parts),
    )


def unemploymentBounceToRecession(
    urMonthly: dict[str, float],
    *,
    thresholdPp: float = 0.3,
) -> URBounceHistory:
    """실업률 12개월 최저에서 반등 → 침체 선행 통계.

    Capabilities:
        실업률 12 개월 rolling 최저 대비 +thresholdPp 이상 반등 시점 추출 →
        12 개월 내 NBER 침체 발생률 + 현재 반등 정도. Sahm Rule 의 단순 변형.

    Args:
        urMonthly: ``{"YYYY-MM": UNRATE %}`` 월별 dict.
        thresholdPp: 반등 임계 (%p). 기본 0.3.

    Returns:
        URBounceHistory — totalBounces/recessionWithin12m/recessionRate12m/
        currentBounce/description.

    Example:
        >>> r = unemploymentBounceToRecession({"2024-08": 4.3, ...})
        >>> r.recessionRate12m
        0.75

    Guide:
        rate12m ≥ 0.7 = 강한 침체 선행 신호. currentBounce ≥ thresholdPp 인용
        시 "현재 진행 중" 강조.

    When:
        ``simultaneousWarningFlags`` 보조 + AI 실업률 답변.

    How:
        12 개월 rolling 윈도우 → 저점 대비 차 ≥ threshold 시점 추출 (이전
        시점은 미만) → 침체 카운트.

    Requires:
        FRED UNRATE 월별 ≥ 1948 + NBER.

    Raises:
        없음.

    See Also:
        - sahmRule : 0.5%p 임계 단순 룰
        - buildHistoricalContext : 본 함수 호출 진입점

    AIContext:
        rate12m + currentBounce 두 필드 인용으로 "실업률 +0.4%p 반등, 과거
        75% 12개월 내 침체" 답변.

    LLM Specifications:
        AntiPatterns:
            - 단발 반등 (이전 월 이미 반등) 도 카운트 (필터링 필요)
            - threshold 임의 변경 (Sahm 0.5 표준)
        OutputSchema:
            URBounceHistory (5 필드).
        Prerequisites: UNRATE 월별 + NBER.
        Freshness: 월간.
        Dataflow: rolling min → bounce → 침체 확률.
        TargetMarkets: US. KR 미지원.
    """
    months = sorted(urMonthly.keys())
    bounces: list[tuple[str, float, float, int]] = []

    for i, m in enumerate(months):
        if i < 12:
            continue
        window = [urMonthly[months[j]] for j in range(i - 12, i + 1)]
        low = min(window)
        bounce = urMonthly[m] - low
        if bounce >= thresholdPp:
            prev_bounce = urMonthly[months[i - 1]] - min(urMonthly[months[j]] for j in range(max(0, i - 13), i))
            if prev_bounce < thresholdPp:
                mtr = _monthsToNextRecession(m)
                bounces.append((m, urMonthly[m], low, mtr))

    pre_rec = [b for b in bounces if not _isRecession(b[0]) and b[3] < 999]
    within_12 = sum(1 for b in pre_rec if b[3] <= 12)
    rate = within_12 / len(pre_rec) if pre_rec else 0.0

    current_bounce = None
    if months:
        latest = months[-1]
        i = len(months) - 1
        if i >= 12:
            window = [urMonthly[months[j]] for j in range(i - 12, i + 1)]
            low = min(window)
            current_bounce = round(urMonthly[latest] - low, 2)

    desc_parts = [f"실업률 12개월 저점 대비 +{thresholdPp}%p 이상 반등: 과거 {len(bounces)}회"]
    if pre_rec:
        desc_parts.append(f"12개월 내 침체 {within_12}/{len(pre_rec)} ({rate * 100:.0f}%)")
    if current_bounce is not None and current_bounce >= thresholdPp:
        desc_parts.append(f"현재 저점 대비 +{current_bounce}%p 반등 중")

    return URBounceHistory(
        totalBounces=len(bounces),
        recessionWithin12m=within_12,
        recessionRate12m=round(rate, 3),
        currentBounce=current_bounce,
        description=". ".join(desc_parts),
    )


def cpiAccelerationEvents(
    cpiRawMonthly: dict[str, float],
    *,
    thresholdPp: float = 1.0,
) -> dict:
    """CPI 가속 구간 식별.

    Capabilities:
        CPI raw 월별 시리즈 → YoY → 3 개월 변화 ≥ thresholdPp 가속 구간 카운트 +
        현재 가속 여부. 인플레 쇼크 시기 진단.

    Args:
        cpiRawMonthly: ``{"YYYY-MM": CPI index}`` 원시 월별 dict.
        thresholdPp: 가속 임계 (%p). 기본 1.0.

    Returns:
        dict — count/currentAcceleration/isAccelerating(bool)/description.

    Example:
        >>> r = cpiAccelerationEvents({"2022-06": 296.3, ...})
        >>> r["isAccelerating"]
        True

    Guide:
        currentAcceleration > 2.0 = 강한 가속 (2021-22 같은 인플레 쇼크). count
        역사적 빈도 (1970s 다발) 와 비교 인용.

    When:
        ``buildHistoricalContext`` 내부 + AI 인플레 답변 보조.

    How:
        _yoy(raw) → _deltaN(3M, YoY) → threshold 매칭 → 현재 latest 가속도.

    Requires:
        FRED CPIAUCSL 월별 원시 ≥ 1947.

    Raises:
        없음.

    See Also:
        - interpretInflation : 현재 인플레 상태
        - rateOutlook : 인플레 → 정책금리 방향

    AIContext:
        isAccelerating + currentAcceleration 두 필드 인용으로 "CPI +1.5%p 가속 중"
        답변.

    LLM Specifications:
        AntiPatterns:
            - YoY 가 아닌 raw 변화로 가속도 산출 (반드시 YoY 후 deltaN)
            - threshold 임의 변경 (1.0 표준)
        OutputSchema:
            ``{count, currentAcceleration, isAccelerating, description}``.
        Prerequisites: CPI 월별 원시.
        Freshness: 월간 (10 일 발표).
        Dataflow: raw → YoY → 3M delta → 임계.
        TargetMarkets: US. KR 동일 적용 가능.
    """
    cpiYoy = _yoy(cpiRawMonthly)
    accel = _deltaN(cpiYoy, 3)

    events = [(m, accel[m]) for m in sorted(accel.keys()) if accel[m] > thresholdPp]

    latest_month = max(accel.keys()) if accel else None
    current_accel = accel.get(latest_month) if latest_month else None

    desc = f"CPI 3개월 +{thresholdPp}%p 이상 가속: 과거 {len(events)}회"
    if current_accel is not None and current_accel > thresholdPp:
        desc += f". 현재 +{current_accel:.1f}%p 가속 중"

    return {
        "count": len(events),
        "currentAcceleration": round(current_accel, 2) if current_accel else None,
        "isAccelerating": current_accel is not None and current_accel > thresholdPp,
        "description": desc,
    }


def simultaneousWarningFlags(
    data: dict[str, dict[str, float] | None],
) -> SimultaneousWarnings:
    """8개 경고등 동시 점등 판정.

    Capabilities:
        8 위험 신호 (HY>5%/HY급등/YC역전/실업↑/VIX>25/NFCI긴축/산업생산↓/
        CPI>5%) 현재 점등 수 + 과거 3 개 이상 동시 점등 횟수 + 이후 18 개월
        내 침체 확률 + 유사 시기 list.

    Args:
        data: ``{"hy_spread"/"hy_spread_d3"/"spread_10y2y"/"ur_d6"/"vix"/"nfci"/
            "ip_yoy"/"cpi_yoy": {"YYYY-MM": value}}`` 월별 dict.

    Returns:
        SimultaneousWarnings — activeFlags/flagCount/historicalOccurrences/
        recessionRate18m/similarPeriods/description.

    Example:
        >>> r = simultaneousWarningFlags({"hy_spread": {...}, ...})
        >>> r.flagCount, r.recessionRate18m
        (4, 0.85)

    Guide:
        flagCount ≥ 5 = 경고 매우 강함. recessionRate18m ≥ 0.7 + similar 사례
        대조 인용으로 "지금 2007-12 와 유사" 답변 가능.

    When:
        ``buildHistoricalContext`` 위기 신호 1 차 진입점.

    How:
        latest 임계 매칭 + 모든 월 임계 매칭 → 3+ 점등 월 → 침체 카운트 + 현재
        active 와 ≥ 2 overlap 인 과거 5 케이스.

    Requires:
        FRED 8 시리즈 월별 + NBER.

    Raises:
        없음.

    See Also:
        - bullishSignalFlags : 반대 (호황 신호)
        - hySpikesToRecession : HY 단일 신호 통계

    AIContext:
        activeFlags + similarPeriods 1 건 인용으로 "지금 4 개 경고등 (HY/YC/실업/
        VIX), 2007-12 와 유사 — 12 개월 후 침체" 답변.

    LLM Specifications:
        AntiPatterns:
            - flagCount 만 인용 + similarPeriods 미노출
            - 침체 중 (in_rec=True) 케이스 rate 계산 포함 (제외)
        OutputSchema:
            SimultaneousWarnings (6 필드).
        Prerequisites: 8 시리즈 월별.
        Freshness: 월간.
        Dataflow: data → 8 임계 → 동시점등 카운트 → 침체 확률.
        TargetMarkets: US. KR 미지원.
    """
    hy = data.get("hy_spread") or {}
    hyD3 = data.get("hy_spread_d3") or {}
    yc = data.get("spread_10y2y") or {}
    urD6 = data.get("ur_d6") or {}
    vixD = data.get("vix") or {}
    nfciD = data.get("nfci") or {}
    ipYoy = data.get("ip_yoy") or {}
    cpiYoy = data.get("cpi_yoy") or {}

    all_months = sorted(set(hy.keys()) & set(yc.keys()))

    latest = all_months[-1] if all_months else None
    active: list[str] = []
    if latest:
        if hy.get(latest, 0) > 5:
            active.append("HY>5%")
        if hyD3.get(latest, 0) > 0.5:
            active.append("HY급등")
        if yc.get(latest, 1) < 0:
            active.append("YC역전")
        if urD6.get(latest, 0) > 0.3:
            active.append("실업↑")
        if vixD.get(latest, 0) > 25:
            active.append("VIX>25")
        if nfciD.get(latest, -1) > 0:
            active.append("NFCI긴축")
        if ipYoy.get(latest, 1) < 0:
            active.append("산업생산↓")
        if cpiYoy.get(latest, 0) > 5:
            active.append("CPI>5%")

    multi_warn_months: list[tuple[str, list[str]]] = []
    for m in all_months:
        flags: list[str] = []
        if hy.get(m, 0) > 5:
            flags.append("HY>5%")
        if hyD3.get(m, 0) > 0.5:
            flags.append("HY급등")
        if yc.get(m, 1) < 0:
            flags.append("YC역전")
        if urD6.get(m, 0) > 0.3:
            flags.append("실업↑")
        if vixD.get(m, 0) > 25:
            flags.append("VIX>25")
        if nfciD.get(m, -1) > 0:
            flags.append("NFCI긴축")
        if ipYoy.get(m, 1) < 0:
            flags.append("산업생산↓")
        if cpiYoy.get(m, 0) > 5:
            flags.append("CPI>5%")
        if len(flags) >= 3:
            multi_warn_months.append((m, flags))

    pre_rec = [(m, flags) for m, flags in multi_warn_months if not _isRecession(m) and _monthsToNextRecession(m) < 999]
    within_18 = sum(1 for m, _ in pre_rec if _monthsToNextRecession(m) <= 18)
    rate = within_18 / len(pre_rec) if pre_rec else 0.0

    similar: list[dict] = []
    if active:
        active_set = set(active)
        for m, flags in reversed(multi_warn_months):
            if m == latest:
                continue
            overlap = set(flags) & active_set
            if len(overlap) >= 2:
                mtr = _monthsToNextRecession(m)
                outcome = "침체 중" if _isRecession(m) else (f"{mtr}개월 후 침체" if mtr < 24 else "침체 없음")
                similar.append({"month": m, "flags": flags, "outcome": outcome, "overlap": list(overlap)})
            if len(similar) >= 5:
                break

    desc = f"현재 경고등 {len(active)}개"
    if active:
        desc += f" ({', '.join(active)})"
    desc += f". 과거 3개+ 동시 점등 {len(multi_warn_months)}회"
    if pre_rec:
        desc += f", 18개월 내 침체 {within_18}/{len(pre_rec)} ({rate * 100:.0f}%)"

    return SimultaneousWarnings(
        activeFlags=active,
        flagCount=len(active),
        historicalOccurrences=len(multi_warn_months),
        recessionRate18m=round(rate, 3),
        similarPeriods=similar,
        description=desc,
    )
