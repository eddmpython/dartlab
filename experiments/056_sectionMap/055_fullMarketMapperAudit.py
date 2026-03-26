"""
실험 ID: 056-055
실험명: 전체 시장 (2,600+종목) section mapper 매핑률 측정

목적:
- 054까지 319종목(310+9)에서 100% 달성했지만, HuggingFace 데이터 대량 추가로
  2,621종목으로 확대됨. 신규 2,300+ 종목에서 미매핑 title을 전수 조사한다.

가설:
1. 319종목 기준 100%였지만, 신규 종목(특히 소형/금융/특수업종)에서
   매핑률이 95% 이하로 떨어지는 구간이 있을 것이다.
2. 빈도 3+ 미매핑 title은 정규화 또는 JSON 흡수로 해결 가능할 것이다.

방법:
1. data/dart/docs/*.parquet 전체(2,621개) 스캔
2. 모든 section_title → mapSectionTitle() 통과
3. 전체/annual/quarterly 매핑률 집계
4. 미매핑 title 빈도순 정렬 → 상위 50개 출력

결과 (실험 후 작성):
- 종목 수: 2,547 (이전 054: 319)
- 전체 title rows: 3,978,643 (054: 258,594)
- 1차 (보강 전): 매핑률 99.890%, 미매핑 4,363 rows, 고유 506개 title
  - 주요 미매핑: 감사 관련 4개(663 rows, 144사), 회사 특화 상세표 다수
- 2차 (JSON 26개 + (상세) suffix fallback + _ suffix fallback 추가): 99.920%, 미매핑 3,185, 고유 473
- 3차 (regex 38개 추가 — 바이오/특허/설비/금융/유통): 99.950%, 미매핑 1,996, 고유 417
- 4차 (regex 22개 추가 — 넓은 캐치 패턴): 99.983%, 미매핑 658, 고유 240
- 5차 (regex 35개 추가 — 잔여 고빈도): 99.992%, 미매핑 304, 고유 169
  - 사업보고서: 1,235,989 rows → 99.992%
  - 분기보고서: 1,814,415 rows → 99.996%
  - 반기보고서: 928,239 rows → 99.985%
- 미매핑 304건 내역: 깨진 인코딩(~50건), 빈 title(~10건), (section-2) artifact(6건), 1사 전용 극소량 표현
- sectionMappings.json: 545 → 571개 (+26)
- _PATTERN_MAPPINGS: 110 → 205개 (+95)

결론:
- 2,547종목 전수 매핑률 99.992% 달성 (054의 319종목 100%에서 8배 확대)
- 신규 2,200+ 종목에서 발견된 미매핑은 감사 상세(144사 공통) + 회사 특화 상세표 2종류
- (상세) suffix fallback + _ suffix fallback 로직으로 회사명 prefix 자동 분리
- 잔여 304건은 깨진 인코딩(원본 parquet 문제), 빈 title, 1사 전용 극소표현으로 매퍼 한계
- 실질 매핑 가능 ceiling에 도달

실험일: 2026-03-26
"""

from __future__ import annotations

import time
from pathlib import Path

import polars as pl

from dartlab.engines.company.dart.docs.sections.mapper import (
    mapSectionTitle,
    normalizeSectionTitle,
)

DOCS_DIR = Path("data/dart/docs")


def audit() -> None:
    """전체 시장 매핑률 측정."""
    rows: list[dict[str, object]] = []
    t0 = time.time()
    paths = sorted(DOCS_DIR.glob("*.parquet"))
    print(f"[scan] {len(paths)} parquet files")

    for i, path in enumerate(paths):
        if (i + 1) % 500 == 0:
            print(f"[scan] {i + 1}/{len(paths)} ({time.time() - t0:.0f}s)")
        stockCode = path.stem
        try:
            df = pl.read_parquet(path, columns=["section_title", "report_type", "year"])
        except Exception:
            continue

        for row in df.iter_rows(named=True):
            raw = (row.get("section_title") or "").strip()
            if not raw:
                continue
            reportType = str(row.get("report_type", ""))
            year = str(row.get("year", ""))
            normalized = normalizeSectionTitle(raw)
            mapped = mapSectionTitle(raw)
            rows.append(
                {
                    "stockCode": stockCode,
                    "year": year,
                    "reportType": reportType,
                    "rawTitle": raw,
                    "normalizedTitle": normalized,
                    "mappedTopic": mapped,
                    "isMapped": mapped != normalized,
                }
            )

    elapsed = time.time() - t0
    print(f"\n[done] {len(paths)} files, {len(rows)} title rows, {elapsed:.1f}s\n")

    full = pl.DataFrame(rows)

    # 전체 매핑률
    total = full.shape[0]
    mappedCount = full.filter(pl.col("isMapped")).shape[0]
    rate = mappedCount / total * 100 if total else 0
    print(f"== 전체 매핑률 ==")
    print(f"  total: {total:,}, mapped: {mappedCount:,}, rate: {rate:.3f}%\n")

    # annual / quarterly
    for rt in ["사업보고서", "분기보고서", "반기보고서"]:
        sub = full.filter(pl.col("reportType").str.contains(rt))
        n = sub.shape[0]
        m = sub.filter(pl.col("isMapped")).shape[0]
        r = m / n * 100 if n else 0
        print(f"  {rt}: {n:,} rows, {r:.3f}%")

    # 미매핑 빈도
    unmapped = full.filter(~pl.col("isMapped"))
    if unmapped.shape[0] == 0:
        print("\n미매핑 0건 — 100% 달성")
        return

    freq = (
        unmapped.group_by("normalizedTitle")
        .agg(
            pl.len().alias("count"),
            pl.col("stockCode").n_unique().alias("companies"),
            pl.col("rawTitle").first().alias("exampleRaw"),
        )
        .sort("count", descending=True)
    )

    print(f"\n== 미매핑: {unmapped.shape[0]:,} rows, {freq.shape[0]} 고유 title ==")
    print(f"\n상위 50:")
    top50 = freq.head(50)
    for row in top50.iter_rows(named=True):
        print(
            f"  [{row['count']:>5}] ({row['companies']:>4}사) "
            f"{row['normalizedTitle']!r}  ← {row['exampleRaw']!r}"
        )

    # 빈도 구간별 분포
    print(f"\n== 빈도 구간 ==")
    for lo, hi, label in [(100, 999999, "100+"), (10, 99, "10~99"), (3, 9, "3~9"), (1, 2, "1~2")]:
        band = freq.filter((pl.col("count") >= lo) & (pl.col("count") <= hi))
        print(f"  {label}: {band.shape[0]}개 title, {band['count'].sum()} rows")


if __name__ == "__main__":
    audit()
