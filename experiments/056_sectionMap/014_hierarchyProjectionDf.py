"""
실험 ID: 056-014
실험명: hierarchy projection DataFrame 검증

목적:
- coarse/fine boundary 관계를 Polars DataFrame 스키마로 표현할 수 있는지 확인한다.

가설:
1. chapter/coarseBoundary/fineBoundary/projectionKind 구조로 hierarchy를 DataFrame에 담을 수 있다.
2. 이 스키마는 이후 canonical map prototype의 기반이 된다.

방법:
1. 삼성전자 2021/2022 사업보고서 title을 비교한다.
2. fine-only boundary를 chapter별로 묶는다.
3. Polars DataFrame으로 투영 관계를 생성한다.

결과 (실험 후 작성):

- 결과 shape: `(34, 4)`
- 스키마: `chapter / coarseBoundary / fineBoundary / projectionKind`
- coarse/fine boundary 관계를 Polars DataFrame으로 직접 표현할 수 있음이 확인되었다.
- 이는 canonical map을 코드 레벨에서 DataFrame 중심으로 다루는 설계가 가능하다는 의미다.
결론:

- coarse/fine boundary 관계를 Polars DataFrame으로 직접 표현할 수 있음이 확인되었다.
- 이는 canonical map을 코드 레벨에서 DataFrame 중심으로 다루는 설계가 가능하다는 의미다.
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
        match = CHAPTER_RE.match(stripped)
        if match:
            chapter = match.group(1)
            current = chapter
            result.setdefault(chapter, [])
            continue
        if current is not None:
            result.setdefault(current, []).append(stripped)
    return result


def main() -> None:
    coarse = chapter_map(load_titles("2021"))
    fine = chapter_map(load_titles("2022"))
    rows: list[dict[str, str]] = []
    for chapter in sorted(fine.keys()):
        coarse_items = coarse.get(chapter, [])
        coarse_label = " | ".join(coarse_items) if coarse_items else "(coarse missing)"
        for fine_item in fine.get(chapter, []):
            projection_kind = "exact" if fine_item in coarse_items else "fine_only"
            rows.append(
                {
                    "chapter": chapter,
                    "coarseBoundary": coarse_label,
                    "fineBoundary": fine_item,
                    "projectionKind": projection_kind,
                }
            )

    df = pl.DataFrame(rows)
    print("=" * 72)
    print("056-014 hierarchy projection DataFrame")
    print("=" * 72)
    print(df.shape)
    print(df.head(20))


if __name__ == "__main__":
    main()
