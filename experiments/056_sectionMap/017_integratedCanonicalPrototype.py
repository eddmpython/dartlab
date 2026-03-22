"""
실험 ID: 056-017
실험명: 통합 canonical prototype 검증

목적:
- 삼성전자 전 연간 사업보고서를 대상으로 boundary, hierarchy, semantic unit, table meta를 한 번에 올리는 단일 Polars prototype을 검증한다.

가설:
1. 2022 teacher boundary를 기준으로 전 연간 사업보고서를 하나의 canonical DataFrame으로 투영할 수 있다.
2. exact match와 coarse chapter 투영을 함께 쓰면 전 기간 수평화 prototype이 가능하다.

방법:
1. 삼성전자 전 연간 사업보고서를 읽는다.
2. 2022 사업보고서를 teacher boundary로 사용한다.
3. 각 연도 raw section을 canonical section(exact 또는 coarse)으로 투영한다.
4. 각 row에서 semantic unit와 tableRows를 추출한다.
5. Polars DataFrame으로 통합한다.

결과 (실험 후 작성):

- 결과 shape: `(11,620, 9)`
- period 수: 27개 (삼성전자 전 연간 사업보고서)
- projectionKind 분포:
- `coarse_chapter`: 7,684
결론:

- boundary, hierarchy, semantic unit, table meta를 하나의 Polars DataFrame prototype으로 통합하는 것이 실제로 가능함이 확인되었다.
- 현재는 exact보다 coarse_chapter가 더 많으므로, 다음 단계는 coarse를 fine boundary 아래로 더 잘 투영하는 규칙을 강화하는 것이다.
실험일: 2026-03-11
"""

from __future__ import annotations

import re
from pathlib import Path

import polars as pl

RE_CHAPTER = re.compile(r"^\s*([IVX]{1,5})\.\s*(.*)$")
RE_MAJOR = re.compile(r"^([가-힣])\.\s+(.+)$")
RE_MINOR = re.compile(r"^\((\d+)\)\s*(.+)$")
FOCUS_CHAPTERS = {"I", "II", "III", "V", "VI", "VIII", "XI", "XII"}


def load_annual_df() -> pl.DataFrame:
    root = Path(__file__).resolve().parents[2]
    path = root / "data" / "dart" / "docs" / "005930.parquet"
    df = pl.read_parquet(path).with_columns(pl.col("year").cast(pl.Utf8))
    return df.filter(pl.col("report_type").str.contains("사업보고서")).sort(["year", "section_order"])


def teacher_boundaries(df: pl.DataFrame, year: str = "2022") -> dict[str, set[str]]:
    boundaries: dict[str, set[str]] = {}
    current = ""
    rows = df.filter(pl.col("year") == year).select(["section_title"]).to_dicts()
    for row in rows:
        title = row["section_title"].strip()
        match = RE_CHAPTER.match(title)
        if match:
            current = match.group(1)
            boundaries.setdefault(current, set())
            continue
        if current in FOCUS_CHAPTERS:
            boundaries.setdefault(current, set()).add(title)
    return boundaries


def extract_units(text: str) -> list[tuple[str, str, str, int]]:
    units: list[tuple[str, str, str, int]] = []
    current_subsection = "(root)"
    current_label = "(root)"
    buffer: list[str] = []
    table_rows = 0

    def flush() -> None:
        if not buffer and table_rows == 0:
            return
        unit_type = "minor" if current_label.startswith("(") else "major"
        units.append((current_subsection, current_label, "\n".join(buffer).strip(), table_rows))

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("|"):
            table_rows += 1
            continue
        major = RE_MAJOR.match(stripped)
        minor = RE_MINOR.match(stripped)
        if major:
            flush()
            current_subsection = stripped
            current_label = stripped
            buffer = []
            table_rows = 0
            continue
        if minor:
            flush()
            current_label = stripped
            buffer = []
            table_rows = 0
            continue
        buffer.append(stripped)

    flush()
    return units


def build_rows(df: pl.DataFrame, teacher: dict[str, set[str]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for year in sorted(df.get_column("year").unique().to_list()):
        year_rows = df.filter(pl.col("year") == year).select(["section_title", "section_content"]).to_dicts()
        current = ""
        for row in year_rows:
            raw_title = row["section_title"].strip()
            content = row["section_content"] or ""
            match = RE_CHAPTER.match(raw_title)
            if match:
                current = match.group(1)
                if current not in FOCUS_CHAPTERS:
                    continue
                canonical = f"__chapter__:{current}"
                projection_kind = "coarse_chapter"
            else:
                if current not in FOCUS_CHAPTERS:
                    continue
                if raw_title in teacher.get(current, set()):
                    canonical = raw_title
                    projection_kind = "exact"
                else:
                    canonical = f"__chapter__:{current}"
                    projection_kind = "coarse_chapter"

            for subsection, semantic_unit, text, table_rows in extract_units(content):
                rows.append(
                    {
                        "period": year,
                        "chapter": current,
                        "rawTitle": raw_title,
                        "canonicalSection": canonical,
                        "projectionKind": projection_kind,
                        "subsection": subsection,
                        "semanticUnit": semantic_unit,
                        "text": text,
                        "tableRows": table_rows,
                    }
                )
    return rows


def main() -> None:
    df = load_annual_df()
    teacher = teacher_boundaries(df)
    records = build_rows(df, teacher)
    out = pl.DataFrame(records)
    print("=" * 72)
    print("056-017 통합 canonical prototype")
    print("=" * 72)
    print("shape=", out.shape)
    print("periods=", out.get_column("period").n_unique())
    print(out.group_by("projectionKind").agg(pl.len().alias("rows")).sort("rows", descending=True))
    print(out.head(12))


if __name__ == "__main__":
    main()
