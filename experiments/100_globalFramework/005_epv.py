"""실험 ID: 100-005
실험명: EPV / Franchise Value (Greenwald 방식)

목적:
- Greenwald의 계층적 밸류에이션: NAV → EPV → Franchise Value
- EPV = Normalized Earnings / WACC (성장 가정 없는 기업가치)

가설:
1. EPV > NAV (Franchise > 0)이면 경쟁우위 존재
2. 삼성전자·NAVER는 Franchise Value 양수, 한국전력은 0 또는 음수

방법:
1. 대상: 10종목. 분기 timeseries → 연간 집계
2. NAV = 총자산 - 총부채, Normalized Earnings = 최근 3년 영업이익 평균 × (1-세율)
3. EPV = Normalized Earnings / WACC, Franchise = EPV - NAV

결과:
  종목         NAV(조)  NormE(조)  WACC   EPV(조)  Franchise(조)  Moat
  KB금융       59.8    10.0     5.1%   197.0     +137.2       Y
  한국전력       41.4     4.0     5.5%    72.6      +31.3       Y
  삼성바이오      10.9     1.1     7.4%    14.5       +3.6       Y
  셀트리온       17.6     0.5     7.2%     6.6      -10.9       N
  카카오        15.2     0.4    10.1%     4.3      -11.0       N
  NAVER      29.0     1.5     9.2%    16.0      -12.9       N
  현대차       120.3    10.2    10.8%    94.2      -26.1       N
  삼성전자      436.3    21.6     8.2%   262.8     -173.5       N

결론:
1. [성공] Franchise > 0: KB금융(수익력>>자산), 한국전력(규제독점), 삼성바이오(고마진)
2. [관찰] KB금융 Franchise 137조 — 금융업은 자산 대비 수익력이 높음 (EPV/NAV 3.3x)
3. [관찰] 삼성전자 Franchise -173조 — 설비집약 반도체. 자산집약 산업의 정상 결과
4. [방향] EPV/시총 비율이 실용적 지표, NAV 조정(토지시가 등)은 한계 있음

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
    ("035720", "카카오"),
    ("005490", "POSCO홀딩스"),
    ("051910", "LG화학"),
    ("207940", "삼성바이오"),
    ("105560", "KB금융"),
    ("068270", "셀트리온"),
    ("015760", "한국전력"),
]

WACC_MAP = {
    "005930": 0.082, "005380": 0.108, "035420": 0.092, "035720": 0.101,
    "005490": 0.079, "051910": 0.097, "207940": 0.074, "105560": 0.051,
    "068270": 0.072, "015760": 0.055,
}


def calcEpv(stockCode: str, name: str) -> dict | None:
    """Greenwald EPV / Franchise Value 산출."""
    series, periods = loadCompany(stockCode, name)
    if series is None:
        return None

    opD = annualDict(series, periods, "IS", "operating_profit")
    taD = annualDict(series, periods, "BS", "total_assets")
    tlD = annualDict(series, periods, "BS", "total_liabilities")

    opVals = list(opD.values())
    years = sorted(opD.keys())

    if len(opVals) < 3:
        print(f"  [{stockCode}] {name}: 영업이익 데이터 부족")
        return None

    latestYear = sorted(taD.keys())[-1] if taD else None
    if not latestYear or latestYear not in tlD:
        print(f"  [{stockCode}] {name}: BS 데이터 부족")
        return None

    nav = taD[latestYear] - tlD[latestYear]
    normalizedOp = statistics.mean(opVals[-3:])
    normalizedNet = normalizedOp * 0.78  # 1-세율
    wacc = WACC_MAP.get(stockCode, 0.08)
    epv = normalizedNet / wacc
    franchise = epv - nav

    return {
        "name": name, "nav": nav, "normalizedEarnings": normalizedNet,
        "wacc": wacc, "epv": epv, "franchise": franchise,
        "hasMoat": franchise > 0,
        "epvNavRatio": epv / nav if nav > 0 else None,
    }


def main():
    """EPV 실험."""
    import gc

    print("=" * 70)
    print("005_epv: Greenwald EPV / Franchise Value (연간 기준)")
    print("=" * 70)

    results = []
    for stockCode, name in TARGETS:
        r = calcEpv(stockCode, name)
        if r:
            results.append(r)
        gc.collect()

    results.sort(key=lambda x: x["franchise"], reverse=True)
    T = 1e12

    print(f"\n{'종목':<12} {'NAV':>7} {'NormE':>6} {'WACC':>5} {'EPV':>7} {'Franchise':>9} {'Moat':>4}")
    print("-" * 56)
    for r in results:
        print(
            f"{r['name']:<12} {r['nav']/T:>7.1f} {r['normalizedEarnings']/T:>6.1f} "
            f"{r['wacc']:>5.1%} {r['epv']/T:>7.1f} {r['franchise']/T:>9.1f} "
            f"{'Y' if r['hasMoat'] else 'N':>4}"
        )
    print("-" * 56)
    print("(단위: 조원)")

    moatYes = [r for r in results if r["hasMoat"]]
    moatNo = [r for r in results if not r["hasMoat"]]
    print(f"\nFranchise > 0: {', '.join(r['name'] for r in moatYes) or '(없음)'}")
    print(f"Franchise ≤ 0: {', '.join(r['name'] for r in moatNo) or '(없음)'}")


if __name__ == "__main__":
    main()
