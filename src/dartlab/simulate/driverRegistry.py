"""Register curated driver sources before path generation.

The registry is an internal safety gate between workbench source adapters and
``driverPaths``. It does not discover data, fit coefficients, issue admission,
or recommend policies. It records why a lane is allowed to behave as a path
driver, rejects state snapshots and semantic laundering, and then delegates the
actual path construction to ``buildDriverPathSet``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import polars as pl

from dartlab.simulate.driverPaths import (
    DriverAssumptionSource,
    DriverFactorSpec,
    DriverHistorySource,
    DriverPathSet,
    buildDriverPathSet,
)
from dartlab.simulate.empiricalPaths import PathMeasureCertificate
from dartlab.simulate.vintage import canonicalPayloadHash

REGISTRY_VERSION = "driver-registry-v1"
_EXECUTABLE_ROLES = {"pathHistory", "explicitAssumption"}
_BLOCKED_ROLES = {"stateSnapshot", "observedFeature", "staticClassification", "unsupported"}
_OPERATING_SHOCK_TARGETS = {
    "marketPriceChange",
    "demandChange",
    "unitCostChange",
    "fixedCostChange",
    "capacityChange",
    "debtRate",
}
_FINANCIAL_RATIO_UNITS = {"ratio", "percent", "percentage", "days", "turnover", "multiple"}


class DriverRegistryError(ValueError):
    """Raised when driver lanes cannot be safely registered for path generation."""


@dataclass(frozen=True)
class DriverRegistryCandidate:
    """One proposed lane and the semantic evidence for admitting it as a driver."""

    laneId: str
    laneRole: str
    source: DriverHistorySource | DriverAssumptionSource
    semanticRefs: tuple[str, ...] = ()
    selectionReason: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "semanticRefs", tuple(self.semanticRefs))


@dataclass(frozen=True)
class DriverRegistryAudit:
    """Audit ledger for a compiled registry path set."""

    registryId: str
    registryHash: str
    registryVersion: str
    knowledgeAsOf: str
    laneIds: tuple[str, ...]
    cardIds: tuple[str, ...]
    factorIds: tuple[str, ...]
    commonObservationCount: int
    sourceObservationCounts: tuple[tuple[str, int], ...]
    eventStart: str
    eventEnd: str
    sourceRefs: tuple[str, ...]
    semanticRefs: tuple[str, ...]
    warnings: tuple[str, ...]
    pathSetHash: str
    pathSetInputHash: str
    validationStatus: str
    historyStatus: str


@dataclass(frozen=True)
class DriverRegistryResult:
    """Registry output paired with the underlying driver path set."""

    pathSet: DriverPathSet
    audit: DriverRegistryAudit


def _dateText(value: str, label: str) -> str:
    text = str(value).replace("-", "")[:8]
    if len(text) != 8 or not text.isdigit():
        raise DriverRegistryError(f"invalid {label}: {value}")
    return text


def _dedupe(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value))


def _sourceColumn(factor: DriverFactorSpec) -> str:
    return factor.sourceColumn or factor.variableId


def _sourceCard(source: DriverHistorySource | DriverAssumptionSource):
    if isinstance(source, DriverHistorySource | DriverAssumptionSource):
        return source.card
    raise DriverRegistryError("unknown driver registry source")


def _sourceText(candidate: DriverRegistryCandidate) -> str:
    card = _sourceCard(candidate.source)
    return " ".join(
        (
            card.providerId,
            card.datasetId,
            card.entityId,
            candidate.laneId,
            candidate.laneRole,
            *card.sourceRefs,
            *candidate.semanticRefs,
        )
    ).lower()


def _candidatePayload(candidate: DriverRegistryCandidate) -> dict:
    card = _sourceCard(candidate.source)
    return {
        "laneId": candidate.laneId,
        "laneRole": candidate.laneRole,
        "card": card,
        "semanticRefs": candidate.semanticRefs,
        "selectionReason": candidate.selectionReason,
    }


def _validateRole(candidate: DriverRegistryCandidate) -> None:
    if not candidate.laneId or not candidate.laneRole:
        raise DriverRegistryError("driver registry candidates need laneId and laneRole")
    if not candidate.semanticRefs:
        raise DriverRegistryError(f"driver registry candidate needs semanticRefs: {candidate.laneId}")
    if candidate.laneRole in _BLOCKED_ROLES:
        raise DriverRegistryError(f"{candidate.laneRole} cannot be registered as driver path: {candidate.laneId}")
    if candidate.laneRole not in _EXECUTABLE_ROLES:
        raise DriverRegistryError(f"unknown driver registry laneRole: {candidate.laneRole}")
    if candidate.laneRole == "pathHistory" and not isinstance(candidate.source, DriverHistorySource):
        raise DriverRegistryError(f"pathHistory needs a DriverHistorySource: {candidate.laneId}")
    if candidate.laneRole == "explicitAssumption" and not isinstance(candidate.source, DriverAssumptionSource):
        raise DriverRegistryError(f"explicitAssumption needs a DriverAssumptionSource: {candidate.laneId}")


def _validateFactorSemantics(candidate: DriverRegistryCandidate) -> None:
    card = _sourceCard(candidate.source)
    sourceText = _sourceText(candidate)
    if candidate.laneRole != "pathHistory":
        return
    if card.providerId == "industry" and any(token in sourceText for token in ("snapshot", "kindlist", "taxonomy")):
        raise DriverRegistryError(f"industry snapshot cannot be registered as path history: {candidate.laneId}")
    for factor in card.factors:
        if ("price" in sourceText or card.providerId in {"gov", "market", "price"}) and (
            factor.variableId in _OPERATING_SHOCK_TARGETS
            or factor.variableId.lower() in {"pricechange", "productpricechange"}
        ):
            raise DriverRegistryError("equity price history cannot be registered as operating shock")
        if ("macro" in sourceText or card.providerId == "macro") and factor.timing == "level":
            raise DriverRegistryError(f"macro level must be transformed before registry admission: {candidate.laneId}")
        if card.providerId in {"dart", "edgar"} and factor.timing == "level":
            unit = factor.unit.lower()
            if unit in _FINANCIAL_RATIO_UNITS:
                raise DriverRegistryError(
                    f"financial ratio level must remain state or observed feature: {candidate.laneId}"
                )


def _validateAsKnownFiling(candidate: DriverRegistryCandidate) -> None:
    card = _sourceCard(candidate.source)
    if not isinstance(candidate.source, DriverHistorySource) or card.historyStatus != "asKnown":
        return
    if card.providerId not in {"dart", "edgar"}:
        return
    refs = tuple(ref.lower() for ref in card.sourceRefs)
    needs = ("sourcereceiptref:", "filingtrace:", "filingidcolumn:")
    if not all(any(ref.startswith(prefix) for ref in refs) for prefix in needs):
        raise DriverRegistryError(
            f"asKnown filing source needs sourceReceiptRef, filingTrace, and filing id: {candidate.laneId}"
        )


def _validateCandidates(
    candidates: tuple[DriverRegistryCandidate, ...],
) -> tuple[tuple[DriverHistorySource | DriverAssumptionSource, ...], tuple[str, ...], tuple[str, ...]]:
    if not candidates:
        raise DriverRegistryError("driver registry needs at least one candidate")
    laneIds = tuple(candidate.laneId for candidate in candidates)
    if len(set(laneIds)) != len(laneIds):
        raise DriverRegistryError("driver registry lane ids must be unique")
    sources: list[DriverHistorySource | DriverAssumptionSource] = []
    semanticRefs: list[str] = []
    warnings: list[str] = []
    for candidate in candidates:
        _validateRole(candidate)
        _validateFactorSemantics(candidate)
        _validateAsKnownFiling(candidate)
        card = _sourceCard(candidate.source)
        sources.append(candidate.source)
        semanticRefs.extend(candidate.semanticRefs)
        warnings.extend(card.warnings)
        if isinstance(candidate.source, DriverHistorySource) and card.historyStatus != "asKnown":
            warnings.append("driverRegistryContainsRevisedHistory")
        if isinstance(candidate.source, DriverAssumptionSource):
            warnings.append("driverRegistryContainsExplicitAssumption")
    return tuple(sources), _dedupe(tuple(semanticRefs)), tuple(sorted(set(warnings)))


def _historyEvents(
    candidate: DriverRegistryCandidate,
    *,
    knowledgeAsOf: str,
) -> tuple[str, ...]:
    if not isinstance(candidate.source, DriverHistorySource):
        return ()
    source = candidate.source
    card = source.card
    required = {"eventTime", "availableAt", *(_sourceColumn(factor) for factor in card.factors)}
    if not required.issubset(source.panel.columns):
        raise DriverRegistryError(
            f"registry history panel missing columns for {candidate.laneId}: {sorted(required - set(source.panel.columns))}"
        )
    cutoff = _dateText(knowledgeAsOf, "knowledgeAsOf")
    valueExprs = [
        pl.col(_sourceColumn(factor)).cast(pl.Float64, strict=False).alias(factor.variableId) for factor in card.factors
    ]
    variableIds = [factor.variableId for factor in card.factors]
    dated = source.panel.with_columns(
        pl.col("eventTime").cast(pl.Utf8).str.replace_all("-", "").str.slice(0, 8).alias("__event"),
        pl.col("availableAt").cast(pl.Utf8).str.replace_all("-", "").str.slice(0, 8).alias("__available"),
        *valueExprs,
    )
    malformed = dated.filter(
        pl.col("__event").is_null()
        | pl.col("__available").is_null()
        | (pl.col("__event").str.len_chars() != 8)
        | (pl.col("__available").str.len_chars() != 8)
        | ~pl.col("__event").str.contains(r"^\d{8}$")
        | ~pl.col("__available").str.contains(r"^\d{8}$")
    )
    if malformed.height:
        raise DriverRegistryError(f"registry history panel contains malformed dates: {candidate.laneId}")
    frame = (
        dated.filter((pl.col("__event") <= cutoff) & (pl.col("__available") <= cutoff))
        .select("__event", *variableIds)
        .drop_nulls(variableIds)
        .sort("__event")
        .unique(subset=["__event"], keep="last", maintain_order=True)
    )
    for variableId in variableIds:
        if any(not math.isfinite(float(value)) for value in frame[variableId].to_list()):
            raise DriverRegistryError(
                f"registry history panel contains non-finite values: {candidate.laneId}.{variableId}"
            )
    return tuple(frame["__event"].to_list())


def _supportSummary(
    candidates: tuple[DriverRegistryCandidate, ...],
    *,
    knowledgeAsOf: str,
    minObservations: int,
) -> tuple[int, tuple[tuple[str, int], ...], str, str]:
    histories = tuple(candidate for candidate in candidates if isinstance(candidate.source, DriverHistorySource))
    if not histories:
        return 0, (), "", ""
    eventSets: list[set[str]] = []
    sourceCounts: list[tuple[str, int]] = []
    for candidate in histories:
        events = _historyEvents(candidate, knowledgeAsOf=knowledgeAsOf)
        eventSets.append(set(events))
        sourceCounts.append((candidate.laneId, len(events)))
    common = set.intersection(*eventSets) if eventSets else set()
    if len(common) < minObservations:
        raise DriverRegistryError("common driver support below minObservations")
    ordered = tuple(sorted(common))
    return len(ordered), tuple(sourceCounts), ordered[0], ordered[-1]


def _ensureCertificateEligible(
    candidates: tuple[DriverRegistryCandidate, ...],
    certificate: PathMeasureCertificate | None,
) -> None:
    if certificate is None:
        return
    cards = tuple(_sourceCard(candidate.source) for candidate in candidates)
    warnings = tuple(warning for card in cards for warning in card.warnings)
    hasAssumption = any(isinstance(candidate.source, DriverAssumptionSource) for candidate in candidates)
    if hasAssumption or warnings or any(card.historyStatus != "asKnown" for card in cards):
        raise DriverRegistryError("path certificate requires exact warning-free historical sources")


def compileDriverRegistryPathSet(
    candidates: tuple[DriverRegistryCandidate, ...],
    *,
    registryId: str,
    knowledgeAsOf: str,
    horizon: int,
    pathCount: int,
    blockLength: int,
    seed: int,
    minObservations: int = 30,
    certificate: PathMeasureCertificate | None = None,
) -> DriverRegistryResult:
    """Compile curated driver registry candidates into a path set.

    Args:
        candidates: Candidate lanes with a source plus semantic admission refs.
        registryId: Stable registry id for this curated source set.
        knowledgeAsOf: Decision cutoff used for registry support checks and paths.
        horizon: Number of future steps to generate.
        pathCount: Number of empirical paths when history lanes are present.
        blockLength: Moving-block length for historical joint resampling.
        seed: Deterministic RNG seed for empirical resampling.
        minObservations: Minimum common historical support after all lane filters.
        certificate: Optional path measure certificate. Only exact warning-free histories can carry it.

    Returns:
        ``DriverRegistryResult`` with a ``DriverPathSet`` and registry audit ledger.

    Raises:
        DriverRegistryError: If candidate roles, semantics, support, or admission eligibility fail.

    Example:
        ``result = compileDriverRegistryPathSet((candidate,), registryId="kr-drivers", knowledgeAsOf="20251231", horizon=4, pathCount=64, blockLength=4, seed=7)``
    """

    if not registryId:
        raise DriverRegistryError("driver registry needs registryId")
    if min(horizon, pathCount, blockLength, minObservations) < 1:
        raise DriverRegistryError("driver registry path dimensions must be positive")
    cutoff = _dateText(knowledgeAsOf, "knowledgeAsOf")
    candidateTuple = tuple(candidates)
    sources, semanticRefs, registryWarnings = _validateCandidates(candidateTuple)
    _ensureCertificateEligible(candidateTuple, certificate)
    commonCount, sourceCounts, eventStart, eventEnd = _supportSummary(
        candidateTuple,
        knowledgeAsOf=cutoff,
        minObservations=minObservations,
    )
    registryHash = canonicalPayloadHash(
        {
            "registryVersion": REGISTRY_VERSION,
            "registryId": registryId,
            "knowledgeAsOf": cutoff,
            "candidates": tuple(_candidatePayload(candidate) for candidate in candidateTuple),
            "commonObservationCount": commonCount,
            "sourceObservationCounts": sourceCounts,
        }
    )
    pathSet = buildDriverPathSet(
        sources,
        knowledgeAsOf=cutoff,
        horizon=horizon,
        pathCount=pathCount,
        blockLength=blockLength,
        seed=seed,
        minObservations=minObservations,
        certificate=certificate,
    )
    cards = tuple(_sourceCard(candidate.source) for candidate in candidateTuple)
    factorIds = tuple(factor.variableId for card in cards for factor in card.factors)
    sourceRefs = _dedupe(tuple(ref for card in cards for ref in card.sourceRefs))
    warnings = tuple(sorted(set((*registryWarnings, *pathSet.audit.warnings))))
    audit = DriverRegistryAudit(
        registryId=registryId,
        registryHash=registryHash,
        registryVersion=REGISTRY_VERSION,
        knowledgeAsOf=cutoff,
        laneIds=tuple(candidate.laneId for candidate in candidateTuple),
        cardIds=tuple(card.cardId for card in cards),
        factorIds=factorIds,
        commonObservationCount=commonCount,
        sourceObservationCounts=sourceCounts,
        eventStart=eventStart,
        eventEnd=eventEnd,
        sourceRefs=sourceRefs,
        semanticRefs=semanticRefs,
        warnings=warnings,
        pathSetHash=pathSet.audit.pathSetHash,
        pathSetInputHash=pathSet.audit.inputHash,
        validationStatus=pathSet.audit.validationStatus,
        historyStatus=pathSet.audit.historyStatus,
    )
    return DriverRegistryResult(pathSet=pathSet, audit=audit)
