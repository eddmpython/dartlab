"""artifactSync — Skill OS 산출물(6 JSON) 비파괴 동기화.

``specs/**/*.md`` (SSOT) → ``catalog/agent/web/mcp/pyodide/graph.json`` 재파생.
**기본 check** (드리프트만 보고, 쓰기 0), **명시 ``--write`` 일 때만 기록**.
CI·addEngine·addAxis·addRecipe·docs workflow 등 *자동 호출 0* (수동 전용).

2026-05-12 ``b6090528b`` 로 폐기된 ``compiler.py`` 의 결정적 derivation 을 복원하되,
무단 auto-overwrite 가 아니라 *check 우선 수동 도구* 로 재설계한다
(자동 sync 금지 / 수동 sync 허용). 6 JSON 은 100%
.md 파생·손가공 전용 필드 0 이라, 기본 check 가 쓰기 전 변경분을 운영자에게 보여준다.

사용::

    uv run python -X utf8 -m dartlab.skills.artifactSync            # check (드리프트 보고)
    uv run python -X utf8 -m dartlab.skills.artifactSync --write    # 재생성 기록
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from .registry import listSkills

# 전체 카탈로그 파일명. EDGAR 공시 index.json(gather/edgar) 과 충돌 회피 + "skills 카탈로그" 명시.
_FULL_CATALOG = "catalog.json"

_CATEGORY_META: dict[str, dict[str, str]] = {
    "start": {
        "title": "Start",
        "description": "설치, 첫 실행, skill catalog 사용법처럼 처음 진입할 때 필요한 절차.",
    },
    "runtime": {
        "title": "Runtime",
        "description": "Local Python, Pyodide, Web AI, MCP, VSCode 같은 실행 환경별 제약과 근거 흐름.",
    },
    "operation": {
        "title": "Operation",
        "description": "ops 원문을 skill 절차로 묶어 테스트, 문서, 릴리즈, 확장 규칙을 찾는 운영 지도.",
    },
    "engines": {
        "title": "Engines",
        "description": "엔진별 기본 사용법과 그 엔진이 소유한 응용 실행 스킬.",
    },
    "recipes": {
        "title": "Recipes",
        "description": "엔진을 엮어 특정 분석 질문을 푸는 재사용 절차.",
    },
    "user": {
        "title": "User Skills",
        "description": "프로젝트 또는 사용자 확장 skill. 배포 산출물에는 기본 포함하지 않는다.",
    },
}
_CATEGORY_ORDER = ("start", "runtime", "operation", "engines", "recipes", "user")


def deriveArtifacts(*, includeUser: bool = False) -> dict[str, Any]:
    """specs SkillSpec → 6 JSON payload (파일명 → payload) 결정적 재파생.

    Args:
        includeUser: True 면 project-local user skill 까지 포함. 배포 산출물 기본 False.

    Returns:
        ``dict[str, Any]`` — ``{catalog.json, agent.json, mcp.json, web.json,
        pyodide.json, graph.json}`` 각 payload (직렬화 전 순수 dict/list).

    Raises:
        ValueError: SkillSpec lint 실패 또는 잘못된 capability ref (listSkills 경유).

    Example:
        >>> sorted(deriveArtifacts())  # doctest: +SKIP
        ['agent.json', 'catalog.json', 'graph.json', 'mcp.json', 'pyodide.json', 'web.json']
    """
    skills = listSkills(includeUser=includeUser)
    categories = _orderedCategories({skill.category for skill in skills})
    searchIndex = [_searchDoc(skill) for skill in skills]
    meta = {
        "entrySkillId": "start.dartlabSkillOs",
        "canonicalSurface": "DartLab Skill OS",
        "skillCount": len(skills),
        "categories": [
            {
                "id": category,
                **_categoryMeta(category),
                "count": sum(1 for skill in skills if skill.category == category),
            }
            for category in categories
        ],
        "sourcePolicy": "Skills are public execution documents. API and behavior changes must update related skills.",
    }
    pyodideManifest = [
        _pyodideDoc(skill) for skill in skills if _runtimeStatus(skill, "pyodide") in {"supported", "limited"}
    ]
    return {
        _FULL_CATALOG: {"meta": meta, "skills": searchIndex},
        "agent.json": {"meta": meta, "skills": searchIndex},  # catalog 와 동일 직렬화 (소비자만 다름)
        "mcp.json": {"meta": meta, "skills": [_mcpDoc(skill, allSkills=skills) for skill in skills]},
        "web.json": {"meta": meta, "skills": [_webDoc(skill) for skill in skills]},
        "pyodide.json": {"skills": pyodideManifest},
        "graph.json": _buildGraphPayload(skills),
    }


def syncArtifacts(*, write: bool = False, webDir: str | Path | None = None, includeUser: bool = False) -> int:
    """6 JSON 을 .md 파생본과 동기화 — 기본 check(드리프트 보고), write 시 기록.

    Args:
        write: True 면 파생본을 파일에 기록. False(기본) 면 드리프트만 보고하고 쓰지 않는다.
        webDir: 산출물 디렉터리. None 이면 ``src/dartlab/skills``.
        includeUser: user skill 포함 여부 (배포 기본 False).

    Returns:
        ``int`` — check 모드: 드리프트 있으면 1, 없으면 0. write 모드: 항상 0.

    Raises:
        OSError: write 모드에서 파일 기록 실패.

    Example:
        >>> syncArtifacts()  # doctest: +SKIP  — check, 드리프트 없으면 0
        0
    """
    artifacts = deriveArtifacts(includeUser=includeUser)
    outDir = Path(webDir) if webDir is not None else Path(__file__).resolve().parent
    if write:
        outDir.mkdir(parents=True, exist_ok=True)
        for name, payload in artifacts.items():
            _writeJson(outDir / name, payload)
        print(f"[artifactSync] {len(artifacts)} JSON 기록 → {outDir}")
        return 0

    driftLines: list[str] = []
    for name, payload in artifacts.items():
        driftLines.extend(_diffArtifact(outDir / name, name, payload))
    if not driftLines:
        print("[artifactSync] check 통과 — 6 JSON 이 specs 와 동기 상태.")
        return 0
    print("[artifactSync] 드리프트 검출 (--write 로 재생성):")
    for line in driftLines:
        print(f"  {line}")
    return 1


def _diffArtifact(path: Path, name: str, derived: Any) -> list[str]:
    """on-disk JSON 과 파생본 비교 — 드리프트 사람용 요약 라인. 파싱 비교(공백 무시)."""
    if not path.exists():
        return [f"{name}: 파일 없음 (생성 필요)"]
    try:
        existing = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"{name}: 읽기/파싱 실패 ({exc})"]
    if existing == derived:
        return []
    lines = [f"{name}: 드리프트"]
    existingSkills = _skillsById(existing)
    derivedSkills = _skillsById(derived)
    added = sorted(set(derivedSkills) - set(existingSkills))
    removed = sorted(set(existingSkills) - set(derivedSkills))
    changed = sorted(i for i in (set(existingSkills) & set(derivedSkills)) if existingSkills[i] != derivedSkills[i])
    if added:
        lines.append(f"  + 추가 {len(added)}: {', '.join(added[:8])}")
    if removed:
        lines.append(f"  - 제거 {len(removed)}: {', '.join(removed[:8])}")
    if changed:
        lines.append(f"  ~ 변경 {len(changed)}: {', '.join(changed[:8])}")
    if not (added or removed or changed):
        lines.append("  (meta 또는 비-skills 필드 차이)")
    return lines


def _skillsById(payload: Any) -> dict[str, Any]:
    """payload 의 skills[] 를 id→entry map 으로 (skills 없는 graph payload 는 빈 dict)."""
    if not isinstance(payload, dict):
        return {}
    return {s.get("id"): s for s in payload.get("skills", []) if isinstance(s, dict)}


def _mcpDoc(skill: Any, *, allSkills: list[Any]) -> dict[str, Any]:
    """외부 LLM(MCP) 용 경량 문서 — 5 핵심 필드 + nextSkills max 5 + bodyPreview.

    Args:
        skill: SkillSpec.
        allSkills: nextSkills chain hint 검증용 전체 skill.

    Returns:
        ``dict`` — id/title/category/purpose/whenToUse/nextSkills/bodyPreview.

    Raises:
        없음.

    Example:
        >>> _mcpDoc(spec, allSkills=specs)["id"]  # doctest: +SKIP
    """
    allIds = {s.id for s in allSkills}
    nextSkills: list[str] = []
    for fieldName in ("linkedSkills", "successors", "succeededBy"):
        for raw in getattr(skill, fieldName, None) or []:
            if not isinstance(raw, str):
                continue
            ref = raw.strip().strip('"').strip("'")
            if ref and ref in allIds and ref not in nextSkills:
                nextSkills.append(ref)
            if len(nextSkills) >= 5:
                break
        if len(nextSkills) >= 5:
            break
    directives = _splitDirectives(str(skill.source.get("body") or ""))
    bodyPreview = directives.get("llm") or (str(skill.source.get("body") or "")[:600])
    return {
        "id": skill.id,
        "title": _publicText(skill.title),
        "category": skill.category,
        "purpose": _publicText(skill.purpose),
        "whenToUse": _publicList(skill.whenToUse),
        "nextSkills": nextSkills,
        "bodyPreview": bodyPreview,
    }


def _webDoc(skill: Any) -> dict[str, Any]:
    """사람(랜딩) 용 풍부 문서 — ``_searchDoc`` + humanIntro/visualRefs/bodyHuman.

    Args:
        skill: SkillSpec.

    Returns:
        ``dict`` — ``_searchDoc`` 전 필드 + humanIntro + visualRefs + bodyHuman.

    Raises:
        없음.

    Example:
        >>> _webDoc(spec)["humanIntro"]  # doctest: +SKIP
    """
    base = _searchDoc(skill)
    body = str(skill.source.get("body") or "")
    directives = _splitDirectives(body)
    base["humanIntro"] = getattr(skill, "humanIntro", None)
    base["visualRefs"] = _publicList(getattr(skill, "visualRefs", None) or [])
    # for-human directive 가 있으면 그 블록만, 없으면 전체 본문(사람 detail page 용 — None 금지).
    base["bodyHuman"] = directives.get("human") or body or None
    return base


def _splitDirectives(body: str) -> dict[str, str]:
    """본문 안 ``:::for-llm`` / ``:::for-agent`` / ``:::for-human`` directive 추출.

    Args:
        body: frontmatter 뒤 본문.

    Returns:
        ``dict`` — key 가 ``llm``/``agent``/``human``, 값이 해당 블록 join (없으면 미포함).

    Raises:
        없음.

    Example:
        >>> _splitDirectives(":::for-llm\\nshort\\n:::end")
        {'llm': 'short'}
    """
    out: dict[str, list[str]] = {"llm": [], "agent": [], "human": []}
    pattern = re.compile(r":::for-(llm|agent|human)\s*\n(.*?)\n:::end", re.DOTALL)
    for match in pattern.finditer(body or ""):
        audience = match.group(1)
        content = match.group(2).strip()
        if content:
            out[audience].append(content)
    return {k: "\n\n".join(v) for k, v in out.items() if v}


def _buildGraphPayload(skills: list[Any]) -> dict[str, Any]:
    """SkillSpec 리스트 → graph.json payload (nodes/edges/entries/cycles/orphans/unreachable).

    Args:
        skills: listSkills() 결과.

    Returns:
        ``dict`` — nodes + edges + entries + cycles + orphans + unreachable.

    Raises:
        없음 (검증/lint 는 graphLint.py).

    Example:
        >>> "nodes" in _buildGraphPayload(listSkills())  # doctest: +SKIP
        True
    """
    from dartlab.skills.graph import buildSkillGraph

    graph = buildSkillGraph(skills)
    return {
        "nodes": [
            {
                "id": node.id,
                "title": node.title,
                "category": node.category,
                "purpose": node.purpose,
                "inDegree": node.inDegree,
                "outDegree": node.outDegree,
                "cluster": node.cluster,
                "isEntry": node.isEntry,
                "isLeaf": node.isLeaf,
                "isOrphan": node.isOrphan,
                "audiences": list(node.audiences),
            }
            for node in graph.nodes
        ],
        "edges": [{"src": edge.src, "dst": edge.dst, "kind": edge.kind} for edge in graph.edges],
        "entries": list(graph.entryNodes),
        "cycles": [list(cycle) for cycle in graph.cycles],
        "orphans": list(graph.orphanNodes),
        "unreachable": list(graph.unreachableFromEntry),
    }


def _searchDoc(skill: Any) -> dict[str, Any]:
    """catalog/agent 용 전체 검색 문서 — frontmatter + 공개 리스트 + bodyPreview(1500) 직렬화."""
    from dartlab.skills.registry import _stepsFromRecipeBody

    body = str(skill.source.get("body") or "")
    recipeSteps = list(skill.recipeSteps) if skill.recipeSteps else _stepsFromRecipeBody(body)
    directives = _splitDirectives(body)
    bodyPreview = directives.get("agent") or directives.get("llm") or body[:1500]
    return {
        "id": skill.id,
        "bodyPreview": bodyPreview,
        "title": _publicText(skill.title),
        "category": skill.category,
        "categoryTitle": _categoryMeta(skill.category)["title"],
        "kind": skill.kind,
        "status": skill.status,
        "purpose": _publicText(skill.purpose),
        "whenToUse": _publicList(skill.whenToUse),
        "inputs": _publicList(skill.inputs),
        "requiredInputs": _publicList(skill.requiredInputs),
        "outputs": _publicList(skill.outputs),
        "apiRefs": _publicList(skill.capabilityRefs),
        "toolRefs": _publicList(skill.toolRefs),
        "datasetRefs": _publicList(skill.datasetRefs),
        "knowledgeRefs": _publicList(skill.knowledgeRefs),
        "linkedSkills": _publicList(skill.linkedSkills),
        "requires": _publicList(skill.requires),
        "alternatives": _publicList(skill.alternatives),
        "succeededBy": _publicList(skill.succeededBy),
        "deprecatedBy": _publicList(skill.deprecatedBy),
        "sourceRefs": _publicList(skill.sourceRefs),
        "procedure": _publicList(skill.procedure),
        "recipeSteps": recipeSteps,
        "requiredEvidence": _publicList(skill.requiredEvidence),
        "expectedOutputs": _publicList(skill.expectedOutputs),
        "visualGuidance": _publicList(skill.visualGuidance),
        "failureModes": _publicList(skill.failureModes),
        "forbidden": _publicList(skill.forbidden),
        "examples": _publicList(skill.examples),
        "runtimeCompatibility": skill.runtimeCompatibility,
    }


def _pyodideDoc(skill: Any) -> dict[str, Any]:
    """Pyodide(브라우저) 용 — runtimeCompatibility.pyodide.* 직통."""
    pyodide = skill.runtimeCompatibility.get("pyodide", {})
    return {
        "id": skill.id,
        "title": skill.title,
        "category": skill.category,
        "status": pyodide.get("status", "unknown"),
        "dataSources": pyodide.get("dataSources", []),
        "requiredSetup": pyodide.get("requiredSetup", []),
        "limitations": pyodide.get("limitations", []),
    }


def _runtimeStatus(skill: Any, runtime: str) -> str:
    value = skill.runtimeCompatibility.get(runtime, {})
    return str(value.get("status", "unknown")) if isinstance(value, dict) else "unknown"


def _publicList(values: list[Any]) -> list[str]:
    items: list[str] = []
    for value in values:
        text = _publicText(str(value))
        if text:
            items.append(text)
    return items


def _publicText(value: str) -> str:
    text = value.strip()
    if not text:
        return ""
    replacements = (
        ("docstring/generated capability", "엔진 기능 설명"),
        ("generated capability", "엔진 기능 설명"),
        ("capability-backed", "근거 기반"),
        ("skill/capability ref", "skill 문서"),
        ("capabilityRefs", "사용 기능"),
        ("capabilityRef", "사용 기능"),
        ("capability ref", "기능 참조"),
        ("capability view", "기능 설명"),
        ("capability schema", "API schema"),
        ("capability", "기능"),
    )
    for before, after in replacements:
        text = text.replace(before, after)
    return text


def _orderedCategories(categories: set[str]) -> list[str]:
    ordered = [category for category in _CATEGORY_ORDER if category in categories]
    ordered.extend(sorted(category for category in categories if category not in _CATEGORY_ORDER))
    return ordered


def _categoryMeta(category: str) -> dict[str, str]:
    return _CATEGORY_META.get(category, {"title": category, "description": f"{category} skill 목록."})


def _writeJson(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    """CLI 진입 — 기본 check, ``--write`` 시 기록 (자동 호출 금지, 운영자 수동)."""
    parser = argparse.ArgumentParser(description="Skill OS 6 JSON 산출물 비파괴 동기화 (check 기본 / --write 기록).")
    parser.add_argument("--write", action="store_true", help="파생본을 파일에 기록 (기본은 check 만)")
    parser.add_argument("--include-user", action="store_true", help="user skill 까지 포함")
    args = parser.parse_args(argv)
    return syncArtifacts(write=args.write, includeUser=args.include_user)


if __name__ == "__main__":
    raise SystemExit(main())
