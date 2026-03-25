"""실험 ID: 100-007
실험명: Uncertainty Rating + Fair Value 밴드 (Morningstar 방식)

목적:
- 매출 변동성, 영업레버리지, 재무레버리지로 불확실성 5단계 등급 산출

가설:
1. NAVER → Low/Medium, 삼성바이오 → Very High
2. 불확실성이 높을수록 요구 안전마진이 커야 한다

방법:
1. 대상: 10종목. 분기 timeseries → 연간 집계
2. 매출 CV, DOL(영업레버리지), D/E(재무레버리지), 영업이익 CV
3. 종합 0~100점 → Low/Medium/High/Very High/Extreme

결과:
  종목         매출CV   DOL   D/E  영업CV   점수    등급       밴드
  NAVER       0.35  1.0   0.4  0.34  29.8  Medium     ±25%
  삼성전자       0.15  5.6   0.3  0.40  32.9  Medium     ±25%
  셀트리온       0.50  1.4   0.2  0.34  36.2  High       ±35%
  POSCO홀딩스   0.40  2.2   0.7  0.54  42.5  High       ±35%
  카카오        0.48  2.1   0.8  0.59  48.8  High       ±35%
  LG화학       0.33  4.4   1.1  0.55  49.1  High       ±35%
  현대차        0.24  4.0   1.8  0.56  49.4  High       ±35%
  삼성바이오      0.75  1.6   0.6  0.90  53.8  Very High  ±45%
  한국전력       0.19 59.7   5.0 36.04  84.4  Extreme    ±55%
  KB금융: sales 부재로 제외

결론:
1. [성공] 5단계 분류가 직관과 부합
   - NAVER·삼성전자 Medium: 안정 매출, 합리적 레버리지
   - 삼성바이오 Very High: 매출CV 0.75, 영업CV 0.90
   - 한국전력 Extreme: D/E 5.0, DOL 59.7, 영업CV 36
2. [관찰] DOL 조정(상한 10배)이 효과적 — 이전 상한 5배보다 분포 개선
3. [방향] 업종 기본 tier + Fair Value 밴드를 synthesizer에 연동

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


def calcUncertainty(stockCode: str, name: str) -> dict | None:
    """Uncertainty Rating 산출."""
    series, periods = loadCompany(stockCode, name)
    if series is None:
        return None

    salesD = annualDict(series, periods, "IS", "sales")
    opD = annualDict(series, periods, "IS", "operating_profit")
    tlD = annualDict(series, periods, "BS", "total_liabilities")
    eqD = annualDict(series, periods, "BS", "total_stockholders_equity")

    sales = list(salesD.values())
    opProfit = list(opD.values())

    if len(sales) < 5 or len(opProfit) < 5:
        print(f"  [{stockCode}] {name}: 데이터 부족")
        return None

    # 매출 CV
    revMean = statistics.mean(sales)
    revCV = statistics.stdev(sales) / abs(revMean) if revMean != 0 else 1.0

    # DOL
    dolList = []
    for i in range(1, min(len(sales), len(opProfit))):
        if sales[i - 1] != 0 and opProfit[i - 1] != 0:
            sChg = (sales[i] - sales[i - 1]) / abs(sales[i - 1])
            oChg = (opProfit[i] - opProfit[i - 1]) / abs(opProfit[i - 1])
            if abs(sChg) > 0.01:
                dolList.append(abs(oChg / sChg))
    dol = statistics.median(dolList) if dolList else 2.0

    # D/E
    latestYear = sorted(eqD.keys())[-1] if eqD else None
    deRatio = 0.0
    if latestYear and latestYear in tlD and latestYear in eqD and eqD[latestYear] > 0:
        deRatio = tlD[latestYear] / eqD[latestYear]

    # 영업이익 CV
    opMean = statistics.mean(opProfit)
    opCV = statistics.stdev(opProfit) / abs(opMean) if opMean != 0 else 1.0

    # 종합 (각 최대 25점)
    revScore = min(25, revCV / 0.5 * 25)
    dolScore = min(25, (dol - 1) / 9 * 25)  # DOL 10 이상 = 최대 (조정됨)
    deScore = min(25, deRatio / 3 * 25)
    opScore = min(25, opCV / 1.0 * 25)
    totalScore = revScore + dolScore + deScore + opScore

    if totalScore < 20:
        rating, margin = "Low", 0.15
    elif totalScore < 35:
        rating, margin = "Medium", 0.25
    elif totalScore < 50:
        rating, margin = "High", 0.35
    elif totalScore < 70:
        rating, margin = "Very High", 0.45
    else:
        rating, margin = "Extreme", 0.55

    return {
        "name": name, "revCV": revCV, "dol": dol, "debtEquity": deRatio,
        "opCV": opCV, "revScore": revScore, "dolScore": dolScore,
        "deScore": deScore, "opScore": opScore, "totalScore": round(totalScore, 1),
        "rating": rating, "margin": margin,
    }


def main():
    """Uncertainty Rating 실험."""
    import gc

    print("=" * 70)
    print("007_uncertainty: Uncertainty Rating (연간 기준)")
    print("=" * 70)

    results = []
    for stockCode, name in TARGETS:
        r = calcUncertainty(stockCode, name)
        if r:
            results.append(r)
        gc.collect()

    results.sort(key=lambda x: x["totalScore"])

    print(f"\n{'종목':<12} {'매출CV':>6} {'DOL':>5} {'D/E':>5} {'영업CV':>6} {'점수':>5} {'등급':>10} {'밴드':>5}")
    print("-" * 62)
    for r in results:
        print(
            f"{r['name']:<12} {r['revCV']:>6.2f} {r['dol']:>5.1f} {r['debtEquity']:>5.1f} "
            f"{r['opCV']:>6.2f} {r['totalScore']:>5.1f} {r['rating']:>10} ±{r['margin']:.0%}"
        )
    print("-" * 62)

    print(f"\n[등급별 분포]")
    for rating in ["Low", "Medium", "High", "Very High", "Extreme"]:
        names = [r["name"] for r in results if r["rating"] == rating]
        if names:
            print(f"  {rating:10}: {', '.join(names)}")


if __name__ == "__main__":
    main()
