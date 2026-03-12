"""CLI error types."""

from __future__ import annotations

from dartlab.cli.context import EXIT_RUNTIME


class CLIError(RuntimeError):
    """User-facing CLI error with an explicit exit code."""

    def __init__(self, message: str, exit_code: int = EXIT_RUNTIME):
        super().__init__(message)
        self.exit_code = exit_code
