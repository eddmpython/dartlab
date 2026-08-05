"""진행 표시는 공식 설치형 runtime 이벤트를 TraceEvent로 투영한다."""

from __future__ import annotations

import importlib.util

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
    def stream(self, question: str, **kwargs):
        from dartlab.ai.runtime.eventProjection import EventProjector

        assert question == "너 뭐 할 수 있니"
        projector = EventProjector("codex", "session-test")
        turn_id = "turn-test"
        yield projector.event("sessionStarted", turnId=turn_id)
        yield projector.event("turnStarted", turnId=turn_id)
        yield projector.event(
            "toolStarted",
            turnId=turn_id,
            payload={"canonicalName": "ReadSkill", "toolCallId": "call-1"},
        )
        yield projector.event(
            "toolCompleted",
            turnId=turn_id,
            payload={"canonicalName": "ReadSkill", "toolCallId": "call-1", "refDetails": []},
        )
        yield projector.event("messageDelta", turnId=turn_id, payload={"text": "기업 분석을 지원합니다."})
        yield projector.event(
            "turnCompleted",
            turnId=turn_id,
            payload={
                "status": "completed",
                "outcomeId": "outcome-test",
                "runtimeCoverage": {"readSkillCalls": 1},
            },
        )


def test_runtime_emits_ordered_public_progress_events(monkeypatch: pytest.MonkeyPatch):
    from dartlab.ai.kernel import _askEvents

    fake_engine = _FakeRuntimeEngine()
    monkeypatch.setattr("dartlab.ai.runtime.getRuntimeEngine", lambda: fake_engine)
    monkeypatch.setattr("dartlab.ai.agent._runtimeAnswerQuality", lambda *args, **kwargs: _PassingQuality())

    events = list(_askEvents("너 뭐 할 수 있니"))
    kinds = [event.kind for event in events]

    # delta 는 모델이 써 내려가는 과정의 실시간 중계다(2026-08-04 추가). 예전에는
    # 본문을 모으기만 해서 사용자가 수 분간 빈 화면을 봤다.
    assert kinds == [
        "runtime_session",
        "runtime_turn",
        "tool_start",
        "tool_result",
        "delta",
        "verify",
        "chunk",
        "done",
    ]
    assert "graph_node" not in kinds


def test_progress_events_use_official_runtime_contract():
    from dartlab.ai.runtime.contracts import PUBLIC_AGENT_EVENT_KINDS

    assert importlib.util.find_spec("dartlab.ai.runtime") is not None
    assert "STATE_DELTA" in PUBLIC_AGENT_EVENT_KINDS
    assert "RUN_FINISHED" in PUBLIC_AGENT_EVENT_KINDS
