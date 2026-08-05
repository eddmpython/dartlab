from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

import dartlab.ai.runtime.engine as runtimeEngineModule
import dartlab.productOutcome as outcomeService
from dartlab.ai.runtime.contracts import AgentEvent, RuntimeDescriptor, RuntimeProbe
from dartlab.ai.runtime.drivers.base import DriverHandle
from dartlab.ai.runtime.engine import AgentRuntimeEngine
from dartlab.ai.runtime.eventProjection import EventProjector
from dartlab.ai.runtime.sessionManager import SessionManager
from dartlab.ai.runtime.sessionStore import SessionStore
from dartlab.productOutcome import OutcomeStore


class FakeDriver:
    def open(
        self,
        descriptor: RuntimeDescriptor,
        executable: str,
        sessionId: str,
        cwd: Path,
        nativeSessionId: str | None = None,
        instructions: str = "",
    ) -> DriverHandle:
        handle = DriverHandle(
            descriptor,
            executable,
            sessionId,
            nativeSessionId or "native-1",
            cwd,
            EventProjector(descriptor.runtimeId, sessionId),
        )
        handle.metadata["instructions"] = instructions
        return handle

    def streamTurn(self, handle: DriverHandle, question: str, *, instructions: str) -> Iterator[AgentEvent]:
        handle.metadata["question"] = question
        turnId = "turn-1"
        yield handle.projector.event("turnStarted", turnId=turnId)
        yield handle.projector.event(
            "toolCompleted",
            turnId=turnId,
            payload={"tool": "ReadSkill", "result": {"ok": True, "skills": [{"id": "engines.company"}]}},
        )
        yield handle.projector.event(
            "toolCompleted",
            turnId=turnId,
            payload={
                "tool": "EngineCall",
                "result": {
                    "ok": True,
                    "refs": [
                        {
                            "id": "table:exact",
                            "kind": "tableRef",
                            "payload": {"rowCount": 1, "rows": [{"metric": "answer", "value": 1}]},
                        },
                        {
                            "id": "value:exact",
                            "kind": "valueRef",
                            "payload": {"metric": "answer", "value": 1},
                        },
                        {"id": "date:exact", "kind": "dateRef", "payload": {"period": "2026Q1"}},
                    ],
                },
            },
        )
        yield handle.projector.event(
            "messageDelta",
            turnId=turnId,
            payload={"text": "2026년 1분기 값은 1이다. table:exact value:exact date:exact"},
        )
        yield handle.projector.event("turnCompleted", turnId=turnId, payload={"status": "completed"})

    def cancel(self, handle: DriverHandle) -> None:
        return None

    def approve(self, handle: DriverHandle, approvalId: str, *, allow: bool) -> None:
        return None

    def close(self, handle: DriverHandle) -> None:
        return None

    def models(self, handle: DriverHandle) -> list[dict[str, Any]]:
        return []


def testRuntimeEngineStreamsAndAdvancesOutcome(tmp_path, monkeypatch):
    descriptor = RuntimeDescriptor(
        "fake",
        "Fake",
        "fake",
        "ndjson",
        ("fake",),
        ("--version",),
        (),
        (),
        "https://example.invalid",
    )
    monkeypatch.setenv("DARTLAB_OUTCOME_DB", str(tmp_path / "outcomes.sqlite3"))
    monkeypatch.setattr(outcomeService, "_DEFAULT_STORE", None)
    monkeypatch.setattr(
        runtimeEngineModule, "probeRuntime", lambda value: RuntimeProbe("fake", "ready", sysExecutable())
    )
    monkeypatch.setattr(
        runtimeEngineModule,
        "probeMcpConnection",
        lambda runtimeId, **_kwargs: {"connected": True, "mode": "test"},
    )
    engine = AgentRuntimeEngine(SessionStore(tmp_path / "sessions.sqlite3"), SessionManager())
    engine.registry = {"fake": descriptor}
    engine.drivers = {"fake": FakeDriver()}

    events = list(engine.stream("질문", runtimeId="fake", cwd=tmp_path))
    assert [event.kind for event in events] == [
        "sessionStarted",
        "turnStarted",
        "toolCompleted",
        "toolCompleted",
        "messageDelta",
        "turnCompleted",
    ]
    outcomeId = str(events[-1].payload["outcomeId"])
    assert events[3].payload["refDetails"] == [
        {
            "id": "table:exact",
            "kind": "tableRef",
            "title": "table:exact",
            "source": "",
            "sourceType": "internal",
            "payload": {"rowCount": 1, "rows": [{"metric": "answer", "value": 1}]},
            "outcomeId": outcomeId,
        },
        {
            "id": "value:exact",
            "kind": "valueRef",
            "title": "value:exact",
            "source": "",
            "sourceType": "internal",
            "payload": {"metric": "answer", "value": 1},
            "outcomeId": outcomeId,
        },
        {
            "id": "date:exact",
            "kind": "dateRef",
            "title": "date:exact",
            "source": "",
            "sourceType": "internal",
            "payload": {"period": "2026Q1"},
            "outcomeId": outcomeId,
        },
    ]
    assert engine.resolveEvidence(outcomeId, "table:exact")["kind"] == "tableRef"
    restarted = AgentRuntimeEngine(SessionStore(tmp_path / "sessions.sqlite3"), SessionManager())
    assert restarted.resolveEvidence(outcomeId, "table:exact")["kind"] == "tableRef"
    store = OutcomeStore(tmp_path / "outcomes.sqlite3")
    assert store.get(outcomeId).state == "delivered"
    assert store.verifyEvidence(outcomeId, "table:exact").state == "verified"


def testRuntimeContextIsBoundedAndTranscriptFree(tmp_path, monkeypatch):
    descriptor = RuntimeDescriptor(
        "fake", "Fake", "fake", "ndjson", ("fake",), ("--version",), (), (), "https://example.invalid"
    )
    monkeypatch.setattr(
        runtimeEngineModule, "probeRuntime", lambda value: RuntimeProbe("fake", "ready", sysExecutable())
    )
    monkeypatch.setattr(
        runtimeEngineModule,
        "probeMcpConnection",
        lambda runtimeId, **_kwargs: {"connected": True, "mode": "test"},
    )
    engine = AgentRuntimeEngine(SessionStore(tmp_path / "sessions.sqlite3"), SessionManager())
    engine.registry = {"fake": descriptor}
    driver = FakeDriver()
    engine.drivers = {"fake": driver}

    list(
        engine.stream(
            "이 회사 매출은?",
            runtimeId="fake",
            cwd=tmp_path,
            context={"stockCode": "005930", "history": [{"content": "TRANSCRIPT_SECRET_8C1A"}]},
        )
    )
    managed = engine.sessionManager.get(engine.sessionStore.list(limit=1)[0].sessionId)
    assert managed is not None
    assert '"stockCode":"005930"' in managed.handle.metadata["question"]
    assert "TRANSCRIPT_SECRET_8C1A" not in managed.handle.metadata["question"]


def testRepairTurnUsesOriginalQuestionForCompletionContract(tmp_path, monkeypatch):
    descriptor = RuntimeDescriptor(
        "fake", "Fake", "fake", "ndjson", ("fake",), ("--version",), (), (), "https://example.invalid"
    )
    monkeypatch.setattr(
        runtimeEngineModule, "probeRuntime", lambda value: RuntimeProbe("fake", "ready", sysExecutable())
    )
    monkeypatch.setattr(
        runtimeEngineModule,
        "probeMcpConnection",
        lambda runtimeId, **_kwargs: {"connected": True, "mode": "test"},
    )
    engine = AgentRuntimeEngine(SessionStore(tmp_path / "sessions.sqlite3"), SessionManager())
    engine.registry = {"fake": descriptor}
    driver = FakeDriver()
    engine.drivers = {"fake": driver}
    session = engine.openSession(runtimeId="fake", cwd=tmp_path)

    list(
        engine.streamTurn(
            session.sessionId,
            "답변 품질을 다시 교정하라",
            qualityQuestion="삼성전자 005930 최근 5년 매출과 영업이익 추이",
        )
    )

    managed = engine.sessionManager.get(session.sessionId)
    assert managed is not None
    nativeQuestion = managed.handle.metadata["question"]
    assert '"period":"recent:5Y"' in nativeQuestion
    assert '"requiredCells":10' in nativeQuestion
    assert nativeQuestion.endswith("[사용자 질문]\n답변 품질을 다시 교정하라")


def testSameSessionRejectsConcurrentTurn(tmp_path, monkeypatch):
    descriptor = RuntimeDescriptor(
        "fake", "Fake", "fake", "ndjson", ("fake",), ("--version",), (), (), "https://example.invalid"
    )
    monkeypatch.setattr(
        runtimeEngineModule, "probeRuntime", lambda value: RuntimeProbe("fake", "ready", sysExecutable())
    )
    monkeypatch.setattr(
        runtimeEngineModule,
        "probeMcpConnection",
        lambda runtimeId, **_kwargs: {"connected": True, "mode": "test"},
    )
    engine = AgentRuntimeEngine(SessionStore(tmp_path / "sessions.sqlite3"), SessionManager())
    engine.registry = {"fake": descriptor}
    engine.drivers = {"fake": FakeDriver()}
    session = engine.openSession(runtimeId="fake", cwd=tmp_path)
    managed = engine.sessionManager.get(session.sessionId)
    assert managed is not None
    assert managed.turnLock.acquire(blocking=False)
    try:
        with pytest.raises(RuntimeError, match="이미 다른 턴"):
            list(engine.streamTurn(session.sessionId, "동시 질문"))
    finally:
        managed.turnLock.release()


def testStoredSessionKeepsItsOriginalWorkspace(tmp_path, monkeypatch):
    descriptor = RuntimeDescriptor(
        "fake",
        "Fake",
        "fake",
        "ndjson",
        ("fake",),
        ("--version",),
        (),
        (),
        "https://example.invalid",
    )
    original = tmp_path / "original"
    changed = tmp_path / "changed"
    original.mkdir()
    changed.mkdir()
    monkeypatch.setattr(
        runtimeEngineModule, "probeRuntime", lambda value: RuntimeProbe("fake", "ready", sysExecutable())
    )
    monkeypatch.setattr(
        runtimeEngineModule,
        "probeMcpConnection",
        lambda runtimeId, **_kwargs: {"connected": True, "mode": "test"},
    )
    engine = AgentRuntimeEngine(SessionStore(tmp_path / "sessions.sqlite3"), SessionManager())
    engine.registry = {"fake": descriptor}
    engine.drivers = {"fake": FakeDriver()}
    session = engine.openSession(runtimeId="fake", cwd=original)
    engine.sessionManager.close(session.sessionId)

    resumed = engine.openSession(sessionId=session.sessionId)
    assert resumed.cwd == str(original.resolve())

    engine.sessionManager.close(session.sessionId)
    with pytest.raises(ValueError, match="작업공간"):
        engine.openSession(sessionId=session.sessionId, cwd=changed)


def testRuntimeSelectionFailsClosedWhenMcpIsDisconnected(tmp_path, monkeypatch):
    descriptor = RuntimeDescriptor(
        "fake",
        "Fake",
        "fake",
        "ndjson",
        ("fake",),
        ("--version",),
        (),
        (),
        "https://example.invalid",
    )
    monkeypatch.setattr(
        runtimeEngineModule, "probeRuntime", lambda value: RuntimeProbe("fake", "ready", sysExecutable())
    )
    monkeypatch.setattr(
        runtimeEngineModule,
        "probeMcpConnection",
        lambda runtimeId, **_kwargs: {"connected": False, "mode": "test"},
    )
    engine = AgentRuntimeEngine(SessionStore(tmp_path / "sessions.sqlite3"), SessionManager())
    engine.registry = {"fake": descriptor}

    with pytest.raises(RuntimeError, match="DartLab MCP가 연결되지 않았습니다"):
        engine.selectRuntime("fake")


def testRuntimeSelectionFailsClosedWithoutEmbeddedGrounding(tmp_path, monkeypatch):
    descriptor = RuntimeDescriptor(
        "fake",
        "Fake",
        "fake",
        "acp-v1",
        ("fake",),
        ("--version",),
        ("--acp",),
        (),
        "https://example.invalid",
        embeddedGrounding=False,
    )
    monkeypatch.setattr(
        runtimeEngineModule, "probeRuntime", lambda value: RuntimeProbe("fake", "ready", sysExecutable())
    )
    monkeypatch.setattr(
        runtimeEngineModule,
        "probeMcpConnection",
        lambda runtimeId, **_kwargs: {"connected": True, "mode": "test"},
    )
    engine = AgentRuntimeEngine(SessionStore(tmp_path / "sessions.sqlite3"), SessionManager())
    engine.registry = {"fake": descriptor}

    with pytest.raises(RuntimeError, match="embedded DartLab MCP"):
        engine.selectRuntime("fake")


def testMultipleReadyRuntimesRequireServerOwnedSelection(tmp_path, monkeypatch):
    descriptors = {
        runtimeId: RuntimeDescriptor(
            runtimeId,
            runtimeId,
            "fake",
            "ndjson",
            (runtimeId,),
            ("--version",),
            (),
            (),
            "https://example.invalid",
        )
        for runtimeId in ("one", "two")
    }
    monkeypatch.setattr(
        runtimeEngineModule,
        "probeRuntime",
        lambda descriptor, **_kwargs: RuntimeProbe(descriptor.runtimeId, "ready", sysExecutable()),
    )
    monkeypatch.setattr(
        runtimeEngineModule,
        "probeRuntimeAuth",
        lambda descriptor, **_kwargs: {"state": "unsupported", "authenticated": None},
    )
    monkeypatch.setattr(
        runtimeEngineModule,
        "probeMcpConnection",
        lambda runtimeId, **_kwargs: {"connected": True, "mode": "test"},
    )
    engine = AgentRuntimeEngine(SessionStore(tmp_path / "sessions.sqlite3"), SessionManager())
    engine.registry = descriptors

    with pytest.raises(RuntimeError, match="여러 개"):
        engine.selectRuntime()

    assert engine.setDefaultRuntime("two") == "two"
    assert engine.selectRuntime() == "two"


def sysExecutable() -> str:
    import sys

    return sys.executable


def testRuntimeAnswerCommitRejectsUncitedOrIncompleteEvidence():
    from dartlab.ai.agent import _runtimeAnswerCommitted

    refs = [
        {
            "id": "table:exact",
            "kind": "tableRef",
            "payload": {"rowCount": 1, "rows": [{"metric": "sales", "value": 1}]},
        },
        {"id": "value:exact", "kind": "valueRef", "payload": {"metric": "sales", "value": 1}},
        {"id": "date:exact", "kind": "dateRef", "payload": {"period": "2026Q1"}},
    ]
    assert _runtimeAnswerCommitted(
        "2026년 1분기 매출은 1원이다. table:exact value:exact date:exact",
        refs,
        {"status": "completed"},
        failed=False,
    )
    assert not _runtimeAnswerCommitted("매출은 1원이다.", refs, {"status": "completed"}, failed=False)
    assert not _runtimeAnswerCommitted(
        "table:exact value:exact date:exact",
        refs,
        {"status": "interrupted"},
        failed=False,
    )


def testDocumentEvidenceProjectionKeepsAuditableClaimFields():
    from dartlab.ai.runtime.engine import _publicEvidencePayload

    payload = _publicEvidencePayload(
        {
            "period": "2024Q4",
            "rceptNo": "20250311001085",
            "fields": {
                "adt_opinion": "적정의견",
                "core_adt_matter": "건설중인자산의 감가상각개시시점 평가",
            },
        },
        kind="docRef",
    )

    assert payload["fields"]["adt_opinion"] == "적정의견"
    assert "감가상각개시시점" in payload["fields"]["core_adt_matter"]


def _readyProbeEngine(tmp_path, monkeypatch):
    """설치·로그인·MCP 가 모두 통과한 가짜 런타임 하나를 가진 엔진을 만든다."""
    descriptor = RuntimeDescriptor(
        "fake",
        "Fake",
        "fake",
        "ndjson",
        ("fake",),
        ("--version",),
        (),
        (),
        "https://example.invalid",
    )
    monkeypatch.setattr(
        runtimeEngineModule, "probeRuntime", lambda value, **_kwargs: RuntimeProbe("fake", "ready", "fake.exe")
    )
    monkeypatch.setattr(
        runtimeEngineModule,
        "probeAllRuntimes",
        lambda **_kwargs: [RuntimeProbe("fake", "ready", "fake.exe")],
    )
    monkeypatch.setattr(runtimeEngineModule, "probeRuntimeAuth", lambda *args, **kwargs: {"state": "authenticated"})
    monkeypatch.setattr(
        runtimeEngineModule, "probeMcpConnection", lambda runtimeId, **_kwargs: {"connected": True, "mode": "test"}
    )
    monkeypatch.setattr(runtimeEngineModule, "_semanticReadiness", lambda **_kwargs: {"ready": True, "checks": {}})
    runtimeEngineModule._DELIVERY_CACHE.clear()
    engine = AgentRuntimeEngine(SessionStore(tmp_path / "sessions.sqlite3"), SessionManager())
    engine.registry = {"fake": descriptor}
    return engine


def testBlockedDeliveryStopsFalseReadySignal(tmp_path, monkeypatch):
    """설치·로그인·MCP 가 통과해도 마지막 턴이 런타임 층에서 죽었으면 준비 완료가 아니다.

    실측(2026-08-06): codex 는 세 축 전부 통과하면서 사용량 한도 소진으로 도구 도달이
    0/18 이었는데 화면은 groundedReady 와 investmentReady 를 모두 True 로 적었다.
    """
    engine = _readyProbeEngine(tmp_path, monkeypatch)

    before = engine.status(blocking=False)["runtimes"][0]
    assert before["groundedReady"] is True
    assert before["readiness"]["delivery"] == "unknown", "재 본 적 없는 것은 모른다고 적는다"

    engine._recordDelivery("fake", toolReached=False, errorReason="사용량 한도를 소진했습니다")
    after = engine.status(blocking=False)["runtimes"][0]

    assert after["groundedReady"] is False
    assert after["investmentReady"] is False
    assert after["readiness"]["delivery"] == "blocked"
    assert after["blockingReason"] == "사용량 한도를 소진했습니다"
    assert after["primaryAction"] == "recheck", "이미 설치·연결됐으니 재설치를 권하면 안 된다"

    with pytest.raises(runtimeEngineModule.RuntimeUnavailableError, match="사용량 한도"):
        engine.selectRuntime("fake")


def testReachedToolClearsPreviousBlock(tmp_path, monkeypatch):
    """도구에 실제로 닿은 턴은 옛 실패 기록을 지운다."""
    engine = _readyProbeEngine(tmp_path, monkeypatch)
    engine._recordDelivery("fake", toolReached=False, errorReason="일시 오류")
    assert engine.status(blocking=False)["runtimes"][0]["groundedReady"] is False

    engine._recordDelivery("fake", toolReached=True, errorReason="")
    row = engine.status(blocking=False)["runtimes"][0]

    assert row["groundedReady"] is True
    assert row["readiness"]["delivery"] == "verified"
    assert engine.selectRuntime("fake") == "fake"


def testToollessButErrorFreeTurnDoesNotBlockRuntime(tmp_path, monkeypatch):
    """도구를 안 부른 것은 답변 품질 문제이지 도달 문제가 아니다."""
    engine = _readyProbeEngine(tmp_path, monkeypatch)

    engine._recordDelivery("fake", toolReached=False, errorReason="")

    assert engine.sessionStore.getDelivery("fake") is None
    assert engine.status(blocking=False)["runtimes"][0]["groundedReady"] is True


def testStaleBlockExpiresInsteadOfFreezingRuntimeForever(tmp_path, monkeypatch):
    """사용량 한도는 시간이 지나면 풀린다. 실패 기록을 영구 차단으로 굳히지 않는다."""
    engine = _readyProbeEngine(tmp_path, monkeypatch)
    engine._recordDelivery("fake", toolReached=False, errorReason="한도 소진")
    assert engine.status(blocking=False)["runtimes"][0]["groundedReady"] is False

    monkeypatch.setattr(runtimeEngineModule, "_isStaleIso", lambda timestamp, ttlSeconds: True)
    runtimeEngineModule._DELIVERY_CACHE.clear()
    row = engine.status(blocking=False)["runtimes"][0]

    assert row["groundedReady"] is True
    assert row["readiness"]["delivery"] == "unknown", "지난 기록은 판정이 아니라 미상이다"


def testExplicitRecheckResetsDeliveryToUnknownNotReady(tmp_path, monkeypatch):
    """다시 확인은 도달을 증명하지 않는다. 준비됨이 아니라 미상으로 되돌린다."""
    engine = _readyProbeEngine(tmp_path, monkeypatch)
    engine._recordDelivery("fake", toolReached=True, errorReason="")
    assert engine.status(blocking=False)["runtimes"][0]["readiness"]["delivery"] == "verified"

    engine.status(refresh=True)

    assert engine.status(blocking=False)["runtimes"][0]["readiness"]["delivery"] == "unknown"


def testRuntimeStorePathFollowsIsolatedDartlabHome(monkeypatch, tmp_path):
    """런타임 DB 는 형제 사용자 상태 저장소와 같은 격리 규약을 따른다.

    실측(2026-08-06): 이 경로만 사용자 home 을 직접 잡고 있어서, 격리된 실행이
    운영자의 실제 도달 판정 원장을 통째로 지웠다. 그러면 화면이 다시 거짓 준비 완료로
    돌아간다.
    """
    from dartlab.ai.runtime.engine import _runtimeStorePath

    monkeypatch.setenv("DARTLAB_HOME", str(tmp_path / "home"))
    monkeypatch.delenv("DARTLAB_RUNTIME_DB", raising=False)
    assert _runtimeStorePath().parent == tmp_path / "home"

    monkeypatch.setenv("DARTLAB_RUNTIME_DB", str(tmp_path / "explicit.sqlite3"))
    assert _runtimeStorePath() == tmp_path / "explicit.sqlite3", "명시 경로가 우선한다"
