"""Live capability와 registry axis 전 후보를 fail-closed 분류한다."""

from __future__ import annotations

import dataclasses
import hashlib
import importlib
import inspect
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from dartlab.reference.capability import loadCapabilities

from ..canonical import CapabilityCensus, RegistryRecord, canonicalDigest
from .schemaDescriptor import (
    SchemaDescriptor,
    buildContractCorpus,
    callableSourceDigest,
    closeSchemaDescriptor,
    extractSchemaDescriptor,
    validateSchemaDescriptor,
)

_ENGINE_CALLABLES = {
    "analysis": ("dartlab.analysis.financial", "Analysis", "__call__"),
    "credit": ("dartlab.credit", None, "credit"),
    "gather": ("dartlab.gather.entry", "GatherEntry", "__call__"),
    "industry": ("dartlab.industry", "Industry", "__call__"),
    "macro": ("dartlab.macro", "Macro", "__call__"),
    "quant": ("dartlab.quant", "Quant", "__call__"),
    "scan": ("dartlab.scan", "Scan", "__call__"),
}
_AXIS_REGISTRIES = {
    "analysis": ("dartlab.analysis.financial._registry", "_AXIS_REGISTRY"),
    "credit": ("dartlab.credit", "_AXIS_REGISTRY"),
    "gather": ("dartlab.gather.entry", "AXIS_REGISTRY"),
    "industry": ("dartlab.industry", "_AXIS_REGISTRY"),
    "macro": ("dartlab.macro", "_AXIS_REGISTRY"),
    "quant": ("dartlab.quant._registry", "_AXIS_REGISTRY"),
    "scan": ("dartlab.scan.router", "_AXIS_REGISTRY"),
}
_ENGINE_PREFIXES = frozenset(_ENGINE_CALLABLES)
_PREVIEW_PREFIXES = frozenset({"simulate"})
_ROOT_CATALOG_KEYS = _ENGINE_PREFIXES | _PREVIEW_PREFIXES
_PUBLIC_COMPANY_METHODS = frozenset({"analysis", "credit", "filings", "panel", "select", "story", "trace"})


@dataclass(frozen=True, slots=True)
class CapabilityRef:
    capabilityId: str
    candidateId: str
    kind: str
    apiRef: str
    engine: str | None
    axis: str | None
    targetScope: str
    runtimeBoundary: str
    determinism: str
    seedPolicy: str
    costClass: str
    memoryClass: str
    timeoutMs: int
    retryPolicy: str
    cachePolicy: str
    concurrencyClass: str
    maturity: str
    visibility: str
    sourceRevision: str
    sourceDigest: str
    status: str
    eligible: bool
    gapReasons: tuple[str, ...]
    schemaDescriptor: SchemaDescriptor | None = None


@dataclass(frozen=True, slots=True)
class UniverseCapabilityRegistry:
    capabilities: tuple[CapabilityRef, ...]
    discoveredCandidateCount: int
    classifiedCandidateCount: int
    eligibleCallableCount: int
    validatedSchemaCount: int
    blockedEligibleCount: int
    catalogCoverage: float
    executionReadiness: float
    inventedAxisCount: int
    censusDigest: str
    registryDigest: str

    def get(self, capabilityId: str) -> CapabilityRef | None:
        return next((item for item in self.capabilities if item.capabilityId == capabilityId), None)

    def byCandidate(self, candidateId: str) -> CapabilityRef | None:
        return next((item for item in self.capabilities if item.candidateId == candidateId), None)


def _dispatcher(engine: str) -> Any:
    moduleName, className, attributeName = _ENGINE_CALLABLES[engine]
    module = importlib.import_module(moduleName)
    owner = getattr(module, className) if className else module
    return getattr(owner, attributeName)


def _runtimeDigest(candidateId: str, runtimeEntry: Any) -> str:
    return canonicalDigest({"candidateId": candidateId, "runtimeEntry": runtimeEntry})


def _registeredAxis(engine: str, axis: str) -> bool:
    moduleName, attributeName = _AXIS_REGISTRIES[engine]
    registry = getattr(importlib.import_module(moduleName), attributeName)
    return isinstance(registry, dict) and axis in registry


def _fileEvidence(target: Any) -> tuple[str, str] | None:
    pathText = inspect.getsourcefile(target) if not inspect.ismodule(target) else getattr(target, "__file__", None)
    if not pathText:
        return None
    path = Path(pathText).resolve()
    if not path.is_file():
        return None
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest, f"source:{path.as_posix()}#sha256={digest}"


def _axisImplementationEvidence(engine: str, axis: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Registry module과 실존 axis implementation byte를 descriptor source에 결박한다."""
    moduleName, attributeName = _AXIS_REGISTRIES[engine]
    module = importlib.import_module(moduleName)
    registry = getattr(module, attributeName)
    entry = registry.get(axis)
    digests = []
    evidence = []
    moduleEvidence = _fileEvidence(module)
    if moduleEvidence is not None:
        digests.append(moduleEvidence[0])
        evidence.append(moduleEvidence[1])
    targets = []
    if entry is not None:
        entryModule = getattr(entry, "module", None)
        entryFunction = getattr(entry, "fn", None)
        if entryModule and entryFunction:
            try:
                targets.append(getattr(importlib.import_module(entryModule), entryFunction))
            except (ImportError, AttributeError) as exc:
                raise RuntimeError(f"axis implementation unresolved: {entryModule}:{entryFunction}") from exc
        for calc in getattr(entry, "calcs", ()):
            calcModule = getattr(calc, "module", None)
            calcFunction = getattr(calc, "fn", None)
            if calcModule and calcFunction:
                try:
                    targets.append(getattr(importlib.import_module(calcModule), calcFunction))
                except (ImportError, AttributeError) as exc:
                    raise RuntimeError(f"axis calc unresolved: {calcModule}:{calcFunction}") from exc
    if engine == "scan" and axis in {"account", "ratio"}:
        edgarModule = importlib.import_module("dartlab.providers.edgar.finance.scanAccount")
        targets.append(getattr(edgarModule, "scanAccount" if axis == "account" else "scanRatio"))
    for target in targets:
        item = _fileEvidence(target)
        if item is not None and item[0] not in digests:
            digests.append(item[0])
            evidence.append(item[1])
    return tuple(sorted(digests)), tuple(sorted(evidence))


def _closeAxisSpecificArgs(descriptor: SchemaDescriptor, engine: str | None, axis: str | None) -> SchemaDescriptor:
    """Dispatcher의 명시적이고 소스에 존재하는 axis별 kwargs만 schema에 추가한다."""
    if engine != "scan" or axis not in {"account", "ratio"}:
        return descriptor
    argsSchema = dict(descriptor.argsSchema)
    properties = dict(argsSchema.get("properties", {}))
    properties["market"] = {"type": "string", "enum": ["dart", "edgar", "us", "US"]}
    argsSchema["properties"] = dict(sorted(properties.items()))
    descriptorInputs = {
        "apiRef": descriptor.apiRef,
        "axis": descriptor.axis,
        "sourceDigest": descriptor.sourceDigest,
        "argsSchema": argsSchema,
        "outputSchema": descriptor.outputSchema,
        "version": descriptor.version,
    }
    return replace(
        descriptor,
        descriptorId=f"du:v1:schema:{canonicalDigest(descriptorInputs)}",
        argsSchema=argsSchema,
    )


def _axisCandidate(
    candidateId: str,
    record: RegistryRecord | None,
    runtimeEntry: Any,
) -> tuple[str | None, str | None]:
    if record is not None:
        return record.owner, record.recordId.split(".", 1)[1]
    prefix, separator, suffix = candidateId.partition(".")
    if separator and prefix in _ENGINE_PREFIXES and _registeredAxis(prefix, suffix):
        return prefix, suffix
    return None, None


def _classification(
    candidateId: str,
    record: RegistryRecord | None,
    runtimeEntry: Any,
) -> tuple[str, bool, tuple[str, ...], str, str, str]:
    engine, axis = _axisCandidate(candidateId, record, runtimeEntry)
    if record is not None and record.hidden:
        return "HIDDEN_PREVIEW", False, ("HIDDEN_PREVIEW",), "PREVIEW_LOCAL", "preview", "SIMULATION"
    if engine in _ENGINE_PREFIXES and axis:
        try:
            callableObject = _dispatcher(engine)
        except Exception as exc:
            return (
                "MIRRORED_MISSING",
                False,
                (f"DISPATCHER_UNAVAILABLE:{type(exc).__name__}",),
                "LOCAL_PYTHON",
                "observed",
                "HEAVY_IO",
            )
        if not callable(callableObject):
            return "MIRRORED_MISSING", False, ("PUBLIC_FACADE_NOT_CALLABLE",), "LOCAL_PYTHON", "observed", "HEAVY_IO"
        status = "ACTIVE" if runtimeEntry is not None else "CALLABLE_UNMIRRORED"
        gaps = () if runtimeEntry is not None else ("CAPABILITY_MIRROR_MISSING",)
        boundary = "LOCAL_SECRET" if engine == "gather" else "LOCAL_PYTHON"
        determinism = "SNAPSHOT_BOUND" if engine != "gather" else "SOURCE_DEPENDENT"
        lane = "HEAVY_IO" if engine in {"gather", "scan"} else "MEMORY_HEAVY"
        return status, True, gaps, boundary, determinism, lane
    prefix, separator, _ = candidateId.partition(".")
    if separator and prefix in _ENGINE_PREFIXES:
        return "MIRRORED_MISSING", False, ("AXIS_NOT_REGISTERED",), "LOCAL_PYTHON", "unknown", "LIGHT_IO"
    if candidateId in _ROOT_CATALOG_KEYS:
        if candidateId in _PREVIEW_PREFIXES:
            return "HIDDEN_PREVIEW", False, ("PREVIEW_NOT_STABLE",), "PREVIEW_LOCAL", "stochastic", "SIMULATION"
        return "REJECTED_INTERNAL", False, ("ENGINE_GUIDE_NOT_AXIS",), "LOCAL_PYTHON", "catalog", "LIGHT_IO"
    if candidateId.startswith("Company."):
        method = candidateId.split(".", 1)[1]
        if method in _PUBLIC_COMPANY_METHODS:
            return (
                "SCHEMA_INCOMPLETE",
                False,
                ("COMPANY_BOUND_EXECUTOR_DEFERRED",),
                "LOCAL_PYTHON",
                "snapshot",
                "MEMORY_HEAVY",
            )
        return "REJECTED_INTERNAL", False, ("NOT_PUBLIC_CALL_CONTRACT",), "LOCAL_PYTHON", "unknown", "LIGHT_IO"
    kind = runtimeEntry.get("kind") if isinstance(runtimeEntry, dict) else None
    if kind in {"class", "property"}:
        return "REJECTED_INTERNAL", False, (f"NON_EXECUTABLE_KIND:{kind}",), "LOCAL_PYTHON", "catalog", "LIGHT_IO"
    return "REJECTED_INTERNAL", False, ("OUTSIDE_ENGINE_AXIS_CONTRACT",), "LOCAL_PYTHON", "unknown", "LIGHT_IO"


def _buildRef(
    candidateId: str,
    record: RegistryRecord | None,
    runtimeEntry: Any,
    census: CapabilityCensus,
) -> CapabilityRef:
    engine, axis = _axisCandidate(candidateId, record, runtimeEntry)
    status, eligible, gaps, boundary, determinism, lane = _classification(candidateId, record, runtimeEntry)
    apiRef = f"dartlab.{engine}" if engine else candidateId
    authorityDigest = _runtimeDigest(candidateId, runtimeEntry)
    sourceDigest = authorityDigest
    sourceRevision = f"capability-census:{census.digest}"
    evidence = (f"capability:{candidateId}#sha256={authorityDigest}",)
    callableObject = None
    if eligible and engine:
        callableObject = _dispatcher(engine)
        sourceDigest, sourceEvidence = callableSourceDigest(callableObject, authorityDigest)
        evidence += sourceEvidence
        implementationDigests, implementationEvidence = _axisImplementationEvidence(engine, axis or "")
        sourceDigest = canonicalDigest(
            {
                "dispatcherDigest": sourceDigest,
                "implementationDigests": implementationDigests,
            }
        )
        evidence += implementationEvidence
    capabilityInputs = {
        "candidateId": candidateId,
        "apiRef": apiRef,
        "axis": axis,
        "sourceDigest": sourceDigest,
    }
    ref = CapabilityRef(
        capabilityId=f"du:v1:capability:{canonicalDigest(capabilityInputs)}",
        candidateId=candidateId,
        kind="AXIS" if axis else "CATALOG_ENTRY",
        apiRef=apiRef,
        engine=engine,
        axis=axis,
        targetScope="COMPANY_OR_MARKET" if axis else "NONE",
        runtimeBoundary=boundary,
        determinism=determinism,
        seedPolicy="FORBIDDEN" if determinism != "stochastic" else "REQUIRED",
        costClass="HIGH" if lane in {"HEAVY_IO", "MEMORY_HEAVY"} else "LOW",
        memoryClass="BOUNDED_WORKER",
        timeoutMs=120_000,
        retryPolicy="TRANSIENT_ONLY" if engine == "gather" else "NONE",
        cachePolicy="SNAPSHOT_IDEMPOTENT" if eligible else "NONE",
        concurrencyClass=lane,
        maturity="PREVIEW" if status == "HIDDEN_PREVIEW" else "OBSERVED",
        visibility="LOCAL",
        sourceRevision=sourceRevision,
        sourceDigest=sourceDigest,
        status=status,
        eligible=eligible,
        gapReasons=gaps,
    )
    if not eligible:
        return ref
    descriptor = extractSchemaDescriptor(
        ref,
        {
            "callable": callableObject,
            "sourceRevision": sourceRevision,
            "sourceDigest": sourceDigest,
            "evidenceRefs": evidence,
        },
    )
    descriptor = _closeAxisSpecificArgs(descriptor, engine, axis)
    corpus = buildContractCorpus(descriptor)
    report = validateSchemaDescriptor(descriptor, corpus)
    descriptor = closeSchemaDescriptor(descriptor, corpus, report)
    if descriptor.status != "VALIDATED":
        return replace(
            ref, status="SCHEMA_INCOMPLETE", gapReasons=("SCHEMA_NOT_VALIDATED",), schemaDescriptor=descriptor
        )
    return replace(ref, schemaDescriptor=descriptor)


def buildCapabilityRegistry(census: CapabilityCensus) -> UniverseCapabilityRegistry:
    """Census union을 다시 live authority와 대조하고 모든 후보를 정확히 한 번 분류한다."""
    runtime = loadCapabilities()
    runtimeIds = tuple(sorted(str(key) for key in runtime))
    if runtimeIds != census.runtimeIds:
        raise ValueError("capability census와 live runtime ID가 달라 재센서스가 필요")
    if census.errors:
        raise ValueError(f"registry census error가 있어 U2를 열 수 없음: {census.errors}")
    recordById = {record.recordId: record for record in census.registryRecords}
    candidateIds = tuple(sorted(set(runtimeIds) | set(recordById)))
    refs = tuple(
        _buildRef(candidateId, recordById.get(candidateId), runtime.get(candidateId), census)
        for candidateId in candidateIds
    )
    eligible = tuple(item for item in refs if item.eligible)
    validated = tuple(
        item for item in eligible if item.schemaDescriptor is not None and item.schemaDescriptor.status == "VALIDATED"
    )
    blocked = tuple(item for item in eligible if item not in validated)
    registryDigest = canonicalDigest({"censusDigest": census.digest, "capabilities": refs})
    return UniverseCapabilityRegistry(
        capabilities=refs,
        discoveredCandidateCount=len(candidateIds),
        classifiedCandidateCount=len(refs),
        eligibleCallableCount=len(eligible),
        validatedSchemaCount=len(validated),
        blockedEligibleCount=len(blocked),
        catalogCoverage=len(refs) / len(candidateIds) if candidateIds else 1.0,
        executionReadiness=len(validated) / len(eligible) if eligible else 1.0,
        inventedAxisCount=0,
        censusDigest=census.digest,
        registryDigest=registryDigest,
    )


def cloneCapability(
    capability: CapabilityRef,
    **changes: Any,
) -> CapabilityRef:
    """Mutation fixture가 불변 CapabilityRef를 명시적으로 파생할 때 사용한다."""
    unknown = set(changes) - {field.name for field in dataclasses.fields(CapabilityRef)}
    if unknown:
        raise ValueError(f"알 수 없는 CapabilityRef field: {sorted(unknown)}")
    return replace(capability, **changes)
