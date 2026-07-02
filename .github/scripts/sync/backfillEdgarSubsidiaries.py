"""EDGAR 자회사(EX-21) 백필 runner. 청크 순회 + HF 시드 리줌 + 체크포인트 발행 (proxy runner 동형).

buildEdgarSubsidiaries 를 청크로 반복 호출해 subsidiaries.parquet 을 edgar/scan/report/ 에 누적 발행.
리줌 = subsidiariesDone.parquet(stockCode+year, 0행 회사 포함). 새 10-K(더 최신 연도) 제출 시 재수집은
연 1회 10-K 주기라 done 의 year 와 최신 10-K 연도 비교로 무효화.

실행::

    uv run python -X utf8 .github/scripts/sync/backfillEdgarSubsidiaries.py [--chunk 500] [--max-chunks N]
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
_NAME = "subsidiaries"
_DONE = "subsidiariesDone"


def _dl(api, name: str, tok: str) -> pl.DataFrame | None:
    """HF 기존 파일 로드(시드). 부재 시 None."""
    from huggingface_hub import hf_hub_download

    try:
        fp = hf_hub_download(_REPO, f"{_REL}/{name}.parquet", repo_type="dataset", token=tok)
        return pl.read_parquet(fp)
    except Exception:  # noqa: BLE001 (최초 실행)
        return None


def main() -> int:
    """청크 순회로 EX-21 자회사 수집·발행. done 마커 리줌."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--chunk", type=int, default=500)
    ap.add_argument("--max-chunks", type=int, default=None)
    args = ap.parse_args()

    tok = os.environ.get("HF_TOKEN", "").strip()
    if not tok:
        print("[ex21Backfill] HF_TOKEN 없음", flush=True)
        return 1
    from huggingface_hub import HfApi

    import dartlab.scan.builders.edgar.report.ex21Build as mod
    from dartlab.core.hfRetry import retryHfCall

    api = HfApi(token=tok)
    seeded = _dl(api, _NAME, tok)
    frame = seeded if seeded is not None else pl.DataFrame(schema=mod.SUBSIDIARIES_COLS)
    doneDf = _dl(api, _DONE, tok)
    done: set[str] = set(doneDf["stockCode"].to_list()) if doneDf is not None else set()
    print(f"[ex21Backfill] 시드: done {len(done)}사 · {frame.height}행", flush=True)

    tmp = Path(tempfile.mkdtemp())
    chunks = 0
    t0 = time.time()
    while args.max_chunks is None or chunks < args.max_chunks:
        rows = mod.buildEdgarSubsidiaries(doneTickers=done, maxCompanies=args.chunk, verbose=True)
        processed = rows.pop("processedTickers")
        if not processed:
            print(f"[ex21Backfill] 전 회사 처리 완료 ({time.time() - t0:.0f}s)", flush=True)
            break
        done |= set(processed)
        fresh = (
            pl.DataFrame(rows["subsidiaries"], schema=mod.SUBSIDIARIES_COLS)
            if rows["subsidiaries"]
            else pl.DataFrame(schema=mod.SUBSIDIARIES_COLS)
        )
        frame = (
            pl.concat([fresh, frame], how="vertical_relaxed")
            .unique(subset=["stockCode", "year", "name"], keep="first")
            .sort(["stockCode", "year", "name"])
        )
        for name, df in ((_NAME, frame), (_DONE, pl.DataFrame({"stockCode": sorted(done)}))):
            out = tmp / f"{name}.parquet"
            df.write_parquet(out, compression="zstd")
            retryHfCall(
                api.upload_file,
                path_or_fileobj=str(out),
                path_in_repo=f"{_REL}/{name}.parquet",
                repo_id=_REPO,
                repo_type="dataset",
                commit_message=f"ex21 백필: {name} {df.height}행",
            )
        chunks += 1
        print(
            f"[ex21Backfill] 청크 {chunks}: done {len(done)}사 · {frame.height}행 "
            f"({frame['stockCode'].n_unique()}종목, {time.time() - t0:.0f}s)",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
