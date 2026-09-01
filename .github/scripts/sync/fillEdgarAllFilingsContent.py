"""US allFilings 본문 점진 수집 runner. recent.parquet 메타로 일자별 content_raw 를 채워 HF per-day 발행.

전 수시공시 본문을 모은다(정기 10-K/10-Q 등은 panel 소유라 recent.parquet 에서 이미 제외). 전 종목 2015 이후
전 공시는 4M+ 이라 한 번에 못 받는다. run 당 예산(maxDays 와 budgetMinutes)만큼 forward(최신 미충전일) +
backfill(과거 미충전일)로 점진 수집한다. 일자별 fillContentDay 가 idempotent(ok/no_body skip, error retry)라
재실행 안전. DART allFilingsBackfill 대칭.

시간 예산: 하루치가 10~55 분(2026-08-31 실측 최장 53.5 분)이라 20 일은 job 상한(120 분) 안에 못 끝난다. 예산 없이 돌리면 매 run 이
timeout 으로 cancelled 로 끝나 감시에서 실패로 보이고(2026-08-31·09-01 실측), 진행분은 남지만 결론이
거짓이다. budgetMinutes 가 지나면 새 날짜를 시작하지 않고 success 로 끝낸다. 남은 시간에 하루치가 들어가야
하므로 workflow timeout 보다 최장 하루치만큼 작게 둔다.

실행::

    uv run python -X utf8 .github/scripts/sync/fillEdgarAllFilingsContent.py [--max-days 20] [--forward-days 3] [--budget-minutes 60]
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from collections.abc import Callable
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


def fillDays(
    todo: list[str],
    fillDay: Callable[[str], None],
    *,
    budgetSeconds: float,
    clock: Callable[[], float] = time.monotonic,
) -> list[str]:
    """예산(초) 안에서 날짜를 순서대로 처리한다(순수 흐름, 테스트 대상).

    새 날짜는 예산이 남았을 때만 시작한다. 시작한 날짜는 끝까지 처리하므로 실제 소요는 예산 + 하루치다.

    Args:
        todo: 처리 순서대로의 날짜(YYYYMMDD).
        fillDay: 하루치를 수집·발행하는 함수.
        budgetSeconds: 새 날짜 시작을 허용하는 누적 시간(초).
        clock: 단조 시계(테스트 주입용).

    Returns:
        처리를 마친 날짜 목록.

    Raises:
        없음. fillDay 의 예외는 그대로 전파한다.

    Example:
        >>> fillDays(["20260101", "20260102"], lambda day: None, budgetSeconds=60)
        ['20260101', '20260102']
    """
    startedAt = clock()
    done: list[str] = []
    for day in todo:
        if clock() - startedAt >= budgetSeconds:
            break
        fillDay(day)
        done.append(day)
    return done


def main() -> int:
    """recent.parquet 메타 → 미충전 일자 선정 → fillContentDay + HF 발행 (예산만큼)."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-days", type=int, default=20, help="이번 run 처리할 일 수 상한")
    ap.add_argument("--forward-days", type=int, default=3, help="최신 미충전일 우선 충전 수(피드 신선도)")
    ap.add_argument(
        "--budget-minutes",
        type=float,
        default=60.0,
        help="이 시간이 지나면 새 날짜를 시작하지 않는다(분). workflow timeout 보다 최장 하루치만큼 작게",
    )
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
    print(
        f"[content] 전 {len(allDays)}일 · 미충전 {unfilled}일 · 이번 run 최대 {len(todo)}일 · 예산 {args.budget_minutes:g}분",
        flush=True,
    )

    outDir = Path(_cfg.dataDir) / "edgar" / "allFilingsContent"

    def fillDay(day: str) -> None:
        startedAt = time.monotonic()
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
        print(f"  발행 {day} ({(time.monotonic() - startedAt) / 60:.1f}분)", flush=True)

    finished = fillDays(todo, fillDay, budgetSeconds=args.budget_minutes * 60.0)
    skipped = len(todo) - len(finished)
    print(
        f"[content] {len(finished)}일 완료 · 남은 {unfilled - len(finished)}일"
        + (f" · 예산 소진으로 이번 run 미착수 {skipped}일" if skipped else ""),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
