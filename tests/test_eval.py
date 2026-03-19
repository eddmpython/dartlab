"""Eval 프레임워크 단위 테스트."""

import pytest


def test_load_golden_dataset():
    from dartlab.engines.ai.eval import load_golden_dataset

    data = load_golden_dataset()
    assert isinstance(data, list)
    assert len(data) >= 10
    for item in data:
        assert "id" in item
        assert "stock_code" in item
        assert "question" in item
        assert "expected_topics" in item


def test_score_factual_accuracy():
    from dartlab.engines.ai.eval.scorer import score_factual_accuracy

    # 정확한 수치 포함
    answer = "삼성전자의 매출액은 약 302조원입니다."
    facts = [{"metric": "sales", "value": 302e12}]  # 302조
    score = score_factual_accuracy(answer, facts)
    assert score > 0.0

    # 수치 없음
    score_empty = score_factual_accuracy("좋은 회사입니다.", [])
    assert score_empty == 1.0


def test_score_completeness():
    from dartlab.engines.ai.eval.scorer import score_completeness

    answer = "삼성전자의 매출과 영업이익은 성장 추세입니다."
    topics = ["매출", "영업이익", "순이익"]
    score = score_completeness(answer, topics)
    assert score == pytest.approx(2 / 3)


def test_score_source_citation():
    from dartlab.engines.ai.eval.scorer import score_source_citation

    answer = "2023년 IS 기준으로 매출 302조, 2024년 BS에서 자산 총계는..."
    score = score_source_citation(answer)
    assert score > 0.5

    score_no_cite = score_source_citation("좋은 회사입니다.")
    assert score_no_cite == 0.0


def test_score_actionability():
    from dartlab.engines.ai.eval.scorer import score_actionability

    answer = "종합적으로 판단하면, 이 기업의 수익성은 양호하며 건전성도 안정적입니다."
    score = score_actionability(answer)
    assert score > 0.5

    score_flat = score_actionability("데이터는 위와 같습니다.")
    assert score_flat == 0.0


def test_auto_score():
    from dartlab.engines.ai.eval import auto_score

    answer = (
        "2024년 기준 삼성전자의 매출은 약 302조원이며, 영업이익률은 양호합니다. 종합 판단으로 건전성은 안정적입니다."
    )
    card = auto_score(
        answer,
        expected_topics=["매출", "영업이익률", "건전성"],
    )
    assert card.completeness == 1.0
    assert card.actionability > 0.0
    assert card.overall > 0.0


def test_validate_structured():
    from dartlab.engines.ai.validation import validate_structured

    structured = {
        "metrics": [
            {"name": "sales", "value": 302000000},
            {"name": "roe", "value": 15.2},
        ],
    }
    expected = [
        {"metric": "sales", "value": 302000000},
        {"metric": "roe", "value": 15.2},
        {"metric": "debt_ratio", "value": 30.5},  # 없음
    ]
    result = validate_structured(structured, expected)
    assert result["matched"] == 2
    assert result["numeric_facts"] == 3
    assert result["coverage"] == pytest.approx(66.7)
