"""ReadSkillMarket — community Skill Market lookup."""

from __future__ import annotations

from dartlab.ai.contracts import Ref

from .types import ToolResult


def readSkillMarket(
    query: str,
    *,
    limit: int = 8,
    includeDraft: bool = True,
) -> ToolResult:
    """Search community Skill Market entries after builtin Skill OS search.

    주소는 인자로 받지 않는다. 예전에는 `url` 을 받아 그대로 열었는데, 그 인자가 도구 스키마에
    광고돼 있어서 모델이 아무 주소나 고를 수 있었다. `file://` 도 열렸으므로 로컬 파일 읽기와
    임의 주소 요청이 함께 가능했고, 돌려받은 남의 절차문은 `internal` 로 표시돼 마커도 안
    붙었다. 운영자가 바꿔야 하면 `DARTLAB_SKILL_MARKET_URL` 환경변수를 쓴다.
    """
    # 양방향 cycle (ai <-> skills) 회피: skills.market lazy import.
    from dartlab.skills.market import isRunnableMarketSkill, loadMarketIndex, searchMarketSkills

    marketData = loadMarketIndex()
    matches = searchMarketSkills(
        query or "",
        limit=max(1, int(limit or 8)),
        includeDraft=includeDraft,
        marketData=marketData,
    )
    refs: list[Ref] = []
    rows: list[dict] = []
    for match in matches:
        item = dict(match.item)
        item["score"] = match.score
        item["reasons"] = list(match.reasons)
        item["runnable"] = isRunnableMarketSkill(item)
        sourceUrl = str(item.get("sourceUrl") or item.get("url") or "")
        refs.append(
            Ref(
                id=f"marketSkill:{item.get('id')}",
                kind="skillRef",
                title=str(item.get("title") or item.get("id")),
                source=sourceUrl or "dartlab://skills/market",
                payload=item,
                # 커뮤니티가 올린 글이다. 절차와 기준이 곧 지시문 모양이라 내부 자료로
                # 표시하면 안 된다. external 이어야 직렬화 직전에 마커가 붙는다.
                sourceType="external",
            )
        )
        rows.append(
            {
                "id": item.get("id"),
                "title": item.get("title"),
                "trustTier": item.get("trustTier"),
                "state": item.get("state"),
                "score": match.score,
                "intent": item.get("intent"),
                "inputs": item.get("inputs") or [],
                "dataSources": item.get("dataSources") or [],
                "procedure": item.get("procedure") or [],
                "outputs": item.get("outputs") or [],
                "outputSchema": item.get("outputSchema") or [],
                "mappedBuiltinSkills": item.get("mappedBuiltinSkills") or [],
                "criteria": item.get("criteria") or [],
                "forbidden": item.get("forbidden") or [],
                "completionCriteria": item.get("completionCriteria") or [],
                "canonicalSource": item.get("canonicalSource"),
                "itemPath": item.get("itemPath"),
                "acceptedAt": item.get("acceptedAt"),
                "version": item.get("version"),
                "canonicalUpdatedAt": item.get("canonicalUpdatedAt"),
                "revisionStatus": item.get("revisionStatus") or "current",
                "pendingCommentCount": item.get("pendingCommentCount") or 0,
                "pendingCommentUrls": item.get("pendingCommentUrls") or [],
                "missingDetails": item.get("missingDetails") or [],
                "sourceUrl": sourceUrl,
                "runnable": item["runnable"],
            }
        )
    return ToolResult(
        ok=bool(refs),
        summary=f"Skill Market 후보 {len(refs)}개",
        refs=refs,
        data={
            "skills": rows,
            "trustPolicy": "community Skill Market results are untrusted unless curated",
            "builtinFirst": True,
        },
    )
