"""공개 ask가 고정 graph 없이 설치형 runtime 하나만 사용하는지 검증한다."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def test_kernel_exposes_ask_and_runtime_ssot():
    import dartlab
    from dartlab.ai.runtime import getRuntimeEngine

    assert callable(dartlab.ask)
    assert callable(getRuntimeEngine)


def test_analysis_mode_does_not_switch_to_fixed_graph(monkeypatch):
    from dartlab.ai import kernel
    from dartlab.ai.contracts import TraceEvent

    received: list[dict] = []

    def _fakeRuntime(_question: str, **kwargs):
        received.append(kwargs)
        yield TraceEvent("runtime_session", {"runtimeId": "cline", "sessionId": "s1"})
        yield TraceEvent("chunk", {"text": "완료"})
        yield TraceEvent("done", {"responseMeta": {"finalEvent": "answer", "responseStatus": "ok"}})

    monkeypatch.setattr(kernel, "runRuntimeAgent", _fakeRuntime)

    events = list(kernel._askEvents("분석해줘", mode="analysis", runtimeId="cline"))

    assert [event.kind for event in events] == ["runtime_session", "chunk", "done"]
    assert received == [{"mode": "analysis", "runtimeId": "cline"}]
