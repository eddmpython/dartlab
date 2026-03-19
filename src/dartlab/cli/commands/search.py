"""`dartlab search` command — 종목 검색."""

from __future__ import annotations

import polars as pl

from dartlab.cli.services.runtime import configure_dartlab


def configure_parser(subparsers) -> None:
    parser = subparsers.add_parser("search", help="종목 검색 (회사명 또는 종목코드)")
    parser.add_argument("keyword", help="검색어 (삼성전자, AAPL, 005930 ...)")
    parser.set_defaults(handler=run)


def run(args) -> int:
    dartlab = configure_dartlab()

    result = dartlab.search(args.keyword)
    if result is None:
        print("검색 결과가 없습니다.")
        return 0
    if isinstance(result, pl.DataFrame):
        print(result)
    else:
        print(result)
    return 0
