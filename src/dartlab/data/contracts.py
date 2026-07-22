"""Unified Data Workbench의 immutable public contract와 typed projection."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal, Mapping

if TYPE_CHECKING:
    import polars as pl
    import pyarrow as pa


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
class DataRequest:
    """한 query 안에서 asset 하나와 원하는 view를 결박한다."""

    assetId: str
    requestId: str | None = None
    projection: Projection | None = None
    subjects: tuple[str, ...] = ()
    measures: tuple[str, ...] = ()
    time: TimeContext | None = None
    params: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.assetId:
            raise ValueError("assetId가 비었습니다")
        if self.requestId == "":
            raise ValueError("requestId는 비어 있을 수 없습니다")


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
    requests: tuple[DataRequest, ...] = ()
    budget: QueryBudget = field(default_factory=QueryBudget)
    completeness: Literal["allowPartial", "requireComplete"] = "allowPartial"
    lineage: Literal["summary", "full"] = "summary"

    def __post_init__(self) -> None:
        if len(self.subjects) > self.budget.maxSubjects:
            raise ValueError("subjects가 query budget을 초과했습니다")
        querySubjects = set(self.subjects) | {subject for request in self.requests for subject in request.subjects}
        if len(querySubjects) > self.budget.maxSubjects:
            raise ValueError("request subjects가 query budget을 초과했습니다")
        if len(self.requests) > self.budget.maxAssets:
            raise ValueError("requests가 query budget을 초과했습니다")
        explicitIds = [request.requestId for request in self.requests if request.requestId is not None]
        if len(explicitIds) != len(set(explicitIds)):
            raise ValueError("requestId는 query 안에서 고유해야 합니다")
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
    selectorKind: Literal["none", "subject", "measure"] = "none"
    selectorRequired: bool = False
    concurrencyGroup: str | None = None
    metadata: tuple[tuple[str, Any], ...] = ()


@dataclass(frozen=True, slots=True)
class DataGap:
    """결손과 차단을 0이나 빈 성공으로 바꾸지 않는 machine-readable gap."""

    code: str
    message: str
    assetId: str | None = None
    subject: str | None = None
    systemic: bool = False
    requestId: str | None = None


@dataclass(frozen=True, slots=True)
class Coverage:
    """요청 asset과 partition의 처리 성적표."""

    requestedAssets: int
    resolvedAssets: int
    succeededPartitions: int
    failedPartitions: int


@dataclass(frozen=True, slots=True)
class DataLineage:
    """OpenLineage의 run, job, dataset 관계를 따르는 경량 계보 facet."""

    runId: str
    jobName: str
    datasetId: str
    datasetVersionId: str
    sourceRefs: tuple[str, ...]
    evidenceRefs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class QualityAssertion:
    """Data partition에 결박된 검증 가능한 품질 판정."""

    assertionId: str
    success: bool | None
    severity: Literal["info", "warning", "error"]
    expected: str
    observed: str
    assetId: str


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
    requestId: str | None = None
    lineage: DataLineage | None = None
    qualityAssertions: tuple[QualityAssertion, ...] = ()

    def toPolars(self) -> pl.DataFrame:
        """Partition data를 외부 분석에 바로 쓰는 Polars DataFrame으로 변환한다.

        Capabilities:
            native DataFrame은 복사 없이 반환하고 record와 mapping은 표로 정규화한다.

        Args:
            없음.

        Returns:
            Polars DataFrame.

        Raises:
            TypeError: Arrow-compatible table로 표현할 수 없는 값일 때.

        Example:
            ``result.partitions[0].toPolars()``.

        Guide:
            factor와 narrative projection은 이미 canonical table이므로 그대로 반환된다.

        SeeAlso:
            ``toArrow``.

        AIContext:
            이 변환은 의미 projection이 아니라 외부 transport adapter다.
        """
        import polars as pl

        if isinstance(self.data, pl.DataFrame):
            return self.data
        if isinstance(self.data, Mapping):
            return pl.DataFrame([dict(self.data)], strict=False)
        if isinstance(self.data, (list, tuple)):
            if not self.data:
                return pl.DataFrame()
            if all(isinstance(item, Mapping) for item in self.data):
                return pl.DataFrame([dict(item) for item in self.data], strict=False)
        raise TypeError(f"{self.projectionKind} partition을 표로 변환할 수 없습니다")

    def toArrow(self) -> pa.Table:
        """Partition을 Arrow Table로 변환한다.

        Capabilities:
            Arrow IPC와 Flight가 소비할 수 있는 columnar transport를 제공한다.

        Args:
            없음.

        Returns:
            PyArrow Table.

        Raises:
            TypeError: partition이 표 형태가 아닐 때.

        Example:
            ``result.partitions[0].toArrow()``.

        Guide:
            zero-copy 가능 여부는 Polars column dtype에 따른다.

        SeeAlso:
            ``toPolars``.

        AIContext:
            Arrow는 transport이며 lineage와 quality 의미를 대체하지 않는다.
        """
        return self.toPolars().to_arrow()


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
    qualityAssertions: tuple[QualityAssertion, ...] = ()

    def byRequest(self, requestId: str) -> tuple[DataPartition, ...]:
        """혼합 query 결과에서 request ID에 해당하는 partition만 반환한다."""

        return tuple(partition for partition in self.partitions if partition.requestId == requestId)

    def toArrow(self) -> dict[str, pa.Table]:
        """표 형태 partition을 request-aware Arrow table mapping으로 변환한다.

        Capabilities:
            외부 프로세스가 혼합 query를 한 번 받은 뒤 view별 Arrow table로 바로 사용하게 한다.

        Args:
            없음.

        Returns:
            request ID와 selector가 결합된 stable key의 Arrow table mapping.

        Raises:
            없음. 표 형태가 아닌 partition은 mapping에서 제외한다.

        Example:
            ``tables = result.toArrow()``.

        Guide:
            graph와 resource locator는 native mapping으로 쓰고 표 projection만 Arrow로 변환한다.

        SeeAlso:
            ``DataPartition.toArrow``와 ``byRequest``.

        AIContext:
            mapping key는 한 result 안에서만 partition을 식별하며 asset identity를 대체하지 않는다.
        """
        tables = {}
        for index, partition in enumerate(self.partitions):
            if partition.projectionKind in {"graph", "resource"}:
                continue
            try:
                table = partition.toArrow()
            except TypeError:
                continue
            requestKey = partition.requestId or partition.asset.assetId
            selectorKey = ",".join(f"{key}={value}" for key, value in partition.selector)
            key = f"{requestKey}:{selectorKey}" if selectorKey else requestKey
            if key in tables:
                key = f"{key}:{index}"
            tables[key] = table
        return tables


def projectionKind(projection: Projection) -> str:
    """Projection instance의 stable discriminator를 반환한다."""

    return projection.kind
