"""
실험 ID: 014
실험명: 사업보고서 범용 청커 프로토타입

목적:
- docs parquet의 section_content를 LLM 친화적 청크로 분할
- 대분류/소분류 중복 제거 (소분류 우선)
- 테이블 vs 텍스트 분리, 대형 테이블은 요약만
- 가/나/다 단위 세분화

가설:
1. 소분류 행이 있으면 소분류 단위로 청크하면 대분류 중복 제거 가능
2. 테이블 비율 90%+ 청크는 메타만 남기면 토큰 절약
3. 가/나/다 분할로 개별 주제 단위 청크 생성 가능

방법:
1. chunker 함수 구현
2. 삼성전자 전체 사업보고서에 적용
3. 청크 수, 크기 분포, 총 토큰 절약률 측정

결과 (실험 후 작성):

결론:

실험일: 2026-03-11
"""

import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\MSI\OneDrive\Desktop\sideProject\dartlab\src")

from dataclasses import dataclass, field

import polars as pl

from dartlab.core.dataLoader import loadData
from dartlab.core.reportSelector import selectReport

ROMAN_MAP = {
    "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5,
    "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10,
    "XI": 11, "XII": 12, "XIII": 13, "XIV": 14, "XV": 15,
}

SKIP_MAJORS = {3}

FINANCE_ENGINE_COVERED = {
    "요약재무정보", "연결재무제표", "연결재무제표 주석",
    "재무제표", "재무제표 주석", "배당에 관한 사항",
}


@dataclass
class Chunk:
    majorNum: int
    majorTitle: str
    subTitle: str
    path: str
    textContent: str
    tableCount: int
    tableRowCount: int
    tableSummary: str
    totalChars: int
    textChars: int
    kind: str


def parseMajorNum(title: str) -> int | None:
    m = re.match(r'^([IVXivx]+)\.\s', title.strip())
    if m:
        return ROMAN_MAP.get(m.group(1).upper())
    return None


def parseSubNum(title: str) -> int | None:
    m = re.match(r'^(\d+)\.\s', title.strip())
    if m:
        return int(m.group(1))
    return None


def splitByHeadings(text: str) -> list[tuple[str, str]]:
    """가/나/다 또는 (1)/(2) 단위로 텍스트 분할.

    Returns: [(heading, body), ...]
    """
    lines = text.split("\n")
    segments = []
    currentHeading = ""
    currentLines = []

    headingPat = re.compile(r'^([가-힣])\.\s+(.+)')

    for line in lines:
        m = headingPat.match(line.strip())
        if m:
            if currentLines:
                segments.append((currentHeading, "\n".join(currentLines)))
            currentHeading = line.strip()
            currentLines = []
        else:
            currentLines.append(line)

    if currentLines:
        segments.append((currentHeading, "\n".join(currentLines)))

    return segments


def separateTableAndText(content: str) -> tuple[str, list[str], int]:
    """content를 텍스트 부분과 테이블 부분으로 분리.

    Returns: (textOnly, tableHeaders, tableRowCount)
    """
    lines = content.split("\n")
    textLines = []
    tableHeaders = []
    tableRowCount = 0
    inTable = False
    headerCaptured = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|"):
            tableRowCount += 1
            if not inTable:
                inTable = True
                headerCaptured = False
            if not headerCaptured and "---" not in stripped:
                cells = [c.strip() for c in stripped.split("|") if c.strip()]
                if cells and cells != ["---"]:
                    tableHeaders.append(" | ".join(cells[:5]))
                    headerCaptured = True
        else:
            if inTable:
                inTable = False
                headerCaptured = False
            if stripped:
                textLines.append(line)

    return "\n".join(textLines), tableHeaders, tableRowCount


def chunkSection(content: str, majorNum: int, majorTitle: str,
                 subTitle: str) -> list[Chunk]:
    """단일 섹션을 청크로 분할."""
    if not content or not content.strip():
        return []

    path = f"{majorTitle}"
    if subTitle:
        path = f"{majorTitle} > {subTitle}"

    textOnly, tableHeaders, tableRowCount = separateTableAndText(content)
    totalChars = len(content)
    textChars = len(textOnly)
    tableRatio = 1 - (textChars / totalChars) if totalChars > 0 else 0

    tableSummary = ""
    if tableHeaders:
        tableSummary = f"테이블 {len(tableHeaders)}개, {tableRowCount}행"
        if tableHeaders:
            tableSummary += f" (컬럼: {tableHeaders[0][:60]})"

    if tableRatio > 0.9 and textChars < 500:
        return [Chunk(
            majorNum=majorNum, majorTitle=majorTitle, subTitle=subTitle,
            path=path, textContent=textOnly.strip() if textOnly.strip() else "(테이블 전용 섹션)",
            tableCount=len(tableHeaders), tableRowCount=tableRowCount,
            tableSummary=tableSummary, totalChars=totalChars,
            textChars=textChars, kind="table_only",
        )]

    segments = splitByHeadings(textOnly)

    if len(segments) <= 1 or all(not h for h, _ in segments):
        return [Chunk(
            majorNum=majorNum, majorTitle=majorTitle, subTitle=subTitle,
            path=path, textContent=textOnly.strip(),
            tableCount=len(tableHeaders), tableRowCount=tableRowCount,
            tableSummary=tableSummary, totalChars=totalChars,
            textChars=textChars,
            kind="text" if tableRatio < 0.5 else "mixed",
        )]

    chunks = []
    for heading, body in segments:
        segText, segTableH, segTableR = separateTableAndText(body)
        segPath = f"{path} > {heading}" if heading else path
        segTableSum = ""
        if segTableH:
            segTableSum = f"테이블 {len(segTableH)}개, {segTableR}행"

        chunks.append(Chunk(
            majorNum=majorNum, majorTitle=majorTitle, subTitle=subTitle,
            path=segPath, textContent=segText.strip(),
            tableCount=len(segTableH), tableRowCount=segTableR,
            tableSummary=segTableSum, totalChars=len(body),
            textChars=len(segText),
            kind="sub_chunk",
        ))

    return chunks


def chunkReport(stockCode: str, year: str = None) -> list[Chunk]:
    """사업보고서 전체를 청크로 분할."""
    df = loadData(stockCode)
    years = sorted(df["year"].unique().to_list(), reverse=True)
    contentCol = "section_content" if "section_content" in df.columns else "content"

    if not year:
        for y in years:
            report = selectReport(df, y, reportKind="annual")
            if report is not None:
                nonEmpty = report.filter(
                    pl.col(contentCol).is_not_null()
                    & (pl.col(contentCol).str.len_chars() > 0)
                )
                if len(nonEmpty) > 0:
                    year = y
                    break

    if not year:
        return []

    report = selectReport(df, year, reportKind="annual")
    if report is None:
        return []

    rows = report.sort("section_order").to_dicts()

    majorSections = {}
    currentMajor = None
    currentMajorNum = None

    for row in rows:
        title = row.get("section_title", "").strip()
        content = row.get(contentCol, "") or ""

        mNum = parseMajorNum(title)
        sNum = parseSubNum(title)

        if mNum is not None:
            currentMajor = title
            currentMajorNum = mNum

            if mNum not in majorSections:
                majorSections[mNum] = {
                    "title": title,
                    "content": content,
                    "subs": [],
                }
        elif sNum is not None and currentMajorNum is not None:
            majorSections[currentMajorNum]["subs"].append({
                "title": title,
                "content": content,
            })

    allChunks = []

    for mNum in sorted(majorSections.keys()):
        section = majorSections[mNum]
        majorTitle = section["title"]

        if mNum in SKIP_MAJORS:
            allChunks.append(Chunk(
                majorNum=mNum, majorTitle=majorTitle, subTitle="",
                path=majorTitle, textContent="(finance 엔진이 정량 처리 — 스킵)",
                tableCount=0, tableRowCount=0, tableSummary="",
                totalChars=len(section["content"]),
                textChars=0, kind="skipped",
            ))
            continue

        if section["subs"]:
            for sub in section["subs"]:
                subTitle = sub["title"]
                subContent = sub["content"]

                subClean = re.sub(r'^\d+\.\s*', '', subTitle).strip()
                if subClean in FINANCE_ENGINE_COVERED:
                    allChunks.append(Chunk(
                        majorNum=mNum, majorTitle=majorTitle, subTitle=subTitle,
                        path=f"{majorTitle} > {subTitle}",
                        textContent=f"(finance/report 엔진이 정량 처리 — 스킵)",
                        tableCount=0, tableRowCount=0, tableSummary="",
                        totalChars=len(subContent),
                        textChars=0, kind="skipped",
                    ))
                    continue

                chunks = chunkSection(subContent, mNum, majorTitle, subTitle)
                allChunks.extend(chunks)
        else:
            chunks = chunkSection(section["content"], mNum, majorTitle, "")
            allChunks.extend(chunks)

    return allChunks


def printChunkReport(chunks: list[Chunk], corpName: str, stockCode: str):
    """청크 분석 리포트 출력."""
    print(f"\n{'='*80}")
    print(f" {corpName} ({stockCode}) — 청킹 결과")
    print(f"{'='*80}")

    totalOriginal = sum(c.totalChars for c in chunks)
    totalText = sum(c.textChars for c in chunks if c.kind != "skipped")
    skippedChars = sum(c.totalChars for c in chunks if c.kind == "skipped")

    kindCounts = {}
    for c in chunks:
        kindCounts[c.kind] = kindCounts.get(c.kind, 0) + 1

    print(f"\n  총 청크: {len(chunks)}개")
    print(f"  원본 총 크기: {totalOriginal:,} chars")
    print(f"  텍스트 크기: {totalText:,} chars")
    print(f"  스킵 크기: {skippedChars:,} chars (finance/report 대체)")
    print(f"  절약률: {(1 - totalText/totalOriginal)*100:.1f}%" if totalOriginal > 0 else "")
    print(f"  종류별: {kindCounts}")

    print(f"\n{'─'*80}")
    print(f" {'#':>3} | {'종류':>12} | {'텍스트':>8} | {'원본':>8} | 경로")
    print(f"{'─'*80}")

    for i, c in enumerate(chunks, 1):
        kindLabel = {
            "text": "텍스트",
            "mixed": "혼합",
            "table_only": "테이블전용",
            "sub_chunk": "세분화",
            "skipped": "스킵",
        }.get(c.kind, c.kind)

        print(f" {i:3d} | {kindLabel:>12} | {c.textChars:>7,} | {c.totalChars:>7,} | {c.path[:55]}")

    print(f"\n\n--- LLM에 제공할 텍스트 청크 (상위 10개) ---\n")

    textChunks = [c for c in chunks if c.kind not in ("skipped", "table_only")]
    textChunks.sort(key=lambda c: c.textChars, reverse=True)

    for c in textChunks[:10]:
        print(f"\n{'─'*60}")
        print(f"  [{c.path[:60]}]")
        print(f"  텍스트: {c.textChars:,} chars, 테이블: {c.tableSummary or '없음'}")
        preview = c.textContent[:300].replace('\n', '\n  ')
        print(f"  {preview}")
        if len(c.textContent) > 300:
            print(f"  ... ({len(c.textContent) - 300:,} chars more)")


if __name__ == "__main__":
    stockCode = "005930"
    df = loadData(stockCode)
    corpName = df.row(0, named=True).get("corp_name", stockCode)

    chunks = chunkReport(stockCode)
    printChunkReport(chunks, corpName, stockCode)

    print("\n\n")
    print("="*80)
    print(" 다종목 비교")
    print("="*80)

    for code in ["000660", "005380", "000020"]:
        df2 = loadData(code)
        name2 = df2.row(0, named=True).get("corp_name", code)
        chunks2 = chunkReport(code)

        totalOrig = sum(c.totalChars for c in chunks2)
        totalText = sum(c.textChars for c in chunks2 if c.kind != "skipped")
        textChunks = [c for c in chunks2 if c.kind not in ("skipped", "table_only")]

        print(f"\n  {name2} ({code})")
        print(f"    청크: {len(chunks2)}개, 텍스트 청크: {len(textChunks)}개")
        print(f"    원본: {totalOrig:,} → 텍스트: {totalText:,} chars")
        print(f"    절약률: {(1 - totalText/totalOrig)*100:.1f}%" if totalOrig > 0 else "")
