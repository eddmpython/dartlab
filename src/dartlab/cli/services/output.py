"""Console output helpers for CLI commands."""

from __future__ import annotations

import sys


def print_error(message: str) -> None:
    print(f"오류: {message}", file=sys.stderr)


def print_info(message: str = "") -> None:
    print(message)


def print_warning(message: str) -> None:
    print(f"경고: {message}", file=sys.stderr)
