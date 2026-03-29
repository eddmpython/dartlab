"""registry 기반 자동 문서 생성.

7개 surface에서 코드를 수집하여 다음 파일을 자동 생성한다:
- CAPABILITIES.md           — 루트 총괄 스펙맵
- landing/static/llms.txt   — AI 크롤러용 구조화 문서
- .claude/skills/dartlab/reference.md — Claude Code 스킬 레퍼런스
- src/dartlab/ai/conversation/_generated_catalog.py — AI 시스템 프롬프트용 도구 카탈로그
- src/dartlab/core/_generatedCapabilities.py — 런타임 capabilities 카탈로그

실행:
    uv run python scripts/generateSpec.py

릴리즈 시 CI에서 자동 실행하여 수동 관리 포인트를 제거한다.
"""

from __future__ import annotations

import ast
import dataclasses
import inspect
import json
import sys
import textwrap
from pathlib import Path
from typing import Any, get_type_hints

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from dartlab.core.registry import getCategories, getEntries  # noqa: E402

# ─── 유틸 ───────────────────────────────────────────────────────


def _inspectDataclass(cls: type) -> list[tuple[str, str, str]]:
    """dataclass의 (필드명, 타입, 기본값) 목록 반환."""
    rows = []
    hints = get_type_hints(cls)
    for f in dataclasses.fields(cls):
        typeName = hints.get(f.name, "")
        if hasattr(typeName, "__name__"):
            typeName = typeName.__name__
        else:
            typeName = str(typeName).replace("typing.", "")
        defaultStr = ""
        if f.default is not dataclasses.MISSING:
            defaultStr = str(f.default)
        elif f.default_factory is not dataclasses.MISSING:
            defaultStr = "[]" if "list" in typeName.lower() else "{}"
        rows.append((f.name, typeName, defaultStr))
    return rows


def _dataclassTable(cls: type, title: str) -> str:
    """dataclass를 마크다운 테이블로."""
    rows = _inspectDataclass(cls)
    lines = [f"### {title}\n"]
    doc = cls.__doc__
    if doc:
        lines.append(f"{doc.strip()}\n")
    lines.append("| 필드 | 타입 | 기본값 |")
    lines.append("|------|------|--------|")
    for name, typ, default in rows:
        lines.append(f"| `{name}` | `{typ}` | {default} |")
    lines.append("")
    return "\n".join(lines)


def _categoryLabel(cat: str) -> str:
    labels = {
        "finance": "시계열 재무제표",
        "report": "공시 파싱 모듈",
        "disclosure": "서술형 공시",
        "notes": "K-IFRS 주석",
        "raw": "원본 데이터",
        "analysis": "분석 엔진",
    }
    return labels.get(cat, cat)


def _parseDocstringSections(doc: str | None) -> dict[str, str]:
    """Google-style docstring에서 Capabilities/Requires/AIContext/Args/Returns 섹션 추출."""
    if not doc:
        return {}

    result: dict[str, str] = {}
    knownSections = {"capabilities", "requires", "aicontext", "guide", "seealso", "args", "returns", "example"}
    currentKey: str | None = None
    currentLines: list[str] = []

    for line in doc.split("\n"):
        stripped = line.strip()
        # "SectionName:" 패턴 (줄 전체가 "단어:" 또는 "단어::" 형태)
        candidate = stripped.rstrip(":").lower()
        if stripped.endswith(":") and candidate in knownSections:
            # 이전 섹션 저장
            if currentKey is not None:
                result[currentKey] = "\n".join(currentLines).strip()
            currentKey = candidate
            currentLines = []
            continue

        if currentKey is not None:
            # 들여쓰기 블록 안의 줄 수집 (leading whitespace 제거)
            if stripped.startswith("- "):
                currentLines.append(stripped[2:].strip())
            elif stripped:
                currentLines.append(stripped)
            elif currentLines:
                # 빈 줄 — 블록 종료가 아님 (다음 섹션이 나올 때까지)
                currentLines.append("")

    # 마지막 섹션 저장
    if currentKey is not None:
        result[currentKey] = "\n".join(currentLines).strip()

    return result


# ─── Surface 1: Python API (__init__.py __all__) ────────────────


def _pythonApiSection() -> str:
    """__init__.py __all__에서 callable의 docstring 첫 줄 + Capabilities/Requires 수집."""
    import dartlab

    allNames = getattr(dartlab, "__all__", [])
    lines = [f"## Python API ({len(allNames)}개)\n"]
    lines.append("`import dartlab` 후 사용 가능한 공개 API.\n")
    lines.append("| 이름 | 종류 | 설명 |")
    lines.append("|------|------|------|")

    # 상세 블록을 위해 수집
    detailEntries: list[tuple[str, dict[str, str]]] = []

    for name in allNames:
        obj = getattr(dartlab, name, None)
        if obj is None:
            lines.append(f"| `{name}` | - | - |")
            continue
        kind = "class" if inspect.isclass(obj) else "function" if callable(obj) else "module"
        doc = inspect.getdoc(obj)
        desc = doc.split("\n")[0].strip() if doc else "-"
        lines.append(f"| `{name}` | {kind} | {desc} |")

        # docstring 섹션 파싱
        sections = _parseDocstringSections(doc)
        if sections.get("capabilities") or sections.get("requires") or sections.get("guide"):
            detailEntries.append((name, sections))

    lines.append("")

    # Capabilities/Requires/Guide/SeeAlso 상세 블록
    if detailEntries:
        lines.append("### Python API 상세\n")
        for name, sections in detailEntries:
            lines.append(f"#### {name}")
            if cap := sections.get("capabilities"):
                lines.append(f"**Capabilities:** {cap}")
            if req := sections.get("requires"):
                lines.append(f"**Requires:** {req}")
            if ctx := sections.get("aicontext"):
                lines.append(f"**AIContext:** {ctx}")
            if guide := sections.get("guide"):
                lines.append(f"**Guide:** {guide}")
            if seeAlso := sections.get("seealso"):
                lines.append(f"**SeeAlso:** {seeAlso}")
            lines.append("")

    return "\n".join(lines)


# ─── Surface 2: CLI (COMMAND_SPECS) ────────────────────────────


def _cliSection() -> str:
    """COMMAND_SPECS에서 name + description 수집."""
    from dartlab.cli.parser import COMMAND_SPECS

    lines = [f"## CLI ({len(COMMAND_SPECS)}개 명령)\n"]
    lines.append("`dartlab <command>` 형태로 사용.\n")
    lines.append("| 명령 | 설명 |")
    lines.append("|------|------|")

    for spec in COMMAND_SPECS:
        desc = spec.description or "-"
        lines.append(f"| `{spec.name}` | {desc} |")

    lines.append("")
    return "\n".join(lines)


# ─── Surface 3: Server API (AST 기반 라우터 파싱) ──────────────


def _parseRouterEndpoints(filepath: Path) -> list[tuple[str, str, str]]:
    """AST로 @router.get/post/put/delete 데코레이터에서 (method, path, docstring) 추출."""
    try:
        tree = ast.parse(filepath.read_text(encoding="utf-8"), filename=str(filepath))
    except SyntaxError:
        return []

    endpoints: list[tuple[str, str, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for deco in node.decorator_list:
            # @router.get("/api/...") 패턴
            if isinstance(deco, ast.Call) and isinstance(deco.func, ast.Attribute):
                attr = deco.func
                if isinstance(attr.value, ast.Name) and attr.value.id == "router":
                    method = attr.attr.upper()
                    if deco.args and isinstance(deco.args[0], ast.Constant):
                        path = str(deco.args[0].value)
                        doc = ast.get_docstring(node) or ""
                        docLine = doc.split("\n")[0].strip() if doc else "-"
                        endpoints.append((method, path, docLine))
    return endpoints


def _serverApiSection() -> str:
    """FastAPI 라우터에서 method, path, docstring 수집."""
    apiDir = SRC / "dartlab" / "server" / "api"
    allEndpoints: list[tuple[str, str, str]] = []

    for pyFile in sorted(apiDir.glob("*.py")):
        if pyFile.name.startswith("_"):
            continue
        allEndpoints.extend(_parseRouterEndpoints(pyFile))

    lines = [f"## Server API ({len(allEndpoints)}개 엔드포인트)\n"]
    lines.append("FastAPI `/api/*` 엔드포인트. 모든 클라이언트의 단일 소비 경로.\n")
    lines.append("| Method | Path | 설명 |")
    lines.append("|--------|------|------|")

    for method, path, doc in allEndpoints:
        lines.append(f"| {method} | `{path}` | {doc} |")

    lines.append("")
    return "\n".join(lines)


# ─── Surface 4: Data Modules (registry) ────────────────────────


def _dataModulesSection() -> str:
    """registry 엔트리를 카테고리별 테이블로."""
    total = len(getEntries())
    lines = [f"## Data Modules ({total}개)\n"]
    lines.append("`core/registry.py` DataEntry 기반. 모듈 추가 = 한 줄 → 7곳 자동 반영.\n")

    for cat in getCategories():
        entries = getEntries(category=cat)
        lines.append(f"### {_categoryLabel(cat)} ({cat})\n")
        lines.append("| name | label | dataType | description |")
        lines.append("|------|-------|----------|-------------|")
        for e in entries:
            lines.append(f"| `{e.name}` | {e.label} | `{e.dataType}` | {e.description} |")
        lines.append("")
    return "\n".join(lines)


# ─── Surface 5: AI Tools (super tools AST 파싱) ────────────────


@dataclasses.dataclass
class ToolSpec:
    """registerTool() 호출에서 추출한 완전 도구 명세."""

    name: str
    description: str
    schema: dict[str, Any]
    category: str
    questionTypes: tuple[str, ...]
    priority: int


def _astToValue(node: ast.expr, localVars: dict[str, ast.expr] | None = None) -> Any:
    """AST 리터럴 노드를 Python 값으로 변환. localVars로 변수 참조 해결."""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.List):
        return [_astToValue(el, localVars) for el in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_astToValue(el, localVars) for el in node.elts)
    if isinstance(node, ast.Dict):
        result = {}
        for k, v in zip(node.keys, node.values):
            if k is None:
                continue
            result[_astToValue(k, localVars)] = _astToValue(v, localVars)
        return result
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_astToValue(node.operand, localVars)
    if isinstance(node, ast.Name):
        if node.id in ("True", "true"):
            return True
        if node.id in ("False", "false"):
            return False
        if node.id in ("None",):
            return None
        # localVars에서 변수 resolve 시도
        if localVars and node.id in localVars:
            return _astToValue(localVars[node.id], localVars)
        return f"<var:{node.id}>"
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _astToValue(node.left, localVars)
        right = _astToValue(node.right, localVars)
        if isinstance(left, str) and isinstance(right, str):
            return left + right
        if isinstance(left, list) and isinstance(right, list):
            return left + right
        # 한쪽 resolve 실패 → <var:partial> 마커 포함해서 런타임 fallback 유도
        if isinstance(right, list):
            return ["<var:partial>"] + right
        if isinstance(left, list):
            return left + ["<var:partial>"]
        return None
    if isinstance(node, ast.JoinedStr):
        parts = []
        for val in node.values:
            if isinstance(val, ast.Constant):
                parts.append(str(val.value))
            else:
                parts.append("{...}")
        return "".join(parts)
    # ast.Call — list(...) 같은 호출은 resolve 불가
    return None


def _extractStr(node: ast.expr) -> str:
    """문자열 또는 문자열 연결 노드에서 전체 텍스트 추출."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return _astToValue(node)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _extractStr(node.left)
        right = _extractStr(node.right)
        if left and right:
            return left + right
    return ""


def _resolveSchemaDict(schemaNode: ast.expr, localVars: dict[str, ast.expr]) -> dict[str, Any]:
    """schema dict 노드를 파싱. 변수 참조는 localVars에서 해결."""
    if isinstance(schemaNode, ast.Dict):
        result = {}
        for k, v in zip(schemaNode.keys, schemaNode.values):
            if k is None:
                continue
            key = _astToValue(k, localVars)
            if isinstance(v, ast.Name) and v.id in localVars:
                result[key] = _resolveSchemaDict(localVars[v.id], localVars)
            elif isinstance(v, ast.Dict):
                result[key] = _resolveSchemaDict(v, localVars)
            else:
                result[key] = _astToValue(v, localVars)
        return result
    return _astToValue(schemaNode, localVars) or {}


def _collectLocalVarAssigns(funcBody: list[ast.stmt]) -> dict[str, ast.expr]:
    """함수 본문에서 dict 변수 할당을 수집 (schema 변수 해결용)."""
    result: dict[str, ast.expr] = {}
    for stmt in funcBody:
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name):
                    result[target.id] = stmt.value
        elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name) and stmt.value:
            result[stmt.target.id] = stmt.value
    return result


def _parseRegisterToolCalls(filepath: Path) -> list[ToolSpec]:
    """AST로 registerTool() 호출에서 완전 ToolSpec 추출."""
    try:
        source = filepath.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(filepath))
    except SyntaxError:
        return []

    # 모듈 레벨 + 함수 내부의 변수 할당 수집
    allLocalVars: dict[str, ast.expr] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            allLocalVars.update(_collectLocalVarAssigns(node.body))
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    allLocalVars[target.id] = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value:
            allLocalVars[node.target.id] = node.value

    tools: list[ToolSpec] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        funcNode = node.func
        funcName = ""
        if isinstance(funcNode, ast.Name):
            funcName = funcNode.id
        elif isinstance(funcNode, ast.Attribute):
            funcName = funcNode.attr

        if funcName not in ("registerTool", "register_tool"):
            continue
        if len(node.args) < 3:
            continue

        # 1: name
        nameNode = node.args[0]
        if isinstance(nameNode, ast.Constant) and isinstance(nameNode.value, str):
            name = nameNode.value
        else:
            continue

        # 3: description (전체)
        description = _extractStr(node.args[2]) or "-"

        # 4: schema dict
        schema: dict[str, Any] = {}
        if len(node.args) >= 4:
            schema = _resolveSchemaDict(node.args[3], allLocalVars)

        # keyword args: category, questionTypes, priority
        category = ""
        questionTypes: tuple[str, ...] = ()
        priority = 50
        for kw in node.keywords:
            if kw.arg == "category":
                val = _astToValue(kw.value, allLocalVars)
                category = val if isinstance(val, str) else ""
            elif kw.arg == "questionTypes":
                val = _astToValue(kw.value, allLocalVars)
                if isinstance(val, (tuple, list)):
                    questionTypes = tuple(str(v) for v in val)
            elif kw.arg == "priority":
                val = _astToValue(kw.value, allLocalVars)
                priority = val if isinstance(val, int) else 50

        tools.append(
            ToolSpec(
                name=name,
                description=description,
                schema=schema,
                category=category,
                questionTypes=questionTypes,
                priority=priority,
            )
        )
    return tools


def _hasUnresolvedVar(obj: Any) -> bool:
    """값 안에 <var:...> 미해결 참조가 있는지 확인."""
    if isinstance(obj, str):
        return "<var:" in obj
    if isinstance(obj, (list, tuple)):
        return any(_hasUnresolvedVar(v) for v in obj)
    if isinstance(obj, dict):
        return any(_hasUnresolvedVar(v) for v in obj.values())
    return False


def _runtimeResolveToolEnums(tools: list[ToolSpec]) -> None:
    """AST로 해결 못한 enum을 런타임 import로 보충."""
    needsResolve = []
    for spec in tools:
        props = spec.schema.get("properties", {})
        for propName, propDef in props.items():
            enumVal = propDef.get("enum")
            # enum이 None (resolve 실패)이거나 <var:> 미해결 참조 포함
            if "enum" in propDef and (enumVal is None or _hasUnresolvedVar(enumVal)):
                needsResolve.append((spec, propName, propDef))

    if not needsResolve:
        return

    # 런타임으로 실제 registerTool 호출을 가로채서 enum 추출
    try:
        capturedSchemas: dict[str, dict] = {}

        def _captureRegister(name: str, _fn, _desc, schema=None, **_kw):
            if schema and isinstance(schema, dict):
                capturedSchemas[name] = schema

        import dartlab.ai.tools.superTools.analysis as _analysisMod  # noqa: F811
        import dartlab.ai.tools.superTools.scan as _scanMod  # noqa: F811

        # scan — registerScanTool 실행
        if hasattr(_scanMod, "registerScanTool"):
            try:
                _scanMod.registerScanTool(_captureRegister)
            except (ImportError, AttributeError, TypeError, ValueError, OSError):
                pass

        # analysis — registerAnalysisTool(company, registerTool) 실행
        if hasattr(_analysisMod, "registerAnalysisTool"):
            try:
                _analysisMod.registerAnalysisTool(None, _captureRegister)
            except (ImportError, AttributeError, TypeError, ValueError, OSError):
                pass

        # 캡처된 schema로 unresolved enum 교체
        for spec, propName, propDef in needsResolve:
            captured = capturedSchemas.get(spec.name)
            if not captured:
                continue
            cProps = captured.get("properties", {})
            cPropDef = cProps.get(propName, {})
            cEnum = cPropDef.get("enum")
            if cEnum and not _hasUnresolvedVar(cEnum):
                propDef["enum"] = list(cEnum)
    except (ImportError, AttributeError, TypeError, ValueError, OSError) as e:
        print(f"  [warn] 런타임 enum resolve 실패: {e}")


def _collectAllToolSpecs() -> list[ToolSpec]:
    """모든 AI tool 파일에서 ToolSpec 수집."""
    toolsDir = SRC / "dartlab" / "ai" / "tools"
    allTools: list[ToolSpec] = []
    seen: set[str] = set()

    for subDir in ("superTools", "defaults"):
        d = toolsDir / subDir
        if not d.exists():
            continue
        for pyFile in sorted(d.glob("*.py")):
            if pyFile.name.startswith("_"):
                continue
            for spec in _parseRegisterToolCalls(pyFile):
                if spec.name not in seen:
                    allTools.append(spec)
                    seen.add(spec.name)

    # AST 해결 실패한 enum을 런타임으로 보충
    _runtimeResolveToolEnums(allTools)

    # priority 내림차순 정렬
    allTools.sort(key=lambda s: -s.priority)
    return allTools


def _toolSpecToMd(spec: ToolSpec) -> str:
    """단일 ToolSpec을 상세 마크다운으로."""
    lines = [f"### {spec.name} (priority: {spec.priority}, category: {spec.category})\n"]

    # description 첫 줄 = 요약, 나머지 = 상세
    descLines = spec.description.strip().split("\n")
    lines.append(descLines[0])
    lines.append("")

    # action enum 추출
    props = spec.schema.get("properties", {})
    actionProp = props.get("action", {})
    actionEnum = actionProp.get("enum", [])

    if actionEnum:
        # description에서 action별 설명 추출
        actionDescs: dict[str, str] = {}
        for line in descLines:
            stripped = line.strip()
            if stripped.startswith("- ") and ":" in stripped:
                parts = stripped[2:].split(":", 1)
                key = parts[0].strip()
                if key in actionEnum:
                    actionDescs[key] = parts[1].strip()

        lines.append("**Actions:**\n")
        lines.append("| action | 설명 |")
        lines.append("|--------|------|")
        for act in actionEnum:
            desc = actionDescs.get(act, "-")
            # 80자 제한
            if len(desc) > 80:
                desc = desc[:77] + "..."
            lines.append(f"| `{act}` | {desc} |")
        lines.append("")

    # parameters 테이블 (action 제외)
    otherParams = {k: v for k, v in props.items() if k != "action"}
    required = spec.schema.get("required", [])
    if otherParams:
        lines.append("**Parameters:**\n")
        lines.append("| 파라미터 | 타입 | 필수 | 설명 |")
        lines.append("|---------|------|------|------|")
        for pName, pSchema in otherParams.items():
            if not isinstance(pSchema, dict):
                continue
            pType = pSchema.get("type", "string")
            enumVals = pSchema.get("enum", [])
            if enumVals and isinstance(enumVals, list):
                # 동적 변수 참조 필터
                cleanEnum = [str(v) for v in enumVals if not str(v).startswith("<var:")]
                if cleanEnum:
                    pType = f"enum({', '.join(cleanEnum[:8])}{'...' if len(cleanEnum) > 8 else ''})"
            isRequired = "O" if pName in required else "-"
            pDesc = pSchema.get("description", "-")
            if pDesc is None or (isinstance(pDesc, str) and pDesc.startswith("{...")):
                pDesc = f"{pName} 파라미터 (company별 동적 생성)"
            if isinstance(pDesc, str) and len(pDesc) > 60:
                pDesc = pDesc[:57] + "..."
            lines.append(f"| `{pName}` | {pType} | {isRequired} | {pDesc} |")
        lines.append("")

    # 질문 유형
    if spec.questionTypes:
        lines.append(f"**질문 유형**: {', '.join(spec.questionTypes)}\n")

    return "\n".join(lines)


def _aiToolsSection() -> str:
    """AI tool 등록에서 완전 명세 수집."""
    allTools = _collectAllToolSpecs()

    lines = [f"## AI Tools ({len(allTools)}개)\n"]
    lines.append("LLM 에이전트가 tool calling으로 사용하는 도구. priority 내림차순.\n")

    for spec in allTools:
        lines.append(_toolSpecToMd(spec))

    return "\n".join(lines)


# ─── Surface 6: Scan Axis Registry ────────────────────────────


def _scanAxisSection() -> str:
    """scan/_AXIS_REGISTRY에서 축 명세 추출."""
    scanInit = SRC / "dartlab" / "scan" / "__init__.py"
    if not scanInit.exists():
        return ""

    try:
        source = scanInit.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(scanInit))
    except SyntaxError:
        return ""

    # _AXIS_REGISTRY dict 찾기 (Assign 또는 AnnAssign)
    registryNode = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "_AXIS_REGISTRY":
                    registryNode = node.value
                    break
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == "_AXIS_REGISTRY" and node.value:
                registryNode = node.value

    if registryNode is None or not isinstance(registryNode, ast.Dict):
        return ""

    axes: list[dict[str, str]] = []
    for key, val in zip(registryNode.keys, registryNode.values):
        if key is None or not isinstance(key, ast.Constant):
            continue
        axisName = str(key.value)
        if not isinstance(val, ast.Call):
            continue

        # _AxisEntry(...) keyword args 추출
        entry: dict[str, str] = {"axis": axisName}
        for kw in val.keywords:
            if kw.arg and isinstance(kw.value, ast.Constant):
                entry[kw.arg] = str(kw.value.value)
            elif kw.arg == "targetRequired" and isinstance(kw.value, ast.Constant):
                entry[kw.arg] = str(kw.value.value)
        axes.append(entry)

    if not axes:
        return ""

    # _ALIASES dict 추출
    aliasNode = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "_ALIASES":
                    aliasNode = node.value
                    break
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == "_ALIASES" and node.value:
                aliasNode = node.value

    aliases: dict[str, list[str]] = {}
    if aliasNode and isinstance(aliasNode, ast.Dict):
        for k, v in zip(aliasNode.keys, aliasNode.values):
            if isinstance(k, ast.Constant) and isinstance(v, ast.Constant):
                target = str(v.value)
                aliases.setdefault(target, []).append(str(k.value))

    lines = [f"## Scan Axis ({len(axes)}개 축)\n"]
    lines.append("`dartlab.scan(axis, target)` 형태로 전종목 횡단분석.\n")
    lines.append("| 축 | 한글 | 설명 | target 파라미터 | 필수 | 반환타입 |")
    lines.append("|----|------|------|----------------|------|---------|")

    for e in axes:
        axis = e.get("axis", "")
        label = e.get("label", "")
        desc = e.get("description", "")
        tp = e.get("targetParam", "None")
        if tp == "None":
            tp = "stockCode 필터"
        required = "O" if e.get("targetRequired", "False") == "True" else "-"
        rt = e.get("returnType", "DataFrame")
        lines.append(f"| `{axis}` | {label} | {desc} | {tp} | {required} | {rt} |")

    lines.append("")

    # 한글 별칭
    if aliases:
        lines.append("**한글 별칭:**\n")
        for target, aliasList in sorted(aliases.items()):
            lines.append(f"- `{target}`: {', '.join(aliasList)}")
        lines.append("")

    # 사용법 예시
    lines.append("**사용법:**\n")
    lines.append("```python")
    lines.append("import dartlab")
    lines.append("")
    lines.append('dartlab.scan("governance")              # 전 상장사 거버넌스')
    lines.append('dartlab.scan("governance", "005930")    # 삼성전자만 필터')
    lines.append('dartlab.scan("ratio", "roe")            # 전종목 ROE')
    lines.append('dartlab.scan("account", "sales")        # 전종목 매출액 시계열')
    lines.append("dartlab.scan.topics()                   # 가용 축 목록")
    lines.append("```\n")

    return "\n".join(lines)


# ─── Surface 7: Gather Axis Registry ──────────────────────────


def _gatherAxisSection() -> str:
    """gather/_AXIS_REGISTRY에서 축 명세 추출 (scan과 동일 AST 패턴)."""
    gatherEntry = SRC / "dartlab" / "gather" / "entry.py"
    if not gatherEntry.exists():
        return ""

    try:
        source = gatherEntry.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(gatherEntry))
    except SyntaxError:
        return ""

    # _AXIS_REGISTRY dict 찾기
    registryNode = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "_AXIS_REGISTRY":
                    registryNode = node.value
                    break
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == "_AXIS_REGISTRY" and node.value:
                registryNode = node.value

    if registryNode is None or not isinstance(registryNode, ast.Dict):
        return ""

    axes: list[dict[str, str]] = []
    for key, val in zip(registryNode.keys, registryNode.values):
        if key is None or not isinstance(key, ast.Constant):
            continue
        axisName = str(key.value)
        if not isinstance(val, ast.Call):
            continue

        entry: dict[str, str] = {"axis": axisName}
        for kw in val.keywords:
            if kw.arg and isinstance(kw.value, ast.Constant):
                entry[kw.arg] = str(kw.value.value)
            elif kw.arg == "targetRequired" and isinstance(kw.value, ast.Constant):
                entry[kw.arg] = str(kw.value.value)
        axes.append(entry)

    if not axes:
        return ""

    # _ALIASES dict 추출
    aliasNode = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "_ALIASES":
                    aliasNode = node.value
                    break
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == "_ALIASES" and node.value:
                aliasNode = node.value

    aliases: dict[str, list[str]] = {}
    if aliasNode and isinstance(aliasNode, ast.Dict):
        for k, v in zip(aliasNode.keys, aliasNode.values):
            if isinstance(k, ast.Constant) and isinstance(v, ast.Constant):
                target = str(v.value)
                aliases.setdefault(target, []).append(str(k.value))

    lines = [f"## Gather Axis ({len(axes)}개 축)\n"]
    lines.append("`dartlab.gather(axis, target)` 형태로 외부 시장 데이터 수집.\n")
    lines.append("| 축 | 한글 | 설명 | target 필수 |")
    lines.append("|----|------|------|------------|")

    for e in axes:
        axis = e.get("axis", "")
        label = e.get("label", "")
        desc = e.get("description", "")
        required = "O" if e.get("targetRequired", "True") == "True" else "-"
        lines.append(f"| `{axis}` | {label} | {desc} | {required} |")

    lines.append("")

    # 한글 별칭
    if aliases:
        lines.append("**한글 별칭:**\n")
        for target, aliasList in sorted(aliases.items()):
            lines.append(f"- `{target}`: {', '.join(aliasList)}")
        lines.append("")

    # 사용법 예시
    lines.append("**사용법:**\n")
    lines.append("```python")
    lines.append("import dartlab")
    lines.append("")
    lines.append('dartlab.gather("price", "005930")   # 삼성전자 주가')
    lines.append('dartlab.gather("flow", "005930")     # 수급 동향')
    lines.append('dartlab.gather("macro")              # KR 거시지표 전체')
    lines.append('dartlab.gather("news", "삼성전자")    # 뉴스')
    lines.append("```\n")

    return "\n".join(lines)


# ─── 도구 연계 가이드 (자동 생성) ──────────────────────────────


def _toolChainSection() -> str:
    """questionTypes + priority에서 질문 유형별 도구 매핑 자동 생성."""
    allTools = _collectAllToolSpecs()
    if not allTools:
        return ""

    # 질문 유형별 도구 수집
    typeToTools: dict[str, list[tuple[str, int]]] = {}
    for spec in allTools:
        for qt in spec.questionTypes:
            typeToTools.setdefault(qt, []).append((spec.name, spec.priority))

    # priority 내림차순 정렬
    for qt in typeToTools:
        typeToTools[qt].sort(key=lambda x: -x[1])

    lines = ["## 질문 유형별 도구 매핑\n"]
    lines.append("registerTool()의 questionTypes + priority에서 자동 생성.\n")
    lines.append("| 질문 유형 | 우선 도구 (priority 순) |")
    lines.append("|----------|----------------------|")

    for qt in sorted(typeToTools):
        toolList = typeToTools[qt]
        toolStr = " > ".join(f"{name}({pri})" for name, pri in toolList)
        lines.append(f"| {qt} | {toolStr} |")

    lines.append("")

    # description에서 연쇄 사용 패턴 추출
    chains: list[str] = []
    for spec in allTools:
        for line in spec.description.split("\n"):
            stripped = line.strip()
            if "연쇄 사용" in stripped or "연쇄사용" in stripped:
                chains.append(f"- **{spec.name}**: {stripped}")

    if chains:
        lines.append("**도구 연쇄 패턴:**\n")
        lines.extend(chains)
        lines.append("")

    return "\n".join(lines)


# ─── Company facade (동적 추출) ─────────────────────────────────


def _companySection() -> str:
    """Company facade 개요 (정적) + 메서드/프로퍼티 docstring 동적 추출."""
    header = textwrap.dedent("""\
    ## Company (통합 facade)

    입력을 자동 판별하여 DART 또는 EDGAR 시장 전용 Company를 생성한다.
    현재 DART Company의 공개 진입점은 **index -> show(topic) -> trace(topic)** 이다.

    ```python
    import dartlab

    kr = dartlab.Company("005930")
    kr = dartlab.Company("삼성전자")
    us = dartlab.Company("AAPL")

    kr.market                    # "KR"
    us.market                    # "US"
    ```

    ### 판별 규칙

    | 입력 | 결과 | 예시 |
    |------|------|------|
    | 6자리 숫자 | DART Company | `Company("005930")` |
    | 한글 포함 | DART Company | `Company("삼성전자")` |
    | 영문 1~5자리 | EDGAR Company | `Company("AAPL")` |

    """)

    # 동적 추출: DartCompany 공개 메서드/프로퍼티
    lines = [header]
    lines.append(_companyMethodsSection())
    return "\n".join(lines)


def _companyMethodsSection() -> str:
    """DartCompany 공개 메서드/프로퍼티에서 docstring 동적 추출."""
    from dartlab.providers.dart.company import Company as DartCompany

    # 공개 멤버 수집
    members: list[tuple[str, str, str, dict[str, str]]] = []
    for name in sorted(dir(DartCompany)):
        if name.startswith("_"):
            continue
        # 정적 메서드 (search, listing 등) 제외 — 이미 Python API 섹션에 있음
        obj = getattr(DartCompany, name, None)
        if obj is None:
            continue
        if isinstance(obj, staticmethod) or isinstance(obj, classmethod):
            continue

        kind = "property" if isinstance(inspect.getattr_static(DartCompany, name), property) else "method"
        doc = None
        if kind == "property":
            prop = inspect.getattr_static(DartCompany, name)
            if prop.fget:
                doc = inspect.getdoc(prop.fget)
        else:
            doc = inspect.getdoc(obj)
        if doc is None:
            continue

        desc = doc.split("\n")[0].strip()
        sections = _parseDocstringSections(doc)
        members.append((name, kind, desc, sections))

    if not members:
        return ""

    lines = ["### Company 메서드/프로퍼티\n"]
    lines.append(f"DartCompany에서 동적 추출 ({len(members)}개).\n")
    lines.append("| 이름 | 종류 | 설명 |")
    lines.append("|------|------|------|")
    for name, kind, desc, _ in members:
        lines.append(f"| `{name}` | {kind} | {desc} |")
    lines.append("")

    # 상세 블록 (Capabilities/Requires/Guide가 있는 것만)
    detailMembers = [(n, s) for n, _, _, s in members if s.get("capabilities") or s.get("requires") or s.get("guide")]
    if detailMembers:
        lines.append("### Company 메서드 상세\n")
        for name, sections in detailMembers:
            lines.append(f"#### Company.{name}")
            if cap := sections.get("capabilities"):
                lines.append(f"**Capabilities:** {cap}")
            if req := sections.get("requires"):
                lines.append(f"**Requires:** {req}")
            if ctx := sections.get("aicontext"):
                lines.append(f"**AIContext:** {ctx}")
            if guide := sections.get("guide"):
                lines.append(f"**Guide:** {guide}")
            if seeAlso := sections.get("seealso"):
                lines.append(f"**SeeAlso:** {seeAlso}")
            lines.append("")

    return "\n".join(lines)


# ─── 주요 데이터 타입 ───────────────────────────────────────────


def _dataclassesSection() -> str:
    """주요 dataclass 스키마."""
    lines = ["## 주요 데이터 타입\n"]

    from dartlab.core.finance.ratios import RatioResult

    lines.append(_dataclassTable(RatioResult, "RatioResult"))

    from dartlab.analysis.financial.insight.types import AnalysisResult, Anomaly, Flag, InsightResult

    lines.append(_dataclassTable(InsightResult, "InsightResult"))
    lines.append(_dataclassTable(Anomaly, "Anomaly"))
    lines.append(_dataclassTable(Flag, "Flag"))
    lines.append(_dataclassTable(AnalysisResult, "AnalysisResult"))

    from dartlab.analysis.comparative.sector.types import SectorInfo, SectorParams

    lines.append(_dataclassTable(SectorInfo, "SectorInfo"))
    lines.append(_dataclassTable(SectorParams, "SectorParams"))

    from dartlab.scan.rank import RankInfo

    lines.append(_dataclassTable(RankInfo, "RankInfo"))

    return "\n".join(lines)


# ─── CAPABILITIES.md 생성 ──────────────────────────────────────


def generateCapabilities() -> str:
    """루트 CAPABILITIES.md 생성 — 7 surface 통합."""
    import dartlab

    version = dartlab.__version__ if hasattr(dartlab, "__version__") else "unknown"
    header = (
        "# dartlab Capabilities\n\n"
        f"> v{version} 기준 자동 생성. 직접 수정 금지.  \n"
        "> `uv run python scripts/generateSpec.py`로 재생성.\n\n"
    )
    parts = [
        header,
        _pythonApiSection(),
        _cliSection(),
        _serverApiSection(),
        _dataModulesSection(),
        _aiToolsSection(),
        _scanAxisSection(),
        _gatherAxisSection(),
        _toolChainSection(),
        _companySection(),
        _dataclassesSection(),
    ]
    return "\n---\n\n".join(parts)


# ─── llms.txt 생성 ─────────────────────────────────────────────


def generateLlmsTxt() -> str:
    """llms.txt 생성 — AI 크롤러용."""
    lines = [
        "# DartLab — DART + EDGAR Disclosure Analysis Python Library",
        "",
        "> Turn Korean DART and US SEC EDGAR filings into one structured company map.",
        "> 한국 DART 전자공시와 미국 SEC EDGAR 공시를 하나의 회사 맵으로 바꾸는 Python 라이브러리.",
        "",
        "DartLab parses corporate disclosure filings — annual reports, 10-K, 10-Q — into structured,",
        "comparable data. Financial statements (BS/IS/CF), 47 financial ratios, 7-area insight grades,",
        "narrative text, and structured reports are all accessible with a single stock code.",
        "Covers 2,700+ Korean listed companies and 970+ US companies.",
        "",
        "## Install",
        "",
        "```bash",
        "pip install dartlab",
        "# or",
        "uv add dartlab",
        "```",
        "",
        "## Quick Start",
        "",
        "```python",
        "import dartlab",
        "",
        "# Korean company (DART)",
        'c = dartlab.Company("005930")       # Samsung Electronics',
        "c.index                              # company structure index",
        'c.show("BS")                         # balance sheet',
        'c.show("executiveCompensation")      # topic payload',
        'c.trace("dividend")                  # source provenance',
        "c.ratios                             # 47 financial ratios",
        "c.insights                           # 7-area A~F grades",
        "",
        "# US company (EDGAR)",
        'us = dartlab.Company("AAPL")         # Apple Inc.',
        "us.BS                                # balance sheet",
        "us.ratios                            # financial ratios",
        "us.sections                          # 10-K sections map",
        "```",
        "",
        "## Key Features",
        "",
        "- **Sections-first architecture**: Every company becomes a topic x period DataFrame",
        "- **Dual market**: DART (Korea) + EDGAR (US) with identical interface",
        "- **One stock code**: `dartlab.Company('005930')` or `dartlab.Company('AAPL')`",
        "- **Financial statements**: BS, IS, CF, CIS, SCE — XBRL-normalized, quarterly standalone",
        "- **47 financial ratios**: ROE, ROA, operating margin, debt ratio, PER, PBR, FCF, etc.",
        "- **7-area insight grades**: Performance, profitability, stability, cash flow, governance, risk, opportunity",
        "- **AI analysis**: `dartlab ask '삼성전자 분석해줘'` — natural language company analysis",
        "- **MCP server**: Expose company data as MCP tools for Claude Desktop, ChatGPT, Cursor",
        "- **329 topics per company**: From dividend policy to segment breakdown",
        "",
        "## Data Modules",
        "",
    ]

    for cat in getCategories():
        entries = getEntries(category=cat)
        lines.append(f"### {_categoryLabel(cat)}")
        lines.append("")
        for e in entries:
            lines.append(f"- **{e.name}** ({e.label}): {e.description}")
        lines.append("")

    lines.extend(
        [
            "## Analysis Engines",
            "",
            "- **Sector classification**: WICS 11 sectors (override -> keyword -> KSIC 3-stage)",
            "- **Insight grades**: 7-area A~F grades"
            " (performance, profitability, stability, cash flow, governance, risk, opportunity)",
            "- **Market rank**: Revenue/assets/growth ranking — overall + within sector",
            "- **Financial ratios**: ROE, ROA, operating margin, debt ratio, PER, PBR, FCF — auto-calculated",
            "- **Supply chain**: Disclosed supplier/customer relationship mapping",
            "- **ESG**: ESG disclosure extraction and scoring",
            "- **Event study**: Abnormal return around disclosure dates",
            "",
            "## Links",
            "",
            "- Documentation: https://eddmpython.github.io/dartlab/docs/",
            "- GitHub: https://github.com/eddmpython/dartlab",
            "- PyPI: https://pypi.org/project/dartlab/",
            "- Demo: https://huggingface.co/spaces/eddmpython/dartlab",
            "",
        ]
    )

    return "\n".join(lines)


# ─── Skills reference 생성 ─────────────────────────────────────


def generateSkillRef() -> str:
    """Claude Code 스킬용 reference.md 생성."""
    header = "# dartlab API Reference (Skills용)\n\n이 문서는 `scripts/generateSpec.py`에 의해 자동 생성됩니다.\n\n"
    parts = [
        header,
        _pythonApiSection(),
        _cliSection(),
        _dataModulesSection(),
        _scanAxisSection(),
        _gatherAxisSection(),
        _companySection(),
        _dataclassesSection(),
    ]
    return "\n---\n\n".join(parts)


# ─── _generated_catalog.py 생성 ────────────────────────────────


_SUPER_TOOL_NAMES = {"execute_code"}


def _generateCatalog() -> str:
    """AI 시스템 프롬프트용 도구 카탈로그 Python 파일 생성.

    Super Tool 11개만 포함 — LLM이 실제 tool calling으로 사용하는 도구만.
    defaults 도구는 Super Tool 내부에서 dispatch되므로 여기 불필요.
    """
    allTools = _collectAllToolSpecs()
    superTools = [s for s in allTools if s.name in _SUPER_TOOL_NAMES]

    catalogLines = [
        "## [필수] 도구 사용 규칙",
        "- **모든 수치 답변은 반드시 도구를 호출해서 실제 데이터를 가져온 뒤 답변하세요.**",
        "- 추측이나 일반 지식으로 숫자를 답하지 마세요. 반드시 도구로 확인 후 답변.",
        "- 도구 호출 없이 재무 수치를 언급하면 오답 위험이 큽니다.",
        "- 도구 파라미터는 아래 명시된 것만 사용하세요. 존재하지 않는 파라미터를 임의 생성하지 마세요.",
        "",
    ]

    # Super Tool 10개 상세 설명
    for spec in superTools:
        descFirst = spec.description.strip().split("\n")[0]
        props = spec.schema.get("properties", {})
        actionProp = props.get("action", {})
        actionEnum = actionProp.get("enum", [])

        catalogLines.append(f"### {spec.name} (priority: {spec.priority}, category: {spec.category})")
        catalogLines.append(descFirst)

        if actionEnum:
            actionDescs: dict[str, str] = {}
            for line in spec.description.split("\n"):
                stripped = line.strip()
                if stripped.startswith("- ") and ":" in stripped:
                    parts = stripped[2:].split(":", 1)
                    key = parts[0].strip()
                    if key in actionEnum:
                        val = parts[1].strip()
                        if len(val) > 70:
                            val = val[:67] + "..."
                        actionDescs[key] = val

            for act in actionEnum:
                desc = actionDescs.get(act, "")
                if desc:
                    catalogLines.append(f"  - {act}: {desc}")
                else:
                    catalogLines.append(f"  - {act}")

        # 핵심 파라미터 (action 제외)
        otherParams = {k: v for k, v in props.items() if k != "action" and isinstance(v, dict)}
        if otherParams:
            paramStrs = []
            for pName, pSchema in otherParams.items():
                pDesc = pSchema.get("description", "")
                if isinstance(pDesc, str) and len(pDesc) > 50:
                    pDesc = pDesc[:47] + "..."
                paramStrs.append(f"  [{pName}] {pDesc}" if pDesc else f"  [{pName}]")
            catalogLines.extend(paramStrs)

        # Guide 섹션 추출 (description에 "## Guide" 또는 "Guide:" 포함 시)
        guideLines: list[str] = []
        inGuide = False
        for line in spec.description.split("\n"):
            stripped = line.strip()
            if stripped.lower() in ("guide:", "## guide"):
                inGuide = True
                continue
            if inGuide:
                if stripped.startswith("##") or (stripped.endswith(":") and not stripped.startswith("-")):
                    break
                if stripped.startswith("- "):
                    guideLines.append(f"  {stripped}")
                elif stripped:
                    guideLines.append(f"  {stripped}")
        if guideLines:
            catalogLines.append("  Guide:")
            catalogLines.extend(guideLines)

        catalogLines.append("")

    # 도구 연쇄 패턴
    chains: list[str] = []
    for spec in superTools:
        for line in spec.description.split("\n"):
            stripped = line.strip()
            if "연쇄 사용" in stripped or "연쇄사용" in stripped:
                chains.append(f"- {spec.name}: {stripped}")

    if chains:
        catalogLines.append("## 도구 연쇄 패턴")
        catalogLines.extend(chains)
        catalogLines.append("")

    # 기업 비교 패턴 (execute_code 기반)
    catalogLines.extend(
        [
            "## 기업 비교 패턴",
            "두 기업의 매출/이익/비율을 비교하려면 execute_code로 코드 생성:",
            "```",
            "import dartlab",
            "c1 = dartlab.Company('005930')",
            "c2 = dartlab.Company('000660')",
            "print('삼성전자 IS:', c1.IS)",
            "print('SK하이닉스 IS:', c2.IS)",
            "```",
            "CAPABILITIES의 Company API를 참조하여 비교 코드를 작성.",
            "",
        ]
    )

    catalogText = "\n".join(catalogLines)

    return (
        '"""AI 시스템 프롬프트용 도구 카탈로그 (자동 생성).\n'
        "\n"
        "이 파일은 scripts/generateSpec.py가 자동 생성합니다. 직접 수정 금지.\n"
        "execute_code 도구 -- CAPABILITIES 기반 코드 생성 + 실행.\n"
        '"""\n'
        "\n"
        f"TOOL_CATALOG = {json.dumps(catalogText, ensure_ascii=False, indent=None)}\n"
    )


# ─── _generatedCapabilities.py 생성 ───────────────────────────


def _generateCapabilitiesPy() -> str:
    """런타임 capabilities 카탈로그 Python 파일 생성.

    __all__ 함수 + Company 메서드 + Scan 축 + Gather 축을 하나의 dict로.
    """
    import dartlab
    from dartlab.providers.dart.company import Company as DartCompany

    entries: dict[str, dict[str, str]] = {}

    # 1) __all__ 함수/클래스
    allNames = getattr(dartlab, "__all__", [])
    for name in allNames:
        obj = getattr(dartlab, name, None)
        if obj is None:
            continue
        kind = "class" if inspect.isclass(obj) else "function" if callable(obj) else "module"
        doc = inspect.getdoc(obj)
        summary = doc.split("\n")[0].strip() if doc else ""
        sections = _parseDocstringSections(doc)
        entry: dict[str, str] = {"summary": summary, "kind": kind}
        if cap := sections.get("capabilities"):
            entry["capabilities"] = cap
        if req := sections.get("requires"):
            entry["requires"] = req
        if ctx := sections.get("aicontext"):
            entry["aicontext"] = ctx
        if guide := sections.get("guide"):
            entry["guide"] = guide
        if seeAlso := sections.get("seealso"):
            entry["seeAlso"] = seeAlso
        entries[name] = entry

    # 2) Company 공개 메서드/프로퍼티
    for memberName in sorted(dir(DartCompany)):
        if memberName.startswith("_"):
            continue
        obj = getattr(DartCompany, memberName, None)
        if obj is None:
            continue
        if isinstance(obj, (staticmethod, classmethod)):
            continue

        kind = "property" if isinstance(inspect.getattr_static(DartCompany, memberName), property) else "method"
        doc = None
        if kind == "property":
            prop = inspect.getattr_static(DartCompany, memberName)
            if prop.fget:
                doc = inspect.getdoc(prop.fget)
        else:
            doc = inspect.getdoc(obj)
        if doc is None:
            continue

        summary = doc.split("\n")[0].strip()
        sections = _parseDocstringSections(doc)
        entry = {"summary": summary, "kind": kind}
        if cap := sections.get("capabilities"):
            entry["capabilities"] = cap
        if req := sections.get("requires"):
            entry["requires"] = req
        if ctx := sections.get("aicontext"):
            entry["aicontext"] = ctx
        if guide := sections.get("guide"):
            entry["guide"] = guide
        if seeAlso := sections.get("seealso"):
            entry["seeAlso"] = seeAlso
        entries[f"Company.{memberName}"] = entry

    # 3) Scan 축 (AST)
    scanInit = SRC / "dartlab" / "scan" / "__init__.py"
    if scanInit.exists():
        try:
            tree = ast.parse(scanInit.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == "_AXIS_REGISTRY":
                            if isinstance(node.value, ast.Dict):
                                for k, v in zip(node.value.keys, node.value.values):
                                    if isinstance(k, ast.Constant) and isinstance(v, ast.Call):
                                        axisName = str(k.value)
                                        axisEntry: dict[str, str] = {"kind": "scan_axis"}
                                        for kw in v.keywords:
                                            if kw.arg == "label" and isinstance(kw.value, ast.Constant):
                                                axisEntry["summary"] = str(kw.value.value)
                                            elif kw.arg == "description" and isinstance(kw.value, ast.Constant):
                                                axisEntry["capabilities"] = str(kw.value.value)
                                        entries[f"scan.{axisName}"] = axisEntry
        except SyntaxError:
            pass

    # 4) Gather 축 (AST)
    gatherEntry = SRC / "dartlab" / "gather" / "entry.py"
    if gatherEntry.exists():
        try:
            tree = ast.parse(gatherEntry.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == "_AXIS_REGISTRY":
                            if isinstance(node.value, ast.Dict):
                                for k, v in zip(node.value.keys, node.value.values):
                                    if isinstance(k, ast.Constant) and isinstance(v, ast.Call):
                                        axisName = str(k.value)
                                        axisEntry = {"kind": "gather_axis"}
                                        for kw in v.keywords:
                                            if kw.arg == "label" and isinstance(kw.value, ast.Constant):
                                                axisEntry["summary"] = str(kw.value.value)
                                            elif kw.arg == "description" and isinstance(kw.value, ast.Constant):
                                                axisEntry["capabilities"] = str(kw.value.value)
                                        entries[f"gather.{axisName}"] = axisEntry
        except SyntaxError:
            pass

    dictRepr = json.dumps(entries, ensure_ascii=False, indent=4, sort_keys=True)

    return (
        '"""런타임 capabilities 카탈로그 (자동 생성).\n'
        "\n"
        "이 파일은 scripts/generateSpec.py가 자동 생성합니다. 직접 수정 금지.\n"
        '"""\n'
        "\n"
        f"CAPABILITIES: dict[str, dict] = {dictRepr}\n"
    )


# ─── main ───────────────────────────────────────────────────────


def main():
    capabilitiesPath = ROOT / "CAPABILITIES.md"
    llmsTxtPath = ROOT / "landing" / "static" / "llms.txt"
    skillRefPath = ROOT / ".claude" / "skills" / "dartlab" / "reference.md"
    catalogPath = SRC / "dartlab" / "ai" / "conversation" / "_generatedCatalog.py"
    capabilitiesPyPath = SRC / "dartlab" / "core" / "_generatedCapabilities.py"

    skillRefPath.parent.mkdir(parents=True, exist_ok=True)

    capabilities = generateCapabilities()
    capabilitiesPath.write_text(capabilities, encoding="utf-8")
    print(f"  CAPABILITIES.md ({len(capabilities):,} chars) -> {capabilitiesPath}")

    llmsTxt = generateLlmsTxt()
    llmsTxtPath.write_text(llmsTxt, encoding="utf-8")
    print(f"  llms.txt        ({len(llmsTxt):,} chars) -> {llmsTxtPath}")

    skillRef = generateSkillRef()
    skillRefPath.write_text(skillRef, encoding="utf-8")
    print(f"  reference.md    ({len(skillRef):,} chars) -> {skillRefPath}")

    catalog = _generateCatalog()
    catalogPath.write_text(catalog, encoding="utf-8")
    print(f"  _generatedCatalog.py ({len(catalog):,} chars) -> {catalogPath}")

    capabilitiesPy = _generateCapabilitiesPy()
    capabilitiesPyPath.write_text(capabilitiesPy, encoding="utf-8")
    print(f"  _generatedCapabilities.py ({len(capabilitiesPy):,} chars) -> {capabilitiesPyPath}")

    print("\n  완료.")


if __name__ == "__main__":
    main()
