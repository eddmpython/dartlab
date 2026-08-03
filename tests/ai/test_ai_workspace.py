"""Workspace evidence ref와 공식 agent runtime 계약."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def test_tool_result_refs_are_evidence_surface():
    from dartlab.ai.contracts import Ref
    from dartlab.ai.tools.types import ToolResult

    ref = Ref(id="table:test", kind="tableRef", title="표", source="unit", payload={"rows": []})
    result = ToolResult(True, "ok", refs=[ref])

    assert result.refs[0].kind == "tableRef"
    assert result.refs[0].payload == {"rows": []}


def test_workspace_runtime_package_exposes_engine_entry():
    import importlib.util

    from dartlab.ai.runtime import getRuntimeEngine

    assert importlib.util.find_spec("dartlab.ai.runtime") is not None
    assert callable(getRuntimeEngine)
