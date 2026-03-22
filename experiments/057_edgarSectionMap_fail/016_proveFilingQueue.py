"""
실험 ID: 057-016
실험명: EDGAR docs filing queue 파이프라인 증명

목적:
- ticker 단위 장시간 수집 대신 filing 단위 queue가 실제로 더 안정적으로 전진하는지 증명한다.
- 빈 data/edgar/docs 에서 대표 종목들을 filing 하나씩 처리해 종목별 parquet를 다시 쌓는다.

방법:
1. 대표 종목들의 2009년 이후 정기 filing 목록을 가져온다.
2. ticker별 filing을 round-robin으로 interleave 해 queue를 만든다.
3. filing 하나씩 timeout을 두고 처리한다.
4. 성공한 filing row는 해당 ticker parquet에 바로 append 저장한다.
5. 실패 filing은 기록만 남기고 다음 filing으로 넘어간다.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import polars as pl
from alive_progress import alive_bar

from dartlab import config
from dartlab.engines.company.edgar.docs.fetch import (
    _downloadFilingSource,
    _FilingTimeout,
    _findFilings,
    _getSubmissions,
    _htmlToText,
    _periodKey,
    _reportType,
    _resolveTickerMeta,
    _split40FSections,
    _splitItems,
)

SINCE_YEAR = 2009
FILING_TIMEOUT_SECONDS = 45
REPRESENTATIVE_TICKERS = [
    "AAPL",
    "MSFT",
    "AMZN",
    "JPM",
    "XOM",
    "TSM",
    "AG",
    "D",
    "O",
    "WMT",
]


def _append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _load_existing_accessions(path: Path) -> set[str]:
    if not path.exists():
        return set()
    df = pl.read_parquet(path, columns=["accession_no"])
    return {str(value) for value in df["accession_no"].drop_nulls().to_list()}


def _append_rows(path: Path, rows: list[dict]) -> None:
    new_df = pl.DataFrame(rows)
    if path.exists():
        current_df = pl.read_parquet(path)
        merged = pl.concat([current_df, new_df], how="vertical_relaxed")
        merged = merged.unique(subset=["accession_no", "section_order", "section_title"], keep="first")
    else:
        merged = new_df
    path.parent.mkdir(parents=True, exist_ok=True)
    merged.write_parquet(path)


def _collect_filing_rows(ticker: str, meta: dict[str, str], filing: dict) -> list[dict]:
    with _FilingTimeout(FILING_TIMEOUT_SECONDS):
        html = _downloadFilingSource(filing)
        text = _htmlToText(html)
        if filing["formType"] == "40-F":
            items = _split40FSections(filing, text)
        else:
            items = _splitItems(text, filing["formType"])

    rows: list[dict] = []
    report_type = _reportType(filing["formType"], filing.get("periodEnd"))
    period_key = _periodKey(filing["formType"], filing.get("periodEnd"), filing["year"])
    for order, item in enumerate(items):
        rows.append({
            "cik": meta["cik"],
            "company_name": meta["title"],
            "ticker": ticker,
            "year": filing["year"],
            "filing_date": filing["filingDate"],
            "period_end": filing.get("periodEnd"),
            "accession_no": filing["accessionNumber"],
            "form_type": filing["formType"],
            "report_type": report_type,
            "period_key": period_key,
            "section_order": order,
            "section_title": item["title"],
            "filing_url": filing["filingUrl"],
            "section_content": item["content"],
        })
    return rows


def _build_queue() -> list[dict]:
    ticker_filings: dict[str, list[dict]] = {}
    metas: dict[str, dict[str, str]] = {}
    max_len = 0
    for ticker in REPRESENTATIVE_TICKERS:
        meta = _resolveTickerMeta(ticker)
        filings = _findFilings(_getSubmissions(meta["cik"]), SINCE_YEAR)
        metas[ticker] = meta
        ticker_filings[ticker] = filings
        max_len = max(max_len, len(filings))

    queue: list[dict] = []
    for idx in range(max_len):
        for ticker in REPRESENTATIVE_TICKERS:
            filings = ticker_filings[ticker]
            if idx >= len(filings):
                continue
            queue.append({
                "ticker": ticker,
                "meta": metas[ticker],
                "filing": filings[idx],
            })
    return queue


def main() -> None:
    data_root = Path(config.dataDir)
    docs_dir = data_root / "edgar" / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    progress_path = Path(__file__).parent / "output" / "proveFilingQueue.progress.jsonl"
    progress_path.parent.mkdir(parents=True, exist_ok=True)

    queue = _build_queue()
    print(f"[057-016] filing queue size={len(queue)} tickers={len(REPRESENTATIVE_TICKERS)}")

    with alive_bar(len(queue), title="057 filing queue proof") as bar:
        for item in queue:
            ticker = item["ticker"]
            meta = item["meta"]
            filing = item["filing"]
            out_path = docs_dir / f"{ticker}.parquet"
            accession = str(filing["accessionNumber"])

            if accession in _load_existing_accessions(out_path):
                _append_jsonl(progress_path, {
                    "ticker": ticker,
                    "accession_no": accession,
                    "filing_date": filing["filingDate"],
                    "form_type": filing["formType"],
                    "status": "exists",
                })
                bar()
                continue

            try:
                rows = _collect_filing_rows(ticker, meta, filing)
                if not rows:
                    raise ValueError("empty rows")
                _append_rows(out_path, rows)
                _append_jsonl(progress_path, {
                    "ticker": ticker,
                    "accession_no": accession,
                    "filing_date": filing["filingDate"],
                    "form_type": filing["formType"],
                    "status": "downloaded",
                    "rows_saved": len(rows),
                    "path": str(out_path),
                })
            except Exception as exc:
                _append_jsonl(progress_path, {
                    "ticker": ticker,
                    "accession_no": accession,
                    "filing_date": filing["filingDate"],
                    "form_type": filing["formType"],
                    "status": "failed",
                    "reason": str(exc),
                })
            bar()


if __name__ == "__main__":
    main()
