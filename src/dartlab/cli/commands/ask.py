"""`dartlab ask` command — 자연어 원스톱 + Rich 스트리밍."""

from __future__ import annotations

from dartlab.cli.context import PROVIDERS
from dartlab.cli.services.errors import CLIError
from dartlab.cli.services.providers import detect_provider
from dartlab.cli.services.runtime import configure_dartlab


def configure_parser(subparsers) -> None:
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
    parser.add_argument(
        "--include", "-i", nargs="+", default=None, help="포함할 topic (BS IS CF dividend ...)"
    )
    parser.add_argument("--exclude", "-e", nargs="+", default=None, help="제외할 topic")
    parser.add_argument("--stream", "-s", action="store_true", default=True, help="스트리밍 출력 (기본값)")
    parser.add_argument("--no-stream", dest="stream", action="store_false", help="스트리밍 비활성화")
    parser.add_argument("--continue", dest="cont", action="store_true", help="이전 대화 이어가기")
    parser.add_argument("--pattern", default=None, help="분석 패턴 (financial, risk, valuation)")
    parser.set_defaults(handler=run)


def run(args) -> int:
    from rich.console import Console
    from rich.live import Live
    from rich.markdown import Markdown

    dartlab = configure_dartlab()
    provider = args.provider or detect_provider()
    console = Console()

    # 자연어 원스톱: query를 하나로 합치고 종목+질문 자동 분리
    full_query = " ".join(args.query)

    if args.company:
        # --company 명시: query 전체가 질문
        try:
            company = dartlab.Company(args.company)
        except (ValueError, FileNotFoundError, OSError, RuntimeError) as exc:
            raise CLIError(str(exc)) from exc
        question = full_query
    else:
        # 자연어에서 종목 자동 추출
        from dartlab.core.resolve import resolve_from_text

        company, question = resolve_from_text(full_query)
        if company is None:
            raise CLIError(
                f"종목을 찾을 수 없습니다: '{full_query}'\n"
                "종목명 또는 종목코드를 포함해 주세요.\n"
                "예: dartlab ask 삼성전자 재무건전성 분석해줘\n"
                "    dartlab ask --company 005930 영업이익률 추세"
            )

    console.print(f"\n  [bold]{company.corpName}[/] ({company.stockCode})")
    console.print(f"  [dim]provider: {provider}", end="")
    if args.model:
        console.print(f" / {args.model}[/]")
    else:
        console.print("[/]")
    console.print()

    from dartlab.engines.ai.runtime.standalone import ask as _ask

    # 대화 연속 모드
    session_id = None
    history = None
    if args.cont:
        from dartlab.cli.services.history import get_latest_session, get_messages

        session_id = get_latest_session(company.stockCode)
        if session_id:
            history = get_messages(session_id)
            console.print(f"  [dim]이전 대화 이어가기 (메시지 {len(history)}개)[/]\n")

    answer = _ask(
        company,
        question,
        include=args.include,
        exclude=args.exclude,
        provider=provider,
        model=args.model,
        stream=args.stream,
        base_url=args.base_url,
        api_key=args.api_key,
        history=history,
        pattern=args.pattern,
    )

    if args.stream:
        buffer = ""
        with Live(console=console, refresh_per_second=8, vertical_overflow="visible") as live:
            for chunk in answer:
                buffer += chunk
                live.update(Markdown(buffer))
        console.print()
    else:
        buffer = answer
        console.print(Markdown(answer))

    # 히스토리 저장
    try:
        from dartlab.cli.services.history import add_message, create_session

        if session_id is None:
            session_id = create_session(company.stockCode)
        add_message(session_id, "user", question)
        add_message(session_id, "assistant", buffer)
    except (OSError, ImportError):
        pass

    return 0
