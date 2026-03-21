"""자연어 종목 추출 — CLI, Python API, Server 공통 원소스.

사용법::

    from dartlab.core.resolve import resolve_from_text, resolve_alias

    # 자연어에서 종목+질문 분리
    company, question = resolve_from_text("삼성전자 재무건전성 분석해줘")
    # company = Company("삼성전자"), question = "재무건전성 분석해줘"

    # 약칭 → 정식명
    resolve_alias("삼전")  # "삼성전자"
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dartlab.company import Company

_RESOLVE_ERRORS = (AttributeError, KeyError, OSError, RuntimeError, TypeError, ValueError)

COMPANY_SUFFIXES = (
    "차",
    "전자",
    "그룹",
    "건설",
    "화학",
    "제약",
    "바이오",
    "증권",
    "보험",
    "은행",
    "금융",
    "지주",
    "산업",
    "통신",
    "에너지",
)

COMMON_ALIASES: dict[str, str] = {
    "삼전": "삼성전자",
    "현차": "현대자동차",
    "현대차": "현대자동차",
    "기차": "기아",
    "삼바": "삼성바이오로직스",
    "삼성바이오": "삼성바이오로직스",
    "셀트리온헬스케어": "셀트리온",
    "네이버": "NAVER",
    "포스코": "포스코홀딩스",
    "에코프로": "에코프로비엠",
    "LG엔솔": "LG에너지솔루션",
    "엔솔": "LG에너지솔루션",
    "카뱅": "카카오뱅크",
    "카페": "카카오",
}


def resolve_alias(text: str) -> str | None:
    """COMMON_ALIASES에서 매칭되는 정식 종목명 반환. 없으면 None."""
    return COMMON_ALIASES.get(text)


def collect_candidates(query: str, *, strict: bool) -> list[dict[str, str]]:
    """검색 결과에서 매칭되는 후보를 수집한다.

    strict=True: 정확히 일치하거나 prefix 관계만 허용
    strict=False: 부분 포함도 허용 (fuzzy — 초성/Levenshtein 포함)
    """
    import dartlab

    if len(query) < 2:
        return []
    try:
        df = dartlab.search(query)
        if len(df) == 0:
            df = None
    except (ValueError, OSError):
        df = None

    exact: list[dict[str, str]] = []
    prefix: list[dict[str, str]] = []
    contains: list[dict[str, str]] = []

    if df is not None:
        for row in df.to_dicts()[:10]:
            name = row.get("회사명", row.get("corpName", ""))
            code = row.get("종목코드", row.get("stockCode", ""))
            if not code:
                continue
            entry = {"corpName": name, "stockCode": code}
            if name == query:
                exact.append(entry)
            elif name.startswith(query) or query.startswith(name):
                prefix.append(entry)
            elif not strict and len(query) >= 3 and query in name:
                contains.append(entry)

    result = exact + prefix + contains

    # fuzzy fallback: substring 매칭이 없으면 초성/Levenshtein 시도
    if not result and not strict:
        from dartlab.core.kindList import fuzzySearch

        try:
            fuzzy_df = fuzzySearch(query, maxResults=5)
            if len(fuzzy_df) > 0:
                seen = {e["stockCode"] for e in result}
                for row in fuzzy_df.to_dicts():
                    name = row.get("회사명", row.get("corpName", ""))
                    code = row.get("종목코드", row.get("stockCode", ""))
                    if code and code not in seen:
                        seen.add(code)
                        result.append({"corpName": name, "stockCode": code})
        except (ValueError, OSError):
            pass

    return result


def search_suggestions(question: str) -> list[dict[str, str]]:
    """질문에서 단어를 추출하여 비슷한 종목 후보를 검색한다."""
    import dartlab

    words = re.split(r"\s+", question)
    seen_codes: set[str] = set()
    suggestions: list[dict[str, str]] = []

    for word in words:
        if len(word) < 2:
            continue
        queries = [word]
        for suffix in COMPANY_SUFFIXES:
            if word.endswith(suffix) and len(word) > len(suffix):
                queries.append(word[: -len(suffix)])
        for q in queries:
            try:
                df = dartlab.search(q)
                for row in df.head(3).to_dicts():
                    code = row.get("종목코드", row.get("stockCode", ""))
                    name = row.get("회사명", row.get("corpName", ""))
                    if code and code not in seen_codes:
                        seen_codes.add(code)
                        suggestions.append({"corpName": name, "stockCode": code})
                        if len(suggestions) >= 5:
                            return suggestions
            except _RESOLVE_ERRORS:
                continue
    return suggestions


def resolve_from_text(text: str) -> tuple[Company | None, str]:
    """자연어 텍스트에서 종목과 질문을 분리한다.

    Returns:
        (Company | None, remaining_question)

    Examples::

        resolve_from_text("삼성전자 재무건전성 분석해줘")
        # → (Company("삼성전자"), "재무건전성 분석해줘")

        resolve_from_text("삼전 배당")
        # → (Company("삼성전자"), "배당")

        resolve_from_text("005930 영업이익률 추세는?")
        # → (Company("005930"), "영업이익률 추세는?")

        resolve_from_text("AAPL dividend trend?")
        # → (Company("AAPL"), "dividend trend?")

        resolve_from_text("오늘 날씨 어때")
        # → (None, "오늘 날씨 어때")
    """
    from dartlab import Company

    text = text.strip()
    if not text:
        return None, text

    # 1) 6자리 종목코드 먼저 시도
    code_match = re.match(r"^(\d{6})\s+(.+)$", text)
    if code_match:
        try:
            return Company(code_match.group(1)), code_match.group(2).strip()
        except _RESOLVE_ERRORS:
            pass

    # 2) US ticker 패턴 (대문자 1~5글자 + 공백 + 나머지)
    ticker_match = re.match(r"^([A-Z]{1,5})\s+(.+)$", text)
    if ticker_match:
        try:
            return Company(ticker_match.group(1)), ticker_match.group(2).strip()
        except _RESOLVE_ERRORS:
            pass

    # 3) 약칭 → 정식명 (단어 조합, 긴 것 우선)
    words = text.split()
    for length in range(min(4, len(words)), 0, -1):
        for i in range(len(words) - length + 1):
            candidate = " ".join(words[i : i + length])
            remaining_parts = words[:i] + words[i + length :]
            remaining = " ".join(remaining_parts).strip()

            # 약칭 매칭
            alias = COMMON_ALIASES.get(candidate)
            if alias:
                try:
                    company = Company(alias)
                    return company, remaining if remaining else candidate
                except _RESOLVE_ERRORS:
                    pass

            # 직접 매칭 시도
            candidates = collect_candidates(candidate, strict=True)
            if len(candidates) == 1:
                try:
                    company = Company(candidates[0]["stockCode"])
                    return company, remaining if remaining else candidate
                except _RESOLVE_ERRORS:
                    continue

            # 정확히 일치하는 후보
            exact = [c for c in candidates if c["corpName"] == candidate]
            if len(exact) == 1:
                try:
                    company = Company(exact[0]["stockCode"])
                    return company, remaining if remaining else candidate
                except _RESOLVE_ERRORS:
                    continue

    return None, text
