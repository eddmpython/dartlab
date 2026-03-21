"""Provider helpers shared across CLI commands."""

from __future__ import annotations


def detect_provider() -> str:
    """Return the first available provider (smart detection)."""
    from dartlab.core.ai.detect import auto_detect_provider

    return auto_detect_provider() or "ollama"
