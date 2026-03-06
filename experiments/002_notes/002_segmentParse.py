"""부문별 보고 파싱 실험.

주석 29번에서 세그먼트별 매출/영업이익 테이블을 파싱한다.

연도별 포맷 차이:
  ~2023: (1) 당기 / (2) 전기 로 분리, 단일행 헤더
  2024~: 마크다운 멀티라인 헤더 (3행), 부문명이 3번째 헤더행에 있음
"""

import re
from pathlib import Path

import polars as pl

DATA_DIR = Path("data/docsData")
OUT = Path("experiments/002_notes/output")
OUT.mkdir(exist_ok=True)


# ── 주석에서 부문별 보고 추출 ──────────────────────────────────


def extractNotes(df: pl.DataFrame, year: str) -> list[str]:
    """해당 연도 연결재무제표 주석 content 목록."""
    notes = df.filter(
        (pl.col("year") == year)
        & pl.col("section_title").str.contains("연결재무제표")
        & pl.col("section_title").str.contains("주석")
    )
    return notes["section_content"].to_list()


def findSegmentSection(contents: list[str]) -> str | None:
    """주석에서 '부문별 보고' 영역 추출."""
    for content in contents:
        lines = content.split("\n")
        startIdx = None
        endIdx = None

        for i, line in enumerate(lines):
            s = line.strip()
            if s.startswith("|"):
                continue
            m = re.match(r"^(\d{1,2})\.\s+(.+)", s)
            if m:
                title = m.group(2).strip()
                if "부문" in title:
                    startIdx = i
                elif startIdx is not None and endIdx is None:
                    endIdx = i
                    break

        if startIdx is not None:
            if endIdx is None:
                endIdx = len(lines)
            return "\n".join(lines[startIdx:endIdx])
    return None


# ── 금액 파싱 ──────────────────────────────────────────────────


def parseAmount(text: str) -> float | None:
    """금액 문자열 → float. '(1,234)' → -1234, '-' → None."""
    s = text.strip().replace("\xa0", "").replace(" ", "")
    if not s or s == "-":
        return None
    if s == "0":
        return 0

    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1]

    s = s.replace(",", "")
    try:
        val = float(s)
        return -val if negative else val
    except ValueError:
        return None


def isDataRow(cells: list[str]) -> bool:
    """셀 중 숫자가 1개 이상이면 데이터 행."""
    numCount = 0
    for c in cells[1:]:  # 첫 셀은 계정명
        s = c.strip().replace(",", "").replace("(", "").replace(")", "")
        if s and s.replace("-", "").replace(".", "").isdigit():
            numCount += 1
    return numCount >= 1


def isHeaderRow(cells: list[str]) -> bool:
    """부문명이 포함된 헤더 행 판별."""
    nonEmpty = [c.strip() for c in cells if c.strip()]
    if len(nonEmpty) < 2:
        return False
    # 숫자가 없고, 텍스트가 2개 이상이면 헤더
    for c in nonEmpty:
        s = c.replace(",", "").replace("(", "").replace(")", "").replace("-", "")
        if s.isdigit():
            return False
    return True


# ── 테이블 블록 파싱 ──────────────────────────────────────────


def mergeHeaders(headers: list[list[str]]) -> list[str]:
    """멀티행 헤더를 병합하여 전체 컬럼 배열 반환.

    헤더 수에 따라 다른 전략:

    1행: 그대로 반환.

    2행 (2022↓ colspan): 상위 유지 + 하위 서브세그먼트 삽입.
      HDR1의 첫 번째 비어있지않은 셀은 소계 라벨 (계(*)) → 스킵.
      나머지 (반도체, DP)를 HDR0의 빈 위치에 삽입.
      예) HDR0: [구 분, CE, IM, DS, '', '', Harman, 계(*)]
          HDR1: [계(*), 반도체, DP, '', ...]
          결과: [구 분, CE, IM, DS, 반도체, DP, Harman, 계(*)]

    3행+ (2024+): 하위 우선 위치 병합.
      각 위치에서 마지막 비어있지 않은 값을 사용.
      예) HDR0: ['', 기업전체총계, '', '', '', '', 합계]
          HDR1: ['', 영업부문, '', '', '', 내부거래, '']
          HDR2: ['', DX, DS, SDC, Harman, '', '']
          결과: ['', DX, DS, SDC, Harman, 내부거래, 합계]
    """
    if len(headers) == 1:
        return list(headers[0])

    maxLen = max(len(h) for h in headers)
    padded = [h + [""] * (maxLen - len(h)) for h in headers]

    if len(headers) >= 3:
        # 하위 우선: 각 위치에서 마지막 비어있지 않은 값
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

    # HDR1의 비어있지 않은 셀 중 첫 번째(소계 라벨) 스킵
    nonEmpty = [cell for cell in hdr1 if cell]
    if len(nonEmpty) <= 1:
        return hdr0
    subLabels = nonEmpty[1:]

    # HDR0의 빈 위치에 삽입
    emptyIdx = [i for i, cell in enumerate(hdr0) if not cell]
    for i, idx in enumerate(emptyIdx):
        if i < len(subLabels):
            hdr0[idx] = subLabels[i]

    return hdr0


def parseSegmentTables(text: str) -> list[dict]:
    """부문별 보고 전체 텍스트 → 파싱된 테이블 목록.

    Returns:
        [{"period": "당기|전기", "type": "segment|product|region",
          "columns": [...], "rows": {계정명: [값, ...]}}, ...]
    """
    lines = text.split("\n")
    results = []

    currentPeriod = ""
    pendingHeaders: list[list[str]] = []
    currentColumns: list[str] = []
    currentRows: dict[str, list[float | None]] = {}
    rowOrder: list[str] = []
    hasData = False

    # 메타 컬럼 (부문명이 아닌 컬럼) 판별
    META_PATTERNS = [
        r"^구\s*분$", r"^계\b", r"^합계\b", r"^소계\b",
        r"조정후금액", r"조정후\s*금액", r"내부거래", r"^기타$",
        r"총계", r"용역\s*합계", r"조정사항", r"지역\s*합계",
    ]

    def isMetaColumn(name: str) -> bool:
        """부문명이 아닌 메타 컬럼인지 판별."""
        s = re.sub(r"\(\*\d*\)", "", name).strip()
        for p in META_PATTERNS:
            if re.search(p, s):
                return True
        return False

    def flush():
        nonlocal currentColumns, currentRows, rowOrder, pendingHeaders, hasData
        if currentColumns and currentRows:
            # 의미 있는 컬럼 인덱스 식별 (빈 셀 + 메타 컬럼 제외)
            keepIdx = [
                i for i, c in enumerate(currentColumns)
                if c and not isMetaColumn(c)
            ]
            cleanCols = [currentColumns[i] for i in keepIdx]

            # 컬럼명 정규화: 주석 마크 제거, 부문명 공백 통일
            cleanCols = [re.sub(r"\(\*\d*\)", "", c).strip() for c in cleanCols]
            cleanCols = [re.sub(r"(\S)(부문)", r"\1 \2", c) for c in cleanCols]

            # 값 배열 필터링
            cleanRows = {}
            nCols = len(cleanCols)
            nAllCols = len(currentColumns)
            aligned = True
            for name in rowOrder:
                vals = currentRows[name]
                if len(vals) == nAllCols:
                    # 전체 컬럼과 같은 길이 → keepIdx로 필터링
                    cleanRows[name] = [vals[i] for i in keepIdx]
                elif len(vals) >= nCols and len(vals) - nCols <= 2:
                    # 약간 초과 → 앞에서 nCols개만
                    cleanRows[name] = vals[:nCols]
                else:
                    cleanRows[name] = vals
                    aligned = False

            tableType = classifyTable(cleanCols)
            results.append({
                "period": currentPeriod,
                "type": tableType,
                "columns": cleanCols,
                "rows": cleanRows,
                "order": list(rowOrder),
                "aligned": aligned,
            })
        currentColumns = []
        currentRows = {}
        rowOrder = []
        pendingHeaders = []
        hasData = False

    for line in lines:
        s = line.strip()

        # 비테이블 행에서 당기/전기 감지 또는 블록 구분
        if not s.startswith("|"):
            if not s:
                continue
            # "당기" 또는 "전기"가 포함된 비테이블 행 → flush + period 설정
            if "당기" in s or "전기" in s:
                flush()
                currentPeriod = "당기" if "당기" in s else "전기"
            # 그 외 텍스트 행(제목 등) → 현재 테이블 블록 종료
            elif hasData:
                flush()
            continue

        # 테이블 행 처리
        cells = [c.strip() for c in s.split("|")]
        if cells and cells[0] == "":
            cells = cells[1:]
        if cells and cells[-1] == "":
            cells = cells[:-1]

        # 구분선 스킵
        if all(re.match(r"^-+$", c) for c in cells if c):
            continue

        # 빈 행 = 블록 구분
        nonEmpty = [c for c in cells if c]
        if not nonEmpty:
            flush()
            continue

        # 단위 행
        if len(nonEmpty) == 1 and "단위" in nonEmpty[0]:
            continue

        # 당기/전기 라벨 행 (테이블 내부)
        if len(nonEmpty) <= 2 and any("당기" in c or "전기" in c for c in nonEmpty):
            flush()
            for c in nonEmpty:
                if "당기" in c:
                    currentPeriod = "당기"
                elif "전기" in c:
                    currentPeriod = "전기"
            continue

        # 기술/설명 행 스킵 (단일 셀, 긴 텍스트)
        if len(nonEmpty) == 1 and len(nonEmpty[0]) > 20:
            continue

        # 헤더 행 vs 데이터 행
        if isDataRow(cells):
            name = cells[0].strip()
            if not name:
                continue
            cleanName = re.sub(r"\(\*\d*\)", "", name).strip()
            if not cleanName or cleanName.startswith("("):
                continue

            # 첫 데이터 행 → pendingHeaders를 병합하여 columns 확정
            if not hasData and pendingHeaders:
                merged = mergeHeaders(pendingHeaders)
                # 첫 셀(계정명 위치) 제외, 빈 셀 유지 (위치 매핑용)
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


def classifyTable(columns: list[str]) -> str:
    """컬럼명으로 테이블 유형 분류."""
    colStr = " ".join(columns)
    if any(kw in colStr for kw in ["국내", "미주", "유럽", "본사 소재지"]):
        return "region"
    if any(kw in colStr for kw in ["영상", "무선", "메모리", "스마트", "TV"]):
        return "product"
    return "segment"


# ── 메인 ──────────────────────────────────────────────────────


def main():
    path = DATA_DIR / "005930.parquet"
    df = pl.read_parquet(str(path))
    years = sorted(df["year"].unique().to_list(), reverse=True)

    out = []

    def p(s=""):
        out.append(s)

    p("=" * 70)
    p("삼성전자 부문별 보고 파싱 결과")
    p("=" * 70)

    for year in years[:10]:
        contents = extractNotes(df, year)
        if not contents:
            continue

        segment = findSegmentSection(contents)
        if segment is None:
            continue

        tables = parseSegmentTables(segment)

        p(f"\n{'=' * 50}")
        p(f"  {year}: {len(tables)}개 테이블")
        p(f"{'=' * 50}")

        for t in tables:
            flag = "" if t["aligned"] else " [MISALIGNED]"
            p(f"\n  [{t['period']}] {t['type']}{flag}")
            p(f"  columns({len(t['columns'])}): {t['columns']}")
            for name in t["order"]:
                vals = t["rows"][name]
                p(f"    {name}({len(vals)}): {vals}")

    # 매출액 시계열 구성 시도
    p("\n\n" + "=" * 70)
    p("사업부문별 매출액 시계열 (당기 기준)")
    p("=" * 70)

    segmentRevenue: dict[str, dict[str, float | None]] = {}

    for year in years[:10]:
        contents = extractNotes(df, year)
        if not contents:
            continue
        segment = findSegmentSection(contents)
        if segment is None:
            continue

        tables = parseSegmentTables(segment)
        for t in tables:
            if t["type"] == "segment" and t["period"] == "당기" and t["aligned"]:
                # 매출액/영업수익 행 찾기
                for name in t["order"]:
                    if ("매출" in name or "영업수익" in name) and "내부" not in name:
                        for i, col in enumerate(t["columns"]):
                            val = t["rows"][name][i] if i < len(t["rows"][name]) else None
                            if col not in segmentRevenue:
                                segmentRevenue[col] = {}
                            segmentRevenue[col][year] = val
                        break
                break

    for segName, yearVals in segmentRevenue.items():
        p(f"\n  {segName}:")
        for year in sorted(yearVals.keys(), reverse=True):
            val = yearVals[year]
            if val is not None:
                p(f"    {year}: {val:>15,.0f}")

    outPath = OUT / "segment_parse_v2.txt"
    outPath.write_text("\n".join(out), encoding="utf-8")
    print(f"결과 저장: {outPath}")
    print(f"총 {len(out)}줄")


if __name__ == "__main__":
    main()
