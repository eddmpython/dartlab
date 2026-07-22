"""Unified Data Workbench의 immutable public contract.

Resource, record, factor를 같은 표로 강제하지 않고 query projection을 tagged type으로
분리한다. 시간, coverage, gap, lineage는 반환 data와 같은 snapshot에 결박한다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Mapping


@dataclass(frozen=True, slots=True)
class TimeContext:
    """Data query의 valid time과 knowledge cutoff."""

    validAt: str | None = None
    knownAt: str | None = None


@dataclass(frozen=True, slots=True)
class QueryBudget:
    """한 query가 사용할 수 있는 결과와 실행 예산."""

    maxRows: int = 100_000
    maxBytes: int = 64 * 1024 * 1024
    timeoutMs: int = 30_000
    maxAssets: int = 32
    maxSubjects: int = 1_000
    maxConcurrency: int = 4

    def __post_init__(self) -> None:
        for name in ("maxRows", "maxBytes", "timeoutMs", "maxAssets", "maxSubjects", "maxConcurrency"):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name}은 양수여야 합니다")


@dataclass(frozen=True, slots=True)
class NativeProjection:
    """Owner native schema를 partition별로 보존한다."""

    kind: Literal["native"] = "native"


@dataclass(frozen=True, slots=True)
class RecordsProjection:
    """Scalar와 text leaf를 tagged knowledge record로 투영한다."""

    kind: Literal["records"] = "records"


@dataclass(frozen=True, slots=True)
class FactorProjection:
    """Scalar-compatible observation을 factor long schema로 투영한다."""

    measures: tuple[str, ...] = ()
    unit: str | None = None
    frequency: str | None = None
    kind: Literal["factor"] = "factor"


@dataclass(frozen=True, slots=True)
class GraphProjection:
    """Node와 directed edge 구조를 보존한다."""

    depth: int = 1
    scope: str = "data"
    kind: Literal["graph"] = "graph"


@dataclass(frozen=True, slots=True)
class NarrativeProjection:
    """문서와 narrative text를 evidence-bearing record로 투영한다."""

    kind: Literal["narrative"] = "narrative"


@dataclass(frozen=True, slots=True)
class ResourceProjection:
    """Payload 대신 revision-fixed resource locator를 반환한다."""

    includePayload: bool = False
    kind: Literal["resource"] = "resource"


Projection = (
    NativeProjection | RecordsProjection | FactorProjection | GraphProjection | NarrativeProjection | ResourceProjection
)


@dataclass(frozen=True, slots=True)
class CatalogQuery:
    """Metadata-only asset catalog filter."""

    layers: tuple[str, ...] = ()
    owners: tuple[str, ...] = ()
    kinds: tuple[str, ...] = ()
    search: str | None = None
    includeHidden: bool = True
    includeOutOfScope: bool = True


@dataclass(frozen=True, slots=True)
class DataQuery:
    """Asset materialization과 projection을 한 번에 고정하는 query."""

    subjects: tuple[str, ...] = ()
    measures: tuple[str, ...] = ()
    projection: Projection = field(default_factory=NativeProjection)
    time: TimeContext | None = None
    params: Mapping[str, Any] = field(default_factory=dict)
    budget: QueryBudget = field(default_factory=QueryBudget)
    completeness: Literal["allowPartial", "requireComplete"] = "allowPartial"
    lineage: Literal["summary", "full"] = "summary"

    def __post_init__(self) -> None:
        if len(self.subjects) > self.budget.maxSubjects:
            raise ValueError("subjects가 query budget을 초과했습니다")
        if self.completeness not in {"allowPartial", "requireComplete"}:
            raise ValueError("completeness가 유효하지 않습니다")


@dataclass(frozen=True, slots=True)
class AssetRef:
    """Stable logical asset와 현재 descriptor version의 결합."""

    assetId: str
    assetVersionId: str


@dataclass(frozen=True, slots=True)
class DataAssetDescriptor:
    """Owner가 선언하고 Workbench가 검증한 metadata-only asset."""

    assetId: str
    assetVersionId: str
    owner: str
    layer: str
    kind: str
    label: str
    description: str
    sourceRef: str
    queryable: bool
    hidden: bool = False
    visibility: str = "LOCAL"
    licenseRef: str | None = None
    temporalSupport: tuple[str, ...] = ("latest",)
    executorKind: str = "catalog"
    executorAxis: str | None = None
    executorModule: str | None = None
    executorAttribute: str | None = None
    subjectParam: str | None = None
    validTimeParam: str | None = None
    knowledgeTimeParam: str | None = None
    metadata: tuple[tuple[str, Any], ...] = ()


@dataclass(frozen=True, slots=True)
class DataGap:
    """결손과 차단을 0이나 빈 성공으로 바꾸지 않는 machine-readable gap."""

    code: str
    message: str
    assetId: str | None = None
    subject: str | None = None
    systemic: bool = False


@dataclass(frozen=True, slots=True)
class Coverage:
    """요청 asset과 partition의 처리 성적표."""

    requestedAssets: int
    resolvedAssets: int
    succeededPartitions: int
    failedPartitions: int


@dataclass(frozen=True, slots=True)
class DataPartition:
    """서로 다른 native schema를 무손실로 분리하는 result partition."""

    asset: AssetRef
    projectionKind: str
    data: Any
    schema: tuple[tuple[str, str], ...]
    rowCount: int
    truncated: bool
    selector: tuple[tuple[str, str], ...]
    temporalStatus: str
    lineageRefs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DataCatalogResult:
    """Catalog axis의 immutable result."""

    status: str
    assets: tuple[DataAssetDescriptor, ...]
    snapshotId: str
    coverage: Coverage
    gaps: tuple[DataGap, ...] = ()


@dataclass(frozen=True, slots=True)
class DataResult:
    """Query data와 provenance를 같은 snapshot에 결박한 result envelope."""

    status: str
    partitions: tuple[DataPartition, ...]
    assets: tuple[AssetRef, ...]
    snapshotId: str
    contractHash: str
    coverage: Coverage
    gaps: tuple[DataGap, ...]
    lineageRefs: tuple[str, ...]
    executionReceipts: tuple[str, ...]
    continuation: str | None = None


def projectionKind(projection: Projection) -> str:
    """Projection instance의 stable discriminator를 반환한다."""

    return projection.kind
