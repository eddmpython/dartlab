"""연결재무제표 주석에서 부문별 보고 영역 추출."""

import re

import polars as pl


def extractNotesContent(report: pl.DataFrame) -> list[str]:
    """보고서에서 연결재무제표 주석 섹션 내용 추출."""
    section = report.filter(
        pl.col("section_title").str.contains("연결재무제표")
        & pl.col("section_title").str.contains("주석")
    )
    if section.height == 0:
        return []
    return section["section_content"].to_list()


def findSegmentSection(contents: list[str]) -> str | None:
    """주석에서 '부문별 보고' 영역 추출.

    번호 매긴 섹션(예: "29. 부문별 보고")에서 다음 번호 섹션까지의 텍스트를 반환.
    """
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
