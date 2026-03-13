"""
실험 ID: 057-002
실험명: EDGAR docs 수집 파이프라인

목적:
- EDGAR docs parquet를 ticker별로 수집한다.
- priority 대형주 → exchange listed 순으로 확장한다.
- Windows/Linux 모두에서 동작해야 한다.

가설:
1. subprocess + timeout으로 ticker별 격리하면 하나가 죽어도 전체가 안 멈춘다.
2. 재시작 가능한 progress 기록으로 중단 후 이어서 수집 가능하다.

방법:
1. listedUniverse.parquet에서 exchange listed ticker를 뽑는다.
2. priority ticker를 앞에 배치한다.
3. ticker별로 subprocess를 띄워 fetchEdgarDocs를 호출한다.
4. 성공/실패를 progress.jsonl에 기록한다.
5. 이미 수집된 ticker는 건너뛴다.

사용법:
    python experiments/057_edgarSectionMap/002_collectDocs.py
    python experiments/057_edgarSectionMap/002_collectDocs.py --limit 100
    python experiments/057_edgarSectionMap/002_collectDocs.py --ticker AAPL

결과 (실험 후 작성):

결론:

실험일: 2026-03-13
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import polars as pl

from dartlab import config

SINCE_YEAR = 2009
TICKER_TIMEOUT_SECONDS = 300
COOLDOWN_SECONDS = 1.0

PRIORITY_TICKERS = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "NFLX",
    "JPM", "BAC", "GS", "WFC",
    "XOM", "CVX",
    "UNH", "JNJ", "LLY", "MRK", "PFE", "ABBV",
    "WMT", "HD", "KO", "MCD", "DIS", "NKE",
    "V", "MA", "BRK-B", "COST",
]


def _progressPath() -> Path:
    return Path(__file__).parent / "output" / "collectDocs.progress.jsonl"


def _docsDir() -> Path:
    d = Path(config.dataDir) / "edgar" / "docs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _appendProgress(record: dict) -> None:
    path = _progressPath()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _loadCompleted() -> set[str]:
    path = _progressPath()
    if not path.exists():
        return set()
    completed: set[str] = set()
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            ticker = str(rec.get("ticker", "")).upper()
            status = str(rec.get("status", ""))
            if ticker and status in ("downloaded", "no_data"):
                completed.add(ticker)
    return completed


def _buildTickerList(limit: int | None = None) -> list[str]:
    universePath = Path(config.dataDir) / "edgar" / "listedUniverse.parquet"
    df = pl.read_parquet(universePath)
    exchangeDf = df.filter(pl.col("is_exchange_listed"))

    allTickers = exchangeDf["ticker"].drop_nulls().unique().sort().to_list()

    prioritySet = set(PRIORITY_TICKERS)
    rest = [t for t in allTickers if t not in prioritySet]
    ordered = list(PRIORITY_TICKERS) + rest

    if limit:
        ordered = ordered[:limit]
    return ordered


def _collectSingleTicker(ticker: str) -> None:
    from dartlab.engines.edgar.docs.fetch import fetchEdgarDocs

    docsDir = _docsDir()
    outPath = docsDir / f"{ticker}.parquet"
    fetchEdgarDocs(ticker, outPath, sinceYear=SINCE_YEAR, showProgress=False)


def _summarize(parquetPath: Path) -> dict:
    df = pl.read_parquet(parquetPath)
    forms = sorted(df["form_type"].drop_nulls().unique().to_list()) if "form_type" in df.columns else []
    years = sorted(df["year"].drop_nulls().unique().to_list()) if "year" in df.columns else []
    filings = df["accession_no"].n_unique() if "accession_no" in df.columns else 0
    return {
        "rows": df.height,
        "filings": filings,
        "forms": forms,
        "year_from": years[0] if years else None,
        "year_to": years[-1] if years else None,
    }


def _runBatch(limit: int | None = None) -> None:
    import subprocess

    tickers = _buildTickerList(limit)
    completed = _loadCompleted()
    docsDir = _docsDir()

    pending = []
    for t in tickers:
        outPath = docsDir / f"{t}.parquet"
        if t in completed or outPath.exists():
            continue
        pending.append(t)

    print(f"[057-002] total={len(tickers)} completed={len(completed)} pending={len(pending)}")

    for idx, ticker in enumerate(pending, start=1):
        outPath = docsDir / f"{ticker}.parquet"
        startedAt = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        print(f"[{idx}/{len(pending)}] {ticker} ...", end=" ", flush=True)

        try:
            subprocess.run(
                [sys.executable, str(Path(__file__).resolve()), "--ticker", ticker],
                check=True,
                timeout=TICKER_TIMEOUT_SECONDS,
                capture_output=True,
            )

            if not outPath.exists() or outPath.stat().st_size == 0:
                record = {
                    "ticker": ticker,
                    "status": "no_data",
                    "started_at": startedAt,
                    "finished_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }
                print("no data")
            else:
                summary = _summarize(outPath)
                record = {
                    "ticker": ticker,
                    "status": "downloaded",
                    "started_at": startedAt,
                    "finished_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    **summary,
                }
                print(f"ok rows={summary['rows']} filings={summary['filings']}")

        except subprocess.TimeoutExpired:
            record = {
                "ticker": ticker,
                "status": "timeout",
                "started_at": startedAt,
                "finished_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "reason": f"timeout after {TICKER_TIMEOUT_SECONDS}s",
            }
            print("TIMEOUT")

        except subprocess.CalledProcessError as e:
            stderr = (e.stderr or b"").decode("utf-8", errors="replace")[-500:]
            record = {
                "ticker": ticker,
                "status": "failed",
                "started_at": startedAt,
                "finished_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "reason": stderr,
            }
            print(f"FAIL: {stderr[:100]}")

        _appendProgress(record)
        time.sleep(COOLDOWN_SECONDS)

    print(f"[057-002] done. check {_progressPath()}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", help="단일 ticker 수집 (subprocess용)")
    parser.add_argument("--limit", type=int, help="수집 대상 수 제한")
    args = parser.parse_args()

    if args.ticker:
        _collectSingleTicker(args.ticker.upper())
        return

    _runBatch(limit=args.limit)


if __name__ == "__main__":
    main()
