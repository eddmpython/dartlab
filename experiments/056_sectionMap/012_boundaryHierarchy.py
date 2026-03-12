"""
실험 ID: 056-012
실험명: boundary hierarchy 초안 검증

목적:
- coarse boundary와 fine boundary의 상위-하위 관계를 계층 구조로 표현할 수 있는지 검증한다.
- 삼성전자 2021/2022를 기준으로 chapter -> coarse -> fine 구조 초안을 만든다.

가설:
1. coarse 연도의 섹션은 fine 연도의 여러 boundary를 대표하는 상위 노드로 모델링할 수 있다.
2. 이 계층 구조가 있으면 exact match가 아닌 부모-자식 정렬로 수평화 품질을 높일 수 있다.

방법:
1. 삼성전자 2021/2022 사업보고서의 chapter별 section_title을 비교한다.
2. 2021에 없고 2022에만 있는 fine boundary를 chapter별로 묶는다.
3. 각 chapter에 대해 coarse node와 fine children 목록을 출력한다.

결과 (실험 후 작성):

- coarse -> fine 계층 초안 생성 완료
- 예시:
- II장 coarse 없음 -> fine children 7개 전체
- III장 coarse 6개 -> fine children `배당`, `자금조달`, `기타 재무`
결론:

- exact match가 아니라 boundary hierarchy(부모-자식 관계)를 두면 coarse/fine 연도 정렬이 가능해진다.
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
    print("=" * 72)
    print("056-012 boundary hierarchy 초안")
    print("=" * 72)
    for chapter in sorted(fine.keys()):
        fine_items = fine.get(chapter, [])
        coarse_items = coarse.get(chapter, [])
        fine_only = [item for item in fine_items if item not in set(coarse_items)]
        if not fine_only:
            continue
        print(f"\n[{chapter}]")
        print(f" coarse: {coarse_items if coarse_items else ['(명시 coarse 없음)']}")
        print(" fine children:")
        for item in fine_only:
            print(f"  - {item}")


if __name__ == "__main__":
    main()
