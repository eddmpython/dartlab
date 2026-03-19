"""CLI package tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from dartlab.cli.context import EXIT_INTERRUPTED, EXIT_RUNTIME, EXIT_USAGE
from dartlab.cli.main import main
from dartlab.cli.parser import build_parser


def test_build_parser_registers_all_commands():
    parser = build_parser()

    choices = parser._subparsers._group_actions[0].choices
    assert set(
        ["ask", "status", "setup", "ai", "excel", "profile", "sections", "statement", "show", "search", "ui"]
    ).issubset(choices.keys())
    assert choices["ui"].help == "==SUPPRESS=="


def test_parse_ask_options():
    parser = build_parser()

    args = parser.parse_args(["ask", "005930", "분석", "--provider", "codex", "--include", "BS", "IS", "--stream"])

    assert args.command == "ask"
    assert args.company == "005930"
    assert args.provider == "codex"
    assert args.include == ["BS", "IS"]
    assert args.stream is True


def test_parse_ui_alias():
    parser = build_parser()

    args = parser.parse_args(["ui", "--port", "9000"])

    assert args.command == "ui"
    assert args.port == 9000
    assert args.cli_alias == "ui"


@patch("dartlab.cli.commands.ai.run", return_value=0)
def test_main_dispatches_to_ui_handler(mock_run):
    result = main(["ui", "--no-browser"])

    assert result == 0
    mock_run.assert_called_once()
    assert mock_run.call_args[0][0].cli_alias == "ui"


def test_main_without_command_prints_help(capsys):
    result = main([])

    captured = capsys.readouterr()
    assert result == 0
    assert "usage:" in captured.out
    assert "{show,search,statement,sections,profile,ask,excel,ai,status,setup,mcp}" in captured.out
    assert "ui" not in captured.out


def test_main_invalid_command_returns_usage_code(capsys):
    result = main(["nope"])

    captured = capsys.readouterr()
    assert result == EXIT_USAGE
    assert "error:" in captured.err


def test_ask_returns_non_zero_on_company_error(capsys):
    mock_dartlab = MagicMock()
    mock_dartlab.Company.side_effect = ValueError("bad company")
    mock_dartlab.llm = MagicMock()

    with patch.dict("sys.modules", {"dartlab": mock_dartlab}):
        result = main(["ask", "bad", "question"])

    captured = capsys.readouterr()
    assert result == 1
    assert "오류: bad company" in captured.err


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


def test_ui_alias_prints_deprecation_message(capsys):
    with patch("dartlab.cli.commands.ai._check_built_ui", return_value=False):
        result = main(["ui"])

    captured = capsys.readouterr()
    assert result == 0
    assert "dartlab ai" in captured.err


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
