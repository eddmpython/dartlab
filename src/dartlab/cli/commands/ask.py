"""`dartlab ask` command."""

from __future__ import annotations

from dartlab.cli.context import PROVIDERS
from dartlab.cli.services.errors import CLIError
from dartlab.cli.services.providers import detect_provider
from dartlab.cli.services.runtime import configure_dartlab


def configure_parser(subparsers) -> None:
    parser = subparsers.add_parser("ask", help="LLM에게 기업 분석 질문")
    parser.add_argument("company", help="종목코드 (005930) 또는 회사명 (삼성전자)")
    parser.add_argument("question", help="질문 텍스트")
    parser.add_argument("--provider", "-p", default=None, choices=PROVIDERS, help="LLM provider")
    parser.add_argument("--model", "-m", default=None, help="모델명")
    parser.add_argument("--base-url", default=None, help="커스텀 API URL")
    parser.add_argument("--api-key", default=None, help="API 키")
    parser.add_argument(
        "--include", "-i", nargs="+", default=None, help="포함할 topic (BS IS CF dividend companyOverview ...)"
    )
    parser.add_argument("--exclude", "-e", nargs="+", default=None, help="제외할 topic")
    parser.add_argument("--stream", "-s", action="store_true", help="스트리밍 출력")
    parser.set_defaults(handler=run)


def run(args) -> int:
    dartlab = configure_dartlab()

    provider = args.provider or detect_provider()

    try:
        company = dartlab.Company(args.company)
    except (ValueError, FileNotFoundError, OSError, RuntimeError) as exc:
        raise CLIError(str(exc)) from exc

    print(f"\n  {company.corpName} ({company.stockCode})")
    print(f"  provider: {provider}")
    print()

    from dartlab.engines.ai.runtime.standalone import ask as _ask

    answer = _ask(
        company,
        args.question,
        include=args.include,
        exclude=args.exclude,
        provider=provider,
        model=args.model,
        stream=args.stream,
        base_url=args.base_url,
        api_key=args.api_key,
    )

    if not args.stream:
        print(answer)
    return 0
