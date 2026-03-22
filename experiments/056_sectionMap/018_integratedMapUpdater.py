"""
실험 ID: 056-018
실험명: 통합 canonical map updater 초안

목적:
- 전체 docs parquet를 한 번에 스캔하여 chapter별 canonical boundary 후보를 누적 생성하는 Polars 기반 updater 초안을 검증한다.

가설:
1. latest annual report 기준 전체 기업을 동시에 보면 chapter별 공통 boundary를 안정적으로 누적 생성할 수 있다.
2. title 정규화만으로도 high-confidence canonical candidate와 industry-specific candidate를 1차 분리할 수 있다.

방법:
1. data/dart/docs/*.parquet 전체를 읽는다.
2. 각 기업의 최신 사업보고서 section_title만 추출한다.
3. chapter별 raw title과 normalized title 빈도, 회사 커버리지를 계산한다.
4. coverage가 높은 항목을 canonical boundary 후보로 출력한다.

결과 (실험 후 작성):

- 전체 최신 사업보고서 기준 스캔 기업 수: 229
- 전체 row 수: 8,557
- chapter별 high-confidence canonical candidate를 전체 기업에서 동시에 누적 생성 가능
- 후보 수:
결론:

- 전체 parquet를 동시에 스캔해서 canonical map 후보를 누적 생성하는 updater 방식이 실제로 가능함이 확인되었다.
- 즉 056은 특정 회사 분석을 넘어서, 데이터가 누적될수록 canonical map이 더 정교해지는 구조로 갈 수 있다.
실험일: 2026-03-11
"""

from __future__ import annotations

import re
from pathlib import Path

import polars as pl

CHAPTER_RE = re.compile(r"^\s*([IVX]{1,5})\.\s*(.*)$")
INDUSTRY_PREFIX_RE = re.compile(r"^\([^)]*업\)")


def docs_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "dart" / "docs"


def normalize_title(title: str) -> str:
    text = title.strip()
    text = INDUSTRY_PREFIX_RE.sub("", text)
    text = text.replace("ㆍ", ",")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def latest_annual_rows(path: Path) -> list[dict[str, str]]:
    stock_code = path.stem
    df = pl.read_parquet(path).with_columns(pl.col("year"))
    annual = df.filter(pl.col("report_type").str.contains("사업보고서"))
    if annual.height == 0:
        return []
    latest_year = annual.get_column("year").max()
    if latest_year is None:
        return []
    rows = annual.filter(pl.col("year") == latest_year).sort("section_order").select(["section_title"]).to_dicts()

    current = ""
    out: list[dict[str, str]] = []
    for row in rows:
        raw_title = (row["section_title"] or "").strip()
        match = CHAPTER_RE.match(raw_title)
        if match:
            current = match.group(1)
            continue
        if not current:
            continue
        out.append(
            {
                "stockCode": stock_code,
                "chapter": current,
                "rawTitle": raw_title,
                "normalizedTitle": normalize_title(raw_title),
            }
        )
    return out


def build_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(docs_dir().glob("*.parquet")):
        rows.extend(latest_annual_rows(path))
    return rows


def main() -> None:
    rows = build_rows()
    df = pl.DataFrame(rows)

    company_count = df.get_column("stockCode").n_unique()
    chapter_summary = (
        df.group_by(["chapter", "normalizedTitle"])
        .agg(
            pl.len().alias("rows"),
            pl.col("stockCode").n_unique().alias("companyCoverage"),
            pl.col("rawTitle").n_unique().alias("rawVariants"),
        )
        .with_columns((pl.col("companyCoverage") / company_count).round(3).alias("coverageRatio"))
        .sort(["chapter", "companyCoverage", "normalizedTitle"], descending=[False, True, False])
    )

    high_conf = chapter_summary.filter(pl.col("coverageRatio") >= 0.7)

    print("=" * 72)
    print("056-018 통합 canonical map updater 초안")
    print("=" * 72)
    print(f"companies={company_count}")
    print(f"rows={df.height}")
    print()
    print("[chapter별 high-confidence canonical candidates]")
    print(high_conf)
    print()
    print("[chapter별 후보 수]")
    print(high_conf.group_by("chapter").agg(pl.len().alias("candidateCount")).sort("chapter"))


if __name__ == "__main__":
    main()
