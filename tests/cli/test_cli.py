"""CLI package tests."""

from __future__ import annotations

import re
from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.unit

from dartlab.cli.context import EXIT_INTERRUPTED, EXIT_RUNTIME, EXIT_USAGE
from dartlab.cli.main import main
from dartlab.cli.parser import buildParser


def test_build_parser_registers_all_commands():
    parser = buildParser()

    choices = parser._subparsers._group_actions[0].choices
    assert set(
        ["ask", "status", "setup", "ai", "excel", "profile", "sections", "statement", "show", "search"]
    ).issubset(choices.keys())
    assert "ui" not in choices


def test_parse_ask_options():
    parser = buildParser()

    args = parser.parse_args(["ask", "005930", "분석", "--runtime", "codex", "--include", "BS", "IS", "--stream"])

    assert args.command == "ask"
    assert args.query == ["005930", "분석"]
    assert args.runtime == "codex"
    assert args.include == ["BS", "IS"]
    assert args.stream is True


def test_main_without_command_prints_help(capsys):
    result = main([])

    captured = capsys.readouterr()
    assert result == 0
    assert "usage:" in captured.out
    # argparse의 usage 줄에서 서브커맨드 목록 확인 (reviewer는 하단 positional에만 표시)
    assert "show" in captured.out
    assert "search" in captured.out
    assert "ask" in captured.out
    assert "story" in captured.out
    assert "setup" in captured.out
    assert "mcp" in captured.out
    assert "plugin" in captured.out
    # 옛 `ui` 서브커맨드 제거 후 잔존 검사 — substring 'ui' (quickstart · guide 등) 가 아닌
    # 단독 토큰만 검출하도록 word boundary 사용.
    assert re.search(r"\bui\b", captured.out) is None


def test_main_invalid_command_returns_usage_code(capsys):
    result = main(["nope"])

    captured = capsys.readouterr()
    assert result == EXIT_USAGE
    assert "error:" in captured.err


def test_ask_proceeds_without_company(capsys):
    # --company 플래그가 없어도 설치형 agent runtime 경로로 진행한다.
    from dartlab.ai.contracts import TraceEvent

    def _fake_analyze(*a, **kw):
        yield TraceEvent("chunk", {"text": "test answer"})
        yield TraceEvent("done", {})

    with (
        patch("dartlab.cli.commands.ask.configureDartlab", return_value=MagicMock()),
        patch("dartlab.ai.kernel._askEvents", side_effect=_fake_analyze),
    ):
        result = main(["ask", "bad", "question"])

    captured = capsys.readouterr()
    assert result == 0
    assert "Agent runtime analysis" in captured.out
    assert "auth/model owned by local CLI" in captured.out


def test_ask_returns_non_zero_when_quality_done_is_rejected(capsys):
    from dartlab.ai.contracts import TraceEvent

    def _fake_analyze(*_args, **_kwargs):
        yield TraceEvent(
            "done",
            {
                "responseMeta": {
                    "finalEvent": "runtime_error",
                    "responseStatus": "failed",
                    "failureReason": "근거 셀 검증 실패",
                }
            },
        )

    with (
        patch("dartlab.cli.commands.ask.configureDartlab", return_value=MagicMock()),
        patch("dartlab.ai.kernel._askEvents", side_effect=_fake_analyze),
    ):
        result = main(["ask", "bad", "question"])

    captured = capsys.readouterr()
    assert result == 1
    assert "근거 셀 검증 실패" in captured.out


def test_excel_returns_non_zero_on_company_error(capsys):
    mock_dartlab = MagicMock()
    mock_dartlab.Company.side_effect = OSError("missing data")

    with patch.dict("sys.modules", {"dartlab": mock_dartlab}):
        result = main(["excel", "bad"])

    captured = capsys.readouterr()
    assert result == 1
    assert "오류" in captured.err


def test_parse_profile_options():
    parser = buildParser()

    args = parser.parse_args(["profile", "005930", "--facts"])

    assert args.command == "profile"
    assert args.company == "005930"
    assert args.facts is True


def test_parse_statement_options():
    parser = buildParser()

    args = parser.parse_args(["statement", "005930", "CIS"])

    assert args.command == "statement"
    assert args.company == "005930"
    assert args.name == "CIS"


@patch("dartlab.cli.commands.ask.run", side_effect=KeyboardInterrupt)
def test_main_maps_keyboard_interrupt_to_exit_code(_):
    result = main(["ask", "005930", "질문"])

    assert result == EXIT_INTERRUPTED


@patch("dartlab.cli.commands.ask.run", side_effect=RuntimeError("boom"))
def test_main_maps_unexpected_error_to_runtime_exit(_, capsys):
    result = main(["ask", "005930", "질문"])

    captured = capsys.readouterr()
    assert result == EXIT_RUNTIME
    assert "boom" in captured.err


def test_version_flag_prints_version(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])

    captured = capsys.readouterr()
    assert exc.value.code == 0
    assert "dartlab " in captured.out
