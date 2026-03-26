"""
실험 ID: 057-002
실험명: EDGAR docs 1차 2,000종목 배치 수집

목적:
- EDGAR section map 연구를 위한 1차 로컬 docs 모집단을 확보한다.
- issuer-deduped collectible universe 2,000개를 대상으로 2009년부터 10-K, 10-Q, 20-F, 40-F를 수집한다.

가설:
1. 2,000개 배치 수집은 재시작 가능한 방식으로 장시간 실행해야 한다.
2. source-native docs parquet를 충분히 확보하면 title frequency와 item coverage 전수조사가 가능하다.

방법:
1. issuer-deduped collectible universe를 구성한다.
2. ticker별로 data/edgar/docs/{ticker}.parquet 존재 여부를 확인한다.
3. 없으면 fetchEdgarDocs(ticker, sinceYear=2009)를 호출한다.
4. 결과를 output/downloadFirst2000.progress.jsonl에 누적 기록한다.

결과 (실험 후 작성):
- 실행 중

결론:
- 실행 후 갱신

실험일: 2026-03-12
"""

from __future__ import annotations

import json
import os
import signal
import time
from pathlib import Path
from uuid import uuid4

from alive_progress import alive_bar

from dartlab import config
from dartlab.providers.edgar.docs.fetch import (
    fetchEdgarDocs,
    prepareEdgarCollectibleUniverse,
    summarizeEdgarDocsParquet,
)
from dartlab.providers.edgar.docs.sections.mapper import loadSectionMappings, normalizeSectionTitle

SINCE_YEAR = 2009
BATCH_SIZE = 25
COOLDOWN_SECONDS = 8.0
STALL_SECONDS = 120.0
TICKER_TIMEOUT_SECONDS = 180
PRIORITY_TICKERS = (
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "NFLX", "COST",
    "AVGO", "AMD", "ADBE", "CSCO", "INTC", "QCOM", "AMGN", "TXN", "INTU",
    "CMCSA", "PEP", "SBUX", "BKNG", "AMAT", "ADP", "GILD", "VRTX", "ISRG",
    "PANW", "SNPS", "CDNS", "CRWD", "SHOP", "UBER", "MU", "LRCX", "ADI",
    "PYPL", "ABNB", "MAR", "MELI",
    "JPM", "BAC", "WFC", "GS", "MS", "BRK-B", "V", "MA", "AXP",
    "XOM", "CVX", "COP", "SLB",
    "UNH", "JNJ", "LLY", "MRK", "ABBV", "PFE",
    "WMT", "HD", "LOW", "KO", "PG", "MCD", "DIS", "NKE",
)


def _loadCompleted(progressPath: Path, docsDir: Path) -> set[str]:
    if not progressPath.exists():
        return set()

    completed: set[str] = set()
    with progressPath.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            ticker = str(record.get("ticker") or "").upper()
            status = str(record.get("status") or "")
            pathText = str(record.get("path") or "")
            outPath = Path(pathText) if pathText else docsDir / f"{ticker}.parquet"
            if ticker and (outPath.exists() or status == "failed"):
                completed.add(ticker)
    return completed


def _appendProgress(progressPath: Path, record: dict) -> None:
    progressPath.parent.mkdir(parents=True, exist_ok=True)
    with progressPath.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _writeJson(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _archiveFile(path: Path, *, suffix: str) -> None:
    if not path.exists():
        return
    archived = path.with_name(f"{path.stem}.{suffix}{path.suffix}")
    path.rename(archived)


def _prepareBatchState(
    *,
    docsDir: Path,
    progressPath: Path,
    heartbeatPath: Path,
    monitorPath: Path,
) -> str:
    runId = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()) + f"-{uuid4().hex[:8]}"
    if not any(docsDir.glob("*.parquet")):
        _archiveFile(progressPath, suffix=f"stale-{runId}")
        _archiveFile(heartbeatPath, suffix=f"stale-{runId}")
        _archiveFile(monitorPath, suffix=f"stale-{runId}")
    return runId


def _prioritizeTickers(candidateDf):
    import polars as pl

    if candidateDf.is_empty():
        return candidateDf

    prioritySet = {ticker.upper() for ticker in PRIORITY_TICKERS}
    prioritized = candidateDf.with_columns(
        pl.col("ticker").cast(pl.Utf8).str.to_uppercase().is_in(prioritySet).alias("_is_priority")
    ).sort(["_is_priority", "candidate_order"], descending=[True, False])
    prioritized = prioritized.drop("_is_priority").with_row_index("candidate_order", offset=1)
    return prioritized


def _isPidAlive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _acquireLock(lockPath: Path) -> None:
    if lockPath.exists():
        try:
            payload = json.loads(lockPath.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = {}
        pid = int(payload.get("pid", 0) or 0)
        if _isPidAlive(pid):
            raise RuntimeError(f"057 batch already running (pid={pid})")
    _writeJson(lockPath, {"pid": os.getpid(), "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})


def _releaseLock(lockPath: Path) -> None:
    if lockPath.exists():
        lockPath.unlink()


def _updateHeartbeat(
    heartbeatPath: Path,
    *,
    runId: str,
    stage: str,
    currentTicker: str | None = None,
    currentCik: str | None = None,
    candidatesReady: int = 0,
    universeChecked: int = 0,
    docsDownloaded: int = 0,
    docsFailed: int = 0,
) -> None:
    _writeJson(heartbeatPath, {
        "run_id": runId,
        "pid": os.getpid(),
        "stage": stage,
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "current_ticker": currentTicker,
        "current_cik": currentCik,
        "candidates_ready": candidatesReady,
        "universe_checked": universeChecked,
        "docs_downloaded": docsDownloaded,
        "docs_failed": docsFailed,
    })


def _loadProgressFrame(progressPath: Path):
    import polars as pl

    if not progressPath.exists():
        return pl.DataFrame(schema={"ticker": pl.Utf8, "status": pl.Utf8, "failure_kind": pl.Utf8})

    rows: list[dict] = []
    with progressPath.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    if not rows:
        return pl.DataFrame(schema={"ticker": pl.Utf8, "status": pl.Utf8, "failure_kind": pl.Utf8})
    return pl.DataFrame(rows)


def _writeDownloadMonitor(
    *,
    runId: str,
    dataRoot: Path,
    progressPath: Path,
    heartbeatPath: Path,
    monitorPath: Path,
) -> None:
    import polars as pl

    progressDf = _loadProgressFrame(progressPath)
    docsDir = dataRoot / "edgar" / "docs"
    docsFiles = sorted(docsDir.glob("*.parquet"))

    heartbeat = {}
    if heartbeatPath.exists():
        heartbeat = json.loads(heartbeatPath.read_text(encoding="utf-8"))

    downloaded = int(progressDf.filter(pl.col("status") == "downloaded").height) if not progressDf.is_empty() else 0
    failed = int(progressDf.filter(pl.col("status") == "failed").height) if not progressDf.is_empty() else 0
    progressRecords = int(progressDf.height)
    formSummary: list[dict] = []
    if docsFiles:
        summaries = [summarizeEdgarDocsParquet(path) for path in docsFiles]
        metrics = []
        for row in summaries:
            metrics.extend(row.get("form_metrics", []))
        if metrics:
            metricDf = pl.DataFrame(metrics)
            formSummary = (
                metricDf.group_by("form_type")
                .agg(
                    pl.col("filings_saved").sum().alias("filings_saved"),
                    pl.col("rows_saved").sum().alias("rows_saved"),
                    pl.col("full_document_rows").sum().alias("full_document_rows"),
                    pl.col("table_rows").sum().alias("table_rows"),
                )
                .with_columns(
                    (pl.col("full_document_rows") / pl.col("filings_saved")).alias("full_document_ratio"),
                    (pl.col("table_rows") / pl.col("rows_saved")).alias("table_ratio"),
                )
                .sort("form_type")
                .to_dicts()
            )

    lastProgressAt = None
    if progressPath.exists():
        lastProgressAt = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(progressPath.stat().st_mtime))
    updatedAt = heartbeat.get("updated_at")
    isStalled = False
    if heartbeatPath.exists():
        age = time.time() - heartbeatPath.stat().st_mtime
        isStalled = age > STALL_SECONDS

    _writeJson(monitorPath, {
        "run_id": runId,
        "stage": heartbeat.get("stage"),
        "docs_files": len(docsFiles),
        "progress_records": progressRecords,
        "downloaded_count": downloaded,
        "failed_count": failed,
        "form_summary": formSummary,
        "last_progress_at": lastProgressAt,
        "heartbeat_updated_at": updatedAt,
        "is_stalled": isStalled,
    })


def _classifyFailure(reason: str, exc: Exception) -> str:
    if isinstance(exc, TimeoutError):
        return "fetch_timeout"
    if "TLS CA certificate bundle" in reason:
        return "legacy_env_error"
    if "filing 없음" in reason:
        return "no_supported_regular_filing"
    if "section 추출 실패" in reason:
        return "parse_error"
    if exc.__class__.__name__.endswith("RequestException"):
        return "fetch_error"
    if isinstance(exc, OSError):
        return "storage_error"
    if isinstance(exc, ValueError):
        return "parse_error"
    return "fetch_error"


class _TickerTimeout:
    def __init__(self, seconds: int):
        self.seconds = seconds
        self._previousHandler = None

    def __enter__(self):
        if self.seconds <= 0:
            return self
        self._previousHandler = signal.getsignal(signal.SIGALRM)
        signal.signal(signal.SIGALRM, self._handle)
        signal.alarm(self.seconds)
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.seconds > 0:
            signal.alarm(0)
            if self._previousHandler is not None:
                signal.signal(signal.SIGALRM, self._previousHandler)
        return False

    @staticmethod
    def _handle(signum, frame):
        raise TimeoutError("ticker fetch timed out")


def _writeCoverageSnapshot() -> None:
    import polars as pl

    docsDir = Path(config.dataDir) / "edgar" / "docs"
    frames: list[pl.DataFrame] = []
    for filePath in sorted(docsDir.glob("*.parquet")):
        frames.append(
            pl.read_parquet(
                filePath,
                columns=["accession_no", "form_type", "section_title"],
            ).with_columns(pl.lit(filePath.stem).alias("ticker"))
        )
    if not frames:
        return

    df = pl.concat(frames, how="vertical")
    mappings = loadSectionMappings()
    mappingKeys = list(mappings.keys())

    rawDf = df.with_columns(
        pl.Series(
            "normalized_title",
            [normalizeSectionTitle(str(title)) for title in df["section_title"].to_list()],
        )
    )
    rawCoverage = (
        rawDf.group_by(["form_type", "section_title", "normalized_title"])
        .agg(
            pl.len().alias("rows"),
            pl.col("ticker").n_unique().alias("tickers"),
            pl.col("accession_no").n_unique().alias("filings"),
        )
        .with_columns(pl.col("normalized_title").is_in(mappingKeys).alias("mapped"))
        .sort(["form_type", "rows"], descending=[False, True])
    )

    filingDf = df.unique(subset=["accession_no", "form_type", "section_title", "ticker"])
    filingDf = filingDf.with_columns(
        pl.Series(
            "normalized_title",
            [normalizeSectionTitle(str(title)) for title in filingDf["section_title"].to_list()],
        )
    )
    formTotals = filingDf.group_by("form_type").agg(pl.col("accession_no").n_unique().alias("total_filings"))
    candidateDf = (
        filingDf.group_by(["form_type", "section_title", "normalized_title"])
        .agg(
            pl.col("accession_no").n_unique().alias("filings"),
            pl.col("ticker").n_unique().alias("tickers"),
        )
        .join(formTotals, on="form_type", how="left")
        .with_columns(
            (pl.col("filings") / pl.col("total_filings")).alias("filing_coverage"),
            pl.col("normalized_title").is_in(mappingKeys).alias("mapped"),
        )
        .filter(pl.col("filing_coverage") >= 0.5)
        .sort(["form_type", "filings"], descending=[False, True])
    )

    candidateSummary = (
        candidateDf.group_by("form_type")
        .agg(
            pl.len().alias("candidates"),
            pl.col("mapped").sum().alias("mapped_candidates"),
        )
        .with_columns((pl.col("mapped_candidates") / pl.col("candidates")).alias("coverage"))
        .sort("form_type")
        .to_dicts()
    )
    rawSummary = (
        rawCoverage.group_by("form_type")
        .agg(
            pl.len().alias("raw_titles"),
            pl.col("mapped").sum().alias("mapped_titles"),
        )
        .with_columns((pl.col("mapped_titles") / pl.col("raw_titles")).alias("coverage"))
        .sort("form_type")
        .to_dicts()
    )
    unmappedTop = rawCoverage.filter(~pl.col("mapped")).select(["form_type", "section_title", "rows", "filings"]).head(20).to_dicts()
    formQuality = (
        df.group_by("form_type")
        .agg(
            pl.len().alias("rows_saved"),
            pl.col("accession_no").n_unique().alias("filings_saved"),
            pl.col("ticker").n_unique().alias("tickers"),
            pl.col("section_title").eq("Full Document").sum().alias("full_document_rows"),
            pl.col("section_content").cast(pl.Utf8).str.contains(r"\|").sum().alias("table_rows"),
        )
        .with_columns(
            (pl.col("full_document_rows") / pl.col("filings_saved")).alias("full_document_ratio"),
            (pl.col("table_rows") / pl.col("rows_saved")).alias("table_ratio"),
        )
        .sort("form_type")
        .to_dicts()
    )

    snapshot = {
        "docs_files": df["ticker"].n_unique(),
        "rows_saved": df.height,
        "filings_saved": df["accession_no"].n_unique(),
        "form_quality": formQuality,
        "candidate_summary": candidateSummary,
        "raw_summary": rawSummary,
        "unmapped_top": unmappedTop,
    }

    outDir = Path(__file__).parent / "output"
    outDir.mkdir(parents=True, exist_ok=True)
    (outDir / "mappingCoverage.latest.json").write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "=" * 72,
        "057-012 mapping coverage snapshot",
        "=" * 72,
        f"docs files={snapshot['docs_files']}",
        f"rows saved={snapshot['rows_saved']}",
        f"filings saved={snapshot['filings_saved']}",
        "",
        "[form quality]",
        *[str(row) for row in snapshot["form_quality"]],
        "",
        "[candidate coverage]",
        *[str(row) for row in snapshot["candidate_summary"]],
        "",
        "[raw coverage]",
        *[str(row) for row in snapshot["raw_summary"]],
        "",
        "[unmapped top]",
        *[str(row) for row in snapshot["unmapped_top"]],
    ]
    (outDir / "mappingCoverage.latest.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        "[057] coverage snapshot "
        f"docs={snapshot['docs_files']} "
        f"forms={snapshot['form_quality']} "
        f"candidate={snapshot['candidate_summary']} "
        f"raw={snapshot['raw_summary']}"
    )


def main() -> None:
    dataRoot = Path(config.dataDir)
    docsDir = dataRoot / "edgar" / "docs"
    docsDir.mkdir(parents=True, exist_ok=True)

    progressPath = Path(__file__).parent / "output" / "downloadFirst2000.progress.jsonl"
    import polars as pl
    import requests
    outputDir = Path(__file__).parent / "output"
    candidatePath = dataRoot / "edgar" / "docsCandidates2000.parquet"
    universeProgressPath = outputDir / "collectibleUniverse.progress.jsonl"
    heartbeatPath = outputDir / "downloadFirst2000.heartbeat.json"
    monitorPath = outputDir / "downloadMonitor.latest.json"
    lockPath = outputDir / "downloadFirst2000.lock"

    _acquireLock(lockPath)
    try:
        runId = _prepareBatchState(
            docsDir=docsDir,
            progressPath=progressPath,
            heartbeatPath=heartbeatPath,
            monitorPath=monitorPath,
        )
        _updateHeartbeat(
            heartbeatPath,
            runId=runId,
            stage="prepare_universe",
            candidatesReady=0,
            universeChecked=0,
            docsDownloaded=0,
            docsFailed=0,
        )
        candidateDf = prepareEdgarCollectibleUniverse(
            limit=2000,
            sinceYear=SINCE_YEAR,
            progressPath=universeProgressPath,
            heartbeat=lambda **kwargs: _updateHeartbeat(
                heartbeatPath,
                runId=runId,
                stage="prepare_universe",
                currentTicker=kwargs.get("currentTicker"),
                currentCik=kwargs.get("currentCik"),
                candidatesReady=int(kwargs.get("candidatesReady", 0)),
                universeChecked=int(kwargs.get("universeChecked", 0)),
                docsDownloaded=0,
                docsFailed=0,
            ),
        )
        if candidateDf.is_empty():
            raise RuntimeError("collectible universe 비어 있음")

        candidateDf = _prioritizeTickers(candidateDf)
        candidatePath.parent.mkdir(parents=True, exist_ok=True)
        candidateDf.write_parquet(candidatePath)
        _writeDownloadMonitor(
            dataRoot=dataRoot,
            runId=runId,
            progressPath=progressPath,
            heartbeatPath=heartbeatPath,
            monitorPath=monitorPath,
        )

        tickers = candidateDf["ticker"].to_list()
        candidateRows = {row["ticker"]: row for row in candidateDf.to_dicts()}
        completed = _loadCompleted(progressPath, docsDir)

        print(f"[057] candidate tickers: {len(tickers)}")
        print(f"[057] completed records: {len(completed)}")

        downloadedCount = 0
        failedCount = 0
        with alive_bar(len(tickers), title="057 EDGAR 2000 수집") as bar:
            for idx, ticker in enumerate(tickers, start=1):
                outPath = docsDir / f"{ticker}.parquet"
                candidateRow = candidateRows.get(ticker, {})
                _updateHeartbeat(
                    heartbeatPath,
                    runId=runId,
                    stage="download_docs",
                    currentTicker=ticker,
                    currentCik=str(candidateRow.get("cik") or ""),
                    candidatesReady=len(tickers),
                    universeChecked=candidateRow.get("candidate_order", idx),
                    docsDownloaded=downloadedCount,
                    docsFailed=failedCount,
                )

                if ticker in completed or outPath.exists():
                    if ticker not in completed:
                        _appendProgress(progressPath, {
                            "run_id": runId,
                            "candidate_order": candidateRow.get("candidate_order"),
                            "ticker": ticker,
                            "cik": candidateRow.get("cik"),
                            "exchange": candidateRow.get("exchange"),
                            "status": "exists",
                        })
                    bar()
                    continue

                record = {
                    "run_id": runId,
                    "candidate_order": candidateRow.get("candidate_order"),
                    "ticker": ticker,
                    "cik": candidateRow.get("cik"),
                    "exchange": candidateRow.get("exchange"),
                    "supported_regular_forms": candidateRow.get("supported_regular_forms"),
                    "status": "downloaded",
                    "sinceYear": SINCE_YEAR,
                }
                try:
                    with _TickerTimeout(TICKER_TIMEOUT_SECONDS):
                        fetchEdgarDocs(ticker, outPath, sinceYear=SINCE_YEAR, showProgress=False)
                    if not outPath.exists() or outPath.stat().st_size == 0:
                        raise OSError(f"저장 실패: parquet 미생성 ({outPath})")
                    record.update(summarizeEdgarDocsParquet(outPath))
                    downloadedCount += 1
                except (OSError, ValueError, requests.RequestException, TimeoutError) as e:
                    record["status"] = "failed"
                    record["reason"] = str(e)
                    record["failure_kind"] = _classifyFailure(str(e), e)
                    failedCount += 1

                _appendProgress(progressPath, record)
                _writeDownloadMonitor(
                    dataRoot=dataRoot,
                    runId=runId,
                    progressPath=progressPath,
                    heartbeatPath=heartbeatPath,
                    monitorPath=monitorPath,
                )
                bar()

                if idx < len(tickers) and idx % BATCH_SIZE == 0:
                    _writeCoverageSnapshot()
                    _updateHeartbeat(
                        heartbeatPath,
                        runId=runId,
                        stage="cooldown",
                        currentTicker=ticker,
                        currentCik=str(candidateRow.get("cik") or ""),
                        candidatesReady=len(tickers),
                        universeChecked=candidateRow.get("candidate_order", idx),
                        docsDownloaded=downloadedCount,
                        docsFailed=failedCount,
                    )
                    print(f"\n[057] {idx}건 처리 완료, {COOLDOWN_SECONDS:.1f}초 휴지")
                    time.sleep(COOLDOWN_SECONDS)

        _writeCoverageSnapshot()
        _writeDownloadMonitor(
            dataRoot=dataRoot,
            runId=runId,
            progressPath=progressPath,
            heartbeatPath=heartbeatPath,
            monitorPath=monitorPath,
        )
    finally:
        _releaseLock(lockPath)


if __name__ == "__main__":
    main()
