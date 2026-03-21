"""CLI package tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.unit

from dartlab.cli.context import EXIT_INTERRUPTED, EXIT_RUNTIME, EXIT_USAGE
from dartlab.cli.main import main
from dartlab.cli.parser import build_parser


def test_build_parser_registers_all_commands():
    parser = build_parser()

    choices = parser._subparsers._group_actions[0].choices
    assert set(
        ["ask", "status", "setup", "ai", "excel", "profile", "sections", "statement", "show", "search"]
    ).issubset(choices.keys())
    assert "ui" not in choices


def test_parse_ask_options():
    parser = build_parser()

    args = parser.parse_args(["ask", "005930", "분석", "--provider", "codex", "--include", "BS", "IS", "--stream"])

    assert args.command == "ask"
    assert args.query == ["005930", "분석"]
    assert args.provider == "codex"
    assert args.include == ["BS", "IS"]
    assert args.stream is True


def test_main_without_command_prints_help(capsys):
    result = main([])

    captured = capsys.readouterr()
    assert result == 0
    assert "usage:" in captured.out
    assert (
        "{show,search,statement,sections,profile,modules,ask,report,excel,collect,ai,status,setup,mcp}" in captured.out
    )
    assert "ui" not in captured.out


def test_main_invalid_command_returns_usage_code(capsys):
    result = main(["nope"])

    captured = capsys.readouterr()
    assert result == EXIT_USAGE
    assert "error:" in captured.err


def test_ask_returns_non_zero_on_company_error(capsys):
    # resolve_from_text가 종목을 못 찾으면 CLIError → exit code 1
    with patch("dartlab.core.resolve.resolve_from_text", return_value=(None, "bad question")):
        result = main(["ask", "bad", "question"])

    captured = capsys.readouterr()
    assert result == 1
    assert "종목을 찾을 수 없습니다" in captured.err


def test_excel_returns_non_zero_on_company_error(capsys):
    mock_dartlab = MagicMock()
    mock_dartlab.Company.side_effect = OSError("missing data")

    with patch.dict("sys.modules", {"dartlab": mock_dartlab}):
        result = main(["excel", "bad"])

    captured = capsys.readouterr()
    assert result == 1
    assert "오류: missing data" in captured.err


def test_parse_profile_options():
    parser = build_parser()

    args = parser.parse_args(["profile", "005930", "--facts"])

    assert args.command == "profile"
    assert args.company == "005930"
    assert args.facts is True


def test_parse_statement_options():
    parser = build_parser()

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
    assert "예상하지 못한 오류" in captured.err


def test_version_flag_prints_version(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])

    captured = capsys.readouterr()
    assert exc.value.code == 0
    assert "dartlab " in captured.out
