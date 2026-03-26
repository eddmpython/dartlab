"""실험 ID: 012
실험명: DART ↔ EDGAR 한미 비교

목적:
- 동일 ratios로 한국(DART 2,661사) vs 미국(EDGAR ~970사) 비교
- 섹터별 한미 구조적 차이 정량화
- 양국 재무 분포 차이의 크기와 방향 파악

가설:
1. 같은 업종의 한미 기업 간 ROE/부채비율에 구조적 차이가 있다
2. 미국 기업이 전반적으로 ROE가 높고 부채비율도 높다 (레버리지 경영)
3. 한국은 소재/산업재 비중이 높고 미국은 IT/건강관리 비중이 높다

방법:
1. DART market_ratios.parquet (001 결과) 로드
2. EDGAR finance 랜덤 500사 → buildTimeseries → calcRatios 수집
3. 공통 비율 기준 비교

결과 (실험 후 작성):
- EDGAR 483/500사 수집 (130s), 실패 17건
- 한미 비율 비교 (중앙값):
  - ROE: DART 3.45% vs EDGAR 15.74% (+12.29) — 미국이 훨씬 높음
  - 부채비율: DART 64.69% vs EDGAR 60.43% (-4.26) — 비슷
  - 유동비율: DART 165.9% vs EDGAR 118.5% (-47.4) — 한국이 높음
  - 자기자본비율: DART 59.7% vs EDGAR 23.5% (-36.2) — 한국이 높음
  - 총자산: DART 2,061억원 vs EDGAR 2.1억달러 (단위 차이)
- EDGAR ROE n=29로 매우 적음 — EDGAR finance에서 equity 매핑이 아직 부족
- EDGAR equityRatio 평균 -2,694% — 음수 자본(자본잠식) 기업 포함

결론:
- 부분 채택: 한미 비교 프레임워크는 동작하나 EDGAR 비율 커버리지가 낮음
- 가설1 확인: ROE에서 구조적 차이 (미국 +12.29%p)
- 가설2 부분 확인: ROE는 미국이 높으나 부채비율은 비슷 (레버리지 가설 불일치)
- EDGAR finance 매핑 개선 필요 (ROE n=29/483 = 6%는 너무 낮음)

실험일: 2026-03-20
"""

from __future__ import annotations

import random
import sys
import time
from dataclasses import asdict
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

DATA_DIR = Path(__file__).parent / "data"

RATIO_FIELDS = [
    "roe", "roa", "operatingMargin", "netMargin", "grossMargin",
    "debtRatio", "currentRatio", "equityRatio",
    "totalAssetTurnover",
    "revenueTTM", "totalAssets",
]


def loadDartSnapshot() -> pl.DataFrame:
    return pl.read_parquet(str(DATA_DIR / "market_ratios.parquet"))


def collectEdgarSnapshot(*, maxCompanies: int = 500, verbose: bool = True) -> pl.DataFrame:
    """EDGAR finance에서 랜덤 종목 ratios 수집."""
    from dartlab import config
    from dartlab.core.finance.ratios import calcRatios
    from dartlab.providers.edgar.finance.pivot import buildTimeseries

    edgarDir = Path(config.dataDir) / "edgar" / "finance"
    files = sorted(edgarDir.glob("*.parquet"))
    if verbose:
        print(f"EDGAR finance files: {len(files)}")

    # 랜덤 샘플
    random.seed(42)
    sample = random.sample(files, min(maxCompanies, len(files)))

    rows = []
    failed = 0
    t0 = time.time()

    for i, path in enumerate(sample):
        cik = path.stem
        if verbose and (i + 1) % 100 == 0:
            print(f"  [{i+1}/{len(sample)}] {time.time()-t0:.0f}s")

        try:
            result = buildTimeseries(cik)
            if result is None:
                failed += 1
                continue
            ts, periods = result
            rr = calcRatios(ts)
            rd = asdict(rr)
            row = {"cik": cik}
            for f in RATIO_FIELDS:
                row[f] = rd.get(f)
            rows.append(row)
        except Exception:
            failed += 1

    elapsed = time.time() - t0
    if verbose:
        print(f"EDGAR 수집: {len(rows)}/{len(sample)} ({elapsed:.1f}s), 실패: {failed}")

    # 스키마 명시 — 모든 비율 필드를 Float64로
    schema = {"cik": pl.Utf8}
    for f in RATIO_FIELDS:
        schema[f] = pl.Float64
    return pl.DataFrame(rows, schema=schema)


def compareDistributions(dartDf: pl.DataFrame, edgarDf: pl.DataFrame) -> pl.DataFrame:
    """한미 비율 분포 비교."""
    rows = []
    for r in RATIO_FIELDS:
        if r not in dartDf.columns or r not in edgarDf.columns:
            continue
        dCol = dartDf[r].drop_nulls().cast(pl.Float64)
        eCol = edgarDf[r].drop_nulls().cast(pl.Float64)
        if dCol.len() < 10 or eCol.len() < 10:
            continue
        rows.append({
            "ratio": r,
            "dart_n": dCol.len(),
            "dart_median": dCol.median(),
            "dart_mean": dCol.mean(),
            "edgar_n": eCol.len(),
            "edgar_median": eCol.median(),
            "edgar_mean": eCol.mean(),
            "diff_median": eCol.median() - dCol.median(),
        })
    return pl.DataFrame(rows)


if __name__ == "__main__":
    print("=== DART 로드 ===")
    dartDf = loadDartSnapshot()
    print(f"DART: {dartDf.shape[0]}사")

    print("\n=== EDGAR 수집 (500사 랜덤) ===")
    edgarDf = collectEdgarSnapshot(maxCompanies=500)
    print(f"EDGAR: {edgarDf.shape[0]}사")

    # 비교
    print(f"\n{'='*70}")
    print("1. 한미 비율 분포 비교")
    print("=" * 70)
    comp = compareDistributions(dartDf, edgarDf)
    print(comp)

    # 핵심 비율 상세
    print(f"\n{'='*70}")
    print("2. 핵심 비율 상세 비교")
    print("=" * 70)
    for r in ["roe", "debtRatio", "operatingMargin", "grossMargin", "totalAssetTurnover"]:
        if r not in dartDf.columns or r not in edgarDf.columns:
            continue
        dCol = dartDf[r].drop_nulls().cast(pl.Float64)
        eCol = edgarDf[r].drop_nulls().cast(pl.Float64)
        if dCol.len() < 10 or eCol.len() < 10:
            continue
        print(f"\n  [{r}]")
        print(f"    DART  (n={dCol.len():>5d}): median={dCol.median():>8.2f}  P25={dCol.quantile(0.25):>8.2f}  P75={dCol.quantile(0.75):>8.2f}")
        print(f"    EDGAR (n={eCol.len():>5d}): median={eCol.median():>8.2f}  P25={eCol.quantile(0.25):>8.2f}  P75={eCol.quantile(0.75):>8.2f}")
        diff = eCol.median() - dCol.median()
        print(f"    차이: EDGAR - DART = {diff:>+8.2f}")
