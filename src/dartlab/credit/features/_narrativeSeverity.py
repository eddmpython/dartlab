"""신용 축 점수를 심각도 라벨로 바꾸는 임계 SSOT.

축별 서술 생성기(`_narrativeAxes`)와 서술 조립 facade(`narrative`)가 같은 아홉 줄을 각자
갖고 있었다. 임계값이 곧 등급 경계라 한쪽만 옮기면 같은 점수가 축 서술과 종합 서술에서
다른 심각도로 읽힌다.

임계 규약: 점수는 낮을수록 좋다 (위험 점수). 10 미만 strong, 25 미만 adequate, 45 미만
weak, 그 위는 critical. 점수가 없으면 adequate 로 본다. 이 기본값은 "모르면 중립" 이지
"모르면 안전" 이 아니다. 축이 아예 계산되지 않았을 때 서술이 강점으로 과장되는 것을
막으려고 strong 이 아니라 adequate 를 준다.
"""

from __future__ import annotations


def _severity(score: float | None) -> str:
    """축 위험 점수를 strong / adequate / weak / critical 로 좁힌다. 점수 없으면 adequate."""
    if score is None:
        return "adequate"
    if score < 10:
        return "strong"
    if score < 25:
        return "adequate"
    if score < 45:
        return "weak"
    return "critical"
