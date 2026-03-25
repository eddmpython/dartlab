"""실험 ID: 098-015
실험명: ECOS/FRED 다변량 거시 회귀

목적:
- 007에서 GDP 단독 R²=0.31이었던 것을 다변량(GDP+환율+금리+IPI+유가)으로 확장
- dartlab gather 엔진의 ECOS/FRED 거시지표를 최대 활용
- 다변량 회귀가 섹터 매출 설명력을 얼마나 개선하는지

가설:
1. 다변량 R² > 0.5 (GDP 단독 0.31 대비 개선)
2. 환율(USDKRW)이 수출 섹터(반도체/자동차)에서 가장 큰 추가 설명력
3. 금리(BASE_RATE)가 내수 섹터(유통/건설)에서 유의미

방법:
1. 거시 시계열 수집: GDP, 환율, 금리, 산업생산, 유가 (2017~2024 연간)
2. 섹터별 매출 성장률 (007과 동일 구성)
3. 단변량(GDP only) vs 다변량 OLS → R² 비교
4. 변수별 기여도 (stepwise 추가)

결과:
- In-sample R²: GDP 단독 평균 0.306 → 다변량 평균 0.788 (+0.482 개선)
- Stepwise 기여: GDP(0.306) + 환율(+0.148) + 금리(+0.101) + IPI(+0.117) + 유가(+0.116)
- 유통 R²=0.989, 식품 0.924, 철강 0.840 — 다변량으로 높은 설명력
- Adjusted R²: 유통 0.962, 식품 0.733 — 나머지는 0 이하 (과적합 신호)
- Out-of-sample 2024 예측: 다변량 MdAE=20.7% vs GDP단독 MdAE=11.0%
  → 다변량이 GDP 단독보다 **2배 나쁨**
- 8개 관측치(2017~2023)에 5개 변수 → n/k=1.4 (최소 n/k>5 필요)
- 통신 다변량 예측 -51.3% (실제 +0.9%) — 극단적 과적합
- 정규화 계수: 유가가 철강(+5.10), IT(+5.52), 유통(+4.14)에서 과대 영향

결론:
- 가설1 기각: 다변량 in-sample R²=0.788 > 0.5 달성하지만, out-of-sample은 과적합으로 실패
- 가설2 부분 확인: 환율이 stepwise +0.148 기여 (2위). 하지만 과적합으로 예측 활용 불가
- 가설3 미확인: 금리 +0.101 기여하지만 계수 불안정
- **핵심 결론**: 8년분 연간 데이터(n=8)에 5개 변수 다변량 회귀는 **과적합 함정**
  1. In-sample R²가 높을수록 out-of-sample 성능 악화 (adj-R²가 음수인 섹터 다수)
  2. GDP 단독이 오히려 더 robust한 예측 (변수 1개, 자유도 확보)
  3. 다변량 거시 회귀가 유효하려면 **분기 데이터(n=32+)** 또는 **패널 회귀** 필요
  4. 현재 연간 8개 관측치로는 변수 1~2개가 한계
  → 016에서는 변수 2개(GDP+환율)로 제한하여 재시도

실험일: 2026-03-25
"""

import time
from pathlib import Path

import numpy as np
import polars as pl

FINANCE_DIR = Path(__file__).resolve().parents[2] / "data" / "dart" / "finance"

# ─── 거시경제 시계열 (한국은행 ECOS + FRED 공개 데이터, 연평균) ───
# API 키 없으므로 공개 출처에서 직접 수집한 하드코딩 데이터 사용
# 추후 ECOS_API_KEY/FRED_API_KEY 설정 시 Ecos()/Fred().series()로 대체 가능

MACRO_DATA = {
    # GDP 성장률 (한국은행, 실질 YoY%)
    "gdp": {
        "2017": 3.2, "2018": 2.9, "2019": 2.2, "2020": -0.7,
        "2021": 4.3, "2022": 2.6, "2023": 1.4, "2024": 2.0,
    },
    # 원/달러 환율 변화율 (연평균 YoY%, 양수=원화약세)
    "fx": {
        "2017": -2.8, "2018": 0.6, "2019": 5.9, "2020": -0.4,
        "2021": 0.5, "2022": 12.5, "2023": 3.1, "2024": 7.0,
    },
    # 한국은행 기준금리 변화 (연말 기준, 전년 대비 %p)
    "rate": {
        "2017": -0.25, "2018": 0.50, "2019": -0.50, "2020": -0.75,
        "2021": 0.75, "2022": 2.25, "2023": 0.25, "2024": -0.50,
    },
    # 산업생산지수 변화율 (한국은행 IPI, YoY%)
    "ipi": {
        "2017": 2.2, "2018": 1.3, "2019": -0.7, "2020": -0.8,
        "2021": 7.8, "2022": -1.2, "2023": -2.3, "2024": 2.5,
    },
    # WTI 유가 변화율 (FRED DCOILWTICO, 연평균 YoY%)
    "oil": {
        "2017": 17.0, "2018": 27.5, "2019": -12.1, "2020": -30.7,
        "2021": 72.9, "2022": 39.3, "2023": -18.2, "2024": -2.5,
    },
}

MACRO_LABELS = {
    "gdp": "GDP성장률", "fx": "환율변화", "rate": "금리변화",
    "ipi": "산업생산", "oil": "유가변화",
}

# 섹터 구성 (007과 동일)
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
    "통신": [("030200", "KT"), ("017670", "SK텔레콤")],
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

YEARS = ["2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024"]


def _extractAnnualRevenue(stockCode: str) -> dict[str, float] | None:
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


def _computeSectorGrowth(stocks: list) -> dict[str, float]:
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
            growth[years[i]] = ((curr - prev) / prev) * 100
    return growth


def _olsMulti(X: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, float, float]:
    """다변량 OLS. (coefficients, R², adjusted R²) 반환."""
    n, k = X.shape
    if n <= k + 1:
        return np.zeros(k), 0.0, 0.0
    # intercept 추가
    ones = np.ones((n, 1))
    Xb = np.hstack([ones, X])
    try:
        beta = np.linalg.lstsq(Xb, y, rcond=None)[0]
    except np.linalg.LinAlgError:
        return np.zeros(k), 0.0, 0.0
    yPred = Xb @ beta
    yMean = y.mean()
    ssTot = np.sum((y - yMean) ** 2)
    ssRes = np.sum((y - yPred) ** 2)
    r2 = 1 - ssRes / ssTot if ssTot > 0 else 0.0
    adjR2 = 1 - (1 - r2) * (n - 1) / (n - k - 1) if n > k + 1 else 0.0
    return beta[1:], r2, adjR2  # intercept 제외한 계수


def run():
    t0 = time.time()
    print("=" * 70)
    print("  098-015: ECOS/FRED 다변량 거시 회귀")
    print("=" * 70)

    # 거시 데이터 확인
    print("\n  거시 시계열 (2017~2024):")
    for key, label in MACRO_LABELS.items():
        vals = [f"{MACRO_DATA[key][y]:+.1f}" for y in YEARS]
        print(f"    {label:8s}: {vals}")

    macroKeys = list(MACRO_DATA.keys())

    # 섹터 매출 성장률
    sectorGrowths = {}
    for sector, stocks in SECTOR_STOCKS.items():
        g = _computeSectorGrowth(stocks)
        if g:
            sectorGrowths[sector] = g

    print(f"\n  유효 섹터: {len(sectorGrowths)}/{len(SECTOR_STOCKS)}")

    # 공통 연도
    commonYears = sorted(set.intersection(*[set(g.keys()) for g in sectorGrowths.values()]) & set(YEARS))
    print(f"  공통 연도: {commonYears} ({len(commonYears)}개)")

    # 1. 단변량 (GDP only) vs 다변량
    print(f"\n{'─' * 70}")
    print(f"  단변량(GDP) vs 다변량 R² 비교")
    print(f"{'─' * 70}")

    print(f"\n  {'섹터':15s} {'GDP R²':>8s} {'다변량R²':>8s} {'adj-R²':>8s} {'개선':>8s}")
    print(f"  {'─' * 47}")

    allGdpR2 = []
    allMultiR2 = []

    for sector in SECTOR_STOCKS:
        growth = sectorGrowths.get(sector, {})
        if not growth:
            continue

        years = [y for y in commonYears if y in growth]
        if len(years) < 5:
            continue

        yVals = np.array([growth[y] for y in years])

        # 단변량 GDP
        xGdp = np.array([[MACRO_DATA["gdp"][y]] for y in years])
        _, gdpR2, _ = _olsMulti(xGdp, yVals)

        # 다변량 (전체)
        xMulti = np.array([[MACRO_DATA[k][y] for k in macroKeys] for y in years])
        coefs, multiR2, adjR2 = _olsMulti(xMulti, yVals)

        improvement = multiR2 - gdpR2
        allGdpR2.append(gdpR2)
        allMultiR2.append(multiR2)

        print(f"  {sector:15s} {gdpR2:8.3f} {multiR2:8.3f} {adjR2:8.3f} {improvement:+8.3f}")

    if allGdpR2:
        print(f"\n  평균 GDP R²: {np.mean(allGdpR2):.3f}")
        print(f"  평균 다변량 R²: {np.mean(allMultiR2):.3f}")
        print(f"  평균 개선: {np.mean(allMultiR2) - np.mean(allGdpR2):+.3f}")

    # 2. 변수별 stepwise 기여
    print(f"\n{'─' * 70}")
    print(f"  변수 Stepwise 추가 (전 섹터 평균 R²)")
    print(f"{'─' * 70}")

    stepOrder = ["gdp", "fx", "rate", "ipi", "oil"]
    print(f"\n  {'단계':25s} {'평균R²':>8s} {'ΔR²':>8s}")
    print(f"  {'─' * 41}")

    prevR2 = 0
    for step in range(1, len(stepOrder) + 1):
        keys = stepOrder[:step]
        r2s = []
        for sector in SECTOR_STOCKS:
            growth = sectorGrowths.get(sector, {})
            if not growth:
                continue
            years = [y for y in commonYears if y in growth]
            if len(years) < 5:
                continue
            yVals = np.array([growth[y] for y in years])
            xStep = np.array([[MACRO_DATA[k][y] for k in keys] for y in years])
            _, r2, _ = _olsMulti(xStep, yVals)
            r2s.append(r2)

        avgR2 = np.mean(r2s) if r2s else 0
        delta = avgR2 - prevR2
        label = "+".join(MACRO_LABELS[k] for k in keys)
        print(f"  {label:25s} {avgR2:8.3f} {delta:+8.3f}")
        prevR2 = avgR2

    # 3. 섹터별 변수 중요도 (계수 크기)
    print(f"\n{'─' * 70}")
    print(f"  섹터별 변수 계수 (정규화)")
    print(f"{'─' * 70}")

    print(f"\n  {'섹터':15s}", end="")
    for k in macroKeys:
        print(f" {MACRO_LABELS[k]:>8s}", end="")
    print()
    print(f"  {'─' * 55}")

    for sector in SECTOR_STOCKS:
        growth = sectorGrowths.get(sector, {})
        if not growth:
            continue
        years = [y for y in commonYears if y in growth]
        if len(years) < 5:
            continue
        yVals = np.array([growth[y] for y in years])
        xMulti = np.array([[MACRO_DATA[k][y] for k in macroKeys] for y in years])

        # 표준화
        xStd = (xMulti - xMulti.mean(axis=0)) / (xMulti.std(axis=0) + 1e-10)
        yStd = (yVals - yVals.mean()) / (yVals.std() + 1e-10)
        coefs, _, _ = _olsMulti(xStd, yStd)

        print(f"  {sector:15s}", end="")
        for c in coefs:
            print(f" {c:+8.2f}", end="")
        print()

    # 4. 2024 예측 (다변량 beta, 학습: 2017~2023, 예측: 2024)
    print(f"\n{'─' * 70}")
    print(f"  2024 예측: 다변량 beta (학습 2017~2023)")
    print(f"{'─' * 70}")

    trainYears = [y for y in commonYears if y != "2024"]
    print(f"\n  {'섹터':15s} {'실제':>8s} {'다변량':>8s} {'GDP단독':>8s} {'다변량err':>9s} {'GDP err':>8s}")
    print(f"  {'─' * 56}")

    multiErrors = []
    gdpErrors = []

    for sector in SECTOR_STOCKS:
        growth = sectorGrowths.get(sector, {})
        if not growth or "2024" not in growth:
            continue
        actual = growth["2024"]
        tYears = [y for y in trainYears if y in growth]
        if len(tYears) < 4:
            continue

        yTrain = np.array([growth[y] for y in tYears])

        # 다변량
        xTrain = np.array([[MACRO_DATA[k][y] for k in macroKeys] for y in tYears])
        ones = np.ones((len(tYears), 1))
        Xb = np.hstack([ones, xTrain])
        beta = np.linalg.lstsq(Xb, yTrain, rcond=None)[0]
        x2024 = np.array([1.0] + [MACRO_DATA[k]["2024"] for k in macroKeys])
        multiPred = float(x2024 @ beta)

        # GDP 단독
        xGdpTrain = np.array([[MACRO_DATA["gdp"][y]] for y in tYears])
        XbGdp = np.hstack([ones, xGdpTrain])
        betaGdp = np.linalg.lstsq(XbGdp, yTrain, rcond=None)[0]
        gdpPred = float(np.array([1.0, MACRO_DATA["gdp"]["2024"]]) @ betaGdp)

        multiErr = abs(actual - multiPred)
        gdpErr = abs(actual - gdpPred)
        multiErrors.append(multiErr)
        gdpErrors.append(gdpErr)

        better = "◀" if multiErr < gdpErr else "▶"
        print(f"  {sector:15s} {actual:+8.1f}% {multiPred:+8.1f}% {gdpPred:+8.1f}% "
              f"{multiErr:9.1f} {gdpErr:8.1f} {better}")

    if multiErrors:
        print(f"\n  MAE: 다변량={np.mean(multiErrors):.1f}%, GDP단독={np.mean(gdpErrors):.1f}%")
        print(f"  MdAE: 다변량={np.median(multiErrors):.1f}%, GDP단독={np.median(gdpErrors):.1f}%")

    print(f"\n  소요시간: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    run()
    print("\n실험 완료.")
