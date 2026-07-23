"""DATA_RELEASES flat resource를 외부 Data Workbench 호출 계약으로 연결한다."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

import pyarrow as pa

import dartlab.config as dartlabConfig
from dartlab.core.dataConfig import DATA_RELEASES

from .contracts import ResourceManifest, ResourceReadReceipt, ResourceReadRequest
from .manifest import loadResourceManifest, validateManifestSources
from .reader import openResourceBatchReader


@dataclass(frozen=True, slots=True)
class ResourceDescription:
    """외부 process에 안전한 flat resource manifest 설명이다.

    Absolute execution root와 cache path는 계약에 포함하지 않는다. Tuple과 scalar만 보존해
    immutable하고 repr에 local path가 나타나지 않는다.
    """

    resourceId: str
    category: str
    sourcePin: str
    schemaFields: tuple[tuple[str, str], ...]
    commonSchemaFields: tuple[tuple[str, str], ...]
    shardCount: int
    totalBytes: int
    cacheHit: bool


@dataclass(frozen=True, slots=True)
class ResourcePage:
    """Arrow IPC stream과 pinned execution receipt를 담는 immutable page다.

    encodedBytes는 repr에서 제외하고 byte count만 표시한다. 실제 projection schema는
    actualSchemaFields로 보존한다.
    """

    resourceId: str
    category: str
    receipt: ResourceReadReceipt
    actualSchemaFields: tuple[tuple[str, str], ...]
    encodedBytes: bytes = field(repr=False)
    encodedByteCount: int = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "encodedByteCount", len(self.encodedBytes))


@dataclass(slots=True)
class ResourceReadSession:
    """한 source manifest를 description과 page read 한 번에 재사용한다.

    Manifest load가 전수 pre-validation을 담당하고 단일 ``read``가 반환 직전 전수
    post-validation을 수행한다. 사이에 source drift가 생기면 touched shard의 metadata gate
    또는 post-validation에서 page 반환 전에 실패한다. Absolute root를 가진 manifest는 repr에서
    제외한다.
    """

    description: ResourceDescription
    _manifest: ResourceManifest = field(repr=False, compare=False)
    _consumed: bool = field(default=False, init=False, repr=False, compare=False)

    def read(self, requestMapping: Mapping[str, object]) -> ResourcePage:
        """Pinned manifest로 page를 읽고 source 전수를 재검증한다.

        Args:
            requestMapping: ResourceReadRequest와 동형인 strict mapping.

        Returns:
            Arrow IPC payload와 pinned receipt를 가진 resource page.

        Raises:
            ValueError: session 재사용, source drift 또는 page 계약 위반일 때.
            TypeError: request mapping 타입이 유효하지 않을 때.

        Example:
            ``prepared.read({"columns": ["stock_code"]})``.
        """

        if self._consumed:
            raise ValueError("RESOURCE_READ_SESSION_CONSUMED: 새 page session이 필요합니다")
        self._consumed = True
        return _readResourcePageFromManifest(
            self.description.resourceId,
            self.description.category,
            requestMapping,
            self._manifest,
        )


def _resolveFlatRoot(resourceId: str, category: str) -> Path:
    if not isinstance(resourceId, str) or not isinstance(category, str):
        raise TypeError("resourceId와 category는 str이어야 합니다")
    if category not in DATA_RELEASES:
        raise ValueError(f"RESOURCE_CATEGORY_UNKNOWN: {category}")
    expectedResourceId = f"resource.{category}"
    if resourceId != expectedResourceId:
        raise ValueError(f"RESOURCE_CATEGORY_MISMATCH: expected {expectedResourceId}, got {resourceId}")
    specification = DATA_RELEASES[category]
    if specification.get("public") is not True or specification.get("deprecated") is True:
        raise ValueError(f"RESOURCE_ACCESS_DENIED: {category}")
    if specification.get("nested"):
        raise ValueError(f"RESOURCE_ROOT_NOT_FLAT: {category}")
    relativeDir = specification.get("dir")
    if not isinstance(relativeDir, str) or not relativeDir.strip():
        raise ValueError(f"RESOURCE_ROOT_INVALID: {category}")
    relativePath = Path(relativeDir)
    if relativePath.is_absolute():
        raise ValueError(f"RESOURCE_ROOT_ESCAPE: {category}")
    dataRoot = Path(dartlabConfig.dataDir).expanduser().resolve()
    resourceRoot = (dataRoot / relativePath).resolve()
    if resourceRoot == dataRoot or not resourceRoot.is_relative_to(dataRoot):
        raise ValueError(f"RESOURCE_ROOT_ESCAPE: {category}")
    if not resourceRoot.is_dir():
        raise ValueError(f"RESOURCE_ROOT_MISSING: {category}")
    if not any(resourceRoot.glob("*.parquet")):
        raise ValueError(f"RESOURCE_ROOT_EMPTY: {category}")
    return resourceRoot


def _loadFullManifest(
    resourceId: str,
    category: str,
    cachePath: str | Path | None,
    *,
    root: Path | None = None,
):
    resolvedRoot = root if root is not None else _resolveFlatRoot(resourceId, category)
    return loadResourceManifest(
        resourceId,
        resolvedRoot,
        integrityMode="full",
        cachePath=cachePath,
    )


def _descriptionFromManifest(category: str, manifest: ResourceManifest) -> ResourceDescription:
    return ResourceDescription(
        resourceId=manifest.resourceId,
        category=category,
        sourcePin=manifest.sourcePin,
        schemaFields=manifest.schemaFields,
        commonSchemaFields=manifest.commonSchemaFields,
        shardCount=len(manifest.shards),
        totalBytes=manifest.totalBytes,
        cacheHit=manifest.cacheHit,
    )


def prepareResourceRead(
    resourceId: str,
    category: str,
    cachePath: str | Path | None = None,
) -> ResourceReadSession:
    """Resource manifest를 한 번 load해 description과 page reader를 함께 준비한다.

    Capabilities:
        동일 작업의 description과 page read가 같은 full manifest를 재사용한다. 첫 load와 각
        page의 post-validation 사이 drift는 page 반환 전에 fail closed한다.

    Args:
        resourceId: DATA_RELEASES와 결박할 stable resource ID.
        category: DATA_RELEASES flat category.
        cachePath: 기존 persistent manifest cache JSON 경로.

    Returns:
        Description과 pinned manifest page reader를 가진 single-use session.

    AIContext:
        Data Workbench가 describe 후 read할 때 full directory scan을 중복하지 않는 owner seam이다.

    Guide:
        ``prepared = prepareResourceRead(...); description = prepared.description; page = prepared.read(mapping)``.

    When:
        한 public page를 계획하면서 schema 설명과 payload가 모두 필요할 때 사용한다.

    How:
        root를 한 번 해소하고 full manifest를 한 번 load한 뒤 immutable session에 보존한다.

    Requires:
        각 read는 반환 전 ``validateManifestSources``를 실행해야 한다.

    Raises:
        ValueError: resource binding, root 또는 manifest가 유효하지 않을 때.

    Example:
        ``prepareResourceRead("resource.finance", "finance").description``.

    SeeAlso:
        describeResource, readResourcePage.
    """

    root = _resolveFlatRoot(resourceId, category)
    manifest = _loadFullManifest(resourceId, category, cachePath, root=root)
    return ResourceReadSession(
        description=_descriptionFromManifest(category, manifest),
        _manifest=manifest,
    )


def describeResource(
    resourceId: str,
    category: str,
    cachePath: str | Path | None = None,
) -> ResourceDescription:
    """DATA_RELEASES flat category의 외부 안전 manifest 설명을 반환한다.

    Capabilities:
        category와 resource ID를 교차검증하고 full source pin, union schema, shard 수와
        persistent cache 상태를 absolute root 없이 반환한다.

    Args:
        resourceId: DATA_RELEASES와 결박할 stable resource ID.
        category: DATA_RELEASES flat category.
        cachePath: 기존 persistent manifest cache JSON 경로.

    Returns:
        Absolute path를 제외한 immutable resource description.

    AIContext:
        동적 Data Workbench가 read 전에 resource identity와 projection 가능 field를 발견한다.

    Guide:
        ``resource.{category}`` ID와 DATA_RELEASES category를 함께 전달한다.

    When:
        외부 process가 resource page query를 계획하거나 source revision을 확인할 때 호출한다.

    How:
        config.dataDir 아래 flat root를 검증하고 full manifest cache를 load한다.

    Requires:
        DATA_RELEASES에 등록된 non-nested category와 하나 이상의 flat parquet shard가 필요하다.

    Raises:
        TypeError: ID 또는 category 타입이 str이 아닐 때.
        ValueError: category, root, flatness 또는 ID binding이 유효하지 않을 때.

    Example:
        ``describeResource("resource.edgar", "edgar")``.

    SeeAlso:
        readResourcePage, ResourceDescription.
    """
    return prepareResourceRead(resourceId, category, cachePath).description


def _readResourcePageFromManifest(
    resourceId: str,
    category: str,
    requestMapping: Mapping[str, object],
    manifest: ResourceManifest,
) -> ResourcePage:
    if not isinstance(requestMapping, Mapping):
        raise TypeError("requestMapping은 Mapping이어야 합니다")
    request = ResourceReadRequest.fromMapping(requestMapping)
    sink = pa.BufferOutputStream()
    options = pa.ipc.IpcWriteOptions(compression=None)
    with openResourceBatchReader(
        manifest,
        request,
        sourcesPrevalidated=True,
        validateAfterRead=False,
    ) as reader:
        schema = reader.schema
        wroteBatch = False
        with pa.ipc.new_stream(sink, schema, options=options) as writer:
            for batch in reader:
                writer.write_batch(batch)
                wroteBatch = True
            if not wroteBatch:
                writer.write_batch(
                    pa.RecordBatch.from_arrays(
                        [pa.array([], type=field.type) for field in schema],
                        schema=schema,
                    )
                )
        receipt = reader.receipt()
    validateManifestSources(manifest)
    encodedBytes = sink.getvalue().to_pybytes()
    return ResourcePage(
        resourceId=resourceId,
        category=category,
        receipt=receipt,
        actualSchemaFields=tuple((field.name, str(field.type)) for field in schema),
        encodedBytes=encodedBytes,
    )


def readResourcePage(
    resourceId: str,
    category: str,
    requestMapping: Mapping[str, object],
    cachePath: str | Path | None = None,
) -> ResourcePage:
    """Flat provider resource page를 uncompressed Arrow IPC stream으로 반환한다.

    Capabilities:
        strict Mapping request를 bounded DuckDB RecordBatch page로 실행하고 단일 Arrow stream,
        actual schema와 pinned receipt를 immutable result로 반환한다.

    Args:
        resourceId: DATA_RELEASES와 결박할 stable resource ID.
        category: DATA_RELEASES flat category.
        requestMapping: ResourceReadRequest와 동형인 strict mapping.
        cachePath: 기존 persistent manifest cache JSON 경로.

    Returns:
        Arrow IPC payload와 pinned receipt를 가진 resource page.

    AIContext:
        외부 process와 simulator가 같은 provider-owned paging surface를 동적으로 호출한다.

    Guide:
        첫 page receipt의 nextRow, sourcePin, queryPin을 다음 requestMapping에 전달한다.

    When:
        전종목 또는 선택 shard projection을 process 경계 밖으로 전달할 때 호출한다.

    How:
        full manifest를 고정하고 RecordBatch를 순차 IPC writer에 써서 전체 table materialization을 피한다.

    Requires:
        requestMapping은 ResourceReadRequest.fromMapping 계약을 따라야 하며 contentRaw 제한을 지켜야 한다.

    Raises:
        TypeError: requestMapping 또는 내부 값의 타입이 유효하지 않을 때.
        ValueError: resource binding, pin, schema, budget 또는 raw content 정책 위반일 때.

    Example:
        ``readResourcePage("resource.finance", "finance", {"columns": ["stock_code"]})``.

    SeeAlso:
        describeResource, ResourceReadRequest, ResourcePage.
    """
    return prepareResourceRead(resourceId, category, cachePath).read(requestMapping)
