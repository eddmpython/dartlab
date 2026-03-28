"""Prompt input -- oterm FlexibleInput pattern, simplified for dartlab."""

from __future__ import annotations

from dataclasses import dataclass

from textual import events, on
from textual.binding import Binding
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import TextArea


class Prompt(TextArea):
    """Chat input (Enter to submit, Shift+Enter for newline)."""

    BINDINGS = [
        Binding("ctrl+shift+v", "paste", "Paste", show=False),
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

    def on_mount(self) -> None:
        self.border_title = "Message"
        self.border_subtitle = "Enter send  |  Shift+Enter newline  |  / commands"

    @on(TextArea.Changed)
    def _onChanged(self, event: TextArea.Changed) -> None:
        self._historyIdx = -1
        if self.text.strip():
            self.border_subtitle = "Enter to send"
        else:
            self.border_subtitle = "Enter send  |  Shift+Enter newline  |  / commands"

    def watch_disabled(self, value: bool) -> None:
        self.set_class(value, "-blocked")

    async def _on_key(self, event: events.Key) -> None:
        key = event.key

        # Enter = submit
        if key == "enter":
            event.stop()
            event.prevent_default()
            text = self.text.strip()
            if text and not self.disabled:
                self._inputHistory.append(text)
                self._historyIdx = -1
                self.clear()
                self.post_message(Prompt.Submitted(value=text))
            elif self.disabled:
                self.app.bell()
            return

        # Shift+Enter = newline
        if key == "shift+enter":
            event.stop()
            event.prevent_default()
            self.insert("\n")
            return

        # History navigation
        if key == "ctrl+up":
            event.stop()
            event.prevent_default()
            self._navigateHistory(-1)
            return
        if key == "ctrl+down":
            event.stop()
            event.prevent_default()
            self._navigateHistory(1)
            return

        # Pass-through app-level shortcuts
        if key in {"ctrl+c", "ctrl+d", "ctrl+l"}:
            return

        await super()._on_key(event)

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
                self.clear()
                return
        self.load_text(self._inputHistory[self._historyIdx])
