"""grading 모듈 소형 헬퍼 — 점수→등급 매핑·YoY·변동성 계산.

analysis/financial/insight/grading.py 가 1427 줄 god module 이라 헬퍼 분리.
identity 보존을 위해 grading.py 가 본 모듈에서 re-export 한다.

함수:
- _scoreToGrade — 점수(획득)/만점 → A~F
- _getGrowthYoY — 시계열 최근 2 유효값 YoY %
- _getVolatility — 최근 4 분기 최대 QoQ 변동률
- _predictabilityGrade — 예측가능성 점수 0~10 → 등급
- _uncertaintyGrade — 불확실성 라벨 → 등급
"""

from __future__ import annotations


def _scoreToGrade(score: int, maxScore: int) -> str:
    """점수를 A~F 등급으로 변환.

    Parameters
    ----------
    score : int
        획득 점수.
    maxScore : int
        만점 기준.

    Returns
    -------
    str
        grade : str — 'A' (>=80%) | 'B' (>=50%) | 'C' (>=20%) | 'D' (>=0%) | 'F'
    """
    ratio = score / maxScore if maxScore > 0 else 0
    if ratio >= 0.8:
        return "A"
    if ratio >= 0.5:
        return "B"
    if ratio >= 0.2:
        return "C"
    if ratio >= 0:
        return "D"
    return "F"


def _getGrowthYoY(annualVals: list[float | None]) -> float | None:
    """최근 2개 유효값의 YoY 성장률 계산."""
    from dartlab.analysis.financial.ratios import yoyPct

    valid = [(i, v) for i, v in enumerate(annualVals) if v is not None]
    if len(valid) < 2:
        return None
    _, prev = valid[-2]
    _, curr = valid[-1]
    return yoyPct(curr, prev)


def _getVolatility(qVals: list[float | None]) -> float | None:
    """최근 4분기 최대 변동률 계산."""
    recent = [v for v in qVals[-4:] if v is not None]
    if len(recent) < 2:
        return None
    changes = []
    for i in range(len(recent) - 1):
        if recent[i] != 0:
            changes.append(abs((recent[i + 1] - recent[i]) / recent[i]) * 100)
    return max(changes) if changes else None


def _predictabilityGrade(score: float) -> str:
    """예측가능성 점수 → 등급. 0~10 점수 → A~F."""
    if score >= 8:
        return "A"
    if score >= 6:
        return "B"
    if score >= 4:
        return "C"
    if score >= 2:
        return "D"
    return "F"


def _uncertaintyGrade(rating: str) -> str:
    """불확실성 등급 → insight 등급 (낮은 불확실성 = 좋은 등급)."""
    return {"Low": "A", "Medium": "B", "High": "C", "Very High": "D", "Extreme": "F"}.get(rating, "C")


__all__ = [
    "_getGrowthYoY",
    "_getVolatility",
    "_predictabilityGrade",
    "_scoreToGrade",
    "_uncertaintyGrade",
]
