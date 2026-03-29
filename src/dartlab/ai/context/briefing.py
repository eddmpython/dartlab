"""Analysis Briefing -- Engine-First AI 컨텍스트 생성.

compact map(프로필 200토큰) + pipeline(분석 결과 2,000-8,000토큰)을 통합하여
LLM에게 풍부한 사전분석 결과를 제공한다.

캐싱: compactMap은 stockCode 기반, pipeline은 (stockCode, questionType) 기반.
같은 세션 내 동일 기업 반복 질문 시 재계산 회피.
"""

from __future__ import annotations

import logging
from typing import Any

from dartlab.core.memory import BoundedCache

_log = logging.getLogger(__name__)

# 캐시: compactMap(stockCode) + pipeline(stockCode:questionType)
_compactMapCache = BoundedCache(max_entries=20, pressure_mb=800.0)
_pipelineCache = BoundedCache(max_entries=30, pressure_mb=800.0)


def buildBriefing(
    company: Any,
    question: str,
    *,
    reportMode: bool = False,
) -> str:
    """Analysis Briefing 생성.

    Args:
        company: Company 객체
        question: 사용자 질문
        reportMode: 리포트 모드 (더 상세한 분석)

    Returns:
        마크다운 텍스트 (compact map + 분석 결과)
    """
    parts: list[str] = []

    # 1. Compact Map (프로필 -- 항상 포함)
    compactMap = _cachedCompactMap(company)
    if compactMap:
        parts.append(compactMap)

    # 2. Pipeline (질문 유형별 사전분석)
    pipelineResult = _cachedPipeline(company, question)
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
        primaryCompany,
        question,
        reportMode=reportMode,
    )
    if mainBriefing:
        parts.append(mainBriefing)
        corpName = getattr(primaryCompany, "corpName", "?")
        events.append(("_briefing", f"{corpName} 분석 브리핑"))

    # 추가 기업: compact map만 (비교용)
    for comp in companies:
        if comp is primaryCompany:
            continue
        try:
            extraMap = _cachedCompactMap(comp)
            if extraMap:
                parts.append(extraMap)
                code = getattr(comp, "stockCode", "?")
                name = getattr(comp, "corpName", "?")
                events.append((f"{code}_compactMap", f"{name} 프로필"))
        except (ValueError, FileNotFoundError, OSError, RuntimeError):
            pass

    return "\n\n".join(parts), events


def clearBriefingCache() -> None:
    """캐시 전체 초기화 (테스트/수동 리셋용)."""
    _compactMapCache.clear()
    _pipelineCache.clear()


# ── 내부 캐시 래퍼 ──────────────────────────────


def _cachedCompactMap(company: Any) -> str:
    """compactMap 캐시. stockCode 기반."""
    stockCode = getattr(company, "stockCode", getattr(company, "ticker", ""))
    if not stockCode:
        return _buildCompactMap(company)

    if stockCode in _compactMapCache:
        return _compactMapCache[stockCode]

    result = _buildCompactMap(company)
    if result:
        _compactMapCache[stockCode] = result
    return result


def _buildCompactMap(company: Any) -> str:
    """compactMap 실제 생성."""
    from dartlab.ai.context.compactMap import buildCompactMap

    return buildCompactMap(company)


def _cachedPipeline(company: Any, question: str) -> str:
    """pipeline 캐시. (stockCode, questionType) 기반."""
    stockCode = getattr(company, "stockCode", getattr(company, "ticker", ""))
    questionType = _classifyForCache(question)
    cacheKey = f"{stockCode}:{questionType}" if stockCode else ""

    if cacheKey and cacheKey in _pipelineCache:
        return _pipelineCache[cacheKey]

    result = _runPipeline(company, question)
    if cacheKey and result:
        _pipelineCache[cacheKey] = result
    return result


def _classifyForCache(question: str) -> str:
    """질문을 캐시 키용 유형으로 분류."""
    try:
        from dartlab.ai.conversation.templates.analysis_rules import (
            QUESTION_TYPE_MAP,
        )

        best, bestScore = "general", 0
        for qType, keywords in QUESTION_TYPE_MAP.items():
            score = sum(1 for kw in keywords if kw in question)
            if score > bestScore:
                best, bestScore = qType, score
        return best
    except (ImportError, AttributeError):
        return "general"


def _runPipeline(company: Any, question: str) -> str:
    """pipeline.py의 run_pipeline을 호출하여 분석 결과를 반환."""
    try:
        from dartlab.ai.runtime.pipeline import run_pipeline

        result = run_pipeline(company, question, included_tables=[])
        return result
    except (ImportError, AttributeError, TypeError, ValueError, OSError, RuntimeError) as e:
        _log.debug("pipeline failed: %s", e)
        return ""
