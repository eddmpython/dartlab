"""
실험 ID: 056-054
실험명: 전 종목 × 전 기간 section mapper 감사

목적:
- 053은 최신 annual만 대상이었다. 데이터가 310개로 증가한 시점에서
  전 종목 × 전 기간(annual + quarterly)을 스캔하여 매퍼 포화도를 측정한다.
- 신규 27개 종목과 과거 기간에서 나오는 미매핑 title을 수집한다.

가설:
1. latest annual 99.95%보다 전 기간 매핑률은 낮을 것이다 (과거 양식 차이).
2. 빈도 3+ 미매핑 title은 패턴/JSON 흡수 대상이다.

방법:
1. `data/dart/docs/*.parquet` 전부 스캔 (310개)
2. 모든 report_type × 모든 year의 section_title을 mapSectionTitle()에 통과
3. 매핑률 집계: 전체, annual only, quarterly only, 연도별 추이
4. 미매핑 title을 빈도순 정렬 → 흡수 후보 식별

결과 (실험 후 작성):
- 종목 수: 319 (310 docs + 추가 9개)
- 전체 title rows: 258,594
- 1차 스캔 (보강 전): 매핑률 99.30%, 미매핑 1,822 rows, 고유 93개 title
- 2차 (JSON 71개 + 패턴 21개 추가 후): 매핑률 99.99%, 미매핑 18 rows, 고유 1개 title
- 3차 (DGB금융 패턴 1개 추가): 매핑률 100.000%, 미매핑 0
- Annual: 68,110 rows → 100%
- Quarterly: 190,484 rows → 100%
- 연도별: 2012~2026 전 구간 100%
- sectionMappings.json: 474 → 545개 (+71)
- _PATTERN_MAPPINGS: 85 → 107개 (+22)

결론:
- 전 종목 × 전 기간 section mapper 100% 포화 달성
- 주요 흡수 대상: 구 양식 장 제목(회사의개황, 기타필요한사항), 금융업 상세표, 재무제표 첨부 변형
- 신규 27개 종목에서 특이 미매핑은 없었고, 기존 종목의 과거 기간(2012~2020)에서 구 양식 변형이 주로 발견됨

실험일: 2026-03-20
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

from dartlab.engines.dart.docs.sections.mapper import mapSectionTitle, normalizeSectionTitle

DOCS_DIR = Path("data/dart/docs")


def full_period_audit() -> tuple[pl.DataFrame, pl.DataFrame]:
    """전 종목 × 전 기간 매핑 감사."""
    rows: list[dict[str, object]] = []
    for path in sorted(DOCS_DIR.glob("*.parquet")):
        stock_code = path.stem
        df = pl.read_parquet(path)
        for row in df.iter_rows(named=True):
            raw = (row.get("section_title") or "").strip()
            if not raw:
                continue
            report_type = str(row.get("report_type", ""))
            year = str(row.get("year", ""))
            normalized = normalizeSectionTitle(raw)
            mapped = mapSectionTitle(raw)
            rows.append(
                {
                    "stockCode": stock_code,
                    "year": year,
                    "reportType": report_type,
                    "rawTitle": raw,
                    "normalizedTitle": normalized,
                    "mappedTopic": mapped,
                    "isMapped": mapped != normalized,
                }
            )

    full = pl.DataFrame(rows)
    return full, _summarize_unmapped(full)


def _summarize_unmapped(full: pl.DataFrame) -> pl.DataFrame:
    return (
        full.filter(pl.col("isMapped").not_())
        .group_by("normalizedTitle")
        .agg(
            pl.len().alias("rows"),
            pl.col("stockCode").n_unique().alias("companies"),
            pl.col("rawTitle").first().alias("exampleRaw"),
            pl.col("stockCode").first().alias("exampleStock"),
        )
        .sort(["rows", "companies"], descending=[True, True])
    )


def main() -> None:
    full, unmapped = full_period_audit()

    total = full.height
    mapped = full["isMapped"].sum()
    stocks = full["stockCode"].n_unique()

    print("=" * 72)
    print("056-054 전 종목 × 전 기간 section mapper 감사")
    print("=" * 72)
    print(f"종목 수: {stocks}")
    print(f"전체 title rows: {total:,}")
    print(f"매핑 rows: {mapped:,}")
    print(f"매핑률: {mapped / total:.6f}" if total else "N/A")
    print(f"미매핑 rows: {total - mapped:,}")
    print(f"미매핑 고유 title: {unmapped.height}")
    print()

    # annual vs quarterly
    is_annual = full["reportType"].str.contains("사업보고서", literal=True)
    annual = full.filter(is_annual)
    quarterly = full.filter(~is_annual)
    if annual.height:
        a_mapped = annual["isMapped"].sum()
        print(f"[Annual]  rows={annual.height:,}  mapped={a_mapped / annual.height:.6f}")
    if quarterly.height:
        q_mapped = quarterly["isMapped"].sum()
        print(f"[Quarterly] rows={quarterly.height:,}  mapped={q_mapped / quarterly.height:.6f}")
    print()

    # 연도별 매핑률 추이 (최근 10년)
    by_year = (
        full.group_by("year")
        .agg(
            pl.len().alias("rows"),
            pl.col("isMapped").mean().round(6).alias("mappedRatio"),
        )
        .sort("year", descending=True)
        .head(15)
    )
    print("[연도별 매핑률 (최근 15)]")
    print(by_year)
    print()

    # 미매핑 top 30
    print(f"[미매핑 title top 30 / 전체 {unmapped.height}개]")
    print(unmapped.head(30))


if __name__ == "__main__":
    main()
