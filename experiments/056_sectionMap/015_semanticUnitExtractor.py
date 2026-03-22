"""
실험 ID: 056-015
실험명: semantic unit 추출기 초안 검증

목적:
- 세분화된 섹션 내부에서 semantic unit row를 Polars-friendly하게 추출할 수 있는지 확인한다.

가설:
1. `가./나.`, `(1)/(2)`, 표 전후 텍스트를 unit row로 분리할 수 있다.
2. unit row는 chapter/section/subsection/unitType/text 구조로 표현 가능하다.

방법:
1. 삼성전자 2022 `위험관리 및 파생거래` 섹션을 샘플로 사용한다.
2. `가./나.`, `(1)/(2)` 패턴을 기준으로 unit row를 추출한다.
3. Polars DataFrame으로 변환한다.

결과 (실험 후 작성):

- 샘플 섹션(`5. 위험관리 및 파생거래`)에서 semantic unit row 7개 추출
- 스키마: `chapter / section / subsection / unitType / unitLabel / text`
- `가./나.` 및 `(1)/(2)` 경계를 기준으로 semantic unit row를 Polars-friendly하게 뽑을 수 있다.
- 표는 제외하고도 설명문 단위 수평화가 가능한 구조가 확인되었다.
결론:

- `가./나.` 및 `(1)/(2)` 경계를 기준으로 semantic unit row를 Polars-friendly하게 뽑을 수 있다.
- 표는 제외하고도 설명문 단위 수평화가 가능한 구조가 확인되었다.
실험일: 2026-03-11
"""

from __future__ import annotations

import re
from pathlib import Path

import polars as pl

RE_MAJOR = re.compile(r"^([가-힣])\.\s+(.+)$")
RE_MINOR = re.compile(r"^\((\d+)\)\s*(.+)$")


def load_text() -> str:
    root = Path(__file__).resolve().parents[2]
    path = root / "data" / "dart" / "docs" / "005930.parquet"
    df = pl.read_parquet(path).with_columns(pl.col("year").cast(pl.Utf8))
    row = (
        df.filter((pl.col("year") == "2022") & pl.col("report_type").str.contains("사업보고서"))
        .filter(pl.col("section_title") == "5. 위험관리 및 파생거래")
        .select("section_content")
        .to_dicts()[0]
    )
    return row["section_content"]


def extract_units(text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    current_major = ""
    current_minor = ""
    buffer: list[str] = []

    def flush() -> None:
        if not buffer:
            return
        rows.append(
            {
                "chapter": "II_or_III_sample",
                "section": "위험관리 및 파생거래",
                "subsection": current_major or "(root)",
                "unitType": "minor" if current_minor else "major",
                "unitLabel": current_minor or current_major or "(root)",
                "text": "\n".join(buffer).strip(),
            }
        )

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        major = RE_MAJOR.match(stripped)
        minor = RE_MINOR.match(stripped)
        if major:
            flush()
            current_major = stripped
            current_minor = ""
            buffer = []
            continue
        if minor:
            flush()
            current_minor = stripped
            buffer = []
            continue
        if stripped.startswith("|"):
            continue
        buffer.append(stripped)

    flush()
    return rows


def main() -> None:
    units = extract_units(load_text())
    df = pl.DataFrame(units)
    print("=" * 72)
    print("056-015 semantic unit 추출기 초안")
    print("=" * 72)
    print(df.shape)
    print(df.head(12))


if __name__ == "__main__":
    main()
