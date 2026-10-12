"""US allFilings 본문 점진 수집 runner. recent.parquet 메타로 일자별 content_raw 를 채워 HF per-day 발행.

전 수시공시 본문을 모은다(정기 10-K/10-Q 등은 panel 소유라 recent.parquet 에서 이미 제외). 전 종목 2015 이후
전 공시는 4M+ 이라 한 번에 못 받는다. run 당 예산(maxDays 와 budgetMinutes)만큼 forward(최신 미충전일) +
backfill(과거 미충전일)로 점진 수집한다. 일자별 fillContentDay 가 idempotent(ok/no_body skip, error retry)라
재실행 안전. DART allFilingsBackfill 대칭.

시간 예산: 하루치가 10~55 분(2026-08-31 실측 최장 53.5 분)이라 20 일은 job 상한(120 분) 안에 못 끝난다. 예산 없이 돌리면 매 run 이
timeout 으로 cancelled 로 끝나 감시에서 실패로 보이고(2026-08-31·09-01 실측), 진행분은 남지만 결론이
거짓이다. budgetMinutes 가 지나면 새 날짜를 시작하지 않고 success 로 끝낸다. 남은 시간에 하루치가 들어가야
하므로 workflow timeout 보다 최장 하루치만큼 작게 둔다.

하루치 안의 마감(hardMinutes)과 연속 오류 차단(tripAfter)도 둔다. 예산 안에 시작한 하루치가 SEC 응답 지연으로
85 분 멈춰 job 상한에 취소된 run 이 있었다(2026-10-09 37919545859). 멈춘 날의 남은 행은 error 로 남겨 발행하고,
연속 오류로 멈췄으면 exit 1 로 끝내 감시가 새 러너로 재실행하게 한다.

재방문: 발행된 날 파일의 error 행(403/429/5xx/timeout)은 그 날짜가 "충전됨" 으로 빠져 다시 받지 않았다.
2026-10-12 표본 60 일 중 19 일, 61,784 행 중 6,737 행이 error 였다. run 마다 발행일 일부(revisitScan)의
parquet footer 에서 fetch_status 최솟값만 읽어 error 가 남은 날을 찾고, 그 날 파일을 HF 에서 받아 error 행만
다시 받는다.

실행::

    uv run python -X utf8 .github/scripts/sync/fillEdgarAllFilingsContent.py [--max-days 20] [--forward-days 3] \\
        [--budget-minutes 60] [--hard-minutes 105] [--trip-after 25] [--revisit-days 5] [--revisit-scan 60]
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from collections import Counter
from collections.abc import Callable
from datetime import date
from pathlib import Path

import polars as pl

import dartlab.config as _cfg
from dartlab.core.hfRetry import retryHfCall
from dartlab.gather.edgar.allFilingsContent import STOP_TRIP, fillContentDay

_REPO = "eddmpython/dartlab-data"
_META = "edgar/allFilings/recent.parquet"
_CONTENT_DIR = "edgar/allFilingsContent"


def _doneDays(api) -> set[str]:
    """이미 발행된 content per-day 파일의 날짜 집합(YYYYMMDD).

    디렉터리 부재(404, 최초 실행)만 빈 집합이다. 429 같은 일시 실패는 ``retryHfCall`` 로 기다렸다 다시
    묻고, 그래도 안 되면 예외를 올린다. 예전에는 모든 예외를 빈 집합으로 바꿔, 목록 조회가 한 번 막히면
    이미 발행한 날짜까지 SEC 에서 다시 받아 덮어썼다.
    """
    from huggingface_hub.errors import HfHubHTTPError

    try:
        entries = retryHfCall(lambda: list(api.list_repo_tree(_REPO, _CONTENT_DIR, repo_type="dataset")))
    except HfHubHTTPError as exc:
        if getattr(getattr(exc, "response", None), "status_code", None) == 404:
            return set()
        raise
    return {p.path.split("/")[-1].replace(".parquet", "") for p in entries if p.path.endswith(".parquet")}


def selectDays(allDays: list[str], done: set[str], *, maxDays: int, forwardDays: int) -> list[str]:
    """이번 run 처리할 날짜. 최신 미충전 forwardDays(forward) + 오래된 미충전(backfill), 합 maxDays."""
    unfilled = [d for d in allDays if d not in done]
    if not unfilled:
        return []
    fwd = unfilled[-forwardDays:] if forwardDays else []
    back = [d for d in unfilled if d not in set(fwd)]
    return (fwd + back)[:maxDays]


def scanSlice(done: list[str], size: int, *, ordinal: int) -> list[str]:
    """발행일 중 이번 run 이 footer 를 볼 구간. 날마다 다음 구간으로 돌아 len(done)/size 일에 한 바퀴 돈다.

    Args:
        done: 발행된 날짜(정렬).
        size: 이번 run 에 볼 날짜 수.
        ordinal: 회전 기준(보통 오늘의 ``date.toordinal()``).

    Returns:
        이번 run 이 볼 날짜 목록(순환).

    Raises:
        없음.

    Example:
        >>> scanSlice(["a", "b", "c"], 2, ordinal=1)
        ['c', 'a']
    """
    if not done or size <= 0:
        return []
    size = min(size, len(done))
    start = (ordinal * size) % len(done)
    return [done[(start + i) % len(done)] for i in range(size)]


def planWork(todo: list[str], revisit: list[str], *, forwardDays: int) -> list[str]:
    """처리 순서. 최신 미충전(forward) 다음 재방문, 그다음 과거 미충전(backfill).

    Args:
        todo: ``selectDays`` 결과(forward 가 앞).
        revisit: error 행이 남은 발행일.
        forwardDays: ``selectDays`` 에 준 forward 수.

    Returns:
        처리 순서대로의 날짜.

    Raises:
        없음.

    Example:
        >>> planWork(["f1", "b1"], ["r1"], forwardDays=1)
        ['f1', 'r1', 'b1']
    """
    head = todo[: min(forwardDays, len(todo))]
    return head + [day for day in revisit if day not in todo] + todo[len(head) :]


def hasErrorRows(metadata) -> bool | None:
    """parquet footer 통계에서 fetch_status 최솟값이 error 인 row group 이 있는지. 통계가 없으면 None.

    상태값은 error < no_body < ok 순이라 최솟값만 보면 된다. 본문(content_raw)은 내려받지 않는다.

    Args:
        metadata: ``pyarrow.parquet.FileMetaData``.

    Returns:
        error 행이 있으면 True, 없으면 False, 판정할 통계가 없으면 None.

    Raises:
        없음.

    Example:
        >>> hasErrorRows(pq.ParquetFile(path).metadata)  # doctest: +SKIP
        False
    """
    names = [metadata.schema.column(i).name for i in range(metadata.num_columns)]
    if "fetch_status" not in names:
        return None
    index = names.index("fetch_status")
    for group in range(metadata.num_row_groups):
        stats = metadata.row_group(group).column(index).statistics
        if stats is None or not stats.has_min_max:
            return None
        if stats.min == "error":
            return True
    return False


def _revisitDays(fs, days: list[str], limit: int) -> list[str]:
    """footer 를 읽어 error 행이 남은 날을 limit 개까지 고른다. 읽기 실패는 건너뛴다(재방문은 보조 경로)."""
    import pyarrow.parquet as pq

    found: list[str] = []
    for day in days:
        if len(found) >= limit:
            break
        try:
            with fs.open(f"datasets/{_REPO}/{_CONTENT_DIR}/{day}.parquet", "rb") as fh:
                metadata = pq.ParquetFile(fh).metadata
        except Exception as exc:  # noqa: BLE001 (재방문 후보 조회 실패는 run 실패로 올리지 않는다)
            print(f"  [revisit] {day} footer 조회 실패: {type(exc).__name__}", flush=True)
            continue
        if hasErrorRows(metadata):
            found.append(day)
    return found


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


def main(argv: list[str] | None = None) -> int:
    """recent.parquet 메타 → 미충전 일자 선정 + 재방문 → fillContentDay + HF 발행 (예산만큼)."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-days", type=int, default=20, help="이번 run 처리할 일 수 상한")
    ap.add_argument("--forward-days", type=int, default=3, help="최신 미충전일 우선 충전 수(피드 신선도)")
    ap.add_argument(
        "--budget-minutes",
        type=float,
        default=60.0,
        help="이 시간이 지나면 새 날짜를 시작하지 않는다(분). workflow timeout 보다 최장 하루치만큼 작게",
    )
    ap.add_argument(
        "--hard-minutes",
        type=float,
        default=105.0,
        help="이 시간이 지나면 하루치 안에서도 fetch 를 멈추고 남은 행을 error 로 발행한다(분). job 상한보다 작게",
    )
    ap.add_argument("--trip-after", type=int, default=25, help="error 가 이만큼 연달아 나면 멈춘다(SEC 차단 추정)")
    ap.add_argument("--revisit-days", type=int, default=5, help="이번 run 에 error 행을 다시 받을 발행일 수 상한")
    ap.add_argument("--revisit-scan", type=int, default=60, help="이번 run 에 footer 를 볼 발행일 수(날마다 회전)")
    args = ap.parse_args(argv)
    # 예산은 스크립트 시작부터 잰다. 시작 시 HF 재시도(429 는 최대 6분 대기)까지 예산에 넣어야
    # "예산 + 최장 하루치 < job timeout" 이 재시도가 붙은 날에도 성립한다.
    scriptStartedAt = time.monotonic()
    hardDeadline = scriptStartedAt + args.hard_minutes * 60.0

    tok = os.environ.get("HF_TOKEN", "").strip()
    if not tok:
        print("[content] HF_TOKEN 없음", flush=True)
        return 1
    from huggingface_hub import HfApi, HfFileSystem, hf_hub_download

    api = HfApi(token=tok)
    # 2026-09-22: HF resolver 한도(5분당 5000, 계정 단위)에 걸린 429 한 번으로 run 이 죽었다. 재시도한다.
    metaFp = retryHfCall(hf_hub_download, _REPO, _META, repo_type="dataset", token=tok)
    meta = pl.read_parquet(metaFp, columns=["accessionNo", "stockCode", "filingDate", "url"])
    allDays = sorted(meta["filingDate"].unique().to_list())
    done = _doneDays(api)
    todo = selectDays(allDays, done, maxDays=args.max_days, forwardDays=args.forward_days)
    unfilled = len([d for d in allDays if d not in done])
    revisit: list[str] = []
    if args.revisit_days > 0 and done:
        scanned = scanSlice(sorted(done & set(allDays)), args.revisit_scan, ordinal=date.today().toordinal())
        revisit = _revisitDays(HfFileSystem(token=tok), scanned, args.revisit_days)
        print(f"[content] 재방문: footer {len(scanned)}일 확인 · error 남은 날 {revisit}", flush=True)
    work = planWork(todo, revisit, forwardDays=args.forward_days)
    if not work:
        print(f"[content] 전 {len(allDays)}일 충전 완료", flush=True)
        return 0
    print(
        f"[content] 전 {len(allDays)}일 · 미충전 {unfilled}일 · 이번 run 최대 {len(todo)}일 + 재방문 {len(revisit)}일"
        f" · 예산 {args.budget_minutes:g}분",
        flush=True,
    )

    outDir = Path(_cfg.dataDir) / "edgar" / "allFilingsContent"
    revisitSet = set(revisit)
    stopped: list[str] = []
    processed: list[str] = []

    def fillDay(day: str) -> None:
        # 연속 오류로 멈췄거나 하루치 마감이 지났으면 새 날짜를 시작하지 않는다.
        if stopped or time.monotonic() >= hardDeadline:
            return
        startedAt = time.monotonic()
        dayMeta = meta.filter(pl.col("filingDate") == day)
        outPath = outDir / f"{day}.parquet"
        if day in revisitSet:
            # 발행본을 병합 base 로 받아 ok/no_body 는 그대로 두고 error 행만 다시 받는다.
            retryHfCall(
                hf_hub_download,
                _REPO,
                f"{_CONTENT_DIR}/{day}.parquet",
                repo_type="dataset",
                token=tok,
                local_dir=str(Path(_cfg.dataDir)),
            )
        print(f"  착수 {day}{' (재방문)' if day in revisitSet else ''}: 메타 {dayMeta.height}건", flush=True)
        reasons: Counter = Counter()
        out = fillContentDay(dayMeta, outPath, deadline=hardDeadline, tripAfter=args.trip_after, reasons=reasons)
        retryHfCall(
            api.upload_file,
            path_or_fileobj=str(outPath),
            path_in_repo=f"{_CONTENT_DIR}/{day}.parquet",
            repo_id=_REPO,
            repo_type="dataset",
            commit_message=f"본문: {_CONTENT_DIR}/{day}",
        )
        counts = sorted(out.group_by("fetch_status").len().rows()) if out.height else []
        print(
            f"  발행 {day} ({(time.monotonic() - startedAt) / 60:.1f}분) · "
            + " · ".join(f"{status} {n}" for status, n in counts)
            + (f" · 오류 원인 {dict(reasons.most_common(5))}" if reasons else ""),
            flush=True,
        )
        processed.append(day)
        if reasons.get(STOP_TRIP):
            stopped.append(day)

    remaining = max(0.0, args.budget_minutes * 60.0 - (time.monotonic() - scriptStartedAt))
    fillDays(work, fillDay, budgetSeconds=remaining)
    skipped = len(work) - len(processed)
    filledNew = len([d for d in processed if d not in revisitSet])
    print(
        f"[content] {len(processed)}일 처리(재방문 {len(processed) - filledNew}) · 남은 미충전 {unfilled - filledNew}일"
        + (f" · 예산·마감·중단으로 이번 run 미착수 {skipped}일" if skipped else ""),
        flush=True,
    )
    if stopped:
        # 새 러너로 재실행하면 SEC 차단이 풀리는 경우가 많다. 실패로 끝내 감시가 재실행하게 한다.
        print(f"::warning::EDGAR 본문 연속 오류로 멈춤({stopped[0]}). 남은 행은 error 로 발행해 재방문이 받는다.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
