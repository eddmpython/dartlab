"""금융위기 감지 — Credit-to-GDP Gap + GHS 위기예측 + 침체 대시보드.

순수 데이터 + 판정 함수. 외부 의존성 없음.
core/ 계층 소속 — macro(시장 해석) 엔진에서 소비.

학술 근거:
- BIS Basel III: Credit-to-GDP gap for CCyB (Drehmann & Tsatsaronis 2014)
- Greenwood, Hanson & Shleifer (2022, JoF): "Predictable Financial Crises"
- Reinhart & Rogoff (2009): "This Time Is Different"
- Dalio, R. (2018), *Principles for Navigating Big Debt Crises* Part 1:
  부채사이클 6단계 + 정책 4 레버(monetary/fiscal/credit/fx) 소진도
"""

from __future__ import annotations

from dartlab.macro.crisis._detectorsDalio import (
    _DALIO_PHASE_LABELS,
    _SUB_PHASE_LABELS,
    _VARIANT_LABELS,
    dalioDebtCyclePhase,
    dalioPolicyLeverStatus,
)

# 결과 타입 (분리: _detectorTypes.py SSOT, re-export 으로 BC 보존)
from dartlab.macro.crisis._detectorsRegime import (
    _beautifulDeleveragingSubPhase,
    _dalioRegimeVariant,
    _oneSidedHpTrend,
)
from dartlab.macro.crisis._detectorTypes import (
    CreditGapResult,
    DalioPhaseResult,
    DalioPolicyLeverResult,
    FisherDeflationResult,
    GHSResult,
    KooRecessionResult,
    KRHousingStressResult,
    MinskyPhaseResult,
    RecessionDashboard,
)

__all_helpers__ = [
    "_DALIO_PHASE_LABELS",
    "_SUB_PHASE_LABELS",
    "_VARIANT_LABELS",
    "_beautifulDeleveragingSubPhase",
    "_dalioRegimeVariant",
    "_oneSidedHpTrend",
    "dalioDebtCyclePhase",
    "dalioPolicyLeverStatus",
]

# ══════════════════════════════════════
# Credit-to-GDP Gap (BIS 방법)
# ══════════════════════════════════════


def creditToGDPGap(creditGDPSeries: list[float]) -> CreditGapResult:
    """Credit-to-GDP Gap (BIS Basel III CCyB 표준) → 신용 거품 + 완충자본 산출.

    Capabilities:
        Drehmann & Tsatsaronis (2014) 의 BIS 방법론 — credit/GDP 시계열에
        one-sided HP filter (λ=400,000) 적용하여 trend 추출 후 gap = actual -
        trend 산출. gap > 2 = 거품 신호, BIS CCyB (counter-cyclical capital
        buffer) 자동 산출.

    Args:
        creditGDPSeries: 분기별 신용/GDP 비율 시계열 (%). 최소 4 기간, 20+
            기간 권장 (BIS 표준).

    Returns:
        CreditGapResult dataclass:
            - ``gap`` (float): actual - trend
            - ``trend`` (float): HP filter 추출 추세
            - ``actual`` (float): 최신 신용/GDP
            - ``zone`` (str): ``"normal"``/``"caution"``/``"alert"``/
              ``"critical"``
            - ``zoneLabel`` (str): 한국어
            - ``ccybBuffer`` (float): BIS CCyB 권고 자본 (% of RWA)
            - ``description`` (str)

    Raises:
        없음. 시계열 < 4 시 빈 결과.

    Example:
        >>> import polars as pl
        >>> series = [...]  # 분기 신용/GDP, 20+ 기간
        >>> r = creditToGDPGap(series)
        >>> r.zone, r.ccybBuffer
        ('alert', 1.5)  # 1.5% RWA 추가 자본 권고

    Guide:
        BIS 임계 (Basel III): gap < 2 = normal (CCyB=0), 2~5 = caution
        (CCyB=0.5 점진), 5~10 = alert (CCyB 1~2%), >10 = critical (CCyB
        2.5% upper bound). 한국은 BOK FSR 매년 발표.

    SeeAlso:
        - ``ghsCrisisScore``: GHS (Greenwood-Hanson-Shleifer) 위기 예측
        - ``minskyPhase``: Minsky 부채 사이클 단계
        - Drehmann & Tsatsaronis (2014) BIS Quarterly Review

    When:
        ``macro("crisis", "creditGap")``. BIS CCyB 자본 권고 산출 시.

    How:
        ``_oneSidedHpTrend(λ=400000)`` → trend 시계열 → gap = actual - trend → 임계 분기 →
        CCyB 매핑.

    Requires:
        creditGDPSeries 최소 4 기간 (HP filter 안정). 20+ 기간 권장.

    AIContext:
        gap > 5 결과는 거품 우려 — 신용 사이클 위치 + Minsky/Dalio 와 함께
        cross-check. ccybBuffer 는 정책 권고이지 즉시 위험 신호 아님.

    LLM Specifications:
        AntiPatterns:
            - 4 기간 미만 series → 빈 결과 (zoneLabel="데이터부족") 무시 금지.
            - 단일 국가 gap 만 인용 — 글로벌 sync (BIS Q3-Q4) 확인.
        OutputSchema:
            CreditGapResult (7 필드 dataclass).
        Prerequisites:
            BIS/한국은행 credit/GDP 분기 series.
        Freshness:
            분기 단위 (BIS Q3 발표 = 1 분기 lag).
        Dataflow:
            series → _oneSidedHpTrend (λ=400000) → trend → gap = last - trend
            → zone 임계 분류 → CCyB 매핑.
        TargetMarkets: Global (BIS 표준). KR 도 한국은행 FSR.
    """
    if len(creditGDPSeries) < 4:
        return CreditGapResult(
            gap=None,
            trend=None,
            actual=None,
            zone=None,
            zoneLabel="데이터부족",
            ccybBuffer=None,
            description="Credit-to-GDP 시계열 데이터 부족",
            status="unavailable",
            observedInputs=len(creditGDPSeries),
            totalInputs=4,
        )

    trend_series = _oneSidedHpTrend(creditGDPSeries, lamb=400_000.0)
    actual = creditGDPSeries[-1]
    trend = trend_series[-1]
    gap = actual - trend

    # CCyB 완충자본 (BIS 규칙)
    if gap <= 2.0:
        ccyb = 0.0
    elif gap >= 10.0:
        ccyb = 2.5
    else:
        ccyb = 2.5 * (gap - 2.0) / 8.0

    # 구간 판별
    if gap < 2:
        zone, zone_label = "normal", "정상"
        desc = f"Credit-to-GDP gap {gap:+.1f}%p — 구조적 불균형 없음"
    elif gap < 6:
        zone, zone_label = "watch", "주의"
        desc = f"Credit-to-GDP gap {gap:+.1f}%p — 신용 팽창 초기, CCyB {ccyb:.1f}%"
    elif gap < 10:
        zone, zone_label = "warning", "경고"
        desc = f"Credit-to-GDP gap {gap:+.1f}%p — 신용 과열, CCyB {ccyb:.1f}%"
    else:
        zone, zone_label = "danger", "위험"
        desc = f"Credit-to-GDP gap {gap:+.1f}%p — 금융 불안정 위험, CCyB 최대 2.5%"

    return CreditGapResult(
        gap=round(gap, 2),
        trend=round(trend, 2),
        actual=round(actual, 2),
        zone=zone,
        zoneLabel=zone_label,
        ccybBuffer=round(ccyb, 2),
        description=desc,
    )


# ══════════════════════════════════════
# GHS 금융위기 예측 (Greenwood-Hanson-Shleifer 2022)
# ══════════════════════════════════════


def ghsCrisisScore(
    creditGrowth3y: float,
    assetPriceGrowth3y: float,
    realRate: float | None = None,
) -> GHSResult:
    """GHS (Greenwood-Hanson-Shleifer 2022) 금융위기 예측 점수 + Dalio 회로.

    Capabilities:
        Greenwood, Hanson & Shleifer (2022, JoF) "Predictable Financial
        Crises" 의 핵심 모델 — 3 년 누적 신용 팽창 + 자산 가격 급등 결합
        시 향후 3 년 내 금융위기 확률 ~40% (정상 시 ~7%). realRate 제공 시
        Dalio Part 1 regime (deflation/inflation) 추가 판정.

    Args:
        creditGrowth3y: 민간 신용/GDP 3 년 누적 변화 (%p).
        assetPriceGrowth3y: 자산가격 (주가 또는 부동산) 3 년 누적 수익률 (%).
        realRate: 실질금리 (%). 제공 시 regime 분기.

    Returns:
        GHSResult dataclass:
            - ``crisisScore`` (float): 0~100 위기 점수
            - ``probability3y`` (float): 3 년 내 위기 확률 (0~1)
            - ``zone`` (str): low/moderate/high/extreme
            - ``regime`` (str|None): deflation/inflation (realRate 있을 때)
            - ``creditScore``/``assetScore`` (float): 분해 점수
            - ``warnings`` (list[str])

    Raises:
        없음.

    Example:
        >>> r = ghsCrisisScore(creditGrowth3y=12, assetPriceGrowth3y=45,
        ...                     realRate=-1.0)
        >>> r.crisisScore, r.probability3y, r.regime
        (75, 0.35, 'inflation')

    Guide:
        GHS 핵심: credit (50 점 만점) + asset (50 점) 합산. credit > 10%p +
        asset > 30% 결합 시 zone="high". Dalio regime: deflation = 실질금리
        +2% + 신용 수축 → 부채 디플레이션, inflation = 실질금리 <0% + 신용
        확장 → 통화/실물 인플레이션 압박.

    SeeAlso:
        - ``creditToGDPGap``: BIS gap (단기 신용 거품)
        - ``minskyPhase``: Minsky 부채 사이클 (구조적)
        - ``dalioDebtCyclePhase``: Dalio 6 단계
        - Greenwood, Hanson & Shleifer (2022) Journal of Finance

    When:
        ``macro("crisis", "ghs")``. 3 년 horizon 위기 예측 답변 / 자산배분 위험 매크로 input.

    How:
        credit / asset 3 년 변화 → 점수 (각 0~50) → 합산 → zone + probability3y 매핑 + realRate
        → regime.

    Requires:
        creditGrowth3y + assetPriceGrowth3y (3 년 누적 변화).

    AIContext:
        probability3y 는 통계적 base rate — 개별 회사 부도 확률과 혼동 금지.
        regime 라벨은 Dalio Part 1 정성 판정 (정확한 1 년 부도율 아님).

    LLM Specifications:
        AntiPatterns:
            - 단년도 신용 증가 (creditGrowth1y) 입력 — 본 함수는 3 년 누적
              표준. 단기 변동성에 과민 반응.
            - realRate=0 입력 → regime 판정 불가 (None 반환), 의도된 동작.
        OutputSchema:
            GHSResult (7 필드 dataclass).
        Prerequisites:
            credit + asset 3 년 시계열. realRate 옵션.
        Freshness:
            BIS credit 분기, asset price 일/월.
        Dataflow:
            creditGrowth3y → credit_score (0~50) + assetGrowth → asset_score
            (0~50) → 합산 → zone → probability 매핑 + realRate → regime.
        TargetMarkets: Global. BIS + Schiller (자산가격) 데이터.
    """
    # 신용 팽창 점수 (0-50)
    if creditGrowth3y > 15:
        credit_score = 50
    elif creditGrowth3y > 10:
        credit_score = 35
    elif creditGrowth3y > 5:
        credit_score = 20
    elif creditGrowth3y > 0:
        credit_score = 10
    else:
        credit_score = 0

    # 자산 가격 점수 (0-50)
    if assetPriceGrowth3y > 80:
        asset_score = 50
    elif assetPriceGrowth3y > 50:
        asset_score = 35
    elif assetPriceGrowth3y > 30:
        asset_score = 20
    elif assetPriceGrowth3y > 10:
        asset_score = 10
    else:
        asset_score = 0

    score = credit_score + asset_score

    # 위기 확률 추정 (GHS 실증 기반 근사)
    if score >= 70:
        crisis_prob = 0.40
    elif score >= 50:
        crisis_prob = 0.25
    elif score >= 30:
        crisis_prob = 0.12
    else:
        crisis_prob = 0.07

    if score >= 70:
        zone, zone_label = "danger", "위험"
    elif score >= 50:
        zone, zone_label = "elevated", "경계"
    elif score >= 30:
        zone, zone_label = "caution", "주의"
    else:
        zone, zone_label = "normal", "정상"

    desc = (
        f"GHS 점수 {score}/100 (신용 {creditGrowth3y:+.1f}%p, 자산 {assetPriceGrowth3y:+.0f}%) "
        f"→ 3년 내 위기 확률 {crisis_prob * 100:.0f}%"
    )

    # Dalio regime 판정
    regime: str | None = None
    regime_label: str | None = None
    if realRate is not None:
        if realRate >= 2.0 and creditGrowth3y < 0:
            regime, regime_label = "deflation", "디플레이션형"
        elif realRate <= 0.0 and creditGrowth3y > 5:
            regime, regime_label = "inflation", "인플레이션형"

    return GHSResult(
        score=round(score, 1),
        zone=zone,
        zoneLabel=zone_label,
        components={
            "creditGrowth3y": round(creditGrowth3y, 2),
            "assetPriceGrowth3y": round(assetPriceGrowth3y, 2),
            "creditScore": credit_score,
            "assetScore": asset_score,
        },
        crisisProb=round(crisis_prob, 3),
        description=desc,
        regime=regime,
        regimeLabel=regime_label,
    )


# ══════════════════════════════════════
# 침체 확률 종합 대시보드
# ══════════════════════════════════════


def recessionDashboard(
    probitProb: float | None = None,
    leiSignal: str | None = None,
    ismLevel: float | None = None,
    creditGap: float | None = None,
    hySpread: float | None = None,
) -> RecessionDashboard:
    """침체 확률 종합 대시보드 — 5 지표 가중 합산 + 역사 패턴 매칭.

    Capabilities:
        Cleveland Fed 프로빗 (35%) + LEI 신호 (25%) + ISM PMI (20%) + Credit
        Gap (10%) + HY 스프레드 (10%) 5 지표 가중평균하여 종합 침체 확률
        산출 + 역사적 침체 패턴 (2008/2020/2001) 와 매칭하여 가장 유사한
        시나리오 식별.

    Args:
        probitProb: Cleveland Fed 프로빗 침체 확률 (0~1).
        leiSignal: LEI 신호 ``"expansion"``/``"caution"``/``"recession_warning"``.
        ismLevel: ISM 제조업 PMI (0~100).
        creditGap: Credit-to-GDP gap (%p, BIS 표준).
        hySpread: HY 스프레드 (bps).

    Returns:
        RecessionDashboard dataclass:
            - ``probabilityComposite`` (float): 가중 합산 (0~1)
            - ``zone``/``zoneLabel`` (str): low/moderate/elevated/high
            - ``signals`` (dict): 5 지표별 변환 확률
            - ``historicalAnalogue`` (str|None): "2008 GFC" 등
            - ``yieldCurveStatus`` (str|None)
            - ``warnings`` (list[str])

    Raises:
        없음.

    Example:
        >>> r = recessionDashboard(probitProb=0.45, leiSignal="recession_warning",
        ...                          ismLevel=48, creditGap=8, hySpread=600)
        >>> r.zone, r.historicalAnalogue
        ('high', '2007-2008 신용 사이클')

    Guide:
        프로빗 가중치 35% 이유: NBER 침체 예측에서 가장 정확. LEI 25%
        는 6 개월 선행. ISM 50 = 확장/수축 경계. composite > 0.50 = 1 년
        내 침체 확률 매우 높음.

    SeeAlso:
        - ``ghsCrisisScore``: GHS 위기 (3 년 horizon)
        - ``minskyPhase``: Minsky 부채 사이클 단계
        - ``classifyCycle``: 매크로 사이클 4 국면

    When:
        ``macro("crisis", "dashboard")``. 침체 가능성 종합 답변 / 자산배분 1 년 horizon.

    How:
        5 지표 각각 임계 분기 → 확률 변환 → 가중 합산 (35/25/20/10/10) → composite + 역사 매칭.

    Requires:
        없음 — 5 지표 모두 옵션, 1 개라도 있으면 동작.

    AIContext:
        composite 만 인용 금지 — signals dict 의 5 지표 분해 + historical
        Analogue 함께 노출. zone="elevated" 결과는 transitioning 신호이지
        즉시 침체 신호 아님.

    LLM Specifications:
        AntiPatterns:
            - hySpread 만 보고 침체 단정 — 본 함수는 5 지표 가중 합산.
            - 프로빗만 5 분기 lag 데이터로 호출 — 결과 신뢰도 낮음 (회귀
              모델 stale).
        OutputSchema:
            RecessionDashboard ``{probabilityComposite, zone, zoneLabel,
            signals, historicalAnalogue, yieldCurveStatus, warnings}``.
        Prerequisites:
            적어도 1 개 지표. 5 개 모두 있으면 신뢰도 high.
        Freshness:
            프로빗 월간 (Cleveland Fed), LEI 월간, ISM 월간 1 일, Credit Gap 분기.
        Dataflow:
            각 지표 → 확률 매핑 → 가중평균 → zone 분류 → 역사 패턴 매칭.
        TargetMarkets: US (Cleveland Fed + ISM + LEI). KR 미적용 (지표 부재).
    """
    observedInputs = sum(value is not None for value in (probitProb, leiSignal, ismLevel, creditGap, hySpread))
    if observedInputs == 0:
        return RecessionDashboard(
            composite=None,
            zone=None,
            zoneLabel="데이터부족",
            components={},
            historicalMatch=None,
            description="침체 대시보드 입력 데이터 부족",
            status="unavailable",
            observedInputs=0,
            totalInputs=5,
        )

    signals: dict[str, float | None] = {}
    weights: list[tuple[float, float]] = []  # (weight, probability)

    # 프로빗 (가장 높은 가중치)
    if probitProb is not None:
        signals["probit"] = round(probitProb, 4)
        weights.append((0.35, probitProb))

    # LEI 신호
    if leiSignal is not None:
        lei_prob = {"expansion": 0.05, "caution": 0.25, "recession_warning": 0.65}.get(leiSignal, 0.15)
        signals["lei"] = round(lei_prob, 4)
        weights.append((0.25, lei_prob))

    # ISM
    if ismLevel is not None:
        if ismLevel < 45:
            ism_prob = 0.60
        elif ismLevel < 48:
            ism_prob = 0.35
        elif ismLevel < 50:
            ism_prob = 0.20
        else:
            ism_prob = 0.05
        signals["ism"] = round(ism_prob, 4)
        weights.append((0.20, ism_prob))

    # Credit gap (장기 신호, 낮은 가중치)
    if creditGap is not None:
        if creditGap > 10:
            cg_prob = 0.40
        elif creditGap > 6:
            cg_prob = 0.20
        elif creditGap > 2:
            cg_prob = 0.10
        else:
            cg_prob = 0.05
        signals["creditGap"] = round(cg_prob, 4)
        weights.append((0.10, cg_prob))

    # HY 스프레드
    if hySpread is not None:
        if hySpread > 700:
            hy_prob = 0.70
        elif hySpread > 500:
            hy_prob = 0.40
        elif hySpread > 400:
            hy_prob = 0.15
        else:
            hy_prob = 0.05
        signals["hySpread"] = round(hy_prob, 4)
        weights.append((0.10, hy_prob))

    # 가중 평균
    if weights:
        total_w = sum(w for w, _ in weights)
        composite = sum(w * p for w, p in weights) / total_w if total_w > 0 else 0.0
    else:
        composite = 0.0

    # 구간
    if composite < 0.15:
        zone, zone_label = "low", "낮음"
    elif composite < 0.30:
        zone, zone_label = "moderate", "보통"
    elif composite < 0.50:
        zone, zone_label = "elevated", "경계"
    else:
        zone, zone_label = "high", "높음"

    # 역사 패턴 매칭 (단순 규칙 기반)
    historical = "normal"
    if composite > 0.5 and creditGap is not None and creditGap > 8:
        historical = "resembles_2008"  # 신용위기형
    elif composite > 0.4 and ismLevel is not None and ismLevel < 45:
        historical = "resembles_2001"  # 제조업 침체형
    elif composite > 0.3 and hySpread is not None and hySpread > 600:
        historical = "resembles_2020"  # 급성 충격형

    desc = f"침체 확률 종합 {composite * 100:.1f}% ({zone_label})"
    if historical != "normal":
        year = historical.split("_")[1]
        desc += f" — {year}년 패턴과 유사"

    return RecessionDashboard(
        composite=round(composite, 4),
        zone=zone,
        zoneLabel=zone_label,
        components=signals,
        historicalMatch=historical if historical != "normal" else None,
        description=desc,
        status="usable" if observedInputs >= 3 else "partial",
        observedInputs=observedInputs,
        totalInputs=5,
    )


# ══════════════════════════════════════
# Minsky 5단계 판별 (Kindleberger-Minsky)
# ══════════════════════════════════════


# ── minskyPhase + kooBalanceSheetRecession + fisherDebtDeflation + krHousingFinancialStress → _detectorsMinsky.py 분리 ──

from dartlab.macro.crisis._detectorsMinsky import (  # noqa: E402, F401
    fisherDebtDeflation,
    kooBalanceSheetRecession,
    krHousingFinancialStress,
    minskyPhase,
)
