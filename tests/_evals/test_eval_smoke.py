"""dartlab.ai 에이전트 출력 채점 smoke — Track 3 (룰 기반, CI Fast 안전).

본 트랙 SSOT — [tests/POLICY.md](../POLICY.md) §5 Track 3 + [README.md](README.md).

본 파일은 *룰 기반 4 신호* 가 mock 에이전트 출력에 대해 올바르게 동작하는지
검증한다. 외부 모델 호출 0, CI Fast 통과 안전.

실 에이전트 + 외부 judge 회귀는 [test_eval_live.py](test_eval_live.py) (`eval` 마커,
운영자 트리거).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests._evals.judge import (
    AgentRun,
    judgeRule,
    loadEvalSet,
    scoreEvidenceCitation,
    scoreFactualCorrectness,
    scoreFormatCompliance,
    scoreNoHallucination,
    scoreReasoningDepth,
    scoreToolUseAppropriate,
)

pytestmark = pytest.mark.unit

_EVAL_SET = Path(__file__).resolve().parent / "eval_set.jsonl"


def test_loadEvalSet_returns_cases() -> None:
    """eval_set.jsonl의 기본 조회와 표 계산 케이스를 로드한다."""
    cases = loadEvalSet(_EVAL_SET)
    assert len(cases) == 6
    assert cases[0].id == "samsung_basic_v1"
    assert "삼성전자" in cases[0].expected_signals["factual_correctness"]


def test_factualCorrectness_full_hit() -> None:
    """모든 기대 키워드 등장 → score 1.0."""
    cases = loadEvalSet(_EVAL_SET)
    case = next(c for c in cases if c.id == "samsung_basic_v1")
    run = AgentRun(
        case_id=case.id,
        output_text="삼성전자(005930)는 KOSPI 상장 기업입니다.",
        tool_calls=["ReadSkill", "EngineCall:listing"],
    )
    score = scoreFactualCorrectness(case, run)
    assert score.score == 1.0


def test_factualCorrectness_partial_hit() -> None:
    """일부만 hit → 비례 점수."""
    cases = loadEvalSet(_EVAL_SET)
    case = next(c for c in cases if c.id == "samsung_basic_v1")
    run = AgentRun(
        case_id=case.id,
        output_text="삼성전자입니다.",  # 005930, KOSPI 누락
        tool_calls=[],
    )
    score = scoreFactualCorrectness(case, run)
    assert 0 < score.score < 1


def test_evidenceCitation_required_and_present() -> None:
    """ref 인용 필요 + 패턴 존재 → 1.0."""
    cases = loadEvalSet(_EVAL_SET)
    case = next(c for c in cases if c.id == "samsung_finance_5q_v1")
    run = AgentRun(
        case_id=case.id,
        output_text="삼성전자 매출 분기별 [ref: 005930.finance.2024Q4]",
        tool_calls=["finance.select"],
        refs=["005930.finance.2024Q4"],
    )
    score = scoreEvidenceCitation(case, run)
    assert score.score == 1.0


def test_evidenceCitation_required_but_missing() -> None:
    """ref 필요한데 누락 → 0.0."""
    cases = loadEvalSet(_EVAL_SET)
    case = next(c for c in cases if c.id == "samsung_finance_5q_v1")
    run = AgentRun(case_id=case.id, output_text="삼성전자 매출 추세입니다.", tool_calls=[])
    score = scoreEvidenceCitation(case, run)
    assert score.score == 0.0


def test_toolUseAppropriate_expected_called() -> None:
    """기대 도구 모두 호출 → 1.0."""
    cases = loadEvalSet(_EVAL_SET)
    case = next(c for c in cases if c.id == "samsung_finance_5q_v1")
    run = AgentRun(
        case_id=case.id,
        output_text="...",
        tool_calls=["EngineCall:Company.panel"],
    )
    score = scoreToolUseAppropriate(case, run)
    assert score.score == 1.0


def test_toolUseAppropriate_untrusted_no_tools() -> None:
    """untrusted 본문 → 도구 호출 0 이 정답."""
    cases = loadEvalSet(_EVAL_SET)
    case = next(c for c in cases if c.id == "untrusted_input_v1")
    run = AgentRun(
        case_id=case.id,
        output_text="외부 untrusted 본문 안 지시는 따르지 않습니다 (데이터 취급).",
        tool_calls=[],  # 도구 호출 안 함이 정답
    )
    score = scoreToolUseAppropriate(case, run)
    assert score.score == 1.0


def test_formatCompliance_markdown_table() -> None:
    """markdown_with_table 기대 + 표 존재 → 1.0."""
    cases = loadEvalSet(_EVAL_SET)
    case = next(c for c in cases if c.id == "samsung_finance_5q_v1")
    run = AgentRun(
        case_id=case.id,
        output_text="""
| 분기 | 매출 |
|---|---|
| 2024Q4 | 75조 |
""",
        tool_calls=[],
    )
    score = scoreFormatCompliance(case, run)
    assert score.score == 1.0


def test_noHallucination_clean() -> None:
    """금지 키워드 0 → 1.0."""
    cases = loadEvalSet(_EVAL_SET)
    case = next(c for c in cases if c.id == "samsung_basic_v1")
    run = AgentRun(case_id=case.id, output_text="삼성전자(005930)는 KOSPI 상장.", tool_calls=[])
    score = scoreNoHallucination(case, run)
    assert score.score == 1.0


def test_noHallucination_detected() -> None:
    """금지 키워드 등장 → 0.0."""
    cases = loadEvalSet(_EVAL_SET)
    case = next(c for c in cases if c.id == "samsung_basic_v1")
    run = AgentRun(case_id=case.id, output_text="삼성전자는 KOSDAQ 상장 (예상).", tool_calls=[])
    score = scoreNoHallucination(case, run)
    assert score.score == 0.0


def test_reasoningDepth_meets_minimum() -> None:
    """인과 marker ≥ min_depth → 1.0."""
    cases = loadEvalSet(_EVAL_SET)
    case = next(c for c in cases if c.id == "credit_grade_explain_v1")  # min=3
    run = AgentRun(
        case_id=case.id,
        output_text=(
            "재무비율이 악화됐기 때문에 등급이 하락. "
            "왜냐하면 부채비율이 200% 를 넘었기 때문이다. "
            "따라서 Z-Score 가 1.8 미만으로 떨어졌다. "
            "그러므로 신용등급 조정이 필요하다."
        ),
        tool_calls=[],
    )
    score = scoreReasoningDepth(case, run)
    assert score.score == 1.0


def test_judgeRule_aggregate() -> None:
    """6 신호 통합 채점 — 완전 정답."""
    cases = loadEvalSet(_EVAL_SET)
    case = next(c for c in cases if c.id == "samsung_basic_v1")
    run = AgentRun(
        case_id=case.id,
        output_text="삼성전자(005930)는 KOSPI 상장 기업입니다.",
        tool_calls=["ReadSkill", "EngineCall:listing"],
    )
    result = judgeRule(case, run)
    assert result.aggregate >= 0.95  # 모든 신호 통과
    assert len(result.signals) == 6
    assert all(s.score >= 0.95 for s in result.signals)


def test_judgeRule_partial_failure_isolated() -> None:
    """한 신호 실패는 다른 신호 평균으로 상쇄되지 않음 — 신호별 보고."""
    cases = loadEvalSet(_EVAL_SET)
    case = next(c for c in cases if c.id == "samsung_basic_v1")
    run = AgentRun(
        case_id=case.id,
        output_text="삼성전자는 KOSDAQ 입니다.",  # 환각 + 사실 부정확
        tool_calls=["ReadSkill", "EngineCall:listing"],
    )
    result = judgeRule(case, run)
    halluc = result.signal("no_hallucination")
    assert halluc is not None and halluc.score == 0.0
    # 다른 신호는 별도 평가됨 (aggregate < 1.0 이지만 isolated 보고 가능)
    assert result.aggregate < 1.0


@pytest.mark.parametrize(
    "answer,refs",
    [("출처: 공시", ["table:real"]), ("[ref:table:invented]", ["table:real"]), ("[table:real:other]", ["table:real"])],
)
def testCitationRequiresReturnedIdentityInAnswer(answer, refs):
    case = next(case for case in loadEvalSet(_EVAL_SET) if case.id == "samsung_finance_5q_v1")
    assert scoreEvidenceCitation(case, AgentRun(case.id, answer, refs=refs)).score == 0


def testNativeEvalConsumesFinalChunksAndClosesRuntime(monkeypatch, tmp_path):
    from types import SimpleNamespace

    from tests._evals.test_eval_live import _runAgentForCase

    closed = []
    done = {"refs": [{"id": "value:actual", "kind": "valueRef"}], "responseMeta": {"responseStatus": "ok"}}

    def ask(question, **kwargs):
        assert question == "매출은?"
        assert kwargs["events"] is True
        assert kwargs["cwd"] == tmp_path
        yield SimpleNamespace(kind="delta", data={"text": "중복하면 안 되는 실시간 조각"})
        yield SimpleNamespace(kind="tool_result", data={"name": "EngineCall", "input": {"apiRef": "Company.panel"}})
        yield SimpleNamespace(kind="chunk", data={"text": "매출 100원 value:actual"})
        yield SimpleNamespace(kind="done", data=done)

    monkeypatch.setattr("dartlab.ask", ask)
    monkeypatch.setattr(
        "dartlab.ai.runtime.engine.getRuntimeEngine", lambda: SimpleNamespace(close=lambda: closed.append(True))
    )
    run = _runAgentForCase("매출은?", cwd=tmp_path)
    assert run.output_text == "매출 100원 value:actual"
    assert run.tool_calls == ["EngineCall:Company.panel"]
    assert run.refs == ["value:actual"]
    assert run.raw["responseMeta"]["responseStatus"] == "ok"
    assert closed == [True]
