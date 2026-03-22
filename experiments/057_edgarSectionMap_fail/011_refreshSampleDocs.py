"""
실험 ID: 057-011
실험명: 10-Q split 적용 샘플 docs 갱신

목적:
- 새 10-Q split 로직을 로컬 대표 샘플에 반영한다.
- 실험과 패키지 sections 출력이 최신 구조를 쓰도록 기준 샘플을 맞춘다.

가설:
1. AAPL, AMZN, A, AA 같은 대표 샘플을 다시 수집하면 10-Q가 더 이상 Full Document만 나오지 않는다.

방법:
1. 지정 ticker를 `fetchEdgarDocs(..., sinceYear=2009)`로 다시 수집한다.
2. 재수집 후 10-Q section title 분포를 확인한다.

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
from dartlab.engines.company.edgar.docs.fetch import fetchEdgarDocs

TARGETS = ["AAPL", "AMZN", "A", "AA"]


def main() -> None:
    docsDir = Path(config.dataDir) / "edgar" / "docs"
    docsDir.mkdir(parents=True, exist_ok=True)

    for ticker in TARGETS:
        fetchEdgarDocs(ticker, docsDir / f"{ticker}.parquet", sinceYear=2009, showProgress=False)

    for ticker in TARGETS:
        df = pl.read_parquet(docsDir / f"{ticker}.parquet")
        qDf = df.filter(pl.col("form_type") == "10-Q")
        print("=" * 72)
        print(ticker)
        print(qDf.group_by("section_title").len().sort("len", descending=True))


if __name__ == "__main__":
    main()
