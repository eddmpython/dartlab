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


def _hfBaseFrame() -> pl.DataFrame | None:
    """기존 HF edgar/allFilings/recent.parquet (있으면). 증분 merge 의 baseline. KR buildAllFilingsRecent 동형.

    US recent 은 submissions recent 블록(회사당 ~1000건)만 재빌드하면 활성 공시기업의 옛 공시가
    블록에서 밀려 사라진다(슬라이딩). HF baseline 과 merge·dedup 하면 전 이력이 누적 보존된다(trim 없음).
    이력 심화(floor 2015)는 backfill(recentOnly=False, 과거 페이지)이 담당하고 본 merge 가 그 결과를 보존한다.
    """
    url = f"https://huggingface.co/datasets/{_REPO}/resolve/main/{_REL_DIR}/{_RECENT_NAME}"
    from dartlab.core.hfRetry import retryHfCall  # HF read SSOT (transient 429/timeout 재시도)

    try:
        return retryHfCall(pl.read_parquet, url, columns=_COLS)
    except Exception:  # noqa: BLE001 (최초 빌드 파일 부재·영구 실패면 None, 다음 cron 자가복구)
        return None


def _accumulate(fresh: pl.DataFrame, base: pl.DataFrame | None) -> pl.DataFrame:
    """신규분 + HF baseline merge → accessionNo dedup, trim 없이 누적 (KR 동형). 순수 함수(네트워크 무관).

    trim 을 두지 않는다. recent 블록이 밀려도 baseline 이 과거를 보존해야 전 이력이 남는다.
    """
    frames = [fresh]
    if base is not None and base.height:
        frames.append(base.select([c for c in _COLS if c in base.columns]))
    out = pl.concat(frames, how="diagonal_relaxed")
    return out.unique(subset=["accessionNo"], keep="first").sort(["stockCode", "filingDate"], descending=[False, True])


def build(*, sinceYear: int, mergeHf: bool = True, zipPath: Path | None = None) -> pl.DataFrame:
    """submissions bulk 순회 + HF baseline merge → 수시공시 전 종목 1프레임 (stockCode 정렬, 전 이력 누적).

    Args:
        sinceYear: filingDate 연도 하한(신규 수집분). baseline 의 과거분은 이 하한과 무관하게 보존.
        mergeHf: True 면 기존 HF recent.parquet 과 merge·dedup 해 전 이력 누적(KR 동형). 슬라이딩 방지.
        zipPath: None 이면 자동 다운로드(TTL 가드).

    Returns:
        pl.DataFrame. _COLS 스키마, stockCode·filingDate(desc) 정렬. 정기보고서 제외.
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
            if r["form"] in _REGULAR:  # 정기보고서 제외(수시만)
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
    fresh = pl.DataFrame(rows, schema=schema) if rows else pl.DataFrame(schema=schema)
    out = _accumulate(fresh, _hfBaseFrame() if mergeHf else None)
    span = f"{out['filingDate'].min()}~{out['filingDate'].max()}" if out.height else "(빈)"
    print(
        f"[build] {out.height:,} rows ({out['stockCode'].n_unique():,} 종목, listed CIK {seen:,}, {span})", flush=True
    )
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
