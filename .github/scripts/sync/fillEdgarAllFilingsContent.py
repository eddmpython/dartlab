"""US allFilings 본문 점진 수집 runner. recent.parquet 메타로 일자별 content_raw 를 채워 HF per-day 발행.

전 수시공시 본문을 모은다(정기 10-K/10-Q 등은 panel 소유라 recent.parquet 에서 이미 제외). 전 종목 2015 이후
전 공시는 4M+ 이라 한 번에 못 받는다. run 당 예산(maxDays)만큼 forward(최신 미충전일) + backfill(과거
미충전일)로 점진 수집한다. 일자별 fillContentDay 가 idempotent(ok/no_body skip, error retry)라 재실행 안전.
DART allFilingsBackfill 대칭.

실행::

    uv run python -X utf8 .github/scripts/sync/fillEdgarAllFilingsContent.py [--max-days 20] [--forward-days 3]
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import polars as pl

import dartlab.config as _cfg
from dartlab.core.hfRetry import retryHfCall
from dartlab.gather.edgar.allFilingsContent import fillContentDay

_REPO = "eddmpython/dartlab-data"
_META = "edgar/allFilings/recent.parquet"
_CONTENT_DIR = "edgar/allFilingsContent"


def _doneDays(api) -> set[str]:
    """이미 발행된 content per-day 파일의 날짜 집합(YYYYMMDD)."""
    try:
        return {
            p.path.split("/")[-1].replace(".parquet", "")
            for p in api.list_repo_tree(_REPO, _CONTENT_DIR, repo_type="dataset")
            if p.path.endswith(".parquet")
        }
    except Exception:  # noqa: BLE001 (디렉터리 부재 = 최초 실행)
        return set()


def selectDays(allDays: list[str], done: set[str], *, maxDays: int, forwardDays: int) -> list[str]:
    """이번 run 처리할 날짜. 최신 미충전 forwardDays(forward) + 오래된 미충전(backfill), 합 maxDays."""
    unfilled = [d for d in allDays if d not in done]
    if not unfilled:
        return []
    fwd = unfilled[-forwardDays:] if forwardDays else []
    back = [d for d in unfilled if d not in set(fwd)]
    return (fwd + back)[:maxDays]


def main() -> int:
    """recent.parquet 메타 → 미충전 일자 선정 → fillContentDay + HF 발행 (예산만큼)."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-days", type=int, default=20, help="이번 run 처리할 일 수(CI 시간 예산)")
    ap.add_argument("--forward-days", type=int, default=3, help="최신 미충전일 우선 충전 수(피드 신선도)")
    args = ap.parse_args()

    tok = os.environ.get("HF_TOKEN", "").strip()
    if not tok:
        print("[content] HF_TOKEN 없음", flush=True)
        return 1
    from huggingface_hub import HfApi, hf_hub_download

    api = HfApi(token=tok)
    metaFp = hf_hub_download(_REPO, _META, repo_type="dataset", token=tok)
    meta = pl.read_parquet(metaFp, columns=["accessionNo", "stockCode", "filingDate", "url"])
    allDays = sorted(meta["filingDate"].unique().to_list())
    done = _doneDays(api)
    todo = selectDays(allDays, done, maxDays=args.max_days, forwardDays=args.forward_days)
    unfilled = len([d for d in allDays if d not in done])
    if not todo:
        print(f"[content] 전 {len(allDays)}일 충전 완료", flush=True)
        return 0
    print(f"[content] 전 {len(allDays)}일 · 미충전 {unfilled}일 · 이번 run {len(todo)}일", flush=True)

    outDir = Path(_cfg.dataDir) / "edgar" / "allFilingsContent"
    for day in todo:
        dayMeta = meta.filter(pl.col("filingDate") == day)
        outPath = outDir / f"{day}.parquet"
        fillContentDay(dayMeta, outPath)
        retryHfCall(
            api.upload_file,
            path_or_fileobj=str(outPath),
            path_in_repo=f"{_CONTENT_DIR}/{day}.parquet",
            repo_id=_REPO,
            repo_type="dataset",
            commit_message=f"본문: {_CONTENT_DIR}/{day}",
        )
        print(f"  발행 {day}", flush=True)
    print(f"[content] {len(todo)}일 완료 · 남은 {unfilled - len(todo)}일", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
