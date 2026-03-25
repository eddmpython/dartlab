"""실험 ID: 100-006
실험명: 잔여이익 모델 (Penman Residual Income)

목적:
- Value = BPS + Σ PV(NI - Ke×B) + Terminal
- 금융주(KB금융)에 특히 적합한지 검증

가설:
1. ROE > Ke이면 RI > 0 (가치 창출)
2. 자산 중심 기업(금융, 유틸리티)에서 안정적 결과

방법:
1. 대상: 10종목. 분기 timeseries → 연간 집계
2. RI = 순이익 - Ke × 기초자기자본 (전년말)
3. RI Value = 최신자본 + Σ PV(RI) + Terminal(g=2%)

결과:
  종목         자본(조)  avgRI(조)  ROE%   Ke    판정
  삼성전자      436.3    12.3    13.2  8.2%  창출
  NAVER      29.0     1.4    30.2  9.2%  창출
  삼성바이오      10.9     0.1     7.6  7.4%  창출
  셀트리온       17.6     0.1    13.0  7.2%  창출
  현대차       120.3    -2.9     7.0 10.8%  파괴
  한국전력       41.4    -7.4    -6.1  5.5%  파괴
  POSCO홀딩스   61.5    -1.3     5.6  7.9%  파괴
  LG화학       47.1    -1.1     7.3  9.7%  파괴
  카카오        15.2    -0.8     2.2 10.1%  파괴
  KB금융: RI 산출 1년뿐(BS Q4 데이터 부족)

결론:
1. [성공] ROE>Ke → 가치 창출 판정이 직관과 정확히 부합
   - 삼성전자(+5.0%p), NAVER(+21.0%p), 셀트리온(+5.8%p) 가치 창출
   - 한국전력(-11.6%p), 카카오(-7.9%p) 가치 파괴
2. [관찰] NAVER ROE 30.2% — 경자산 플랫폼의 극적 자본효율
3. [관찰] 삼성전자 RI Value 618조 — 자본 436조 + 초과수익 PV
4. [방향] KB금융 BS Q4 매핑 이슈 해결 필요, Terminal g=GDP 연동

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

KE_MAP = {
    "005930": 0.082, "005380": 0.108, "035420": 0.092, "035720": 0.101,
    "005490": 0.079, "051910": 0.097, "207940": 0.074, "105560": 0.051,
    "068270": 0.072, "015760": 0.055,
}


def calcResidualIncome(stockCode: str, name: str) -> dict | None:
    """잔여이익 모델 산출."""
    series, periods = loadCompany(stockCode, name)
    if series is None:
        return None

    niD = annualDict(series, periods, "IS", "net_profit")
    eqD = annualDict(series, periods, "BS", "total_stockholders_equity")

    if not niD or not eqD:
        print(f"  [{stockCode}] {name}: 데이터 부족")
        return None

    ke = KE_MAP.get(stockCode, 0.08)
    g = 0.02
    years = sorted(set(niD) & set(eqD))

    riList = []
    roeList = []
    for i, y in enumerate(years):
        ni = niD[y]
        prevYear = years[i - 1] if i > 0 else None
        begEq = eqD[prevYear] if prevYear and prevYear in eqD else None
        if ni is not None and begEq and begEq > 0:
            ri = ni - ke * begEq
            riList.append({"year": y, "ni": ni, "begEq": begEq, "ri": ri})
            roeList.append(ni / begEq * 100)

    if len(riList) < 3:
        print(f"  [{stockCode}] {name}: RI 산출 가능 연도 부족 ({len(riList)}년)")
        return None

    latestEq = eqD[years[-1]]
    pvSum = sum(item["ri"] / ((1 + ke) ** (idx + 1)) for idx, item in enumerate(riList))
    lastRi = riList[-1]["ri"]
    pvTerminal = (lastRi * (1 + g) / (ke - g)) / ((1 + ke) ** len(riList)) if ke > g else 0
    riValue = latestEq + pvSum + pvTerminal
    avgRoe = statistics.mean(roeList) if roeList else None
    avgRi = statistics.mean([item["ri"] for item in riList])

    return {
        "name": name, "latestEquity": latestEq, "avgRi": avgRi,
        "pvRiSum": pvSum, "pvTerminal": pvTerminal, "riValue": riValue,
        "riYears": len(riList), "ke": ke, "avgRoe": avgRoe,
        "valueCreating": avgRi > 0,
    }


def main():
    """잔여이익 모델 실험."""
    import gc

    print("=" * 70)
    print("006_residualIncome: Penman 잔여이익 모델 (연간 기준)")
    print("=" * 70)

    results = []
    for stockCode, name in TARGETS:
        r = calcResidualIncome(stockCode, name)
        if r:
            results.append(r)
        gc.collect()

    results.sort(key=lambda x: x["riValue"], reverse=True)
    T = 1e12

    print(f"\n{'종목':<12} {'자본':>6} {'avgRI':>7} {'PV(RI)':>7} {'Term':>6} {'RIValue':>7} {'ROE':>5} {'Ke':>5} {'판정':>4}")
    print("-" * 68)
    for r in results:
        verdict = "창출" if r["valueCreating"] else "파괴"
        roeStr = f"{r['avgRoe']:.1f}" if r["avgRoe"] else "N/A"
        print(
            f"{r['name']:<12} {r['latestEquity']/T:>6.1f} {r['avgRi']/T:>7.1f} "
            f"{r['pvRiSum']/T:>7.1f} {r['pvTerminal']/T:>6.1f} {r['riValue']/T:>7.1f} "
            f"{roeStr:>5} {r['ke']:>5.1%} {verdict:>4}"
        )
    print("-" * 68)
    print("(단위: 조원, ROE: %)")

    creating = [r for r in results if r["valueCreating"]]
    destroying = [r for r in results if not r["valueCreating"]]
    print(f"\n가치 창출 (RI>0): {', '.join(r['name'] for r in creating) or '(없음)'}")
    print(f"가치 파괴 (RI<0): {', '.join(r['name'] for r in destroying) or '(없음)'}")

    print(f"\n[ROE - Ke 스프레드]")
    for r in results:
        if r["avgRoe"]:
            spread = r["avgRoe"] - r["ke"] * 100
            print(f"  {r['name']:<12} ROE {r['avgRoe']:.1f}% - Ke {r['ke']:.1%} = {spread:+.1f}%p")


if __name__ == "__main__":
    main()
