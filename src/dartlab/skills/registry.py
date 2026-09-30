"""Skill registry and linting for shared DartLab execution skills."""

from __future__ import annotations

import builtins
import json
import logging
import os
import re
from pathlib import Path
from typing import Any

from .models import EvidenceCheckResult, SkillMatch, SkillSpec

logger = logging.getLogger(__name__)

_FORBIDDEN_TEMPLATE_MARKERS = ("final answer", "최종 답변:", "답변 템플릿", "{{answer", "{answer}")
_MAX_PROCEDURE_ITEM_CHARS = 1200
_TICKER_QUERY_RE = re.compile(r"\b[A-Z]{1,5}\b")
_INTENT_BOOSTS_CACHE: tuple[dict[str, Any], ...] | None = None
_INTENT_BOOSTS_SOURCE = "specs/operation/intentBoosts.md"

# 0.10 — listSkills() 가 호출마다 74+N skill 의 lint 재실행으로 e2e probe 에서 alias 호출이 11s
# 까지 걸리는 회귀 발견. process-lifetime 캐시로 해소. dev 에서 spec 바로 반영 필요 시
# DARTLAB_SKILL_NO_CACHE=1 환경변수로 우회. user spec 변경은 process restart 까지 미적용.
_LIST_SKILLS_CACHE: dict[bool, tuple[SkillSpec, ...]] = {}
_KNOWN_CAPS_CACHE: frozenset[str] | None = None


def _skillsCacheDisabled() -> bool:
    return os.environ.get("DARTLAB_SKILL_NO_CACHE") == "1"


def _loadIntentBoosts() -> tuple[dict[str, Any], ...]:
    """``operation.intentBoosts`` skill frontmatter 에서 의도 boost 규칙을 로드.

    SSOT 는 ``src/dartlab/skills/specs/operation/intentBoosts.md`` 의 frontmatter
    ``intentBoosts[]``. 코드 하드코딩 금지 — 새 규칙은 markdown 에만 추가한다.
    Lazy 캐시 — 첫 호출 시 로드, 이후 동일 tuple 재사용.
    """
    global _INTENT_BOOSTS_CACHE
    if _INTENT_BOOSTS_CACHE is not None:
        return _INTENT_BOOSTS_CACHE
    path = _builtinSpecsRoot() / "operation" / "intentBoosts.md"
    if not path.exists():
        _INTENT_BOOSTS_CACHE = ()
        return _INTENT_BOOSTS_CACHE
    data = _readMapping(path)
    raw = data.get("intentBoosts") or []
    out: list[dict[str, Any]] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        skillIds = tuple(entry.get("skillIds") or ())
        terms = tuple(entry.get("terms") or ())
        boost = entry.get("boost")
        if not skillIds or not terms or boost is None:
            continue
        try:
            boost_val = float(boost)
        except (TypeError, ValueError):
            continue
        out.append({"skillIds": skillIds, "terms": terms, "boost": boost_val})
    _INTENT_BOOSTS_CACHE = tuple(out)
    return _INTENT_BOOSTS_CACHE


_MANUAL_SKILL_CATEGORIES = {"start", "runtime", "operation", "engines", "recipes", "user"}


def listSkills(*, includeUser: bool = True) -> list[SkillSpec]:
    """Skill 목록 — builtin 과 user skill 을 함께 반환.

    Description
    -----------
    DartLab 공용 실행 스킬을 로드한다. builtin skill 은 `dartlab.skills`
    package 안의 `specs/**` Markdown source 만 읽는다. capability/docstring 기반
    자동 skill 은 생성하지 않는다. user skill 은 project-local
    `.dartlab/skills`에서 읽는다.

    Parameters
    ----------
    includeUser : bool, optional
        True 면 현재 workspace 의 user skill 도 포함한다.

    Returns
    -------
    list[SkillSpec]
        id : str — skill 식별자
        kind : str — generated/curated/user
        scope : str — builtin/project/user
        status : str — 검증 상태

    Raises
    ------
    ValueError
        skill spec lint 실패.

    Examples
    --------
    >>> any(s.id == "engines.scan.krxIndexStrength" for s in listSkills())
    True

    Notes
    -----
    Skill 은 공개 호출 방식, 동작, 대표 반환 형태, 검증 기준을 담는 실행 문서다.

    Guide
    -----
    사용자 확장은 `.dartlab/skills/**/*.md`에 둔다. 공개 API 변경이나 운영 방식 변경이 있으면 관련 skill 도 함께 갱신한다.

    See Also
    --------
    searchSkills : 질의 기반 skill 검색.
    """

    if not _skillsCacheDisabled():
        cached = _LIST_SKILLS_CACHE.get(includeUser)
        if cached is not None:
            return list(cached)

    # builtin spec — 정상 contract 는 모두 통과해야 하지만, 1 개의 frontmatter 누락이 전체
    # ReadSkill 검색을 마비시키면 ask mode 자체가 죽는다 (2026-05-17 OAuth probe 6/6 에서
    # cardCatalog.md WIP frontmatter 누락 → ReadSkill cascade ValueError 발견). 따라서 runtime
    # 은 user spec 과 동일하게 spec 단위 skip + 경고. 엄격 검증은 `verifyAllBuiltinSpecsStrict()`
    # 가 CI / test 에서 명시 호출 (tests/skills/test_skills.py::test_all_builtin_specs_lint_clean).
    specs: list[SkillSpec] = []
    for path in _builtinSpecPaths():
        try:
            spec = _loadSpec(path, defaultScope="builtin")
        except Exception as exc:  # noqa: BLE001
            logger.warning("builtin skill spec skipped on load (%s): %s", path.name, exc)
            continue
        specs.append(spec)
    if includeUser:
        # user spec 은 실험적 — 1 개 깨져도 전체 listSkills 가 무너지면 ReadSkill tool 자체가
        # 못 돈다. spec 단위로 skip + 경고. lintSkill 도 동일 — user spec 1 개의 lint 실패가
        # 전체 검색을 막지 않게.
        for path in _userSpecPaths():
            try:
                spec = _loadSpec(path, defaultScope="user", forceUser=True)
            except Exception as exc:  # noqa: BLE001
                logger.warning("user skill spec skipped (%s): %s", path.name, exc)
                continue
            try:
                lintSkill(spec)
            except Exception as exc:  # noqa: BLE001
                logger.warning("user skill spec failed lint (%s): %s", path.name, exc)
                continue
            specs.append(spec)
    _validateUniqueIds(specs)
    valid_specs: list[SkillSpec] = []
    for spec in specs:
        if spec.scope == "builtin":
            try:
                lintSkill(spec)
            except Exception as exc:  # noqa: BLE001
                logger.warning("builtin skill spec failed lint, skipped (%s): %s", spec.id, exc)
                continue
        valid_specs.append(spec)
    result = sorted(valid_specs, key=lambda item: item.id)
    _warnGraphIntegrityOnce(result)

    if not _skillsCacheDisabled():
        _LIST_SKILLS_CACHE[includeUser] = tuple(result)
    return result


def verifyAllBuiltinSpecsStrict() -> None:
    """모든 builtin spec 의 load + lint 를 strict 모드로 검증 (실패 시 첫 실패에서 raise).

    listSkills 는 runtime resilience 를 위해 broken builtin 을 skip + warn 하지만,
    CI / test 는 contract 위반을 fail-loud 로 잡아야 한다. 본 함수가 그 strict gate.

    Raises
    ------
    ValueError
        builtin spec load 또는 lint 실패. message 에 file path + 원인 포함.
    """
    failures: list[str] = []
    for path in _builtinSpecPaths():
        try:
            spec = _loadSpec(path, defaultScope="builtin")
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{path.name}: load 실패 — {type(exc).__name__}: {exc}")
            continue
        try:
            lintSkill(spec)
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{spec.id} ({path.name}): lint 실패 — {exc}")
    if failures:
        raise ValueError("builtin skill spec contract 위반:\n  - " + "\n  - ".join(failures))


_GRAPH_WARNED = False


def _warnGraphIntegrityOnce(specs: list[SkillSpec]) -> None:
    """그래프 정합성 lint — 모듈 lifetime 1 회.

    Description
    -----------
    listSkills 호출 시 1 회만 실행. 깨진 ref · 3+ SCC · orphan · unreachable 카운트
    출력. 두 모드:

    - **phase 1 warn-only (기본)** — `logger.warning` 만 출력. raise 없음.
    - **phase 2 strict** (`DARTLAB_SKILL_GRAPH_LINT_STRICT=1`) — broken ref 또는
      3+ SCC 가 1 건이라도 있으면 ``ValueError`` raise. orphan / unreachable 은
      여전히 warn (사용자 손작업 결).

    환경변수:
    - `DARTLAB_SKILL_GRAPH_LINT=1` — phase 1 warn 출력 활성 (기본 off).
    - `DARTLAB_SKILL_GRAPH_LINT_STRICT=1` — phase 2 활성 (신규/수정 spec 차단).

    기본 off — listSkills 호출이 잦은 결 (MCP / ask / `import dartlab`) 결로 매번
    warn 출력 결이 시끄러운 결. 운영자가 점검 결로 명시 활성. 별도 점검 결은
    `src/dartlab/skills/skillGraphOrphanReport.py` 결로 가능.

    phase 2 활성 시 listSkills 호출이 ValueError 로 차단되어 검색 cascade
    영향. 운영자가 broken / cycle 0 으로 만든 후에만 켤 것 (feedback_skill_os_dogfood
    메모리 참조).
    """
    global _GRAPH_WARNED
    if _GRAPH_WARNED:
        return
    import os

    if os.environ.get("DARTLAB_SKILL_GRAPH_LINT", "0") != "1":
        _GRAPH_WARNED = True
        return
    strict = os.environ.get("DARTLAB_SKILL_GRAPH_LINT_STRICT", "0") == "1"
    try:
        from .graph import buildSkillGraph
        from .graphLint import detectThreePlusCycles, reportOrphans, validateReachability, validateRefExistence

        all_ids = frozenset(s.id for s in specs)
        graph = buildSkillGraph(specs)
        broken_total = 0
        for s in specs:
            broken_total += len(validateRefExistence(s, all_ids))
        cycles = detectThreePlusCycles(graph)
        orphans = reportOrphans(graph)
        unreachable = validateReachability(graph)
        if broken_total or cycles or orphans or unreachable:
            phase = "phase2 strict" if strict else "phase1 warn"
            logger.warning(
                "[skill-graph] %s — broken=%d cycles=%d orphans=%d unreachable=%d",
                phase,
                broken_total,
                len(cycles),
                len(orphans),
                len(unreachable),
            )
            if strict and (broken_total or cycles):
                _GRAPH_WARNED = True
                raise ValueError(
                    f"[skill-graph] phase2 strict — broken={broken_total} cycles={len(cycles)} "
                    "blocking listSkills. fix or unset DARTLAB_SKILL_GRAPH_LINT_STRICT."
                )
    except ValueError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.warning("[skill-graph] lint 자체 실패: %s", exc)
    _GRAPH_WARNED = True


def getSkill(skillId: str, *, includeUser: bool = True) -> SkillSpec:
    """id 로 SkillSpec 조회."""

    for spec in listSkills(includeUser=includeUser):
        if spec.id == skillId:
            return spec
    raise KeyError(f"unknown DartLab skill: {skillId}")


def searchSkills(
    query: str, *, limit: int = 8, includeUser: bool = True, excludeCategories: tuple[str, ...] = ()
) -> list[SkillMatch]:
    """Skill 검색 — 분석 목적과 capability ref 를 기준으로 매칭."""

    terms = _terms(query)
    matches: list[SkillMatch] = []
    for spec in listSkills(includeUser=includeUser):
        if spec.category in excludeCategories:
            continue
        score, reasons = _score(spec, terms, query=query)
        if score > 0 or not terms:
            matches.append(SkillMatch(skill=spec, score=score, reasons=reasons))
    return sorted(matches, key=lambda item: (item.score, item.skill.status == "official", item.skill.id), reverse=True)[
        :limit
    ]


def describeSkill(skillId: str, *, includeUser: bool = True) -> dict[str, Any]:
    """Skill 설명 dict 반환."""

    return getSkill(skillId, includeUser=includeUser).toDict()


def checkEvidence(
    skillId: str, refs: list[dict[str, Any]] | list[Any], *, includeUser: bool = True
) -> EvidenceCheckResult:
    """Skill evidence 충족도 확인.

    Notes
    -----
    이 검사는 근거 이름의 존재 여부를 보는 경량 점검이다. 숫자·날짜 claim 의
    실제 값 대조는 Ask Workbench verifier 가 담당한다.
    """

    spec = getSkill(skillId, includeUser=includeUser)
    present_names = _evidenceNames(refs)
    required = set(spec.requiredEvidence)
    present = sorted(required & present_names)
    missing = sorted(required - present_names)
    return EvidenceCheckResult(ok=not missing, skillId=spec.id, present=present, missing=missing)


def lintSkill(spec: SkillSpec) -> None:
    """SkillSpec 정합성 검사."""

    if not spec.id or not spec.title or not spec.purpose:
        raise ValueError("skill id/title/purpose are required")
    for item in [*spec.procedure, *spec.examples]:
        if len(item) > _MAX_PROCEDURE_ITEM_CHARS:
            raise ValueError(f"skill {spec.id} contains an oversized procedure/example item")
        lowered = item.lower()
        if any(marker in lowered for marker in _FORBIDDEN_TEMPLATE_MARKERS):
            raise ValueError(f"skill {spec.id} contains a final-answer template marker")
    _validateRuntimeCompatibility(spec)
    _validateStatusEvidence(spec)
    if spec.kind == "curated" and "pyodide" not in spec.runtimeCompatibility:
        raise ValueError(f"curated skill {spec.id} must declare runtimeCompatibility.pyodide")
    if spec.kind == "recipe":
        _validateRecipeSkill(spec)
    else:
        _validateExecutionSkillContract(spec)
    _validateCapabilityRefs(spec)


def _validateRecipeSkill(spec: SkillSpec) -> None:
    """recipe kind 검증 — 본문 ## 연계 절차 + linkedSkills 또는 step list 비어있지 않음.

    순환 의존 검사는 listSkills() 재귀 위험으로 본 단계에서 수행하지 않는다 — 별도
    validateRecipes() 후속 작업으로 분리. 여기서는 구조 검증만.

    gap/falsifier 첫 wave 정책: 존재하면 구조 검증, 없으면 warn-only (logger.warning).
    enforced lint 는 tests/test_recipe_lint.py 가 담당.
    """
    body = str(spec.source.get("body") or "")
    if "## 연계 절차" not in body:
        raise ValueError(f"recipe skill {spec.id} missing '## 연계 절차' section")
    has_linked = bool(spec.linkedSkills)
    has_body_steps = bool(_stepsFromRecipeBody(body))
    if not (has_linked or has_body_steps):
        raise ValueError(f"recipe skill {spec.id} must declare linkedSkills frontmatter or '## 연계 절차' step list")
    if spec.gap:
        primary = spec.gap.get("primary")
        if not isinstance(primary, list) or len(primary) < 2:
            raise ValueError(f"recipe skill {spec.id} gap.primary must be a list of ≥2 engine names (got {primary!r})")
    if spec.falsifier:
        if not isinstance(spec.falsifier.get("description"), str) or not spec.falsifier["description"].strip():
            raise ValueError(f"recipe skill {spec.id} falsifier.description must be non-empty string")


_RECIPE_STEP_RE = re.compile(r"^\s*(?:\d+\.|-)\s*([\w.]+)(?:\s*[—\-:]\s*(.*))?$")


def _stepsFromRecipeBody(body: str) -> list[dict[str, str]]:
    """recipe 본문의 '## 연계 절차' 섹션에서 step list 파싱.

    인식 형식:
        1. engines.macro — 매크로 환경
        - engines.scan — peer 5 종

    반환: [{"skillId": "engines.macro", "note": "매크로 환경"}, ...]
    """
    if not body:
        return []
    text = str(body)
    marker = "## 연계 절차"
    idx = text.find(marker)
    if idx < 0:
        return []
    section = text[idx + len(marker) :]
    next_heading = section.find("\n## ")
    if next_heading >= 0:
        section = section[:next_heading]
    steps: list[dict[str, str]] = []
    for line in section.splitlines():
        match = _RECIPE_STEP_RE.match(line)
        if not match:
            continue
        skill_id = match.group(1).strip()
        note = (match.group(2) or "").strip()
        if "." in skill_id:
            steps.append({"skillId": skill_id, "note": note})
    return steps


def _validateExecutionSkillContract(spec: SkillSpec) -> None:
    if spec.category != "engines":
        return
    body = str(spec.source.get("body") or "")
    required = (
        "## 공개 호출 방식",
        "## 호출 동작",
        "## 대표 반환 형태",
        "## 기본 검증",
    )
    missing = [heading for heading in required if heading not in body]
    if missing:
        raise ValueError(f"engine skill {spec.id} missing execution sections: {', '.join(missing)}")


def validateExecutionSkillSubstance(spec: SkillSpec) -> list[str]:
    """엔진 skill 의 강제 섹션이 *실제 내용* 을 갖는지 추가 검사 — 신규/수정 파일 게이트용.

    `lintSkill` 은 listSkills 안에서 174 개 기존 파일에 매번 호출되므로 너무 엄격한
    검사를 넣으면 회귀가 난다 (`SCHEMA.md` "174 개 기존 파일에 일괄 강제하지 않는다").
    이 함수는 `validateSkills.py` 가 신규/수정 파일에만 호출하는 *추가* 게이트 —
    빈 placeholder 섹션이 신규로 들어오는 회귀를 잡는다.

    Returns
    -------
    list[str]
        위반 메시지 list. 빈 list 면 통과.
    """
    if spec.category != "engines":
        return []
    body = str(spec.source.get("body") or "")
    required = (
        "## 공개 호출 방식",
        "## 호출 동작",
        "## 대표 반환 형태",
        "## 기본 검증",
    )
    issues: list[str] = []
    sections = _splitSections(body, required)
    for heading, sectionBody in sections.items():
        if not _sectionHasSubstance(sectionBody, heading):
            issues.append(f"engine skill {spec.id} section {heading} is empty or lacks code/table/prose substance")
    return issues


def _splitSections(body: str, headings: tuple[str, ...]) -> dict[str, str]:
    """본문에서 각 강제 헤딩 아래의 텍스트 블록을 추출.

    다음 H2 헤딩 (`## `) 이 나오기 전까지를 한 섹션으로 본다.
    """
    out: dict[str, str] = {}
    for heading in headings:
        idx = body.find(heading)
        if idx < 0:
            continue
        start = idx + len(heading)
        next_h2 = body.find("\n## ", start)
        section = body[start:] if next_h2 < 0 else body[start:next_h2]
        out[heading] = section.strip()
    return out


def _sectionHasSubstance(sectionBody: str, heading: str) -> bool:
    """섹션 본문이 빈 placeholder 가 아닌지 확인.

    `## 공개 호출 방식` 은 ``` 코드블록 1 개 이상 — 없으면 AI 가 따라 실행할 수 없다.
    `## 호출 동작` / `## 대표 반환 형태` 는 표 (`|...|---|...|`) 또는 코드블록 또는
    최소 60 자 이상의 산문.
    """
    if not sectionBody:
        return False
    if heading == "## 공개 호출 방식":
        return "```" in sectionBody
    has_code = "```" in sectionBody
    has_table = "|" in sectionBody and "---" in sectionBody
    long_prose = len(sectionBody) >= 60
    return bool(has_code or has_table or long_prose)


def _builtinSpecPaths() -> list[Path]:
    """builtin spec 전수 수집 — `.archive/` 폴더 제외.

    `.archive/` 는 drafted/unverified recipe 페르소나 보존 격리 (T4 archive).
    catalog/agent/mcp/web/pyodide/graph.json 에 미등록 + registry/landing 노출 X.
    승격 시 `recipePromote.py archive --restore <id>` 또는 git mv 로 다시 활성.
    """
    root = _builtinSpecsRoot()
    if not root.exists():
        return []
    paths: list[Path] = [
        *root.rglob("*.md"),
        *root.rglob("*.yaml"),
        *root.rglob("*.yml"),
        *root.rglob("*.json"),
    ]
    return sorted(p for p in paths if ".archive" not in p.parts and not _isDirReadme(p))


def _isDirReadme(path: Path) -> bool:
    """디렉터리 README 는 스킬이 아니라 폴더 문서 — skill discovery 에서 제외."""
    return path.name.lower() == "readme.md"


def _userSpecPaths() -> list[Path]:
    root = _repoRoot() / ".dartlab" / "skills"
    if not root.exists():
        return []
    paths: list[Path] = [
        *root.rglob("*.md"),
        *root.rglob("*.yaml"),
        *root.rglob("*.yml"),
        *root.rglob("*.json"),
    ]
    return sorted(p for p in paths if ".archive" not in p.parts and not _isDirReadme(p))


def _loadSpec(path: Path, *, defaultScope: str, forceUser: bool = False) -> SkillSpec:
    data = _readMapping(path)
    if forceUser:
        data["kind"] = "user"
        data["scope"] = "user"
        data["category"] = "user"
        data.setdefault("status", "unverified")
    else:
        data.setdefault("kind", "curated")
        data.setdefault("scope", defaultScope)
        data.setdefault("category", _categoryFromPath(path))
    data.setdefault("source", {})
    data["source"].setdefault("path", str(path))
    return SkillSpec(**_normalizeSpecData(data))


def _readMapping(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix == ".md":
        data = _readMarkdownSkill(text, path)
    elif suffix == ".json":
        data = json.loads(text)
    else:
        try:
            import yaml
        except ImportError:
            data = _readSimpleYaml(text)
        else:
            data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError(f"skill spec must be a mapping: {path}")
    return data


def _readMarkdownSkill(text: str, path: Path) -> dict[str, Any]:
    text = text.lstrip("\ufeff").lstrip()
    if not text.startswith("---"):
        raise ValueError(f"markdown skill requires frontmatter: {path}")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"markdown skill frontmatter is not closed: {path}")
    raw_meta = parts[1].strip()
    body = parts[2].strip()
    try:
        import yaml
    except ImportError:
        data = _readSimpleYaml(raw_meta)
    else:
        data = yaml.safe_load(raw_meta)
    if not isinstance(data, dict):
        raise ValueError(f"markdown skill frontmatter must be a mapping: {path}")
    data.setdefault("source", {})
    data["source"]["format"] = "markdown"
    data["source"]["body"] = body
    if body and not data.get("procedure"):
        data["procedure"] = _procedureFromMarkdownBody(body)
    if body and not data.get("purpose"):
        data["purpose"] = _shortText(body, limit=220)
    return data


def _procedureFromMarkdownBody(body: str) -> list[str]:
    items: list[str] = []
    for raw in body.splitlines():
        line = raw.strip()
        if line.startswith("- "):
            item = line[2:].strip()
            if item:
                items.append(item)
        if len(items) >= 12:
            break
    return items


def _coerceStringItem(value: Any) -> str:
    """frontmatter 의 list 항목이 dict / 숫자 / None 으로 들어와도 string 으로 강제.

    근거: SkillSpec 의 string list 필드 (procedure / examples / inputs / ...) 는
    downstream 에서 item.lower() · join 등 string 연산 가정. 운영자가 frontmatter 를
    `- key: value` (dict) 또는 `- 1.5` (숫자) 로 작성하면 type 불일치로 폭발.
    여기서 한 번 흡수해 모든 downstream (lintSkill / _joinAny / _score / 공개 dict) 안전.

    dict 우선순위 키: step / description / text / summary / title / name → 의미 있는 줄 추출.
    없으면 value 들 공백 join. 모두 실패 시 JSON 직렬화 (절대 폭발 X).
    """
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    if isinstance(value, dict):
        for key in ("step", "description", "text", "summary", "title", "name"):
            v = value.get(key)
            if isinstance(v, str) and v.strip():
                return v
        joined = " ".join(str(v) for v in value.values() if v is not None)
        if joined.strip():
            return joined
        try:
            return json.dumps(value, ensure_ascii=False)
        except (TypeError, ValueError):
            return str(value)
    return str(value)


def _normalizeSpecData(data: dict[str, Any]) -> dict[str, Any]:
    list_fields = {
        "inputs",
        "outputs",
        "whenToUse",
        "requiredInputs",
        "capabilityRefs",
        "datasetRefs",
        "toolRefs",
        "knowledgeRefs",
        "sourceRefs",
        "visualRefs",
        "linkedSkills",
        "requires",
        "alternatives",
        "succeededBy",
        "deprecatedBy",
        "procedure",
        "requiredEvidence",
        "expectedOutputs",
        "visualGuidance",
        "failureModes",
        "forbidden",
        "examples",
        "verifiedBy",
        "expectedNovelty",
        "predecessors",
        "successors",
    }
    for field in list_fields:
        value = data.get(field)
        if value is None:
            data[field] = []
        elif isinstance(value, str):
            data[field] = [value]
        else:
            data[field] = [_coerceStringItem(item) for item in builtins.list(value)]
    # recipeSteps 는 list[dict] — frontmatter 에 박혀 있을 수 있다 (운영자 명시).
    rs = data.get("recipeSteps")
    if rs is None:
        data["recipeSteps"] = []
    elif isinstance(rs, list):
        data["recipeSteps"] = [item if isinstance(item, dict) else {"skillId": str(item)} for item in rs]
    else:
        data["recipeSteps"] = []
    for field in (
        "runtimeCompatibility",
        "pyodide",
        "docs",
        "quality",
        "source",
        "gap",
        "testUniverse",
        "falsifier",
        "audiences",
    ):
        value = data.get(field)
        if value is None:
            data[field] = {}
        elif not isinstance(value, dict):
            raise ValueError(f"skill field must be a mapping: {field}")
    # validationRuns 는 list[dict] — ValidateRecipe 가 append. dict 가 아닌 항목은 drop.
    vr = data.get("validationRuns")
    if vr is None:
        data["validationRuns"] = []
    elif isinstance(vr, list):
        data["validationRuns"] = [item for item in vr if isinstance(item, dict)]
    else:
        data["validationRuns"] = []
    if data.get("pyodide") and not data["runtimeCompatibility"].get("pyodide"):
        data["runtimeCompatibility"]["pyodide"] = data["pyodide"]
    # yaml 이 따옴표 없는 ISO date (`lastUpdated: 2026-05-12`) 를 datetime.date 로 파싱한다.
    # 본 spec dict 는 JSON 직렬화 대상 (mcp/agent/web.json + MCP `_resourcePayload`) — date 객체는
    # json.dumps 가 TypeError 로 차단한다. 운영자가 따옴표 빠뜨려도 무탈하게 ISO str 로 강제.
    import datetime as _dt

    lu = data.get("lastUpdated")
    if isinstance(lu, (_dt.date, _dt.datetime)):
        data["lastUpdated"] = lu.isoformat()
    # SkillSpec field 가 아닌 frontmatter 키는 drop — markdown 에 자유 메타 (intentBoosts 등) 허용.
    import dataclasses as _dc

    spec_fields = {f.name for f in _dc.fields(SkillSpec)}
    for key in list(data.keys()):
        if key not in spec_fields:
            data.pop(key)
    return data


def _categoryFromPath(path: Path) -> str:
    specs = _builtinSpecsRoot()
    try:
        relative = path.relative_to(specs)
    except ValueError:
        return "engines"
    first = relative.parts[0] if relative.parts else "engines"
    if first in _MANUAL_SKILL_CATEGORIES:
        return first
    return "engines"


def _builtinSpecsRoot() -> Path:
    """Builtin SkillSpec root.

    `src/dartlab/skills/specs`가 repo checkout과 wheel에서 모두 같은 공식
    SkillSpec 원본이다.
    """

    return Path(__file__).resolve().parent / "specs"


def _validateUniqueIds(specs: list[SkillSpec]) -> None:
    seen: set[str] = set()
    for spec in specs:
        if spec.id in seen:
            raise ValueError(f"duplicate DartLab skill id: {spec.id}")
        seen.add(spec.id)


def _validateCapabilityRefs(spec: SkillSpec) -> None:
    if not spec.capabilityRefs:
        return
    known = _knownCapabilities()
    missing = [ref for ref in spec.capabilityRefs if ref not in known]
    if missing:
        raise ValueError(f"skill {spec.id} references unknown capabilities: {', '.join(missing)}")


def _shortText(text: str, *, limit: int = 500) -> str:
    return " ".join(text.split())[:limit]


def _knownCapabilities() -> set[str]:
    global _KNOWN_CAPS_CACHE
    if _KNOWN_CAPS_CACHE is not None and not _skillsCacheDisabled():
        return set(_KNOWN_CAPS_CACHE)
    try:
        from dartlab.reference.capability import loadCapabilities

        CAPABILITIES = loadCapabilities()
    except Exception:
        return set()
    caps = frozenset(str(key) for key in CAPABILITIES)
    _KNOWN_CAPS_CACHE = caps
    return set(caps)


def _validateRuntimeCompatibility(spec: SkillSpec) -> None:
    allowed = {"supported", "limited", "unsupported", "unknown"}
    for runtime, value in spec.runtimeCompatibility.items():
        if not isinstance(value, dict):
            raise ValueError(f"skill {spec.id} runtimeCompatibility.{runtime} must be a mapping")
        status = str(value.get("status") or "unknown")
        if status not in allowed:
            raise ValueError(f"skill {spec.id} runtimeCompatibility.{runtime}.status is invalid: {status}")


def _validateStatusEvidence(spec: SkillSpec) -> None:
    if spec.status == "auditP":
        count = int(spec.quality.get("serverAuditPCount") or 0)
        if count < 2 or not spec.verifiedBy:
            raise ValueError(f"skill {spec.id} auditP requires two server audit P records and verifiedBy")
    if spec.status == "official":
        if not spec.verifiedBy:
            raise ValueError(f"skill {spec.id} official requires verifiedBy")
        if not spec.quality.get("serverAuditP") or not spec.quality.get("userConfirmed"):
            raise ValueError(f"skill {spec.id} official requires serverAuditP and userConfirmed quality evidence")


def _readSimpleYaml(text: str) -> dict[str, Any]:
    lines = text.splitlines()
    parsed, _ = _parseYamlBlock(lines, 0, 0)
    if not isinstance(parsed, dict):
        raise ValueError("skill yaml fallback parser expected a mapping")
    return parsed


def _parseYamlBlock(lines: list[str], start: int, indent: int) -> tuple[Any, int]:
    index = _skipYamlBlank(lines, start)
    if index >= len(lines):
        return {}, index
    current = lines[index]
    current_indent = len(current) - len(current.lstrip(" "))
    if current_indent < indent:
        return {}, index
    if current.lstrip().startswith("- "):
        return _parseYamlList(lines, index, current_indent)
    return _parseYamlMapping(lines, index, indent)


def _parseYamlMapping(lines: list[str], start: int, indent: int) -> tuple[dict[str, Any], int]:
    out: dict[str, Any] = {}
    index = start
    while index < len(lines):
        index = _skipYamlBlank(lines, index)
        if index >= len(lines):
            break
        line = lines[index]
        current_indent = len(line) - len(line.lstrip(" "))
        if current_indent < indent:
            break
        if current_indent > indent:
            break
        stripped = line.strip()
        if stripped.startswith("- ") or ":" not in stripped:
            break
        key, raw = stripped.split(":", 1)
        raw = raw.strip()
        if raw == ">":
            value, index = _parseYamlFolded(lines, index + 1, current_indent + 2)
        elif raw:
            value = _parseYamlScalar(raw)
            index += 1
        else:
            value, index = _parseYamlBlock(lines, index + 1, current_indent + 2)
        out[key] = value
    return out, index


_DICT_LIST_KEY_RE = re.compile(r"^[A-Za-z_][\w]*\s*:")


def _parseYamlList(lines: list[str], start: int, indent: int) -> tuple[list[Any], int]:
    out: list[Any] = []
    index = start
    while index < len(lines):
        index = _skipYamlBlank(lines, index)
        if index >= len(lines):
            break
        line = lines[index]
        current_indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if current_indent != indent or not stripped.startswith("- "):
            break
        item = stripped[2:].strip()
        # dict-list 처리: "- key: value" 형식 + 다음 줄도 같은 들여쓰기 dict key 면 dict.
        # 단순 문장 안 콜론 (예: "When: 분석") 은 string 으로 보존 — 정규식으로 첫 단어가 식별자 + 콜론인지 검사.
        is_dict_form = _DICT_LIST_KEY_RE.match(item) is not None and not item.startswith("[") and not item.endswith(":")
        next_indent_is_dict = False
        if is_dict_form and index + 1 < len(lines):
            nxt = lines[index + 1]
            nxt_strip = nxt.strip()
            nxt_indent = len(nxt) - len(nxt.lstrip(" "))
            if nxt_strip and nxt_indent == current_indent + 2 and _DICT_LIST_KEY_RE.match(nxt_strip):
                next_indent_is_dict = True
        if is_dict_form and next_indent_is_dict:
            key, raw = item.split(":", 1)
            entry: dict[str, Any] = {key.strip(): _parseYamlScalar(raw.strip()) if raw.strip() else None}
            index += 1
            inner_indent = current_indent + 2
            while index < len(lines):
                nextLine = lines[index]
                next_indent = len(nextLine) - len(nextLine.lstrip(" "))
                next_stripped = nextLine.strip()
                if not next_stripped:
                    index += 1
                    continue
                if next_indent < inner_indent or next_stripped.startswith("- "):
                    break
                if not _DICT_LIST_KEY_RE.match(next_stripped):
                    break
                k2, r2 = next_stripped.split(":", 1)
                entry[k2.strip()] = _parseYamlScalar(r2.strip()) if r2.strip() else None
                index += 1
            out.append(entry)
            continue
        out.append(_parseYamlScalar(item))
        index += 1
    return out, index


def _parseYamlFolded(lines: list[str], start: int, indent: int) -> tuple[str, int]:
    parts: list[str] = []
    index = start
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        current_indent = len(line) - len(line.lstrip(" "))
        if current_indent < indent:
            break
        parts.append(line.strip())
        index += 1
    return " ".join(parts), index


def _parseYamlScalar(raw: str) -> Any:
    if raw == "[]":
        return []
    if raw == "{}":
        return {}
    if (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("'") and raw.endswith("'")):
        return raw[1:-1]
    lowered = raw.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"null", "none"}:
        return None
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        return raw


def _skipYamlBlank(lines: list[str], start: int) -> int:
    index = start
    while index < len(lines) and (not lines[index].strip() or lines[index].lstrip().startswith("#")):
        index += 1
    return index


def _joinAny(values: Any) -> str:
    """list 의 원소가 str / dict / 기타 섞여도 안전하게 join — 점수 계산용 검색 텍스트."""
    if not values:
        return ""
    out: list[str] = []
    for v in values:
        if v is None:
            continue
        if isinstance(v, str):
            out.append(v)
        elif isinstance(v, dict):
            out.append(" ".join(str(x) for x in v.values() if x is not None))
        else:
            out.append(str(v))
    return " ".join(out)


def _score(spec: SkillSpec, terms: list[str], *, query: str = "") -> tuple[float, list[str]]:
    # list 안에 dict-form item (recipeSteps 또는 frontmatter 의 `- key: value`) 이 섞여도
    # 점수 계산 텍스트 생성이 깨지지 않도록 모든 list 필드는 _joinAny 사용.
    haystacks = {
        "id": spec.id,
        "title": spec.title,
        "category": spec.category,
        "purpose": spec.purpose,
        "whenToUse": _joinAny(spec.whenToUse),
        "inputs": _joinAny(spec.inputs),
        "outputs": _joinAny(spec.outputs),
        "capabilityRefs": _joinAny(spec.capabilityRefs),
        "datasetRefs": _joinAny(spec.datasetRefs),
        "visualRefs": _joinAny(spec.visualRefs),
        "knowledgeRefs": _joinAny(spec.knowledgeRefs),
        "linkedSkills": _joinAny(spec.linkedSkills),
        "requires": _joinAny(spec.requires),
        "alternatives": _joinAny(spec.alternatives),
        "succeededBy": _joinAny(spec.succeededBy),
        "deprecatedBy": _joinAny(spec.deprecatedBy),
        "sourceRefs": _joinAny(spec.sourceRefs),
        "runtimeCompatibility": json.dumps(spec.runtimeCompatibility, ensure_ascii=False),
        "docs": json.dumps(spec.docs, ensure_ascii=False),
        "procedure": _joinAny(spec.procedure),
        "requiredEvidence": _joinAny(spec.requiredEvidence),
        "expectedOutputs": _joinAny(spec.expectedOutputs),
        "failureModes": _joinAny(spec.failureModes),
        "forbidden": _joinAny(spec.forbidden),
        "examples": _joinAny(spec.examples),
        "body": str(spec.source.get("body") or ""),
    }
    score = 0.0
    reasons: list[str] = []
    normalizedQuery = query.lower()
    for term in terms:
        for name, hay in haystacks.items():
            field = hay.lower()
            if term in field:
                weight = _fieldWeight(name)
                if spec.category in {"engines", "runtime", "operation", "start"}:
                    weight += 0.75
                if normalizedQuery and normalizedQuery in field:
                    weight += 3.0
                score += weight
                reasons.append(f"{name}:{term}")
    boost, boost_reasons = _intentBoost(spec, query)
    if boost:
        score += boost
        reasons.extend(boost_reasons)
    if spec.status in {"auditP", "official"}:
        score += 0.5
    domain_bonus, domain_reasons = _domainBonus(spec, normalizedQuery)
    if domain_bonus:
        score += domain_bonus
        reasons.extend(domain_reasons)
    return score, reasons


_COMPOSITE_TERMS: tuple[str, ...] = (
    "종합",
    "깊이",
    "비교",
    "추세",
    "사이클",
    "다단",
    "deep",
    "comprehensive",
    "compare",
)


def _domainBonus(spec: SkillSpec, normalizedQuery: str) -> tuple[float, list[str]]:
    """recipe / engines kind 우선 — 종합 키워드 매칭 시 recipe 추가 가중.

    base 가중:
    - recipe: +1.0 (다단 절차)
    - 종합 키워드 매칭 시 recipe: +2.5 추가 (회사명 매칭 점수와 경쟁 가능 수준)
    - engines.* category: +0.3
    """
    bonus = 0.0
    reasons: list[str] = []
    if spec.kind == "recipe":
        bonus += 1.0
        reasons.append("kind:recipe")
        if normalizedQuery and any(term in normalizedQuery for term in _COMPOSITE_TERMS):
            bonus += 2.5
            reasons.append("composite_query+recipe")
    elif spec.category == "engines":
        bonus += 0.3
        reasons.append("category:engines")
    return bonus, reasons


def _fieldWeight(name: str) -> float:
    if name == "id":
        return 4.0
    if name == "title":
        return 3.5
    if name in {"whenToUse", "purpose"}:
        return 2.75
    if name in {"capabilityRefs", "toolRefs", "requiredEvidence", "expectedOutputs"}:
        return 2.0
    if name in {
        "procedure",
        "examples",
        "body",
        "linkedSkills",
        "requires",
        "alternatives",
        "succeededBy",
        "deprecatedBy",
    }:
        return 1.25
    return 1.0


def _intentBoost(spec: SkillSpec, query: str) -> tuple[float, list[str]]:
    query_text = query.lower()
    score = 0.0
    reasons: list[str] = []
    for entry in _loadIntentBoosts():
        if spec.id not in entry["skillIds"]:
            continue
        matched = [term for term in entry["terms"] if term.lower() in query_text]
        if not matched:
            continue
        score += float(entry["boost"])
        reasons.append(f"intent:{matched[0]}")
    if spec.id == "engines.company.usEdgarReview" and _TICKER_QUERY_RE.search(query):
        score += 8.0
        reasons.append("intent:ticker")
    return score, reasons


def _terms(query: str) -> list[str]:
    terms: list[str] = []
    for raw in query.replace("/", " ").replace(".", " ").split():
        term = raw.lower()
        if len(term) < 2:
            continue
        terms.append(term)
        if _containsHangul(term) and len(term) >= 3:
            terms.extend(term[index : index + 2] for index in range(len(term) - 1))
    return list(dict.fromkeys(terms))


def _containsHangul(text: str) -> bool:
    return any("\uac00" <= char <= "\ud7a3" for char in text)


def _evidenceNames(refs: list[dict[str, Any]] | list[Any]) -> set[str]:
    names: set[str] = set()
    for ref in refs:
        payload = ref.get("payload", ref) if isinstance(ref, dict) else getattr(ref, "payload", {})
        if not isinstance(payload, dict):
            continue
        for key in ("target", "metric", "period", "asOf", "observedDate", "basis", "universe"):
            if payload.get(key) is not None:
                names.add(key)
        if payload.get("rows"):
            names.add("table")
        if payload.get("latest"):
            names.add("latestAsOf")
    return names


def _repoRoot() -> Path:
    here = Path.cwd()
    module_path = Path(__file__).resolve()
    for base in [here, *here.parents, *module_path.parents]:
        if (base / "pyproject.toml").exists() and (base / "src" / "dartlab").exists():
            return base
    return here


search = searchSkills
get = getSkill
describe = describeSkill
