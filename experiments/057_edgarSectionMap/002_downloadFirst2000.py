"""
실험 ID: 057-002
실험명: EDGAR docs 1차 2,000종목 배치 수집

목적:
- EDGAR section map 연구를 위한 1차 로컬 docs 모집단을 확보한다.
- listed universe 상장 종목 2,000개를 대상으로 2009년부터 10-K, 10-Q, 20-F를 수집한다.

가설:
1. 2,000개 배치 수집은 재시작 가능한 방식으로 장시간 실행해야 한다.
2. source-native docs parquet를 충분히 확보하면 title frequency와 item coverage 전수조사가 가능하다.

방법:
1. data/edgar/docsCandidates2000.parquet를 읽는다.
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
from pathlib import Path

from alive_progress import alive_bar

from dartlab import config
from dartlab.engines.edgar.docs.fetch import fetchEdgarDocs
from dartlab.engines.edgar.docs.sections.mapper import loadSectionMappings, normalizeSectionTitle


SINCE_YEAR = 2009
BATCH_SIZE = 25
COOLDOWN_SECONDS = 8.0


def _loadCompleted(progressPath: Path) -> set[str]:
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
            if ticker:
                completed.add(ticker)
    return completed


def _appendProgress(progressPath: Path, record: dict) -> None:
    progressPath.parent.mkdir(parents=True, exist_ok=True)
    with progressPath.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


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
    snapshot = {
        "docs_files": df["ticker"].n_unique(),
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
        f"candidate={snapshot['candidate_summary']} "
        f"raw={snapshot['raw_summary']}"
    )


def main() -> None:
    dataRoot = Path(config.dataDir)
    docsDir = dataRoot / "edgar" / "docs"
    docsDir.mkdir(parents=True, exist_ok=True)

    candidatePath = dataRoot / "edgar" / "docsCandidates2000.parquet"
    progressPath = Path(__file__).parent / "output" / "downloadFirst2000.progress.jsonl"

    import polars as pl
    import requests
    import time

    candidateDf = pl.read_parquet(candidatePath).sort("ticker")
    tickers = candidateDf["ticker"].to_list()
    completed = _loadCompleted(progressPath)

    print(f"[057] candidate tickers: {len(tickers)}")
    print(f"[057] completed records: {len(completed)}")

    with alive_bar(len(tickers), title="057 EDGAR 2000 수집") as bar:
        for idx, ticker in enumerate(tickers, start=1):
            outPath = docsDir / f"{ticker}.parquet"
            if ticker in completed or outPath.exists():
                if ticker not in completed:
                    _appendProgress(progressPath, {"ticker": ticker, "status": "exists"})
                bar()
                continue

            record = {"ticker": ticker, "status": "downloaded", "sinceYear": SINCE_YEAR}
            try:
                fetchEdgarDocs(ticker, outPath, sinceYear=SINCE_YEAR, showProgress=False)
            except (OSError, ValueError, requests.RequestException) as e:
                record["status"] = "failed"
                record["reason"] = str(e)

            _appendProgress(progressPath, record)
            bar()

            if idx < len(tickers) and idx % BATCH_SIZE == 0:
                _writeCoverageSnapshot()
                print(f"\n[057] {idx}건 처리 완료, {COOLDOWN_SECONDS:.1f}초 휴지")
                time.sleep(COOLDOWN_SECONDS)

    _writeCoverageSnapshot()


if __name__ == "__main__":
    main()
