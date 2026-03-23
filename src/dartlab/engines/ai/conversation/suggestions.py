"""회사 상태에 맞는 추천 질문 생성기."""

from __future__ import annotations

from typing import Any

import polars as pl


def _hasFrame(data: Any) -> bool:
    return isinstance(data, pl.DataFrame) and data.height > 0


def _hasTimeseries(company: Any) -> bool:
    try:
        timeseries = getattr(company.finance, "timeseries", None) if hasattr(company, "finance") else None
        if callable(timeseries):
            timeseries = timeseries()
        if isinstance(timeseries, tuple):
            timeseries = timeseries[0] if timeseries else None
        return bool(timeseries)
    except (AttributeError, TypeError, ValueError):
        return False


def _pushUnique(items: list[str], question: str) -> None:
    if question and question not in items:
        items.append(question)


def suggestQuestions(company: Any) -> list[str]:
    """회사 데이터 상태에 맞춰 추천 질문 5~8개를 생성한다."""
    suggestions: list[str] = []

    _pushUnique(suggestions, "이 회사의 핵심 투자 포인트를 한눈에 정리해주세요")
    _pushUnique(suggestions, "재무건전성과 현금흐름을 함께 점검해주세요")

    if _hasFrame(getattr(company, "IS", None)):
        _pushUnique(suggestions, "최근 수익성 추세와 이익의 질을 분석해주세요")
        _pushUnique(suggestions, "매출 성장률과 영업이익률 변화의 원인을 설명해주세요")

    if _hasFrame(getattr(company, "BS", None)):
        _pushUnique(suggestions, "부채 구조와 유동성 리스크를 점검해주세요")

    if _hasFrame(getattr(company, "CF", None)):
        _pushUnique(suggestions, "영업현금흐름이 이익을 잘 따라오고 있는지 평가해주세요")

    if _hasFrame(getattr(company, "dividend", None)):
        _pushUnique(suggestions, "배당 지속가능성과 주주환원 정책을 평가해주세요")

    if _hasTimeseries(company):
        _pushUnique(suggestions, "적정 주가와 밸류에이션을 산출해주세요")
        _pushUnique(suggestions, "경기침체 시나리오에서 이 회사가 얼마나 버틸지 분석해주세요")

    topics = []
    try:
        topics = list(getattr(company, "topics", None) or [])
    except (AttributeError, TypeError):
        topics = []

    topicText = " ".join(str(topic) for topic in topics).lower()
    if "risk" in topicText or "리스크" in topicText:
        _pushUnique(suggestions, "최근 공시에서 드러난 핵심 리스크를 요약해주세요")
    if "dividend" in topicText or "배당" in topicText:
        _pushUnique(suggestions, "배당 관련 공시 문맥까지 포함해 해석해주세요")
    if "segments" in topicText or "segment" in topicText or "부문" in topicText:
        _pushUnique(suggestions, "사업부문별 실적과 성장성을 비교해주세요")

    _pushUnique(suggestions, "최근 공시 중 꼭 읽어야 할 문서를 우선순위로 골라주세요")
    return suggestions[:8]
