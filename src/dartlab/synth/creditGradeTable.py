"""신용등급 표준 매핑표 (S&P/Moody's 기준 + KIS 1998-2025 실측).

20단계 신용등급 (AAA~D) 과 1년 부도확률 (PD) 매핑은 도메인-중립 universal 표준이다.
credit (신용 평가), analysis (distress 분석), bond (채권 평가) 모두 같은 표 사용.

본 모듈은 SSOT - 다른 도메인은 여기서 import. 자체 표 복제 금지.
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


def gradeRank(grade: str) -> int | None:
    """AAA부터 D까지의 20단계 순서를 반환한다. 알 수 없는 등급은 None."""
    return _GRADE_TO_IDX.get(grade)


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
