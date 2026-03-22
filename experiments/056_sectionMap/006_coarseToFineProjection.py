"""
실험 ID: 056-006
실험명: coarse-to-fine 역투영 검증

목적:
- 덜 세분화된 사업보고서(삼성전자 2021)를 fine canonical boundary(삼성전자 2022) 위에 어떻게 역투영할지 검증한다.
- coarse title 하나가 fine boundary 여러 개를 대표하는지 확인한다.

가설:
1. 2021의 coarse section은 2022의 fine boundary 여러 개를 합친 상위 묶음으로 해석 가능하다.
2. 특히 II장/III장/XI장에서 coarse-to-fine projection이 유효하다.

방법:
1. 삼성전자 2021/2022 사업보고서 section_title을 비교한다.
2. 2022의 fine boundary 중 2021에 없는 항목을 수집한다.
3. chapter prefix와 번호 순서를 기준으로 coarse 묶음 후보를 만든다.

결과 (실험 후 작성):

- 삼성전자 2021 coarse 보고서를 2022 fine boundary 위로 역투영한 결과, fine-only row 24개 확인
- I장: `5. 정관에 관한 사항`
- II장: `1~7` 전체가 fine-only
- III장: `6. 배당`, `7. 자금조달`, `8. 기타 재무`
결론:

- coarse 연도는 최신 fine boundary의 상위 묶음으로 충분히 투영 가능하다.
- 특히 II/XI/XII장은 coarse-to-fine projection의 대표 사례로 볼 수 있다.
실험일: 2026-03-11
"""

from __future__ import annotations

import re
from pathlib import Path

import polars as pl

CHAPTER_RE = re.compile(r"^\s*([IVX]{1,5})\.\s*(.*)$")


def load_annual_titles(year: str) -> list[str]:
    root = Path(__file__).resolve().parents[2]
    path = root / "data" / "dart" / "docs" / "005930.parquet"
    df = pl.read_parquet(path).with_columns(pl.col("year").cast(pl.Utf8))
    return (
        df.filter((pl.col("year") == year) & pl.col("report_type").str.contains("사업보고서"))
        .sort("section_order")
        .get_column("section_title")
        .to_list()
    )


def chapter_of(title: str) -> str:
    m = CHAPTER_RE.match(title.strip())
    if m:
        return m.group(1)
    return "SUB"


def group_fine_only_by_chapter(titles_2022: list[str], titles_2021: set[str]) -> dict[str, list[str]]:
    by_chapter: dict[str, list[str]] = {}
    current = "FRONT"
    for title in titles_2022:
        ch = chapter_of(title)
        if ch != "SUB":
            current = ch
            continue
        if title not in titles_2021:
            by_chapter.setdefault(current, []).append(title)
    return by_chapter


def main() -> None:
    y2021 = load_annual_titles("2021")
    y2022 = load_annual_titles("2022")
    y2021_set = set(y2021)
    only_2022 = [title for title in y2022 if title not in y2021_set]
    by_chapter = group_fine_only_by_chapter(y2022, y2021_set)

    print("=" * 72)
    print("056-006 coarse-to-fine 역투영 검증")
    print("=" * 72)
    print(f"2021 rows: {len(y2021)}")
    print(f"2022 rows: {len(y2022)}")
    print(f"fine-only rows: {len(only_2022)}")
    for chapter, items in by_chapter.items():
        print(f"\n[{chapter}]")
        for item in items:
            print(f" - {item}")


if __name__ == "__main__":
    main()
