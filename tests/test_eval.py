"""Eval 프레임워크 단위 테스트."""

import pytest

pytestmark = pytest.mark.unit


def test_load_golden_dataset():
    from dartlab.ai.eval import load_golden_dataset

    data = load_golden_dataset()
    assert isinstance(data, list)
    assert len(data) >= 10
    for item in data:
        assert "id" in item
        assert "stock_code" in item
        assert "question" in item
        assert "expected_topics" in item


def test_score_factual_accuracy():
    from dartlab.ai.eval.scorer import score_factual_accuracy

    # 정확한 수치 포함
    answer = "삼성전자의 매출액은 약 302조원입니다."
    facts = [{"metric": "sales", "value": 302e12}]  # 302조
    score = score_factual_accuracy(answer, facts)
    assert score > 0.0

    # 수치 없음
    score_empty = score_factual_accuracy("좋은 회사입니다.", [])
    assert score_empty == 1.0


def test_score_completeness():
    from dartlab.ai.eval.scorer import score_completeness

    answer = "삼성전자의 매출과 영업이익은 성장 추세입니다."
    topics = ["매출", "영업이익", "순이익"]
    score = score_completeness(answer, topics)
    assert score == pytest.approx(2 / 3)


def test_score_source_citation():
    from dartlab.ai.eval.scorer import score_source_citation

    answer = "2023년 IS 기준으로 매출 302조, 2024년 BS에서 자산 총계는..."
    score = score_source_citation(answer)
    assert score > 0.5

    score_no_cite = score_source_citation("좋은 회사입니다.")
    assert score_no_cite == 0.0


def test_score_actionability():
    from dartlab.ai.eval.scorer import score_actionability

    answer = "종합적으로 판단하면, 이 기업의 수익성은 양호하며 건전성도 안정적입니다."
    score = score_actionability(answer)
    assert score > 0.5

    score_flat = score_actionability("데이터는 위와 같습니다.")
    assert score_flat == 0.0


def test_auto_score():
    from dartlab.ai.eval import auto_score

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


def test_load_persona_question_set():
    from dartlab.ai.eval import loadPersonaCases, loadPersonaQuestionSet

    dataset = loadPersonaQuestionSet()
    assert dataset["version"]
    assert dataset["source"] == "curated_persona_regression"

    cases = loadPersonaCases()
    assert len(cases) >= 12
    personas = {case.persona for case in cases}
    assert {
        "assistant",
        "data_manager",
        "operator",
        "installer",
        "research_gather",
        "accountant",
        "business_owner",
        "investor",
        "analyst",
    }.issubset(personas)


def test_auto_score_extended_dimensions():
    from dartlab.ai.eval import auto_score

    answer = "배당과 현금흐름을 함께 보면 추가 확인이 필요합니다. 다음으로 투자자가 확인할 질문도 던질 수 있습니다."
    card = auto_score(
        answer,
        expected_topics=["배당", "현금흐름"],
        included_modules=["dividend", "CF"],
        expected_modules=["dividend", "IS", "CF"],
        must_not_say=["데이터가 없습니다"],
        must_include=["배당", "현금흐름"],
        forbidden_terms=["costByNature", "module_"],
        clarification_allowed=False,
        expected_followups=["추가", "질문"],
        expected_route="hybrid",
        actual_route="hybrid",
    )

    assert card.module_utilization == pytest.approx(2 / 3)
    assert card.false_unavailable == 1.0
    assert card.grounding_quality == 1.0
    assert card.ui_language_compliance == 1.0
    assert "retrieval_failure" in card.failure_types


def test_evaluate_replay_uses_structural_and_answer_checks():
    from dartlab.ai.eval import PersonaEvalCase, evaluateReplay
    from dartlab.ai.runtime.events import AnalysisEvent

    case = PersonaEvalCase(
        id="investor.dividend",
        persona="investor",
        personaLabel="투자자",
        stockCode="005930",
        question="배당 지속 가능성",
        userIntent="dividend_sustainability",
        expectedRoute="hybrid",
        expectedModules=["dividend", "IS", "CF"],
        mustNotSay=["데이터가 없습니다"],
        mustInclude=["배당", "현금흐름"],
        expectedUserFacingTerms=["배당", "현금흐름"],
        expectedFollowups=["추가", "확인"],
    )
    events = [
        AnalysisEvent("meta", {"company": "삼성전자", "includedModules": ["dividend", "CF"]}),
        AnalysisEvent("context", {"module": "report_dividend", "label": "배당 데이터", "text": "..."}),
        AnalysisEvent("chunk", {"text": "배당과 현금흐름을 같이 보면 추가 확인이 필요합니다."}),
        AnalysisEvent("done", {"route": "hybrid", "includedModules": ["dividend", "CF"]}),
    ]

    result = evaluateReplay(case, events, provider="oauth-codex")

    assert result.answer.startswith("배당과 현금흐름")
    assert result.structural.routeMatch == 1.0
    assert result.structural.moduleUtilization == pytest.approx(2 / 3)
    assert result.score.false_unavailable == 1.0
    assert "retrieval_failure" in result.score.failure_types


def test_append_and_load_review_log(tmp_path, monkeypatch):
    import dartlab.ai.eval.replayRunner as replayRunner
    from dartlab.ai.eval import (
        PersonaEvalCase,
        ReplayResult,
        ScoreCard,
        StructuralEval,
        appendReviewEntry,
        loadReviewLog,
    )

    monkeypatch.setattr(replayRunner, "_REVIEW_LOG_DIR", tmp_path / "reviewLog")

    result = ReplayResult(
        case=PersonaEvalCase(
            id="case-1",
            persona="investor",
            personaLabel="투자자",
            question="배당은?",
            userIntent="dividend",
        ),
        answer="배당 데이터를 기준으로 보면 추가 확인이 필요합니다.",
        provider="oauth-codex",
        score=ScoreCard(failure_types=["retrieval_failure"]),
        structural=StructuralEval(failureTypes=["retrieval_failure"]),
    )
    entry = appendReviewEntry(
        result,
        effectiveness="partial",
        improvementActions=["배당 질문은 DPS와 현금흐름 커버를 먼저 요약"],
        notes="초기 응답은 결론이 약함",
        reviewedAt="2026-03-23T12:00:00",
    )

    loaded = loadReviewLog(persona="investor", caseId="case-1")
    assert entry.effectiveness == "partial"
    assert loaded[0].reviewedAt == "2026-03-23T12:00:00"
    assert loaded[0].improvementActions == ["배당 질문은 DPS와 현금흐름 커버를 먼저 요약"]
    assert (tmp_path / "reviewLog" / "investor.jsonl").exists()


def test_validate_structured():
    from dartlab.ai.runtime.validation import validate_structured

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
