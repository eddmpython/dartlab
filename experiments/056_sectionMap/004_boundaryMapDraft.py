"""
실험 ID: 056-004
실험명: canonical boundary map 초안 생성

목적:
- 세분화 teacher 샘플(삼성전자 2022 사업보고서)을 기준으로 chapter별 canonical boundary 초안을 만든다.
- coarse/fine 정렬의 기준이 될 수 있는 최소 section map을 텍스트로 출력한다.

가설:
1. 삼성전자 2022 사업보고서만으로도 chapter별 대표 boundary 초안을 만들 수 있다.
2. 특히 II장/III장/V장/XI장/XII장은 canonical boundary 후보가 뚜렷하다.

방법:
1. 삼성전자 2022 사업보고서 section_title을 section_order 순으로 읽는다.
2. 로마숫자 대분류 아래의 하위 title을 chapter별로 그룹화한다.
3. canonical boundary draft를 chapter -> subtopics 구조로 출력한다.

결과 (실험 후 작성):

- 삼성전자 2022 사업보고서를 기준으로 chapter별 canonical boundary draft 생성 완료
- I장: 5개
- II장: 7개
- III장: 8개
결론:

- 삼성전자 2022는 056의 boundary teacher 샘플로 충분할 정도로 세분화가 뚜렷하다.
- 다만 IV/VII/IX/X처럼 삼성전자 데이터만으로는 세부 boundary가 비어 있는 장이 있어, 다음 단계는 다른 기업을 함께 대조해 공통 boundary를 보강해야 한다.
실험일: 2026-03-11
"""

from __future__ import annotations

import re
from pathlib import Path

import polars as pl


CHAPTER_RE = re.compile(r"^\s*([IVX]{1,5})\.\s*(.*)$")


def load_titles() -> list[str]:
    root = Path(__file__).resolve().parents[2]
    path = root / "data" / "dart" / "docs" / "005930.parquet"
    df = pl.read_parquet(path).with_columns(pl.col("year").cast(pl.Utf8))
    return (
        df.filter((pl.col("year") == "2022") & pl.col("report_type").str.contains("사업보고서"))
        .sort("section_order")
        .get_column("section_title")
        .to_list()
    )


def build_boundary_map(titles: list[str]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    current: str | None = None
    for title in titles:
        stripped = title.strip()
        chapter_match = CHAPTER_RE.match(stripped)
        if chapter_match:
            current = chapter_match.group(1)
            result.setdefault(current, [])
            continue
        if current is None:
            continue
        result.setdefault(current, []).append(stripped)
    return result


def main() -> None:
    titles = load_titles()
    boundary_map = build_boundary_map(titles)

    print("=" * 72)
    print("056-004 canonical boundary map 초안")
    print("=" * 72)
    for chapter, items in boundary_map.items():
        print(f"\n[{chapter}] ({len(items)})")
        for item in items:
            print(f" - {item}")


if __name__ == "__main__":
    main()
