"""현재 snapshot에 결박된 DART와 EDGAR engine capability live canary."""

from __future__ import annotations

import hashlib
import io
import os
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, replace
from pathlib import Path

import polars as pl
from huggingface_hub import hf_hub_download

from ..canonical import canonicalDigest
from ..catalog.models import CatalogObject, CatalogResource, CatalogState
from ..catalog.snapshot import CatalogSnapshot
from ..contracts import Visibility
from ..execution.receipts import ExecutionStore, replayExecution
from ..execution.registry import UniverseCapabilityRegistry
from ..graph.query import GraphStore
from ..validation.g4e import validateRetrievalEvidencePack
from .capability import CapabilityExecutionAdapter
from .engine import UniverseQueryEngine
from .models import CapabilityRequest, QueryTimeContext, buildUniverseQuery
from .planner import buildQueryPlan

_PERIOD_RE = re.compile(r"^\d{4}(?:Q[1-4])?$")
_MARKET_ARTIFACTS = (
    ("DART", "dart", "dart/scan/finance.parquet", 2_600, 0.95),
    ("EDGAR", "edgar", "edgar/scan/finance.parquet", 4_000, 0.70),
)
_DART_EXECUTION_PATHS = (
    "dart/scan/finance.parquet",
    "dart/scan/changes.parquet",
    "dart/scan/sharesOutstanding.parquet",
    "metadata/corpList.parquet",
)
_EXECUTION_ALIASES = {
    "DART": (("metadata/corpList.parquet", "kindList/corpList.parquet"),),
    "EDGAR": (("edgar/tickers/tickers.parquet", "edgar/tickers.parquet"),),
}


@dataclass(frozen=True, slots=True)
class CapabilityDataBinding:
    market: str
    relativePath: str
    resourceVersionId: str
    objectId: str
    contentDigest: str
    byteSize: int
    executionResourceCount: int
    executionByteSize: int
    executionArtifactSetDigest: str
    digest: str


@dataclass(frozen=True, slots=True)
class CapabilityMarketCanary:
    market: str
    passed: bool
    binding: CapabilityDataBinding
    executionId: str
    status: str
    returnedRows: int
    sourceUniverseCount: int
    rowCoverageRatio: float
    outputBytes: int
    periodColumnCount: int
    numericPeriodValueCount: int
    arrowMagicValid: bool
    replayValid: bool
    executionRefValid: bool
    g4eValid: bool
    failureCodes: tuple[str, ...]
    digest: str


@dataclass(frozen=True, slots=True)
class CapabilityCanaryReport:
    passed: bool
    snapshotId: str
    candidateId: str
    capabilityId: str
    markets: tuple[CapabilityMarketCanary, ...]
    failureCodes: tuple[str, ...]
    digest: str


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resourceAtPath(catalog: CatalogState, relativePath: str) -> CatalogResource:
    matches = tuple(
        item
        for item in catalog.resources
        if item.resourceKind == "HF_FILE" and dict(item.locator).get("path") == relativePath
    )
    if len(matches) != 1:
        raise ValueError(f"capability data resource cardinality={len(matches)} path={relativePath}")
    return matches[0]


def _matchesResource(path: Path, resource: CatalogResource) -> bool:
    return path.is_file() and path.stat().st_size == resource.byteSize and _sha256(path) == resource.contentDigest


def _rootedPath(root: Path, relativePath: str) -> Path:
    """기존 HF cache symlink를 따라가지 않고 lexical data-root 경계를 검사한다."""
    resolvedRoot = root.resolve()
    path = Path(os.path.abspath(resolvedRoot / relativePath))
    if not path.is_relative_to(resolvedRoot):
        raise ValueError(f"capability resource path가 data root를 벗어남 path={relativePath}")
    return path


def _ensurePinnedResource(
    resource: CatalogResource,
    *,
    dataRoot: Path,
    localDataRoot: Path,
    token: str | None,
    preferLocal: bool,
) -> Path:
    """정확히 고정된 HF byte만 Universe source cache에 준비한다."""
    relativePath = dict(resource.locator).get("path", "")
    if not relativePath:
        raise ValueError("capability resource path가 비어 있음")
    resolvedRoot = dataRoot.resolve()
    destination = _rootedPath(resolvedRoot, relativePath)
    if _matchesResource(destination, resource):
        return destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        destination.unlink()
    localSource = _rootedPath(localDataRoot, relativePath)
    if preferLocal and _matchesResource(localSource, resource):
        try:
            os.link(localSource, destination)
            return destination
        except OSError:
            pass
    downloaded = Path(
        hf_hub_download(
            repo_id=resource.sourceRef,
            filename=relativePath,
            revision=resource.sourceRevision,
            repo_type="dataset",
            local_dir=resolvedRoot,
            token=token,
            force_download=True,
        )
    ).resolve()
    if downloaded != destination or not _matchesResource(downloaded, resource):
        raise ValueError(f"capability resource snapshot mismatch path={relativePath}")
    return downloaded


def _createReadAlias(dataRoot: Path, sourceRelativePath: str, aliasRelativePath: str) -> None:
    root = dataRoot.resolve()
    source = _rootedPath(root, sourceRelativePath)
    alias = _rootedPath(root, aliasRelativePath)
    if not source.is_file():
        raise ValueError("capability read alias 입력이 잘못됨")
    alias.parent.mkdir(parents=True, exist_ok=True)
    if alias.exists():
        try:
            if source.samefile(alias):
                return
        except OSError:
            pass
        alias.unlink()
    os.link(source, alias)


def _executionResources(catalog: CatalogState, market: str) -> tuple[CatalogResource, ...]:
    if market == "DART":
        return tuple(_resourceAtPath(catalog, path) for path in _DART_EXECUTION_PATHS)
    resources = tuple(
        item
        for item in catalog.resources
        if item.resourceKind == "HF_FILE"
        and dict(item.locator).get("path", "").startswith("edgar/finance/")
        and dict(item.locator).get("path", "").endswith(".parquet")
    )
    ticker = _resourceAtPath(catalog, "edgar/tickers/tickers.parquet")
    if len(resources) < 5_000:
        raise ValueError(f"EDGAR finance source coverage below threshold count={len(resources)}")
    return tuple(sorted((*resources, ticker), key=lambda item: item.resourceVersionId))


def _prepareExecutionResources(
    catalog: CatalogState,
    *,
    dataRoot: Path,
    localDataRoot: Path,
    market: str,
    token: str | None,
) -> tuple[int, int, str]:
    resources = _executionResources(catalog, market)

    def prepare(resource: CatalogResource) -> tuple[str, str, int]:
        path = dict(resource.locator).get("path", "")
        preferLocal = path.startswith("edgar/finance/") or path.startswith("dart/scan/")
        _ensurePinnedResource(
            resource,
            dataRoot=dataRoot,
            localDataRoot=localDataRoot,
            token=token,
            preferLocal=preferLocal,
        )
        return path, resource.contentDigest, resource.byteSize

    with ThreadPoolExecutor(max_workers=8, thread_name_prefix=f"universe-{market.casefold()}") as pool:
        prepared = tuple(pool.map(prepare, resources))
    for sourceRelativePath, aliasRelativePath in _EXECUTION_ALIASES[market]:
        _createReadAlias(dataRoot, sourceRelativePath, aliasRelativePath)
    ordered = tuple(sorted(prepared))
    return len(ordered), sum(item[2] for item in ordered), canonicalDigest(ordered)


def bindCapabilityDataArtifact(
    catalog: CatalogState,
    *,
    dataRoot: Path,
    market: str,
    relativePath: str,
) -> CapabilityDataBinding:
    """로컬 engine artifact를 pinned HF resource byte와 일치할 때만 결박한다."""
    resource = _resourceAtPath(catalog, relativePath)
    resolvedDataRoot = dataRoot.resolve()
    localPath = (resolvedDataRoot / Path(relativePath)).resolve()
    if not localPath.is_relative_to(resolvedDataRoot) or not localPath.is_file():
        raise ValueError(f"{market} capability data artifact missing")
    byteSize = localPath.stat().st_size
    contentDigest = _sha256(localPath)
    if byteSize != resource.byteSize or contentDigest != resource.contentDigest:
        raise ValueError(f"{market} capability data artifact snapshot mismatch")
    objects = tuple(item for item in catalog.objects if resource.resourceVersionId in item.resourceRefs)
    if len(objects) != 1:
        raise ValueError(f"{market} capability data object cardinality={len(objects)}")
    base = CapabilityDataBinding(
        market=market,
        relativePath=relativePath,
        resourceVersionId=resource.resourceVersionId,
        objectId=objects[0].objectId,
        contentDigest=contentDigest,
        byteSize=byteSize,
        executionResourceCount=1,
        executionByteSize=byteSize,
        executionArtifactSetDigest=canonicalDigest(((relativePath, contentDigest, byteSize),)),
        digest="",
    )
    return replace(base, digest=canonicalDigest(base))


def prepareCapabilityDataArtifact(
    catalog: CatalogState,
    *,
    dataRoot: Path,
    market: str,
    relativePath: str,
    token: str | None,
    localDataRoot: Path | None = None,
) -> CapabilityDataBinding:
    """Universe 전용 cache에 pinned HF artifact를 lazy fetch하고 byte 결박한다."""
    try:
        return bindCapabilityDataArtifact(
            catalog,
            dataRoot=dataRoot,
            market=market,
            relativePath=relativePath,
        )
    except ValueError:
        pass
    resource = _resourceAtPath(catalog, relativePath)
    dataRoot.mkdir(parents=True, exist_ok=True)
    _ensurePinnedResource(
        resource,
        dataRoot=dataRoot,
        localDataRoot=(localDataRoot or dataRoot),
        token=token,
        preferLocal=localDataRoot is not None,
    )
    return bindCapabilityDataArtifact(
        catalog,
        dataRoot=dataRoot,
        market=market,
        relativePath=relativePath,
    )


def _validateArrow(payload: bytes) -> tuple[bool, int, int, int]:
    arrowMagicValid = payload[:6] == b"ARROW1" and payload[-6:] == b"ARROW1"
    if not arrowMagicValid:
        return False, 0, 0, 0
    frame = pl.read_ipc(io.BytesIO(payload))
    periodColumns = tuple(column for column in frame.columns if _PERIOD_RE.fullmatch(column))
    numericValues = sum(
        frame.select(pl.col(column).cast(pl.Float64, strict=False).is_not_null().sum()).item()
        for column in periodColumns
    )
    return True, frame.height, len(periodColumns), int(numericValues)


def _sourceUniverseCount(dataRoot: Path, market: str) -> int:
    if market == "DART":
        return int(
            pl.scan_parquet(dataRoot / "dart" / "scan" / "finance.parquet")
            .filter(pl.col("account_id_std") == "sales")
            .select(pl.col("stockCode").n_unique())
            .collect()
            .item()
        )
    financeCiks = {item.stem for item in (dataRoot / "edgar" / "finance").glob("*.parquet")}
    tickerCiks = set(
        pl.read_parquet(dataRoot / "edgar" / "tickers.parquet", columns=["cik"])["cik"]
        .cast(pl.Utf8)
        .str.zfill(10)
        .to_list()
    )
    return len(financeCiks & tickerCiks)


def runCapabilityCanary(
    *,
    repoRoot: Path,
    controlRoot: Path,
    dataRoot: Path,
    token: str | None,
    catalog: CatalogState,
    snapshot: CatalogSnapshot,
    graph: GraphStore,
    registry: UniverseCapabilityRegistry,
) -> tuple[CapabilityCanaryReport, CapabilityExecutionAdapter | None]:
    """DART와 EDGAR 전수 account axis를 U2 worker와 G4E로 실제 실행한다."""
    capability = registry.byCandidate("scan.account")
    topFailures = []
    if capability is None or not capability.eligible or capability.schemaDescriptor is None:
        topFailures.append("SCAN_ACCOUNT_CAPABILITY_UNAVAILABLE")
        base = CapabilityCanaryReport(False, snapshot.snapshotId, "scan.account", "", (), tuple(topFailures), "")
        return replace(base, digest=canonicalDigest(base)), None
    bindings = []
    for market, _marketArg, relativePath, _minRows, _minCoverageRatio in _MARKET_ARTIFACTS:
        try:
            primary = prepareCapabilityDataArtifact(
                catalog,
                dataRoot=dataRoot,
                market=market,
                relativePath=relativePath,
                token=token,
                localDataRoot=repoRoot / "data",
            )
            resourceCount, byteSize, artifactSetDigest = _prepareExecutionResources(
                catalog,
                dataRoot=dataRoot,
                localDataRoot=repoRoot / "data",
                market=market,
                token=token,
            )
            enriched = replace(
                primary,
                executionResourceCount=resourceCount,
                executionByteSize=byteSize,
                executionArtifactSetDigest=artifactSetDigest,
                digest="",
            )
            bindings.append(replace(enriched, digest=canonicalDigest(enriched)))
        except (OSError, RuntimeError, ValueError):
            topFailures.append(f"{market}_DATA_BINDING_FAILED")
    if topFailures:
        base = CapabilityCanaryReport(
            False,
            snapshot.snapshotId,
            capability.candidateId,
            capability.capabilityId,
            (),
            tuple(sorted(topFailures)),
            "",
        )
        return replace(base, digest=canonicalDigest(base)), None
    adapter = CapabilityExecutionAdapter(
        catalog,
        registry,
        controlRoot=controlRoot,
        protectedPaths=(repoRoot / "src", repoRoot / "tests" / "_attempts" / "dartlabUniverse"),
        readDataRoot=dataRoot,
    )
    marketResults = []
    store = ExecutionStore(controlRoot)
    for (market, marketArg, _relativePath, minRows, minCoverageRatio), binding in zip(
        _MARKET_ARTIFACTS, bindings, strict=True
    ):
        request = CapabilityRequest(
            capabilityId=capability.capabilityId,
            targetRefs=(binding.objectId,),
            args=(("freq", "Y"), ("market", marketArg), ("target", "sales")),
            assumptionRefs=(f"du:v1:capability-input:{binding.executionArtifactSetDigest}",),
        )
        query = buildUniverseQuery(
            f"{binding.objectId} scan.account sales {marketArg}",
            timeContext=QueryTimeContext("9999-12-30T00:00:00Z", "9999-12-30T00:00:00Z"),
            allowedVisibility=frozenset({Visibility.LOCAL}),
            capabilityRequests=(request,),
        )
        plan = buildQueryPlan(query, snapshot)
        with UniverseQueryEngine(catalog, snapshot, graph, capabilityExecutor=adapter) as engine:
            pack = engine.execute(query, plan=plan)
        receipt = store.loadReceipt(pack.executionRefs[0]) if len(pack.executionRefs) == 1 else None
        payload = b""
        replayValid = False
        if receipt is not None:
            replay = replayExecution(receipt, store)
            replayValid = replay.valid
            if replay.payloads:
                payload = replay.payloads[0]
        arrowMagicValid, frameRows, periodColumnCount, numericPeriodValueCount = _validateArrow(payload)
        sourceUniverseCount = _sourceUniverseCount(dataRoot, market)
        rowCoverageRatio = frameRows / sourceUniverseCount if sourceUniverseCount else 0.0
        executionRefValid = bool(receipt and adapter.verifyExecutionRef(receipt.executionId))
        g4e = validateRetrievalEvidencePack(
            pack,
            query=query,
            plan=plan,
            snapshot=snapshot,
            catalog=catalog,
            graph=graph,
            executionRefVerifiers=(adapter.verifyExecutionRef,),
        )
        failures = []
        if receipt is None or receipt.status != "SUCCEEDED":
            failures.append("EXECUTION_NOT_SUCCEEDED")
        if not arrowMagicValid:
            failures.append("ARROW_OUTPUT_INVALID")
        if frameRows < minRows or (receipt is not None and frameRows != receipt.budgetUsed.returnedRows):
            failures.append("MARKET_ROW_COVERAGE_BELOW_THRESHOLD")
        if rowCoverageRatio < minCoverageRatio:
            failures.append("MARKET_SOURCE_COVERAGE_RATIO_BELOW_THRESHOLD")
        if periodColumnCount < 3 or numericPeriodValueCount < frameRows:
            failures.append("PERIOD_VALUE_COVERAGE_INVALID")
        if not replayValid or not executionRefValid:
            failures.append("EXECUTION_REPLAY_INVALID")
        if not g4e.valid:
            failures.append("EXECUTION_G4E_INVALID")
        baseMarket = CapabilityMarketCanary(
            market=market,
            passed=not failures,
            binding=binding,
            executionId=receipt.executionId if receipt else "",
            status=receipt.status if receipt else "MISSING",
            returnedRows=receipt.budgetUsed.returnedRows if receipt else 0,
            sourceUniverseCount=sourceUniverseCount,
            rowCoverageRatio=round(rowCoverageRatio, 6),
            outputBytes=receipt.budgetUsed.outputBytes if receipt else 0,
            periodColumnCount=periodColumnCount,
            numericPeriodValueCount=numericPeriodValueCount,
            arrowMagicValid=arrowMagicValid,
            replayValid=replayValid,
            executionRefValid=executionRefValid,
            g4eValid=g4e.valid,
            failureCodes=tuple(sorted(failures)),
            digest="",
        )
        marketResults.append(replace(baseMarket, digest=canonicalDigest(baseMarket)))
    if any(not item.passed for item in marketResults):
        topFailures.append("MARKET_CAPABILITY_CANARY_FAILED")
    base = CapabilityCanaryReport(
        passed=not topFailures,
        snapshotId=snapshot.snapshotId,
        candidateId=capability.candidateId,
        capabilityId=capability.capabilityId,
        markets=tuple(marketResults),
        failureCodes=tuple(sorted(topFailures)),
        digest="",
    )
    return replace(base, digest=canonicalDigest(base)), adapter


def capabilityCanarySummary(report: CapabilityCanaryReport) -> dict[str, object]:
    """CLI report에서 dataclass 중첩을 안정적으로 직렬화한다."""
    return asdict(report)
