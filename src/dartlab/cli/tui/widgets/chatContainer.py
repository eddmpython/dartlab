"""Chat container -- oterm ChatContainer + ChatItem pattern with Toad design."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.css.query import NoMatches
from textual.reactive import reactive
from textual.widgets import LoadingIndicator, Markdown, Static

from dartlab.cli.brand import CLR, CLR_SUCCESS


class ChatItem(Static):
    """Single message bubble (oterm ChatItem pattern).

    User messages render as plain text.
    Assistant messages render as Markdown with streaming support.
    """

    text: reactive[str] = reactive("")
    author: reactive[str] = reactive("")

    def compose(self) -> ComposeResult:
        if self.author == "user":
            yield Static(self.text, markup=False, classes="messageText")
        else:
            yield Markdown(classes="messageText")

    async def watch_text(self, text: str) -> None:
        if self.author == "user":
            return
        try:
            md = self.query_one(".messageText", Markdown)
            await md.update(text)
        except NoMatches:
            return
        # Markdown height changed -- ask parent container to scroll
        parent = self.parent
        if isinstance(parent, ChatContainer):
            parent._autoScroll()


class ChatContainer(VerticalScroll):
    """Scrollable chat area (oterm messageContainer pattern)."""

    can_focus = False

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._streamingItem: ChatItem | None = None
        self._buffer: str = ""
        self._toolGroup: Vertical | None = None
        self._toolCount: int = 0
        self._currentToolId: str | None = None

    _userScrolledUp: bool = False

    def on_scroll_up(self) -> None:
        self._userScrolledUp = True

    def _autoScroll(self) -> None:
        if not self._userScrolledUp:
            self.call_later(lambda: self.scroll_end(animate=False))

    # -- Messages --

    def appendUser(self, text: str) -> None:
        self._userScrolledUp = False
        item = ChatItem(classes="userMessage")
        item.author = "user"
        item.text = text
        self.mount(item)
        self._autoScroll()

    def appendSystem(self, text: str) -> None:
        self.mount(Static(text, classes="systemMessage"))
        self._autoScroll()

    def beginAssistant(self) -> None:
        self._userScrolledUp = False
        self._toolGroup = None
        self._buffer = ""
        item = ChatItem(classes="assistantMessage")
        item.author = "assistant"
        self._streamingItem = item
        self.mount(item)
        self._autoScroll()

    def appendChunk(self, text: str) -> None:
        if self._streamingItem is None:
            self.beginAssistant()
        self._buffer += text
        self._streamingItem.text = self._buffer
        self._autoScroll()

    def finishAssistant(self) -> str:
        content = self._buffer
        self._streamingItem = None
        self._buffer = ""
        self._toolGroup = None
        self._toolCount = 0
        return content

    def markCancelled(self) -> None:
        if self._streamingItem is not None:
            self._streamingItem.add_class("cancelledMessage")

    # -- Tool calls (Toad pattern: collapsible group with status) --

    def _ensureToolGroup(self) -> Vertical:
        if self._toolGroup is None:
            self._toolGroup = Vertical(classes="toolGroup")
            self.mount(self._toolGroup)
        return self._toolGroup

    def addToolCall(self, toolName: str, label: str) -> None:
        self._toolCount += 1
        toolId = f"tool-{self._toolCount}"
        self._currentToolId = toolId
        group = self._ensureToolGroup()
        group.mount(
            Static(
                f"[{CLR}]>[/] [dim]{label}[/] ...",
                id=toolId,
                classes="toolStatus",
            )
        )
        self._autoScroll()

    def finishToolCall(self, elapsed: float, preview: str = "") -> None:
        if self._currentToolId is None:
            return
        try:
            widget = self.query_one(f"#{self._currentToolId}", Static)
        except NoMatches:
            return
        elapsedStr = f"{elapsed * 1000:.0f}ms" if elapsed < 1.0 else f"{elapsed:.1f}s"
        line = f"[{CLR_SUCCESS}]>[/] done ({elapsedStr})"
        if preview:
            line += f" [dim]-- {preview}[/]"
        widget.update(line)
        widget.remove_class("toolStatus")
        widget.add_class("toolDone")
        self._currentToolId = None

    # -- Thinking indicator --

    def showThinking(self) -> None:
        self.hideThinking()
        self.mount(LoadingIndicator(id="thinkingIndicator"))
        self._autoScroll()

    def hideThinking(self) -> None:
        try:
            self.query_one("#thinkingIndicator").remove()
        except NoMatches:
            pass

    # -- Clear --

    def clearAll(self) -> None:
        self.remove_children()
        self._streamingItem = None
        self._buffer = ""
        self._toolGroup = None
        self._toolCount = 0
        self._currentToolId = None
