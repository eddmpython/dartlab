"""실험 ID: 098-008
실험명: 거시경제 충격 backtesting (2020 코로나 + 2022 금리인상)

목적:
- 실제 거시경제 충격 시 섹터별 매출 반응이 SECTOR_ELASTICITY 방향과 일치하는지
- GDP/환율/금리 복합 충격에서 섹터별 차별 반응 확인
- 007의 실증 beta를 활용한 예측 vs 하드코딩 beta 예측 비교

가설:
1. 2020 코로나: 경기민감 섹터(반도체/자동차/유통)의 매출 하락이
   방어적 섹터(식품/통신)보다 큼
2. 2022 금리인상: 내수의존 섹터(유통/건설) 타격 > 수출주(반도체/자동차)
3. 실증 beta 기반 예측이 하드코딩 beta보다 실제 매출 변화에 가까움 (MAE 개선)

방법:
1. 2020/2022 실제 거시지표 변화 (GDP, 환율, 금리)
2. 섹터별 실제 매출 변화 계산 (2019→2020, 2021→2022)
3. 하드코딩 beta 기반 예측 매출 변화 vs 실제
4. 실증 beta(007) 기반 예측 매출 변화 vs 실제
5. MAE 비교

결과:
- 2020 코로나 MAE: 하드코딩=6.3%, 실증=17.8% → 실증 악화 11.5%p
- 2022 금리인상 MAE: 하드코딩=16.5%, 실증=28.9% → 실증 악화 12.5%p
- 전체 MAE: 하드코딩=11.4%, 실증=23.4% → 실증 악화 12.0%p
- 실증beta는 식품(방어적)에서만 하드코딩보다 우수 (역방향 beta 효과)
- 2020 코로나: 반도체(+2.8%), 화학(+5.1%), IT(+2.8%)가 GDP 하락에도 매출 증가
  → GDP 단일변수로 설명 불가 (비대면/반도체 수요 구조변화)
- 2022 금리인상: 유통(+29.7%), IT(+26.4%)가 금리인상에도 매출 급증
  → 코로나 후 보복소비/디지털전환 효과가 금리 영향 압도
- 가설1: 부분 채택 — 유통(-18.0%) 대폭 하락 vs 식품(+12.6%) 방어 맞음
  단 반도체(+2.8%)는 경기민감인데도 매출 증가
- 가설2: 기각 — 2022 내수(유통+29.7%)가 수출(반도체+8.1%)보다 오히려 급증

결론:
- 가설1 부분 채택: 유통/자동차 경기민감 하락 확인, 식품 방어 확인
  단 반도체/화학/IT는 코로나 특수로 GDP와 디커플링
- 가설2 기각: 2022 보복소비 효과로 내수 섹터가 오히려 급증
- 가설3 기각: 실증 beta(GDP only)가 하드코딩보다 MAE 12%p 악화
  → 007의 큰 실증 beta가 예측을 과대하게 만듦
  → GDP 단일변수 회귀는 과적합 위험이 크고 일반화 실패
- **핵심 발견**: GDP 탄성도만으로 거시 충격을 예측하는 것은 근본적 한계가 있음
  1. 코로나 같은 구조적 충격은 GDP로 포착 불가 (산업별 비대칭 효과)
  2. 보복소비/수요이전 같은 2차 효과가 1차 충격보다 클 수 있음
  3. 하드코딩 beta의 보수적 크기(~1.0)가 오히려 안정적 예측 제공
  4. 거시 시나리오 시뮬레이션에는 GDP+환율+금리 복합 beta가 최소 필요
     → 나아가 기업별/시점별 가변 beta 또는 regime-switching 모델 검토 필요

실험일: 2026-03-25
"""

import time
from pathlib import Path

import numpy as np
import polars as pl

FINANCE_DIR = Path(__file__).resolve().parents[2] / "data" / "dart" / "finance"

# 거시경제 시나리오 (실제 데이터)
MACRO_SCENARIOS = {
    "2020_코로나": {
        "year": "2020",
        "prevYear": "2019",
        "gdpChange": -0.7 - 2.2,  # 2020(-0.7) vs 2019(2.2) = -2.9%p 변화
        "fxChange": 5.0,  # 원/달러 약 5% 원화 약세
        "rateChange": -0.75,  # 기준금리 1.25→0.50%p
        "description": "코로나19 팬데믹, GDP -0.7%, 기준금리 인하",
    },
    "2022_금리인상": {
        "year": "2022",
        "prevYear": "2021",
        "gdpChange": 2.6 - 4.3,  # 2022(2.6) vs 2021(4.3) = -1.7%p 변화
        "fxChange": 12.0,  # 원/달러 약 12% 원화 약세
        "rateChange": 2.25,  # 기준금리 1.0→3.25 (누적 +2.25%p)
        "description": "미 연준 급격 금리인상, 원화 약세, GDP 둔화",
    },
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

# 하드코딩 beta (simulation.py 기준)
HARDCODED_BETA = {
    "반도체": {"gdp": 1.8, "fx": 0.8, "rate": -0.3},
    "자동차": {"gdp": 1.3, "fx": 0.6, "rate": -0.2},
    "화학": {"gdp": 1.2, "fx": 0.5, "rate": -0.1},
    "철강": {"gdp": 1.4, "fx": 0.4, "rate": -0.2},
    "통신": {"gdp": 0.4, "fx": 0.1, "rate": 0.1},
    "식품": {"gdp": 0.3, "fx": 0.1, "rate": 0.0},
    "IT/소프트웨어": {"gdp": 1.0, "fx": 0.3, "rate": -0.1},
    "유통": {"gdp": 0.8, "fx": -0.2, "rate": -0.3},
}

# 007 실증 beta (GDP만 — 환율/금리는 아직 미산출)
EMPIRICAL_GDP_BETA = {
    "반도체": 3.93, "자동차": 1.87, "화학": 7.02, "철강": 12.77,
    "통신": 8.22, "식품": -2.40, "IT/소프트웨어": 5.73, "유통": 12.88,
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


def _computeSectorRevenue(stocks: list) -> dict[str, float]:
    """섹터 대표 종목의 합산 매출."""
    yearTotals = {}
    count = 0
    for code, name in stocks:
        rev = _extractAnnualRevenue(code)
        if not rev:
            continue
        count += 1
        for year, val in rev.items():
            yearTotals[year] = yearTotals.get(year, 0) + val
    return yearTotals


def _predictGrowth(sector: str, scenario: dict, useEmpirical: bool) -> float:
    """beta 기반 매출 변화율 예측 (%)."""
    gdpChg = scenario["gdpChange"]
    if useEmpirical:
        # 실증 beta는 GDP만 있으므로 GDP beta만 사용
        gdpBeta = EMPIRICAL_GDP_BETA.get(sector, 1.0)
        return gdpBeta * gdpChg
    else:
        betas = HARDCODED_BETA.get(sector, {"gdp": 0.8, "fx": 0.0, "rate": 0.0})
        return (betas["gdp"] * gdpChg +
                betas["fx"] * scenario["fxChange"] +
                betas["rate"] * scenario["rateChange"])


def run():
    t0 = time.time()
    print("=" * 70)
    print("  098-008: 거시경제 충격 backtesting")
    print("=" * 70)

    # 섹터별 매출 데이터 수집
    sectorRevenues = {}
    for sector, stocks in SECTOR_STOCKS.items():
        revs = _computeSectorRevenue(stocks)
        if revs:
            sectorRevenues[sector] = revs

    print(f"\n  유효 섹터: {len(sectorRevenues)}/{len(SECTOR_STOCKS)}")

    allHardErrors = []
    allEmpErrors = []

    for scenarioName, scenario in MACRO_SCENARIOS.items():
        print(f"\n{'─' * 70}")
        print(f"  시나리오: {scenarioName}")
        print(f"  {scenario['description']}")
        print(f"  GDP 변화: {scenario['gdpChange']:+.1f}%p, "
              f"환율: {scenario['fxChange']:+.1f}%, "
              f"금리: {scenario['rateChange']:+.2f}%p")
        print(f"{'─' * 70}")

        print(f"\n  {'섹터':15s} {'실제':>8s} {'하드β':>8s} {'실증β':>8s} "
              f"{'하드err':>8s} {'실증err':>8s}")
        print(f"  {'─' * 55}")

        hardErrors = []
        empErrors = []

        for sector in SECTOR_STOCKS:
            revs = sectorRevenues.get(sector, {})
            prevRev = revs.get(scenario["prevYear"])
            currRev = revs.get(scenario["year"])
            if not prevRev or not currRev or prevRev == 0:
                print(f"  {sector:15s}    데이터 부족")
                continue

            actualGrowth = ((currRev - prevRev) / prevRev) * 100
            hardPred = _predictGrowth(sector, scenario, useEmpirical=False)
            empPred = _predictGrowth(sector, scenario, useEmpirical=True)

            hardErr = abs(actualGrowth - hardPred)
            empErr = abs(actualGrowth - empPred)
            hardErrors.append(hardErr)
            empErrors.append(empErr)
            allHardErrors.append(hardErr)
            allEmpErrors.append(empErr)

            better = "◀" if empErr < hardErr else ("▶" if hardErr < empErr else "=")
            print(f"  {sector:15s} {actualGrowth:+8.1f}% {hardPred:+8.1f}% {empPred:+8.1f}% "
                  f"{hardErr:8.1f} {empErr:8.1f} {better}")

        if hardErrors:
            hardMAE = np.mean(hardErrors)
            empMAE = np.mean(empErrors)
            print(f"\n  MAE: 하드코딩={hardMAE:.1f}%, 실증={empMAE:.1f}%")
            print(f"  실증 {'개선' if empMAE < hardMAE else '악화'}: "
                  f"{abs(empMAE - hardMAE):.1f}%p")

    # 종합
    print(f"\n{'=' * 70}")
    print(f"  종합 비교")
    print(f"{'=' * 70}")
    if allHardErrors:
        totalHardMAE = np.mean(allHardErrors)
        totalEmpMAE = np.mean(allEmpErrors)
        print(f"  전체 MAE: 하드코딩={totalHardMAE:.1f}%, 실증={totalEmpMAE:.1f}%")
        print(f"  실증 {'개선' if totalEmpMAE < totalHardMAE else '악화'}: "
              f"{abs(totalEmpMAE - totalHardMAE):.1f}%p")

        # 가설 검증
        print(f"\n  가설 검증:")

        # 가설1: 2020 경기민감 > 방어적 하락
        print(f"\n  가설1 (2020 코로나: 경기민감 > 방어적 하락):")
        for sector in ["반도체", "자동차", "유통", "식품", "통신"]:
            revs = sectorRevenues.get(sector, {})
            prev = revs.get("2019")
            curr = revs.get("2020")
            if prev and curr and prev != 0:
                g = ((curr - prev) / prev) * 100
                tag = "경기민감" if sector in ["반도체", "자동차", "유통"] else "방어적"
                print(f"    {sector:12s} ({tag}): {g:+.1f}%")

        # 가설2: 2022 내수 > 수출 타격
        print(f"\n  가설2 (2022 금리인상: 내수 > 수출 타격):")
        for sector in ["유통", "식품", "반도체", "자동차"]:
            revs = sectorRevenues.get(sector, {})
            prev = revs.get("2021")
            curr = revs.get("2022")
            if prev and curr and prev != 0:
                g = ((curr - prev) / prev) * 100
                tag = "내수" if sector in ["유통", "식품"] else "수출"
                print(f"    {sector:12s} ({tag}): {g:+.1f}%")

    print(f"\n  소요시간: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    run()
    print("\n실험 완료.")
