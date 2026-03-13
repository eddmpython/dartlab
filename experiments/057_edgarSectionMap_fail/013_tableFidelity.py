"""
실험 ID: 057-013
실험명: EDGAR table markdown fidelity 점검

목적:
- 대량 수집이 늘어나는 동안 section_content 안의 markdown table이 실제로 보존되는지 점검한다.
- form_type별 table-containing section 비율과 table line 비중을 측정한다.

가설:
1. 현재 fetch 파이프라인은 table-heavy section에서도 markdown table을 유지한다.
2. 10-Q 재구조화 이후에도 재무표가 들어 있는 섹션은 table line 비중이 높게 남는다.

방법:
1. data/edgar/docs/*.parquet를 전수 스캔한다.
2. section_content에서 markdown table line(`|`) 존재 여부를 계산한다.
3. form_type별 section 수, table section 수, table line 수를 집계한다.

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


def _tableLineCount(text: str) -> int:
    return sum(1 for line in (text or "").splitlines() if line.strip().startswith("|"))


def main() -> None:
    docsDir = Path(config.dataDir) / "edgar" / "docs"
    files = sorted(docsDir.glob("*.parquet"))
    if not files:
        raise RuntimeError("EDGAR docs parquet 없음")

    frames: list[pl.DataFrame] = []
    for filePath in files:
        frames.append(
            pl.read_parquet(filePath, columns=["form_type", "section_content"]).with_columns(
                pl.lit(filePath.stem).alias("ticker")
            )
        )

    df = pl.concat(frames, how="vertical")
    df = df.with_columns(
        pl.Series(
            "table_lines",
            [_tableLineCount(str(text)) for text in df["section_content"].to_list()],
        )
    ).with_columns(
        (pl.col("table_lines") > 0).alias("has_table"),
    )

    summary = (
        df.group_by("form_type")
        .agg(
            pl.len().alias("sections"),
            pl.col("ticker").n_unique().alias("tickers"),
            pl.col("has_table").sum().alias("table_sections"),
            pl.col("table_lines").sum().alias("table_lines"),
        )
        .with_columns(
            (pl.col("table_sections") / pl.col("sections")).alias("table_section_ratio")
        )
        .sort("form_type")
    )

    print("=" * 72)
    print("057-013 table markdown fidelity")
    print("=" * 72)
    print(summary)


if __name__ == "__main__":
    main()
