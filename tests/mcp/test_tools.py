"""MCP 부속 — installMcpConfig / _MCP_INSTRUCTIONS / cli config 출력 검증.

0.10 부터 33 generated 도구 + _executeTool if/elif + _fmt / _fmtDict / _cache / _getCompany 가
모두 폐기되어 해당 mock 테스트는 제거되었다. canonical dispatch 검증은 test_mcp.py 가 담당.
"""

from __future__ import annotations

import json

import pytest

pytestmark = pytest.mark.unit


# ── installMcpConfig ──


def test_install_mcp_config_creates_file(tmp_path):
    """이슈 #28 follow-up: command='dartlab' entry point 직접 호출 (Microsoft Store Python ENOENT 회피)."""
    from dartlab.mcp import installMcpConfig

    result = installMcpConfig(str(tmp_path))
    assert "생성 완료" in result

    mcp_file = tmp_path / ".mcp.json"
    assert mcp_file.exists()
    config = json.loads(mcp_file.read_text(encoding="utf-8"))
    assert "dartlab" in config["mcpServers"]
    assert config["mcpServers"]["dartlab"]["command"] == "dartlab"
    assert config["mcpServers"]["dartlab"]["args"] == ["mcp"]
    assert config["mcpServers"]["dartlab"]["env"]["PYTHONUNBUFFERED"] == "1"
    assert config["mcpServers"]["dartlab"]["env"]["PYTHONUTF8"] == "1"


def test_install_mcp_config_skips_if_exists(tmp_path):
    mcp_file = tmp_path / ".mcp.json"
    existing = {"mcpServers": {"dartlab": {"command": "existing"}}}
    mcp_file.write_text(json.dumps(existing), encoding="utf-8")

    from dartlab.mcp import installMcpConfig

    result = installMcpConfig(str(tmp_path))
    assert "이미 등록됨" in result

    config = json.loads(mcp_file.read_text(encoding="utf-8"))
    assert config["mcpServers"]["dartlab"]["command"] == "existing"


def test_install_mcp_config_merges_with_existing(tmp_path):
    """기존 .mcp.json 에 다른 서버가 있으면 dartlab 만 추가한다."""
    mcp_file = tmp_path / ".mcp.json"
    existing = {"mcpServers": {"other": {"command": "other_cmd"}}}
    mcp_file.write_text(json.dumps(existing), encoding="utf-8")

    from dartlab.mcp import installMcpConfig

    result = installMcpConfig(str(tmp_path))
    assert "생성 완료" in result

    config = json.loads(mcp_file.read_text(encoding="utf-8"))
    assert "other" in config["mcpServers"]
    assert "dartlab" in config["mcpServers"]


# ── cli config print ──


def test_cli_mcp_config_uses_dartlab_entry_point(capsys):
    """이슈 #28 follow-up: 1 순위 = command='dartlab' entry point. python -m 은 fallback."""
    from dartlab.cli.commands.mcp import _printConfig

    _printConfig("claude-code")
    out = capsys.readouterr().out

    # 1 순위 — entry point
    assert '"command": "dartlab"' in out
    assert '"mcp"' in out
    # fallback 도 함께 노출 (python -m)
    assert '"command": "python"' in out
    assert "Microsoft Store Python" in out


def test_cli_mcp_config_claude_desktop(capsys):
    """claude-desktop 출력은 README 인라인 대상 — entry point + fallback + PYTHONUNBUFFERED."""
    from dartlab.cli.commands.mcp import _printConfig

    _printConfig("claude-desktop")
    out = capsys.readouterr().out

    assert '"command": "dartlab"' in out
    assert "PYTHONUNBUFFERED" in out
    assert "PYTHONUTF8" in out
    assert "Microsoft Store Python" in out
    # fallback 도 노출
    assert '"command": "python"' in out


# ── _MCP_INSTRUCTIONS ──


def test_mcp_instructions_contains_key_info():
    """지침은 정체성과 첫 진입 도구를 담는다.

    옛 버전은 `RunPython` 이 담기는 것까지 고정했다. 그 도구는 실서비스 `agent` 프로필에서
    광고되지 않으므로 그 단언이 오히려 드리프트를 붙잡아 두고 있었다. 프로필별 정합은
    `test_brokerSurfaceCoherence.py` 가 전담한다.
    """
    from dartlab.mcp import _MCP_INSTRUCTIONS

    assert "설치형 agent CLI" in _MCP_INSTRUCTIONS
    assert "ReadSkill" in _MCP_INSTRUCTIONS
    assert "EngineCall" in _MCP_INSTRUCTIONS


def test_mcp_instructions_signals_breaking_change():
    """옛 generated 도구가 폐기되었다는 안내가 instructions 에 남아 있다."""
    from dartlab.mcp import _MCP_INSTRUCTIONS

    assert "companyAnalysis" in _MCP_INSTRUCTIONS
    assert "폐기" in _MCP_INSTRUCTIONS
