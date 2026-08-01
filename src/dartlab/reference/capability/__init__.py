"""capability — dartlab 능력 기준 SSOT (the WHAT).

dartlab 의 독스트링·calc 함수·엔진 메서드를 한데 모은 자기 기술 카탈로그.
``skills`` 가 "AI 가 능력을 상황에 맞게 사용하는 절차서 (the HOW)" 라면,
``capability`` 는 그 절차서가 가리키는 능력 자체의 정의·검색·관계 그래프다.

Submodules
----------
- ``registry`` — ``CapabilityKind`` / ``CapabilitySpec`` / ``CapabilityRegistry``
  / ``build_capability_summary`` / ``ANALYSIS_CONTRACTS`` (런타임 등록 SSOT).
- ``search``   — ``searchCapabilities`` / ``formatSearchResults`` (자연어 검색).
- ``analysisGraph`` — graph queries (``loadAnalysisGraph`` 결과 위에서 동작).
- ``builder`` — ``loadCapabilities()`` / ``loadAnalysisGraph()`` 라이브 빌더.
  docstring 소스에서 첫 조회 시 1 회 빌드(캐시) — 생성 사본 파일 없음, drift 표면 0.

카탈로그 SSOT = 엔진 docstring (operation.code §"CAPABILITIES 단일 진실의 원천").
공개 함수 ``dartlab.capabilities()`` (복수, root) 와는 이름이 분리돼 있어
충돌 없음 — 본 패키지는 단수 ``capability`` (서브패키지).
"""

from __future__ import annotations

from dartlab.reference.capability.builder import (
    buildCapabilities,
    loadAnalysisGraph,
    loadCapabilities,
)
from dartlab.reference.capability.execution import (
    CANONICAL_COMPANY_CAPABILITY_REFS,
    isEngineCallableRef,
)

try:
    from dartlab.core.di import setCapabilityCatalogProvider

    setCapabilityCatalogProvider(loadCapabilities)
except Exception:
    pass

__all__ = [
    "CANONICAL_COMPANY_CAPABILITY_REFS",
    "buildCapabilities",
    "isEngineCallableRef",
    "loadAnalysisGraph",
    "loadCapabilities",
]
