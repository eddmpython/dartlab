"""Build provider observation batches for driver lanes before path projection."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping

import polars as pl

from dartlab.simulate.admissionRegistry import AdmissionReceipt
from dartlab.simulate.driverPaths import DriverCard, DriverFactorSpec, DriverHistorySource
from dartlab.simulate.stateCompiler import (
    ProviderObservationBatch,
    buildProviderObservationBatch,
    makeVariableObservation,
)
from dartlab.simulate.stateVariables import STATE_EVIDENCE_ROLES, STATE_TIMINGS
from dartlab.simulate.vintage import VintageRef, canonicalPayloadHash

DRIVER_OBSERVATION_BATCH_VERSION = "driver-observation-lane-batch-v1"
_FORBIDDEN_EVIDENCE_ROLES = {"explicitAssumption", "derivedFromAssumption"}
_CONDITIONAL_REVISION_POLICIES = {"latestRetained", "revisedHistory"}
_CONDITIONAL_COVERAGES = {"periodOnly", "latestOnly"}


class DriverObservationBatchError(ValueError):
    """드라이버 원천 lane을 provider observation batch로 만들 수 없으면 발생한다."""


@dataclass(frozen=True)
class DriverObservationSignalSpec:
    """One signal column and its observation meaning contract."""

    signalId: str
    sourceColumn: str
    unit: str
    frequency: str
    timing: str
    transformId: str
    evidenceRole: str = "observed"
    normalizationRuleHash: str = ""


@dataclass(frozen=True)
class DriverObservationLaneSpec:
    """Raw or normalized lane contract used to create provider observations."""

    providerId: str
    datasetId: str
    entityId: str
    knowledgeAsOf: str
    eventTimeColumn: str
    availableAtColumn: str
    revisionIdColumn: str
    sourceArtifactKind: str
    sourceArtifactId: str
    sourceArtifactHash: str
    signalSpecs: tuple[DriverObservationSignalSpec, ...]
    sourceRefs: tuple[str, ...]
    knowledgeAsOfColumn: str = ""
    sourceArtifactHashColumn: str = ""
    eventDateRole: str = "eventThrough"
    requireAvailableAfterEvent: bool = False
    conditionalRevisionPolicy: str = "latestRetained"
    conditionalCoverage: str = "periodOnly"
    availabilityPrecision: str = "date"
    schemaVersion: str = DRIVER_OBSERVATION_BATCH_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "signalSpecs", tuple(self.signalSpecs))
        object.__setattr__(self, "sourceRefs", tuple(self.sourceRefs))


def _dateText(value: str, label: str) -> str:
    text = str(value).replace("-", "")[:8]
    if len(text) != 8 or not text.isdigit():
        raise DriverObservationBatchError(f"invalid {label}: {value}")
    return text


def _dateExpr(column: str) -> pl.Expr:
    return pl.col(column).cast(pl.Utf8).str.replace_all("-", "").str.slice(0, 8)


def _validDigest(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value.lower())


def _finite(value: float | None, label: str) -> float:
    if value is None:
        raise DriverObservationBatchError(f"{label} is missing")
    number = float(value)
    if not math.isfinite(number):
        raise DriverObservationBatchError(f"{label} must be finite")
    return number


def _dedupe(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value))


def _normalizationHash(signal: DriverObservationSignalSpec) -> str:
    if signal.normalizationRuleHash:
        if not _validDigest(signal.normalizationRuleHash):
            raise DriverObservationBatchError(f"normalization hash is invalid: {signal.signalId}")
        return signal.normalizationRuleHash
    return canonicalPayloadHash(
        {
            "schemaVersion": DRIVER_OBSERVATION_BATCH_VERSION,
            "signalId": signal.signalId,
            "sourceColumn": signal.sourceColumn,
            "unit": signal.unit,
            "frequency": signal.frequency,
            "timing": signal.timing,
            "transformId": signal.transformId,
            "evidenceRole": signal.evidenceRole,
        }
    )


def _validateSignalSpecs(signals: tuple[DriverObservationSignalSpec, ...]) -> None:
    if not signals:
        raise DriverObservationBatchError("driver observation lane needs signal specs")
    signalIds = [signal.signalId for signal in signals]
    sourceColumns = [signal.sourceColumn or signal.signalId for signal in signals]
    if len(set(signalIds)) != len(signalIds):
        raise DriverObservationBatchError("driver observation signal ids must be unique")
    if len(set(sourceColumns)) != len(sourceColumns):
        raise DriverObservationBatchError("driver observation source columns must be unique")
    for signal in signals:
        if (
            not signal.signalId
            or not (signal.sourceColumn or signal.signalId)
            or not signal.unit
            or not signal.frequency
            or signal.timing not in STATE_TIMINGS
            or not signal.transformId
            or signal.evidenceRole not in STATE_EVIDENCE_ROLES
            or signal.evidenceRole in _FORBIDDEN_EVIDENCE_ROLES
        ):
            raise DriverObservationBatchError(f"driver observation signal contract is invalid: {signal.signalId}")
        _normalizationHash(signal)


def _validateLaneSpec(spec: DriverObservationLaneSpec) -> None:
    if (
        spec.schemaVersion != DRIVER_OBSERVATION_BATCH_VERSION
        or not spec.providerId
        or not spec.datasetId
        or not spec.entityId
        or not spec.knowledgeAsOf
        or not spec.eventTimeColumn
        or not spec.availableAtColumn
        or not spec.revisionIdColumn
        or not spec.sourceArtifactKind
        or not spec.sourceArtifactId
        or not spec.sourceRefs
        or spec.availabilityPrecision != "date"
    ):
        raise DriverObservationBatchError("driver observation lane spec is incomplete")
    if spec.eventTimeColumn == spec.availableAtColumn:
        raise DriverObservationBatchError("driver observation lane needs separate event and availability columns")
    if spec.eventDateRole not in {"eventThrough", "fiscalThrough"}:
        raise DriverObservationBatchError("driver observation event date role is invalid")
    if not _validDigest(spec.sourceArtifactHash):
        raise DriverObservationBatchError("driver observation source artifact hash is invalid")
    if spec.conditionalRevisionPolicy not in _CONDITIONAL_REVISION_POLICIES:
        raise DriverObservationBatchError("driver observation conditional revision policy is invalid")
    if spec.conditionalCoverage not in _CONDITIONAL_COVERAGES:
        raise DriverObservationBatchError("driver observation conditional coverage is invalid")
    _dateText(spec.knowledgeAsOf, "knowledgeAsOf")
    _validateSignalSpecs(spec.signalSpecs)


def _validateSourceReceipt(
    spec: DriverObservationLaneSpec,
    sourceReceipt: AdmissionReceipt | None,
    *,
    expectedArtifactHash: str,
    expectedKnowledgeAsOf: str,
    requireExact: bool,
) -> tuple[str, str, str]:
    if sourceReceipt is None:
        if requireExact:
            raise DriverObservationBatchError("exact driver observation batch needs a source dataVintage receipt")
        return "", spec.conditionalRevisionPolicy, spec.conditionalCoverage
    if (
        sourceReceipt.kind != "dataVintage"
        or sourceReceipt.status != "verifiedVintage"
        or sourceReceipt.revisionPolicy != "asKnown"
        or sourceReceipt.coverage != "asOfExact"
        or sourceReceipt.artifactHash != expectedArtifactHash
        or sourceReceipt.subjectHash != expectedArtifactHash
        or sourceReceipt.knowledgeAsOf != expectedKnowledgeAsOf
    ):
        raise DriverObservationBatchError("driver observation source receipt does not match the lane artifact")
    return sourceReceipt.receiptId, "asKnown", "asOfExact"


def _resolveSourceReceipt(
    spec: DriverObservationLaneSpec,
    *,
    revisionId: str,
    sourceArtifactHash: str,
    knowledgeAsOf: str,
    sourceReceipt: AdmissionReceipt | None,
    sourceReceipts: Mapping[str, AdmissionReceipt] | None,
    requireExact: bool,
) -> tuple[str, str, str]:
    if sourceReceipt is not None and sourceReceipts is not None:
        raise DriverObservationBatchError("driver observation lane received duplicate source receipt inputs")
    if sourceReceipts is None:
        return _validateSourceReceipt(
            spec,
            sourceReceipt,
            expectedArtifactHash=sourceArtifactHash,
            expectedKnowledgeAsOf=knowledgeAsOf,
            requireExact=requireExact,
        )
    receipt = sourceReceipts.get(revisionId)
    return _validateSourceReceipt(
        spec,
        receipt,
        expectedArtifactHash=sourceArtifactHash,
        expectedKnowledgeAsOf=knowledgeAsOf,
        requireExact=requireExact,
    )


def _normalizedPanel(panel: pl.DataFrame, spec: DriverObservationLaneSpec) -> pl.DataFrame:
    required = {
        spec.eventTimeColumn,
        spec.availableAtColumn,
        spec.revisionIdColumn,
        *(signal.sourceColumn or signal.signalId for signal in spec.signalSpecs),
    }
    if spec.knowledgeAsOfColumn:
        required.add(spec.knowledgeAsOfColumn)
    if spec.sourceArtifactHashColumn:
        required.add(spec.sourceArtifactHashColumn)
    if not required.issubset(panel.columns):
        raise DriverObservationBatchError(
            f"driver observation lane missing columns: {sorted(required - set(panel.columns))}"
        )
    cutoff = _dateText(spec.knowledgeAsOf, "knowledgeAsOf")
    valueExprs = [
        pl.col(signal.sourceColumn or signal.signalId).cast(pl.Float64, strict=False).alias(signal.signalId)
        for signal in spec.signalSpecs
    ]
    out = (
        panel.with_columns(
            _dateExpr(spec.eventTimeColumn).alias("__eventAt"),
            _dateExpr(spec.availableAtColumn).alias("__availableAt"),
            (_dateExpr(spec.knowledgeAsOfColumn) if spec.knowledgeAsOfColumn else pl.lit(cutoff, dtype=pl.Utf8)).alias(
                "__knowledgeAsOf"
            ),
            pl.col(spec.revisionIdColumn).cast(pl.Utf8).str.strip_chars().alias("__revisionId"),
            (
                pl.col(spec.sourceArtifactHashColumn).cast(pl.Utf8).str.strip_chars()
                if spec.sourceArtifactHashColumn
                else pl.lit(spec.sourceArtifactHash, dtype=pl.Utf8)
            ).alias("__sourceArtifactHash"),
            *valueExprs,
        )
        .filter(
            (pl.col("__eventAt") <= cutoff)
            & (pl.col("__availableAt") <= cutoff)
            & (pl.col("__knowledgeAsOf") <= cutoff)
        )
        .select(
            "__eventAt",
            "__availableAt",
            "__knowledgeAsOf",
            "__revisionId",
            "__sourceArtifactHash",
            *(signal.signalId for signal in spec.signalSpecs),
        )
        .sort(["__eventAt", "__availableAt", "__revisionId"])
    )
    malformed = out.filter(
        pl.col("__eventAt").is_null()
        | pl.col("__availableAt").is_null()
        | pl.col("__knowledgeAsOf").is_null()
        | (pl.col("__eventAt").str.len_chars() != 8)
        | (pl.col("__availableAt").str.len_chars() != 8)
        | (pl.col("__knowledgeAsOf").str.len_chars() != 8)
        | ~pl.col("__eventAt").str.contains(r"^\d{8}$")
        | ~pl.col("__availableAt").str.contains(r"^\d{8}$")
        | ~pl.col("__knowledgeAsOf").str.contains(r"^\d{8}$")
        | pl.col("__revisionId").is_null()
        | (pl.col("__revisionId").str.len_chars() == 0)
        | pl.col("__sourceArtifactHash").is_null()
        | (pl.col("__sourceArtifactHash").str.len_chars() != 64)
        | ~pl.col("__sourceArtifactHash").str.contains(r"^[0-9a-fA-F]{64}$")
    )
    if malformed.height:
        raise DriverObservationBatchError(
            "driver observation lane contains malformed dates, revision ids, or artifact hashes"
        )
    if out.filter(pl.col("__eventAt") > pl.col("__availableAt")).height:
        raise DriverObservationBatchError("driver observation event time cannot be after availability")
    if out.filter(pl.col("__availableAt") > pl.col("__knowledgeAsOf")).height:
        raise DriverObservationBatchError("driver observation availability cannot be after knowledgeAsOf")
    if spec.requireAvailableAfterEvent and out.filter(pl.col("__availableAt") <= pl.col("__eventAt")).height:
        raise DriverObservationBatchError("driver observation availability must be after event time")
    if out.height == 0:
        raise DriverObservationBatchError("driver observation lane has no rows available by knowledgeAsOf")
    if out.group_by("__eventAt").len().filter(pl.col("len") > 1).height:
        raise DriverObservationBatchError("driver observation lane has duplicate event observations")
    if any(
        out.select(
            *(pl.col(signal.signalId).is_null().any().alias(signal.signalId) for signal in spec.signalSpecs)
        ).row(0)
    ):
        raise DriverObservationBatchError("driver observation lane has missing signal values")
    for signal in spec.signalSpecs:
        if any(not math.isfinite(float(value)) for value in out[signal.signalId].to_list()):
            raise DriverObservationBatchError(f"driver observation lane has non-finite values: {signal.signalId}")
    return out


def _vintageRef(
    spec: DriverObservationLaneSpec,
    *,
    eventAt: str,
    availableAt: str,
    knowledgeAsOf: str,
    revisionId: str,
    sourceArtifactHash: str,
    receiptId: str,
    revisionPolicy: str,
    coverage: str,
    signal: DriverObservationSignalSpec,
) -> VintageRef:
    eventThrough = eventAt if spec.eventDateRole == "eventThrough" else ""
    fiscalThrough = eventAt if spec.eventDateRole == "fiscalThrough" else ""
    rowRef = f"{signal.signalId}:{revisionId}:{eventAt}:{availableAt}:{knowledgeAsOf}"
    return VintageRef(
        artifactKind=spec.sourceArtifactKind,
        provider=spec.providerId,
        artifactId=f"{spec.sourceArtifactId}:{revisionId}",
        artifactHash=sourceArtifactHash,
        payloadHash=sourceArtifactHash,
        knowledgeAsOf=knowledgeAsOf,
        availableAt=availableAt,
        revisionPolicy=revisionPolicy,
        coverage=coverage,
        fiscalThrough=fiscalThrough,
        eventThrough=eventThrough,
        receiptId=receiptId,
        contractHash=_normalizationHash(signal),
        sourceRefs=_dedupe(
            (
                *(f"{ref}:{rowRef}" for ref in spec.sourceRefs),
                f"revisionId:{revisionId}:rowRef:{rowRef}",
                f"eventAt:{eventAt}:rowRef:{rowRef}",
                f"availableAt:{availableAt}:rowRef:{rowRef}",
                f"knowledgeAsOf:{knowledgeAsOf}:rowRef:{rowRef}",
                f"sourceColumn:{signal.sourceColumn or signal.signalId}:rowRef:{rowRef}",
            )
        ),
    )


def buildDriverObservationBatchFromPanel(
    panel: pl.DataFrame,
    spec: DriverObservationLaneSpec,
    *,
    sourceReceipt: AdmissionReceipt | None = None,
    sourceReceipts: Mapping[str, AdmissionReceipt] | None = None,
    requireExact: bool = False,
) -> ProviderObservationBatch:
    """Build a provider observation batch from a driver data lane.

    Args:
        panel: Raw or normalized lane frame with event, availability, revision id, and signal columns.
        spec: Provider, source artifact, signal, timing, and evidence contract.
        sourceReceipt: Optional exact ``dataVintage`` receipt for the source artifact.
        sourceReceipts: Optional exact ``dataVintage`` receipts keyed by row revision id.
        requireExact: If true, refuse to build without an exact source receipt.

    Returns:
        Unsigned ``ProviderObservationBatch``. Exact batches can then be signed by ``issueProviderObservationBatch``.

    Raises:
        DriverObservationBatchError: If identity, timing, evidence, source receipt, or row uniqueness is unsafe.

    Example:
        ``batch = buildDriverObservationBatchFromPanel(panel, spec, sourceReceipt=receipt, requireExact=True)``
    """

    if isinstance(panel, DriverHistorySource):
        raise DriverObservationBatchError("DriverHistorySource cannot be promoted to provider observations")
    _validateLaneSpec(spec)
    normalized = _normalizedPanel(panel, spec)
    observations = []
    for row in normalized.iter_rows(named=True):
        eventAt = _dateText(row["__eventAt"], "eventAt")
        availableAt = _dateText(row["__availableAt"], "availableAt")
        rowKnowledgeAsOf = _dateText(row["__knowledgeAsOf"], "knowledgeAsOf")
        revisionId = str(row["__revisionId"])
        sourceArtifactHash = str(row["__sourceArtifactHash"]).lower()
        receiptId, revisionPolicy, coverage = _resolveSourceReceipt(
            spec,
            revisionId=revisionId,
            sourceArtifactHash=sourceArtifactHash,
            knowledgeAsOf=rowKnowledgeAsOf,
            sourceReceipt=sourceReceipt,
            sourceReceipts=sourceReceipts,
            requireExact=requireExact,
        )
        for signal in spec.signalSpecs:
            observations.append(
                makeVariableObservation(
                    providerId=spec.providerId,
                    datasetId=spec.datasetId,
                    entityId=spec.entityId,
                    signalId=signal.signalId,
                    value=_finite(row[signal.signalId], signal.signalId),
                    unit=signal.unit,
                    frequency=signal.frequency,
                    timing=signal.timing,
                    transformId=signal.transformId,
                    evidenceRole=signal.evidenceRole,
                    eventAt=eventAt,
                    availableAt=availableAt,
                    knowledgeAsOf=rowKnowledgeAsOf,
                    availabilityPrecision=spec.availabilityPrecision,
                    revisionId=revisionId,
                    vintage=_vintageRef(
                        spec,
                        eventAt=eventAt,
                        availableAt=availableAt,
                        knowledgeAsOf=rowKnowledgeAsOf,
                        revisionId=revisionId,
                        sourceArtifactHash=sourceArtifactHash,
                        receiptId=receiptId,
                        revisionPolicy=revisionPolicy,
                        coverage=coverage,
                        signal=signal,
                    ),
                    normalizationRuleHash=_normalizationHash(signal),
                )
            )
    return buildProviderObservationBatch(
        tuple(observations),
        providerId=spec.providerId,
        datasetId=spec.datasetId,
        entityId=spec.entityId,
        signalIds=tuple(signal.signalId for signal in spec.signalSpecs),
        cutoffAsOf=spec.knowledgeAsOf,
    )


def driverHistorySourceFromProviderObservationBatch(
    batch: ProviderObservationBatch,
    *,
    cardId: str,
    factors: tuple[DriverFactorSpec, ...],
    stepSpan: int = 1,
    sourceRefs: tuple[str, ...] = (),
    status: str = "active",
    warnings: tuple[str, ...] = (),
) -> DriverHistorySource:
    """Project provider observations down to a path-generation history source.

    Args:
        batch: Provider observation batch built before path generation.
        cardId: Driver card id for the projected source.
        factors: Driver factor contracts that must match batch observations.
        stepSpan: Positive path step span for the projected driver card.
        sourceRefs: Additional audit references for the path source.
        status: Driver card execution status.
        warnings: Honest-gap warnings to carry into path generation.

    Returns:
        ``DriverHistorySource`` whose row values are copied from provider observations.

    Raises:
        DriverObservationBatchError: If observation meaning, event coverage, or duplicate rows are unsafe.

    Example:
        ``source = driverHistorySourceFromProviderObservationBatch(batch, cardId="fx", factors=factors)``
    """

    if not isinstance(batch, ProviderObservationBatch) or not cardId:
        raise DriverObservationBatchError("provider observation batch projection is incomplete")
    factorTuple = tuple(factors)
    if not factorTuple or stepSpan < 1:
        raise DriverObservationBatchError("provider observation batch projection needs factors")
    factorById = {factor.variableId: factor for factor in factorTuple}
    if len(factorById) != len(factorTuple):
        raise DriverObservationBatchError("provider observation batch projection factor ids must be unique")
    frequencies = {factor.frequency for factor in factorTuple}
    if len(frequencies) != 1:
        raise DriverObservationBatchError("provider observation batch projection needs one frequency")
    rowsByEvent: dict[str, dict] = {}
    seen: set[tuple[str, str]] = set()
    for observation in batch.observations:
        if observation.signalId not in factorById:
            continue
        factor = factorById[observation.signalId]
        if (
            observation.unit != factor.unit
            or observation.frequency != factor.frequency
            or observation.transformId != factor.transformId
        ):
            raise DriverObservationBatchError("provider observation projection meaning drift")
        eventAt = _dateText(observation.eventAt, "observation.eventAt")
        key = (eventAt, observation.signalId)
        if key in seen:
            raise DriverObservationBatchError("provider observation projection has duplicate signal events")
        seen.add(key)
        row = rowsByEvent.setdefault(eventAt, {"eventTime": eventAt, "availableAt": observation.availableAt})
        if row["availableAt"] != observation.availableAt:
            raise DriverObservationBatchError("provider observation projection availability drift")
        row[observation.signalId] = _finite(observation.value, observation.signalId)
    requiredSignals = set(factorById)
    rows = []
    for eventAt in sorted(rowsByEvent):
        row = rowsByEvent[eventAt]
        if set(row) - {"eventTime", "availableAt"} != requiredSignals:
            raise DriverObservationBatchError("provider observation projection signal coverage is incomplete")
        rows.append(row)
    if not rows:
        raise DriverObservationBatchError("provider observation batch projection has no rows")
    historyStatus = (
        "asKnown" if batch.historyStatus == "exact" and _validDigest(batch.batchReceiptId) else "revisedHistory"
    )
    projectionWarnings = tuple(warnings)
    if historyStatus != "asKnown":
        projectionWarnings += ("conditionalProviderObservationBatch",)
    card = DriverCard(
        cardId=cardId,
        sourceKind="history",
        providerId=batch.providerId,
        datasetId=batch.datasetId,
        entityId=batch.entityId,
        frequency=factorTuple[0].frequency,
        stepSpan=stepSpan,
        factors=factorTuple,
        historyStatus=historyStatus,
        sourceRefs=_dedupe(
            (
                *sourceRefs,
                f"providerObservationBatch:{batch.batchReceiptId or batch.batchId}",
                f"providerObservationBatchId:{batch.batchId}",
            )
        ),
        status=status,
        warnings=_dedupe(projectionWarnings),
    )
    return DriverHistorySource(card, pl.DataFrame(rows))
