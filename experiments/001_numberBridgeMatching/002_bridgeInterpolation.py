"""
실험 ID: 001-002
실험명: 숫자 브릿지 보간 - 3개년 중복 + 순서 보정으로 미매칭 제거

목적:
- 001 실험에서 미매칭 1.4%를 보간으로 0%에 근접시킬 수 있는지 확인
- 3개년 중복 구간(전전기 브릿지)과 계정 순서(position)를 활용한 보정
- 삼성전자 외 다수 기업(중소, 금융)에서도 브릿지 매칭이 작동하는지 검증

가설:
1. 3개년 중복 보간 + 순서 보정으로 미매칭률을 0.5% 이하로 줄일 수 있다
2. 동화약품(중소), KR모터스(중소), SK하이닉스(대기업), 유진증권(금융) 모두
   브릿지 매칭률 95% 이상을 달성할 것이다

방법:
1. 5개 기업의 요약재무정보에서 전 연도 계정 추출
2. 1차: 당기-전기 숫자 브릿지 매칭 (001과 동일)
3. 2차: 미매칭에 대해 전전기 브릿지 시도 (N년 전전기 = N-2년 당기)
4. 3차: 여전히 미매칭인 건에 대해 계정 순서(position) 기반 매칭
5. 기업별 매칭률 비교

결과 (실험 후 작성):
- 5개 기업, 1336건 테스트
  | 기업 | 연도 | 합계 | 동일 | 변경 | 미매칭 | 매칭률 |
  | 삼성전자 | 11 | 360 | 352 | 6 | 2 | 99.4% |
  | 동화약품 | 8 | 260 | 215 | 32 | 13 | 95.0% |
  | KR모터스 | 6 | 184 | 112 | 62 | 10 | 94.6% |
  | SK하이닉스 | 6 | 188 | 124 | 49 | 15 | 92.0% |
  | 유진증권 | 10 | 344 | 315 | 16 | 13 | 96.2% |
  | 전체 | - | 1336 | 1118 | 165 | 53 | 96.0% |
- 3차 순서 보정이 대부분의 보간을 담당 (특히 연도 갭이 클 때)
- 연속 연도(2025↔2024 등)는 거의 100% 매칭
- 연도 갭이 클수록(2022↔2017, 2017↔1999 등) 미매칭 급증
- 3차 순서 보정은 연도 갭이 크면 오매칭 다발 (계정 자체가 완전히 달라짐)

결론:
- 가설1 기각: 미매칭 3.96%로 0.5% 미달. 연도 갭이 큰 경우가 원인
- 가설2 부분 채택: 삼성전자 99.4%, 유진증권 96.2% 달성. SK하이닉스 92.0% 미달
- 연속 연도 간 매칭은 97~100%로 매우 우수
- 연도 갭(2년 이상)에서 3차 순서 보정이 오매칭을 유발 → 순서 보정은 연속 연도에만 적용해야
- K-GAAP→K-IFRS 전환(2011년), 계정체계 대폭 변경 시 브릿지 불가 → 별도 처리 필요

실험일: 2026-03-06
"""

import os
import re
from pathlib import Path

import polars as pl

DATA_DIR = Path("data/docsData")

TARGETS = {
    "005930": "삼성전자",
    "000020": "동화약품",
    "000040": "KR모터스",
    "000660": "SK하이닉스",
    "001200": "유진증권",
}


def extractTables(content):
    tables = []
    lines = content.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("|") and i + 1 < len(lines) and "---" in lines[i + 1]:
            cells = [c.strip() for c in line.split("|")]
            cells = [c for c in cells if c != ""]
            headers = cells
            i += 2

            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rowLine = lines[i].strip()
                if "---" in rowLine:
                    if rows:
                        newHeader = rows.pop()
                        if rows:
                            tables.append({"headers": headers, "rows": rows})
                        headers = newHeader
                        rows = []
                    i += 1
                    continue
                rowCells = [c.strip() for c in rowLine.split("|")]
                rowCells = [c for c in rowCells if c != ""]
                if rowCells:
                    rows.append(rowCells)
                i += 1

            if headers and rows and len(headers) >= 2:
                tables.append({"headers": headers, "rows": rows})
        else:
            i += 1
    return tables


def parseAmount(text):
    if not text or text.strip() in ("", "-", "　"):
        return None
    cleaned = text.strip()
    isNegative = "△" in cleaned or "(" in cleaned
    cleaned = cleaned.replace("△", "").replace(",", "").replace(" ", "")
    cleaned = cleaned.replace("(", "").replace(")", "")
    cleaned = re.sub(r"[^\d.]", "", cleaned)
    if not cleaned:
        return None
    try:
        val = float(cleaned)
        return -val if isNegative else val
    except ValueError:
        return None


def extractYearAccounts(content):
    tables = extractTables(content)
    result = {}
    order = []
    for table in tables:
        headers = table["headers"]
        if len(headers) < 3:
            continue
        if not any("기" in h for h in headers[1:]):
            continue
        for row in table["rows"]:
            if len(row) < 2:
                continue
            name = row[0].strip()
            if not name or "※" in name or "월" in name:
                continue
            amounts = []
            for cell in row[1:]:
                amounts.append(parseAmount(cell))
            result[name] = amounts
            order.append(name)
    return result, order


def bridgeMatchWithInterpolation(accCurrent, orderCurrent, accPrev, orderPrev, accPrevPrev=None):
    matched = {}
    nameChanges = []
    usedPrev = set()

    for nameCur, amtsCur in accCurrent.items():
        if len(amtsCur) < 2 or amtsCur[1] is None:
            continue
        prevAmt = amtsCur[1]

        for namePrev, amtsPrev in accPrev.items():
            if namePrev in usedPrev:
                continue
            if len(amtsPrev) < 1 or amtsPrev[0] is None:
                continue
            if abs(prevAmt - amtsPrev[0]) < 0.5:
                matched[nameCur] = namePrev
                usedPrev.add(namePrev)
                if nameCur != namePrev:
                    nameChanges.append((nameCur, namePrev, prevAmt, "1차:당기-전기"))
                break

    unmatchedCur = [n for n in accCurrent if n not in matched and len(accCurrent[n]) >= 2 and accCurrent[n][1] is not None]

    if accPrevPrev and unmatchedCur:
        for nameCur in list(unmatchedCur):
            amtsCur = accCurrent[nameCur]
            if len(amtsCur) < 3 or amtsCur[2] is None:
                continue
            prevPrevAmt = amtsCur[2]

            for namePP, amtsPP in accPrevPrev.items():
                if len(amtsPP) < 1 or amtsPP[0] is None:
                    continue
                if abs(prevPrevAmt - amtsPP[0]) < 0.5:
                    for namePrev, amtsPrev in accPrev.items():
                        if namePrev in usedPrev:
                            continue
                        posPP = list(accPrevPrev.keys()).index(namePP) if namePP in accPrevPrev else -1
                        posPrev = list(accPrev.keys()).index(namePrev) if namePrev in accPrev else -1
                        if posPP >= 0 and posPrev >= 0 and abs(posPP - posPrev) <= 2:
                            matched[nameCur] = namePrev
                            usedPrev.add(namePrev)
                            unmatchedCur.remove(nameCur)
                            nameChanges.append((nameCur, namePrev, prevPrevAmt, "2차:전전기+순서"))
                            break
                    break

    if unmatchedCur:
        unusedPrev = [n for n in accPrev if n not in usedPrev]
        for nameCur in list(unmatchedCur):
            posCur = orderCurrent.index(nameCur) if nameCur in orderCurrent else -1
            if posCur < 0:
                continue
            bestMatch = None
            bestDist = 999
            for namePrev in unusedPrev:
                posPrev = orderPrev.index(namePrev) if namePrev in orderPrev else -1
                if posPrev < 0:
                    continue
                dist = abs(posCur - posPrev)
                if dist < bestDist:
                    bestDist = dist
                    bestMatch = namePrev
            if bestMatch and bestDist <= 2:
                matched[nameCur] = bestMatch
                usedPrev.add(bestMatch)
                unusedPrev.remove(bestMatch)
                unmatchedCur.remove(nameCur)
                nameChanges.append((nameCur, bestMatch, None, "3차:순서"))

    sameCount = sum(1 for k, v in matched.items() if k == v)
    changeCount = sum(1 for k, v in matched.items() if k != v)
    noMatchCount = len(unmatchedCur)

    return sameCount, changeCount, noMatchCount, nameChanges, unmatchedCur


def processCompany(code, name):
    filepath = DATA_DIR / f"{code}.parquet"
    if not filepath.exists():
        print(f"  {code} ({name}): 파일 없음")
        return None

    df = pl.read_parquet(str(filepath))
    yearData = {}
    yearOrder = {}
    years = sorted(df["year"].unique().to_list(), reverse=True)

    for year in years:
        annual = df.filter(
            (pl.col("year") == year)
            & (pl.col("report_type").str.contains("사업보고서"))
            & (~pl.col("report_type").str.contains("기재정정|첨부"))
        )
        if annual.height == 0:
            continue
        summary = annual.filter(pl.col("section_title").str.contains("요약재무정보"))
        if summary.height == 0:
            continue
        content = summary["section_content"][0]
        accounts, order = extractYearAccounts(content)
        if accounts:
            yearData[year] = accounts
            yearOrder[year] = order

    if len(yearData) < 2:
        print(f"  {code} ({name}): 연도 부족 ({len(yearData)}개)")
        return None

    sortedYears = sorted(yearData.keys(), reverse=True)
    totalSame = 0
    totalChange = 0
    totalNoMatch = 0
    allChanges = []
    allUnmatched = []

    print(f"\n{'='*60}")
    print(f"{code} ({name}) - {len(sortedYears)}개 연도")

    for i in range(len(sortedYears) - 1):
        curYear = sortedYears[i]
        prevYear = sortedYears[i + 1]
        prevPrevYear = sortedYears[i + 2] if i + 2 < len(sortedYears) else None

        accCur = yearData[curYear]
        orderCur = yearOrder[curYear]
        accPrev = yearData[prevYear]
        orderPrev = yearOrder[prevYear]
        accPP = yearData.get(prevPrevYear) if prevPrevYear else None

        sc, cc, nm, changes, unmatched = bridgeMatchWithInterpolation(
            accCur, orderCur, accPrev, orderPrev, accPP
        )
        total = sc + cc + nm

        print(f"  {curYear} ↔ {prevYear}: 동일={sc}, 변경={cc}, 미매칭={nm} ({total}건)")
        for c in changes:
            if c[0] != c[1]:
                amt = f" 금액={c[2]:,.0f}" if c[2] else ""
                print(f"    [{c[3]}] '{c[0]}' → '{c[1]}'{amt}")
        for u in unmatched:
            print(f"    미매칭: '{u}'")

        totalSame += sc
        totalChange += cc
        totalNoMatch += nm
        allChanges.extend(changes)
        allUnmatched.extend(unmatched)

    grandTotal = totalSame + totalChange + totalNoMatch
    matchRate = (totalSame + totalChange) / grandTotal * 100 if grandTotal > 0 else 0
    print(f"  --- 합계: 동일={totalSame}, 변경={totalChange}, 미매칭={totalNoMatch}, 매칭률={matchRate:.1f}%")

    return {
        "code": code,
        "name": name,
        "years": len(sortedYears),
        "total": grandTotal,
        "same": totalSame,
        "change": totalChange,
        "noMatch": totalNoMatch,
        "rate": matchRate,
    }


def main():
    print("=== 숫자 브릿지 보간 실험 (다수 기업) ===\n")

    results = []
    for code, name in TARGETS.items():
        r = processCompany(code, name)
        if r:
            results.append(r)

    print(f"\n{'='*60}")
    print("=== 종합 결과 ===")
    print(f"{'기업':>12} | {'연도':>4} | {'합계':>5} | {'동일':>5} | {'변경':>4} | {'미매칭':>4} | {'매칭률':>6}")
    print("-" * 60)
    for r in results:
        print(f"{r['name']:>12} | {r['years']:>4} | {r['total']:>5} | {r['same']:>5} | {r['change']:>4} | {r['noMatch']:>4} | {r['rate']:>5.1f}%")

    totalAll = sum(r["total"] for r in results)
    sameAll = sum(r["same"] for r in results)
    changeAll = sum(r["change"] for r in results)
    noMatchAll = sum(r["noMatch"] for r in results)
    rateAll = (sameAll + changeAll) / totalAll * 100 if totalAll > 0 else 0
    print("-" * 60)
    print(f"{'전체':>12} |      | {totalAll:>5} | {sameAll:>5} | {changeAll:>4} | {noMatchAll:>4} | {rateAll:>5.1f}%")


if __name__ == "__main__":
    main()
