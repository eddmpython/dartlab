"""API 키 미설정 시 AI 응답 경로에 안내가 전달되는지 검증.

근본 이슈:
- 서버 (uvicorn) 환경은 TTY 없음 → ``promptAndSave()`` 의 ``input()`` 이 EOFError.
- 과거 동작: except 에서 ``None`` 반환 → 상위에서 데이터 없음으로 오해 →
  AI 응답 본문에 "키가 필요합니다" 안내가 전혀 담기지 않음.
- 개선 동작: TTY 없으면 ``AuthKeyMissing`` 예외 raise → 상위로 전파.
  예외 본문이 서비스명, 발급 URL, `.env` 설정법을 포함해 상위 런타임이 그대로 안내할 수 있다.
"""

from __future__ import annotations

import pytest

from dartlab.core.env import AuthKeyMissing, promptAndSave

pytestmark = pytest.mark.unit


def _disableTty(monkeypatch):
    """sys.stdin.isatty() 를 False 로 강제해 서버와 백그라운드 시나리오를 시뮬레이션한다."""

    class _FakeStdin:
        def isatty(self):
            return False

    monkeypatch.setattr("sys.stdin", _FakeStdin())


def test_promptAndSave_raises_AuthKeyMissing_without_tty(monkeypatch):
    """TTY 없는 환경 + 키 미설정 → AuthKeyMissing 예외 raise."""
    monkeypatch.delenv("TEST_AUTH_KEY", raising=False)
    _disableTty(monkeypatch)

    with pytest.raises(AuthKeyMissing) as ei:
        promptAndSave(
            "TEST_AUTH_KEY",
            label="테스트 키가 필요합니다.",
            guide="https://example.com/apply",
        )

    msg = str(ei.value)
    # 사용자가 곧바로 행동할 수 있는 3 요소 포함
    assert "TEST_AUTH_KEY" in msg
    assert "https://example.com/apply" in msg
    assert ".env" in msg


def test_AuthKeyMissing_exposes_attributes():
    """예외 속성으로 envKey / label / guide 에 직접 접근 가능."""
    err = AuthKeyMissing("MY_KEY", label="My label", guide="https://x.test")
    assert err.envKey == "MY_KEY"
    assert err.label == "My label"
    assert err.guide == "https://x.test"


def test_promptAndSave_returns_existing_env_value(monkeypatch):
    """키가 이미 설정돼 있으면 TTY 여부와 무관하게 값 반환 (예외 없음)."""
    monkeypatch.setenv("TEST_EXISTING_KEY", "already-set-value")
    _disableTty(monkeypatch)

    result = promptAndSave(
        "TEST_EXISTING_KEY",
        label="라벨",
        guide="https://example.com",
    )

    assert result == "already-set-value"


def test_auth_guidance_remains_in_core_env_with_official_runtime_installed():
    """공식 runtime 설치 여부와 무관하게 API 키 안내는 core.env가 소유한다."""
    import importlib.util
    import inspect

    import dartlab.core.env as env_module

    assert importlib.util.find_spec("dartlab.ai.runtime") is not None
    assert "dartlab.ai.runtime" not in inspect.getsource(env_module)
