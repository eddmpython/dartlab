"""registry 기반 자동 문서 생성.

5개 surface에서 코드를 수집하여 다음 파일을 자동 생성한다:
- CAPABILITIES.md           — 루트 총괄 스펙맵 (신규)
- landing/static/llms.txt   — AI 크롤러용 구조화 문서
- .claude/skills/dartlab/reference.md — Claude Code 스킬 레퍼런스

실행:
    uv run python scripts/generateSpec.py

릴리즈 시 CI에서 자동 실행하여 수동 관리 포인트를 제거한다.
"""

from __future__ import annotations

import ast
import dataclasses
import inspect
import sys
import textwrap
from pathlib import Path
from typing import get_type_hints

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


# ─── Surface 1: Python API (__init__.py __all__) ────────────────


def _pythonApiSection() -> str:
    """__init__.py __all__에서 callable의 docstring 첫 줄 수집."""
    import dartlab

    allNames = getattr(dartlab, "__all__", [])
    lines = [f"## Python API ({len(allNames)}개)\n"]
    lines.append("`import dartlab` 후 사용 가능한 공개 API.\n")
    lines.append("| 이름 | 종류 | 설명 |")
    lines.append("|------|------|------|")

    for name in allNames:
        obj = getattr(dartlab, name, None)
        if obj is None:
            lines.append(f"| `{name}` | - | - |")
            continue
        kind = "class" if inspect.isclass(obj) else "function" if callable(obj) else "module"
        doc = inspect.getdoc(obj)
        desc = doc.split("\n")[0].strip() if doc else "-"
        lines.append(f"| `{name}` | {kind} | {desc} |")

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


def _parseRegisterToolCalls(filepath: Path) -> list[tuple[str, str]]:
    """AST로 registerTool(name, func, description, ...) 호출에서 (name, description) 추출."""
    try:
        tree = ast.parse(filepath.read_text(encoding="utf-8"), filename=str(filepath))
    except SyntaxError:
        return []

    tools: list[tuple[str, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        # registerTool(...) 또는 register_tool(...)
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

        # 첫 번째 인자: name (문자열)
        nameNode = node.args[0]
        if isinstance(nameNode, ast.Constant) and isinstance(nameNode.value, str):
            name = nameNode.value
        else:
            continue

        # 세 번째 인자: description (문자열 또는 JoinedStr)
        descNode = node.args[2]
        if isinstance(descNode, ast.Constant) and isinstance(descNode.value, str):
            desc = descNode.value.split("\n")[0].strip()
        elif isinstance(descNode, ast.JoinedStr):
            # f-string — 첫 Constant 조각만
            parts = []
            for val in descNode.values:
                if isinstance(val, ast.Constant):
                    parts.append(str(val.value))
            desc = "".join(parts).split("\n")[0].strip()
        else:
            desc = "-"

        tools.append((name, desc))
    return tools


def _aiToolsSection() -> str:
    """AI tool 등록에서 name + description 수집."""
    toolsDir = SRC / "dartlab" / "ai" / "tools"
    allTools: list[tuple[str, str]] = []
    seen: set[str] = set()

    # super tools 우선
    superDir = toolsDir / "superTools"
    if superDir.exists():
        for pyFile in sorted(superDir.glob("*.py")):
            if pyFile.name.startswith("_"):
                continue
            for name, desc in _parseRegisterToolCalls(pyFile):
                if name not in seen:
                    allTools.append((name, desc))
                    seen.add(name)

    # defaults
    defaultsDir = toolsDir / "defaults"
    if defaultsDir.exists():
        for pyFile in sorted(defaultsDir.glob("*.py")):
            if pyFile.name.startswith("_"):
                continue
            for name, desc in _parseRegisterToolCalls(pyFile):
                if name not in seen:
                    allTools.append((name, desc))
                    seen.add(name)

    lines = [f"## AI Tools ({len(allTools)}개)\n"]
    lines.append("LLM 에이전트가 tool calling으로 사용하는 도구.\n")
    lines.append("| 도구 | 설명 |")
    lines.append("|------|------|")

    for name, desc in allTools:
        # 80자 제한
        if len(desc) > 80:
            desc = desc[:77] + "..."
        lines.append(f"| `{name}` | {desc} |")

    lines.append("")
    return "\n".join(lines)


# ─── Company facade (기존 유지) ─────────────────────────────────


def _companySection() -> str:
    """Company facade + 엔진 Company 사용법."""
    return textwrap.dedent("""\
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

    ### 핵심 property

    | property | 반환 | 설명 |
    |----------|------|------|
    | `BS` | DataFrame | 재무상태표 |
    | `IS` | DataFrame | 손익계산서 |
    | `CIS` | DataFrame | 포괄손익계산서 |
    | `CF` | DataFrame | 현금흐름표 |
    | `sections` | DataFrame | merged topic x period company table |
    | `ratios` | RatioResult | 재무비율 |
    | `index` | DataFrame | 회사 구조 인덱스 |
    | `insights` | AnalysisResult | 7영역 인사이트 등급 |

    ### 핵심 메서드

    | 메서드 | 설명 |
    |--------|------|
    | `show(topic)` | topic payload 조회 |
    | `trace(topic)` | source provenance 조회 |
    | `diff()` | 기간간 변화 감지 |
    | `filings()` | 공시 문서 목록 |
    """)


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

    from dartlab.analysis.comparative.rank.rank import RankInfo

    lines.append(_dataclassTable(RankInfo, "RankInfo"))

    return "\n".join(lines)


# ─── CAPABILITIES.md 생성 ──────────────────────────────────────


def generateCapabilities() -> str:
    """루트 CAPABILITIES.md 생성 — 5 surface 통합."""
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
        _companySection(),
        _dataclassesSection(),
    ]
    return "\n---\n\n".join(parts)


# ─── main ───────────────────────────────────────────────────────


def main():
    capabilitiesPath = ROOT / "CAPABILITIES.md"
    llmsTxtPath = ROOT / "landing" / "static" / "llms.txt"
    skillRefPath = ROOT / ".claude" / "skills" / "dartlab" / "reference.md"

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

    print("\n  완료.")


if __name__ == "__main__":
    main()
