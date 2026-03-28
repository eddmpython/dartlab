"""DartLab TUI -- full-screen Textual chat (elia pattern)."""

from __future__ import annotations

import time
from threading import Event
from typing import Any

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.css.query import NoMatches

from dartlab.cli.tui.widgets.chatArea import ChatArea
from dartlab.cli.tui.widgets.headerBar import HeaderBar
from dartlab.cli.tui.widgets.inputArea import InputArea, InputSubmitted, SlashTriggered
from dartlab.cli.tui.widgets.welcomeScreen import WelcomeScreen


class DartLabApp(App[None]):
    """Full-screen TUI for dartlab AI chat."""

    CSS_PATH = "app.tcss"

    BINDINGS = [
        Binding("ctrl+c", "cancel_or_quit", "Cancel/Quit", priority=True),
        Binding("ctrl+d", "quit", "Exit", show=True, priority=True),
        Binding("ctrl+p", "command_palette", "Commands", show=True, priority=True),
        Binding("ctrl+l", "clear_chat", "Clear", show=False, priority=True),
        Binding("ctrl+e", "open_editor", "Editor", show=False, priority=True),
    ]

    def __init__(self, args: Any = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._args = args
        self._state: Any = None
        self._cancelEvent: Event | None = None
        self._running = False

    def compose(self) -> ComposeResult:
        yield HeaderBar(id="header-bar")
        with Horizontal(id="body"):
            yield ChatArea(id="chat-area")
        yield InputArea(id="input-area")

    async def on_mount(self) -> None:
        """Initialize state and show welcome."""
        from dartlab.cli.commands.chat import _ChatState
        from dartlab.cli.services.providers import detect_provider

        self._state = _ChatState()

        # CLI args
        if self._args:
            self._state.provider = getattr(self._args, "provider", None)
            self._state.model = getattr(self._args, "model", None)
            self._state.baseUrl = getattr(self._args, "base_url", None)
            self._state.apiKey = getattr(self._args, "api_key", None)

        # Auto-detect provider
        if not self._state.provider:
            try:
                detected = detect_provider()
                if detected:
                    self._state.provider = detected
            except (ImportError, OSError):
                pass

        # Update header
        header = self.query_one(HeaderBar)
        header.provider = self._state.provider or ""
        header.model = self._state.model or ""

        # Load company from args
        companyArg = getattr(self._args, "company", None) if self._args else None
        if companyArg:
            self._loadCompany(companyArg)

        # Show welcome
        chatArea = self.query_one(ChatArea)
        chatArea.mount(
            WelcomeScreen(
                provider=self._state.provider or "",
                model=self._state.model or "",
            )
        )

        # Focus input
        self.query_one(InputArea).focus()

    # ── Company loading ──

    @work(thread=True)
    def _loadCompany(self, identifier: str) -> None:
        """Load company in background thread."""
        try:
            import dartlab

            company = dartlab.Company(identifier)
            self._state.company = company
            self._state.stockCode = company.stockCode
            self.call_from_thread(self._refreshStatus)
        except (ImportError, OSError, ValueError, FileNotFoundError):
            pass

    # ── Event handlers ──

    async def on_slash_triggered(self, event: SlashTriggered) -> None:
        """Open command palette on "/"."""
        self.action_command_palette()

    async def on_input_submitted(self, event: InputSubmitted) -> None:
        """Handle user input."""
        text = event.value.strip()
        if not text:
            return

        # Remove welcome screen
        try:
            welcome = self.query_one(WelcomeScreen)
            welcome.remove()
        except NoMatches:
            pass

        chatArea = self.query_one(ChatArea)

        # Slash command
        if text.startswith("/"):
            chatArea.appendUser(text)
            self._handleSlash(text)
            return

        # Normal query
        chatArea.appendUser(text)
        self._executeQuery(text)

    # ── Slash commands ──

    def _handleSlash(self, text: str) -> None:
        """Dispatch slash command."""
        cmd = text.split()[0].lower()
        chatArea = self.query_one(ChatArea)

        if cmd in ("/quit", "/exit", "/q"):
            self.exit()
        elif cmd == "/clear":
            chatArea.clearAll()
            if self._state:
                self._state.history.clear()
            chatArea.appendSystem("[dim]Conversation cleared.[/]")
        elif cmd == "/help":
            self._showHelp()
        elif cmd in ("/company", "/c"):
            parts = text.split(maxsplit=1)
            if len(parts) > 1:
                self._loadCompany(parts[1].strip())
                chatArea.appendSystem(f"[dim]Loading {parts[1].strip()}...[/]")
            else:
                name = self._state.stockCode or "none"
                chatArea.appendSystem(f"[dim]Current: {name}[/]")
        elif cmd == "/status":
            self._showStatus()
        elif cmd in ("/history", "/h"):
            self._showHistory()
        elif cmd == "/compact":
            if self._state and len(self._state.history) > 10:
                self._state.history = self._state.history[-8:]
                chatArea.appendSystem("[dim]History compacted.[/]")
            else:
                chatArea.appendSystem("[dim]History already short.[/]")
        elif cmd in ("/report", "/r"):
            parts = text.split(maxsplit=1)
            question = parts[1].strip() if len(parts) > 1 else "Comprehensive analysis"
            self._executeQuery(question, reportMode=True)
        elif cmd in ("/suggest", "/s"):
            self._showSuggest()
        elif cmd == "/export":
            parts = text.split(maxsplit=1)
            self._handleExport(parts[1].strip() if len(parts) > 1 else "")
        elif cmd == "/cost":
            self._showCost()
        elif cmd in ("/model", "/m"):
            parts = text.split(maxsplit=1)
            if len(parts) > 1:
                self._state.model = parts[1].strip()
                self.query_one(HeaderBar).model = self._state.model
                chatArea.appendSystem(f"[dim]Model: {self._state.model}[/]")
            else:
                chatArea.appendSystem(f"[dim]Model: {self._state.model or 'default'}[/]")
        elif cmd in ("/provider", "/p"):
            parts = text.split(maxsplit=1)
            if len(parts) > 1:
                self._state.provider = parts[1].strip()
                self.query_one(HeaderBar).provider = self._state.provider
                chatArea.appendSystem(f"[dim]Provider: {self._state.provider}[/]")
            else:
                chatArea.appendSystem(f"[dim]Provider: {self._state.provider or 'auto'}[/]")
        else:
            # Check skill commands
            self._handleSkillCommand(cmd, text)

    def _handleSkillCommand(self, cmd: str, text: str) -> None:
        """Handle skill slash commands."""
        from dartlab.cli.commands.chat import _SKILL_COMMANDS, _SKILL_DEFAULT_QUESTIONS

        chatArea = self.query_one(ChatArea)
        for name, skillId, _desc in _SKILL_COMMANDS:
            if cmd == name:
                parts = text.split(maxsplit=1)
                question = parts[1].strip() if len(parts) > 1 else _SKILL_DEFAULT_QUESTIONS.get(skillId, "Analyze")
                self._executeQuery(question, skillId=skillId)
                return
        chatArea.appendSystem(f"[dim]Unknown command: {cmd}[/]")

    def _showHelp(self) -> None:
        """Show help in chat area."""
        from dartlab.cli.commands.chat import _COMMANDS, _SKILL_COMMANDS

        chatArea = self.query_one(ChatArea)
        lines = ["[bold]Commands:[/]"]
        for name, aliases, desc in _COMMANDS:
            aliasStr = f" ({', '.join(aliases)})" if aliases else ""
            lines.append(f"  [#89b4fa]{name}[/]{aliasStr}  [dim]{desc}[/]")
        lines.append("")
        lines.append("[bold]Analysis skills:[/]")
        for name, _skillId, desc in _SKILL_COMMANDS:
            lines.append(f"  [#ea4647]{name}[/]  [dim]{desc}[/]")
        chatArea.appendSystem("\n".join(lines))

    def _showStatus(self) -> None:
        """Show session status."""
        chatArea = self.query_one(ChatArea)
        s = self._state
        elapsed = time.monotonic() - s.startTime
        lines = [
            "[bold]Session status:[/]",
            f"  Provider: [#a6adc8]{s.provider or 'none'}[/]",
            f"  Model: [#a6adc8]{s.model or 'default'}[/]",
            f"  Company: [#a6adc8]{s.stockCode or 'none'}[/]",
            f"  Queries: [#a6adc8]{s.queryCount}[/]",
            f"  Tool calls: [#a6adc8]{s.toolCallCount}[/]",
            f"  History: [#a6adc8]{len(s.history)} messages[/]",
            f"  Elapsed: [#a6adc8]{elapsed:.0f}s[/]",
        ]
        chatArea.appendSystem("\n".join(lines))

    def _showHistory(self) -> None:
        """Show recent history."""
        chatArea = self.query_one(ChatArea)
        if not self._state or not self._state.history:
            chatArea.appendSystem("[dim]No history yet.[/]")
            return
        for msg in self._state.history[-6:]:
            role = msg.get("role", "?")
            content = msg.get("content", "")[:100]
            chatArea.appendSystem(f"[dim]{role}: {content}[/]")

    def _showCost(self) -> None:
        """Show token usage."""
        chatArea = self.query_one(ChatArea)
        try:
            from dartlab.cli.services.history import get_total_usage

            usage = get_total_usage()
            lines = [
                "[bold]Token usage:[/]",
                f"  Input: [#a6adc8]{usage.get('input_tokens', 0):,}[/]",
                f"  Output: [#a6adc8]{usage.get('output_tokens', 0):,}[/]",
                f"  Cost: [#a6adc8]${usage.get('cost_usd', 0):.4f}[/]",
            ]
            chatArea.appendSystem("\n".join(lines))
        except (ImportError, OSError):
            chatArea.appendSystem("[dim]Usage data unavailable.[/]")

    def _showSuggest(self) -> None:
        """Show suggested questions."""
        from dartlab.cli.commands.chat import _SUGGESTIONS

        chatArea = self.query_one(ChatArea)
        questions = list(_SUGGESTIONS)
        if self._state and self._state.company:
            try:
                from dartlab.ai.conversation.suggestions import suggestQuestions

                engineQuestions = suggestQuestions(self._state.company)
                if engineQuestions:
                    questions = engineQuestions
            except (ImportError, AttributeError):
                pass
        lines = ["[bold]Suggested questions:[/]"]
        for i, q in enumerate(questions, 1):
            lines.append(f"  [#a6adc8]{i}.[/] {q}")
        chatArea.appendSystem("\n".join(lines))

    def _handleExport(self, arg: str) -> None:
        """Export conversation to markdown."""
        from datetime import datetime
        from pathlib import Path

        chatArea = self.query_one(ChatArea)
        if not self._state or not self._state.history:
            chatArea.appendSystem("[dim]No conversation to export.[/]")
            return

        path = arg or f"dartlab_chat_{datetime.now():%Y%m%d_%H%M%S}.md"
        lines = ["# DartLab Chat Export", f"Date: {datetime.now():%Y-%m-%d %H:%M}", ""]
        if self._state.company:
            try:
                lines.append(f"Company: {self._state.company.corpName} ({self._state.stockCode})")
            except AttributeError:
                lines.append(f"Company: {self._state.stockCode}")
            lines.append("")
        lines.append(f"Provider: {self._state.provider} | Model: {self._state.model or 'default'}")
        lines.append(f"Queries: {self._state.queryCount} | Tool calls: {self._state.toolCallCount}")
        lines.append("")
        lines.append("---")
        lines.append("")

        for msg in self._state.history:
            role = "You" if msg["role"] == "user" else "DartLab"
            lines.append(f"## {role}")
            lines.append("")
            lines.append(msg["content"])
            lines.append("")

        Path(path).write_text("\n".join(lines), encoding="utf-8")
        chatArea.appendSystem(f"[dim]Exported to {path}[/]")

    # ── Query execution (elia pattern: @work(thread=True) + call_from_thread) ──

    def _executeQuery(self, question: str, *, reportMode: bool = False, skillId: str | None = None) -> None:
        """Start AI query."""
        if self._running:
            return
        self._running = True
        self._cancelEvent = Event()

        inputArea = self.query_one(InputArea)
        inputArea.submitReady = False

        chatArea = self.query_one(ChatArea)
        chatArea.showThinking()

        self._runAnalysis(question, reportMode, skillId)

    @work(thread=True)
    def _runAnalysis(self, question: str, reportMode: bool, skillId: str | None) -> None:
        """Execute AI analysis in background thread (elia pattern)."""
        from dartlab.ai.runtime.core import analyze
        from dartlab.cli.commands.chat import _TOOL_LABELS

        state = self._state
        chatArea = self.query_one(ChatArea)

        # Provider check
        if not state.provider:
            self.call_from_thread(chatArea.hideThinking)
            self.call_from_thread(chatArea.appendSystem, "[#f38ba8]No AI provider. Run: dartlab setup[/]")
            self._finalize()
            return

        # Build kwargs
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
                if self._cancelEvent and self._cancelEvent.is_set():
                    break

                if ev.kind == "chunk":
                    text = ev.data.get("text", "")
                    if not assistantStarted:
                        self.call_from_thread(chatArea.hideThinking)
                        self.call_from_thread(chatArea.beginAssistant)
                        assistantStarted = True
                    self.call_from_thread(chatArea.appendChunk, text)
                    buffer += text

                elif ev.kind == "tool_call":
                    if not assistantStarted:
                        self.call_from_thread(chatArea.setResponding)
                    toolName = ev.data.get("name", "")
                    toolArgs = ev.data.get("arguments", {})
                    label = _TOOL_LABELS.get(toolName, toolName)
                    if toolArgs:
                        argPreview = ", ".join(f"{k}={v}" for k, v in list(toolArgs.items())[:2])
                        label = f"{label}({argPreview})"
                    toolCount += 1
                    state.toolCallCount += 1
                    self.call_from_thread(chatArea.addToolCall, toolName, label)
                    ev.data["_start"] = time.monotonic()

                elif ev.kind == "tool_result":
                    elapsed = time.monotonic() - ev.data.get("_start", time.monotonic())
                    resultText = ev.data.get("result", "")
                    preview = str(resultText)[:60] if resultText else ""
                    self.call_from_thread(chatArea.finishToolCall, elapsed, preview)

                elif ev.kind == "error":
                    self.call_from_thread(chatArea.hideThinking)
                    errorMsg = ev.data.get("error", "Unknown error")
                    self.call_from_thread(chatArea.appendSystem, f"[#f38ba8]{errorMsg}[/]")
                    break

        except (OSError, ImportError, RuntimeError, ValueError, TypeError) as exc:
            self.call_from_thread(chatArea.hideThinking)
            self.call_from_thread(chatArea.appendSystem, f"[#f38ba8]Error: {type(exc).__name__}: {exc}[/]")

        # Finalize
        self.call_from_thread(chatArea.hideThinking)
        content = ""
        if assistantStarted:
            content = self.call_from_thread(chatArea.finishAssistant)

        elapsed = time.monotonic() - queryStart
        footerParts = [f"{elapsed:.1f}s"]
        if toolCount > 0:
            footerParts.append(f"{toolCount} tool{'s' if toolCount != 1 else ''}")
        self.call_from_thread(chatArea.appendSystem, f"[dim]{'  |  '.join(footerParts)}[/]")

        # Update history
        if content:
            state.history.append({"role": "user", "content": question})
            state.history.append({"role": "assistant", "content": content})
            state.queryCount += 1
            self._saveMessage("user", question)
            self._saveMessage("assistant", content)

            # Follow-up hints
            if state.company:
                self._showFollowUpHints(chatArea, state)

        self.call_from_thread(self._finalize)

    def _showFollowUpHints(self, chatArea: ChatArea, state) -> None:
        """Show follow-up question hints after response."""
        from dartlab.cli.commands.chat import _SUGGESTIONS

        suggestions = _SUGGESTIONS[:3]
        try:
            from dartlab.ai.conversation.suggestions import suggestQuestions

            engineSuggestions = suggestQuestions(state.company)
            if engineSuggestions:
                suggestions = engineSuggestions[:3]
        except (ImportError, AttributeError):
            pass
        parts = []
        for q in suggestions:
            short = q[:50] + "..." if len(q) > 50 else q
            parts.append(short)
        hint = "  |  ".join(parts)
        self.call_from_thread(chatArea.appendSystem, f"[dim]Try: {hint}[/]")

    def _finalize(self) -> None:
        """Clean up after query completion."""
        self._running = False
        self._cancelEvent = None
        inputArea = self.query_one(InputArea)
        inputArea.submitReady = True
        inputArea.focus()
        self._refreshStatus()

    def _refreshStatus(self) -> None:
        """Update header from state."""
        if not self._state:
            return
        header = self.query_one(HeaderBar)
        header.provider = self._state.provider or ""
        header.model = self._state.model or ""
        header.stockCode = self._state.stockCode or ""

    def _saveMessage(self, role: str, content: str) -> None:
        """Persist message to SQLite."""
        try:
            from dartlab.cli.services.history import add_message, create_session

            if self._state.sessionId is None:
                stockCode = self._state.stockCode or "__no_company__"
                self._state.sessionId = create_session(stockCode)
            add_message(self._state.sessionId, role, content)
        except (OSError, ImportError):
            pass

    # ── Actions ──

    def action_cancel_or_quit(self) -> None:
        """Cancel running query, or quit if idle."""
        if self._running and self._cancelEvent:
            self._cancelEvent.set()
            chatArea = self.query_one(ChatArea)
            chatArea.markCancelled()
            chatArea.appendSystem("[dim]Cancelled.[/]")
            self._finalize()
        else:
            self.exit()

    def action_command_palette(self) -> None:
        """Open command palette."""
        from dartlab.cli.tui.widgets.commandPalette import CommandPalette

        async def _onResult(result: str | None) -> None:
            if result:
                inputArea = self.query_one(InputArea)
                inputArea.load_text(result + " ")
                inputArea.focus()

        self.push_screen(CommandPalette(), callback=_onResult)

    def action_clear_chat(self) -> None:
        """Clear the chat area."""
        chatArea = self.query_one(ChatArea)
        chatArea.clearAll()
        if self._state:
            self._state.history.clear()

    def action_open_editor(self) -> None:
        """Open external editor for input."""
        import subprocess
        import tempfile

        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
                tmpPath = f.name

            with self.suspend():
                import os

                editor = os.environ.get("EDITOR", "notepad" if os.name == "nt" else "vim")
                subprocess.run([editor, tmpPath], check=False)

            with open(tmpPath, encoding="utf-8") as f:
                text = f.read().strip()

            if text:
                inputArea = self.query_one(InputArea)
                inputArea.load_text(text)
                inputArea.focus()
        except (OSError, FileNotFoundError):
            pass
