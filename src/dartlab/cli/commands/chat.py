"""`dartlab chat` -- interactive AI analysis REPL.

This module delegates to `dartlab.cli.repl` (the new world-class REPL).
The old monolithic implementation is preserved below for reference
during migration, but the active entry point is repl.run().
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from dartlab.cli.context import PROVIDERS
from dartlab.cli.services.errors import CLIError
from dartlab.cli.services.providers import detect_provider
from dartlab.cli.services.runtime import configure_dartlab

# ---------------------------------------------------------------------------
# Brand colors (synced with landing/src/lib/brand.ts)
# ---------------------------------------------------------------------------

_CLR = "#ea4647"  # primary (brand.ts primary — 로고/강조)
_CLR_DIM = "#c83232"  # primaryDark (brand.ts primaryDark — 보조 강조)
_CLR_ACCENT = "#fb923c"  # accent (brand.ts accent)
_CLR_MUTED = "#94a3b8"  # textMuted (brand.ts textMuted)
_CLR_SUCCESS = "#34d399"  # success (brand.ts success)
_CLR_WARN = "#fbbf24"  # warning (brand.ts warning)

# ---------------------------------------------------------------------------
# Suggestions (English defaults)
# ---------------------------------------------------------------------------

_SUGGESTIONS = [
    "Analyze profitability trends and earnings quality",
    "Evaluate financial health and cash flow sustainability",
    "Assess debt structure and liquidity risks",
    "Compare dividend sustainability and shareholder returns",
    "Summarize the key investment thesis for this company",
]

# ---------------------------------------------------------------------------
# Tool labels
# ---------------------------------------------------------------------------

_TOOL_LABELS = {
    "explore": "Disclosure",
    "finance": "Financial Data",
    "analyze": "Analysis Engine",
    "market": "Market Data",
    "openapi": "OpenDART API",
    "system": "System Info",
    "chart": "Chart",
    "macro": "Macro",
    "scan": "Scan",
    "company": "Company",
    "ui": "UI",
}

# ---------------------------------------------------------------------------
# Slash command registry
# ---------------------------------------------------------------------------

_COMMANDS: list[tuple[str, tuple[str, ...], str]] = [
    ("/help", (), "Show available commands"),
    ("/company", ("/c",), "Switch or show current company"),
    ("/model", ("/m",), "Switch model"),
    ("/provider", ("/p",), "Switch LLM provider"),
    ("/clear", (), "Clear conversation history"),
    ("/suggest", ("/s",), "Suggested questions"),
    ("/status", (), "Session status and config"),
    ("/cost", (), "Token usage and cost"),
    ("/export", (), "Export conversation to markdown"),
    ("/history", ("/h",), "Show recent conversation turns"),
    ("/compact", (), "Compact conversation history"),
    ("/report", ("/r",), "Deep analysis (report mode)"),
    ("/quit", ("/exit", "/q"), "Exit"),
]

# ---------------------------------------------------------------------------
# Skill commands (analysis domain shortcuts)
# ---------------------------------------------------------------------------

_SKILL_COMMANDS: list[tuple[str, str, str]] = [
    ("/profitability", "profitability", "Profitability analysis (DuPont, margins, earnings quality)"),
    ("/health", "health", "Financial health (leverage, liquidity, coverage)"),
    ("/valuation", "valuation", "Valuation (multiples, DCF, fair value range)"),
    ("/risk", "risk", "Risk assessment (financial, business, accounting)"),
    ("/strategy", "strategy", "Business strategy (segments, moat, growth)"),
    ("/accounting", "accounting", "Accounting quality (accruals, audit, changes)"),
    ("/dividend", "dividend", "Dividend analysis (sustainability, payout, yield)"),
    ("/comprehensive", "comprehensive", "Comprehensive investment analysis"),
]

_SKILL_DEFAULT_QUESTIONS: dict[str, str] = {
    "profitability": "Analyze profitability trends: DuPont decomposition, margin structure, and earnings quality",
    "health": "Evaluate financial health: leverage structure, liquidity layers, and debt coverage",
    "valuation": "Assess valuation: key multiples vs peers, DCF fair value range, and safety margin",
    "risk": "Identify risks: financial distress signals, business risks, and accounting red flags",
    "strategy": "Analyze business strategy: segment structure, competitive moat, and growth direction",
    "accounting": "Evaluate accounting quality: accrual ratio, audit history, and policy changes",
    "dividend": "Analyze dividends: payout history, FCF sustainability, and shareholder return policy",
    "comprehensive": "Provide a comprehensive investment analysis covering financials, valuation, risks, and thesis",
}

_SLASH_WORDS: list[str] = [_name for _name, _, _ in _COMMANDS]
_SLASH_WORDS.extend(_skillCmd for _skillCmd, _, _ in _SKILL_COMMANDS)


def configure_parser(subparsers) -> None:
    """Register the chat subcommand."""
    parser = subparsers.add_parser("chat", help="Interactive AI analysis REPL")
    parser.add_argument("company", nargs="?", default=None, help="Stock code or company name (optional)")
    parser.add_argument("--provider", "-p", default=None, choices=PROVIDERS, help="LLM provider")
    parser.add_argument("--model", "-m", default=None, help="Model name")
    parser.add_argument("--base-url", default=None, help="Custom API URL")
    parser.add_argument("--api-key", default=None, help="API key")
    parser.add_argument("--continue", dest="cont", action="store_true", help="Resume previous conversation")
    # Route to Textual TUI
    from dartlab.cli.tui import run as tuiRun

    parser.set_defaults(handler=tuiRun)


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------


@dataclass
class _ChatState:
    """REPL session state."""

    company: Any | None = None
    stockCode: str | None = None
    provider: str | None = None
    model: str | None = None
    baseUrl: str | None = None
    apiKey: str | None = None
    sessionId: int | None = None
    history: list[dict[str, str]] = field(default_factory=list)
    startTime: float = field(default_factory=time.monotonic)
    queryCount: int = 0
    toolCallCount: int = 0
    companiesUsed: list[str] = field(default_factory=list)
    cachedSnapshot: dict | None = None
    lastFollowUps: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------


def run(args) -> int:
    """Entry point for `dartlab chat`."""
    from rich.console import Console

    configure_dartlab()
    console = Console()
    provider = args.provider or detect_provider()

    state = _ChatState(
        provider=provider,
        model=args.model,
        baseUrl=args.base_url,
        apiKey=args.api_key,
    )

    if args.company:
        if not _loadCompany(state, args.company, console, quiet=True):
            raise CLIError(f"Company not found: {args.company}")

    _printWelcome(state, console)

    if not provider:
        _printSetupGuide(console)

    if args.cont and state.stockCode:
        _resumeSession(state, console)
    _replLoop(state, console)
    return 0


# ---------------------------------------------------------------------------
# REPL loop
# ---------------------------------------------------------------------------


def _replLoop(state: _ChatState, console) -> None:
    """Main REPL loop."""
    promptFn = _makePromptFn(state)
    lastInterrupt = 0.0

    while True:
        try:
            userInput = promptFn()
        except KeyboardInterrupt:
            now = time.monotonic()
            if now - lastInterrupt < 1.5:
                console.print()
                _printSessionSummary(state, console)
                break
            lastInterrupt = now
            console.print(f"\n  [{_CLR_MUTED}]Press Ctrl+C again to exit[/]")
            continue
        except EOFError:
            console.print()
            _printSessionSummary(state, console)
            break

        userInput = userInput.strip()
        if not userInput:
            continue

        # bare "exit" / "quit" without slash
        if userInput.lower() in ("exit", "quit", "q"):
            console.print(f"  [{_CLR_MUTED}]Exiting chat.[/]")
            _printSessionSummary(state, console)
            break

        # follow-up selection by number (1, 2)
        if userInput in ("1", "2", "3") and state.lastFollowUps:
            idx = int(userInput) - 1
            if idx < len(state.lastFollowUps):
                selected = state.lastFollowUps[idx]
                state.lastFollowUps = []
                # follow-up is a slash command (e.g. "/health -- Check...")
                cmdPart = selected.split(" -- ")[0].strip()
                if cmdPart.startswith("/"):
                    shouldExit = _handleSlash(cmdPart, state, console)
                    if shouldExit:
                        _printSessionSummary(state, console)
                        break
                else:
                    _executeQuery(cmdPart, state, console)
                continue

        state.lastFollowUps = []

        # "/" alone → show commands (Claude Code pattern)
        if userInput == "/":
            _cmdHelp("", state, console)
            continue

        if userInput.startswith("/"):
            shouldExit = _handleSlash(userInput, state, console)
            if shouldExit:
                _printSessionSummary(state, console)
                break
            continue

        if state.company is None:
            _tryAutoDetect(userInput, state, console)

        _executeQuery(userInput, state, console)


def _makePromptFn(state: _ChatState):
    """Return a callable that reads user input with prompt_toolkit or plain input()."""
    try:
        import sys

        if not sys.stdin.isatty():
            return lambda: input(_buildPromptPlain(state))

        from prompt_toolkit import PromptSession
        from prompt_toolkit.completion import WordCompleter
        from prompt_toolkit.formatted_text import HTML
        from prompt_toolkit.history import FileHistory

        historyDir = Path.home() / ".dartlab"
        historyDir.mkdir(parents=True, exist_ok=True)
        historyFile = historyDir / "chat.history"

        completer = WordCompleter(_SLASH_WORDS, sentence=True)
        session = PromptSession(
            history=FileHistory(str(historyFile)),
            completer=completer,
            complete_while_typing=False,
        )

        def _prompt():
            if state.company:
                msg = HTML(
                    f'\n<style fg="{_CLR}"><b>{state.company.corpName}</b></style><style fg="{_CLR_MUTED}"> &gt; </style>'
                )
            else:
                msg = HTML(f'\n<style fg="{_CLR}"><b>dartlab</b></style><style fg="{_CLR_MUTED}"> &gt; </style>')
            return session.prompt(msg)

        return _prompt
    except (ImportError, RuntimeError, OSError):
        return lambda: input(_buildPromptPlain(state))


def _buildPromptPlain(state: _ChatState) -> str:
    """Fallback plain-text prompt."""
    if state.company:
        return f"\n{state.company.corpName} > "
    return "\ndartlab > "


# ---------------------------------------------------------------------------
# Query execution
# ---------------------------------------------------------------------------


def _executeQuery(
    question: str,
    state: _ChatState,
    console,
    *,
    reportMode: bool = False,
    skillId: str | None = None,
) -> None:
    """Execute a query against the AI engine and stream the response."""
    from rich.console import Group
    from rich.live import Live
    from rich.markdown import Markdown
    from rich.spinner import Spinner
    from rich.text import Text

    from dartlab.ai.runtime.core import analyze

    # auto-compact long history
    if len(state.history) > 20:
        state.history = state.history[-12:]

    analyzeKwargs: dict[str, Any] = {
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
        analyzeKwargs["question_types"] = (skillId,)
    if state.cachedSnapshot:
        analyzeKwargs["snapshot"] = state.cachedSnapshot

    events = analyze(state.company, question, **analyzeKwargs)

    buffer = ""
    toolStartTime: float | None = None
    toolLines: list[str] = []
    toolPanels: list[str] = []
    queryStart = time.monotonic()
    queryToolCount = 0
    thinkingPhase = True

    try:
        with Live(console=console, refresh_per_second=10, vertical_overflow="visible", transient=True) as live:
            spinner = Spinner("dots", text=f"[{_CLR_MUTED}]Thinking...[/]", style=_CLR_MUTED)
            live.update(spinner)

            for ev in events:
                if ev.kind == "chunk":
                    thinkingPhase = False
                    buffer += ev.data["text"]
                    live.update(Markdown(buffer))

                elif ev.kind == "tool_call":
                    thinkingPhase = False
                    toolName = ev.data.get("name", "")
                    label = _toolLabel(toolName)
                    toolStartTime = time.monotonic()
                    state.toolCallCount += 1
                    queryToolCount += 1
                    toolSpinner = Spinner(
                        "dots", text=f"[{_CLR_MUTED}][{queryToolCount}] {label}...[/]", style=_CLR_MUTED
                    )
                    statusBlock = "\n".join(toolLines)
                    if statusBlock:
                        live.update(Group(Markdown(statusBlock), toolSpinner))
                    else:
                        live.update(toolSpinner)

                elif ev.kind == "tool_result":
                    toolName = ev.data.get("name", "")
                    label = _toolLabel(toolName)
                    elapsed = ""
                    if toolStartTime is not None:
                        dt = time.monotonic() - toolStartTime
                        elapsed = f" ({dt:.1f}s)"
                        toolStartTime = None
                    resultText = ev.data.get("result", "")
                    preview = _toolResultPreview(resultText)
                    line = f"> {label} done{elapsed}"
                    if preview:
                        line += f" -- {preview}"
                        toolPanels.append(resultText)
                    toolLines.append(line)
                    statusBlock = "\n".join(toolLines)
                    live.update(Markdown(statusBlock))

                elif ev.kind == "error":
                    errorMsg = ev.data.get("error", "Unknown error")
                    console.print(f"\n  [red]{errorMsg}[/]")
                    return
    except KeyboardInterrupt:
        console.print(f"\n  [{_CLR_MUTED}]Response interrupted[/]")

    # tool status log (compact)
    if toolLines:
        for tl in toolLines:
            console.print(f"  [{_CLR_MUTED}]{tl}[/]")

    # tool data tables
    if toolPanels:
        for panel in toolPanels:
            _renderToolData(panel, console)

    # final LLM response
    if buffer:
        console.print()
        console.print(Markdown(buffer))

    console.print()

    totalElapsed = time.monotonic() - queryStart
    footerParts = [f"{totalElapsed:.1f}s"]
    if queryToolCount > 0:
        footerParts.append(f"{queryToolCount} tool call{'s' if queryToolCount != 1 else ''}")
    console.print(Text("  " + "  |  ".join(footerParts), style="dim"))

    if buffer:
        state.history.append({"role": "user", "content": question})
        state.history.append({"role": "assistant", "content": buffer})
        state.queryCount += 1
        _saveMessage(state, "user", question)
        _saveMessage(state, "assistant", buffer)

        # follow-up suggestions (selectable by number)
        state.lastFollowUps = []
        if state.company and state.queryCount >= 1:
            followUps = _generateFollowUps(buffer, skillId)
            if followUps:
                state.lastFollowUps = followUps
                console.print()
                for i, fq in enumerate(followUps, 1):
                    console.print(f"  [{_CLR_MUTED}]{i}. {fq}[/]")


def _toolResultPreview(resultText: str) -> str:
    """Extract a one-line preview from tool result text."""
    if not resultText or resultText.startswith("[Error]") or resultText.startswith("["):
        return ""
    lines = resultText.strip().splitlines()
    tableRows = [ln for ln in lines if ln.startswith("|") and "---" not in ln]
    if len(tableRows) > 1:
        return f"{len(tableRows) - 1} rows"
    firstLine = lines[0].strip().lstrip("#").strip() if lines else ""
    if len(firstLine) > 60:
        firstLine = firstLine[:57] + "..."
    return firstLine


def _renderToolData(resultText: str, console) -> None:
    """Render tool result data — Rich Table for tables, Markdown panel fallback."""
    from dartlab.cli.rendering import renderToolResult

    if renderToolResult(resultText, console):
        return

    # fallback: markdown panel for non-table content
    from rich.markdown import Markdown
    from rich.panel import Panel

    lines = resultText.strip().splitlines()
    hasTable = any(ln.startswith("|") for ln in lines)
    if hasTable:
        if len(lines) > 30:
            truncated = "\n".join(lines[:30]) + f"\n\n... (+{len(lines) - 30} lines)"
        else:
            truncated = resultText.strip()
        console.print(Panel(Markdown(truncated), border_style="dim", padding=(0, 1)))


def _toolLabel(toolName: str) -> str:
    """Resolve tool name to display label."""
    return _TOOL_LABELS.get(toolName, toolName)


# ---------------------------------------------------------------------------
# Company management
# ---------------------------------------------------------------------------


def _loadCompany(state: _ChatState, identifier: str, console, *, quiet: bool = False) -> bool:
    """Load a company by stock code or name."""
    import dartlab

    state.company = None

    try:
        company = dartlab.Company(identifier)
    except (ValueError, FileNotFoundError, OSError, RuntimeError):
        from dartlab.core.resolve import resolve_from_text

        company, _ = resolve_from_text(identifier)

    if company is None:
        console.print(f"  [red]Company not found: {identifier}[/]")
        return False

    state.company = company
    state.stockCode = company.stockCode
    state.cachedSnapshot = None
    if company.corpName not in state.companiesUsed:
        state.companiesUsed.append(company.corpName)
    if not quiet:
        console.print(f"  [bold]{company.corpName}[/] ({company.stockCode}) loaded")
    _displaySnapshot(company, state, console)
    return True


def _tryAutoDetect(userInput: str, state: _ChatState, console) -> None:
    """Try to auto-detect a company from user input text."""
    from dartlab.core.resolve import resolve_from_text

    company, _ = resolve_from_text(userInput)
    if company is not None:
        state.company = company
        state.stockCode = company.stockCode
        state.cachedSnapshot = None
        if company.corpName not in state.companiesUsed:
            state.companiesUsed.append(company.corpName)
        console.print(f"  [{_CLR_MUTED}]{company.corpName} ({company.stockCode}) auto-detected[/]")


def _displaySnapshot(company: Any, state: _ChatState, console) -> None:
    """Show key metrics snapshot when a company loads."""
    try:
        from dartlab.ai.context.snapshot import build_snapshot

        snap = build_snapshot(company, includeInsights=False)
        if snap is None:
            return
        items = snap.get("items", [])
        if not items:
            return
        state.cachedSnapshot = snap
        from dartlab.cli.rendering import renderSnapshot

        renderSnapshot(items, console)
    except (ImportError, AttributeError, KeyError, OSError):
        pass


# ---------------------------------------------------------------------------
# Slash commands — dispatcher
# ---------------------------------------------------------------------------


def _handleSlash(userInput: str, state: _ChatState, console) -> bool:
    """Dispatch slash command. Returns True if session should exit."""
    parts = userInput.split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1].strip() if len(parts) > 1 else ""

    # resolve aliases
    aliasMap: dict[str, str] = {}
    for name, aliases, _ in _COMMANDS:
        aliasMap[name] = name
        for alias in aliases:
            aliasMap[alias] = name
    resolved = aliasMap.get(cmd)

    if resolved == "/quit":
        console.print(f"  [{_CLR_MUTED}]Exiting chat.[/]")
        return True

    handlers = {
        "/help": _cmdHelp,
        "/company": _cmdCompany,
        "/model": _cmdModel,
        "/provider": _cmdProvider,
        "/clear": _cmdClear,
        "/suggest": _cmdSuggest,
        "/status": _cmdStatus,
        "/cost": _cmdCost,
        "/export": _cmdExport,
        "/history": _cmdHistory,
        "/compact": _cmdCompact,
        "/report": _cmdReport,
    }

    handler = handlers.get(resolved)  # type: ignore[arg-type]
    if handler:
        handler(arg, state, console)
        return False

    # check skill commands
    for skillCmd, skillId, _ in _SKILL_COMMANDS:
        if cmd == skillCmd:
            _cmdSkill(skillId, arg, state, console)
            return False

    console.print(f"  [{_CLR_WARN}]Unknown command: {cmd}[/]  /help for available commands")

    return False


# ---------------------------------------------------------------------------
# Slash command handlers
# ---------------------------------------------------------------------------


def _cmdHelp(_arg: str, _state: _ChatState, console) -> None:
    from rich.text import Text

    console.print()
    console.print("  [bold]Commands[/]")
    console.print(f"  [{_CLR_MUTED}]{'─' * 44}[/]")
    for name, aliases, desc in _COMMANDS:
        label = Text()
        label.append(f"  {name}", style="bold")
        aliasStr = ""
        if aliases:
            aliasStr = f"  {', '.join(aliases)}"
            label.append(aliasStr, style="dim")
        pad = 22 - len(name) - len(aliasStr)
        label.append(" " * max(pad, 1))
        label.append(desc, style="dim")
        console.print(label)

    console.print()
    console.print(f"  [bold]Skills[/] [{_CLR_MUTED}]load a company first[/]")
    console.print(f"  [{_CLR_MUTED}]{'─' * 44}[/]")
    for cmdName, _, desc in _SKILL_COMMANDS:
        label = Text()
        label.append(f"  {cmdName}", style="bold")
        pad = 22 - len(cmdName)
        label.append(" " * max(pad, 1))
        label.append(desc, style="dim")
        console.print(label)

    console.print()
    tipLine = Text()
    tipLine.append("  /", style=f"bold {_CLR_MUTED}")
    tipLine.append(" this menu", style="dim")
    tipLine.append("    exit", style=_CLR_MUTED)
    tipLine.append(" quit without slash", style="dim")
    console.print(tipLine)
    console.print()


def _cmdCompany(arg: str, state: _ChatState, console) -> None:
    if not arg:
        if state.company:
            console.print(f"  current: [bold]{state.company.corpName}[/] ({state.stockCode})")
        else:
            console.print(f"  [{_CLR_MUTED}]No company loaded. Use /company <name or code>[/]")
        return

    if arg.lower() in ("none", "clear"):
        state.company = None
        state.stockCode = None
        state.cachedSnapshot = None
        state.history.clear()
        state.sessionId = None
        console.print(f"  [{_CLR_MUTED}]Company cleared. Switched to general mode.[/]")
        return

    hadCompany = state.company is not None
    if _loadCompany(state, arg, console):
        if hadCompany:
            state.history.clear()
            state.sessionId = None
            console.print(f"  [{_CLR_MUTED}]Conversation cleared due to company change.[/]")
    else:
        # show search candidates
        _showCompanyCandidates(arg, state, console)


def _showCompanyCandidates(keyword: str, state: _ChatState, console) -> None:
    """Show search results when exact match fails."""
    try:
        from dartlab.gather.listing import searchName

        results = searchName(keyword)
        if results is None or len(results) == 0:
            return

        maxShow = min(len(results), 8)
        console.print()
        console.print(f'  [bold {_CLR}]"{keyword}"[/] [{_CLR_MUTED}]search results[/]')
        console.print()

        candidates = []
        for i in range(maxShow):
            row = results.row(i, named=True)
            name = row.get("회사명", "")
            code = row.get("종목코드", "")
            industry = row.get("업종명", "")
            if industry and len(industry) > 16:
                industry = industry[:14] + ".."
            candidates.append((code, name))
            console.print(f"    {i + 1}. [bold]{name:<16s}[/] [{_CLR_MUTED}]{code}[/]    [{_CLR_MUTED}]{industry}[/]")

        if len(results) > maxShow:
            console.print(f"    [{_CLR_MUTED}](+{len(results) - maxShow} more)[/]")

        console.print()
        console.print(f"  [{_CLR_MUTED}]Type number to select:[/]")

        try:
            choice = input("  > ").strip()
        except (EOFError, KeyboardInterrupt):
            return
        if not choice:
            return

        if choice.isdigit() and 1 <= int(choice) <= len(candidates):
            code, _ = candidates[int(choice) - 1]
            hadCompany = state.company is not None
            if _loadCompany(state, code, console):
                if hadCompany:
                    state.history.clear()
                    state.sessionId = None
                    console.print(f"  [{_CLR_MUTED}]Conversation cleared due to company change.[/]")
    except (ImportError, OSError):
        pass


def _cmdModel(arg: str, state: _ChatState, console) -> None:
    if arg:
        state.model = arg
        console.print(f"  model -> [bold]{arg}[/]")
        return

    # interactive model selection
    models = _getRecommendedModels(state.provider)
    if not models:
        console.print(f"  model: {state.model or '(default)'}")
        console.print(f"  [{_CLR_MUTED}]Type /model <name> to change[/]")
        return

    console.print()
    console.print(f"  [bold {_CLR}]{state.provider}[/] models")
    console.print()
    for i, (name, desc) in enumerate(models, 1):
        marker = f"[{_CLR}]*[/]" if name == (state.model or models[0][0]) else " "
        console.print(f"  {marker} {i}. [bold]{name:<24s}[/] [{_CLR_MUTED}]{desc}[/]")
    console.print()
    console.print(f"  [{_CLR_MUTED}]Type number or model name (current: {state.model or 'default'}):[/]")

    try:
        choice = input("  > ").strip()
    except (EOFError, KeyboardInterrupt):
        return
    if not choice:
        return
    if choice.isdigit() and 1 <= int(choice) <= len(models):
        state.model = models[int(choice) - 1][0]
    else:
        state.model = choice
    console.print(f"  model -> [bold]{state.model}[/]")


def _getRecommendedModels(providerId: str | None) -> list[tuple[str, str]]:
    """Return recommended (model_name, description) pairs for a provider."""
    _MODEL_MAP: dict[str, list[tuple[str, str]]] = {
        "openai": [
            ("gpt-4o", "Fast + tool use (recommended)"),
            ("gpt-4o-mini", "Budget-friendly"),
            ("o1", "Deep reasoning"),
            ("o3-mini", "Reasoning + budget"),
        ],
        "gemini": [
            ("gemini-2.5-pro", "Best quality (free)"),
            ("gemini-2.5-flash", "Fast (free)"),
        ],
        "groq": [
            ("llama-3.3-70b-versatile", "Fast inference (free)"),
            ("llama-3.1-8b-instant", "Ultra-fast (free)"),
        ],
        "cerebras": [
            ("llama-3.3-70b", "Fast inference (free)"),
        ],
        "mistral": [
            ("mistral-small-latest", "Balanced (free)"),
            ("mistral-large-latest", "Best quality"),
        ],
        "oauth-codex": [
            ("gpt-5.4", "Latest (ChatGPT Plus)"),
            ("gpt-5.3-codex", "Codex optimized"),
        ],
    }
    return _MODEL_MAP.get(providerId or "", [])


def _cmdProvider(arg: str, state: _ChatState, console) -> None:
    if arg:
        if arg in PROVIDERS:
            state.provider = arg
            state.model = None
            console.print(f"  provider -> [bold]{arg}[/]")
        else:
            console.print(f"  [{_CLR_WARN}]Unknown provider: {arg}[/]")
            console.print(f"  [{_CLR_MUTED}]available: {', '.join(PROVIDERS)}[/]")
        return

    # interactive provider selection
    from dartlab.core.ai.providers import get_provider_spec

    console.print()
    console.print(f"  [bold {_CLR}]Provider[/]")
    console.print()

    providerList = list(PROVIDERS)
    for i, pid in enumerate(providerList, 1):
        spec = get_provider_spec(pid)
        label = spec.label if spec else pid
        hint = ""
        if spec and spec.freeTierHint:
            hint = f"[{_CLR_SUCCESS}]{spec.freeTierHint}[/]"
        marker = f"[{_CLR}]*[/]" if pid == state.provider else " "
        console.print(f"  {marker} {i}. [bold]{pid:<16s}[/] [{_CLR_MUTED}]{label}[/]  {hint}")

    console.print()
    console.print(f"  [{_CLR_MUTED}]Type number or name (current: {state.provider}):[/]")

    try:
        choice = input("  > ").strip()
    except (EOFError, KeyboardInterrupt):
        return
    if not choice:
        return

    selected = None
    if choice.isdigit() and 1 <= int(choice) <= len(providerList):
        selected = providerList[int(choice) - 1]
    elif choice in PROVIDERS:
        selected = choice

    if selected:
        state.provider = selected
        state.model = None
        console.print(f"  provider -> [bold]{selected}[/]")
    else:
        console.print(f"  [{_CLR_WARN}]Unknown provider: {choice}[/]")


def _cmdClear(_arg: str, state: _ChatState, console) -> None:
    state.history.clear()
    state.sessionId = None
    console.print(f"  [{_CLR_MUTED}]Conversation cleared.[/]")


def _cmdSuggest(_arg: str, state: _ChatState, console) -> None:
    questions = _SUGGESTIONS
    if state.company:
        try:
            from dartlab.ai.conversation.suggestions import suggestQuestions

            engineQuestions = suggestQuestions(state.company)
            if engineQuestions:
                questions = engineQuestions
        except (ImportError, AttributeError):
            pass

    console.print()
    for i, q in enumerate(questions, 1):
        console.print(f"  [{_CLR_MUTED}]{i}.[/] {q}")
    console.print()


def _cmdStatus(_arg: str, state: _ChatState, console) -> None:
    mode = "general (no company)" if state.company is None else f"analysis ({state.company.corpName})"
    console.print(f"  mode:     {mode}")
    console.print(f"  provider: [bold]{state.provider}[/]")
    console.print(f"  model:    {state.model or '(default)'}")
    console.print(f"  history:  {len(state.history)} messages")
    console.print(f"  queries:  {state.queryCount}")
    console.print(f"  tools:    {state.toolCallCount} calls")


def _cmdCost(_arg: str, _state: _ChatState, console) -> None:
    try:
        from dartlab.cli.services.history import get_total_usage

        usage = get_total_usage()
        console.print(f"  total requests:  {usage.get('total_requests', 0)}")
        console.print(f"  input tokens:    {usage.get('input_tokens', 0):,}")
        console.print(f"  output tokens:   {usage.get('output_tokens', 0):,}")
        costUsd = usage.get("cost_usd", 0)
        if costUsd > 0:
            console.print(f"  estimated cost:  ${costUsd:.4f}")
    except (ImportError, OSError):
        console.print(f"  [{_CLR_MUTED}]Usage data not available.[/]")


def _cmdExport(arg: str, state: _ChatState, console) -> None:
    if not state.history:
        console.print(f"  [{_CLR_MUTED}]No conversation to export.[/]")
        return

    path = arg or f"dartlab_chat_{datetime.now():%Y%m%d_%H%M%S}.md"

    lines = ["# DartLab Chat Export", f"Date: {datetime.now():%Y-%m-%d %H:%M}", ""]
    if state.company:
        lines.append(f"Company: {state.company.corpName} ({state.stockCode})")
        lines.append("")
    lines.append(f"Provider: {state.provider} | Model: {state.model or 'default'}")
    lines.append(f"Queries: {state.queryCount} | Tool calls: {state.toolCallCount}")
    lines.append("")
    lines.append("---")
    lines.append("")

    for msg in state.history:
        role = "You" if msg["role"] == "user" else "DartLab"
        lines.append(f"## {role}")
        lines.append("")
        lines.append(msg["content"])
        lines.append("")

    Path(path).write_text("\n".join(lines), encoding="utf-8")
    console.print(f"  Exported to [bold]{path}[/]")


def _cmdHistory(arg: str, state: _ChatState, console) -> None:
    n = int(arg) if arg and arg.isdigit() else 5
    recent = state.history[-(n * 2) :]
    if not recent:
        console.print(f"  [{_CLR_MUTED}]No conversation history.[/]")
        return

    console.print()
    for msg in recent:
        role = "You" if msg["role"] == "user" else "DartLab"
        style = f"bold {_CLR}" if msg["role"] == "user" else _CLR_MUTED
        content = msg["content"]
        if len(content) > 120:
            content = content[:117] + "..."
        console.print(f"  [{style}]{role}:[/] {content}")
    console.print()


def _cmdCompact(_arg: str, state: _ChatState, console) -> None:
    if len(state.history) <= 6:
        console.print(f"  [{_CLR_MUTED}]History too short to compact.[/]")
        return

    dropped = len(state.history) - 6
    state.history = state.history[-6:]
    console.print(f"  [{_CLR_MUTED}]Compacted: dropped {dropped} messages, kept {len(state.history)}[/]")


def _cmdSkill(skillId: str, arg: str, state: _ChatState, console) -> None:
    """Run an analysis skill command."""
    question = arg or _SKILL_DEFAULT_QUESTIONS.get(skillId, "Analyze this company")
    if state.company is None:
        console.print(f"  [{_CLR_MUTED}]No company loaded — LLM will search via tools[/]")
    console.print(f"  [{_CLR_ACCENT}]Running {skillId} analysis...[/]")
    _executeQuery(question, state, console, skillId=skillId)


def _cmdReport(arg: str, state: _ChatState, console) -> None:
    question = arg or "Provide a comprehensive investment analysis report"
    if state.company is None:
        console.print(f"  [{_CLR_MUTED}]No company loaded — LLM will search via tools[/]")
    console.print(f"  [{_CLR_ACCENT}]Running deep analysis (report mode)...[/]")
    _executeQuery(question, state, console, reportMode=True)


# ---------------------------------------------------------------------------
# Follow-up suggestions (rule-based, no LLM call)
# ---------------------------------------------------------------------------

_FOLLOWUP_MAP: dict[str, list[str]] = {
    "profitability": ["/health -- Check financial health", "/valuation -- Assess valuation"],
    "health": ["/risk -- Identify risk factors", "/valuation -- Evaluate fair value"],
    "valuation": ["/profitability -- Analyze earnings quality", "/risk -- Check risks"],
    "risk": ["/health -- Verify financial resilience", "/strategy -- Review business model"],
    "strategy": ["/profitability -- Check profitability", "/comprehensive -- Full analysis"],
    "accounting": ["/risk -- Check related risks", "/profitability -- Earnings quality"],
    "dividend": ["/health -- Dividend sustainability", "/valuation -- Fair value range"],
    "comprehensive": [],
}

_KEYWORD_FOLLOWUPS: list[tuple[str, str]] = [
    ("margin", "/profitability -- Deep dive into margins"),
    ("debt", "/health -- Financial health analysis"),
    ("valuation", "/valuation -- Detailed valuation"),
    ("risk", "/risk -- Risk assessment"),
    ("dividend", "/dividend -- Dividend sustainability"),
    ("growth", "/strategy -- Growth strategy analysis"),
]


def _generateFollowUps(response: str, skillId: str | None) -> list[str]:
    """Generate 2-3 follow-up suggestions based on response content."""
    if skillId and skillId in _FOLLOWUP_MAP:
        return _FOLLOWUP_MAP[skillId][:2]

    responseLower = response.lower()
    suggestions: list[str] = []
    for keyword, suggestion in _KEYWORD_FOLLOWUPS:
        if keyword in responseLower and len(suggestions) < 2:
            suggestions.append(suggestion)
    return suggestions


# ---------------------------------------------------------------------------
# Session summary
# ---------------------------------------------------------------------------


def _printSessionSummary(state: _ChatState, console) -> None:
    """Print session statistics on exit."""
    from rich.rule import Rule

    elapsed = time.monotonic() - state.startTime
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)

    console.print()
    console.print(Rule(style="dim"))

    timeStr = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"

    parts = [f"[dim]{timeStr}[/]"]
    if state.queryCount > 0:
        parts.append(f"[dim]{state.queryCount} {'queries' if state.queryCount != 1 else 'query'}[/]")
    if state.toolCallCount > 0:
        parts.append(f"[dim]{state.toolCallCount} tool calls[/]")
    if state.companiesUsed:
        names = ", ".join(state.companiesUsed)
        parts.append(f"[dim]{names}[/]")

    console.print("  " + "  |  ".join(parts))
    console.print()


# ---------------------------------------------------------------------------
# Session persistence
# ---------------------------------------------------------------------------


def _saveMessage(state: _ChatState, role: str, content: str) -> None:
    """Persist a message to the SQLite history database."""
    try:
        from dartlab.cli.services.history import add_message, create_session

        if state.sessionId is None:
            stockCode = state.stockCode or "__no_company__"
            state.sessionId = create_session(stockCode)
        add_message(state.sessionId, role, content)
    except (OSError, ImportError):
        pass


def _resumeSession(state: _ChatState, console) -> None:
    """Resume the latest session for the current company."""
    try:
        from dartlab.cli.services.history import get_latest_session, get_messages

        sessionId = get_latest_session(state.stockCode)
        if sessionId:
            state.sessionId = sessionId
            state.history = get_messages(sessionId)
            console.print(f"  [{_CLR_MUTED}]Resuming previous session ({len(state.history)} messages)[/]")
    except (OSError, ImportError):
        pass


# ---------------------------------------------------------------------------
# Welcome
# ---------------------------------------------------------------------------


def _printWelcome(state: _ChatState, console) -> None:
    """Print the branded welcome screen."""
    from rich import box
    from rich.panel import Panel
    from rich.text import Text

    try:
        from importlib.metadata import PackageNotFoundError
        from importlib.metadata import version as pkgVersion

        ver = pkgVersion("dartlab")
    except PackageNotFoundError:
        ver = "dev"

    # -- header panel --
    modelDisplay = state.model or "default"
    providerDisplay = state.provider or "none"

    header = Text()
    header.append("DartLab", style=f"bold {_CLR}")
    header.append("\n")
    header.append("Every company tells its story in filings.", style=_CLR_MUTED)
    header.append("\n")
    header.append("We make it readable.", style=_CLR_MUTED)
    header.append("\n")
    header.append(f"\n{providerDisplay}", style="bold")
    header.append(f"  {modelDisplay}", style="dim")
    header.append(f"        v{ver}", style="dim")

    console.print()
    console.print(Panel(header, box=box.ROUNDED, border_style="dim", padding=(1, 3), expand=False))

    if state.company:
        console.print(f"  [bold]{state.company.corpName}[/] [{_CLR_MUTED}]{state.stockCode}[/]")
        console.print()
        hints = Text()
        hints.append("  Try: ", style="dim")
        for i, cmd in enumerate(("/comprehensive", "/profitability", "/health", "/valuation")):
            if i > 0:
                hints.append("  ", style="dim")
            hints.append(cmd, style=_CLR_MUTED)
        console.print(hints)
    else:
        console.print(
            f"  [{_CLR_MUTED}]Type a question, or[/] [bold]/company[/] [{_CLR_MUTED}]<name> to load a company[/]"
        )

    console.print()
    tipLine = Text()
    tipLine.append("  /", style=f"bold {_CLR_MUTED}")
    tipLine.append(" commands", style="dim")
    tipLine.append("    Ctrl+C", style=_CLR_MUTED)
    tipLine.append(" x2 exit", style="dim")
    console.print(tipLine)
    console.print()


def _printSetupGuide(console) -> None:
    """Show provider setup guide when no provider is detected."""
    console.print(f"  [{_CLR_WARN}]No LLM provider detected.[/]")
    console.print()
    console.print(f"  [{_CLR_MUTED}]Free options:[/]")
    console.print(f"    [bold]dartlab setup gemini[/]     [{_CLR_MUTED}]Google AI Studio (free, Gemini 2.5)[/]")
    console.print(f"    [bold]dartlab setup groq[/]       [{_CLR_MUTED}]Groq (free, ultra-fast)[/]")
    console.print()
    console.print(f"  [{_CLR_MUTED}]Premium:[/]")
    console.print(f"    [bold]dartlab setup openai[/]     [{_CLR_MUTED}]OpenAI API key[/]")
    console.print(f"    [bold]dartlab setup ollama[/]     [{_CLR_MUTED}]Local models (offline)[/]")
    console.print()
    console.print(f"  [{_CLR_MUTED}]Or type /provider in chat to switch[/]")
    console.print()
