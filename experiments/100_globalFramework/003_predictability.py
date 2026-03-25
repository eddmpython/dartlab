"""실험 ID: 100-003
실험명: Business Predictability Score (GuruFocus 방식)

목적:
- 매출/영업이익의 장기 일관성을 0-10점으로 정량화
- GuruFocus의 Business Predictability Rank을 DART 데이터로 재현

가설:
1. 매출과 영업이익의 연도별 변동계수(CV)로 일관성 측정 가능
2. 연속 성장 연수, 적자 전환 횟수가 추가 판별력을 가진다
3. 직관적으로 안정적인 기업(삼성전자, KB금융)이 높은 점수를 받아야 한다

방법:
1. 대상: 10종목 (001_wacc.py와 동일)
2. 분기 timeseries → 연간 집계 (IS: Q1+Q2+Q3+Q4 합산)
3. 매출 CV, 영업이익 CV (연간 기준)
4. 연속 매출 성장 연수, 영업이익 적자 연수
5. 가중합산 → 0-10 스케일 정규화

결과:
  종목         년수  매출CV  영업CV  연속성장  적자  점수
  NAVER       10   0.35   0.34     5    0   7.2
  삼성전자       10   0.15   0.40     2    0   6.5
  현대차        10   0.24   0.56     0    0   4.5
  카카오        10   0.48   0.59     2    0   4.2
  LG화학       10   0.33   0.55     0    0   4.1
  셀트리온       10   0.50   0.34     0    0   3.9
  POSCO홀딩스   10   0.40   0.54     0    0   3.8
  삼성바이오       9   0.75   0.90     0    0   2.5
  한국전력       10   0.19  36.04     0    5   1.6
  KB금융: sales 부재(금융업)
  점수 범위: 1.6~7.2, 평균 4.3

결론:
1. [채택] 연간 기준 4요소 Predictability가 직관과 부합
   - NAVER 7.2(5년 연속성장+안정), 한국전력 1.6(적자5년+영업CV 36)
2. [관찰] 삼성전자 매출CV 0.15로 최저(안정) — 반도체 대형주 특성
3. [주의] 금융업 sales 부재, 한전 영업CV 36(거의 적자↔흑자 진동)
4. [방향] 금융업 매출 프록시(이자수익+수수료수익) 필요

실험일: 2026-03-25
"""

import sys
import os
import statistics

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))

from _helpers import annualValues, loadCompany

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


def calcPredictability(stockCode: str, name: str) -> dict | None:
    """Business Predictability Score 산출."""
    series, periods = loadCompany(stockCode, name)
    if series is None:
        return None

    revenue = annualValues(series, periods, "IS", "sales")
    opProfit = annualValues(series, periods, "IS", "operating_profit")

    if len(revenue) < 3:
        print(f"  [{stockCode}] {name}: 데이터 부족 (매출 {len(revenue)}년)")
        return None

    # ── 1. 매출 CV (낮을수록 좋음) ──
    revMean = statistics.mean(revenue)
    revCV = statistics.stdev(revenue) / abs(revMean) if revMean != 0 and len(revenue) > 1 else 1.0
    revScore = max(0, min(2.5, 2.5 * (1 - revCV / 0.5)))

    # ── 2. 영업이익 CV (낮을수록 좋음) ──
    opCV = 1.0
    opScore = 0.0
    if len(opProfit) > 1:
        opMean = statistics.mean(opProfit)
        opCV = statistics.stdev(opProfit) / abs(opMean) if opMean != 0 else 1.0
        opScore = max(0, min(2.5, 2.5 * (1 - opCV / 0.8)))

    # ── 3. 연속 매출 성장 연수 (길수록 좋음) ──
    consecutiveGrowth = 0
    for i in range(len(revenue) - 1, 0, -1):
        if revenue[i] > revenue[i - 1]:
            consecutiveGrowth += 1
        else:
            break
    growthScore = min(2.5, consecutiveGrowth * 0.5)

    # ── 4. 영업이익 적자 연수 (적을수록 좋음) ──
    lossYears = sum(1 for v in opProfit if v < 0)
    totalYears = len(opProfit)
    lossRatio = lossYears / totalYears if totalYears > 0 else 0
    lossScore = max(0, min(2.5, 2.5 * (1 - lossRatio / 0.5)))

    totalScore = revScore + opScore + growthScore + lossScore
    finalScore = round(totalScore, 1)

    return {
        "stockCode": stockCode,
        "name": name,
        "years": len(revenue),
        "revCV": revCV,
        "opCV": opCV,
        "consecutiveGrowth": consecutiveGrowth,
        "lossYears": lossYears,
        "revScore": revScore,
        "opScore": opScore,
        "growthScore": growthScore,
        "lossScore": lossScore,
        "totalScore": finalScore,
    }


def main():
    """Predictability 실험 메인."""
    import gc

    print("=" * 70)
    print("003_predictability: Business Predictability Score (연간 기준)")
    print("=" * 70)

    results = []
    for stockCode, name in TARGETS:
        r = calcPredictability(stockCode, name)
        if r:
            results.append(r)
        gc.collect()

    results.sort(key=lambda x: x["totalScore"], reverse=True)

    print(f"\n{'종목':<12} {'년수':>4} {'매출CV':>7} {'영업CV':>7} {'연속성장':>6} {'적자':>4} {'점수':>5}")
    print("-" * 50)

    for r in results:
        print(
            f"{r['name']:<12} {r['years']:>4} {r['revCV']:>7.2f} {r['opCV']:>7.2f} "
            f"{r['consecutiveGrowth']:>6} {r['lossYears']:>4} {r['totalScore']:>5.1f}"
        )

    print("-" * 50)
    if results:
        scores = [r["totalScore"] for r in results]
        print(f"점수 범위: {min(scores):.1f} ~ {max(scores):.1f}")
        print(f"점수 평균: {statistics.mean(scores):.1f}")

    print(f"\n[점수 분해 (각 최대 2.5점)]")
    print(f"{'종목':<12} {'매출안정':>7} {'영업안정':>7} {'연속성장':>7} {'무적자':>7} {'합계':>6}")
    print("-" * 50)
    for r in results:
        print(
            f"{r['name']:<12} {r['revScore']:>7.1f} {r['opScore']:>7.1f} "
            f"{r['growthScore']:>7.1f} {r['lossScore']:>7.1f} {r['totalScore']:>6.1f}"
        )


if __name__ == "__main__":
    main()
