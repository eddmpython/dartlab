"""실험 ID: 001
실험명: SECTOR_ELASTICITY β값 실증 교정 — GDP×섹터 매출성장률 회귀

목적:
- simulation.py의 하드코딩 SECTOR_ELASTICITY β값을 실제 데이터로 검증/교정
- 한국 GDP 성장률 vs 섹터별 매출 성장률의 감응도(β)를 실증적으로 측정

가설:
1. 반도체 β > 1.5 (GDP 대비 과민 반응, 경기민감주)
2. 식품/필수소비재 β < 0.5 (경기방어주)
3. 상위 5개 섹터에서 회귀 R² > 0.3

방법:
1. 50사(Phase 1) buildTimeseries로 연도별 revenue 시계열 추출 (2019-2024, 최대 6개년)
2. 연도별 매출 성장률 계산 (YoY%)
3. 한국 GDP 성장률 (한국은행 공표): 2019(-0.7), 2020(-0.9), 2021(4.3), 2022(2.6), 2023(1.4), 2024(2.0)
   ※ 2020은 코로나, 2021은 리바운드 — 변동 폭 큰 기간
4. 섹터별 매출성장률 vs GDP 성장률 단순 OLS → β, R² 산출
5. 현재 하드코딩 β와 실증 β 비교

결과 (실행 후 작성):
- 수집: 8.1s, 37/48사에서 매출 성장률 추출 (금융 0사 — IS에 revenue/sales 키 없음)
- 섹터별 GDP 감응도 (β):
  | 섹터         | 실증β  | R²    | 현행β | 차이   | N | 판정 |
  |-------------|-------|-------|------|-------|---|------|
  | IT/반도체     | 4.05  | 0.079 | 1.8  | +2.25 | 6 | 상향 |
  | 산업재        | 3.36  | 0.370 | 1.3  | +2.06 | 6 | 상향 |
  | 건강관리       | 6.91  | 0.847 | 0.5  | +6.41 | 6 | 상향 |
  | 금융         | N/A   | N/A   | 1.0  | N/A   | 0 | — |
  | 필수소비재      | -43.1 | 0.025 | 0.3  | -43.4 | 6 | 이상 |
- 이상값 주의:
  - 필수소비재 2023: +1101% → 특정 기업 극단 성장(삼양식품 추정)이 β 왜곡
  - 건강관리 R²=0.847이지만 β=6.91 → 바이오 고성장이 GDP가 아닌 기업 고유 요인
  - IT/반도체 R²=0.079 → GDP 변동이 반도체 매출 설명 거의 못 함 (반도체 사이클 비동기)
- 교차 검증 (market_ratios 2,661사):
  - IT 3Y CAGR +1.7%, 건강관리 +5.0%, 필수소비재 +2.3%, 산업재 -0.2%
  - 50사 대기업 편향 vs 시장 전체 차이가 큼

결론:
- 가설 1 부분 채택: IT/반도체 실증β(4.05) > 1.5이지만 R²=0.079으로 GDP 설명력 극히 낮음
  → 반도체는 GDP가 아닌 메모리 사이클에 연동. β보다 산업 사이클 지표가 필요
- 가설 2 기각: 필수소비재 실증β=-43.1 (이상값) → 50사 표본에서 β 추정 불안정
  → 이상값 제거 후 재추정 또는 2,661사 시장 전체 데이터 필요
- 가설 3 부분 채택: 산업재만 R²=0.370 > 0.3 충족. 나머지 4개 섹터 미달
- 핵심 시사점:
  1. GDP-매출 선형 β 모델의 한계: 대기업 50사는 GDP보다 글로벌/산업 사이클에 반응
  2. 현행 하드코딩 β(1.8, 1.3 등)는 방향성은 맞지만 절대값은 과소평가
  3. 금융 섹터: IS에 revenue 없어 별도 감응도 모델 필요 (이자수익/NIM 기반)
  4. 이상값 처리 필수: 극단 성장 기업(삼양식품 등)이 섹터 평균을 왜곡
  5. 교정 권장: 산업재 β=3.36→현행 1.3 대비 2.6배, 유의미한 상향 필요
- 002_industryScenario에서 산업 특화 지표(메모리 가격, 자동차 판매 등) 활용 검토

실험일: 2026-03-22
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

DATA_DIR = Path(__file__).parent / "data"

# 한국 실질 GDP 성장률 (%, 한국은행)
# 2018은 기준점, 2019~2024가 분석 대상
GDP_GROWTH = {
    2019: 2.2,
    2020: -0.7,
    2021: 4.3,
    2022: 2.6,
    2023: 1.4,
    2024: 2.0,
}

# Phase 1에서 사용한 48사 (중복 제거)
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
    ("068270", "셀트리온", "건강관리"), ("207940", "삼성바이오로직스", "건강관리"),
    ("326030", "SK바이오팜", "건강관리"), ("128940", "한미약품", "건강관리"),
    ("006280", "녹십자", "건강관리"), ("000100", "유한양행", "건강관리"),
    ("185750", "종근당", "건강관리"), ("003060", "에이치엘비", "건강관리"),
    ("145720", "덴티움", "건강관리"), ("214150", "클래시스", "건강관리"),
    ("105560", "KB금융", "금융"), ("055550", "신한지주", "금융"),
    ("086790", "하나금융지주", "금융"), ("316140", "우리금융지주", "금융"),
    ("024110", "기업은행", "금융"), ("138930", "BNK금융지주", "금융"),
    ("175330", "JB금융지주", "금융"), ("032830", "삼성생명", "금융"),
    ("000810", "삼성화재", "금융"), ("088350", "한화생명", "금융"),
    ("097950", "CJ제일제당", "필수소비재"), ("004370", "농심", "필수소비재"),
    ("271560", "오리온", "필수소비재"), ("280360", "롯데웰푸드", "필수소비재"),
    ("005300", "롯데칠성", "필수소비재"), ("007310", "오뚜기", "필수소비재"),
    ("003230", "삼양식품", "필수소비재"), ("002270", "롯데지주", "필수소비재"),
    ("001040", "CJ", "필수소비재"), ("282330", "BGF리테일", "필수소비재"),
]

# 현재 하드코딩 β (simulation.py SECTOR_ELASTICITY)
CURRENT_BETA = {
    "IT/반도체": 1.8,     # "반도체" + "IT/소프트웨어" 혼합
    "산업재": 1.3,         # "자동차" + "화학" 등
    "건강관리": 0.5,       # "제약/바이오"
    "금융": 1.0,           # "금융/은행"
    "필수소비재": 0.3,     # "식품"
}


def _extractRevenueTimeseries(stockCode: str) -> dict[int, float]:
    """buildTimeseries로 연도별 revenue 추출."""
    from dartlab.engines.company.dart.finance.pivot import buildTimeseries

    try:
        result = buildTimeseries(stockCode)
        if result is None:
            return {}

        series, periods = result
        isSeries = series.get("IS", {})

        # revenue 키 찾기
        revVals = []
        for key in ["revenue", "sales"]:
            if key in isSeries and any(v is not None for v in isSeries[key]):
                revVals = isSeries[key]
                break

        if not revVals:
            return {}

        # periods는 (year, quarter) 형태 — 연간 데이터 추출
        # buildTimeseries는 standalone 기준이므로 연간(Q4) 값을 찾아야 함
        # periods 형식 확인 필요 — 보통 문자열 "2023" 또는 튜플
        yearRevenue: dict[int, float] = {}

        # periods와 revVals 매핑
        for i, period in enumerate(periods):
            if i >= len(revVals) or revVals[i] is None:
                continue
            # period가 int, str, tuple 등 다양할 수 있음
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
                # 같은 연도 여러 분기가 있으면 가장 큰 값(연간 누적) 사용
                if yr not in yearRevenue or revVals[i] > yearRevenue[yr]:
                    yearRevenue[yr] = revVals[i]

        return yearRevenue

    except (FileNotFoundError, RuntimeError, OSError):
        return {}


def _calcYoYGrowth(yearRevenue: dict[int, float]) -> dict[int, float]:
    """연도별 매출 YoY 성장률(%)."""
    growth = {}
    sortedYears = sorted(yearRevenue.keys())
    for i in range(1, len(sortedYears)):
        yr = sortedYears[i]
        prevYr = sortedYears[i - 1]
        if prevYr == yr - 1 and yearRevenue[prevYr] > 0:
            growth[yr] = (yearRevenue[yr] / yearRevenue[prevYr] - 1) * 100
    return growth


def _simpleOLS(x: list[float], y: list[float]) -> tuple[float, float, float]:
    """단순 OLS 회귀. return: (β, intercept, R²)."""
    n = len(x)
    if n < 3:
        return 0.0, 0.0, 0.0

    mx = sum(x) / n
    my = sum(y) / n

    ssxy = sum((x[i] - mx) * (y[i] - my) for i in range(n))
    ssxx = sum((x[i] - mx) ** 2 for i in range(n))
    ssyy = sum((y[i] - my) ** 2 for i in range(n))

    if ssxx == 0 or ssyy == 0:
        return 0.0, my, 0.0

    beta = ssxy / ssxx
    intercept = my - beta * mx
    r_sq = (ssxy ** 2) / (ssxx * ssyy)

    return beta, intercept, r_sq


def runElasticityCalibration(*, verbose: bool = True) -> pl.DataFrame:
    """감응도 교정 실행."""
    # 1단계: 기업별 연도별 매출 시계열 추출
    allGrowth: dict[str, dict[int, list[float]]] = {}  # sector → {year → [growth%]}
    companyData = []

    for stockCode, corpName, sector in ALL_COMPANIES:
        yearRev = _extractRevenueTimeseries(stockCode)
        growth = _calcYoYGrowth(yearRev)

        if growth:
            companyData.append({
                "stockCode": stockCode, "corpName": corpName, "sector": sector,
                "years": len(growth), "growthYears": sorted(growth.keys()),
            })

            if sector not in allGrowth:
                allGrowth[sector] = {}
            for yr, g in growth.items():
                if yr not in allGrowth[sector]:
                    allGrowth[sector][yr] = []
                allGrowth[sector][yr].append(g)

    if verbose:
        print(f"\n[데이터 수집] {len(companyData)}사에서 매출 성장률 추출")
        for sector in ["IT/반도체", "산업재", "건강관리", "금융", "필수소비재"]:
            data = allGrowth.get(sector, {})
            yearCounts = {yr: len(vals) for yr, vals in data.items()}
            print(f"  {sector:12s}: {yearCounts}")

    # 2단계: 섹터별 연평균 매출성장률 vs GDP 성장률 회귀
    results = []
    if verbose:
        print(f"\n[섹터별 GDP 감응도 (β) 교정]")
        print(f"{'섹터':12s} | {'실증β':>6s} | {'R²':>6s} | {'현행β':>6s} | {'차이':>6s} | {'N':>3s} | {'판정'}")
        print("-" * 70)

    for sector in ["IT/반도체", "산업재", "건강관리", "금융", "필수소비재"]:
        sectorGrowth = allGrowth.get(sector, {})

        # GDP 성장률과 매칭되는 연도의 섹터 평균 성장률
        gdpList = []
        revGrowthList = []

        for yr in sorted(GDP_GROWTH.keys()):
            if yr in sectorGrowth and len(sectorGrowth[yr]) >= 2:
                gdpList.append(GDP_GROWTH[yr])
                avgGrowth = sum(sectorGrowth[yr]) / len(sectorGrowth[yr])
                revGrowthList.append(avgGrowth)

        beta, intercept, r_sq = _simpleOLS(gdpList, revGrowthList)
        currentBeta = CURRENT_BETA.get(sector, 0.8)

        verdict = "일치" if abs(beta - currentBeta) < 0.5 else ("상향" if beta > currentBeta else "하향")

        results.append({
            "sector": sector,
            "empiricalBeta": round(beta, 2),
            "r_squared": round(r_sq, 3),
            "currentBeta": currentBeta,
            "diff": round(beta - currentBeta, 2),
            "n_years": len(gdpList),
            "verdict": verdict,
        })

        if verbose:
            print(f"{sector:12s} | {beta:6.2f} | {r_sq:6.3f} | {currentBeta:6.1f} | "
                  f"{beta - currentBeta:+6.2f} | {len(gdpList):3d} | {verdict}")

            # 연도별 상세
            for i, yr in enumerate(sorted(GDP_GROWTH.keys())):
                if yr in sectorGrowth:
                    avgG = sum(sectorGrowth[yr]) / len(sectorGrowth[yr])
                    n = len(sectorGrowth[yr])
                    print(f"    {yr}: GDP={GDP_GROWTH[yr]:+5.1f}% → 섹터매출={avgG:+6.1f}% (n={n})")

    # 3단계: market_ratios 교차 검증 (revenueGrowth3Y)
    if verbose:
        print(f"\n[교차 검증: market_ratios revenueGrowth3Y]")
        try:
            mrDf = pl.read_parquet(
                Path(__file__).resolve().parents[1] / "076_marketLab" / "data" / "market_ratios.parquet"
            )
            valid = mrDf.filter(pl.col("revenueGrowth3Y").is_not_null())

            # WICS 섹터 → Phase1 섹터 매핑
            sectorMap = {
                "IT": "IT/반도체", "산업재": "산업재", "건강관리": "건강관리",
                "금융": "금융", "필수소비재": "필수소비재", "소재": "산업재",
                "경기관련소비재": "산업재",
            }

            for wics, phase1 in sectorMap.items():
                sdf = valid.filter(pl.col("sector") == wics)
                if sdf.is_empty():
                    continue
                avgG = sdf["revenueGrowth3Y"].mean()
                n = len(sdf)
                print(f"  {wics:20s} (→{phase1}): 3Y CAGR={avgG:+5.1f}% (n={n})")

        except FileNotFoundError:
            print("  market_ratios.parquet 없음")

    return pl.DataFrame(results)


if __name__ == "__main__":
    print("=" * 60)
    print("085-001: SECTOR_ELASTICITY β값 실증 교정")
    print("=" * 60)

    start = time.time()
    resultDf = runElasticityCalibration()
    elapsed = time.time() - start

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    resultDf.write_parquet(DATA_DIR / "001_elasticityCalibration.parquet")
    print(f"\n→ {DATA_DIR / '001_elasticityCalibration.parquet'} ({elapsed:.1f}s)")
