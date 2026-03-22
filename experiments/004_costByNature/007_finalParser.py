"""
실험 ID: 004-007
실험명: 비용의 성격별 분류 — 최종 파서 + 전체 종목 테스트

목적:
- 006에서 발견된 나머지 실패 케이스 9개 해결
- 인라인: "제 N(당) 기" → "당기" 매핑
- 멀티컬럼: (당기), <당기>, ① 당기 패턴 추가
- 전체 267개 종목에서 98%+ 성공률 달성

가설:
1. "제 N(당) 기" 패턴을 당기/전기로 매핑하면 인라인 4개 해결
2. 멀티컬럼 구분자 확장하면 나머지 5개 해결
3. 비용의 성격 존재 종목 기준 99% 이상 달성

방법:
1. _isDanggi / _isJeongi 헬퍼로 기간 판별 통합
2. multiCol 구분자: (당기), <당기>, ① 당기, 1) 당기, 제N(당)기
3. 전체 267개 종목 테스트

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


def _isDanggi(text: str) -> bool:
    t = text.replace(" ", "")
    if "당기" in t:
        return True
    if re.search(r"제\d+\(당\)기", t):
        return True
    return False


def _isJeongi(text: str) -> bool:
    t = text.replace(" ", "")
    if "전기" in t:
        return True
    if re.search(r"제\d+\(전\)기", t):
        return True
    return False


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


def _tryParseInlineTable(text: str) -> dict | None:
    """인라인 테이블: | 구분 | 당기 | 전기 | 또는 | 구분 | 제N(당)기 | 제N(전)기 |"""
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
            hasPeriod = any(_isPeriodLabel(c) for c in cells)
            if hasPeriod and len(cells) >= 2:
                headerLine = cells
                continue
        if headerLine and len(cells) >= 2:
            dataLines.append(cells)

    if not headerLine or not dataLines:
        return None

    danggiIdx = None
    jeongiIdx = None
    for j, h in enumerate(headerLine):
        if _isDanggi(h) and danggiIdx is None:
            danggiIdx = j
        if _isJeongi(h) and jeongiIdx is None:
            jeongiIdx = j

    if danggiIdx is None and jeongiIdx is None:
        return None

    danggiData: dict[str, float | None] = {}
    jeongiData: dict[str, float | None] = {}
    order: list[str] = []

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


def _tryParseSplitTable(text: str) -> dict | None:
    """분리형: 당기/전기가 별도 블록. DART 공시 스타일 단일 컬럼."""
    lines = text.split("\n")
    unit = detectUnit(text)

    blocks: list[tuple[str, list[str]]] = []
    currentPeriod = None
    currentLines: list[str] = []

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

    periodData: dict[str, dict[str, float | None]] = {}
    allAccounts: list[str] = []

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


def _parseSimpleRows(tableLines: list[str], unit: float) -> dict[str, float | None]:
    accounts: dict[str, float | None] = {}
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


def _tryParseMultiColTable(text: str) -> dict | None:
    """통합형: | 계정 | 판관비 | 원가 | 합계 |

    구분자 패턴:
    - 1) 당기 / 2) 전기
    - (당기) / (전기)
    - <당기> / <전기>
    - ① 당기 / ② 전기
    - 제 N(당) 기 등
    """
    lines = text.split("\n")
    unit = detectUnit(text)

    blocks: list[tuple[str, list[str]]] = []
    currentPeriod = None
    currentLines: list[str] = []

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
            continue

    if currentPeriod and currentLines:
        blocks.append((currentPeriod, currentLines))

    if len(blocks) < 2:
        return None

    periodData: dict[str, dict[str, float | None]] = {}
    allAccounts: list[str] = []

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


def _parseMultiColRows(tableLines: list[str], unit: float) -> dict[str, float | None]:
    accounts: dict[str, float | None] = {}
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


def _isSkipRow(name: str) -> bool:
    cleaned = name.strip()
    if not cleaned:
        return True
    if cleaned in _SKIP_KEYWORDS:
        return True
    cleanedNoSpace = cleaned.replace(" ", "")
    if cleanedNoSpace in {"합계", "계", "성격별비용합계", "성격별비용"}:
        return True
    return False


def _cleanAccountName(name: str) -> str:
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
        print(f"  성공률 (비용의 성격 존재 종목 기준): {len(successList)}/{targetBase} = {len(successList)/targetBase*100:.1f}%")

    print(f"\n테이블 유형 분포:")
    for t, cnt in typeCount.items():
        print(f"  {t}: {cnt}개")

    accountCounts = [r[3] for r in successList]
    if accountCounts:
        print(f"\n계정 항목 수 통계:")
        print(f"  평균: {sum(accountCounts)/len(accountCounts):.1f}개")
        print(f"  최소: {min(accountCounts)}개, 최대: {max(accountCounts)}개")

    if failList:
        print(f"\n파싱 실패 ({len(failList)}개):")
        for code, name, snippet in failList:
            print(f"  {code} {name}")
            print(f"    {snippet[:150]}")

    if noSectionList:
        print(f"\n비용의 성격 미발견 ({len(noSectionList)}개):")
        for code, name, reason in noSectionList[:15]:
            print(f"  {code} {name} ({reason})")
        if len(noSectionList) > 15:
            print(f"  ... +{len(noSectionList) - 15}개")
