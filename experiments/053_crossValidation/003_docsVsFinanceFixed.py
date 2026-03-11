"""
실험 ID: 053-003
실험명: docs fsSummary vs finance XBRL 교차검증 (연도 보정 + 단위 보정)

목적:
- 002에서 발견한 1년 시차 및 백만원 단위 보정 후 실제 일치율 측정
- docs year N의 값(idx=0) = finance year N-1의 값 (전기 표시)
- docs 단위: 백만원, finance 단위: 원 → ×1,000,000 변환

가설:
1. 연도+단위 보정 후 핵심 계정 일치율 90%+ 달성
2. 일부 종목은 원 단위 사용 (소규모 기업)
3. 보정 후에도 불일치하면 데이터 품질 문제

방법:
1. docs year N → finance year N-1로 매핑
2. docs 값 × 1,000,000으로 보정 시도
3. 보정 없이 직접 비교도 병행 (원 단위 종목 대응)
4. 최적 단위(1, 1e3, 1e6) 자동 감지

결과 (실험 후 작성):
- 259종목 교집합, 159종목 성공, 14,926건 비교
- 완전일치 30.3%, 1%이내 48.6%, 5%이내 2.0% → 합산 80.9%
- 단위 분포: 백만원(×1M) 661건, 원 15건, 천원 5건
- 핵심 BS 일치율: total_assets 95.0%, current_assets 92.9%, retained_earnings 92.3%
- IS 일치율: sales 81.7%, operating_profit 84.2%, net_profit 60.0%
- 불일치 원인: EPS 단위 오보정, 자본총계/지배기업자본 혼재, 비지배지분 이름변이, 부호차이

결론:
- docs fsSummary는 "전기" 값이 idx=0 → docs year N = finance year N-1
- 단위는 대부분 백만원(×1M), 소수 종목은 원/천원 단위
- BS 핵심 계정은 90%+ 일치 → 교차검증 기반 데이터 신뢰
- IS는 80%+, net_profit이 60%로 낮은 이유는 지배/비지배 혼재
- EPS는 단위 보정 대상에서 제외 필요 (이미 원 단위)
- 교차검증 프로덕션 적용 시: 계정별 단위 예외 처리 + 자본 계정 정규화 필요

실험일: 2026-03-10
"""

from __future__ import annotations

import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))


def _detectUnit(docsVals: dict[str, float], finVals: dict[str, float]) -> float:
    """docs와 finance 값을 비교해 최적 단위 배수를 추정."""
    ratios = []
    for snakeId in docsVals:
        if snakeId in finVals:
            dv = docsVals[snakeId]
            fv = finVals[snakeId]
            if dv != 0 and fv != 0:
                ratios.append(abs(fv / dv))

    if not ratios:
        return 1.0

    median = sorted(ratios)[len(ratios) // 2]

    for scale in [1.0, 1e3, 1e6, 1e9]:
        if 0.5 < median / scale < 2.0:
            return scale
    return 1.0


def main():
    from dartlab import config
    from dartlab.core.dataConfig import DATA_RELEASES
    from dartlab.engines.dart.finance.pivot import buildAnnual
    from dartlab.engines.dart.finance.mapper import AccountMapper
    from dartlab.engines.dart.docs.finance.summary.pipeline import fsSummary

    dataDir = Path(config.dataDir)
    financeDir = dataDir / DATA_RELEASES["finance"]["dir"]
    docsDir = dataDir / DATA_RELEASES["docs"]["dir"]

    financeCodes = {p.stem for p in financeDir.glob("*.parquet")}
    docsCodes = {p.stem for p in docsDir.glob("*.parquet")}
    bothCodes = sorted(financeCodes & docsCodes)
    print(f"교집합: {len(bothCodes)}개", flush=True)

    mapper = AccountMapper.get()

    totalCompared = 0
    exactMatch = 0
    within1pct = 0
    within5pct = 0
    bigDiff = 0

    unitDistribution: dict[float, int] = defaultdict(int)
    yearShiftResults: dict[str, dict[str, int]] = {}
    perAccountStats: dict[str, dict[str, int]] = {}

    successCount = 0
    noDocsCount = 0
    noFinanceCount = 0
    diffExamples: list[tuple[str, str, str, float, float, float]] = []

    t0 = time.time()

    for i, code in enumerate(bothCodes):
        if (i + 1) % 50 == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            eta = (len(bothCodes) - i - 1) / rate
            print(f"  [{i+1}/{len(bothCodes)}] {elapsed:.0f}s, {rate:.1f}/s, ETA {eta:.0f}s", flush=True)

        annual = buildAnnual(code)
        if annual is None:
            noFinanceCount += 1
            continue

        aSeries, aYears = annual

        docResult = fsSummary(code, ifrsOnly=True, period="y")
        if docResult is None or not docResult.yearAccounts:
            noDocsCount += 1
            continue

        successCount += 1

        for docsYear, ya in docResult.yearAccounts.items():
            finYear = str(int(docsYear[:4]) - 1)
            if finYear not in aYears:
                continue

            yIdx = aYears.index(finYear)

            docsSnakeVals: dict[str, float] = {}
            for accountNm, amts in ya.accounts.items():
                if not amts or amts[0] is None:
                    continue
                snakeId = mapper.map("", accountNm)
                if snakeId:
                    docsSnakeVals[snakeId] = amts[0]

            finSnakeVals: dict[str, float] = {}
            for sjDiv in ["BS", "IS", "CF"]:
                for sid, vals in aSeries.get(sjDiv, {}).items():
                    if yIdx < len(vals) and vals[yIdx] is not None:
                        finSnakeVals[sid] = vals[yIdx]

            unit = _detectUnit(docsSnakeVals, finSnakeVals)
            unitDistribution[unit] += 1

            for snakeId, docsVal in docsSnakeVals.items():
                if snakeId not in finSnakeVals:
                    continue

                finVal = finSnakeVals[snakeId]
                scaledDocs = docsVal * unit

                totalCompared += 1

                if snakeId not in perAccountStats:
                    perAccountStats[snakeId] = {"total": 0, "match": 0}
                perAccountStats[snakeId]["total"] += 1

                if scaledDocs == finVal or (scaledDocs == 0 and finVal == 0):
                    exactMatch += 1
                    perAccountStats[snakeId]["match"] += 1
                elif scaledDocs == 0 or finVal == 0:
                    bigDiff += 1
                    if len(diffExamples) < 30:
                        diffExamples.append((code, finYear, snakeId, scaledDocs, finVal, 999.0))
                else:
                    pctDiff = abs(scaledDocs - finVal) / max(abs(scaledDocs), abs(finVal)) * 100
                    if pctDiff <= 1:
                        within1pct += 1
                        perAccountStats[snakeId]["match"] += 1
                    elif pctDiff <= 5:
                        within5pct += 1
                        perAccountStats[snakeId]["match"] += 1
                    else:
                        bigDiff += 1
                        if len(diffExamples) < 30:
                            diffExamples.append((code, finYear, snakeId, scaledDocs, finVal, pctDiff))

    elapsed = time.time() - t0

    print(f"\n{'='*70}", flush=True)
    print(f"docs vs finance 교차검증 (연도-1 + 단위보정) ({elapsed:.0f}s)")
    print(f"{'='*70}")
    print(f"종목: {len(bothCodes)}, 성공: {successCount}, docs없음: {noDocsCount}, finance없음: {noFinanceCount}")
    print()

    base = max(totalCompared, 1)
    print("[ 숫자 비교 ]")
    print(f"총 비교 건수:    {totalCompared:>8}")
    print(f"완전 일치:       {exactMatch:>8} ({exactMatch/base*100:.1f}%)")
    print(f"1% 이내:         {within1pct:>8} ({within1pct/base*100:.1f}%)")
    print(f"5% 이내:         {within5pct:>8} ({within5pct/base*100:.1f}%)")
    print(f"큰 불일치:       {bigDiff:>8} ({bigDiff/base*100:.1f}%)")
    totalMatch = exactMatch + within1pct + within5pct
    print(f"합산 일치(~5%):  {totalMatch:>8} ({totalMatch/base*100:.1f}%)")
    print()

    print("[ 단위 분포 ]")
    for unit, cnt in sorted(unitDistribution.items()):
        label = "원" if unit == 1 else f"×{unit:,.0f}"
        print(f"  {label:<15} {cnt:>6}건")
    print()

    print("[ 계정별 일치율 (주요 계정) ]")
    print(f"{'계정(snakeId)':<40} {'비교':>6} {'일치':>6} {'일치율':>8}")
    print("-" * 62)
    keyAccounts = [
        "total_assets", "total_liabilities", "total_stockholders_equity",
        "owners_of_parent_equity", "current_assets", "noncurrent_assets",
        "current_liabilities", "noncurrent_liabilities",
        "cash_and_cash_equivalents", "inventories", "tangible_assets",
        "retained_earnings", "paidin_capital",
        "sales", "operating_profit", "net_profit", "gross_profit",
        "cost_of_sales",
        "operating_cashflow", "investing_cashflow",
    ]
    for sid in keyAccounts:
        if sid in perAccountStats:
            s = perAccountStats[sid]
            rate = s["match"] / max(s["total"], 1) * 100
            print(f"{sid:<40} {s['total']:>6} {s['match']:>6} {rate:>7.1f}%")

    print()
    print("[ 전체 계정 일치율 상위 20개 ]")
    sortedAccounts = sorted(
        perAccountStats.items(),
        key=lambda x: x[1]["total"],
        reverse=True,
    )
    for sid, s in sortedAccounts[:20]:
        rate = s["match"] / max(s["total"], 1) * 100
        print(f"  {sid:<40} {s['total']:>6} {s['match']:>6} {rate:>7.1f}%")

    if diffExamples:
        print(f"\n[ 큰 불일치 예시 (처음 15개) ]")
        print(f"{'종목':>8} {'연도':>6} {'계정':>30} {'docs(보정)':>18} {'finance':>18} {'차이%':>8}")
        print("-" * 92)
        for code, yr, sid, dv, fv, pct in diffExamples[:15]:
            print(f"{code:>8} {yr:>6} {sid:>30} {dv:>18,.0f} {fv:>18,.0f} {pct:>7.1f}%")


if __name__ == "__main__":
    main()
