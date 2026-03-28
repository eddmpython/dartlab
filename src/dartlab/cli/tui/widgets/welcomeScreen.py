"""Welcome screen -- centered brand logo."""

from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Center, Vertical
from textual.widget import Widget
from textual.widgets import Static

_LOGO = """\
██████╗  █████╗ ██████╗ ████████╗██╗      █████╗ ██████╗
██╔══██╗██╔══██╗██╔══██╗╚══██╔══╝██║     ██╔══██╗██╔══██╗
██║  ██║███████║██████╔╝   ██║   ██║     ███████║██████╔╝
██║  ██║██╔══██║██╔══██╗   ██║   ██║     ██╔══██║██╔══██╗
██████╔╝██║  ██║██║  ██║   ██║   ███████╗██║  ██║██████╔╝
╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚═════╝"""

_LOGO_SMALL = """\
    ____             __  __          __
   / __ \\____ ______/ /_/ /   ____ _/ /_
  / / / / __ `/ ___/ __/ /   / __ `/ __ \\
 / /_/ / /_/ / /  / /_/ /___/ /_/ / /_/ /
/_____/\\__,_/_/   \\__/_____/\\__,_/_.___/"""


class _Logo(Static):
    def render(self) -> Text:
        try:
            w = self.screen.size.width
        except Exception:
            w = 100
        logo = _LOGO if w >= 70 else _LOGO_SMALL
        text = Text()
        for i, line in enumerate(logo.split("\n")):
            if i > 0:
                text.append("\n")
            text.append(line, style="bold #c0392b")
        return text


class WelcomeScreen(Widget):
    """Startup screen."""

    def __init__(self, provider: str = "", model: str = "", **kwargs) -> None:
        super().__init__(**kwargs)
        self._provider = provider
        self._model = model

    def compose(self) -> ComposeResult:
        with Center():
            with Vertical(id="welcomeOuter"):
                yield _Logo(id="welcomeBrand")
                yield Static("DART / EDGAR AI Analysis", id="welcomeTagline")

                parts: list[str] = []
                if self._provider:
                    parts.append(self._provider)
                if self._model:
                    parts.append(self._model)
                if parts:
                    yield Static(" | ".join(parts), id="welcomeProviderInfo")

                yield Static(
                    "Type / for commands  |  Enter to send",
                    id="welcomeShortcuts",
                )

                if not self._provider:
                    yield Static(
                        "No AI provider detected -- run dartlab setup",
                        id="welcomeSetupHint",
                    )
