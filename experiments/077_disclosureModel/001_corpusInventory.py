"""
실험 ID: 001
실험명: DART+EDGAR 전체 텍스트/테이블 규모 감사

목적:
- 파인튜닝용 코퍼스의 총 규모를 정량화
- 회사별 데이터 분포(텍스트/테이블 행 수, 기간 수) 측정
- 파인튜닝 가능성의 1차 판단 근거 확보

가설:
1. DART 319개사 + EDGAR 974개사 → 총 100만+ 행의 sections 데이터 보유
2. 텍스트 블록이 전체의 60%+ (테이블보다 많음)
3. 기간 수 중앙값 5+ (시계열 비교 학습에 충분)

방법:
1. data/dart/docs/*.parquet, data/edgar/docs/*.parquet 파일 목록 수집
2. 각 파일을 sections pipeline으로 로드, blockType별 행 수 집계
3. 기간 컬럼 수(period columns) 측정
4. 회사별 통계(행 수, 기간 수, text/table 비율) 산출
5. 전체 합산 + 분포 출력

결과:
- DART: 319개사 전부 로드 성공
  - 총 행: 1,873,440 (text: 1,603,628 / table: 269,812)
  - 회사별 행 중앙값: 4,444, 평균: 5,872.9
  - 기간 컬럼 중앙값: 11, 평균: 16.7
  - topic 중앙값: 39
- EDGAR: 974개사 중 972개 성공 (2개 실패)
  - 총 행: 3,194,940 (text: 3,174,102 / table: 20,838)
  - 회사별 행 중앙값: 2,042, 평균: 3,287.0
  - 기간 컬럼 중앙값: 37, 평균: 38.8
  - topic 중앙값: 34
- 합산: 1,291개사, 5,068,380행
- text 비율: 94.3%
- 행 수 분포: p10=1195, p25=1560, p50=2382, p75=4442, p90=7814

결론:
- 500만+ 행으로 파인튜닝 코퍼스 규모 압도적 (가설1 5배 초과 달성)
- text 94.3% — 가설2 대비 훨씬 텍스트 중심. EDGAR table이 2만행뿐
- 기간 중앙값: DART 11, EDGAR 37 — 가설3 초과 (시계열 학습 충분)
- EDGAR 행 수가 DART의 1.7배지만, EDGAR 기간 수가 3.5배 → 기간당 행은 DART가 더 많음
- 채택: 코퍼스 규모로는 파인튜닝 충분히 가능

실험일: 2026-03-20
"""

import sys
import re
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from dartlab.config import dataDir


def _period_cols(df: pl.DataFrame) -> list[str]:
    """기간 컬럼만 추출 (2024, 2024Q1 등)."""
    return [c for c in df.columns if re.match(r"^\d{4}(Q[1-4])?$", c)]


def _load_sections(code: str, market: str) -> dict | None:
    """sections pipeline으로 로드 후 통계 반환."""
    try:
        if market == "DART":
            from dartlab.engines.company.dart.docs.sections.pipeline import sections
            df = sections(code)
        else:
            from dartlab.engines.company.edgar.docs.sections.pipeline import sections
            df = sections(code)

        if df is None or df.height == 0:
            return None

        periods = _period_cols(df)
        text_rows = df.filter(pl.col("blockType") == "text").height
        table_rows = df.filter(pl.col("blockType") == "table").height
        return {
            "market": market,
            "code": code,
            "rows": df.height,
            "text_rows": text_rows,
            "table_rows": table_rows,
            "period_count": len(periods),
            "topic_count": df["topic"].n_unique(),
        }
    except Exception as e:
        return None


def main():
    data = Path(dataDir)
    dart_dir = data / "dart" / "docs"
    edgar_dir = data / "edgar" / "docs"

    results = []

    # DART
    dart_files = sorted(dart_dir.glob("*.parquet"))
    print(f"DART docs: {len(dart_files)} files")
    for i, f in enumerate(dart_files):
        if i % 50 == 0:
            print(f"  DART progress: {i}/{len(dart_files)}")
        r = _load_sections(f.stem, "DART")
        if r:
            results.append(r)

    dart_ok = sum(1 for r in results if r["market"] == "DART")
    dart_fail = len(dart_files) - dart_ok
    print(f"DART: {dart_ok} loaded, {dart_fail} failed")

    # EDGAR
    edgar_files = sorted(edgar_dir.glob("*.parquet"))
    print(f"\nEDAGAR docs: {len(edgar_files)} files")
    for i, f in enumerate(edgar_files):
        if i % 100 == 0:
            print(f"  EDGAR progress: {i}/{len(edgar_files)}")
        r = _load_sections(f.stem, "EDGAR")
        if r:
            results.append(r)

    edgar_ok = sum(1 for r in results if r["market"] == "EDGAR")
    edgar_fail = len(edgar_files) - edgar_ok
    print(f"EDGAR: {edgar_ok} loaded, {edgar_fail} failed")

    # 집계
    df = pl.DataFrame(results)
    print(f"\n{'='*60}")
    print(f"총 회사: {df.height}")
    print(f"총 행: {df['rows'].sum():,}")
    print(f"  text: {df['text_rows'].sum():,}")
    print(f"  table: {df['table_rows'].sum():,}")
    text_ratio = df["text_rows"].sum() / df["rows"].sum() * 100
    print(f"  text 비율: {text_ratio:.1f}%")

    for market in ["DART", "EDGAR"]:
        sub = df.filter(pl.col("market") == market)
        if sub.height == 0:
            continue
        print(f"\n--- {market} ---")
        print(f"  회사: {sub.height}")
        print(f"  총 행: {sub['rows'].sum():,}")
        print(f"  text: {sub['text_rows'].sum():,} / table: {sub['table_rows'].sum():,}")
        print(f"  행 중앙값: {sub['rows'].median():.0f}, 평균: {sub['rows'].mean():.1f}")
        print(f"  기간 중앙값: {sub['period_count'].median():.0f}, 평균: {sub['period_count'].mean():.1f}")
        print(f"  topic 중앙값: {sub['topic_count'].median():.0f}")

    # 분포
    print(f"\n--- 행 수 분포 (전체) ---")
    for pct in [10, 25, 50, 75, 90]:
        val = df["rows"].quantile(pct / 100)
        print(f"  p{pct}: {val:.0f}")


if __name__ == "__main__":
    main()
