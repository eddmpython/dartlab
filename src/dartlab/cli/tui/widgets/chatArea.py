"""Chat area -- scrollable message container (elia chat.py pattern)."""

from __future__ import annotations

from textual.containers import VerticalScroll
from textual.css.query import NoMatches
from textual.widgets import Static

from dartlab.cli.tui.widgets.chatbox import Chatbox
from dartlab.cli.tui.widgets.responseStatus import ResponseStatus


class ChatArea(VerticalScroll):
    """Scrollable chat area with auto-scroll (elia pattern)."""

    can_focus = False

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._streamingBox: Chatbox | None = None
        self._currentToolId: str | None = None
        self._toolCount = 0

    # ── auto-scroll (elia exact pattern) ──

    def _autoScroll(self) -> None:
        """Scroll to bottom only if already near bottom."""
        scrollY = self.scroll_y
        maxY = self.max_scroll_y
        if scrollY in range(maxY - 3, maxY + 1):
            self.scroll_end(animate=False)

    # ── messages ──

    def appendUser(self, text: str) -> None:
        """Add a user message."""
        self.mount(Chatbox("user", text))
        self._autoScroll()

    def appendSystem(self, text: str) -> None:
        """Add a system/info message."""
        self.mount(Static(f"[#6c7086]{text}[/]", classes="system-message"))
        self._autoScroll()

    def beginAssistant(self) -> Chatbox:
        """Start a new streaming assistant message."""
        box = Chatbox("assistant", "")
        self._streamingBox = box
        self.mount(box)
        self._autoScroll()
        return box

    def appendChunk(self, text: str) -> None:
        """Append a chunk to the streaming message."""
        if self._streamingBox is None:
            self.beginAssistant()
        self._streamingBox.appendChunk(text)
        self._autoScroll()

    def finishAssistant(self) -> str:
        """Finish streaming. Returns full content."""
        content = ""
        if self._streamingBox is not None:
            content = self._streamingBox.content
        self._streamingBox = None
        self._toolCount = 0
        return content

    # ── tool calls ──

    def addToolCall(self, toolName: str, label: str) -> None:
        """Add a tool call indicator."""
        self._toolCount += 1
        toolId = f"tool-{self._toolCount}"
        self._currentToolId = toolId
        self.mount(
            Static(
                f"[#fab387]>[/] [#6c7086]{label}[/] [dim]...[/]",
                id=toolId,
                classes="tool-status",
            )
        )
        self._autoScroll()

    def finishToolCall(self, elapsed: float, preview: str = "") -> None:
        """Mark tool call as done."""
        if self._currentToolId is None:
            return
        try:
            widget = self.query_one(f"#{self._currentToolId}", Static)
        except NoMatches:
            return
        elapsedStr = f"{elapsed * 1000:.0f}ms" if elapsed < 1.0 else f"{elapsed:.1f}s"
        # Reconstruct label from existing text
        line = f"[#a6e3a1]>[/] [#a6adc8]done[/] [#45475a]({elapsedStr})[/]"
        if preview:
            line += f" [#6c7086]-- {preview}[/]"
        widget.update(line)
        widget.remove_class("tool-status")
        widget.add_class("tool-done")
        self._currentToolId = None

    # ── thinking indicator (elia ResponseStatus pattern) ──

    def showThinking(self) -> None:
        """Show thinking indicator."""
        self.hideThinking()
        status = ResponseStatus(id="thinking-status")
        self.mount(status)
        status.setAwaiting()
        self._autoScroll()

    def setResponding(self) -> None:
        """Switch thinking to responding."""
        try:
            status = self.query_one("#thinking-status", ResponseStatus)
            status.setResponding()
        except NoMatches:
            pass

    def hideThinking(self) -> None:
        """Remove thinking indicator."""
        try:
            status = self.query_one("#thinking-status", ResponseStatus)
            status.remove()
        except NoMatches:
            pass

    # ── clear ──

    def clearAll(self) -> None:
        """Remove all messages."""
        self.remove_children()
        self._streamingBox = None
        self._currentToolId = None
        self._toolCount = 0
