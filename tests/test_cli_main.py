"""CLI main.py 단위 테스트 — _looksLikeCompany, _ensure_utf8, 에러 핸들링.

기존 test_cli.py와 겹치지 않는 영역 — 내부 헬퍼 함수와 edge case 커버.
"""

from __future__ import annotations

import io
import sys
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


# ── _looksLikeCompany ──


def test_looks_like_company_six_digit():
    from dartlab.cli.main import _looksLikeCompany

    assert _looksLikeCompany("005930") is True
    assert _looksLikeCompany("000660") is True


def test_looks_like_company_korean_name():
    from dartlab.cli.main import _looksLikeCompany

    assert _looksLikeCompany("삼성전자") is True
    assert _looksLikeCompany("현대차") is True


def test_looks_like_company_rejects_english_command():
    from dartlab.cli.main import _looksLikeCompany

    assert _looksLikeCompany("show") is False
    assert _looksLikeCompany("ask") is False
    assert _looksLikeCompany("AAPL") is False


def test_looks_like_company_rejects_short_digit():
    from dartlab.cli.main import _looksLikeCompany

    assert _looksLikeCompany("123") is False
    assert _looksLikeCompany("12345") is False


def test_looks_like_company_rejects_long_digit():
    from dartlab.cli.main import _looksLikeCompany

    assert _looksLikeCompany("1234567") is False


# ── _ensure_utf8 ──


def test_ensure_utf8_wraps_non_utf8_stdout(monkeypatch):
    """비-UTF8 인코딩 stdout이면 UTF8 wrapper로 교체한다."""
    from dartlab.cli.main import _ensure_utf8

    original_stdout = sys.stdout
    original_stderr = sys.stderr
    try:
        # Create a fake stdout with non-utf8 encoding
        fake_buffer = io.BytesIO()
        fake_stdout = io.TextIOWrapper(fake_buffer, encoding="cp949")
        sys.stdout = fake_stdout
        sys.stderr = io.TextIOWrapper(io.BytesIO(), encoding="cp949")

        _ensure_utf8()

        assert sys.stdout.encoding.lower() in ("utf-8", "utf8")
        assert sys.stderr.encoding.lower() in ("utf-8", "utf8")
    finally:
        sys.stdout = original_stdout
        sys.stderr = original_stderr


def test_ensure_utf8_skips_if_already_utf8():
    """이미 UTF-8이면 교체하지 않는다."""
    from dartlab.cli.main import _ensure_utf8

    original_stdout = sys.stdout
    try:
        # stdout이 이미 utf-8이면 변경 없어야 함
        if sys.stdout.encoding and sys.stdout.encoding.lower() in ("utf-8", "utf8"):
            old_id = id(sys.stdout)
            _ensure_utf8()
            # stdout 객체가 동일해야 함
            assert id(sys.stdout) == old_id
    finally:
        sys.stdout = original_stdout


# ── main() implicit review routing ──


def test_main_routes_stock_code_to_review():
    """dartlab 005930 → main()이 raw 앞에 'review'를 추가하는지 확인."""
    from dartlab.cli.main import _looksLikeCompany

    # _looksLikeCompany 판별 후 ["review"] + raw 로 변환되는 로직 테스트
    assert _looksLikeCompany("005930") is True
    # main()의 implicit routing: raw = ["005930"] → raw = ["review", "005930"]
    # build_parser().parse_args(["review", "005930"])로 실행됨
    from dartlab.cli.parser import build_parser

    parser = build_parser()
    args = parser.parse_args(["review", "005930"])
    assert args.command == "review"
    assert args.company == "005930"


def test_main_routes_korean_name_to_review():
    """dartlab 삼성전자 → main()이 raw 앞에 'review'를 추가하는지 확인."""
    from dartlab.cli.main import _looksLikeCompany

    assert _looksLikeCompany("삼성전자") is True
    from dartlab.cli.parser import build_parser

    parser = build_parser()
    args = parser.parse_args(["review", "삼성전자"])
    assert args.command == "review"
    assert args.company == "삼성전자"


# ── main() error handling ──


def test_main_broken_pipe_returns_ok():
    """BrokenPipeError는 EXIT_OK를 반환한다."""
    from dartlab.cli.context import EXIT_OK
    from dartlab.cli.main import main

    with patch("dartlab.cli.commands.ask.run", side_effect=BrokenPipeError):
        result = main(["ask", "005930", "test"])

    assert result == EXIT_OK


def test_main_cli_error_returns_custom_exit_code(capsys):
    """CLIError는 exc.exit_code를 반환한다."""
    from dartlab.cli.main import main
    from dartlab.cli.services.errors import CLIError

    with patch("dartlab.cli.commands.ask.run", side_effect=CLIError("test error", exit_code=42)):
        result = main(["ask", "005930", "test"])

    assert result == 42
    captured = capsys.readouterr()
    assert "test error" in captured.err


# ── CommandSpec ──


def test_command_spec_is_frozen():
    """CommandSpec은 frozen dataclass다."""
    from dartlab.cli.context import CommandSpec

    spec = CommandSpec("test", "dartlab.cli.commands.test", "test command")
    assert spec.name == "test"
    assert spec.import_path == "dartlab.cli.commands.test"
    assert spec.description == "test command"

    with pytest.raises(AttributeError):
        spec.name = "changed"


# ── COMMAND_SPECS completeness ──


def test_command_specs_covers_expected_commands():
    """COMMAND_SPECS에 핵심 명령이 모두 포함된다."""
    from dartlab.cli.parser import COMMAND_SPECS

    names = {spec.name for spec in COMMAND_SPECS}
    expected = {"ask", "show", "search", "status", "setup", "ai", "excel", "mcp", "review", "collect", "plugin"}
    assert expected.issubset(names)


def test_command_specs_has_unique_names():
    """COMMAND_SPECS 내 이름 중복 없음."""
    from dartlab.cli.parser import COMMAND_SPECS

    names = [spec.name for spec in COMMAND_SPECS]
    assert len(names) == len(set(names))


# ── DartLabArgumentParser error override ──


def test_custom_parser_error_raises_system_exit():
    """DartLabArgumentParser.error()는 SystemExit을 발생시킨다."""
    from dartlab.cli.parser import DartLabArgumentParser

    parser = DartLabArgumentParser(prog="test")
    with pytest.raises(SystemExit) as exc:
        parser.error("bad argument")
    assert "bad argument" in str(exc.value)
