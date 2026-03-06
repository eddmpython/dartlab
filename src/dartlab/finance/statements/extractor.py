"""연결재무제표 섹션에서 개별 제표 영역을 분리."""

import re

import polars as pl

_STATEMENT_PATTERNS = {
    "BS": r"재무상태표",
    "PNL": r"손익계산서",
    "CI": r"포괄손익",
    "SCE": r"자본변동표",
    "CF": r"현금흐름표",
}


def extractConsolidatedContent(report: pl.DataFrame) -> str | None:
    """보고서에서 연결재무제표 섹션 내용을 추출."""
    section = report.filter(pl.col("section_title").str.contains("연결재무제표"))
    if section.height == 0:
        return None
    # "주석" 제외
    section = section.filter(~pl.col("section_title").str.contains("주석"))
    if section.height == 0:
        return None
    return section["section_content"][0]


def splitStatements(content: str) -> dict[str, str]:
    """연결재무제표 전체 내용을 개별 제표별 텍스트로 분리.

    Returns:
        {"BS": "...", "PNL": "...", "CI": "...", "SCE": "...", "CF": "..."}
    """
    lines = content.split("\n")

    # 헤더 위치 찾기
    # 2024+: "2-1. 연결 재무상태표" (독립 행)
    # ~2023: "| 연결 재무상태표 |" (테이블 행, 셀 1개)
    headers: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        s = line.strip()
        if not s or len(s) >= 80:
            continue

        # 테이블 행인 경우: 셀이 1개이고 키워드 포함 시에만 헤더로 인식
        if s.startswith("|"):
            cells = [c.strip() for c in s.split("|") if c.strip()]
            if len(cells) != 1:
                continue
            s = cells[0]

        for key, pattern in _STATEMENT_PATTERNS.items():
            if re.search(pattern, s):
                headers.append((i, key))
                break

    # 중복 키 처리: 뒤에 나온 게 우선 (포괄손익 vs 손익계산서 구분)
    seen: dict[str, int] = {}
    uniqueHeaders: list[tuple[int, str]] = []
    for idx, key in headers:
        if key in seen:
            uniqueHeaders[seen[key]] = (idx, key)
        else:
            seen[key] = len(uniqueHeaders)
            uniqueHeaders.append((idx, key))

    result: dict[str, str] = {}
    for j, (startIdx, key) in enumerate(uniqueHeaders):
        if j + 1 < len(uniqueHeaders):
            endIdx = uniqueHeaders[j + 1][0]
        else:
            endIdx = len(lines)
        result[key] = "\n".join(lines[startIdx:endIdx])

    return result
