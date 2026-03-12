"""
실험 ID: 056-010
실험명: table-aware semantic unit 검증

목적:
- 긴 섹션에서 표 전후 설명과 표 자체를 분리 저장할 필요가 있는지 검증한다.

가설:
1. 표 중심 섹션은 본문 설명과 표가 섞여 있어 semantic unit과 tableMeta 분리가 유효하다.
2. 특히 `매출 및 수주상황`, `위험관리 및 파생거래`, `주요계약 및 연구개발활동`은 표 비중이 높다.

방법:
1. 삼성전자 2022 대표 섹션 3개를 읽는다.
2. 텍스트 줄 수와 표 줄 수를 분리 계산한다.
3. 표 비율과 표 전후 설명 존재 여부를 확인한다.

결과 (실험 후 작성):

- `4. 매출 및 수주상황`: 0.77 (text 23 / table 77)
- `5. 위험관리 및 파생거래`: 0.49 (text 39 / table 38)
- `6. 주요계약 및 연구개발활동`: 0.83 (text 19 / table 91)
- 대표 섹션 다수가 표 중심이며, 동시에 표 전후 설명 텍스트가 모두 존재한다.
결론:

- 대표 섹션 다수가 표 중심이며, 동시에 표 전후 설명 텍스트가 모두 존재한다.
- 따라서 semanticUnit와 tableMeta를 분리 저장하는 구조가 필요하다.
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


def summarize(content: str) -> tuple[int, int, int, bool, bool]:
    lines = [line for line in content.splitlines() if line.strip()]
    table_lines = [line for line in lines if line.strip().startswith("|")]
    text_lines = [line for line in lines if not line.strip().startswith("|")]
    first_table_idx = next((i for i, line in enumerate(lines) if line.strip().startswith("|")), -1)
    has_text_before = first_table_idx > 0
    has_text_after = False
    if first_table_idx != -1:
        for line in lines[first_table_idx + 1 :]:
            if not line.strip().startswith("|"):
                has_text_after = True
                break
    return len(lines), len(text_lines), len(table_lines), has_text_before, has_text_after


def main() -> None:
    print("=" * 72)
    print("056-010 table-aware semantic unit 검증")
    print("=" * 72)
    for row in load_rows():
        total, text_count, table_count, before, after = summarize(row["section_content"])
        ratio = table_count / total if total else 0.0
        print(
            f"{row['section_title']}: total={total}, text={text_count}, table={table_count}, ratio={ratio:.2f}, before={before}, after={after}"
        )


if __name__ == "__main__":
    main()
