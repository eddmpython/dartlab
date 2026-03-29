"""DartLab TUI -- oterm architecture + Toad design."""

from __future__ import annotations

import asyncio
import time
from typing import Any

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.theme import Theme
from textual.widgets import Footer

from dartlab.cli.brand import CLR, CLR_ACCENT, CLR_DANGER, CLR_DIM, CLR_SUCCESS, CLR_WARN
from dartlab.cli.tui.widgets.chatContainer import ChatContainer
from dartlab.cli.tui.widgets.headerBar import HeaderBar
from dartlab.cli.tui.widgets.prompt import Prompt
from dartlab.cli.tui.widgets.welcomeScreen import WelcomeScreen

_THEME = Theme(
    name="dartlab",
    primary=CLR,
    secondary=CLR_DIM,
    accent=CLR_ACCENT,
    success=CLR_SUCCESS,
    warning=CLR_WARN,
    error=CLR_DANGER,
    dark=True,
)


class DartLabApp(App[None]):
    """DartLab AI chat TUI (oterm pattern)."""

    CSS_PATH = "app.tcss"
    TITLE = "DartLab"
    SUB_TITLE = "DART / EDGAR AI Analysis"
    theme = "dartlab"

    BINDINGS = [
        Binding("ctrl+c", "cancelOrQuit", "Cancel/Quit", priority=True),
        Binding("ctrl+d", "quit", "Exit", show=True, priority=True),
        Binding("ctrl+l", "clearChat", "Clear", show=False, priority=True),
    ]

    def __init__(self, args: Any = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.register_theme(_THEME)
        self._args = args
        self._state: Any = None
        self._inferenceTask: asyncio.Task | None = None

    def compose(self) -> ComposeResult:
        yield HeaderBar(id="headerBar")
        yield ChatContainer(id="chatContainer")
        yield Prompt(id="prompt")
        yield Footer()

    async def on_mount(self) -> None:
        from dartlab.cli.commands.chat import _ChatState
        from dartlab.cli.services.providers import detect_provider

        self._state = _ChatState()

        if self._args:
            self._state.provider = getattr(self._args, "provider", None)
            self._state.model = getattr(self._args, "model", None)
            self._state.baseUrl = getattr(self._args, "base_url", None)
            self._state.apiKey = getattr(self._args, "api_key", None)

        if not self._state.provider:
            try:
                detected = detect_provider()
                if detected:
                    self._state.provider = detected
            except (ImportError, OSError):
                pass

        header = self.query_one(HeaderBar)
        header.provider = self._state.provider or ""
        header.model = self._state.model or ""

        companyArg = getattr(self._args, "company", None) if self._args else None
        if companyArg:
            self._loadCompany(companyArg)

        container = self.query_one(ChatContainer)
        await container.mount(
            WelcomeScreen(
                provider=self._state.provider or "",
                model=self._state.model or "",
            )
        )

        self.query_one(Prompt).focus()

    # -- Company loading --

    @work(thread=True)
    def _loadCompany(self, identifier: str) -> None:
        try:
            import dartlab

            company = dartlab.Company(identifier)
            self._state.company = company
            self._state.stockCode = company.stockCode
            self.call_from_thread(self._refreshHeader)
        except (ImportError, OSError, ValueError, FileNotFoundError):
            pass

    # -- Input handling (oterm on_submit pattern) --

    @on(Prompt.Submitted)
    async def onPromptSubmitted(self, event: Prompt.Submitted) -> None:
        text = event.value.strip()
        if not text:
            return

        # Remove welcome screen
        container = self.query_one(ChatContainer)
        for w in container.query(WelcomeScreen):
            w.remove()

        if text.startswith("/"):
            container.appendSystem(f"[dim]> {text}[/]")
            self._handleSlash(text)
            return

        container.appendUser(text)
        self._executeQuery(text)

    # -- Slash commands --

    def _handleSlash(self, text: str) -> None:
        cmd = text.split()[0].lower()
        container = self.query_one(ChatContainer)

        if cmd in ("/quit", "/exit", "/q"):
            self.exit()
        elif cmd == "/clear":
            container.clearAll()
            if self._state:
                self._state.history.clear()
            container.appendSystem("[dim]Conversation cleared.[/]")
        elif cmd == "/help":
            self._showHelp()
        elif cmd in ("/company", "/c"):
            parts = text.split(maxsplit=1)
            if len(parts) > 1:
                self._loadCompany(parts[1].strip())
                container.appendSystem(f"[dim]Loading {parts[1].strip()}...[/]")
            else:
                name = self._state.stockCode or "none"
                container.appendSystem(f"[dim]Current: {name}[/]")
        elif cmd == "/status":
            self._showStatus()
        elif cmd in ("/model", "/m"):
            parts = text.split(maxsplit=1)
            if len(parts) > 1:
                self._state.model = parts[1].strip()
                self.query_one(HeaderBar).model = self._state.model
                container.appendSystem(f"[dim]Model: {self._state.model}[/]")
            else:
                container.appendSystem(f"[dim]Model: {self._state.model or 'default'}[/]")
        elif cmd in ("/provider", "/p"):
            parts = text.split(maxsplit=1)
            if len(parts) > 1:
                self._state.provider = parts[1].strip()
                self.query_one(HeaderBar).provider = self._state.provider
                container.appendSystem(f"[dim]Provider: {self._state.provider}[/]")
            else:
                container.appendSystem(f"[dim]Provider: {self._state.provider or 'auto'}[/]")
        elif cmd == "/export":
            parts = text.split(maxsplit=1)
            self._handleExport(parts[1].strip() if len(parts) > 1 else "")
        elif cmd == "/compact":
            if self._state and len(self._state.history) > 10:
                self._state.history = self._state.history[-8:]
                container.appendSystem("[dim]History compacted.[/]")
            else:
                container.appendSystem("[dim]History already short.[/]")
        else:
            self._handleSkillCommand(cmd, text)

    def _handleSkillCommand(self, cmd: str, text: str) -> None:
        from dartlab.cli.commands.chat import _SKILL_COMMANDS, _SKILL_DEFAULT_QUESTIONS

        container = self.query_one(ChatContainer)
        for name, skillId, _desc in _SKILL_COMMANDS:
            if cmd == name:
                parts = text.split(maxsplit=1)
                question = parts[1].strip() if len(parts) > 1 else _SKILL_DEFAULT_QUESTIONS.get(skillId, "Analyze")
                self._executeQuery(question, skillId=skillId)
                return
        container.appendSystem(f"[dim]Unknown command: {cmd}[/]")

    def _showHelp(self) -> None:
        from dartlab.cli.commands.chat import _COMMANDS, _SKILL_COMMANDS

        container = self.query_one(ChatContainer)
        lines = ["[bold]Commands[/]"]
        for name, aliases, desc in _COMMANDS:
            aliasStr = f" ({', '.join(aliases)})" if aliases else ""
            lines.append(f"  {name}{aliasStr}  [dim]{desc}[/]")
        lines.append("")
        lines.append("[bold]Analysis[/]")
        for name, _skillId, desc in _SKILL_COMMANDS:
            lines.append(f"  {name}  [dim]{desc}[/]")
        container.appendSystem("\n".join(lines))

    def _showStatus(self) -> None:
        container = self.query_one(ChatContainer)
        s = self._state
        elapsed = time.monotonic() - s.startTime
        lines = [
            "[bold]Status[/]",
            f"  Provider: {s.provider or 'none'}",
            f"  Model: {s.model or 'default'}",
            f"  Company: {s.stockCode or 'none'}",
            f"  Queries: {s.queryCount}",
            f"  Tools: {s.toolCallCount}",
            f"  History: {len(s.history)} messages",
            f"  Elapsed: {elapsed:.0f}s",
        ]
        container.appendSystem("\n".join(lines))

    def _handleExport(self, arg: str) -> None:
        from datetime import datetime
        from pathlib import Path

        container = self.query_one(ChatContainer)
        if not self._state or not self._state.history:
            container.appendSystem("[dim]No conversation to export.[/]")
            return

        path = arg or f"dartlab_chat_{datetime.now():%Y%m%d_%H%M%S}.md"
        lines = ["# DartLab Chat Export", f"Date: {datetime.now():%Y-%m-%d %H:%M}", ""]
        for msg in self._state.history:
            role = "You" if msg["role"] == "user" else "DartLab"
            lines.append(f"## {role}\n\n{msg['content']}\n")

        Path(path).write_text("\n".join(lines), encoding="utf-8")
        container.appendSystem(f"[dim]Exported to {path}[/]")

    # -- Query execution --

    def _executeQuery(self, question: str, *, reportMode: bool = False, skillId: str | None = None) -> None:
        if self._inferenceTask and not self._inferenceTask.done():
            return

        prompt = self.query_one(Prompt)
        prompt.disabled = True

        container = self.query_one(ChatContainer)
        container.showSpinner("Thinking")

        self._inferenceTask = asyncio.get_event_loop().create_task(self._runInThread(question, reportMode, skillId))

    async def _runInThread(self, question: str, reportMode: bool, skillId: str | None) -> None:
        """Bridge: run blocking analyze() in a thread, post results back."""
        import asyncio

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._analyze, question, reportMode, skillId)

    def _analyze(self, question: str, reportMode: bool, skillId: str | None) -> None:
        from dartlab.ai.runtime.core import analyze
        from dartlab.cli.commands.chat import _TOOL_LABELS

        state = self._state
        container = self.query_one(ChatContainer)

        if not state.provider:
            self.call_from_thread(container.hideSpinner)
            self.call_from_thread(container.appendSystem, "[bold red]No AI provider. Run: dartlab setup[/]")
            self.call_from_thread(self._finalize)
            return

        kwargs: dict[str, Any] = {
            "provider": state.provider,
            "model": state.model,
            "base_url": state.baseUrl,
            "api_key": state.apiKey,
            "use_tools": True,
            "report_mode": reportMode,
            "max_turns": 15 if reportMode else (8 if skillId else 5),
            "history": state.history if state.history else None,
            "validate": reportMode,
        }
        if skillId:
            kwargs["question_types"] = (skillId,)
        if state.cachedSnapshot:
            kwargs["snapshot"] = state.cachedSnapshot

        queryStart = time.monotonic()
        buffer = ""
        toolCount = 0
        assistantStarted = False

        try:
            for ev in analyze(state.company, question, **kwargs):
                # Check cancellation
                if self._inferenceTask and self._inferenceTask.cancelled():
                    break

                if ev.kind == "chunk":
                    text = ev.data.get("text", "")
                    if not assistantStarted:
                        self.call_from_thread(container.hideSpinner)
                        self.call_from_thread(container.beginAssistant)
                        assistantStarted = True
                    self.call_from_thread(container.appendChunk, text)
                    buffer += text

                elif ev.kind == "tool_call":
                    toolName = ev.data.get("name", "")
                    toolArgs = ev.data.get("arguments", {})
                    label = _TOOL_LABELS.get(toolName, toolName)
                    if toolArgs:
                        argPreview = ", ".join(f"{k}={v}" for k, v in list(toolArgs.items())[:2])
                        label = f"{label}({argPreview})"
                    toolCount += 1
                    state.toolCallCount += 1
                    self.call_from_thread(container.addToolCall, toolName, label)
                    self.call_from_thread(container.showSpinner, f"Running {_TOOL_LABELS.get(toolName, toolName)}")
                    ev.data["_start"] = time.monotonic()

                elif ev.kind == "tool_result":
                    elapsed = time.monotonic() - ev.data.get("_start", time.monotonic())
                    preview = str(ev.data.get("result", ""))[:60]
                    self.call_from_thread(container.finishToolCall, elapsed, preview)
                    self.call_from_thread(container.showSpinner, "Thinking")

                elif ev.kind == "error":
                    self.call_from_thread(container.hideSpinner)
                    errorMsg = ev.data.get("error", "Unknown error")
                    self.call_from_thread(container.appendSystem, f"[bold red]{errorMsg}[/]")
                    break

        except Exception as exc:
            self.call_from_thread(container.hideSpinner)
            self.call_from_thread(container.appendSystem, f"[bold red]{type(exc).__name__}: {exc}[/]")

        # Finalize
        self.call_from_thread(container.hideSpinner)
        content = ""
        if assistantStarted:
            content = self.call_from_thread(container.finishAssistant)

        elapsed = time.monotonic() - queryStart
        footerParts = [f"{elapsed:.1f}s"]
        if toolCount > 0:
            footerParts.append(f"{toolCount} tool{'s' if toolCount != 1 else ''}")
        self.call_from_thread(container.appendSystem, f"[dim]{'  |  '.join(footerParts)}[/]")

        if content:
            state.history.append({"role": "user", "content": question})
            state.history.append({"role": "assistant", "content": content})
            state.queryCount += 1

        self.call_from_thread(self._finalize)

    def _finalize(self) -> None:
        self._inferenceTask = None
        prompt = self.query_one(Prompt)
        prompt.disabled = False
        prompt.focus()
        self._refreshHeader()

    def _refreshHeader(self) -> None:
        if not self._state:
            return
        header = self.query_one(HeaderBar)
        header.provider = self._state.provider or ""
        header.model = self._state.model or ""
        header.stockCode = self._state.stockCode or ""

    # -- Actions --

    def action_cancelOrQuit(self) -> None:
        if self._inferenceTask and not self._inferenceTask.done():
            self._inferenceTask.cancel()
            container = self.query_one(ChatContainer)
            container.hideSpinner()
            container.markCancelled()
            container.appendSystem("[dim]Cancelled.[/]")
            self._finalize()
        else:
            self.exit()

    def action_clearChat(self) -> None:
        self.query_one(ChatContainer).clearAll()
        if self._state:
            self._state.history.clear()
