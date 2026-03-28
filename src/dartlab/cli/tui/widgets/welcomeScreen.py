"""Welcome screen -- large brand logo, centered (Gemini CLI pattern)."""

from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Center, Vertical
from textual.widget import Widget
from textual.widgets import Static

# ansi_shadow font, hardcoded (no pyfiglet runtime dependency)
# 57 chars wide, 6 lines tall -- fits 80-col terminals
_LOGO_LARGE = """\
██████╗  █████╗ ██████╗ ████████╗██╗      █████╗ ██████╗
██╔══██╗██╔══██╗██╔══██╗╚══██╔══╝██║     ██╔══██╗██╔══██╗
██║  ██║███████║██████╔╝   ██║   ██║     ███████║██████╔╝
██║  ██║██╔══██║██╔══██╗   ██║   ██║     ██╔══██║██╔══██╗
██████╔╝██║  ██║██║  ██║   ██║   ███████╗██║  ██║██████╔╝
╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚═════╝"""

# slant font fallback for narrow terminals (41 chars wide)
_LOGO_SMALL = """\
    ____             __  __          __
   / __ \\____ ______/ /_/ /   ____ _/ /_
  / / / / __ `/ ___/ __/ /   / __ `/ __ \\
 / /_/ / /_/ / /  / /_/ /___/ /_/ / /_/ /
/_____/\\__,_/_/   \\__/_____/\\__,_/_.___/"""


class _LogoWidget(Static):
    """Logo widget -- Rich Text for safe rendering."""

    def render(self) -> Text:
        """Pick logo size based on available width."""
        try:
            w = self.screen.size.width
        except Exception:
            w = 100
        logo = _LOGO_LARGE if w >= 70 else _LOGO_SMALL
        text = Text()
        for i, line in enumerate(logo.split("\n")):
            if i > 0:
                text.append("\n")
            text.append(line, style="bold #c0392b")
        return text


class WelcomeScreen(Widget):
    """Startup screen with large brand logo (Gemini CLI pattern)."""

    def __init__(
        self,
        provider: str = "",
        model: str = "",
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._provider = provider
        self._model = model

    def compose(self) -> ComposeResult:
        """Build welcome card."""
        with Center():
            with Vertical(id="welcome-outer"):
                yield _LogoWidget(id="welcome-brand")

                yield Static(
                    "DART / EDGAR  AI Analysis",
                    id="welcome-tagline",
                )

                parts: list[str] = []
                if self._provider:
                    parts.append(self._provider)
                if self._model:
                    parts.append(self._model)
                if parts:
                    yield Static(
                        " | ".join(parts),
                        id="welcome-provider-info",
                    )

                yield Static(
                    "Type / for commands  |  Enter to send",
                    id="welcome-shortcuts",
                )

                if not self._provider:
                    yield Static(
                        "No AI provider detected -- run dartlab setup",
                        id="welcome-setup-hint",
                    )
