"""`dartlab ask` command -- one-shot AI analysis with tool visibility."""

from __future__ import annotations

import time

from dartlab.cli.brand import CLR, CLR_MUTED
from dartlab.cli.constants import toolLabel, toolResultPreview
from dartlab.cli.context import PROVIDERS
from dartlab.cli.services.errors import CLIError
from dartlab.cli.services.providers import detect_provider
from dartlab.cli.services.runtime import configure_dartlab


def configure_parser(subparsers) -> None:
    """ask 서브커맨드 등록 -- one-shot AI 분석."""
    parser = subparsers.add_parser(
        "ask",
        help="LLM에게 기업 분석 질문 (자연어 원스톱)",
    )
    parser.add_argument(
        "query",
        nargs="+",
        help="질문 (종목명 포함). 예: 삼성전자 재무건전성 분석해줘",
    )
    parser.add_argument("--company", "-c", default=None, help="종목 명시 (종목코드 또는 회사명)")
    parser.add_argument("--provider", "-p", default=None, choices=PROVIDERS, help="LLM provider")
    parser.add_argument("--model", "-m", default=None, help="모델명")
    parser.add_argument("--base-url", default=None, help="커스텀 API URL")
    parser.add_argument("--api-key", default=None, help="API 키")
    parser.add_argument("--include", "-i", nargs="+", default=None, help="포함할 topic (BS IS CF dividend ...)")
    parser.add_argument("--exclude", "-e", nargs="+", default=None, help="제외할 topic")
    parser.add_argument("--stream", "-s", action="store_true", default=True, help="스트리밍 출력 (기본값)")
    parser.add_argument("--no-stream", dest="stream", action="store_false", help="스트리밍 비활성화")
    parser.add_argument("--continue", dest="cont", action="store_true", help="이전 대화 이어가기")
    parser.add_argument("--pattern", default=None, help="분석 패턴 (financial, risk, valuation)")
    parser.add_argument("--report", action="store_true", help="전문 분석보고서 모드 (7섹션 구조화 보고서)")
    parser.set_defaults(handler=run)


def run(args) -> int:
    """질문에서 종목을 추출하고 AI 분석 결과를 Rich 스트리밍으로 출력한다."""
    from rich.console import Console, Group
    from rich.live import Live
    from rich.markdown import Markdown
    from rich.spinner import Spinner
    from rich.text import Text

    dartlab = configure_dartlab()
    provider = args.provider or detect_provider()
    console = Console()

    # ── 종목 추출 ──
    full_query = " ".join(args.query)
    company, question = _resolveCompany(full_query, args, dartlab)

    # ── 헤더 ──
    if company is not None:
        console.print(f"\n  [bold {CLR}]{company.corpName}[/] ({company.stockCode})")
    else:
        console.print(f"\n  [bold {CLR}]Free analysis[/] [dim](LLM will search for companies)[/]")
    providerLine = f"  [{CLR_MUTED}]provider: {provider}"
    if args.model:
        providerLine += f" / {args.model}"
    providerLine += "[/]"
    console.print(providerLine)
    console.print()

    # ── 히스토리 연속 ──
    session_id = None
    history = None
    if args.cont and company is not None:
        session_id, history = _loadHistory(company.stockCode, console)

    # ── analyze() 직접 호출 (이벤트 스트림) ──
    from dartlab.ai.runtime.core import analyze

    events = analyze(
        company,
        question,
        include=args.include,
        exclude=args.exclude,
        provider=provider,
        model=args.model,
        base_url=args.base_url,
        api_key=args.api_key,
        history=history,
        report_mode=args.report,
        use_tools=True,
        max_turns=10 if args.report else 5,
    )

    buffer = ""
    toolLines: list[str] = []
    toolPanels: list[str] = []
    toolCount = 0
    toolStartTime: float | None = None
    queryStart = time.monotonic()

    try:
        with Live(
            Spinner("dots", text=f"[{CLR_MUTED}]Thinking...[/]", style=CLR_MUTED),
            console=console,
            refresh_per_second=8,
            vertical_overflow="visible",
            transient=True,
        ) as live:
            for ev in events:
                if ev.kind == "chunk":
                    buffer += ev.data["text"]
                    live.update(Markdown(buffer))

                elif ev.kind == "tool_call":
                    toolCount += 1
                    label = toolLabel(ev.data.get("name", ""))
                    toolStartTime = time.monotonic()
                    toolSpinner = Spinner(
                        "dots",
                        text=f"[{CLR_MUTED}][{toolCount}] {label}...[/]",
                        style=CLR_MUTED,
                    )
                    statusBlock = "\n".join(toolLines)
                    if statusBlock:
                        live.update(Group(Markdown(statusBlock), toolSpinner))
                    else:
                        live.update(toolSpinner)

                elif ev.kind == "tool_result":
                    label = toolLabel(ev.data.get("name", ""))
                    elapsed = ""
                    if toolStartTime is not None:
                        dt = time.monotonic() - toolStartTime
                        elapsed = f" ({dt:.1f}s)"
                        toolStartTime = None
                    resultText = ev.data.get("result", "")
                    preview = toolResultPreview(resultText)
                    line = f"> {label} done{elapsed}"
                    if preview:
                        line += f" -- {preview}"
                        toolPanels.append(resultText)
                    toolLines.append(line)
                    live.update(Markdown("\n".join(toolLines)))

                elif ev.kind == "code_round":
                    r = ev.data.get("round", "?")
                    mx = ev.data.get("maxRounds", "?")
                    live.update(
                        Spinner(
                            "dots",
                            text=f"[{CLR_MUTED}]코드 실행 {r}/{mx}...[/]",
                            style=CLR_MUTED,
                        )
                    )

                elif ev.kind == "error":
                    errorMsg = ev.data.get("error", "Unknown error")
                    guideMsg = ev.data.get("guide")
                    _printErrorWithHint(errorMsg, console, guideMsg=guideMsg)
                    return 1

    except KeyboardInterrupt:
        console.print(f"\n  [{CLR_MUTED}]Interrupted[/]")

    # ── 도구 호출 로그 ──
    if toolLines:
        for tl in toolLines:
            console.print(f"  [{CLR_MUTED}]{tl}[/]")

    # ── 도구 데이터 테이블 ──
    if toolPanels:
        for panel in toolPanels:
            _renderToolData(panel, console)

    # ── 최종 응답 ──
    if buffer:
        console.print()
        console.print(Markdown(buffer))

    # ── footer ──
    console.print()
    totalElapsed = time.monotonic() - queryStart
    footerParts = [f"{totalElapsed:.1f}s"]
    if toolCount > 0:
        footerParts.append(f"{toolCount} tool{'s' if toolCount != 1 else ''}")
    console.print(Text("  " + "  |  ".join(footerParts), style="dim"))

    # ── 히스토리 저장 ──
    if company is not None and buffer:
        _saveHistory(company.stockCode, session_id, question, buffer)

    return 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolveCompany(full_query: str, args, dartlab):
    """--company 플래그만 처리. 나머지는 AI가 자율 판단."""
    if args.company:
        from dartlab.guide.integration import cliCompany

        company = cliCompany(args.company)
        return company, full_query
    return None, full_query


def _loadHistory(stockCode: str, console):
    """이전 대화 세션 로드."""
    try:
        from dartlab.cli.services.history import get_latest_session, get_messages

        session_id = get_latest_session(stockCode)
        if session_id:
            history = get_messages(session_id)
            console.print(f"  [{CLR_MUTED}]Resuming session ({len(history)} messages)[/]\n")
            return session_id, history
    except (OSError, ImportError):
        pass
    return None, None


def _saveHistory(stockCode: str, session_id, question: str, answer: str) -> None:
    """대화 히스토리 SQLite 저장."""
    try:
        from dartlab.cli.services.history import add_message, create_session

        if session_id is None:
            session_id = create_session(stockCode)
        add_message(session_id, "user", question)
        add_message(session_id, "assistant", answer)
    except (OSError, ImportError):
        pass


def _printErrorWithHint(errorMsg: str, console, *, guideMsg: str | None = None) -> None:
    """에러 메시지 + 복구 힌트 출력."""
    from dartlab.cli.brand import CLR_DANGER, CLR_MUTED

    console.print(f"\n  [{CLR_DANGER}]{errorMsg}[/]")

    # guide 안내 데스크 메시지 우선
    if guideMsg:
        for line in guideMsg.split("\n"):
            console.print(f"  [{CLR_MUTED}]{line}[/]")
        return

    # 폴백: 키워드 기반 힌트
    msg = errorMsg.lower()
    if any(w in msg for w in ("api key", "auth", "401", "403", "invalid key", "unauthorized")):
        console.print(f"  [{CLR_MUTED}]hint: run `dartlab setup` to configure your API key[/]")
    elif any(w in msg for w in ("connection", "timeout", "network", "refused", "resolve")):
        console.print(f"  [{CLR_MUTED}]hint: check network or try --provider <other>[/]")
    elif any(w in msg for w in ("context", "token", "too long", "limit")):
        console.print(f"  [{CLR_MUTED}]hint: try --exclude <topic> to reduce context size[/]")
    elif "provider" in msg or "no provider" in msg:
        console.print(f"  [{CLR_MUTED}]hint: run `dartlab setup` or pass --provider <name>[/]")


def _renderToolData(resultText: str, console) -> None:
    """도구 결과 테이블 렌더링."""
    from dartlab.cli.rendering import renderToolResult

    if renderToolResult(resultText, console):
        return

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
