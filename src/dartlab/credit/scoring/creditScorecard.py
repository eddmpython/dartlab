"""신용등급 산출 순수 로직.

업종별 기준표에서 각 지표를 0-100 위험 점수로 변환하고,
5축 가중평균으로 종합 점수를 산출한다. 20단계 등급(AAA~D) 매핑표는
``credit.gradeTable`` SSOT (P3.6 후 도메인 복귀).
"""

from __future__ import annotations

# 20단계 등급 매핑표 + 변환 함수는 credit 도메인 SSOT — analysis/bond 등은 단방향 import.
from dartlab.credit.scoring.gradeTable import (  # noqa: F401
    estimatePD,
    gradeCategory,
    isInvestmentGrade,
    mapTo20Grade,
    notchGrade,
)


def scoreMetric(
    value: float | None,
    thresholdDef: dict,
) -> float | None:
    """단일 지표 → 0-100 위험 점수 (선형 보간).

    Capabilities:
        thresholdDef 의 breakpoints 와 lower_is_better 플래그로 입력값을 0~100 위험 점수로
        선형 보간 변환. 범위 밖 값은 양 끝 클램프. credit scorecard 의 기본 매핑 primitive.

    thresholdDef: {"lower_is_better": bool, "breakpoints": [(value, score), ...]}
    breakpoints는 값 오름차순 정렬 가정.

    Args:
        value: 입력 metric 값.
        thresholdDef: {"lower_is_better": bool, "breakpoints": list[tuple]}.

    Returns:
        float | None — 0~100 위험 점수. value=None 이면 None.

    Raises:
        KeyError: thresholdDef 에 ``lower_is_better`` / ``breakpoints`` 키 부재 시.

    Example:
        >>> scoreMetric(2.5, {"lower_is_better": True, "breakpoints": [(0.0, 0), (5.0, 50)]})
        25.0

    Guide:
        breakpoints 는 0 ~ 100 점수 (0=최우량). lower_is_better=True 면 값 ↑ 위험 ↑.

    When:
        ``calcCreditHistory`` / scorecard 내부에서 각 metric 점수 산출 시.

    How:
        lower_is_better 반전 → 양 끝 클램프 → 인접 breakpoint 쌍 보간.

    Requires:
        - thresholdDef 의 breakpoints 오름차순 + 각 (value, score) tuple

    See Also:
        - ``dartlab.credit.scoring.creditScorecard.weightedScore`` : 7 축 합성
        - ``dartlab.credit.features.sectorThresholds.getThresholds`` : 기준표 소스

    AIContext:
        AI 직접 호출 없음 (내부 헬퍼).
    """
    if value is None:
        return None

    lower_is_better = thresholdDef["lower_is_better"]
    bps = thresholdDef["breakpoints"]

    if not bps:
        return None

    # lower_is_better=False인 지표는 값 내림차순 → 오름차순 반전
    if not lower_is_better:
        bps = [(v, s) for v, s in reversed(bps)]

    # 범위 밖 처리
    if value <= bps[0][0]:
        return bps[0][1]
    if value >= bps[-1][0]:
        return bps[-1][1]

    # 선형 보간
    for i in range(len(bps) - 1):
        v0, s0 = bps[i]
        v1, s1 = bps[i + 1]
        if v0 <= value <= v1:
            if v1 == v0:
                return s0
            ratio = (value - v0) / (v1 - v0)
            return round(s0 + ratio * (s1 - s0), 2)

    return bps[-1][1]


def weightedScore(axes: list[dict]) -> float | None:
    """7 축 결과 list → 가중평균 종합 신용 위험 점수.

    Capabilities:
        각 축의 ``score`` 와 ``weight`` 를 받아 None 축 제외 후 나머지로
        가중치 재분배하여 0~100 점 (0=최우량, 100=최위험) 점수 산출.
        credit/engine 의 최종 등급 산출에 사용.

    Args:
        axes: ``[{"name": str, "score": float|None, "weight": float}, ...]``
            형태 리스트. score=None 인 축은 가중치 재분배로 제외.

    Returns:
        float | None: 0~100 점 가중평균. 모든 score=None 또는 totalWeight=0 시 None.

    Raises:
        없음. score/weight 가 dict 에 없으면 KeyError 가능.

    Example:
        >>> axes = [{"name": "repayment", "score": 30, "weight": 0.3},
        ...         {"name": "leverage", "score": 25, "weight": 0.2}]
        >>> weightedScore(axes)
        28.0

    Guide:
        7 축 weights 표준 (engine 설정): repayment 0.30 + leverage 0.20 +
        liquidity 0.10 + cashFlow 0.15 + businessStability 0.10 +
        reliability 0.10 + disclosureRisk 0.05. 결과 점수는 ``mapTo20Grade``
        로 dCR 등급 (AAA ~ D) 변환.

    SeeAlso:
        - ``dartlab.synth.creditGradeTable.mapTo20Grade``: 점수 → 등급
        - ``axisScore``: 개별 축 점수 산출
        - ``creditOutlook``: 점수 시계열 → 전망

    When:
        ``credit.engine.evaluateCompany`` 가 7 축 score 합성 시.

    How:
        valid (score is not None) 축 추출 → totalWeight 합 → 가중합 / totalWeight.

    Requires:
        없음 (순수 함수).

    AIContext:
        score=None 축이 절반 이상이면 결과 신뢰도 낮음 — 호출자는 valid 축
        개수를 함께 확인. 관측 축이 없으면 실제 중립 점수로 대체하지 않고 None을 반환한다.

    LLM Specifications:
        AntiPatterns:
            - 결과 점수만 단독 인용 금지. 등급 + outlook + valid 축 개수도 함께.
            - axes dict 의 weight 변경하면서 합계 1.0 보존 가정 금지 — 본 함수가
              내부에서 재분배.
        OutputSchema:
            float ∈ [0, 100]. 0 = 최우량 (AAA), 100 = 최위험 (D).
        Prerequisites:
            axes list 의 각 dict 가 ``score``, ``weight`` 키 보유.
        Freshness:
            stateless — 입력 axes 의 freshness 에 따름.
        Dataflow:
            axes → (score, weight) pair list (None 제외) → totalWeight → 가중합/totalWeight.
        TargetMarkets: KR + Global. 등급표 (mapTo20Grade) 가 시장별 분기.
    """
    valid = [(a["score"], a["weight"]) for a in axes if a.get("score") is not None]
    if not valid:
        return None

    totalWeight = sum(w for _, w in valid)
    if totalWeight <= 0:
        return None

    return round(sum(s * w for s, w in valid) / totalWeight, 2)


# mapTo20Grade / estimatePD / notchGrade / isInvestmentGrade / gradeCategory:
# synth/creditGradeTable SSOT 에서 import (모듈 상단 from 절). 중복 정의 제거.


# ── 현금흐름등급 (eCR) ──


def cashFlowGrade(
    ocfToSales: float | None,
    fcfPositive: bool | None,
    ocfToDebt: float | None,
    ocfTrendStable: bool | None = None,
) -> str:
    """현금흐름등급 eCR-1 ~ eCR-6.

    Capabilities:
        OCF/매출 + FCF 양수 여부 + OCF/총차입금 (+ 안정성) 입력으로 eCR-1 (최상) ~ eCR-6 (심각)
        라벨 결정. 한국 신평사 현금흐름창출능력 별도 평가 대응.

    한국 신평사 현금흐름창출능력 별도 평가 대응.

    Args:
        ocfToSales: 영업현금흐름/매출 (%).
        fcfPositive: FCF 양수 여부.
        ocfToDebt: 영업현금흐름/총차입금 (%).
        ocfTrendStable: 시계열 안정성 (optional).

    Returns:
        str: "eCR-1" ~ "eCR-6" 또는 "eCR-?" (ocfToSales None).

    Raises:
        없음.

    Example:
        >>> cashFlowGrade(18.0, True, 35.0)
        'eCR-1'

    Guide:
        eCR-1: OCF/매출 > 15% + FCF 양수 + OCF/총차입금 > 30%. eCR-6: OCF/매출 ≤ -5%.

    When:
        ``calcCashFlowGrade`` 가 기간별로 본 함수 호출.

    How:
        ocfToSales 임계 분기 → 보조 조건 (FCF / OCF-Debt / trend) → eCR 라벨.

    Requires:
        - 외부 의존 없음.

    See Also:
        - ``dartlab.credit.scoring.calcs.calcCashFlowGrade`` : 본 함수 사용자

    AIContext:
        AI 답변에 eCR 단독 인용 가능. 회계 grade 와 차이 있으면 "현금/이익 괴리" 단서 권장.
    """
    if ocfToSales is None:
        return "eCR-?"

    # eCR-1: 최상의 현금흐름
    if ocfToSales > 15 and (fcfPositive is True) and (ocfToDebt is not None and ocfToDebt > 30):
        return "eCR-1"

    # eCR-2: 우수
    if ocfToSales > 10 and (ocfToDebt is not None and ocfToDebt > 20):
        return "eCR-2"

    # eCR-3: 양호
    if ocfToSales > 5 and (ocfTrendStable is not False):
        return "eCR-3"

    # eCR-4: 보통
    if ocfToSales > 0:
        return "eCR-4"

    # eCR-5: 취약
    if ocfToSales > -5:
        return "eCR-5"

    # eCR-6: 심각
    return "eCR-6"


# ── 등급 전망 (Outlook) ──


def creditOutlook(scoreHistory: list[float]) -> str:
    """5개년 종합점수 추세 → 안정적/긍정적/부정적.

    Capabilities:
        최신 vs 가장 오래된 점수 차이 (delta) 가 ±5 점 임계를 넘으면 긍정적/부정적, 그 외는 안정적
        라벨 반환. credit grade 의 outlook 필드 산출 헬퍼.

    scoreHistory: 최신→과거 순서 점수 리스트.

    Args:
        scoreHistory: 최신 → 과거 순서 점수 리스트. 길이 < 2 면 "N/A".

    Returns:
        str: "긍정적" | "안정적" | "부정적" | "N/A".

    Raises:
        없음.

    Example:
        >>> creditOutlook([15, 20, 28, 35])
        '긍정적'

    Guide:
        점수 ↓ 이 위험 ↓ (개선) = 긍정적. 5 점은 ~1 notch 변동.

    When:
        ``credit.engine.evaluateCompany`` 가 grade 의 outlook 산출 시.

    How:
        scoreHistory[0] - scoreHistory[-1] = delta → ±5 임계 → 라벨.

    Requires:
        - 외부 의존 없음.

    See Also:
        - ``dartlab.credit.scoring.calcs.calcCreditHistory`` : 점수 시계열

    AIContext:
        AI 답변 "outlook 긍정적/부정적" 인용 시 임계 ±5 점 단서 명시 권장.
    """
    if not scoreHistory or len(scoreHistory) < 2:
        return "N/A"

    recent = scoreHistory[0]
    oldest = scoreHistory[-1]
    delta = recent - oldest

    # 점수 하락(개선) = 긍정적, 상승(악화) = 부정적
    if delta < -5:
        return "긍정적"
    if delta > 5:
        return "부정적"
    return "안정적"


def axisScore(
    metricScores: list,
) -> float | None:
    """축 내 개별 지표 점수들의 평균 → 축 점수.

    Capabilities:
        축 내 개별 지표 점수 (tuple 또는 dict 입력) 의 단순 평균 산출. None 지표는 제외. 모두
        None 이면 None 반환.

    metricScores: [(지표명, 점수|None), ...] 또는 [{"name", "value", "score"}, ...]
    None인 지표는 제외. tuple/dict 둘 다 지원 (R21-1: metrics 에 value 포함).

    Args:
        metricScores: 지표 점수 list. tuple ``(name, score)`` 또는 dict ``{name, value, score}``.

    Returns:
        float | None — 평균 점수. 모두 None 이면 None.

    Raises:
        없음.

    Example:
        >>> axisScore([("ocfToSales", 25.0), ("fcfMargin", 18.0)])
        21.5

    Guide:
        축 가중치는 ``weightedScore`` 에서 적용 — 본 함수는 축 내부 평균만.

    When:
        ``credit.engine`` 의 축별 score 합성 시.

    How:
        valid 점수 추출 (None 제외) → 단순 평균.

    Requires:
        - 외부 의존 없음.

    See Also:
        - ``dartlab.credit.scoring.creditScorecard.weightedScore`` : 축 가중평균

    AIContext:
        AI 직접 호출 없음 (내부 헬퍼).
    """
    valid: list[float] = []
    for item in metricScores:
        if isinstance(item, dict):
            s = item.get("score")
        else:
            _, s = item
        if s is not None:
            valid.append(s)
    if not valid:
        return None
    return round(sum(valid) / len(valid), 2)
