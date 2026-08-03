"""Provider SDK 경계 계약 - dartlab camelCase 가 외부 SDK 로 새지 않는지.

========================================
이 파일이 잡는 버그 클래스
========================================
dartlab 코드 규약은 camelCase 지만, openai/anthropic SDK 는 snake_case 다.
일괄 camelCase codemod 가 SDK 호출 인자와 응답 속성까지 바꿔버리면
`generate()` 가 첫 호출에서 TypeError/AttributeError 로 즉사한다.

실제 사고 (2026-07-26):
    `ai/providers/__init__.py` 가 `client.chat.completions.create(toolChoice=...)`
    와 `message.toolCalls` 를 쓰고 있었다. openai SDK 는 **kwargs 를 받지 않으므로
    `OpenAICompatibleProvider.generate()` 는 openai 계열에서 100% TypeError.
    채팅은 `generateStream()` 만 타서 살아있었지만, `workbench/runner.py` 가
    `provider.generate()` 를 쓰므로 5 패스 workbench 는 전멸해 있었다.
    스트리밍 경로만 수동 확인하면 못 잡는다. 그래서 stub client 로 generate 를 직접 친다.

테스트는 네트워크를 타지 않는다. 가짜 SDK client 를 주입해 호출 인자를 그대로 포획한다.
"""

from __future__ import annotations

import inspect

import pytest

pytestmark = [pytest.mark.unit]


# ════════════════════════════════════════
# 1) OpenAI 호환 경로 - 실제 SDK 시그니처 대조
# ════════════════════════════════════════


def test_openaiCompatible_generate_usesSnakeCaseKwargs():
    """chat.completions 경로가 SDK 가 실제로 받는 인자명만 쓰는지 stub 으로 포획."""
    from dartlab.ai.providers import OpenAICompatibleProvider, ProviderConfig

    captured: dict = {}

    class _FakeFunction:
        name = "panel"
        arguments = '{"axis": "IS"}'

    class _FakeToolCall:
        id = "call_1"
        function = _FakeFunction()

    class _FakeMessage:
        content = "ok"
        # SDK 의 실제 속성명. camelCase 로 읽으면 AttributeError 가 나야 정상이다.
        tool_calls = [_FakeToolCall()]

    class _FakeChoice:
        message = _FakeMessage()

    class _FakeResponse:
        choices = [_FakeChoice()]

        def model_dump(self):
            return {}

    class _FakeCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            return _FakeResponse()

    class _FakeChat:
        completions = _FakeCompletions()

    class _FakeClient:
        chat = _FakeChat()

    provider = OpenAICompatibleProvider(ProviderConfig(provider="custom", model="m", apiKey="k", baseUrl="http://x"))
    turn = provider._generateChatCompletions(_FakeClient(), [{"role": "user", "content": "hi"}], [])

    assert turn.content == "ok"
    assert [c.name for c in turn.toolCalls] == ["panel"]
    assert turn.toolCalls[0].args == {"axis": "IS"}

    # 포획한 kwargs 가 실제 openai SDK 시그니처에 전부 존재해야 한다.
    from openai.resources.chat.completions import Completions

    allowed = set(inspect.signature(Completions.create).parameters)
    unknown = sorted(k for k in captured if k not in allowed)
    assert not unknown, (
        f"openai chat.completions.create 가 받지 않는 인자: {unknown}\n"
        "SDK 경계는 snake_case 다. dartlab camelCase 규약을 여기 적용하면 TypeError 로 즉사한다."
    )
    assert captured.get("tool_choice") == "auto"


def test_openaiResponses_generate_usesSnakeCaseKwargs():
    """responses 경로도 동일 계약 (openai/oauth-codex 가 먼저 시도하는 경로)."""
    from dartlab.ai.providers import OpenAICompatibleProvider, ProviderConfig

    captured: dict = {}

    class _FakeResponse:
        output = []
        output_text = "done"

        def model_dump(self):
            return {}

    class _FakeResponses:
        def create(self, **kwargs):
            captured.update(kwargs)
            return _FakeResponse()

    class _FakeClient:
        responses = _FakeResponses()

    provider = OpenAICompatibleProvider(ProviderConfig(provider="openai", model="m", apiKey="k"))
    turn = provider._generateResponses(_FakeClient(), [{"role": "user", "content": "hi"}], [])
    assert turn.content == "done"

    from openai.resources.responses import Responses

    allowed = set(inspect.signature(Responses.create).parameters)
    unknown = sorted(k for k in captured if k not in allowed)
    assert not unknown, f"openai responses.create 가 받지 않는 인자: {unknown}"
    assert captured.get("tool_choice") == "auto"


# ════════════════════════════════════════
# 2) provider 레지스트리 정합
# ════════════════════════════════════════


def test_gateway_uses_installed_agent_runtime_for_all_modes():
    """서버가 provider 리터럴 게이트 없이 공식 설치형 런타임을 호출하는지."""
    from dartlab.ai.agent import runRuntimeAgent
    from dartlab.server import agentGateway

    source = inspect.getsource(agentGateway.streamAgentRun)

    assert agentGateway.runRuntimeAgent is runRuntimeAgent
    assert "runRuntimeAgent" in source
    assert "_isLLMProvider" not in source


def test_wiredProviderIds_matchesFactoryKeys():
    """카탈로그 키와 팩토리 키가 어긋나면 provider 가 조용히 UnavailableProvider 로 떨어진다."""
    from dartlab.ai.providers import _PROVIDER_FACTORIES
    from dartlab.ai.settings.providerCatalog import wiredProviderIds

    catalog = set(wiredProviderIds())
    factories = set(_PROVIDER_FACTORIES)
    missing = sorted(catalog - factories)
    assert not missing, f"카탈로그에 있는데 팩토리가 없는 provider: {missing}"
