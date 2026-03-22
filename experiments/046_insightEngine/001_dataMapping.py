"""
실험 ID: 001
실험명: DartWings ↔ dartlab 데이터 구조 매핑 검증

목적:
- DartWings insightEngine이 사용하는 데이터 키와 dartlab financeEngine의 시계열 키가 어떻게 대응되는지 확인
- dartlab 시계열 dict에서 insightEngine이 필요로 하는 모든 값을 뽑을 수 있는지 검증
- 성장률/변동성 등 파생 지표 계산이 dartlab 데이터로 가능한지 확인

가설:
1. DartWings의 TimeSeriesData.values 키와 dartlab series[sjDiv][snakeId] 간 1:1 매핑이 가능하다
2. dartlab의 ratios.py calcRatios()가 이미 대부분의 인사이트 입력값을 계산하고 있다
3. reportEngine pivot 데이터로 governance 인사이트를 만들 수 있다

방법:
1. 삼성전자(005930) financeEngine 시계열 빌드 (분기별 + 연간)
2. ratios 계산 결과와 DartWings가 필요로 하는 값 비교
3. reportEngine pivot 데이터 확인
4. 매핑 테이블 작성

결과 (실험 후 작성):
- DartWings 12개 필요 키 전부 dartlab에서 OK (revenue, operating_income, net_income, margins, ratios, CF)
- 분기 시계열 40개(2015_Q4~2025_Q3), 연간 11년치 — 성장률/변동성 계산 충분
- ratios.py가 Profitability/Health/Cashflow 입력값을 이미 다 제공
- Valuation(PER/PBR)만 시가총액 미제공으로 MISSING — Phase 2
- reportEngine pivot 결과(DividendResult, MajorHolderResult, AuditResult, EmployeeResult, ExecutiveResult)로 Governance 입력값 확보

결론:
- 가설 1,2,3 모두 채택
- dartlab financeEngine + reportEngine 데이터만으로 insightEngine 구현 가능
- Performance는 시계열 직접 접근 필요, 나머지는 ratios 결과로 충분

실험일: 2026-03-09
"""

import sys

sys.path.insert(0, "src")

import dartlab

dartlab.verbose = False

from dartlab.engines.financeEngine.extract import getAnnualValues, getLatest, getTTM
from dartlab.engines.financeEngine.pivot import buildAnnual, buildTimeseries
from dartlab.engines.financeEngine.ratios import calcRatios

STOCK = "005930"


def checkFinanceMapping():
    print("=" * 70)
    print("1. financeEngine 시계열 → DartWings 인사이트 매핑 검증")
    print("=" * 70)

    result = buildTimeseries(STOCK)
    if result is None:
        print("시계열 빌드 실패")
        return
    series, periods = result

    print(f"\nperiods: {len(periods)}개 ({periods[0]} ~ {periods[-1]})")

    dwKeysMapping = {
        "revenue": ("IS", "revenue"),
        "operating_income": ("IS", "operating_income"),
        "net_income": ("IS", "net_income"),
        "operatingMargin": "RATIO",
        "netMargin": "RATIO",
        "roe": "RATIO",
        "roa": "RATIO",
        "debtRatio": "RATIO",
        "currentRatio": "RATIO",
        "operating_cashflow": ("CF", "operating_cashflow"),
        "investing_cashflow": ("CF", "investing_cashflow"),
        "financing_cashflow": ("CF", "financing_cashflow"),
    }

    print("\n[DartWings 필요 키 → dartlab 매핑]")
    print(f"{'DartWings key':<25} {'dartlab 소스':<20} {'최신값':>15} {'상태'}")
    print("-" * 70)

    for dwKey, src in dwKeysMapping.items():
        if src == "RATIO":
            r = calcRatios(series)
            val = getattr(r, dwKey, None)
            srcLabel = "ratios.py"
        else:
            sjDiv, snakeId = src
            val = getLatest(series, sjDiv, snakeId)
            srcLabel = f"series[{sjDiv}][{snakeId}]"

        status = "OK" if val is not None else "MISSING"
        valStr = f"{val:>15,.0f}" if isinstance(val, (int, float)) and abs(val) > 100 else f"{val}"
        print(f"{dwKey:<25} {srcLabel:<20} {valStr:>15} {status}")

    print("\n[시계열 길이 확인 — 성장률/변동성 계산 가능성]")
    for sjDiv in ["IS", "CF", "BS"]:
        keys = list(series.get(sjDiv, {}).keys())[:5]
        for k in keys:
            vals = series[sjDiv][k]
            nonNull = sum(1 for v in vals if v is not None)
            print(f"  {sjDiv}.{k}: {nonNull}/{len(vals)} non-null")


def checkAnnualMapping():
    print("\n" + "=" * 70)
    print("2. 연간 시계열 — 성장률 계산 검증")
    print("=" * 70)

    result = buildAnnual(STOCK)
    if result is None:
        print("연간 빌드 실패")
        return
    series, years = result

    print(f"\nyears: {years}")

    revenueVals = getAnnualValues(series, "IS", "revenue")
    opIncomeVals = getAnnualValues(series, "IS", "operating_income")

    print(f"\n매출 시계열 ({len(revenueVals)}개):")
    for i, (y, v) in enumerate(zip(years, revenueVals)):
        vStr = f"{v/1e8:,.0f}억" if v else "None"
        growth = ""
        if i > 0 and v and revenueVals[i - 1] and revenueVals[i - 1] > 0:
            g = ((v - revenueVals[i - 1]) / abs(revenueVals[i - 1])) * 100
            growth = f" (YoY {g:+.1f}%)"
        print(f"  {y}: {vStr}{growth}")

    print(f"\n영업이익 시계열 ({len(opIncomeVals)}개):")
    for i, (y, v) in enumerate(zip(years, opIncomeVals)):
        vStr = f"{v/1e8:,.0f}억" if v else "None"
        print(f"  {y}: {vStr}")


def checkRatiosCompleteness():
    print("\n" + "=" * 70)
    print("3. ratios → DartWings insightEngine 입력값 완전성 체크")
    print("=" * 70)

    result = buildAnnual(STOCK)
    if result is None:
        print("연간 빌드 실패")
        return
    series, years = result
    r = calcRatios(series)

    dwInsightInputs = {
        "Performance": ["revenueTTM", "operatingIncomeTTM", "netIncomeTTM"],
        "Profitability": ["operatingMargin", "netMargin", "roe", "roa"],
        "Health": ["debtRatio", "currentRatio"],
        "Cashflow": ["operatingCashflowTTM", "investingCashflowTTM", "fcf"],
        "Valuation": ["per", "pbr", "psr", "evEbitda"],
    }

    for category, keys in dwInsightInputs.items():
        print(f"\n  [{category}]")
        for key in keys:
            val = getattr(r, key, None)
            status = "OK" if val is not None else "MISSING (시가총액 미제공)" if key in ["per", "pbr", "psr", "evEbitda"] else "MISSING"
            if val is not None:
                if abs(val) > 1000:
                    print(f"    {key:<30} = {val:>15,.0f}  {status}")
                else:
                    print(f"    {key:<30} = {val:>15.2f}  {status}")
            else:
                print(f"    {key:<30} = {'None':>15}  {status}")


def checkReportData():
    print("\n" + "=" * 70)
    print("4. reportEngine → Governance 인사이트 입력값")
    print("=" * 70)

    c = dartlab.Company(STOCK)
    if c.report is None:
        print("report 데이터 없음 — governance 인사이트는 finance-only로 동작 필요")
        return

    rpt = c.report

    div = rpt.dividend
    print(f"\n  dividend: {'있음' if div is not None else '없음'}")
    if div is not None:
        print(f"    type: {type(div).__name__}")
        print(f"    years: {div.years}")
        print(f"    dps: {div.dps}")
        print(f"    dividendYield: {div.dividendYield}")

    emp = rpt.employee
    print(f"\n  employee: {'있음' if emp is not None else '없음'}")
    if emp is not None:
        print(f"    type: {type(emp).__name__}")
        print(f"    years: {emp.years}")
        print(f"    totalEmployee: {emp.totalEmployee}")

    major = rpt.majorHolder
    print(f"\n  majorHolder: {'있음' if major is not None else '없음'}")
    if major is not None:
        print(f"    type: {type(major).__name__}")
        print(f"    years: {major.years}")
        print(f"    totalShareRatio: {major.totalShareRatio}")
        if major.latestHolders:
            print(f"    latestHolders[0]: {major.latestHolders[0]}")

    audit = rpt.audit
    print(f"\n  audit: {'있음' if audit is not None else '없음'}")
    if audit is not None:
        print(f"    type: {type(audit).__name__}")
        print(f"    years: {audit.years}")
        print(f"    opinions: {audit.opinions}")
        print(f"    auditors: {audit.auditors}")

    exec_ = rpt.executive
    print(f"\n  executive: {'있음' if exec_ is not None else '없음'}")
    if exec_ is not None:
        print(f"    type: {type(exec_).__name__}")
        print(f"    totalCount: {exec_.totalCount}")
        print(f"    outsideCount: {exec_.outsideCount}")


def summarize():
    print("\n" + "=" * 70)
    print("5. 매핑 결론")
    print("=" * 70)
    print("""
DartWings insightEngine → dartlab 매핑 정리:

[Performance] 실적 분석
  revenue growth      ← series["IS"]["revenue"] YoY 계산
  opIncome growth     ← series["IS"]["operating_income"] YoY 계산
  volatility          ← 최근 4분기 값에서 max 변화율 계산
  → 시계열 직접 접근 필요 (ratios에 없음)

[Profitability] 수익성 분석
  operatingMargin     ← ratios.operatingMargin ✓
  netMargin           ← ratios.netMargin ✓
  roe                 ← ratios.roe ✓
  roa                 ← ratios.roa ✓
  → ratios 결과로 충분

[Health] 재무건전성
  debtRatio           ← ratios.debtRatio ✓
  currentRatio        ← ratios.currentRatio ✓
  → ratios 결과로 충분

[Cashflow] 현금흐름
  operatingCF         ← ratios.operatingCashflowTTM ✓
  investingCF         ← ratios.investingCashflowTTM ✓
  fcf                 ← ratios.fcf ✓
  → ratios 결과로 충분

[Governance] 지배구조
  majorHolder ratio   ← reportEngine.majorHolder pivot DataFrame
  audit opinion       ← reportEngine 직접 접근 필요 (pivot에 없을 수 있음)
  → reportEngine 데이터 구조 추가 확인 필요

[Valuation] 밸류에이션
  per, pbr, psr       ← ratios (marketCap 필요!)
  perBand, pbrBand    ← 시계열 PER/PBR 히스토리 필요 (현재 없음)
  → Phase 2에서 다룸 (주가 데이터 소스 필요)

핵심 발견:
1. ratios.py가 Profitability/Health/Cashflow의 기본 입력값을 이미 다 계산함
2. Performance는 "시계열 성장률 + 변동성" 계산이 추가로 필요
3. Governance는 reportEngine 피벗 결과를 직접 써야 함
4. Valuation 인사이트는 시가총액 의존 → Phase 2로 분리
""")


if __name__ == "__main__":
    checkFinanceMapping()
    checkAnnualMapping()
    checkRatiosCompleteness()
    checkReportData()
    summarize()
