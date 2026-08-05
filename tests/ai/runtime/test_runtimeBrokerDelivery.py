"""중개 세션의 답변 전달 계약.

DartLab 은 설치형 agent 를 통제하지 않고 중개한다. 품질 계약은 답을 삭제하는
게이트가 아니라 사용자에게 보이는 검증 뱃지다. 실측(2026-08-04 분석 배터리):
게이트 시절 8 질문 중 6 건이 인용 서식 사유로 기각됐고, 기각된 답들도 근거를
8~56 개 실제로 인용한 실분석이었다. 이 파일은 그 회귀를 고정한다.
"""

from __future__ import annotations

import pytest

from dartlab.ai.agent import runRuntimeAgent
from dartlab.ai.runtime.eventProjection import EventProjector

pytestmark = pytest.mark.unit


def _refs() -> list[dict]:
    """정량 근거 3종(table/value/date) 표본."""
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


def _fakeEngine(projector: EventProjector, *, answer: str, refs: list[dict], turns: list[str]):
    """turn 1 회만 도는 런타임 대역. 재호출되면 turns 에 기록돼 repair 재발을 잡는다."""

    class FakeEngine:
        def stream(self, question, **kwargs):
            turns.append(question)
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
            yield projector.event("messageDelta", turnId="turn-1", payload={"text": answer})
            yield projector.event(
                "turnCompleted",
                turnId="turn-1",
                payload={"status": "completed", "outcomeId": "outcome-1"},
            )

        def streamTurn(self, *args, **kwargs):  # pragma: no cover - 호출되면 테스트가 실패한다
            raise AssertionError("중개 모델은 자동 repair 재주입을 하지 않는다")

    return FakeEngine()


def testUnverifiedAnswerIsDeliveredWithBadgeInsteadOfBlocked(monkeypatch):
    """근거 계약 미충족이어도 답변은 사용자에게 전달되고 뱃지로 표시된다."""
    projector = EventProjector("codex", "session-1")
    turns: list[str] = []
    monkeypatch.setattr(
        "dartlab.ai.runtime.getRuntimeEngine",
        lambda: _fakeEngine(projector, answer="매출이 늘었다.", refs=_refs(), turns=turns),
    )

    events = list(runRuntimeAgent("005930 매출 알려줘", runtimeId="codex"))
    done = next(event.data for event in events if event.kind == "done")
    meta = done["responseMeta"]

    assert meta["responseStatus"] == "ok"
    assert meta["verificationStatus"] == "unverified"
    assert meta["verificationNotes"], "미검증 사유가 사용자에게 표시돼야 한다"
    assert meta["evidenceCount"] == len(_refs())
    assert done["refs"], "미검증이어도 근거는 버리지 않는다"
    # 답변 본문이 실제로 전달된다
    assert any(event.kind == "chunk" and event.data.get("text") for event in events)
    assert len(turns) == 1, "자동 repair 턴이 없어야 한다"


def testProcessIsStreamedAsDeltaEvents(monkeypatch):
    """모델이 써 내려가는 과정이 delta 로 실시간 방출된다."""
    projector = EventProjector("codex", "session-2")
    turns: list[str] = []
    monkeypatch.setattr(
        "dartlab.ai.runtime.getRuntimeEngine",
        lambda: _fakeEngine(projector, answer="먼저 재무를 확인한다.", refs=_refs(), turns=turns),
    )

    events = list(runRuntimeAgent("005930 매출 알려줘", runtimeId="codex"))

    deltas = [event for event in events if event.kind == "delta"]
    assert deltas, "과정 중계가 없으면 사용자는 빈 화면을 본다"
    assert "".join(str(event.data.get("text") or "") for event in deltas) == "먼저 재무를 확인한다."


def testRuntimeErrorReasonSurvivesWhenTurnNeverCompletes(monkeypatch):
    """런타임 자체가 실패한 경우는 진짜 실패로 남는다(뱃지 대상 아님)."""
    projector = EventProjector("codex", "session-timeout")

    class FakeEngine:
        def stream(self, question, **kwargs):
            yield projector.event("sessionStarted", turnId="", payload={"nativeSessionId": "native-timeout"})
            yield projector.event("turnStarted", turnId="turn-timeout")
            yield projector.event(
                "runtimeError",
                turnId="turn-timeout",
                payload={"error": "에이전트 턴이 600초 제한을 초과했습니다"},
            )

    monkeypatch.setattr("dartlab.ai.runtime.getRuntimeEngine", lambda: FakeEngine())

    events = list(runRuntimeAgent("005930 투자 판단", runtimeId="codex"))

    done = next(event.data for event in events if event.kind == "done")
    assert done["responseMeta"]["failureReason"] == "에이전트 턴이 600초 제한을 초과했습니다"
    assert done["responseMeta"]["verificationStatus"] == "failed"


def testTimeoutKeepsPartialAnswerInsteadOfDiscardingIt(monkeypatch):
    """턴이 끝나지 않아도 그때까지 쓴 본문과 근거는 전달한다.

    실측 회귀(2026-08-05): 무거운 스크리닝 질문이 10분 상한을 치면 9분간 만든
    분석이 통째로 사라지고 사용자는 빈 오류만 봤다.
    """
    projector = EventProjector("claude", "session-timeout-partial")

    class FakeEngine:
        def stream(self, question, **kwargs):
            yield projector.event("sessionStarted", turnId="", payload={"nativeSessionId": "native-1"})
            yield projector.event("turnStarted", turnId="turn-1")
            yield projector.event(
                "toolCompleted",
                turnId="turn-1",
                payload={"canonicalName": "EngineCall", "refDetails": _refs(), "outcomeId": "outcome-1"},
            )
            yield projector.event("messageDelta", turnId="turn-1", payload={"text": "여기까지 분석했다."})
            yield projector.event(
                "runtimeError",
                turnId="turn-1",
                payload={"error": "에이전트 턴이 600초 제한을 초과했습니다"},
            )

    monkeypatch.setattr("dartlab.ai.runtime.getRuntimeEngine", lambda: FakeEngine())

    events = list(runRuntimeAgent("코스피 스크리닝", runtimeId="claude"))
    done = next(event.data for event in events if event.kind == "done")
    meta = done["responseMeta"]

    assert any(event.kind == "chunk" and "여기까지" in str(event.data.get("text")) for event in events)
    assert meta["responseStatus"] == "ok"
    assert meta["verificationStatus"] == "unverified"
    assert meta["verificationNotes"], "미완이라는 사실을 표시해야 한다"
    assert done["refs"], "모인 근거도 버리지 않는다"


def testRuntimeFailureReasonDoesNotDumpEveryQualityIssue():
    """런타임 실패 사유는 근본 원인 하나다. 결과로 생긴 품질 이슈를 나열하지 않는다.

    실측 회귀(2026-08-05): 세미콜론으로 이어붙인 내부 진단문 8개가 화면에 빨간 벽으로
    나갔다("런타임이 정상 완료되지 않았습니다; 질문에 맞는 Skill OS 계약을 ...").
    """
    from dartlab.ai.agent import _qualityFailureReason

    reason = _qualityFailureReason(
        {
            "issues": [
                "runtime_not_completed",
                "read_skill_missing",
                "empty_answer",
                "source_ref_missing",
                "date_ref_missing",
            ]
        }
    )

    assert ";" not in reason
    assert reason == "런타임이 정상 완료되지 않았습니다"
