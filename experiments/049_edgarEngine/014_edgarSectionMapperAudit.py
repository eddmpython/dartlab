"""
실험 ID: 049-014
실험명: EDGAR 전 종목 × 전 기간 section mapper 감사

목적:
- 현재 986개 EDGAR docs parquet을 전수 스캔하여 section mapper 포화도를 측정한다.
- 10-K/10-Q/20-F/40-F 각 form별 매핑률과 미매핑 title을 수집한다.

가설:
1. 10-K/10-Q는 표준화 정도가 높아 매핑률 95%+일 것이다.
2. 20-F/40-F는 비표준 section이 많아 매핑률이 낮을 것이다.

방법:
1. `data/edgar/docs/*.parquet` 전부 스캔
2. 모든 section_title을 mapSectionTitle()에 통과
3. normalized != mapped 기준으로 매핑률 집계
4. form별, 빈도별 미매핑 title 분석

결과 (실험 후 작성):
- 종목 수: 997 (수집 진행 중, 974→997+)
- 전체 title rows: 485,285
- 1차 스캔 (보강 전): 매핑률 99.99%, 미매핑 37 rows, 고유 7개 title
  - BX 10-Q "UNAUDITED SUPPLEMENTAL" (30 rows) — Item 1A 오분류
  - UL 20-F Item 5A/3D 변형 (4 rows)
  - NEM 10-K Item 4B 파이프 오타 (1 row)
  - LOW 10-Q Part II Item 103 Reg S-K (1 row)
  - UNP 10-K Item 601 Reg S-K 변형 (1 row)
- 보강 후: 매핑률 100.000%, 미매핑 0
- 보강 내용:
  - mapper.py: UNAUDITED SUPPLEMENTAL 오타 보정, Item 4B/5A/3D 처리, Part-Reg S-K 3자리 수렴
  - sectionMappings.json: 199 → 201개 (+2)
- Form별: 10-K 100%, 10-Q 100%, 20-F 100%, 40-F 100%

결론:
- EDGAR section mapper도 전 종목 × 전 기간 100% 포화 달성
- 주요 미매핑 원인: OCR/파이프 오타(BX, NEM), 20-F 비표준 Item 번호(UL), Regulation S-K 변형(LOW, UNP)
- DART(258K rows)과 EDGAR(485K rows) 합산 74만+ rows에서 양쪽 모두 100%

실험일: 2026-03-20
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

from dartlab.providers.edgar.docs.sections.mapper import (
    mapSectionTitle,
    normalizeSectionTitle,
)

DOCS_DIR = Path("data/edgar/docs")


def edgar_mapper_audit() -> tuple[pl.DataFrame, pl.DataFrame]:
    """전 종목 × 전 기간 EDGAR section 매핑 감사."""
    rows: list[dict[str, object]] = []
    for path in sorted(DOCS_DIR.glob("*.parquet")):
        ticker = path.stem
        df = pl.read_parquet(path)
        for row in df.iter_rows(named=True):
            raw = (row.get("section_title") or "").strip()
            if not raw:
                continue
            form_type = str(row.get("form_type", ""))
            year = str(row.get("year", ""))
            normalized = normalizeSectionTitle(raw)
            mapped = mapSectionTitle(form_type, raw)
            # mapped format: "{formType}::{topicId}"
            topic = mapped.split("::", 1)[1] if "::" in mapped else mapped
            is_mapped = topic != normalized
            rows.append(
                {
                    "ticker": ticker,
                    "year": year,
                    "formType": form_type,
                    "rawTitle": raw,
                    "normalizedTitle": normalized,
                    "mappedTopic": topic,
                    "isMapped": is_mapped,
                }
            )

    full = pl.DataFrame(rows)
    unmapped = (
        full.filter(pl.col("isMapped").not_())
        .group_by("normalizedTitle")
        .agg(
            pl.len().alias("rows"),
            pl.col("ticker").n_unique().alias("tickers"),
            pl.col("formType").first().alias("exampleForm"),
            pl.col("rawTitle").first().alias("exampleRaw"),
            pl.col("ticker").first().alias("exampleTicker"),
        )
        .sort(["rows", "tickers"], descending=[True, True])
    )
    return full, unmapped


def main() -> None:
    full, unmapped = edgar_mapper_audit()

    total = full.height
    mapped = full["isMapped"].sum()
    tickers = full["ticker"].n_unique()

    print("=" * 72)
    print("049-014 EDGAR 전 종목 × 전 기간 section mapper 감사")
    print("=" * 72)
    print(f"종목 수: {tickers}")
    print(f"전체 title rows: {total:,}")
    print(f"매핑 rows: {mapped:,}")
    print(f"매핑률: {mapped / total:.6f}" if total else "N/A")
    print(f"미매핑 rows: {total - mapped:,}")
    print(f"미매핑 고유 title: {unmapped.height}")
    print()

    # form별 매핑률
    by_form = (
        full.group_by("formType")
        .agg(
            pl.len().alias("rows"),
            pl.col("isMapped").mean().round(6).alias("mappedRatio"),
            pl.col("isMapped").not_().sum().alias("unmappedRows"),
        )
        .sort("rows", descending=True)
    )
    print("[Form별 매핑률]")
    print(by_form)
    print()

    # 미매핑 top 40
    pl.Config.set_tbl_rows(50)
    pl.Config.set_fmt_str_lengths(70)
    print(f"[미매핑 title top 40 / 전체 {unmapped.height}개]")
    print(unmapped.head(40))


if __name__ == "__main__":
    main()
