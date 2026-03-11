"""
실험 ID: 053-001
실험명: docs fsSummary vs finance XBRL 교차검증

목적:
- docs(HTML 파싱)의 요약재무정보 숫자와 finance(XBRL)의 숫자가 얼마나 일치하는지 측정
- accountMappings.json의 한글명→snakeId 브릿지가 실제로 작동하는지 검증
- 불일치 원인 분류 (매핑 실패 vs 숫자 차이 vs 기간 불일치)

가설:
1. 핵심 계정(매출, 자산총계, 부채총계, 자본총계)은 90%+ 일치
2. 세부 계정은 한글명 변이로 매핑률이 낮을 것
3. 숫자 불일치 시 대부분 단위 차이(원 vs 백만원) 또는 반올림

방법:
1. 로컬에 finance+docs parquet 모두 보유하는 종목 대상
2. finance buildAnnual → 연도별 snakeId:값
3. docs fsSummary → 연도별 한글계정명:값
4. AccountMapper로 한글명→snakeId 변환 후 같은 연도·계정 비교
5. 일치 기준: (a) 완전일치 (b) 5% 이내 (c) 단위 차이(×1000 또는 ÷1000)

결과 (실험 후 작성):

결론:

실험일: 2026-03-10
"""

from __future__ import annotations

import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))


def main():
    from dartlab import config
    from dartlab.core.dataConfig import DATA_RELEASES
    from dartlab.engines.dart.finance.pivot import buildAnnual
    from dartlab.engines.dart.finance.mapper import AccountMapper, ACCOUNT_NAME_SYNONYMS
    from dartlab.engines.dart.docs.finance.summary.pipeline import fsSummary

    dataDir = Path(config.dataDir)
    financeDir = dataDir / DATA_RELEASES["finance"]["dir"]
    docsDir = dataDir / DATA_RELEASES["docs"]["dir"]

    print(f"financeDir: {financeDir}", flush=True)
    print(f"docsDir: {docsDir}", flush=True)

    if not financeDir.exists() or not docsDir.exists():
        print("데이터 디렉토리 없음")
        return

    financeCodes = {p.stem for p in financeDir.glob("*.parquet")}
    docsCodes = {p.stem for p in docsDir.glob("*.parquet")}
    bothCodes = sorted(financeCodes & docsCodes)
    print(f"finance: {len(financeCodes)}, docs: {len(docsCodes)}, 교집합: {len(bothCodes)}", flush=True)

    if not bothCodes:
        print("교집합 종목 없음")
        return

    mapper = AccountMapper.get()

    totalAccounts = 0
    mappedAccounts = 0
    comparedAccounts = 0
    exactMatch = 0
    within5pct = 0
    unitDiff = 0
    unitMatchNear = 0
    bigDiff = 0
    noFinanceYear = 0

    unmappedNames: dict[str, int] = defaultdict(int)
    diffExamples: list[tuple[str, str, str, float, float, float]] = []
    matchExamples: list[tuple[str, str, str, float, float]] = []

    successCount = 0
    noDocsCount = 0
    noFinanceCount = 0

    yearStats: dict[str, dict[str, int]] = {}

    t0 = time.time()

    for i, code in enumerate(bothCodes):
        if (i + 1) % 20 == 0:
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
        if docResult is None or docResult.yearAccounts is None:
            noDocsCount += 1
            continue

        successCount += 1

        for periodKey, ya in docResult.yearAccounts.items():
            year = periodKey[:4]
            if year not in aYears:
                noFinanceYear += 1
                continue

            yIdx = aYears.index(year)

            if year not in yearStats:
                yearStats[year] = {"total": 0, "mapped": 0, "compared": 0, "exact": 0, "near": 0}

            for accountNm, amts in ya.accounts.items():
                if not amts or amts[0] is None:
                    continue

                docsVal = amts[0]
                totalAccounts += 1
                yearStats[year]["total"] += 1

                snakeId = mapper.map("", accountNm)

                if snakeId is None:
                    unmappedNames[accountNm] = unmappedNames.get(accountNm, 0) + 1
                    continue

                mappedAccounts += 1
                yearStats[year]["mapped"] += 1

                finVal = None
                for sjDiv in ["BS", "IS", "CF"]:
                    vals = aSeries.get(sjDiv, {}).get(snakeId)
                    if vals and yIdx < len(vals) and vals[yIdx] is not None:
                        finVal = vals[yIdx]
                        break

                if finVal is None:
                    continue

                comparedAccounts += 1
                yearStats[year]["compared"] += 1

                if docsVal == finVal:
                    exactMatch += 1
                    yearStats[year]["exact"] += 1
                    if len(matchExamples) < 10:
                        matchExamples.append((code, year, accountNm, docsVal, finVal))
                elif docsVal == 0 or finVal == 0:
                    bigDiff += 1
                    if len(diffExamples) < 50:
                        diffExamples.append((code, year, accountNm, docsVal, finVal, 999.0))
                else:
                    pctDiff = abs(docsVal - finVal) / max(abs(docsVal), abs(finVal)) * 100
                    if pctDiff <= 5:
                        within5pct += 1
                        yearStats[year]["near"] += 1
                    else:
                        ratio = finVal / docsVal
                        absRatio = abs(ratio)
                        isUnit = False
                        for scale in [1e3, 1e6, 1e9]:
                            if 0.9 < absRatio / scale < 1.1:
                                isUnit = True
                                break
                            if 0.9 < scale / absRatio < 1.1:
                                isUnit = True
                                break
                        if isUnit:
                            unitDiff += 1
                            scaledDocs = docsVal * round(absRatio)
                            scaledPct = abs(scaledDocs - finVal) / max(abs(scaledDocs), abs(finVal)) * 100
                            if scaledPct <= 5:
                                unitMatchNear += 1
                                yearStats[year]["near"] += 1
                        else:
                            bigDiff += 1
                            if len(diffExamples) < 50:
                                diffExamples.append((code, year, accountNm, docsVal, finVal, pctDiff))

    elapsed = time.time() - t0

    print(f"\n{'='*70}", flush=True)
    print(f"docs fsSummary vs finance XBRL 교차검증 ({elapsed:.0f}s)")
    print(f"{'='*70}")
    print(f"종목: {len(bothCodes)}, 성공: {successCount}, docs없음: {noDocsCount}, finance없음: {noFinanceCount}")
    print()

    print("[ 매핑 통계 ]")
    print(f"총 계정(docs 쪽):     {totalAccounts}")
    print(f"snakeId 매핑 성공:    {mappedAccounts} ({mappedAccounts/max(totalAccounts,1)*100:.1f}%)")
    print(f"매핑 실패:            {totalAccounts - mappedAccounts} ({(totalAccounts-mappedAccounts)/max(totalAccounts,1)*100:.1f}%)")
    print(f"finance에 값 존재:    {comparedAccounts} ({comparedAccounts/max(mappedAccounts,1)*100:.1f}% of mapped)")
    print(f"연도 불일치 건너뜀:   {noFinanceYear}")
    print()

    print("[ 숫자 비교 ]")
    base = max(comparedAccounts, 1)
    print(f"완전 일치:          {exactMatch:>6} ({exactMatch/base*100:.1f}%)")
    print(f"5% 이내:            {within5pct:>6} ({within5pct/base*100:.1f}%)")
    print(f"단위 차이 총:       {unitDiff:>6} ({unitDiff/base*100:.1f}%)")
    print(f"  단위 보정 후 일치: {unitMatchNear:>6} ({unitMatchNear/base*100:.1f}%)")
    print(f"큰 불일치:          {bigDiff:>6} ({bigDiff/base*100:.1f}%)")
    totalMatch = exactMatch + within5pct + unitMatchNear
    print(f"합산 일치(보정포함): {totalMatch:>6} ({totalMatch/base*100:.1f}%)")
    print()

    if yearStats:
        print("[ 연도별 통계 ]")
        print(f"{'연도':>6} {'총계정':>8} {'매핑':>8} {'비교':>8} {'일치':>8} {'일치율':>8}")
        print("-" * 50)
        for year in sorted(yearStats.keys()):
            s = yearStats[year]
            rate = (s["exact"] + s["near"]) / max(s["compared"], 1) * 100
            print(f"{year:>6} {s['total']:>8} {s['mapped']:>8} {s['compared']:>8} {s['exact']+s['near']:>8} {rate:>7.1f}%")
        print()

    if matchExamples:
        print("[ 완전 일치 예시 ]")
        for code, year, nm, dv, fv in matchExamples:
            print(f"  {code} {year} {nm}: docs={dv:,.0f} finance={fv:,.0f}")
        print()

    if unmappedNames:
        print(f"[ 미매핑 한글계정명 (상위 30개) ]")
        for name, cnt in sorted(unmappedNames.items(), key=lambda x: -x[1])[:30]:
            print(f"  {cnt:>4}건: {name}")
        print()

    if diffExamples:
        print(f"[ 큰 불일치 예시 (처음 20개) ]")
        print(f"{'종목':>8} {'연도':>6} {'계정명':<30} {'docs':>18} {'finance':>18} {'차이%':>8}")
        print("-" * 92)
        for code, year, nm, dv, fv, pct in diffExamples[:20]:
            print(f"{code:>8} {year:>6} {nm:<30} {dv:>18,.0f} {fv:>18,.0f} {pct:>7.1f}%")


if __name__ == "__main__":
    main()
