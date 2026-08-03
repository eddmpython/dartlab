"""`dartlab ask` command -- one-shot AI analysis with tool visibility."""

from __future__ import annotations

import time

from dartlab.cli.brand import CLR, CLR_MUTED
from dartlab.cli.constants import toolLabel, toolResultPreview
from dartlab.cli.services.errors import CLIError
from dartlab.cli.services.runtime import configureDartlab


def configureParser(subparsers) -> None:
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
    parser.add_argument("--runtime", "-r", choices=["codex", "claude", "cline"], default=None)
    parser.add_argument("--session", default=None, help="재개할 DartLab agent session ID")
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
    from rich.console import Group
    from rich.live import Live
    from rich.markdown import Markdown
    from rich.spinner import Spinner
    from rich.text import Text

    from dartlab.core.logger import getConsole

    dartlab = configureDartlab()
    console = getConsole()

    # ── 종목 추출 ──
    fullQuery = " ".join(args.query)
    company, question = _resolveCompany(fullQuery, args, dartlab)

    # ── 헤더 ──
    if company is not None:
        console.print(f"\n  [bold {CLR}]{company.corpName}[/] ({company.stockCode})")
    else:
        console.print(f"\n  [bold {CLR}]Agent runtime analysis[/] [dim](DartLab MCP grounded)[/]")
    console.print(f"  [{CLR_MUTED}]entry: dartlab.ask · auth/model owned by local CLI[/]")
    console.print()

    # ── 히스토리 연속 ──
    sessionId = None
    history = None
    if args.cont and company is not None:
        sessionId, history = _loadHistory(company.stockCode, console)

    # ── ask 내부 이벤트 스트림 ──
    from dartlab.ai.kernel import _askEvents, _doneFailure

    events = _askEvents(
        question,
        runtimeId=args.runtime,
        sessionId=args.session or (str(sessionId) if sessionId is not None else None),
        include=args.include,
        exclude=args.exclude,
        history=history,
        report_mode=args.report,
        stockCode=getattr(company, "stockCode", None) if company is not None else None,
    )

    buffer = ""
    toolLines: list[str] = []
    toolPanels: list[str] = []
    toolCount = 0
    toolStartTime: float | None = None
    finalFailure: str | None = None
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
                if ev.kind == "runtime_session":
                    sessionId = ev.data.get("sessionId") or sessionId
                    runtimeId = ev.data.get("runtimeId") or "agent"
                    resumed = " resumed" if ev.data.get("resumed") else ""
                    toolLines.append(f"> runtime: {runtimeId}{resumed} | session={sessionId}")
                    live.update(Markdown("\n".join(toolLines)))

                elif ev.kind == "chunk":
                    buffer += ev.data["text"]
                    live.update(Markdown(buffer))

                elif ev.kind == "tool_start":
                    toolCount += 1
                    label = toolLabel(ev.data.get("name", ""))
                    argText = _eventArgsPreview(ev.data)
                    toolStartTime = time.monotonic()
                    toolSpinner = Spinner(
                        "dots",
                        text=f"[{CLR_MUTED}][{toolCount}] {label}{argText}[/]",
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
                    preview = ev.data.get("outputSummary") or toolResultPreview(resultText)
                    line = f"> {label} done{elapsed}"
                    if ev.data.get("persisted"):
                        line += " | full result saved"
                    if preview:
                        line += f" -- {preview}"
                        toolPanels.append(resultText)
                    toolLines.append(line)
                    live.update(Markdown("\n".join(toolLines)))

                elif ev.kind == "tool_progress":
                    message = ev.data.get("line") or ev.data.get("message")
                    if message:
                        toolLines.append(f"> progress: {_shortPreview(str(message), 100)}")
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

                elif ev.kind in {
                    "task",
                    "plan",
                    "reference",
                    "inspect",
                    "execute",
                    "visual",
                    "observation",
                    "decision",
                    "draft",
                    "verify",
                    "answer",
                    "unable",
                }:
                    line = _kernelEventLine(ev.kind, ev.data)
                    if line:
                        toolLines.append(line)
                        live.update(Markdown("\n".join(toolLines)))

                elif ev.kind == "error":
                    errorMsg = ev.data.get("error", "Unknown error")
                    guideMsg = ev.data.get("guide")
                    _printErrorWithHint(errorMsg, console, guideMsg=guideMsg)
                    return 1

                elif ev.kind == "done":
                    finalFailure = _doneFailure(ev)

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

    if finalFailure:
        _printErrorWithHint(finalFailure, console)
        return 1

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
    return 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolveCompany(fullQuery: str, args, dartlab):
    """--company 플래그만 처리. 나머지는 AI가 자율 판단."""
    if args.company:
        try:
            company = dartlab.Company(args.company)
        except (ValueError, FileNotFoundError, OSError, RuntimeError) as exc:
            from dartlab.cli.services.errors import wrapError

            raise CLIError(wrapError(exc, stockCode=args.company)) from exc
        return company, fullQuery
    return None, fullQuery


def _kernelEventLine(kind: str, data: dict) -> str:
    """Ask Workbench canonical event를 CLI 상태 라인으로 변환."""
    if kind == "task":
        task = data.get("task") or {}
        actions = task.get("actions") if isinstance(task, dict) else None
        suffix = f" ({len(actions)} actions)" if isinstance(actions, list) else ""
        return f"> task: ask workbench{suffix}"
    if kind == "plan":
        skills = data.get("selectedSkillIds") or []
        skill_text = ", ".join(str(item) for item in skills[:3]) if isinstance(skills, list) else ""
        return f"> plan: {skill_text or data.get('entrySkillId') or 'skill OS'}"
    if kind == "reference":
        refs = data.get("refs") or []
        selected = data.get("selectedSkillCandidates") or []
        if selected:
            names = ", ".join(str(item.get("id") or "?") for item in selected[:3])
            return f"> reference: {len(refs)} refs | skills: {names}"
        return f"> reference: {len(refs)} refs"
    if kind == "inspect":
        target = data.get("target") or data.get("action") or "dataset"
        result = data.get("result") or {}
        latest = result.get("latest") if isinstance(result, dict) else None
        suffix = f" latest={latest.get('value')}" if isinstance(latest, dict) and latest.get("value") else ""
        return f"> inspect: {target}{suffix}"
    if kind == "execute":
        result = data.get("result") or {}
        ok = "ok" if result.get("ok") else "failed"
        output = _shortPreview(result.get("stdout") or result.get("stderr") or "", 90)
        suffix = f" | {output}" if output else ""
        return f"> execute: {ok} ({result.get('duration_ms') or result.get('durationMs') or '?'}ms){suffix}"
    if kind == "visual":
        return f"> visual: {len(data.get('visuals') or [])} spec"
    if kind == "observation":
        facts = data.get("facts") or []
        refs = data.get("evidenceRefs") or []
        fact = _shortPreview(facts[0], 90) if facts else ""
        suffix = f" | refs={len(refs)}" if refs else ""
        return f"> observation: {fact}{suffix}".rstrip()
    if kind == "decision":
        action = data.get("action") or "continue"
        skipped = data.get("skippedToolCalls") or 0
        suffix = f" | skipped={skipped}" if skipped else ""
        return f"> decision: {action}{suffix}"
    if kind == "draft":
        refs = data.get("evidenceRefs") or []
        return f"> draft: {len(refs)} refs"
    if kind == "verify":
        result = data.get("result") or {}
        ok = "ok" if result.get("ok") else "failed"
        issues = result.get("issues") or []
        return f"> verify: {ok}" + (f" ({len(issues)} issues)" if issues else "")
    if kind == "answer":
        refs = data.get("evidenceRefs") or []
        return f"> answer: verified ({len(refs)} refs)"
    if kind == "unable":
        issues = data.get("issues") or []
        return "> unable: transparent failure" + (f" ({len(issues)} issues)" if issues else "")
    return ""


def _eventArgsPreview(data: dict) -> str:
    if isinstance(data.get("input"), dict):
        data = {**data, **data["input"]}
    if data.get("query"):
        return f": {_shortPreview(data['query'], 72)}"
    if data.get("target"):
        return f": {_shortPreview(data['target'], 72)}"
    if data.get("path"):
        return f": {_shortPreview(data['path'], 72)}"
    if data.get("codePreview"):
        return f": {_shortPreview(data['codePreview'], 72)}"
    args = data.get("arguments")
    if isinstance(args, dict) and args:
        from dartlab.cli.constants import formatToolArgs

        preview = formatToolArgs(args)
        return f": {preview}" if preview else ""
    return ""


def _shortPreview(value: object, limit: int) -> str:
    text = " ".join(str(value).strip().split())
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)].rstrip() + "..."


def _loadHistory(stockCode: str, console):
    """transcript를 복제하지 않고 가장 최근 agent 세션 ID만 재개한다."""
    try:
        from dartlab.ai.runtime import getRuntimeEngine

        sessions = getRuntimeEngine().sessionStore.list(limit=1)
        if sessions:
            console.print(f"  [{CLR_MUTED}]Resuming agent session {sessions[0].sessionId}[/]\n")
            return sessions[0].sessionId, None
    except (OSError, ImportError):
        pass
    return None, None


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
        console.print(f"  [{CLR_MUTED}]hint: run the selected agent CLI and complete its login[/]")
    elif any(w in msg for w in ("connection", "timeout", "network", "refused", "resolve")):
        console.print(f"  [{CLR_MUTED}]hint: run `dartlab agent status --refresh`[/]")
    elif any(w in msg for w in ("context", "token", "too long", "limit")):
        console.print(f"  [{CLR_MUTED}]hint: try --exclude <topic> to reduce context size[/]")
    elif "runtime" in msg or "agent cli" in msg:
        console.print(f"  [{CLR_MUTED}]hint: run `dartlab agent install <runtime>`[/]")


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
