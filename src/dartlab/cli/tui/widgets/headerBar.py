"""Header bar -- elia AppHeader pattern."""

from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label


class HeaderBar(Widget):
    """App header (elia pattern): title left, model right."""

    provider: reactive[str] = reactive("", layout=True)
    model: reactive[str] = reactive("", layout=True)
    stockCode: reactive[str] = reactive("", layout=True)

    def compose(self) -> ComposeResult:
        """Build header (elia pattern: Label, not Static)."""
        yield Label(Text("DartLab", style="bold"), id="header-brand")
        yield Label("", id="header-info")

    def watch_provider(self) -> None:
        self._updateInfo()

    def watch_model(self) -> None:
        self._updateInfo()

    def watch_stockCode(self) -> None:
        self._updateInfo()

    def _updateInfo(self) -> None:
        """Update right-side info (elia pattern: dim text)."""
        info = self.query_one("#header-info", Label)
        parts = []
        if self.stockCode:
            parts.append(self.stockCode)
        if self.provider:
            parts.append(self.provider)
        if self.model:
            parts.append(self.model)
        info.update(" | ".join(parts) if parts else "")
