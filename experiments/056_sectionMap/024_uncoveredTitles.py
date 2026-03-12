"""
실험 ID: 056-024
실험명: 미흡수 raw title 예외 분석

목적:
- sectionMappings draft에 잡히지 않는 raw title 예외를 추출하고 유형별로 분류한다.

가설:
1. 남은 미흡수 title은 소수의 반복 패턴(업종 변형, 상세표 확장, 전문가 확인류, 회사 고유 상세항목)으로 묶인다.
2. 이 예외군만 정리하면 raw coverage를 추가로 끌어올릴 수 있다.

방법:
1. 최신 사업보고서 전체 raw title을 수집한다.
2. 현재 draft mapping에 없는 title만 필터링한다.
3. 정규식 규칙으로 예외 유형을 분류한다.

결과 (실험 후 작성):

- uncovered rows: 316
- uncovered unique titles: 109
- `genericMatter`: 135 rows / 7 titles
- `detailExpansion`: 70 rows / 59 titles
결론:

- 남은 3.7%는 랜덤 노이즈가 아니라 소수의 반복 유형으로 수렴한다.
- 다음 개선은 전면 재설계가 아니라, `공시내용 진행 및 변경사항`, `영업의 현황`, 상세표 확장류를 흡수하는 예외 규칙 몇 개를 추가하면 된다.
실험일: 2026-03-11
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import polars as pl


CHAPTER_RE = re.compile(r"^\s*([IVX]{1,5})\.\s*(.*)$")
INDUSTRY_PREFIX_RE = re.compile(r"^\([^)]*업\)")


def base_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def docs_dir() -> Path:
    return base_dir() / "data" / "dart" / "docs"


def draft_path() -> Path:
    return Path(__file__).resolve().parent / "output" / "sectionMappings.draft.json"


def normalize_title(title: str) -> str:
    text = title.strip()
    text = INDUSTRY_PREFIX_RE.sub("", text)
    text = text.replace("ㆍ", ",")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def classify_title(title: str) -> str:
    if title.startswith("("):
        return "industryPrefixed"
    if "(상세)" in title:
        return "detailExpansion"
    if "전문가의 확인" in title:
        return "expertConfirmation"
    if "현황" in title:
        return "statusVariant"
    if "실적" in title or "수주" in title:
        return "metricDetail"
    if "사항" in title:
        return "genericMatter"
    return "other"


def latest_title_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(docs_dir().glob("*.parquet")):
        stock_code = path.stem
        df = pl.read_parquet(path).with_columns(pl.col("year"))
        annual = df.filter(pl.col("report_type").str.contains("사업보고서"))
        if annual.height == 0:
            continue
        latest_year = annual.get_column("year").max()
        if latest_year is None:
            continue
        current = ""
        titles = (
            annual.filter(pl.col("year") == latest_year).sort("section_order").get_column("section_title").to_list()
        )
        for raw_title in titles:
            stripped = (raw_title or "").strip()
            match = CHAPTER_RE.match(stripped)
            if match:
                current = match.group(1)
                continue
            if not current:
                continue
            rows.append(
                {
                    "stockCode": stock_code,
                    "chapter": current,
                    "rawTitle": stripped,
                    "normalizedTitle": normalize_title(stripped),
                }
            )
    return rows


def main() -> None:
    mapping = json.loads(draft_path().read_text(encoding="utf-8"))
    covered_titles = set(mapping.keys())
    df = pl.DataFrame(latest_title_rows())
    uncovered = df.filter(~pl.col("normalizedTitle").is_in(list(covered_titles)))
    uncovered = uncovered.with_columns(
        pl.col("rawTitle").map_elements(classify_title, return_dtype=pl.Utf8).alias("reason")
    )

    reason_summary = (
        uncovered.group_by("reason")
        .agg(pl.len().alias("rows"), pl.col("rawTitle").n_unique().alias("uniqueTitles"))
        .sort("rows", descending=True)
    )
    top_titles = (
        uncovered.group_by(["reason", "rawTitle"])
        .agg(pl.col("stockCode").n_unique().alias("companyCoverage"), pl.len().alias("rows"))
        .sort(["rows", "companyCoverage", "rawTitle"], descending=[True, True, False])
        .head(30)
    )

    print("=" * 72)
    print("056-024 미흡수 raw title 예외 분석")
    print("=" * 72)
    print(f"uncovered_rows={uncovered.height}")
    print(f"uncovered_unique_titles={uncovered.get_column('rawTitle').n_unique()}")
    print()
    print("[reason summary]")
    print(reason_summary)
    print()
    print("[top uncovered titles]")
    print(top_titles)


if __name__ == "__main__":
    main()
