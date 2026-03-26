"""
실험 ID: 016
실험명: 섹터별 재무비율 벤치마크 데이터 수집

목적:
- KIND 전체 종목의 finance parquet에서 섹터별 재무비율 분포 측정
- 영업이익률, ROE, 부채비율, 유동비율 4개 지표의 섹터별 중앙값/사분위수 확인
- 현재 insightEngine 절대 기준 (영업이익률 >20% 우수, 부채비율 <50% 양호 등)의 적정성 검증

가설:
1. 섹터별 재무비율 분포가 유의미하게 다를 것 (반도체 vs 은행 영업이익률 차이 >10%p)
2. 현재 절대 기준은 일부 업종에서 편향된 등급을 줄 것 (건설업 부채비율 거의 F 예상)
3. finance parquet 보유 종목의 80% 이상에서 4개 비율 중 3개 이상 계산 가능할 것

방법:
1. getKindList()로 전체 종목 확보
2. classify()로 섹터/산업군 배정
3. financeEngine buildAnnual + calcRatios로 비율 계산
4. 섹터별 [중앙값, Q1, Q3, min, max, N] 테이블 작성
5. 현재 절대 기준과 비교해서 편향 영역 식별

결과 (실험 후 작성):
- 2663종목 중 finance 보유 2508 (94.2%)
- 영업이익률 중앙값: 전 섹터 1~7% 사이. 현재 기준 ">20% A"는 전체의 6%만 달성
- 부채비율 중앙값: IT 63% / 에너지 123% / 유틸리티 141% — 섹터별 편차 극심
- ROE 중앙값: 건강관리 0.8% / 커뮤니케이션 -0.3% / 금융 25.2% / 유틸리티 21.9%
- 현재 절대 기준 ">20% OM A" 달성률: IT 6%, 필수소비재 1.6%, 금융 23.8%
- 현재 절대 기준 "<50% DR A" 달성률: 에너지 20%, 유틸리티 18%, IT 42%

결론:
- 가설1 채택: 섹터별 분포 차이 극명 (에너지 DR 중앙값 123% vs IT 63%)
- 가설2 채택: 에너지/유틸리티 DR은 절대 기준으로 거의 D/F, 건강관리 ROE 중앙값 0.8%
- 가설3 채택: finance 보유 94.2%, OM/ROE/DR/CR 모두 2000+개 계산 성공
- 절대 기준만으로는 업종 특성 무시 → 섹터 상대 보정 필요

실험일: 2026-03-09
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import statistics
from collections import defaultdict
from pathlib import Path

from dartlab.core.dataConfig import DATA_RELEASES
from dartlab.engines.financeEngine.pivot import buildAnnual
from dartlab.engines.financeEngine.ratios import calcRatios
from dartlab.gather.listing import getKindList
from dartlab.engines.sectorEngine import classify


def _financeExists(stockCode: str) -> bool:
    from dartlab import config
    dataDir = Path(config.dataDir) / DATA_RELEASES["finance"]["dir"]
    return (dataDir / f"{stockCode}.parquet").exists()


def _percentile(data, p):
    n = len(data)
    if n == 0:
        return None
    k = (n - 1) * p / 100
    f = int(k)
    c = f + 1
    if c >= n:
        return data[-1]
    return data[f] + (k - f) * (data[c] - data[f])


def run():
    kindDf = getKindList()
    codes = kindDf["종목코드"].to_list()
    names = kindDf["회사명"].to_list()
    industries = kindDf["업종"].to_list() if "업종" in kindDf.columns else [None] * len(codes)
    products = kindDf["주요제품"].to_list() if "주요제품" in kindDf.columns else [None] * len(codes)

    sectorData = defaultdict(lambda: {
        "om": [], "roe": [], "dr": [], "cr": [],
        "nm": [], "roa": [], "fcfMargin": [],
        "count": 0, "hasFinance": 0,
    })

    totalProcessed = 0
    totalFinance = 0

    for i, code in enumerate(codes):
        if i % 200 == 0:
            print(f"  [{i}/{len(codes)}] processing...")

        info = classify(names[i], industries[i], products[i])
        sectorLabel = info.sector.value

        sectorData[sectorLabel]["count"] += 1

        if not _financeExists(code):
            continue

        aResult = buildAnnual(code)
        if aResult is None:
            continue

        aSeries, aYears = aResult
        ratios = calcRatios(aSeries)
        totalProcessed += 1
        totalFinance += 1
        sectorData[sectorLabel]["hasFinance"] += 1

        if ratios.operatingMargin is not None:
            sectorData[sectorLabel]["om"].append(ratios.operatingMargin)
        if ratios.roe is not None:
            sectorData[sectorLabel]["roe"].append(ratios.roe)
        if ratios.debtRatio is not None:
            sectorData[sectorLabel]["dr"].append(ratios.debtRatio)
        if ratios.currentRatio is not None:
            sectorData[sectorLabel]["cr"].append(ratios.currentRatio)
        if ratios.netMargin is not None:
            sectorData[sectorLabel]["nm"].append(ratios.netMargin)
        if ratios.roa is not None:
            sectorData[sectorLabel]["roa"].append(ratios.roa)
        if ratios.fcf is not None and ratios.revenueTTM and ratios.revenueTTM > 0:
            fcfMargin = (ratios.fcf / ratios.revenueTTM) * 100
            sectorData[sectorLabel]["fcfMargin"].append(fcfMargin)

    print(f"\n전체: {len(codes)}종목 중 finance 보유 {totalFinance} ({totalFinance/len(codes)*100:.1f}%)")
    print(f"{'='*100}")

    metrics = [
        ("om", "영업이익률(%)", 5, 10, 20),
        ("roe", "ROE(%)", 5, 10, 20),
        ("dr", "부채비율(%)", 200, 150, 100),
        ("cr", "유동비율(%)", 100, 150, 200),
        ("nm", "순이익률(%)", 3, 8, 15),
        ("roa", "ROA(%)", 2, 5, 10),
        ("fcfMargin", "FCF마진(%)", 0, 5, 15),
    ]

    for key, label, lowThresh, midThresh, highThresh in metrics:
        print(f"\n[{label}]")
        print(f"{'섹터':<15} {'N':>4} {'중앙값':>8} {'Q1':>8} {'Q3':>8} {'최소':>8} {'최대':>8}")
        print("-" * 60)

        allVals = []
        for sector in sorted(sectorData.keys()):
            vals = sorted(sectorData[sector][key])
            allVals.extend(vals)
            n = len(vals)
            if n < 3:
                print(f"{sector:<15} {n:>4}   (데이터 부족)")
                continue
            med = statistics.median(vals)
            q1 = _percentile(vals, 25)
            q3 = _percentile(vals, 75)
            print(f"{sector:<15} {n:>4} {med:>8.1f} {q1:>8.1f} {q3:>8.1f} {vals[0]:>8.1f} {vals[-1]:>8.1f}")

        if allVals:
            allVals.sort()
            n = len(allVals)
            med = statistics.median(allVals)
            q1 = _percentile(allVals, 25)
            q3 = _percentile(allVals, 75)
            print("-" * 60)
            print(f"{'전체':<15} {n:>4} {med:>8.1f} {q1:>8.1f} {q3:>8.1f} {allVals[0]:>8.1f} {allVals[-1]:>8.1f}")

    print(f"\n{'='*100}")
    print("\n[현재 insightEngine 절대 기준과의 비교]")
    print(f"{'섹터':<15} {'OM중앙':>8} {'기준>20A':>8} {'기준>10B':>8} | {'DR중앙':>8} {'기준<50A':>8} {'기준<100B':>8}")
    print("-" * 80)
    for sector in sorted(sectorData.keys()):
        omVals = sectorData[sector]["om"]
        drVals = sectorData[sector]["dr"]
        if len(omVals) < 3 or len(drVals) < 3:
            continue
        omMed = statistics.median(omVals)
        drMed = statistics.median(drVals)
        omAboveA = sum(1 for v in omVals if v > 20) / len(omVals) * 100
        omAboveB = sum(1 for v in omVals if v > 10) / len(omVals) * 100
        drBelowA = sum(1 for v in drVals if v < 50) / len(drVals) * 100
        drBelowB = sum(1 for v in drVals if v < 100) / len(drVals) * 100
        print(f"{sector:<15} {omMed:>8.1f} {omAboveA:>7.1f}% {omAboveB:>7.1f}% | {drMed:>8.1f} {drBelowA:>7.1f}% {drBelowB:>7.1f}%")

    print(f"\n\n[섹터별 종목 수]")
    for sector in sorted(sectorData.keys()):
        d = sectorData[sector]
        print(f"  {sector:<15} 전체 {d['count']:>4} / finance {d['hasFinance']:>4} ({d['hasFinance']/d['count']*100:.0f}%)")


if __name__ == "__main__":
    run()
