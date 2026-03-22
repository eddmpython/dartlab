"""
실험 ID: 022-02
실험명: 이사회 파서 + 시계열

목적:
- 이사회 섹션에서 정량 데이터 파싱
- (1) 이사 수 / 사외이사 수 테이블
- (2) 이사회 개최횟수 + 참석률 집계
- (3) 위원회 구성 현황
- 연도별 시계열 생성

가설:
1. 이사 수 테이블: "이사의 수 | 사외이사 수" 패턴으로 분류 가능
2. 이사회 개최: 개최일자 행 수 = 개최횟수, 참석률은 헤더 또는 셀에서 추출
3. 위원회 구성: 위원회명 + 구성 + 이사명 패턴
4. 219/267 이상에서 이사회 데이터 추출 가능

방법:
1. classifyBlock으로 테이블 분류
2. 각 유형별 파서 구현
3. 267개 대량 테스트

결과 (실험 후 작성):

결론:

실험일: 2026-03-08
"""
import collections
import os
import re
import sys

import polars as pl

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import selectReport

DATA_DIR = r"C:\Users\MSI\OneDrive\Desktop\sideProject\nicegui\eddmpython\data\dartData\docsData"

BOARD_SECTION_PATTERNS = [
    r"이사회에\s*관한\s*사항",
]

BOARD_PARENT_PATTERNS = [
    r"이사회\s*등\s*회사의\s*기관",
]


# ──────────────────────────────────────────────
# 유틸리티
# ──────────────────────────────────────────────

def _cellsFromLine(line: str) -> list[str]:
    return [c.strip() for c in line.split("|")[1:-1]]


def _isSeparator(cells: list[str]) -> bool:
    return all(re.match(r"^-+$", c.strip()) or c.strip() == "" for c in cells)


def _parseFloat(text: str) -> float | None:
    if not text or text.strip() in ("-", "", "—", "해당없음"):
        return None
    text = text.replace(",", "").replace(" ", "").strip()
    try:
        return float(text)
    except ValueError:
        return None


def _parseInt(text: str) -> int | None:
    v = _parseFloat(text)
    return int(v) if v is not None else None


def extractTableBlocks(content: str) -> list[list[str]]:
    lines = content.split("\n")
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if line.strip().startswith("|"):
            current.append(line)
        else:
            if current:
                blocks.append(current)
                current = []
    if current:
        blocks.append(current)
    return blocks


# ──────────────────────────────────────────────
# 섹션 탐색
# ──────────────────────────────────────────────

def findBoardSection(df: pl.DataFrame, year: str) -> str | None:
    report = selectReport(df, year, reportKind="annual")
    if report is None:
        return None

    for row in report.iter_rows(named=True):
        title = row.get("section_title", "") or ""
        if any(re.search(p, title) for p in BOARD_SECTION_PATTERNS):
            content = row.get("section_content", "") or ""
            if len(content) > 100:
                return content

    for row in report.iter_rows(named=True):
        title = row.get("section_title", "") or ""
        if any(re.search(p, title) for p in BOARD_PARENT_PATTERNS):
            content = row.get("section_content", "") or ""
            if len(content) > 100:
                return content

    return None


# ──────────────────────────────────────────────
# 블록 분류
# ──────────────────────────────────────────────

def classifyBlock(block: list[str]) -> str:
    """테이블 블록 분류.

    Returns: "directorCount" | "boardMeeting" | "committee" | "committeeActivity" | "education" | "independence" | "other"
    """
    allText = ""
    for line in block[:6]:
        cells = _cellsFromLine(line)
        if not _isSeparator(cells):
            allText += " " + " ".join(c for c in cells if c.strip())

    # 이사 수 테이블: "이사의 수" + "사외이사 수"
    if re.search(r"이사의\s*수", allText) and re.search(r"사외이사\s*수", allText):
        return "directorCount"

    # 이사회 개최/참석: "개최일자" + "의안" + "가결"
    if re.search(r"개최일자", allText) and re.search(r"의\s*안|의안", allText) and re.search(r"가결", allText):
        # 위원회 활동과 구분: "위원회명"이 있으면 committeeActivity
        if re.search(r"위원회명", allText):
            return "committeeActivity"
        return "boardMeeting"

    # 위원회 구성: "위원회명" + "구성" 또는 "설치목적"
    if re.search(r"위원회명", allText) and re.search(r"구\s*성|설치목적|권한", allText):
        return "committee"

    # 사외이사 교육: "교육일자" + "참석"
    if re.search(r"교육일자", allText) and re.search(r"참석", allText):
        return "education"

    # 사외이사 독립성: "추천인" + "선임배경" 또는 "활동분야"
    if re.search(r"추천인", allText) and re.search(r"선임배경|활동분야|임\s*기", allText):
        return "independence"

    return "other"


# ──────────────────────────────────────────────
# 이사 수 파서
# ──────────────────────────────────────────────

def parseDirectorCount(block: list[str]) -> dict | None:
    """이사 수 / 사외이사 수 파싱.

    Returns: {"totalDirectors": int, "outsideDirectors": int,
              "newOutside": int|None, "retiredOutside": int|None}
    """
    rows = []
    for line in block:
        cells = _cellsFromLine(line)
        if _isSeparator(cells):
            continue
        rows.append(cells)

    if len(rows) < 2:
        return None

    # 헤더 찾기
    headerIdx = None
    for i, row in enumerate(rows):
        text = " ".join(row)
        if re.search(r"이사의\s*수", text) and re.search(r"사외이사\s*수", text):
            headerIdx = i
            break

    if headerIdx is None:
        return None

    header = rows[headerIdx]
    nCols = len(header)

    colTotal = None
    colOutside = None
    colNew = None
    colRetired = None

    for i, h in enumerate(header):
        h = h.replace(" ", "")
        if re.search(r"이사의수", h):
            colTotal = i
        elif re.search(r"사외이사수", h):
            colOutside = i
        elif re.search(r"선임", h):
            colNew = i
        elif re.search(r"해임|퇴임", h):
            colRetired = i

    if colTotal is None or colOutside is None:
        return None

    # 데이터 행: 헤더 이후 숫자가 포함된 행 탐색
    # 서브헤더가 있을 수 있음 (선임 | 해임 | 중도퇴임)
    dataRow = None
    for row in rows[headerIdx + 1:]:
        text = " ".join(row)
        if re.search(r"단위", text):
            continue
        # 서브헤더 스킵: "선임", "해임" 등 텍스트만 있는 행
        if re.search(r"선임|해임|중도퇴임", text) and not any(_parseInt(c) is not None for c in row):
            continue
        # 숫자가 있는 행
        for cell in row:
            if _parseInt(cell) is not None:
                dataRow = row
                break
        if dataRow is not None:
            break

    if dataRow is None:
        return None

    while len(dataRow) < nCols:
        dataRow.append("")

    result = {
        "totalDirectors": _parseInt(dataRow[colTotal]),
        "outsideDirectors": _parseInt(dataRow[colOutside]),
    }

    if colNew is not None:
        result["newOutside"] = _parseInt(dataRow[colNew])
    if colRetired is not None:
        result["retiredOutside"] = _parseInt(dataRow[colRetired])

    return result


# ──────────────────────────────────────────────
# 이사회 개최/참석률 파서
# ──────────────────────────────────────────────

def parseBoardMeeting(block: list[str]) -> dict | None:
    """이사회 개최 횟수 + 출석률 파싱.

    Returns: {"meetingCount": int, "attendanceRates": {이름: float}}
    """
    rows = []
    for line in block:
        cells = _cellsFromLine(line)
        if _isSeparator(cells):
            continue
        rows.append(cells)

    if len(rows) < 3:
        return None

    # 헤더 찾기: "개최일자" + "의안" + "가결"
    headerIdx = None
    for i, row in enumerate(rows):
        text = " ".join(row)
        if re.search(r"개최일자", text) and re.search(r"가결", text):
            headerIdx = i
            break

    if headerIdx is None:
        return None

    # 출석률 추출: 이름(출석률:XX%) 패턴
    attendanceRates = {}
    for row in rows[:headerIdx + 2]:
        for cell in row:
            matches = re.findall(r"(\S+?)\s*\(출석률\s*:?\s*([\d.]+)\s*%\)", cell)
            for name, rate in matches:
                try:
                    attendanceRates[name] = float(rate)
                except ValueError:
                    pass

    # 개최횟수: 날짜 패턴 행 카운트
    # 4자리 연도 또는 축약형 ('24.01.31) 모두 매칭
    datePattern = re.compile(r"(?:\d{4}|'\d{2})[.\-/]\d{1,2}[.\-/]\d{1,2}")
    meetingDates = set()
    for row in rows[headerIdx + 1:]:
        for cell in row:
            dates = datePattern.findall(cell)
            for d in dates:
                meetingDates.add(d)

    # 회차 번호로도 카운트 (예: "1차", "(1차)", 또는 첫 셀이 숫자)
    maxSession = 0
    sessionPattern = re.compile(r"^(\d+)$")
    sessionInText = re.compile(r"\((\d+)차\)")
    for row in rows[headerIdx + 1:]:
        if row:
            m = sessionPattern.match(row[0].strip())
            if m:
                maxSession = max(maxSession, int(m.group(1)))
        # 텍스트 내 (N차) 패턴
        for cell in row:
            for sm in sessionInText.finditer(cell):
                maxSession = max(maxSession, int(sm.group(1)))

    meetingCount = max(len(meetingDates), maxSession)

    if meetingCount == 0 and not attendanceRates:
        return None

    return {
        "meetingCount": meetingCount,
        "attendanceRates": attendanceRates,
    }


# ──────────────────────────────────────────────
# 위원회 구성 파서
# ──────────────────────────────────────────────

def parseCommittee(block: list[str]) -> list[dict]:
    """위원회 구성 파싱.

    Returns: [{"name": str, "composition": str, "members": str}]
    """
    rows = []
    for line in block:
        cells = _cellsFromLine(line)
        if _isSeparator(cells):
            continue
        rows.append(cells)

    if len(rows) < 2:
        return []

    # 헤더 찾기
    headerIdx = None
    for i, row in enumerate(rows):
        text = " ".join(row)
        if re.search(r"위원회명", text) and re.search(r"구\s*성|소속", text):
            headerIdx = i
            break

    if headerIdx is None:
        return []

    header = rows[headerIdx]
    nCols = len(header)

    colName = None
    colComp = None
    colMembers = None

    for i, h in enumerate(header):
        h = h.replace(" ", "")
        if re.search(r"위원회명", h):
            colName = i
        elif re.search(r"구성", h):
            colComp = i
        elif re.search(r"소속|성명", h):
            colMembers = i

    if colName is None:
        colName = 0

    result = []
    for row in rows[headerIdx + 1:]:
        while len(row) < nCols:
            row.append("")

        name = row[colName].strip()
        if not name:
            continue

        comp = row[colComp].strip() if colComp is not None else ""
        members = row[colMembers].strip() if colMembers is not None else ""

        result.append({
            "name": name,
            "composition": comp,
            "members": members,
        })

    return result


# ──────────────────────────────────────────────
# 통합 파싱 + 시계열
# ──────────────────────────────────────────────

def _parseDirectorCountFromText(content: str) -> dict | None:
    """content 텍스트에서 이사 수 / 사외이사 수를 직접 추출 (fallback)."""
    # "이사의 수 | 사외이사 수" 패턴 찾기
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if re.search(r"이사의\s*수", line) and re.search(r"사외이사\s*수", line):
            # 이 줄 이후 2~4줄 내에 숫자 행이 있음
            for j in range(i + 1, min(i + 5, len(lines))):
                cells = _cellsFromLine(lines[j]) if lines[j].strip().startswith("|") else []
                if not cells:
                    continue
                if _isSeparator(cells):
                    continue
                # 서브헤더 스킵
                text = " ".join(cells)
                if re.search(r"선임|해임|중도퇴임|단위", text) and not any(_parseInt(c) is not None for c in cells):
                    continue
                # 첫 두 숫자가 이사수, 사외이사수
                nums = [_parseInt(c) for c in cells]
                validNums = [n for n in nums if n is not None]
                if len(validNums) >= 2:
                    return {
                        "totalDirectors": validNums[0],
                        "outsideDirectors": validNums[1],
                    }
    return None


def parseBoardSection(content: str) -> dict:
    """이사회 섹션 전체를 파싱."""
    blocks = extractTableBlocks(content)

    directorCount = None
    meeting = None
    committees = []

    for block in blocks:
        kind = classifyBlock(block)
        if kind == "directorCount" and directorCount is None:
            directorCount = parseDirectorCount(block)
        elif kind == "boardMeeting" and meeting is None:
            meeting = parseBoardMeeting(block)
        elif kind == "committee" and not committees:
            committees = parseCommittee(block)

    # fallback: 블록 분류에서 놓친 이사 수 직접 탐색
    if directorCount is None:
        directorCount = _parseDirectorCountFromText(content)

    return {
        "directorCount": directorCount,
        "meeting": meeting,
        "committees": committees,
    }


def buildBoardTimeSeries(stockCode: str) -> dict | None:
    """이사회 시계열 생성."""
    df = loadData(stockCode)
    corpName = extractCorpName(df)
    years = sorted(df["year"].unique().to_list(), reverse=True)

    rows: list[dict] = []
    committeeRows: list[dict] = []

    for year in years:
        content = findBoardSection(df, year)
        if content is None:
            continue

        result = parseBoardSection(content)

        row = {"year": year}

        if result["directorCount"]:
            dc = result["directorCount"]
            row["totalDirectors"] = dc.get("totalDirectors")
            row["outsideDirectors"] = dc.get("outsideDirectors")

        if result["meeting"]:
            m = result["meeting"]
            row["meetingCount"] = m.get("meetingCount")
            rates = m.get("attendanceRates", {})
            if rates:
                row["avgAttendanceRate"] = round(sum(rates.values()) / len(rates), 1)

        if row.keys() > {"year"}:
            rows.append(row)

        if result["committees"]:
            for comm in result["committees"]:
                committeeRows.append({
                    "year": year,
                    "committeeName": comm["name"],
                    "composition": comm["composition"],
                    "members": comm["members"],
                })

    if not rows and not committeeRows:
        return None

    boardDf = _buildBoardDf(rows) if rows else None
    committeeDf = _buildCommitteeDf(committeeRows) if committeeRows else None

    return {
        "corpName": corpName,
        "nYears": len(rows),
        "boardDf": boardDf,
        "committeeDf": committeeDf,
    }


def _buildBoardDf(rows: list[dict]) -> pl.DataFrame:
    data = sorted(rows, key=lambda x: x["year"], reverse=True)
    schema = {
        "year": pl.Utf8,
        "totalDirectors": pl.Int64,
        "outsideDirectors": pl.Int64,
        "meetingCount": pl.Int64,
        "avgAttendanceRate": pl.Float64,
    }
    for r in data:
        for col in schema:
            if col not in r:
                r[col] = None
    return pl.DataFrame(data, schema=schema)


def _buildCommitteeDf(rows: list[dict]) -> pl.DataFrame:
    data = sorted(rows, key=lambda x: (x["year"], x["committeeName"]), reverse=True)
    schema = {
        "year": pl.Utf8,
        "committeeName": pl.Utf8,
        "composition": pl.Utf8,
        "members": pl.Utf8,
    }
    return pl.DataFrame(data, schema=schema)


if __name__ == "__main__":
    # 샘플 테스트
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

        result = buildBoardTimeSeries(code)
        if result is None:
            print("  결과 없음")
            continue

        print(f"  {result['corpName']} — {result['nYears']}년")

        if result["boardDf"] is not None:
            print(f"\n  [이사회 시계열]")
            print(result["boardDf"])

        if result["committeeDf"] is not None:
            print(f"\n  [위원회 구성] (최근)")
            print(result["committeeDf"].head(10))

    # 대량 테스트
    print(f"\n\n{'='*60}")
    print("267개 대량 테스트")
    print(f"{'='*60}")

    codes = sorted([f.replace(".parquet", "") for f in os.listdir(DATA_DIR) if f.endswith(".parquet")])

    hasBoard = 0
    hasCommittee = 0
    hasMeeting = 0
    hasDirectorCount = 0
    noData = 0
    errors = []

    for code in codes:
        try:
            result = buildBoardTimeSeries(code)
            if result is None:
                noData += 1
            else:
                if result["boardDf"] is not None:
                    hasBoard += 1
                    df = result["boardDf"]
                    if df["meetingCount"].drop_nulls().len() > 0:
                        hasMeeting += 1
                    if df["totalDirectors"].drop_nulls().len() > 0:
                        hasDirectorCount += 1
                if result["committeeDf"] is not None:
                    hasCommittee += 1
        except Exception as e:
            errors.append((code, str(e)[:100]))

    total = len(codes)
    print(f"  이사회 시계열: {hasBoard}/{total}")
    print(f"  이사수 데이터: {hasDirectorCount}/{total}")
    print(f"  개최횟수: {hasMeeting}/{total}")
    print(f"  위원회 구성: {hasCommittee}/{total}")
    print(f"  NoData: {noData}")
    print(f"  에러: {len(errors)}")

    if errors:
        for code, msg in errors[:10]:
            print(f"    {code}: {msg}")
