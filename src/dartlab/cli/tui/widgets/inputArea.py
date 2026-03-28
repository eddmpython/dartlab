"""Input area -- elia PromptInput pattern."""

from __future__ import annotations

from textual import events, on
from textual.binding import Binding
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import TextArea


class InputSubmitted(Message):
    """User submitted input."""

    def __init__(self, value: str) -> None:
        super().__init__()
        self.value = value


class SlashTriggered(Message):
    """Slash typed on empty input -- open command palette."""


class InputArea(TextArea):
    """Chat input with Enter submit (elia PromptInput pattern)."""

    BINDINGS = [
        Binding("ctrl+shift+v", "paste", "Paste", show=False),
    ]

    submitReady: reactive[bool] = reactive(True)

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
        """Set border title and subtitle (elia pattern)."""
        self.border_title = "Message"
        self.border_subtitle = "/ commands  ^C cancel  ^D exit"

    @on(TextArea.Changed)
    def _onChanged(self, event: TextArea.Changed) -> None:
        """Dynamic border_subtitle hint (elia pattern)."""
        if self.text.strip():
            self.border_subtitle = "Enter to send"
        else:
            self.border_subtitle = "/ commands  ^C cancel  ^D exit"

    def watch_submitReady(self, ready: bool) -> None:
        """Visual feedback when input is blocked."""
        self.set_class(not ready, "-submit-blocked")

    async def _on_key(self, event: events.Key) -> None:
        """Key handling."""
        key = event.key

        # "/" on empty -> command palette
        if key == "slash" and self.text.strip() == "":
            event.stop()
            event.prevent_default()
            self.post_message(SlashTriggered())
            return

        # Enter = submit
        if key == "enter":
            event.stop()
            event.prevent_default()
            text = self.text.strip()
            if text and self.submitReady:
                self._inputHistory.append(text)
                self._historyIdx = -1
                self.clear()
                self.post_message(InputSubmitted(text))
            elif not self.submitReady:
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
        _appKeys = {"ctrl+c", "ctrl+d", "ctrl+p", "ctrl+l", "ctrl+b", "ctrl+e"}
        if key in _appKeys:
            return

        await super()._on_key(event)

    def _navigateHistory(self, direction: int) -> None:
        """Navigate input history."""
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
