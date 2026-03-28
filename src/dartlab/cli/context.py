"""Shared CLI constants and metadata."""

from __future__ import annotations

from dataclasses import dataclass

from dartlab.core.ai import cli_provider_choices, provider_choices

PROVIDERS = provider_choices()
CLI_PROVIDERS = cli_provider_choices()

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_RUNTIME = 1
EXIT_INTERRUPTED = 130
DEPRECATED_ALIASES: dict[str, str] = {}


@dataclass(frozen=True)
class CommandSpec:
    """CLI 서브커맨드 메타데이터."""

    name: str
    import_path: str
    description: str = ""
