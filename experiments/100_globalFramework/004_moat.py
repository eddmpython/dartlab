"""실험 ID: 100-004
실험명: Economic Moat 정량 프록시 (Morningstar 방식)

목적:
- Morningstar의 5가지 경쟁우위 소스를 DART 재무데이터로 정량 측정
- ROIC > WACC 지속 여부를 Moat 필수조건으로 검증

가설:
1. ROIC - WACC 스프레드가 양수이면 경쟁우위 존재
2. 5가지 Moat 소스를 재무 프록시로 정량 근사 가능
3. 직관적으로 Wide Moat 기업(삼성전자, NAVER)이 높은 점수를 받아야 한다

방법:
1. 대상: 10종목. 분기 timeseries → 연간 집계
2. 5소스 정량 프록시 (각 0~2점):
   - 원가우위: 영업이익률 수준 + 안정성
   - 무형자산: 무형자산/총자산 비율
   - 전환비용: 매출 변동성(낮을수록 높음)
   - 네트워크효과: 매출성장 vs CAPEX 레버리지
   - 효율적규모: 자산회전율 + ROA
3. ROIC 보너스: 최근 3년 ROIC > 8%이면 +2점

결과:
  종목         원가  무형  전환  네트워크  규모  ROIC+  합계  판정
  삼성전자       1.4  0.5  1.0   0.6   1.6   0.0   5.1  None
  NAVER       1.5  0.8  0.0   1.5   1.0   0.0   4.8  None
  카카오        1.2  1.9  0.0   1.3   0.4   0.0   4.8  None
  셀트리온       1.0  0.0  0.0   1.6   1.1   0.0   3.6  None
  현대차        1.2  0.0  0.4   0.8   0.7   0.0   3.1  None
  POSCO홀딩스   1.1  0.0  0.0   0.6   1.3   0.0   3.0  None
  LG화학       1.1  0.3  0.0   0.0   1.3   0.0   2.7  None
  삼성바이오      1.0  0.0  0.0   1.0   0.4   0.0   2.4  None
  한국전력       0.0  0.0  0.8   0.3   0.2   0.0   1.2  None
  avgROIC: 삼성전자 4.9%, NAVER 4.7%, 삼성바이오 7.0%

결론:
1. [부분 성공] 5소스 점수 합산으로 종목간 순위 구분 가능
   - 삼성전자·NAVER 상위, 한국전력 최하위 — 직관 부합
2. [관찰] ROIC 보너스 전종목 0 — ROIC 5~7%로 WACC(8%) 미달
   → 한국 대기업 ROIC가 글로벌 기준 낮음, 보너스 임계값 조정 필요
3. [관찰] 카카오 무형자산 1.9점(18.8%) — 플랫폼 M&A로 영업권 반영
4. [관찰] 네트워크효과: NAVER 1.5, 셀트리온 1.6 — 고성장+저CAPEX
5. [방향] Moat 임계값 조정(9/6→7/4 등), ROIC 보너스 임계 하향(8→5%)

실험일: 2026-03-25
"""

import sys
import os
import statistics

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))

from _helpers import annualValues, annualDict, loadCompany

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


def calcMoat(stockCode: str, name: str) -> dict | None:
    """Economic Moat 5소스 정량 프록시 산출."""
    series, periods = loadCompany(stockCode, name)
    if series is None:
        return None

    salesD = annualDict(series, periods, "IS", "sales")
    opD = annualDict(series, periods, "IS", "operating_profit")
    taD = annualDict(series, periods, "BS", "total_assets")
    tlD = annualDict(series, periods, "BS", "total_liabilities")
    eqD = annualDict(series, periods, "BS", "total_stockholders_equity")
    clD = annualDict(series, periods, "BS", "current_liabilities")
    iaD = annualDict(series, periods, "BS", "intangible_assets")
    capexD = annualDict(series, periods, "CF", "purchase_of_property_plant_and_equipment")

    sales = list(salesD.values())
    opProfit = list(opD.values())
    years = sorted(salesD.keys())

    if len(sales) < 3 or len(opProfit) < 3:
        print(f"  [{stockCode}] {name}: 데이터 부족")
        return None

    # ── 1. 원가우위 (Cost Advantage) ──
    opMargins = []
    for y in years:
        s = salesD.get(y)
        op = opD.get(y)
        if s and s > 0 and op is not None:
            opMargins.append(op / s * 100)

    costScore = 0.0
    if len(opMargins) >= 3:
        avgMargin = statistics.mean(opMargins)
        marginStd = statistics.stdev(opMargins) if len(opMargins) > 1 else 0
        levelScore = min(1.0, max(0, avgMargin / 15))
        stabilityScore = min(1.0, max(0, 1 - marginStd / 10))
        costScore = levelScore + stabilityScore

    # ── 2. 무형자산 (Intangible Assets) ──
    intangibleScore = 0.0
    latestYear = years[-1]
    ia = iaD.get(latestYear)
    ta = taD.get(latestYear)
    if ia and ta and ta > 0:
        intangibleRatio = ia / ta * 100
        intangibleScore = min(2.0, intangibleRatio / 10)  # 20%+ = 2.0
    else:
        intangibleRatio = None

    # ── 3. 전환비용 (Switching Costs) ──
    switchScore = 0.0
    if len(sales) >= 3:
        revMean = statistics.mean(sales)
        revCV = statistics.stdev(sales) / abs(revMean) if revMean != 0 else 1.0
        switchScore = min(2.0, max(0, 2.0 * (1 - revCV / 0.3)))

    # ── 4. 네트워크 효과 (Network Effect) ──
    networkScore = 0.0
    if len(sales) >= 4 and capexD:
        s0 = sales[-4] if sales[-4] > 0 else None
        s1 = sales[-1]
        latestCapex = capexD.get(latestYear) or capexD.get(years[-2] if len(years) > 1 else latestYear)
        if s0 and s1 > 0 and latestCapex:
            cagr = (s1 / s0) ** (1 / 3) - 1
            capexIntensity = abs(latestCapex) / s1
            growthPt = min(1.0, max(0, cagr / 0.10))
            effPt = min(1.0, max(0, 1 - capexIntensity / 0.20))
            networkScore = growthPt + effPt

    # ── 5. 효율적 규모 (Efficient Scale) ──
    scaleScore = 0.0
    turnovers = []
    roaList = []
    for y in years:
        s = salesD.get(y)
        ta_y = taD.get(y)
        op_y = opD.get(y)
        if s and ta_y and ta_y > 0:
            turnovers.append(s / ta_y)
        if op_y is not None and ta_y and ta_y > 0:
            roaList.append(op_y / ta_y * 100)
    if turnovers:
        scaleScore += min(1.0, max(0, (statistics.mean(turnovers) - 0.2) / 0.8))
    if roaList:
        scaleScore += min(1.0, max(0, statistics.mean(roaList) / 10))

    # ── ROIC 보너스 ──
    roicList = []
    for y in years:
        op_y = opD.get(y)
        ta_y = taD.get(y)
        cl_y = clD.get(y)
        if op_y is not None and ta_y and cl_y is not None:
            ic = ta_y - cl_y
            if ic > 0:
                roicList.append(op_y * 0.78 / ic * 100)

    roicBonus = 0.0
    avgRoic = None
    if len(roicList) >= 3:
        recent3 = roicList[-3:]
        avgRoic = statistics.mean(recent3)
        yearsAbove = sum(1 for r in recent3 if r > 8)
        if yearsAbove == 3:
            roicBonus = 2.0
        elif yearsAbove >= 2:
            roicBonus = 1.0

    totalScore = costScore + intangibleScore + switchScore + networkScore + scaleScore
    finalScore = round(totalScore + roicBonus, 1)

    if finalScore >= 9:
        moatRating = "Wide"
    elif finalScore >= 6:
        moatRating = "Narrow"
    else:
        moatRating = "None"

    return {
        "stockCode": stockCode,
        "name": name,
        "costScore": round(costScore, 2),
        "intangibleScore": round(intangibleScore, 2),
        "switchScore": round(switchScore, 2),
        "networkScore": round(networkScore, 2),
        "scaleScore": round(scaleScore, 2),
        "roicBonus": round(roicBonus, 1),
        "totalScore": finalScore,
        "moatRating": moatRating,
        "avgRoic": round(avgRoic, 1) if avgRoic else None,
        "intangibleRatio": round(intangibleRatio, 1) if intangibleRatio else None,
    }


def main():
    """Economic Moat 실험."""
    import gc

    print("=" * 70)
    print("004_moat: Economic Moat 5소스 정량 프록시 (연간 기준)")
    print("=" * 70)

    results = []
    for stockCode, name in TARGETS:
        r = calcMoat(stockCode, name)
        if r:
            results.append(r)
        gc.collect()

    results.sort(key=lambda x: x["totalScore"], reverse=True)

    print(f"\n{'종목':<12} {'원가':>5} {'무형':>5} {'전환':>5} {'네트워크':>6} {'규모':>5} {'ROIC+':>5} {'합계':>5} {'판정':>6}")
    print("-" * 62)
    for r in results:
        print(
            f"{r['name']:<12} {r['costScore']:>5.1f} {r['intangibleScore']:>5.1f} "
            f"{r['switchScore']:>5.1f} {r['networkScore']:>6.1f} {r['scaleScore']:>5.1f} "
            f"{r['roicBonus']:>5.1f} {r['totalScore']:>5.1f} {r['moatRating']:>6}"
        )
    print("-" * 62)

    print(f"\n[보조 지표]")
    print(f"{'종목':<12} {'avgROIC':>8} {'무형자산%':>8}")
    print("-" * 30)
    for r in results:
        roicStr = f"{r['avgRoic']:.1f}%" if r["avgRoic"] else "N/A"
        intStr = f"{r['intangibleRatio']:.1f}%" if r["intangibleRatio"] else "N/A"
        print(f"{r['name']:<12} {roicStr:>8} {intStr:>8}")

    print(f"\n[Moat 분포]")
    for rating in ["Wide", "Narrow", "None"]:
        names = [r["name"] for r in results if r["moatRating"] == rating]
        print(f"  {rating:6}: {', '.join(names) if names else '(없음)'}")


if __name__ == "__main__":
    main()
