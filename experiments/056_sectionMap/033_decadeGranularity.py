"""
실험 ID: 056-033
실험명: section 세분화 강도 전기간 연도대 분석

목적:
- 사업보고서 section 수평화에서 세분화가 실제로 어떤 시기에 강하게 발생하는지,
  전기간 인접연도 기준으로 정량화한다.

가설:
1. 2020년대 구간에서 평균 세분화 강도가 가장 높다.
2. 2000/2010년대는 양식 개편 영향으로 증가/감소가 혼재한다.

방법:
1. data/dart/docs/*.parquet에서 연간 사업보고서만 사용한다.
2. 회사별 인접 연도 페어(prevYear, currYear)를 만들고 leaf section set을 비교한다.
3. 세분화 지표(delta, fineOnly, fineOnlyRatio)를 계산한다.
4. currYear 기준 decade(2000s/2010s/2020s)로 집계한다.

결과 (실험 후 작성):
- filtered_pairs: 671
- decade별 집계:
  - 2000s: meanDelta -1.289, weightedFineOnlyRatio 0.094972, pos/zero/neg=9/12/17
  - 2010s: meanDelta -0.530, weightedFineOnlyRatio 0.055147, pos/zero/neg=15/76/9
  - 2020s: meanDelta 2.201, weightedFineOnlyRatio 0.106890, pos/zero/neg=208/257/68

결론:
- 세분화는 모든 시기에 균등하지 않고, 2020년대에서 가장 강하게 증가한다.
- 2000/2010년대는 양식 개편 영향으로 증가/유지가 혼재하며 순증이 작거나 음수일 수 있다.
- 운영 수평화는 2020년대 세분화 패턴을 기준으로 하고, 구연도는 projection 계층으로 흡수하는 접근이 타당하다.

실험일: 2026-03-11
"""

from __future__ import annotations

import re
from pathlib import Path

import polars as pl


CHAPTER_RE = re.compile(r"^\s*([IVX]{1,5})\.\s*(.*)$")


def root_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def docs_dir() -> Path:
    return root_dir() / "data" / "dart" / "docs"


def annual_leaf_set(df: pl.DataFrame, year: int | str) -> set[str]:
    report = df.filter(pl.col("year") == year).sort("section_order")
    titles = report.get_column("section_title").to_list()

    current_chapter = ""
    out: set[str] = set()
    for raw in titles:
        title = (raw or "").strip()
        if not title:
            continue
        chapter_match = CHAPTER_RE.match(title)
        if chapter_match:
            current_chapter = chapter_match.group(1)
            continue
        if not current_chapter:
            continue
        out.add(title)
    return out


def build_pair_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in sorted(docs_dir().glob("*.parquet")):
        df = pl.read_parquet(path)
        annual = df.filter(pl.col("report_type").str.contains("사업보고서"))
        if annual.height == 0:
            continue

        years = sorted(set(annual.get_column("year").to_list()))
        if len(years) < 2:
            continue

        year_to_set = {year: annual_leaf_set(annual, year) for year in years}
        for idx in range(1, len(years)):
            prev_year = years[idx - 1]
            curr_year = years[idx]
            prev_set = year_to_set[prev_year]
            curr_set = year_to_set[curr_year]
            if len(prev_set) == 0 or len(curr_set) == 0:
                continue

            fine_only = curr_set - prev_set
            delta = len(curr_set) - len(prev_set)
            decade_num = (int(curr_year) // 10) * 10
            rows.append(
                {
                    "stockCode": path.stem,
                    "prevYear": int(prev_year),
                    "currYear": int(curr_year),
                    "decade": f"{decade_num}s",
                    "prevCount": len(prev_set),
                    "currCount": len(curr_set),
                    "delta": delta,
                    "deltaRatio": delta / len(prev_set),
                    "fineOnly": len(fine_only),
                    "fineOnlyRatio": len(fine_only) / len(curr_set),
                }
            )
    return rows


def main() -> None:
    pairs = pl.DataFrame(build_pair_rows())
    summary = (
        pairs.group_by("decade")
        .agg(
            pl.len().alias("pairs"),
            pl.col("delta").mean().alias("meanDelta"),
            pl.col("delta").median().alias("medianDelta"),
            pl.col("deltaRatio").mean().alias("meanDeltaRatio"),
            pl.col("deltaRatio").median().alias("medianDeltaRatio"),
            pl.col("fineOnly").mean().alias("meanFineOnly"),
            pl.col("fineOnlyRatio").mean().alias("meanFineOnlyRatio"),
            (pl.col("fineOnly").sum() / pl.col("currCount").sum()).alias("weightedFineOnlyRatio"),
            (pl.col("delta") > 0).sum().alias("posCount"),
            (pl.col("delta") == 0).sum().alias("zeroCount"),
            (pl.col("delta") < 0).sum().alias("negCount"),
        )
        .sort("decade")
    )

    print("=" * 72)
    print("056-033 전기간 연도대 세분화 강도")
    print("=" * 72)
    print(f"filtered_pairs={pairs.height}")
    print(summary)


if __name__ == "__main__":
    main()
