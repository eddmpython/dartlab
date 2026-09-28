"""GDELT 2.0 GKG backfill cron — Phase D 글로벌 5 년 백필 진입점.

http://data.gdeltproject.org/gdeltv2/ 의 15-min GKG 슬롯을 시간대 루프로
다운로드 → market 필터 → 일별 parquet 통합 → `data/news/gdelt/{market}/{date}.parquet`.

실행::

    # smoke (1 일, 6-시간 슬롯 = 4 fetch)
    uv run python -X utf8 .github/scripts/sync/syncGdeltBackfill.py --start 2026-05-27 --end 2026-05-27 --step-minutes 360

    # 30 일 (6-시간 슬롯, 120 fetch)
    uv run python -X utf8 .github/scripts/sync/syncGdeltBackfill.py --start 2026-04-28 --end 2026-05-28

    # 5 년 (heavy, ~7300 fetch, 24-시간 슬롯)
    uv run python -X utf8 .github/scripts/sync/syncGdeltBackfill.py --start 2021-05-28 --end 2026-05-28 --step-minutes 1440

GDELT 슬롯 빈도:
    15  → 모든 슬롯 (전수)
    60  → 시간당 1 슬롯 (24/day)
    360 → 6 시간당 1 슬롯 (4/day, narrative 충분)
    1440 → 일당 1 슬롯 (1/day, 가장 빠름)

실패 처리 (슬롯 단위 격리):
    한 슬롯의 공급 실패(SourceUnavailableError: HTTP, ZIP, CSV)는 ``::warning::`` 으로 남기고
    나머지 슬롯을 계속 처리한 뒤 끝에 실패 슬롯 요약을 출력한다. 종료코드 1 은 슬롯이 0 개이거나
    모든 슬롯이 실패한 경우뿐이다(실제 공급 장애는 RED 로 드러남). 그 밖의 예외(프로그래밍 오류)는
    잡지 않고 그대로 전파한다.

ToS: GDELT 명시 학술+상업 무료 (https://www.gdeltproject.org/about.html).
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from datetime import date as _date
from datetime import datetime, timedelta, timezone
from pathlib import Path

import polars as pl

REPO_ROOT = Path(__file__).resolve().parents[3]
_log = logging.getLogger("syncGdeltBackfill")

# 저장 경로·upsert 는 gather.sources.newsIo.writeDailyParquet 공유 (dir SSOT=newsSources).


def _failureReason(exc: BaseException) -> str:
    """슬롯 실패 사유 한 줄. 래핑 예외는 원인(__cause__)까지 붙여 로그만으로 진단되게 한다."""
    reason = str(exc)
    cause = exc.__cause__
    if cause is not None:
        reason = f"{reason} ({type(cause).__name__}: {cause})"
    # workflow command(::warning::)는 한 줄 단위라 여러 줄 메시지(httpx 등)를 한 줄로 접는다.
    return " ".join(reason.split())


def _reportFailedSlots(failedSlots: list[tuple[str, str]], total: int) -> None:
    """실패 슬롯 요약 (run 끝에 1 회)."""
    _log.warning("실패 슬롯 %d/%d:", len(failedSlots), total)
    for slotId, reason in failedSlots:
        _log.warning("  %s  %s", slotId, reason)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="GDELT 2.0 GKG backfill cron")
    parser.add_argument("--start", required=True, help="YYYY-MM-DD UTC")
    parser.add_argument("--end", required=True, help="YYYY-MM-DD UTC (inclusive)")
    parser.add_argument(
        "--step-minutes",
        type=int,
        default=360,
        help="슬롯 간격 — 15(전수)/60(시간)/360(6h, default narrative 충분)/1440(일)",
    )
    parser.add_argument(
        "--markets",
        nargs="+",
        default=None,
        help="시장 필터 (KR US JP CN GLOBAL). 미지정 시 전체.",
    )
    parser.add_argument("--sleep", type=float, default=0.5, help="슬롯 간 sleep 초 (GDELT 부담 완화)")
    parser.add_argument("--max-slots", type=int, default=None, help="상한 (테스트용)")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    from dartlab.gather.sources.gdelt import fetchGdeltGkg, iterGdeltSlots
    from dartlab.gather.types import SourceUnavailableError

    startDt = datetime.fromisoformat(args.start).replace(tzinfo=timezone.utc)
    endDt = datetime.fromisoformat(args.end).replace(tzinfo=timezone.utc) + timedelta(hours=23, minutes=45)

    slots = iterGdeltSlots(startDt, endDt, stepMinutes=args.step_minutes)
    if args.max_slots:
        slots = slots[: args.max_slots]
    _log.info(
        "범위 %s~%s, %d 슬롯 (step=%d 분, markets=%s)",
        args.start,
        args.end,
        len(slots),
        args.step_minutes,
        args.markets or "전체",
    )

    if not slots:
        _log.warning("슬롯 0 — abort")
        return 1

    # 일자별 누적 — same day 의 여러 슬롯 결과를 한 parquet 으로 합침.
    dayBuffer: dict[tuple[str, _date], list[pl.DataFrame]] = {}
    # 슬롯 단위 격리. forward 창(D-2~D-1)은 같은 슬롯을 이틀 연속 다시 받으므로, 격리가 없으면
    # 불량 파일 1 개가 두 날의 run 을 연달아 실패시키고 나머지 슬롯까지 함께 버린다.
    failedSlots: list[tuple[str, str]] = []

    for i, slot in enumerate(slots):
        slotId = slot.strftime("%Y%m%d%H%M%S")
        try:
            df = fetchGdeltGkg(slot, markets=args.markets)
        except SourceUnavailableError as exc:
            reason = _failureReason(exc)
            failedSlots.append((slotId, reason))
            print(f"::warning::GDELT 슬롯 {slotId} 건너뜀: {reason}", flush=True)
            time.sleep(args.sleep)
            continue
        if df.height == 0:
            _log.debug("슬롯 %s — 0 row", slot)
            time.sleep(args.sleep)
            continue
        # 슬롯 결과를 (market, day) 그룹으로 분리
        for (m, d), partDf in df.group_by(["market", "date"]):
            dayBuffer.setdefault((m, d), []).append(partDf)
        _log.info(
            "[%d/%d] %s → %d row (markets=%s)",
            i + 1,
            len(slots),
            slot.strftime("%Y-%m-%d %H:%M"),
            df.height,
            list(df["market"].unique().to_list()),
        )
        time.sleep(args.sleep)

    if len(failedSlots) == len(slots):
        # 성공 슬롯 0 = 실제 공급 장애. 조용히 green 으로 넘기지 않고 RED 로 드러낸다.
        _reportFailedSlots(failedSlots, len(slots))
        print(f"::error::GDELT 모든 슬롯 실패 ({len(slots)}/{len(slots)}). 성공한 슬롯이 없어 종료합니다", flush=True)
        return 1

    # 일자별 flush
    from dartlab.gather.sources.newsIo import writeDailyParquet
    from dartlab.gather.sources.newsSources import getNewsSource

    gdeltDir = getNewsSource("gdelt").dir
    totalAdded = 0
    for (m, d), frames in dayBuffer.items():
        combined = pl.concat(frames, how="diagonal_relaxed")
        target, total, added = writeDailyParquet(combined, dir=gdeltDir, market=m, day=d)
        totalAdded += added
        _log.info("저장 %s — total=%d added=%d", target, total, added)

    _log.info("완료 — %d (market, day) 파일, 신규 %d row", len(dayBuffer), totalAdded)

    # uploadData.py 호환
    distDir = REPO_ROOT / "dist"
    distDir.mkdir(parents=True, exist_ok=True)
    (distDir / "changed_newsGdelt.txt").write_text(
        "\n".join(f"{m}/{d.isoformat()}.parquet" for (m, d) in dayBuffer.keys()) + "\n",
        encoding="utf-8",
    )
    if failedSlots:
        _reportFailedSlots(failedSlots, len(slots))
    return 0


if __name__ == "__main__":
    sys.exit(main())
