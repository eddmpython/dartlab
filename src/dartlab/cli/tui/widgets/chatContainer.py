"""Chat container -- message display with streaming and tool call visualization."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.css.query import NoMatches
from textual.reactive import reactive
from textual.timer import Timer
from textual.widgets import Markdown, Static

from dartlab.cli.brand import CLR, CLR_MUTED, CLR_SUCCESS

_SPINNER_FRAMES = [".", "..", "...", ".."]


class SpinnerWidget(Static):
    """Animated spinner with label text."""

    DEFAULT_CSS = """
    SpinnerWidget {
        height: 1;
        margin: 0 1;
    }
    """

    _frame: reactive[int] = reactive(0)

    def __init__(self, label: str = "Thinking", **kwargs) -> None:
        super().__init__(f"[{CLR}]{label}[/] [{CLR_MUTED}]...[/]", **kwargs)
        self._label = label
        self._timer: Timer | None = None

    def on_mount(self) -> None:
        self._timer = self.set_interval(0.4, self._tick)

    def _tick(self) -> None:
        self._frame = (self._frame + 1) % len(_SPINNER_FRAMES)

    def watch__frame(self, _value: int) -> None:
        dots = _SPINNER_FRAMES[self._frame]
        self.update(f"[{CLR}]{self._label}[/] [{CLR_MUTED}]{dots}[/]")

    def setLabel(self, label: str) -> None:
        self._label = label
        dots = _SPINNER_FRAMES[self._frame]
        self.update(f"[{CLR}]{self._label}[/] [{CLR_MUTED}]{dots}[/]")

    def on_unmount(self) -> None:
        if self._timer:
            self._timer.stop()


class ChatItem(Static):
    """Single message bubble. User=plain text, Assistant=Markdown streaming."""

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
        parent = self.parent
        if isinstance(parent, ChatContainer):
            parent._autoScroll()


class ChatContainer(VerticalScroll):
    """Scrollable chat area with streaming support."""

    can_focus = False

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._streamingItem: ChatItem | None = None
        self._buffer: str = ""
        self._toolGroup: Vertical | None = None
        self._toolCount: int = 0
        self._currentToolId: str | None = None
        self._spinner: SpinnerWidget | None = None

    _userScrolledUp: bool = False

    def on_scroll_up(self) -> None:
        self._userScrolledUp = True

    def _autoScroll(self) -> None:
        if not self._userScrolledUp:
            self.call_later(lambda: self.scroll_end(animate=False))

    # -- Spinner --

    def showSpinner(self, label: str = "Thinking") -> None:
        if self._spinner:
            self._spinner.setLabel(label)
            return
        self._spinner = SpinnerWidget(label)
        self.mount(self._spinner)
        self._autoScroll()

    def hideSpinner(self) -> None:
        if self._spinner:
            self._spinner.remove()
            self._spinner = None

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

    # -- Tool calls --

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
                f"[{CLR}]>[/] [dim]{label}[/]",
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

    # -- Clear --

    def clearAll(self) -> None:
        self.hideSpinner()
        self.remove_children()
        self._streamingItem = None
        self._buffer = ""
        self._toolGroup = None
        self._toolCount = 0
        self._currentToolId = None
