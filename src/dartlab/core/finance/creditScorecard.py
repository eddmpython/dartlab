"""신용등급 산출 순수 로직.

업종별 기준표에서 각 지표를 0-100 위험 점수로 변환하고,
5축 가중평균으로 종합 점수를 산출한 뒤 20단계 등급(AAA~D)을 매핑한다.

이 모듈은 L0(core)에 위치하며 업종/시장 독립적인 순수 함수만 포함한다.
"""

from __future__ import annotations

# ── 20단계 등급 테이블 ──
#
# (상한점수, 등급, 설명, 1년PD%)
# KIS 실측(1998-2025) + S&P 글로벌 PD를 종합.

_GRADE_20_TABLE: list[tuple[float, str, str, float]] = [
    (3, "AAA", "투자적격 최상위", 0.00),
    (5, "AA+", "투자적격 상위+", 0.01),
    (8, "AA", "투자적격 상위", 0.02),
    (10, "AA-", "투자적격 상위-", 0.03),
    (13, "A+", "투자적격+", 0.04),
    (16, "A", "투자적격", 0.06),
    (19, "A-", "투자적격-", 0.08),
    (22, "BBB+", "투자적격 하한+", 0.15),
    (27, "BBB", "투자적격 하한", 0.25),
    (32, "BBB-", "투자적격 하한-", 0.40),
    (37, "BB+", "투기등급+", 0.75),
    (42, "BB", "투기등급", 1.50),
    (48, "BB-", "투기등급-", 2.50),
    (55, "B+", "투기등급 하위+", 4.00),
    (62, "B", "투기등급 하위", 7.00),
    (70, "B-", "투기등급 하위-", 10.00),
    (78, "CCC", "상당한 부실 위험", 15.00),
    (85, "CC", "부실 임박", 25.00),
    (93, "C", "부도 직전", 40.00),
    (100, "D", "부도", 100.00),
]

# ── 등급 순서 인덱스 (notching 계산용) ──

_GRADE_ORDER: list[str] = [row[1] for row in _GRADE_20_TABLE]
_GRADE_TO_IDX: dict[str, int] = {g: i for i, g in enumerate(_GRADE_ORDER)}


def scoreMetric(
    value: float | None,
    thresholdDef: dict,
) -> float | None:
    """단일 지표 → 0-100 위험 점수 (선형 보간).

    thresholdDef: {"lower_is_better": bool, "breakpoints": [(value, score), ...]}
    breakpoints는 값 오름차순 정렬 가정.
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


def weightedScore(axes: list[dict]) -> float:
    """5축 가중평균 종합 점수.

    axes: [{"name": str, "score": float|None, "weight": float}, ...]
    score가 None인 축은 제외하고 나머지 가중치를 재분배.
    """
    valid = [(a["score"], a["weight"]) for a in axes if a.get("score") is not None]
    if not valid:
        return 50.0  # 데이터 없으면 중립

    totalWeight = sum(w for _, w in valid)
    if totalWeight <= 0:
        return 50.0

    return round(sum(s * w for s, w in valid) / totalWeight, 2)


def mapTo20Grade(score: float) -> tuple[str, str, float]:
    """종합 점수(0-100) → (등급, 설명, PD추정%).

    점수가 클수록 위험. 0=AAA, 100=D.
    """
    score = max(0.0, min(100.0, score))
    for threshold, grade, desc, pd in _GRADE_20_TABLE:
        if score < threshold:
            return grade, desc, pd
    return "D", "부도", 100.0


def estimatePD(grade: str) -> float:
    """등급 → 1년 부도확률(%) 추정."""
    for _, g, _, pd in _GRADE_20_TABLE:
        if g == grade:
            return pd
    return 50.0


def notchGrade(grade: str, notches: int) -> str:
    """등급을 n notch 상향(+) 또는 하향(-) 조정."""
    idx = _GRADE_TO_IDX.get(grade)
    if idx is None:
        return grade
    newIdx = max(0, min(len(_GRADE_ORDER) - 1, idx + notches))
    return _GRADE_ORDER[newIdx]


def isInvestmentGrade(grade: str) -> bool:
    """투자적격 등급(BBB- 이상) 여부."""
    idx = _GRADE_TO_IDX.get(grade)
    if idx is None:
        return False
    bbbMinusIdx = _GRADE_TO_IDX.get("BBB-", 9)
    return idx <= bbbMinusIdx


def gradeCategory(grade: str) -> str:
    """등급 대분류 카테고리."""
    if isInvestmentGrade(grade):
        idx = _GRADE_TO_IDX.get(grade, 0)
        if idx <= 3:
            return "최우량"
        if idx <= 6:
            return "우량"
        return "적격"
    idx = _GRADE_TO_IDX.get(grade, 10)
    if idx <= 12:
        return "투기"
    if idx <= 15:
        return "고위험"
    return "부실"


# ── 현금흐름등급 (eCR) ──


def cashFlowGrade(
    ocf_to_sales: float | None,
    fcf_positive: bool | None,
    ocf_to_debt: float | None,
    ocf_trend_stable: bool | None = None,
) -> str:
    """현금흐름등급 eCR-1 ~ eCR-6.

    한국 신평사 현금흐름창출능력 별도 평가 대응.
    """
    if ocf_to_sales is None:
        return "eCR-?"

    # eCR-1: 최상의 현금흐름
    if ocf_to_sales > 15 and (fcf_positive is True) and (ocf_to_debt is not None and ocf_to_debt > 30):
        return "eCR-1"

    # eCR-2: 우수
    if ocf_to_sales > 10 and (ocf_to_debt is not None and ocf_to_debt > 20):
        return "eCR-2"

    # eCR-3: 양호
    if ocf_to_sales > 5 and (ocf_trend_stable is not False):
        return "eCR-3"

    # eCR-4: 보통
    if ocf_to_sales > 0:
        return "eCR-4"

    # eCR-5: 취약
    if ocf_to_sales > -5:
        return "eCR-5"

    # eCR-6: 심각
    return "eCR-6"


# ── 등급 전망 (Outlook) ──


def creditOutlook(scoreHistory: list[float]) -> str:
    """5개년 종합점수 추세 → 안정적/긍정적/부정적.

    scoreHistory: 최신→과거 순서 점수 리스트.
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
    metricScores: list[tuple[str, float | None]],
) -> float | None:
    """축 내 개별 지표 점수들의 평균 → 축 점수.

    metricScores: [(지표명, 점수|None), ...]
    None인 지표는 제외.
    """
    valid = [s for _, s in metricScores if s is not None]
    if not valid:
        return None
    return round(sum(valid) / len(valid), 2)
