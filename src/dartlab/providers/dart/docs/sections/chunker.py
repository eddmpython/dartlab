"""사업보고서 섹션 청킹 로직.

docs parquet의 section_content를 LLM 친화적 청크로 분할한다.

전략:
- 소분류 행이 있으면 소분류 단위로 분할 (대분류 중복 제거)
- 가/나/다 패턴으로 세분화
- 테이블 비율 90%+ 섹션은 메타만 보존
- III. 재무에 관한 사항은 finance 엔진이 대체하므로 스킵
- MAX_CHUNK_CHARS 초과 텍스트는 문단 단위로 추가 분할
"""

from __future__ import annotations

import re

from dartlab.providers.dart.docs.sections.types import SectionChunk

ROMAN_MAP = {
    "I": 1,
    "II": 2,
    "III": 3,
    "IV": 4,
    "V": 5,
    "VI": 6,
    "VII": 7,
    "VIII": 8,
    "IX": 9,
    "X": 10,
    "XI": 11,
    "XII": 12,
    "XIII": 13,
    "XIV": 14,
    "XV": 15,
}

SKIP_MAJORS = {3}

FINANCE_ENGINE_COVERED = {
    "요약재무정보",
    "연결재무제표",
    "연결재무제표 주석",
    "재무제표",
    "재무제표 주석",
    "배당에 관한 사항",
}

_RE_KOREAN_HEADING = re.compile(r"^([가-힣])\.\s+(.+)")

MAX_CHUNK_CHARS = 4000


def parseMajorNum(title: str) -> int | None:
    """section_title에서 대분류 로마 숫자 추출."""
    m = re.match(r"^([IVXivx]+)\.\s", title.strip())
    if m:
        return ROMAN_MAP.get(m.group(1).upper())
    return None


def parseSubNum(title: str) -> int | None:
    """section_title에서 소분류 아라비아 숫자 추출."""
    m = re.match(r"^(\d+)\.\s", title.strip())
    if m:
        return int(m.group(1))
    return None


def splitByHeadings(text: str) -> list[tuple[str, str]]:
    """가/나/다 단위로 텍스트 분할."""
    lines = text.split("\n")
    segments: list[tuple[str, str]] = []
    currentHeading = ""
    currentLines: list[str] = []

    for line in lines:
        m = _RE_KOREAN_HEADING.match(line.strip())
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
    """content를 텍스트 / 테이블로 분리.

    Returns:
        (textOnly, tableHeaders, tableRowCount)
    """
    lines = content.split("\n")
    textLines: list[str] = []
    tableHeaders: list[str] = []
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


_RE_SUBHEADING = re.compile(r"^(?:●|▶|◆|■|□|○|\(\d+\)|\d+\)\s|\[\S+[^\]]*\]$|<주요|<자회사)")


def _splitLargeText(text: str, maxChars: int = MAX_CHUNK_CHARS) -> list[str]:
    """대형 텍스트를 maxChars 이내 파트로 분할.

    분할 우선순위:
    1. 빈 줄 (문단)
    2. 소제목 패턴 (●, ▶, (1), (2) 등)
    3. 줄 단위 병합
    """
    text = text.strip()
    if len(text) <= maxChars:
        return [text]

    paragraphs = re.split(r"\n\s*\n", text)
    if len(paragraphs) > 1:
        return _mergeSegments(paragraphs, maxChars, "\n\n")

    lines = text.split("\n")
    segments: list[str] = []
    buf: list[str] = []

    for line in lines:
        if _RE_SUBHEADING.match(line.strip()) and buf:
            segments.append("\n".join(buf))
            buf = [line]
        else:
            buf.append(line)
    if buf:
        segments.append("\n".join(buf))

    if len(segments) > 1:
        return _mergeSegments(segments, maxChars, "\n")

    return _mergeSegments(lines, maxChars, "\n")


def _mergeSegments(
    segments: list[str],
    maxChars: int,
    sep: str,
) -> list[str]:
    """세그먼트들을 maxChars 이내로 병합."""
    result: list[str] = []
    buf: list[str] = []
    bufLen = 0
    sepLen = len(sep)

    for seg in segments:
        seg = seg.strip()
        if not seg:
            continue
        segLen = len(seg)

        if bufLen + segLen + sepLen > maxChars and buf:
            result.append(sep.join(buf))
            buf = [seg]
            bufLen = segLen
        else:
            buf.append(seg)
            bufLen += segLen + sepLen

    if buf:
        result.append(sep.join(buf))

    return result if result else [sep.join(segments)]


def _splitLargeChunk(chunk: SectionChunk) -> list[SectionChunk]:
    """MAX_CHUNK_CHARS 초과 청크를 문단/소제목/줄 단위로 분할."""
    if chunk.textChars <= MAX_CHUNK_CHARS:
        return [chunk]

    parts = _splitLargeText(chunk.textContent, MAX_CHUNK_CHARS)
    if len(parts) <= 1:
        return [chunk]

    chunks: list[SectionChunk] = []
    for i, part in enumerate(parts, 1):
        chunks.append(
            SectionChunk(
                majorNum=chunk.majorNum,
                majorTitle=chunk.majorTitle,
                subTitle=chunk.subTitle,
                path=f"{chunk.path} [{i}/{len(parts)}]",
                textContent=part,
                tableCount=0,
                tableRowCount=0,
                tableSummary=chunk.tableSummary if i == 1 else "",
                totalChars=len(part),
                textChars=len(part),
                kind="split",
            )
        )
    return chunks


def chunkSection(
    content: str,
    majorNum: int,
    majorTitle: str,
    subTitle: str,
) -> list[SectionChunk]:
    """단일 섹션을 청크로 분할."""
    if not content or not content.strip():
        return []

    path = majorTitle
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
        return [
            SectionChunk(
                majorNum=majorNum,
                majorTitle=majorTitle,
                subTitle=subTitle,
                path=path,
                textContent=textOnly.strip() if textOnly.strip() else "(테이블 전용 섹션)",
                tableCount=len(tableHeaders),
                tableRowCount=tableRowCount,
                tableSummary=tableSummary,
                totalChars=totalChars,
                textChars=textChars,
                kind="table_only",
            )
        ]

    segments = splitByHeadings(textOnly)

    if len(segments) <= 1 or all(not h for h, _ in segments):
        return [
            SectionChunk(
                majorNum=majorNum,
                majorTitle=majorTitle,
                subTitle=subTitle,
                path=path,
                textContent=textOnly.strip(),
                tableCount=len(tableHeaders),
                tableRowCount=tableRowCount,
                tableSummary=tableSummary,
                totalChars=totalChars,
                textChars=textChars,
                kind="text" if tableRatio < 0.5 else "mixed",
            )
        ]

    chunks: list[SectionChunk] = []
    for heading, body in segments:
        segText, segTableH, segTableR = separateTableAndText(body)
        segPath = f"{path} > {heading}" if heading else path
        segTableSum = ""
        if segTableH:
            segTableSum = f"테이블 {len(segTableH)}개, {segTableR}행"

        chunks.append(
            SectionChunk(
                majorNum=majorNum,
                majorTitle=majorTitle,
                subTitle=subTitle,
                path=segPath,
                textContent=segText.strip(),
                tableCount=len(segTableH),
                tableRowCount=segTableR,
                tableSummary=segTableSum,
                totalChars=len(body),
                textChars=len(segText),
                kind="sub_chunk",
            )
        )

    return chunks


def chunkRows(rows: list[dict], contentCol: str) -> list[SectionChunk]:
    """section_order로 정렬된 행 목록을 청크로 변환.

    Args:
        rows: selectReport 결과의 dict 목록 (section_title, section_content 포함)
        contentCol: content 컬럼명
    """
    majorSections: dict[int, dict] = {}
    currentMajorNum: int | None = None

    for row in rows:
        title = row.get("section_title", "").strip()
        content = row.get(contentCol, "") or ""

        mNum = parseMajorNum(title)
        sNum = parseSubNum(title)

        if mNum is not None:
            currentMajorNum = mNum
            if mNum not in majorSections:
                majorSections[mNum] = {
                    "title": title,
                    "content": content,
                    "subs": [],
                }
        elif sNum is not None and currentMajorNum is not None:
            majorSections[currentMajorNum]["subs"].append(
                {
                    "title": title,
                    "content": content,
                }
            )

    allChunks: list[SectionChunk] = []

    for mNum in sorted(majorSections.keys()):
        section = majorSections[mNum]
        majorTitle = section["title"]

        if mNum in SKIP_MAJORS:
            allChunks.append(
                SectionChunk(
                    majorNum=mNum,
                    majorTitle=majorTitle,
                    subTitle="",
                    path=majorTitle,
                    textContent="(finance 엔진이 정량 처리)",
                    tableCount=0,
                    tableRowCount=0,
                    tableSummary="",
                    totalChars=len(section["content"]),
                    textChars=0,
                    kind="skipped",
                )
            )
            continue

        if section["subs"]:
            for sub in section["subs"]:
                subTitle = sub["title"]
                subContent = sub["content"]

                subClean = re.sub(r"^\d+\.\s*", "", subTitle).strip()
                if subClean in FINANCE_ENGINE_COVERED:
                    allChunks.append(
                        SectionChunk(
                            majorNum=mNum,
                            majorTitle=majorTitle,
                            subTitle=subTitle,
                            path=f"{majorTitle} > {subTitle}",
                            textContent="(finance/report 엔진이 정량 처리)",
                            tableCount=0,
                            tableRowCount=0,
                            tableSummary="",
                            totalChars=len(subContent),
                            textChars=0,
                            kind="skipped",
                        )
                    )
                    continue

                allChunks.extend(chunkSection(subContent, mNum, majorTitle, subTitle))
        else:
            allChunks.extend(chunkSection(section["content"], mNum, majorTitle, ""))

    finalChunks: list[SectionChunk] = []
    for chunk in allChunks:
        finalChunks.extend(_splitLargeChunk(chunk))
    return finalChunks
