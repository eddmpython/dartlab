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
            payload={
                "tool": "EngineCall",
                "result": {
                    "ok": True,
                    "refs": [
                        {"id": "table:exact", "kind": "tableRef"},
                        {"id": "value:exact", "kind": "valueRef"},
                        {"id": "date:exact", "kind": "dateRef"},
                    ],
                },
            },
        )
        yield handle.projector.event(
            "messageDelta",
            turnId=turnId,
            payload={"text": "근거 답변 table:exact value:exact date:exact"},
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
        "messageDelta",
        "turnCompleted",
    ]
    outcomeId = str(events[-1].payload["outcomeId"])
    assert events[2].payload["refDetails"] == [
        {
            "id": "table:exact",
            "kind": "tableRef",
            "title": "table:exact",
            "source": "",
            "sourceType": "internal",
            "payload": {},
            "outcomeId": outcomeId,
        },
        {
            "id": "value:exact",
            "kind": "valueRef",
            "title": "value:exact",
            "source": "",
            "sourceType": "internal",
            "payload": {},
            "outcomeId": outcomeId,
        },
        {
            "id": "date:exact",
            "kind": "dateRef",
            "title": "date:exact",
            "source": "",
            "sourceType": "internal",
            "payload": {},
            "outcomeId": outcomeId,
        },
    ]
    assert engine.resolveEvidence(outcomeId, "table:exact")["kind"] == "tableRef"
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
            context={"stockCode": "005930", "history": [{"content": "민감"}]},
        )
    )
    managed = engine.sessionManager.get(engine.sessionStore.list(limit=1)[0].sessionId)
    assert managed is not None
    assert '"stockCode":"005930"' in managed.handle.metadata["question"]
    assert "민감" not in managed.handle.metadata["question"]


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


def sysExecutable() -> str:
    import sys

    return sys.executable


def testRuntimeAnswerCommitRejectsUncitedOrIncompleteEvidence():
    from dartlab.ai.agent import _runtimeAnswerCommitted

    refs = [
        {"id": "table:exact", "kind": "tableRef"},
        {"id": "value:exact", "kind": "valueRef"},
        {"id": "date:exact", "kind": "dateRef"},
    ]
    assert _runtimeAnswerCommitted(
        "매출은 1원이다. table:exact value:exact date:exact",
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
