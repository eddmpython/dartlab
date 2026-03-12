"""
실험 ID: 056-011
실험명: fine map projection 점수화

목적:
- coarse 연도 사업보고서가 fine canonical boundary map에 얼마나 안정적으로 투영되는지 정량화한다.

가설:
1. 2021 삼성전자 사업보고서는 2022 fine map의 상당 부분을 chapter 단위로 수용할 수 있다.
2. chapter별 projection score를 만들면 우선 보완이 필요한 장을 식별할 수 있다.

방법:
1. 삼성전자 2021/2022 사업보고서 title을 비교한다.
2. 2022 fine boundary 기준으로 2021에 없는 항목 비율을 chapter별로 계산한다.
3. score = 1 - missing_ratio 로 정의한다.

결과 (실험 후 작성):

- I: 0.80
- II: 0.00
- III: 0.62
- V: 0.00
결론:

- 2021 coarse 보고서를 2022 fine map에 그대로 exact 투영하면 II/V/XI/XII 장은 사실상 실패한다.
- 즉 coarse-to-fine projection에는 chapter 내부의 상위-하위 boundary 관계를 명시하는 별도 규칙 계층이 필요하다.
실험일: 2026-03-11
"""

from __future__ import annotations

import re
from pathlib import Path

import polars as pl


CHAPTER_RE = re.compile(r"^\s*([IVX]{1,5})\.\s*(.*)$")


def load_titles(year: str) -> list[str]:
    root = Path(__file__).resolve().parents[2]
    path = root / "data" / "dart" / "docs" / "005930.parquet"
    df = pl.read_parquet(path).with_columns(pl.col("year").cast(pl.Utf8))
    return (
        df.filter((pl.col("year") == year) & pl.col("report_type").str.contains("사업보고서"))
        .sort("section_order")
        .get_column("section_title")
        .to_list()
    )


def chapter_map(titles: list[str]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    current: str | None = None
    for title in titles:
        stripped = title.strip()
        m = CHAPTER_RE.match(stripped)
        if m:
            chapter = m.group(1)
            current = chapter
            result.setdefault(chapter, [])
            continue
        if current is not None:
            result.setdefault(current, []).append(stripped)
    return result


def main() -> None:
    coarse = chapter_map(load_titles("2021"))
    fine = chapter_map(load_titles("2022"))
    print("=" * 72)
    print("056-011 fine map projection score")
    print("=" * 72)
    for chapter in sorted(fine.keys()):
        fine_set = set(fine[chapter])
        if not fine_set:
            continue
        coarse_set = set(coarse.get(chapter, []))
        missing_ratio = len(fine_set - coarse_set) / len(fine_set)
        score = 1 - missing_ratio
        print(f"{chapter}: score={score:.2f} fineCount={len(fine_set)} missing={len(fine_set - coarse_set)}")


if __name__ == "__main__":
    main()
