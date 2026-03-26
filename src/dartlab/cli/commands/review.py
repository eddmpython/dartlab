"""`dartlab review` command — 기업 분석 리뷰 (rich 렌더링).

사용 예시::

    dartlab review 005930               # 전체 분석
    dartlab review 005930 수익구조       # 수익구조 섹션만
"""

from __future__ import annotations

from dartlab.cli.services.errors import CLIError
from dartlab.cli.services.runtime import configure_dartlab


def configure_parser(subparsers) -> None:
    parser = subparsers.add_parser("review", help="기업 분석 리뷰 (수익구조, 자금구조 등)")
    parser.add_argument("company", help="종목코드 (005930) 또는 회사명 (삼성전자)")
    parser.add_argument("section", nargs="?", default=None, help="분석 섹션 (수익구조 등). 기본: 전체")
    parser.set_defaults(handler=run)


def run(args) -> int:
    dartlab = configure_dartlab()

    try:
        company = dartlab.Company(args.company)
    except (ValueError, OSError) as exc:
        raise CLIError(str(exc)) from exc

    from dartlab.analysis.review import buildReport, renderReport
    from dartlab.cli.services.output import get_console

    report = buildReport(company, section=args.section)

    if not report.sections:
        console = get_console()
        name = getattr(company, "corpName", args.company) or args.company
        if args.section:
            console.print(f"  [yellow]'{args.section}' 섹션에 대한 분석 결과가 없습니다.[/]")
        else:
            console.print(f"  [yellow]{name} — 분석 결과가 없습니다.[/]")
        return 0

    console = get_console()
    renderReport(console, report)
    return 0
