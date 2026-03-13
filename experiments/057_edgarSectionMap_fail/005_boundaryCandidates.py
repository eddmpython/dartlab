"""
실험 ID: 057-005
실험명: EDGAR form별 canonical boundary 후보 추출

목적:
- 10-K, 10-Q, 20-F별 canonical topic 초안을 만든다.
- title frequency와 filing coverage를 기준으로 form-native topic 집합을 도출한다.

가설:
1. 10-K는 item title 세트가 높은 filing coverage로 안정적으로 반복된다.
2. 20-F도 표본이 늘면 유사한 item teacher set을 만들 수 있다.
3. 10-Q는 현재 Full Document만 안정적이라 별도 구조화 이전에는 단일 topic으로 두는 편이 안전하다.

방법:
1. data/edgar/docs/*.parquet를 읽는다.
2. filing 단위 중복을 제거한 뒤 form_type, section_title별 filing 수와 ticker 수를 센다.
3. form_type별 filing coverage 50% 이상 title을 canonical boundary 후보로 저장한다.
4. 결과를 output/formTopicDrafts.json에 기록한다.

결과 (실험 후 작성):
- 실행 후 갱신

결론:
- 실행 후 갱신

실험일: 2026-03-12
"""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from dartlab import config


MIN_FILING_COVERAGE = 0.5


def docsDir() -> Path:
    return Path(config.dataDir) / "edgar" / "docs"


def outPath() -> Path:
    return Path(__file__).resolve().parent / "output" / "formTopicDrafts.json"


def loadRows() -> pl.DataFrame:
    frames: list[pl.DataFrame] = []
    for filePath in sorted(docsDir().glob("*.parquet")):
        frames.append(
            pl.read_parquet(
                filePath,
                columns=["accession_no", "form_type", "section_title"],
            ).with_columns(pl.lit(filePath.stem).alias("ticker"))
        )
    if not frames:
        return pl.DataFrame()
    return pl.concat(frames, how="vertical")


def main() -> None:
    df = loadRows()
    if df.is_empty():
        raise RuntimeError("EDGAR docs parquet 없음")

    filingDf = df.unique(subset=["accession_no", "form_type", "section_title", "ticker"])
    formTotals = filingDf.group_by("form_type").agg(pl.col("accession_no").n_unique().alias("total_filings"))
    titleStats = (
        filingDf.group_by(["form_type", "section_title"])
        .agg(
            pl.col("accession_no").n_unique().alias("filings"),
            pl.col("ticker").n_unique().alias("tickers"),
        )
        .join(formTotals, on="form_type", how="left")
        .with_columns((pl.col("filings") / pl.col("total_filings")).alias("filing_coverage"))
        .sort(["form_type", "filings", "section_title"], descending=[False, True, False])
    )

    drafts: dict[str, list[dict[str, object]]] = {}
    for formType in titleStats["form_type"].unique().to_list():
        subset = titleStats.filter(
            (pl.col("form_type") == formType)
            & (pl.col("filing_coverage") >= MIN_FILING_COVERAGE)
        )
        drafts[str(formType)] = subset.select(
            ["section_title", "filings", "tickers", "filing_coverage"]
        ).to_dicts()

    out = outPath()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(drafts, ensure_ascii=False, indent=2), encoding="utf-8")

    print("=" * 72)
    print("057-005 canonical boundary candidates")
    print("=" * 72)
    print(f"path={out}")
    for formType, rows in drafts.items():
        print()
        print(f"[{formType}] candidates={len(rows)}")
        for row in rows[:15]:
            print(row)


if __name__ == "__main__":
    main()
