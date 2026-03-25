"""실험 ID: 100-009
실험명: 5축 Snowflake 캘리브레이션 (Simply Wall St 방식)

목적:
- 5축(Past, Health, Future, Value, Dividends) 스코어를 DART 데이터로 재현
- 각 축 6개 체크 중 산출 가능한 항목 확인

가설:
1. Past와 Health는 DART만으로 완전 산출 가능
2. Value와 Future는 시가총액 의존 → 부분 산출

방법:
1. 대상: 10종목. 분기 timeseries → 연간 집계
2. Past 6체크: 매출CAGR>0, 영업CAGR>0, ROE>15%, NI증가, OM>10%, 3Y흑자
3. Health 6체크: D/E<1, CR>1.5, ICR>3, OCF>0, FCF>0, NetDebt<50%
4. Future 3체크: 매출성장>5%, 영업성장>0, 마진개선

결과:
  종목         Past  Health  Future  Value  Div  Total
  삼성전자       5/6    6/6     2/6    0/6   2/6   15/30
  NAVER       4/6    5/6     3/6    0/6   0/6   12/30
  카카오        3/6    4/6     3/6    0/6   2/6   12/30
  삼성바이오      5/6    3/6     3/6    0/6   0/6   11/30
  셀트리온       4/6    3/6     2/6    0/6   2/6   11/30
  한국전력       4/6    2/6     1/6    0/6   2/6    9/30
  현대차        3/6    1/6     0/6    0/6   2/6    6/30
  POSCO홀딩스   1/6    1/6     0/6    0/6   1/6    3/30
  LG화학       1/6    1/6     0/6    0/6   1/6    3/30

결론:
1. [성공] Past·Health 100% 산출, 삼성전자 Health 6/6 만점
2. [성공] OCF·FCF 연간 집계로 정상 작동 (operating_cashflow snakeId 확인)
3. [성공] 종목 순위가 직관과 부합 — 삼성전자 15점, LG화학 3점
4. [관찰] ROE>15% 전종목 X — 연간 기준에서도 ROE 15% 초과가 드묾 (한국 시장 특성)
5. [블로커] Value 6체크 전부 시총 의존 → 17/30 = 57% 산출 가능
6. [방향] 시총 확보로 Value축 완성, 기존 insight 7영역과 매핑 통합

실험일: 2026-03-25
"""

import sys
import os
import statistics

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))

from _helpers import annualDict, loadCompany

TARGETS = [
    ("005930", "삼성전자"), ("005380", "현대차"), ("035420", "NAVER"),
    ("035720", "카카오"), ("005490", "POSCO홀딩스"), ("051910", "LG화학"),
    ("207940", "삼성바이오"), ("105560", "KB금융"), ("068270", "셀트리온"),
    ("015760", "한국전력"),
]


def calcSnowflake(stockCode: str, name: str) -> dict | None:
    """5축 Snowflake 스코어."""
    series, periods = loadCompany(stockCode, name)
    if series is None:
        return None

    salesD = annualDict(series, periods, "IS", "sales")
    opD = annualDict(series, periods, "IS", "operating_profit")
    niD = annualDict(series, periods, "IS", "net_profit")
    fcD = annualDict(series, periods, "IS", "finance_costs")
    taD = annualDict(series, periods, "BS", "total_assets")
    tlD = annualDict(series, periods, "BS", "total_liabilities")
    eqD = annualDict(series, periods, "BS", "total_stockholders_equity")
    caD = annualDict(series, periods, "BS", "current_assets")
    clD = annualDict(series, periods, "BS", "current_liabilities")
    cashD = annualDict(series, periods, "BS", "cash_and_cash_equivalents")
    ocfD = annualDict(series, periods, "CF", "operating_cashflow")
    capexD = annualDict(series, periods, "CF", "purchase_of_property_plant_and_equipment")
    divD = annualDict(series, periods, "CF", "dividends_paid")

    salesVals = list(salesD.values())
    opVals = list(opD.values())
    niVals = list(niD.values())
    years = sorted(salesD.keys())

    if len(salesVals) < 3:
        print(f"  [{stockCode}] {name}: 데이터 부족")
        return None

    ly = years[-1]  # latest year

    # ═══ PAST ═══
    past = []
    # 1. 매출 CAGR > 0 (5년 또는 가능한 범위)
    if len(salesVals) >= 6:
        cagr = (salesVals[-1] / salesVals[-6]) ** (1 / 5) - 1 if salesVals[-6] > 0 else -1
        past.append(1 if cagr > 0 else 0)
    elif len(salesVals) >= 4:
        cagr = (salesVals[-1] / salesVals[-4]) ** (1 / 3) - 1 if salesVals[-4] > 0 else -1
        past.append(1 if cagr > 0 else 0)
    else:
        past.append(0)

    # 2. 영업이익 CAGR > 0
    if len(opVals) >= 6 and opVals[-6] > 0 and opVals[-1] > 0:
        cagr = (opVals[-1] / opVals[-6]) ** (1 / 5) - 1
        past.append(1 if cagr > 0 else 0)
    else:
        past.append(1 if len(opVals) >= 2 and opVals[-1] > opVals[0] else 0)

    # 3. ROE > 15%
    roe = niD.get(ly, 0) / eqD[ly] * 100 if ly in eqD and eqD[ly] > 0 else 0
    past.append(1 if roe > 15 else 0)

    # 4. 순이익 증가 (전년 대비)
    if len(niVals) >= 2:
        past.append(1 if niVals[-1] > niVals[-2] else 0)
    else:
        past.append(0)

    # 5. 영업이익률 > 10%
    opMargin = opD.get(ly, 0) / salesD[ly] * 100 if ly in salesD and salesD[ly] > 0 else 0
    past.append(1 if opMargin > 10 else 0)

    # 6. 3년 연속 흑자
    if len(niVals) >= 3:
        past.append(1 if all(v > 0 for v in niVals[-3:]) else 0)
    else:
        past.append(0)

    # ═══ HEALTH ═══
    health = []
    # 1. D/E < 1
    de = tlD.get(ly, 0) / eqD[ly] if ly in eqD and eqD[ly] > 0 else 999
    health.append(1 if de < 1 else 0)

    # 2. 유동비율 > 1.5
    cr = caD.get(ly, 0) / clD[ly] if ly in clD and clD[ly] > 0 else 0
    health.append(1 if cr > 1.5 else 0)

    # 3. 이자보상배율 > 3
    icr = opD.get(ly, 0) / fcD[ly] if ly in fcD and fcD[ly] > 0 else 0
    health.append(1 if icr > 3 else 0)

    # 4. 영업CF > 0
    ocf = ocfD.get(ly)
    health.append(1 if ocf and ocf > 0 else 0)

    # 5. FCF > 0
    capex = capexD.get(ly)
    fcf = (ocf - abs(capex)) if ocf and capex else None
    health.append(1 if fcf and fcf > 0 else 0)

    # 6. 순차입금비율 < 50%
    cash = cashD.get(ly, 0)
    netDebt = tlD.get(ly, 0) - cash
    ndRatio = netDebt / eqD[ly] * 100 if ly in eqD and eqD[ly] > 0 else 999
    health.append(1 if ndRatio < 50 else 0)

    # ═══ FUTURE ═══
    future = []
    # 1. 매출 3년 CAGR > 5%
    if len(salesVals) >= 4 and salesVals[-4] > 0:
        cagr3 = (salesVals[-1] / salesVals[-4]) ** (1 / 3) - 1
        future.append(1 if cagr3 > 0.05 else 0)
    else:
        future.append(0)

    # 2. 영업이익 성장
    if len(opVals) >= 4 and opVals[-4] > 0 and opVals[-1] > 0:
        cagr3 = (opVals[-1] / opVals[-4]) ** (1 / 3) - 1
        future.append(1 if cagr3 > 0 else 0)
    else:
        future.append(0)

    # 3. 마진 개선
    if len(salesVals) >= 3 and len(opVals) >= 3:
        m1 = opVals[-3] / salesVals[-3] if salesVals[-3] > 0 else 0
        m2 = opVals[-1] / salesVals[-1] if salesVals[-1] > 0 else 0
        future.append(1 if m2 > m1 else 0)
    else:
        future.append(0)

    future.extend([0, 0, 0])  # 시총 의존 3개

    # ═══ VALUE / DIVIDENDS ═══
    value = [0, 0, 0, 0, 0, 0]  # 시총 의존

    dividends = []
    div = divD.get(ly)
    dividends.append(1 if div and abs(div) > 0 else 0)
    niLatest = niD.get(ly, 0)
    if div and niLatest > 0:
        payout = abs(div) / niLatest * 100
        dividends.append(1 if payout < 80 else 0)
    else:
        dividends.append(0)
    dividends.extend([0, 0, 0, 0])

    pastS = sum(past)
    healthS = sum(health)
    futureS = sum(future)
    valueS = sum(value)
    divS = sum(dividends)
    totalS = pastS + healthS + futureS + valueS + divS

    return {
        "name": name, "past": pastS, "health": healthS, "future": futureS,
        "value": valueS, "dividends": divS, "total": totalS,
        "pastD": past, "healthD": health,
    }


def main():
    """Snowflake 실험."""
    import gc

    print("=" * 70)
    print("009_snowflake: 5축 Snowflake (연간 기준)")
    print("=" * 70)

    results = []
    for stockCode, name in TARGETS:
        r = calcSnowflake(stockCode, name)
        if r:
            results.append(r)
        gc.collect()

    results.sort(key=lambda x: x["total"], reverse=True)

    print(f"\n{'종목':<12} {'Past':>4} {'Health':>6} {'Future':>6} {'Value':>5} {'Div':>3} {'Total':>5}")
    print("-" * 48)
    for r in results:
        print(
            f"{r['name']:<12} {r['past']:>4}/6 {r['health']:>4}/6 "
            f"{r['future']:>4}/6 {r['value']:>3}/6 {r['dividends']:>1}/6 "
            f"{r['total']:>5}/30"
        )
    print("-" * 48)

    print(f"\n[Past 상세]")
    print(f"{'종목':<12} {'매출5Y':>5} {'영업5Y':>5} {'ROE>15':>6} {'NI증가':>5} {'OM>10':>5} {'3Y흑자':>5}")
    print("-" * 48)
    for r in results:
        d = r["pastD"]
        row = " ".join(f"{'O' if v else 'X':>5}" for v in d)
        print(f"{r['name']:<12} {row}")

    print(f"\n[Health 상세]")
    print(f"{'종목':<12} {'D/E<1':>5} {'CR>1.5':>6} {'ICR>3':>5} {'OCF>0':>5} {'FCF>0':>5} {'ND<50':>5}")
    print("-" * 48)
    for r in results:
        d = r["healthD"]
        row = " ".join(f"{'O' if v else 'X':>5}" for v in d)
        print(f"{r['name']:<12} {row}")


if __name__ == "__main__":
    main()
