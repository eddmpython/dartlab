"""
실험 ID: 057-018
실험명: 우선순위 ticker 종목별 docs 수집

목적:
- bulk 스캔 대신 대표 종목/S&P/Nasdaq 대형주를 종목별로 바로 수집한다.
- 각 ticker는 2009년부터 정기공시를 받아 하나의 parquet로 저장한다.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

from alive_progress import alive_bar

from dartlab import config
from dartlab.providers.edgar.docs.fetch import fetchEdgarDocs, summarizeEdgarDocsParquet

TARGET_TICKERS = [
    "AAPL",
    "MSFT",
    "AMZN",
    "GOOGL",
    "META",
    "NVDA",
    "JPM",
    "XOM",
    "WMT",
    "TSM",
    "AG",
    "O",
    "NFLX",
    "COST",
    "AVGO",
    "AMD",
    "JNJ",
    "KO",
    "MA",
    "MRK",
    "BAC",
    "BRK-B",
    "V",
    "HD",
    "MCD",
    "DIS",
    "UNH",
    "CVX",
    "ABBV",
    "PFE",
]
SINCE_YEAR = 2009
TICKER_TIMEOUT_SECONDS = 600


def _append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _load_completed(progress_path: Path, docs_dir: Path) -> set[str]:
    completed: set[str] = set()
    if not progress_path.exists():
        return completed

    with progress_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            ticker = str(record.get("ticker") or "").upper()
            status = str(record.get("status") or "")
            out_path = docs_dir / f"{ticker}.parquet"
            if ticker and status == "downloaded" and out_path.exists():
                completed.add(ticker)
    return completed


def _load_failed(progress_path: Path) -> set[str]:
    failed: set[str] = set()
    if not progress_path.exists():
        return failed

    with progress_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            ticker = str(record.get("ticker") or "").upper()
            status = str(record.get("status") or "")
            if ticker and status == "failed":
                failed.add(ticker)
    return failed


def _collect_single_ticker(ticker: str) -> None:
    docs_dir = Path(config.dataDir) / "edgar" / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    out_path = docs_dir / f"{ticker}.parquet"
    fetchEdgarDocs(
        ticker,
        out_path,
        sinceYear=SINCE_YEAR,
        showProgress=False,
    )


def _run_collection() -> None:
    docs_dir = Path(config.dataDir) / "edgar" / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    progress_path = Path(__file__).parent / "output" / "priorityTickerCollection.progress.jsonl"

    completed = _load_completed(progress_path, docs_dir)
    failed = _load_failed(progress_path)
    targets = [ticker for ticker in TARGET_TICKERS if ticker not in completed]
    targets = sorted(targets, key=lambda ticker: (ticker in failed, TARGET_TICKERS.index(ticker)))
    print(f"[057-018] targets={len(targets)}")

    with alive_bar(len(targets), title="057 priority ticker collect") as bar:
        for ticker in targets:
            out_path = docs_dir / f"{ticker}.parquet"
            try:
                started_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                print(f"[057-018] start {ticker}")
                subprocess.run(
                    [sys.executable, str(Path(__file__).resolve()), "--ticker", ticker],
                    check=True,
                    timeout=TICKER_TIMEOUT_SECONDS,
                )
                record = {"ticker": ticker, "status": "downloaded", "sinceYear": SINCE_YEAR}
                record.update(summarizeEdgarDocsParquet(out_path))
                record["started_at"] = started_at
                record["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                print(f"[057-018] done {ticker}")
            except Exception as exc:
                record = {
                    "ticker": ticker,
                    "status": "failed",
                    "sinceYear": SINCE_YEAR,
                    "reason": str(exc),
                    "finished_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }
                print(f"[057-018] fail {ticker}: {exc}")
            _append_jsonl(progress_path, record)
            bar()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker")
    args = parser.parse_args()

    if args.ticker:
        _collect_single_ticker(str(args.ticker).upper())
        return

    _run_collection()


if __name__ == "__main__":
    main()
