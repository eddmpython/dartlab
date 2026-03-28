"""Header bar -- provider/model/company display."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label


class HeaderBar(Widget):
    """Minimal header: brand left, info right."""

    provider: reactive[str] = reactive("", layout=True)
    model: reactive[str] = reactive("", layout=True)
    stockCode: reactive[str] = reactive("", layout=True)

    def compose(self) -> ComposeResult:
        yield Label("DartLab", id="headerBrand")
        yield Label("", id="headerInfo")

    def watch_provider(self) -> None:
        self._updateInfo()

    def watch_model(self) -> None:
        self._updateInfo()

    def watch_stockCode(self) -> None:
        self._updateInfo()

    def _updateInfo(self) -> None:
        info = self.query_one("#headerInfo", Label)
        parts = []
        if self.stockCode:
            parts.append(self.stockCode)
        if self.provider:
            parts.append(self.provider)
        if self.model:
            parts.append(self.model)
        info.update(" | ".join(parts) if parts else "")
