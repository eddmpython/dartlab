"""CLI 기반 provider 테스트 — mock subprocess로 CLI 불필요."""

import json
import os
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from dartlab.engines.ai.types import LLMConfig

_SKIP_CI = pytest.mark.skipif(
    os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true",
    reason="CI 환경에서 CLI provider 테스트 불가",
)

_CLEAN_CLAUDE_ENV = {
    k: v
    for k, v in os.environ.items()
    if not k.startswith("CLAUDE")
    and not k.startswith("VSCODE")
    and k not in ("ELECTRON_RUN_AS_NODE", "ELECTRON_NO_ASAR")
}


# ══════════════════════════════════════
# ClaudeCodeProvider
# ══════════════════════════════════════


@_SKIP_CI
@patch.dict(os.environ, _CLEAN_CLAUDE_ENV, clear=True)
class TestClaudeCodeProvider:
    def _make_provider(self, model=None):
        from dartlab.engines.ai.providers.claude_code import ClaudeCodeProvider

        config = LLMConfig(provider="claude-code", model=model)
        return ClaudeCodeProvider(config)

    def test_default_model(self):
        provider = self._make_provider()
        assert provider.default_model == "sonnet"

    def test_resolved_model_override(self):
        provider = self._make_provider(model="opus")
        assert provider.resolved_model == "opus"

    @patch("shutil.which", return_value=None)
    def test_check_available_not_installed(self, _):
        provider = self._make_provider()
        assert provider.check_available() is False

    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/bin/claude")
    def test_check_available_authenticated(self, _, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        provider = self._make_provider()
        assert provider.check_available() is True

    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/bin/claude")
    def test_check_available_not_authenticated(self, _, mock_run):
        mock_run.return_value = MagicMock(returncode=1)
        provider = self._make_provider()
        assert provider.check_available() is False

    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/bin/claude")
    def test_complete_success(self, _, mock_run):
        response_json = json.dumps(
            {
                "type": "result",
                "subtype": "success",
                "result": "분석 결과입니다.",
                "is_error": False,
                "total_cost_usd": 0.01,
                "num_turns": 1,
                "duration_ms": 2000,
            }
        )
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=response_json,
            stderr="",
        )
        provider = self._make_provider()
        result = provider.complete(
            [
                {"role": "system", "content": "시스템"},
                {"role": "user", "content": "분석해줘"},
            ]
        )
        assert result.answer == "분석 결과입니다."
        assert result.provider == "claude-code"
        assert result.usage["total_cost_usd"] == 0.01

    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/bin/claude")
    def test_complete_with_system_prompt(self, _, mock_run):
        """시스템 프롬프트가 --system-prompt 플래그로 전달되는지 확인."""
        response_json = json.dumps(
            {
                "type": "result",
                "result": "ok",
                "is_error": False,
            }
        )
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=response_json,
            stderr="",
        )
        provider = self._make_provider()
        provider.complete(
            [
                {"role": "system", "content": "재무 분석가"},
                {"role": "user", "content": "분석"},
            ]
        )
        cmd = mock_run.call_args[0][0]
        assert "--system-prompt" in cmd
        idx = cmd.index("--system-prompt")
        assert cmd[idx + 1] == "재무 분석가"

    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/bin/claude")
    def test_complete_cli_error(self, _, mock_run):
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error: not authenticated",
        )
        provider = self._make_provider()
        with pytest.raises(RuntimeError, match="Claude Code CLI 오류"):
            provider.complete([{"role": "user", "content": "test"}])

    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/bin/claude")
    def test_complete_is_error_flag(self, _, mock_run):
        response_json = json.dumps(
            {
                "type": "result",
                "result": "something broke",
                "is_error": True,
            }
        )
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=response_json,
            stderr="",
        )
        provider = self._make_provider()
        with pytest.raises(RuntimeError, match="Claude Code CLI 오류"):
            provider.complete([{"role": "user", "content": "test"}])

    @patch("shutil.which", return_value=None)
    def test_complete_not_installed(self, _):
        provider = self._make_provider()
        with pytest.raises(FileNotFoundError, match="Claude Code CLI"):
            provider.complete([{"role": "user", "content": "test"}])

    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/bin/claude")
    def test_complete_timeout(self, _, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="claude", timeout=300)
        provider = self._make_provider()
        with pytest.raises(TimeoutError):
            provider.complete([{"role": "user", "content": "test"}])

    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/bin/claude")
    def test_model_in_command(self, _, mock_run):
        """모델명이 --model 플래그로 전달되는지 확인."""
        response_json = json.dumps(
            {
                "type": "result",
                "result": "ok",
                "is_error": False,
            }
        )
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=response_json,
            stderr="",
        )
        provider = self._make_provider(model="opus")
        provider.complete([{"role": "user", "content": "test"}])
        cmd = mock_run.call_args[0][0]
        assert "--model" in cmd
        idx = cmd.index("--model")
        assert cmd[idx + 1] == "opus"


# ══════════════════════════════════════
# CodexProvider
# ══════════════════════════════════════


@_SKIP_CI
class TestCodexProvider:
    def _make_provider(self, model=None):
        from dartlab.engines.ai.providers.codex import CodexProvider

        config = LLMConfig(provider="codex", model=model)
        return CodexProvider(config)

    def test_default_model(self):
        from dartlab.engines.ai.codex_cli import get_codex_configured_model

        provider = self._make_provider()
        assert provider.default_model == (get_codex_configured_model() or "gpt-4.1")

    def test_resolved_model_override(self):
        provider = self._make_provider(model="gpt-4o")
        assert provider.resolved_model == "gpt-4o"

    @patch("shutil.which", return_value=None)
    def test_check_available_not_installed(self, _):
        provider = self._make_provider()
        assert provider.check_available() is False

    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/bin/codex")
    def test_check_available_installed(self, _, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="codex-cli 0.115.0", stderr="")
        provider = self._make_provider()
        assert provider.check_available() is True

    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/bin/codex")
    def test_complete_success(self, _, mock_run):
        jsonl_output = "\n".join(
            [
                json.dumps({"type": "thread.started", "thread_id": "abc"}),
                json.dumps({"type": "turn.started"}),
                json.dumps(
                    {
                        "type": "item.completed",
                        "item": {"type": "agent_message", "text": "결과입니다."},
                    }
                ),
                json.dumps(
                    {
                        "type": "turn.completed",
                        "usage": {"input_tokens": 100, "output_tokens": 50},
                    }
                ),
            ]
        )
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=jsonl_output,
            stderr="",
        )
        provider = self._make_provider()
        result = provider.complete([{"role": "user", "content": "분석해줘"}])
        assert result.answer == "결과입니다."
        assert result.provider == "codex"
        assert result.usage["total_tokens"] == 150

    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/bin/codex")
    def test_complete_with_system(self, _, mock_run):
        """시스템 메시지가 프롬프트에 포함되는지 확인."""
        jsonl_output = json.dumps(
            {
                "type": "item.completed",
                "item": {"type": "agent_message", "text": "ok"},
            }
        )
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=jsonl_output,
            stderr="",
        )
        provider = self._make_provider()
        provider.complete(
            [
                {"role": "system", "content": "재무 분석가"},
                {"role": "user", "content": "분석"},
            ]
        )
        # 프롬프트는 stdin(input kwarg)으로 전달
        stdin_input = mock_run.call_args[1].get("input", b"")
        prompt = stdin_input.decode("utf-8") if isinstance(stdin_input, bytes) else stdin_input
        assert "[System Instructions]" in prompt
        assert "재무 분석가" in prompt

    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/bin/codex")
    def test_complete_passes_model_flag(self, _, mock_run):
        jsonl_output = json.dumps(
            {
                "type": "item.completed",
                "item": {"type": "agent_message", "text": "ok"},
            }
        )
        mock_run.return_value = MagicMock(returncode=0, stdout=jsonl_output, stderr="")
        provider = self._make_provider(model="gpt-5.4")
        provider.complete([{"role": "user", "content": "분석"}])
        cmd = mock_run.call_args[0][0]
        assert "--model" in cmd
        idx = cmd.index("--model")
        assert cmd[idx + 1] == "gpt-5.4"

    @patch(
        "dartlab.engines.ai.codex_cli.inspect_codex_cli",
        return_value={"sandboxModes": ["read-only", "workspace-write"]},
    )
    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/bin/codex")
    def test_complete_uses_workspace_write_for_code_tasks(self, _, mock_run, __):
        jsonl_output = json.dumps(
            {
                "type": "item.completed",
                "item": {"type": "agent_message", "text": "ok"},
            }
        )
        mock_run.return_value = MagicMock(returncode=0, stdout=jsonl_output, stderr="")
        provider = self._make_provider()
        provider.complete([{"role": "user", "content": "src/app.py 버그를 수정해줘"}])
        cmd = mock_run.call_args_list[-1][0][0]
        idx = cmd.index("--sandbox")
        assert cmd[idx + 1] == "workspace-write"

    @patch(
        "dartlab.engines.ai.codex_cli.inspect_codex_cli",
        return_value={"sandboxModes": ["read-only", "workspace-write"]},
    )
    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/bin/codex")
    def test_complete_uses_read_only_for_analysis_tasks(self, _, mock_run, __):
        jsonl_output = json.dumps(
            {
                "type": "item.completed",
                "item": {"type": "agent_message", "text": "ok"},
            }
        )
        mock_run.return_value = MagicMock(returncode=0, stdout=jsonl_output, stderr="")
        provider = self._make_provider()
        provider.complete([{"role": "user", "content": "삼성전자 재무를 설명해줘"}])
        cmd = mock_run.call_args_list[-1][0][0]
        idx = cmd.index("--sandbox")
        assert cmd[idx + 1] == "read-only"

    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/bin/codex")
    def test_complete_cli_error(self, _, mock_run):
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error: not logged in",
        )
        provider = self._make_provider()
        with pytest.raises(RuntimeError, match="Codex CLI 오류"):
            provider.complete([{"role": "user", "content": "test"}])

    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/bin/codex")
    def test_complete_no_answer(self, _, mock_run):
        """응답에 agent_message가 없으면 에러."""
        jsonl_output = json.dumps({"type": "turn.completed"})
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=jsonl_output,
            stderr="",
        )
        provider = self._make_provider()
        with pytest.raises(RuntimeError, match="응답을 추출할 수 없습니다"):
            provider.complete([{"role": "user", "content": "test"}])

    @patch("shutil.which", return_value=None)
    def test_complete_not_installed(self, _):
        provider = self._make_provider()
        with pytest.raises(FileNotFoundError, match="Codex CLI"):
            provider.complete([{"role": "user", "content": "test"}])

    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/bin/codex")
    def test_complete_timeout(self, _, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="codex", timeout=300)
        provider = self._make_provider()
        with pytest.raises(TimeoutError):
            provider.complete([{"role": "user", "content": "test"}])


# ══════════════════════════════════════
# CLI Detection
# ══════════════════════════════════════


class TestCliDetection:
    def test_detect_claude_code_structure(self):
        from dartlab.engines.ai.cli_setup import detect_claude_code

        result = detect_claude_code()
        assert "installed" in result
        assert "authenticated" in result
        assert "version" in result

    def test_detect_codex_structure(self):
        from dartlab.engines.ai.cli_setup import detect_codex

        result = detect_codex()
        assert "installed" in result
        assert "version" in result
        assert "configuredModel" in result
        assert "supportsWorkspaceWrite" in result

    def test_claude_code_install_guide(self):
        from dartlab.engines.ai.cli_setup import get_claude_code_install_guide

        guide = get_claude_code_install_guide()
        assert isinstance(guide, str)
        assert "npm" in guide
        assert "claude" in guide

    def test_codex_install_guide(self):
        from dartlab.engines.ai.cli_setup import get_codex_install_guide

        guide = get_codex_install_guide()
        assert isinstance(guide, str)
        assert "npm" in guide
        assert "codex" in guide


# ══════════════════════════════════════
# Provider Registry
# ══════════════════════════════════════


class TestProviderRegistry:
    def test_claude_code_in_registry(self):
        from dartlab.engines.ai.providers import available_providers

        assert "claude-code" in available_providers()

    def test_codex_in_registry(self):
        from dartlab.engines.ai.providers import available_providers

        assert "codex" in available_providers()

    def test_create_claude_code_provider(self):
        from dartlab.engines.ai.providers import create_provider

        config = LLMConfig(provider="claude-code")
        provider = create_provider(config)
        assert provider.__class__.__name__ == "ClaudeCodeProvider"

    def test_create_codex_provider(self):
        from dartlab.engines.ai.providers import create_provider

        config = LLMConfig(provider="codex")
        provider = create_provider(config)
        assert provider.__class__.__name__ == "CodexProvider"


# ══════════════════════════════════════
# Status Integration
# ══════════════════════════════════════


@pytest.mark.skipif(not hasattr(__import__("dartlab"), "llm"), reason="dartlab.llm 미등록")
class TestStatusIntegration:
    def test_status_claude_code(self):
        import dartlab

        dartlab.llm.configure(provider="claude-code")
        result = dartlab.llm.status()
        assert result["provider"] == "claude-code"
        assert "claude-code" in result

    def test_status_codex(self):
        import dartlab

        dartlab.llm.configure(provider="codex")
        result = dartlab.llm.status()
        assert result["provider"] == "codex"
        assert "codex" in result
