"""Capability discovery와 EngineCall 실행 권한 사이의 정본 경계."""

from __future__ import annotations

CANONICAL_COMPANY_CAPABILITY_REFS = frozenset(
    {
        "Company.panel",
        "Company.select",
        "Company.trace",
        "Company.filings",
        "Company.analysis",
        "Company.credit",
        "Company.gather",
        "Company.quant",
        "Company.macro",
        "Company.story",
        "Company.reportModel",
        "Company.industry",
        "Company.simulate",
    }
)

CANONICAL_DATA_HUB_CAPABILITY_REFS = frozenset({"dataHub", "dataHub.catalog", "dataHub.query"})
CANONICAL_AXIS_ENGINES = frozenset({"gather", "macro", "industry", "quant", "credit", "analysis"})
CANONICAL_TOP_LEVEL_CAPABILITY_REFS = frozenset(
    {
        "analysis",
        "capabilities",
        "codeToName",
        "compare",
        "credit",
        "data",
        "dataHub",
        "gather",
        "help",
        "industry",
        "listing",
        "macro",
        "nameToCode",
        "pastInsight",
        "quant",
        "scan",
        "search",
        "searchName",
        "sectorInsights",
        "simulate",
    }
)


def isEngineCallableRef(apiRef: str) -> bool:
    """Capability ref가 EngineCall 단일 실행 계약에 포함되는지 판정한다.

    Catalog 등재는 검색/문서 발견 계약이고 실행 권한이 아니다. Company는 formal
    facade 13개만, dataHub는 catalog/query만, axis 엔진은 등록 축만 허용한다.
    점 없는 top-level ref도 명시적인 read/analysis-safe allowlist만 허용한다.
    """
    ref = str(apiRef or "").strip()
    if not ref or ref.startswith("aiContract.") or ref.startswith("_") or "._" in ref:
        return False
    if ref.startswith("Company."):
        return ref in CANONICAL_COMPANY_CAPABILITY_REFS
    if ref in CANONICAL_DATA_HUB_CAPABILITY_REFS:
        return True
    if ref == "capabilities" or ref == "scan" or ref.startswith("scan."):
        return True
    head, separator, axis = ref.partition(".")
    if separator:
        return bool(axis) and head in CANONICAL_AXIS_ENGINES
    return ref in CANONICAL_TOP_LEVEL_CAPABILITY_REFS


def executionGuide(apiRef: str, *, engineCallable: bool | None = None) -> str:
    """Capability 소비자가 실행 가능성과 대체 경로를 혼동하지 않게 안내한다."""
    allowed = isEngineCallableRef(apiRef) if engineCallable is None else bool(engineCallable)
    if allowed:
        return f'EngineCall({{"apiRef": "{apiRef}", "args": {{...}}}})로 단일 호출할 수 있습니다.'
    return (
        "공개 참조 전용입니다. EngineCall apiRef로 사용하지 말고 관련 canonical engine/Company capability를 선택하세요."
    )


__all__ = [
    "CANONICAL_AXIS_ENGINES",
    "CANONICAL_COMPANY_CAPABILITY_REFS",
    "CANONICAL_DATA_HUB_CAPABILITY_REFS",
    "CANONICAL_TOP_LEVEL_CAPABILITY_REFS",
    "executionGuide",
    "isEngineCallableRef",
]
