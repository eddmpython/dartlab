"""이사의 경영진단 및 분석의견(MD&A) 파서."""

import re

KOREAN_NUMS = {
    "가": 1,
    "나": 2,
    "다": 3,
    "라": 4,
    "마": 5,
    "바": 6,
    "사": 7,
    "아": 8,
    "자": 9,
    "차": 10,
}

SECTION_ALIASES = {
    "overview": ["개요", "영업상황"],
    "forecast": ["예측정보"],
    "financials": ["재무상태", "영업실적", "경영성과"],
    "liquidity": ["유동성", "자금조달"],
    "offBalance": ["부외거래", "부외 거래"],
    "other": ["그 밖에", "그 밖의", "투자의사결정", "투자결정"],
    "accounting": ["회계정책", "회계추정"],
    "regulation": ["법규상", "규제"],
    "derivative": ["파생상품", "위험관리"],
    "strategy": ["추진 전략", "사업전망"],
}


def _isSectionHeader(line: str) -> tuple[int, str] | None:
    s = line.strip()

    m = re.match(r"^(\d{1,2})\.\s+(.+)", s)
    if m:
        num = int(m.group(1))
        title = m.group(2).strip()
        if num <= 20 and len(title) >= 2:
            return (num, title)

    m = re.match(r"^([가-차])\.\s+(.+)", s)
    if m:
        char = m.group(1)
        title = m.group(2).strip()
        if char in KOREAN_NUMS and len(title) >= 2:
            return (KOREAN_NUMS[char], title)

    return None


def classifySection(title: str) -> str:
    for key, keywords in SECTION_ALIASES.items():
        for kw in keywords:
            if kw in title:
                return key
    return "unknown"


def parseMdna(content: str) -> dict[str, str]:
    """MD&A 콘텐츠를 섹션별로 분리.

    Returns:
        {sectionTitle: sectionContent} 딕셔너리.
        예: {"1. 예측정보에 대한 주의사항": "...", "2. 개요": "..."}
    """
    lines = content.split("\n")
    sections: dict[str, str] = {}
    currentKey = None
    currentLines: list[str] = []

    for line in lines:
        s = line.strip()

        if s.startswith("IV.") or s.startswith("V."):
            continue

        header = _isSectionHeader(s)
        if header:
            num, title = header
            if currentKey and currentLines:
                sections[currentKey] = "\n".join(currentLines)
            currentKey = f"{num}. {title}"
            currentLines = []
            continue

        if currentKey is not None:
            currentLines.append(line)

    if currentKey and currentLines:
        sections[currentKey] = "\n".join(currentLines)

    return sections


def extractOverview(sections: dict[str, str]) -> str | None:
    """섹션 딕셔너리에서 개요 텍스트 추출."""
    for key, content in sections.items():
        if classifySection(key) == "overview":
            textLines = [l for l in content.split("\n") if l.strip() and not l.strip().startswith("|")]
            result = "\n".join(textLines).strip()
            return result or None
    return None
