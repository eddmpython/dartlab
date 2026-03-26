"""`dartlab collect` command — DART/EDGAR 데이터 수집.

사용 예시::

    # DART (종목코드 = 숫자 → 자동 감지)
    dartlab collect 005930                    # 단일 종목 docs
    dartlab collect --auto                    # 미수집 docs 전체
    dartlab collect --batch                   # 전체 상장, 미수집만
    dartlab collect --batch -c finance        # 전체 상장, 재무만
    dartlab collect --check 005930            # freshness 체크
    dartlab collect --incremental 005930      # 누락 공시 증분 수집

    # EDGAR (ticker = 영문 → 자동 감지)
    dartlab collect AAPL MSFT GOOGL           # 지정 ticker
    dartlab collect --tier sp500              # S&P 500 전체
    dartlab collect --tier sp500 --limit 10   # 10개만 테스트
"""

from __future__ import annotations


def _isEdgarCode(code: str) -> bool:
    """영문 ticker면 True, 숫자 종목코드면 False."""
    return not code.isdigit()


def _detectSource(args) -> str:
    """인자로부터 dart/edgar 자동 감지."""
    if getattr(args, "tier", None):
        return "edgar"
    if args.codes and all(_isEdgarCode(c) for c in args.codes):
        return "edgar"
    return "dart"


def configure_parser(subparsers) -> None:
    parser = subparsers.add_parser(
        "collect",
        help="DART/EDGAR 공시문서 수집 (종목코드=DART, ticker=EDGAR 자동 감지)",
    )
    parser.add_argument(
        "codes",
        nargs="*",
        help="종목코드/ticker (숫자=DART, 영문=EDGAR)",
    )
    # DART 전용
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
        help="미수집 종목 자동 수집 (DART)",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="수집 현황 통계 출력 (DART)",
    )
    parser.add_argument(
        "--uncollected",
        action="store_true",
        help="미수집 종목 목록 출력 (DART)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="최대 종목 수",
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="배치 모드 (DART: finance/report/docs 전체, 멀티키 병렬)",
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
        help="freshness 체크만 (수집 안 함, DART)",
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="누락 공시만 증분 수집 (DART)",
    )
    # EDGAR 전용
    parser.add_argument(
        "--tier",
        type=str,
        default=None,
        help="EDGAR 배치 tier (sp500)",
    )
    parser.set_defaults(handler=run)


def run(args) -> int:
    from dartlab.cli.services.output import get_console

    console = get_console()

    source = _detectSource(args)

    if source == "edgar":
        return _runEdgar(console, args)

    # --- DART ---
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
        _printHelp(console)
        return 1

    return _runCollect(console, args)


def _printHelp(console) -> None:
    """통합 도움말."""
    console.print("[bold]dartlab collect[/] — DART/EDGAR 데이터 수집\n")
    console.print("  [bold]DART[/] (종목코드 = 숫자 → 자동 감지):")
    console.print("  dartlab collect 005930              단일 종목 docs")
    console.print("  dartlab collect --auto              미수집 docs 자동 수집")
    console.print("  dartlab collect --stats             수집 현황")
    console.print("  dartlab collect --check 005930      freshness 체크")
    console.print("  dartlab collect --incremental 005930 누락 공시 증분 수집")
    console.print("  dartlab collect --batch             전체 상장 배치 수집")
    console.print()
    console.print("  [bold]EDGAR[/] (ticker = 영문 → 자동 감지):")
    console.print("  dartlab collect AAPL MSFT           지정 ticker 수집")
    console.print("  dartlab collect --tier sp500        S&P 500 전체 수집")
    console.print("  dartlab collect --tier sp500 --limit 10  10개만 테스트")


# ── EDGAR ─────────────────────────────────────────────


def _runEdgar(console, args) -> int:
    """EDGAR docs 수집."""
    from dartlab.core.dataLoader import _dataDir
    from dartlab.providers.edgar.docs.fetch import fetchEdgarDocs

    outDir = _dataDir("edgarDocs")
    outDir.mkdir(parents=True, exist_ok=True)

    tickers: list[str] = []

    if args.codes:
        tickers = [c.upper() for c in args.codes]
    elif args.tier:
        tickers = _loadEdgarTickers(args.tier)
        if tickers is None:
            console.print(f"[red]tier '{args.tier}'에 해당하는 ticker 없음[/]")
            return 1
    else:
        console.print("[bold]dartlab collect[/] — EDGAR docs 수집\n")
        console.print("  dartlab collect AAPL MSFT           지정 ticker")
        console.print("  dartlab collect --tier sp500        S&P 500 전체")
        console.print("  dartlab collect --tier sp500 --limit 10  10개만")
        return 1

    if args.limit and len(tickers) > args.limit:
        tickers = tickers[: args.limit]

    # 이미 수집된 ticker 스킵
    existing = {f.stem for f in outDir.glob("*.parquet")}
    targets = [t for t in tickers if t not in existing]
    skippedCount = len(tickers) - len(targets)

    console.print(f"[bold]EDGAR docs 수집[/]: {len(targets)}개 ticker (스킵 {skippedCount}개)\n")

    if not targets:
        console.print("[green]모든 ticker가 이미 수집되었습니다.[/]")
        return 0

    succeeded = 0
    failed = 0
    failedTickers: list[str] = []

    for i, ticker in enumerate(targets, 1):
        outPath = outDir / f"{ticker}.parquet"
        console.print(f"  [{i}/{len(targets)}] {ticker} ... ", end="")
        try:
            fetchEdgarDocs(ticker, outPath, showProgress=True)
            succeeded += 1
            console.print("[green]OK[/]")
        except (ValueError, KeyError, RuntimeError, OSError, TimeoutError, AttributeError) as e:
            failed += 1
            failedTickers.append(ticker)
            console.print(f"[red]실패: {e}[/]")

    console.print(f"\n[bold green]완료[/]: 성공 {succeeded} / 실패 {failed} / 스킵 {skippedCount}")
    if failedTickers:
        console.print(f"실패 목록: {', '.join(failedTickers[:20])}")
    return 0


def _loadEdgarTickers(tier: str) -> list[str] | None:
    """edgarTickers.json에서 tier별 ticker 목록."""
    import json
    from pathlib import Path

    candidates = [
        Path(__file__).resolve().parents[4] / ".github" / "data" / "edgarTickers.json",
    ]
    for fp in candidates:
        if fp.exists():
            data = json.loads(fp.read_text(encoding="utf-8"))
            tickers = data.get(tier, [])
            return tickers if tickers else None
    return None


# ── DART ──────────────────────────────────────────────


def _runStats(console) -> int:
    from dartlab.providers.dart.openapi.collector import collectionStats

    stats = collectionStats()
    console.print(f"전체 상장: {stats['totalListed']}")
    console.print(f"수집 완료: {stats['collected']}")
    console.print(f"미수집:    {stats['uncollected']}")
    return 0


def _runUncollected(console, limit: int) -> int:
    from dartlab.providers.dart.openapi.collector import listUncollectedKind

    stocks = listUncollectedKind()
    showing = min(limit, len(stocks))
    console.print(f"미수집 종목: {len(stocks)}개 (상위 {showing}개 표시)")
    for code, name in stocks[:limit]:
        console.print(f"  {code}  {name}")
    return 0


def _runAuto(console, args) -> int:
    from dartlab.providers.dart.openapi.batch import batchCollect
    from dartlab.providers.dart.openapi.collector import listUncollectedKind

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
    from dartlab.providers.dart.openapi.batch import batchCollect, batchCollectAll
    from dartlab.providers.dart.openapi.dartKey import resolveDartKeys

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
    from dartlab.providers.dart.openapi.dartKey import hasDartApiKey
    from dartlab.providers.dart.openapi.freshness import (
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
                console.print(
                    f"  ⚠ {row['stockCode']} {row['corpName']} — 새 공시 {row['newCount']}건 ({row['latestReport']})"
                )
    return 0


def _runIncremental(console, args) -> int:
    from dartlab.providers.dart.openapi.dartKey import hasDartApiKey
    from dartlab.providers.dart.openapi.freshness import (
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
        from dartlab.providers.dart.openapi.zipCollector import ZipDocsCollector

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
        from dartlab.providers.dart.openapi.batch import batchCollect

        results = batchCollect(codes, categories=["docs"])
        total = len(results)
        success = sum(1 for v in results.values() if v.get("docs", 0) > 0)
        console.print(f"\n[bold green]완료[/]: 성공 {success} / 총 {total}")

    return 0
