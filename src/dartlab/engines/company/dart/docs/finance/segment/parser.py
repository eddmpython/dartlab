"""부문별 보고 테이블 파싱.

마크다운 테이블에서 세그먼트별 매출/영업이익 데이터를 추출한다.
멀티행 헤더 병합(colspan 복원), 메타 컬럼 필터링, 테이블 유형 분류를 포함.
"""

import re

from dartlab.core.tableParser import parseAmount
from dartlab.engines.company.dart.docs.finance.segment.types import SegmentTable

# ── 메타 컬럼 패턴 (부문명이 아닌 컬럼) ──────────────────────

_META_PATTERNS = [
    r"^구\s*분$",
    r"^계\b",
    r"^합계\b",
    r"^소계\b",
    r"조정후금액",
    r"조정후\s*금액",
    r"내부거래",
    r"^기타$",
    r"총계",
    r"용역\s*합계",
    r"조정사항",
    r"지역\s*합계",
]


def _isMetaColumn(name: str) -> bool:
    """부문명이 아닌 메타 컬럼인지 판별."""
    s = re.sub(r"\(\*\d*\)", "", name).strip()
    for p in _META_PATTERNS:
        if re.search(p, s):
            return True
    return False


# ── 행 분류 ──────────────────────────────────────────────────


def isDataRow(cells: list[str]) -> bool:
    """셀 중 숫자가 1개 이상이면 데이터 행."""
    numCount = 0
    for c in cells[1:]:
        s = c.strip().replace(",", "").replace("(", "").replace(")", "")
        if s and s.replace("-", "").replace(".", "").isdigit():
            numCount += 1
    return numCount >= 1


def isHeaderRow(cells: list[str]) -> bool:
    """부문명이 포함된 헤더 행 판별."""
    nonEmpty = [c.strip() for c in cells if c.strip()]
    if len(nonEmpty) < 2:
        return False
    for c in nonEmpty:
        s = c.replace(",", "").replace("(", "").replace(")", "").replace("-", "")
        if s.isdigit():
            return False
    return True


# ── 헤더 병합 ────────────────────────────────────────────────


def mergeHeaders(headers: list[list[str]]) -> list[str]:
    """멀티행 헤더를 병합하여 전체 컬럼 배열 반환.

    헤더 수에 따라 다른 전략:

    1행: 그대로 반환.

    2행 (2022↓ colspan): 상위 유지 + 하위 서브세그먼트 삽입.
      HDR1의 첫 번째 비어있지않은 셀은 소계 라벨 (계(*)) → 스킵.
      나머지 (반도체, DP)를 HDR0의 빈 위치에 삽입.

    3행+ (2024+): 하위 우선 위치 병합.
      각 위치에서 마지막 비어있지 않은 값을 사용.
    """
    if len(headers) == 1:
        return list(headers[0])

    maxLen = max(len(h) for h in headers)
    padded = [h + [""] * (maxLen - len(h)) for h in headers]

    if len(headers) >= 3:
        merged = []
        for col in range(maxLen):
            cell = ""
            for h in padded:
                if h[col]:
                    cell = h[col]
            merged.append(cell)
        return merged

    # 2행: 상위 유지 + 하위 서브세그먼트 삽입
    hdr0 = list(padded[0])
    hdr1 = padded[1]

    nonEmpty = [cell for cell in hdr1 if cell]
    if len(nonEmpty) <= 1:
        return hdr0
    subLabels = nonEmpty[1:]

    emptyIdx = [i for i, cell in enumerate(hdr0) if not cell]
    for i, idx in enumerate(emptyIdx):
        if i < len(subLabels):
            hdr0[idx] = subLabels[i]

    return hdr0


# ── 테이블 유형 분류 ─────────────────────────────────────────


def classifyTable(columns: list[str]) -> str:
    """컬럼명으로 테이블 유형 분류."""
    colStr = " ".join(columns)
    if any(kw in colStr for kw in ["국내", "미주", "유럽", "본사 소재지"]):
        return "region"
    if any(kw in colStr for kw in ["영상", "무선", "메모리", "스마트", "TV"]):
        return "product"
    return "segment"


# ── 메인 파싱 ────────────────────────────────────────────────


def parseSegmentTables(text: str) -> list[SegmentTable]:
    """부문별 보고 전체 텍스트 → 파싱된 SegmentTable 목록."""
    lines = text.split("\n")
    results: list[SegmentTable] = []

    currentPeriod = ""
    pendingHeaders: list[list[str]] = []
    currentColumns: list[str] = []
    currentRows: dict[str, list[float | None]] = {}
    rowOrder: list[str] = []
    hasData = False

    def flush():
        nonlocal currentColumns, currentRows, rowOrder, pendingHeaders, hasData
        if currentColumns and currentRows:
            keepIdx = [i for i, c in enumerate(currentColumns) if c and not _isMetaColumn(c)]
            cleanCols = [currentColumns[i] for i in keepIdx]

            cleanCols = [re.sub(r"\(\*\d*\)", "", c).strip() for c in cleanCols]
            cleanCols = [re.sub(r"(\S)(부문)", r"\1 \2", c) for c in cleanCols]

            cleanRows: dict[str, list[float | None]] = {}
            nCols = len(cleanCols)
            nAllCols = len(currentColumns)
            aligned = True
            for name in rowOrder:
                vals = currentRows[name]
                if len(vals) == nAllCols:
                    cleanRows[name] = [vals[i] for i in keepIdx]
                elif len(vals) >= nCols and len(vals) - nCols <= 2:
                    cleanRows[name] = vals[:nCols]
                else:
                    cleanRows[name] = vals
                    aligned = False

            tableType = classifyTable(cleanCols)
            results.append(
                SegmentTable(
                    period=currentPeriod,
                    tableType=tableType,
                    columns=cleanCols,
                    rows=cleanRows,
                    order=list(rowOrder),
                    aligned=aligned,
                )
            )
        currentColumns = []
        currentRows = {}
        rowOrder = []
        pendingHeaders = []
        hasData = False

    for line in lines:
        s = line.strip()

        if not s.startswith("|"):
            if not s:
                continue
            if "당기" in s or "전기" in s:
                flush()
                currentPeriod = "당기" if "당기" in s else "전기"
            elif hasData:
                flush()
            continue

        cells = [c.strip() for c in s.split("|")]
        if cells and cells[0] == "":
            cells = cells[1:]
        if cells and cells[-1] == "":
            cells = cells[:-1]

        if all(re.match(r"^-+$", c) for c in cells if c):
            continue

        nonEmpty = [c for c in cells if c]
        if not nonEmpty:
            flush()
            continue

        if len(nonEmpty) == 1 and "단위" in nonEmpty[0]:
            continue

        if len(nonEmpty) <= 2 and any("당기" in c or "전기" in c for c in nonEmpty):
            flush()
            for c in nonEmpty:
                if "당기" in c:
                    currentPeriod = "당기"
                elif "전기" in c:
                    currentPeriod = "전기"
            continue

        if len(nonEmpty) == 1 and len(nonEmpty[0]) > 20:
            continue

        if isDataRow(cells):
            name = cells[0].strip()
            if not name:
                continue
            cleanName = re.sub(r"\(\*\d*\)", "", name).strip()
            if not cleanName or cleanName.startswith("("):
                continue

            if not hasData and pendingHeaders:
                merged = mergeHeaders(pendingHeaders)
                currentColumns = merged[1:] if merged else []
                hasData = True

            vals = [parseAmount(c) for c in cells[1:]]
            currentRows[cleanName] = vals
            rowOrder.append(cleanName)
        elif isHeaderRow(cells):
            if not hasData:
                pendingHeaders.append(cells)

    flush()
    return results
