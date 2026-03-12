"""
실험 ID: 056-016
실험명: canonical map prototype 생성

목적:
- chapter/section/subsection/semanticUnit/tableMeta 구조를 하나의 Polars DataFrame prototype으로 합칠 수 있는지 검증한다.

가설:
1. hierarchy와 semantic unit, tableMeta를 한 DataFrame 스키마로 통합할 수 있다.
2. 이 prototype이 향후 sections 엔진 리팩터링의 직접적인 기반이 된다.

방법:
1. 삼성전자 2022 `위험관리 및 파생거래` 섹션을 샘플로 사용한다.
2. semantic unit row와 table row count를 함께 넣는다.
3. canonical map prototype DataFrame을 생성한다.

결과 (실험 후 작성):

- 결과 shape: `(7, 8)`
- 스키마: `period / chapter / section / subsection / semanticUnit / unitType / text / tableRows`
- hierarchy + semantic unit + tableMeta(tableRows)를 한 DataFrame prototype으로 통합할 수 있음이 확인되었다.
- 즉 최종 sections 엔진 리팩터링은 nested object가 아니라 Polars DataFrame 중심으로도 충분히 가능하다.
결론:

- hierarchy + semantic unit + tableMeta(tableRows)를 한 DataFrame prototype으로 통합할 수 있음이 확인되었다.
- 즉 최종 sections 엔진 리팩터링은 nested object가 아니라 Polars DataFrame 중심으로도 충분히 가능하다.
실험일: 2026-03-11
"""

from __future__ import annotations

import re
from pathlib import Path

import polars as pl


RE_MAJOR = re.compile(r"^([가-힣])\.\s+(.+)$")
RE_MINOR = re.compile(r"^\((\d+)\)\s*(.+)$")


def load_row() -> dict[str, str]:
    root = Path(__file__).resolve().parents[2]
    path = root / "data" / "dart" / "docs" / "005930.parquet"
    df = pl.read_parquet(path).with_columns(pl.col("year").cast(pl.Utf8))
    return (
        df.filter((pl.col("year") == "2022") & pl.col("report_type").str.contains("사업보고서"))
        .filter(pl.col("section_title") == "5. 위험관리 및 파생거래")
        .select(["year", "section_title", "section_content"])
        .to_dicts()[0]
    )


def extract_rows(title: str, text: str, period: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    current_major = ""
    current_minor = ""
    buffer: list[str] = []
    table_count = 0

    def flush() -> None:
        if not buffer:
            return
        rows.append(
            {
                "period": period,
                "chapter": "III_like",
                "section": title,
                "subsection": current_major or "(root)",
                "semanticUnit": current_minor or current_major or "(root)",
                "unitType": "minor" if current_minor else "major",
                "text": "\n".join(buffer).strip(),
                "tableRows": table_count,
            }
        )

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("|"):
            table_count += 1
            continue
        major = RE_MAJOR.match(stripped)
        minor = RE_MINOR.match(stripped)
        if major:
            flush()
            current_major = stripped
            current_minor = ""
            buffer = []
            table_count = 0
            continue
        if minor:
            flush()
            current_minor = stripped
            buffer = []
            table_count = 0
            continue
        buffer.append(stripped)
    flush()
    return rows


def main() -> None:
    row = load_row()
    records = extract_rows(row["section_title"], row["section_content"], row["year"])
    df = pl.DataFrame(records)
    print("=" * 72)
    print("056-016 canonical map prototype")
    print("=" * 72)
    print(df.shape)
    print(df.head(12))


if __name__ == "__main__":
    main()
