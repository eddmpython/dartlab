"""CLI 기반 LLM 도구 (Claude Code, Codex) 설치 감지 및 안내."""

from __future__ import annotations

import platform
import shutil
import subprocess

_IS_WINDOWS = platform.system() == "Windows"


def detect_claude_code() -> dict:
    """Claude Code CLI 상태 감지.

    Returns:
            {"installed": bool, "authenticated": bool, "version": str | None}
    """
    result: dict = {
        "installed": False,
        "authenticated": False,
        "version": None,
    }

    if not shutil.which("claude"):
        return result

    result["installed"] = True

    try:
        proc = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            shell=_IS_WINDOWS,
        )
        if proc.returncode == 0:
            result["version"] = proc.stdout.strip()
    except (subprocess.TimeoutExpired, OSError):
        pass

    try:
        proc = subprocess.run(
            ["claude", "auth", "status"],
            capture_output=True,
            text=True,
            timeout=10,
            shell=_IS_WINDOWS,
        )
        result["authenticated"] = proc.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        pass

    return result


def detect_codex() -> dict:
    """OpenAI Codex CLI 상태 감지.

    Returns:
            {"installed": bool, "version": str | None}
    """
    result: dict = {
        "installed": False,
        "version": None,
    }

    if not shutil.which("codex"):
        return result

    result["installed"] = True

    try:
        proc = subprocess.run(
            ["codex", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            shell=_IS_WINDOWS,
        )
        if proc.returncode == 0:
            result["version"] = proc.stdout.strip()
    except (subprocess.TimeoutExpired, OSError):
        pass

    return result


def get_claude_code_install_guide() -> str:
    """OS별 Claude Code CLI 설치 안내."""
    os_name = platform.system()

    guide = "[ Claude Code CLI 설치 안내 ]\n\n"

    if os_name == "Darwin":
        guide += (
            "1. npm install -g @anthropic-ai/claude-code\n"
            "   또는: brew install claude-code\n"
            "2. 인증: claude auth login\n"
            "3. 확인: claude --version\n"
        )
    else:
        guide += "1. npm install -g @anthropic-ai/claude-code\n2. 인증: claude auth login\n3. 확인: claude --version\n"

    guide += "\nClaude Pro/Max 구독이 필요합니다.\n문서: https://code.claude.com/\n"
    return guide


def get_codex_install_guide() -> str:
    """OS별 Codex CLI 설치 안내."""
    guide = "[ OpenAI Codex CLI 설치 안내 ]\n\n"
    guide += "1. npm install -g @openai/codex\n2. 처음 실행 시 로그인: codex\n3. 확인: codex --version\n"
    guide += "\nChatGPT Plus/Pro 구독이 필요합니다.\n문서: https://developers.openai.com/codex/cli/\n"
    return guide
