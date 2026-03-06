"""
실험 ID: 004-008
실험명: 비용의 성격별 분류 — 시계열 구성

목적:
- 한 종목의 여러 연도 사업보고서에서 비용의 성격 데이터를 추출
- 연도별 비용 항목 DataFrame 구성
- 당기 값만 추출하여 실제 해당 연도 비용으로 사용 (전기는 검증용)
- 분기/반기보고서 포함 시 분기별 시계열도 가능한지 확인

가설:
1. 사업보고서 기준으로 2016~2025년 시계열 구성 가능
2. 당기 금액은 해당 연도의 실제 비용
3. 전기 금액은 이전 연도 당기와 일치해야 함 (교차검증)

방법:
1. 삼성전자(005930) 전체 연도 보고서에서 비용의 성격 추출
2. 연도×계정명 DataFrame 생성
3. 당기/전기 교차검증
4. 5개 종목 추가 테스트

결과 (실험 후 작성):

결론:

실험일: 2026-03-06
"""

import re
import sys
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from dartlab.core.tableParser import parseAmount, detectUnit
from dartlab.core.reportSelector import selectReport

DATA_DIR = Path("data/docsData")


def _isDanggi(text: str) -> bool:
    t = text.replace(" ", "")
    return "당기" in t or bool(re.search(r"제\d+\(당\)기", t))


def _isJeongi(text: str) -> bool:
    t = text.replace(" ", "")
    return "전기" in t or bool(re.search(r"제\d+\(전\)기", t))


def _isPeriodLabel(text: str) -> str | None:
    if _isDanggi(text):
        return "당기"
    if _isJeongi(text):
        return "전기"
    return None


def extractNotesContent(report: pl.DataFrame) -> list[str]:
    section = report.filter(pl.col("section_title").str.contains("주석"))
    if section.height == 0:
        return []
    return section["section_content"].to_list()


def _findNextSection(lines, fromIdx, pattern):
    for i in range(fromIdx, len(lines)):
        s = lines[i].strip()
        if s.startswith("|"):
            continue
        if re.match(pattern, s):
            return i
    return len(lines)


def _findTableEnd(lines, fromIdx):
    emptyCount = 0
    lastTable = fromIdx
    for i in range(fromIdx, len(lines)):
        s = lines[i].strip()
        if s.startswith("|"):
            emptyCount = 0
            lastTable = i + 1
        elif not s:
            emptyCount += 1
            if emptyCount >= 2 and lastTable > fromIdx:
                return lastTable
        else:
            period = _isPeriodLabel(s)
            if period or re.match(r"^[\d①②③④⑤][\.\)]\s*", s):
                emptyCount = 0
                continue
            if lastTable > fromIdx + 5:
                return lastTable
    return len(lines)


def findCostByNatureSection(contents: list[str]) -> str | None:
    for content in contents:
        lines = content.split("\n")
        for i, line in enumerate(lines):
            s = line.strip()
            if s.startswith("|"):
                continue
            m = re.match(r"^(\d{1,2})\.\s+(.+)", s)
            if m and "비용" in m.group(2) and "성격" in m.group(2):
                endIdx = _findNextSection(lines, i + 1, r"^(\d{1,2})\.\s+")
                return "\n".join(lines[i:endIdx])
            m2 = re.match(r"^\((\d{1,2})\)\s+(.+)", s)
            if m2 and "비용" in m2.group(2) and "성격" in m2.group(2):
                endIdx = _findNextSection(lines, i + 1, r"^\(\d{1,2}\)\s+")
                return "\n".join(lines[i:endIdx])

    for content in contents:
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if "비용의 성격" in line or ("성격별" in line and "비용" in line):
                startIdx = max(0, i - 1)
                endIdx = _findTableEnd(lines, i + 1)
                return "\n".join(lines[startIdx:endIdx])
    return None


def parseCostByNature(sectionText: str) -> dict | None:
    result = _tryParseInlineTable(sectionText)
    if result:
        return result
    result = _tryParseSplitTable(sectionText)
    if result:
        return result
    result = _tryParseMultiColTable(sectionText)
    if result:
        return result
    return None


def _tryParseInlineTable(text):
    lines = text.split("\n")
    unit = detectUnit(text)
    tableLines = [l for l in lines if l.strip().startswith("|") and "---" not in l]
    if len(tableLines) < 3:
        return None

    headerLine = None
    dataLines = []
    for line in tableLines:
        cells = [c.strip() for c in line.split("|") if c.strip()]
        if not cells:
            continue
        if "단위" in " ".join(cells):
            continue
        if headerLine is None:
            if any(_isPeriodLabel(c) for c in cells) and len(cells) >= 2:
                headerLine = cells
                continue
        if headerLine and len(cells) >= 2:
            dataLines.append(cells)

    if not headerLine or not dataLines:
        return None

    danggiIdx = jeongiIdx = None
    for j, h in enumerate(headerLine):
        if _isDanggi(h) and danggiIdx is None:
            danggiIdx = j
        if _isJeongi(h) and jeongiIdx is None:
            jeongiIdx = j

    if danggiIdx is None and jeongiIdx is None:
        return None

    danggiData, jeongiData, order = {}, {}, []
    for cells in dataLines:
        name = cells[0]
        if _isSkipRow(name):
            continue
        name = _cleanAccountName(name)
        if not name:
            continue
        if danggiIdx is not None and danggiIdx < len(cells):
            val = parseAmount(cells[danggiIdx])
            if val is not None and unit != 1.0:
                val = val * unit
            danggiData[name] = val
        if jeongiIdx is not None and jeongiIdx < len(cells):
            val = parseAmount(cells[jeongiIdx])
            if val is not None and unit != 1.0:
                val = val * unit
            jeongiData[name] = val
        if name not in order:
            order.append(name)

    if not order:
        return None
    return {"당기": danggiData, "전기": jeongiData, "order": order, "type": "inline"}


def _tryParseSplitTable(text):
    lines = text.split("\n")
    unit = detectUnit(text)

    blocks = []
    currentPeriod = None
    currentLines = []

    for line in lines:
        s = line.strip()
        if not s.startswith("|"):
            period = _isPeriodLabel(s)
            if period:
                if currentPeriod and currentLines:
                    blocks.append((currentPeriod, currentLines))
                currentPeriod = period
                currentLines = []
            continue
        cells = [c.strip() for c in s.split("|") if c.strip()]
        if not cells:
            continue
        cellJoined = "".join(cells).replace(" ", "")
        period = _isPeriodLabel(cellJoined)
        if period and len(cells) <= 2:
            if currentPeriod and currentLines:
                blocks.append((currentPeriod, currentLines))
            currentPeriod = period
            currentLines = []
            continue
        if currentPeriod:
            currentLines.append(s)

    if currentPeriod and currentLines:
        blocks.append((currentPeriod, currentLines))

    if len(blocks) < 2:
        return None

    periodData, allAccounts = {}, []
    for period, tableLines in blocks:
        accounts = _parseSimpleRows(tableLines, unit)
        if not accounts:
            continue
        periodData[period] = accounts
        for name in accounts:
            if name not in allAccounts:
                allAccounts.append(name)

    if not periodData or not allAccounts:
        return None
    return {"당기": periodData.get("당기", {}), "전기": periodData.get("전기", {}),
            "order": allAccounts, "type": "split"}


def _parseSimpleRows(tableLines, unit):
    accounts = {}
    for line in tableLines:
        if "---" in line:
            continue
        cells = [c.strip() for c in line.split("|") if c.strip()]
        if len(cells) < 2:
            continue
        name = cells[0]
        if _isSkipRow(name):
            continue
        val = parseAmount(cells[-1])
        if val is not None and unit != 1.0:
            val = val * unit
        name = _cleanAccountName(name)
        if name:
            accounts[name] = val
    return accounts


def _tryParseMultiColTable(text):
    lines = text.split("\n")
    unit = detectUnit(text)
    blocks = []
    currentPeriod = None
    currentLines = []
    for line in lines:
        s = line.strip()
        if s.startswith("|"):
            if currentPeriod:
                currentLines.append(s)
            continue
        period = _isPeriodLabel(s)
        if period:
            if currentPeriod and currentLines:
                blocks.append((currentPeriod, currentLines))
            currentPeriod = period
            currentLines = []
    if currentPeriod and currentLines:
        blocks.append((currentPeriod, currentLines))
    if len(blocks) < 2:
        return None

    periodData, allAccounts = {}, []
    for period, tableLines in blocks:
        accounts = _parseMultiColRows(tableLines, unit)
        if not accounts:
            continue
        periodData[period] = accounts
        for name in accounts:
            if name not in allAccounts:
                allAccounts.append(name)
    if not periodData or not allAccounts:
        return None
    return {"당기": periodData.get("당기", {}), "전기": periodData.get("전기", {}),
            "order": allAccounts, "type": "multiCol"}


def _parseMultiColRows(tableLines, unit):
    accounts = {}
    headerPassed = False
    for line in tableLines:
        if "---" in line:
            headerPassed = True
            continue
        if not headerPassed:
            continue
        cells = [c.strip() for c in line.split("|") if c.strip()]
        if len(cells) < 3:
            continue
        name = cells[0]
        if _isSkipRow(name) or "단위" in name:
            continue
        val = parseAmount(cells[-1])
        if val is not None and unit != 1.0:
            val = val * unit
        name = _cleanAccountName(name)
        if name:
            accounts[name] = val
    return accounts


_SKIP_KEYWORDS = {
    "구분", "구 분", "계정과목", "공시금액",
    "단위", "합 계", "합계", "성격별 비용 합계",
    "성격별비용합계", "성격별 비용", "계", "성격별비용",
}


def _isSkipRow(name):
    cleaned = name.strip()
    if not cleaned:
        return True
    if cleaned in _SKIP_KEYWORDS:
        return True
    if cleaned.replace(" ", "") in {"합계", "계", "성격별비용합계", "성격별비용"}:
        return True
    return False


def _cleanAccountName(name):
    name = name.strip()
    name = re.sub(r"^\d+[\.\)]\s*", "", name)
    name = re.sub(r"\s+", "", name)
    return name


def buildTimeSeries(
    df: pl.DataFrame,
    period: str = "y",
) -> tuple[pl.DataFrame | None, dict]:
    """한 종목의 비용의 성격 시계열 DataFrame 생성.

    Returns:
        (DataFrame, meta)
        DataFrame: 계정명 × 연도 (당기 기준)
        meta: {"corpName": str, "years": list, "crossCheck": dict}
    """
    corpName = df["corp_name"][0] if "corp_name" in df.columns else "?"
    years = sorted(df["year"].unique().to_list(), reverse=True)

    yearData: dict[str, dict[str, float | None]] = {}
    prevData: dict[str, dict[str, float | None]] = {}
    allAccounts: list[str] = []

    for year in years:
        report = selectReport(df, year, reportKind="annual")
        if report is None:
            continue

        notes = extractNotesContent(report)
        if not notes:
            continue

        section = findCostByNatureSection(notes)
        if section is None:
            continue

        result = parseCostByNature(section)
        if result is None:
            continue

        danggi = result["당기"]
        jeongi = result["전기"]

        if danggi:
            yearData[year] = danggi
            for name in result["order"]:
                if name not in allAccounts:
                    allAccounts.append(name)

        if jeongi:
            prevData[year] = jeongi

    if not yearData:
        return None, {"corpName": corpName}

    sortedYears = sorted(yearData.keys(), reverse=True)

    crossCheck = {}
    for year in sortedYears:
        if year not in prevData:
            continue
        prevYear = str(int(year) - 1)
        if prevYear not in yearData:
            continue
        matches = 0
        mismatches = 0
        for name, prevVal in prevData[year].items():
            actualVal = yearData[prevYear].get(name)
            if prevVal is not None and actualVal is not None:
                if abs(prevVal - actualVal) < 1:
                    matches += 1
                else:
                    mismatches += 1
        crossCheck[year] = {"matches": matches, "mismatches": mismatches}

    rows = []
    for name in allAccounts:
        row: dict[str, object] = {"계정명": name}
        for year in sortedYears:
            row[year] = yearData[year].get(name)
        rows.append(row)

    if not rows:
        return None, {"corpName": corpName}

    schema = {"계정명": pl.Utf8}
    for year in sortedYears:
        schema[year] = pl.Float64

    return pl.DataFrame(rows, schema=schema), {
        "corpName": corpName,
        "years": sortedYears,
        "crossCheck": crossCheck,
    }


if __name__ == "__main__":
    TEST_CODES = ["005930", "000270", "000660", "051910", "003550"]

    for code in TEST_CODES:
        fpath = DATA_DIR / f"{code}.parquet"
        if not fpath.exists():
            print(f"\n{code}: 파일 없음")
            continue

        df = pl.read_parquet(str(fpath))
        result, meta = buildTimeSeries(df)

        print(f"\n{'=' * 80}")
        print(f"{meta['corpName']} ({code})")
        print(f"{'=' * 80}")

        if result is None:
            print("  시계열 구성 실패")
            continue

        print(f"  연도: {meta['years']}")
        print(f"  계정 수: {result.height}개")
        print(f"  기간: {len(meta['years'])}년")

        if meta["crossCheck"]:
            print(f"\n  교차검증 (당기 vs 전기):")
            for year, cc in sorted(meta["crossCheck"].items()):
                total = cc["matches"] + cc["mismatches"]
                rate = cc["matches"] / total * 100 if total > 0 else 0
                print(f"    {year}: {cc['matches']}/{total} 일치 ({rate:.0f}%)")

        print(f"\n  DataFrame:")
        with pl.Config(tbl_cols=min(len(meta["years"]) + 1, 12), tbl_width_chars=120):
            print(result)
