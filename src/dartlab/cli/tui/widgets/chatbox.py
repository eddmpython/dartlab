"""Single message widget -- elia Chatbox pattern."""

from __future__ import annotations

from rich.markdown import Markdown as RichMarkdown
from rich.text import Text
from textual.binding import Binding
from textual.reactive import reactive
from textual.render import RenderableType
from textual.widget import Widget


class Chatbox(Widget, can_focus=True):
    """Individual chat message with border_title role label (elia pattern)."""

    BINDINGS = [
        Binding("y,c", "copy", "Copy", show=False),
        Binding("escape", "screen.focus('input-area')", "Focus input", show=False),
    ]

    highlight = reactive(False)

    def __init__(self, role: str, content: str = "", **kwargs) -> None:
        super().__init__(**kwargs)
        self._role = role
        self._content = content

    def on_mount(self) -> None:
        """Set border_title and CSS class based on role."""
        if self._role == "user":
            self.add_class("user-message")
            self.border_title = "You"
        elif self._role == "assistant":
            self.add_class("assistant-message")
            self.border_title = "DartLab"
        else:
            self.add_class("system-message")

    def render(self) -> RenderableType:
        """Render message content (elia pattern: Rich renderable, not Textual widget)."""
        if not self._content:
            return Text("")
        if self._role == "assistant":
            return RichMarkdown(self._content)
        return Text(self._content)

    def appendChunk(self, chunk: str) -> None:
        """Append streaming chunk and refresh layout (elia pattern)."""
        self._content += chunk
        self.refresh(layout=True)

    @property
    def content(self) -> str:
        """Full message content."""
        return self._content

    def action_copy(self) -> None:
        """Copy message to clipboard."""
        try:
            import pyperclip

            pyperclip.copy(self._content)
            self.notify("Copied to clipboard")
        except ImportError:
            self.notify("pyperclip not installed: pip install pyperclip", severity="error")
        except OSError as exc:
            self.notify(f"Clipboard error: {exc}", severity="error")
