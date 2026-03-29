"""AI 엔진 총괄 스펙 수집기.

각 엔진 폴더의 spec.py에서 buildSpec()을 호출하여 합산.
LLM에게는 경로만 알려주고, 필요 시 이 모듈의 함수로 조회.
"""

from __future__ import annotations

from typing import Any

from dartlab.core.capabilities import build_capability_summary, get_capability_specs

_ENGINE_SPECS = [
    "dartlab.providers.dart.finance.spec",
    "dartlab.providers.dart.report.spec",
    "dartlab.scan.spec",
    "dartlab.core.sector.spec",
    "dartlab.analysis.financial.insight.spec",
    "dartlab.gather.fred.spec",
    "dartlab.analysis.financial.research.spec",
]


def _loadEngineSpec(modulePath: str) -> dict | None:
    """엔진 spec 모듈을 동적 임포트하여 buildSpec() 호출."""
    import importlib

    try:
        mod = importlib.import_module(modulePath)
        return mod.buildSpec()
    except (ImportError, AttributeError):
        return None


def buildSpec(depth: str = "summary") -> dict:
    """시스템 전체 스펙 반환.

    Args:
        depth: "summary" | "detail"
    """
    import dartlab

    if not get_capability_specs():
        from dartlab.ai.tools.registry import build_tool_runtime

        build_tool_runtime(object(), name="spec-capabilities")

    engines: dict[str, Any] = {}
    for path in _ENGINE_SPECS:
        spec = _loadEngineSpec(path)
        if spec is None:
            continue
        name = spec["name"]
        if depth == "summary":
            engines[name] = {
                "description": spec.get("description", ""),
                "summary": spec.get("summary", {}),
            }
        else:
            engines[name] = spec

    version = dartlab.__version__ if hasattr(dartlab, "__version__") else "unknown"
    capability_specs = get_capability_specs()
    capabilities: dict[str, Any] = {
        "summary": build_capability_summary(capability_specs),
    }
    if depth != "summary":
        capabilities["items"] = [spec.to_dict(detail=True) for spec in capability_specs]

    return {
        "system": {
            "name": "DartLab",
            "version": version,
            "description": "DART 전자공시 데이터 분석",
            "coverage": "한국 상장사 ~2,700개",
        },
        "engines": engines,
        "capabilities": capabilities,
    }


def getEngineSpec(engine: str, section: str | None = None) -> dict | None:
    """특정 엔진의 상세 스펙 반환.

    Args:
        engine: 엔진 이름 (예: "insight", "sector", "dart.finance")
        section: 특정 섹션만 반환 (예: "detail", "summary")
    """
    for path in _ENGINE_SPECS:
        spec = _loadEngineSpec(path)
        if spec and spec.get("name") == engine:
            if section and section in spec:
                return {section: spec[section]}
            return spec
    return None
