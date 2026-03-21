"""6차원 답변 채점기.

차원:
    1. factual_accuracy — 수치 정확도 (실제 finance 값 대비)
    2. completeness — 기대 항목 포함률
    3. source_citation — 출처(테이블명, 연도) 인용 비율
    4. hallucination — 허위 수치 포함 여부
    5. actionability — 결론/판단/제안 포함 여부
    6. ratio_utilization — 제공된 복합 지표(DuPont, Piotroski F, Altman Z 등) 활용도
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class ScoreCard:
    """6차원 채점 결과."""

    factual_accuracy: float = 0.0  # 0~1
    completeness: float = 0.0  # 0~1
    source_citation: float = 0.0  # 0~1
    hallucination: float = 1.0  # 1=없음, 0=있음
    actionability: float = 0.0  # 0~1
    ratio_utilization: float = 0.0  # 0~1
    details: dict = field(default_factory=dict)

    @property
    def overall(self) -> float:
        """6차원 가중 평균 (5.5 만점)."""
        return (
            self.factual_accuracy * 1.5
            + self.completeness * 1.0
            + self.source_citation * 0.5
            + self.hallucination * 1.0
            + self.actionability * 1.0
            + self.ratio_utilization * 0.5
        )


def score_factual_accuracy(answer: str, expected_facts: list[dict]) -> float:
    """답변 내 수치가 기대값과 일치하는 비율.

    Args:
            expected_facts: [{"metric": "sales", "value": 1234567, "unit": "millions"}]
    """
    numeric_facts = [f for f in expected_facts if isinstance(f.get("value"), (int, float))]
    if not numeric_facts:
        return 1.0

    matched = 0
    for fact in numeric_facts:
        val = fact["value"]
        # 답변에서 수치 추출 후 15% 이내 매칭
        numbers = re.findall(r"[\d,]+(?:\.\d+)?", answer)
        for num_str in numbers:
            try:
                parsed = float(num_str.replace(",", ""))
            except ValueError:
                continue
            if val != 0 and abs(parsed - val) / abs(val) < 0.15:
                matched += 1
                break
            # 단위 변환 (조/억)
            for divisor in [1e12, 1e8, 1e6, 1e4]:
                converted = val / divisor
                if converted != 0 and abs(parsed - converted) / abs(converted) < 0.15:
                    matched += 1
                    break

    return matched / len(numeric_facts)


def score_completeness(answer: str, expected_topics: list[str]) -> float:
    """기대 항목이 답변에 포함된 비율."""
    if not expected_topics:
        return 1.0
    found = sum(1 for t in expected_topics if t.lower() in answer.lower())
    return found / len(expected_topics)


def score_source_citation(answer: str) -> float:
    """출처 인용 비율 (연도, 테이블명 등)."""
    year_pattern = r"20[12]\d년"
    source_pattern = r"(?:BS|IS|CF|손익|재무|대차|현금)"
    year_count = len(re.findall(year_pattern, answer))
    source_count = len(re.findall(source_pattern, answer))
    # 최소 1개 연도 + 1개 출처면 1.0
    year_score = min(year_count / 2, 1.0)
    source_score = min(source_count / 1, 1.0)
    return (year_score + source_score) / 2


def score_hallucination(answer: str, known_facts: list[dict]) -> float:
    """허위 수치 비율. 1.0=허위 없음."""
    numeric_facts = [f for f in known_facts if isinstance(f.get("value"), (int, float))]
    if not numeric_facts:
        return 1.0

    # 답변에서 추출한 수치 중 알려진 사실과 50% 이상 차이나면 허위
    numbers = re.findall(r"[\d,]+(?:\.\d+)?", answer)
    hallucination_count = 0
    checked = 0
    for num_str in numbers:
        try:
            parsed = float(num_str.replace(",", ""))
        except ValueError:
            continue
        if parsed < 10:  # 너무 작은 수치는 무시 (비율 등)
            continue
        checked += 1
        # 알려진 사실과 비교
        is_known = False
        for fact in numeric_facts:
            val = fact["value"]
            for divisor in [1, 1e12, 1e8, 1e6, 1e4]:
                converted = val / divisor
                if converted != 0 and abs(parsed - converted) / abs(converted) < 0.5:
                    is_known = True
                    break
            if is_known:
                break
        if not is_known and checked <= 10:  # 처음 10개만 검사
            hallucination_count += 1

    if checked == 0:
        return 1.0
    return max(0.0, 1.0 - hallucination_count / checked)


def score_actionability(answer: str) -> float:
    """결론/판단/제안이 포함되어 있는지."""
    action_keywords = [
        "결론",
        "판단",
        "종합",
        "평가",
        "의견",
        "긍정",
        "부정",
        "양호",
        "우려",
        "주의",
        "개선",
        "악화",
        "안정",
        "위험",
        "추천",
        "제안",
        "고려",
    ]
    found = sum(1 for kw in action_keywords if kw in answer)
    return min(found / 3, 1.0)


_COMPOSITE_INDICATORS = [
    "DuPont",
    "듀퐁",
    "Piotroski",
    "피오트로스키",
    "F-Score",
    "Altman",
    "Z-Score",
    "ROIC",
    "CCC",
    "현금전환주기",
    "이익의 질",
    "영업CF/순이익",
]


def score_ratio_utilization(answer: str, provided_indicators: list[str] | None = None) -> float:
    """제공된 복합 지표가 답변에서 실제 활용되었는지 측정.

    Args:
        provided_indicators: context에 제공된 복합 지표 이름 리스트.
            None이면 _COMPOSITE_INDICATORS 전체에서 탐색.
    """
    indicators = provided_indicators or _COMPOSITE_INDICATORS
    if not indicators:
        return 1.0

    found = sum(1 for ind in indicators if ind.lower() in answer.lower())
    # 제공된 지표 중 최소 30%를 활용했으면 만점
    return min(found / max(len(indicators) * 0.3, 1), 1.0)


def auto_score(
    answer: str,
    expected_facts: list[dict] | None = None,
    expected_topics: list[str] | None = None,
    provided_indicators: list[str] | None = None,
) -> ScoreCard:
    """답변 자동 채점."""
    facts = expected_facts or []
    topics = expected_topics or []

    return ScoreCard(
        factual_accuracy=score_factual_accuracy(answer, facts),
        completeness=score_completeness(answer, topics),
        source_citation=score_source_citation(answer),
        hallucination=score_hallucination(answer, facts),
        actionability=score_actionability(answer),
        ratio_utilization=score_ratio_utilization(answer, provided_indicators),
    )
