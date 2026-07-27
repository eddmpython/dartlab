"""`dartlab collect` command — DART/EDGAR 데이터 수집.

사용 예시::

    # DART (종목코드 = 숫자 → 자동 감지)
    dartlab collect 005930                    # 단일 종목 (finance+report 증분)
    dartlab collect 005930 -c finance         # finance만 증분 수집
    dartlab collect 005930 -c finance,report  # finance+report만
    dartlab collect --check 005930            # freshness 체크 (panel+finance+report)
    dartlab collect --incremental 005930      # 누락 공시 증분 수집
    dartlab collect --auto                    # 안내 출력
    dartlab collect --batch                   # 전체 상장, 미수집만
    dartlab collect --batch -c finance        # 전체 상장, 재무만

    # EDGAR (ticker = 영문 → 자동 감지)
    dartlab collect AAPL MSFT GOOGL           # 지정 ticker
    dartlab collect --tier sp500              # S&P 500 전체
    dartlab collect --tier sp500 --limit 10   # 10개만 테스트
"""

from __future__ import annotations


def _isEdgarCode(code: str) -> bool:
    """영문 ticker면 True, KR 종목코드면 False."""
    from dartlab.core.market import isKrStockCode

    # KRX 단축코드 (6자리 숫자 또는 숫자 선두 영숫자, 예 0008Z0) 는 DART 경로.
    return not isKrStockCode(code) and not code.isdigit()


def _detectSource(args) -> str:
    """인자로부터 dart/edgar 자동 감지."""
    if getattr(args, "tier", None):
        return "edgar"
    if args.codes and all(_isEdgarCode(c) for c in args.codes):
        return "edgar"
    return "dart"


def configureParser(subparsers) -> None:
    """collect 서브커맨드 등록 — DART/EDGAR 데이터 수집."""
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
        help="배치 모드 (DART: finance/report, 멀티키 병렬)",
    )
    parser.add_argument(
        "--categories",
        "-c",
        type=str,
        default=None,
        help="수집 카테고리 (쉼표 구분: finance,report)",
    )
    parser.add_argument(
        "--mode",
        choices=["new", "all"],
        default="all",
        help="all=전체 종목 증분 / new=미수집 종목만 (기본: all)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="freshness 체크만 (수집 안 함, DART)",
    )
    parser.add_argument(
        "--repair-cache",
        action="store_true",
        help="로컬 캐시 무결성 일괄 검사 + stale 파일 자동 재다운로드 (DART)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="--repair-cache와 함께 — 다운로드 안 하고 stale 통계만 출력",
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="누락 공시만 증분 수집 (DART)",
    )
    # scan 프리빌드
    parser.add_argument(
        "--scan",
        nargs="?",
        const="all",
        default=None,
        help="전종목 scan 프리빌드 (all/changes/finance/finance-lite/report)",
    )
    parser.add_argument(
        "--since-year",
        type=int,
        default=2021,
        help="scan 프리빌드 시작 연도 (기본 2021)",
    )
    # EDGAR 전용
    parser.add_argument(
        "--tier",
        type=str,
        default=None,
        help="EDGAR 배치 tier (all/nasdaq/nyse/sp500)",
    )
    parser.add_argument(
        "--deploy",
        action="store_true",
        help="수집 후 HuggingFace에 업로드 (EDGAR)",
    )
    parser.set_defaults(handler=run)


def run(args) -> int:
    """소스 자동 감지 후 DART/EDGAR 데이터를 수집한다."""
    from dartlab.cli.services.output import getConsole

    console = getConsole()

    source = _detectSource(args)

    if source == "edgar":
        # EDGAR scan 프리빌드
        if getattr(args, "scan", None):
            return _runEdgarScan(console, args)
        # EDGAR freshness 체크
        if getattr(args, "check", False):
            return _runEdgarCheck(console, args)
        if getattr(args, "incremental", False):
            return _runEdgarIncremental(console, args)
        if getattr(args, "stats", False):
            return _runEdgarStats(console, args)
        if getattr(args, "uncollected", False):
            return _runEdgarUncollected(console, args)
        return _runEdgar(console, args)

    # --- scan 프리빌드 ---
    if getattr(args, "scan", None):
        return _runScan(console, args)

    # --- DART ---
    if getattr(args, "repair_cache", False):
        return _runRepairCache(console, args)

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
    console.print("  dartlab collect 005930              단일 종목 (finance+report)")
    console.print("  dartlab collect 005930 -c finance   finance만 증분 수집")
    console.print("  dartlab collect --check 005930      freshness 체크 (panel+finance+report)")
    console.print("  dartlab collect --incremental 005930 누락 증분 수집")
    console.print("  dartlab collect --auto              collect 안내")
    console.print("  dartlab collect --batch             전체 상장 배치 수집")
    console.print("  dartlab collect --stats             수집 현황")
    console.print()
    console.print("  [bold]scan 프리빌드[/]:")
    console.print("  dartlab collect --scan              DART 전종목 횡단분석 프리빌드")
    console.print("  dartlab collect --scan changes      changes만 프리빌드")
    console.print("  dartlab collect --scan finance      finance만 프리빌드")
    console.print("  dartlab collect --scan finance-lite 브라우저 용 경량 finance (~18MB)")
    console.print("  dartlab collect --scan report       report만 프리빌드")
    console.print("  dartlab collect --tier sp500 --scan EDGAR scan 프리빌드")
    console.print()
    console.print("  [bold]EDGAR[/] (ticker = 영문 → 자동 감지):")
    console.print("  dartlab collect AAPL MSFT                   지정 ticker (finance+docs)")
    console.print("  dartlab collect AAPL -c finance              finance만 수집")
    console.print("  dartlab collect --tier sp500                 S&P 500 전체")
    console.print("  dartlab collect --tier all                   Nasdaq+NYSE 전체")
    console.print("  dartlab collect --tier nasdaq -c finance     Nasdaq finance만")
    console.print("  dartlab collect --tier sp500 --limit 10      10개만 테스트")
    console.print("  dartlab collect --batch --tier all            전체 배치")
    console.print("  dartlab collect --batch --tier all --mode new 미수집만")


# ── 캐시 무결성 회복 ────────────────────────────────────


def _runRepairCache(console, args) -> int:
    """로컬 dart 캐시 전수 무결성 검사 + 손상된 파일 자동 재다운로드.

    과거 ETag 사이드카 first-write 버그(2026-04-06 발견)로 영구 stale로 굳어진
    로컬 parquet들을 일괄 회복한다. ETag + Content-Length 2단계 검증.
    """
    from dartlab.core.dataLoader import repairLocalCache

    dryRun = getattr(args, "dry_run", False)
    catsArg = getattr(args, "categories", None)
    cats = [c.strip() for c in catsArg.split(",")] if catsArg else ["finance", "report", "panel"]

    console.print(f"[bold]캐시 무결성 회복[/] categories={cats} dryRun={dryRun}")
    if dryRun:
        console.print("[yellow]dryRun 모드: 통계만 출력, 다운로드 안 함[/]")

    total = {"checked": 0, "stale": 0, "repaired": 0, "failed": 0, "fresh": 0}
    for cat in cats:
        console.print(f"\n[cyan]── {cat} ──[/]")
        try:
            stats = repairLocalCache(cat, dryRun=dryRun)
        except (OSError, RuntimeError) as e:
            console.print(f"[red]{cat} 실패: {e}[/]")
            continue
        for k, v in stats.items():
            total[k] = total.get(k, 0) + v
        console.print(
            f"  checked={stats['checked']}  fresh={stats['fresh']}  "
            f"stale={stats['stale']}  repaired={stats['repaired']}  failed={stats['failed']}"
        )

    console.print(f"\n[bold green]총합[/]: {total}")
    return 0 if total["failed"] == 0 else 2


# ── scan 프리빌드 ──────────────────────────────────────


def _runScan(console, args) -> int:
    """전종목 scan 프리빌드 실행."""
    from dartlab.scan.builders.kr.core import (
        buildChanges,
        buildFinance,
        buildFinanceLite,
        buildReport,
        buildScan,
    )

    target = getattr(args, "scan", "all")
    sinceYear = getattr(args, "since_year", 2021)

    console.print(f"[bold]scan 프리빌드[/] target={target}, sinceYear={sinceYear}")

    if target == "all":
        buildScan(sinceYear=sinceYear, verbose=True)
    elif target == "changes":
        buildChanges(sinceYear=sinceYear, verbose=True)
    elif target == "finance":
        buildFinance(sinceYear=sinceYear, verbose=True)
    elif target == "finance-lite":
        buildFinanceLite(verbose=True)
    elif target == "report":
        buildReport(sinceYear=sinceYear, verbose=True)
    else:
        console.print(f"[red]알 수 없는 scan 타겟: {target}[/]")
        return 1

    return 0


# ── EDGAR ─────────────────────────────────────────────


def _runEdgar(console, args) -> int:
    """EDGAR 데이터 수집 — 배치 병렬 + 카테고리 선택."""
    from dartlab.gather.edgar.batch import (
        batchCollectEdgar,
        batchCollectEdgarAll,
    )

    # 카테고리 파싱
    cats = [c.strip() for c in args.categories.split(",")] if args.categories else ["finance", "docs"]

    # 카테고리 검증
    validCats = {"finance", "docs"}
    invalidCats = [c for c in cats if c not in validCats]
    if invalidCats:
        console.print(f"[red]유효하지 않은 EDGAR 카테고리: {invalidCats}. 지원: {sorted(validCats)}[/]")
        return 1
    catLabel = ", ".join(cats)

    # tier 검증
    validTiers = {"all", "nasdaq", "nyse", "sp500"}
    if args.tier and args.tier not in validTiers:
        console.print(f"[red]유효하지 않은 tier: '{args.tier}'. 지원: {sorted(validTiers)}[/]")
        return 1

    tickers: list[str] = []

    if args.codes:
        tickers = [c.upper() for c in args.codes]
    elif args.tier:
        loaded = _loadEdgarTickers(args.tier)
        if loaded is None:
            console.print(f"[red]tier '{args.tier}'에 해당하는 ticker 없음[/]")
            return 1
        tickers = loaded
    else:
        console.print("[bold]dartlab collect[/] — EDGAR 데이터 수집\n")
        console.print("  dartlab collect AAPL MSFT                   지정 ticker")
        console.print("  dartlab collect AAPL -c finance              finance만")
        console.print("  dartlab collect --tier sp500                 S&P 500 전체")
        console.print("  dartlab collect --tier all                   Nasdaq+NYSE 전체")
        console.print("  dartlab collect --tier sp500 -c finance      S&P 500 finance만")
        console.print("  dartlab collect --tier sp500 --limit 10      10개만 테스트")
        console.print("  dartlab collect --batch --tier all            전체 배치")
        console.print("  dartlab collect --batch --tier all --mode new 미수집만")
        return 1

    if args.limit and len(tickers) > args.limit:
        tickers = tickers[: args.limit]

    # --batch + --tier → batchCollectEdgarAll
    if getattr(args, "batch", False) and getattr(args, "tier", None):
        mode = getattr(args, "mode", "all")
        console.print(f"[bold]EDGAR 배치 수집[/]: tier={args.tier}, mode={mode}, {catLabel}\n")
        results = batchCollectEdgarAll(
            tier=args.tier,
            categories=cats,
            mode=mode,
        )
        total = len(results)
        success = sum(1 for v in results.values() if any(cnt > 0 for cnt in v.values()))
        console.print(f"\n[bold green]완료[/]: 수집 {success} / 총 {total}")
        return 0

    console.print(f"[bold]EDGAR 수집[/]: {len(tickers)}개 ticker | {catLabel}\n")

    results = batchCollectEdgar(
        tickers,
        categories=cats,
        incremental=True,
    )

    total = len(results)
    success = sum(1 for v in results.values() if any(cnt > 0 for cnt in v.values()))
    skipped = sum(1 for v in results.values() if all(cnt == 0 for cnt in v.values()))
    console.print(f"\n[bold green]완료[/]: 수집 {success} / 스킵 {skipped} / 총 {total}")

    # --deploy: HuggingFace 업로드
    if getattr(args, "deploy", False):
        from dartlab.providers.edgar.openapi.deploy import deployEdgarToHF

        console.print("\n[bold]HuggingFace 업로드 시작[/]...\n")
        deployResult = deployEdgarToHF(categories=cats)
        for cat, count in deployResult.items():
            console.print(f"  {cat}: {count}개 업로드")

    return 0


def _runEdgarScan(console, args) -> int:
    """EDGAR scan 프리빌드."""
    from dartlab.scan.builders.edgar.builder import buildEdgarScan

    sinceYear = getattr(args, "since_year", 2021)
    console.print(f"[bold]EDGAR scan 프리빌드[/] sinceYear={sinceYear}\n")
    path = buildEdgarScan(sinceYear=sinceYear, verbose=True)
    console.print(f"\n[bold green]완료[/]: {path}")
    return 0


def _runEdgarCheck(console, args) -> int:
    """EDGAR freshness 체크."""
    from dartlab.providers.edgar.openapi.freshness import checkEdgarFreshness

    tickers = []
    if args.codes:
        tickers = [c.upper() for c in args.codes]
    elif args.tier:
        loaded = _loadEdgarTickers(args.tier)
        tickers = (loaded or [])[: args.limit or 20]

    if not tickers:
        console.print("[red]체크할 ticker를 지정하세요.[/]")
        return 1

    for t in tickers:
        result = checkEdgarFreshness(t, forceCheck=True)
        if result.docsMissing:
            console.print(f"  ⚠ {t} docs — 미수집")
        elif result.missingCount > 0:
            console.print(f"  ⚠ {t} docs — 새 filing {result.missingCount}건")
        else:
            console.print(f"  ✓ {t} docs — 최신 상태")

        if result.financeMissing:
            console.print(f"  ⚠ {t} finance — 미수집")
        else:
            console.print(f"  ✓ {t} finance — 최신 상태")
    return 0


def _runEdgarIncremental(console, args) -> int:
    """EDGAR 증분 수집."""
    from dartlab.providers.edgar.openapi.freshness import (
        checkEdgarFreshness,
        collectEdgarMissing,
    )

    cats = [c.strip() for c in args.categories.split(",")] if args.categories else None

    tickers = []
    if args.codes:
        tickers = [c.upper() for c in args.codes]
    elif args.tier:
        loaded = _loadEdgarTickers(args.tier)
        tickers = (loaded or [])[: args.limit or 50]

    if not tickers:
        console.print("[red]수집할 ticker를 지정하세요.[/]")
        return 1

    for t in tickers:
        result = checkEdgarFreshness(t, forceCheck=True)
        if result.isFresh:
            console.print(f"  ✓ {t} — 최신 상태")
        else:
            console.print(f"  ⚠ {t} — 수집 중...")
            counts = collectEdgarMissing(t, categories=cats)
            summary = ", ".join(f"{k}:{v}" for k, v in counts.items() if v > 0)
            console.print(f"  ✓ {t} ({summary or '변경 없음'})")
    return 0


def _runEdgarStats(console, args) -> int:
    """EDGAR 수집 현황 통계."""
    import polars as pl

    from dartlab.providers.edgar.openapi.freshness import scanEdgarMarketFreshness

    tier = getattr(args, "tier", None) or "sp500"
    console.print(f"[bold]EDGAR 수집 현황[/] (tier={tier})\n")

    df = scanEdgarMarketFreshness(tier=tier)
    if df.is_empty():
        console.print("[yellow]유니버스가 비어 있습니다.[/]")
        return 0

    total = df.height
    complete = df.filter(pl.col("status") == "complete").height
    partial = df.filter(pl.col("status") == "partial").height
    missing = df.filter(pl.col("status") == "missing").height
    hasDocs = df.filter(pl.col("hasDocs")).height
    hasFinance = df.filter(pl.col("hasFinance")).height

    console.print(f"  전체: {total}")
    console.print(f"  완전 수집 (docs+finance): {complete}")
    console.print(f"  부분 수집: {partial}")
    console.print(f"  미수집: {missing}")
    console.print(f"  docs 보유: {hasDocs}")
    console.print(f"  finance 보유: {hasFinance}")
    return 0


def _runEdgarUncollected(console, args) -> int:
    """EDGAR 미수집 ticker 목록."""
    from dartlab.providers.edgar.openapi.freshness import scanEdgarMarketFreshness

    tier = getattr(args, "tier", None) or "sp500"
    limit = args.limit or 20

    import polars as pl

    df = scanEdgarMarketFreshness(tier=tier)
    uncollected = df.filter(pl.col("status") != "complete")

    showing = min(limit, uncollected.height)
    console.print(f"[bold]EDGAR 미수집[/]: {uncollected.height}개 (tier={tier}, 상위 {showing}개)\n")

    for row in uncollected.head(limit).iter_rows(named=True):
        parts = []
        if not row["hasDocs"]:
            parts.append("docs")
        if not row["hasFinance"]:
            parts.append("finance")
        console.print(f"  {row['ticker']:<8} 미수집: {', '.join(parts)}")
    return 0


def _loadEdgarTickers(tier: str) -> list[str] | None:
    """tier별 EDGAR ticker 목록 — SEC 동적 유니버스 우선, 정적 JSON fallback."""
    try:
        from dartlab.core.dataLoader import loadEdgarTargetUniverse

        df = loadEdgarTargetUniverse(tier)
        if df.height > 0:
            return df["ticker"].to_list()
    except (ImportError, OSError, ValueError):
        pass

    # fallback: 정적 JSON
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
    from dartlab.gather.dart.collector import collectionStats

    stats = collectionStats()
    console.print(f"전체 상장: {stats['totalListed']}")
    console.print(f"수집 완료: {stats['collected']}")
    console.print(f"미수집:    {stats['uncollected']}")
    return 0


def _runUncollected(console, limit: int) -> int:
    from dartlab.gather.dart.collector import listUncollectedKind

    stocks = listUncollectedKind()
    showing = min(limit, len(stocks))
    console.print(f"미수집 종목: {len(stocks)}개 (상위 {showing}개 표시)")
    for code, name in stocks[:limit]:
        console.print(f"  {code}  {name}")
    return 0


def _runAuto(console, args) -> int:
    console.print(
        "[yellow]DART collect는 finance/report 증분 수집만 담당합니다. panel은 pipeline/buildPanel 경로를 사용하세요.[/]"
    )
    return 0


def _parseDartCollectCategories(raw: str | None, console) -> list[str] | None:
    """CLI 입력 카테고리를 DART batch 수집 표면으로 제한."""
    if raw is None:
        return None
    cats = [c.strip() for c in raw.split(",") if c.strip()]
    invalid = [c for c in cats if c not in {"finance", "report"}]
    if invalid:
        console.print(f"[red]DART collect 카테고리는 finance/report만 지원합니다: {invalid}[/]")
        return []
    return cats


def _runBatch(console, args) -> int:
    from dartlab.gather.dart.batch import batchCollect, batchCollectAll
    from dartlab.gather.dart.keys import resolveDartKeys

    keys = resolveDartKeys()
    if not keys:
        console.print("[red]DART API 키가 필요합니다. DART_API_KEY(S) 환경변수를 설정하세요.[/]")
        return 1

    cats = _parseDartCollectCategories(args.categories, console)
    if cats == []:
        return 1
    catLabel = ", ".join(cats) if cats else "finance, report"

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
    from dartlab.gather.dart.freshness import (
        checkFreshness,
        scanMarketFreshness,
    )
    from dartlab.gather.dart.keys import hasDartApiKey

    if not hasDartApiKey():
        console.print("[red]DART API 키가 필요합니다: dartlab setup dart-key[/]")
        return 1

    if args.codes:
        for code in args.codes:
            result = checkFreshness(code, forceCheck=True)
            # panel freshness
            if result.missingCount > 0:
                console.print(f"  ⚠ {code} panel — 새 공시 {result.missingCount}건")
                for f in result.missingFilings[:5]:
                    console.print(f"    {f['rcept_dt']} {f['report_nm']}")
            else:
                console.print(f"  ✓ {code} panel — 최신 상태")

            # finance freshness
            if result.financeMissing:
                console.print(
                    f"  ⚠ {code} finance — 미수집 {len(result.financeMissing)}기간: {', '.join(result.financeMissing[:6])}"
                )
            else:
                console.print(f"  ✓ {code} finance — 최신 상태")

            # report freshness
            if result.reportMissing:
                console.print(
                    f"  ⚠ {code} report — 미수집 {len(result.reportMissing)}기간: {', '.join(result.reportMissing[:6])}"
                )
            else:
                console.print(f"  ✓ {code} report — 최신 상태")
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
    from dartlab.gather.dart.freshness import (
        checkFreshness,
        collectMissing,
        scanMarketFreshness,
    )
    from dartlab.gather.dart.keys import hasDartApiKey

    if not hasDartApiKey():
        console.print("[red]DART API 키가 필요합니다: dartlab setup dart-key[/]")
        return 1

    cats = _parseDartCollectCategories(args.categories, console)
    if cats == []:
        return 1

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
    cats = _parseDartCollectCategories(args.categories, console) if args.categories else ["finance", "report"]
    if cats == []:
        return 1

    if len(codes) == 1:
        code = codes[0]
        result: dict[str, int] = {}

        # finance/report 증분 수집
        frCats = [c for c in cats if c in ("finance", "report")]
        if frCats:
            from dartlab.gather.dart.batch import batchCollect

            console.print(f"\n[bold]{', '.join(frCats)}[/] 증분 수집 중...")
            counts = batchCollect([code], categories=frCats, incremental=True)
            codeResult = counts.get(code, {})
            for cat in frCats:
                result[cat] = codeResult.get(cat, 0) if isinstance(codeResult, dict) else 0

        summary = " / ".join(f"{k}: {v}" for k, v in result.items())
        console.print(f"\n[bold green]완료[/]: {summary}")
    else:
        from dartlab.gather.dart.batch import batchCollect

        results = batchCollect(codes, categories=cats)
        total = len(results)
        success = sum(1 for v in results.values() if any(cnt > 0 for cnt in v.values()))
        console.print(f"\n[bold green]완료[/]: 성공 {success} / 총 {total}")

    return 0
