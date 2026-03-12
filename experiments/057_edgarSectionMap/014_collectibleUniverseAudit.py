"""
실험 ID: 057-014
실험명: EDGAR docs collectible universe audit

목적:
- listed ticker universe와 실제 docs collectible universe의 차이를 정량화한다.
- ticker 중복, foreign issuer 40-F, true no filing을 분리해 수집 기준을 확정한다.

가설:
1. exchange listed ticker universe는 issuer 단위로 보면 중복이 많다.
2. `40-F`를 포함하지 않으면 foreign issuer 일부가 false negative로 빠진다.
3. docs 배치는 ticker가 아니라 issuer-deduped collectible universe가 맞다.

방법:
1. listedUniverse.parquet에서 exchange listed row 수와 unique CIK 수를 계산한다.
2. recent progress에서 실패 이유를 집계한다.
3. sample foreign issuer의 regular forms를 확인한다.

결과 (실험 후 작성):
- 실행 후 갱신

결론:
- 실행 후 갱신

실험일: 2026-03-12
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import polars as pl

from dartlab import config


def main() -> None:
    dataRoot = Path(config.dataDir)
    listed = pl.read_parquet(dataRoot / "edgar" / "listedUniverse.parquet").filter(pl.col("is_exchange_listed"))
    progressPath = Path(__file__).resolve().parent / "output" / "downloadFirst2000.progress.jsonl"

    reasons = Counter()
    status = Counter()
    if progressPath.exists():
        for line in progressPath.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            status[str(record.get("status") or "")] += 1
            if record.get("status") == "failed":
                reasons[str(record.get("failure_kind") or "unclassified")] += 1

    print("=" * 72)
    print("057-014 collectible universe audit")
    print("=" * 72)
    print(f"exchange listed rows: {listed.height}")
    print(f"exchange listed unique cik: {listed['cik'].n_unique()}")
    print()
    print("status:", dict(status))
    print("failure kinds:", dict(reasons))


if __name__ == "__main__":
    main()
