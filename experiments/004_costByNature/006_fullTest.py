"""
실험 ID: 004-006
실험명: 비용의 성격별 분류 — 전체 종목 파싱 성공률 테스트

목적:
- 005에서 만든 파서를 267개 전체 종목에 적용
- 테이블 유형별 분포, 실패 유형별 분류, 전체 성공률 측정

가설:
1. K-IFRS 비금융 종목에서 90% 이상 성공
2. 금융업(증권, 은행, 보험 등)은 비용의 성격 공시 비율이 낮을 것

방법:
1. 전체 parquet 로드 → 최신 사업보고서 선택 → 파싱
2. 성공/실패/스킵 분류
3. 실패 종목의 원인 분류

결과 (실험 후 작성):

결론:

실험일: 2026-03-06
"""

import re
import sys
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from dartlab.core.reportSelector import selectReport
from dartlab.core.tableParser import detectUnit, parseAmount

DATA_DIR = Path("data/docsData")


def extractNotesContent(report: pl.DataFrame) -> list[str]:
    section = report.filter(pl.col("section_title").str.contains("주석"))
    if section.height == 0:
        return []
    return section["section_content"].to_list()


def findCostByNatureSection(contents: list[str]) -> str | None:
    for content in contents:
        lines = content.split("\n")

        for i, line in enumerate(lines):
            s = line.strip()
            if s.startswith("|"):
                continue

            m = re.match(r"^(\d{1,2})\.\s+(.+)", s)
            if m and "비용의 성격" in m.group(2):
                endIdx = _findNextSection(lines, i + 1, r"^(\d{1,2})\.\s+")
                return "\n".join(lines[i:endIdx])

            m2 = re.match(r"^\((\d{1,2})\)\s+(.+)", s)
            if m2 and "비용의 성격" in m2.group(2):
                endIdx = _findNextSection(lines, i + 1, r"^\(\d{1,2}\)\s+")
                return "\n".join(lines[i:endIdx])

    for content in contents:
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if "비용의 성격" in line:
                startIdx = max(0, i - 1)
                endIdx = _findTableEnd(lines, i + 1)
                return "\n".join(lines[startIdx:endIdx])

    return None


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
            if "당기" in s or "전기" in s or re.match(r"^\d\)", s):
                emptyCount = 0
                continue
            if lastTable > fromIdx + 5:
                return lastTable
    return len(lines)


def parseCostByNature(sectionText):
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


def _tryParseSplitTable(text):
    lines = text.split("\n")
    unit = detectUnit(text)

    blocks = []
    currentPeriod = None
    currentLines = []

    for line in lines:
        s = line.strip()
        if not s.startswith("|"):
            if re.match(r"^\d\)\s*(당기|전기)", s):
                if currentPeriod and currentLines:
                    blocks.append((currentPeriod, currentLines))
                currentPeriod = "당기" if "당기" in s else "전기"
                currentLines = []
            continue

        cells = [c.strip() for c in s.split("|") if c.strip()]
        if not cells:
            continue

        cellJoined = "".join(cells).replace(" ", "")
        if len(cells) <= 2 and ("당기" in cellJoined or "전기" in cellJoined):
            if currentPeriod and currentLines:
                blocks.append((currentPeriod, currentLines))
            currentPeriod = "당기" if "당기" in cellJoined else "전기"
            currentLines = []
            continue

        if currentPeriod:
            currentLines.append(s)

    if currentPeriod and currentLines:
        blocks.append((currentPeriod, currentLines))

    if len(blocks) < 2:
        return None

    periodData = {}
    allAccounts = []

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

    return {
        "당기": periodData.get("당기", {}),
        "전기": periodData.get("전기", {}),
        "order": allAccounts,
        "type": "split",
    }


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
        m = re.match(r"^\d\)\s*(당기|전기)", s)
        if m:
            if currentPeriod and currentLines:
                blocks.append((currentPeriod, currentLines))
            currentPeriod = m.group(1)
            currentLines = []
            continue
        if s.startswith("|") and currentPeriod:
            currentLines.append(s)

    if currentPeriod and currentLines:
        blocks.append((currentPeriod, currentLines))

    if len(blocks) < 2:
        return None

    periodData = {}
    allAccounts = []

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

    return {
        "당기": periodData.get("당기", {}),
        "전기": periodData.get("전기", {}),
        "order": allAccounts,
        "type": "multiCol",
    }


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
        cellText = "".join(cells).replace(" ", "")
        if headerLine is None and ("당기" in cellText or "전기" in cellText) and len(cells) >= 2:
            headerLine = cells
            continue
        if headerLine and len(cells) >= 2:
            dataLines.append(cells)

    if not headerLine or not dataLines:
        return None

    danggiIdx = None
    jeongiIdx = None
    for j, h in enumerate(headerLine):
        hClean = h.replace(" ", "")
        if "당기" in hClean and danggiIdx is None:
            danggiIdx = j
        if "전기" in hClean and jeongiIdx is None:
            jeongiIdx = j

    if danggiIdx is None and jeongiIdx is None:
        return None

    danggiData = {}
    jeongiData = {}
    order = []

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

    return {
        "당기": danggiData,
        "전기": jeongiData,
        "order": order,
        "type": "inline",
    }


_SKIP_KEYWORDS = [
    "구분", "구 분", "계정과목", "공시금액",
    "단위", "합 계", "합계", "성격별 비용 합계",
    "성격별비용합계", "성격별 비용", "계",
]


def _isSkipRow(name):
    cleaned = name.strip()
    if not cleaned:
        return True
    for kw in _SKIP_KEYWORDS:
        if cleaned == kw:
            return True
    return False


def _cleanAccountName(name):
    name = name.strip()
    name = re.sub(r"^\d+[\.\)]\s*", "", name)
    name = re.sub(r"\s+", "", name)
    return name


if __name__ == "__main__":
    files = sorted(DATA_DIR.glob("*.parquet"))

    print(f"전체 종목: {len(files)}개")
    print("=" * 80)

    successList = []
    failList = []
    noSectionList = []
    noReportList = []

    typeCount = {"inline": 0, "split": 0, "multiCol": 0}

    for f in files:
        df = pl.read_parquet(str(f))
        corpName = df["corp_name"][0] if "corp_name" in df.columns else f.stem

        years = sorted(df["year"].unique().to_list(), reverse=True)
        report = None
        for y in years:
            report = selectReport(df, y, reportKind="annual")
            if report is not None:
                break

        if report is None:
            noReportList.append((f.stem, corpName))
            continue

        notes = extractNotesContent(report)
        if not notes:
            noSectionList.append((f.stem, corpName, "주석없음"))
            continue

        section = findCostByNatureSection(notes)
        if section is None:
            noSectionList.append((f.stem, corpName, "키워드없음"))
            continue

        result = parseCostByNature(section)
        if result is None:
            failList.append((f.stem, corpName, section[:200]))
            continue

        successList.append((f.stem, corpName, result["type"], len(result["order"])))
        typeCount[result["type"]] += 1

    total = len(files)
    withData = total - len(noReportList)

    print(f"\n결과 요약")
    print(f"  전체: {total}개")
    print(f"  보고서 없음: {len(noReportList)}개")
    print(f"  주석/키워드 없음: {len(noSectionList)}개")
    print(f"  파싱 실패: {len(failList)}개")
    print(f"  파싱 성공: {len(successList)}개")
    print()
    print(f"  성공률 (보고서 있는 종목 기준): {len(successList)}/{withData} = {len(successList)/withData*100:.1f}%")

    targetBase = withData - len(noSectionList)
    if targetBase > 0:
        print(f"  성공률 (비용의 성격 존재하는 종목 기준): {len(successList)}/{targetBase} = {len(successList)/targetBase*100:.1f}%")

    print(f"\n테이블 유형 분포:")
    for t, cnt in typeCount.items():
        print(f"  {t}: {cnt}개")

    accountCounts = [r[3] for r in successList]
    if accountCounts:
        print(f"\n계정 항목 수 통계:")
        print(f"  평균: {sum(accountCounts)/len(accountCounts):.1f}개")
        print(f"  최소: {min(accountCounts)}개, 최대: {max(accountCounts)}개")

    if noSectionList:
        print(f"\n비용의 성격 미발견 ({len(noSectionList)}개):")
        for code, name, reason in noSectionList[:20]:
            print(f"  {code} {name} ({reason})")
        if len(noSectionList) > 20:
            print(f"  ... +{len(noSectionList) - 20}개")

    if failList:
        print(f"\n파싱 실패 ({len(failList)}개):")
        for code, name, snippet in failList[:10]:
            print(f"  {code} {name}")
            print(f"    {snippet[:150]}")
        if len(failList) > 10:
            print(f"  ... +{len(failList) - 10}개")

    if noReportList:
        print(f"\n보고서 없음 ({len(noReportList)}개):")
        for code, name in noReportList[:10]:
            print(f"  {code} {name}")
        if len(noReportList) > 10:
            print(f"  ... +{len(noReportList) - 10}개")
