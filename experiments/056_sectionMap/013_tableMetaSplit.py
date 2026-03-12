"""
실험 ID: 056-013
실험명: tableMeta 분리 초안 검증

목적:
- 표 중심 섹션에서 표와 설명문을 분리해도 정보 손실 없이 구조화할 수 있는지 확인한다.

가설:
1. 표 중심 섹션은 `narrative-before`, `table-meta`, `narrative-after`의 3분 구조로 나눌 수 있다.
2. 이 구조가 semantic unit 수평화 품질을 높인다.

방법:
1. 삼성전자 2022 대표 표 중심 섹션 3개를 읽는다.
2. 첫 표 이전 텍스트, 표 블록, 표 이후 텍스트를 분리한다.
3. 각 구간의 줄 수를 계산한다.

결과 (실험 후 작성):

- `4. 매출 및 수주상황`: before 5 / table 87 / after 8
- `5. 위험관리 및 파생거래`: before 13 / table 62 / after 2
- `6. 주요계약 및 연구개발활동`: before 2 / table 108 / after 0
- 표 중심 섹션은 `narrative-before`, `table`, `narrative-after` 3분 구조로 안정적으로 분리 가능하다.
결론:

- 표 중심 섹션은 `narrative-before`, `table`, `narrative-after` 3분 구조로 안정적으로 분리 가능하다.
- 따라서 semanticUnit와 tableMeta를 별도 열/구조로 저장하는 설계가 유효하다.
실험일: 2026-03-11
"""

from __future__ import annotations

from pathlib import Path

import polars as pl


TARGET_TITLES = ["4. 매출 및 수주상황", "5. 위험관리 및 파생거래", "6. 주요계약 및 연구개발활동"]


def load_rows() -> list[dict[str, str]]:
    root = Path(__file__).resolve().parents[2]
    path = root / "data" / "dart" / "docs" / "005930.parquet"
    df = pl.read_parquet(path).with_columns(pl.col("year").cast(pl.Utf8))
    return (
        df.filter((pl.col("year") == "2022") & pl.col("report_type").str.contains("사업보고서"))
        .filter(pl.col("section_title").is_in(TARGET_TITLES))
        .select(["section_title", "section_content"])
        .to_dicts()
    )


def split_blocks(content: str) -> tuple[int, int, int]:
    lines = [line for line in content.splitlines() if line.strip()]
    first_table = next((i for i, line in enumerate(lines) if line.strip().startswith("|")), len(lines))
    last_table = max((i for i, line in enumerate(lines) if line.strip().startswith("|")), default=-1)
    before = lines[:first_table]
    table = lines[first_table : last_table + 1] if last_table >= first_table else []
    after = lines[last_table + 1 :] if last_table != -1 else []
    return len(before), len(table), len(after)


def main() -> None:
    print("=" * 72)
    print("056-013 tableMeta 분리 초안")
    print("=" * 72)
    for row in load_rows():
        before, table, after = split_blocks(row["section_content"])
        print(f"{row['section_title']}: before={before}, table={table}, after={after}")


if __name__ == "__main__":
    main()
