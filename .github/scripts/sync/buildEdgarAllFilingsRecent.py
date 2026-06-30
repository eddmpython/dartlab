"""EDGAR 공시 피드 빌드 — submissions.zip bulk → edgar/allFilings/{recent,market_recent}.parquet + HF push.

KR ``buildAllFilingsRecent.py`` 대칭. 수집은 gather(``bulkSubmissions``)에 위임 — 본 스크립트는 가공
(순회·정기 제외·ticker 매핑·정렬·HF 발행)만. recent 블록(회사당 ~1000건, 수년치)만 써 네트워크/메모리 절약.

산출물 (런타임 ``nonRegularFilingsSource`` US 분기가 직독):
  - ``recent.parquet``         : stockCode 정렬(filter pushdown — 우측 단일기업 패널). 전 종목 수시공시.
  - ``market_recent.parquet``  : filingDate 내림차순 최근 90일(좌측 시장 피드). 단일 whole-file GET.

정기보고서(10-K/10-Q/20-F/40-F)는 제외 — 그건 재무 패널 몫. 수시(8-K·DEF 14A·SC 13·Form 4 등)만.

Usage:
    uv run python -X utf8 .github/scripts/sync/buildEdgarAllFilingsRecent.py [--no-push] [--since-year 2023]
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import polars as pl

import dartlab.config as _cfg
from dartlab.core.edgarClient import SUPPORTED_REGULAR_FORMS
from dartlab.gather.edgar.bulkSubmissions import downloadSubmissionsBulk, iterSubmissionsBulk
from dartlab.gather.edgar.submissions import findAllFilings

_REPO = "eddmpython/dartlab-data"
_REL_DIR = "edgar/allFilings"
_RECENT_NAME = "recent.parquet"
_FEED_NAME = "market_recent.parquet"  # ★endsWith('recent.parquet') → worker max-age=600 (바꾸지 말 것)
_FEED_WINDOW_DAYS = 90
_FEED_ROW_GROUP = 5_000
_COLS = ["stockCode", "entityName", "filingDate", "form", "accessionNo", "docDescription", "url"]
_REGULAR = set(SUPPORTED_REGULAR_FORMS)


def _cikToTicker() -> dict[str, str]:
    """CIK(0-padded 10) → ticker(대문자). 상장 universe 만 — 미상장 CIK 공시는 피드 제외."""
    from dartlab.core.dataLoader import loadEdgarListedUniverse

    univ = loadEdgarListedUniverse()
    return {str(c).zfill(10): str(t).upper() for c, t in zip(univ["cik"].to_list(), univ["ticker"].to_list()) if t}


def build(*, sinceYear: int, zipPath: Path | None = None) -> pl.DataFrame:
    """submissions bulk 순회 → 수시공시 전 종목 1프레임 (stockCode 정렬).

    Args:
        sinceYear: filingDate 연도 하한(피드 윈도).
        zipPath: None 이면 자동 다운로드(TTL 가드).

    Returns:
        pl.DataFrame — _COLS 스키마, stockCode·filingDate(desc) 정렬. 정기보고서 제외.
    """
    cikToTicker = _cikToTicker()
    zp = zipPath if zipPath is not None else downloadSubmissionsBulk()
    rows: list[dict] = []
    seen = 0
    for cik, payload in iterSubmissionsBulk(zp, recentOnly=True):
        ticker = cikToTicker.get(cik)
        if not ticker:
            continue
        seen += 1
        for r in findAllFilings(payload, sinceYear=sinceYear):
            if r["form"] in _REGULAR:  # 정기보고서 제외 — 수시만
                continue
            rows.append(
                {
                    "stockCode": ticker,
                    "entityName": r["entityName"],
                    "filingDate": r["filing_date"].replace("-", ""),  # YYYYMMDD
                    "form": r["form"],
                    "accessionNo": r["accession_no"],
                    "docDescription": r["primary_doc_description"],
                    "url": r["filing_url"],
                }
            )
    schema = {c: pl.Utf8 for c in _COLS}
    out = pl.DataFrame(rows, schema=schema) if rows else pl.DataFrame(schema=schema)
    out = out.unique(subset=["accessionNo"], keep="first").sort(["stockCode", "filingDate"], descending=[False, True])
    print(f"[build] {out.height:,} rows ({out['stockCode'].n_unique():,} 종목, listed CIK {seen:,})", flush=True)
    return out


def buildFeed(out: pl.DataFrame) -> pl.DataFrame:
    """전체시장 시간순 피드 — filingDate 내림차순 최근 90일(좌측 레일). 빈 데이터면 빈 프레임."""
    dataMax = out["filingDate"].max() if out.height else None
    if dataMax is None:
        return out
    cutoff = (datetime.strptime(str(dataMax), "%Y%m%d") - timedelta(days=_FEED_WINDOW_DAYS)).strftime("%Y%m%d")
    return out.filter(pl.col("filingDate") >= cutoff).sort("filingDate", descending=True)


def push(dest: Path, token: str, name: str) -> None:
    """단일 parquet → HF edgar/allFilings/{name} (retry)."""
    from huggingface_hub import HfApi

    from dartlab.core.hfRetry import retryHfCall

    retryHfCall(
        HfApi(token=token).upload_file,
        path_or_fileobj=str(dest),
        path_in_repo=f"{_REL_DIR}/{name}",
        repo_id=_REPO,
        repo_type="dataset",
        commit_message=f"갱신: {_REL_DIR}/{name}",
    )
    print(f"[push] {name} → HF {_REL_DIR}/", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-push", action="store_true", help="HF 발행 생략(로컬 검증)")
    ap.add_argument("--since-year", type=int, default=2023, help="filingDate 연도 하한")
    args = ap.parse_args()

    out = build(sinceYear=args.since_year)
    outDir = Path(_cfg.dataDir) / "edgar" / "allFilings"
    outDir.mkdir(parents=True, exist_ok=True)
    recentPath = outDir / _RECENT_NAME
    out.write_parquet(recentPath, compression="zstd", row_group_size=20_000)
    feed = buildFeed(out)
    feedPath = outDir / _FEED_NAME
    feed.write_parquet(feedPath, compression="zstd", row_group_size=_FEED_ROW_GROUP)
    print(f"[feed] {feed.height:,} rows → {feedPath} ({feedPath.stat().st_size / 1e6:.2f} MB)", flush=True)

    if args.no_push:
        print("[main] --no-push — HF 발행 생략", flush=True)
        return 0
    token = os.environ.get("HF_TOKEN", "").strip()
    if not token:
        print("[main] HF_TOKEN 없음 — 발행 생략", flush=True)
        return 1
    push(recentPath, token, _RECENT_NAME)
    push(feedPath, token, _FEED_NAME)
    return 0


if __name__ == "__main__":
    sys.exit(main())
