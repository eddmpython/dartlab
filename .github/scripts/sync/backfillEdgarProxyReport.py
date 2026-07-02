"""EDGAR proxy 거버넌스 4표 백필 runner. 청크 순회 + HF 시드 리줌 + 체크포인트 발행.

buildEdgarProxyReport(오케스트레이션)를 청크로 반복 호출해 감사보수·개별임원보수·실질지분·이사회구성
parquet 을 edgar/scan/report/ 에 누적 발행한다. 리줌 = proxyDone.parquet(처리 마킹, 0행 회사 포함)가
시드라 죽어도 재실행이 남은 회사만 처리(backfillEmployee 동형). 회사별 최신 DEF 14A 1건.

실행::

    uv run python -X utf8 .github/scripts/sync/backfillEdgarProxyReport.py [--chunk 400] [--max-chunks N]
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import polars as pl

_REPO = "eddmpython/dartlab-data"
_REL = "edgar/scan/report"
_TABLES = {
    "auditFees": "AUDIT_FEES_COLS",
    "execPayIndividual": "EXEC_PAY_COLS",
    "ownership": "OWNERSHIP_COLS",
    "board": "BOARD_COLS",
}
_DONE = "proxyDone.parquet"
# 재수집 dedup 키. 같은 키의 신규(fresh)가 구값을 대체(정정 proxy 반영).
_KEYS = {
    "auditFees": ["stockCode", "year"],
    "execPayIndividual": ["stockCode", "year", "name"],
    "ownership": ["stockCode", "year", "holder"],
    "board": ["stockCode", "year"],
}


def _dl(api, name: str, tok: str) -> pl.DataFrame | None:
    """HF 기존 파일 로드(시드). 부재 시 None."""
    from huggingface_hub import hf_hub_download

    try:
        fp = hf_hub_download(_REPO, f"{_REL}/{name}", repo_type="dataset", token=tok)
        return pl.read_parquet(fp)
    except Exception:  # noqa: BLE001 (최초 실행)
        return None


def _publish(api, frames: dict[str, pl.DataFrame], done: pl.DataFrame, tmp: Path, tok: str) -> None:
    """3표 + done 마커를 HF 로 발행 (retry)."""
    from dartlab.core.hfRetry import retryHfCall

    for name, df in {**frames, _DONE.replace(".parquet", ""): done}.items():
        out = tmp / f"{name}.parquet"
        df.write_parquet(out, compression="zstd")
        retryHfCall(
            api.upload_file,
            path_or_fileobj=str(out),
            path_in_repo=f"{_REL}/{name}.parquet",
            repo_id=_REPO,
            repo_type="dataset",
            commit_message=f"proxy 백필: {name} {df.height}행",
        )
    print("  publish: " + " · ".join(f"{k}={v.height}" for k, v in frames.items()), flush=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chunk", type=int, default=400, help="청크당 회사 수(체크포인트 간격)")
    ap.add_argument("--max-chunks", type=int, default=None, help="이번 run 청크 상한(CI 예산)")
    args = ap.parse_args()

    tok = os.environ.get("HF_TOKEN", "").strip()
    if not tok:
        print("[proxyBackfill] HF_TOKEN 없음", flush=True)
        return 1
    from huggingface_hub import HfApi

    import dartlab.scan.builders.edgar.report.proxyBuild as pb

    api = HfApi(token=tok)
    schemas = {k: getattr(pb, v) for k, v in _TABLES.items()}
    frames = {}
    for k, sc in schemas.items():
        seeded = _dl(api, f"{k}.parquet", tok)
        frames[k] = seeded if seeded is not None else pl.DataFrame(schema=sc)  # polars 진리값 불가(or 금지)
    # done 마커 = stockCode+filingDate. 새 proxy(더 최신 filingDate) 제출 시 자동 무효화 → 주기 재수집.
    import dartlab.config as _cfg

    metaFp = Path(_cfg.dataDir) / "edgar" / "allFilings" / "recent.parquet"
    meta = pl.read_parquet(metaFp, columns=["stockCode", "form", "filingDate"]).filter(pl.col("form") == "DEF 14A")
    latestFd: dict[str, str] = dict(
        meta.sort("filingDate", descending=True)
        .group_by("stockCode")
        .head(1)
        .select(["stockCode", "filingDate"])
        .iter_rows()
    )
    doneDf = _dl(api, _DONE, tok)
    doneFd: dict[str, str] = {}
    if doneDf is not None:
        if "filingDate" in doneDf.columns:
            doneFd = dict(doneDf.select(["stockCode", "filingDate"]).iter_rows())
        else:  # 구스키마(stockCode only) = 현재 최신 proxy 로 처리된 것 (백필 당시 최신)
            doneFd = {tk: latestFd.get(tk, "") for tk in doneDf["stockCode"].to_list()}
    done: set[str] = {tk for tk, fd in doneFd.items() if fd >= latestFd.get(tk, "")}
    print(
        f"[proxyBackfill] 시드: done {len(done)}사(마커 {len(doneFd)}, 신규 proxy 무효화 {len(doneFd) - len(done)}) · "
        + " · ".join(f"{k}={v.height}행" for k, v in frames.items()),
        flush=True,
    )

    import tempfile

    tmp = Path(tempfile.mkdtemp())
    chunks = 0
    t0 = time.time()
    while args.max_chunks is None or chunks < args.max_chunks:
        rows = pb.buildEdgarProxyReport(doneTickers=done, maxCompanies=args.chunk, verbose=True)
        processed = rows.pop("processedTickers")
        if not processed:
            print(f"[proxyBackfill] 전 회사 처리 완료 ({time.time() - t0:.0f}s)", flush=True)
            break
        done |= set(processed)
        for tk in processed:
            doneFd[tk] = latestFd.get(tk, "")
        for k in frames:
            fresh = pl.DataFrame(rows[k], schema=schemas[k]) if rows[k] else pl.DataFrame(schema=schemas[k])
            frames[k] = (
                pl.concat([fresh, frames[k]], how="vertical_relaxed")
                .unique(subset=_KEYS[k], keep="first")  # fresh 우선(정정 proxy 가 구값 대체)
                .sort(["stockCode", "year"])
            )
        doneOut = pl.DataFrame({"stockCode": sorted(doneFd), "filingDate": [doneFd[t] for t in sorted(doneFd)]})
        _publish(api, frames, doneOut, tmp, tok)
        chunks += 1
        print(f"[proxyBackfill] 청크 {chunks} 완료: 누적 done {len(done)}사 ({time.time() - t0:.0f}s)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
