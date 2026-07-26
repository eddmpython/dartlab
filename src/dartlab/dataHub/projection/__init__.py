"""Owner 반환값을 typed projection 으로 투영하는 계층.

native, records, factor, narrative, graph, resource 는 모두 여기서 갈린다.
계산은 owner 가 하고 이 계층은 표현과 예산, 증거 결박만 담당한다.
"""

from __future__ import annotations

from dartlab.dataHub.projection.evidence import (
    lineageFacet,
    narrativeFrame,
    qualityAssertions,
)
from dartlab.dataHub.projection.factorKernel import (
    classifyShape,
    emitGap,
    emptyCanonical,
    foldToCanonical,
    laneOf,
    reflectAxes,
    universeScopeOf,
)
from dartlab.dataHub.projection.output import projectOutput

__all__ = [
    "classifyShape",
    "emitGap",
    "emptyCanonical",
    "foldToCanonical",
    "laneOf",
    "lineageFacet",
    "narrativeFrame",
    "projectOutput",
    "qualityAssertions",
    "reflectAxes",
    "universeScopeOf",
]
