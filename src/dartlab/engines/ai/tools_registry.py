"""DartLab 분석 도구 레지스트리 — OpenAI function calling 형식.

LLM 에이전트가 사용할 수 있는 도구를 등록·관리한다.
Company 인스턴스에 바인딩된 도구를 생성하여 tool calling에 사용.
"""

from __future__ import annotations

import json
from typing import Any, Callable

import polars as pl

from dartlab.engines.ai.tool_runtime import (
    ToolRuntime,
    create_tool_runtime,
    get_default_tool_runtime,
    set_default_tool_runtime,
)


def register_tool(
    name: str,
    func: Callable[..., str],
    description: str,
    parameters: dict,
) -> None:
    """도구 등록."""
    get_default_tool_runtime().register_tool(name, func, description, parameters)


def get_tool_schemas() -> list[dict]:
    """등록된 도구의 OpenAI function calling 스키마 목록."""
    return get_default_tool_runtime().get_tool_schemas()


def execute_tool(name: str, arguments: dict) -> str:
    """도구 실행. 결과는 문자열(마크다운)로 반환."""
    return get_default_tool_runtime().execute_tool(name, arguments)


def clear_registry() -> None:
    """등록된 모든 도구 제거 (테스트용)."""
    get_default_tool_runtime().clear()


def _df_to_md(df: pl.DataFrame, max_rows: int = 15) -> str:
    """DataFrame → 마크다운 테이블."""
    if df is None or df.height == 0:
        return "(데이터 없음)"

    from dartlab.engines.ai.context import df_to_markdown

    return df_to_markdown(df, max_rows=max_rows)


def _json_to_text(value: Any, max_chars: int = 4000) -> str:
    """dict/list/json 직렬화."""
    text = json.dumps(value, ensure_ascii=False, indent=2, default=str)
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n... (truncated)"


def _format_tool_value(value: Any, *, max_rows: int = 30, max_chars: int = 4000) -> str:
    """도구 반환값을 문자열로 표준화."""
    if isinstance(value, pl.DataFrame):
        return _df_to_md(value, max_rows=max_rows)
    if isinstance(value, (dict, list, tuple)):
        return _json_to_text(value, max_chars=max_chars)
    return str(value)


def _maybe_int(value: Any) -> int | None:
    """빈 값이면 None, 아니면 int 변환."""
    if value in (None, "", False):
        return None
    return int(value)


def _csv_list(value: str | None) -> list[str] | None:
    """쉼표 구분 문자열 → 리스트."""
    if not value:
        return None
    items = [item.strip() for item in value.split(",") if item.strip()]
    return items or None


def _build_system_spec_markdown() -> str:
    """시스템 요약 스펙을 사람이 읽기 쉬운 마크다운으로 반환."""
    from dartlab.engines.ai.spec import buildSpec

    spec = buildSpec(depth="summary")
    lines = [f"# {spec['system']['name']} v{spec['system']['version']}"]
    lines.append(f"{spec['system']['description']} ({spec['system']['coverage']})")
    lines.append("")
    lines.append("## 엔진 목록")
    for name, info in spec.get("engines", {}).items():
        lines.append(f"### {name}")
        lines.append(f"- {info.get('description', '')}")
        summary = info.get("summary", {})
        for key, value in summary.items():
            lines.append(f"- {key}: {value}")
    return "\n".join(lines)


def _count_local_parquets(category: str) -> int:
    """카테고리별 로컬 parquet 파일 수."""
    from dartlab.core.dataLoader import _dataDir

    try:
        data_dir = _dataDir(category)
    except (FileNotFoundError, KeyError, OSError, PermissionError, ValueError):
        return 0
    if not data_dir.exists():
        return 0
    return len(list(data_dir.glob("*.parquet")))


def _build_tool_catalog_markdown(include_parameters: bool = False) -> str:
    """현재 등록된 tool schema를 마크다운으로 노출."""
    schemas = get_tool_schemas()
    lines = [f"# 등록된 대화 도구 ({len(schemas)}개)"]
    for schema in schemas:
        fn = schema.get("function", {})
        name = fn.get("name", "")
        desc = fn.get("description", "")
        lines.append(f"## `{name}`")
        lines.append(f"- {desc}")
        if include_parameters:
            params = fn.get("parameters", {}).get("properties", {})
            required = set(fn.get("parameters", {}).get("required", []))
            for key, info in params.items():
                info_type = info.get("type", "any")
                requirement = "required" if key in required else "optional"
                description = info.get("description", "")
                lines.append(f"- `{key}` ({info_type}, {requirement}): {description}")
    return "\n".join(lines)


def _build_runtime_capabilities_markdown(company: Any | None = None) -> str:
    """UI 대화에서 설명해야 하는 실제 기능 범위를 registry/tool 기준으로 요약."""
    from dartlab.core.registry import getCategories, getEntries
    from dartlab.engines.ai.codex_cli import inspect_codex_cli

    local_counts = {
        "docs": _count_local_parquets("docs"),
        "finance": _count_local_parquets("finance"),
        "edgarDocs": _count_local_parquets("edgarDocs"),
        "edgar": _count_local_parquets("edgar"),
    }
    registry_counts = {category: len(getEntries(category=category)) for category in getCategories()}
    tool_names = [schema.get("function", {}).get("name", "") for schema in get_tool_schemas()]
    codex_info = inspect_codex_cli()
    codex_commands = ", ".join(f"`{name}`" for name in codex_info.get("commands", [])[:8]) or "(미확인)"
    sandbox_modes = ", ".join(f"`{mode}`" for mode in codex_info.get("sandboxModes", [])) or "(미확인)"

    lines = [
        "# DartLab 런타임 기능 범위",
        "",
        "## 자동 인식된 대화 도구",
        f"- 현재 등록된 도구: {len(tool_names)}개",
        f"- 도구 목록: {', '.join(f'`{name}`' for name in tool_names)}",
        "- 새 도구가 등록되면 이 목록과 에이전트 사용 surface에 자동 반영됨",
        "",
        "## 시장 / 진입점",
        '- `Company("005930")`, `Company("삼성전자")` → 한국 DART Company',
        '- `Company("AAPL")` → 미국 SEC EDGAR Company',
        "- `OpenDart()` → DART 공개 API 원문/편의 래퍼",
        "- `OpenEdgar()` → SEC 공개 API 원문/편의 래퍼",
        "",
        "## Registry 기반 데이터 surface",
        f"- registry 카테고리: {', '.join(f'`{name}`({registry_counts[name]}개)' for name in sorted(registry_counts))}",
        "- `core/registry.py`에 엔트리를 추가하면 모듈 설명/검색/조회 surface가 함께 확장됨",
        "",
        "## UI 대화에서 가능한 것",
        "- 종목 검색, 회사 선택, sections/show/trace/diff 기반 공시 탐색",
        "- 재무표 조회, 재무비율, YoY, CAGR, 이상치, 요약 통계 계산",
        "- insight/sector/rank 분석 엔진 호출",
        "- OpenDart/OpenEdgar 공개 API를 대화 도구로 직접 호출",
        "- Excel 내보내기, 템플릿 생성/조회/재사용",
        "- 로컬 데이터 현황 확인, 데이터 다운로드 트리거",
        "- Codex CLI 브리지로 실제 코드 작업, 수정, 리뷰 요청 전달",
        "",
        "## EDGAR에서 더 받을 수 있는 데이터",
        '- `Company("AAPL")` 경로로 저장된 EDGAR docs/finance를 바로 읽을 수 있음',
        '- `OpenEdgar().search("Apple")` → issuer 검색',
        '- `OpenEdgar()("AAPL").filings()` → submissions 기반 filing 목록',
        '- `OpenEdgar()("AAPL").companyFactsJson()` / `companyConceptJson()` / `frameJson(...)` → SEC raw 데이터',
        '- `OpenEdgar()("AAPL").saveDocs(sinceYear=2009)` → EDGAR docs parquet 추가 수집',
        '- `OpenEdgar()("AAPL").saveFinance()` → companyfacts parquet 저장',
        "",
        "## OpenAPI 범위",
        "- DART: 기업 검색, 공시 목록, 정기보고서/재무 API, 저장용 saver",
        "- EDGAR: issuer resolve/search, submissions, filings DataFrame, companyfacts/companyconcept/frames, docs/finance saver",
        "",
        "## GPT / Codex 연결 범위",
        "- OpenAI, ChatGPT, Codex CLI, Ollama 등을 채팅 백엔드로 연결 가능",
        "- 현재 UI에서는 코드 설명, 코드 초안, 리팩터링 제안 같은 텍스트 기반 코딩 보조는 가능",
        f"- Codex CLI 상태: {'설치됨' if codex_info.get('installed') else '미설치'}"
        + (f" / {codex_info['version']}" if codex_info.get("version") else ""),
        f"- Codex CLI 명령 자동 인식: {codex_commands}",
        f"- Codex sandbox 자동 인식: {sandbox_modes}",
        "- `codex` provider는 코드/파일 수정 의도가 보이면 `workspace-write`를 우선 사용하고, 일반 질의는 `read-only`를 유지",
        "- `run_codex_task` 도구를 통해 다른 provider에서도 Codex CLI에 코드 작업을 위임할 수 있음",
        "- `claude-code` provider는 OAuth 지원 전까지 공개 surface에서 제공하지 않음",
        "- Codex CLI help/config가 바뀌면 상태/설명 경로가 다시 검사되어 자동 반영됨",
        "",
        "## 로컬 데이터 현황",
        f"- DART docs: {local_counts['docs']}개",
        f"- DART finance: {local_counts['finance']}개",
        f"- EDGAR docs: {local_counts['edgarDocs']}개",
        f"- EDGAR finance: {local_counts['edgar']}개",
    ]

    if company is not None:
        from dartlab.engines.ai.context import scan_available_modules

        modules = scan_available_modules(company)
        lines.extend(
            [
                "",
                "## 현재 선택 기업에서 바로 쓸 수 있는 데이터",
                f"- 회사: {getattr(company, 'corpName', '-')}",
                f"- 즉시 조회 가능한 모듈: {len(modules)}개",
            ]
        )
        if modules:
            module_preview = ", ".join(f"`{module['name']}`" for module in modules[:15])
            lines.append(f"- 상위 모듈: {module_preview}")

    lines.extend(
        [
            "",
            "## 추천 다음 질문",
            "- `AAPL에서 지금 바로 볼 수 있는 데이터 알려줘`",
            "- `EDGAR docs를 더 받으려면 어떤 경로를 써야 해?`",
            "- `OpenDart와 OpenEdgar로 할 수 있는 일을 비교해줘`",
            "- `현재 등록된 도구 목록과 파라미터를 보여줘`",
            "- `현재 워크스페이스에서 이 버그를 고치도록 Codex에 맡겨줘`",
        ]
    )
    return "\n".join(lines)


def build_tool_runtime(company: Any | None = None, *, name: str = "session") -> ToolRuntime:
    """Build an isolated tool runtime populated with current default tools."""
    runtime = create_tool_runtime(name=name)
    register_defaults(company, runtime=runtime)
    return runtime


def register_defaults(company: Any | None = None, *, runtime: ToolRuntime | None = None) -> ToolRuntime:
    """전역 기능 + Company 바인딩 분석 도구 등록."""
    if runtime is not None:
        previous_runtime = get_default_tool_runtime()
        set_default_tool_runtime(runtime)
        try:
            return register_defaults(company)
        finally:
            set_default_tool_runtime(previous_runtime)

    clear_registry()

    def get_system_spec() -> str:
        return _build_system_spec_markdown()

    register_tool(
        "get_system_spec",
        get_system_spec,
        "DartLab 시스템의 전체 스펙(엔진 목록, 데이터 종류, 기능)을 조회합니다. "
        "사용자가 '어떤 데이터가 있어?', '무슨 분석이 가능해?' 같은 메타 질문을 할 때 사용하세요.",
        {"type": "object", "properties": {}},
    )

    def get_engine_spec(engine: str) -> str:
        from dartlab.engines.ai.spec import buildSpec, getEngineSpec

        spec = getEngineSpec(engine)
        if spec is None:
            all_spec = buildSpec(depth="summary")
            available = ", ".join(all_spec.get("engines", {}).keys())
            return f"'{engine}' 엔진을 찾을 수 없습니다. 사용 가능한 엔진: {available}"
        return json.dumps(spec, ensure_ascii=False, indent=2, default=str)

    register_tool(
        "get_engine_spec",
        get_engine_spec,
        "특정 엔진의 상세 스펙을 조회합니다. "
        "엔진명 예시: insight(인사이트), sector(섹터분류), rank(규모순위), "
        "dart.finance(재무제표), dart.report(정기보고서). "
        "각 엔진이 제공하는 구체적 지표·영역·분류 기준을 확인할 수 있습니다.",
        {
            "type": "object",
            "properties": {
                "engine": {
                    "type": "string",
                    "description": "엔진명 (예: insight, sector, rank, dart.finance, dart.report)",
                },
            },
            "required": ["engine"],
        },
    )

    def get_runtime_capabilities() -> str:
        return _build_runtime_capabilities_markdown(company)

    register_tool(
        "get_runtime_capabilities",
        get_runtime_capabilities,
        "DartLab UI 대화에서 실제로 가능한 기능 범위를 요약합니다. "
        "EDGAR에서 더 받을 수 있는 데이터, OpenAPI 범위, GPT/Codex 연결 시 가능한 코딩 범위를 물을 때 우선 사용하세요.",
        {"type": "object", "properties": {}},
    )

    def get_tool_catalog(include_parameters: bool = False) -> str:
        return _build_tool_catalog_markdown(include_parameters=include_parameters)

    register_tool(
        "get_tool_catalog",
        get_tool_catalog,
        "현재 대화에서 등록된 도구 목록을 조회합니다. 새로 추가된 도구도 현재 registry 기준으로 자동 반영됩니다.",
        {
            "type": "object",
            "properties": {
                "include_parameters": {
                    "type": "boolean",
                    "description": "true면 각 도구의 파라미터까지 함께 출력",
                    "default": False,
                }
            },
        },
    )

    def run_codex_task(
        prompt: str,
        sandbox: str = "workspace-write",
        model: str = "",
        timeout_seconds: int = 300,
    ) -> str:
        from dartlab.engines.ai.codex_cli import inspect_codex_cli, run_codex_exec

        info = inspect_codex_cli()
        if not info.get("installed"):
            return "Codex CLI가 설치되어 있지 않습니다. 먼저 `codex --version`이 동작해야 합니다."

        sandbox_modes = set(info.get("sandboxModes") or [])
        selected_sandbox = sandbox
        if sandbox_modes and sandbox not in sandbox_modes:
            selected_sandbox = "workspace-write" if "workspace-write" in sandbox_modes else "read-only"

        answer, usage = run_codex_exec(
            prompt,
            model=model or None,
            sandbox=selected_sandbox,
            timeout=timeout_seconds,
        )
        lines = [
            "## Codex 작업 결과",
            f"- sandbox: {selected_sandbox}",
            f"- model: {model or info.get('configuredModel') or 'CLI default'}",
        ]
        if usage:
            lines.append(f"- tokens: {usage.get('total_tokens', '?')}")
        lines.extend(["", answer])
        return "\n".join(lines)

    register_tool(
        "run_codex_task",
        run_codex_task,
        "Codex CLI에 현재 워크스페이스 코드 작업을 위임합니다. "
        "명시적인 코드 수정, 리팩터링, 테스트 보강, 리뷰 요청에서만 사용하세요. "
        "workspace-write sandbox를 사용하면 실제 파일이 수정될 수 있습니다.",
        {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Codex에 전달할 코드 작업 지시문",
                },
                "sandbox": {
                    "type": "string",
                    "description": "read-only, workspace-write, danger-full-access 중 하나",
                    "default": "workspace-write",
                },
                "model": {
                    "type": "string",
                    "description": "Codex CLI에 전달할 모델명. 비우면 CLI 기본값 사용",
                    "default": "",
                },
                "timeout_seconds": {
                    "type": "integer",
                    "description": "최대 대기 시간(초)",
                    "default": 300,
                },
            },
            "required": ["prompt"],
        },
    )

    def search_company(keyword: str) -> str:
        from dartlab.core.kindList import searchName

        results = searchName(keyword)
        if results is None or (isinstance(results, pl.DataFrame) and results.is_empty()):
            return f"'{keyword}' 검색 결과가 없습니다."
        if isinstance(results, pl.DataFrame):
            return _df_to_md(results, max_rows=20)
        return str(results)[:2000]

    register_tool(
        "search_company",
        search_company,
        "종목명/종목코드로 기업을 검색합니다. 종목코드를 모를 때 사용하세요.",
        {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "검색 키워드 (예: '삼성', '현대차', '반도체')",
                },
            },
            "required": ["keyword"],
        },
    )

    def download_data(stock_code: str = "", category: str = "docs") -> str:
        from dartlab.core.dataLoader import downloadAll, loadData

        if category == "edgarDocs" and not stock_code:
            return (
                "EDGAR docs는 ticker를 지정한 개별 수집 경로를 사용하세요. 예: stock_code='AAPL', category='edgarDocs'"
            )
        if stock_code:
            loadData(stock_code, category=category)
            return f"{stock_code} {category} 데이터 다운로드 완료."
        downloadAll(category)
        return f"{category} 전체 데이터 다운로드 완료."

    register_tool(
        "download_data",
        download_data,
        "데이터를 다운로드합니다. "
        "stock_code를 지정하면 해당 종목만, 비워두면 카테고리 전체를 다운로드합니다. "
        "category: docs(공시문서), finance(재무), report(정기보고서), edgarDocs(미국 공시문서, ticker 필요).",
        {
            "type": "object",
            "properties": {
                "stock_code": {
                    "type": "string",
                    "description": "종목코드 또는 ticker (비워두면 전체)",
                    "default": "",
                },
                "category": {
                    "type": "string",
                    "description": "카테고리 (docs, finance, report, edgarDocs)",
                    "default": "docs",
                },
            },
        },
    )

    def data_status() -> str:
        from dartlab.core.dataLoader import DATA_RELEASES, _dataDir

        lines = ["| 카테고리 | 라벨 | 파일 수 |", "| --- | --- | --- |"]
        for cat, conf in DATA_RELEASES.items():
            data_dir = _dataDir(cat)
            count = len(list(data_dir.glob("*.parquet"))) if data_dir.exists() else 0
            lines.append(f"| {cat} | {conf['label']} | {count} |")
        return "\n".join(lines)

    register_tool(
        "data_status",
        data_status,
        "로컬에 저장된 데이터 현황(카테고리별 파일 수)을 조회합니다. "
        "'데이터 몇 개 있어?', '어떤 데이터가 있지?' 같은 질문에 사용하세요.",
        {"type": "object", "properties": {}},
    )

    def get_openapi_capabilities(market: str = "all") -> str:
        from dartlab import OpenDart

        sections: list[str] = []
        target = (market or "all").lower()

        if target in {"all", "dart", "kr"}:
            sections.extend(
                [
                    "## DART OpenAPI",
                    "- facade: `OpenDart()`",
                    "- action: `search`, `company`, `corp_code`, `corp_codes`",
                    "- action: `filings`, `finstate`, `report`",
                    "- action: `major_shareholders`, `executive_shares`",
                    "- action: `report_types`, `filing_types`, `markets`, `xbrl_taxonomy`",
                    "- save: `finance`, `report`, `filings`, `xbrl`",
                    f"- report type count: {len(OpenDart.reportTypes())}",
                ]
            )

        if target in {"all", "edgar", "us"}:
            sections.extend(
                [
                    "## EDGAR OpenAPI",
                    "- facade: `OpenEdgar()`",
                    "- action: `search`, `company`, `submissions`, `filings`",
                    "- action: `company_facts`, `company_concept`, `frame`",
                    "- save: `docs`, `finance`",
                ]
            )

        if not sections:
            return "market은 `all`, `dart`, `edgar` 중 하나여야 합니다."

        sections.extend(
            [
                "",
                "## 예시",
                "- `call_dart_openapi(action='report_types')`",
                "- `call_dart_openapi(action='report', corp='삼성전자', report_type='배당', start='2023')`",
                "- `call_edgar_openapi(action='filings', identifier='AAPL', forms='10-K,10-Q')`",
                "- `openapi_save(market='edgar', identifier='AAPL', dataset='docs', since_year=2018)`",
            ]
        )
        return "\n".join(["# OpenAPI 기능 범위", *sections])

    register_tool(
        "get_openapi_capabilities",
        get_openapi_capabilities,
        "DART/EDGAR OpenAPI surface를 요약합니다. "
        "사용자가 OpenDart, OpenEdgar, 공개 API로 뭘 할 수 있는지 물을 때 먼저 호출하세요.",
        {
            "type": "object",
            "properties": {
                "market": {
                    "type": "string",
                    "description": "all, dart, edgar 중 하나",
                    "default": "all",
                }
            },
        },
    )

    def call_dart_openapi(
        action: str,
        corp: str = "",
        query: str = "",
        start: str = "",
        end: str = "",
        quarter: int | None = None,
        report_type: str = "",
        listed: bool = False,
        disclosure_type: str = "",
        final: bool = False,
        market_code: str = "",
        consolidated: bool = True,
        full: bool = False,
        taxonomy_category: str = "",
    ) -> str:
        from dartlab import OpenDart

        dart = OpenDart()
        action_key = (action or "").strip().lower()
        start_arg = start or None
        end_arg = _maybe_int(end)

        if action_key == "search":
            if not query:
                return "query가 필요합니다."
            return _format_tool_value(dart.search(query, listed=listed))

        if action_key == "company":
            if not corp:
                return "corp가 필요합니다."
            return _format_tool_value(dart.company(corp))

        if action_key == "corp_code":
            target = corp or query
            if not target:
                return "corp 또는 query가 필요합니다."
            return _format_tool_value({"corpCode": dart.corpCode(target)})

        if action_key == "corp_codes":
            return _format_tool_value(dart.corpCodes())

        if action_key == "filings":
            corp_arg = corp or None
            result = dart.filings(
                corp_arg,
                start_arg,
                end or None,
                type=disclosure_type or None,
                final=final,
                market=market_code or None,
            )
            return _format_tool_value(result)

        if action_key == "finstate":
            if not corp:
                return "corp가 필요합니다."
            result = dart.finstate(
                corp,
                start_arg,
                end=end_arg,
                q=quarter,
                consolidated=consolidated,
                full=full,
            )
            return _format_tool_value(result)

        if action_key == "report":
            if not corp or not report_type:
                return "corp와 report_type이 필요합니다."
            result = dart.report(
                corp,
                report_type,
                start_arg,
                end=end_arg,
                q=quarter,
            )
            return _format_tool_value(result)

        if action_key == "major_shareholders":
            if not corp:
                return "corp가 필요합니다."
            return _format_tool_value(dart.majorShareholders(corp))

        if action_key == "executive_shares":
            if not corp:
                return "corp가 필요합니다."
            return _format_tool_value(dart.executiveShares(corp))

        if action_key == "report_types":
            return _format_tool_value(OpenDart.reportTypes())

        if action_key == "filing_types":
            return _format_tool_value(OpenDart.filingTypes())

        if action_key == "markets":
            return _format_tool_value(OpenDart.markets())

        if action_key == "xbrl_taxonomy":
            if not taxonomy_category:
                return "taxonomy_category가 필요합니다. 예: BS1, IS1, CF1"
            return _format_tool_value(dart.xbrlTaxonomy(taxonomy_category))

        return (
            "지원하지 않는 action입니다. "
            "search, company, corp_code, corp_codes, filings, finstate, report, "
            "major_shareholders, executive_shares, report_types, filing_types, markets, xbrl_taxonomy"
        )

    register_tool(
        "call_dart_openapi",
        call_dart_openapi,
        "DART OpenAPI를 직접 호출합니다. "
        "action 예시: search, company, corp_code, corp_codes, filings, finstate, report, "
        "major_shareholders, executive_shares, report_types, filing_types, markets, xbrl_taxonomy.",
        {
            "type": "object",
            "properties": {
                "action": {"type": "string", "description": "호출할 DART action"},
                "corp": {"type": "string", "description": "회사명/종목코드/corp_code"},
                "query": {"type": "string", "description": "search용 검색어"},
                "start": {"type": "string", "description": "시작일 또는 연도"},
                "end": {"type": "string", "description": "종료일 또는 종료 연도"},
                "quarter": {"type": "integer", "description": "분기. 0~4 또는 null"},
                "report_type": {"type": "string", "description": "예: 배당, 직원, 임원"},
                "listed": {"type": "boolean", "description": "상장사만 검색", "default": False},
                "disclosure_type": {"type": "string", "description": "공시유형 예: A"},
                "final": {"type": "boolean", "description": "최종보고서만", "default": False},
                "market_code": {"type": "string", "description": "법인구분 Y/K/N/E"},
                "consolidated": {"type": "boolean", "description": "연결 기준", "default": True},
                "full": {"type": "boolean", "description": "전체 계정", "default": False},
                "taxonomy_category": {"type": "string", "description": "xbrl taxonomy 카테고리"},
            },
            "required": ["action"],
        },
    )

    def call_edgar_openapi(
        action: str,
        identifier: str = "",
        query: str = "",
        forms: str = "",
        since: str = "",
        until: str = "",
        taxonomy: str = "",
        tag: str = "",
        unit: str = "",
        period: str = "",
    ) -> str:
        from dartlab import OpenEdgar

        edgar = OpenEdgar()
        action_key = (action or "").strip().lower()

        if action_key == "search":
            if not query:
                return "query가 필요합니다."
            return _format_tool_value(edgar.search(query))

        if action_key == "company":
            if not identifier:
                return "identifier가 필요합니다."
            return _format_tool_value(edgar.company(identifier))

        if action_key == "submissions":
            if not identifier:
                return "identifier가 필요합니다."
            return _format_tool_value(edgar.submissionsJson(identifier))

        if action_key == "filings":
            if not identifier:
                return "identifier가 필요합니다."
            return _format_tool_value(
                edgar.filings(
                    identifier,
                    forms=_csv_list(forms),
                    since=since or None,
                    until=until or None,
                )
            )

        if action_key == "company_facts":
            if not identifier:
                return "identifier가 필요합니다."
            return _format_tool_value(edgar.companyFactsJson(identifier))

        if action_key == "company_concept":
            if not identifier or not taxonomy or not tag:
                return "identifier, taxonomy, tag가 필요합니다."
            return _format_tool_value(edgar.companyConceptJson(identifier, taxonomy, tag))

        if action_key == "frame":
            if not taxonomy or not tag or not unit or not period:
                return "taxonomy, tag, unit, period가 필요합니다."
            return _format_tool_value(edgar.frameJson(taxonomy, tag, unit, period))

        return (
            "지원하지 않는 action입니다. search, company, submissions, filings, company_facts, company_concept, frame"
        )

    register_tool(
        "call_edgar_openapi",
        call_edgar_openapi,
        "EDGAR OpenAPI를 직접 호출합니다. "
        "action 예시: search, company, submissions, filings, company_facts, company_concept, frame.",
        {
            "type": "object",
            "properties": {
                "action": {"type": "string", "description": "호출할 EDGAR action"},
                "identifier": {"type": "string", "description": "ticker 또는 CIK"},
                "query": {"type": "string", "description": "search용 검색어"},
                "forms": {"type": "string", "description": "쉼표 구분 form 목록 예: 10-K,10-Q"},
                "since": {"type": "string", "description": "시작일"},
                "until": {"type": "string", "description": "종료일"},
                "taxonomy": {"type": "string", "description": "taxonomy 예: us-gaap"},
                "tag": {"type": "string", "description": "tag 예: RevenueFromContractWithCustomerExcludingAssessedTax"},
                "unit": {"type": "string", "description": "frame unit 예: USD"},
                "period": {"type": "string", "description": "frame period 예: CY2024Q4I"},
            },
            "required": ["action"],
        },
    )

    def openapi_save(
        market: str,
        identifier: str,
        dataset: str,
        start: str = "",
        end: str = "",
        quarter: int | None = None,
        since_year: int = 2009,
        full: bool = True,
        categories: str = "",
    ) -> str:
        from dartlab import OpenDart, OpenEdgar

        market_key = (market or "").strip().lower()
        dataset_key = (dataset or "").strip().lower()
        end_arg = _maybe_int(end)

        if market_key in {"dart", "kr"}:
            if not identifier:
                return "identifier가 필요합니다."
            company_api = OpenDart()(identifier)
            if dataset_key == "finance":
                return _format_tool_value(company_api.saveFinance(start or None, end=end_arg, q=quarter, full=full))
            if dataset_key == "report":
                return _format_tool_value(
                    company_api.saveReport(
                        start or None,
                        end=end_arg,
                        q=quarter,
                        categories=_csv_list(categories),
                    )
                )
            if dataset_key == "filings":
                return _format_tool_value(company_api.saveFilings(start or None, end or None))
            if dataset_key == "xbrl":
                return _format_tool_value(company_api.xbrl(start or None, q=quarter))
            return "DART dataset은 finance, report, filings, xbrl 중 하나여야 합니다."

        if market_key in {"edgar", "us"}:
            if not identifier:
                return "identifier가 필요합니다."
            company_api = OpenEdgar()(identifier)
            if dataset_key == "docs":
                return _format_tool_value(company_api.saveDocs(sinceYear=since_year))
            if dataset_key == "finance":
                return _format_tool_value(company_api.saveFinance())
            return "EDGAR dataset은 docs, finance 중 하나여야 합니다."

        return "market은 dart 또는 edgar여야 합니다."

    register_tool(
        "openapi_save",
        openapi_save,
        "DART/EDGAR OpenAPI saver를 실행해 로컬 parquet를 생성합니다. "
        "DART dataset: finance, report, filings, xbrl. EDGAR dataset: docs, finance.",
        {
            "type": "object",
            "properties": {
                "market": {"type": "string", "description": "dart 또는 edgar"},
                "identifier": {"type": "string", "description": "회사명/종목코드/ticker/CIK"},
                "dataset": {"type": "string", "description": "저장할 데이터 종류"},
                "start": {"type": "string", "description": "DART 시작 연도/일자"},
                "end": {"type": "string", "description": "DART 종료 연도/일자"},
                "quarter": {"type": "integer", "description": "DART 분기"},
                "since_year": {"type": "integer", "description": "EDGAR docs 시작 연도", "default": 2009},
                "full": {"type": "boolean", "description": "DART finance 전체 계정", "default": True},
                "categories": {"type": "string", "description": "DART report 카테고리 목록"},
            },
            "required": ["market", "identifier", "dataset"],
        },
    )

    if company is None:
        return get_default_tool_runtime()

    # 0. list_modules: 사용 가능한 모듈 목록 조회
    def list_modules() -> str:
        from dartlab.engines.ai.context import scan_available_modules

        modules = scan_available_modules(company)
        if not modules:
            return "사용 가능한 데이터 모듈이 없습니다."
        lines = ["| 모듈명 | 설명 | 유형 | 행수 |", "| --- | --- | --- | --- |"]
        for m in modules:
            lines.append(f"| `{m['name']}` | {m['label']} | {m.get('type', '-')} | {m.get('rows', '-')} |")
        return "\n".join(lines)

    register_tool(
        "list_modules",
        list_modules,
        "이 기업에서 조회 가능한 모든 데이터 모듈 목록을 반환합니다. 어떤 데이터가 있는지 모를 때 먼저 호출하세요.",
        {"type": "object", "properties": {}},
    )

    # 1. get_data: 파서 모듈 데이터 조회
    def get_data(module_name: str) -> str:
        data = getattr(company, module_name, None) if hasattr(company, module_name) else company.show(module_name)
        if data is None:
            # 유사한 모듈명 제안
            from dartlab.engines.ai.metadata import MODULE_META

            suggestions = [
                f"`{n}` ({m.label})"
                for n, m in MODULE_META.items()
                if module_name.lower() in n.lower() or module_name.lower() in m.label.lower()
            ]
            msg = f"'{module_name}' 데이터가 없습니다."
            if suggestions:
                msg += f" 유사한 모듈: {', '.join(suggestions[:5])}"
            msg += " `list_modules` 도구로 사용 가능한 모듈을 확인하세요."
            return msg
        if isinstance(data, pl.DataFrame):
            return _df_to_md(data)
        if isinstance(data, dict):
            return "\n".join(f"- {k}: {v}" for k, v in data.items())
        if isinstance(data, list):
            return "\n".join(f"- {item}" for item in data[:20])
        return str(data)[:2000]

    from dartlab.core.registry import buildModuleDescription

    register_tool(
        "get_data",
        get_data,
        "기업의 재무/공시 데이터를 조회합니다. "
        "주요 module_name: "
        f"{buildModuleDescription()}. "
        "모듈명을 모르면 먼저 `list_modules`를 호출하세요.",
        {
            "type": "object",
            "properties": {
                "module_name": {
                    "type": "string",
                    "description": "조회할 모듈명 (예: BS, IS, CF, dividend, audit, fsSummary)",
                },
            },
            "required": ["module_name"],
        },
    )

    # 1b. search_data: 키워드로 데이터 검색
    def search_data(keyword: str) -> str:
        """모든 모듈을 검색하여 키워드와 관련된 데이터를 찾습니다."""
        from dartlab.engines.ai.metadata import MODULE_META

        results = []
        keyword_lower = keyword.lower()

        for name, meta in MODULE_META.items():
            try:
                data = getattr(company, name, None)
                if data is None:
                    continue
                if isinstance(data, pl.DataFrame) and data.height > 0:
                    # 컬럼명에서 검색
                    matched_cols = [c for c in data.columns if keyword_lower in c.lower()]
                    # 계정명 컬럼에서 검색
                    if "계정명" in data.columns:
                        matched_rows = data.filter(pl.col("계정명").str.contains(f"(?i){keyword}"))
                        if matched_rows.height > 0:
                            results.append(f"### {meta.label} (`{name}`) — 계정명 매칭 {matched_rows.height}건")
                            results.append(_df_to_md(matched_rows, max_rows=10))
                    elif matched_cols:
                        results.append(f"### {meta.label} (`{name}`) — 컬럼 매칭: {', '.join(matched_cols)}")
                elif isinstance(data, dict):
                    matched_keys = [
                        k for k in data if keyword_lower in str(k).lower() or keyword_lower in str(data[k]).lower()
                    ]
                    if matched_keys:
                        results.append(f"### {meta.label} (`{name}`)")
                        for k in matched_keys[:5]:
                            results.append(f"- {k}: {data[k]}")
            except Exception:
                continue

        if not results:
            return f"'{keyword}'와 관련된 데이터를 찾지 못했습니다. 다른 키워드를 시도하거나 `list_modules`로 사용 가능한 데이터를 확인하세요."
        return "\n\n".join(results)

    register_tool(
        "search_data",
        search_data,
        "키워드로 모든 데이터 모듈을 검색합니다. "
        "특정 계정과목(예: '매출액', '부채'), 지표명, 또는 컬럼명으로 검색합니다. "
        "어떤 모듈에 데이터가 있는지 모를 때 유용합니다.",
        {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "검색할 키워드 (예: '매출', '부채비율', 'R&D', '이자비용')",
                },
            },
            "required": ["keyword"],
        },
    )

    # 2. compute_ratios: 재무비율 계산
    def compute_ratios() -> str:
        from dartlab.tools.table import ratio_table

        bs = getattr(company, "BS", None)
        is_ = getattr(company, "IS", None)
        if not isinstance(bs, pl.DataFrame) or not isinstance(is_, pl.DataFrame):
            return "BS 또는 IS 데이터가 없어 재무비율을 계산할 수 없습니다."
        result = ratio_table(bs, is_)
        return _df_to_md(result)

    register_tool(
        "compute_ratios",
        compute_ratios,
        "재무상태표(BS)와 손익계산서(IS)로 핵심 재무비율을 계산합니다. "
        "부채비율, 유동비율, 영업이익률, 순이익률, ROE, ROA를 연도별로 반환.",
        {"type": "object", "properties": {}},
    )

    # 3. detect_anomalies: 이상치 탐지
    def find_anomalies(module_name: str, threshold_pct: float = 50.0) -> str:
        from dartlab.engines.ai.aiParser import detect_anomalies

        data = getattr(company, module_name, None)
        if not isinstance(data, pl.DataFrame):
            return f"'{module_name}' DataFrame 데이터가 없습니다."
        anomalies = detect_anomalies(data, use_llm=False, threshold_pct=threshold_pct)
        if not anomalies:
            return f"'{module_name}'에서 이상치가 발견되지 않았습니다."
        lines = []
        for a in anomalies:
            lines.append(f"- [{a.severity}] {a.column} {a.year}: {a.description} (변동 {a.change_pct:+.1f}%)")
        return "\n".join(lines)

    register_tool(
        "detect_anomalies",
        find_anomalies,
        "재무 데이터에서 이상치(급격한 변동, 부호 반전)를 탐지합니다.",
        {
            "type": "object",
            "properties": {
                "module_name": {
                    "type": "string",
                    "description": "분석할 모듈명 (예: BS, IS, CF)",
                },
                "threshold_pct": {
                    "type": "number",
                    "description": "이상치 판정 기준 YoY 변동률 (기본 50%)",
                    "default": 50.0,
                },
            },
            "required": ["module_name"],
        },
    )

    # 4. compute_growth: 성장률 매트릭스
    def compute_growth(module_name: str) -> str:
        from dartlab.tools.table import growth_matrix, pivot_accounts

        data = getattr(company, module_name, None)
        if not isinstance(data, pl.DataFrame):
            return f"'{module_name}' DataFrame 데이터가 없습니다."

        pivoted = pivot_accounts(data)
        if "year" not in pivoted.columns:
            return "연도 데이터가 부족하여 성장률을 계산할 수 없습니다."

        result = growth_matrix(pivoted)
        return _df_to_md(result)

    register_tool(
        "compute_growth",
        compute_growth,
        "다기간 CAGR(복합연간성장률) 매트릭스를 계산합니다. 1Y, 2Y, 3Y, 5Y 성장률 반환.",
        {
            "type": "object",
            "properties": {
                "module_name": {
                    "type": "string",
                    "description": "분석할 모듈명 (예: IS, dividend)",
                },
            },
            "required": ["module_name"],
        },
    )

    # 5. yoy_analysis: YoY 변동 분석
    def yoy_analysis(module_name: str) -> str:
        from dartlab.tools.table import pivot_accounts, yoy_change

        data = getattr(company, module_name, None)
        if not isinstance(data, pl.DataFrame):
            return f"'{module_name}' DataFrame 데이터가 없습니다."

        # 계정명 구조면 피벗
        if "계정명" in data.columns:
            data = pivot_accounts(data)

        if "year" not in data.columns:
            return "year 컬럼이 없어 YoY 분석을 할 수 없습니다."

        result = yoy_change(data)
        return _df_to_md(result)

    register_tool(
        "yoy_analysis",
        yoy_analysis,
        "데이터의 전년 대비(YoY) 변동률을 계산합니다.",
        {
            "type": "object",
            "properties": {
                "module_name": {
                    "type": "string",
                    "description": "분석할 모듈명 (예: IS, BS, dividend)",
                },
            },
            "required": ["module_name"],
        },
    )

    # 6. get_summary_stats: 요약 통계
    def get_summary(module_name: str) -> str:
        from dartlab.tools.table import pivot_accounts, summary_stats

        data = getattr(company, module_name, None)
        if not isinstance(data, pl.DataFrame):
            return f"'{module_name}' DataFrame 데이터가 없습니다."

        if "계정명" in data.columns:
            data = pivot_accounts(data)

        result = summary_stats(data)
        return _df_to_md(result)

    register_tool(
        "get_summary",
        get_summary,
        "데이터의 요약 통계(평균, 최솟값, 최댓값, 표준편차, CAGR, 추세)를 계산합니다.",
        {
            "type": "object",
            "properties": {
                "module_name": {
                    "type": "string",
                    "description": "분석할 모듈명 (예: IS, BS, dividend)",
                },
            },
            "required": ["module_name"],
        },
    )

    # 7b. get_report_data: 정기보고서 데이터 조회
    def get_report_data(api_type: str) -> str:
        """reportEngine의 apiType별 정제 데이터를 조회합니다."""
        report = getattr(company, "report", None)
        if report is None:
            return "정기보고서 데이터가 없습니다."
        df = report.extract(api_type)
        if df is None:
            from dartlab.engines.dart.report.types import API_TYPE_LABELS

            available = ", ".join(f"`{k}` ({v})" for k, v in list(API_TYPE_LABELS.items())[:10])
            return f"'{api_type}' 데이터가 없습니다. 사용 가능한 타입 예시: {available}"
        return _df_to_md(df)

    register_tool(
        "get_report_data",
        get_report_data,
        "OpenDART 정기보고서 API 데이터를 조회합니다. "
        "api_type 예시: dividend(배당), employee(직원현황), executive(임원현황), "
        "majorHolder(최대주주), auditOpinion(감사의견), capitalChange(증자감자), "
        "corporateBond(회사채), stockTotal(주식총수), treasuryStock(자기주식), "
        "investedCompany(타법인출자), outsideDirector(사외이사), "
        "executivePayAllTotal(임원보수전체), topPay(5억이상 개인보수). "
        "docsParser와 다르게 정기보고서 API의 표준화된 수치를 제공합니다.",
        {
            "type": "object",
            "properties": {
                "api_type": {
                    "type": "string",
                    "description": "조회할 API 타입 (예: dividend, employee, majorHolder)",
                },
            },
            "required": ["api_type"],
        },
    )

    # 7. get_company_info: 기업 기본 정보
    def get_company_info() -> str:
        info_parts = [
            f"기업명: {company.corpName}",
            f"종목코드: {getattr(company, 'stockCode', getattr(company, 'ticker', ''))}",
        ]
        overview = company.show("companyOverview") if hasattr(company, "show") else None
        if isinstance(overview, dict):
            for key in ("ceo", "mainBusiness", "indutyName", "foundedDate"):
                if overview.get(key):
                    info_parts.append(f"{key}: {overview[key]}")
        return "\n".join(info_parts)

    register_tool(
        "get_company_info",
        get_company_info,
        "기업의 기본 정보(기업명, 종목코드, 대표자, 업종 등)를 조회합니다.",
        {"type": "object", "properties": {}},
    )

    # 8. get_system_spec: DartLab 시스템 스펙 조회
    def get_system_spec() -> str:
        return _build_system_spec_markdown()

    register_tool(
        "get_system_spec",
        get_system_spec,
        "DartLab 시스템의 전체 스펙(엔진 목록, 데이터 종류, 기능)을 조회합니다. "
        "사용자가 '어떤 데이터가 있어?', '무슨 분석이 가능해?' 같은 메타 질문을 할 때 사용하세요.",
        {"type": "object", "properties": {}},
    )

    # 9. get_engine_spec: 특정 엔진 상세 스펙 조회
    def get_engine_spec(engine: str) -> str:
        from dartlab.engines.ai.spec import getEngineSpec

        spec = getEngineSpec(engine)
        if spec is None:
            from dartlab.engines.ai.spec import buildSpec

            all_spec = buildSpec(depth="summary")
            available = ", ".join(all_spec.get("engines", {}).keys())
            return f"'{engine}' 엔진을 찾을 수 없습니다. 사용 가능한 엔진: {available}"
        return json.dumps(spec, ensure_ascii=False, indent=2, default=str)

    register_tool(
        "get_engine_spec",
        get_engine_spec,
        "특정 엔진의 상세 스펙을 조회합니다. "
        "엔진명 예시: insight(인사이트), sector(섹터분류), rank(규모순위), "
        "dart.finance(재무제표), dart.report(정기보고서). "
        "각 엔진이 제공하는 구체적 지표·영역·분류 기준을 확인할 수 있습니다.",
        {
            "type": "object",
            "properties": {
                "engine": {
                    "type": "string",
                    "description": "엔진명 (예: insight, sector, rank, dart.finance, dart.report)",
                },
            },
            "required": ["engine"],
        },
    )

    # 10. get_insight: 기업 인사이트 분석 실행
    def get_insight() -> str:
        stockCode = getattr(company, "stockCode", None)
        if not stockCode:
            return "종목코드가 없어 인사이트 분석을 실행할 수 없습니다."
        try:
            from dartlab.engines.insight import analyze

            result = analyze(stockCode, company=company)
            if result is None:
                return "재무 데이터 부족으로 인사이트 분석을 수행할 수 없습니다."
            grades = result.grades()
            lines = [f"프로파일: {result.profile}", ""]
            lines.append("| 영역 | 등급 | 요약 |")
            lines.append("| --- | --- | --- |")
            areaMap = {
                "performance": "실적",
                "profitability": "수익성",
                "health": "건전성",
                "cashflow": "현금흐름",
                "governance": "지배구조",
                "risk": "리스크",
                "opportunity": "기회",
            }
            for key, label in areaMap.items():
                ir = getattr(result, key, None)
                grade = grades.get(key, "N")
                summary = ir.summary if ir else "-"
                lines.append(f"| {label} | {grade} | {summary} |")
            if result.anomalies:
                lines.append("")
                for a in result.anomalies[:5]:
                    lines.append(f"- [{a.severity}] {a.text}")
            if result.summary:
                lines.append(f"\n{result.summary}")
            return "\n".join(lines)
        except ImportError:
            return "insight 엔진을 불러올 수 없습니다."

    register_tool(
        "get_insight",
        get_insight,
        "기업의 7영역 인사이트 분석을 실행합니다. "
        "실적, 수익성, 재무건전성, 현금흐름, 지배구조, 리스크, 기회를 A~F 등급으로 평가. "
        "이상치 탐지와 프로파일(premium/growth/stable/caution/distress) 분류를 포함합니다.",
        {"type": "object", "properties": {}},
    )

    # 11. get_sector_info: 기업 섹터 분류 조회
    def get_sector_info() -> str:
        try:
            from dartlab.engines.sector import classify, getParams

            corpName = getattr(company, "corpName", "")
            overview = company.show("companyOverview") if hasattr(company, "show") else None
            kindIndustry = None
            if isinstance(overview, dict):
                kindIndustry = overview.get("indutyName")
            detail = company.show("companyOverviewDetail") if hasattr(company, "show") else None
            mainProducts = None
            if isinstance(detail, dict):
                mainProducts = detail.get("mainBusiness")
            info = classify(corpName, kindIndustry=kindIndustry, mainProducts=mainProducts)
            params = getParams(info)
            lines = [
                f"대분류: {info.sector.value}",
                f"중분류: {info.industryGroup.value}",
                f"분류근거: {info.source} (신뢰도 {info.confidence:.0%})",
            ]
            if params:
                lines.append(f"섹터 기준 PER: {params.perMultiple}배")
                lines.append(f"섹터 기준 PBR: {params.pbrMultiple}배")
                lines.append(f"할인율: {params.discountRate}%")
                lines.append(f"성장률: {params.growthRate}%")
            return "\n".join(lines)
        except ImportError:
            return "sector 엔진을 불러올 수 없습니다."

    register_tool(
        "get_sector_info",
        get_sector_info,
        "기업의 WICS 섹터 분류와 섹터 파라미터(PER, PBR, 할인율)를 조회합니다.",
        {"type": "object", "properties": {}},
    )

    # 12. get_rank: 기업 시장 순위 조회
    def get_rank_info() -> str:
        stockCode = getattr(company, "stockCode", None)
        if not stockCode:
            return "종목코드가 없습니다."
        try:
            from dartlab.engines.rank import getRank

            rank = getRank(stockCode)
            if rank is None:
                return "순위 데이터가 없습니다. (rank snapshot 미생성)"
            lines = []
            if rank.revenueRank is not None:
                lines.append(f"매출 순위(전체): {rank.revenueRank}/{rank.revenueTotal}")
            if rank.assetRank is not None:
                lines.append(f"자산 순위(전체): {rank.assetRank}/{rank.assetTotal}")
            if rank.growthRank is not None:
                lines.append(f"성장률 순위(전체): {rank.growthRank}/{rank.growthTotal}")
            if rank.revenueRankInSector is not None:
                lines.append(f"매출 순위({rank.sector}): {rank.revenueRankInSector}/{rank.revenueSectorTotal}")
            if rank.sizeClass:
                lines.append(f"규모 분류: {rank.sizeClass}")
            return "\n".join(lines) if lines else "순위 데이터가 비어있습니다."
        except ImportError:
            return "rank 엔진을 불러올 수 없습니다."

    register_tool(
        "get_rank",
        get_rank_info,
        "기업의 전체 시장 및 섹터 내 규모 순위(매출, 자산, 성장률)를 조회합니다.",
        {"type": "object", "properties": {}},
    )

    # 13. export_to_excel: Excel 파일 내보내기
    def export_to_excel(modules: str = "") -> str:
        import tempfile

        from dartlab.export.excel import exportToExcel, listAvailableModules

        modList = [m.strip() for m in modules.split(",") if m.strip()] or None
        safeName = company.corpName.replace("/", "_").replace("\\", "_")
        outPath = Path(tempfile.gettempdir()) / f"{company.stockCode}_{safeName}.xlsx"

        exportToExcel(company, outputPath=outPath, modules=modList)
        available = listAvailableModules(company)
        modDesc = ", ".join(m["label"] for m in available) if not modList else ", ".join(modList)
        return f"Excel 파일 생성 완료: {outPath}\n포함 시트: {modDesc}"

    from pathlib import Path

    register_tool(
        "export_to_excel",
        export_to_excel,
        "기업 데이터를 Excel(.xlsx) 파일로 내보냅니다. "
        "modules: 쉼표 구분 시트 선택 (IS,BS,CF,ratios,dividend,audit,employee,executive 등 Company의 모든 property). "
        "비워두면 데이터가 있는 모든 모듈 자동 포함.",
        {
            "type": "object",
            "properties": {
                "modules": {
                    "type": "string",
                    "description": "포함할 시트 (쉼표 구분, 예: 'IS,BS,ratios,dividend'). 비워두면 전체.",
                    "default": "",
                },
            },
        },
    )

    # 14. create_template: 엑셀 템플릿 생성
    def create_template(name: str, sheets_json: str) -> str:
        """JSON 시트 정의로 Excel 내보내기 템플릿을 생성합니다."""
        from dartlab.export.store import TemplateStore
        from dartlab.export.template import ExcelTemplate, SheetSpec

        try:
            sheets_data = json.loads(sheets_json)
        except json.JSONDecodeError:
            return 'sheets_json 파싱 오류. JSON 배열 형태로 입력하세요. 예: [{"source":"IS","label":"손익"}]'
        sheets = [SheetSpec(**s) for s in sheets_data]
        tmpl = ExcelTemplate(name=name, sheets=sheets)
        store = TemplateStore()
        tid = store.save(tmpl)
        sheetNames = ", ".join(s.label for s in sheets)
        return f"템플릿 '{name}' 생성 완료 (ID: {tid})\n시트: {sheetNames}"

    register_tool(
        "create_template",
        create_template,
        "Excel 내보내기 템플릿을 생성합니다. "
        "시트 구성을 JSON으로 정의하면 저장되어 다음에도 재사용 가능합니다. "
        "프리셋: preset_full(전체), preset_summary(요약), preset_governance(지배구조).",
        {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "템플릿 이름 (예: '내 분석 양식')",
                },
                "sheets_json": {
                    "type": "string",
                    "description": '시트 목록 JSON. 예: [{"source":"IS","label":"손익계산서"},{"source":"BS"},{"source":"dividend"}]',
                },
            },
            "required": ["name", "sheets_json"],
        },
    )

    # 15. export_with_template: 템플릿 기반 엑셀 내보내기
    def export_with_template(template_id: str) -> str:
        """저장된 템플릿으로 Excel 파일을 생성합니다."""
        import tempfile

        from dartlab.export.excel import exportWithTemplate
        from dartlab.export.store import TemplateStore

        store = TemplateStore()
        tmpl = store.get(template_id)
        if tmpl is None:
            available = store.list()
            avail_str = ", ".join(f"{t.templateId}({t.name})" for t in available)
            return f"템플릿 '{template_id}'을 찾을 수 없습니다. 사용 가능: {avail_str}"

        safeName = company.corpName.replace("/", "_").replace("\\", "_")
        templateSafe = tmpl.name.replace("/", "_").replace("\\", "_")
        outPath = Path(tempfile.gettempdir()) / f"{company.stockCode}_{safeName}_{templateSafe}.xlsx"

        exportWithTemplate(company, tmpl, outPath)
        return f"Excel 파일 생성 완료: {outPath}\n템플릿: {tmpl.name} ({len(tmpl.sheets)}개 시트)"

    register_tool(
        "export_with_template",
        export_with_template,
        "저장된 템플릿으로 Excel 파일을 생성합니다. "
        "템플릿 ID 예시: preset_full(전체), preset_summary(요약), preset_governance(지배구조). "
        "사용자가 만든 커스텀 템플릿도 ID로 사용 가능합니다.",
        {
            "type": "object",
            "properties": {
                "template_id": {
                    "type": "string",
                    "description": "사용할 템플릿 ID (예: preset_full, preset_summary, t_1234567890)",
                },
            },
            "required": ["template_id"],
        },
    )

    # 16. list_templates: 저장된 템플릿 목록
    def list_templates() -> str:
        """저장된 Excel 내보내기 템플릿 목록을 조회합니다."""
        from dartlab.export.store import TemplateStore

        store = TemplateStore()
        templates = store.list()
        if not templates:
            return "저장된 템플릿이 없습니다."
        lines = ["| ID | 이름 | 시트 수 | 설명 |", "| --- | --- | --- | --- |"]
        for t in templates:
            lines.append(f"| `{t.templateId}` | {t.name} | {len(t.sheets)} | {t.description or '-'} |")
        return "\n".join(lines)

    register_tool(
        "list_templates",
        list_templates,
        "저장된 Excel 내보내기 템플릿 목록을 조회합니다. 프리셋과 사용자 커스텀 템플릿을 모두 포함합니다.",
        {"type": "object", "properties": {}},
    )

    # ── 17. sections: 전체 공시 지도 조회 ──
    def get_sections() -> str:
        sec = company.sections
        if sec is None:
            return "sections 데이터가 없습니다."
        topics = []
        seen = set()
        for row in sec.to_dicts():
            t = row.get("topic", "")
            if t not in seen:
                seen.add(t)
                src = row.get("source", "docs")
                ch = row.get("chapter", "")
                topics.append(f"| {ch} | `{t}` | {src} |")
        lines = ["| 장 | topic | source |", "| --- | --- | --- |"] + topics
        return "\n".join(lines)

    register_tool(
        "get_sections",
        get_sections,
        "기업의 전체 공시 지도(sections)를 조회합니다. "
        "어떤 topic이 어떤 장(chapter)에 있는지, source(docs/finance/report)가 무엇인지 확인. "
        "show(topic, block)으로 접근하기 전에 먼저 이 도구로 전체 구조를 파악하세요.",
        {"type": "object", "properties": {}},
    )

    # ── 18. show_block: sections 블록 데이터 조회 ──
    def show_block(topic: str, block: int | None = None) -> str:
        if block is None:
            result = company.show(topic)
        else:
            result = company.show(topic, block)
        if result is None:
            return f"'{topic}' block={block} 데이터가 없습니다."
        if isinstance(result, pl.DataFrame):
            return _df_to_md(result, max_rows=30)
        return str(result)[:3000]

    register_tool(
        "show_block",
        show_block,
        "sections의 특정 topic/block 데이터를 조회합니다. "
        "block=null이면 블록 목차(block, type, source, preview)를 반환. "
        "block=N이면 해당 블록의 실제 데이터(text 또는 수평화 table)를 반환. "
        "get_sections로 topic 목록을 확인한 뒤 사용하세요.",
        {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "topic명 (예: companyOverview, dividend, BS)",
                },
                "block": {
                    "type": "integer",
                    "description": "blockOrder (null이면 블록 목차, 숫자면 해당 블록 데이터)",
                },
            },
            "required": ["topic"],
        },
    )

    # ── 19. search_company: 종목 검색 ──
    def search_company(keyword: str) -> str:
        from dartlab.core.kindList import searchName

        results = searchName(keyword)
        if results is None or (isinstance(results, pl.DataFrame) and results.is_empty()):
            return f"'{keyword}' 검색 결과가 없습니다."
        if isinstance(results, pl.DataFrame):
            return _df_to_md(results, max_rows=20)
        return str(results)[:2000]

    register_tool(
        "search_company",
        search_company,
        "종목명/종목코드로 기업을 검색합니다. 종목코드를 모를 때 사용하세요.",
        {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "검색 키워드 (예: '삼성', '현대차', '반도체')",
                },
            },
            "required": ["keyword"],
        },
    )

    # ── 20. download_data: 데이터 다운로드 ──
    def download_data(stock_code: str = "", category: str = "docs") -> str:
        from dartlab.core.dataLoader import downloadAll, loadData

        if category == "edgarDocs" and not stock_code:
            return (
                "EDGAR docs는 ticker를 지정한 개별 수집 경로를 사용하세요. 예: stock_code='AAPL', category='edgarDocs'"
            )
        if stock_code:
            loadData(stock_code, category=category)
            return f"{stock_code} {category} 데이터 다운로드 완료."
        downloadAll(category)
        return f"{category} 전체 데이터 다운로드 완료."

    register_tool(
        "download_data",
        download_data,
        "데이터를 다운로드합니다. "
        "stock_code를 지정하면 해당 종목만, 비워두면 카테고리 전체를 다운로드합니다. "
        "category: docs(공시문서), finance(재무), report(정기보고서), edgarDocs(미국 공시문서, ticker 필요).",
        {
            "type": "object",
            "properties": {
                "stock_code": {
                    "type": "string",
                    "description": "종목코드 또는 ticker (비워두면 전체)",
                    "default": "",
                },
                "category": {
                    "type": "string",
                    "description": "카테고리 (docs, finance, report, edgarDocs)",
                    "default": "docs",
                },
            },
        },
    )

    # ── 21. data_status: 데이터 현황 조회 ──
    def data_status() -> str:
        from dartlab.core.dataLoader import DATA_RELEASES, _dataDir

        lines = ["| 카테고리 | 라벨 | 파일 수 |", "| --- | --- | --- |"]
        for cat, conf in DATA_RELEASES.items():
            dataDir = _dataDir(cat)
            count = len(list(dataDir.glob("*.parquet"))) if dataDir.exists() else 0
            lines.append(f"| {cat} | {conf['label']} | {count} |")
        return "\n".join(lines)

    register_tool(
        "data_status",
        data_status,
        "로컬에 저장된 데이터 현황(카테고리별 파일 수)을 조회합니다. "
        "'데이터 몇 개 있어?', '어떤 데이터가 있지?' 같은 질문에 사용하세요.",
        {"type": "object", "properties": {}},
    )

    return get_default_tool_runtime()
