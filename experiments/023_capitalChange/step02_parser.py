"""
실험 ID: 023
실험명: 자본금 변동사항 + 주식의 총수 파서

목적:
- "3. 자본금 변동사항" 테이블에서 보통주/우선주 발행주식총수·액면금액·자본금 시계열 추출
- "4. 주식의 총수 등" 테이블에서 발행할주식총수, 현재까지발행, 감소, 유통주식수 추출
- 자기주식 변동(취득/처분/소각) 추출

가설:
1. "자본금 변동사항" 테이블은 보통주/우선주 행이 반복되며 연도 컬럼이 있는 시계열
2. "주식의 총수" 테이블은 Ⅰ~Ⅳ 행으로 표준화된 고정 구조
3. 220/267 이상의 기업에서 파싱 가능

방법:
1. 자본금 변동 테이블 파서
2. 주식 총수 테이블 파서
3. 자기주식 변동 테이블 파서
4. 267개 배치 테스트

결과 (실험 후 작성):
-

결론:
-

실험일: 2026-03-08
"""

import os
import re
import sys
from collections import Counter

sys.path.insert(0, r"C:\Users\MSI\OneDrive\Desktop\sideProject\dartlab\src")

DATA_DIR = r"C:\Users\MSI\OneDrive\Desktop\sideProject\nicegui\eddmpython\data\dartData\docsData"

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import selectReport

# ──────────────────────────────────────────────
# 유틸리티
# ──────────────────────────────────────────────

def parseAmount(text: str) -> int | None:
    """숫자 문자열을 정수로 변환. 콤마, 공백 등 제거."""
    if not text or not isinstance(text, str):
        return None
    text = text.strip().replace(",", "").replace(" ", "")
    if text in ("-", "−", "–", ""):
        return None
    # 음수 처리
    neg = False
    if text.startswith("(") and text.endswith(")"):
        neg = True
        text = text[1:-1]
    elif text.startswith("-") or text.startswith("△") or text.startswith("▲"):
        neg = True
        text = text.lstrip("-△▲")

    text = re.sub(r"[^\d.]", "", text)
    if not text:
        return None
    try:
        val = int(float(text))
        return -val if neg else val
    except ValueError:
        return None


def extractTableBlocks(content: str) -> list[list[str]]:
    """content에서 |(pipe) 구분 테이블 블록들 추출."""
    lines = content.split("\n")
    blocks = []
    current = []
    for line in lines:
        stripped = line.strip()
        if "|" in stripped:
            current.append(stripped)
        else:
            if current:
                blocks.append(current)
                current = []
    if current:
        blocks.append(current)
    return blocks


def splitCells(line: str) -> list[str]:
    """파이프 라인을 셀 리스트로 분할."""
    cells = [c.strip() for c in line.split("|")]
    # 앞뒤 빈셀 제거
    while cells and cells[0] == "":
        cells.pop(0)
    while cells and cells[-1] == "":
        cells.pop()
    return cells


def isSeparatorRow(line: str) -> bool:
    """--- 구분선 행인지 확인."""
    cells = splitCells(line)
    return all(re.match(r"^-+$", c.strip()) for c in cells if c.strip())


# ──────────────────────────────────────────────
# 1. 자본금 변동사항 파서
# ──────────────────────────────────────────────

def parseCapitalChangeTable(block: list[str]) -> dict | None:
    """자본금 변동사항 테이블 파싱.

    구조 (멀티 기간):
    | 종류 | 구분 | 57기(2024년말) | 56기(2023년말) | ...
    | 보통주 | 발행주식총수 | 209,416,191 | 211,531,506 | ...
    |        | 액면금액   | 5,000 | 5,000 | ...
    |        | 자본금     | 1,157,982,395,000 | ...

    구조 (단일 기간 — 삼성전자):
    | 종류 | 구분 | 제56기말 |
    | 보통주 | 발행주식총수 | 5,969,782,550 |
    | 액면금액 | 100 |  |    ← 종류 셀 누락, 라벨이 첫 셀

    Returns:
        {
            "periods": ["56기(2024년말)", ...],
            "common": {"발행주식총수": [v1, v2, ...], "액면금액": [...], "자본금": [...]},
            "preferred": {"발행주식총수": [...], ...},
        }
    """
    # 데이터 행만 (--- 구분선 제외)
    dataRows = [line for line in block if not isSeparatorRow(line)]
    if len(dataRows) < 4:
        return None

    # 헤더 행: "종류 | 구분 | 제XX기말 | ..."
    headerRow = None
    for row in dataRows:
        cells = splitCells(row)
        if any("기" in c and ("말" in c or "년" in c) for c in cells):
            headerRow = row
            break

    if headerRow is None:
        return None

    headerCells = splitCells(headerRow)
    # period 컬럼: "제56기말" 또는 "56기(2024년말)" 형태
    periods = []
    periodStartIdx = None
    for i, cell in enumerate(headerCells):
        if re.search(r"\d+기|\d{4}년", cell):
            if periodStartIdx is None:
                periodStartIdx = i
            periods.append(cell)

    if not periods or periodStartIdx is None:
        return None

    # 데이터 파싱
    currentType = None  # "보통주" | "우선주"
    result = {"periods": periods, "common": {}, "preferred": {}}

    for row in dataRows:
        if row == headerRow:
            continue
        cells = splitCells(row)
        if len(cells) < 2:
            continue

        # 단위 행 건너뛰기
        if any("단위" in c for c in cells):
            continue
        # 합계 행은 건너뛰기
        if cells[0].strip() == "합계":
            continue

        # 종류 감지
        for cell in cells:
            c = cell.strip()
            if re.search(r"보통주", c):
                currentType = "common"
                break
            elif re.search(r"우선주", c):
                currentType = "preferred"
                break

        if currentType is None:
            continue

        # 라벨 감지 — 모든 셀에서 탐색 (종류 셀이 누락될 수 있으므로)
        label = None
        for cell in cells:
            c = cell.strip()
            if c and c not in ("보통주", "우선주", "-", ""):
                if re.search(r"발행주식|액면|자본금", c):
                    label = c
                    break

        if label is None:
            continue

        # 값 추출 — 숫자 셀을 뒤에서 추출 (컬럼 오프셋 변동 대응)
        # 숫자가 될 수 있는 셀만 뽑기
        numericCells = []
        for cell in cells:
            c = cell.strip()
            # 숫자인지 확인 (콤마 허용, - 허용)
            if c and (re.match(r"^[\d,]+$", c) or c in ("-", "−", "–", "")):
                numericCells.append(c)

        values = []
        for c in numericCells[:len(periods)]:
            values.append(parseAmount(c))

        # 라벨 정규화
        if "발행주식" in label:
            label = "발행주식총수"
        elif "액면" in label:
            label = "액면금액"
        elif "자본금" in label:
            label = "자본금"

        target = result[currentType]
        if label not in target:
            target[label] = values

    # 결과가 있는지 확인
    if not result["common"] and not result["preferred"]:
        return None

    return result


# ──────────────────────────────────────────────
# 2. 주식의 총수 파서
# ──────────────────────────────────────────────

def parseShareTotalTable(block: list[str]) -> dict | None:
    """주식의 총수 등 테이블 파싱.

    구조:
    | 구 분 |  | 주식의 종류 |  |  | 비고 |
    |       |  | 보통주 | 우선주 | 합계 |      |     ← sub-header (인덱스 0부터)
    | Ⅰ. 발행할 주식의 총수 |  | 20,000,000,000 | 5,000,000,000 | 25,000,000,000 | - |

    핵심: sub-header의 보통주/우선주/합계 셀 위치와 데이터 행의 숫자 셀 위치가
    다를 수 있음 (빈 셀 오프셋). 따라서 숫자 셀 기반으로 추출.

    Returns:
        {
            "referenceDate": "2024년 12월 31일",
            "authorizedShares": {"common": int, "preferred": int, "total": int},
            "issuedShares": {"common": int, "preferred": int, "total": int},
            "reducedShares": {"common": int, "preferred": int, "total": int},
            "outstandingShares": {"common": int, "preferred": int, "total": int},
        }
    """
    dataRows = [line for line in block if not isSeparatorRow(line)]
    if len(dataRows) < 5:
        return None

    # 기준일 추출
    refDate = None
    for row in dataRows:
        m = re.search(r"(\d{4}년\s*\d{1,2}월\s*\d{1,2}일)", row)
        if m:
            refDate = m.group(1)
            break

    # 보통주/우선주 헤더 존재 여부로 컬럼 수 판단
    hasPreferred = any("우선주" in row for row in dataRows)

    # 데이터 행 파싱 — Ⅰ~Ⅵ 행에서 숫자 셀 추출
    result = {"referenceDate": refDate}
    labelMap = {
        "발행할": "authorizedShares",
        "현재까지 발행한": "issuedShares",
        "현재까지발행한": "issuedShares",
        "감소한": "reducedShares",
        "발행주식의 총수": "outstandingShares",
        "발행주식의총수": "outstandingShares",
        "유통주식": "floatingShares",
    }

    for row in dataRows:
        cells = splitCells(row)
        if len(cells) < 3:
            continue

        # 라벨 검출
        rowText = " ".join(cells)
        matchedKey = None
        for pattern, key in labelMap.items():
            if pattern in rowText:
                matchedKey = key
                break

        if matchedKey is None:
            continue

        # 숫자 셀 추출 (콤마 구분 숫자 + - 허용)
        numericValues = []
        for cell in cells:
            c = cell.strip()
            if re.match(r"^[\d,]+$", c):
                numericValues.append(parseAmount(c))
            elif c in ("-", "−", "–"):
                numericValues.append(None)

        if not numericValues:
            continue

        # 보통주/우선주/합계 매핑
        values = {}
        if hasPreferred:
            if len(numericValues) >= 3:
                values = {"common": numericValues[0], "preferred": numericValues[1], "total": numericValues[2]}
            elif len(numericValues) == 2:
                values = {"common": numericValues[0], "total": numericValues[1]}
            elif len(numericValues) == 1:
                values = {"total": numericValues[0]}
        else:
            if len(numericValues) >= 2:
                values = {"common": numericValues[0], "total": numericValues[1]}
            elif len(numericValues) == 1:
                values = {"common": numericValues[0], "total": numericValues[0]}

        if values:
            result[matchedKey] = values

    if len(result) <= 1:
        return None

    return result


# ──────────────────────────────────────────────
# 3. 자기주식 변동 파서
# ──────────────────────────────────────────────

def parseTreasuryStockTable(block: list[str]) -> dict | None:
    """자기주식 변동 테이블 파싱.

    | 취득방법 | 주식의 종류 | 기초수량 | 취득(+) | 처분(-) | 소각(-) | 기말수량 |

    Returns:
        {
            "referenceDate": "2024년 12월 31일",
            "rows": [
                {"method": "장내직접 취득", "stockType": "보통주",
                 "beginQty": int, "acquired": int, "disposed": int, "cancelled": int, "endQty": int},
                ...
            ],
            "totalBegin": int, "totalEnd": int,
        }
    """
    dataRows = [line for line in block if not isSeparatorRow(line)]
    if len(dataRows) < 5:
        return None

    # 기초수량 + 기말수량 키워드 확인
    hasKeywords = False
    for row in dataRows:
        if "기초수량" in row and "기말수량" in row:
            hasKeywords = True
            break
    if not hasKeywords:
        return None

    # 기준일
    refDate = None
    for row in dataRows:
        m = re.search(r"(\d{4}년\s*\d{1,2}월\s*\d{1,2}일)", row)
        if m:
            refDate = m.group(1)
            break

    # 헤더에서 컬럼 위치
    headerRow = None
    for row in dataRows:
        if "기초수량" in row:
            headerRow = row
            break
    if headerRow is None:
        return None

    headerCells = splitCells(headerRow)
    beginIdx = acquiredIdx = disposedIdx = cancelledIdx = endIdx = typeIdx = None
    for i, cell in enumerate(headerCells):
        if "기초" in cell:
            beginIdx = i
        elif "취득" in cell and "방법" not in cell:
            acquiredIdx = i
        elif "처분" in cell:
            disposedIdx = i
        elif "소각" in cell:
            cancelledIdx = i
        elif "기말" in cell:
            endIdx = i
        elif "종류" in cell:
            typeIdx = i

    if beginIdx is None or endIdx is None:
        return None

    # 데이터 행 파싱 — 보통주/우선주 행만
    rows = []
    currentMethod = ""
    totalBegin = 0
    totalEnd = 0

    foundHeader = False
    for row in dataRows:
        if row == headerRow:
            foundHeader = True
            continue
        if not foundHeader:
            continue

        cells = splitCells(row)
        if len(cells) < max(beginIdx, endIdx) + 1:
            continue

        # 보통주/우선주 확인
        stockType = None
        for cell in cells:
            if "보통주" in cell:
                stockType = "보통주"
                break
            elif "우선주" in cell:
                stockType = "우선주"
                break

        if stockType is None:
            # 소계/합계 행 or 메소드 업데이트
            for cell in cells[:3]:
                if cell.strip() and cell.strip() not in ("-", ""):
                    if any(kw in cell for kw in ["취득", "처분", "이익", "직접", "간접", "신탁", "기타"]):
                        currentMethod = cell.strip()
            continue

        begin = parseAmount(cells[beginIdx]) if beginIdx < len(cells) else None
        acquired = parseAmount(cells[acquiredIdx]) if acquiredIdx and acquiredIdx < len(cells) else None
        disposed = parseAmount(cells[disposedIdx]) if disposedIdx and disposedIdx < len(cells) else None
        cancelled = parseAmount(cells[cancelledIdx]) if cancelledIdx and cancelledIdx < len(cells) else None
        end = parseAmount(cells[endIdx]) if endIdx < len(cells) else None

        rows.append({
            "method": currentMethod,
            "stockType": stockType,
            "beginQty": begin,
            "acquired": acquired,
            "disposed": disposed,
            "cancelled": cancelled,
            "endQty": end,
        })

        if begin:
            totalBegin += begin
        if end:
            totalEnd += end

    if not rows:
        return None

    return {
        "referenceDate": refDate,
        "rows": rows,
        "totalBegin": totalBegin,
        "totalEnd": totalEnd,
    }


# ──────────────────────────────────────────────
# 통합 파이프라인
# ──────────────────────────────────────────────

def findSection(report, patterns: list[str]) -> str | None:
    """report DataFrame에서 패턴 매칭 섹션 content 반환."""
    for row in report.iter_rows(named=True):
        title = row.get("section_title", "") or ""
        if any(re.search(p, title) for p in patterns):
            content = row.get("section_content", "") or ""
            if len(content) > 50:
                return content
    return None


def parseCapitalChange(stockCode: str) -> dict | None:
    """자본금 변동 + 주식 총수 통합 파서."""
    try:
        df = loadData(stockCode)
    except Exception:
        return None

    corpName = extractCorpName(df)
    years = sorted(df["year"].unique().to_list(), reverse=True)

    capitalChanges = []  # 자본금 변동사항 (시계열)
    shareTotals = []     # 주식의 총수 (연도별 스냅샷)
    treasuryStocks = []  # 자기주식 변동

    for year in years:
        report = selectReport(df, year, reportKind="annual")
        if report is None:
            continue

        # 3. 자본금 변동사항
        capitalContent = findSection(report, [r"자본금\s*변동"])
        if capitalContent:
            blocks = extractTableBlocks(capitalContent)
            for block in blocks:
                parsed = parseCapitalChangeTable(block)
                if parsed:
                    parsed["year"] = year
                    capitalChanges.append(parsed)
                    break  # 첫 번째 유효 테이블만

        # 4. 주식의 총수 등
        shareContent = findSection(report, [r"주식의\s*총수"])
        if shareContent:
            blocks = extractTableBlocks(shareContent)
            for block in blocks:
                # 주식 총수 테이블
                if "발행할" in " ".join(block) or "Ⅰ" in " ".join(block):
                    parsed = parseShareTotalTable(block)
                    if parsed:
                        parsed["year"] = year
                        shareTotals.append(parsed)
                        break

            for block in blocks:
                # 자기주식 변동 테이블
                if "기초수량" in " ".join(block) and "기말수량" in " ".join(block):
                    parsed = parseTreasuryStockTable(block)
                    if parsed:
                        parsed["year"] = year
                        treasuryStocks.append(parsed)
                        break

    if not capitalChanges and not shareTotals:
        return None

    return {
        "corpName": corpName,
        "nYears": len(years),
        "capitalChanges": capitalChanges,
        "shareTotals": shareTotals,
        "treasuryStocks": treasuryStocks,
    }


# ──────────────────────────────────────────────
# 배치 테스트
# ──────────────────────────────────────────────

def batchTest():
    """267개 기업 배치 테스트."""
    codes = sorted([f.replace(".parquet", "") for f in os.listdir(DATA_DIR) if f.endswith(".parquet")])

    ok = 0
    noData = 0
    errors = 0
    capCount = 0
    shareCount = 0
    treasuryCount = 0

    for code in codes:
        try:
            result = parseCapitalChange(code)
            if result is None:
                noData += 1
            else:
                ok += 1
                if result["capitalChanges"]:
                    capCount += 1
                if result["shareTotals"]:
                    shareCount += 1
                if result["treasuryStocks"]:
                    treasuryCount += 1
        except Exception as e:
            errors += 1
            print(f"  ERROR {code}: {e}")

    print(f"\n=== 배치 테스트 결과 ({len(codes)}개) ===")
    print(f"성공: {ok}, 데이터없음: {noData}, 에러: {errors}")
    print(f"자본금변동: {capCount}, 주식총수: {shareCount}, 자기주식: {treasuryCount}")


def testSingle(stockCode: str):
    """단일 기업 테스트."""
    result = parseCapitalChange(stockCode)
    if result is None:
        print(f"  {stockCode}: 데이터 없음")
        return

    corpName = result["corpName"]
    print(f"\n=== {corpName} ({stockCode}) ===")

    # 자본금 변동
    for cap in result["capitalChanges"]:
        print(f"\n  [{cap['year']}] 자본금 변동사항")
        print(f"    기간: {cap['periods']}")
        for stype in ("common", "preferred"):
            if stype in cap and cap[stype]:
                label = "보통주" if stype == "common" else "우선주"
                print(f"    {label}:")
                for k, v in cap[stype].items():
                    print(f"      {k}: {v}")

    # 주식 총수
    for st in result["shareTotals"]:
        print(f"\n  [{st['year']}] 주식의 총수 (기준일: {st.get('referenceDate')})")
        for key in ("authorizedShares", "issuedShares", "reducedShares", "outstandingShares"):
            if key in st:
                print(f"    {key}: {st[key]}")

    # 자기주식
    for ts in result["treasuryStocks"]:
        print(f"\n  [{ts['year']}] 자기주식 (기초: {ts['totalBegin']:,}, 기말: {ts['totalEnd']:,})")
        for row in ts["rows"][:5]:
            print(f"    {row['method']} {row['stockType']}: {row['beginQty']} → {row['endQty']}")


if __name__ == "__main__":
    testSingle("005930")  # 삼성전자
    testSingle("005380")  # 현대차
    testSingle("035720")  # 카카오
    print()
    batchTest()
