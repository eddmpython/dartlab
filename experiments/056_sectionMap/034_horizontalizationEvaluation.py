"""
실험 ID: 056-034
실험명: section 수평화 평가 기준 확정 및 실데이터 검증

목적:
- sectionMappings 기반 수평화가 실제로 잘 작동하는지 전종목 기준으로 재평가한다.
- 단일 종목을 넣으면 기간별 raw topic과 mapped topic 정렬 상태를 직접 확인할 수 있게 한다.

가설:
1. 현재 section map은 최신 사업보고서 기준 높은 raw coverage를 유지한다.
2. 인접 기간 비교에서 mapped topic set의 overlap이 raw topic set보다 높아진다.
3. 남은 미흡수는 공통 core보다 회사 특화 appendix/detail 쪽에 더 가깝다.

방법:
1. 전체 docs parquet를 스캔해 latest annual raw title coverage를 계산한다.
2. 전종목 annual 인접연도 pair에서 raw topic Jaccard와 mapped topic Jaccard를 비교한다.
3. 대표 종목 또는 입력 종목 1개에 대해 기간별 topic 수, 인접 기간 overlap 개선, 실제 merge 사례를 출력한다.

결과 (실험 후 작성):
- latest annual raw coverage: `0.990`
- annual pair 수: `1,898`
- avg raw Jaccard: `0.690`
- avg mapped Jaccard: `0.778`
- avg delta: `0.088`
- positive / zero / negative: `1018 / 725 / 155`
- 삼성전자(005930) 기간 수: `106`
- 삼성전자 avg pair delta: `0.142`

결론:
- 현재 section map은 단순 title 치환을 넘어 인접 기간의 topic alignment를 실제로 개선하고 있다.
- 전종목 기준 평균 Jaccard가 0.088p 상승하고, 개선 pair가 악화 pair보다 크게 많아 수평화 방향은 타당하다.
- 따라서 이 작업은 한국 DART 사업보고서를 장기적으로 누적 커버하기 위한 공시 프로파일링 층으로 해석하는 것이 맞다.

실험일: 2026-03-12
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import polars as pl

from dartlab.core.dataLoader import loadData
from dartlab.core.reportSelector import selectReport
from dartlab.engines.company.dart.docs.sections.chunker import chunkRows
from dartlab.engines.company.dart.docs.sections.mapper import (
    loadSectionMappings,
    mapSectionTitle,
    normalizeSectionTitle,
    stripSectionPrefix,
)


_REPORT_KINDS = [
    ("annual", ""),
    ("Q1", "Q1"),
    ("semi", "Q2"),
    ("Q3", "Q3"),
]
_CHAPTER_RE = re.compile(r"^\s*([IVX]{1,5})\.\s*(.*)$")
_SPLIT_SUFFIX_RE = re.compile(r" \[\d+/\d+\]$")
_CAMEL_RE = re.compile(r"[A-Za-z][A-Za-z0-9]*$")


def root_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def docs_dir() -> Path:
    return root_dir() / "data" / "dart" / "docs"


def content_col(df: pl.DataFrame) -> str:
    if "section_content" in df.columns:
        return "section_content"
    return "content"


def leaf_title(path: str) -> str:
    base = _SPLIT_SUFFIX_RE.sub("", path)
    parts = base.split(" > ")
    return stripSectionPrefix(parts[-1])


def period_sort_key(period: str) -> tuple[int, int]:
    if "Q" not in period:
        return int(period), 4
    year = int(period[:4])
    quarter = int(period[-1])
    return year, quarter


def jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    if not union:
        return 0.0
    return len(left & right) / len(union)


def latest_annual_coverage() -> tuple[float, int, int]:
    mapping_keys = set(loadSectionMappings().keys())
    total = 0
    uncovered = 0
    unique_uncovered: set[str] = set()
    for path in sorted(docs_dir().glob("*.parquet")):
        df = pl.read_parquet(path)
        annual = df.filter(pl.col("report_type").str.contains("사업보고서"))
        if annual.height == 0:
            continue
        latest_year = annual.get_column("year").max()
        if latest_year is None:
            continue
        current = ""
        titles = annual.filter(pl.col("year") == latest_year).sort("section_order").get_column("section_title").to_list()
        for raw in titles:
            title = (raw or "").strip()
            if not title:
                continue
            chapter_match = _CHAPTER_RE.match(title)
            if chapter_match:
                current = chapter_match.group(1)
                continue
            if not current:
                continue
            total += 1
            normalized = normalizeSectionTitle(title)
            if normalized in mapping_keys:
                continue
            uncovered += 1
            unique_uncovered.add(normalized)
    coverage = 1 - (uncovered / total) if total else 0.0
    return coverage, uncovered, len(unique_uncovered)


def annual_leaf_sets(df: pl.DataFrame) -> dict[str, dict[str, set[str]]]:
    rows_by_year: dict[str, dict[str, set[str]]] = {}
    ccol = content_col(df)
    years = sorted({str(year) for year in df.get_column("year").to_list()})
    for year in years:
        report = selectReport(df, year, reportKind="annual")
        if report is None or ccol not in report.columns:
            continue
        non_empty = report.filter(pl.col(ccol).is_not_null() & (pl.col(ccol).str.len_chars() > 0))
        if non_empty.height == 0:
            continue
        chunks = chunkRows(report.sort("section_order").to_dicts(), ccol)
        raw_set: set[str] = set()
        mapped_set: set[str] = set()
        for chunk in chunks:
            if chunk.kind in ("skipped", "table_only"):
                continue
            title = leaf_title(chunk.path)
            if not title:
                continue
            raw_set.add(title)
            mapped_set.add(mapSectionTitle(title))
        if raw_set or mapped_set:
            rows_by_year[year] = {"raw": raw_set, "mapped": mapped_set}
    return rows_by_year


def global_alignment_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in sorted(docs_dir().glob("*.parquet")):
        stock_code = path.stem
        df = pl.read_parquet(path)
        year_map = annual_leaf_sets(df)
        years = sorted(year_map.keys(), key=int)
        for idx in range(1, len(years)):
            prev_year = years[idx - 1]
            curr_year = years[idx]
            prev_sets = year_map[prev_year]
            curr_sets = year_map[curr_year]
            raw_score = jaccard(prev_sets["raw"], curr_sets["raw"])
            mapped_score = jaccard(prev_sets["mapped"], curr_sets["mapped"])
            rows.append(
                {
                    "stockCode": stock_code,
                    "prevYear": int(prev_year),
                    "currYear": int(curr_year),
                    "rawJaccard": raw_score,
                    "mappedJaccard": mapped_score,
                    "delta": mapped_score - raw_score,
                }
            )
    return rows


def stock_period_rows(stock_code: str) -> list[dict[str, object]]:
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
            period = f"{year}{suffix}"
            chunks = chunkRows(report.sort("section_order").to_dicts(), ccol)
            raw_titles: list[str] = []
            mapped_titles: list[str] = []
            merge_map: dict[str, set[str]] = {}
            for chunk in chunks:
                if chunk.kind in ("skipped", "table_only"):
                    continue
                raw_title = leaf_title(chunk.path)
                if not raw_title:
                    continue
                mapped_title = mapSectionTitle(raw_title)
                raw_titles.append(raw_title)
                mapped_titles.append(mapped_title)
                if mapped_title not in merge_map:
                    merge_map[mapped_title] = set()
                merge_map[mapped_title].add(raw_title)
            raw_set = set(raw_titles)
            mapped_set = set(mapped_titles)
            merge_examples = sorted(
                [
                    f"{topic} <- {sorted(source_titles)}"
                    for topic, source_titles in merge_map.items()
                    if len(source_titles) > 1
                ]
            )
            rows.append(
                {
                    "period": period,
                    "rawSet": raw_set,
                    "mappedSet": mapped_set,
                    "rawTopicCount": len(raw_set),
                    "mappedTopicCount": len(mapped_set),
                    "reductionRate": 1 - (len(mapped_set) / len(raw_set)) if raw_set else 0.0,
                    "canonicalTopicRatio": (
                        sum(1 for topic in mapped_set if _CAMEL_RE.fullmatch(topic)) / len(mapped_set)
                        if mapped_set else 0.0
                    ),
                    "mergeExampleCount": len(merge_examples),
                    "mergeExamples": merge_examples[:8],
                }
            )
    return sorted(rows, key=lambda row: period_sort_key(str(row["period"])))


def print_global_summary(summary: pl.DataFrame, coverage: float, uncovered_rows: int, uncovered_unique: int) -> None:
    print("=" * 72)
    print("056-034 section 수평화 평가")
    print("=" * 72)
    print(f"latestAnnualCoverage={coverage:.3f}")
    print(f"latestAnnualUncoveredRows={uncovered_rows}")
    print(f"latestAnnualUncoveredUnique={uncovered_unique}")
    print(summary)


def print_stock_detail(stock_code: str) -> None:
    rows = stock_period_rows(stock_code)
    if not rows:
        print()
        print(f"[{stock_code}] 기간별 section 데이터 없음")
        return

    detail = pl.DataFrame(
        [
            {
                "period": row["period"],
                "rawTopicCount": row["rawTopicCount"],
                "mappedTopicCount": row["mappedTopicCount"],
                "reductionRate": row["reductionRate"],
                "canonicalTopicRatio": row["canonicalTopicRatio"],
                "mergeExampleCount": row["mergeExampleCount"],
            }
            for row in rows
        ]
    )

    pair_rows: list[dict[str, object]] = []
    for idx in range(1, len(rows)):
        prev_row = rows[idx - 1]
        curr_row = rows[idx]
        raw_score = jaccard(prev_row["rawSet"], curr_row["rawSet"])
        mapped_score = jaccard(prev_row["mappedSet"], curr_row["mappedSet"])
        pair_rows.append(
            {
                "prevPeriod": prev_row["period"],
                "currPeriod": curr_row["period"],
                "rawJaccard": raw_score,
                "mappedJaccard": mapped_score,
                "delta": mapped_score - raw_score,
            }
        )
    pair_df = pl.DataFrame(pair_rows) if pair_rows else pl.DataFrame()

    print()
    print("=" * 72)
    print(f"{stock_code} 기간별 수평화 상세")
    print("=" * 72)
    print(detail)
    if pair_rows:
        print()
        print("[인접 기간 overlap]")
        print(pair_df)
        print()
        print(
            pair_df.select(
                pl.col("rawJaccard").mean().alias("avgRawJaccard"),
                pl.col("mappedJaccard").mean().alias("avgMappedJaccard"),
                pl.col("delta").mean().alias("avgDelta"),
                (pl.col("delta") > 0).sum().alias("positivePairs"),
                (pl.col("delta") == 0).sum().alias("zeroPairs"),
                (pl.col("delta") < 0).sum().alias("negativePairs"),
            )
        )

    merge_samples: list[str] = []
    for row in rows:
        for sample in row["mergeExamples"]:
            merge_samples.append(f"{row['period']}: {sample}")
            if len(merge_samples) >= 10:
                break
        if len(merge_samples) >= 10:
            break
    if merge_samples:
        print()
        print("[merge 사례]")
        for sample in merge_samples:
            print(sample)


def main() -> None:
    coverage, uncovered_rows, uncovered_unique = latest_annual_coverage()
    global_rows = pl.DataFrame(global_alignment_rows())
    summary = global_rows.select(
        pl.len().alias("annualPairs"),
        pl.col("rawJaccard").mean().alias("avgRawJaccard"),
        pl.col("mappedJaccard").mean().alias("avgMappedJaccard"),
        pl.col("delta").mean().alias("avgDelta"),
        pl.col("delta").median().alias("medianDelta"),
        (pl.col("delta") > 0).sum().alias("positivePairs"),
        (pl.col("delta") == 0).sum().alias("zeroPairs"),
        (pl.col("delta") < 0).sum().alias("negativePairs"),
    )
    print_global_summary(summary, coverage, uncovered_rows, uncovered_unique)

    stock_code = sys.argv[1] if len(sys.argv) > 1 else "005930"
    print_stock_detail(stock_code)


if __name__ == "__main__":
    main()
