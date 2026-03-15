"""연결재무제표 주석 섹션 추출 공통 유틸."""

import re

import polars as pl


def extractNotesContent(report: pl.DataFrame) -> list[str]:
    """보고서에서 연결재무제표 주석 섹션 내용 추출."""
    section = report.filter(
        pl.col("section_title").str.contains("연결재무제표") & pl.col("section_title").str.contains("주석")
    )
    if section.height == 0:
        return []
    return section["section_content"].to_list()


def findNumberedSection(contents: list[str], keyword: str) -> str | None:
    """번호 매긴 섹션에서 keyword 포함 섹션 텍스트."""
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
                if keyword in title:
                    startIdx = i
                elif startIdx is not None and endIdx is None:
                    endIdx = i
                    break
        if startIdx is not None:
            if endIdx is None:
                endIdx = len(lines)
            return "\n".join(lines[startIdx:endIdx])
    return None
