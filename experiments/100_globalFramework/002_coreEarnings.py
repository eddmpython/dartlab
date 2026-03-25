"""실험 ID: 100-002
실험명: Core Earnings 분리 — 비경상 항목 식별

목적:
- DART XBRL IS 계정에서 비경상 항목을 분리하여 Core Earnings 산출 검증
- Core Earnings vs Reported Earnings의 변동성(CV) 비교

가설:
1. Core Earnings = operating_profit × (1-세율)은 Reported보다 변동성이 낮아야
2. 금융업(KB금융)은 금융수익/비용이 본업이므로 별도 처리 필요

방법:
1. 대상: 5종목. 분기 timeseries → 연간 집계
2. Core = 연간 operating_profit × (1-유효세율)
3. Reported = 연간 net_profit
4. CV(변동계수) 비교

결과:
  종목         Core CV  Reported CV  개선
  삼성전자       0.40      0.37       X
  현대차        0.56      0.47       X
  NAVER       0.34      1.95       O
  POSCO홀딩스   0.54      0.79       O
  KB금융       0.42      0.52       O
  CV 개선 비율: 3/5 (60%)

결론:
1. [채택] Core Earnings = op_profit×(1-세율)로 NAVER·POSCO·KB금융에서 CV 개선
2. [관찰] 삼성전자·현대차는 비경상 항목 비중이 작아 Core≈Reported
3. [관찰] NAVER Reported CV 1.95 → Core 0.34로 극적 개선 (기타비용 일회성 반영)
4. [방향] 금융업도 Core가 Reported보다 안정 — 다만 금융업은 해석 주의

실험일: 2026-03-25
"""

import sys
import os
import statistics

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))

from _helpers import annualDict, loadCompany

TARGETS = [
    ("005930", "삼성전자"),
    ("005380", "현대차"),
    ("035420", "NAVER"),
    ("005490", "POSCO홀딩스"),
    ("105560", "KB금융"),
]


def analyzeEarnings(stockCode: str, name: str) -> dict | None:
    """Core vs Reported 비교."""
    series, periods = loadCompany(stockCode, name)
    if series is None:
        return None

    opD = annualDict(series, periods, "IS", "operating_profit")
    niD = annualDict(series, periods, "IS", "net_profit")
    taxD = annualDict(series, periods, "IS", "income_taxes")
    pbtD = annualDict(series, periods, "IS", "profit_before_tax")

    years = sorted(set(opD) & set(niD))
    if len(years) < 3:
        print(f"  [{stockCode}] {name}: 데이터 부족")
        return None

    # 유효세율 추정
    effectiveTax = 0.22
    ly = years[-1]
    if ly in taxD and ly in pbtD and pbtD[ly] > 0:
        t = taxD[ly] / pbtD[ly]
        if 0 < t < 0.5:
            effectiveTax = t

    print(f"\n  [{stockCode}] {name}: 유효세율 {effectiveTax:.1%}, {len(years)}년")

    coreVals = []
    reportedVals = []
    for y in years:
        op = opD[y]
        ni = niD[y]
        coreVals.append(op * (1 - effectiveTax))
        reportedVals.append(ni)

    coreMean = statistics.mean(coreVals)
    coreStd = statistics.stdev(coreVals) if len(coreVals) > 1 else 0
    coreCV = coreStd / abs(coreMean) if coreMean != 0 else float("inf")

    repMean = statistics.mean(reportedVals)
    repStd = statistics.stdev(reportedVals) if len(reportedVals) > 1 else 0
    repCV = repStd / abs(repMean) if repMean != 0 else float("inf")

    print(f"    Core CV={coreCV:.2f}, Reported CV={repCV:.2f}")

    return {
        "name": name, "coreCV": coreCV, "reportedCV": repCV,
        "improved": coreCV < repCV,
        "coreMean": coreMean, "reportedMean": repMean,
    }


def main():
    """Core Earnings 실험."""
    import gc

    print("=" * 60)
    print("002_coreEarnings: Core Earnings 분리 (연간 기준)")
    print("=" * 60)

    results = []
    for stockCode, name in TARGETS:
        r = analyzeEarnings(stockCode, name)
        if r:
            results.append(r)
        gc.collect()

    print(f"\n{'종목':<12} {'Core CV':>8} {'Reported CV':>12} {'CV 개선':>8}")
    print("-" * 42)
    improved = 0
    for r in results:
        check = "O" if r["improved"] else "X"
        print(f"{r['name']:<12} {r['coreCV']:>8.2f} {r['reportedCV']:>12.2f} {check:>8}")
        if r["improved"]:
            improved += 1

    if results:
        print("-" * 42)
        print(f"CV 개선 비율: {improved}/{len(results)} ({improved/len(results):.0%})")


if __name__ == "__main__":
    main()
