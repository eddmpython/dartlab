"""Header bar -- brand + provider/model/company display."""

from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static

from dartlab.cli.brand import CLR, CLR_ACCENT, CLR_MUTED


class _BrandLabel(Static):
    """Styled brand label with accent separator."""

    def render(self) -> Text:
        t = Text()
        t.append("DartLab", style=f"bold {CLR}")
        return t


class HeaderBar(Widget):
    """Minimal header: brand left, info right."""

    provider: reactive[str] = reactive("", layout=True)
    model: reactive[str] = reactive("", layout=True)
    stockCode: reactive[str] = reactive("", layout=True)

    def compose(self) -> ComposeResult:
        yield _BrandLabel(id="headerBrand")
        yield Static("", id="headerInfo")

    def watch_provider(self) -> None:
        self._updateInfo()

    def watch_model(self) -> None:
        self._updateInfo()

    def watch_stockCode(self) -> None:
        self._updateInfo()

    def _updateInfo(self) -> None:
        info = self.query_one("#headerInfo", Static)
        t = Text()
        parts = []
        if self.stockCode:
            parts.append(("stockCode", self.stockCode))
        if self.provider:
            parts.append(("provider", self.provider))
        if self.model:
            parts.append(("model", self.model))
        for i, (kind, val) in enumerate(parts):
            if i > 0:
                t.append(" | ", style=CLR_MUTED)
            if kind == "stockCode":
                t.append(val, style=f"bold {CLR_ACCENT}")
            else:
                t.append(val, style=CLR_MUTED)
        info.update(t)
