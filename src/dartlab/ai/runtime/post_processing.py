"""AI 분석 후처리 — navigate action 감지 + 답변 검증."""

from __future__ import annotations

from typing import Any

from dartlab.ai.runtime.events import AnalysisEvent, EventKind
from dartlab.core.capabilities import UiAction


def _detect_navigate_action(company: Any, question: str) -> AnalysisEvent | None:
    """질문에서 viewer 이동 의도를 감지해 navigate ui_action을 만든다."""
    from dartlab.ai.conversation.dialogue import detect_viewer_intent

    viewer_intent = detect_viewer_intent(question)
    if viewer_intent is None:
        return None
    if not viewer_intent.get("topic"):
        company_topics = None
        try:
            docs = getattr(company, "docs", None)
            sections = getattr(docs, "sections", None)
            if sections is not None and hasattr(sections, "topics"):
                company_topics = sections.topics()
            elif hasattr(company, "topics"):
                company_topics = list(getattr(company, "topics", None) or [])
        except (AttributeError, TypeError, ValueError):
            company_topics = None

        if company_topics:
            viewer_intent = detect_viewer_intent(question, topics=company_topics) or viewer_intent

    nav_payload: dict[str, Any] = {"action": "navigate", "topic": viewer_intent.get("topic", "")}
    stock_id = getattr(company, "stockCode", getattr(company, "ticker", None))
    corp_name = getattr(company, "corpName", None)
    if stock_id:
        nav_payload["stockCode"] = stock_id
    if corp_name:
        nav_payload["company"] = corp_name

    return AnalysisEvent(EventKind.UI_ACTION, nav_payload)


def autoInjectArtifacts(
    company: Any,
    questionType: str | None,
    toolCallNames: list[str],
) -> list[AnalysisEvent]:
    """분석 완료 후 차트/테이블을 자동 주입한다.

    LLM이 차트 도구를 호출하지 않았지만 데이터 도구를 사용한 경우,
    질문 유형에 맞는 차트를 자동 생성하여 ui_action 이벤트로 반환한다.
    """
    if company is None:
        return []

    chartTools = {"chart"}
    dataTools = {"finance", "analyze"}

    hasChart = bool(chartTools & set(toolCallNames))
    hasData = bool(dataTools & set(toolCallNames))

    if hasChart or not hasData:
        return []

    # 질문 유형 → 차트 타입 매핑
    typeToChart: dict[str | None, list[str]] = {
        "수익성": ["profitability"],
        "건전성": ["balance_sheet"],
        "성장성": ["revenue_trend"],
        "배당": ["dividend"],
        "종합": ["insight_radar", "revenue_trend"],
        "투자": ["revenue_trend"],
        "리스크": ["balance_sheet"],
    }

    chartTypes = typeToChart.get(questionType, ["revenue_trend"])[:2]

    events: list[AnalysisEvent] = []
    try:
        from dartlab.tools.chart import _SPEC_GENERATORS

        for ct in chartTypes:
            gen = _SPEC_GENERATORS.get(ct)
            if gen is None:
                continue
            spec = gen(company)
            if spec is not None:
                action = UiAction.render_widget(
                    "chart",
                    {"spec": spec},
                    title="자동 생성 차트",
                    source={"tool": "autoInjectArtifacts", "chartType": ct, "questionType": questionType or ""},
                )
                events.append(
                    AnalysisEvent(
                        EventKind.UI_ACTION,
                        action.to_payload(),
                    )
                )
            if len(events) >= 2:
                break
    except (ImportError, AttributeError, TypeError, ValueError, OSError):
        pass

    return events


def _run_validation(company: Any, full_response_parts: list[str]) -> AnalysisEvent | None:
    """LLM 답변의 재무 수치를 실제 값과 대조 + context 내부 교차검증."""
    try:
        from dartlab.ai.runtime.validation import (
            cross_validate_context,
            extract_numbers,
            validate_claims,
        )

        payload: dict[str, Any] = {}

        # 1) LLM 답변 숫자 검증
        full_text = "".join(full_response_parts)
        claims = extract_numbers(full_text)
        if claims:
            vresult = validate_claims(claims, company)
            if vresult.mismatches:
                payload["mismatches"] = [
                    {
                        "label": mm.label,
                        "claimed": mm.claimed,
                        "actual": mm.actual,
                        "diffPct": round(mm.diff_pct, 1),
                        "unit": mm.unit,
                    }
                    for mm in vresult.mismatches
                ]

        # 2) context 내부 교차검증
        cross_warnings = cross_validate_context(company)
        if cross_warnings:
            payload["crossValidation"] = cross_warnings

        if payload:
            return AnalysisEvent("validation", payload)
    except (ImportError, AttributeError, TypeError, ValueError, OSError):
        pass
    return None


def buildCorrectionPrompt(company: Any, full_response_parts: list[str]) -> str | None:
    """mismatch 감지 시 LLM에 보낼 correction prompt 생성.

    Returns None if no correction needed.
    """
    try:
        from dartlab.ai.runtime.validation import extract_numbers, validate_claims

        full_text = "".join(full_response_parts)
        claims = extract_numbers(full_text)
        if not claims:
            return None

        vresult = validate_claims(claims, company)
        if not vresult.mismatches:
            return None

        lines = ["[수치 검증 결과] 아래 수치가 실제 데이터와 불일치합니다. 수정하세요:\n"]
        for mm in vresult.mismatches:
            if mm.unit == "%":
                lines.append(
                    f"- {mm.label}: 당신 인용 {mm.claimed:.1f}%, 실제값 {mm.actual:.1f}% (차이 {mm.diff_pct:.0f}%)"
                )
            else:
                lines.append(
                    f"- {mm.label}: 당신 인용 {mm.claimed:,.0f}백만원, 실제값 {mm.actual:,.0f}백만원 (차이 {mm.diff_pct:.0f}%)"
                )
        lines.append("\n위 수치를 실제값으로 수정하여 답변을 다시 작성하세요. 나머지 내용은 유지하세요.")
        return "\n".join(lines)
    except (ImportError, AttributeError, TypeError, ValueError, OSError):
        return None
