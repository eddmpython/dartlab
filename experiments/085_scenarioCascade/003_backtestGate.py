"""실험 ID: 003
실험명: 시나리오 예측 백테스트 — Phase 2 관문 실험

목적:
- simulation.py의 시나리오 예측이 실제 실적과 얼마나 일치하는지 백테스트
- Phase 2 관문: 방향성 정확도 > 55% 달성 여부 판정

가설:
1. GDP β모델 기반 매출 예측의 방향성 정확도 > 55% (동전 던지기보다 나음)
2. 영업이익 방향성 예측도 55%+ (매출 방향 + 마진 변동 모델)
3. 섹터별 순위 상관(Spearman) > 0.2

방법:
1. 27사(3섹터) × 2022 기준 데이터로 2023-2024 예측
2. GDP β모델 예측: 매출' = 매출 × (1 + β × ΔGDP%)
3. 마진 예측: 마진' = 마진 + margin_to_gdp × ΔGDP (bps)
4. 실제 2023-2024 실적 대비 방향성, MAPE, 순위 상관 측정
5. 성공 기준: 방향성 > 55%, 순위 상관 > 0.2

결과 (실행 후 작성):
- 대상: 51건 (27사 × 2023-2024), 수행 시간 1.3s
- 매출 방향성 정확도: 54.9% ✗ FAIL (기준 >55%)
- 마진 방향성 정확도: 54.9% ✗ FAIL (기준 >55%)
- 매출 MAPE 평균: 20.3%
- 섹터별:
  | 섹터         | 매출방향 | 마진방향 | MAPE  | N  |
  |-------------|--------|--------|-------|----|
  | IT/반도체     | 44%    | 56%    | 24.8% | 16 |
  | 산업재        | 59%    | 59%    | 8.1%  | 17 |
  | 필수소비재      | 61%    | 50%    | 27.8% | 18 |
- 순위 상관 (Spearman): 전체 ρ=-0.167 ✗ FAIL
  - IT/반도체 ρ=-0.297 (역상관), 산업재 ρ=-0.056, 필수소비재 ρ=0.356 (유일 양수)
- GATE 판정: ✗ FAIL

결론:
- 가설 1 기각 (경계): 매출 방향성 54.9% — 55% 기준에 0.1%p 차이로 FAIL
  - 산업재(59%)와 필수소비재(61%)는 통과하나 IT/반도체(44%)가 전체를 하락시킴
- 가설 2 기각: 마진 방향성 54.9% — 동전 던지기 수준
- 가설 3 기각: 순위 상관 ρ=-0.167 — GDP β모델이 기업간 상대 순위 예측에 실패
  - IT/반도체 ρ=-0.297: GDP 기반 예측이 반도체 기업 순위를 반대로 매김
- Phase 2 GATE: FAIL → simulation.py 재설계 필요
  - 현행 GDP β 선형 모델의 근본적 한계:
    1. 반도체 사이클과 GDP 비동기 (IT 방향성 44%)
    2. 기업간 차별화 불가 (같은 섹터는 동일 β → 순위 예측 불가)
    3. 마진 변동 모델(bps 단위)이 실제 마진 변동 폭을 포착 못 함
  - 재설계 방향:
    1. 기업 고유 특성(비용구조, 해자) 반영 → Phase 1 결과 활용
    2. 산업 사이클 지표 도입 (메모리 가격, 자동차 판매 등)
    3. 마진 모델: 고정 bps가 아닌 비용구조 기반 시뮬레이션
    4. 필수소비재는 방향성 61%, ρ=0.356으로 양호 → 방어주에는 현행 모델이 적절
- 즉시 조치: Phase 4에서 simulation.py 강화 시 IT/반도체 β 모델 분리 설계

실험일: 2026-03-22
"""

from __future__ import annotations

import math
import sys
import time
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

DATA_DIR = Path(__file__).parent / "data"

GDP_GROWTH = {2023: 1.4, 2024: 2.0}

# simulation.py의 SECTOR_ELASTICITY 기반
SECTOR_PARAMS = {
    "IT/반도체": {"beta": 1.8, "margin_bps": 50, "cyclicality": "high"},
    "산업재": {"beta": 1.3, "margin_bps": 30, "cyclicality": "high"},
    "필수소비재": {"beta": 0.3, "margin_bps": 5, "cyclicality": "defensive"},
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


def _extractFinancials(stockCode: str) -> dict[int, dict]:
    """연도별 매출, 영업이익, 영업이익률 추출."""
    from dartlab.engines.company.dart.finance.pivot import buildTimeseries

    try:
        result = buildTimeseries(stockCode)
        if result is None:
            return {}
        series, periods = result
        isSeries = series.get("IS", {})

        # revenue
        revVals = []
        for key in ["revenue", "sales"]:
            if key in isSeries and any(v is not None for v in isSeries[key]):
                revVals = isSeries[key]
                break

        # operating profit
        opVals = []
        for key in ["operating_profit", "operating_income"]:
            if key in isSeries and any(v is not None for v in isSeries[key]):
                opVals = isSeries[key]
                break

        yearData: dict[int, dict] = {}
        for i, period in enumerate(periods):
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

            if yr and 2021 <= yr <= 2025:
                rev = revVals[i] if i < len(revVals) else None
                op = opVals[i] if i < len(opVals) else None
                margin = (op / rev * 100) if rev and op and rev > 0 else None

                if yr not in yearData or (rev and (yearData[yr].get("revenue") is None or rev > yearData[yr]["revenue"])):
                    yearData[yr] = {"revenue": rev, "opProfit": op, "opMargin": margin}

        return yearData
    except (FileNotFoundError, RuntimeError, OSError):
        return {}


def _spearmanCorr(x: list[float], y: list[float]) -> float:
    """Spearman 순위상관."""
    n = len(x)
    if n < 3:
        return 0.0

    def _rank(vals: list) -> list[float]:
        indexed = sorted(enumerate(vals), key=lambda t: t[1])
        ranks = [0.0] * n
        for rank, (idx, _) in enumerate(indexed, 1):
            ranks[idx] = float(rank)
        return ranks

    rx = _rank(x)
    ry = _rank(y)
    d_sq = sum((rx[i] - ry[i]) ** 2 for i in range(n))
    return 1 - (6 * d_sq) / (n * (n ** 2 - 1))


def runBacktestGate(*, verbose: bool = True) -> pl.DataFrame:
    """백테스트 관문 실행."""
    results = []

    for stockCode, corpName, sector in ALL_COMPANIES:
        yearData = _extractFinancials(stockCode)
        params = SECTOR_PARAMS.get(sector, {"beta": 0.8, "margin_bps": 15})

        for testYr in [2023, 2024]:
            baseYr = testYr - 1
            if baseYr not in yearData or testYr not in yearData:
                continue

            baseRev = yearData[baseYr].get("revenue")
            baseMargin = yearData[baseYr].get("opMargin")
            actualRev = yearData[testYr].get("revenue")
            actualMargin = yearData[testYr].get("opMargin")

            if not baseRev or not actualRev:
                continue

            gdp = GDP_GROWTH[testYr]

            # 매출 예측
            predRev = baseRev * (1 + params["beta"] * gdp / 100)

            # 마진 예측
            predMargin = None
            if baseMargin is not None:
                predMargin = baseMargin + params["margin_bps"] * gdp / 10000

            # 영업이익 예측
            predOpProfit = predRev * predMargin / 100 if predMargin is not None else None

            # 방향성
            actualRevDir = 1 if actualRev > baseRev else -1
            predRevDir = 1 if predRev > baseRev else -1
            revDirCorrect = actualRevDir == predRevDir

            actualMarginDir = None
            marginDirCorrect = None
            if actualMargin is not None and baseMargin is not None:
                actualMarginDir = 1 if actualMargin > baseMargin else -1
                predMarginDir = 1 if predMargin and predMargin > baseMargin else -1
                marginDirCorrect = actualMarginDir == predMarginDir

            # MAPE
            revMAPE = abs(predRev - actualRev) / actualRev * 100

            results.append({
                "stockCode": stockCode, "corpName": corpName, "sector": sector,
                "year": testYr,
                "baseRevenue": baseRev, "actualRevenue": actualRev, "predRevenue": predRev,
                "baseMargin": baseMargin, "actualMargin": actualMargin, "predMargin": predMargin,
                "revMAPE": round(revMAPE, 1),
                "revDirCorrect": revDirCorrect,
                "marginDirCorrect": marginDirCorrect,
                "actualRevGrowth": round((actualRev / baseRev - 1) * 100, 1),
                "predRevGrowth": round((predRev / baseRev - 1) * 100, 1),
            })

    df = pl.DataFrame(results)

    if verbose:
        _printResults(df)

    return df


def _printResults(df: pl.DataFrame) -> None:
    """결과 출력."""
    # 전체 방향성 정확도
    revDir = df["revDirCorrect"].sum() / len(df) * 100
    marginDf = df.filter(pl.col("marginDirCorrect").is_not_null())
    marginDir = marginDf["marginDirCorrect"].sum() / len(marginDf) * 100 if len(marginDf) > 0 else 0
    avgMAPE = df["revMAPE"].mean()

    print(f"\n[백테스트 결과 요약]")
    print(f"  대상: {len(df)}건 (27사 × 2023-2024)")
    print(f"  매출 방향성 정확도: {revDir:.1f}% {'✓ PASS' if revDir > 55 else '✗ FAIL'} (기준: >55%)")
    print(f"  마진 방향성 정확도: {marginDir:.1f}% {'✓ PASS' if marginDir > 55 else '✗ FAIL'} (기준: >55%)")
    print(f"  매출 MAPE 평균: {avgMAPE:.1f}%")

    # 섹터별
    print(f"\n[섹터별 상세]")
    print(f"{'섹터':12s} | {'매출방향':>8s} | {'마진방향':>8s} | {'MAPE':>8s} | {'N':>3s}")
    print("-" * 50)

    for sector in ["IT/반도체", "산업재", "필수소비재"]:
        sdf = df.filter(pl.col("sector") == sector)
        if sdf.is_empty():
            continue
        rd = sdf["revDirCorrect"].sum() / len(sdf) * 100
        mdf = sdf.filter(pl.col("marginDirCorrect").is_not_null())
        md = mdf["marginDirCorrect"].sum() / len(mdf) * 100 if len(mdf) > 0 else 0
        mape = sdf["revMAPE"].mean()
        print(f"{sector:12s} | {rd:7.0f}% | {md:7.0f}% | {mape:7.1f}% | {len(sdf):3d}")

    # 순위 상관 (실제 성장률 순위 vs 예측 성장률 순위)
    rankDf = df.filter(
        pl.col("actualRevGrowth").is_not_null() & pl.col("predRevGrowth").is_not_null()
    )
    if len(rankDf) >= 5:
        actual = rankDf["actualRevGrowth"].to_list()
        pred = rankDf["predRevGrowth"].to_list()
        rho = _spearmanCorr(actual, pred)
        print(f"\n[순위 상관 (Spearman)]")
        print(f"  전체: ρ={rho:.3f} {'✓ PASS' if rho > 0.2 else '✗ FAIL'} (기준: >0.2)")

        # 섹터별
        for sector in ["IT/반도체", "산업재", "필수소비재"]:
            sdf = rankDf.filter(pl.col("sector") == sector)
            if len(sdf) >= 3:
                a = sdf["actualRevGrowth"].to_list()
                p = sdf["predRevGrowth"].to_list()
                rho_s = _spearmanCorr(a, p)
                print(f"  {sector:12s}: ρ={rho_s:.3f}")

    # GATE 판정
    print(f"\n{'='*50}")
    gatePass = revDir > 55
    print(f"Phase 2 GATE 판정: {'✓ PASS' if gatePass else '✗ FAIL'}")
    print(f"  매출 방향성 {revDir:.1f}% {'>' if gatePass else '<='} 55%")
    if not gatePass:
        print(f"  → simulation.py 재설계 필요")
    print(f"{'='*50}")


if __name__ == "__main__":
    print("=" * 60)
    print("085-003: 시나리오 예측 백테스트 (Phase 2 GATE)")
    print("=" * 60)

    start = time.time()
    resultDf = runBacktestGate()
    elapsed = time.time() - start

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    resultDf.write_parquet(DATA_DIR / "003_backtestGate.parquet")
    print(f"\n→ {DATA_DIR / '003_backtestGate.parquet'} ({elapsed:.1f}s)")
