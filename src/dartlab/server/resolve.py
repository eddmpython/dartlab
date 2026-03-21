"""종목 매칭/검색 로직 — 의도 분류 + 신뢰도 기반 매칭."""

from __future__ import annotations

import re as _re

import dartlab
from dartlab import Company

from .models import AskRequest, HistoryMessage

_RESOLVE_ERRORS = (AttributeError, KeyError, OSError, RuntimeError, TypeError, ValueError)

_COMPANY_SUFFIXES = (
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

_COMMON_ALIASES: dict[str, str] = {
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

# ── 의도 분류: engines/ai/intent.py에서 re-export ──
from dartlab.engines.ai.conversation.intent import (
    _ANALYSIS_KEYWORDS,
    _META_KEYWORDS,
    _SYSTEM_ENTITIES,
    has_analysis_intent,
    is_meta_question,
    is_pure_conversation as _is_pure_conversation,
)


def _collect_candidates(query: str, *, strict: bool) -> list[dict[str, str]]:
    """검색 결과에서 매칭되는 후보를 수집한다.

    strict=True: 정확히 일치하거나 prefix 관계만 허용
    strict=False: 부분 포함도 허용 (fuzzy — 초성/Levenshtein 포함)
    """
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


def _search_suggestions(question: str) -> list[dict[str, str]]:
    """질문에서 단어를 추출하여 비슷한 종목 후보를 검색한다."""
    import re

    words = re.split(r"\s+", question)
    seen_codes: set[str] = set()
    suggestions: list[dict[str, str]] = []

    for word in words:
        if len(word) < 2:
            continue
        queries = [word]
        for suffix in _COMPANY_SUFFIXES:
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


class ResolveResult:
    """종목 검색 결과를 담는 컨테이너.

    상태:
    - company 있음: 정확히 1개 매칭
    - not_found=True: 종목을 찾을 수 없음 (suggestions에 비슷한 후보)
    - ambiguous=True: 여러 후보가 매칭됨 (suggestions에 후보 목록)
    """

    __slots__ = ("company", "not_found", "ambiguous", "suggestions")

    def __init__(
        self,
        company: Company | None = None,
        *,
        not_found: bool = False,
        ambiguous: bool = False,
        suggestions: list[dict[str, str]] | None = None,
    ):
        self.company = company
        self.not_found = not_found
        self.ambiguous = ambiguous
        self.suggestions = suggestions or []


def build_not_found_msg(suggestions: list[dict[str, str]]) -> str:
    """NOT_FOUND 안내 메시지. 후보가 있으면 목록 포함."""
    if not suggestions:
        return (
            "해당 종목을 찾을 수 없습니다. "
            "정확한 종목명(예: 삼성전자, 기아, LG에너지솔루션) 또는 "
            "6자리 종목코드(예: 005930)로 다시 질문해 주세요."
        )
    lines = ["해당 종목을 정확히 찾지 못했습니다. 혹시 아래 종목을 찾으시나요?\n"]
    for s in suggestions:
        lines.append(f"- **{s['corpName']}** ({s['stockCode']})")
    lines.append("\n종목명이나 종목코드를 정확히 입력하시면 바로 분석해 드리겠습니다.")
    return "\n".join(lines)


def build_ambiguous_msg(suggestions: list[dict[str, str]]) -> str:
    """여러 종목이 매칭될 때 선택 안내 메시지."""
    lines = ["여러 종목이 검색되었습니다. 어떤 종목을 분석할까요?\n"]
    for s in suggestions:
        lines.append(f"- **{s['corpName']}** ({s['stockCode']})")
    lines.append("\n종목명이나 종목코드를 정확히 입력해 주세요.")
    return "\n".join(lines)


def _resolve_alias(text: str) -> str | None:
    """_COMMON_ALIASES에서 매칭되는 정식 종목명 반환. 없으면 None."""
    return _COMMON_ALIASES.get(text)


def try_resolve_company(req: AskRequest) -> ResolveResult:
    """company 필드 또는 질문에서 종목을 찾는다.

    신뢰도 기반 매칭:
    - company 필드가 명시적으로 지정되면 그대로 사용
    - _COMMON_ALIASES로 약칭 → 정식명 변환 (최우선)
    - 6자리 종목코드는 항상 신뢰
    - 메타 질문(버전, 사용법, 데이터 현황)은 종목 매칭 스킵
    - 검색 결과가 2개 이상이면 suggestions로 반환 (사용자 선택)
    """
    import re

    q = req.question

    # 메타 질문은 company/viewContext가 있어도 회사 분석 스킵 — 최우선
    if is_meta_question(q):
        return ResolveResult()

    # 순수 대화 ("응", "잘되나", "대화 계속 안되나" 등)는 회사 분석 스킵 — 최우선
    if _is_pure_conversation(q):
        return ResolveResult()

    if req.company:
        alias = _resolve_alias(req.company)
        if alias:
            try:
                return ResolveResult(company=Company(alias))
            except (ValueError, OSError):
                pass
        try:
            return ResolveResult(company=Company(req.company))
        except (ValueError, OSError):
            suggestions = _search_suggestions(req.company)
            return ResolveResult(not_found=True, suggestions=suggestions)

    if req.viewContext and req.viewContext.company:
        view_company = req.viewContext.company
        identifiers = [
            view_company.stockCode,
            view_company.corpName,
            view_company.company,
        ]
        for identifier in identifiers:
            if not identifier:
                continue
            try:
                return ResolveResult(company=Company(identifier))
            except (ValueError, OSError):
                continue

    code_match = re.search(r"\b(\d{6})\b", q)
    if code_match:
        try:
            return ResolveResult(company=Company(code_match.group(1)))
        except (ValueError, OSError):
            return ResolveResult(not_found=True)

    intent = has_analysis_intent(q)

    words = re.split(r"\s+", q)
    for length in range(min(4, len(words)), 0, -1):
        for i in range(len(words) - length + 1):
            candidate = " ".join(words[i : i + length])

            alias = _resolve_alias(candidate)
            if alias:
                try:
                    return ResolveResult(company=Company(alias))
                except (ValueError, OSError):
                    pass

            candidates = _collect_candidates(candidate, strict=not intent)
            if not candidates:
                continue

            if len(candidates) == 1:
                try:
                    return ResolveResult(company=Company(candidates[0]["stockCode"]))
                except (ValueError, OSError):
                    continue

            exact = [c for c in candidates if c["corpName"] == candidate]
            if len(exact) == 1:
                try:
                    return ResolveResult(company=Company(exact[0]["stockCode"]))
                except (ValueError, OSError):
                    continue

            return ResolveResult(ambiguous=True, suggestions=candidates[:5])

    return ResolveResult()


def needs_match_verification(question: str, corpName: str) -> bool:
    """사용자 질문과 매칭된 종목명이 불일치하는지 판별.

    정확히 일치하면 OK. prefix 매칭(현대차→현대차증권)은 의심 대상.
    alias 경유 매칭은 OK.
    불일치 의심 시 True 반환 → LLM 검증 필요.
    """
    if corpName in question:
        return False

    import re

    words = re.split(r"\s+", question)
    for length in range(min(4, len(words)), 0, -1):
        for i in range(len(words) - length + 1):
            candidate = " ".join(words[i : i + length])
            if candidate == corpName:
                return False
            if _COMMON_ALIASES.get(candidate) == corpName:
                return False

    return True


_VERIFY_PROMPT = (
    '사용자가 "{question}"이라고 질문했습니다.\n'
    '시스템이 "{corpName}" ({stockCode}) 종목을 찾았습니다.\n\n'
    '사용자가 실제로 "{corpName}"에 대해 물어본 것이 맞습니까?\n'
    "반드시 아래 형식으로만 답하세요:\n"
    "YES — 맞으면\n"
    "NO:정확한종목명 — 다른 종목이면 (예: NO:현대자동차)\n"
    "UNSURE — 판단 불가면"
)


def verify_match_with_llm(
    question: str,
    corpName: str,
    stockCode: str,
) -> str | None:
    """LLM으로 종목 매칭 검증. 불일치 시 올바른 종목명 반환, 일치 시 None.

    Returns:
            None: 매칭 정상 (YES 또는 UNSURE)
            str: LLM이 제안한 올바른 종목명 (NO:종목명에서 추출)
    """
    from dartlab.engines.ai import get_config
    from dartlab.engines.ai.providers import create_provider

    config = get_config()
    llm = create_provider(config)

    prompt = _VERIFY_PROMPT.format(
        question=question,
        corpName=corpName,
        stockCode=stockCode,
    )
    messages = [
        {"role": "system", "content": "당신은 한국 주식 종목명 검증 도우미입니다. 간결하게 답하세요."},
        {"role": "user", "content": prompt},
    ]

    try:
        resp = llm.complete(messages)
        answer = resp.answer.strip() if hasattr(resp, "answer") else str(resp).strip()
    except (OSError, RuntimeError, ValueError):
        return None

    if answer.startswith("YES") or answer.startswith("UNSURE"):
        return None

    if answer.startswith("NO:"):
        suggested = answer[3:].strip()
        if len(suggested) >= 2:
            return suggested

    return None


def try_resolve_from_history(history: list[HistoryMessage]) -> Company | None:
    """대화 히스토리에서 가장 최근 분석된 종목을 찾는다. 메타 우선, 텍스트 fallback."""
    if not history:
        return None
    for msg in reversed(history):
        if msg.meta and msg.meta.stockCode:
            try:
                return Company(msg.meta.stockCode)
            except _RESOLVE_ERRORS:
                continue
    import re

    for msg in reversed(history):
        if not msg.text:
            continue
        code_match = re.search(r"\b(\d{6})\b", msg.text)
        if code_match:
            try:
                return Company(code_match.group(1))
            except _RESOLVE_ERRORS:
                continue
    return None
