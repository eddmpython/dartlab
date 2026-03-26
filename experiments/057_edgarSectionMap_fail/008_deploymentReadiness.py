"""
실험 ID: 057-008
실험명: EDGAR sections 파이프라인 배치 준비도 점검

목적:
- 현재까지 수집된 로컬 EDGAR docs에 대해 sections 파이프라인이 무에러로 동작하는지 확인한다.
- 패키지 배치 가능한 최소 수준인지 판단한다.

가설:
1. source-native sections 파이프라인은 현재 로컬 docs 전 범위에서 동작한다.
2. 주요 남은 갭은 실행 에러보다 10-Q 구조화 품질이다.

방법:
1. data/edgar/docs/*.parquet를 순회한다.
2. 각 ticker에 대해 `dartlab.providers.edgar.docs.sections.sections()`를 호출한다.
3. shape, period 수, topic 수, 에러 유무를 기록한다.

결과 (실험 후 작성):
- 실행 후 갱신

결론:
- 실행 후 갱신

실험일: 2026-03-12
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

from dartlab import config
from dartlab.providers.edgar.docs.sections import sections


def main() -> None:
    docsDir = Path(config.dataDir) / "edgar" / "docs"
    files = sorted(docsDir.glob("*.parquet"))
    if not files:
        raise RuntimeError("EDGAR docs parquet 없음")

    records: list[dict[str, object]] = []
    for filePath in files:
        ticker = filePath.stem
        try:
            df = sections(ticker)
            if df is None:
                records.append({
                    "ticker": ticker,
                    "status": "empty",
                    "rows": 0,
                    "periods": 0,
                })
                continue
            records.append({
                "ticker": ticker,
                "status": "ok",
                "rows": df.height,
                "periods": len(df.columns) - 1,
            })
        except (OSError, ValueError, RuntimeError) as e:
            records.append({
                "ticker": ticker,
                "status": "error",
                "rows": 0,
                "periods": 0,
                "reason": str(e),
            })

    result = pl.DataFrame(records).sort(["status", "ticker"])
    print("=" * 72)
    print("057-008 deployment readiness")
    print("=" * 72)
    print(result)
    print()
    print(result.group_by("status").len().sort("status"))


if __name__ == "__main__":
    main()
