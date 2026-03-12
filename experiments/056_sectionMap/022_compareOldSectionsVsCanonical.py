"""
실험 ID: 056-022
실험명: 기존 sections vs canonical prototype 비교

목적:
- 기존 sections() 결과와 canonical prototype 결과를 비교해 수평화 품질 개선 가능성을 확인한다.

가설:
1. 기존 sections()는 leaf title 기준이라 topic 수가 과도하게 많다.
2. canonical prototype은 row 수는 많더라도 canonicalSection 축에서 더 안정적인 비교 구조를 만든다.

방법:
1. 기존 sections('005930')의 topic 수를 확인한다.
2. 017 integrated canonical prototype을 재생성한다.
3. canonicalSection, semanticUnit 기준 고유 축 수를 계산한다.

결과 (실험 후 작성):

- 기존 `sections('005930')` topic 수: 329
- canonical prototype row 수: 11,620
- canonicalSection 수: 42
- semanticUnit 수: 1,344
결론:

- 기존 sections는 leaf title 329개 수준의 거친 수평화다.
- canonical prototype은 row 수는 늘어나지만, canonicalSection 축은 42개로 안정화되고 그 아래 semanticUnit 1,344개로 구조화된다.
- 즉 비교 축은 더 안정적이고, 정보 밀도는 더 높아진다.
실험일: 2026-03-11
"""

from __future__ import annotations

import re
from pathlib import Path

import polars as pl

from dartlab.engines.dart.docs.sections.pipeline import sections


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


def build_integrated(df: pl.DataFrame, teacher: dict[str, set[str]]) -> pl.DataFrame:
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
            else:
                if current not in FOCUS_CHAPTERS:
                    continue
                canonical = raw_title if raw_title in teacher.get(current, set()) else f"__chapter__:{current}"

            for subsection, semantic_unit, text, table_rows in extract_units(content):
                rows.append(
                    {
                        "period": year,
                        "canonicalSection": canonical,
                        "semanticUnit": semantic_unit,
                        "tableRows": table_rows,
                        "text": text,
                    }
                )
    return pl.DataFrame(rows)


def main() -> None:
    old = sections("005930")
    old_topic_count = 0 if old is None else old.height

    annual = load_annual_df()
    teacher = teacher_boundaries(annual)
    canonical = build_integrated(annual, teacher)

    print("=" * 72)
    print("056-022 기존 sections vs canonical prototype 비교")
    print("=" * 72)
    print(f"old_topic_count={old_topic_count}")
    print(f"canonical_rows={canonical.height}")
    print(f"canonical_section_count={canonical.get_column('canonicalSection').n_unique()}")
    print(f"semantic_unit_count={canonical.get_column('semanticUnit').n_unique()}")


if __name__ == "__main__":
    main()
