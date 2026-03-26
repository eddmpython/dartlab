"""
실험 ID: 017
실험명: 섹터 상대등급 vs 절대등급 비교 검증

목적:
- 016에서 확인한 섹터별 재무비율 분포를 활용
- 20종목에 대해 섹터 내 백분위(percentile) 기반 등급과 현재 절대 등급 비교
- 섹터 보정이 등급 분별력에 미치는 영향 측정

가설:
1. 에너지/유틸리티 부채비율 → 절대등급 D/F인데 섹터 상대등급은 B/C가 될 것
2. 건강관리/커뮤니케이션 ROE → 절대등급 D인데 업종 중앙값 근처라 상대등급 C가 될 것
3. 전체적으로 상대등급의 분포가 더 균등할 것 (A~F 고르게 분산)

방법:
1. 전체 종목에서 섹터별 분포 미리 수집 (016 로직 재활용)
2. 20종목에 대해 섹터 내 percentile rank 계산
3. percentile → 등급 변환 (상위 20% A, 20-40% B, 40-60% C, 60-80% D, 하위 20% F)
4. 절대등급 vs 상대등급 차이 비교 테이블

결과 (실험 후 작성):
- 등급 분포 — 절대 A:18 B:13 C:14 D:9 F:13 / 상대 A:11 B:16 C:16 D:12 F:12
- 영업이익률: 상대등급이 11/15 상승, 0 하락 (절대 기준이 너무 가혹)
- ROE: 상대등급 2 상승, 8 하락 (대기업은 절대로도 우수, 섹터 내에선 평범)
- 부채비율: 상대등급 2 상승, 9 하락 (절대 기준이 대기업에 관대)
- 유동비율: 상대등급 0 상승, 11 하락 (대기업 유동비율이 업종 상위는 아님)
- 금융업: ROE/OM 대부분 N (계산 불가), 부채비율만 나옴

결론:
- 가설1 부분 채택: 에너지/유틸리티 DR은 절대 F→상대 D/F (기대보다 개선 미미, 분포 자체가 나쁨)
- 가설2 채택: 카카오 ROE -3.3% 절대 F→상대 C (커뮤니케이션 중앙값 -0.3%)
- 가설3 채택: 상대등급 분포가 더 균등 (A비중 22.5→13.8%, C+D비중 28.8→35%)
- 핵심 인사이트: 순수 상대등급보다 **절대 기준 + 섹터 보정** 하이브리드가 최선
  - 영업이익률/수익성 → 섹터 보정 가치 높음
  - 부채비율/유동성 → 금융업 제외하면 절대 기준 유지가 합리적
  - 보정 방식: 섹터 중앙값 기준 가점/감점 (±1등급)

실험일: 2026-03-09
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from collections import defaultdict
from pathlib import Path

from dartlab.core.dataConfig import DATA_RELEASES
from dartlab.engines.financeEngine.pivot import buildAnnual
from dartlab.engines.financeEngine.ratios import calcRatios
from dartlab.gather.listing import getKindList
from dartlab.engines.sectorEngine import classify

TEST_STOCKS = [
    ("005930", "삼성전자"), ("000660", "SK하이닉스"), ("005380", "현대자동차"),
    ("005490", "POSCO홀딩스"), ("035420", "NAVER"), ("035720", "카카오"),
    ("105560", "KB금융"), ("055550", "신한지주"), ("006800", "미래에셋증권"),
    ("032830", "삼성생명"), ("051910", "LG화학"), ("373220", "LG에너지솔루션"),
    ("066570", "LG전자"), ("003550", "LG"), ("000270", "기아"),
    ("068270", "셀트리온"), ("028260", "삼성물산"), ("096770", "SK이노베이션"),
    ("034730", "SK"), ("015760", "한국전력"),
]


def _financeExists(stockCode: str) -> bool:
    from dartlab import config
    dataDir = Path(config.dataDir) / DATA_RELEASES["finance"]["dir"]
    return (dataDir / f"{stockCode}.parquet").exists()


def _percentileRank(value: float, distribution: list[float]) -> float:
    if not distribution:
        return 50.0
    belowCount = sum(1 for v in distribution if v < value)
    equalCount = sum(1 for v in distribution if v == value)
    return ((belowCount + 0.5 * equalCount) / len(distribution)) * 100


def _percentileToGrade(pct: float, higherIsBetter: bool = True) -> str:
    if not higherIsBetter:
        pct = 100 - pct
    if pct >= 80:
        return "A"
    if pct >= 60:
        return "B"
    if pct >= 40:
        return "C"
    if pct >= 20:
        return "D"
    return "F"


def _absoluteGradeOM(om: float | None) -> str:
    if om is None:
        return "N"
    if om > 20:
        return "A"
    if om > 10:
        return "B"
    if om > 5:
        return "C"
    if om > 0:
        return "D"
    return "F"


def _absoluteGradeROE(roe: float | None) -> str:
    if roe is None:
        return "N"
    if roe > 20:
        return "A"
    if roe > 10:
        return "B"
    if roe > 5:
        return "C"
    if roe > 0:
        return "D"
    return "F"


def _absoluteGradeDR(dr: float | None) -> str:
    if dr is None:
        return "N"
    if dr < 50:
        return "A"
    if dr < 100:
        return "B"
    if dr < 150:
        return "C"
    if dr < 200:
        return "D"
    return "F"


def _absoluteGradeCR(cr: float | None) -> str:
    if cr is None:
        return "N"
    if cr > 200:
        return "A"
    if cr > 150:
        return "B"
    if cr > 100:
        return "C"
    if cr > 80:
        return "D"
    return "F"


def run():
    kindDf = getKindList()
    codes = kindDf["종목코드"].to_list()
    names = kindDf["회사명"].to_list()
    industries = kindDf["업종"].to_list() if "업종" in kindDf.columns else [None] * len(codes)
    products = kindDf["주요제품"].to_list() if "주요제품" in kindDf.columns else [None] * len(codes)

    sectorDist = defaultdict(lambda: {"om": [], "roe": [], "dr": [], "cr": []})

    print("1단계: 전체 종목 섹터별 분포 수집...")
    for i, code in enumerate(codes):
        if i % 500 == 0:
            print(f"  [{i}/{len(codes)}]")
        if not _financeExists(code):
            continue
        info = classify(names[i], industries[i], products[i])
        aResult = buildAnnual(code)
        if aResult is None:
            continue
        aSeries, _ = aResult
        ratios = calcRatios(aSeries)
        sector = info.sector.value
        if ratios.operatingMargin is not None:
            sectorDist[sector]["om"].append(ratios.operatingMargin)
        if ratios.roe is not None:
            sectorDist[sector]["roe"].append(ratios.roe)
        if ratios.debtRatio is not None:
            sectorDist[sector]["dr"].append(ratios.debtRatio)
        if ratios.currentRatio is not None:
            sectorDist[sector]["cr"].append(ratios.currentRatio)

    print(f"\n분포 수집 완료: {len(sectorDist)}개 섹터\n")

    print("2단계: 20종목 절대 vs 상대 등급 비교\n")

    header = (
        f"{'종목':<12} {'섹터':<10} "
        f"{'OM':>6} {'절대':>3} {'상대':>3} {'차':>3} | "
        f"{'ROE':>6} {'절대':>3} {'상대':>3} {'차':>3} | "
        f"{'DR':>6} {'절대':>3} {'상대':>3} {'차':>3} | "
        f"{'CR':>6} {'절대':>3} {'상대':>3} {'차':>3}"
    )
    print(header)
    print("-" * len(header))

    gradeOrder = {"A": 5, "B": 4, "C": 3, "D": 2, "F": 1, "N": 0}

    totalDiffs = {"om": 0, "roe": 0, "dr": 0, "cr": 0}
    improveCounts = {"om": 0, "roe": 0, "dr": 0, "cr": 0}
    worsenCounts = {"om": 0, "roe": 0, "dr": 0, "cr": 0}
    validCounts = {"om": 0, "roe": 0, "dr": 0, "cr": 0}

    absGradeDist = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0, "N": 0}
    relGradeDist = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0, "N": 0}

    for code, name in TEST_STOCKS:
        row = kindDf.filter(kindDf["종목코드"] == code)
        kindIndustry = row["업종"][0] if row.height > 0 else None
        mainProducts = row["주요제품"][0] if row.height > 0 else None
        info = classify(name, kindIndustry, mainProducts)
        sector = info.sector.value

        aResult = buildAnnual(code)
        if aResult is None:
            print(f"{name:<12} 데이터 없음")
            continue

        aSeries, _ = aResult
        ratios = calcRatios(aSeries)

        dist = sectorDist[sector]

        metrics = []
        for key, val, absFunc, higherBetter in [
            ("om", ratios.operatingMargin, _absoluteGradeOM, True),
            ("roe", ratios.roe, _absoluteGradeROE, True),
            ("dr", ratios.debtRatio, _absoluteGradeDR, False),
            ("cr", ratios.currentRatio, _absoluteGradeCR, True),
        ]:
            absG = absFunc(val)
            if val is not None and dist[key]:
                pct = _percentileRank(val, dist[key])
                relG = _percentileToGrade(pct, higherBetter)
            else:
                relG = "N"

            diff = gradeOrder.get(relG, 0) - gradeOrder.get(absG, 0)
            diffStr = f"+{diff}" if diff > 0 else str(diff) if diff != 0 else " 0"
            valStr = f"{val:.1f}" if val is not None else "N/A"
            metrics.append((valStr, absG, relG, diffStr))

            absGradeDist[absG] += 1
            relGradeDist[relG] += 1
            if absG != "N" and relG != "N":
                totalDiffs[key] += abs(diff)
                validCounts[key] += 1
                if diff > 0:
                    improveCounts[key] += 1
                elif diff < 0:
                    worsenCounts[key] += 1

        om, roe, dr, cr = metrics
        print(
            f"{name:<12} {sector:<10} "
            f"{om[0]:>6} {om[1]:>3} {om[2]:>3} {om[3]:>3} | "
            f"{roe[0]:>6} {roe[1]:>3} {roe[2]:>3} {roe[3]:>3} | "
            f"{dr[0]:>6} {dr[1]:>3} {dr[2]:>3} {dr[3]:>3} | "
            f"{cr[0]:>6} {cr[1]:>3} {cr[2]:>3} {cr[3]:>3}"
        )

    print(f"\n{'='*80}")
    print("\n[등급 분포 비교]")
    print(f"{'':>10} {'A':>5} {'B':>5} {'C':>5} {'D':>5} {'F':>5} {'N':>5}")
    print(f"{'절대':>10} {absGradeDist['A']:>5} {absGradeDist['B']:>5} {absGradeDist['C']:>5} {absGradeDist['D']:>5} {absGradeDist['F']:>5} {absGradeDist['N']:>5}")
    print(f"{'상대':>10} {relGradeDist['A']:>5} {relGradeDist['B']:>5} {relGradeDist['C']:>5} {relGradeDist['D']:>5} {relGradeDist['F']:>5} {relGradeDist['N']:>5}")

    print("\n[지표별 등급 변동 요약]")
    for key, label in [("om", "영업이익률"), ("roe", "ROE"), ("dr", "부채비율"), ("cr", "유동비율")]:
        n = validCounts[key]
        if n == 0:
            continue
        avg = totalDiffs[key] / n
        up = improveCounts[key]
        down = worsenCounts[key]
        same = n - up - down
        print(f"  {label}: 평균 변동 {avg:.1f}단계 | 상승 {up} / 동일 {same} / 하락 {down} (총 {n})")


if __name__ == "__main__":
    run()
