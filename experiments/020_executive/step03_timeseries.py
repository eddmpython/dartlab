"""
실험 ID: 020-03
실험명: 임원 현황 시계열 DataFrame 생성

목적:
- step02 파서 결과를 연도별 시계열 DataFrame으로 변환
- 등기임원 집계, 직원현황, 미등기임원 보수를 연도 인덱스로 정렬

가설:
1. executiveDf: year | totalRegistered | insideDirectors | outsideDirectors | otherNonexec |
                fullTimeCount | partTimeCount | maleCount | femaleCount
2. employeeDf:  year | totalEmployees | avgTenure | totalSalary | avgSalary
3. unregPayDf:  year | headcount | totalSalary | avgSalary

방법:
1. 연도별 findExecutiveSection + parseExecutiveSection 호출
2. 당기 데이터 추출
3. DataFrame 생성

결과 (실험 후 작성):

결론:

실험일: 2026-03-07
"""
import os
import re
import sys

import polars as pl

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import selectReport

DATA_DIR = r"C:\Users\MSI\OneDrive\Desktop\sideProject\nicegui\eddmpython\data\dartData\docsData"

sys.path.insert(0, os.path.dirname(__file__))
from step02_parser import (
    _cellsFromLine,
    _flatText,
    _isSeparator,
    _parseFloat,
    aggregateExecutives,
    classifyBlock,
    extractTableBlocks,
    findExecutiveSection,
    parseExecutiveBlock,
    parseUnregisteredPayBlock,
)

# ──────────────────────────────────────────────
# 직원현황 합계행 파서 (개선)
# ──────────────────────────────────────────────

def _parseTenure(text: str) -> float | None:
    """평균근속연수 파싱. '13.4' 또는 '5년 6개월' 등."""
    if not text or text.strip() in ("-", "", "—"):
        return None
    text = text.strip()

    # 숫자만 있으면 바로 반환
    try:
        return float(text.replace(",", ""))
    except ValueError:
        pass

    # "N년 M개월" 패턴
    m = re.match(r"(\d+)\s*년\s*(\d+)\s*개월", text)
    if m:
        return int(m.group(1)) + int(m.group(2)) / 12

    m = re.match(r"(\d+)\s*년", text)
    if m:
        return float(m.group(1))

    m = re.match(r"(\d+)\s*개월", text)
    if m:
        return int(m.group(1)) / 12

    return None


def parseEmployeeTotal(block: list[str]) -> dict | None:
    """직원현황 합계행에서 정형 데이터 추출.

    헤더에서 컬럼 위치를 동적으로 찾아 매핑.
    DART 표준 헤더: 사업부문|성별|직원수(정규/계약/기타/합계)|평균근속|급여총액|1인평균|비고

    Returns:
        {
            "totalEmployees": int,
            "avgTenure": float,        # 년
            "totalSalary": float,      # 백만원
            "avgSalary": float,        # 백만원
        }
    """
    rows = []
    for line in block:
        cells = _cellsFromLine(line)
        if _isSeparator(cells):
            continue
        rows.append(cells)

    if len(rows) < 4:
        return None

    # 1) 헤더에서 컬럼 인덱스 찾기
    #    "근속" = 평균근속연수
    #    "연간급여|급여총" = 급여총액
    #    "1인|평균급여" = 1인평균
    #    총직원수 = 근속 바로 앞 컬럼
    colTenure = None
    colTotalSal = None
    colAvgSal = None

    for row in rows[:6]:  # 헤더는 상단 6행 안에
        for i, cell in enumerate(row):
            c = cell.replace(" ", "")
            if re.search(r"근속", c) and colTenure is None:
                colTenure = i
            if re.search(r"연간급여|급여총", c) and colTotalSal is None:
                colTotalSal = i
            if re.search(r"1인|평균급여", c) and colAvgSal is None:
                colAvgSal = i

    # 총직원수 = 근속 바로 앞 컬럼
    colTotal = (colTenure - 1) if colTenure is not None and colTenure > 0 else None

    # 2) 합계 행 찾기
    totalRow = None
    for row in rows:
        first3 = " ".join(row[:3])
        if re.search(r"합\s*계", first3) and "성별" not in first3:
            totalRow = row

    if totalRow is None:
        for row in rows:
            first3 = " ".join(row[:3])
            if re.search(r"합\s*계", first3):
                totalRow = row

    if totalRow is None:
        return None

    # 3) 컬럼 인덱스로 값 추출
    def safeGet(row, idx):
        if idx is not None and idx < len(row):
            return row[idx]
        return None

    totalEmp = _parseFloat(safeGet(totalRow, colTotal))
    tenure = _parseTenure(safeGet(totalRow, colTenure)) if colTenure else None
    totalSal = _parseFloat(safeGet(totalRow, colTotalSal))
    avgSal = _parseFloat(safeGet(totalRow, colAvgSal))

    if totalEmp is not None and totalEmp > 0:
        return {
            "totalEmployees": int(totalEmp),
            "avgTenure": tenure,
            "totalSalary": totalSal,
            "avgSalary": avgSal,
        }

    # Fallback: 숫자 기반 추정 (헤더 탐색 실패 시)
    nums = []
    for i, cell in enumerate(totalRow):
        n = _parseFloat(cell)
        if n is not None:
            nums.append((i, n))

    if not nums:
        return None

    # 합계행 패턴: ... | 큰숫자(직원수) | 소숫점(근속) | 큰숫자(급여) | 작은숫자(평균) |
    result = {"totalEmployees": None, "avgTenure": None, "totalSalary": None, "avgSalary": None}

    for i, (idx, n) in enumerate(nums):
        if result["totalEmployees"] is None and n >= 1:
            result["totalEmployees"] = int(n)
        elif result["totalEmployees"] is not None and result["avgTenure"] is None:
            tn = _parseTenure(totalRow[idx])
            if tn is not None and tn < 50:
                result["avgTenure"] = tn
            else:
                result["totalSalary"] = n
                result["avgTenure"] = None
        elif result["totalSalary"] is None:
            result["totalSalary"] = n
        elif result["avgSalary"] is None:
            result["avgSalary"] = n

    if result["totalEmployees"]:
        return result
    return None


# ──────────────────────────────────────────────
# 시계열 빌더
# ──────────────────────────────────────────────

def buildExecutiveTimeSeries(stockCode: str) -> dict | None:
    """임원 현황 시계열 생성.

    Returns:
        {
            "corpName": str,
            "nYears": int,
            "executiveDf": pl.DataFrame | None,
            "employeeDf": pl.DataFrame | None,
            "unregPayDf": pl.DataFrame | None,
        }
    """
    df = loadData(stockCode)
    corpName = extractCorpName(df)
    years = sorted(df["year"].unique().to_list(), reverse=True)

    execRows = []
    empRows = []
    payRows = []

    for year in years:
        content = findExecutiveSection(df, year)
        if content is None:
            continue

        blocks = extractTableBlocks(content)

        # 등기임원
        for block in blocks:
            kind = classifyBlock(block)
            if kind == "executive":
                executives = parseExecutiveBlock(block)
                if executives:
                    stats = aggregateExecutives(executives)
                    stats["year"] = year
                    execRows.append(stats)
                break

        # 직원현황
        for block in blocks:
            kind = classifyBlock(block)
            if kind == "employee":
                emp = parseEmployeeTotal(block)
                if emp:
                    emp["year"] = year
                    empRows.append(emp)
                break

        # 미등기임원 보수
        for block in blocks:
            kind = classifyBlock(block)
            if kind == "unregisteredPay":
                pay = parseUnregisteredPayBlock(block)
                if pay:
                    pay["year"] = year
                    payRows.append(pay)
                break

    if not execRows and not empRows and not payRows:
        return None

    # 중복 연도 제거 (최신 우선)
    def dedup(rows):
        seen = set()
        result = []
        for r in rows:
            if r["year"] not in seen:
                seen.add(r["year"])
                result.append(r)
        return result

    execRows = dedup(execRows)
    empRows = dedup(empRows)
    payRows = dedup(payRows)

    executiveDf = _buildExecutiveDf(execRows) if execRows else None
    employeeDf = _buildEmployeeDf(empRows) if empRows else None
    unregPayDf = _buildUnregPayDf(payRows) if payRows else None

    nYears = max(len(execRows), len(empRows), len(payRows))

    return {
        "corpName": corpName,
        "nYears": nYears,
        "executiveDf": executiveDf,
        "employeeDf": employeeDf,
        "unregPayDf": unregPayDf,
    }


def _buildExecutiveDf(rows: list[dict]) -> pl.DataFrame:
    data = []
    for r in sorted(rows, key=lambda x: x["year"], reverse=True):
        data.append({
            "year": r["year"],
            "totalRegistered": r["totalRegistered"],
            "insideDirectors": r["insideDirectors"],
            "outsideDirectors": r["outsideDirectors"],
            "otherNonexec": r["otherNonexec"],
            "fullTimeCount": r["fullTimeCount"],
            "partTimeCount": r["partTimeCount"],
            "maleCount": r["maleCount"],
            "femaleCount": r["femaleCount"],
        })
    return pl.DataFrame(data)


def _buildEmployeeDf(rows: list[dict]) -> pl.DataFrame:
    data = []
    for r in sorted(rows, key=lambda x: x["year"], reverse=True):
        data.append({
            "year": r["year"],
            "totalEmployees": r["totalEmployees"],
            "avgTenure": r["avgTenure"],
            "totalSalary": r["totalSalary"],
            "avgSalary": r["avgSalary"],
        })
    schema = {
        "year": pl.Utf8,
        "totalEmployees": pl.Int64,
        "avgTenure": pl.Float64,
        "totalSalary": pl.Float64,
        "avgSalary": pl.Float64,
    }
    return pl.DataFrame(data, schema=schema)


def _buildUnregPayDf(rows: list[dict]) -> pl.DataFrame:
    data = []
    for r in sorted(rows, key=lambda x: x["year"], reverse=True):
        data.append({
            "year": r["year"],
            "headcount": r["headcount"],
            "totalSalary": r["totalSalary"],
            "avgSalary": r["avgSalary"],
        })
    schema = {
        "year": pl.Utf8,
        "headcount": pl.Int64,
        "totalSalary": pl.Float64,
        "avgSalary": pl.Float64,
    }
    return pl.DataFrame(data, schema=schema)


if __name__ == "__main__":
    targets = [
        ("005930", "삼성전자"),
        ("005380", "현대자동차"),
        ("000660", "SK하이닉스"),
        ("035720", "카카오"),
    ]

    for code, name in targets:
        print(f"\n{'='*60}")
        print(f"{name} ({code})")
        print(f"{'='*60}")

        result = buildExecutiveTimeSeries(code)
        if result is None:
            print("  결과 없음")
            continue

        print(f"  {result['corpName']} — {result['nYears']}년")

        if result["executiveDf"] is not None:
            print(f"\n  [등기임원 시계열]")
            print(result["executiveDf"])

        if result["employeeDf"] is not None:
            print(f"\n  [직원현황 시계열]")
            print(result["employeeDf"])

        if result["unregPayDf"] is not None:
            print(f"\n  [미등기임원 보수 시계열]")
            print(result["unregPayDf"])

    # 대량 테스트
    print(f"\n\n{'='*60}")
    print("267개 대량 테스트")
    print(f"{'='*60}")

    codes = sorted([f.replace(".parquet", "") for f in os.listdir(DATA_DIR) if f.endswith(".parquet")])

    hasExec = 0
    hasEmp = 0
    hasPay = 0
    noData = 0
    errors = []

    for code in codes:
        try:
            result = buildExecutiveTimeSeries(code)
            if result is None:
                noData += 1
                continue
            if result["executiveDf"] is not None:
                hasExec += 1
            if result["employeeDf"] is not None:
                hasEmp += 1
            if result["unregPayDf"] is not None:
                hasPay += 1
        except Exception as e:
            errors.append((code, str(e)[:100]))

    total = len(codes)
    print(f"  등기임원 시계열: {hasExec}/{total}")
    print(f"  직원현황 시계열: {hasEmp}/{total}")
    print(f"  미등기보수 시계열: {hasPay}/{total}")
    print(f"  NoData: {noData}")
    print(f"  에러: {len(errors)}")

    if errors:
        for code, msg in errors[:10]:
            print(f"    {code}: {msg}")
