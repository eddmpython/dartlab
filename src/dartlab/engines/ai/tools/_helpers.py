"""registry.py의 private 헬퍼 함수들 — defaults/system.py 등에서 참조.

registry.py가 직접 가지고 있던 빌더/정책 함수를 여기로 분리하여
defaults/ 서브모듈에서도 import 가능하게 만든다.
"""

from __future__ import annotations

import os
from typing import Any

from dartlab.core.capabilities import (
    CapabilityChannel,
    build_capability_summary,
    get_capability_specs,
)

from .runtime import get_default_tool_runtime

_TRUTHY_ENV = {"1", "true", "yes", "on"}
_FALSY_ENV = {"0", "false", "no", "off"}
_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


def get_coding_runtime_policy() -> tuple[bool, str]:
    """코딩 런타임 도구 노출 정책을 계산한다."""
    raw = os.environ.get("DARTLAB_ENABLE_CODING_RUNTIME")
    if raw is not None:
        normalized = raw.strip().lower()
        if normalized in _TRUTHY_ENV:
            return True, "환경변수 `DARTLAB_ENABLE_CODING_RUNTIME=1`로 강제 활성화"
        if normalized in _FALSY_ENV:
            return False, "환경변수 `DARTLAB_ENABLE_CODING_RUNTIME=0`로 비활성화"

    host = os.environ.get("DARTLAB_HOST", "127.0.0.1").strip().lower()
    if host in _LOOPBACK_HOSTS:
        return True, f"로컬 host `{host}`에서 실행 중이어서 활성화"
    return (
        False,
        f"비로컬 host `{host}`에서는 기본 비활성화. 필요하면 `DARTLAB_ENABLE_CODING_RUNTIME=1`로 명시적 활성화",
    )


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


def build_system_spec_markdown() -> str:
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
    capability_summary = spec.get("capabilities", {}).get("summary", {})
    if capability_summary:
        lines.append("")
        lines.append("## Capability Surface")
        lines.append(f"- total: {capability_summary.get('total', 0)}")
        by_kind = capability_summary.get("byKind", {})
        if by_kind:
            lines.append("- by kind: " + ", ".join(f"`{k}` {v}개" for k, v in sorted(by_kind.items())))
    return "\n".join(lines)


def build_tool_catalog_markdown(include_parameters: bool = False) -> str:
    """현재 등록된 tool schema를 마크다운으로 노출."""
    schemas_by_name = {
        schema.get("function", {}).get("name", ""): schema for schema in get_default_tool_runtime().get_tool_schemas()
    }
    specs = sorted(get_capability_specs(channel=CapabilityChannel.CHAT), key=lambda spec: spec.id)
    lines = [f"# 등록된 대화 도구 ({len(specs)}개)"]
    for spec in specs:
        schema = schemas_by_name.get(spec.id, {})
        fn = schema.get("function", {})
        lines.append(f"## `{spec.id}`")
        lines.append(f"- {spec.description}")
        lines.append(
            f"- kind: `{spec.kind}` / result: `{spec.result_kind}` / channels: {', '.join(f'`{c}`' for c in spec.channels)}"
        )
        if include_parameters:
            params = fn.get("parameters", {}).get("properties", {})
            required = set(fn.get("parameters", {}).get("required", []))
            for key, info in params.items():
                info_type = info.get("type", "any")
                requirement = "required" if key in required else "optional"
                description = info.get("description", "")
                lines.append(f"- `{key}` ({info_type}, {requirement}): {description}")
    return "\n".join(lines)


def build_coding_runtime_markdown() -> str:
    """Summarize currently registered coding backends."""
    from .coding import get_default_coding_runtime

    runtime = get_default_coding_runtime()
    enabled, reason = get_coding_runtime_policy()
    lines = [f"# Coding Runtime ({runtime.name})", f"- enabled: {enabled}", f"- policy: {reason}"]
    for backend in runtime.inspect_backends():
        lines.append(f"## `{backend['name']}`")
        lines.append(f"- label: {backend.get('label', backend['name'])}")
        lines.append(f"- available: {backend.get('available')}")
        if backend.get("version"):
            lines.append(f"- version: {backend['version']}")
        if backend.get("configuredModel"):
            lines.append(f"- configuredModel: {backend['configuredModel']}")
        sandbox_modes = backend.get("sandboxModes") or []
        if sandbox_modes:
            lines.append(f"- sandboxModes: {', '.join(f'`{mode}`' for mode in sandbox_modes)}")
        lines.append(f"- description: {backend.get('description', '')}")
    return "\n".join(lines)


def build_runtime_capabilities_markdown(company: Any | None = None) -> str:
    """UI 대화에서 설명해야 하는 실제 기능 범위를 registry/tool 기준으로 요약."""
    from dartlab.core.registry import getCategories, getEntries
    from dartlab.engines.ai.providers.support.codex_cli import inspect_codex_cli
    from dartlab.engines.company.dart.openapi.dartKey import getDartKeyStatus

    from .coding import get_default_coding_runtime

    local_counts = {
        "docs": _count_local_parquets("docs"),
        "finance": _count_local_parquets("finance"),
        "edgarDocs": _count_local_parquets("edgarDocs"),
        "edgar": _count_local_parquets("edgar"),
    }
    registry_counts = {category: len(getEntries(category=category)) for category in getCategories()}
    capability_specs = get_capability_specs()
    capability_summary = build_capability_summary(capability_specs)
    tool_names = [
        schema.get("function", {}).get("name", "") for schema in get_default_tool_runtime().get_tool_schemas()
    ]
    codex_info = inspect_codex_cli()
    open_dart = getDartKeyStatus()
    coding_runtime = get_default_coding_runtime()
    coding_backends = coding_runtime.inspect_backends()
    coding_backend_labels = ", ".join(f"`{item['name']}`" for item in coding_backends) or "(없음)"
    codex_commands = ", ".join(f"`{name}`" for name in codex_info.get("commands", [])[:8]) or "(미확인)"
    sandbox_modes = ", ".join(f"`{mode}`" for mode in codex_info.get("sandboxModes", [])) or "(미확인)"
    coding_runtime_enabled, coding_runtime_reason = get_coding_runtime_policy()

    lines = [
        "# DartLab 런타임 기능 범위",
        "",
        "## 자동 인식된 대화 도구",
        f"- 현재 등록된 도구: {len(tool_names)}개",
        f"- 도구 목록: {', '.join(f'`{name}`' for name in tool_names)}",
        "- 새 도구가 등록되면 이 목록과 에이전트 사용 surface에 자동 반영됨",
        f"- capability 수: {capability_summary.get('total', 0)}개",
        (
            "- capability kind: "
            + ", ".join(f"`{name}` {count}개" for name, count in sorted(capability_summary.get("byKind", {}).items()))
        ),
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
        "- OpenDART 최근 공시목록, 수주공시, 계약공시, 단일판매공급계약 목록을 질문 기반으로 검색",
        "- Excel 내보내기, 템플릿 생성/조회/재사용",
        "- 로컬 데이터 현황 확인, 데이터 다운로드 트리거",
        "- 로컬 안전 정책이 허용되면 coding runtime을 통해 실제 코드 작업, 수정, 리뷰 요청 전달",
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
        f"- DART key 상태: {'설정됨' if open_dart.configured else '미설정'} / source={open_dart.source} / keyCount={open_dart.keyCount}",
        "- EDGAR: issuer resolve/search, submissions, filings DataFrame, companyfacts/companyconcept/frames, docs/finance saver",
        "",
        "## GPT / Codex 연결 범위",
        "- OpenAI API, ChatGPT OAuth, Codex CLI, Ollama, Custom OpenAI-compatible backend를 채팅 백엔드로 연결 가능",
        "- 현재 UI에서는 코드 설명, 코드 초안, 리팩터링 제안 같은 텍스트 기반 코딩 보조는 가능",
        f"- 등록된 coding backend: {coding_backend_labels}",
        f"- coding runtime 노출 상태: {'활성화' if coding_runtime_enabled else '비활성화'}",
        f"- coding runtime 정책: {coding_runtime_reason}",
        f"- Codex CLI 상태: {'설치됨' if codex_info.get('installed') else '미설치'}"
        + (f" / {codex_info['version']}" if codex_info.get("version") else ""),
        f"- Codex CLI 명령 자동 인식: {codex_commands}",
        f"- Codex sandbox 자동 인식: {sandbox_modes}",
        "- `codex` provider는 코드/파일 수정 의도가 보이면 `workspace-write`를 우선 사용하고, 일반 질의는 `read-only`를 유지",
        "- Codex CLI help/config가 바뀌면 상태/설명 경로가 다시 검사되어 자동 반영됨",
        "",
        "## 로컬 데이터 현황",
        f"- DART docs: {local_counts['docs']}개",
        f"- DART finance: {local_counts['finance']}개",
        f"- EDGAR docs: {local_counts['edgarDocs']}개",
        f"- EDGAR finance: {local_counts['edgar']}개",
    ]

    if company is not None:
        from dartlab.engines.ai.context.builder import scan_available_modules

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

    if coding_runtime_enabled:
        lines.extend(
            [
                "",
                "- `run_coding_task` 도구가 coding runtime의 표준 진입점이며, 현재 기본 backend는 `codex`",
                "- `run_codex_task` 도구를 통해 다른 provider에서도 Codex CLI에 코드 작업을 위임할 수 있음",
            ]
        )
    else:
        lines.append("")
        lines.append("- 현재 세션에서는 `run_coding_task` / `run_codex_task`가 안전 정책 때문에 등록되지 않음")

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
