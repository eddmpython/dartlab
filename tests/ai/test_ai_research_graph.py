from __future__ import annotations

import polars as pl
import pytest

pytestmark = pytest.mark.unit


class _PassingQuality:
    passed = True
    issues: tuple[str, ...] = ()
    score = 100
    requiredClaimCells = 0
    coveredClaimCells = 0

    def toDict(self) -> dict[str, object]:
        return {
            "passed": self.passed,
            "issues": list(self.issues),
            "score": self.score,
            "requiredClaimCells": self.requiredClaimCells,
            "coveredClaimCells": self.coveredClaimCells,
        }


class _FakeRuntimeEngine:
    def __init__(self, answer: str, refs: list[dict] | None = None):
        self.answer = answer
        self.refs = refs or []
        self.calls: list[dict] = []

    def stream(self, question: str, **kwargs):
        from dartlab.ai.runtime.eventProjection import EventProjector

        self.calls.append({"question": question, **kwargs})
        projector = EventProjector("codex", "session-research")
        turn_id = "turn-research"
        yield projector.event("sessionStarted", turnId=turn_id)
        yield projector.event("turnStarted", turnId=turn_id)
        if self.refs:
            yield projector.event(
                "toolStarted",
                turnId=turn_id,
                payload={"canonicalName": "EngineCall", "toolCallId": "call-research"},
            )
            yield projector.event(
                "toolCompleted",
                turnId=turn_id,
                payload={
                    "canonicalName": "EngineCall",
                    "toolCallId": "call-research",
                    "refDetails": self.refs,
                },
            )
        yield projector.event("messageDelta", turnId=turn_id, payload={"text": self.answer})
        yield projector.event(
            "turnCompleted",
            turnId=turn_id,
            payload={
                "status": "completed",
                "outcomeId": "outcome-research",
                "runtimeCoverage": {"readSkillCalls": 1},
            },
        )


def _installRuntime(monkeypatch: pytest.MonkeyPatch, answer: str, refs: list[dict] | None = None):
    engine = _FakeRuntimeEngine(answer, refs)
    monkeypatch.setattr("dartlab.ai.runtime.getRuntimeEngine", lambda: engine)
    monkeypatch.setattr("dartlab.ai.agent._runtimeAnswerQuality", lambda *args, **kwargs: _PassingQuality())
    return engine


class _FakeCompany:
    stockCode = "005930"
    corpName = "삼성전자"

    def panel(self, statement: str):
        assert statement == "BS"
        return pl.DataFrame(
            {
                "snakeId": [
                    "cash_and_cash_equivalents",
                    "current_assets",
                    "total_assets",
                    "total_liabilities",
                    "owners_of_parent_equity",
                ],
                "항목": ["현금및현금성자산", "유동자산", "자산총계", "부채총계", "지배주주지분"],
                "2025Q4": [
                    57_856_000_000_000,
                    247_680_000_000_000,
                    566_900_000_000_000,
                    130_600_000_000_000,
                    424_300_000_000_000,
                ],
            }
        )


class _FakePeerCompany:
    stockCode = "000660"
    corpName = "SK하이닉스"

    def panel(self, statement: str):
        assert statement == "BS"
        return pl.DataFrame(
            {
                "snakeId": [
                    "cash_and_cash_equivalents",
                    "current_assets",
                    "total_assets",
                    "total_liabilities",
                    "owners_of_parent_equity",
                ],
                "항목": ["현금및현금성자산", "유동자산", "자산총계", "부채총계", "지배주주지분"],
                "2025Q4": [
                    10_000_000_000_000,
                    70_000_000_000_000,
                    176_000_000_000_000,
                    55_000_000_000_000,
                    120_000_000_000_000,
                ],
            }
        )


def _answer(events) -> str:
    return "".join(str(event.data.get("text") or "") for event in events if event.kind == "chunk")


def _done(events) -> dict:
    return [event for event in events if event.kind == "done"][-1].data


@pytest.mark.skip(
    reason=(
        "intent.py keyword routing 폐기 (SSOT P-revised, 2026-05-07): kernel 은 "
        "mode==analyze 또는 LLM tool 호출만 분기. 'unknown_api_ref' 결과는 "
        "verifyAnswer 가 financialStatement apiRef 를 capability catalog 에서 "
        "찾지 못함. RunPython 패턴 + mock provider 로 재작성 필요 (별도 PR)."
    )
)
def test_ask_public_entry_financial_statement_uses_engine_call(monkeypatch) -> None:
    import dartlab.ai.tools.engineCall as engine_call_mod
    from dartlab.ai.kernel import ask

    monkeypatch.setattr(engine_call_mod, "_resolveCompany", lambda target: _FakeCompany())

    events = list(ask("삼성전자 재무상태표 확인", events=True))
    answer = _answer(events)
    done = _done(events)

    assert "삼성전자(005930)" in answer
    assert "재무상태표 (2025Q4)" in answer
    assert "57.9조원" in answer
    assert "5.7856e13" not in answer
    assert done["responseMeta"]["responseStatus"] == "ok"
    assert any(ref["kind"] == "tableRef" for ref in done["refs"])
    assert any(ref["kind"] == "valueRef" for ref in done["refs"])
    assert any(ref["kind"] == "dateRef" for ref in done["refs"])


def test_ask_public_entry_compares_two_financial_statements(monkeypatch) -> None:
    from dartlab.ai.kernel import ask

    answer_text = "삼성전자(005930)와 SK하이닉스(000660)의 자산총계를 비교하면 약 3.2배입니다."
    refs = [
        {"id": "value:005930:BS:assets", "kind": "valueRef", "title": "삼성전자 자산총계"},
        {"id": "value:000660:BS:assets", "kind": "valueRef", "title": "SK하이닉스 자산총계"},
    ]
    engine = _installRuntime(monkeypatch, answer_text, refs)

    events = list(ask("삼성전자와 SK하이닉스 재무상태표 비교", events=True))
    answer = _answer(events)
    done = _done(events)

    assert "삼성전자(005930)와 SK하이닉스(000660)" in answer
    assert "자산총계" in answer
    assert "약 3.2배" in answer
    assert done["responseMeta"]["responseStatus"] == "ok"
    assert len(done["refs"]) == 2
    assert engine.calls[0]["question"] == "삼성전자와 SK하이닉스 재무상태표 비교"


def test_ask_growth_scan_returns_candidate_table(monkeypatch) -> None:
    from dartlab.ai.kernel import ask

    answer_text = "성장성 스캔 결과입니다.\n\n| 순위 | 기업 |\n|---:|---|\n| 1 | 하나투어(039130) |"
    table_ref = {"id": "table:scan:growth:top", "kind": "tableRef", "title": "growth top"}
    _installRuntime(monkeypatch, answer_text, [table_ref])

    events = list(ask("요즘 성장하는 회사는?", events=True))
    answer = _answer(events)
    done = _done(events)

    assert "성장성 스캔" in answer
    assert "하나투어(039130)" in answer
    assert [ref["id"] for ref in done["refs"]] == ["table:scan:growth:top"]
    assert [event.kind for event in events].count("tool_result") == 1


def test_runask_is_not_public_kernel_entry() -> None:
    import dartlab.ai.kernel as kernel

    assert not hasattr(kernel, "runAsk")


def test_ask_missing_company_returns_actionable_failure(monkeypatch) -> None:
    from dartlab.ai.kernel import ask

    actionable = "종목을 먼저 특정해 주세요. 예: 삼성전자 재무상태표 확인"
    engine = _installRuntime(monkeypatch, actionable)

    answer = ask("재무상태표 확인", stream=False)

    assert "종목을 먼저 특정" in answer
    assert "삼성전자 재무상태표 확인" in answer
    assert engine.calls[0]["context"]["stockCode"] is None
