"""실험 ID: 098-017
실험명: 거시 선행지표 시차 상관 분석

목적:
- 경기선행지수(CLI), 산업생산(IPI), 소비자물가(CPI) 등 선행지표가
  6~12개월 후 섹터 매출 성장률과 유의미한 시차 상관을 보이는지
- 015/016에서 동시적(concurrent) 거시 회귀가 실패 → 선행(leading) 관계로 전환
- 선행지표가 존재하면 예측 타이밍 우위(information advantage) 확보 가능

가설:
1. CLI(경기선행지수) 6개월 선행 상관 > 0.3 (섹터 매출과)
2. IPI 3개월 선행 상관이 동시 상관보다 높음
3. 환율(USDKRW) 선행 상관이 수출 섹터에서 > 0.3

방법:
1. 거시 연간 시계열 (2016~2024) — 015와 동일 fallback 데이터
2. 섹터별 매출 성장률 (007/015와 동일)
3. 1년 전 거시 → 당해 매출 시차 상관 (연간 데이터라 lag=1년)
4. 동시 상관 vs 1년 선행 상관 비교
5. 최적 선행지표 조합 → 단순 예측 규칙 도출

결과:
| 지표 | 동시|r| | 선행|r| | 선행-동시 |
|------|---------|---------|-----------|
| GDP | 0.472 | 0.336 | -0.136 |
| FX | 0.330 | 0.361 | +0.031 |
| RATE | 0.402 | 0.448 | +0.046 |
| IPI | 0.518 | 0.305 | -0.212 |
| OIL | 0.546 | 0.392 | -0.153 |
| CPI | 0.402 | 0.403 | +0.001 |

- 선행 |r|>0.3 조합: 29/48개 (60%) — 수치상으로는 많음
- 선행이 동시보다 +0.1 이상 개선: 7/48개 (15%) — FX, RATE가 일부 섹터에서
- **방향 예측 정확도: 48.2%** (랜덤 50%와 동일)
  - 반도체/자동차/화학 85.7% vs 통신/식품/IT 0%
  - 0%인 섹터: 음의 lag 상관인데 해당 기간 매출이 계속 양수 → 부호 규칙 실패
- 히트맵: 철강에 5/6 지표가 |r|>0.3, IT에도 4/6 — but 과적합 시그널

결론:
- **가설 1 기각**: CLI 대신 CPI/RATE가 높은 lag r 보이지만 방향 예측 0% (음의 상관 함정)
- **가설 2 기각**: IPI 선행이 동시보다 평균 -0.21 악화 (동시가 더 강함)
- **가설 3 부분 확인**: FX lag r = 화학 -0.672, 철강 -0.630 (but 부호 반전)
- **핵심 발견**: 높은 lag 상관 ≠ 예측력. 8개 연간 데이터의 상관은 spurious
  1. 음의 lag 상관이 다수 → 금리↑ → 1년 후 매출↓ 논리적이나 방향 예측 불가
  2. 상관 크기는 높지만 n=8로 통계적 유의성 부족 (p>0.05가 대부분)
  3. 전체 방향 정확도 48.2% = 동전 던지기와 동일
- **Phase E 중간 결론**: 연간 8개 관측치로는 동시든 선행이든 거시→매출 예측 불가

실험일: 2026-03-25
"""

import time
from pathlib import Path

import numpy as np
import polars as pl

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "dart"
FINANCE_DIR = DATA_DIR / "finance"

# 거시 시계열 (fallback 하드코딩)
MACRO_SERIES = {
    "GDP": {
        "2015": 2.8, "2016": 2.9, "2017": 3.2, "2018": 2.9, "2019": 2.2,
        "2020": -0.7, "2021": 4.3, "2022": 2.6, "2023": 1.4, "2024": 2.0,
    },
    "FX": {  # 원/달러 YoY%
        "2015": 7.0, "2016": -2.0, "2017": -2.8, "2018": 0.6, "2019": 5.9,
        "2020": -0.4, "2021": 0.5, "2022": 12.5, "2023": 3.1, "2024": 7.0,
    },
    "RATE": {  # 기준금리 연말 수준
        "2015": 1.50, "2016": 1.25, "2017": 1.50, "2018": 1.75, "2019": 1.25,
        "2020": 0.50, "2021": 1.00, "2022": 3.25, "2023": 3.50, "2024": 3.00,
    },
    "IPI": {  # 산업생산지수 YoY%
        "2015": -0.3, "2016": 1.1, "2017": 2.1, "2018": 1.3, "2019": -0.7,
        "2020": -0.8, "2021": 7.5, "2022": 0.6, "2023": 2.1, "2024": 3.5,
    },
    "OIL": {  # WTI YoY%
        "2015": -47.8, "2016": -11.0, "2017": 12.5, "2018": 27.4, "2019": -12.1,
        "2020": -30.5, "2021": 73.5, "2022": 5.5, "2023": -18.1, "2024": -2.5,
    },
    "CPI": {  # 소비자물가 YoY%
        "2015": 0.7, "2016": 1.0, "2017": 1.9, "2018": 1.5, "2019": 0.4,
        "2020": 0.5, "2021": 2.5, "2022": 5.1, "2023": 3.6, "2024": 2.3,
    },
}

# 섹터별 매출 성장률 (015 실험과 동일)
SECTOR_REVENUE_GROWTH = {
    "반도체": {"2017": 21.8, "2018": 1.4, "2019": -29.1, "2020": 4.0,
              "2021": 28.5, "2022": -8.0, "2023": -14.7, "2024": 35.2},
    "자동차": {"2017": 2.3, "2018": 2.0, "2019": 2.9, "2020": -9.8,
              "2021": 16.3, "2022": 18.6, "2023": 12.7, "2024": 3.1},
    "화학": {"2017": 15.1, "2018": 12.0, "2019": -8.5, "2020": -10.4,
            "2021": 35.0, "2022": 6.3, "2023": -12.6, "2024": -2.1},
    "철강": {"2017": 10.2, "2018": 7.0, "2019": -5.3, "2020": -7.8,
            "2021": 27.0, "2022": -3.5, "2023": -10.7, "2024": 0.5},
    "통신": {"2017": 2.1, "2018": 3.5, "2019": 2.8, "2020": 3.0,
            "2021": 2.5, "2022": 3.2, "2023": 1.5, "2024": 0.9},
    "식품": {"2017": 3.5, "2018": 3.2, "2019": 1.8, "2020": 5.5,
            "2021": 8.2, "2022": 12.1, "2023": 5.3, "2024": 1.0},
    "IT/소프트웨어": {"2017": 15.2, "2018": 17.1, "2019": 12.5, "2020": 21.3,
                    "2021": 16.0, "2022": 9.5, "2023": 5.2, "2024": 8.0},
    "유통": {"2017": 5.3, "2018": 3.5, "2019": -2.1, "2020": -8.5,
            "2021": 12.0, "2022": 8.5, "2023": 3.1, "2024": 1.5},
}


def computeLagCorrelation():
    """동시 상관 vs 1년 선행 상관 비교."""
    years = ["2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024"]
    lagYears = ["2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023"]

    results = []

    for macroName, macroData in MACRO_SERIES.items():
        for sectorName, sectorData in SECTOR_REVENUE_GROWTH.items():
            # 동시 상관 (같은 해)
            macroVals = [macroData[y] for y in years]
            sectorVals = [sectorData[y] for y in years]

            if np.std(macroVals) > 0 and np.std(sectorVals) > 0:
                concurrentCorr = np.corrcoef(macroVals, sectorVals)[0, 1]
            else:
                concurrentCorr = 0.0

            # 1년 선행 상관 (t-1 거시 → t 매출)
            macroLag = [macroData[y] for y in lagYears]
            if np.std(macroLag) > 0 and np.std(sectorVals) > 0:
                lagCorr = np.corrcoef(macroLag, sectorVals)[0, 1]
            else:
                lagCorr = 0.0

            results.append({
                "macro": macroName,
                "sector": sectorName,
                "concurrent": round(concurrentCorr, 3),
                "lag1yr": round(lagCorr, 3),
                "lagImprovement": round(lagCorr - concurrentCorr, 3),
                "absLag": round(abs(lagCorr), 3),
            })

    return pl.DataFrame(results)


def analyzeLeadingPower(df):
    """선행력이 강한 지표-섹터 조합 찾기."""
    # 선행 상관 |r| > 0.3인 조합
    strong = df.filter(pl.col("absLag") > 0.3).sort("absLag", descending=True)

    # 선행이 동시보다 개선된 조합
    improved = df.filter(pl.col("lagImprovement") > 0.1).sort("lagImprovement", descending=True)

    return strong, improved


def simpleForecastRule(df):
    """선행 상관 기반 단순 예측 규칙 생성 및 검증.

    가장 강한 lag 상관 조합으로 부호 방향 예측 정확도 측정.
    """
    years = ["2018", "2019", "2020", "2021", "2022", "2023", "2024"]
    lagYears = ["2017", "2018", "2019", "2020", "2021", "2022", "2023"]

    # 각 섹터에서 가장 강한 선행지표 선택
    bestBySection = {}
    for sector in SECTOR_REVENUE_GROWTH:
        sectorRows = df.filter(pl.col("sector") == sector)
        best = sectorRows.sort("absLag", descending=True).head(1)
        if len(best) > 0:
            bestBySection[sector] = best.row(0, named=True)

    # 부호 방향 예측 정확도
    totalCorrect = 0
    totalPredictions = 0
    sectorResults = {}

    for sector, bestRow in bestBySection.items():
        macroName = bestRow["macro"]
        lagSign = 1.0 if bestRow["lag1yr"] > 0 else -1.0
        macroData = MACRO_SERIES[macroName]
        sectorData = SECTOR_REVENUE_GROWTH[sector]

        correct = 0
        total = 0
        for yr, lagYr in zip(years, lagYears):
            macroPrev = macroData[lagYr]
            actualGrowth = sectorData[yr]

            # 예측: lagSign * sign(macroPrev) → 매출 방향
            predictedDir = lagSign * np.sign(macroPrev)
            actualDir = np.sign(actualGrowth)

            if predictedDir == actualDir:
                correct += 1
            total += 1

        accuracy = correct / total if total > 0 else 0
        sectorResults[sector] = {
            "bestMacro": macroName,
            "lagCorr": bestRow["lag1yr"],
            "directionAccuracy": round(accuracy * 100, 1),
        }
        totalCorrect += correct
        totalPredictions += total

    overallAccuracy = totalCorrect / totalPredictions if totalPredictions > 0 else 0
    return sectorResults, round(overallAccuracy * 100, 1)


def main():
    startTime = time.time()

    print("=" * 70)
    print("  098-017: 거시 선행지표 시차 상관 분석")
    print("=" * 70)

    # 1. 시차 상관 계산
    print("\n  시차 상관 계산 중...")
    df = computeLagCorrelation()

    # 2. 지표별 평균 상관 요약
    print("\n" + "=" * 70)
    print("  지표별 평균 상관 (동시 vs 1년 선행)")
    print("=" * 70)
    print(f"\n  {'지표':<8} {'동시|r|':>8} {'선행|r|':>8} {'선행-동시':>10}  선행 우위?")
    print(f"  {'─' * 48}")

    for macro in MACRO_SERIES:
        subset = df.filter(pl.col("macro") == macro)
        avgConcurrent = subset["concurrent"].abs().mean()
        avgLag = subset["absLag"].mean()
        diff = avgLag - avgConcurrent
        better = "✓" if diff > 0.02 else "—"
        print(f"  {macro:<8} {avgConcurrent:>8.3f} {avgLag:>8.3f} {diff:>+10.3f}  {better}")

    # 3. 강한 선행 상관 조합
    strong, improved = analyzeLeadingPower(df)

    print(f"\n" + "=" * 70)
    print(f"  선행 상관 |r| > 0.3인 조합 ({len(strong)}개)")
    print("=" * 70)
    if len(strong) > 0:
        print(f"\n  {'지표':<8} {'섹터':<12} {'동시':>6} {'선행':>6} {'개선':>6}")
        print(f"  {'─' * 42}")
        for row in strong.iter_rows(named=True):
            print(f"  {row['macro']:<8} {row['sector']:<12} {row['concurrent']:>+6.3f} {row['lag1yr']:>+6.3f} {row['lagImprovement']:>+6.3f}")

    # 4. 선행이 동시보다 +0.1 이상 개선된 조합
    print(f"\n" + "=" * 70)
    print(f"  선행이 동시보다 +0.1 이상 개선 ({len(improved)}개)")
    print("=" * 70)
    if len(improved) > 0:
        for row in improved.iter_rows(named=True):
            print(f"  {row['macro']:<8} {row['sector']:<12} 동시={row['concurrent']:>+.3f} → 선행={row['lag1yr']:>+.3f} ({row['lagImprovement']:>+.3f})")

    # 5. 방향 예측 정확도
    print(f"\n" + "=" * 70)
    print(f"  선행지표 기반 방향 예측 정확도")
    print("=" * 70)

    sectorResults, overallAccuracy = simpleForecastRule(df)
    print(f"\n  {'섹터':<12} {'최적 선행지표':<10} {'lag r':>8} {'방향 정확':>10}")
    print(f"  {'─' * 44}")
    for sector, info in sectorResults.items():
        print(f"  {sector:<12} {info['bestMacro']:<10} {info['lagCorr']:>+8.3f} {info['directionAccuracy']:>9.1f}%")

    print(f"\n  전체 평균 방향 정확도: {overallAccuracy}%")
    print(f"  (참고: 랜덤 50%, 동시 GDP 방향 정확도 ~60%)")

    # 6. 섹터-지표 히트맵 (선행 상관)
    print(f"\n" + "=" * 70)
    print(f"  선행 상관 히트맵 (1년 lag)")
    print("=" * 70)

    sectors = list(SECTOR_REVENUE_GROWTH.keys())
    macros = list(MACRO_SERIES.keys())

    header = f"  {'':>12}" + "".join(f"{m:>8}" for m in macros)
    print(header)
    print(f"  {'─' * (12 + 8 * len(macros))}")

    for sector in sectors:
        row = df.filter(pl.col("sector") == sector)
        vals = []
        for macro in macros:
            cell = row.filter(pl.col("macro") == macro)
            if len(cell) > 0:
                v = cell["lag1yr"][0]
                marker = "*" if abs(v) > 0.3 else " "
                vals.append(f"{v:>+7.3f}{marker}")
            else:
                vals.append(f"{'—':>8}")
        print(f"  {sector:>12}" + "".join(vals))

    print(f"\n  (* = |r| > 0.3)")

    elapsed = time.time() - startTime
    print(f"\n  소요시간: {elapsed:.1f}s")
    print("\n실험 완료.")


if __name__ == "__main__":
    main()
