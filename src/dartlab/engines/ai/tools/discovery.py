"""MCP 호환 도구 디스커버리 인터페이스."""

from __future__ import annotations

from typing import Any

from dartlab.core.capabilities import (
    CapabilityChannel,
    CapabilitySpec,
    get_capability_specs,
)


def listTools(
    *,
    channel: str = "chat",
    category: str | None = None,
) -> list[dict[str, Any]]:
    """MCP tools/list 호환. CapabilitySpec에서 도구 목록 반환."""
    specs = get_capability_specs(channel=channel, category=category)
    return [_specToDict(s) for s in specs]


def describeTools(toolIds: list[str]) -> list[dict[str, Any]]:
    """MCP tools/describe 호환. 특정 도구의 상세 스키마."""
    specs = get_capability_specs()
    specMap = {s.id: s for s in specs}
    results = []
    for tid in toolIds:
        spec = specMap.get(tid)
        if spec is not None:
            results.append(_specToDetailDict(spec))
    return results


def searchTools(query: str, *, maxResults: int = 10) -> list[dict[str, Any]]:
    """키워드 기반 도구 검색. description + ai_hint + questionTypes 매칭."""
    specs = get_capability_specs(channel=CapabilityChannel.CHAT)
    queryLower = query.lower()
    queryWords = set(queryLower.split())

    scored: list[tuple[float, CapabilitySpec]] = []
    for spec in specs:
        score = 0.0
        descLower = spec.description.lower()
        hintLower = spec.ai_hint.lower() if spec.ai_hint else ""
        labelLower = spec.label.lower()

        # 정확 매칭
        if queryLower in spec.id.lower():
            score += 50.0
        if queryLower in labelLower:
            score += 40.0
        if queryLower in descLower:
            score += 30.0
        if queryLower in hintLower:
            score += 20.0

        # questionTypes 매칭
        for qt in spec.questionTypes:
            if queryLower in qt.lower():
                score += 35.0
                break

        # 단어별 매칭
        searchable = f"{spec.id} {labelLower} {descLower} {hintLower}"
        for w in queryWords:
            if w in searchable:
                score += 5.0

        if score > 0:
            scored.append((score, spec))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [_specToDict(s) for _, s in scored[:maxResults]]


def _specToDict(spec: CapabilitySpec) -> dict[str, Any]:
    """CapabilitySpec → 간결한 dict."""
    return {
        "id": spec.id,
        "label": spec.label,
        "description": spec.description[:120],
        "category": spec.category,
        "priority": spec.priority,
        "questionTypes": list(spec.questionTypes),
        "requiresCompany": spec.requires_company,
    }


def _specToDetailDict(spec: CapabilitySpec) -> dict[str, Any]:
    """CapabilitySpec → 상세 dict (파라미터 포함)."""
    return {
        "id": spec.id,
        "label": spec.label,
        "description": spec.description,
        "category": spec.category,
        "priority": spec.priority,
        "questionTypes": list(spec.questionTypes),
        "dependsOn": list(spec.dependsOn),
        "kind": spec.kind,
        "channels": list(spec.channels),
        "requiresCompany": spec.requires_company,
        "resultKind": spec.result_kind,
        "stability": spec.stability,
        "aiHint": spec.ai_hint,
        "inputSchema": spec.input_schema,
    }
