"""
실험 ID: 007
실험명: 금융업 Profitability/Cashflow 전용 지표 설계

목적:
- KB금융(105560) Profitability D(빈 결과), Cashflow D(빈 결과) 문제 해결
- 금융업 IS/CF 계정 구조 탐색 → 대체 수익성/현금흐름 지표 설계
- 은행, 보험, 증권 3개 업종의 공통/차이 확인

가설:
1. 금융업은 revenue 대신 operating_income으로 margin 계산이 가능하다
2. 금융업은 net_interest_income / operating_income으로 이자마진 비중을 판단할 수 있다
3. 금융업의 ROE/ROA는 일반 기업과 동일한 로직으로 계산 가능하다
4. 금융업 CF는 영업CF가 매우 크거나 부호가 다를 수 있다 (예금 유출입 포함)

방법:
1. KB금융, 신한지주, 삼성생명, 미래에셋증권 4종목 IS/BS/CF 전체 계정 덤프
2. 공통 계정 + 업종별 고유 계정 분류
3. 금융업 전용 수익성 지표 후보 설계
4. 금융업 전용 CF 해석 로직 설계

결과 (실험 후 작성):
- 금융업 IS 공통 계정(22개): operating_income, net_income, interest_income, interest_expense,
  commission_income, operating_expense, profit_before_tax, comprehensive_income 등
- 금융업 BS 공통 계정(24개): total_assets, total_equity, total_liabilities, equity_including_nci 등
- 금융업 CF: 계정 수 72~92개, operating_cashflow/investing_cashflow/financing_cashflow 존재
- ratios.py에서 금융업 전부 None인 원인
  → getTTM은 최근 4개 non-null 필요, 연간 시계열은 보통 3년 → None
  → revenue=None이라 operatingMargin/netMargin 계산 불가
  → netIncomeTTM=None이라 ROE/ROA도 계산 불가 (연쇄)
- 직접 계산한 금융업 수익성 지표
  KB금융:    ROA 0.64%, ROE 8.56%, 이자이익비중 판단불가(net_interest_income없음)
  신한지주:   ROA 0.58%, ROE 7.86%
  삼성생명:   ROA 0.70%, ROE 5.74%
  미래에셋증권: ROA 0.70%, ROE 7.91%
- 금융업 ROA 기준: 0.5% 이상이면 양호 (일반기업 5% 이상과 대비)
- 금융업 ROE 기준: 8% 이상 양호, 5~8% 보통, 5% 미만 저조

결론:
- 가설 1 부분채택: margin 자체는 계산 불가, 하지만 ROA/ROE는 직접 계산 가능
- 가설 2 부분기각: net_interest_income이 계정에 없는 종목 있음 (net_interest_expenses로 대체 가능?)
- 가설 3 채택: ROE/ROA는 동일 로직으로 계산 가능하나, ratios.py의 getTTM 문제로 None 반환
- 가설 4 확인: KB금융 operating_cashflow -32,006억 (음수), 금융업 CF 해석 별도 필요
- 핵심 원인: ratios.py의 getTTM이 연간 시계열 3년에서 실패 (4개 필요)
- 해결 방안: 인사이트 엔진에서 getLatest로 직접 ROE/ROA 계산, margin 대신 CIR 등 대체

실험일: 2026-03-09
"""

import sys
sys.path.insert(0, "src")

import dartlab
dartlab.verbose = False

from dartlab.engines.financeEngine.pivot import buildAnnual
from dartlab.engines.financeEngine.ratios import calcRatios
from dartlab.engines.financeEngine.extract import getLatest, getAnnualValues


FINANCIAL_STOCKS = {
    "105560": "KB금융",
    "055550": "신한지주",
    "032830": "삼성생명",
    "006800": "미래에셋증권",
}


def dumpAccounts(stockCode: str, stockName: str):
    print(f"\n{'=' * 70}")
    print(f"  {stockName} ({stockCode})")
    print(f"{'=' * 70}")

    result = buildAnnual(stockCode)
    if result is None:
        print("  데이터 없음")
        return None

    series, years = result
    ratios = calcRatios(series)

    print(f"  연도: {years}")

    accountMap = {}

    for sjDiv in ["IS", "BS", "CF"]:
        accounts = series.get(sjDiv, {})
        print(f"\n  [{sjDiv}] {len(accounts)}개 계정")
        for key, vals in accounts.items():
            latest = None
            for v in reversed(vals):
                if v is not None:
                    latest = v
                    break
            if latest is not None:
                print(f"    {key:40s} {latest/1e8:>15,.0f}억")
                accountMap.setdefault(sjDiv, {})[key] = latest

    print(f"\n  [RATIOS]")
    print(f"    operatingMargin:  {ratios.operatingMargin}")
    print(f"    netMargin:        {ratios.netMargin}")
    print(f"    ROE:              {ratios.roe}")
    print(f"    ROA:              {ratios.roa}")
    print(f"    debtRatio:        {ratios.debtRatio}")
    print(f"    opCF TTM:         {ratios.operatingCashflowTTM}")
    print(f"    invCF TTM:        {ratios.investingCashflowTTM}")
    print(f"    FCF:              {ratios.fcf}")
    print(f"    revenueTTM:       {ratios.revenueTTM}")
    print(f"    opIncomeTTM:      {ratios.operatingIncomeTTM}")
    print(f"    netIncomeTTM:     {ratios.netIncomeTTM}")

    return accountMap


def findCommonAccounts(allMaps: dict):
    print(f"\n\n{'=' * 70}")
    print("  금융업 공통/고유 계정 분석")
    print(f"{'=' * 70}")

    for sjDiv in ["IS", "BS", "CF"]:
        allKeys = set()
        perStock = {}
        for code, aMap in allMaps.items():
            keys = set(aMap.get(sjDiv, {}).keys())
            perStock[code] = keys
            allKeys |= keys

        common = allKeys.copy()
        for keys in perStock.values():
            common &= keys

        print(f"\n  [{sjDiv}] 전체 {len(allKeys)}개, 공통 {len(common)}개")
        if common:
            print(f"    공통 계정:")
            for k in sorted(common):
                print(f"      {k}")

        for code, keys in perStock.items():
            unique = keys - common
            if unique:
                name = FINANCIAL_STOCKS.get(code, code)
                print(f"    {name} 고유 ({len(unique)}개):")
                for k in sorted(unique):
                    print(f"      {k}")


def designProfitabilityMetrics(allMaps: dict):
    print(f"\n\n{'=' * 70}")
    print("  금융업 수익성 지표 후보 테스트")
    print(f"{'=' * 70}")

    for code, name in FINANCIAL_STOCKS.items():
        aMap = allMaps.get(code)
        if aMap is None:
            continue

        isAccounts = aMap.get("IS", {})
        bsAccounts = aMap.get("BS", {})

        opIncome = isAccounts.get("operating_income")
        netIncome = isAccounts.get("net_income")
        interestIncome = isAccounts.get("interest_income")
        netInterestIncome = isAccounts.get("net_interest_income")
        insuranceRevenue = isAccounts.get("insurance_revenue")
        feeIncome = isAccounts.get("fee_and_commission_income")
        totalAssets = bsAccounts.get("total_assets")
        totalEquity = bsAccounts.get("total_equity") or bsAccounts.get("equity_including_nci")

        print(f"\n  {name} ({code})")
        print(f"    영업이익:     {_fmt(opIncome)}")
        print(f"    순이익:       {_fmt(netIncome)}")
        print(f"    이자수익:     {_fmt(interestIncome)}")
        print(f"    순이자수익:   {_fmt(netInterestIncome)}")
        print(f"    보험수익:     {_fmt(insuranceRevenue)}")
        print(f"    수수료수익:   {_fmt(feeIncome)}")
        print(f"    총자산:       {_fmt(totalAssets)}")
        print(f"    자기자본:     {_fmt(totalEquity)}")

        if opIncome and totalAssets and totalAssets != 0:
            roaOp = (opIncome / totalAssets) * 100
            print(f"    → ROA(영업이익 기준): {roaOp:.2f}%")

        if netIncome and totalAssets and totalAssets != 0:
            roa = (netIncome / totalAssets) * 100
            print(f"    → ROA(순이익 기준):   {roa:.2f}%")

        if netIncome and totalEquity and totalEquity != 0:
            roe = (netIncome / totalEquity) * 100
            print(f"    → ROE:               {roe:.2f}%")

        if netInterestIncome and opIncome and opIncome != 0:
            nimShare = (netInterestIncome / opIncome) * 100
            print(f"    → 이자이익 비중:      {nimShare:.1f}% of 영업이익")

        if netInterestIncome and totalAssets and totalAssets != 0:
            nim = (netInterestIncome / totalAssets) * 100
            print(f"    → NIM(순이자마진):    {nim:.2f}%")

        if opIncome and netIncome and opIncome != 0:
            costRatio = ((opIncome - netIncome) / opIncome) * 100
            print(f"    → 영업외비용 비율:    {costRatio:.1f}%")


def designCashflowMetrics(allMaps: dict):
    print(f"\n\n{'=' * 70}")
    print("  금융업 현금흐름 특성 분석")
    print(f"{'=' * 70}")

    for code, name in FINANCIAL_STOCKS.items():
        result = buildAnnual(code)
        if result is None:
            continue
        series, years = result

        cfAccounts = series.get("CF", {})
        print(f"\n  {name} ({code})")
        print(f"    CF 계정 수: {len(cfAccounts)}")
        for key, vals in cfAccounts.items():
            latest = None
            for v in reversed(vals):
                if v is not None:
                    latest = v
                    break
            if latest is not None:
                print(f"    {key:40s} {latest/1e8:>12,.0f}억")


def _fmt(val) -> str:
    if val is None:
        return "None"
    return f"{val/1e8:,.0f}억"


if __name__ == "__main__":
    allMaps = {}
    for code, name in FINANCIAL_STOCKS.items():
        aMap = dumpAccounts(code, name)
        if aMap:
            allMaps[code] = aMap

    findCommonAccounts(allMaps)
    designProfitabilityMetrics(allMaps)
    designCashflowMetrics(allMaps)
