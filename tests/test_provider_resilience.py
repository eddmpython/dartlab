"""provider 예외 경계 테스트."""

from unittest.mock import MagicMock, patch

from dartlab.engines.ai.providers.claude import ClaudeProvider
from dartlab.engines.ai.providers.claude_code import ClaudeCodeProvider
from dartlab.engines.ai.providers.ollama import OllamaProvider
from dartlab.engines.ai.providers.openai_compat import OpenAICompatProvider
from dartlab.engines.ai.types import LLMConfig


class TestOpenAICompatProvider:
    def test_check_available_returns_false_on_runtime_error(self, monkeypatch):
        provider = OpenAICompatProvider(LLMConfig(provider="openai"))

        def raise_runtime_error():
            raise RuntimeError("client init failed")

        monkeypatch.setattr(provider, "_get_client", raise_runtime_error)

        assert provider.check_available() is False


class TestClaudeProvider:
    def test_check_available_returns_false_on_runtime_error(self, monkeypatch):
        provider = ClaudeProvider(LLMConfig(provider="claude"))

        def raise_runtime_error():
            raise RuntimeError("client init failed")

        monkeypatch.setattr(provider, "_get_client", raise_runtime_error)

        assert provider.check_available() is False


class TestOllamaProvider:
    def test_get_installed_models_returns_empty_on_bad_json(self):
        provider = OllamaProvider(LLMConfig(provider="ollama"))

        with patch("requests.get", return_value=MagicMock(json=MagicMock(side_effect=ValueError("bad json")))):
            assert provider.get_installed_models() == []


class TestClaudeCodeProvider:
    def test_get_sdk_api_key_returns_none_on_bad_json(self, monkeypatch):
        provider = ClaudeCodeProvider(LLMConfig(provider="claude-code"))
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        with patch("subprocess.run", return_value=MagicMock(returncode=0, stdout="not-json")):
            assert provider._get_sdk_api_key() is None
