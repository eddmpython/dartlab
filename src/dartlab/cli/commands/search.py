"""`dartlab search` command — 종목 검색."""

from __future__ import annotations

import polars as pl

from dartlab.cli.services.runtime import configureDartlab


def configureParser(subparsers) -> None:
    """search 서브커맨드 등록 — 종목코드/회사명 검색."""
    parser = subparsers.add_parser("search", help="종목 검색 (회사명 또는 종목코드)")
    parser.add_argument("keyword", nargs="?", default="", help="검색어 (삼성전자, AAPL, 005930 ...)")
    parser.add_argument("--semantic", action="store_true", help="회사·기간을 넘나드는 문단 의미 검색")
    parser.add_argument(
        "--build-semantic", action="store_true", help="로컬 catalog·원문 전체의 의미 인덱스를 증분 준비"
    )
    parser.add_argument("--related-to", help="검색 결과 passageId와 의미가 연결되는 문서 조회")
    parser.add_argument("--corp", help="의미 검색의 회사 코드·이름·미국 ticker 필터")
    parser.add_argument("--exclude-corp", help="관련 문단 검색에서 제외할 회사")
    parser.add_argument("--start", help="의미 검색 시작일 YYYYMMDD")
    parser.add_argument("--end", help="의미 검색 종료일 YYYYMMDD")
    parser.add_argument("--limit", type=int, default=10, help="의미 검색 결과 수")
    parser.set_defaults(handler=run)


def run(args) -> int:
    """키워드로 종목을 검색해 결과를 콘솔에 출력한다."""
    dartlab = configureDartlab()

    if args.build_semantic:
        from dartlab.cli.services.output import getConsole
        from dartlab.providers.dart.search.semanticIndex import buildSemanticIndex, prepareSemanticModels

        prepareSemanticModels()
        getConsole().print(buildSemanticIndex())
        return 0
    if args.semantic or args.related_to:
        from dartlab.cli.services.output import getConsole

        result = dartlab.search(
            args.keyword,
            scope="semantic",
            relatedTo=args.related_to,
            corp=args.corp,
            excludeCorp=args.exclude_corp,
            start=args.start,
            end=args.end,
            limit=args.limit,
        )
        getConsole().print(result)
        return 0
    if not args.keyword:
        from dartlab.cli.services.output import getConsole

        getConsole().print("검색어 또는 --build-semantic을 지정하세요.")
        return 2

    result = dartlab.searchName(args.keyword)
    if result is None:
        from dartlab.cli.services.output import getConsole

        getConsole().print("[dim]검색 결과가 없습니다.[/]")
        return 0
    if isinstance(result, pl.DataFrame):
        from dartlab.cli.services.output import printSearchResults

        printSearchResults(result)
    else:
        from dartlab.cli.services.output import getConsole

        getConsole().print(str(result))
    return 0
