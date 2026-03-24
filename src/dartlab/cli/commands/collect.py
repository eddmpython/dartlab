"""`dartlab collect` command — DART 데이터 수집.

사용 예시::

    dartlab collect 005930                    # 단일 종목 docs (기존)
    dartlab collect --auto                    # 미수집 docs 전체 (기존)
    dartlab collect --stats                   # 수집 현황
    dartlab collect --uncollected             # 미수집 목록

    # 배치 모드 (finance/report/docs 전체, 멀티키 병렬)
    dartlab collect --batch                          # 전체 상장, 미수집만
    dartlab collect --batch --mode all               # 전체 상장, 전부
    dartlab collect --batch -c finance               # 전체 상장, 재무만
    dartlab collect --batch 005930 000660            # 지정 종목
    dartlab collect --batch 005930 -c finance,report # 지정 종목 + 카테고리
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
        "--quarters",
        "-q",
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
    parser.add_argument(
        "--batch",
        action="store_true",
        help="배치 모드 (finance/report/docs 전체, 멀티키 병렬)",
    )
    parser.add_argument(
        "--categories",
        "-c",
        type=str,
        default=None,
        help="수집 카테고리 (쉼표 구분: finance,report,docs)",
    )
    parser.add_argument(
        "--mode",
        choices=["new", "all"],
        default="new",
        help="new=미수집만 / all=전체 (기본: new)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="freshness 체크만 (수집 안 함). 종목 지정 시 해당 종목, 미지정 시 전체 스캔",
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="누락 공시만 증분 수집. 종목 지정 시 해당 종목, 미지정 시 전체 스캔 후 수집",
    )
    parser.set_defaults(handler=run)


def run(args) -> int:
    from dartlab.cli.services.output import get_console

    console = get_console()

    if getattr(args, "check", False):
        return _runCheck(console, args)

    if getattr(args, "incremental", False):
        return _runIncremental(console, args)

    if args.stats:
        return _runStats(console)

    if args.uncollected:
        return _runUncollected(console, args.limit or 20)

    if args.batch:
        return _runBatch(console, args)

    if args.auto:
        return _runAuto(console, args)

    if not args.codes:
        console.print("[bold]dartlab collect[/] — DART 데이터 수집\n")
        console.print("  dartlab collect 005930              단일 종목 docs")
        console.print("  dartlab collect --auto              미수집 docs 자동 수집")
        console.print("  dartlab collect --stats             수집 현황")
        console.print("  dartlab collect --uncollected       미수집 목록")
        console.print()
        console.print("  [bold]freshness 체크 / 증분 수집[/]:")
        console.print("  dartlab collect --check 005930      종목 freshness 체크")
        console.print("  dartlab collect --check             전체 종목 스캔 (7일)")
        console.print("  dartlab collect --incremental 005930 누락 공시만 증분 수집")
        console.print("  dartlab collect --incremental       전체 종목 증분 수집")
        console.print()
        console.print("  [bold]배치 모드[/] (finance/report/docs, 멀티키 병렬):")
        console.print("  dartlab collect --batch                          전체 상장, 미수집")
        console.print("  dartlab collect --batch -c finance               전체 상장, 재무만")
        console.print("  dartlab collect --batch 005930 000660            지정 종목")
        console.print("  dartlab collect --batch 005930 -c finance,report 지정 종목 + 카테고리")
        return 1

    return _runCollect(console, args)


def _runStats(console) -> int:
    from dartlab.engines.company.dart.openapi.collector import collectionStats

    stats = collectionStats()
    console.print(f"전체 상장: {stats['totalListed']}")
    console.print(f"수집 완료: {stats['collected']}")
    console.print(f"미수집:    {stats['uncollected']}")
    return 0


def _runUncollected(console, limit: int) -> int:
    from dartlab.engines.company.dart.openapi.collector import listUncollectedKind

    stocks = listUncollectedKind()
    showing = min(limit, len(stocks))
    console.print(f"미수집 종목: {len(stocks)}개 (상위 {showing}개 표시)")
    for code, name in stocks[:limit]:
        console.print(f"  {code}  {name}")
    return 0


def _runAuto(console, args) -> int:
    from dartlab.engines.company.dart.openapi.batch import batchCollect
    from dartlab.engines.company.dart.openapi.collector import listUncollectedKind

    stocks = listUncollectedKind(limit=args.limit)

    if not stocks:
        console.print("[green]모든 종목이 수집되었습니다.[/]")
        return 0

    codes = [code for code, _name in stocks]

    console.print(f"[bold]자동 수집 시작[/]: {len(codes)}개 종목 docs\n")

    for i, (code, name) in enumerate(stocks[:10]):
        console.print(f"  {i + 1:>3}. {name} ({code})")
    if len(stocks) > 10:
        console.print(f"  ... 외 {len(stocks) - 10}개")

    results = batchCollect(codes, categories=["docs"])

    total = len(results)
    success = sum(1 for v in results.values() if v.get("docs", 0) > 0)
    console.print(f"\n[bold green]완료[/]: 성공 {success} / 총 {total}")
    return 0


def _runBatch(console, args) -> int:
    from dartlab.engines.company.dart.openapi.batch import batchCollect, batchCollectAll
    from dartlab.engines.company.dart.openapi.dartKey import resolveDartKeys

    keys = resolveDartKeys()
    if not keys:
        console.print("[red]DART API 키가 필요합니다. DART_API_KEY(S) 환경변수를 설정하세요.[/]")
        return 1

    cats = [c.strip() for c in args.categories.split(",")] if args.categories else None
    catLabel = ", ".join(cats) if cats else "finance, report, docs"

    if args.codes:
        console.print(f"[bold]배치 수집[/]: {len(args.codes)}개 종목 | {catLabel} | {len(keys)}키 병렬\n")
        for code in args.codes[:10]:
            console.print(f"  {code}")
        if len(args.codes) > 10:
            console.print(f"  ... 외 {len(args.codes) - 10}개")
        console.print()
        results = batchCollect(args.codes, categories=cats, incremental=True)
    else:
        console.print(f"[bold]배치 수집[/]: 전체 상장 ({args.mode}) | {catLabel} | {len(keys)}키 병렬\n")
        results = batchCollectAll(categories=cats, mode=args.mode)

    total = len(results)
    success = sum(1 for v in results.values() if any(cnt > 0 for cnt in v.values()))
    skipped = sum(1 for v in results.values() if all(cnt == 0 for cnt in v.values()))
    console.print(f"\n[bold green]완료[/]: 수집 {success} / 스킵 {skipped} / 총 {total}")
    return 0


def _runCheck(console, args) -> int:
    from dartlab.engines.company.dart.openapi.dartKey import hasDartApiKey
    from dartlab.engines.company.dart.openapi.freshness import (
        checkFreshness,
        scanMarketFreshness,
    )

    if not hasDartApiKey():
        console.print("[red]DART API 키가 필요합니다: dartlab setup dart-key[/]")
        return 1

    if args.codes:
        for code in args.codes:
            result = checkFreshness(code, forceCheck=True)
            if result.isFresh:
                console.print(f"  ✓ {code} — 최신 상태 ({result.source})")
            else:
                console.print(f"  ⚠ {code} — 새 공시 {result.missingCount}건")
                for f in result.missingFilings[:5]:
                    console.print(f"    {f['rcept_dt']} {f['report_nm']}")
    else:
        console.print("[bold]전체 종목 freshness 스캔[/] (최근 7일)\n")
        df = scanMarketFreshness(days=7)
        if df.is_empty():
            console.print("[green]모든 로컬 종목이 최신 상태입니다.[/]")
        else:
            for row in df.iter_rows(named=True):
                console.print(f"  ⚠ {row['stockCode']} {row['corpName']} — 새 공시 {row['newCount']}건 ({row['latestReport']})")
    return 0


def _runIncremental(console, args) -> int:
    from dartlab.engines.company.dart.openapi.dartKey import hasDartApiKey
    from dartlab.engines.company.dart.openapi.freshness import (
        checkFreshness,
        collectMissing,
        scanMarketFreshness,
    )

    if not hasDartApiKey():
        console.print("[red]DART API 키가 필요합니다: dartlab setup dart-key[/]")
        return 1

    cats = [c.strip() for c in args.categories.split(",")] if args.categories else None

    if args.codes:
        for code in args.codes:
            result = checkFreshness(code, forceCheck=True)
            if result.isFresh:
                console.print(f"  ✓ {code} — 최신 상태")
            else:
                console.print(f"  ⚠ {code} — 새 공시 {result.missingCount}건, 수집 중...")
                counts = collectMissing(code, categories=cats)
                summary = ", ".join(f"{k}:{v}" for k, v in counts.items() if v > 0)
                console.print(f"  ✓ {code} 수집 완료 ({summary or '변경 없음'})")
    else:
        console.print("[bold]전체 종목 증분 수집[/] (최근 7일)\n")
        df = scanMarketFreshness(days=7)
        if df.is_empty():
            console.print("[green]모든 로컬 종목이 최신 상태입니다.[/]")
            return 0

        for row in df.iter_rows(named=True):
            code = row["stockCode"]
            console.print(f"  {code} {row['corpName']} — {row['newCount']}건 수집 중...")
            counts = collectMissing(code, categories=cats)
            summary = ", ".join(f"{k}:{v}" for k, v in counts.items() if v > 0)
            console.print(f"  ✓ {code} ({summary or '변경 없음'})")

        console.print(f"\n[bold green]완료[/]: {df.height}종목 증분 수집")
    return 0


def _runCollect(console, args) -> int:
    codes = args.codes

    if len(codes) == 1:
        from dartlab.engines.company.dart.openapi.zipCollector import ZipDocsCollector

        try:
            collector = ZipDocsCollector(codes[0])
            count = collector.collect(
                includeQuarterly=not args.annual_only,
                showProgress=True,
            )
            console.print(f"\n[bold green]완료[/]: {count}개 섹션 저장")
        except ValueError as e:
            console.print(f"[red]{e}[/]")
            return 1
    else:
        from dartlab.engines.company.dart.openapi.batch import batchCollect

        results = batchCollect(codes, categories=["docs"])
        total = len(results)
        success = sum(1 for v in results.values() if v.get("docs", 0) > 0)
        console.print(f"\n[bold green]완료[/]: 성공 {success} / 총 {total}")

    return 0
