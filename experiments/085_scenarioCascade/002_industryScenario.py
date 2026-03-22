"""실험 ID: 002
실험명: 산업 특화 시나리오 vs 범용 GDP 시나리오 — 예측 정확도 비교

목적:
- 001에서 GDP-β 모델의 한계가 드러남 (IT R²=0.08, 필수소비재 이상값)
- 산업 특화 시나리오(반도체 사이클, 자동차 판매, 제약 파이프라인)가
  범용 GDP 시나리오보다 매출 예측에 우월한지 검증

가설:
1. 산업 특화 지표 기반 예측의 MAPE가 GDP 기반 대비 20%+ 개선
2. 반도체/자동차/식품 3섹터에서 산업 특화 우위 확인

방법:
1. 3섹터(IT/반도체, 산업재, 필수소비재) × 매출 시계열(2019-2024) 사용
2. 범용 예측: GDP 성장률 × 현행β → 예측 매출
3. 산업 특화 예측: 직전년도 성장률 + 섹터 평균 회귀(mean reversion) → 예측 매출
   (외부 산업 데이터 없이 내부 데이터만으로 가능한 최선의 산업 특화 접근)
4. 2023-2024 실적 대비 MAPE 비교

결과 (실행 후 작성):
- 수집: ~8s, 3섹터 27사, 테스트 기간 2023-2024, 학습 기간 2019-2022
- 섹터 평균 매출성장률 (학습기간): IT +31.2%, 산업재 +9.6%, 필수소비재 +18.5%
- 예측 비교:
  | 섹터         | GDP MAPE | MR MAPE | GDP방향 | MR방향 | N  | 우위 |
  |-------------|----------|---------|--------|-------|----|----|
  | IT/반도체     | 24.8%    | 47.0%   | 44%    | 50%   | 16 | GDP |
  | 산업재        | 8.1%     | 12.0%   | 59%    | 59%   | 17 | GDP |
  | 필수소비재      | 14.4%    | 79.8%   | 67%    | 67%   | GDP |
  | 전체         | 15.6%    | 46.9%   | 57%    | 59%   | 51 | GDP |
- 평균회귀 모델 패배 원인: 학습기간(2019-2022)의 높은 평균 성장률(특히 IT +31%)이
  2023-2024 둔화기를 반영 못 함 → 과대 예측

결론:
- 가설 1 기각: 평균회귀 기반 산업 특화 모델(MAPE 46.9%) vs GDP 모델(15.6%) → GDP 우위
  - 단, 이 실험의 "산업 특화"는 외부 데이터 없이 과거 성장률 평균 회귀만 사용
  - 진정한 산업 특화(메모리 가격, 자동차 판매 등 외부 지표)는 미검증
- 가설 2 기각: 모든 3섹터에서 GDP 모델이 우수
- GDP 모델의 장점: 보수적 예측(β × GDP ≈ 소폭 변동)이 극단적 성장/하락 시 오차 작음
- 핵심 시사점:
  1. 과거 성장률 기반 평균 회귀는 레짐 전환(호황→둔화)에 취약
  2. GDP β모델은 "보수적"이라서 오히려 MAPE가 낮음 (큰 변동을 예측 못 하지만 안정적)
  3. 방향성 정확도: GDP 57% vs MR 59% → 둘 다 동전 던지기 수준
  4. 진정한 개선은 산업 고유 외부 지표(DRAM 가격, 자동차 등록대수 등) 필요 → 현재 dartlab 범위 밖
  5. 현행 simulation.py의 GDP β 접근은 방향성은 유효하나, β값 자체는 001에서 확인한 대로 교정 필요
- 003_backtestGate에서 현행 시나리오의 실전 백테스트 실행

실험일: 2026-03-22
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

DATA_DIR = Path(__file__).parent / "data"

GDP_GROWTH = {
    2019: 2.2, 2020: -0.7, 2021: 4.3, 2022: 2.6, 2023: 1.4, 2024: 2.0,
}

CURRENT_BETA = {
    "IT/반도체": 1.8, "산업재": 1.3, "필수소비재": 0.3,
}

ALL_COMPANIES = [
    ("005930", "삼성전자", "IT/반도체"), ("000660", "SK하이닉스", "IT/반도체"),
    ("035420", "NAVER", "IT/반도체"), ("035720", "카카오", "IT/반도체"),
    ("006400", "삼성SDI", "IT/반도체"), ("247540", "에코프로비엠", "IT/반도체"),
    ("373220", "LG에너지솔루션", "IT/반도체"), ("036570", "엔씨소프트", "IT/반도체"),
    ("005380", "현대차", "산업재"), ("000270", "기아", "산업재"),
    ("012330", "현대모비스", "산업재"), ("010130", "고려아연", "산업재"),
    ("051910", "LG화학", "산업재"), ("011170", "롯데케미칼", "산업재"),
    ("003550", "LG", "산업재"), ("034730", "SK", "산업재"),
    ("028260", "삼성물산", "산업재"), ("009150", "삼성전기", "산업재"),
    ("097950", "CJ제일제당", "필수소비재"), ("004370", "농심", "필수소비재"),
    ("271560", "오리온", "필수소비재"), ("280360", "롯데웰푸드", "필수소비재"),
    ("005300", "롯데칠성", "필수소비재"), ("007310", "오뚜기", "필수소비재"),
    ("003230", "삼양식품", "필수소비재"), ("001040", "CJ", "필수소비재"),
    ("282330", "BGF리테일", "필수소비재"),
]


def _extractRevenueTimeseries(stockCode: str) -> dict[int, float]:
    """연도별 매출 시계열 추출."""
    from dartlab.engines.company.dart.finance.pivot import buildTimeseries

    try:
        result = buildTimeseries(stockCode)
        if result is None:
            return {}
        series, periods = result
        isSeries = series.get("IS", {})

        revVals = []
        for key in ["revenue", "sales"]:
            if key in isSeries and any(v is not None for v in isSeries[key]):
                revVals = isSeries[key]
                break
        if not revVals:
            return {}

        yearRevenue: dict[int, float] = {}
        for i, period in enumerate(periods):
            if i >= len(revVals) or revVals[i] is None:
                continue
            yr = None
            if isinstance(period, (int, float)):
                yr = int(period)
            elif isinstance(period, str):
                try:
                    yr = int(period[:4])
                except (ValueError, IndexError):
                    continue
            elif isinstance(period, (tuple, list)):
                try:
                    yr = int(period[0])
                except (ValueError, IndexError, TypeError):
                    continue
            if yr and 2018 <= yr <= 2025:
                if yr not in yearRevenue or revVals[i] > yearRevenue[yr]:
                    yearRevenue[yr] = revVals[i]
        return yearRevenue
    except (FileNotFoundError, RuntimeError, OSError):
        return {}


def _predictGDP(prevRevenue: float, gdpGrowth: float, beta: float) -> float:
    """GDP 기반 매출 예측."""
    return prevRevenue * (1 + beta * gdpGrowth / 100)


def _predictMeanReversion(prevRevenue: float, prevGrowth: float,
                          sectorAvgGrowth: float, reversion: float = 0.5) -> float:
    """평균 회귀 기반 매출 예측.
    예측 성장률 = prevGrowth × (1-reversion) + sectorAvgGrowth × reversion
    """
    predictedGrowth = prevGrowth * (1 - reversion) + sectorAvgGrowth * reversion
    return prevRevenue * (1 + predictedGrowth / 100)


def runIndustryScenario(*, verbose: bool = True) -> pl.DataFrame:
    """산업 특화 시나리오 비교 실행."""
    # 1단계: 기업별 매출 시계열 수집
    companyRevenues: dict[str, dict[str, dict[int, float]]] = {}  # sector → {code → {year: rev}}

    for stockCode, corpName, sector in ALL_COMPANIES:
        yearRev = _extractRevenueTimeseries(stockCode)
        if yearRev:
            if sector not in companyRevenues:
                companyRevenues[sector] = {}
            companyRevenues[sector][stockCode] = yearRev

    # 2단계: 섹터별 평균 성장률 계산 (2019-2022를 학습, 2023-2024를 테스트)
    sectorAvgGrowth: dict[str, float] = {}
    for sector, companies in companyRevenues.items():
        allGrowths = []
        for yearRev in companies.values():
            sortedYears = sorted(yearRev.keys())
            for i in range(1, len(sortedYears)):
                yr = sortedYears[i]
                prevYr = sortedYears[i - 1]
                if prevYr == yr - 1 and 2019 <= yr <= 2022 and yearRev[prevYr] > 0:
                    g = (yearRev[yr] / yearRev[prevYr] - 1) * 100
                    allGrowths.append(g)
        sectorAvgGrowth[sector] = sum(allGrowths) / len(allGrowths) if allGrowths else 0

    if verbose:
        print(f"\n[섹터별 평균 매출성장률 2019-2022 (학습 기간)]")
        for sector, avg in sectorAvgGrowth.items():
            print(f"  {sector:12s}: {avg:+.1f}%")

    # 3단계: 2023-2024 예측 비교
    testYears = [2023, 2024]
    results = []

    for sector, companies in companyRevenues.items():
        beta = CURRENT_BETA.get(sector, 0.8)

        for stockCode, yearRev in companies.items():
            corpName = next((n for c, n, s in ALL_COMPANIES if c == stockCode), stockCode)

            for testYr in testYears:
                if testYr not in yearRev or (testYr - 1) not in yearRev:
                    continue

                actual = yearRev[testYr]
                prevRev = yearRev[testYr - 1]
                gdp = GDP_GROWTH.get(testYr, 0)

                # 직전년도 성장률
                prevGrowth = 0
                if (testYr - 2) in yearRev and yearRev[testYr - 2] > 0:
                    prevGrowth = (yearRev[testYr - 1] / yearRev[testYr - 2] - 1) * 100

                # 두 가지 예측
                predGDP = _predictGDP(prevRev, gdp, beta)
                predMR = _predictMeanReversion(prevRev, prevGrowth, sectorAvgGrowth[sector])

                # MAPE
                mapeGDP = abs(predGDP - actual) / actual * 100 if actual > 0 else None
                mapeMR = abs(predMR - actual) / actual * 100 if actual > 0 else None

                # 방향성 (성장/감소 맞혔는지)
                actualDir = 1 if actual > prevRev else -1
                gdpDir = 1 if predGDP > prevRev else -1
                mrDir = 1 if predMR > prevRev else -1

                results.append({
                    "stockCode": stockCode, "corpName": corpName, "sector": sector,
                    "year": testYr, "actual": actual, "prevRevenue": prevRev,
                    "predGDP": predGDP, "predMR": predMR,
                    "mapeGDP": round(mapeGDP, 1) if mapeGDP is not None else None,
                    "mapeMR": round(mapeMR, 1) if mapeMR is not None else None,
                    "dirGDP": gdpDir == actualDir,
                    "dirMR": mrDir == actualDir,
                })

    df = pl.DataFrame(results)

    if verbose:
        _printResults(df)

    return df


def _printResults(df: pl.DataFrame) -> None:
    """결과 출력."""
    print(f"\n[예측 비교: GDP β모델 vs 평균회귀 모델]")
    print(f"{'섹터':12s} | {'GDP MAPE':>10s} | {'MR MAPE':>10s} | "
          f"{'GDP방향':>8s} | {'MR방향':>8s} | {'N':>3s} | {'우위'}")
    print("-" * 75)

    overall_gdp_mape = []
    overall_mr_mape = []
    overall_gdp_dir = []
    overall_mr_dir = []

    for sector in ["IT/반도체", "산업재", "필수소비재"]:
        sdf = df.filter(pl.col("sector") == sector)
        if sdf.is_empty():
            continue

        gdpMape = sdf["mapeGDP"].drop_nulls().mean()
        mrMape = sdf["mapeMR"].drop_nulls().mean()
        gdpDir = sdf["dirGDP"].sum() / len(sdf) * 100
        mrDir = sdf["dirMR"].sum() / len(sdf) * 100
        n = len(sdf)

        winner = "MR" if mrMape and gdpMape and mrMape < gdpMape else "GDP"
        improvement = ((gdpMape - mrMape) / gdpMape * 100) if gdpMape and mrMape and gdpMape > 0 else 0

        print(f"{sector:12s} | {gdpMape:9.1f}% | {mrMape:9.1f}% | "
              f"{gdpDir:7.0f}% | {mrDir:7.0f}% | {n:3d} | {winner} ({improvement:+.0f}%)")

        overall_gdp_mape.extend(sdf["mapeGDP"].drop_nulls().to_list())
        overall_mr_mape.extend(sdf["mapeMR"].drop_nulls().to_list())
        overall_gdp_dir.extend(sdf["dirGDP"].to_list())
        overall_mr_dir.extend(sdf["dirMR"].to_list())

    # 전체 평균
    if overall_gdp_mape and overall_mr_mape:
        avgGDP = sum(overall_gdp_mape) / len(overall_gdp_mape)
        avgMR = sum(overall_mr_mape) / len(overall_mr_mape)
        dirGDP = sum(1 for d in overall_gdp_dir if d) / len(overall_gdp_dir) * 100
        dirMR = sum(1 for d in overall_mr_dir if d) / len(overall_mr_dir) * 100
        improvement = (avgGDP - avgMR) / avgGDP * 100 if avgGDP > 0 else 0
        winner = "MR" if avgMR < avgGDP else "GDP"

        print("-" * 75)
        print(f"{'전체':12s} | {avgGDP:9.1f}% | {avgMR:9.1f}% | "
              f"{dirGDP:7.0f}% | {dirMR:7.0f}% | {len(overall_gdp_mape):3d} | {winner} ({improvement:+.0f}%)")

    # 기업별 상세 (이상값 확인)
    print(f"\n[기업별 MAPE 상세 — 이상값 TOP 5]")
        sorted_df = df.filter(pl.col("mapeGDP").is_not_null()).sort("mapeGDP", descending=True)
        for row in sorted_df.head(5).iter_rows(named=True):
            print(f"  {row['corpName']:12s} {row['year']} | "
                  f"GDP={row['mapeGDP']:6.1f}% MR={row['mapeMR']:6.1f}%")


if __name__ == "__main__":
    print("=" * 60)
    print("085-002: 산업 특화 시나리오 vs 범용 GDP 시나리오")
    print("=" * 60)

    start = time.time()
    resultDf = runIndustryScenario()
    elapsed = time.time() - start

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    resultDf.write_parquet(DATA_DIR / "002_industryScenario.parquet")
    print(f"\n→ {DATA_DIR / '002_industryScenario.parquet'} ({elapsed:.1f}s)")
