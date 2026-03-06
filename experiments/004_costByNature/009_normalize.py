"""
실험 ID: 004-009
실험명: 비용의 성격별 분류 — 계정명 정규화 + 합계행 필터링

목적:
- 전체 종목에서 출현하는 계정명 빈도 분석
- 유사 계정명 통합 매핑 구축 (종업원급여 vs 종업원급여비용 등)
- 합계/소계 행 완전 제거
- 시계열 DataFrame에서 null 비율 감소 효과 측정

가설:
1. 핵심 계정 6~8개로 70% 이상 종목 커버 가능
2. 계정명 정규화로 null 비율 30% 이상 감소
3. 합계행 패턴은 5가지 이내

방법:
1. 171개 성공 종목에서 모든 계정명 수집
2. 빈도 분석 → 유사 계정 그룹핑
3. 정규화 매핑 구축 → 적용 전후 비교

결과 (실험 후 작성):

결론:

실험일: 2026-03-06
"""

import re
import sys
from pathlib import Path
from collections import Counter

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from dartlab.core.tableParser import parseAmount, detectUnit
from dartlab.core.reportSelector import selectReport

DATA_DIR = Path("data/docsData")


def _isDanggi(text):
    t = text.replace(" ", "")
    return "당기" in t or bool(re.search(r"제\d+\(당\)기", t))

def _isJeongi(text):
    t = text.replace(" ", "")
    return "전기" in t or bool(re.search(r"제\d+\(전\)기", t))

def _isPeriodLabel(text):
    if _isDanggi(text): return "당기"
    if _isJeongi(text): return "전기"
    return None

def extractNotesContent(report):
    section = report.filter(pl.col("section_title").str.contains("주석"))
    return section["section_content"].to_list() if section.height > 0 else []

def _findNextSection(lines, fromIdx, pattern):
    for i in range(fromIdx, len(lines)):
        s = lines[i].strip()
        if s.startswith("|"): continue
        if re.match(pattern, s): return i
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
            if emptyCount >= 2 and lastTable > fromIdx: return lastTable
        else:
            if _isPeriodLabel(s) or re.match(r"^[\d①②③④⑤][\.\)]\s*", s):
                emptyCount = 0
                continue
            if lastTable > fromIdx + 5: return lastTable
    return len(lines)

def findCostByNatureSection(contents):
    for content in contents:
        lines = content.split("\n")
        for i, line in enumerate(lines):
            s = line.strip()
            if s.startswith("|"): continue
            m = re.match(r"^(\d{1,2})\.\s+(.+)", s)
            if m and "비용" in m.group(2) and "성격" in m.group(2):
                return "\n".join(lines[i:_findNextSection(lines, i+1, r"^(\d{1,2})\.\s+")])
            m2 = re.match(r"^\((\d{1,2})\)\s+(.+)", s)
            if m2 and "비용" in m2.group(2) and "성격" in m2.group(2):
                return "\n".join(lines[i:_findNextSection(lines, i+1, r"^\(\d{1,2}\)\s+")])
    for content in contents:
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if "비용의 성격" in line or ("성격별" in line and "비용" in line):
                return "\n".join(lines[max(0,i-1):_findTableEnd(lines, i+1)])
    return None

def parseCostByNature(sectionText):
    for fn in [_tryParseInlineTable, _tryParseSplitTable, _tryParseMultiColTable]:
        result = fn(sectionText)
        if result: return result
    return None

def _tryParseInlineTable(text):
    lines = text.split("\n")
    unit = detectUnit(text)
    tableLines = [l for l in lines if l.strip().startswith("|") and "---" not in l]
    if len(tableLines) < 3: return None
    headerLine = None
    dataLines = []
    for line in tableLines:
        cells = [c.strip() for c in line.split("|") if c.strip()]
        if not cells: continue
        if "단위" in " ".join(cells): continue
        if headerLine is None:
            if any(_isPeriodLabel(c) for c in cells) and len(cells) >= 2:
                headerLine = cells; continue
        if headerLine and len(cells) >= 2: dataLines.append(cells)
    if not headerLine or not dataLines: return None
    danggiIdx = jeongiIdx = None
    for j, h in enumerate(headerLine):
        if _isDanggi(h) and danggiIdx is None: danggiIdx = j
        if _isJeongi(h) and jeongiIdx is None: jeongiIdx = j
    if danggiIdx is None and jeongiIdx is None: return None
    danggiData, jeongiData, order = {}, {}, []
    for cells in dataLines:
        name = cells[0]
        if _isSkipRow(name): continue
        name = _cleanAccountName(name)
        if not name: continue
        if danggiIdx is not None and danggiIdx < len(cells):
            val = parseAmount(cells[danggiIdx])
            if val is not None and unit != 1.0: val *= unit
            danggiData[name] = val
        if jeongiIdx is not None and jeongiIdx < len(cells):
            val = parseAmount(cells[jeongiIdx])
            if val is not None and unit != 1.0: val *= unit
            jeongiData[name] = val
        if name not in order: order.append(name)
    return {"당기": danggiData, "전기": jeongiData, "order": order, "type": "inline"} if order else None

def _tryParseSplitTable(text):
    lines = text.split("\n")
    unit = detectUnit(text)
    blocks, currentPeriod, currentLines = [], None, []
    for line in lines:
        s = line.strip()
        if not s.startswith("|"):
            period = _isPeriodLabel(s)
            if period:
                if currentPeriod and currentLines: blocks.append((currentPeriod, currentLines))
                currentPeriod = period; currentLines = []
            continue
        cells = [c.strip() for c in s.split("|") if c.strip()]
        if not cells: continue
        period = _isPeriodLabel("".join(cells).replace(" ",""))
        if period and len(cells) <= 2:
            if currentPeriod and currentLines: blocks.append((currentPeriod, currentLines))
            currentPeriod = period; currentLines = []
            continue
        if currentPeriod: currentLines.append(s)
    if currentPeriod and currentLines: blocks.append((currentPeriod, currentLines))
    if len(blocks) < 2: return None
    periodData, allAccounts = {}, []
    for period, tl in blocks:
        acc = _parseSimpleRows(tl, unit)
        if not acc: continue
        periodData[period] = acc
        for n in acc:
            if n not in allAccounts: allAccounts.append(n)
    if not periodData or not allAccounts: return None
    return {"당기": periodData.get("당기",{}), "전기": periodData.get("전기",{}), "order": allAccounts, "type": "split"}

def _parseSimpleRows(tableLines, unit):
    accounts = {}
    for line in tableLines:
        if "---" in line: continue
        cells = [c.strip() for c in line.split("|") if c.strip()]
        if len(cells) < 2: continue
        name = cells[0]
        if _isSkipRow(name): continue
        val = parseAmount(cells[-1])
        if val is not None and unit != 1.0: val *= unit
        name = _cleanAccountName(name)
        if name: accounts[name] = val
    return accounts

def _tryParseMultiColTable(text):
    lines = text.split("\n")
    unit = detectUnit(text)
    blocks, currentPeriod, currentLines = [], None, []
    for line in lines:
        s = line.strip()
        if s.startswith("|"):
            if currentPeriod: currentLines.append(s)
            continue
        period = _isPeriodLabel(s)
        if period:
            if currentPeriod and currentLines: blocks.append((currentPeriod, currentLines))
            currentPeriod = period; currentLines = []
    if currentPeriod and currentLines: blocks.append((currentPeriod, currentLines))
    if len(blocks) < 2: return None
    periodData, allAccounts = {}, []
    for period, tl in blocks:
        acc = _parseMultiColRows(tl, unit)
        if not acc: continue
        periodData[period] = acc
        for n in acc:
            if n not in allAccounts: allAccounts.append(n)
    if not periodData or not allAccounts: return None
    return {"당기": periodData.get("당기",{}), "전기": periodData.get("전기",{}), "order": allAccounts, "type": "multiCol"}

def _parseMultiColRows(tableLines, unit):
    accounts = {}
    headerPassed = False
    for line in tableLines:
        if "---" in line: headerPassed = True; continue
        if not headerPassed: continue
        cells = [c.strip() for c in line.split("|") if c.strip()]
        if len(cells) < 3: continue
        name = cells[0]
        if _isSkipRow(name) or "단위" in name: continue
        val = parseAmount(cells[-1])
        if val is not None and unit != 1.0: val *= unit
        name = _cleanAccountName(name)
        if name: accounts[name] = val
    return accounts


_SKIP_KEYWORDS = {
    "구분", "구 분", "계정과목", "공시금액",
    "단위", "합 계", "합계", "성격별 비용 합계",
    "성격별비용합계", "성격별 비용", "계", "성격별비용",
}

def _isSkipRow(name):
    cleaned = name.strip()
    if not cleaned: return True
    if cleaned in _SKIP_KEYWORDS: return True
    if cleaned.replace(" ","") in {"합계","계","성격별비용합계","성격별비용"}: return True
    return False

def _cleanAccountName(name):
    name = name.strip()
    name = re.sub(r"^\d+[\.\)]\s*", "", name)
    name = re.sub(r"\s+", "", name)
    return name


if __name__ == "__main__":
    files = sorted(DATA_DIR.glob("*.parquet"))

    allNames = Counter()
    perCompany = {}

    for f in files:
        df = pl.read_parquet(str(f))
        corpName = df["corp_name"][0] if "corp_name" in df.columns else f.stem

        years = sorted(df["year"].unique().to_list(), reverse=True)
        for y in years:
            report = selectReport(df, y, reportKind="annual")
            if report is None:
                continue
            notes = extractNotesContent(report)
            if not notes:
                break
            section = findCostByNatureSection(notes)
            if section is None:
                break
            result = parseCostByNature(section)
            if result is None:
                break

            for name in result["order"]:
                allNames[name] += 1
            perCompany[f.stem] = result["order"]
            break

    print(f"분석 종목 수: {len(perCompany)}")
    print(f"고유 계정명 수: {len(allNames)}")
    print()

    print("=" * 80)
    print("PART 1: 빈도 TOP 50")
    print("=" * 80)
    for name, cnt in allNames.most_common(50):
        pct = cnt / len(perCompany) * 100
        print(f"  {cnt:>4}개 ({pct:>5.1f}%)  {name}")

    print()
    print("=" * 80)
    print("PART 2: 합계/소계 패턴 탐지")
    print("=" * 80)
    totalPatterns = Counter()
    for name, cnt in allNames.items():
        cleaned = name.replace(" ", "")
        if any(kw in cleaned for kw in ["합계", "계(*", "총영업", "매출원가와", "성격별비용"]):
            totalPatterns[name] = cnt

    for name, cnt in totalPatterns.most_common(30):
        print(f"  {cnt:>4}개  {name}")

    print()
    print("=" * 80)
    print("PART 3: 유사 계정 그룹")
    print("=" * 80)

    groups = {
        "원재료사용": [],
        "종업원급여": [],
        "감가상각": [],
        "무형자산상각": [],
        "재고변동": [],
        "외주가공": [],
        "지급수수료": [],
        "운반비": [],
        "기타비용": [],
        "광고선전": [],
        "수선비": [],
        "전력/동력": [],
    }

    keywords = {
        "원재료사용": ["원재료", "원부재료", "소모품사용", "상품매입"],
        "종업원급여": ["종업원", "급여", "인건비"],
        "감가상각": ["감가상각"],
        "무형자산상각": ["무형자산상각", "무형자산감가"],
        "재고변동": ["재고", "제품및재공품", "제품,반제품"],
        "외주가공": ["외주"],
        "지급수수료": ["수수료"],
        "운반비": ["운반"],
        "기타비용": ["기타"],
        "광고선전": ["광고"],
        "수선비": ["수선"],
        "전력/동력": ["전력", "동력", "수도"],
    }

    for name, cnt in allNames.items():
        cleaned = name.replace(" ", "")
        for group, kws in keywords.items():
            if any(kw in cleaned for kw in kws):
                groups[group].append((name, cnt))
                break

    for group, items in groups.items():
        if not items:
            continue
        items.sort(key=lambda x: -x[1])
        total = sum(c for _, c in items)
        print(f"\n  [{group}] ({len(items)}개 변형, 총 {total}건)")
        for name, cnt in items[:8]:
            print(f"    {cnt:>4}개  {name}")
        if len(items) > 8:
            print(f"    ... +{len(items) - 8}개")
