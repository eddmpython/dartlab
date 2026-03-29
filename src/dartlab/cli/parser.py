"""Argument parser builder for DartLab CLI."""

from __future__ import annotations

import argparse
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as pkg_version

from dartlab.cli.context import DEPRECATED_ALIASES, CommandSpec
from dartlab.cli.services.runtime import load_command_module

COMMAND_SPECS = (
    # 데이터 조회
    CommandSpec("show", "dartlab.cli.commands.show", "topic 기반 데이터 조회"),
    CommandSpec("search", "dartlab.cli.commands.search", "종목코드/회사명 검색"),
    CommandSpec("statement", "dartlab.cli.commands.statement", "재무제표 출력 (BS/IS/CIS/CF/SCE)"),
    CommandSpec("sections", "dartlab.cli.commands.sections", "docs 수평화 sections 출력"),
    CommandSpec("profile", "dartlab.cli.commands.profile", "Company index/facts 출력"),
    CommandSpec("modules", "dartlab.cli.commands.modules", "사용 가능한 데이터 모듈 목록"),
    # AI / 내보내기
    CommandSpec("ask", "dartlab.cli.commands.ask", "자연어 원스톱 AI 분석"),
    CommandSpec("chat", "dartlab.cli.commands.chat", "대화형 AI 분석 REPL"),
    CommandSpec("report", "dartlab.cli.commands.report", "Markdown 분석 보고서 생성"),
    CommandSpec("excel", "dartlab.cli.commands.excel", "기업 데이터 Excel 내보내기"),
    # 분석
    CommandSpec("review", "dartlab.cli.commands.review", "기업 분석 검토서 (데이터/AI)"),
    # 수집/갱신
    CommandSpec("collect", "dartlab.cli.commands.collect", "DART/EDGAR 데이터 수집"),
    CommandSpec("update", "dartlab.cli.commands.update", "로컬 데이터를 HuggingFace 최신으로 갱신"),
    # 서버 / 설정
    CommandSpec("ai", "dartlab.cli.commands.ai", "AI 분석 웹 인터페이스 실행"),
    CommandSpec("share", "dartlab.cli.commands.share", "터널로 로컬 서버 외부 공유"),
    CommandSpec("status", "dartlab.cli.commands.status", "LLM 연결 상태 확인"),
    CommandSpec("setup", "dartlab.cli.commands.setup", "LLM provider/API 키 설정"),
    # MCP
    CommandSpec("mcp", "dartlab.cli.commands.mcp", "MCP 서버 실행 (stdio)"),
    # 플러그인
    CommandSpec("plugin", "dartlab.cli.commands.plugin", "플러그인 관리 (list/create)"),
)


class DartLabArgumentParser(argparse.ArgumentParser):
    """Parser that exits with stable CLI usage codes."""

    def error(self, message):
        self.print_usage()
        raise SystemExit(f"{self.prog}: error: {message}")


def build_parser() -> argparse.ArgumentParser:
    """CLI ArgumentParser 생성 및 서브커맨드 등록."""
    parser = DartLabArgumentParser(
        prog="dartlab",
        description="DartLab — DART 공시 데이터 + LLM 분석",
    )
    try:
        version = pkg_version("dartlab")
    except PackageNotFoundError:
        version = "0.0.0"
    parser.add_argument("--version", action="version", version=f"%(prog)s {version}")
    visible_commands = ",".join(spec.name for spec in COMMAND_SPECS)
    subparsers = parser.add_subparsers(dest="command", metavar=f"{{{visible_commands}}}")

    for spec in COMMAND_SPECS:
        command_module = load_command_module(spec)
        command_module.configure_parser(subparsers)

    for alias, target in DEPRECATED_ALIASES.items():
        if alias in subparsers.choices:
            subparsers.choices[alias].help = argparse.SUPPRESS

    return parser
