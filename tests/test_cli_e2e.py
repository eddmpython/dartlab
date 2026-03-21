"""CLI end-to-end smoke tests through a subprocess."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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
    assert "{show,search,statement,sections,profile,modules,ask,report,excel,collect,ai,status,setup,mcp}" in result.stdout
    assert "ui" not in result.stdout
    assert result.stderr == ""


def test_cli_version_contract():
    result = _run_cli("--version")

    assert result.returncode == 0
    assert result.stdout.startswith("dartlab ")
    assert result.stderr == ""


def test_cli_setup_contract():
    result = _run_cli("setup")

    assert result.returncode == 0
    assert "사용 가능한 provider" in result.stdout
    assert "dartlab setup codex" in result.stdout
    assert "claude-code" not in result.stdout
    assert result.stderr == ""


def test_cli_invalid_command_contract():
    result = _run_cli("nonexistent")

    assert result.returncode == 2
    assert "error:" in result.stderr
    assert "invalid choice" in result.stderr
