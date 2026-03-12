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
    parser.add_argument("--include", "-i", nargs="+", default=None, help="포함할 데이터 (BS IS dividend ...)")
    parser.add_argument("--exclude", "-e", nargs="+", default=None, help="제외할 데이터")
    parser.add_argument("--stream", "-s", action="store_true", help="스트리밍 출력")
    parser.set_defaults(handler=run)


def run(args) -> int:
    dartlab = configure_dartlab()

    provider = args.provider or detect_provider()
    kwargs = {"provider": provider}
    if args.model:
        kwargs["model"] = args.model
    if args.base_url:
        kwargs["base_url"] = args.base_url
    if args.api_key:
        kwargs["api_key"] = args.api_key

    dartlab.llm.configure(**kwargs)

    try:
        company = dartlab.Company(args.company)
    except Exception as exc:
        raise CLIError(str(exc)) from exc

    print(f"\n  {company.corpName} ({company.stockCode})")
    print(f"  provider: {provider}")
    print()

    answer = company.ask(
        args.question,
        include=args.include,
        exclude=args.exclude,
        stream=args.stream,
    )

    if not args.stream:
        print(answer)
    return 0
