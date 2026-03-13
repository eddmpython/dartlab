"""Argument parser builder for DartLab CLI."""

from __future__ import annotations

import argparse
from importlib.metadata import version as pkg_version

from dartlab.cli.context import DEPRECATED_ALIASES, CommandSpec
from dartlab.cli.services.runtime import load_command_module

COMMAND_SPECS = (
    CommandSpec("ask", "dartlab.cli.commands.ask"),
    CommandSpec("status", "dartlab.cli.commands.status"),
    CommandSpec("setup", "dartlab.cli.commands.setup"),
    CommandSpec("ai", "dartlab.cli.commands.ai"),
    CommandSpec("excel", "dartlab.cli.commands.excel"),
    CommandSpec("profile", "dartlab.cli.commands.profile"),
    CommandSpec("sections", "dartlab.cli.commands.sections"),
    CommandSpec("statement", "dartlab.cli.commands.statement"),
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
    except Exception:
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
