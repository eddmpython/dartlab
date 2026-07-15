"""Compile driver cards and explicit assumptions into typed scenario paths.

This module is the path generation coordinator for the simulator. It does not
admit paths, fit causal laws, or recommend strategies. It freezes historical
driver panels on a common event grid, overlays first-class explicit assumptions,
and returns ``ScenarioPath`` objects plus factor meaning contracts that can be
fed into bridge layers such as ``operatingBridge``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping

import polars as pl

from dartlab.simulate.empiricalPaths import (
    EmpiricalPathError,
    EmpiricalPathSet,
    PathMeasureCertificate,
    PathVariable,
    buildJointBlockPaths,
)
from dartlab.simulate.operatingBridge import OperatingFactorSpec
from dartlab.simulate.vintage import canonicalPayloadHash
from dartlab.simulate.world import ScenarioPath, pathSetAdmissionSubjectHash

GENERATOR_VERSION = "driver-path-registry-v1"
_SOURCE_KINDS = {"history", "explicitAssumption"}
_CARD_STATUSES = {"active", "blocked", "rejected"}
_FACTOR_TIMINGS = {"innovation", "change", "level", "rate"}
_ADMISSION_REF_PREFIXES = ("pathAdmission:", "pathSetAdmission:", "policyEvaluation:", "policyCertificate:")


class DriverPathError(ValueError):
    """Raised when driver cards, history, or explicit assumptions cannot form a path set."""


@dataclass(frozen=True)
class DriverFactorSpec:
    """One source factor and its executable meaning contract."""

    variableId: str
    unit: str
    frequency: str
    timing: str
    transformId: str
    sourceColumn: str = ""


@dataclass(frozen=True)
class DriverCard:
    """Data card that admits one history or explicit-assumption source into path generation."""

    cardId: str
    sourceKind: str
    providerId: str
    datasetId: str
    entityId: str
    frequency: str
    stepSpan: int
    factors: tuple[DriverFactorSpec, ...]
    historyStatus: str
    sourceRefs: tuple[str, ...]
    status: str = "active"
    assumptionId: str = ""
    claim: str = ""
    falsifier: str = ""
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "factors", tuple(self.factors))
        object.__setattr__(self, "sourceRefs", tuple(self.sourceRefs))
        object.__setattr__(self, "warnings", tuple(self.warnings))


@dataclass(frozen=True)
class DriverHistorySource:
    """Historical source panel for one driver card."""

    card: DriverCard
    panel: pl.DataFrame


@dataclass(frozen=True)
class DriverAssumptionSource:
    """Explicit assumption steps for one driver card."""

    card: DriverCard
    steps: tuple[Mapping[str, float], ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "steps", tuple(dict(step) for step in self.steps))


@dataclass(frozen=True)
class DriverPathAudit:
    """Auditable path generation ledger."""

    pathSetHash: str
    inputHash: str
    historyInputHash: str
    assumptionHash: str
    assumptionStepHashes: tuple[str, ...]
    basePathSetHash: str
    basePathAdmissionReceiptId: str
    basePathAdmissionContentHash: str
    basePathAdmissionSubjectHash: str
    basePathValidationStatus: str
    basePathMaxAdmittedStep: int
    overlayHash: str
    registryHash: str
    factorContractHash: str
    generatorVersion: str
    knowledgeAsOf: str
    frequency: str
    stepSpan: int
    horizon: int
    pathCount: int
    blockLength: int
    seed: int
    driverCardIds: tuple[str, ...]
    assumptionDescriptors: tuple[tuple[str, str, str, str], ...]
    validationStatus: str
    observedHistoryStatus: str
    historyStatus: str
    sourceRefs: tuple[str, ...]
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "assumptionStepHashes", tuple(self.assumptionStepHashes))
        object.__setattr__(self, "driverCardIds", tuple(self.driverCardIds))
        object.__setattr__(
            self,
            "assumptionDescriptors",
            tuple(tuple(item) for item in self.assumptionDescriptors),
        )
        object.__setattr__(self, "sourceRefs", tuple(self.sourceRefs))
        object.__setattr__(self, "warnings", tuple(self.warnings))


@dataclass(frozen=True)
class DriverPathSet:
    """Generated driver path set and its factor contracts."""

    paths: tuple[ScenarioPath, ...]
    factorSpecs: tuple[DriverFactorSpec, ...]
    audit: DriverPathAudit


def _dateText(value: str, label: str) -> str:
    text = str(value).replace("-", "")[:8]
    if len(text) != 8 or not text.isdigit():
        raise DriverPathError(f"invalid {label}: {value}")
    return text


def _finite(value: float | None, label: str) -> float:
    if value is None:
        raise DriverPathError(f"{label} is missing")
    number = float(value)
    if not math.isfinite(number):
        raise DriverPathError(f"{label} must be finite")
    return number


def _dedupe(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value))


def _validDigest(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value.lower())


def _dropAdmissionRefs(refs: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(ref for ref in refs if not ref.startswith(_ADMISSION_REF_PREFIXES))


def _sourceColumn(factor: DriverFactorSpec) -> str:
    return factor.sourceColumn or factor.variableId


def _cardPayload(card: DriverCard) -> dict:
    return {
        "cardId": card.cardId,
        "sourceKind": card.sourceKind,
        "providerId": card.providerId,
        "datasetId": card.datasetId,
        "entityId": card.entityId,
        "frequency": card.frequency,
        "stepSpan": card.stepSpan,
        "factors": card.factors,
        "historyStatus": card.historyStatus,
        "sourceRefs": card.sourceRefs,
        "status": card.status,
        "assumptionId": card.assumptionId,
        "claim": card.claim,
        "falsifier": card.falsifier,
        "warnings": card.warnings,
    }


def _validateCard(card: DriverCard, expectedKind: str) -> None:
    if (
        not card.cardId
        or card.sourceKind not in _SOURCE_KINDS
        or card.sourceKind != expectedKind
        or not card.providerId
        or not card.datasetId
        or not card.entityId
        or not card.frequency
        or card.stepSpan < 1
        or not card.historyStatus
        or not card.sourceRefs
        or card.status not in _CARD_STATUSES
        or not card.factors
    ):
        raise DriverPathError(f"driver card contract is incomplete: {card.cardId}")
    if card.status != "active":
        raise DriverPathError(f"driver card is not executable: {card.cardId}")
    factorIds = [factor.variableId for factor in card.factors]
    if len(set(factorIds)) != len(factorIds):
        raise DriverPathError(f"driver card factor ids must be unique: {card.cardId}")
    sourceColumns = [_sourceColumn(factor) for factor in card.factors]
    if expectedKind == "history" and len(set(sourceColumns)) != len(sourceColumns):
        raise DriverPathError(f"driver card source columns must be unique: {card.cardId}")
    for factor in card.factors:
        if (
            not factor.variableId
            or not factor.unit
            or factor.frequency != card.frequency
            or factor.timing not in _FACTOR_TIMINGS
            or not factor.transformId
        ):
            raise DriverPathError(f"driver factor contract is incomplete: {factor.variableId}")
    if expectedKind == "explicitAssumption" and (not card.assumptionId or not card.claim or not card.falsifier):
        raise DriverPathError(f"explicit assumption needs id, claim, and falsifier: {card.cardId}")


def _collectSources(
    sources: tuple[DriverHistorySource | DriverAssumptionSource, ...],
) -> tuple[tuple[DriverHistorySource, ...], tuple[DriverAssumptionSource, ...], tuple[DriverCard, ...]]:
    histories: list[DriverHistorySource] = []
    assumptions: list[DriverAssumptionSource] = []
    cards: list[DriverCard] = []
    for source in sources:
        if isinstance(source, DriverHistorySource):
            _validateCard(source.card, "history")
            histories.append(source)
            cards.append(source.card)
        elif isinstance(source, DriverAssumptionSource):
            _validateCard(source.card, "explicitAssumption")
            assumptions.append(source)
            cards.append(source.card)
        else:
            raise DriverPathError("unknown driver path source")
    if not cards:
        raise DriverPathError("driver path set needs at least one source")
    if len({card.cardId for card in cards}) != len(cards):
        raise DriverPathError("driver card ids must be unique")
    factorIds = [factor.variableId for card in cards for factor in card.factors]
    if len(set(factorIds)) != len(factorIds):
        raise DriverPathError("driver factor ids must be globally unique")
    frequencies = {card.frequency for card in cards}
    spans = {card.stepSpan for card in cards}
    if len(frequencies) != 1 or len(spans) != 1:
        raise DriverPathError("driver cards must share one step contract")
    return tuple(histories), tuple(assumptions), tuple(cards)


def _historyFrame(source: DriverHistorySource, *, knowledgeAsOf: str, index: int) -> pl.DataFrame:
    card = source.card
    required = {"eventTime", "availableAt", *(_sourceColumn(factor) for factor in card.factors)}
    if not required.issubset(source.panel.columns):
        raise DriverPathError(
            f"history panel missing columns for {card.cardId}: {sorted(required - set(source.panel.columns))}"
        )
    cutoff = _dateText(knowledgeAsOf, "knowledgeAsOf")
    dated = source.panel.with_columns(
        pl.col("eventTime").cast(pl.Utf8).str.replace_all("-", "").str.slice(0, 8).alias("__event"),
        pl.col("availableAt").cast(pl.Utf8).str.replace_all("-", "").str.slice(0, 8).alias("__available"),
    )
    malformed = dated.filter(
        (pl.col("__event").str.len_chars() != 8)
        | (pl.col("__available").str.len_chars() != 8)
        | ~pl.col("__event").str.contains(r"^\d{8}$")
        | ~pl.col("__available").str.contains(r"^\d{8}$")
    )
    if malformed.height:
        raise DriverPathError(f"history panel contains malformed dates: {card.cardId}")
    factorExprs = [
        pl.col(_sourceColumn(factor)).cast(pl.Float64, strict=False).alias(factor.variableId) for factor in card.factors
    ]
    variableIds = [factor.variableId for factor in card.factors]
    frame = (
        dated.filter((pl.col("__event") <= cutoff) & (pl.col("__available") <= cutoff))
        .select("__event", "__available", *factorExprs)
        .drop_nulls(variableIds)
        .sort(["__event", "__available"])
        .unique(subset=["__event"], keep="last", maintain_order=True)
        .rename({"__available": f"__available{index}"})
    )
    for variableId in variableIds:
        if any(not math.isfinite(float(value)) for value in frame[variableId].to_list()):
            raise DriverPathError(f"history panel contains non-finite values: {card.cardId}.{variableId}")
    return frame


def _joinedHistoryPanel(
    sources: tuple[DriverHistorySource, ...],
    *,
    knowledgeAsOf: str,
) -> tuple[pl.DataFrame | None, tuple[PathVariable, ...], str, str]:
    if not sources:
        return None, (), "", ""
    frames = [_historyFrame(source, knowledgeAsOf=knowledgeAsOf, index=index) for index, source in enumerate(sources)]
    joined = frames[0]
    for frame in frames[1:]:
        joined = joined.join(frame, on="__event", how="inner")
    availabilityColumns = [f"__available{index}" for index in range(len(frames))]
    variableIds = [factor.variableId for source in sources for factor in source.card.factors]
    panel = joined.with_columns(
        pl.max_horizontal(*(pl.col(column) for column in availabilityColumns)).alias("availableAt"),
        pl.col("__event").alias("eventTime"),
    ).select("eventTime", "availableAt", *variableIds)
    variables = tuple(
        PathVariable(factor.variableId, factor.variableId, factor.unit)
        for source in sources
        for factor in source.card.factors
    )
    historyStatuses = {source.card.historyStatus for source in sources}
    historyStatus = "asKnown" if historyStatuses == {"asKnown"} else "revisedHistory"
    historyInputHash = canonicalPayloadHash(
        {
            "cards": tuple(_cardPayload(source.card) for source in sources),
            "rows": panel.to_dicts(),
        }
    )
    return panel, variables, historyStatus, historyInputHash


def _assumptionPayload(source: DriverAssumptionSource, horizon: int) -> dict:
    card = source.card
    if len(source.steps) != horizon:
        raise DriverPathError(f"explicit assumption horizon mismatch: {card.cardId}")
    expected = {factor.variableId for factor in card.factors}
    steps = []
    for stepIndex, step in enumerate(source.steps):
        if set(step) != expected:
            raise DriverPathError(f"explicit assumption factor coverage drift: {card.cardId}.{stepIndex}")
        steps.append(
            {
                variableId: _finite(value, f"{card.cardId}.{variableId}.{stepIndex}")
                for variableId, value in step.items()
            }
        )
    return {"card": _cardPayload(card), "steps": tuple(steps)}


def _assumptionSteps(
    sources: tuple[DriverAssumptionSource, ...],
    horizon: int,
) -> tuple[tuple[dict[str, float], ...], str, tuple[str, ...]]:
    if not sources:
        return tuple({} for _ in range(horizon)), "", ()
    payloads = tuple(_assumptionPayload(source, horizon) for source in sources)
    steps: list[dict[str, float]] = []
    for stepIndex in range(horizon):
        merged: dict[str, float] = {}
        for payload in payloads:
            merged.update(payload["steps"][stepIndex])
        steps.append(merged)
    assumptionStepHashes = tuple(
        canonicalPayloadHash(
            {
                "schemaVersion": "driver-path-assumption-step-v1",
                "stepIndex": stepIndex,
                "sources": tuple(
                    {
                        "card": payload["card"],
                        "step": payload["steps"][stepIndex],
                    }
                    for payload in payloads
                ),
            }
        )
        for stepIndex in range(horizon)
    )
    assumptionHash = canonicalPayloadHash(
        {
            "schemaVersion": "driver-path-assumption-set-v1",
            "assumptionStepHashes": assumptionStepHashes,
            "payloads": payloads,
        }
    )
    return tuple(steps), assumptionHash, assumptionStepHashes


def _assumptionDescriptors(sources: tuple[DriverAssumptionSource, ...]) -> tuple[tuple[str, str, str, str], ...]:
    return tuple(
        (factor.variableId, source.card.assumptionId, source.card.claim, source.card.falsifier)
        for source in sources
        for factor in source.card.factors
    )


def _pathSetHash(paths: tuple[ScenarioPath, ...]) -> str:
    return canonicalPayloadHash(
        tuple(
            {
                "pathId": path.pathId,
                "steps": tuple(dict(step) for step in path.steps),
                "weight": path.weight,
                "weightKind": path.weightKind,
                "refs": path.refs,
                "frequency": path.frequency,
                "stepSpan": path.stepSpan,
                "validationStatus": path.validationStatus,
                "knowledgeAsOf": path.knowledgeAsOf,
                "historyStatus": path.historyStatus,
                "parameterDraws": dict(path.parameterDraws),
                "parameterDrawReceipt": path.parameterDrawReceipt,
                "certificateId": path.certificateId,
                "maxAdmittedStep": path.maxAdmittedStep,
                "admissionContentHash": path.admissionContentHash,
                "admissionReceiptId": path.admissionReceiptId,
                "vintage": path.vintage,
            }
            for path in paths
        )
    )


def _basePathAdmissionFields(paths: tuple[ScenarioPath, ...]) -> tuple[str, str, str, str, int]:
    if not paths:
        return "", "", "", "", 0
    validationStatuses = {path.validationStatus for path in paths}
    validationStatus = next(iter(validationStatuses)) if len(validationStatuses) == 1 else "mixed"
    maxAdmittedSteps = {int(path.maxAdmittedStep) for path in paths}
    maxAdmittedStep = next(iter(maxAdmittedSteps)) if len(maxAdmittedSteps) == 1 else 0
    if validationStatuses != {"admitted"}:
        return "", "", "", validationStatus, maxAdmittedStep
    receiptIds = {path.admissionReceiptId for path in paths}
    contentHashes = {path.admissionContentHash for path in paths}
    if len(receiptIds) != 1 or len(contentHashes) != 1:
        return "", "", "", validationStatus, maxAdmittedStep
    receiptId = next(iter(receiptIds))
    contentHash = next(iter(contentHashes))
    subjectHash = pathSetAdmissionSubjectHash(paths)
    if not _validDigest(receiptId) or contentHash != subjectHash or not _validDigest(subjectHash):
        return "", "", "", validationStatus, maxAdmittedStep
    return receiptId, contentHash, subjectHash, validationStatus, maxAdmittedStep


def _overlayHash(
    *,
    assumptionHash: str,
    assumptionSteps: tuple[dict[str, float], ...],
    sourceRefs: tuple[str, ...],
    horizon: int,
) -> str:
    if not assumptionHash:
        return ""
    return canonicalPayloadHash(
        {
            "schemaVersion": "driver-path-explicit-overlay-v1",
            "assumptionHash": assumptionHash,
            "assumptionSteps": assumptionSteps,
            "sourceRefs": sourceRefs,
            "horizon": horizon,
        }
    )


def _makeExplicitOnlyPath(
    *,
    steps: tuple[dict[str, float], ...],
    refs: tuple[str, ...],
    frequency: str,
    stepSpan: int,
    knowledgeAsOf: str,
    registryHash: str,
    assumptionHash: str,
) -> ScenarioPath:
    return ScenarioPath(
        f"driver-explicit-{assumptionHash[:12]}",
        steps,
        refs=_dedupe((*refs, f"driverRegistry:{registryHash}")),
        frequency=frequency,
        stepSpan=stepSpan,
        validationStatus="unvalidated",
        knowledgeAsOf=_dateText(knowledgeAsOf, "knowledgeAsOf"),
        historyStatus="explicitAssumption",
    )


def _overlayAssumptions(
    paths: tuple[ScenarioPath, ...],
    *,
    assumptionSteps: tuple[dict[str, float], ...],
    refs: tuple[str, ...],
    registryHash: str,
    assumptionHash: str,
    validationStatus: str,
    historyStatus: str,
) -> tuple[ScenarioPath, ...]:
    out: list[ScenarioPath] = []
    for path in paths:
        mergedSteps = tuple({**dict(step), **assumptionSteps[index]} for index, step in enumerate(path.steps))
        pathId = f"driver-{path.pathId}" if not assumptionHash else f"driver-{path.pathId}-{assumptionHash[:12]}"
        out.append(
            ScenarioPath(
                pathId,
                mergedSteps,
                weight=path.weight,
                weightKind=path.weightKind,
                refs=_dedupe((*_dropAdmissionRefs(path.refs), *refs, f"driverRegistry:{registryHash}")),
                frequency=path.frequency,
                stepSpan=path.stepSpan,
                certificateId="",
                validationStatus=validationStatus,
                maxAdmittedStep=0,
                parameterDraws={},
                parameterDrawReceipt=None,
                knowledgeAsOf=path.knowledgeAsOf,
                historyStatus=historyStatus,
                vintage=path.vintage,
            )
        )
    return tuple(out)


def composeDriverPathSetWithAssumptions(
    basePathSet: DriverPathSet,
    assumptions: tuple[DriverAssumptionSource, ...],
    *,
    registryId: str = "",
) -> DriverPathSet:
    """Overlay explicit future assumptions onto a history-only driver path set.

    Args:
        basePathSet: History-only path set, optionally already admitted.
        assumptions: Explicit future assumption sources with the same horizon.
        registryId: Optional stable id for the composition audit.

    Returns:
        Conditional composed ``DriverPathSet`` whose base admission remains parent
        lineage only and never transfers to composed paths.

    Raises:
        DriverPathError: If the base path set or assumption contracts are unsafe.

    Example:
        ``composed = composeDriverPathSetWithAssumptions(admittedBase, (assumption,))``
    """

    if basePathSet.audit.assumptionHash:
        raise DriverPathError("base path set must be history-only")
    assumptionTuple = tuple(assumptions)
    if not assumptionTuple:
        raise DriverPathError("explicit overlay needs at least one assumption source")
    if not basePathSet.paths or not basePathSet.factorSpecs:
        raise DriverPathError("base path set is empty")
    horizon = len(basePathSet.paths[0].steps)
    if horizon != basePathSet.audit.horizon or any(len(path.steps) != horizon for path in basePathSet.paths):
        raise DriverPathError("base path set horizon drift")
    cards: list[DriverCard] = []
    for source in assumptionTuple:
        _validateCard(source.card, "explicitAssumption")
        cards.append(source.card)
    if any(
        card.frequency != basePathSet.audit.frequency or card.stepSpan != basePathSet.audit.stepSpan for card in cards
    ):
        raise DriverPathError("explicit overlay step contract mismatch")
    baseFactorIds = {factor.variableId for factor in basePathSet.factorSpecs}
    assumptionFactorIds = [factor.variableId for card in cards for factor in card.factors]
    if len(set(assumptionFactorIds)) != len(assumptionFactorIds) or baseFactorIds.intersection(assumptionFactorIds):
        raise DriverPathError("explicit overlay factor ids must not overwrite observed history")
    assumptionStepTuple, assumptionHash, assumptionStepHashes = _assumptionSteps(assumptionTuple, horizon)
    factorSpecs = (*basePathSet.factorSpecs, *(factor for card in cards for factor in card.factors))
    factorContractHash = canonicalPayloadHash(
        tuple(
            (factor.variableId, factor.unit, factor.frequency, factor.timing, factor.transformId)
            for factor in sorted(factorSpecs, key=lambda item: item.variableId)
        )
    )
    assumptionRefs = _dedupe(tuple(ref for card in cards for ref in card.sourceRefs))
    sourceRefs = _dedupe((*basePathSet.audit.sourceRefs, *assumptionRefs))
    basePathSetHash = _pathSetHash(basePathSet.paths)
    (
        basePathAdmissionReceiptId,
        basePathAdmissionContentHash,
        basePathAdmissionSubjectHash,
        basePathValidationStatus,
        basePathMaxAdmittedStep,
    ) = _basePathAdmissionFields(basePathSet.paths)
    registryHash = canonicalPayloadHash(
        {
            "generatorVersion": GENERATOR_VERSION,
            "compositionVersion": "driver-path-explicit-overlay-composition-v1",
            "registryId": registryId,
            "baseRegistryHash": basePathSet.audit.registryHash,
            "basePathSetHash": basePathSetHash,
            "basePathInputHash": basePathSet.audit.inputHash,
            "basePathAdmissionReceiptId": basePathAdmissionReceiptId,
            "assumptionCards": tuple(_cardPayload(card) for card in cards),
            "factorSpecs": factorSpecs,
        }
    )
    paths = _overlayAssumptions(
        basePathSet.paths,
        assumptionSteps=assumptionStepTuple,
        refs=assumptionRefs,
        registryHash=registryHash,
        assumptionHash=assumptionHash,
        validationStatus="unvalidated",
        historyStatus="explicitAssumption",
    )
    overlayHash = _overlayHash(
        assumptionHash=assumptionHash,
        assumptionSteps=assumptionStepTuple,
        sourceRefs=sourceRefs,
        horizon=horizon,
    )
    pathSetHash = _pathSetHash(paths)
    inputHash = canonicalPayloadHash(
        {
            "registryHash": registryHash,
            "historyInputHash": basePathSet.audit.historyInputHash,
            "assumptionHash": assumptionHash,
            "assumptionStepHashes": assumptionStepHashes,
            "basePathSetHash": basePathSetHash,
            "basePathAdmissionReceiptId": basePathAdmissionReceiptId,
            "basePathAdmissionContentHash": basePathAdmissionContentHash,
            "basePathAdmissionSubjectHash": basePathAdmissionSubjectHash,
            "overlayHash": overlayHash,
            "horizon": horizon,
            "pathCount": len(paths),
            "blockLength": basePathSet.audit.blockLength,
            "seed": basePathSet.audit.seed,
        }
    )
    warnings = tuple(
        sorted(
            set(
                (
                    *basePathSet.audit.warnings,
                    *(warning for card in cards for warning in card.warnings),
                    *(f"explicitAssumption:{source.card.assumptionId}" for source in assumptionTuple),
                    "basePathAdmittedButOverlayConditional" if basePathAdmissionReceiptId else "",
                )
            )
            - {""}
        )
    )
    audit = DriverPathAudit(
        pathSetHash=pathSetHash,
        inputHash=inputHash,
        historyInputHash=basePathSet.audit.historyInputHash,
        assumptionHash=assumptionHash,
        assumptionStepHashes=assumptionStepHashes,
        basePathSetHash=basePathSetHash,
        basePathAdmissionReceiptId=basePathAdmissionReceiptId,
        basePathAdmissionContentHash=basePathAdmissionContentHash,
        basePathAdmissionSubjectHash=basePathAdmissionSubjectHash,
        basePathValidationStatus=basePathValidationStatus,
        basePathMaxAdmittedStep=basePathMaxAdmittedStep,
        overlayHash=overlayHash,
        registryHash=registryHash,
        factorContractHash=factorContractHash,
        generatorVersion=GENERATOR_VERSION,
        knowledgeAsOf=basePathSet.audit.knowledgeAsOf,
        frequency=basePathSet.audit.frequency,
        stepSpan=basePathSet.audit.stepSpan,
        horizon=horizon,
        pathCount=len(paths),
        blockLength=basePathSet.audit.blockLength,
        seed=basePathSet.audit.seed,
        driverCardIds=(*basePathSet.audit.driverCardIds, *(card.cardId for card in cards)),
        assumptionDescriptors=(*basePathSet.audit.assumptionDescriptors, *_assumptionDescriptors(assumptionTuple)),
        validationStatus="unvalidated",
        observedHistoryStatus=basePathSet.audit.observedHistoryStatus,
        historyStatus="explicitAssumption",
        sourceRefs=sourceRefs,
        warnings=warnings,
    )
    return DriverPathSet(paths=paths, factorSpecs=factorSpecs, audit=audit)


def driverFactorsToOperatingSpecs(factors: tuple[DriverFactorSpec, ...]) -> tuple[OperatingFactorSpec, ...]:
    """Convert generic driver factors into operating bridge factor specs.

    Args:
        factors: Driver factor contracts produced by ``buildDriverPathSet``.

    Returns:
        Tuple of ``OperatingFactorSpec`` values with identical meaning fields.

    Raises:
        DriverPathError: If factor identifiers are duplicated or incomplete.

    Example:
        ``factorSpecs = driverFactorsToOperatingSpecs(pathSet.factorSpecs)``
    """

    if not factors or len({factor.variableId for factor in factors}) != len(factors):
        raise DriverPathError("operating factor conversion needs unique factors")
    specs = []
    for factor in factors:
        if (
            not factor.variableId
            or not factor.unit
            or not factor.frequency
            or factor.timing not in _FACTOR_TIMINGS
            or not factor.transformId
        ):
            raise DriverPathError(f"driver factor contract is incomplete: {factor.variableId}")
        specs.append(
            OperatingFactorSpec(
                factor.variableId,
                factor.unit,
                factor.frequency,
                factor.timing,
                factor.transformId,
            )
        )
    return tuple(specs)


def buildDriverPathSet(
    sources: tuple[DriverHistorySource | DriverAssumptionSource, ...],
    *,
    knowledgeAsOf: str,
    horizon: int,
    pathCount: int,
    blockLength: int,
    seed: int,
    minObservations: int = 30,
    certificate: PathMeasureCertificate | None = None,
) -> DriverPathSet:
    """Build typed factor paths from history cards and explicit assumptions.

    Args:
        sources: History and explicit-assumption cards to compile on one step grid.
        knowledgeAsOf: Decision cutoff for every source row used by the path set.
        horizon: Number of future steps.
        pathCount: Number of empirical paths when history sources are present. Explicit-only
            path sets must use one path.
        blockLength: Moving-block length for historical joint resampling.
        seed: Deterministic RNG seed for empirical resampling.
        minObservations: Minimum joined historical support.
        certificate: Optional path measure certificate for the historical joint source.

    Returns:
        ``DriverPathSet`` containing scenario paths, factor contracts, and an audit ledger.

    Raises:
        DriverPathError: If source coverage, timing, status, support, or assumptions are invalid.

    Example:
        ``pathSet = buildDriverPathSet((historySource, assumptionSource), knowledgeAsOf="20250101", horizon=4, pathCount=64, blockLength=4, seed=7)``
    """

    if min(horizon, pathCount, blockLength, minObservations) < 1:
        raise DriverPathError("driver path dimensions must be positive")
    cutoff = _dateText(knowledgeAsOf, "knowledgeAsOf")
    histories, assumptions, cards = _collectSources(tuple(sources))
    frequency = cards[0].frequency
    stepSpan = cards[0].stepSpan
    factorSpecs = tuple(factor for card in cards for factor in card.factors)
    registryHash = canonicalPayloadHash(
        {
            "generatorVersion": GENERATOR_VERSION,
            "cards": tuple(_cardPayload(card) for card in cards),
            "factorSpecs": factorSpecs,
        }
    )
    factorContractHash = canonicalPayloadHash(
        tuple(
            (factor.variableId, factor.unit, factor.frequency, factor.timing, factor.transformId)
            for factor in sorted(factorSpecs, key=lambda item: item.variableId)
        )
    )
    sourceRefs = _dedupe(tuple(ref for card in cards for ref in card.sourceRefs))
    warnings: list[str] = []
    warnings.extend(warning for card in cards for warning in card.warnings)
    assumptionStepTuple, assumptionHash, assumptionStepHashes = _assumptionSteps(assumptions, horizon)
    if assumptions:
        warnings.extend(f"explicitAssumption:{source.card.assumptionId}" for source in assumptions)
    historyPanel, variables, historyStatus, historyInputHash = _joinedHistoryPanel(histories, knowledgeAsOf=cutoff)
    historySet: EmpiricalPathSet | None = None
    observedHistoryStatus = historyStatus
    basePathSetHash = ""
    if historyPanel is not None:
        try:
            historySet = buildJointBlockPaths(
                historyPanel,
                variables,
                knowledgeAsOf=cutoff,
                frequency=frequency,
                stepSpan=stepSpan,
                horizon=horizon,
                pathCount=pathCount,
                blockLength=blockLength,
                seed=seed,
                historyStatus=historyStatus,
                minObservations=minObservations,
                certificate=certificate,
                refs=sourceRefs + (f"driverRegistry:{registryHash}",),
            )
        except EmpiricalPathError as error:
            raise DriverPathError(str(error)) from error
        warnings.extend(historySet.audit.warnings)
        basePathSetHash = historySet.audit.pathSetHash
        validationStatus = "unvalidated" if assumptions else historySet.audit.validationStatus
        outputHistoryStatus = "explicitAssumption" if assumptions else historyStatus
        paths = _overlayAssumptions(
            historySet.paths,
            assumptionSteps=assumptionStepTuple,
            refs=sourceRefs,
            registryHash=registryHash,
            assumptionHash=assumptionHash,
            validationStatus=validationStatus,
            historyStatus=outputHistoryStatus,
        )
    else:
        if certificate is not None:
            raise DriverPathError("explicit-only driver paths cannot carry a path certificate")
        if pathCount != 1 or blockLength != 1:
            raise DriverPathError("explicit-only driver paths must use pathCount=1 and blockLength=1")
        paths = (
            _makeExplicitOnlyPath(
                steps=assumptionStepTuple,
                refs=sourceRefs,
                frequency=frequency,
                stepSpan=stepSpan,
                knowledgeAsOf=cutoff,
                registryHash=registryHash,
                assumptionHash=assumptionHash,
            ),
        )
        validationStatus = "unvalidated"
        outputHistoryStatus = "explicitAssumption"
    pathSetHash = _pathSetHash(paths)
    (
        basePathAdmissionReceiptId,
        basePathAdmissionContentHash,
        basePathAdmissionSubjectHash,
        basePathValidationStatus,
        basePathMaxAdmittedStep,
    ) = _basePathAdmissionFields(historySet.paths if historySet is not None else ())
    overlayHash = _overlayHash(
        assumptionHash=assumptionHash,
        assumptionSteps=assumptionStepTuple,
        sourceRefs=sourceRefs,
        horizon=horizon,
    )
    inputHash = canonicalPayloadHash(
        {
            "registryHash": registryHash,
            "historyInputHash": historyInputHash,
            "assumptionHash": assumptionHash,
            "assumptionStepHashes": assumptionStepHashes,
            "basePathSetHash": basePathSetHash,
            "basePathAdmissionReceiptId": basePathAdmissionReceiptId,
            "basePathAdmissionContentHash": basePathAdmissionContentHash,
            "basePathAdmissionSubjectHash": basePathAdmissionSubjectHash,
            "overlayHash": overlayHash,
            "certificate": certificate,
            "knowledgeAsOf": cutoff,
            "horizon": horizon,
            "pathCount": pathCount,
            "blockLength": blockLength,
            "seed": int(seed),
            "minObservations": minObservations,
        }
    )
    audit = DriverPathAudit(
        pathSetHash=pathSetHash,
        inputHash=inputHash,
        historyInputHash=historyInputHash,
        assumptionHash=assumptionHash,
        assumptionStepHashes=assumptionStepHashes,
        basePathSetHash=basePathSetHash,
        basePathAdmissionReceiptId=basePathAdmissionReceiptId,
        basePathAdmissionContentHash=basePathAdmissionContentHash,
        basePathAdmissionSubjectHash=basePathAdmissionSubjectHash,
        basePathValidationStatus=basePathValidationStatus,
        basePathMaxAdmittedStep=basePathMaxAdmittedStep,
        overlayHash=overlayHash,
        registryHash=registryHash,
        factorContractHash=factorContractHash,
        generatorVersion=GENERATOR_VERSION,
        knowledgeAsOf=cutoff,
        frequency=frequency,
        stepSpan=stepSpan,
        horizon=horizon,
        pathCount=len(paths),
        blockLength=blockLength,
        seed=int(seed),
        driverCardIds=tuple(card.cardId for card in cards),
        assumptionDescriptors=_assumptionDescriptors(assumptions),
        validationStatus=validationStatus,
        observedHistoryStatus=observedHistoryStatus,
        historyStatus=outputHistoryStatus,
        sourceRefs=sourceRefs,
        warnings=tuple(sorted(set(warnings))),
    )
    return DriverPathSet(paths=paths, factorSpecs=factorSpecs, audit=audit)
