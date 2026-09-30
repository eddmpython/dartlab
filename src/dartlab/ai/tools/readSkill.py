"""질문에 필요한 Skill 후보와 실행 계약을 짧게 반환한다. 전문은 GetSkillBody로 조회한다."""

from __future__ import annotations

from dartlab.ai.contracts import Ref

from .types import ToolResult

_BODY_PREVIEW_CHARS = 3000  # 엔진 spec p75 (~3174) 가 한 번에 들어가 GetSkillBody 추가 호출 불필요. 이전 600 자 cap 은 procedure 섹션 못 봤다 (2026-05-17 OAuth probe 회귀 — body 의 ## 공개 호출 방식 / ## 호출 동작 절차 미노출 → LLM 가 직접 dartlab.scan 호출 형태 추측 → company_not_resolved thrashing).
_PROCEDURE_SECTION_HEADINGS = ("## 공개 호출 방식", "## 호출 동작", "## 대표 반환 형태", "## 절차")

# capability auto-inline cap — top-1 후보의 capabilityRefs id 마다 CAPABILITIES dict
# 에서 payload fetch → rows[].capabilityDetails 로 inline. 이전엔 ReadSkill 후 LLM 이
# ReadCapability 자동 동행 (시그니처/args 모르니) — capability id 만 노출되어. 2026-05-18
# OAuth probe 결과 패턴: ReadSkill → ReadCapability → EngineCall. 본 옵션 ON 시 사라짐.
_CAP_FIELD_CAPS = {
    "summary": 200,
    "args": 600,
    "example": 500,
    "guide": 800,
    "capabilities": 600,
    "returns": 400,
}
# top-1 외 다른 후보는 더 짧게 (summary + args 만)
_CAP_FIELD_CAPS_OTHERS = {"summary": 200, "args": 400}


def _inlineCapabilities(
    capabilityRefs: list[str],
    *,
    isTopRank: bool,
    capabilityLimit: int | None = None,
    compact: bool = False,
) -> dict[str, dict]:
    """spec.capabilityRefs id 마다 CAPABILITIES payload fetch → trimmed dict.

    top-1 후보: 모든 capabilityRefs 의 6 필드 (summary/args/example/guide/capabilities/returns).
    그 외 후보: summary + args 만 (token 절약).

    capability 가 카탈로그에 없으면 (LLM 이 spec 본문 의지) skip — graceful.
    """
    if not capabilityRefs:
        return {}
    try:
        from dartlab.reference.capability import loadCapabilities

        CAPABILITIES = loadCapabilities()
    except Exception:  # noqa: BLE001
        return {}
    field_caps = _CAP_FIELD_CAPS if isTopRank else _CAP_FIELD_CAPS_OTHERS
    if compact:
        field_caps = {"summary": 200, "args": 600, "guide": 400}
    out: dict[str, dict] = {}
    boundedLimit = capabilityLimit if capabilityLimit is not None else (10 if isTopRank else 5)
    for ref in capabilityRefs[: max(1, min(int(boundedLimit), 12))]:
        entry = CAPABILITIES.get(ref)
        if not isinstance(entry, dict):
            continue
        trimmed: dict[str, object] = {
            "engineCallable": bool(entry.get("engineCallable", False)),
            "executionGuide": str(entry.get("executionGuide") or ""),
            "replacementRefs": list(entry.get("replacementRefs") or ())[:5],
        }
        if isTopRank and not compact and isinstance(entry.get("declared"), dict):
            trimmed["declared"] = dict(entry["declared"])
        if isTopRank and isinstance(entry.get("execution"), dict):
            trimmed["execution"] = dict(entry["execution"])
            if compact:
                trimmed["execution"].pop("nativeExample", None)
                trimmed.pop("executionGuide", None)
                trimmed.pop("replacementRefs", None)
        for field, cap in field_caps.items():
            value = entry.get(field)
            if not value:
                continue
            text = str(value)
            trimmed[field] = text[:cap] if len(text) > cap else text
        if trimmed:
            out[ref] = trimmed
    return out


def _extractProcedureSections(body: str, *, cap: int) -> str:
    """body 가 cap 보다 길면 procedure 섹션 우선 추출 — 절차가 빠지는 회귀 방지.

    1) body ≤ cap → 그대로 반환.
    2) body > cap → '## 공개 호출 방식' / '## 호출 동작' / '## 대표 반환 형태' / '## 절차'
       섹션을 우선 cap 안에 packing. 남은 자리는 본문 앞부분 (개요/엔진 역할) 으로 채움.

    절차 섹션이 없으면 단순 truncate.
    """
    if len(body) <= cap:
        return body
    lines = body.splitlines(keepends=True)
    sections: list[tuple[str, list[str]]] = []
    current_heading: str | None = "_intro"
    current_lines: list[str] = []
    for line in lines:
        stripped = line.lstrip("# ").strip()
        if line.startswith("## "):
            if current_lines:
                sections.append((current_heading or "_intro", current_lines))
            current_heading = "## " + stripped
            current_lines = [line]
        else:
            current_lines.append(line)
    if current_lines:
        sections.append((current_heading or "_intro", current_lines))
    # 우선순위: procedure 섹션 → 그 외 → intro
    priority: dict[str, int] = {}
    for heading in _PROCEDURE_SECTION_HEADINGS:
        priority[heading] = 0
    for heading, _ in sections:
        priority.setdefault(heading, 5)
    priority["_intro"] = 9  # intro 는 마지막에
    ordered = sorted(sections, key=lambda item: priority.get(item[0], 5))
    out_parts: list[str] = []
    used = 0
    truncate_note = "\n\n_(본문 일부 — 전문은 GetSkillBody)_\n"
    for heading, body_lines in ordered:
        text = "".join(body_lines)
        if used + len(text) + len(truncate_note) <= cap:
            out_parts.append(text)
            used += len(text)
        else:
            remaining = cap - used - len(truncate_note)
            if remaining > 200:
                out_parts.append(text[:remaining])
                used += remaining
            break
    return "".join(out_parts) + truncate_note


def readSkill(
    query: str,
    *,
    limit: int = 3,
    includeUser: bool = True,
    includeBody: bool = False,
    audience: str = "analysis",
) -> ToolResult:
    """기본 세 후보와 실행 계약을 반환한다.

    Args: audience=analysis는 개발·운영 문서를 제외한다. all은 전체 카탈로그를 검색한다.
        includeBody=True는 본문과 연결 스킬을 함께 읽는 기존 호출자를 위한 옵션이다.
    Returns: 후보의 짧은 설명, 실행 인자 계약, 원문을 여는 skillRef.
    Guide: 본문 preview는 첫 후보에만 한 번 싣는다. 추가 절차는 GetSkillBody로 확인한다.
    """
    from dartlab.reference.capability.analysisGraph import coveragePacketForQuestion
    from dartlab.reference.capability.execution import isEngineCallableRef
    from dartlab.skills import describeSkill, getSkill, searchSkills

    if audience not in {"analysis", "all"}:
        return ToolResult(False, "audience는 analysis 또는 all입니다.", error="invalid_audience")
    matches = searchSkills(
        query or "",
        limit=max(1, min(int(limit or 3), 20)),
        includeUser=includeUser,
        excludeCategories=("operation", "start", "runtime") if audience == "analysis" else (),
    )
    coverage = coveragePacketForQuestion(query or "")
    coverageRefs = [str(ref) for ref in coverage.get("candidateCapabilityRefs") or []]
    refs: list[Ref] = []
    rows: list[dict] = []

    def _loadBody(skillId: str) -> str:
        try:
            described = describeSkill(skillId)
        except Exception:  # noqa: BLE001
            return ""
        if not isinstance(described, dict):
            return ""
        return ((described.get("source") or {}).get("body") or "") if described else ""

    for rank, match in enumerate(matches):
        spec = match.skill
        body = _loadBody(spec.id)

        previewCap = (_BODY_PREVIEW_CHARS if rank == 0 else 1_000) if includeBody else (900 if rank == 0 else 0)
        body_preview = _extractProcedureSections(body, cap=previewCap) if body and previewCap else ""
        payload = {
            "status": spec.status,
            "id": spec.id,
            "title": spec.title,
            "purpose": spec.purpose[:200],
            "kind": spec.kind,
            "scope": spec.scope,
            "score": match.score,
            "capabilityRefs": list(spec.capabilityRefs)[:12],
            "requiredEvidence": list(spec.requiredEvidence)[:16],
        }
        if includeBody:
            payload["body"] = body
            payload["bodyPreview"] = body_preview
        refs.append(
            Ref(
                id=f"skill:{spec.id}",
                kind="skillRef",
                title=spec.title,
                source=f"dartlab://skills/{spec.id}",
                payload=payload,
            )
        )
        # Chain — linkedSkills 우선 + succeededBy 합류 (중복 제거). LLM 이 다음 호출 가이드.
        next_skills = list(spec.linkedSkills or [])
        for sid in spec.succeededBy or ():
            if sid not in next_skills:
                next_skills.append(sid)
        next_skills = next_skills[:5]

        # Skill pack chain expansion — top-1 후보 한정으로 linkedSkills/succeededBy 본문도
        # 같은 ReadSkill 응답에 inline. 사용자 직관 ("스킬팩 = 연결연결, 다 안 읽으면
        # 절차 끊김") 정공: top 후보 하나만 골랐을 때 LLM 이 GetSkillBody 추가 호출 없이
        # 체인 전체 (max 3 노드) 를 한 번에 본다. cap 자체는 절차 섹션 우선 추출이라 inline
        # 노드당 ~2k chars → 3 노드 = 6k chars 한도. 추가 비용 ~1.5k token (수용).
        chain_inline: list[dict] = []
        if includeBody and rank == 0 and next_skills:
            seen = {spec.id}
            for linked_id in next_skills[:3]:
                if linked_id in seen:
                    continue
                seen.add(linked_id)
                try:
                    linked_spec = getSkill(linked_id, includeUser=includeUser)
                except Exception:  # noqa: BLE001
                    continue
                linked_body = _loadBody(linked_spec.id)
                chain_inline.append(
                    {
                        "id": linked_spec.id,
                        "title": linked_spec.title,
                        "kind": linked_spec.kind,
                        "purpose": linked_spec.purpose,
                        "whenToUse": list(linked_spec.whenToUse),
                        "capabilityRefs": list(linked_spec.capabilityRefs),
                        "requiredEvidence": list(linked_spec.requiredEvidence),
                        "bodyPreview": _extractProcedureSections(linked_body, cap=1_200) if linked_body else "",
                        "bodyTruncated": bool(linked_body) and len(linked_body) > 1_200,
                    }
                )

        # capability auto-inline — capabilityRefs id 마다 CAPABILITIES payload 자동 fetch.
        # top-1 후보: 6 필드 (summary/args/example/guide/capabilities/returns).
        # 그 외: summary + args 만. → ReadCapability 자동 동행 회귀 해소.
        explicitRefs = list(spec.capabilityRefs)
        executableRefs = [ref for ref in explicitRefs if isEngineCallableRef(ref)]
        combinedRefs = list(dict.fromkeys([*executableRefs[:2], *(coverageRefs if rank == 0 else []), *explicitRefs]))
        capability_details = (
            _inlineCapabilities(combinedRefs, isTopRank=True, capabilityLimit=8, compact=not includeBody)
            if rank == 0
            else {}
        )

        rows.append(
            {
                "id": spec.id,
                "title": spec.title,
                "kind": spec.kind,
                "scope": spec.scope,
                "status": spec.status,
                "trustTier": "localUserDraft" if spec.scope == "user" else "builtin",
                "score": match.score,
                "purpose": spec.purpose[:300],
                "whenToUse": list(spec.whenToUse)[:3],
                "capabilityRefs": list(spec.capabilityRefs)[:12],
                "coverageCapabilityRefs": coverageRefs if rank == 0 else [],
                "capabilityDetails": capability_details,
                "requiredEvidence": list(spec.requiredEvidence)[:16],
                "expectedOutputs": list(spec.expectedOutputs)[:3],
                "visualGuidance": list(spec.visualGuidance)[:8],
                "visualRefs": list(spec.visualRefs)[:8],
                "nextSkills": next_skills,
                "bodyPreview": body_preview,
                "bodyTruncated": bool(body) and len(body) > previewCap,
                "chainInline": chain_inline,  # top-1 만 채워짐. 나머지는 빈 list.
            }
        )
    return ToolResult(
        ok=bool(refs),
        summary=f"Skill OS 후보 {len(refs)}개"
        + (f" (+ chain {len(rows[0]['chainInline'])})" if rows and rows[0].get("chainInline") else ""),
        refs=refs,
        data={
            "skills": rows,
            "coverage": coverage,
            "more": "GetSkillBody(skillId)로 절차 전문, ReadCapability(query)로 추가 실행 계약을 조회할 수 있습니다.",
        },
    )


def getSkillBody(skillId: str, *, includeUser: bool = True) -> ToolResult:
    """단일 skill 의 raw markdown 본문 fetch.

    read_skill 이 default 로 bodyPreview 만 노출해 LLM context 를 아낀 뒤,
    특정 skill 의 *공개 호출 방식 / 호출 동작 / 대표 반환 형태* 같은 본문 절차가
    필요하면 이 도구로 단일 skill 본문을 가져온다.
    """
    from dartlab.skills import describeSkill, getSkill

    if not skillId or not str(skillId).strip():
        return ToolResult(
            ok=False,
            summary="skillId 가 비어 있습니다.",
            error="missing_skill_id",
        )
    skill_id = str(skillId).strip()
    try:
        spec = getSkill(skill_id, includeUser=includeUser)
    except KeyError:
        from dartlab.skills import searchSkills

        alternatives = [
            {"skillId": match.skill.id, "title": match.skill.title}
            for match in searchSkills(skill_id, limit=3, includeUser=includeUser)
        ]
        return ToolResult(
            ok=False,
            summary=f"Skill 없음: {skill_id}. availableSkills의 실제 skillId를 선택하세요.",
            error="skill_not_found",
            data={"availableSkills": alternatives},
        )
    body = ""
    try:
        described = describeSkill(spec.id)
        body = ((described or {}).get("source") or {}).get("body", "") if isinstance(described, dict) else ""
    except Exception:  # noqa: BLE001
        body = ""
    payload = spec.toDict()
    payload["body"] = body
    payload["bodyChars"] = len(body)
    return ToolResult(
        ok=True,
        summary=f"Skill 본문: {spec.id}",
        refs=[
            Ref(
                id=f"skill:{spec.id}",
                kind="skillRef",
                title=spec.title,
                source=f"dartlab://skills/{spec.id}",
                payload=payload,
            )
        ],
        data=payload,
    )
