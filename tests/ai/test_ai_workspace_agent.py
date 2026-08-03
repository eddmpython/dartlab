"""Workspace agent 진입점과 설치형 런타임 연결 계약."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def test_workbench_is_the_workspace_agent_entry():
    from dartlab.ai.workbench.loop import GRAPH_NODES

    assert GRAPH_NODES == (
        "brief",
        "work",
        "critique",
        "compose",
        "gate",
        "harvest",
    )


def test_workspace_agent_uses_official_runtime():
    import importlib.util
    import inspect

    from dartlab.ai.kernel import _askEvents

    assert importlib.util.find_spec("dartlab.ai.runtime") is not None
    assert "runRuntimeAgent" in inspect.getsource(_askEvents)
