"""AI 분석 후처리 — navigate action 감지 + 답변 검증."""

from __future__ import annotations

from typing import Any

from dartlab.engines.ai.runtime.events import AnalysisEvent, EventKind


def _detect_navigate_action(company: Any, question: str) -> AnalysisEvent | None:
    """질문에서 viewer 이동 의도를 감지해 navigate ui_action을 만든다."""
    from dartlab.engines.ai.conversation.dialogue import detect_viewer_intent

    company_topics = None
    try:
        company_topics = list(getattr(company, "topics", None) or [])
    except (AttributeError, TypeError):
        pass

    viewer_intent = detect_viewer_intent(question, topics=company_topics)
    if viewer_intent is None:
        return None

    nav_payload: dict[str, Any] = {"action": "navigate", "topic": viewer_intent.get("topic", "")}
    stock_id = getattr(company, "stockCode", getattr(company, "ticker", None))
    corp_name = getattr(company, "corpName", None)
    if stock_id:
        nav_payload["stockCode"] = stock_id
    if corp_name:
        nav_payload["company"] = corp_name

    return AnalysisEvent(EventKind.UI_ACTION, nav_payload)


def _run_validation(company: Any, full_response_parts: list[str]) -> AnalysisEvent | None:
    """LLM 답변의 재무 수치를 실제 값과 대조 + context 내부 교차검증."""
    try:
        from dartlab.engines.ai.runtime.validation import (
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
