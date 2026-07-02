"""EDGAR proxy 거버넌스 4표 히스토리 백필 runner. 전연도 DEF 14A(2015~) 시계열 채움.

최신 1건만 처리한 본 백필(backfillEdgarProxyReport)과 달리 회사별 *전체* DEF 14A 를 순회해
감사보수·개별임원보수·실질지분·이사회구성 4표의 과거 연도를 채운다. DART 거버넌스 시계열의 US 대칭.

리줌 = proxyHistoryDone.parquet(accessionNo 단위). 신규분(최신 proxy)은 주간 edgarProxySync 가
담당하므로 본 runner 는 1회성 히스토리 전용. 같은 키 충돌은 기존 발행본(최신 proxy 유래)이 우선
(seed-wins). run 내부는 filingDate 내림차순이라 최신 proxy 값이 먼저 앉는다(keep=first).

실행::

    uv run python -X utf8 .github/scripts/sync/backfillEdgarProxyHistory.py [--checkpoint 1200] [--max-docs N]
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
_TABLES = {
    "auditFees": "AUDIT_FEES_COLS",
    "execPayIndividual": "EXEC_PAY_COLS",
    "ownership": "OWNERSHIP_COLS",
    "board": "BOARD_COLS",
}
_DONE = "proxyHistoryDone"
_KEYS = {
    "auditFees": ["stockCode", "year"],
    "execPayIndividual": ["stockCode", "year", "name"],
    "ownership": ["stockCode", "year", "holder"],
    "board": ["stockCode", "year"],
}


def _dl(api, name: str, tok: str) -> pl.DataFrame | None:
    """HF 기존 파일 로드(시드). 부재 시 None."""
    from huggingface_hub import hf_hub_download

    from dartlab.core.hfRetry import retryHfCall

    try:
        fp = retryHfCall(hf_hub_download, _REPO, f"{_REL}/{name}.parquet", repo_type="dataset", token=tok)
        return pl.read_parquet(fp)
    except Exception:  # noqa: BLE001 (최초 실행)
        return None


def _publish(api, frames: dict[str, pl.DataFrame], doneAcc: set[str], tmp: Path) -> None:
    """4표 + history done 마커 발행(retry)."""
    from dartlab.core.hfRetry import retryHfCall

    doneDf = pl.DataFrame({"accessionNo": sorted(doneAcc)})
    for name, df in {**frames, _DONE: doneDf}.items():
        out = tmp / f"{name}.parquet"
        df.write_parquet(out, compression="zstd")
        retryHfCall(
            api.upload_file,
            path_or_fileobj=str(out),
            path_in_repo=f"{_REL}/{name}.parquet",
            repo_id=_REPO,
            repo_type="dataset",
            commit_message=f"proxy 히스토리 백필: {name} {df.height}행",
        )
    print("  publish: " + " · ".join(f"{k}={v.height}" for k, v in frames.items()), flush=True)


def main() -> int:
    """전연도 DEF 14A 순회 → 4표 히스토리 누적 발행. accessionNo 리줌."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", type=int, default=1200, help="발행 간격(문서 수)")
    ap.add_argument("--max-docs", type=int, default=None, help="이번 run 처리 상한(스모크)")
    args = ap.parse_args()

    tok = os.environ.get("HF_TOKEN", "").strip()
    if not tok:
        print("[proxyHistory] HF_TOKEN 없음", flush=True)
        return 1
    import httpx
    from huggingface_hub import HfApi

    import dartlab.config as _cfg
    import dartlab.scan.builders.edgar.report.proxyBuild as pb
    from dartlab.gather.edgar.allFilingsContent import getFilingBody

    api = HfApi(token=tok)
    schemas = {k: getattr(pb, v) for k, v in _TABLES.items()}
    frames: dict[str, pl.DataFrame] = {}
    for k, sc in schemas.items():
        seeded = _dl(api, k, tok)
        frames[k] = seeded if seeded is not None else pl.DataFrame(schema=sc)

    metaFp = Path(_cfg.dataDir) / "edgar" / "allFilings" / "recent.parquet"
    meta = (
        pl.read_parquet(metaFp, columns=["stockCode", "form", "filingDate", "url", "accessionNo"])
        .filter(pl.col("form") == "DEF 14A")
        .sort("filingDate", descending=True)  # 최신 우선 = 같은 키는 최신 proxy 값이 먼저 앉음
    )
    doneDf = _dl(api, _DONE, tok)
    doneAcc: set[str] = set(doneDf["accessionNo"].to_list()) if doneDf is not None else set()
    # (선마킹 폐기 2026-07-03) 옛 proxyDone 기반 최신 proxy 선마킹은 그 회사들의 board 최신연도 행을
    # 영구 누락시켰다. 이제 proxyHistoryDone(accession 단위)만 리줌 정본이다.
    todo = meta.filter(~pl.col("accessionNo").is_in(sorted(doneAcc)))
    print(f"[proxyHistory] 전체 {meta.height} · done {len(doneAcc)} · 남은 {todo.height}", flush=True)

    tmp = Path(tempfile.mkdtemp())
    fresh: dict[str, list[dict]] = {k: [] for k in _TABLES}
    n = 0
    t0 = time.time()
    with httpx.Client(headers={"User-Agent": "dartlab research (contact: research@dartlab.io)"}) as client:
        for r in todo.iter_rows(named=True):
            if args.max_docs is not None and n >= args.max_docs:
                break
            n += 1
            acc = str(r["accessionNo"])
            body, status = getFilingBody(str(r["url"] or ""), client=client)
            if status == "ok" and body:
                try:
                    af, ep, ow, bd = pb.proxyRowsFromHtml(body, str(r["stockCode"]), str(r["filingDate"])[:4])
                    fresh["auditFees"].extend(af)
                    fresh["execPayIndividual"].extend(ep)
                    fresh["ownership"].extend(ow)
                    fresh["board"].extend(bd)
                except Exception as exc:  # noqa: BLE001 (개별 proxy 파싱 실패 격리)
                    print(f"  parse skip {r['stockCode']} {acc}: {exc!r}"[:120], flush=True)
            doneAcc.add(acc)
            if n % args.checkpoint == 0:
                for k in frames:
                    fdf = pl.DataFrame(fresh[k], schema=schemas[k]) if fresh[k] else pl.DataFrame(schema=schemas[k])
                    # seed(최신 proxy 유래)·run 내 최신 우선. fresh 는 filingDate 내림차순 누적이라 first=최신.
                    frames[k] = (
                        pl.concat([frames[k], fdf], how="vertical_relaxed")
                        .unique(subset=_KEYS[k], keep="first")
                        .sort(["stockCode", "year"])
                    )
                    fresh[k] = []
                print(f"[{n}/{todo.height}] {time.time() - t0:.0f}s", flush=True)
                _publish(api, frames, doneAcc, tmp)
            time.sleep(0.12)  # SEC fair-access(~8req/s)
    for k in frames:
        fdf = pl.DataFrame(fresh[k], schema=schemas[k]) if fresh[k] else pl.DataFrame(schema=schemas[k])
        frames[k] = (
            pl.concat([frames[k], fdf], how="vertical_relaxed")
            .unique(subset=_KEYS[k], keep="first")
            .sort(["stockCode", "year"])
        )
    _publish(api, frames, doneAcc, tmp)
    print(f"DONE {n}건 처리 ({time.time() - t0:.0f}s)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
