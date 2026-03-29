"""Prompt input widget for chat TUI."""

from __future__ import annotations

from dataclasses import dataclass

from textual import events, on
from textual.binding import Binding
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import TextArea


class Prompt(TextArea):
    """Chat input (Enter to submit, Shift+Enter for newline)."""

    DEFAULT_CSS = """
    Prompt {
        dock: bottom;
        width: 1fr;
        height: auto;
        min-height: 2;
        max-height: 8;
        border: none;
        padding: 0 1;
        background: $surface;
    }
    Prompt:focus {
        border: none;
    }
    Prompt.-blocked {
        opacity: 0.4;
    }
    Prompt .text-area--cursor-line {
        background: transparent;
    }
    Prompt .text-area--cursor-gutter {
        background: transparent;
    }
    """

    BINDINGS = [
        Binding("ctrl+shift+v", "paste", "Paste", show=False),
        Binding("ctrl+up", "historyBack", "History back", show=False),
        Binding("ctrl+down", "historyForward", "History forward", show=False),
    ]

    @dataclass
    class Submitted(Message):
        """User submitted input."""

        value: str

    disabled: reactive[bool] = reactive(False)

    def __init__(self, **kwargs) -> None:
        super().__init__(
            language=None,
            show_line_numbers=False,
            soft_wrap=True,
            tab_behavior="focus",
            **kwargs,
        )
        self._inputHistory: list[str] = []
        self._historyIdx: int = -1
        self._navigating: bool = False

    @on(TextArea.Changed)
    def _onChanged(self, event: TextArea.Changed) -> None:
        if not self._navigating:
            self._historyIdx = -1
        self._adjustHeight()

    def _adjustHeight(self) -> None:
        """Grow height to fit content, within min/max bounds."""
        lineCount = self.document.line_count
        # +1 for cursor row padding
        desired = max(2, lineCount + 1)
        clamped = min(desired, 8)
        self.styles.height = clamped

    def watch_disabled(self, value: bool) -> None:
        self.set_class(value, "-blocked")

    def on_focus(self) -> None:
        self.add_class("-focused")

    def on_blur(self) -> None:
        self.remove_class("-focused")

    async def _on_key(self, event: events.Key) -> None:
        if self.disabled and event.key not in {"ctrl+c", "ctrl+d"}:
            self.app.bell()
            event.stop()
            event.prevent_default()
            return

        key = event.key

        # Enter = submit
        if key == "enter":
            event.stop()
            event.prevent_default()
            text = self.text.strip()
            if text:
                self._inputHistory.append(text)
                self._historyIdx = -1
                self.clear()
                self.styles.height = 2
                self.post_message(Prompt.Submitted(value=text))
            return

        # Shift+Enter = newline
        if key == "shift+enter":
            event.stop()
            event.prevent_default()
            self.insert("\n")
            return

        # Escape = clear input
        if key == "escape":
            event.stop()
            event.prevent_default()
            if self.text:
                self.clear()
                self.styles.height = 2
            return

        # Pass-through app-level shortcuts
        if key in {"ctrl+c", "ctrl+d", "ctrl+l"}:
            return

        await super()._on_key(event)

    def action_historyBack(self) -> None:
        self._navigateHistory(-1)

    def action_historyForward(self) -> None:
        self._navigateHistory(1)

    def _navigateHistory(self, direction: int) -> None:
        if not self._inputHistory:
            return
        if self._historyIdx == -1:
            if direction == -1:
                self._historyIdx = len(self._inputHistory) - 1
            else:
                return
        else:
            self._historyIdx += direction
            if self._historyIdx < 0:
                self._historyIdx = 0
                return
            if self._historyIdx >= len(self._inputHistory):
                self._historyIdx = -1
                self._navigating = True
                self.clear()
                self.styles.height = 2
                self._navigating = False
                return
        self._navigating = True
        self.load_text(self._inputHistory[self._historyIdx])
        self._navigating = False
