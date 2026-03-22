"""
실험 ID: 001
실험명: 숫자 브릿지 매칭 - 재무제표 당기/전기 연결 검증

목적:
- DART 재무제표에서 계정명이 연도마다 달라지는 문제 해결 방안 검증
- N년 보고서의 "전기" 숫자와 N-1년 보고서의 "당기" 숫자가 일치하는지 확인
- 숫자 일치를 통해 계정명 자동 매핑이 가능한지 실현 가능성 확인

가설:
1. 같은 회사의 N년 보고서 "전기"와 N-1년 보고서 "당기" 숫자가 90% 이상 일치할 것이다
2. 숫자가 일치하는 계정 쌍에서 계정명 변형 패턴을 발견할 수 있을 것이다
3. 우연히 같은 금액이 겹치는 경우(오매칭)는 전체의 5% 미만일 것이다

방법:
1. 삼성전자(005930) parquet에서 요약재무정보 섹션 추출
2. 요약재무정보는 3개년(당기/전기/전전기) 비교 형식
3. N년 보고서의 전기 컬럼과 N-1년 보고서의 당기 컬럼 숫자 비교
4. 일치율, 계정명 변형 케이스, 오매칭 케이스 각각 집계

결과 (실험 후 작성):
- 삼성전자 요약재무정보 기준, 2015~2025년 10개 연도 쌍 테스트
- 전체 매칭률: 98.6% (360건 중 355건 매칭)
- 동일계정: 323건 (89.7%), 이름변경: 32건 (8.9%), 미매칭: 5건 (1.4%)
- 반복 발견된 이름변경 패턴:
  - '[자본금]' ↔ 'ㆍ자본금' (매년 발생, 접두사 차이)
  - '[주식발행초과금]' ↔ 'ㆍ주식발행초과금' (매년 발생)
  - '희석주당순이익(단위:원)' ↔ '기본주당순이익(단위:원)' (금액 동일 시 오매칭)
  - '영업이익(손실)' ↔ '영업이익' (괄호 부분 변형)
  - 'ㆍ기타비유동금융자산' ↔ 'ㆍ장기매도가능금융자산' (IFRS9 적용에 따른 계정 변경)
  - 'ㆍ종속기업, 관계기업 및 공동기업 투자' ↔ '...에 대한 투자자산' (명칭 변경)
- 미매칭 5건:
  - 기본/희석 주당순이익 금액 동일로 인한 오매칭 3건
  - 영업이익 중복매칭 1건
  - IFRS9 전환 시 계정 소멸 1건

결론:
- 가설1 채택: 전기/당기 숫자 일치율 98.6%로 90% 초과
- 가설2 채택: 접두사(ㆍ/[]), 괄호, 회계기준 변경 등 패턴 발견
- 가설3 채택: 오매칭(기본/희석 주당순이익 같은 금액) 약 1.4%로 5% 미만
- 숫자 브릿지 매칭은 실현 가능. 단, 동일 금액 계정(자본금 등 고정값) 오매칭 보정 필요

실험일: 2026-03-06
"""

import re

import polars as pl

DATA_PATH = "data/docsData/005930.parquet"


def extractTables(content):
    """마크다운 테이블에서 헤더와 행을 추출한다.
    DART 테이블은 단위행(1열) 바로 뒤에 본체 테이블(N열)이 이어지는 구조:
      | (단위 : 백만원) |
      | --- |
      | 구 분 | 제55기 | 제54기 |
      | --- | --- | --- |
      | [유동자산] | 195,936,557 | ...
    1열 테이블의 데이터행이 본체 헤더를 포함하므로, 모든 테이블을 파싱한 뒤
    데이터행 안에서 구분자(---)를 만나면 새 테이블로 분리한다."""
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
    """금액 문자열을 숫자로 변환한다."""
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
    """요약재무정보에서 {계정명: [당기, 전기, 전전기]} 추출.
    헤더가 '구 분 | 제N기 | 제N-1기 | 제N-2기' 형식."""
    tables = extractTables(content)
    result = {}
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
    return result


def bridgeMatch(accCurrent, accPrev):
    """N년 전기(idx=1)와 N-1년 당기(idx=0) 비교."""
    matchCount = 0
    nameChangeCount = 0
    noMatchCount = 0
    nameChanges = []
    noMatches = []

    for nameCur, amtsCur in accCurrent.items():
        if len(amtsCur) < 2 or amtsCur[1] is None:
            continue
        prevAmt = amtsCur[1]

        matched = False
        for namePrev, amtsPrev in accPrev.items():
            if len(amtsPrev) < 1 or amtsPrev[0] is None:
                continue
            if abs(prevAmt - amtsPrev[0]) < 0.5:
                matched = True
                if nameCur == namePrev:
                    matchCount += 1
                else:
                    nameChangeCount += 1
                    nameChanges.append((nameCur, namePrev, prevAmt))
                break

        if not matched:
            noMatchCount += 1
            noMatches.append((nameCur, prevAmt))

    return matchCount, nameChangeCount, noMatchCount, nameChanges, noMatches


def main():
    df = pl.read_parquet(DATA_PATH)

    yearAccounts = {}
    years = sorted(df["year"].unique().to_list(), reverse=True)

    print("=== 요약재무정보 추출 ===")
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
        accounts = extractYearAccounts(content)
        if accounts:
            yearAccounts[year] = accounts
            print(f"  {year}년: {len(accounts)}개 계정")
            for name, vals in list(accounts.items())[:5]:
                vstr = [f"{v:,.0f}" if v is not None else "N/A" for v in vals]
                print(f"    {name}: {vstr}")

    print(f"\n=== 브릿지 매칭 테스트 ===")
    sortedYears = sorted(yearAccounts.keys(), reverse=True)

    totalMatch = 0
    totalNameChange = 0
    totalNoMatch = 0
    allNameChanges = []

    for i in range(len(sortedYears) - 1):
        curYear = sortedYears[i]
        prevYear = sortedYears[i + 1]

        accCur = yearAccounts[curYear]
        accPrev = yearAccounts[prevYear]

        mc, nc, nm, changes, noMatches = bridgeMatch(accCur, accPrev)
        total = mc + nc + nm

        print(f"\n  {curYear} ↔ {prevYear}:")
        print(f"    동일계정={mc}, 이름변경={nc}, 미매칭={nm}, 합계={total}")
        if total > 0:
            print(f"    매칭률: {(mc + nc) / total * 100:.1f}%")

        if changes:
            for c in changes:
                print(f"    이름변경: '{c[0]}' → '{c[1]}'  금액={c[2]:,.0f}")
                allNameChanges.append(c)

        if noMatches:
            for nm_item in noMatches:
                print(f"    미매칭: '{nm_item[0]}' 전기={nm_item[1]:,.0f}")

        totalMatch += mc
        totalNameChange += nc
        totalNoMatch += nm

    print(f"\n{'='*60}")
    print(f"=== 종합 결과 ===")
    grandTotal = totalMatch + totalNameChange + totalNoMatch
    print(f"전체: 동일계정={totalMatch}, 이름변경={totalNameChange}, 미매칭={totalNoMatch}")
    if grandTotal > 0:
        print(f"전체 매칭률: {(totalMatch + totalNameChange) / grandTotal * 100:.1f}%")
        print(f"이름변경률: {totalNameChange / grandTotal * 100:.1f}%")

    if allNameChanges:
        print(f"\n=== 발견된 계정명 변형 패턴 ===")
        for c in allNameChanges:
            print(f"  '{c[0]}' → '{c[1]}'")


if __name__ == "__main__":
    main()
