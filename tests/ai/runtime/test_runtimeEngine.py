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
