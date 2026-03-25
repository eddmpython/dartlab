"""실험 ID: 100-008
실험명: Forward P/E, PEG (예측 기반 배수)

목적:
- 정규화 마진 × 매출 트렌드로 Forward EPS 근사 가능성 검증

가설:
1. 정규화 마진 × (매출 × (1+CAGR))로 Forward 순이익 추정 가능
2. Forward NI vs Trailing NI 비교로 이익 방향성 확인

방법:
1. 대상: 10종목. 분기 timeseries → 연간 집계
2. 정규화마진 = 최근 3년 영업이익률 평균
3. 매출CAGR = 최근 3년 CAGR
4. Forward NI = 매출예측 × 정규화마진 × (1-세율)

결과:
  종목         NormM   CAGR  매출(조)  FwdNI(조) TrailNI(조) 방향
  삼성전자       8.8%   3.3%    334    23.7      45.2     ↓
  현대차        8.1%  -0.7%    139     8.8       5.9     ↑
  한국전력       6.5%   1.2%     74     3.8       7.3     ↓
  NAVER      17.4%  13.6%     12     1.9       1.8     ↑
  삼성바이오     33.0%  12.3%      4     1.2       1.3     ↓
  POSCO홀딩스   4.2% -29.5%     52     1.2       0.8     ↑
  LG화학       3.0%  -3.9%     46     1.0      -1.0     ↑
  셀트리온      22.7%   7.1%      3     0.5       0.5     ↑
  카카오        7.5%   6.0%      8     0.5       0.5     ↓

결론:
1. [성공] 정규화마진이 현실적 — 삼성바이오 33%, NAVER 17.4%, LG화학 3%
2. [성공] CAGR로 성장 방향 포착 — NAVER 13.6%, POSCO -29.5%
3. [관찰] FwdNI < TrailNI인 종목(삼성전자·한국전력·삼성바이오) = 정규화가 최근 호실적 평탄화
4. [블로커] 시가총액 없이 Forward P/E·PEG 산출 불가 → gather.price 필요

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


def calcForwardMultiple(stockCode: str, name: str) -> dict | None:
    """Forward Multiple 산출."""
    series, periods = loadCompany(stockCode, name)
    if series is None:
        return None

    salesD = annualDict(series, periods, "IS", "sales")
    opD = annualDict(series, periods, "IS", "operating_profit")
    niD = annualDict(series, periods, "IS", "net_profit")

    salesVals = list(salesD.values())
    years = sorted(salesD.keys())

    if len(salesVals) < 4:
        print(f"  [{stockCode}] {name}: 데이터 부족")
        return None

    # 정규화 마진 (최근 3년)
    margins = []
    for y in years[-3:]:
        s = salesD.get(y)
        op = opD.get(y)
        if s and s > 0 and op is not None:
            margins.append(op / s)
    normalizedMargin = statistics.mean(margins) if margins else 0

    # 매출 3년 CAGR
    s0, s1 = salesVals[-4], salesVals[-1]
    salesCagr = (s1 / s0) ** (1 / 3) - 1 if s0 > 0 and s1 > 0 else 0

    # Forward
    forwardSales = s1 * (1 + salesCagr)
    forwardOp = forwardSales * normalizedMargin
    forwardNet = forwardOp * 0.78

    # Trailing
    trailingNet = niD.get(years[-1])

    return {
        "name": name, "normalizedMargin": normalizedMargin, "salesCagr": salesCagr,
        "forwardSales": forwardSales, "forwardNet": forwardNet,
        "trailingNet": trailingNet,
        "latestSales": s1,
    }


def main():
    """Forward Multiple 실험."""
    import gc

    print("=" * 70)
    print("008_forwardMultiple: Forward P/E, PEG (연간 기준)")
    print("=" * 70)

    results = []
    for stockCode, name in TARGETS:
        r = calcForwardMultiple(stockCode, name)
        if r:
            results.append(r)
        gc.collect()

    results.sort(key=lambda x: x["forwardNet"], reverse=True)
    T = 1e12

    print(f"\n{'종목':<12} {'NormM':>6} {'CAGR':>6} {'매출':>6} {'FwdNI':>6} {'TrailNI':>7} {'방향':>4}")
    print("-" * 52)
    for r in results:
        tniStr = f"{r['trailingNet']/T:.1f}" if r["trailingNet"] else "N/A"
        direction = "↑" if r["forwardNet"] > (r["trailingNet"] or 0) else "↓"
        print(
            f"{r['name']:<12} {r['normalizedMargin']:>6.1%} {r['salesCagr']:>6.1%} "
            f"{r['latestSales']/T:>6.0f} {r['forwardNet']/T:>6.1f} {tniStr:>7} {direction:>4}"
        )
    print("-" * 52)
    print("(단위: 조원)")


if __name__ == "__main__":
    main()
