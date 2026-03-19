"""대화 상태/모드 분류 유틸리티."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .models import HistoryMessage, ViewContext
from .resolve import has_analysis_intent, is_meta_question

_LEGACY_VIEWER_RE = re.compile(
    r"\[사용자가 현재\s+(?P<company>.+?)\((?P<stock>[A-Za-z0-9]+)\)\s+공시를 보고 있습니다"
    r"(?:\s+—\s+현재 섹션:\s+(?P<label>.+?)\((?P<topic>[^()]+)\))?\]",
)
_LEGACY_DATA_RE = re.compile(r'\[사용자가 현재\s+"(?P<label>.+?)"\s+데이터를 보고 있습니다\]')

_CODING_KEYWORDS = (
    "코드",
    "버그",
    "에러",
    "리팩터",
    "리팩토링",
    "파일",
    "함수",
    "테스트",
    "구현",
    "수정",
    "patch",
    "diff",
    "workspace",
    "cli",
    "codex",
)
_EXPLORE_KEYWORDS = (
    "어떤 데이터",
    "무슨 데이터",
    "뭘 볼 수",
    "뭐가 있어",
    "어떤 기능",
    "가능한 것",
    "가능한거",
    "범위",
    "얼마나",
    "더 받을 수",
    "추가 수집",
    "openapi",
)
_FOLLOW_UP_PREFIXES = ("그럼", "그러면", "이건", "이거", "그거", "왜", "어째서", "더", "계속", "이어")

# "보여줘" 의도 감지 — Viewer 탭 전환 트리거
_VIEWER_INTENT_KEYWORDS = (
    "보여줘",
    "보여 줘",
    "보여주세요",
    "열어줘",
    "열어 줘",
    "공시 보기",
    "공시 열기",
    "원문 보기",
    "원문 보여",
    "sections 보여",
    "section 보여",
    "show me",
    "open viewer",
)
_DIALOGUE_MODE_LABELS = {
    "capability": "기능 탐색",
    "coding": "코딩 작업",
    "company_explore": "회사 탐색",
    "company_analysis": "회사 분석",
    "follow_up": "후속 질문",
    "general_chat": "일반 대화",
}
_USER_GOAL_LABELS = {
    "capability": "지금 가능한 기능/범위를 확인",
    "coding": "코드 작업 실행 또는 검토",
    "company_explore": "현재 회사에서 볼 수 있는 데이터와 경로 확인",
    "company_analysis": "현재 회사의 구체적 분석",
    "follow_up": "이전 맥락을 이어서 추가 확인",
    "general_chat": "일반 질문 또는 가벼운 대화",
}


@dataclass(frozen=True)
class ConversationState:
    question: str
    dialogue_mode: str
    user_goal: str
    company: str | None = None
    stock_code: str | None = None
    market: str | None = None
    topic: str | None = None
    topic_label: str | None = None
    question_types: tuple[str, ...] = ()
    modules: tuple[str, ...] = ()
    prev_dialogue_mode: str | None = None
    prev_question_types: tuple[str, ...] = ()
    turn_count: int = 0


def _infer_market(
    *,
    company: Any | None = None,
    stock_code: str | None = None,
    view_context: ViewContext | None = None,
    history_market: str | None = None,
) -> str | None:
    if view_context and view_context.company and view_context.company.market:
        return view_context.company.market.lower()
    if history_market:
        return history_market.lower()
    company_market = getattr(company, "market", None)
    if isinstance(company_market, str) and company_market.strip():
        return company_market.lower()
    code = stock_code or getattr(company, "stockCode", None) or getattr(company, "ticker", None)
    if isinstance(code, str) and code:
        return "dart" if code.isdigit() and len(code) == 6 else "edgar"
    return None


def _last_history_meta(history: list[HistoryMessage] | None) -> Any | None:
    if not history:
        return None
    for item in reversed(history):
        if item.meta:
            return item.meta
    return None


def _parse_legacy_view_context(question: str) -> tuple[str, ViewContext | None]:
    cleaned = question
    viewer_match = _LEGACY_VIEWER_RE.search(question)
    if viewer_match:
        cleaned = cleaned.replace(viewer_match.group(0), "").strip()
        return (
            cleaned,
            ViewContext(
                type="viewer",
                company={
                    "company": viewer_match.group("company"),
                    "corpName": viewer_match.group("company"),
                    "stockCode": viewer_match.group("stock"),
                },
                topic=viewer_match.group("topic"),
                topicLabel=viewer_match.group("label"),
            ),
        )

    data_match = _LEGACY_DATA_RE.search(question)
    if data_match:
        cleaned = cleaned.replace(data_match.group(0), "").strip()
        return cleaned, ViewContext(type="data", data={"label": data_match.group("label")})

    return cleaned, None


def detect_viewer_intent(question: str, *, topics: list[str] | None = None) -> dict[str, str] | None:
    """질문에서 '보여줘' 의도 + topic을 감지한다.

    Returns:
        {"topic": "businessOverview"} 또는 None.
        topic 특정 불가 시 {"topic": ""} (Viewer 탭만 전환).
    """
    lowered = question.lower().strip()
    has_show = any(kw in lowered for kw in _VIEWER_INTENT_KEYWORDS)
    if not has_show:
        return None

    # topic 추출 — topics 목록과 대조
    if topics:
        for t in topics:
            if t.lower() in lowered or t in question:
                return {"topic": t}

    # 한국어 topic 힌트 → canonical topic 매핑
    _TOPIC_HINTS: dict[str, str] = {
        "사업": "businessOverview",
        "사업 개요": "businessOverview",
        "사업개요": "businessOverview",
        "사업의 개요": "businessOverview",
        "배당": "dividend",
        "직원": "employee",
        "임원": "executive",
        "주주": "majorHolder",
        "최대주주": "majorHolder",
        "감사": "audit",
        "리스크": "riskManagement",
        "위험": "riskManagement",
        "소송": "litigation",
        "회사 개요": "companyOverview",
        "회사개요": "companyOverview",
        "재무": "financialStatements",
        "연결재무": "consolidatedStatements",
        "주석": "financialNotes",
        "내부통제": "internalControl",
        "투자": "investmentInOtherDetail",
        "자회사": "subsidiaryDetail",
        "R&D": "rndDetail",
        "연구개발": "rndDetail",
        "제품": "productService",
        "매출": "salesRevenue",
        "자본변동": "capitalChange",
        "자금조달": "fundraising",
    }
    for hint, topic in _TOPIC_HINTS.items():
        if hint in question:
            return {"topic": topic}

    return {"topic": ""}


def _classify_dialogue_mode(question: str, *, has_company: bool) -> str:
    lowered = question.lower().strip()
    if any(keyword in lowered for keyword in _CODING_KEYWORDS):
        return "coding"
    if is_meta_question(question):
        return "capability"
    if has_company:
        if has_analysis_intent(question):
            return "company_analysis"
        if any(keyword in lowered for keyword in _EXPLORE_KEYWORDS):
            return "company_explore"
        if len(question.strip()) <= 18 or any(lowered.startswith(prefix) for prefix in _FOLLOW_UP_PREFIXES):
            return "follow_up"
        return "company_explore"
    return "general_chat"


def build_conversation_state(
    question: str,
    *,
    history: list[HistoryMessage] | None = None,
    company: Any | None = None,
    view_context: ViewContext | None = None,
) -> ConversationState:
    cleaned_question, legacy_view_context = _parse_legacy_view_context(question)
    active_view = view_context or legacy_view_context
    history_meta = _last_history_meta(history)

    company_name = getattr(company, "corpName", None)
    stock_code = getattr(company, "stockCode", None)
    if not company_name and history_meta and history_meta.company:
        company_name = history_meta.company
    if not stock_code and history_meta and history_meta.stockCode:
        stock_code = history_meta.stockCode

    if active_view and active_view.company:
        company_name = company_name or active_view.company.corpName or active_view.company.company
        stock_code = stock_code or active_view.company.stockCode

    topic = None
    topic_label = None
    if active_view and active_view.type == "viewer":
        topic = active_view.topic
        topic_label = active_view.topicLabel or active_view.topic
    elif history_meta:
        topic = history_meta.topic
        topic_label = history_meta.topicLabel or history_meta.topic

    modules = tuple(history_meta.modules or []) if history_meta and history_meta.modules else ()

    try:
        from dartlab.engines.ai.prompts import _classify_question_multi

        question_types = tuple(_classify_question_multi(cleaned_question))
    except (ImportError, AttributeError, ValueError):
        question_types = ()

    dialogue_mode = _classify_dialogue_mode(cleaned_question, has_company=bool(company_name or stock_code))
    user_goal = _USER_GOAL_LABELS[dialogue_mode]
    market = _infer_market(
        company=company,
        stock_code=stock_code,
        view_context=active_view,
        history_market=history_meta.market if history_meta else None,
    )

    # 이전 대화 맥락
    prev_dialogue_mode = history_meta.dialogueMode if history_meta else None
    prev_question_types = tuple(history_meta.questionTypes or []) if history_meta and history_meta.questionTypes else ()
    turn_count = len(history) if history else 0

    return ConversationState(
        question=cleaned_question or question,
        dialogue_mode=dialogue_mode,
        user_goal=user_goal,
        company=company_name,
        stock_code=stock_code,
        market=market,
        topic=topic,
        topic_label=topic_label,
        question_types=question_types,
        modules=modules,
        prev_dialogue_mode=prev_dialogue_mode,
        prev_question_types=prev_question_types,
        turn_count=turn_count,
    )


def conversation_state_to_meta(state: ConversationState) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "company": state.company,
        "stockCode": state.stock_code,
        "market": state.market,
        "topic": state.topic,
        "topicLabel": state.topic_label,
        "dialogueMode": state.dialogue_mode,
        "questionTypes": list(state.question_types) if state.question_types else None,
        "userGoal": state.user_goal,
        "turnCount": state.turn_count if state.turn_count > 0 else None,
    }
    return {key: value for key, value in payload.items() if value not in (None, [], "", 0)}


def build_dialogue_policy(state: ConversationState) -> str:
    from dartlab.engines.ai.tools_registry import get_coding_runtime_policy

    coding_runtime_enabled, coding_runtime_reason = get_coding_runtime_policy()
    lines = [
        "## 현재 대화 상태",
        f"- 대화 모드: {_DIALOGUE_MODE_LABELS.get(state.dialogue_mode, state.dialogue_mode)}",
        f"- 사용자 목표: {state.user_goal}",
    ]
    if state.company and state.stock_code:
        lines.append(f"- 현재 회사: {state.company} ({state.stock_code})")
    elif state.company:
        lines.append(f"- 현재 회사: {state.company}")
    if state.market:
        lines.append(f"- 시장: {state.market}")
    if state.topic_label or state.topic:
        lines.append(f"- 현재 보고 있는 주제: {state.topic_label or state.topic}")
    if state.modules:
        lines.append(f"- 직전 분석 모듈: {', '.join(f'`{name}`' for name in state.modules[:8])}")
    if state.question_types:
        lines.append(f"- 감지된 질문 유형: {', '.join(state.question_types)}")
    if state.turn_count > 0:
        lines.append(f"- 대화 턴: {state.turn_count}회차")
    if state.prev_dialogue_mode:
        lines.append(f"- 직전 모드: {_DIALOGUE_MODE_LABELS.get(state.prev_dialogue_mode, state.prev_dialogue_mode)}")
    if state.prev_question_types:
        lines.append(f"- 직전 질문 유형: {', '.join(state.prev_question_types)}")

    lines.extend(["", "## 대화 진행 규칙"])

    # 멀티턴 연속성 지시
    if state.turn_count >= 2 and state.company:
        lines.extend(
            [
                "### 멀티턴 연속성",
                "- 이전 턴의 분석 결과와 맥락을 이어받으세요. 같은 회사 반복 소개 불필요.",
                "- 사용자가 짧게 물으면 이전 맥락에서 가장 관련 있는 데이터를 자동 활용하세요.",
                "- 직전 분석 모듈이 있으면 해당 모듈 데이터를 우선 참조하세요.",
                "",
            ]
        )
    if state.dialogue_mode == "capability":
        lines.extend(
            [
                "- 가능한 것 / 바로 할 수 있는 것 / 아직 안 되는 것을 먼저 3줄 안에 정리하세요.",
                "- 바로 실행 가능한 다음 질문이나 액션을 2~4개 제안하세요.",
                "- 실제로 등록된 도구와 런타임 상태만 말하고 추측하지 마세요.",
            ]
        )
        lines.extend(
            [
                "",
                "## 응답 템플릿",
                "1. 가능한 것: 현재 세션에서 바로 가능한 기능 2~4개",
                "2. 바로 할 수 있는 것: 지금 즉시 실행 가능한 조회/분석/저장 작업",
                "3. 아직 안 되는 것: 미지원 또는 현재 세션에서 닫힌 기능",
                "4. 다음 액션: 사용자가 바로 복사해서 물을 수 있는 질문 2~4개",
            ]
        )
    elif state.dialogue_mode == "coding":
        lines.extend(
            [
                "- 먼저 작업 범위와 제약을 짧게 요약하세요.",
                "- 수정 결과를 말할 때 변경점, 검증, 남은 리스크를 분리해서 설명하세요.",
            ]
        )
        if coding_runtime_enabled:
            lines.append(
                "- 이 세션에서는 coding runtime이 열려 있으므로 실행 가능한 코드 작업이면 `run_coding_task` 사용을 우선 검토하세요."
            )
        else:
            lines.append(
                f"- 이 세션에서는 coding runtime이 비활성화되어 있으니 실제 코드 수정은 약속하지 말고, 텍스트 기반 수정안과 활성화 조건만 안내하세요. ({coding_runtime_reason})"
            )
        lines.extend(
            [
                "",
                "## 응답 템플릿",
                "1. 작업 범위: 무엇을 고치거나 만들지 한두 문장으로 요약",
                "2. 실행 상태: 실제 코드 작업 가능 여부 또는 막힌 이유",
                "3. 변경점: 파일/동작 기준 핵심 변경 또는 제안안",
                "4. 검증: 테스트/빌드/확인 방법",
                "5. 남은 리스크: 아직 확인되지 않은 점 1~2개",
            ]
        )
    elif state.dialogue_mode == "company_analysis":
        lines.extend(
            [
                "- 핵심 결론 1~2문장을 먼저 제시하고 곧바로 근거 표를 붙이세요.",
                "- 숫자는 반드시 해석과 함께 제시하고, 마지막에 추가 drill-down 제안 1~2개를 남기세요.",
                "- 사용자가 이미 보고 있는 topic이 있으면 그 topic을 우선 활용하세요.",
            ]
        )
        lines.extend(
            [
                "",
                "## 응답 템플릿",
                "1. 한줄 결론: 가장 중요한 판단 1~2문장",
                "2. 근거 표: 핵심 수치 2개 이상이면 반드시 표로 정리",
                "3. 해석: 숫자가 의미하는 변화와 원인",
                "4. 다음 drill-down: 더 파볼 주제 1~2개",
            ]
        )
    elif state.dialogue_mode in {"company_explore", "follow_up"}:
        lines.extend(
            [
                "- 이전 맥락을 이어받아 불필요한 재질문 없이 바로 답하세요.",
                "- 현재 회사에서 바로 볼 수 있는 데이터나 다음 탐색 경로를 먼저 보여주세요.",
                "- 짧은 답 후 구체적 drill-down 옵션을 제안하세요.",
            ]
        )
        lines.extend(
            [
                "",
                "## 응답 템플릿",
                "1. 직접 답: 사용자의 현재 질문에 바로 답변",
                "2. 지금 볼 수 있는 데이터/경로: topic, show, trace, OpenAPI 중 적절한 경로",
                "3. 다음 선택지: 이어서 물을 만한 drill-down 질문 2~3개",
            ]
        )
    else:
        lines.extend(
            [
                "- 짧고 직접적으로 답하고, 필요한 경우에만 다음 행동을 제안하세요.",
                "- 회사 맥락이 없으면 특정 종목명/코드가 있으면 더 정확히 도와줄 수 있다고 안내하세요.",
            ]
        )
        lines.extend(
            [
                "",
                "## 응답 템플릿",
                "1. 직접 답변",
                "2. 필요하면 짧은 보충 설명",
                "3. 필요한 경우에만 다음 행동 1~2개",
            ]
        )
    return "\n".join(lines)
