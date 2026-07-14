"""Discover and register safe driver sources before path generation.

The registry is an internal safety gate between workbench source adapters and
``driverPaths``. Discovery only selects from already materialized source
objects using explicit lane specs. It does not fetch data, fit coefficients,
issue admission, or recommend policies. It records why a lane is allowed to
behave as a path driver, rejects state snapshots and semantic laundering, and
then delegates the actual path construction to ``buildDriverPathSet``.
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
DISCOVERY_VERSION = "driver-registry-discovery-v1"
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
class DriverRegistryLaneSpec:
    """Explicit discovery contract for selecting one source card as a lane."""

    laneId: str
    laneRole: str
    providerId: str
    datasetId: str
    entityId: str
    factorIds: tuple[str, ...]
    semanticRefs: tuple[str, ...]
    selectionReason: str
    requiredSourceRefs: tuple[str, ...] = ()
    historyStatus: str = ""
    assumptionId: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "factorIds", tuple(self.factorIds))
        object.__setattr__(self, "semanticRefs", tuple(self.semanticRefs))
        object.__setattr__(self, "requiredSourceRefs", tuple(self.requiredSourceRefs))


@dataclass(frozen=True)
class DriverRegistryDiscoveryRecord:
    """One source discovery decision, including blocked lanes and unmatched source cards."""

    laneId: str
    laneRole: str
    sourceCardId: str
    providerId: str
    datasetId: str
    entityId: str
    factorIds: tuple[str, ...]
    status: str
    blockedReason: str = ""
    selectionReason: str = ""
    semanticRefs: tuple[str, ...] = ()
    sourceRefs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "factorIds", tuple(self.factorIds))
        object.__setattr__(self, "semanticRefs", tuple(self.semanticRefs))
        object.__setattr__(self, "sourceRefs", tuple(self.sourceRefs))


@dataclass(frozen=True)
class DriverRegistryDiscoveryAudit:
    """Audit ledger for source discovery before registry path compilation."""

    discoveryId: str
    discoveryHash: str
    discoveryVersion: str
    knowledgeAsOf: str
    laneSpecHash: str
    sourceSetHash: str
    allowedLaneIds: tuple[str, ...]
    blockedLaneIds: tuple[str, ...]
    unmatchedSourceCardIds: tuple[str, ...]
    allowedCount: int
    blockedCount: int
    allowedRecords: tuple[DriverRegistryDiscoveryRecord, ...]
    blockedRecords: tuple[DriverRegistryDiscoveryRecord, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class DriverRegistryDiscoveryResult:
    """Discovered executable candidates paired with allowed and blocked audit records."""

    candidates: tuple[DriverRegistryCandidate, ...]
    audit: DriverRegistryDiscoveryAudit


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


def _factorIds(card) -> tuple[str, ...]:
    return tuple(factor.variableId for factor in card.factors)


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
    return {
        "laneId": candidate.laneId,
        "laneRole": candidate.laneRole,
        "source": _sourcePayload(candidate.source),
        "semanticRefs": candidate.semanticRefs,
        "selectionReason": candidate.selectionReason,
    }


def _laneSpecPayload(spec: DriverRegistryLaneSpec) -> dict:
    return {
        "laneId": spec.laneId,
        "laneRole": spec.laneRole,
        "providerId": spec.providerId,
        "datasetId": spec.datasetId,
        "entityId": spec.entityId,
        "factorIds": spec.factorIds,
        "semanticRefs": spec.semanticRefs,
        "selectionReason": spec.selectionReason,
        "requiredSourceRefs": spec.requiredSourceRefs,
        "historyStatus": spec.historyStatus,
        "assumptionId": spec.assumptionId,
    }


def _sourcePayload(source: DriverHistorySource | DriverAssumptionSource) -> dict:
    card = _sourceCard(source)
    if isinstance(source, DriverAssumptionSource):
        contentHash = canonicalPayloadHash({"sourceType": "DriverAssumptionSource", "steps": source.steps})
    else:
        columns = tuple(source.panel.columns)
        rows = tuple(tuple(row[column] for column in columns) for row in source.panel.to_dicts())
        contentHash = canonicalPayloadHash({"sourceType": "DriverHistorySource", "columns": columns, "rows": rows})
    return {
        "card": card,
        "sourceType": type(source).__name__,
        "contentHash": contentHash,
    }


def _validateLaneSpec(spec: DriverRegistryLaneSpec) -> None:
    if (
        not spec.laneId
        or spec.laneRole not in _EXECUTABLE_ROLES
        or not spec.providerId
        or not spec.datasetId
        or not spec.entityId
        or not spec.factorIds
        or not spec.semanticRefs
        or not spec.selectionReason
        or any(not ref for ref in spec.requiredSourceRefs)
    ):
        raise DriverRegistryError(f"driver registry lane spec is incomplete: {spec.laneId}")
    if len(set(spec.factorIds)) != len(spec.factorIds):
        raise DriverRegistryError(f"driver registry lane spec factor ids must be unique: {spec.laneId}")


def _roleMatches(source: DriverHistorySource | DriverAssumptionSource, laneRole: str) -> bool:
    return (laneRole == "pathHistory" and isinstance(source, DriverHistorySource)) or (
        laneRole == "explicitAssumption" and isinstance(source, DriverAssumptionSource)
    )


def _matchesLaneIdentity(source: DriverHistorySource | DriverAssumptionSource, spec: DriverRegistryLaneSpec) -> bool:
    if not _roleMatches(source, spec.laneRole):
        return False
    card = _sourceCard(source)
    if (
        card.status != "active"
        or card.providerId != spec.providerId
        or card.datasetId != spec.datasetId
        or card.entityId != spec.entityId
        or _factorIds(card) != spec.factorIds
    ):
        return False
    if spec.historyStatus and card.historyStatus != spec.historyStatus:
        return False
    if spec.assumptionId and card.assumptionId != spec.assumptionId:
        return False
    return True


def _missingRequiredRefs(card, spec: DriverRegistryLaneSpec) -> tuple[str, ...]:
    refs = tuple(str(ref).lower() for ref in card.sourceRefs)
    missing = []
    for required in spec.requiredSourceRefs:
        requiredText = str(required).lower()
        if requiredText.endswith(":"):
            if not any(ref.startswith(requiredText) for ref in refs):
                missing.append(required)
        elif requiredText not in refs:
            missing.append(required)
    return tuple(missing)


def _allowedDiscoveryRecord(
    spec: DriverRegistryLaneSpec,
    card,
    *,
    semanticRefs: tuple[str, ...],
) -> DriverRegistryDiscoveryRecord:
    return DriverRegistryDiscoveryRecord(
        laneId=spec.laneId,
        laneRole=spec.laneRole,
        sourceCardId=card.cardId,
        providerId=card.providerId,
        datasetId=card.datasetId,
        entityId=card.entityId,
        factorIds=_factorIds(card),
        status="allowed",
        selectionReason=spec.selectionReason,
        semanticRefs=semanticRefs,
        sourceRefs=card.sourceRefs,
    )


def _blockedLaneRecord(
    spec: DriverRegistryLaneSpec,
    *,
    reason: str,
    card=None,
) -> DriverRegistryDiscoveryRecord:
    return DriverRegistryDiscoveryRecord(
        laneId=spec.laneId,
        laneRole=spec.laneRole,
        sourceCardId=card.cardId if card is not None else "",
        providerId=card.providerId if card is not None else spec.providerId,
        datasetId=card.datasetId if card is not None else spec.datasetId,
        entityId=card.entityId if card is not None else spec.entityId,
        factorIds=_factorIds(card) if card is not None else spec.factorIds,
        status="blocked",
        blockedReason=reason,
        selectionReason=spec.selectionReason,
        semanticRefs=spec.semanticRefs,
        sourceRefs=card.sourceRefs if card is not None else (),
    )


def _blockedUnmatchedSourceRecord(
    source: DriverHistorySource | DriverAssumptionSource,
) -> DriverRegistryDiscoveryRecord:
    card = _sourceCard(source)
    return DriverRegistryDiscoveryRecord(
        laneId="",
        laneRole=card.sourceKind,
        sourceCardId=card.cardId,
        providerId=card.providerId,
        datasetId=card.datasetId,
        entityId=card.entityId,
        factorIds=_factorIds(card),
        status="blocked",
        blockedReason="sourceNotMatchedByLaneSpec",
        sourceRefs=card.sourceRefs,
    )


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


def discoverDriverRegistryCandidates(
    sources: tuple[DriverHistorySource | DriverAssumptionSource, ...],
    laneSpecs: tuple[DriverRegistryLaneSpec, ...],
) -> tuple[DriverRegistryCandidate, ...]:
    """Select exact source cards for explicit registry lane specs.

    Args:
        sources: Already materialized driver sources from workbench adapters or explicit assumptions.
        laneSpecs: Lane contracts that declare provider, dataset, entity, factors, refs, and semantics.

    Returns:
        Ordered ``DriverRegistryCandidate`` values with discovery trace refs in ``semanticRefs``.

    Raises:
        DriverRegistryError: If a lane is missing, ambiguous, incomplete, or lacks required refs.

    Example:
        ``candidates = discoverDriverRegistryCandidates((source,), (laneSpec,))``
    """

    sourceTuple = tuple(sources)
    specTuple = tuple(laneSpecs)
    if not sourceTuple or not specTuple:
        raise DriverRegistryError("driver registry discovery needs sources and lane specs")
    laneIds = tuple(spec.laneId for spec in specTuple)
    if len(set(laneIds)) != len(laneIds):
        raise DriverRegistryError("driver registry discovery lane ids must be unique")
    selectedCardIds: set[str] = set()
    candidates: list[DriverRegistryCandidate] = []
    for spec in specTuple:
        _validateLaneSpec(spec)
        identityMatches = tuple(source for source in sourceTuple if _matchesLaneIdentity(source, spec))
        if not identityMatches:
            raise DriverRegistryError(f"driver registry discovery missing source for lane: {spec.laneId}")
        refCompleteMatches = tuple(
            source for source in identityMatches if not _missingRequiredRefs(_sourceCard(source), spec)
        )
        if not refCompleteMatches:
            missingRefs = _missingRequiredRefs(_sourceCard(identityMatches[0]), spec)
            raise DriverRegistryError(
                f"driver registry discovery missing required sourceRefs: {spec.laneId}: {missingRefs}"
            )
        if len(refCompleteMatches) > 1:
            raise DriverRegistryError(f"ambiguous driver registry discovery for lane: {spec.laneId}")
        source = refCompleteMatches[0]
        card = _sourceCard(source)
        if card.cardId in selectedCardIds:
            raise DriverRegistryError(f"driver registry discovery reuses one source card: {card.cardId}")
        selectedCardIds.add(card.cardId)
        discoveryHash = canonicalPayloadHash(
            {
                "discoveryVersion": DISCOVERY_VERSION,
                "laneSpec": _laneSpecPayload(spec),
                "source": _sourcePayload(source),
            }
        )
        candidates.append(
            DriverRegistryCandidate(
                spec.laneId,
                spec.laneRole,
                source,
                semanticRefs=_dedupe(
                    (*spec.semanticRefs, f"sourceCard:{card.cardId}", f"driverDiscovery:{discoveryHash}")
                ),
                selectionReason=f"{spec.selectionReason} sourceCard={card.cardId}",
            )
        )
    return tuple(candidates)


def auditDriverRegistryDiscovery(
    sources: tuple[DriverHistorySource | DriverAssumptionSource, ...],
    laneSpecs: tuple[DriverRegistryLaneSpec, ...],
    *,
    discoveryId: str,
    knowledgeAsOf: str,
) -> DriverRegistryDiscoveryResult:
    """Discover executable sources while retaining blocked discovery records.

    Args:
        sources: Already materialized driver sources from workbench adapters or explicit assumptions.
        laneSpecs: Lane contracts that declare which source cards may become executable.
        discoveryId: Stable identifier for this discovery pass.
        knowledgeAsOf: Decision cutoff recorded in the discovery audit.

    Returns:
        ``DriverRegistryDiscoveryResult`` with executable candidates and blocked records.

    Raises:
        DriverRegistryError: If discovery identity, lane spec identity, or source card identity is invalid.

    Example:
        ``result = auditDriverRegistryDiscovery((source,), (laneSpec,), discoveryId="kr-drivers", knowledgeAsOf="20251231")``
    """

    if not discoveryId:
        raise DriverRegistryError("driver registry discovery needs discoveryId")
    cutoff = _dateText(knowledgeAsOf, "knowledgeAsOf")
    sourceTuple = tuple(sources)
    specTuple = tuple(laneSpecs)
    if not sourceTuple or not specTuple:
        raise DriverRegistryError("driver registry discovery needs sources and lane specs")
    laneIds = tuple(spec.laneId for spec in specTuple)
    if len(set(laneIds)) != len(laneIds):
        raise DriverRegistryError("driver registry discovery lane ids must be unique")
    cardIds = tuple(_sourceCard(source).cardId for source in sourceTuple)
    if len(set(cardIds)) != len(cardIds):
        raise DriverRegistryError("driver registry discovery source card ids must be unique")
    for spec in specTuple:
        _validateLaneSpec(spec)
    selectedCardIds: set[str] = set()
    consideredCardIds: set[str] = set()
    candidates: list[DriverRegistryCandidate] = []
    allowedRecords: list[DriverRegistryDiscoveryRecord] = []
    blockedRecords: list[DriverRegistryDiscoveryRecord] = []
    for spec in specTuple:
        identityMatches = tuple(source for source in sourceTuple if _matchesLaneIdentity(source, spec))
        for source in identityMatches:
            consideredCardIds.add(_sourceCard(source).cardId)
        if not identityMatches:
            blockedRecords.append(_blockedLaneRecord(spec, reason="missingSourceForLane"))
            continue
        refCompleteMatches = tuple(
            source for source in identityMatches if not _missingRequiredRefs(_sourceCard(source), spec)
        )
        if not refCompleteMatches:
            blockedRecords.extend(
                _blockedLaneRecord(spec, reason="missingRequiredSourceRefs", card=_sourceCard(source))
                for source in identityMatches
            )
            continue
        if len(refCompleteMatches) > 1:
            blockedRecords.extend(
                _blockedLaneRecord(spec, reason="ambiguousSourceForLane", card=_sourceCard(source))
                for source in refCompleteMatches
            )
            continue
        source = refCompleteMatches[0]
        card = _sourceCard(source)
        if card.cardId in selectedCardIds:
            blockedRecords.append(_blockedLaneRecord(spec, reason="sourceCardAlreadySelected", card=card))
            continue
        discoveryHash = canonicalPayloadHash(
            {
                "discoveryVersion": DISCOVERY_VERSION,
                "discoveryId": discoveryId,
                "knowledgeAsOf": cutoff,
                "laneSpec": _laneSpecPayload(spec),
                "source": _sourcePayload(source),
            }
        )
        semanticRefs = _dedupe((*spec.semanticRefs, f"sourceCard:{card.cardId}", f"driverDiscovery:{discoveryHash}"))
        candidate = DriverRegistryCandidate(
            spec.laneId,
            spec.laneRole,
            source,
            semanticRefs=semanticRefs,
            selectionReason=f"{spec.selectionReason} sourceCard={card.cardId}",
        )
        candidates.append(candidate)
        allowedRecords.append(_allowedDiscoveryRecord(spec, card, semanticRefs=semanticRefs))
        selectedCardIds.add(card.cardId)
    unmatched = tuple(
        source for source in sourceTuple if _sourceCard(source).cardId not in consideredCardIds | selectedCardIds
    )
    blockedRecords.extend(_blockedUnmatchedSourceRecord(source) for source in unmatched)
    blockedLaneIds = _dedupe(tuple(record.laneId for record in blockedRecords if record.laneId))
    unmatchedSourceCardIds = _dedupe(
        tuple(record.sourceCardId for record in blockedRecords if record.blockedReason == "sourceNotMatchedByLaneSpec")
    )
    laneSpecHash = canonicalPayloadHash(tuple(_laneSpecPayload(spec) for spec in specTuple))
    sourceSetHash = canonicalPayloadHash(tuple(_sourcePayload(source) for source in sourceTuple))
    discoveryHash = canonicalPayloadHash(
        {
            "discoveryVersion": DISCOVERY_VERSION,
            "discoveryId": discoveryId,
            "knowledgeAsOf": cutoff,
            "laneSpecHash": laneSpecHash,
            "sourceSetHash": sourceSetHash,
            "allowedRecords": tuple(allowedRecords),
            "blockedRecords": tuple(blockedRecords),
        }
    )
    warnings = ("driverDiscoveryBlockedCandidates",) if blockedRecords else ()
    audit = DriverRegistryDiscoveryAudit(
        discoveryId=discoveryId,
        discoveryHash=discoveryHash,
        discoveryVersion=DISCOVERY_VERSION,
        knowledgeAsOf=cutoff,
        laneSpecHash=laneSpecHash,
        sourceSetHash=sourceSetHash,
        allowedLaneIds=tuple(record.laneId for record in allowedRecords),
        blockedLaneIds=blockedLaneIds,
        unmatchedSourceCardIds=unmatchedSourceCardIds,
        allowedCount=len(allowedRecords),
        blockedCount=len(blockedRecords),
        allowedRecords=tuple(allowedRecords),
        blockedRecords=tuple(blockedRecords),
        warnings=warnings,
    )
    return DriverRegistryDiscoveryResult(tuple(candidates), audit)


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
