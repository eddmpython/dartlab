from __future__ import annotations

import pytest

from dartlab.ai.agent import runRuntimeAgent
from dartlab.ai.runtime.eventProjection import EventProjector

pytestmark = pytest.mark.unit


def _refs() -> list[dict]:
    return [
        {
            "id": "table:005930:IS:2025FY",
            "kind": "tableRef",
            "payload": {"stockCode": "005930", "rowCount": 1, "rows": [{"metric": "revenue", "value": 100}]},
        },
        {
            "id": "value:005930:IS:2025FY:revenue",
            "kind": "valueRef",
            "payload": {
                "stockCode": "005930",
                "canonicalMetricId": "revenue",
                "period": "2025FY",
                "value": 100,
            },
        },
        {
            "id": "date:005930:IS:2025FY",
            "kind": "dateRef",
            "payload": {"stockCode": "005930", "period": "2025FY"},
        },
    ]


def testQualityFailureRepairsOnceInSameNativeSession(monkeypatch):
    projector = EventProjector("codex", "session-1")
    refs = _refs()
    repairCalls: list[dict] = []

    class FakeEngine:
        def stream(self, question, **kwargs):
            yield projector.event("sessionStarted", turnId="", payload={"nativeSessionId": "native-1"})
            yield projector.event("turnStarted", turnId="turn-1")
            yield projector.event(
                "toolCompleted",
                turnId="turn-1",
                payload={
                    "canonicalName": "EngineCall",
                    "nativeName": "mcp__dartlab__EngineCall",
                    "toolCallId": "call-1",
                    "refDetails": refs,
                    "outcomeId": "outcome-1",
                },
            )
            yield projector.event(
                "messageDelta",
                turnId="turn-1",
                payload={
                    "text": "2025년 매출은 999원이다. table:005930:IS:2025FY value:005930:IS:2025FY:revenue date:005930:IS:2025FY"
                },
            )
            yield projector.event(
                "turnCompleted",
                turnId="turn-1",
                payload={
                    "status": "completed",
                    "outcomeId": "outcome-1",
                    "runtimeCoverage": {"readSkillCalls": 1},
                },
            )

        def streamTurn(self, sessionId, prompt, **kwargs):
            repairCalls.append({"sessionId": sessionId, "prompt": prompt, **kwargs})
            yield projector.event("turnStarted", turnId="turn-2")
            yield projector.event(
                "messageDelta",
                turnId="turn-2",
                payload={
                    "text": "2025년 매출은 100원이다. table:005930:IS:2025FY value:005930:IS:2025FY:revenue date:005930:IS:2025FY"
                },
            )
            yield projector.event(
                "turnCompleted",
                turnId="turn-2",
                payload={
                    "status": "completed",
                    "outcomeId": "outcome-1",
                    "runtimeCoverage": {"readSkillCalls": 1},
                },
            )

    monkeypatch.setattr("dartlab.ai.runtime.getRuntimeEngine", lambda: FakeEngine())

    events = list(runRuntimeAgent("삼성전자 005930의 2025년 매출은?", runtimeId="codex"))

    assert len(repairCalls) == 1
    assert repairCalls[0]["sessionId"] == "session-1"
    assert repairCalls[0]["outcomeId"] == "outcome-1"
    assert repairCalls[0]["qualityQuestion"] == "삼성전자 005930의 2025년 매출은?"
    assert [event.data["text"] for event in events if event.kind == "chunk"] == [
        "2025년 매출은 100원이다. table:005930:IS:2025FY value:005930:IS:2025FY:revenue date:005930:IS:2025FY"
    ]
    verifyEvents = [event.data for event in events if event.kind == "verify"]
    assert [event["result"]["ok"] for event in verifyEvents] == [False, True]
    assert [event["stage"] for event in verifyEvents] == ["candidate", "final"]
    assert verifyEvents[-1]["result"]["requiredClaimCells"] == 1
    assert verifyEvents[-1]["result"]["coveredClaimCells"] == 1
    done = next(event.data for event in events if event.kind == "done")
    assert done["responseMeta"]["finalEvent"] == "answer"
    assert done["responseMeta"]["repairAttempt"] == 1
    assert done["candidateRefs"] == []
