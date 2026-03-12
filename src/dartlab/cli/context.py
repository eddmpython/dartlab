"""Shared CLI constants and metadata."""

from __future__ import annotations

from dataclasses import dataclass

PROVIDERS = ["codex", "claude-code", "ollama", "openai", "claude", "custom"]
CLI_PROVIDERS = ["codex", "claude-code", "ollama"]

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_RUNTIME = 1
EXIT_INTERRUPTED = 130
DEPRECATED_ALIASES = {"ui": "ai"}


@dataclass(frozen=True)
class CommandSpec:
    name: str
    import_path: str
