"""`dartlab review` / `dartlab reviewer` — 기업 분석 검토서 (rich 렌더링).

사용 예시::

    dartlab review 005930               # 데이터 검토서
    dartlab review 005930 수익구조       # 수익구조만
    dartlab reviewer 005930             # AI 종합의견 포함
"""

from __future__ import annotations

from dartlab.cli.services.errors import CLIError
from dartlab.cli.services.runtime import configure_dartlab


def configure_parser(subparsers) -> None:
    # review: 순수 데이터 검토서
    parser = subparsers.add_parser("review", help="기업 분석 검토서 (데이터만)")
    parser.add_argument("company", help="종목코드 (005930) 또는 회사명 (삼성전자)")
    parser.add_argument("section", nargs="?", default=None, help="분석 섹션 (수익구조 등). 기본: 전체")
    parser.set_defaults(handler=_runReview)

    # reviewer: AI 종합의견 포함
    parserAi = subparsers.add_parser("reviewer", help="AI 분석 보고서 (데이터 + AI 종합의견)")
    parserAi.add_argument("company", help="종목코드 (005930) 또는 회사명 (삼성전자)")
    parserAi.add_argument("section", nargs="?", default=None, help="분석 섹션 (수익구조 등). 기본: 전체")
    parserAi.set_defaults(handler=_runReviewer)


def _runReview(args) -> int:
    """순수 데이터 검토서."""
    dartlab = configure_dartlab()

    try:
        company = dartlab.Company(args.company)
    except (ValueError, OSError) as exc:
        raise CLIError(str(exc)) from exc

    from dartlab.review.registry import buildReview

    report = buildReview(company, section=args.section)
    return _printReport(report, args)


def _runReviewer(args) -> int:
    """AI 종합의견 포함 보고서."""
    dartlab = configure_dartlab()

    try:
        company = dartlab.Company(args.company)
    except (ValueError, OSError) as exc:
        raise CLIError(str(exc)) from exc

    from dartlab.ai.reviewer import buildReviewWithAI

    report = buildReviewWithAI(company, section=args.section)
    return _printReport(report, args)


def _printReport(report, args) -> int:
    """보고서 렌더링 공통."""
    from dartlab.cli.services.output import get_console
    from dartlab.review.renderer import renderReview

    if not report.sections:
        console = get_console()
        name = getattr(report, "corpName", args.company) or args.company
        if args.section:
            console.print(f"  [yellow]'{args.section}' 섹션에 대한 분석 결과가 없습니다.[/]")
        else:
            console.print(f"  [yellow]{name} — 분석 결과가 없습니다.[/]")
        return 0

    console = get_console()
    renderReview(console, report)
    return 0
