"""Status bar -- 1-line bottom bar."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static


class StatusBar(Widget):
    """Bottom status bar."""

    companies: reactive[str] = reactive("", layout=True)
    tokens: reactive[int] = reactive(0)
    cost: reactive[float] = reactive(0.0)

    def compose(self) -> ComposeResult:
        """Build status bar."""
        yield Static(id="status-companies")
        yield Static(id="status-right")

    def on_mount(self) -> None:
        """Initialize."""
        self._refresh()

    def watch_companies(self) -> None:
        self._refresh()

    def watch_tokens(self) -> None:
        self._refresh()

    def watch_cost(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        """Rebuild status bar content."""
        left = self.query_one("#status-companies", Static)
        right = self.query_one("#status-right", Static)

        leftParts = []
        if self.companies:
            leftParts.append(f"[bold #cdd6f4]{self.companies}[/]")
        leftParts.append(
            "[#6c7086]/[/][#45475a] commands  [/]"
            "[#6c7086]^C[/][#45475a] cancel  [/]"
            "[#6c7086]^D[/][#45475a] exit[/]"
        )
        left.update(" [#313244]|[/] ".join(leftParts))

        rightParts = []
        if self.tokens > 0:
            rightParts.append(f"[#a6adc8]{self.tokens:,}[/] [#45475a]tok[/]")
        if self.cost > 0:
            rightParts.append(f"[#a6adc8]${self.cost:.3f}[/]")
        right.update("  ".join(rightParts))
