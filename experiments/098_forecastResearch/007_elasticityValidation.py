"""실험 ID: 098-007
실험명: 섹터별 GDP 탄성도 실증 검증

목적:
- simulation.py의 SECTOR_ELASTICITY 하드코딩 beta가 실제 과거 데이터와 부합하는지 확인
- 특히 revenueToGdp (GDP 1%p 변화 → 매출 변화 배수) 검증

가설:
1. 하드코딩 beta의 방향성이 실제와 80% 이상 일치 (경기민감 > 방어적)
2. 실증 beta와 설정 beta의 상관 > 0.5
3. 반도체/자동차는 높은 beta, 식품/통신은 낮은 beta

방법:
1. 한국 GDP 성장률 시계열 (한국은행 기준, 2017~2024)
2. 섹터별 대표 종목 10사의 매출 성장률 시계열
3. 섹터 매출 성장률 ~ GDP 성장률 단순회귀 → 실증 beta 산출
4. SECTOR_ELASTICITY.revenueToGdp와 비교

결과:
- 8개 섹터 전부 실증 beta 산출 성공 (2017~2024, 7개 성장률 관측)
- 방향성 일치율: 7/8 (88%) — 통신만 불일치
- 실증β vs 설정β 상관: 0.169 (0.5 미달)
- 실증 beta 크기가 설정보다 3~10배 큼:
  반도체 3.93 vs 1.8, 자동차 1.87 vs 1.3, 화학 7.02 vs 1.2
  철강 12.77 vs 1.4, 통신 8.22 vs 0.4, 식품 -2.40 vs 0.3
  IT 5.73 vs 1.0, 유통 12.88 vs 0.8
- R² 범위: 0.061(통신)~0.764(유통), 평균 약 0.31
- 식품 beta가 -2.40 → 경기역행 (방어적) 특성 확인
- 통신 불일치 원인: 2017년 KT 139% 매출 급증 (이상치)이 beta 왜곡

결론:
- 가설1 채택: 방향성 88% 일치 (80% 기준 초과). 경기민감 > 방어적 구조 맞음
- 가설2 기각: 상관 0.169 (0.5 미달). 설정 beta는 크기를 과소 설정
- 가설3 부분 채택: 반도체(3.93) > 식품(-2.40) 확인, 자동차(1.87) 확인
  단 통신(8.22)은 이상치로 왜곡
- **simulation.py 하드코딩 beta의 방향성은 유효하나, 절대 크기는 현실과 큰 괴리**
  → revenueToGdp beta를 실증값으로 교정하면 시뮬레이션 현실성 개선 가능
  → 단, R²가 낮아(평균 0.31) GDP만으로는 매출 변동의 30%만 설명
  → 환율, 유가, 금리 등 추가 거시변수 결합 필요 (008에서 확인)

실험일: 2026-03-25
"""

import time
from pathlib import Path

import numpy as np
import polars as pl

FINANCE_DIR = Path(__file__).resolve().parents[2] / "data" / "dart" / "finance"

# 한국 GDP 성장률 (한국은행 기준, 실질 GDP YoY%)
# 2017~2024
GDP_GROWTH = {
    "2017": 3.2, "2018": 2.9, "2019": 2.2, "2020": -0.7,
    "2021": 4.3, "2022": 2.6, "2023": 1.4, "2024": 2.0,
}

# 섹터별 대표 종목 (simulation.py SECTOR_ELASTICITY 키 기준)
SECTOR_STOCKS = {
    "반도체": [
        ("005930", "삼성전자"), ("000660", "SK하이닉스"), ("009150", "삼성전기"),
        ("058470", "리노공업"), ("403870", "HPSP"),
    ],
    "자동차": [
        ("005380", "현대자동차"), ("000270", "기아"), ("012330", "현대모비스"),
        ("018880", "한온시스템"), ("161390", "한국타이어앤테크놀로지"),
    ],
    "화학": [
        ("051910", "LG화학"), ("011170", "롯데케미칼"), ("009830", "한화솔루션"),
        ("006120", "SK디스커버리"), ("004000", "롯데정밀화학"),
    ],
    "철강": [
        ("005490", "POSCO홀딩스"), ("004020", "현대제철"), ("001230", "동국제강"),
        ("004990", "롯데지주"),
    ],
    "통신": [
        ("030200", "KT"), ("017670", "SK텔레콤"),
    ],
    "식품": [
        ("005440", "현대그린푸드"), ("097950", "CJ제일제당"), ("004370", "농심"),
        ("271560", "오리온"), ("014680", "한솔케미칼"),
    ],
    "IT/소프트웨어": [
        ("035420", "NAVER"), ("035720", "카카오"), ("036570", "엔씨소프트"),
        ("018260", "삼성에스디에스"), ("293490", "카카오게임즈"),
    ],
    "유통": [
        ("004170", "신세계"), ("069960", "현대백화점"), ("023530", "롯데쇼핑"),
    ],
}

# simulation.py 하드코딩 beta
HARDCODED_BETA = {
    "반도체": 1.8, "자동차": 1.3, "화학": 1.2, "철강": 1.4,
    "통신": 0.4, "식품": 0.3, "IT/소프트웨어": 1.0, "유통": 0.8,
}


def _extractAnnualRevenue(stockCode: str) -> dict[str, float] | None:
    """연간 사업보고서의 Revenue 추출."""
    fp = FINANCE_DIR / f"{stockCode}.parquet"
    if not fp.exists():
        return None
    try:
        df = pl.read_parquet(str(fp))
    except Exception:
        return None
    requiredCols = {"sj_div", "account_id", "bsns_year", "thstrm_amount", "fs_div", "reprt_code"}
    if not requiredCols.issubset(set(df.columns)):
        return None
    df = df.filter(pl.col("reprt_code") == "11011")
    if df.height == 0:
        return None
    isRows = df.filter(
        (pl.col("sj_div") == "IS") &
        (pl.col("account_id").str.to_lowercase().str.contains("revenue"))
    )
    if isRows.height == 0:
        isRows = df.filter(
            (pl.col("sj_div") == "IS") &
            (pl.col("account_nm").str.contains("매출액|수익\\(매출"))
        )
    if isRows.height == 0:
        return None
    yearValues = {}
    for row in isRows.iter_rows(named=True):
        year = str(row.get("bsns_year", ""))
        amount = row.get("thstrm_amount")
        if not year or amount is None:
            continue
        try:
            val = float(str(amount).replace(",", ""))
        except (ValueError, TypeError):
            continue
        if val == 0:
            continue
        fsDiv = str(row.get("fs_div", ""))
        if year not in yearValues or fsDiv == "CFS":
            yearValues[year] = val
    return yearValues if len(yearValues) >= 3 else None


def _computeSectorGrowth(sector: str, stocks: list) -> dict[str, float]:
    """섹터 대표 종목의 합산 매출 성장률."""
    yearTotals = {}
    count = 0
    for code, name in stocks:
        rev = _extractAnnualRevenue(code)
        if not rev:
            continue
        count += 1
        for year, val in rev.items():
            yearTotals[year] = yearTotals.get(year, 0) + val

    if count == 0:
        return {}

    years = sorted(yearTotals.keys())
    growth = {}
    for i in range(1, len(years)):
        prev = yearTotals[years[i - 1]]
        curr = yearTotals[years[i]]
        if prev > 0:
            growth[years[i]] = ((curr - prev) / prev) * 100  # %
    return growth


def _olsBeta(x: list[float], y: list[float]) -> tuple[float, float]:
    """단순 OLS beta와 R²."""
    n = len(x)
    if n < 3:
        return 0.0, 0.0
    xArr = np.array(x)
    yArr = np.array(y)
    xMean = xArr.mean()
    yMean = yArr.mean()
    ssXY = np.sum((xArr - xMean) * (yArr - yMean))
    ssXX = np.sum((xArr - xMean) ** 2)
    if ssXX == 0:
        return 0.0, 0.0
    beta = ssXY / ssXX
    yPred = xMean + beta * (xArr - xMean) + yMean - beta * xMean
    # 수정: y = alpha + beta * x
    alpha = yMean - beta * xMean
    yPred2 = alpha + beta * xArr
    ssTot = np.sum((yArr - yMean) ** 2)
    ssRes = np.sum((yArr - yPred2) ** 2)
    r2 = 1 - ssRes / ssTot if ssTot > 0 else 0.0
    return beta, r2


def run():
    t0 = time.time()
    print("=" * 70)
    print("  098-007: 섹터별 GDP 탄성도 실증 검증")
    print("=" * 70)

    print(f"\n  GDP 성장률: {GDP_GROWTH}")

    results = []

    for sector, stocks in SECTOR_STOCKS.items():
        growth = _computeSectorGrowth(sector, stocks)
        if not growth:
            print(f"\n  {sector}: ❌ 매출 데이터 부족")
            continue

        # 공통 연도
        commonYears = sorted(set(growth.keys()) & set(GDP_GROWTH.keys()))
        if len(commonYears) < 3:
            print(f"\n  {sector}: ❌ 공통 연도 {len(commonYears)}개 미달")
            continue

        gdpVals = [GDP_GROWTH[y] for y in commonYears]
        revVals = [growth[y] for y in commonYears]
        beta, r2 = _olsBeta(gdpVals, revVals)

        hardBeta = HARDCODED_BETA.get(sector, 0.8)
        results.append((sector, beta, r2, hardBeta, len(commonYears)))

        print(f"\n  {sector}")
        print(f"    연도: {commonYears}")
        print(f"    매출 성장률: {[f'{growth[y]:+.1f}%' for y in commonYears]}")
        print(f"    GDP 성장률:  {[f'{GDP_GROWTH[y]:+.1f}%' for y in commonYears]}")
        print(f"    실증 beta: {beta:.2f} (R²={r2:.3f})")
        print(f"    설정 beta: {hardBeta:.1f}")
        print(f"    차이: {beta - hardBeta:+.2f}")

    # 비교 요약
    print(f"\n{'=' * 70}")
    print(f"  비교 요약")
    print(f"{'=' * 70}")
    print(f"  {'섹터':15s} {'실증β':>8s} {'설정β':>8s} {'R²':>8s} {'방향일치':>8s}")
    print(f"  {'─'*47}")

    directionMatch = 0
    empiricalBetas = []
    hardcodedBetas = []
    for sector, beta, r2, hardBeta, n in results:
        match = "✅" if (beta > 0.5 and hardBeta > 0.5) or (beta <= 0.5 and hardBeta <= 0.5) else "❌"
        if match == "✅":
            directionMatch += 1
        empiricalBetas.append(beta)
        hardcodedBetas.append(hardBeta)
        print(f"  {sector:15s} {beta:8.2f} {hardBeta:8.1f} {r2:8.3f} {match:>8s}")

    if results:
        matchRate = directionMatch / len(results)
        # 상관
        if len(empiricalBetas) >= 3:
            corr = float(np.corrcoef(empiricalBetas, hardcodedBetas)[0, 1])
        else:
            corr = 0.0
        print(f"\n  방향성 일치율: {directionMatch}/{len(results)} ({matchRate:.0%})")
        print(f"  실증β vs 설정β 상관: {corr:.3f}")

    print(f"\n  소요시간: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    run()
    print("\n실험 완료.")
