"""EDGAR 문서 텍스트 구조 파서.

영문 heading 패턴을 감지하여 body/heading 분리 + 계층 구조를 생성한다.
DART textStructure.py와 동일한 출력 형태를 제공한다.

heading 감지 규칙:
  - 60자 이하 단독 라인
  - Title Case 또는 ALL CAPS
  - 숫자 접두사 불포함 (페이지 번호 등 제외)
  - 이전/이후 라인이 비어있으면 heading 확률 상승
"""

from __future__ import annotations

import re
from typing import Any, Literal

TextNodeType = Literal["heading", "body"]

_RE_PAGE_MARKER = re.compile(
    r"^(?:.*\|\s*\d{4}\s+Form (?:10-[KQ]|20-F)\s*\|.*|.*Form (?:10-[KQ]|20-F).*\|\s*\d+)$",
    re.IGNORECASE,
)
_RE_ALL_CAPS_HEADING = re.compile(r"^[A-Z][A-Z\s,&/\-–—()]{2,58}$")
_RE_TITLE_CASE = re.compile(
    r"^(?:[A-Za-z][A-Za-z''®]*"  # 첫 단어 (iPhone, AppleCare 등)
    r"(?:\s+(?:and|of|the|for|in|to|a|an|or|with|by))*"  # 접속/전치사
    r"(?:[\s,&/\-–—]+[A-Za-z][A-Za-z''®]*"  # 추가 단어
    r"(?:\s+(?:and|of|the|for|in|to|a|an|or|with|by))*"
    r")*)\s*$"
)
_RE_TRAILING_PUNCT = re.compile(r"[.;]\s*$")  # comma 제외 — "Wearables, Home and Accessories"
_RE_SENTENCE_LIKE = re.compile(
    r"\b(?:is|are|was|were|has|have|had|does|do|did|will|would|can|could|shall|should|may|might"
    r"|designs|manufactures|markets|includes|operates|provides|offers|consists|sells|manages"
    r"|reported|announced|filed|disclosed|acquired|established|recognized|recorded)\b",
    re.IGNORECASE,
)
_MAX_HEADING_LEN = 65


def _is_heading(
    line: str,
    *,
    prev_blank: bool,
    next_blank: bool,
    next_line: str | None = None,
) -> tuple[bool, int]:
    """라인이 heading인지 감지. (is_heading, level) 반환."""
    stripped = line.strip()
    if not stripped or stripped.startswith("|"):
        return False, 0
    if len(stripped) > _MAX_HEADING_LEN:
        return False, 0
    if _RE_PAGE_MARKER.fullmatch(stripped):
        return False, 0
    if _RE_TRAILING_PUNCT.search(stripped):
        return False, 0
    # 동사가 포함되면 문장 → body
    if _RE_SENTENCE_LIKE.search(stripped):
        return False, 0

    # 다음 라인이 긴 본문이면 heading 확률 높음
    next_is_body = (
        next_line is not None
        and len(next_line.strip()) > _MAX_HEADING_LEN
    )

    # ALL CAPS → level 1
    if _RE_ALL_CAPS_HEADING.fullmatch(stripped):
        return True, 1

    # Title Case → level 2
    if _RE_TITLE_CASE.fullmatch(stripped):
        return True, 2

    # 짧은 단독 라인 (25자 이하) + 대문자 시작 + 다음 라인이 본문
    if len(stripped) <= 25 and stripped[0].isupper() and (next_is_body or next_blank):
        return True, 2

    return False, 0


def parseTextStructure(
    text: str,
    *,
    topic: str | None = None,
) -> list[dict[str, Any]]:
    """텍스트를 줄 단위로 파싱하여 heading/body 구조 메타를 반환.

    Returns:
        list of dicts with keys:
            - text: str
            - textNodeType: "heading" | "body"
            - textLevel: int (0=body, 1=major heading, 2=sub heading)
            - textPath: str (heading 계층 경로)
    """
    lines = text.split("\n")
    results: list[dict[str, Any]] = []
    heading_stack: list[tuple[int, str]] = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        if _RE_PAGE_MARKER.fullmatch(stripped):
            continue

        prev_blank = i == 0 or not lines[i - 1].strip()
        next_blank = i == len(lines) - 1 or (not lines[i + 1].strip() if i + 1 < len(lines) else True)
        next_line = lines[i + 1] if i + 1 < len(lines) else None

        is_heading, level = _is_heading(
            line,
            prev_blank=prev_blank,
            next_blank=next_blank,
            next_line=next_line,
        )

        if is_heading:
            # heading stack 정리 — 같은/상위 레벨이면 pop
            while heading_stack and heading_stack[-1][0] >= level:
                heading_stack.pop()
            heading_stack.append((level, stripped))

            path = " > ".join(h[1] for h in heading_stack)
            results.append({
                "text": stripped,
                "textNodeType": "heading",
                "textLevel": level,
                "textPath": path,
            })
        else:
            path = " > ".join(h[1] for h in heading_stack) if heading_stack else ""
            results.append({
                "text": stripped,
                "textNodeType": "body",
                "textLevel": 0,
                "textPath": path,
            })

    return results
