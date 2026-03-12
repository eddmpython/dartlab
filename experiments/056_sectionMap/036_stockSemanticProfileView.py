"""
실험 ID: 056-036
실험명: 단일 종목 section profile 및 semantic unit 뷰

목적:
- 단일 종목에서 기간별 수평화 상태와, 그 다음 단계인 큰 섹션 내부 semantic unit 분해 결과를 한 번에 확인한다.
- section map의 최종 목표가 title 통일이 아니라 report profile 표준화라는 점을 실제 출력으로 점검한다.

가설:
1. 단일 종목 기준으로 기간별 raw topic / mapped topic 상태를 빠르게 점검할 수 있다.
2. 큰 canonical section 내부를 semantic unit로 나누면 비교 가능한 정보 단위가 더 선명해진다.

방법:
1. 입력 종목의 전체 기간 docs를 읽는다.
2. 기간별 raw topic 수, mapped topic 수, canonical topic ratio를 계산한다.
3. 선택한 연간 보고서에서 canonical topic별 text 길이와 semantic unit 수를 계산한다.
4. 대상 topic 하나를 골라 semantic unit row를 출력한다.

결과 (실험 후 작성):
- 삼성전자(005930) 2025 사업보고서에서 큰 canonical section의 semantic unit 분해 결과를 직접 확인 가능
- period-level summary와 annual semantic profile을 한 스크립트에서 동시에 점검 가능

결론:
- stock-level 확인은 전종목 lazy 평가와 분리하는 것이 맞다.
- 다음 단계 실험은 canonical section 내부를 semantic unit 축으로 안정적으로 표준화하는 쪽에 집중하면 된다.

실험일: 2026-03-12
"""

from __future__ import annotations

import re
import sys

import polars as pl

from dartlab.core.dataLoader import loadData
from dartlab.core.reportSelector import selectReport
from dartlab.engines.dart.docs.sections.chunker import chunkRows
from dartlab.engines.dart.docs.sections.mapper import mapSectionTitle, stripSectionPrefix


_REPORT_KINDS = [
    ("annual", ""),
    ("Q1", "Q1"),
    ("semi", "Q2"),
    ("Q3", "Q3"),
]
_SPLIT_SUFFIX_RE = re.compile(r" \[\d+/\d+\]$")
_MAJOR_RE = re.compile(r"^([가-힣])\.\s+(.+)$")
_MINOR_RE = re.compile(r"^\((\d+)\)\s*(.+)$")
_CAMEL_RE = re.compile(r"[A-Za-z][A-Za-z0-9]*$")


def content_col(df: pl.DataFrame) -> str:
    if "section_content" in df.columns:
        return "section_content"
    return "content"


def leaf_title(path: str) -> str:
    base = _SPLIT_SUFFIX_RE.sub("", path)
    leaf = base.split(" > ")[-1]
    return stripSectionPrefix(leaf)


def period_sort_key(period: str) -> tuple[int, int]:
    if "Q" not in period:
        return int(period), 4
    return int(period[:4]), int(period[-1])


def extract_semantic_units(text: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    current_subsection = "(root)"
    current_unit = "(root)"
    buffer: list[str] = []
    table_rows = 0

    def flush() -> None:
        nonlocal buffer, table_rows
        body = "\n".join(buffer).strip()
        if not body and table_rows == 0:
            return
        rows.append(
            {
                "subsection": current_subsection,
                "unitLabel": current_unit,
                "unitType": "minor" if current_unit.startswith("(") else "major",
                "textChars": len(body),
                "tableRows": table_rows,
                "text": body,
            }
        )
        buffer = []
        table_rows = 0

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("|"):
            table_rows += 1
            continue
        if _MAJOR_RE.match(stripped):
            flush()
            current_subsection = stripped
            current_unit = stripped
            continue
        if _MINOR_RE.match(stripped):
            flush()
            current_unit = stripped
            continue
        buffer.append(stripped)

    flush()
    return rows


def period_rows(stock_code: str) -> list[dict[str, object]]:
    df = loadData(stock_code)
    ccol = content_col(df)
    years = sorted({str(year) for year in df.get_column("year").to_list()}, reverse=True)
    rows: list[dict[str, object]] = []
    for year in years:
        for report_kind, suffix in _REPORT_KINDS:
            report = selectReport(df, year, reportKind=report_kind)
            if report is None or ccol not in report.columns:
                continue
            non_empty = report.filter(pl.col(ccol).is_not_null() & (pl.col(ccol).str.len_chars() > 0))
            if non_empty.height == 0:
                continue
            chunks = chunkRows(report.sort("section_order").to_dicts(), ccol)
            raw_topics: set[str] = set()
            mapped_topics: set[str] = set()
            for chunk in chunks:
                if chunk.kind in ("skipped", "table_only"):
                    continue
                raw = leaf_title(chunk.path)
                if not raw:
                    continue
                raw_topics.add(raw)
                mapped_topics.add(mapSectionTitle(raw))
            if not raw_topics:
                continue
            rows.append(
                {
                    "period": f"{year}{suffix}",
                    "rawTopicCount": len(raw_topics),
                    "mappedTopicCount": len(mapped_topics),
                    "reductionRate": 1 - (len(mapped_topics) / len(raw_topics)),
                    "canonicalTopicRatio": (
                        sum(1 for topic in mapped_topics if _CAMEL_RE.fullmatch(topic)) / len(mapped_topics)
                    ),
                }
            )
    return sorted(rows, key=lambda row: period_sort_key(str(row["period"])))


def annual_semantic_profile(stock_code: str, year: str) -> tuple[pl.DataFrame, dict[str, list[dict[str, object]]]]:
    df = loadData(stock_code)
    ccol = content_col(df)
    report = selectReport(df, year, reportKind="annual")
    if report is None or ccol not in report.columns:
        return pl.DataFrame(), {}

    chunks = chunkRows(report.sort("section_order").to_dicts(), ccol)
    topic_rows: list[dict[str, object]] = []
    semantic_map: dict[str, list[dict[str, object]]] = {}

    for chunk in chunks:
        if chunk.kind in ("skipped", "table_only"):
            continue
        raw = leaf_title(chunk.path)
        if not raw:
            continue
        topic = mapSectionTitle(raw)
        units = extract_semantic_units(chunk.textContent)
        semantic_map.setdefault(topic, []).extend(
            [
                {
                    "rawTitle": raw,
                    "path": chunk.path,
                    **unit,
                }
                for unit in units
            ]
        )
        topic_rows.append(
            {
                "topic": topic,
                "rawTitle": raw,
                "path": chunk.path,
                "textChars": len(chunk.textContent),
                "semanticUnitCount": max(len(units), 1),
                "chunkKind": chunk.kind,
            }
        )

    if not topic_rows:
        return pl.DataFrame(), semantic_map

    summary = (
        pl.DataFrame(topic_rows)
        .group_by("topic")
        .agg(
            pl.col("rawTitle").n_unique().alias("rawTitleVariants"),
            pl.col("path").n_unique().alias("chunkPaths"),
            pl.col("textChars").sum().alias("textChars"),
            pl.col("semanticUnitCount").sum().alias("semanticUnits"),
        )
        .sort(["textChars", "semanticUnits"], descending=[True, True])
    )
    return summary, semantic_map


def main() -> None:
    stock_code = sys.argv[1] if len(sys.argv) > 1 else "005930"
    year = sys.argv[2] if len(sys.argv) > 2 else "2025"
    target_topic = sys.argv[3] if len(sys.argv) > 3 else ""

    period_summary = pl.DataFrame(period_rows(stock_code))
    semantic_summary, semantic_map = annual_semantic_profile(stock_code, year)

    print("=" * 72)
    print(f"056-036 {stock_code} section profile")
    print("=" * 72)
    print(period_summary)

    print()
    print("=" * 72)
    print(f"{stock_code} {year} annual semantic profile")
    print("=" * 72)
    print(semantic_summary.head(20))

    if semantic_summary.height == 0:
        return

    chosen_topic = target_topic or semantic_summary.get_column("topic").to_list()[0]
    semantic_rows = semantic_map.get(chosen_topic, [])
    semantic_df = pl.DataFrame(semantic_rows) if semantic_rows else pl.DataFrame()

    print()
    print("=" * 72)
    print(f"{stock_code} {year} semantic units: {chosen_topic}")
    print("=" * 72)
    print(semantic_df.head(20))


if __name__ == "__main__":
    main()
