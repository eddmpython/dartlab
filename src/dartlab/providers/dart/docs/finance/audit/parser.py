"""감사의견 섹션 파서."""

from __future__ import annotations

import re

import polars as pl

AUDIT_TITLE_KEYWORDS = [
    "외부감사에 관한 사항",
    "감사인의 감사의견",
    "회계감사인의 감사의견",
    "감사인(공인회계사)의 감사의견",
]


def findAuditSections(df: pl.DataFrame, year: str) -> list[str]:
    """사업보고서에서 감사 관련 섹션 내용 반환. 원본 우선, 기재정정 fallback."""
    report = df.filter(
        (pl.col("year") == year)
        & (pl.col("report_type").str.contains("사업보고서"))
        & (~pl.col("report_type").str.contains("기재정정|첨부"))
    )
    if report.height == 0:
        report = df.filter((pl.col("year") == year) & (pl.col("report_type").str.contains("사업보고서")))
        if report.height > 0:
            latest = report.sort("rcept_date", descending=True)
            latestType = latest["report_type"][0]
            report = report.filter(pl.col("report_type") == latestType)

    if report.height == 0:
        return []

    results = []
    for row in report.iter_rows(named=True):
        title = row["section_title"]
        for kw in AUDIT_TITLE_KEYWORDS:
            if kw in title:
                content = row["section_content"]
                if content:
                    results.append(content)
                break

    return results


def _isSeparator(cells: list[str]) -> bool:
    return all(re.match(r"^-+$|^:?-+:?$", c) for c in cells if c)


def extractTableBlocks(text: str) -> list[dict]:
    """마크다운 테이블 블록 추출.

    연속 파이프 라인을 수집한 뒤, 1셀 제목행 기준으로 서브블록 분리.
    """
    rawGroups: list[list[str]] = []
    currentLines: list[str] = []

    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            currentLines.append(stripped)
        else:
            if currentLines:
                rawGroups.append(currentLines[:])
                currentLines = []
    if currentLines:
        rawGroups.append(currentLines[:])

    blocks = []
    for rawLines in rawGroups:
        parsed = _splitAndParseBlocks(rawLines)
        blocks.extend(parsed)

    return blocks


def _splitAndParseBlocks(lines: list[str]) -> list[dict]:
    """연속 파이프 라인을 1셀 제목행 기준으로 서브블록 분리."""
    rows = []
    for line in lines:
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if _isSeparator(cells):
            continue
        rows.append(cells)

    if len(rows) < 2:
        return []

    subGroups: list[list[list[str]]] = []
    current: list[list[str]] = []

    for row in rows:
        nCells = len([c for c in row if c.strip()])
        if nCells <= 1 and current:
            hasHeader = any(len([c for c in r if c.strip()]) > 1 for r in current)
            if hasHeader:
                subGroups.append(current)
                current = []
        current.append(row)

    if current:
        subGroups.append(current)

    results = []
    for group in subGroups:
        block = _parseSubBlock(group)
        if block:
            results.append(block)

    return results


def _parseSubBlock(rows: list[list[str]]) -> dict | None:
    """서브블록 → 구조화된 블록."""
    meta: list[str] = []
    dataRows: list[list[str]] = []
    header = None
    subheader = None

    for row in rows:
        nCells = len([c for c in row if c.strip()])
        if nCells <= 1:
            if header is None:
                meta.append(row[0].strip() if row else "")
            continue

        if header is None:
            header = row
            continue

        if subheader is None and header:
            isSubheader = all(c.strip() in ("보수", "시간", "") for c in row)
            if isSubheader and "보수" in " ".join(row):
                subheader = row
                continue

        dataRows.append(row)

    if not header or not dataRows:
        return None

    return {
        "meta": meta,
        "header": header,
        "subheader": subheader,
        "rows": dataRows,
    }


def classifyBlock(block: dict) -> str:
    """블록 분류: opinion, fee, nonAuditFee, schedule, communication, unknown."""
    headerStr = " ".join(block["header"])
    metaStr = " ".join(block["meta"]) if block["meta"] else ""
    allText = metaStr + " " + headerStr

    row1Str = " ".join(block["rows"][0]) if block["rows"] else ""
    allText += " " + row1Str

    if "비감사" in allText:
        return "nonAuditFee"

    if "커뮤니케이션" in allText or "참석자" in headerStr or "논의 내용" in headerStr:
        return "communication"

    if "검토기간" in allText or "사전검토" in allText:
        return "schedule"
    if "일 정" in headerStr and ("구 분" in headerStr or "구분" in headerStr):
        return "schedule"

    if ("보수" in headerStr and "시간" in headerStr) or block["subheader"]:
        return "fee"
    if "감사계약" in allText and "보수" in allText:
        return "fee"

    if "감사의견" in headerStr:
        return "opinion"
    if "감사인" in headerStr and ("의견" in headerStr or "감사의견" in allText):
        return "opinion"
    if "사업연도" in headerStr and "감사인" in headerStr:
        if "적정" in " ".join(" ".join(r) for r in block["rows"][:3]):
            return "opinion"

    return "unknown"


def parseOpinionBlock(block: dict) -> list[dict]:
    """감사의견 블록 파싱."""
    header = block["header"]
    nCols = len(header)
    results = []
    currentPeriod = ""

    hasReportType = any("구분" in h for h in header)
    isWide = nCols >= 7

    for row in block["rows"]:
        while len(row) < max(nCols, 8):
            row.append("")

        firstCell = row[0].strip()
        if firstCell and "기" in firstCell:
            currentPeriod = firstCell

        if isWide and hasReportType:
            reportType = row[1].strip()
            auditor = row[2].strip()
            opinion = row[3].strip()
            goingConcern = row[5].strip() if len(row) > 5 else ""
            emphasis = row[6].strip() if len(row) > 6 else ""
            keyMatters = row[7].strip() if len(row) > 7 else ""
        elif isWide:
            reportType = ""
            auditor = row[1].strip()
            opinion = row[2].strip()
            goingConcern = ""
            emphasis = row[3].strip() if len(row) > 3 else ""
            keyMatters = row[4].strip() if len(row) > 4 else ""
        else:
            reportType = ""
            auditor = row[1].strip()
            opinion = row[2].strip()
            goingConcern = ""
            emphasis = row[3].strip() if len(row) > 3 else ""
            keyMatters = row[4].strip() if len(row) > 4 else ""

        if not _isAuditor(auditor):
            continue

        period = currentPeriod if currentPeriod else firstCell

        results.append(
            {
                "fiscalPeriod": period,
                "reportType": reportType,
                "auditor": auditor,
                "opinion": opinion,
                "goingConcern": goingConcern,
                "emphasis": emphasis,
                "keyAuditMatters": keyMatters,
            }
        )

    return results


def parseFeeBlock(block: dict) -> list[dict]:
    """감사보수 블록 파싱."""
    results = []
    currentPeriod = ""

    for row in block["rows"]:
        while len(row) < 7:
            row.append("")

        firstCell = row[0].strip()
        if firstCell and "기" in firstCell:
            currentPeriod = firstCell

        auditor = row[1].strip()
        content = row[2].strip()

        if not _isAuditor(auditor):
            continue

        contractFee = _parseNum(row[3])
        contractHours = _parseNum(row[4])
        actualFee = _parseNum(row[5])
        actualHours = _parseNum(row[6])

        results.append(
            {
                "fiscalPeriod": currentPeriod if currentPeriod else firstCell,
                "auditor": auditor,
                "content": content,
                "contractFee": contractFee,
                "contractHours": contractHours,
                "actualFee": actualFee,
                "actualHours": actualHours,
            }
        )

    return results


def _isAuditor(s: str) -> bool:
    if not s or s in ("-", ""):
        return False
    if "회계법인" in s or "감사법인" in s:
        return True
    if re.search(r"(EY|KPMG|PwC|PWC|Deloitte)", s, re.IGNORECASE):
        return True
    return False


def _parseNum(s: str) -> float | None:
    if not s:
        return None
    s = s.strip()
    if s in ("-", "", "해당사항없음", "해당사항 없음"):
        return None
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg = True
        s = s[1:-1]
    s = s.replace(",", "").replace(" ", "")
    try:
        v = float(s)
        return -v if neg else v
    except ValueError:
        return None


_FISCAL_NUM_RE = re.compile(r"제?(\d+)기")


def fiscalPeriodToYear(
    fiscalPeriod: str,
    baseYear: str,
    allPeriods: list[str] | None = None,
) -> str | None:
    """제N기(당기/전기) → 실제 연도 변환."""
    base = int(baseYear)

    if re.search(r"당기|당분기|당반기", fiscalPeriod):
        return str(base)
    if re.search(r"전전기", fiscalPeriod):
        return str(base - 2)
    if re.search(r"전기", fiscalPeriod):
        return str(base - 1)

    m = _FISCAL_NUM_RE.search(fiscalPeriod)
    if m and allPeriods:
        thisNum = int(m.group(1))
        maxNum = 0
        for p in allPeriods:
            pm = _FISCAL_NUM_RE.search(p)
            if pm:
                maxNum = max(maxNum, int(pm.group(1)))
        if maxNum > 0:
            diff = maxNum - thisNum
            return str(base - diff)

    return None


def normalizeOpinion(raw: str) -> str:
    """감사의견 정규화."""
    if not raw:
        return ""
    raw = raw.strip()
    if raw in ("적정의견", "적정"):
        return "적정"
    if "한정" in raw:
        return "한정"
    if "부적정" in raw:
        return "부적정"
    if "의견거절" in raw:
        return "의견거절"
    return raw


def dedup(items: list[dict], keys: list[str]) -> list[dict]:
    """중복 제거 (첫 출현 유지)."""
    seen: set[tuple] = set()
    result = []
    for item in items:
        k = tuple(item.get(key, "") for key in keys)
        if k not in seen:
            seen.add(k)
            result.append(item)
    return result
