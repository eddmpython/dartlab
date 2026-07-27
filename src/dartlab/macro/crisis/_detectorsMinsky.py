"""macro/crisis/detectors.py 위기 detector 분리 — Minsky/Koo/Fisher/KR Housing.

분리 이유: detectors.py 903 줄. 4 detector (minskyPhase 161 + kooBalanceSheetRecession
94 + fisherDebtDeflation 102 + krHousingFinancialStress 44) 약 400 줄. detectors.py
의 facade (creditToGDPGap · ghsCrisisScore · recessionDashboard) 책임 유지.

BC: detectors 모듈에서 4 detector 모두 import 가능 (re-export).
"""

from __future__ import annotations

from dartlab.macro.crisis._detectorsRegime import _oneSidedHpTrend
from dartlab.macro.crisis._detectorTypes import (
    FisherDeflationResult,
    KooRecessionResult,
    KRHousingStressResult,
    MinskyPhaseResult,
)


def minskyPhase(
    creditGap: float | None = None,
    assetReturn3y: float | None = None,
    hySpread: float | None = None,
    vix: float | None = None,
    ponziRatio: float | None = None,
    dxyChange: float | None = None,
) -> MinskyPhaseResult:
    """Kindleberger-Minsky 5 단계 (displacement→boom→overtrading→discredit→revulsion).

    Capabilities:
        Minsky (1986) "Stabilizing an Unstable Economy" + Kindleberger (1978)
        "Manias, Panics and Crashes" 의 5 단계 모델 — Credit gap + 자산 수익
        + HY 스프레드 + VIX + Ponzi 비율 + 달러 변화 6 지표 가중 투표로 현재
        단계 판정. 부채 사이클 분석의 결정판.

    Args:
        creditGap: Credit-to-GDP gap (%p).
        assetReturn3y: 자산 3 년 수익률 (%).
        hySpread: HY 스프레드 (bps).
        vix: CBOE VIX.
        ponziRatio: Ponzi 단계 비율 (회수성 대비 신규차입 의존도, %).
        dxyChange: 달러 인덱스 변화 (%).

    Returns:
        MinskyPhaseResult dataclass:
            - ``phase`` (str): 5 단계 중 하나
            - ``phaseLabel`` (str): 한국어
            - ``signals`` (list[str]): 판정 근거
            - ``scores`` (dict): 5 단계 점수
            - ``confidence`` (str)

    Raises:
        없음.

    Example:
        >>> r = minskyPhase(creditGap=12, assetReturn3y=60, vix=15,
        ...                  ponziRatio=35)
        >>> r.phase
        'overtrading'

    Guide:
        5 단계 시간 순서:
        - displacement: 외부 충격 (기술 혁신, 정책 변화) → 신용 시작
        - boom: 자산 가격 상승 + 신용 확장
        - overtrading: 과열 (credit gap > 10%, asset > 50% 3Y)
        - discredit: panic 시작 (HY 급등, VIX panic)
        - revulsion: 신용 수축 (credit gap < -5, asset 하락)

    SeeAlso:
        - ``creditToGDPGap``: BIS 신용 거품
        - ``ghsCrisisScore``: GHS 위기 예측
        - ``dalioDebtCyclePhase``: Dalio 6 단계 (Minsky 확장)

    When:
        ``macro("crisis", "minsky")``. AI 가 부채 사이클 답변 시.

    How:
        6 지표 각각 임계 분기 → 5 단계 scores 누적 → max score → phase 결정 → confidence.

    Requires:
        없음 — 6 지표 모두 옵션. 1 개라도 있으면 동작.

    AIContext:
        phase 라벨 + signals 함께 인용. confidence=low 결과는 전환기 — 분기
        후 재호출 권장. ponziRatio > 50 은 Hyman Minsky 의 Ponzi 단계 강신호.

    LLM Specifications:
        AntiPatterns:
            - 단일 지표 (VIX 만) 로 단계 판정 — 본 함수는 6 지표 합산.
            - displacement → revulsion 5 단계는 시간 순서이지만 동시 신호
              가능 — phase 가 항상 순서대로 진행하지 않음.
        OutputSchema:
            MinskyPhaseResult ``{phase, phaseLabel, signals, scores, confidence}``.
        Prerequisites:
            적어도 2 개 지표 권장 (1 개만이면 confidence=low).
        Freshness:
            지표별 (BIS 분기, VIX/HY 일, asset return 월).
        Dataflow:
            지표별 룰 → scores 5 단계 누적 → max → phase 결정 → confidence.
        TargetMarkets: US (FRED 표준), Global (BIS).
    """
    signals: list[str] = []
    scores = {"displacement": 0, "boom": 0, "overtrading": 0, "discredit": 0, "revulsion": 0}

    if creditGap is not None:
        if creditGap > 10:
            scores["overtrading"] += 3
            signals.append(f"Credit-to-GDP gap {creditGap:+.1f}%p — 과열")
        elif creditGap > 5:
            scores["boom"] += 2
            signals.append(f"Credit-to-GDP gap {creditGap:+.1f}%p — 호황")
        elif creditGap < -5:
            scores["revulsion"] += 2
            signals.append(f"Credit-to-GDP gap {creditGap:+.1f}%p — 신용 수축")

    if assetReturn3y is not None:
        if assetReturn3y > 60:
            scores["overtrading"] += 2
            signals.append(f"자산가격 3Y 수익률 {assetReturn3y:.0f}% — 과열")
        elif assetReturn3y > 30:
            scores["boom"] += 2
            signals.append(f"자산가격 3Y 수익률 {assetReturn3y:.0f}% — 호황")
        elif assetReturn3y < -20:
            scores["discredit"] += 2
            signals.append(f"자산가격 3Y 수익률 {assetReturn3y:.0f}% — 공황")

    if hySpread is not None:
        if hySpread > 600:
            scores["discredit"] += 3
            signals.append(f"HY 스프레드 {hySpread:.0f}bp — 공황")
        elif hySpread < 300:
            scores["overtrading"] += 1
            signals.append(f"HY 스프레드 {hySpread:.0f}bp — 과열(신용 완화)")

    if vix is not None:
        if vix > 35:
            scores["discredit"] += 2
        elif vix < 15:
            scores["overtrading"] += 1

    if ponziRatio is not None:
        if ponziRatio > 0.3:
            scores["overtrading"] += 2
            signals.append(f"Ponzi 비율 {ponziRatio:.1%} — 과열")
        elif ponziRatio > 0.2:
            scores["boom"] += 1

    if dxyChange is not None:
        if dxyChange > 5:
            scores["revulsion"] += 2
            signals.append(f"달러 급등 {dxyChange:+.1f}% — 전염")

    # 최고 점수 단계
    best = max(scores, key=scores.get)
    best_score = scores[best]

    labels = {
        "displacement": "이전",
        "boom": "호황",
        "overtrading": "과열",
        "discredit": "공황",
        "revulsion": "전염",
    }

    if best_score >= 4:
        confidence = "high"
    elif best_score >= 2:
        confidence = "medium"
    else:
        confidence = "low"
        best = "displacement"  # 판별 불가 시 초기 단계

    return MinskyPhaseResult(
        phase=best,
        phaseLabel=labels[best],
        confidence=confidence,
        signals=signals,
        description=f"Minsky 순환: {labels[best]} ({confidence})",
    )


# ══════════════════════════════════════
# Koo Balance Sheet Recession
# ══════════════════════════════════════


def kooBalanceSheetRecession(
    privateSaving: float,
    privateInvestment: float,
    gdp: float,
    policyRate: float,
) -> KooRecessionResult:
    """Koo Balance Sheet Recession — 민간 금융 잉여 + 저금리 = BSR 진단.

    Capabilities:
        Richard Koo (Nomura, 2003) 의 BSR 모델 — 민간 (가계 + 기업) 이 부채
        상환을 우선시할 때 차입 수요가 사라져 통화정책 무력화. 잉여 > GDP
        3% + 정책금리 < 2% = BSR 신호. 일본 잃어버린 30년 + 2008 후 미국/
        유럽 일부 적용.

    Args:
        privateSaving: 민간 부문 총저축 (원).
        privateInvestment: 민간 총투자 (원).
        gdp: GDP (원). 잉여 비율 계산 분모.
        policyRate: 정책금리 (%).

    Returns:
        KooRecessionResult dataclass:
            - ``surplus`` (float): 민간 금융 잉여 (% of GDP)
            - ``policyRate`` (float)
            - ``isBSR`` (bool): 본격 BSR 여부
            - ``description`` (str)

    Raises:
        없음.

    Example:
        >>> r = kooBalanceSheetRecession(privateSaving=200e12,
        ...                              privateInvestment=170e12,
        ...                              gdp=1000e12, policyRate=0.5)
        >>> r.isBSR
        True

    Guide:
        BSR 임계: surplus > 3% + policyRate < 2%. surplus 만 높으면 부분
        BSR (재정 확대 효과 약화), 둘 다 충족하면 본격 BSR (금리 무력화,
        재정 확대 필수). 일본 1995~2005, 미국 2009~2015 사례.

    SeeAlso:
        - ``fisherDebtDeflation``: Fisher (1933) 부채 디플레이션 (BSR 의
          극단)
        - ``minskyPhase``: Minsky revulsion (deleveraging 단계)
        - Koo, R. (2003) "Balance Sheet Recession" Nomura

    When:
        ``macro("crisis", "bsr")``. 일본형 / 미국형 BSR 답변, 정책 권고 산출 시.

    How:
        surplus = (privateSaving - privateInvestment) / GDP × 100 → 임계 (3% + 정책금리 < 2%)
        → isBSR 플래그 + 설명문.

    Requires:
        privateSaving + privateInvestment + gdp > 0 + policyRate.

    AIContext:
        BSR 진단 + 정책 권고 ("재정 확대 필수") 함께 노출. surplus 음수면
        민간 차입 우위 (정상), positive 큰 값이 위기 신호.

    LLM Specifications:
        AntiPatterns:
            - GDP=0 또는 음수 입력 시 빈 결과 → 호출자 분기 필요.
            - 단기 (1 분기) 잉여만 보고 BSR 단정 — 3~5 년 sustained 필요.
        OutputSchema:
            KooRecessionResult ``{surplus, policyRate, isBSR, description}``.
        Prerequisites:
            국민계정 (saving/investment/GDP) + 정책금리.
        Freshness:
            국민계정 분기. 정책금리 일.
        Dataflow:
            (saving - investment) / GDP × 100 → surplus → +rate 임계 → isBSR.
        TargetMarkets: 일본 (Koo 원형), 미국 (2008 후), 한국 (2020~).
    """
    if gdp <= 0:
        return KooRecessionResult(0, policyRate, False, "GDP 데이터 없음")

    surplus = ((privateSaving - privateInvestment) / gdp) * 100

    is_bsr = surplus > 3.0 and policyRate < 2.0

    if is_bsr:
        desc = (
            f"민간 금융 잉여 GDP의 {surplus:.1f}% + 정책금리 {policyRate:.2f}% "
            f"— 재무상태표 침체: 민간이 차입 대신 부채 상환 중. 재정 확대 필수"
        )
    elif surplus > 3.0:
        desc = f"민간 잉여 {surplus:.1f}% 높으나 금리 {policyRate:.2f}% — 부분적 BSR 징후"
    else:
        desc = f"민간 잉여 {surplus:.1f}%, 금리 {policyRate:.2f}% — 정상"

    return KooRecessionResult(round(surplus, 2), round(policyRate, 2), is_bsr, desc)


# ══════════════════════════════════════
# Fisher Debt-Deflation
# ══════════════════════════════════════


def fisherDebtDeflation(
    dsr: float,
    cpiYoy: float,
    nplRate: float | None = None,
) -> FisherDeflationResult:
    """Fisher (1933) Debt-Deflation — 고부채 + 디플레이션 → 실질 부채 증가 악순환.

    Capabilities:
        Irving Fisher (1933) "The Debt-Deflation Theory of Great Depressions"
        의 핵심 — 고부채 + 디플레이션 결합 시 실질 부채 부담 증가 → 자산
        매각 → 자산 가격 하락 → 신용 수축 → 추가 디플레이션 의 9-step
        악순환. DSR + CPI + NPL 3 지표로 위험 점수 산출.

    Args:
        dsr: 부채서비스비율 (원리금/소득, %). > 14% = 역사적 고수준.
        cpiYoy: CPI YoY (%). < 0 = 디플레이션, < 1 = 준디플레.
        nplRate: 부실대출비율 (%). 옵션. > 5% = 위기 임박.

    Returns:
        FisherDeflationResult dataclass:
            - ``riskScore`` (int): 0~7
            - ``zone`` (str): low/moderate/high/extreme
            - ``zoneLabel`` (str): 한국어
            - ``description`` (str): 한국어 진단

    Raises:
        없음.

    Example:
        >>> r = fisherDebtDeflation(dsr=15, cpiYoy=-0.5, nplRate=4.5)
        >>> r.zone
        'high'

    Guide:
        riskScore 임계: 0~1 = low (정상), 2~3 = moderate (주의), 4~5 = high
        (위험), 6+ = extreme (Fisher 시나리오 본격). 디플레이션 (CPI<0) 단
        독으로 +3점 — 가장 큰 가중치.

    SeeAlso:
        - ``kooBalanceSheetRecession``: BSR (Fisher 의 시장 측면)
        - ``minskyPhase``: Minsky revulsion (deleveraging)
        - Fisher, I. (1933) "The Debt-Deflation Theory of Great Depressions"

    When:
        ``macro("crisis", "fisher")``. 일본형 디플레 / 대공황 시나리오 답변 시.

    How:
        DSR 임계 (>14 +2 / >11 +1) + CPI 임계 (디플레 +3 / 준디플레 +1) + NPL 임계 → riskScore →
        zone 라벨.

    Requires:
        dsr + cpiYoy 필수. nplRate 옵션 (없으면 2 지표만).

    AIContext:
        Fisher 시나리오는 통화정책 무력화 + 재정 확대 필수 (Friedman + Koo).
        zone="extreme" 결과는 정책 결정자 향 (개별 기업 향이 아님).

    LLM Specifications:
        AntiPatterns:
            - 단기 (1 개월) CPI 음수 → 디플레 단정 — 3 개월 연속 음수 필요.
            - DSR > 14% 만 보고 위기 단정 — CPI 정상이면 정상 부채 부담.
        OutputSchema:
            FisherDeflationResult ``{riskScore, zone, zoneLabel, description}``.
        Prerequisites:
            국민계정 DSR (분기) + CPI (월) + NPL (분기).
        Freshness:
            DSR 분기, CPI 월, NPL 분기.
        Dataflow:
            DSR + CPI + NPL 룰 → riskScore 누적 → zone 분류.
        TargetMarkets: KR (한국은행 DSR), Global. 일본 1995~2000 가장 적합.
    """
    riskScore = 0

    if dsr > 14:
        riskScore += 2  # 역사적 고수준
    elif dsr > 11:
        riskScore += 1

    if cpiYoy < 0:
        riskScore += 3  # 디플레이션
    elif cpiYoy < 1:
        riskScore += 1  # 준디플레

    if nplRate is not None:
        if nplRate > 5:
            riskScore += 2
        elif nplRate > 2:
            riskScore += 1

    if riskScore >= 4:
        risk, risk_label = "high", "높음"
        desc = f"DSR {dsr:.1f}% + CPI {cpiYoy:.1f}% — 부채 디플레이션 악순환 위험"
    elif riskScore >= 2:
        risk, risk_label = "moderate", "보통"
        desc = f"DSR {dsr:.1f}% + CPI {cpiYoy:.1f}% — 부분적 디플레이션 압력"
    else:
        risk, risk_label = "low", "낮음"
        desc = f"DSR {dsr:.1f}% + CPI {cpiYoy:.1f}% — 정상"

    return FisherDeflationResult(
        round(dsr, 1), round(nplRate, 1) if nplRate else None, round(cpiYoy, 1), risk, risk_label, desc
    )


# ══════════════════════════════════════
# 한국 부동산-금융 스트레스
# ══════════════════════════════════════


def krHousingFinancialStress(
    housePriceYoy: float,
    householdDebtYoy: float | None = None,
) -> KRHousingStressResult:
    """한국 부동산-금융 스트레스: 주택가격 + 가계부채 복합.

    Capabilities:
        주택가격 YoY + 가계부채 YoY 결합 스트레스 점수 산출. 한국 가계부채/GDP 91% 환경에서
        주택 가격 → 전세 → 대출 전이 경로 위험 진단.

    한국 가계부채/GDP = 91%. 주택가격 → 전세 → 대출 전이 경로.

    Args:
        housePriceYoy: 주택가격 YoY (%).
        householdDebtYoy: 가계부채 YoY (%) (optional).

    Returns:
        KRHousingStressResult dataclass.

    Raises:
        없음.

    Example:
        >>> krHousingFinancialStress(housePriceYoy=-5, householdDebtYoy=8)

    Guide:
        주택가격 급락 + 가계부채 증가 = 한국 특이 위기 패턴. 일반 BSR/Fisher 와 분리 사용.

    When:
        ``macro("crisis", "krHousing")``. 한국 부동산 시장 위기 답변 시.

    How:
        주택가격 YoY 음수 가중 + 가계부채 YoY 증가 가중 → 점수 → 라벨.

    Requires:
        - 입력 지표 (한국은행 / KB부동산 시계열)

    See Also:
        - ``dartlab.macro.crisis._detectorsMinsky.fisherDebtDeflation`` : 일반 디플레

    AIContext:
        한국 특이 위기 답변 시 본 함수 결과 인용. 일반 디플레와 분리 명시.
    """
    score = 0
    if housePriceYoy > 10:
        score += 2  # 과열
    elif housePriceYoy < -5:
        score += 2  # 급락 (역방향 스트레스)

    if householdDebtYoy is not None:
        if householdDebtYoy > 8:
            score += 2
        elif householdDebtYoy > 5:
            score += 1

    if score >= 3:
        return KRHousingStressResult(
            round(housePriceYoy, 1),
            round(householdDebtYoy, 1) if householdDebtYoy else None,
            "high",
            "높음",
            f"주택가격 {housePriceYoy:+.1f}% + 가계부채 위험",
        )
    elif score >= 1:
        return KRHousingStressResult(
            round(housePriceYoy, 1),
            round(householdDebtYoy, 1) if householdDebtYoy else None,
            "moderate",
            "보통",
            f"주택가격 {housePriceYoy:+.1f}% — 경계 필요",
        )
    else:
        return KRHousingStressResult(
            round(housePriceYoy, 1),
            round(householdDebtYoy, 1) if householdDebtYoy else None,
            "low",
            "낮음",
            f"주택가격 {housePriceYoy:+.1f}% — 안정",
        )
