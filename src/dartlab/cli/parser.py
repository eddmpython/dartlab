"""Argument parser builder for DartLab CLI."""

from __future__ import annotations

import argparse
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as pkg_version

from dartlab.cli.context import DEPRECATED_ALIASES, CommandSpec
from dartlab.cli.services.runtime import load_command_module

COMMAND_SPECS = (
    # 데이터 조회
    CommandSpec("show", "dartlab.cli.commands.show"),
    CommandSpec("search", "dartlab.cli.commands.search"),
    CommandSpec("statement", "dartlab.cli.commands.statement"),
    CommandSpec("sections", "dartlab.cli.commands.sections"),
    CommandSpec("profile", "dartlab.cli.commands.profile"),
    CommandSpec("modules", "dartlab.cli.commands.modules"),
    # AI / 내보내기
    CommandSpec("ask", "dartlab.cli.commands.ask"),
    CommandSpec("report", "dartlab.cli.commands.report"),
    CommandSpec("excel", "dartlab.cli.commands.excel"),
    # 분석
    CommandSpec("review", "dartlab.cli.commands.review"),
    # 수집
    CommandSpec("collect", "dartlab.cli.commands.collect"),
    # 서버 / 설정
    CommandSpec("ai", "dartlab.cli.commands.ai"),
    CommandSpec("share", "dartlab.cli.commands.share"),
    CommandSpec("status", "dartlab.cli.commands.status"),
    CommandSpec("setup", "dartlab.cli.commands.setup"),
    # MCP
    CommandSpec("mcp", "dartlab.cli.commands.mcp"),
    # 플러그인
    CommandSpec("plugin", "dartlab.cli.commands.plugin"),
)


class DartLabArgumentParser(argparse.ArgumentParser):
    """Parser that exits with stable CLI usage codes."""

    def error(self, message):
        self.print_usage()
        raise SystemExit(f"{self.prog}: error: {message}")


def build_parser() -> argparse.ArgumentParser:
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
