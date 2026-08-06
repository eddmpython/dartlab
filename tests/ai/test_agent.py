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


class TestEmptyTurnReason:
    """런타임이 답 없이 끝냈을 때 그 이유를 그대로 전한다.

    실측(2026-08-06). 배터리 11 개 질문이 전부 "최종 답변이 비어 있습니다" 로 끝났다.
    사실이지만 무엇을 해야 할지는 알 수 없는 문장이다. 정작 런타임은 종료 메시지에 자기
    상태를 실어 보냈고 우리가 그것을 버렸다.
    """

    def test정상완료는사유가없다(self) -> None:
        """멀쩡히 끝난 턴에 없는 사유를 붙이면 그게 새 거짓말이다."""
        from dartlab.ai.agent import _emptyTurnReason

        assert _emptyTurnReason({"status": "success"}) is None
        assert _emptyTurnReason({"status": "completed"}) is None
        assert _emptyTurnReason({}) is None

    def test아는상태는사람말로바꾼다(self) -> None:
        """`error_max_turns` 를 그대로 보이면 사용자가 읽을 수 없다."""
        from dartlab.ai.agent import _emptyTurnReason

        assert "턴 수" in (_emptyTurnReason({"status": "error_max_turns"}) or "")
        assert "거절" in (_emptyTurnReason({"turn": {"status": "refusal"}}) or "")

    def test모르는상태는번역하지않고그대로옮긴다(self) -> None:
        """임의로 해석하면 진짜 사유가 사라진다. 모르면 원문을 보인다."""
        from dartlab.ai.agent import _emptyTurnReason

        reason = _emptyTurnReason({"status": "brand_new_stop_code"}) or ""

        assert "brand_new_stop_code" in reason
