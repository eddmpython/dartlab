"""EDGAR 부문별 매출 백필 runner. DERA notes stem 역순(최신 우선) 순회 + HF 발행.

buildEdgarSegments 계열(가공)을 stem 단위로 호출해 edgar/scan/report/segments.parquet 을 누적
발행한다. 리줌 = segmentsStemsDone.parquet(stem 단위). 최신 stem 부터 돌므로 터미널이 먼저 점등되고,
같은 키 충돌은 먼저 앉은(더 최신 stem) 값이 이긴다(seed-wins·keep=first).

zip 은 stem 당 0.3~1.5GB 라 처리 후 즉시 삭제(--keep-zips 로 보존).

실행::

    uv run python -X utf8 .github/scripts/sync/backfillEdgarSegments.py [--since-year 2015] [--max-stems N]
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
import time
from pathlib import Path

import polars as pl

_REPO = "eddmpython/dartlab-data"
_REL = "edgar/scan/report"
_NAME = "segments"
_DONE = "segmentsStemsDone"
_KEYS = ["stockCode", "period", "flow", "segment"]


def _dl(api, name: str, tok: str) -> pl.DataFrame | None:
    """HF 기존 파일 로드(시드). 부재 시 None."""
    from huggingface_hub import hf_hub_download

    from dartlab.core.hfRetry import retryHfCall

    try:
        fp = retryHfCall(hf_hub_download, _REPO, f"{_REL}/{name}.parquet", repo_type="dataset", token=tok)
        return pl.read_parquet(fp)
    except Exception:  # noqa: BLE001 (최초 실행)
        return None


def main() -> int:
    """stem 역순 순회 → 부문 매출 누적 발행. stem 단위 리줌."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--since-year", type=int, default=2015)
    ap.add_argument("--max-stems", type=int, default=None)
    ap.add_argument("--keep-zips", action="store_true")
    args = ap.parse_args()

    tok = os.environ.get("HF_TOKEN", "").strip()
    if not tok:
        print("[segmentsBackfill] HF_TOKEN 없음", flush=True)
        return 1
    from huggingface_hub import HfApi

    from dartlab.core.hfRetry import retryHfCall
    from dartlab.gather.edgar.identity import loadTickers
    from dartlab.gather.edgar.notesBulk import downloadNotesBulk, notesStems
    from dartlab.scan.builders.edgar.report.segmentsBuild import SEGMENTS_COLS, segmentRowsFromZip

    api = HfApi(token=tok)
    seeded = _dl(api, _NAME, tok)
    frame = seeded if seeded is not None else pl.DataFrame(schema=SEGMENTS_COLS)
    doneDf = _dl(api, _DONE, tok)
    done: set[str] = set(doneDf["stem"].to_list()) if doneDf is not None else set()
    allStems = notesStems(sinceYear=args.since_year)
    newest = allStems[-1] if allStems else ""
    # 최신 stem 은 월중 zip 이 계속 자라므로 done 이어도 항상 재처리(강제 재다운로드 + fresh 우선 병합).
    stems = [s for s in reversed(allStems) if s not in done or s == newest]
    if args.max_stems is not None:
        stems = stems[: args.max_stems]
    print(f"[segmentsBackfill] 시드 {frame.height}행 · done {len(done)} stem · 남은 {len(stems)}", flush=True)

    tickers = loadTickers()
    cikToTicker = dict(zip(tickers["cik"].to_list(), tickers["ticker"].to_list()))
    tmp = Path(tempfile.mkdtemp())
    t0 = time.time()
    for i, stem in enumerate(stems, start=1):
        try:
            zp = downloadNotesBulk(stem, force=stem == newest)
        except Exception as e:  # noqa: BLE001 (미배포 stem 등 · done 마킹 안 함 = 다음 run 재시도)
            print(f"  skip {stem}: {repr(e)[:60]}", flush=True)
            continue
        rows = segmentRowsFromZip(zp, cikToTicker, verbose=True)
        fresh = pl.DataFrame(rows, schema=SEGMENTS_COLS) if rows else pl.DataFrame(schema=SEGMENTS_COLS)
        # 역순(최신 우선) 순회라 frame(더 최신 stem 누적본)이 우선. 단 최신 stem 재처리는 fresh 가 갱신본.
        pair = [fresh, frame] if stem == newest else [frame, fresh]
        frame = (
            pl.concat(pair, how="vertical_relaxed")
            .unique(subset=_KEYS, keep="first")
            .sort(["stockCode", "period", "segment"])
        )
        done.add(stem)
        if not args.keep_zips:
            zp.unlink(missing_ok=True)
        for name, df in ((_NAME, frame), (_DONE, pl.DataFrame({"stem": sorted(done)}))):
            out = tmp / f"{name}.parquet"
            df.write_parquet(out, compression="zstd")
            retryHfCall(
                api.upload_file,
                path_or_fileobj=str(out),
                path_in_repo=f"{_REL}/{name}.parquet",
                repo_id=_REPO,
                repo_type="dataset",
                commit_message=f"segments 백필: {stem} 반영 {df.height}행",
            )
        print(
            f"[segmentsBackfill] {i}/{len(stems)} {stem}: 누적 {frame.height}행 "
            f"({frame['stockCode'].n_unique()}종목, {time.time() - t0:.0f}s)",
            flush=True,
        )
    print(f"DONE {len(stems)} stem ({time.time() - t0:.0f}s)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
