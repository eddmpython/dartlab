"""EDGAR 배치 수집 — 병렬 + 증분.

DART batch.py 패턴을 SEC에 이식.
워커 N개 → asyncio.Queue 기반 ticker 분배.
API 키 불필요 (SEC public API, User-Agent 식별).

개별: saveDocs("AAPL"), saveFinance("0000320193")
배치: batchCollectEdgar(["AAPL", "MSFT"], categories=["finance", "docs"])
전체: batchCollectEdgarAll(tier="sp500", categories=["finance"])
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import logging
import os
import threading
import uuid
from pathlib import Path

import httpx
import polars as pl

from dartlab.core.edgarClient import DEFAULT_BASE_URL, EdgarApiError
from dartlab.gather.batchProgress import buildWorkerTable
from dartlab.gather.edgar.asyncClient import AsyncEdgarClient

_log = logging.getLogger(__name__)

# ── 상수 ──

_MAX_WORKERS = 3

# ticker-level lock: 동일 ticker 동시 쓰기 방지
_TICKER_LOCKS: dict[str, asyncio.Lock] = {}
_TICKER_LOCK_GUARD = asyncio.Lock()


async def _getTickerLock(key: str) -> asyncio.Lock:
    """ticker/cik 키별 asyncio Lock 반환 (동시 쓰기 방지)."""
    async with _TICKER_LOCK_GUARD:
        if key not in _TICKER_LOCKS:
            _TICKER_LOCKS[key] = asyncio.Lock()
        return _TICKER_LOCKS[key]


# ── 증분 유틸 ──


def _edgarDataPath(category: str, key: str) -> Path:
    """EDGAR parquet 저장 경로."""
    from dartlab.core.dataConfig import DATA_RELEASES
    from dartlab.core.dataLoader import _getDataRoot

    subDir = DATA_RELEASES[category]["dir"]
    dest = _getDataRoot() / subDir / f"{key}.parquet"
    dest.parent.mkdir(parents=True, exist_ok=True)
    return dest


def _existingDocsAccessions(path: Path) -> set[str]:
    """기존 docs parquet에서 수집된 accession_no 세트."""
    if not path.exists():
        return set()
    try:
        schema = pl.read_parquet_schema(path)
        if "accession_no" not in schema:
            return set()
        df = pl.scan_parquet(path).select("accession_no").unique().collect(engine="streaming")
        return set(df["accession_no"].drop_nulls().to_list())
    except (pl.exceptions.ComputeError, pl.exceptions.SchemaError, OSError):
        return set()


def _existingFinanceLatestFiled(path: Path) -> str | None:
    """기존 finance parquet에서 최신 filed 날짜."""
    if not path.exists():
        return None
    try:
        schema = pl.read_parquet_schema(path)
        if "filed" not in schema:
            return None
        df = pl.scan_parquet(path).select(pl.col("filed").max()).collect(engine="streaming")
        val = df[0, 0]
        return str(val) if val is not None else None
    except (pl.exceptions.ComputeError, pl.exceptions.SchemaError, OSError):
        return None


def _resolveTickerMap(tickers: list[str]) -> dict[str, dict[str, str]]:
    """ticker 목록 → {ticker: {"cik": ..., "title": ...}} 맵."""
    from dartlab.core.dataLoader import loadEdgarListedUniverse

    universe = loadEdgarListedUniverse()
    tickerMap: dict[str, dict[str, str]] = {}

    for t in tickers:
        upper = t.upper()
        match = universe.filter(pl.col("ticker") == upper)
        if match.height > 0:
            row = match.row(0, named=True)
            tickerMap[upper] = {"cik": row["cik"], "title": row.get("title", upper)}
        else:
            tickerMap[upper] = {"cik": "", "title": upper}

    return tickerMap


# ── 단일 종목 수집 (비동기) ──


async def _collectEdgarFinance(
    ticker: str,
    cik: str,
    client: AsyncEdgarClient,
    *,
    incremental: bool = True,
    onPeriod=None,
) -> int:
    """companyfacts API → parquet 저장. 반환: 행 수."""
    from dartlab.core.edgarClient import companyFactsToRows

    if not cik:
        return 0

    path = _edgarDataPath("edgar", cik)

    # incremental: 파일이 있으면 스킵 (companyfacts는 전체 교체)
    if incremental and path.exists():
        latestFiled = _existingFinanceLatestFiled(path)
        if latestFiled:
            from datetime import date

            try:
                filedDate = date.fromisoformat(latestFiled)
                if (date.today() - filedDate).days < 7:
                    return 0
            except (ValueError, TypeError):
                pass

    if onPeriod:
        onPeriod(f"finance {ticker}")

    url = f"{DEFAULT_BASE_URL}/api/xbrl/companyfacts/CIK{cik}.json"
    try:
        payload = await client.getJson(url)
    except EdgarApiError as exc:
        _log.warning("finance %s (CIK %s): API 오류 — %s", ticker, cik, exc)
        return 0

    df = companyFactsToRows(payload)
    if df.height == 0:
        return 0

    lock = await _getTickerLock(f"finance:{cik}")
    async with lock:
        tmpPath = path.with_name(f"{path.stem}.tmp-{uuid.uuid4().hex[:8]}{path.suffix}")
        try:
            df.write_parquet(tmpPath)
            os.replace(tmpPath, path)
        finally:
            if tmpPath.exists():
                tmpPath.unlink(missing_ok=True)

    return df.height


async def _collectEdgarDocs(
    ticker: str,
    cik: str,
    client: AsyncEdgarClient,
    *,
    incremental: bool = True,
    onPeriod=None,
) -> int:
    """SEC submissions → 10-K/10-Q HTML fetch → parquet. 반환: 섹션 수."""
    from dartlab.gather.edgar.docs.fetch import fetchEdgarDocs

    if not cik:
        return 0

    path = _edgarDataPath("edgarDocs", ticker)

    # incremental: 파일이 있으면 스킵
    if incremental and path.exists():
        return 0

    if onPeriod:
        onPeriod(f"docs {ticker}")

    lock = await _getTickerLock(f"docs:{ticker}")
    async with lock:
        # lock 획득 후 다시 확인 (다른 워커가 이미 완료했을 수 있음)
        if incremental and path.exists():
            return 0

        tmpPath = path.with_name(f"{path.stem}.tmp-{uuid.uuid4().hex[:8]}{path.suffix}")
        try:
            fetchEdgarDocs(ticker, tmpPath, showProgress=False)
            if tmpPath.exists() and tmpPath.stat().st_size > 0:
                os.replace(tmpPath, path)
                df = pl.read_parquet(path)
                return df.height
            return 0
        except (ValueError, KeyError, RuntimeError, OSError, TimeoutError, AttributeError) as exc:
            _log.warning("docs %s: 수집 실패 — %s: %s", ticker, type(exc).__name__, exc)
            return 0
        finally:
            if tmpPath.exists():
                tmpPath.unlink(missing_ok=True)


# ── asyncio 유틸 ──


def _runAsync(coro):
    """코루틴을 별도 스레드에서 실행 (이미 이벤트 루프가 있을 때)."""
    with concurrent.futures.ThreadPoolExecutor(1) as pool:
        future = pool.submit(asyncio.run, coro)
        return future.result()


# ── 워커 + 배치 ──


async def _workerLoop(
    workerIndex: int,
    client: AsyncEdgarClient,
    queue: asyncio.Queue,
    categories: list[str],
    results: dict,
    tickerMap: dict[str, dict[str, str]],
    incremental: bool,
    onComplete,
    onStatus,
    onPeriod,
) -> None:
    """워커: 큐에서 ticker 꺼내서 수집. rate limit 시 종료."""
    while not client.exhausted:
        try:
            ticker = queue.get_nowait()
        except asyncio.QueueEmpty:
            if onPeriod:
                onPeriod(workerIndex, "", "완료")
            return

        info = tickerMap.get(ticker, {"cik": "", "title": ticker})
        cik = info["cik"]
        title = info["title"]
        result: dict[str, int] = {}

        if onStatus:
            onStatus(workerIndex, ticker, title)

        def _periodCb(msg):
            if onPeriod:
                onPeriod(workerIndex, title, msg)

        for cat in categories:
            if client.exhausted:
                await queue.put(ticker)
                return
            try:
                if cat == "finance":
                    count = await _collectEdgarFinance(
                        ticker,
                        cik,
                        client,
                        incremental=incremental,
                        onPeriod=_periodCb,
                    )
                elif cat == "docs":
                    count = await _collectEdgarDocs(
                        ticker,
                        cik,
                        client,
                        incremental=incremental,
                        onPeriod=_periodCb,
                    )
                else:
                    count = 0
                result[cat] = count
            except asyncio.CancelledError:
                return
            except (httpx.HTTPError, OSError, ValueError, KeyError, RuntimeError, EdgarApiError) as exc:
                _log.warning("worker %d: %s/%s 실패 — %s: %s", workerIndex, ticker, cat, type(exc).__name__, exc)
                result[cat] = 0

        if not client.exhausted:
            results[ticker] = result
            if onComplete:
                catSummary = " ".join(f"{k}:{v}" for k, v in result.items() if v > 0)
                onComplete(title, catSummary)

        queue.task_done()


def batchCollectEdgar(
    tickers: list[str],
    *,
    categories: list[str] | None = None,
    maxWorkers: int | None = None,
    incremental: bool = True,
    showProgress: bool = True,
) -> dict[str, dict[str, int]]:
    """병렬 배치 수집. 워커 N개 → ticker 분배.

    Args:
        tickers: 대상 ticker 리스트.
        categories: ``["finance", "docs"]`` 기본. None 이면 동일.
        maxWorkers: 동시 워커 수.
        incremental: 기존 파일 skip 여부.
        showProgress: Rich live progress 표시.

    Returns:
        ``{"AAPL": {"finance": 12000, "docs": 450}, ...}`` dict.

    Raises:
        없음 (KeyboardInterrupt 는 정상 종료).

    Example:
        >>> batchCollectEdgar(["AAPL", "MSFT"], categories=["finance"])

    SeeAlso:
        - ``AsyncEdgarClient`` / ``batchCollectEdgar`` / ``batchCollectEdgarAll`` — 본 모듈.

    Requires:
        - asyncio
        - concurrent
        - dartlab
        - httpx
        - logging

    Capabilities:
        - EDGAR 배치 수집 — ticker list × 카테고리 ($workers=3) 분배 + parquet 저장.

    Guide:
        - 운영자 batch — 사용자 API 직접 호출 X.

    AIContext:
        internal batch — AI 직접 호출 X.

    LLM Specifications:
        AntiPatterns:
            - User-Agent 미설정 → 403.
            - 워커 > 3 (_MAX_WORKERS) → rate limit.
        OutputSchema:
            - dict / pl.DataFrame / Path — 함수별.
        Prerequisites:
            - 인터넷 + SEC EDGAR public API.
        Freshness:
            - SEC EDGAR 실시간.
        Dataflow:
            - ticker list → asyncio Queue → SEC API → parquet.
        TargetMarkets:
            - US (SEC EDGAR) 배치.
    """
    import time as _time

    from dartlab.core.messaging import emit

    cats = categories or ["finance", "docs"]
    numWorkers = min(maxWorkers or _MAX_WORKERS, _MAX_WORKERS)

    # ticker → cik/title 맵 사전 로드
    tickerMap = _resolveTickerMap(tickers)
    total = len(tickers)

    kindLabel = "+".join(cats)
    emit("edgar:bulk_start", kind=kindLabel, total=total)
    _bulkStart = _time.time()

    async def _run(completeFn, statusFn, periodFn) -> dict[str, dict[str, int]]:
        clients = [AsyncEdgarClient() for _ in range(numWorkers)]
        queue: asyncio.Queue = asyncio.Queue()
        for t in tickers:
            await queue.put(t.upper())

        results: dict[str, dict[str, int]] = {}

        try:
            workers = [
                asyncio.create_task(
                    _workerLoop(i, c, queue, cats, results, tickerMap, incremental, completeFn, statusFn, periodFn)
                )
                for i, c in enumerate(clients)
            ]
            await asyncio.gather(*workers)
        finally:
            for c in clients:
                await c.close()
            # ticker lock 정리 (메모리 누수 방지)
            _TICKER_LOCKS.clear()

        remaining = queue.qsize()
        if remaining > 0:
            from dartlab.core.messaging import emit

            emit("edgar:collect_exhausted")

        return results

    def _emitDone(res: dict[str, dict[str, int]]) -> None:
        success = sum(1 for v in res.values() if any(c > 0 for c in v.values()))
        failed = total - success
        elapsedSec = _time.time() - _bulkStart
        if failed > 0 and success > 0:
            emit(
                "edgar:bulk_partial",
                kind=kindLabel,
                done=success,
                total=total,
                errors=failed,
            )
        emit(
            "edgar:bulk_done",
            kind=kindLabel,
            success=success,
            failed=failed,
            elapsedSec=elapsedSec,
        )

    if not showProgress:
        try:
            res = _runAsync(_run(None, None, None))
            _emitDone(res)
            return res
        except KeyboardInterrupt:
            _log.info("\n[EDGAR 배치] 사용자 중단.")
            return {}

    # ── Rich Live progress ──
    from rich.live import Live
    from rich.table import Table

    workerLines = ["⏳ 대기 중..."] * numWorkers
    completedCount = [0]
    lock = threading.Lock()
    result: dict[str, dict[str, int]] = {}
    runError: list[BaseException] = []

    ", ".join(cats)

    def _buildDisplay() -> Table:
        return buildWorkerTable(numWorkers, workerLines, completedCount[0], total)

    def _completeFn(title: str, catSummary: str) -> None:
        with lock:
            completedCount[0] += 1
            for wIdx in range(numWorkers):
                if title in workerLines[wIdx] and "✓" not in workerLines[wIdx]:
                    summary = f" ({catSummary})" if catSummary else ""
                    workerLines[wIdx] = f"✓ {title}{summary}"
                    break

    def _statusFn(workerIdx: int, ticker: str, title: str) -> None:
        with lock:
            workerLines[workerIdx] = f"{title} ({ticker})"

    def _periodFn(workerIdx: int, title: str, detail: str) -> None:
        with lock:
            workerLines[workerIdx] = f"{title} | {detail}"

    def _threadTarget():
        try:
            nonlocal result
            result = asyncio.run(_run(_completeFn, _statusFn, _periodFn))
        except KeyboardInterrupt:
            pass
        except BaseException as exc:
            runError.append(exc)

    t = threading.Thread(target=_threadTarget, daemon=True)
    t.start()

    from dartlab.core.logger import getConsole

    try:
        with Live(_buildDisplay(), refresh_per_second=8, console=getConsole()) as live:
            while t.is_alive():
                with lock:
                    live.update(_buildDisplay())
                t.join(timeout=0.12)
            with lock:
                live.update(_buildDisplay())
    except KeyboardInterrupt:
        _log.info("\n[EDGAR 배치] 사용자 중단.")

    if runError and not isinstance(runError[0], KeyboardInterrupt):
        raise runError[0]

    _emitDone(result)
    return result


def batchCollectEdgarAll(
    *,
    tier: str = "all",
    categories: list[str] | None = None,
    mode: str = "all",
    maxWorkers: int | None = None,
    incremental: bool = True,
    showProgress: bool = True,
) -> dict[str, dict[str, int]]:
    """전체 상장 ticker 배치 수집.

    tier: "all" | "nasdaq" | "nyse" | "sp500"
    mode: "new" — 파일 없는 ticker 만 / "all" — 전체 증분

    Args:
        tier: 종목 universe 계층.
        categories: ``["finance", "docs"]`` 기본.
        mode: ``"new"`` 또는 ``"all"``.
        maxWorkers: 동시 워커 수.
        incremental: 기존 파일 skip 여부.
        showProgress: Rich live progress 표시.

    Returns:
        ``{"AAPL": {"finance": N, "docs": M}, ...}`` dict.

    Raises:
        없음.

    Example:
        >>> batchCollectEdgarAll(tier="sp500", mode="new")

    SeeAlso:
        - ``AsyncEdgarClient`` / ``batchCollectEdgar`` / ``batchCollectEdgarAll`` — 본 모듈.

    Requires:
        - asyncio
        - concurrent
        - dartlab
        - httpx
        - logging

    Capabilities:
        - EDGAR 배치 수집 — ticker list × 카테고리 ($workers=3) 분배 + parquet 저장.

    Guide:
        - 운영자 batch — 사용자 API 직접 호출 X.

    AIContext:
        internal batch — AI 직접 호출 X.

    LLM Specifications:
        AntiPatterns:
            - User-Agent 미설정 → 403.
            - 워커 > 3 (_MAX_WORKERS) → rate limit.
        OutputSchema:
            - dict / pl.DataFrame / Path — 함수별.
        Prerequisites:
            - 인터넷 + SEC EDGAR public API.
        Freshness:
            - SEC EDGAR 실시간.
        Dataflow:
            - ticker list → asyncio Queue → SEC API → parquet.
        TargetMarkets:
            - US (SEC EDGAR) 배치.
    """
    from dartlab.core.dataLoader import loadEdgarTargetUniverse

    universe = loadEdgarTargetUniverse(tier)
    allTickers = universe["ticker"].to_list()

    if mode == "new":
        cats = categories or ["finance", "docs"]
        newTickers = []
        for t in allTickers:
            missing = False
            if "finance" in cats:
                info = universe.filter(pl.col("ticker") == t)
                if info.height > 0:
                    cik = info["cik"][0]
                    if not _edgarDataPath("edgar", cik).exists():
                        missing = True
            if "docs" in cats:
                if not _edgarDataPath("edgarDocs", t).exists():
                    missing = True
            if missing:
                newTickers.append(t)
        targetTickers = newTickers
    else:
        targetTickers = allTickers

    from dartlab.core.messaging import emit

    if not targetTickers:
        emit("edgar:bulk_empty")
        return {}

    emit("edgar:bulk_target", count=len(targetTickers), tier=tier, mode=mode)
    return batchCollectEdgar(
        targetTickers,
        categories=categories,
        maxWorkers=maxWorkers,
        incremental=incremental,
        showProgress=showProgress,
    )
