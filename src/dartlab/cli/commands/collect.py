"""`dartlab collect` command — DART 공시문서 수집.

사용 예시::

    dartlab collect 005930                    # 단일 종목, 최근 8분기
    dartlab collect 005930 000660 -q 12       # 여러 종목, 12분기
    dartlab collect --auto                    # 미수집 전체, 8분기
    dartlab collect --auto --limit 50 -q 50   # 미수집 50개, 50분기
    dartlab collect --stats                   # 수집 현황
    dartlab collect --uncollected             # 미수집 목록
"""

from __future__ import annotations


def configure_parser(subparsers) -> None:
    parser = subparsers.add_parser(
        "collect",
        help="DART 공시문서 수집 (HTML → parquet)",
    )
    parser.add_argument(
        "codes",
        nargs="*",
        help="종목코드 (예: 005930 000660)",
    )
    parser.add_argument(
        "--quarters", "-q",
        type=int,
        default=8,
        help="최근 분기 수 (기본 8 = 2년치)",
    )
    parser.add_argument(
        "--annual-only",
        action="store_true",
        help="사업보고서만 (분기/반기 제외)",
    )
    parser.add_argument(
        "--min-delay",
        type=float,
        default=5.0,
        help="요청 간 최소 대기 초 (기본 5.0)",
    )
    parser.add_argument(
        "--max-delay",
        type=float,
        default=10.0,
        help="요청 간 최대 대기 초 (기본 10.0)",
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="미수집 종목 자동 수집",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="수집 현황 통계 출력",
    )
    parser.add_argument(
        "--uncollected",
        action="store_true",
        help="미수집 종목 목록 출력",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="--auto / --uncollected 시 최대 종목 수",
    )
    parser.set_defaults(handler=run)


def run(args) -> int:
    from dartlab.cli.services.output import get_console

    console = get_console()

    if args.stats:
        return _runStats(console)

    if args.uncollected:
        return _runUncollected(console, args.limit or 20)

    if args.auto:
        return _runAuto(console, args)

    if not args.codes:
        console.print("[bold]dartlab collect[/] — DART 공시문서 수집\n")
        console.print("  dartlab collect 005930              단일 종목")
        console.print("  dartlab collect 005930 000660 -q 12 여러 종목, 12분기")
        console.print("  dartlab collect --auto              미수집 자동 수집")
        console.print("  dartlab collect --auto --limit 50   미수집 50개")
        console.print("  dartlab collect --stats             수집 현황")
        console.print("  dartlab collect --uncollected       미수집 목록")
        return 1

    return _runCollect(console, args)


def _runStats(console) -> int:
    from dartlab.engines.dart.openapi.collector import collectionStats

    stats = collectionStats()
    console.print(f"전체 상장: {stats['totalListed']}")
    console.print(f"수집 완료: {stats['collected']}")
    console.print(f"미수집:    {stats['uncollected']}")
    return 0


def _runUncollected(console, limit: int) -> int:
    from dartlab.engines.dart.openapi.collector import listUncollectedKind

    stocks = listUncollectedKind()
    showing = min(limit, len(stocks))
    console.print(f"미수집 종목: {len(stocks)}개 (상위 {showing}개 표시)")
    for code, name in stocks[:limit]:
        console.print(f"  {code}  {name}")
    return 0


def _runAuto(console, args) -> int:
    from dartlab.engines.dart.openapi.collector import (
        collectMultiple,
        listUncollectedKind,
    )

    stocks = listUncollectedKind(limit=args.limit)

    if not stocks:
        console.print("[green]모든 종목이 수집되었습니다.[/]")
        return 0

    codes = [code for code, _name in stocks]
    includeQ = not args.annual_only

    console.print(f"[bold]자동 수집 시작[/]: {len(codes)}개 종목, 최근 {args.quarters}분기")
    console.print(f"딜레이: {args.min_delay}~{args.max_delay}초 | 분기보고서: {'포함' if includeQ else '제외'}\n")

    for i, (code, name) in enumerate(stocks[:10]):
        console.print(f"  {i + 1:>3}. {name} ({code})")
    if len(stocks) > 10:
        console.print(f"  ... 외 {len(stocks) - 10}개")

    results = collectMultiple(
        codes,
        quarters=args.quarters,
        includeQuarterly=includeQ,
        minDelay=args.min_delay,
        maxDelay=args.max_delay,
    )

    success = sum(1 for v in results.values() if v > 0)
    failed = sum(1 for v in results.values() if v < 0)
    console.print(f"\n[bold green]완료[/]: 성공 {success} / 실패 {failed} / 총 {len(codes)}")
    return 0


def _runCollect(console, args) -> int:
    from dartlab.engines.dart.openapi.collector import DocsCollector, collectMultiple

    codes = args.codes
    includeQ = not args.annual_only

    if len(codes) == 1:
        try:
            collector = DocsCollector(codes[0])
            count = collector.collect(
                quarters=args.quarters,
                includeQuarterly=includeQ,
                minDelay=args.min_delay,
                maxDelay=args.max_delay,
            )
            console.print(f"\n[bold green]완료[/]: {count}개 섹션 저장")
        except ValueError as e:
            console.print(f"[red]{e}[/]")
            return 1
    else:
        results = collectMultiple(
            codes,
            quarters=args.quarters,
            includeQuarterly=includeQ,
            minDelay=args.min_delay,
            maxDelay=args.max_delay,
        )
        success = sum(1 for v in results.values() if v > 0)
        failed = sum(1 for v in results.values() if v < 0)
        console.print(f"\n[bold green]완료[/]: 성공 {success} / 실패 {failed}")

    return 0
