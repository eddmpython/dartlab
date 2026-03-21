"""AI provider / shared profile 테스트."""

from __future__ import annotations

import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.unit

from dartlab.engines.ai.types import LLMConfig


class TestCodexProvider:
    def _make_provider(self, model=None):
        from dartlab.engines.ai.providers.codex import CodexProvider

        return CodexProvider(LLMConfig(provider="codex", model=model))

    @patch(
        "dartlab.engines.ai.providers.support.codex_cli.inspect_codex_cli",
        return_value={"installed": False, "authenticated": False},
    )
    def test_check_available_not_installed(self, _mock_inspect):
        provider = self._make_provider()
        assert provider.check_available() is False

    @patch(
        "dartlab.engines.ai.providers.support.codex_cli.inspect_codex_cli",
        return_value={"installed": True, "authenticated": True},
    )
    def test_check_available_authenticated(self, _mock_inspect):
        provider = self._make_provider()
        assert provider.check_available() is True

    @patch(
        "dartlab.engines.ai.providers.support.codex_cli.inspect_codex_cli",
        return_value={"installed": True, "authenticated": True, "sandboxModes": ["read-only", "workspace-write"]},
    )
    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/bin/codex")
    def test_complete_success(self, _mock_which, mock_run, _mock_inspect):
        jsonl_output = "\n".join(
            [
                json.dumps({"type": "thread.started", "thread_id": "abc"}),
                json.dumps({"type": "turn.started"}),
                json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "결과입니다."}}),
                json.dumps({"type": "turn.completed", "usage": {"input_tokens": 100, "output_tokens": 50}}),
            ]
        )
        mock_run.return_value = MagicMock(returncode=0, stdout=jsonl_output, stderr="")

        provider = self._make_provider()
        result = provider.complete([{"role": "user", "content": "분석해줘"}])

        assert result.answer == "결과입니다."
        assert result.provider == "codex"
        assert result.usage["total_tokens"] == 150

    @patch(
        "dartlab.engines.ai.providers.support.codex_cli.inspect_codex_cli",
        return_value={"installed": True, "authenticated": True, "sandboxModes": ["read-only", "workspace-write"]},
    )
    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/bin/codex")
    def test_complete_passes_model_flag(self, _mock_which, mock_run, _mock_inspect):
        jsonl_output = json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "ok"}})
        mock_run.return_value = MagicMock(returncode=0, stdout=jsonl_output, stderr="")

        provider = self._make_provider(model="gpt-5.4")
        provider.complete([{"role": "user", "content": "분석"}])

        cmd = mock_run.call_args[0][0]
        assert "--model" in cmd
        idx = cmd.index("--model")
        assert cmd[idx + 1] == "gpt-5.4"

    @patch(
        "dartlab.engines.ai.providers.support.codex_cli.inspect_codex_cli",
        return_value={"installed": True, "authenticated": True, "sandboxModes": ["read-only", "workspace-write"]},
    )
    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/bin/codex")
    def test_complete_uses_workspace_write_for_code_tasks(self, _mock_which, mock_run, _mock_inspect):
        jsonl_output = json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "ok"}})
        mock_run.return_value = MagicMock(returncode=0, stdout=jsonl_output, stderr="")

        provider = self._make_provider()
        provider.complete([{"role": "user", "content": "src/app.py 버그를 수정해줘"}])

        cmd = mock_run.call_args_list[-1][0][0]
        idx = cmd.index("--sandbox")
        assert cmd[idx + 1] == "workspace-write"

    @patch(
        "dartlab.engines.ai.providers.support.codex_cli.inspect_codex_cli",
        return_value={"installed": True, "authenticated": True, "sandboxModes": ["read-only", "workspace-write"]},
    )
    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/bin/codex")
    def test_complete_uses_read_only_for_analysis_tasks(self, _mock_which, mock_run, _mock_inspect):
        jsonl_output = json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "ok"}})
        mock_run.return_value = MagicMock(returncode=0, stdout=jsonl_output, stderr="")

        provider = self._make_provider()
        provider.complete([{"role": "user", "content": "삼성전자 재무를 설명해줘"}])

        cmd = mock_run.call_args_list[-1][0][0]
        idx = cmd.index("--sandbox")
        assert cmd[idx + 1] == "read-only"

    @patch("shutil.which", return_value=None)
    def test_complete_not_installed(self, _mock_which):
        provider = self._make_provider()
        with pytest.raises(FileNotFoundError, match="Codex CLI"):
            provider.complete([{"role": "user", "content": "test"}])

    @patch(
        "dartlab.engines.ai.providers.support.codex_cli.inspect_codex_cli",
        return_value={"installed": True, "authenticated": True, "sandboxModes": ["read-only", "workspace-write"]},
    )
    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/bin/codex")
    def test_complete_timeout(self, _mock_which, mock_run, _mock_inspect):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="codex", timeout=300)
        provider = self._make_provider()
        with pytest.raises(TimeoutError):
            provider.complete([{"role": "user", "content": "test"}])


class TestCliDetection:
    def test_detect_codex_structure(self):
        from dartlab.engines.ai.providers.support.cli_setup import detect_codex

        result = detect_codex()
        assert "installed" in result
        assert "version" in result
        assert "configuredModel" in result
        assert "authenticated" in result
        assert "supportsWorkspaceWrite" in result

    def test_codex_install_guide(self):
        from dartlab.engines.ai.providers.support.cli_setup import get_codex_install_guide

        guide = get_codex_install_guide()
        assert isinstance(guide, str)
        assert "npm" in guide
        assert "codex" in guide


class TestProviderRegistry:
    def test_available_providers(self):
        from dartlab.engines.ai.providers import available_providers

        assert set(available_providers()) == {"openai", "ollama", "custom", "codex", "oauth-codex"}

    def test_create_codex_provider(self):
        from dartlab.engines.ai.providers import create_provider

        provider = create_provider(LLMConfig(provider="codex"))
        assert provider.__class__.__name__ == "CodexProvider"

    def test_create_oauth_codex_provider(self):
        from dartlab.engines.ai.providers import create_provider

        provider = create_provider(LLMConfig(provider="oauth-codex"))
        assert provider.__class__.__name__ == "OAuthCodexProvider"

    def test_unknown_provider_rejected(self):
        from dartlab.engines.ai.providers import create_provider

        with pytest.raises(ValueError, match="지원하지 않는 provider"):
            create_provider(LLMConfig(provider="chatgpt"))  # type: ignore[arg-type]


class TestSharedProfileRouting:
    def test_configure_role_binding_changes_resolved_config(self):
        from dartlab.engines.ai import configure, get_config

        configure(provider="openai", model="gpt-5.4")
        configure(provider="ollama", model="qwen3", role="summary")

        analysis = get_config()
        summary = get_config(role="summary")

        assert analysis.provider == "openai"
        assert analysis.model == "gpt-5.4"
        assert summary.provider == "ollama"
        assert summary.model == "qwen3"

    def test_status_uses_requested_provider_without_mutating_default(self, monkeypatch):
        import dartlab
        from dartlab.engines.ai import configure, get_config

        class DummyProvider:
            def __init__(self, config):
                self.resolved_model = config.model or "dummy-model"

            def check_available(self):
                return True

        monkeypatch.setattr("dartlab.engines.ai.providers.create_provider", lambda config: DummyProvider(config))

        configure(provider="openai", model="gpt-5.4")
        before = get_config()
        result = dartlab.llm.status(provider="codex")
        after = get_config()

        assert result["provider"] == "codex"
        assert result["available"] is True
        assert before.provider == after.provider == "openai"
