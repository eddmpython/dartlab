"""CLI end-to-end smoke tests through a subprocess."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    pythonpath = str(ROOT / "src")
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = pythonpath if not existing else f"{pythonpath}{os.pathsep}{existing}"
    env["DARTLAB_NO_BROWSER"] = "1"
    return subprocess.run(
        [sys.executable, "-m", "dartlab.cli.main", *args],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        encoding="utf-8",
        errors="replace",
    )


def test_cli_help_contract():
    result = _run_cli("--help")

    assert result.returncode == 0
    assert "DartLab" in result.stdout
    # 핵심 명령이 모두 존재하는지 확인 (새 명령 추가 시 깨지지 않도록 개별 체크)
    for cmd in ("show", "search", "ask", "excel", "ai", "status", "setup", "mcp"):
        assert cmd in result.stdout, f"핵심 명령 '{cmd}'이 help에 없음"
    # 옛 `ui` 서브커맨드 잔존 검사 — quickstart · guide 등 substring false positive 방지.
    assert re.search(r"\bui\b", result.stdout) is None
    # stderr 의 SyntaxWarning 류 무시 (prompts.py escape sequence 등 cosmetic warning)
    assert "Error" not in result.stderr and "Traceback" not in result.stderr


def test_cli_version_contract():
    result = _run_cli("--version")

    assert result.returncode == 0
    assert result.stdout.startswith("dartlab ")
    assert "Error" not in result.stderr and "Traceback" not in result.stderr


def test_cli_setup_contract():
    result = _run_cli("setup")

    assert result.returncode == 0
    assert "데이터 수집" in result.stdout
    assert "dartlab ask" in result.stdout
    assert "dartlab agent status" in result.stdout
    assert "claude-code" not in result.stdout
    assert "Error" not in result.stderr and "Traceback" not in result.stderr


def test_cli_invalid_command_contract():
    result = _run_cli("nonexistent")

    assert result.returncode == 2
    assert "error:" in result.stderr
    assert "invalid choice" in result.stderr
