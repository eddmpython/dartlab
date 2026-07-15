"""Universe가 소비하는 source version을 한 재현 단위로 묶는다.

Capabilities
    map, search, panel, finance, capability catalog, recipe catalog의 실제
    version을 수집하고 source 순서와 관측 시각에 독립적인 snapshotSetId를 만든다.

Args
    CLI 인자는 필요하지 않다. 현재 공개 HF dataset과 로컬 catalog를 읽는다.

Returns
    :class:`SourceSnapshotSet`을 stdout JSON으로 출력한다.

Example
    ``uv run python -X utf8 tests/_attempts/dartlabUniverse/snapshot/sourceSnapshotSetProbe.py``

Guide
    moving ``main`` URL 자체는 version으로 인정하지 않는다. HF commit과 ETag를
    함께 보존하고 version을 얻지 못한 source는 ``unreplayable``로 기록한다.

SeeAlso
    ``mainPlan/dartlab-universe/12-innovation-validation-scorecard.md`` 5절.

Requires
    Python 표준 라이브러리와 현재 DartLab capability catalog builder를 사용한다.

AIContext
    AI 역할: exact replay의 입력 정체성을 fail-closed로 판정한다. projection이나
    public redistribution 승인을 대신하지 않는다.

LLM Specifications
    AntiPatterns: map buildId 하나를 전체 snapshot identity로 사용하지 않는다.
    OutputSchema: SourceSnapshotSet의 JSON 직렬화 형태다.
    Prerequisites: 공개 HF source와 로컬 catalog에 접근할 수 있어야 한다.
    Freshness: 실행 중 관측한 source version 기준이다.
    Dataflow: source heads와 catalog payload -> canonical versions -> snapshotSetId.
    TargetMarkets: 현재 KR source set, 이후 같은 계약의 market source set.

결과
    2026-07-15 live source 10개 중 HF 8개와 recipe catalog는 immutable commit,
    ETag 또는 Git blob으로 복원했다. capability catalog는 226개 canonical output
    hash만 있고 immutable manifest가 없어 unreplayable이다. panel의 dataAsOf
    1개와 redistribution receipt 10개는 비어 있다.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import urllib.request
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

HF_REPO = "eddmpython/dartlab-data"
HF_RESOLVE_BASE = f"https://huggingface.co/datasets/{HF_REPO}/resolve"
SCHEMA_VERSION = "sourceSnapshotSet.v1"
MAP_META_PATH = "landing/map/meta.json"
REMOTE_SOURCE_PATHS = (
    ("mapMeta", MAP_META_PATH, "buildTime"),
    ("mapAtlas", "landing/map/atlas.json", "buildTime"),
    ("mapEcosystem", "landing/map/ecosystem.json", "buildTime"),
    ("searchIndex", "landing/map/search-index.json", "buildTime"),
    ("mapTimeline", "landing/map/timeline.json", "buildTime"),
    ("mapMovers", "landing/map/movers.json", "buildTime"),
    ("dartPanelSample", "dart/panel/005930.parquet", "dart"),
    ("dartFinanceSample", "dart/finance/005930.parquet", "finance"),
)


def currentSourceIds() -> tuple[str, ...]:
    """현재 U0 SourceSnapshotSet이 요구하는 source ID를 반환한다.

    Capabilities
        network 없이 remote artifact와 local catalog source ID를 한 목록으로 만든다.

    Args
        없음.

    Returns
        sourceId로 정렬한 tuple.

    Example
        ``currentSourceIds()``

    Guide
        policy와 lens attempt가 source 이름을 별도로 복제하지 않게 한다.

    When
        U0-S01 source set과 후속 gate의 coverage를 맞출 때 호출한다.

    How
        REMOTE_SOURCE_PATHS의 ID에 capability와 recipe catalog ID를 더한다.

    Requires
        없음.

    See Also
        :func:`inspectLiveSourceSnapshotSet`.

    AIContext
        AI 역할: 후속 attempt의 source census drift를 막는다.

    Raises
        고정 상수만 사용하므로 예외를 발생시키지 않는다.
    """

    return tuple(sorted([sourceId for sourceId, _, _ in REMOTE_SOURCE_PATHS] + ["capabilityCatalog", "recipeCatalog"]))


@dataclass(frozen=True)
class SnapshotSource:
    """한 source의 재현 identity와 진단 metadata를 보존한다.

    Capabilities
        source path, version, optional payload hash, dataAsOf, policy receipt를
        content replay 상태와 함께 보존한다.

    Args
        sourceId는 snapshot 안에서 유일해야 하고 versionOrEtag가 없으면 build가
        replayStatus를 unreplayable로 정규화한다.

    Returns
        JSON 직렬화 가능한 immutable source record.

    Example
        ``SnapshotSource("map", "hfDataset", "map.json", "etag:abc")``

    Guide
        redistributionReceiptId 부재는 content version 부재와 다른 문제다.

    SeeAlso
        :func:`buildSourceSnapshotSet`.

    Requires
        없음.

    AIContext
        AI 역할: source version 결손과 policy 결손을 혼동하지 않는다.

    LLM Specifications
        AntiPatterns: signed redirect URL을 immutable path로 저장하지 않는다.
        OutputSchema: 선언된 dataclass 필드.
        Prerequisites: sourceId, origin, path.
        Freshness: source 관측 시점 기준.
        Dataflow: source probe -> SnapshotSource.
        TargetMarkets: market neutral.
    """

    sourceId: str
    origin: str
    path: str
    versionOrEtag: str | None
    payloadHash: str | None = None
    dataAsOf: str | None = None
    redistributionReceiptId: str | None = None
    replayStatus: str = "replayable"
    unreplayableReason: str | None = None
    contentLength: int | None = None

    def toDict(self) -> dict[str, Any]:
        """Source record를 JSON 직렬화 가능한 dict로 바꾼다.

            Args
                없음.

            Returns
                dataclass 선언 순서를 보존한 dict.

        Example
            ``source.toDict()``

        Requires
            없음.

        Raises
            직렬화 가능한 필드만 사용하므로 예외를 발생시키지 않는다.
        """

        return asdict(self)


@dataclass(frozen=True)
class SourceSnapshotSet:
    """여러 source version을 묶은 immutable replay identity다.

    Capabilities
        canonical snapshotSetId, content replay 상태, metadata 결손을 함께 노출한다.

    Args
        sources는 sourceId 순으로 정규화되고 createdAt은 hash에서 제외된다.

    Returns
        JSON 직렬화 가능한 snapshot record.

    Example
        ``snapshot.toDict()``

    Guide
        exactReplayReady는 content identity만 뜻하며 public 정책 승인이 아니다.

    SeeAlso
        :func:`buildSourceSnapshotSet`.

    Requires
        sourceId가 중복되지 않아야 한다.

    AIContext
        AI 역할: current rerun과 exact source replay 가능성을 구분한다.

    LLM Specifications
        AntiPatterns: createdAt 또는 query cutoff를 snapshotSetId에 넣지 않는다.
        OutputSchema: 선언된 dataclass 필드.
        Prerequisites: normalized SnapshotSource tuple.
        Freshness: source versions 기준.
        Dataflow: sources -> canonical payload -> SHA-256.
        TargetMarkets: market neutral.
    """

    schemaVersion: str
    snapshotSetId: str
    createdAt: str
    sources: tuple[SnapshotSource, ...]
    mapBuildId: str | None
    capabilityCatalogVersion: str | None
    recipeCatalogVersion: str | None
    exactReplayReady: bool
    unreplayableSourceIds: tuple[str, ...]
    missingDataAsOfSourceIds: tuple[str, ...]
    missingRedistributionReceiptSourceIds: tuple[str, ...]

    def toDict(self) -> dict[str, Any]:
        """Snapshot을 JSON 직렬화 가능한 dict로 바꾼다.

            Args
                없음.

            Returns
                source tuple을 list로 변환한 dict.

        Example
            ``json.dumps(snapshot.toDict())``

        Requires
            없음.

        Raises
            직렬화 가능한 필드만 사용하므로 예외를 발생시키지 않는다.
        """

        return asdict(self)


@dataclass(frozen=True)
class ReplayAssessment:
    """Share replay 요청이 exact replay를 주장할 수 있는지 설명한다.

    Capabilities
        snapshotSetId 일치, source replayability, legacy buildId fallback을 구분한다.

    Args
        exactReplayAllowed, mode, reason은 fail-closed 판정 결과다.

    Returns
        JSON 직렬화 가능한 immutable assessment.

    Example
        ``assessment.exactReplayAllowed``

    Guide
        legacy buildId는 compatibility hint일 뿐 exact source identity가 아니다.

    SeeAlso
        :func:`assessReplayRequest`.

    Requires
        없음.

    AIContext
        AI 역할: 현재 데이터 재실행을 역사적 exact replay로 표현하지 않는다.

    LLM Specifications
        AntiPatterns: buildId 일치만으로 exactReplayAllowed를 true로 만들지 않는다.
        OutputSchema: 선언된 dataclass 필드.
        Prerequisites: 없음.
        Freshness: available snapshot 기준.
        Dataflow: replay request -> assessment.
        TargetMarkets: market neutral.
    """

    exactReplayAllowed: bool
    mode: str
    reason: str


def _canonicalSource(source: SnapshotSource) -> dict[str, str | None]:
    return {
        "sourceId": source.sourceId,
        "origin": source.origin,
        "path": source.path,
        "versionOrEtag": source.versionOrEtag,
        "payloadHash": source.payloadHash,
        "replayStatus": source.replayStatus,
    }


def _canonicalHash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def buildSourceSnapshotSet(
    sources: Iterable[SnapshotSource],
    *,
    mapBuildId: str | None,
    capabilityCatalogVersion: str | None,
    recipeCatalogVersion: str | None,
    createdAt: str,
) -> SourceSnapshotSet:
    """Source를 정규화하고 canonical snapshotSetId를 계산한다.

    Capabilities
        순서 독립 정렬, 중복 차단, missing version의 unreplayable 승격,
        metadata 결손 목록 생성을 수행한다.

    Args
        sources: snapshot에 포함할 source record iterable.
        mapBuildId: legacy map compatibility build ID.
        capabilityCatalogVersion: 관측한 capability catalog version.
        recipeCatalogVersion: 관측한 recipe catalog version.
        createdAt: snapshot 관측 시각. canonical hash에는 포함하지 않는다.

    Returns
        canonical :class:`SourceSnapshotSet`.

    Example
        ``buildSourceSnapshotSet(sources, mapBuildId="b1", createdAt=now, ...)``

    Guide
        source version 하나라도 없으면 exactReplayReady는 false다. policy receipt
        부재는 별도 목록에 남기고 content replay 판정에는 넣지 않는다.

    When
        source 목록을 share replay 또는 projection 입력으로 고정할 때 호출한다.

    How
        probe가 만든 SnapshotSource 전체와 catalog version을 함께 전달한다.

    See Also
        :class:`SnapshotSource`.

    Requires
        모든 sourceId, origin, path가 비어 있지 않아야 한다.

    AIContext
        AI 역할: source identity hash를 결정적으로 만들고 결손을 숨기지 않는다.

    LLM Specifications
        AntiPatterns: 입력 순서, createdAt, dataAsOf, contentLength를 hash하지 않는다.
        OutputSchema: SourceSnapshotSet.
        Prerequisites: unique sourceId.
        Freshness: 호출자가 준 source versions 기준.
        Dataflow: iterable -> normalized tuple -> canonical hash.
        TargetMarkets: market neutral.

    Raises
        ValueError: identity field가 비었거나 sourceId가 중복될 때.
    """

    normalized: list[SnapshotSource] = []
    seenSourceIds: set[str] = set()
    for source in sources:
        if not source.sourceId or not source.origin or not source.path:
            raise ValueError("sourceId, origin, and path are required")
        if source.sourceId in seenSourceIds:
            raise ValueError(f"duplicate sourceId: {source.sourceId}")
        seenSourceIds.add(source.sourceId)
        if source.versionOrEtag in (None, ""):
            reason = source.unreplayableReason or "missingSourceVersion"
            source = replace(
                source,
                versionOrEtag=None,
                replayStatus="unreplayable",
                unreplayableReason=reason,
            )
        elif source.replayStatus != "replayable":
            raise ValueError("versioned source must use replayable status")
        normalized.append(replace(source, path=source.path.replace("\\", "/")))

    orderedSources = tuple(sorted(normalized, key=lambda item: item.sourceId))
    unreplayableSourceIds = tuple(source.sourceId for source in orderedSources if source.replayStatus == "unreplayable")
    canonicalPayload = {
        "schemaVersion": SCHEMA_VERSION,
        "sources": [_canonicalSource(source) for source in orderedSources],
        "mapBuildId": mapBuildId,
        "capabilityCatalogVersion": capabilityCatalogVersion,
        "recipeCatalogVersion": recipeCatalogVersion,
    }
    return SourceSnapshotSet(
        schemaVersion=SCHEMA_VERSION,
        snapshotSetId=f"sha256:{_canonicalHash(canonicalPayload)}",
        createdAt=createdAt,
        sources=orderedSources,
        mapBuildId=mapBuildId,
        capabilityCatalogVersion=capabilityCatalogVersion,
        recipeCatalogVersion=recipeCatalogVersion,
        exactReplayReady=not unreplayableSourceIds,
        unreplayableSourceIds=unreplayableSourceIds,
        missingDataAsOfSourceIds=tuple(source.sourceId for source in orderedSources if not source.dataAsOf),
        missingRedistributionReceiptSourceIds=tuple(
            source.sourceId for source in orderedSources if not source.redistributionReceiptId
        ),
    )


def assessReplayRequest(
    availableSnapshot: SourceSnapshotSet,
    *,
    requestedSnapshotSetId: str | None,
    legacyBuildId: str | None,
) -> ReplayAssessment:
    """Share replay 요청을 exact, current rerun, unavailable로 판정한다.

    Capabilities
        canonical snapshot 일치와 source replayability를 검사하고 legacy buildId
        only 요청을 current rerun으로 강등한다.

    Args
        availableSnapshot: 현재 해소 가능한 source snapshot.
        requestedSnapshotSetId: share가 요구한 canonical snapshot ID.
        legacyBuildId: 옛 share의 map build ID.

    Returns
        fail-closed :class:`ReplayAssessment`.

    Example
        ``assessReplayRequest(snapshot, requestedSnapshotSetId=None, legacyBuildId="b1")``

    Guide
        ID가 같아도 snapshot 안에 unreplayable source가 있으면 exact replay를
        허용하지 않는다.

    When
        share URL 또는 저장된 flight plan을 현재 source로 열기 전에 호출한다.

    How
        available snapshot과 요청 ID를 비교한 뒤 반환 mode로 UI 문구를 고른다.

    See Also
        :class:`ReplayAssessment`.

    Requires
        availableSnapshot은 buildSourceSnapshotSet 결과여야 한다.

    AIContext
        AI 역할: share replay 문구의 사실성을 판정한다.

    LLM Specifications
        AntiPatterns: legacy buildId 또는 current source만으로 exact를 주장하지 않는다.
        OutputSchema: ReplayAssessment.
        Prerequisites: available source snapshot.
        Freshness: available snapshot 기준.
        Dataflow: requested identity plus available identity -> replay mode.
        TargetMarkets: market neutral.

    Raises
        입력 상태를 reason code로 반환하므로 validation 예외를 발생시키지 않는다.
    """

    if not requestedSnapshotSetId:
        reason = "legacyBuildIdOnly" if legacyBuildId else "snapshotSetIdMissing"
        return ReplayAssessment(False, "currentRerun", reason)
    if requestedSnapshotSetId != availableSnapshot.snapshotSetId:
        return ReplayAssessment(False, "unavailable", "sourceSnapshotUnavailable")
    if not availableSnapshot.exactReplayReady:
        return ReplayAssessment(False, "unavailable", "snapshotContainsUnreplayableSources")
    return ReplayAssessment(True, "exactReplay", "sourceSnapshotMatched")


def _stripEtag(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip().strip('"')
    return stripped or None


def _headHeaders(url: str) -> tuple[str | None, str | None, int | None]:
    request = urllib.request.Request(url, method="HEAD")
    with urllib.request.urlopen(request, timeout=30) as response:
        etag = _stripEtag(response.headers.get("etag"))
        repoCommit = response.headers.get("x-repo-commit")
        contentLengthHeader = response.headers.get("content-length")
        contentLength = int(contentLengthHeader) if contentLengthHeader else None
    return repoCommit, etag, contentLength


def _loadJson(url: str) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=30) as response:
        payload = json.load(response)
    if not isinstance(payload, dict):
        raise ValueError("remote JSON payload must be an object")
    return payload


def _payloadHash(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        default=str,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _fileHash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _trackedGitBlob(repoRoot: Path, path: Path) -> str | None:
    relativePath = path.relative_to(repoRoot).as_posix()
    status = subprocess.run(
        ["git", "status", "--short", "--", relativePath],
        cwd=repoRoot,
        check=True,
        capture_output=True,
        text=True,
    )
    if status.stdout.strip():
        return None
    blob = subprocess.run(
        ["git", "rev-parse", f"HEAD:{relativePath}"],
        cwd=repoRoot,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return f"gitBlob:{blob}" if blob else None


def _sourceDataAsOf(meta: dict[str, Any], dataKey: str) -> str | None:
    if dataKey == "buildTime":
        value = meta.get("buildTime")
    else:
        dataAsOf = meta.get("dataAsOf")
        value = dataAsOf.get(dataKey) if isinstance(dataAsOf, dict) else None
    return str(value) if value not in (None, "") else None


def _remoteSource(
    sourceId: str,
    path: str,
    repoCommit: str,
    dataAsOf: str | None,
) -> SnapshotSource:
    immutableUrl = f"{HF_RESOLVE_BASE}/{repoCommit}/{path}"
    _, etag, contentLength = _headHeaders(immutableUrl)
    version = f"hfCommit:{repoCommit};etag:{etag}" if etag else f"hfCommit:{repoCommit}"
    payloadHash = f"sha256:{etag}" if etag and len(etag) == 64 else None
    return SnapshotSource(
        sourceId=sourceId,
        origin="hfDataset",
        path=f"datasets/{HF_REPO}@{repoCommit}/{path}",
        versionOrEtag=version,
        payloadHash=payloadHash,
        dataAsOf=dataAsOf,
        contentLength=contentLength,
    )


def inspectLiveSourceSnapshotSet() -> SourceSnapshotSet:
    """현재 공개 HF와 runtime catalog의 SourceSnapshotSet을 측정한다.

    Capabilities
        HF main의 실제 repo commit을 찾은 뒤 모든 remote path를 immutable commit으로
        재조회하고 capability와 recipe payload의 canonical SHA-256을 계산한다.

    Args
        없음.

    Returns
        현재 source versions를 담은 :class:`SourceSnapshotSet`.

    Example
        ``snapshot = inspectLiveSourceSnapshotSet()``

    Guide
        capability catalog는 live builder 출력의 content hash를 사용한다. 현재 dirty
        worktree의 commit SHA를 catalog version으로 오인하지 않는다.

    When
        현재 공개 source set의 exact replay 가능성을 센서스할 때 호출한다.

    How
        HF commit을 먼저 찾고 immutable path를 검사한 뒤 catalog hash를 결속한다.

    See Also
        :func:`buildSourceSnapshotSet`.

    Requires
        HF public network access와 DartLab import가 가능해야 한다.

    AIContext
        AI 역할: live source version 가용성을 측정한다.

    LLM Specifications
        AntiPatterns: Xet signed redirect URL을 source path에 보존하지 않는다.
        OutputSchema: SourceSnapshotSet.
        Prerequisites: HF source paths와 local catalog file.
        Freshness: 실행 시점.
        Dataflow: HF heads, map meta, catalogs -> snapshot builder.
        TargetMarkets: KR public source set.

    Raises
        RuntimeError: HF main response에 repo commit이 없을 때.
        OSError: remote 또는 local source를 읽지 못할 때.
    """

    movingMetaUrl = f"{HF_RESOLVE_BASE}/main/{MAP_META_PATH}"
    repoCommit, _, _ = _headHeaders(movingMetaUrl)
    if not repoCommit:
        raise RuntimeError("HF source did not expose x-repo-commit")

    immutableMetaUrl = f"{HF_RESOLVE_BASE}/{repoCommit}/{MAP_META_PATH}"
    meta = _loadJson(immutableMetaUrl)
    sources = [
        _remoteSource(sourceId, path, repoCommit, _sourceDataAsOf(meta, dataKey))
        for sourceId, path, dataKey in REMOTE_SOURCE_PATHS
    ]

    from dartlab.reference.capability import loadCapabilities

    createdAt = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    capabilityVersion = _payloadHash(loadCapabilities())
    repoRoot = Path(__file__).resolve().parents[4]
    recipeCatalogPath = repoRoot / "src" / "dartlab" / "skills" / "catalog.json"
    recipeVersion = _fileHash(recipeCatalogPath)
    recipeBlobVersion = _trackedGitBlob(repoRoot, recipeCatalogPath)
    sources.extend(
        [
            SnapshotSource(
                sourceId="capabilityCatalog",
                origin="runtimeCatalog",
                path="dartlab.reference.capability.loadCapabilities",
                versionOrEtag=None,
                payloadHash=capabilityVersion,
                dataAsOf=createdAt,
                replayStatus="unreplayable",
                unreplayableReason="liveCompiledCatalogHasNoImmutableManifest",
            ),
            SnapshotSource(
                sourceId="recipeCatalog",
                origin="localRepository",
                path="src/dartlab/skills/catalog.json",
                versionOrEtag=recipeBlobVersion,
                payloadHash=recipeVersion,
                dataAsOf=createdAt,
                unreplayableReason=(None if recipeBlobVersion else "dirtyCatalogHasNoImmutableBlob"),
                contentLength=recipeCatalogPath.stat().st_size,
            ),
        ]
    )
    return buildSourceSnapshotSet(
        sources,
        mapBuildId=str(meta.get("buildId")) if meta.get("buildId") else None,
        capabilityCatalogVersion=capabilityVersion,
        recipeCatalogVersion=recipeVersion,
        createdAt=createdAt,
    )


def main() -> int:
    """Live SourceSnapshotSet을 측정해 stdout JSON으로 출력한다.

    Capabilities
        live source probe를 CLI에서 실행하고 JSON report를 남긴다.

    Args
        없음.

    Returns
        성공 시 0.

    Example
        ``python sourceSnapshotSetProbe.py``

    Guide
        stdout을 근거로 사용하며 임의 snapshot 파일을 만들지 않는다.

    When
        U0-S01 source version 센서스를 재실행할 때 사용한다.

    How
        inspectLiveSourceSnapshotSet을 호출한 결과를 정렬 JSON으로 출력한다.

    Requires
        HF network, Git CLI, DartLab capability catalog import가 필요하다.

    See Also
        :func:`inspectLiveSourceSnapshotSet`.

    AIContext
        AI 역할: live replay gap을 재측정하고 원장 기록용 JSON을 만든다.

    Raises
        source load와 version 오류를 숨기지 않는다.
    """

    snapshot = inspectLiveSourceSnapshotSet()
    print(json.dumps(snapshot.toDict(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
