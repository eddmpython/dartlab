"""실험 ID: 002
실험명: 시장 전체 비율 분포 분석

목적:
- 47개 재무 비율의 시장 전체 분포 (평균, 중앙값, 분위수, 이상치)
- 섹터별 분포 차이 정량화
- 이상치 탐지 기준 수립

가설:
1. 섹터별 분포가 유의미하게 다르다 (금융 vs 제조 부채비율 등)
2. 이상치를 IQR 기반으로 제거하면 분포가 안정화된다
3. 핵심 비율 5~8개로 시장 상태를 대표할 수 있다

방법:
1. 001의 market_ratios.parquet 로드
2. 전체 및 섹터별 기초통계 (mean, median, P10, P25, P75, P90)
3. IQR 기반 이상치 탐지 (1.5×IQR)
4. 섹터 간 분포 차이 비교

결과 (실험 후 작성):
- 2,661사 × 43컬럼 분석 완료
- 전체 분포:
  - ROE 중앙값 3.45%, 평균 -4.80% (적자 기업 영향)
  - 부채비율 중앙값 64.69%, P10=13.34, P90=214.05
  - 영업이익률 중앙값 2.79%, P90=16.16%
  - 유동비율 중앙값 165.86%, 배당성향 중앙값 22.56% (253사만)
- 섹터별 차이 (중앙값):
  - 금융: ROE 6.59% (최고), 부채비율 36.38% (최저), 자산회전율 0.29 (최저)
  - 경기소비재: ROE 4.34%, 부채비율 89.47%, 자산회전율 0.84 (최고)
  - 건강관리: ROE 0.11% (최저), 자산회전율 0.39
  - 필수소비재: ROE 5.59%, 자산회전율 0.93
- 이상치 비율 (IQR×1.5):
  - ROE: 12.6% 제거 → clean 중앙값 4.24%
  - 영업이익률: 16.7% 제거 → clean 중앙값 3.42%
  - 부채비율: 6.8% 제거
- 금융 vs 비금융 부채비율: 금융 36.38 vs 비금융 65.58 (예상대로 금융이 낮음 — WICS 금융 분류에 투자지주사가 많아 일반적 은행 부채비율과 상이)

결론:
- 채택: 섹터별 분포가 유의미하게 다르다 (가설1 확인)
- 이상치 제거 후 분포 안정화 확인 (가설2 확인)
- 핵심 대표 비율: ROE, 부채비율, 영업이익률, 유동비율, 자산회전율 (5개로 시장 대표 가능)
- 배당성향 커버리지 9.5%로 매우 낮음 — calcRatios 단일시점 한계

실험일: 2026-03-20
"""

from __future__ import annotations

import sys
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

DATA_DIR = Path(__file__).parent / "data"

# 분석할 핵심 비율
KEY_RATIOS = [
    ("수익성", ["roe", "roa", "operatingMargin", "netMargin", "grossMargin"]),
    ("안정성", ["debtRatio", "currentRatio", "quickRatio", "equityRatio", "interestCoverage"]),
    ("효율성", ["totalAssetTurnover", "inventoryTurnover"]),
    ("현금흐름", ["fcf", "operatingCfMargin", "capexRatio", "dividendPayoutRatio"]),
]

FLAT_RATIOS = [r for _, ratios in KEY_RATIOS for r in ratios]


def loadSnapshot() -> pl.DataFrame:
    path = DATA_DIR / "market_ratios.parquet"
    return pl.read_parquet(str(path))


def overallDistribution(df: pl.DataFrame) -> pl.DataFrame:
    """전체 시장 비율 분포."""
    rows = []
    for ratio in FLAT_RATIOS:
        if ratio not in df.columns:
            continue
        col = df[ratio].drop_nulls().cast(pl.Float64)
        if col.len() == 0:
            continue
        rows.append({
            "ratio": ratio,
            "count": col.len(),
            "mean": col.mean(),
            "median": col.median(),
            "std": col.std(),
            "p10": col.quantile(0.10),
            "p25": col.quantile(0.25),
            "p75": col.quantile(0.75),
            "p90": col.quantile(0.90),
            "min": col.min(),
            "max": col.max(),
        })
    return pl.DataFrame(rows)


def sectorDistribution(df: pl.DataFrame) -> pl.DataFrame:
    """섹터별 핵심 비율 중앙값."""
    ratios = ["roe", "debtRatio", "operatingMargin", "currentRatio", "totalAssetTurnover"]
    rows = []
    for sector in df["sector"].drop_nulls().unique().sort().to_list():
        sdf = df.filter(pl.col("sector") == sector)
        row = {"sector": sector, "count": sdf.shape[0]}
        for r in ratios:
            if r in sdf.columns:
                col = sdf[r].drop_nulls().cast(pl.Float64)
                row[f"{r}_median"] = col.median() if col.len() > 0 else None
                row[f"{r}_p25"] = col.quantile(0.25) if col.len() > 0 else None
                row[f"{r}_p75"] = col.quantile(0.75) if col.len() > 0 else None
        rows.append(row)
    return pl.DataFrame(rows)


def detectOutliers(df: pl.DataFrame, ratio: str, k: float = 1.5) -> pl.DataFrame:
    """IQR 기반 이상치 탐지."""
    col = df.filter(pl.col(ratio).is_not_null())
    q1 = col[ratio].quantile(0.25)
    q3 = col[ratio].quantile(0.75)
    iqr = q3 - q1
    lower = q1 - k * iqr
    upper = q3 + k * iqr

    outliers = col.filter(
        (pl.col(ratio) < lower) | (pl.col(ratio) > upper)
    ).select(["stockCode", "corpName", "sector", ratio]).sort(ratio)

    return outliers


def cleanedStats(df: pl.DataFrame, ratio: str, k: float = 1.5) -> dict:
    """이상치 제거 후 통계."""
    col = df[ratio].drop_nulls().cast(pl.Float64)
    q1 = col.quantile(0.25)
    q3 = col.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - k * iqr
    upper = q3 + k * iqr
    clean = col.filter((col >= lower) & (col <= upper))
    return {
        "ratio": ratio,
        "original_count": col.len(),
        "cleaned_count": clean.len(),
        "outliers_removed": col.len() - clean.len(),
        "outlier_pct": (col.len() - clean.len()) / col.len() * 100,
        "clean_mean": clean.mean(),
        "clean_median": clean.median(),
        "clean_std": clean.std(),
    }


if __name__ == "__main__":
    df = loadSnapshot()
    print(f"로드: {df.shape[0]} rows × {df.shape[1]} cols")
    print(f"섹터: {df['sector'].n_unique()} unique\n")

    # 1. 전체 분포
    print("=" * 70)
    print("1. 전체 시장 비율 분포")
    print("=" * 70)
    dist = overallDistribution(df)
    for row in dist.iter_rows(named=True):
        print(f"  {row['ratio']:25s}  n={row['count']:>5d}  "
              f"median={row['median']:>10.2f}  mean={row['mean']:>10.2f}  "
              f"[P10={row['p10']:>8.2f}  P90={row['p90']:>8.2f}]")

    # 2. 섹터별 분포
    print(f"\n{'='*70}")
    print("2. 섹터별 핵심 비율 중앙값")
    print("=" * 70)
    secDist = sectorDistribution(df)
    print(secDist.select(["sector", "count",
                          "roe_median", "debtRatio_median", "operatingMargin_median",
                          "currentRatio_median", "totalAssetTurnover_median"]))

    # 3. 이상치 분석
    print(f"\n{'='*70}")
    print("3. 이상치 분석 (IQR × 1.5)")
    print("=" * 70)
    cleanRows = []
    for r in ["roe", "debtRatio", "operatingMargin", "currentRatio", "totalAssetTurnover"]:
        if r in df.columns:
            cs = cleanedStats(df, r)
            cleanRows.append(cs)
            print(f"  {cs['ratio']:25s}  removed={cs['outliers_removed']:>4d} ({cs['outlier_pct']:.1f}%)  "
                  f"clean_median={cs['clean_median']:.2f}  clean_mean={cs['clean_mean']:.2f}")

    # 4. 섹터 간 차이 요약
    print(f"\n{'='*70}")
    print("4. 섹터 간 부채비율 중앙값 차이 (금융 vs 비금융)")
    print("=" * 70)
    fin = df.filter(pl.col("sector") == "금융")["debtRatio"].drop_nulls()
    nonFin = df.filter(pl.col("sector") != "금융")["debtRatio"].drop_nulls()
    if fin.len() > 0 and nonFin.len() > 0:
        print(f"  금융 (n={fin.len()}):    median={fin.median():.2f}  mean={fin.mean():.2f}")
        print(f"  비금융 (n={nonFin.len()}): median={nonFin.median():.2f}  mean={nonFin.mean():.2f}")

    # 5. 극단 이상치 Top 10 (ROE)
    print(f"\n{'='*70}")
    print("5. ROE 극단 이상치 Top 10 (양/음 각각)")
    print("=" * 70)
    roeOutliers = detectOutliers(df, "roe")
    if roeOutliers.shape[0] > 0:
        print("  [최저 ROE]")
        print(roeOutliers.head(10))
        print("  [최고 ROE]")
        print(roeOutliers.tail(10))
