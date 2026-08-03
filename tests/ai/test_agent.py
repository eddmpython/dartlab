"""공식 설치형 AI runtime 공개 계약 테스트."""

from __future__ import annotations

import importlib.util

import pytest

pytestmark = pytest.mark.unit


def test_installed_agent_runtime_package_is_available():
    from dartlab.ai.runtime import AgentRuntimeEngine, getRuntimeEngine

    assert importlib.util.find_spec("dartlab.ai.runtime") is not None
    assert callable(getRuntimeEngine)
    assert AgentRuntimeEngine.__module__ == "dartlab.ai.runtime.engine"
