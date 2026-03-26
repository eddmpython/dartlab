"""
실험 ID: 057-015
실험명: EDGAR docs downloader readiness 리포트

목적:
- 배치 수집 progress와 로컬 docs parquet 품질을 함께 요약한다.
- downloader가 DART급 parquet 품질에 근접했는지 운영 지표로 판단한다.

실험일: 2026-03-12
"""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from dartlab import config
from dartlab.providers.edgar.docs.fetch import summarizeEdgarDocsParquet


def _loadProgress(progressPath: Path) -> pl.DataFrame:
    if not progressPath.exists():
        return pl.DataFrame(
            schema={
                "ticker": pl.Utf8,
                "cik": pl.Utf8,
                "status": pl.Utf8,
                "failure_kind": pl.Utf8,
                "rows_saved": pl.Int64,
                "filings_saved": pl.Int64,
                "full_document_rows": pl.Int64,
                "table_rows": pl.Int64,
            }
        )

    rows: list[dict[str, object]] = []
    with progressPath.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    if not rows:
        return pl.DataFrame()
    return pl.DataFrame(rows)


def main() -> None:
    dataRoot = Path(config.dataDir)
    progressPath = Path(__file__).parent / "output" / "downloadFirst2000.progress.jsonl"
    outDir = Path(__file__).parent / "output"
    heartbeatPath = outDir / "downloadFirst2000.heartbeat.json"
    outDir.mkdir(parents=True, exist_ok=True)

    progressDf = _loadProgress(progressPath)
    docsDir = dataRoot / "edgar" / "docs"
    docsFiles = sorted(docsDir.glob("*.parquet"))
    docSummaries = [summarizeEdgarDocsParquet(path) for path in docsFiles]
    heartbeat = {}
    if heartbeatPath.exists():
        heartbeat = json.loads(heartbeatPath.read_text(encoding="utf-8"))

    if progressDf.is_empty():
        summary = {
            "docs_files": len(docsFiles),
            "message": "progress 기록 없음",
            "stage": heartbeat.get("stage"),
            "heartbeat_updated_at": heartbeat.get("updated_at"),
            "current_ticker": heartbeat.get("current_ticker"),
        }
    else:
        downloaded = progressDf.filter(pl.col("status") == "downloaded")
        failed = progressDf.filter(pl.col("status") == "failed")
        exists = progressDf.filter(pl.col("status") == "exists")

        failureSummary = []
        if not failed.is_empty() and "failure_kind" in failed.columns:
            failureSummary = (
                failed.group_by("failure_kind")
                .agg(pl.len().alias("count"))
                .sort("count", descending=True)
                .to_dicts()
            )

        formSummary = []
        if docSummaries:
            docSummaryDf = pl.DataFrame(docSummaries)
            exploded = (
                docSummaryDf
                .select(["ticker", "form_metrics"])
                .explode("form_metrics")
                .drop_nulls("form_metrics")
                .unnest("form_metrics")
            )
            formSummary = (
                exploded.group_by("form_type")
                .agg(
                    pl.col("ticker").n_unique().alias("tickers"),
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
        elif not downloaded.is_empty() and "form_metrics" in downloaded.columns:
            exploded = (
                downloaded
                .select(["ticker", "form_metrics"])
                .explode("form_metrics")
                .drop_nulls("form_metrics")
                .unnest("form_metrics")
            )
            if not exploded.is_empty():
                formSummary = (
                    exploded.group_by("form_type")
                    .agg(
                        pl.col("ticker").n_unique().alias("tickers"),
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

        summary = {
            "docs_files": len(docsFiles),
            "downloaded": downloaded.height,
            "failed": failed.height,
            "exists": exists.height,
            "rows_saved_total": sum(int(row["rows_saved"]) for row in docSummaries),
            "filings_saved_total": sum(int(row["filings_saved"]) for row in docSummaries),
            "failure_summary": failureSummary,
            "form_summary": formSummary,
            "stage": heartbeat.get("stage"),
            "heartbeat_updated_at": heartbeat.get("updated_at"),
            "current_ticker": heartbeat.get("current_ticker"),
        }

    outJson = outDir / "downloaderReadiness.latest.json"
    outTxt = outDir / "downloaderReadiness.latest.txt"
    outJson.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "=" * 72,
        "057-015 downloader readiness",
        "=" * 72,
        f"docs_files={summary.get('docs_files')}",
        f"stage={summary.get('stage')} heartbeat_updated_at={summary.get('heartbeat_updated_at')} current_ticker={summary.get('current_ticker')}",
        f"downloaded={summary.get('downloaded', 0)} failed={summary.get('failed', 0)} exists={summary.get('exists', 0)}",
        f"rows_saved_total={summary.get('rows_saved_total', 0)} filings_saved_total={summary.get('filings_saved_total', 0)}",
        "",
        "[failure summary]",
        *[str(row) for row in summary.get("failure_summary", [])],
        "",
        "[form summary]",
        *[str(row) for row in summary.get("form_summary", [])],
    ]
    outTxt.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
