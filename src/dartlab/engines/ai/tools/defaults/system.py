"""시스템 메타 도구 — 스펙/카탈로그/런타임/코딩 조회."""

from __future__ import annotations

from typing import Any


def register_system_tools(register_tool, *, company: Any | None = None) -> None:
    """시스템 관련 도구를 등록한다."""
    from dartlab.core.capabilities import CapabilityChannel, CapabilityKind

    from .._helpers import (
        build_coding_runtime_markdown,
        build_runtime_capabilities_markdown,
        build_system_spec_markdown,
        build_tool_catalog_markdown,
        get_coding_runtime_policy,
    )
    from ..coding import get_default_coding_runtime

    def get_system_spec() -> str:
        return build_system_spec_markdown()

    register_tool(
        "get_system_spec",
        get_system_spec,
        "DartLab 시스템의 전체 스펙(엔진 목록, 데이터 종류, 기능)을 조회합니다. "
        "사용자가 '어떤 데이터가 있어?', '무슨 분석이 가능해?' 같은 메타 질문을 할 때 사용하세요.",
        {"type": "object", "properties": {}},
        kind=CapabilityKind.SYSTEM,
    )

    def get_engine_spec(engine: str) -> str:
        import json

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
        kind=CapabilityKind.SYSTEM,
    )

    def get_runtime_capabilities() -> str:
        return build_runtime_capabilities_markdown(company)

    register_tool(
        "get_runtime_capabilities",
        get_runtime_capabilities,
        "DartLab UI 대화에서 실제로 가능한 기능 범위를 요약합니다. "
        "EDGAR에서 더 받을 수 있는 데이터, OpenAPI 범위, GPT/Codex 연결 시 가능한 코딩 범위를 물을 때 우선 사용하세요.",
        {"type": "object", "properties": {}},
        kind=CapabilityKind.SYSTEM,
    )

    def get_tool_catalog(include_parameters: bool = False) -> str:
        return build_tool_catalog_markdown(include_parameters=include_parameters)

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
        kind=CapabilityKind.SYSTEM,
    )

    def get_coding_runtime_status() -> str:
        return build_coding_runtime_markdown()

    register_tool(
        "get_coding_runtime_status",
        get_coding_runtime_status,
        "현재 등록된 coding backend와 가용 상태를 조회합니다. 아직 provider와 분리된 코드 작업 런타임의 상태를 확인할 때 사용하세요.",
        {"type": "object", "properties": {}},
        kind=CapabilityKind.SYSTEM,
    )

    coding_runtime_enabled, _ = get_coding_runtime_policy()
    if coding_runtime_enabled:

        def run_coding_task(
            prompt: str,
            backend: str = "codex",
            sandbox: str = "workspace-write",
            model: str = "",
            timeout_seconds: int = 300,
        ) -> str:
            runtime = get_default_coding_runtime()
            try:
                result = runtime.run_task(
                    prompt,
                    backend=backend or None,
                    sandbox=sandbox,
                    model=model or None,
                    timeout_seconds=timeout_seconds,
                )
            except KeyError as e:
                return str(e)
            except (FileNotFoundError, PermissionError, RuntimeError) as e:
                return str(e)

            lines = [
                "## Coding 작업 결과",
                f"- backend: {result.backend}",
                f"- sandbox: {result.sandbox}",
                f"- model: {result.model}",
            ]
            if result.usage:
                lines.append(f"- tokens: {result.usage.get('total_tokens', '?')}")
            lines.extend(["", result.answer])
            return "\n".join(lines)

        register_tool(
            "run_coding_task",
            run_coding_task,
            "표준 coding runtime을 통해 워크스페이스 코드 작업을 실행합니다. "
            "backend를 바꾸면 미래에 Codex 외 다른 coding backend도 같은 인터페이스로 호출할 수 있습니다.",
            {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "coding backend에 전달할 코드 작업 지시문",
                    },
                    "backend": {
                        "type": "string",
                        "description": "사용할 coding backend 이름. 현재 기본값은 codex",
                        "default": "codex",
                    },
                    "sandbox": {
                        "type": "string",
                        "description": "read-only, workspace-write, danger-full-access 중 하나",
                        "default": "workspace-write",
                    },
                    "model": {
                        "type": "string",
                        "description": "backend에 전달할 모델명. 비우면 backend 기본값 사용",
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
            kind=CapabilityKind.CODING,
            channels=(CapabilityChannel.CHAT, CapabilityChannel.MCP),
            result_kind="coding_result",
        )

        def run_codex_task(
            prompt: str,
            sandbox: str = "workspace-write",
            model: str = "",
            timeout_seconds: int = 300,
        ) -> str:
            result = run_coding_task(
                prompt,
                backend="codex",
                sandbox=sandbox,
                model=model,
                timeout_seconds=timeout_seconds,
            )
            return result.replace("## Coding 작업 결과", "## Codex 작업 결과", 1)

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
            kind=CapabilityKind.CODING,
            channels=(CapabilityChannel.CHAT, CapabilityChannel.MCP),
            result_kind="coding_result",
        )

    # ── discover_features ──

    def discover_features(category: str = "all") -> str:
        from dartlab.core.registry import buildFeatureDescription

        return buildFeatureDescription(category)

    register_tool(
        "discover_features",
        discover_features,
        "카테고리별 사용 가능한 기능을 상세히 안내합니다. "
        "category: finance, report, disclosure, notes, analysis, raw, all. "
        "사용자가 '어떤 기능이 있어?', '주석 데이터 뭐가 있어?' 같은 질문에 사용하세요.",
        {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "카테고리 (finance, report, disclosure, notes, analysis, raw, all)",
                    "default": "all",
                },
            },
        },
    )

    # ── global search / download / data_status ──

    def search_company(keyword: str) -> str:
        import polars as pl

        from dartlab.core.kindList import searchName

        from .helpers import df_to_md

        results = searchName(keyword)
        if results is None or (isinstance(results, pl.DataFrame) and results.is_empty()):
            return f"'{keyword}' 검색 결과가 없습니다."
        if isinstance(results, pl.DataFrame):
            return df_to_md(results, max_rows=20)
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
