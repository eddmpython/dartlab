"""`dartlab search` command — 종목 검색."""

from __future__ import annotations

import polars as pl

from dartlab.cli.services.runtime import configure_dartlab


def configure_parser(subparsers) -> None:
    """search 서브커맨드 등록 — 종목코드/회사명 검색."""
    parser = subparsers.add_parser("search", help="종목 검색 (회사명 또는 종목코드)")
    parser.add_argument("keyword", help="검색어 (삼성전자, AAPL, 005930 ...)")
    parser.set_defaults(handler=run)


def run(args) -> int:
    """키워드로 종목을 검색해 결과를 콘솔에 출력한다."""
    dartlab = configure_dartlab()

    result = dartlab.searchName(args.keyword)
    if result is None:
        from dartlab.cli.services.output import get_console

        get_console().print("[dim]검색 결과가 없습니다.[/]")
        return 0
    if isinstance(result, pl.DataFrame):
        from dartlab.cli.services.output import print_search_results

        print_search_results(result)
    else:
        from dartlab.cli.services.output import get_console

        get_console().print(str(result))
    return 0
