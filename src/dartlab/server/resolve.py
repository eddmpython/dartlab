"""종목 매칭/검색 로직 — 의도 분류 + 신뢰도 기반 매칭."""

from __future__ import annotations

import re as _re

import dartlab
from dartlab import Company
from dartlab.core.resolve import (
    COMMON_ALIASES as _COMMON_ALIASES,
    COMPANY_SUFFIXES as _COMPANY_SUFFIXES,
    _RESOLVE_ERRORS,
    collect_candidates as _collect_candidates,
    resolve_alias as _resolve_alias,
    search_suggestions as _search_suggestions,
)

from .models import AskRequest, HistoryMessage

# ── 의도 분류: engines/ai/intent.py에서 re-export ──
from dartlab.engines.ai.conversation.intent import (
    _ANALYSIS_KEYWORDS,
    _META_KEYWORDS,
    _SYSTEM_ENTITIES,
    has_analysis_intent,
    is_meta_question,
    is_pure_conversation as _is_pure_conversation,
)


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
