"""경제 사이클 판별 + 자산 해석 + 멀티플 밴드 + 전환 시퀀스 + 금리 분해.

순수 데이터 + 판정 함수. 외부 의존성 없음.
core/ 계층 소속 — gather(수집), macro(시장 해석), analysis(기업 해석) 에서 사용.

사이클 4국면: contraction(침체) → recovery(회복) → expansion(확장) → slowdown(둔화)
"""

from __future__ import annotations

import math

from dartlab.macro.cycles._macroCycleAssets import (
    classifyVixRegime,
    copperGoldRatio,
    interpretFxDrivers,
    interpretGoldDrivers,
    marketLevelValuation,
    realRateRegime,
)

# 결과 타입 (분리: _macroCycleTypes.py SSOT, re-export 으로 BC 보존)
from dartlab.macro.cycles._macroCycleStats import (
    _SIGNAL_SERIES_MAP,
    _findFirstTriggerDates,
    _normCdf,
)
from dartlab.macro.cycles._macroCycleTypes import (
    PHASE_LABELS,
    AssetSignal,
    CopperGoldSignal,
    CyclePhase,
    FxDrivers,
    GoldDrivers,
    MarketValuation,
    MultipleBand,
    RateDecomposition,
    RealRateRegimeResult,
    TransitionSignal,
    VixRegime,
)

__all_helpers__ = [
    "_SIGNAL_SERIES_MAP",
    "_findFirstTriggerDates",
    "_normCdf",
    "classifyVixRegime",
    "copperGoldRatio",
    "interpretFxDrivers",
    "interpretGoldDrivers",
    "marketLevelValuation",
    "realRateRegime",
]

# classifyCycle + CYCLE_SECTOR_MAP 분리 (BC re-export)
from dartlab.macro.cycles._macroCycleClassify import CYCLE_SECTOR_MAP, classifyCycle  # noqa: F401

# ══════════════════════════════════════
# 5대 자산 해석
# ══════════════════════════════════════


def interpretAssets(indicators: dict[str, float | None]) -> list[AssetSignal]:
    """5 대 자산 (단기금리/장기금리/환율/금/VIX) 현재 상태 해석.

    Capabilities:
        매크로 지표 dict 를 받아 5 자산의 (현 수준 + 변화) 를 해석한 list
        반환. 단기/장기금리는 정책/inflation 근거 분리. 환율은 한미 금리차
        교차 해석. 금은 YoY 모멘텀. VIX 는 변화량.

    Args:
        indicators: 매크로 지표 dict. 지원 키 (모두 옵션):
            - ``short_rate``/``short_rate_change`` (%, %p)
            - ``long_rate``/``long_rate_change`` (%, %p)
            - ``bei_change``/``real_rate_change`` (%p) — 장기금리 "왜" 분해
            - ``fx_usdkrw``/``fx_change_pct`` (원, %)
            - ``rate_diff``/``rate_diff_change`` (%p) — 한미 금리차
            - ``gold``/``gold_yoy`` ($/oz, %)
            - ``vix``/``vix_change`` (index, pts)

    Returns:
        list[AssetSignal]: 자산별 dataclass:
            - ``asset`` (str): 자산명
            - ``level`` (float|None)
            - ``interpretation`` (str): 한국어 해석
            - ``implication`` (str): 함의 라벨 (긴축기대/완화기대/안전선호 등)

    Raises:
        없음.

    Example:
        >>> r = interpretAssets({"short_rate": 3.5, "short_rate_change": 0.5,
        ...                      "vix": 28, "vix_change": 8})
        >>> [s.implication for s in r]
        ['긴축기대', ..., '안전선호']

    Guide:
        장기금리 변화를 BEI/real rate 분해로 인플레 vs 성장 기대 구분.
        환율 변화는 한미 금리차 변화와 교차 — 금리차 확대 + 환율 상승 =
        달러 강세, 금리차 축소 + 환율 하락 = 원화 강세.

    SeeAlso:
        - ``classifyCycle``: 사이클 4 국면 (자산 신호 종합)
        - ``interpretGoldDrivers``: 금 3 요인 분해
        - ``interpretFxDrivers``: 환율 드라이버 분해

    When:
        ``macro("cycle")`` 진입점이 본 함수 호출. AI 매크로 환경 답변 직접 인용 시.

    How:
        indicators dict → 5 자산별 임계 분기 (level + change) → AssetSignal dataclass list.

    Requires:
        없음 (순수 함수). indicators dict 일부 키만 있어도 동작.

    AIContext:
        해석 라벨 (interpretation) 을 그대로 인용 — 사용자에게 매크로 환경
        의 직접 텍스트 노출 가능. implication 만으로는 정량 정보 부족.

    LLM Specifications:
        AntiPatterns:
            - 단기금리만 보고 "긴축" 단정 — 장기금리 + 환율 함께 확인.
            - VIX 절대값 (예 18) 만 인용 — vix_change 도 함께 (급등 시 panic).
        OutputSchema:
            list[AssetSignal] — 자산 개수만큼 (입력 indicators 에 따름).
        Prerequisites:
            indicators dict (적어도 1 자산의 level + change).
        Freshness:
            지표별 (금리/환율 일, VIX 일, 금 일).
        Dataflow:
            indicators → 자산별 분기 룰 → AssetSignal dataclass list.
        TargetMarkets: KR (USDKRW + 한미 금리차), Global (long_rate/gold/VIX).
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
    indicators.get("rate_diff")  # US금리 - KR금리
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
    goldYoy = indicators.get("gold_yoy")
    if gold is not None:
        if goldYoy is not None and goldYoy > 15:
            interp = f"금 급등 (${gold:,.0f}, YoY {goldYoy:+.1f}%) — 인플레·불안심리"
            impl = "위험회피"
        elif goldYoy is not None and goldYoy < -5:
            interp = f"금 하락 (${gold:,.0f}, YoY {goldYoy:+.1f}%) — 위험자산 선호"
            impl = "위험선호"
        else:
            interp = f"금 안정 (${gold:,.0f})"
            impl = "중립"
        results.append(AssetSignal("gold", "금", gold, goldYoy, interp, impl))

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
    """멀티플 정규분포 밴드 — z-score + 백분위 + 저평가/적정/고평가 zone.

    Capabilities:
        과거 멀티플 시계열에서 평균·표준편차를 산출하고, 현재값을 z-score 로 평가해 백분위 +
        ±1σ 구간 zone ("cheap" | "fair" | "expensive") 을 반환. PER · PBR · EV/EBITDA 동일
        구조로 사용 가능. 0 이하·200 초과 극단값은 자동 제외.

    Parameters
    ----------
    values : list[float]
        과거 멀티플 값 리스트. 유효값 ≥ 5 필요 (필터 후 기준).
    current : float
        현재 멀티플 값.
    metric : str, default "PER"
        멀티플 종류 ("PER" | "PBR" | "EV/EBITDA" 등). 결과 dict 의 metric 필드에 그대로 기록.

    Returns
    -------
    MultipleBand | None
        metric : str — 입력 그대로
        current : float — 현재값
        mean : float — 과거 평균
        std : float — 과거 표준편차
        percentile : float — 정규분포 CDF 기반 백분위 (%)
        zone : str — "cheap" | "fair" | "expensive"
        zLabel : str — "저평가" | "적정" | "고평가"
        유효값 < 5 또는 std==0 이면 None.

    Raises
    ------
    없음.

    Example
    -------
    >>> hist = [12.3, 14.5, 11.8, 13.9, 15.2, 16.1, 12.0]
    >>> band = calcMultipleBand(hist, current=18.5, metric="PER")
    >>> band.zone, band.zLabel
    ('expensive', '고평가')

    Guide
    -----
    정규분포 가정이라 시계열이 right-skewed (예: PER) 인 경우 백분위가 약간 보수적으로 나옴.
    극단값 (PER > 200) 자동 제외는 적자 기업의 음수 PER 같은 노이즈 차단용.

    SeeAlso
    -------
    - ``dartlab.macro.cycles.macroCycle.classifyCycle`` : 매크로 국면 판정
    - ``dartlab.analysis.valuation.dcf`` : 절대가치 평가
    - See Also: 위와 동일

    When:
        과거 시계열 멀티플 분포 대비 현재 위치 답변 시.

    How:
        valid 필터 → mean/std → z-score → normCdf 백분위 → ±1σ zone.

    Requires
    --------
    - 과거 멀티플 시계열 ≥ 5 (필터 후 기준)
    - 시계열 단위 일관성 (TTM PER vs forward PER 혼용 금지)

    AIContext
    ---------
    "현재 PER 이 역사적으로 어느 수준" 답변에 사용. zone/zLabel/percentile 세 필드 묶음으로
    한 줄 답변. None 반환 시 "기간 부족" 으로 답변하고 다른 지표 (PBR/EV) 시도 권장.
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
    percentile = _normCdf(z) * 100

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


# rateOutlook + detectTransitionSequence + _TRANSITION_SEQUENCES — _macroCycleOutlook.py 분리 (BC re-export)
from dartlab.macro.cycles._macroCycleOutlook import (  # noqa: E402, F401
    _TRANSITION_SEQUENCES,
    detectTransitionSequence,
    rateOutlook,
)

# ══════════════════════════════════════
# 장기금리 DKW 근사 분해
# ══════════════════════════════════════


def decomposeLongRate(
    nominal: float,
    bei: float,
    tips: float,
    acmTermPremium: float | None = None,
) -> RateDecomposition:
    """10 년 명목금리를 3 요소로 분해 — DKW (Diebold-Kilian-Wright) 모델 근사.

    Capabilities:
        명목 10Y 금리 = 기대인플레이션 (BEI) + 실질금리 (TIPS) + 기간프리미엄.
        ACM (Adrian-Crump-Moench, NY Fed) 추정치가 있으면 직접 사용, 없으면
        잔차로 근사 (nominal - BEI - TIPS).

    Args:
        nominal: 10년 명목금리 DGS10 (%).
        bei: 10년 BEI T10YIE (%) — 기대인플레이션.
        tips: 10년 TIPS DFII10 (%) — 실질금리.
        acmTermPremium: ACM 10년 기간프리미엄 (%). FRED THREEFYTP10. None
            이면 잔차 근사.

    Returns:
        ``RateDecomposition`` — ``nominal``/``expectedInflation``/``realRate``/
        ``termPremium`` 4 float (소수점 3 자리).

    Example:
        >>> from dartlab.macro.cycles.macroCycle import decomposeLongRate
        >>> r = decomposeLongRate(nominal=4.5, bei=2.5, tips=2.0)
        >>> r.expectedInflation, r.termPremium
        (2.5, 0.0)
        >>> r = decomposeLongRate(nominal=4.5, bei=2.5, tips=2.0, acmTermPremium=0.5)
        >>> r.termPremium
        0.5

    Guide:
        장기금리 상승의 원인 분해 — BEI 상승 (인플레 기대) vs realRate 상승
        (성장 기대) vs termPremium 상승 (불확실성). 단일 nominal 변동만 보고
        해석 금지.

    SeeAlso:
        - ``interpretAssets``: 장기금리 분해를 자동 호출
        - ``rateOutlook``: 정책금리 방향 (decomposeLongRate 보완)
        - NY Fed ACM term premium 시계열

    When:
        ``macro("cycle", "rates")``. AI 가 장기금리 변동 원인 분해 답변 시.

    How:
        acmTermPremium 명시 시 직접 사용, 없으면 termPremium = nominal - BEI - TIPS.

    Raises:
        없음 — 순수 산술. NaN 입력은 호출자가 사전 필터.

    Requires:
        FRED 시리즈 DGS10 + T10YIE + DFII10 (+ THREEFYTP10 옵션). API key 불필요.

    AIContext:
        "장기금리 왜 올랐나" · "인플레 기대 vs 성장 기대 분해" 등 금리 해석
        질문에 호출. 결과의 termPremium 부호에 주의 (음수도 가능 — flight to
        quality).

    LLM Specifications:
        AntiPatterns:
            - bei + tips ≠ nominal 인데 acmTermPremium 미사용 — 데이터 비일치
              가능 (다른 기준일). 동일 일자 데이터 권장.
            - termPremium 단순 인용 — 추세 (변화) 도 함께 검토.
        OutputSchema:
            ``RateDecomposition(nominal: float, expectedInflation: float,
            realRate: float, termPremium: float)``.
        Prerequisites:
            없음 (순수 함수). 입력 4 float 만.
        Freshness:
            FRED 일간 갱신 시리즈 — 호출자가 일자 동기화.
        Dataflow:
            (nominal, bei, tips, acmTermPremium?) → 잔차 또는 ACM 직접 →
            RateDecomposition.
        TargetMarkets: US (FRED DGS10/T10YIE/DFII10 풀세트). KR 은 미지원.
    """
    if acmTermPremium is not None:
        # ACM 모델 기간프리미엄 사용 (NY Fed 추정치)
        term_premium = acmTermPremium
    else:
        # 잔차 근사: 명목 - BEI - TIPS
        term_premium = nominal - bei - tips
    return RateDecomposition(
        nominal=round(nominal, 3),
        expectedInflation=round(bei, 3),
        realRate=round(tips, 3),
        termPremium=round(term_premium, 3),
    )


# ══════════════════════════════════════
# 금 3요인 해석
