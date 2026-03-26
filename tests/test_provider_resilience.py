"""public provider 예외 경계 테스트."""

import pytest

pytestmark = pytest.mark.unit

from unittest.mock import MagicMock, patch

from dartlab.ai.providers.ollama import OllamaProvider
from dartlab.ai.providers.openai_compat import OpenAICompatProvider
from dartlab.ai.types import LLMConfig


class TestOpenAICompatProvider:
    def test_check_available_returns_false_on_runtime_error(self, monkeypatch):
        provider = OpenAICompatProvider(LLMConfig(provider="openai"))

        def raise_runtime_error():
            raise RuntimeError("client init failed")

        monkeypatch.setattr(provider, "_get_client", raise_runtime_error)

        assert provider.check_available() is False


class TestOllamaProvider:
    def test_get_installed_models_returns_empty_on_bad_json(self):
        provider = OllamaProvider(LLMConfig(provider="ollama"))

        with patch("requests.get", return_value=MagicMock(json=MagicMock(side_effect=ValueError("bad json")))):
            assert provider.get_installed_models() == []
