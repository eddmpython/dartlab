"""
실험 ID: 056-053
실험명: 전 docs 포트폴리오 section mapper 감사

목적:
- 현재 로컬 docs 전체 회사를 기준으로 section mapper가 어디까지 포화되었는지 측정한다.
- latest annual section title 기준으로 broad mapper 잔여가 실제로 얼마나 남았는지 확인한다.

가설:
1. 현재 mapper.py 패턴 보강 이후 latest annual section title 매핑률은 99.9%에 근접한다.
2. 남은 미매핑 title은 소수의 저빈도 예외로 수렴한다.

방법:
1. `data/dart/docs/*.parquet` 전부를 스캔한다.
2. 각 회사의 최신 `사업보고서`만 골라 `section_title`을 `mapSectionTitle()`에 통과시킨다.
3. `mapped != normalized` 기준으로 매핑률, 미매핑 row 수, 남은 title 목록을 집계한다.

결과 (실험 후 작성):
- latest annual 대상 회사 수: `245`
- latest annual title rows: `12,667`
- mapped rows: `12,661`
- mapped ratio: `0.999526`
- unmapped rows: `6`
- unmapped unique titles: `3`
- 잔여 title:
  - `주유소부동산세부내역(상세)` `4`
  - `4-6.사업의개요-시장여건및영업의개황등(상세)` `1`
  - `사업의내용과관련된사항` `1`

결론:
- 현재 section mapper는 latest annual title 기준으로 사실상 포화 단계다.
- 남은 3개 title은 반복 회사가 거의 없고 의미도 더 애매해, broad mapper 확대보다 semantic/detail projector 또는 수동 검토가 더 적절하다.

실험일: 2026-03-19
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

from dartlab.engines.dart.docs.sections.mapper import mapSectionTitle, normalizeSectionTitle
DOCS_DIR = Path("data/dart/docs")
ANNUAL_KEYWORD = "사업보고서"


def latest_annual_mapping_audit() -> tuple[pl.DataFrame, pl.DataFrame]:
    rows: list[dict[str, object]] = []
    for path in sorted(DOCS_DIR.glob("*.parquet")):
        df = pl.read_parquet(path)
        annual = df.filter(pl.col("report_type").cast(pl.Utf8).str.contains(ANNUAL_KEYWORD, literal=True))
        if annual.is_empty():
            continue
        latest = annual["year"].max()
        titles = annual.filter(pl.col("year") == latest).sort("section_order").get_column("section_title").to_list()
        for title in titles:
            raw = (title or "").strip()
            if not raw:
                continue
            normalized = normalizeSectionTitle(raw)
            mapped = mapSectionTitle(raw)
            rows.append(
                {
                    "stockCode": path.stem,
                    "year": str(latest),
                    "normalizedTitle": normalized,
                    "mappedTopic": mapped,
                    "isMapped": mapped != normalized,
                }
            )

    full = pl.DataFrame(rows)
    unmapped = (
        full.filter(pl.col("isMapped").not_())
        .group_by("normalizedTitle")
        .agg(pl.len().alias("rows"), pl.col("stockCode").n_unique().alias("companies"))
        .sort(["rows", "companies", "normalizedTitle"], descending=[True, True, False])
    )
    return full, unmapped


def main() -> None:
    full, unmapped = latest_annual_mapping_audit()

    print("=" * 72)
    print("056-053 전 docs 포트폴리오 section mapper 감사")
    print("=" * 72)
    print(
        full.select(
            pl.col("stockCode").n_unique().alias("stocks"),
            pl.len().alias("rows"),
            pl.col("isMapped").sum().alias("mappedRows"),
            pl.col("isMapped").mean().round(6).alias("mappedRatio"),
        )
    )
    print()
    print("[unmapped latest annual titles]")
    print(unmapped)


if __name__ == "__main__":
    main()
