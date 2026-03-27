"""`dartlab chat` command -- 인터랙티브 터미널 REPL."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dartlab.cli.context import PROVIDERS
from dartlab.cli.services.errors import CLIError
from dartlab.cli.services.providers import detect_provider
from dartlab.cli.services.runtime import configure_dartlab


def configure_parser(subparsers) -> None:
    parser = subparsers.add_parser("chat", help="대화형 AI 분석 (인터랙티브 REPL)")
    parser.add_argument("company", nargs="?", default=None, help="종목코드 또는 회사명 (생략 가능)")
    parser.add_argument("--provider", "-p", default=None, choices=PROVIDERS, help="LLM provider")
    parser.add_argument("--model", "-m", default=None, help="모델명")
    parser.add_argument("--base-url", default=None, help="커스텀 API URL")
    parser.add_argument("--api-key", default=None, help="API 키")
    parser.add_argument("--continue", dest="cont", action="store_true", help="이전 대화 이어가기")
    parser.set_defaults(handler=run)


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

@dataclass
class _ChatState:
    """REPL 세션 상태."""

    company: Any | None = None
    stockCode: str | None = None
    provider: str | None = None
    model: str | None = None
    baseUrl: str | None = None
    apiKey: str | None = None
    sessionId: int | None = None
    history: list[dict[str, str]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------

def run(args) -> int:
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
        if not _loadCompany(state, args.company, console):
            raise CLIError(f"종목을 찾을 수 없습니다: {args.company}")

    if args.cont and state.stockCode:
        _resumeSession(state, console)

    _printWelcome(state, console)
    _replLoop(state, console)
    return 0


# ---------------------------------------------------------------------------
# REPL loop
# ---------------------------------------------------------------------------

_SLASH_WORDS = ["/help", "/company", "/model", "/clear", "/suggest", "/status", "/quit", "/exit", "/q"]


def _replLoop(state: _ChatState, console) -> None:
    promptFn = _makePromptFn()

    while True:
        prompt = _buildPrompt(state)
        try:
            userInput = promptFn(prompt)
        except KeyboardInterrupt:
            continue
        except EOFError:
            console.print("\n[dim]채팅을 종료합니다.[/]")
            break

        userInput = userInput.strip()
        if not userInput:
            continue

        if userInput.startswith("/"):
            shouldExit = _handleSlash(userInput, state, console)
            if shouldExit:
                break
            continue

        # 종목 없으면 텍스트에서 자동 감지 시도
        if state.company is None:
            _tryAutoDetect(userInput, state, console)

        _executeQuery(userInput, state, console)


def _makePromptFn():
    """prompt_toolkit PromptSession을 반환. 터미널이 아니면 input() fallback."""
    try:
        import sys

        if not sys.stdin.isatty():
            return input

        from prompt_toolkit import PromptSession
        from prompt_toolkit.completion import WordCompleter
        from prompt_toolkit.history import FileHistory

        historyDir = Path.home() / ".dartlab"
        historyDir.mkdir(parents=True, exist_ok=True)
        historyFile = historyDir / "chat.history"

        completer = WordCompleter(_SLASH_WORDS, sentence=True)
        session = PromptSession(
            history=FileHistory(str(historyFile)),
            completer=completer,
        )
        return session.prompt
    except (ImportError, RuntimeError, OSError):
        return input


def _buildPrompt(state: _ChatState) -> str:
    if state.company:
        return f"\ndartlab {state.company.corpName} > "
    return "\ndartlab > "


# ---------------------------------------------------------------------------
# Query execution
# ---------------------------------------------------------------------------

def _executeQuery(question: str, state: _ChatState, console) -> None:
    from rich.live import Live
    from rich.markdown import Markdown
    from rich.text import Text

    from dartlab.ai.runtime.core import analyze

    events = analyze(
        state.company,
        question,
        provider=state.provider,
        model=state.model,
        base_url=state.baseUrl,
        api_key=state.apiKey,
        use_tools=True,
        history=state.history if state.history else None,
    )

    buffer = ""
    toolStartTime: float | None = None
    toolPanels: list[str] = []  # tool 결과 데이터 누적 (LLM 응답 전 표시)
    queryStart = time.monotonic()

    try:
        with Live(console=console, refresh_per_second=8, vertical_overflow="visible") as live:
            for ev in events:
                if ev.kind == "chunk":
                    buffer += ev.data["text"]
                    live.update(Markdown(buffer))
                elif ev.kind == "tool_call":
                    toolName = ev.data.get("name", "")
                    label = _toolLabel(toolName)
                    toolStartTime = time.monotonic()
                    live.update(Markdown(buffer + f"\n\n> {label} 조회 중..."))
                elif ev.kind == "tool_result":
                    toolName = ev.data.get("name", "")
                    label = _toolLabel(toolName)
                    elapsed = ""
                    if toolStartTime is not None:
                        dt = time.monotonic() - toolStartTime
                        elapsed = f" ({dt:.1f}s)"
                        toolStartTime = None
                    # tool 결과 데이터 수집
                    resultText = ev.data.get("result", "")
                    preview = _toolResultPreview(resultText)
                    statusLine = f"> {label} 완료{elapsed}"
                    if preview:
                        statusLine += f" -- {preview}"
                        toolPanels.append(resultText)
                    live.update(Markdown(buffer + f"\n\n{statusLine}"))
                elif ev.kind == "error":
                    errorMsg = ev.data.get("error", "알 수 없는 오류")
                    console.print(f"\n  [red]{errorMsg}[/]")
                    return
    except KeyboardInterrupt:
        console.print("\n  [dim]응답 중단[/]")

    # tool 결과 데이터 인라인 표시 (LLM 응답 전에 나온 테이블)
    if toolPanels:
        console.print()
        for panel in toolPanels:
            _renderToolData(panel, console)

    console.print()

    # done 요약 (소요 시간)
    totalElapsed = time.monotonic() - queryStart
    console.print(Text(f"  {totalElapsed:.1f}s", style="dim"))

    if buffer:
        state.history.append({"role": "user", "content": question})
        state.history.append({"role": "assistant", "content": buffer})
        _saveMessage(state, "user", question)
        _saveMessage(state, "assistant", buffer)


def _toolResultPreview(resultText: str) -> str:
    """tool 결과 텍스트에서 한 줄 요약을 추출한다."""
    if not resultText or resultText.startswith("[오류]"):
        return ""
    lines = resultText.strip().splitlines()
    # markdown 테이블이 있으면 행 수 표시
    tableRows = [ln for ln in lines if ln.startswith("|") and "---" not in ln]
    if len(tableRows) > 1:
        return f"{len(tableRows) - 1}행"  # 헤더 제외
    # 일반 텍스트면 첫 줄 앞부분
    firstLine = lines[0].strip().lstrip("#").strip() if lines else ""
    if len(firstLine) > 60:
        firstLine = firstLine[:57] + "..."
    return firstLine


def _renderToolData(resultText: str, console) -> None:
    """tool 결과를 Rich로 렌더링한다 (markdown 테이블 포함)."""
    from rich.markdown import Markdown
    from rich.panel import Panel

    # markdown 테이블이 포함된 경우 패널로 감싸서 표시
    lines = resultText.strip().splitlines()
    hasTable = any(ln.startswith("|") for ln in lines)
    if hasTable:
        # 너무 길면 앞부분만 (최대 30줄)
        if len(lines) > 30:
            truncated = "\n".join(lines[:30]) + f"\n\n... (+{len(lines) - 30}줄)"
        else:
            truncated = resultText.strip()
        console.print(Panel(Markdown(truncated), border_style="dim", padding=(0, 1)))


_TOOL_LABELS = {
    "explore": "공시 탐색",
    "finance": "재무 데이터",
    "analyze": "분석 엔진",
    "market": "시장 데이터",
    "openapi": "OpenDART API",
    "system": "시스템 정보",
    "chart": "차트 생성",
}


def _toolLabel(toolName: str) -> str:
    return _TOOL_LABELS.get(toolName, toolName)


# ---------------------------------------------------------------------------
# Company management
# ---------------------------------------------------------------------------

def _loadCompany(state: _ChatState, identifier: str, console) -> bool:
    import dartlab

    state.company = None  # GC 유도

    try:
        company = dartlab.Company(identifier)
    except (ValueError, FileNotFoundError, OSError, RuntimeError):
        from dartlab.core.resolve import resolve_from_text

        company, _ = resolve_from_text(identifier)

    if company is None:
        console.print(f"  [red]종목을 찾을 수 없습니다: {identifier}[/]")
        return False

    state.company = company
    state.stockCode = company.stockCode
    console.print(f"  [bold]{company.corpName}[/] ({company.stockCode}) 로드 완료")
    return True


def _tryAutoDetect(userInput: str, state: _ChatState, console) -> None:
    from dartlab.core.resolve import resolve_from_text

    company, _ = resolve_from_text(userInput)
    if company is not None:
        state.company = company
        state.stockCode = company.stockCode
        console.print(f"  [dim]{company.corpName} ({company.stockCode}) 자동 감지[/]")


# ---------------------------------------------------------------------------
# Slash commands
# ---------------------------------------------------------------------------

def _handleSlash(userInput: str, state: _ChatState, console) -> bool:
    parts = userInput.split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1].strip() if len(parts) > 1 else ""

    if cmd in ("/quit", "/exit", "/q"):
        console.print("[dim]채팅을 종료합니다.[/]")
        return True

    handlers = {
        "/help": _cmdHelp,
        "/company": _cmdCompany,
        "/model": _cmdModel,
        "/clear": _cmdClear,
        "/suggest": _cmdSuggest,
        "/status": _cmdStatus,
    }

    handler = handlers.get(cmd)
    if handler:
        handler(arg, state, console)
    else:
        console.print(f"  [yellow]알 수 없는 명령: {cmd}[/]  /help 로 사용법 확인")

    return False


def _cmdHelp(_arg: str, _state: _ChatState, console) -> None:
    console.print("""
  [bold]명령어[/]
    /help                이 도움말
    /company <이름/코드>   종목 변경
    /model <이름>         모델/provider 변경
    /clear               대화 기록 초기화
    /suggest             추천 질문
    /status              현재 설정
    /quit                종료
""")


def _cmdCompany(arg: str, state: _ChatState, console) -> None:
    if not arg:
        if state.company:
            console.print(f"  현재: [bold]{state.company.corpName}[/] ({state.stockCode})")
        else:
            console.print("  [dim]로드된 종목이 없습니다. /company 삼성전자[/]")
        return

    hadCompany = state.company is not None
    if _loadCompany(state, arg, console):
        if hadCompany:
            state.history.clear()
            state.sessionId = None
            console.print("  [dim]종목 변경으로 대화 기록이 초기화되었습니다.[/]")


def _cmdModel(arg: str, state: _ChatState, console) -> None:
    if not arg:
        console.print(f"  provider: [bold]{state.provider}[/]")
        console.print(f"  model: {state.model or '(기본값)'}")
        return

    if arg in PROVIDERS:
        state.provider = arg
        state.model = None
        console.print(f"  provider -> [bold]{arg}[/]")
    else:
        state.model = arg
        console.print(f"  model -> [bold]{arg}[/]")


def _cmdClear(_arg: str, state: _ChatState, console) -> None:
    state.history.clear()
    state.sessionId = None
    console.print("  [dim]대화 기록이 초기화되었습니다.[/]")


def _cmdSuggest(_arg: str, state: _ChatState, console) -> None:
    if state.company is None:
        console.print("  [dim]종목을 먼저 로드하세요. /company 삼성전자[/]")
        return

    from dartlab.ai.conversation.suggestions import suggestQuestions

    questions = suggestQuestions(state.company)
    for i, q in enumerate(questions, 1):
        console.print(f"  [cyan]{i}.[/] {q}")


def _cmdStatus(_arg: str, state: _ChatState, console) -> None:
    console.print(f"  provider: [bold]{state.provider}[/]")
    console.print(f"  model: {state.model or '(기본값)'}")
    if state.company:
        console.print(f"  company: [bold]{state.company.corpName}[/] ({state.stockCode})")
    else:
        console.print("  company: (없음)")
    console.print(f"  history: {len(state.history)}개 메시지")


# ---------------------------------------------------------------------------
# Session persistence
# ---------------------------------------------------------------------------

def _saveMessage(state: _ChatState, role: str, content: str) -> None:
    try:
        from dartlab.cli.services.history import add_message, create_session

        if state.sessionId is None:
            stockCode = state.stockCode or "__no_company__"
            state.sessionId = create_session(stockCode)
        add_message(state.sessionId, role, content)
    except (OSError, ImportError):
        pass


def _resumeSession(state: _ChatState, console) -> None:
    try:
        from dartlab.cli.services.history import get_latest_session, get_messages

        sessionId = get_latest_session(state.stockCode)
        if sessionId:
            state.sessionId = sessionId
            state.history = get_messages(sessionId)
            console.print(f"  [dim]이전 대화 이어가기 (메시지 {len(state.history)}개)[/]")
    except (OSError, ImportError):
        pass


# ---------------------------------------------------------------------------
# Welcome
# ---------------------------------------------------------------------------

def _printWelcome(state: _ChatState, console) -> None:
    console.print()
    console.print("  [bold cyan]DartLab Chat[/]  --  대화형 AI 기업 분석")
    providerLine = f"  [dim]provider: {state.provider}"
    if state.model:
        providerLine += f" / {state.model}"
    providerLine += "[/]"
    console.print(providerLine)
    console.print()

    if state.company:
        console.print(f"  [bold]{state.company.corpName}[/] ({state.stockCode})")
        try:
            from dartlab.ai.conversation.suggestions import suggestQuestions

            questions = suggestQuestions(state.company)
            if questions:
                console.print()
                console.print("  [dim]추천 질문:[/]")
                for q in questions[:4]:
                    console.print(f"    [dim]-[/] {q}")
        except (ImportError, AttributeError):
            pass
    else:
        console.print("  [dim]종목 없이 시작합니다. 질문에 종목명을 포함하거나 /company 명령을 사용하세요.[/]")

    console.print()
    console.print("  [dim]/help 사용법  |  /quit 종료  |  Ctrl+C 입력 취소[/]")
    console.print()
