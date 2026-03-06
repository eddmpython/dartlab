"""
실험 ID: 004-010
실험명: 비용의 성격별 분류 — 최종 파이프라인 (정규화 + 시계열 + 전체 종목)

목적:
- 계정명 정규화 매핑 적용
- 합계/소계 행 완전 제거
- 전체 267개 종목에 대해 시계열 구성 + 품질 검증
- 최종 성공률, 교차검증 일치율, null 비율 측정

가설:
1. 정규화 후 핵심 계정 커버율 90% 이상
2. 교차검증(당기 vs 전년 전기) 일치율 95% 이상
3. 시계열 null 비율 20% 이하

방법:
1. 정규화 매핑 적용 (키워드 기반 → 표준 계정명)
2. 합계행 필터 강화
3. 전체 종목 시계열 구성
4. 품질 지표 측정

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

NORMALIZE_MAP = [
    ("원재료사용", ["원재료", "원부재료", "소모품사용", "소모품의사용", "상품매입"]),
    ("종업원급여", ["종업원급여", "종업원급", "인건비"]),
    ("급여", ["급여"]),
    ("퇴직급여", ["퇴직급여"]),
    ("감가상각비", ["감가상각"]),
    ("무형자산상각비", ["무형자산상각", "무형자산감가"]),
    ("사용권자산상각비", ["사용권자산"]),
    ("재고자산변동", ["재고자산의변동", "재고자산변동", "재고자산의매입", "재고자산매입"]),
    ("제품재공품변동", ["제품및재공품", "제품과재공품", "제품,반제품", "제품,재공품"]),
    ("외주가공비", ["외주"]),
    ("지급수수료", ["지급수수료", "수수료비용", "판매수수료"]),
    ("운반비", ["운반"]),
    ("기타비용", ["기타비용", "기타영업비용"]),
    ("광고선전비", ["광고"]),
    ("수선비", ["수선"]),
    ("전력/수도", ["전력", "수도광열", "동력", "가스수도"]),
    ("소모품비", ["소모품비"]),
    ("복리후생비", ["복리후생"]),
    ("세금과공과", ["세금과공과"]),
    ("임차료", ["임차료", "지급임차료"]),
    ("여비교통비", ["여비교통"]),
    ("보험료", ["보험료"]),
    ("경상연구개발비", ["연구개발", "경상연구"]),
    ("대손상각비", ["대손상각"]),
    ("주식보상비용", ["주식보상"]),
    ("접대비", ["접대"]),
    ("포장비", ["포장비"]),
    ("용역비", ["용역비"]),
    ("판매촉진비", ["판매촉진"]),
    ("연료비", ["연료"]),
]

TOTAL_PATTERNS = [
    "합계", "소계", "성격별비용", "총영업비용",
    "매출원가및", "매출원가와", "매출원가,",
    "영업비용합계", "계속영업", "중단영업",
    "합계에대한", "비용의합계",
]


def normalizeAccountName(raw: str) -> str:
    cleaned = raw.replace(" ", "")
    for stdName, keywords in NORMALIZE_MAP:
        for kw in keywords:
            if kw in cleaned:
                return stdName
    return raw


def isTotalRow(name: str) -> bool:
    cleaned = name.replace(" ", "")
    for p in TOTAL_PATTERNS:
        if p in cleaned:
            return True
    if re.match(r"^계\(?[\*\d]*\)?$", cleaned):
        return True
    return False


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
    emptyCount, lastTable = 0, fromIdx
    for i in range(fromIdx, len(lines)):
        s = lines[i].strip()
        if s.startswith("|"): emptyCount = 0; lastTable = i + 1
        elif not s:
            emptyCount += 1
            if emptyCount >= 2 and lastTable > fromIdx: return lastTable
        else:
            if _isPeriodLabel(s) or re.match(r"^[\d①②③④⑤][\.\)]\s*", s): emptyCount = 0; continue
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
    headerLine, dataLines = None, []
    for line in tableLines:
        cells = [c.strip() for c in line.split("|") if c.strip()]
        if not cells: continue
        if "단위" in " ".join(cells): continue
        if headerLine is None:
            if any(_isPeriodLabel(c) for c in cells) and len(cells) >= 2: headerLine = cells; continue
        if headerLine and len(cells) >= 2: dataLines.append(cells)
    if not headerLine or not dataLines: return None
    danggiIdx = jeongiIdx = None
    for j, h in enumerate(headerLine):
        if _isDanggi(h) and danggiIdx is None: danggiIdx = j
        if _isJeongi(h) and jeongiIdx is None: jeongiIdx = j
    if danggiIdx is None and jeongiIdx is None: return None
    danggiData, jeongiData, order = {}, {}, []
    for cells in dataLines:
        name = _cleanAccountName(cells[0])
        if not name or _isSkipRow(name): continue
        if danggiIdx is not None and danggiIdx < len(cells):
            val = parseAmount(cells[danggiIdx])
            if val is not None and unit != 1.0: val *= unit
            danggiData[name] = val
        if jeongiIdx is not None and jeongiIdx < len(cells):
            val = parseAmount(cells[jeongiIdx])
            if val is not None and unit != 1.0: val *= unit
            jeongiData[name] = val
        if name not in order: order.append(name)
    return {"당기": danggiData, "전기": jeongiData, "order": order} if order else None

def _tryParseSplitTable(text):
    lines = text.split("\n"); unit = detectUnit(text)
    blocks, cur, cl = [], None, []
    for line in lines:
        s = line.strip()
        if not s.startswith("|"):
            p = _isPeriodLabel(s)
            if p:
                if cur and cl: blocks.append((cur, cl))
                cur = p; cl = []
            continue
        cells = [c.strip() for c in s.split("|") if c.strip()]
        if not cells: continue
        p = _isPeriodLabel("".join(cells).replace(" ",""))
        if p and len(cells) <= 2:
            if cur and cl: blocks.append((cur, cl))
            cur = p; cl = []
            continue
        if cur: cl.append(s)
    if cur and cl: blocks.append((cur, cl))
    if len(blocks) < 2: return None
    pd2, aa = {}, []
    for p, tl in blocks:
        acc = _parseSimpleRows(tl, unit)
        if not acc: continue
        pd2[p] = acc
        for n in acc:
            if n not in aa: aa.append(n)
    if not pd2 or not aa: return None
    return {"당기": pd2.get("당기",{}), "전기": pd2.get("전기",{}), "order": aa}

def _parseSimpleRows(tableLines, unit):
    accounts = {}
    for line in tableLines:
        if "---" in line: continue
        cells = [c.strip() for c in line.split("|") if c.strip()]
        if len(cells) < 2: continue
        name = _cleanAccountName(cells[0])
        if not name or _isSkipRow(name): continue
        val = parseAmount(cells[-1])
        if val is not None and unit != 1.0: val *= unit
        if name: accounts[name] = val
    return accounts

def _tryParseMultiColTable(text):
    lines = text.split("\n"); unit = detectUnit(text)
    blocks, cur, cl = [], None, []
    for line in lines:
        s = line.strip()
        if s.startswith("|"):
            if cur: cl.append(s)
            continue
        p = _isPeriodLabel(s)
        if p:
            if cur and cl: blocks.append((cur, cl))
            cur = p; cl = []
    if cur and cl: blocks.append((cur, cl))
    if len(blocks) < 2: return None
    pd2, aa = {}, []
    for p, tl in blocks:
        acc = _parseMultiColRows(tl, unit)
        if not acc: continue
        pd2[p] = acc
        for n in acc:
            if n not in aa: aa.append(n)
    if not pd2 or not aa: return None
    return {"당기": pd2.get("당기",{}), "전기": pd2.get("전기",{}), "order": aa}

def _parseMultiColRows(tableLines, unit):
    accounts, hp = {}, False
    for line in tableLines:
        if "---" in line: hp = True; continue
        if not hp: continue
        cells = [c.strip() for c in line.split("|") if c.strip()]
        if len(cells) < 3: continue
        name = _cleanAccountName(cells[0])
        if not name or _isSkipRow(name) or "단위" in name: continue
        val = parseAmount(cells[-1])
        if val is not None and unit != 1.0: val *= unit
        if name: accounts[name] = val
    return accounts

_SKIP_KEYWORDS = {"구분","구 분","계정과목","공시금액","단위"}

def _isSkipRow(name):
    if not name: return True
    c = name.replace(" ","")
    if c in _SKIP_KEYWORDS or name in _SKIP_KEYWORDS: return True
    if isTotalRow(name): return True
    return False

def _cleanAccountName(name):
    name = name.strip()
    name = re.sub(r"^\d+[\.\)]\s*", "", name)
    name = re.sub(r"\s+", "", name)
    return name


def buildTimeSeries(df, normalize=True):
    corpName = df["corp_name"][0] if "corp_name" in df.columns else "?"
    years = sorted(df["year"].unique().to_list(), reverse=True)

    yearData = {}
    prevData = {}
    allAccounts = []

    for year in years:
        report = selectReport(df, year, reportKind="annual")
        if report is None: continue
        notes = extractNotesContent(report)
        if not notes: continue
        section = findCostByNatureSection(notes)
        if section is None: continue
        result = parseCostByNature(section)
        if result is None: continue

        danggi = {}
        jeongi = {}
        order = []

        for rawName in result["order"]:
            if isTotalRow(rawName):
                continue
            stdName = normalizeAccountName(rawName) if normalize else rawName

            if stdName in danggi:
                continue

            dVal = result["당기"].get(rawName)
            jVal = result["전기"].get(rawName)

            danggi[stdName] = dVal
            jeongi[stdName] = jVal

            if stdName not in order:
                order.append(stdName)

        if danggi:
            yearData[year] = danggi
            for n in order:
                if n not in allAccounts:
                    allAccounts.append(n)
        if jeongi:
            prevData[year] = jeongi

    if not yearData:
        return None, {"corpName": corpName}

    sortedYears = sorted(yearData.keys(), reverse=True)

    crossCheck = {}
    for year in sortedYears:
        if year not in prevData: continue
        prevYear = str(int(year) - 1)
        if prevYear not in yearData: continue
        matches = mismatches = 0
        for name, pv in prevData[year].items():
            av = yearData[prevYear].get(name)
            if pv is not None and av is not None:
                if abs(pv - av) < 1: matches += 1
                else: mismatches += 1
        crossCheck[year] = {"matches": matches, "mismatches": mismatches}

    rows = []
    for name in allAccounts:
        row = {"계정명": name}
        for year in sortedYears:
            row[year] = yearData[year].get(name)
        rows.append(row)

    if not rows:
        return None, {"corpName": corpName}

    schema = {"계정명": pl.Utf8}
    for y in sortedYears: schema[y] = pl.Float64

    return pl.DataFrame(rows, schema=schema), {
        "corpName": corpName,
        "years": sortedYears,
        "crossCheck": crossCheck,
    }


if __name__ == "__main__":
    files = sorted(DATA_DIR.glob("*.parquet"))

    totalSuccess = 0
    totalFail = 0
    totalSkip = 0
    allCrossMatches = 0
    allCrossMismatches = 0
    allCells = 0
    allNulls = 0
    yearCounts = Counter()
    accountCounts = []

    print(f"전체 종목: {len(files)}개")
    print("=" * 80)

    sampleCodes = {"005930", "000660", "051910", "005380", "035420"}
    sampleResults = {}

    for f in files:
        df = pl.read_parquet(str(f))
        result, meta = buildTimeSeries(df, normalize=True)

        if result is None:
            if meta.get("corpName"):
                totalSkip += 1
            else:
                totalFail += 1
            continue

        totalSuccess += 1
        nYears = len(meta["years"])
        nAccounts = result.height
        yearCounts[nYears] += 1
        accountCounts.append(nAccounts)

        dataCols = [c for c in result.columns if c != "계정명"]
        for col in dataCols:
            vals = result[col].to_list()
            allCells += len(vals)
            allNulls += sum(1 for v in vals if v is None)

        for cc in meta["crossCheck"].values():
            allCrossMatches += cc["matches"]
            allCrossMismatches += cc["mismatches"]

        if f.stem in sampleCodes:
            sampleResults[f.stem] = (result, meta)

    print(f"\n결과 요약")
    print(f"  성공: {totalSuccess}개")
    print(f"  스킵 (데이터 없음): {totalSkip}개")
    print(f"  실패: {totalFail}개")

    crossTotal = allCrossMatches + allCrossMismatches
    if crossTotal > 0:
        print(f"\n교차검증 (당기 vs 전기)")
        print(f"  일치: {allCrossMatches}/{crossTotal} ({allCrossMatches/crossTotal*100:.1f}%)")
        print(f"  불일치: {allCrossMismatches}/{crossTotal}")

    if allCells > 0:
        print(f"\nnull 비율")
        print(f"  전체 셀: {allCells:,}")
        print(f"  null 셀: {allNulls:,} ({allNulls/allCells*100:.1f}%)")
        print(f"  유효 셀: {allCells - allNulls:,} ({(allCells-allNulls)/allCells*100:.1f}%)")

    if accountCounts:
        print(f"\n계정 수 통계 (정규화 후)")
        print(f"  평균: {sum(accountCounts)/len(accountCounts):.1f}개")
        print(f"  최소: {min(accountCounts)}개, 최대: {max(accountCounts)}개")

    print(f"\n시계열 기간 분포")
    for nYears in sorted(yearCounts.keys(), reverse=True):
        cnt = yearCounts[nYears]
        print(f"  {nYears}년: {cnt}개 종목")

    for code in ["005930", "000660", "051910"]:
        if code not in sampleResults:
            continue
        result, meta = sampleResults[code]
        print(f"\n{'=' * 80}")
        print(f"[샘플] {meta['corpName']} ({code})")
        print(f"{'=' * 80}")
        print(f"  기간: {meta['years']}")
        print(f"  계정 수: {result.height}개")

        with pl.Config(tbl_cols=min(len(meta["years"]) + 1, 12), tbl_width_chars=120):
            print(result)
