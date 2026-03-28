"""Response status indicator -- elia agent_is_typing.py pattern."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import Label, LoadingIndicator


class ResponseStatus(Vertical):
    """Thinking/responding overlay (elia pattern)."""

    message: reactive[str] = reactive("Thinking", recompose=True)

    def compose(self) -> ComposeResult:
        """Label + LoadingIndicator."""
        yield Label(f" {self.message}")
        yield LoadingIndicator()

    def setAwaiting(self) -> None:
        """LLM call pending."""
        self.message = "Thinking"
        self.remove_class("-responding")
        self.add_class("-awaiting")

    def setResponding(self) -> None:
        """LLM streaming active."""
        self.message = "Responding"
        self.remove_class("-awaiting")
        self.add_class("-responding")

    def hide(self) -> None:
        """Remove visible state."""
        self.remove_class("-awaiting")
        self.remove_class("-responding")
