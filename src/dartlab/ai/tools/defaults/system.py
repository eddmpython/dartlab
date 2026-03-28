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
        """DartLab 시스템 전체 스펙을 조회한다."""
        return build_system_spec_markdown()

    register_tool(
        "get_system_spec",
        get_system_spec,
        "DartLab 시스템의 전체 스펙(엔진 목록, 데이터 종류, 기능)을 조회합니다. "
        "사용자가 '어떤 데이터가 있어?', '무슨 분석이 가능해?' 같은 메타 질문을 할 때 사용하세요.",
        {"type": "object", "properties": {}},
        kind=CapabilityKind.SYSTEM,
        category="meta",
        priority=70,
    )

    def get_engine_spec(engine: str) -> str:
        """특정 엔진의 상세 스펙을 조회한다."""
        import json

        from dartlab.ai.spec import buildSpec, getEngineSpec

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
        category="meta",
        priority=60,
    )

    def get_runtime_capabilities() -> str:
        """현재 런타임에서 가능한 기능 범위를 요약한다."""
        return build_runtime_capabilities_markdown(company)

    register_tool(
        "get_runtime_capabilities",
        get_runtime_capabilities,
        "DartLab UI 대화에서 실제로 가능한 기능 범위를 요약합니다. "
        "EDGAR에서 더 받을 수 있는 데이터, OpenAPI 범위, GPT/Codex 연결 시 가능한 코딩 범위를 물을 때 우선 사용하세요.",
        {"type": "object", "properties": {}},
        kind=CapabilityKind.SYSTEM,
        category="meta",
        priority=55,
    )

    def get_tool_catalog(include_parameters: bool = False) -> str:
        """등록된 도구 카탈로그를 조회한다."""
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
        category="meta",
        priority=65,
    )

    def get_coding_runtime_status() -> str:
        """코딩 백엔드 등록 및 가용 상태를 조회한다."""
        return build_coding_runtime_markdown()

    register_tool(
        "get_coding_runtime_status",
        get_coding_runtime_status,
        "현재 등록된 coding backend와 가용 상태를 조회합니다. 아직 provider와 분리된 코드 작업 런타임의 상태를 확인할 때 사용하세요.",
        {"type": "object", "properties": {}},
        kind=CapabilityKind.SYSTEM,
        category="meta",
        priority=30,
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
            """코딩 런타임으로 워크스페이스 코드 작업을 실행한다."""
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
            category="coding",
            priority=40,
        )

        def run_codex_task(
            prompt: str,
            sandbox: str = "workspace-write",
            model: str = "",
            timeout_seconds: int = 300,
        ) -> str:
            """Codex CLI로 코드 작업을 위임한다."""
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
            category="coding",
            priority=45,
        )

    # ── discover_features ──

    def discover_features(category: str = "all") -> str:
        """카테고리별 사용 가능한 기능을 안내한다."""
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
        category="meta",
        priority=60,
    )

    # ── global search / download / data_status ──

    def search_company(keyword: str) -> str:
        """종목명 또는 종목코드로 기업을 검색한다."""
        import polars as pl

        from dartlab.gather.listing import searchName

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
        category="global",
        priority=70,
    )

    def download_data(stock_code: str = "", category: str = "docs") -> str:
        """HuggingFace에서 데이터를 다운로드한다."""
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
        category="global",
        priority=30,
    )

    def checkDataReady(stockCode: str) -> str:
        """종목의 데이터 준비 상태를 확인한다."""
        from dartlab.ai.conversation.data_ready import formatDataReadyStatus

        return formatDataReadyStatus(stockCode, detailed=True)

    register_tool(
        "checkDataReady",
        checkDataReady,
        "종목의 데이터 준비 상태(docs/finance/report)를 확인합니다. 분석 전 데이터가 있는지 확인할 때 사용하세요.",
        {
            "type": "object",
            "properties": {
                "stockCode": {
                    "type": "string",
                    "description": "종목코드 (예: 005930)",
                },
            },
            "required": ["stockCode"],
        },
        category="global",
        priority=75,
    )

    def suggest_questions(stockCode: str = "") -> str:
        """현재 회사 또는 종목코드 기준 추천 질문을 생성한다."""
        targetCompany = company
        targetCode = stockCode.strip()

        if targetCompany is None:
            if not targetCode:
                return "현재 선택된 회사가 없습니다. stockCode를 넣어 다시 호출하세요."
            from dartlab import Company

            targetCompany = Company(targetCode)

        from dartlab.ai.conversation.suggestions import suggestQuestions

        questions = suggestQuestions(targetCompany)
        if not questions:
            return "추천 질문을 만들 수 있는 데이터가 부족합니다."

        corpName = getattr(targetCompany, "corpName", None) or targetCode or "선택 기업"
        lines = [f"## {corpName} 추천 질문", ""]
        for index, question in enumerate(questions, start=1):
            lines.append(f"{index}. {question}")
        return "\n".join(lines)

    register_tool(
        "suggest_questions",
        suggest_questions,
        "현재 기업의 데이터 상태에 맞는 추천 질문 5~8개를 생성합니다. "
        "사용자가 '무엇을 물어보면 돼?', '추천 질문 보여줘'라고 할 때 사용하세요. "
        "현재 company가 없으면 stockCode를 넣어 호출할 수 있습니다.",
        {
            "type": "object",
            "properties": {
                "stockCode": {
                    "type": "string",
                    "description": "현재 회사가 없을 때 사용할 종목코드",
                    "default": "",
                },
            },
        },
        kind=CapabilityKind.SYSTEM,
        category="meta",
        priority=58,
    )

    def estimateTime(operation: str, stockCode: str = "") -> str:
        """작업 예상 시간을 반환한다."""
        estimates = {
            "company_load": ("Company 객체 로드", "3~5초"),
            "full_analysis": ("전체 분석 (insights)", "10~20초"),
            "forecast": ("매출 예측", "5~10초"),
            "valuation": ("밸류에이션", "5~10초"),
            "simulation": ("시나리오 시뮬레이션", "5~10초"),
            "market_scan": ("시장 전체 스캔", "1~3분"),
            "download_docs": ("docs 다운로드 (전체)", "2~5분"),
            "download_finance": ("finance 다운로드 (전체)", "3~8분"),
            "download_single": ("단일 종목 다운로드", "5~15초"),
        }
        if operation in estimates:
            label, time = estimates[operation]
            msg = f"**{label}**: 약 {time}"
            if stockCode:
                msg += f" ({stockCode})"
            return msg
        available = ", ".join(estimates.keys())
        return f"알 수 없는 작업입니다. 지원 작업: {available}"

    register_tool(
        "estimateTime",
        estimateTime,
        "작업의 예상 소요 시간을 안내합니다. "
        "오래 걸리는 작업 전에 사용자에게 미리 안내할 때 사용하세요. "
        "operation: company_load, full_analysis, forecast, valuation, simulation, "
        "market_scan, download_docs, download_finance, download_single.",
        {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "작업 종류",
                },
                "stockCode": {
                    "type": "string",
                    "description": "종목코드 (선택)",
                    "default": "",
                },
            },
            "required": ["operation"],
        },
        category="global",
        priority=70,
    )

    def data_status() -> str:
        """로컬 데이터 현황을 카테고리별로 조회한다."""
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
        category="global",
        priority=25,
    )
