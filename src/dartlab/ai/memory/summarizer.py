"""분석 결과 요약기 — 규칙 기반 (LLM 호출 없이).

LLM 답변에서 저장용 요약을 추출한다.
"""

from __future__ import annotations

import re


def summarizeResponse(response: str, maxChars: int = 500) -> str:
    """LLM 응답에서 핵심 요약 추출."""
    if not response:
        return ""

    # 1. "종합" 또는 "결론" 섹션 추출 시도
    conclusionMatch = re.search(
        r"(?:##?\s*(?:종합|결론|요약|판단|Bull|강점).*?\n)(.*?)(?:\n##|\Z)",
        response,
        re.DOTALL,
    )
    if conclusionMatch:
        text = conclusionMatch.group(1).strip()
        return _cleanText(text, maxChars)

    # 2. 마지막 단락 추출
    paragraphs = [p.strip() for p in response.split("\n\n") if p.strip()]
    if paragraphs:
        lastParagraph = paragraphs[-1]
        # 테이블이나 코드 블록이 아닌 마지막 텍스트 단락
        for p in reversed(paragraphs):
            if not p.startswith("|") and not p.startswith("```"):
                return _cleanText(p, maxChars)
        return _cleanText(lastParagraph, maxChars)

    return _cleanText(response, maxChars)


def extractGrade(response: str) -> str | None:
    """응답에서 등급 정보 추출."""
    # "종합 등급: B+" 같은 패턴
    gradeMatch = re.search(r"종합\s*(?:등급|점수)\s*[:：]\s*([A-F][+-]?)", response)
    if gradeMatch:
        return gradeMatch.group(1)
    return None


def _cleanText(text: str, maxChars: int) -> str:
    """마크다운 정리 + 길이 제한."""
    # 마크다운 헤더, 볼드, 이모지 제거
    cleaned = re.sub(r"[#*_`]", "", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if len(cleaned) > maxChars:
        return cleaned[: maxChars - 3] + "..."
    return cleaned
