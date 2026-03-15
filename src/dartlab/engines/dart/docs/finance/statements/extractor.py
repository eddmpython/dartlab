"""재무제표 섹션 추출 및 개별 제표 영역 분리."""

import re

import polars as pl

_STATEMENT_PATTERNS = {
    "BS": r"재무상태표",
    "PNL": r"손익계산서",
    "CI": r"포괄손익",
    "SCE": r"자본변동표",
    "CF": r"현금흐름표",
}


def extractContent(
    report: pl.DataFrame,
    scope: str | None = None,
) -> tuple[str | None, str]:
    """보고서에서 재무제표 섹션 추출.

    Args:
        report: 보고서 DataFrame
        scope: 지정 시 해당 scope만 추출
            None — 연결 우선, 별도 fallback (기본)
            "consolidated" — 연결만
            "separate" — 별도만

    Returns:
        (content, scope) — scope은 "consolidated" | "separate"
        추출 불가 시 (None, "none")
    """
    if scope != "separate":
        cons = report.filter(
            pl.col("section_title").str.contains("연결재무제표") & ~pl.col("section_title").str.contains("주석")
        )
        if cons.height > 0:
            content = cons["section_content"][0]
            # "연결대상이 없어 연결재무제표를 작성하지 않습니다" 처리
            hasNoSub = "연결대상" in content and ("없어" in content or "없으므로" in content)
            if not hasNoSub:
                if scope == "consolidated":
                    return content, "consolidated"
                return content, "consolidated"

        if scope == "consolidated":
            return None, "none"

    # 별도/개별 재무제표
    sep = report.filter(
        pl.col("section_title").str.contains("재무제표")
        & ~pl.col("section_title").str.contains("연결")
        & ~pl.col("section_title").str.contains("주석")
    )
    if sep.height > 0:
        return sep["section_content"][0], "separate"

    return None, "none"


def extractConsolidatedContent(report: pl.DataFrame) -> str | None:
    """보고서에서 연결재무제표 섹션 내용을 추출. (하위 호환)"""
    content, scope = extractContent(report)
    return content


def splitStatements(content: str) -> dict[str, str]:
    """재무제표 전체 내용을 개별 제표별 텍스트로 분리.

    Returns:
        {"BS": "...", "PNL": "...", "CI": "...", "SCE": "...", "CF": "..."}
    """
    lines = content.split("\n")

    # 헤더 위치 찾기
    # 2024+: "2-1. 연결 재무상태표" (독립 행)
    # ~2023: "| 연결 재무상태표 |" (테이블 행, 셀 1개)
    # 일부 기업: "연 결 재 무 상 태 표" (공백 삽입)
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

        # 공백 제거 후 패턴 매칭 ("재 무 상 태 표" → "재무상태표")
        sNoSpace = re.sub(r"\s+", "", s)
        for key, pattern in _STATEMENT_PATTERNS.items():
            if re.search(pattern, sNoSpace):
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
