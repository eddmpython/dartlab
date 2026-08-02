"""read_capability — generated capability/docstring 검색.

generatedSpecSearch.py 의 후속. dartlab.reference.capability.search 래퍼.
"""

from __future__ import annotations

from dartlab.ai.contracts import Ref

from .types import ToolResult


def readCapability(query: str, *, limit: int = 8) -> ToolResult:
    """CAPABILITIES 검색 → apiRef + 실행 가능성 + score + payload list 반환."""
    from dartlab.reference.capability.search import searchCapabilities

    results = searchCapabilities(query or "", limit=max(1, int(limit or 8)), minScore=0.0)
    refs: list[Ref] = []
    rows: list[dict] = []
    for apiRef, entry, score in results:
        payload = {
            "apiRef": apiRef,
            "summary": str(entry.get("summary") or "")[:400],
            "engineCallable": bool(entry.get("engineCallable", False)),
            "executionGuide": str(entry.get("executionGuide") or "")[:800],
            "replacementRefs": list(entry.get("replacementRefs") or ())[:8],
            "declared": dict(entry.get("declared") or {}),
            "execution": dict(entry.get("execution") or {}),
            "args": str(entry.get("args") or "")[:800],
            "example": str(entry.get("example") or "")[:600],
            "score": score,
        }
        refs.append(
            Ref(
                id=f"api:{apiRef}",
                kind="apiRef",
                title=apiRef,
                source="dartlab.reference.capability.loadCapabilities",
                payload=payload,
            )
        )
        rows.append(
            {
                "apiRef": apiRef,
                "summary": str(entry.get("summary") or "")[:400],
                "guide": str(entry.get("guide") or "")[:800],
                "args": str(entry.get("args") or "")[:800],
                "example": str(entry.get("example") or "")[:600],
                "engineCallable": bool(entry.get("engineCallable", False)),
                "executionGuide": str(entry.get("executionGuide") or "")[:800],
                "replacementRefs": list(entry.get("replacementRefs") or ())[:8],
                "declared": dict(entry.get("declared") or {}),
                "execution": dict(entry.get("execution") or {}),
                "score": score,
            }
        )
    return ToolResult(
        ok=bool(refs),
        summary=f"capability 후보 {len(refs)}개",
        refs=refs,
        data={"capabilities": rows},
    )
