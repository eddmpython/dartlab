"""DartLab TUI -- full-screen Textual chat application."""

from __future__ import annotations

from typing import Any


def run(args: Any = None) -> int:
    """Entry point for `dartlab chat` TUI."""
    from dartlab.cli.tui.app import DartLabApp

    app = DartLabApp(args=args)
    app.run()
    return 0
