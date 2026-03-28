"""Analysis Briefing — Engine-First AI 컨텍스트 생성.

compact map(프로필 200토큰) + pipeline(분석 결과 2,000-8,000토큰)을 통합하여
LLM에게 풍부한 사전분석 결과를 제공한다.

기존 compact map 체제에서는 200토큰만 제공하고 나머지는 도구 호출에 의존했다.
Engine-First 체제에서는 엔진이 질문 유형에 맞는 분석을 사전 실행하여
LLM이 도구 호출 없이도 분석 품질을 유지한다.
"""

from __future__ import annotations

import logging
from typing import Any

_log = logging.getLogger(__name__)


def buildBriefing(
    company: Any,
    question: str,
    *,
    maxTokens: int = 0,
    reportMode: bool = False,
) -> str:
    """Analysis Briefing 생성.

    Args:
        company: Company 객체
        question: 사용자 질문
        maxTokens: 토큰 상한 (0=자동 결정)
        reportMode: 리포트 모드 (더 상세한 분석)

    Returns:
        마크다운 텍스트 (compact map + 분석 결과)
    """
    from dartlab.ai.context.compactMap import buildCompactMap

    parts: list[str] = []

    # 1. Compact Map (프로필 — 항상 포함)
    compactMap = buildCompactMap(company)
    if compactMap:
        parts.append(compactMap)

    # 2. Pipeline (질문 유형별 사전분석)
    pipelineResult = _runPipeline(company, question)
    if pipelineResult:
        parts.append(pipelineResult)

    if not parts:
        return ""

    return "\n\n".join(parts)


def buildBriefingMulti(
    companies: list[Any],
    primaryCompany: Any,
    question: str,
    *,
    reportMode: bool = False,
) -> tuple[str, list[tuple[str, str]]]:
    """멀티 기업 briefing 생성.

    Returns:
        (briefing_text, [(stockCode, label)] 이벤트 목록)
    """
    parts: list[str] = []
    events: list[tuple[str, str]] = []

    # 주 기업: 풍부한 briefing
    mainBriefing = buildBriefing(
        primaryCompany, question, reportMode=reportMode,
    )
    if mainBriefing:
        parts.append(mainBriefing)
        corpName = getattr(primaryCompany, "corpName", "?")
        events.append(("_briefing", f"{corpName} 분석 브리핑"))

    # 추가 기업: compact map만 (비교용)
    from dartlab.ai.context.compactMap import buildCompactMap

    for comp in companies:
        if comp is primaryCompany:
            continue
        try:
            extraMap = buildCompactMap(comp)
            if extraMap:
                parts.append(extraMap)
                code = getattr(comp, "stockCode", "?")
                name = getattr(comp, "corpName", "?")
                events.append((f"{code}_compactMap", f"{name} 프로필"))
        except (ValueError, FileNotFoundError, OSError, RuntimeError):
            pass

    return "\n\n".join(parts), events


def _runPipeline(company: Any, question: str) -> str:
    """pipeline.py의 run_pipeline을 호출하여 분석 결과를 반환."""
    try:
        from dartlab.ai.runtime.pipeline import run_pipeline

        result = run_pipeline(company, question, included_tables=[])
        return result
    except (ImportError, AttributeError, TypeError, ValueError, OSError, RuntimeError) as e:
        _log.debug("pipeline failed: %s", e)
        return ""
