"""Build driver coefficient frames from signed provider observation batches."""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from datetime import date

import polars as pl

from dartlab.simulate.stateCompiler import (
    PROVIDER_OBSERVATION_BATCH_SCHEMA,
    ProviderObservationBatch,
    VariableObservation,
    buildProviderObservationBatch,
)
from dartlab.simulate.vintage import canonicalPayloadHash

DRIVER_OBSERVATION_FRAME_VERSION = "driver-coefficient-observation-frame-v1"
SELECTION_RULE_ID = "single-observation-per-signal-event-v1"
ORIGIN_KNOWLEDGE_POLICY_ID = "sourceObservationKnowledgeAsOf"
SOURCE_REF_POLICY_ID = "observationId"


class DriverObservationFrameError(ValueError):
    """공급자 관측 batch에서 coefficient frame을 안전하게 만들 수 없으면 발생한다."""


@dataclass(frozen=True)
class DriverCoefficientObservationFrameSpec:
    """Signed provider batches를 coefficient frame으로 묶는 source, label, horizon 계약이다."""

    frameId: str
    sourceSignalId: str
    labelSignalId: str
    sourceVariableId: str
    targetVariableId: str
    sourceUnit: str
    targetUnit: str
    frequency: str
    stepSpan: int
    horizonSteps: int
    originStart: str = ""
    originThrough: str = ""
    sourceEvidenceRoles: tuple[str, ...] = ("observed", "deterministicDerived")
    labelEvidenceRoles: tuple[str, ...] = ("observed",)
    selectionRuleId: str = SELECTION_RULE_ID
    originKnowledgePolicy: str = ORIGIN_KNOWLEDGE_POLICY_ID
    sourceRefPolicy: str = SOURCE_REF_POLICY_ID
    schemaVersion: str = DRIVER_OBSERVATION_FRAME_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "sourceEvidenceRoles", tuple(self.sourceEvidenceRoles))
        object.__setattr__(self, "labelEvidenceRoles", tuple(self.labelEvidenceRoles))


@dataclass(frozen=True)
class DriverCoefficientObservationFrame:
    """Provider batch observation ids로 row refs가 결속된 coefficient frame이다."""

    frameId: str
    frame: pl.DataFrame
    frameHash: str
    sourceBatchReceiptId: str
    labelBatchReceiptId: str
    sourceParentReceiptIds: tuple[str, ...]
    labelParentReceiptIds: tuple[str, ...]
    rowCount: int
    specHash: str
    spec: DriverCoefficientObservationFrameSpec | None = None
    schemaVersion: str = DRIVER_OBSERVATION_FRAME_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "sourceParentReceiptIds", tuple(self.sourceParentReceiptIds))
        object.__setattr__(self, "labelParentReceiptIds", tuple(self.labelParentReceiptIds))


def _dateText(value: str, label: str) -> str:
    text = str(value).replace("-", "")[:8]
    if len(text) != 8 or not text.isdigit():
        raise DriverObservationFrameError(f"invalid {label}: {value}")
    return text


def _dateParts(value: str, label: str) -> tuple[int, int, int]:
    text = _dateText(value, label)
    year = int(text[:4])
    month = int(text[4:6])
    day = int(text[6:8])
    try:
        date(year, month, day)
    except ValueError as error:
        raise DriverObservationFrameError(f"invalid {label}: {value}") from error
    return year, month, day


def _periodIndex(value: str, frequency: str, label: str) -> int:
    year, month, day = _dateParts(value, label)
    normalized = frequency.lower()
    if normalized in {"day", "daily"}:
        return date(year, month, day).toordinal()
    if normalized in {"month", "monthly"}:
        return year * 12 + month - 1
    if normalized in {"quarter", "quarterly"}:
        return year * 4 + (month - 1) // 3
    if normalized in {"year", "yearly", "annual"}:
        return year
    raise DriverObservationFrameError(f"unsupported driver observation frequency: {frequency}")


def _validDigest(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value.lower())


def _finite(value: float, label: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise DriverObservationFrameError(f"{label} must be finite")
    return number


def _validateSpec(spec: DriverCoefficientObservationFrameSpec) -> None:
    if (
        spec.schemaVersion != DRIVER_OBSERVATION_FRAME_VERSION
        or not spec.frameId
        or not spec.sourceSignalId
        or not spec.labelSignalId
        or not spec.sourceVariableId
        or not spec.targetVariableId
        or not spec.sourceUnit
        or not spec.targetUnit
        or not spec.frequency
        or spec.stepSpan < 1
        or spec.horizonSteps < 1
        or not spec.sourceEvidenceRoles
        or not spec.labelEvidenceRoles
    ):
        raise DriverObservationFrameError("driver observation frame spec is incomplete")
    if (
        spec.selectionRuleId != SELECTION_RULE_ID
        or spec.originKnowledgePolicy != ORIGIN_KNOWLEDGE_POLICY_ID
        or spec.sourceRefPolicy != SOURCE_REF_POLICY_ID
    ):
        raise DriverObservationFrameError("driver observation frame policy is unsupported")
    if spec.originStart:
        _dateText(spec.originStart, "originStart")
    if spec.originThrough:
        _dateText(spec.originThrough, "originThrough")
    if spec.originStart and spec.originThrough and spec.originStart > spec.originThrough:
        raise DriverObservationFrameError("driver observation origin window is inverted")


def _validateBatch(batch: ProviderObservationBatch, *, role: str) -> None:
    if not isinstance(batch, ProviderObservationBatch) or batch.schemaVersion != PROVIDER_OBSERVATION_BATCH_SCHEMA:
        raise DriverObservationFrameError(f"{role} provider batch protocol mismatch")
    expected = buildProviderObservationBatch(
        batch.observations,
        providerId=batch.providerId,
        datasetId=batch.datasetId,
        entityId=batch.entityId,
        signalIds=batch.signalIds,
        cutoffAsOf=batch.cutoffAsOf,
    )
    if replace(batch, batchReceiptId="") != expected:
        raise DriverObservationFrameError(f"{role} provider batch does not reproduce")
    if not _validDigest(batch.batchReceiptId):
        raise DriverObservationFrameError(f"{role} provider batch must be signed")
    if batch.historyStatus != "exact" or not batch.sourceReceiptIds:
        raise DriverObservationFrameError(f"{role} provider batch must be exact")


def _validateObservation(
    observation: VariableObservation,
    *,
    role: str,
    signalId: str,
    unit: str,
    frequency: str,
    evidenceRoles: tuple[str, ...],
    batchCutoff: str,
) -> None:
    if observation.signalId != signalId:
        return
    if observation.unit != unit or observation.frequency != frequency:
        raise DriverObservationFrameError(f"{role} observation meaning drift")
    if observation.evidenceRole not in evidenceRoles:
        raise DriverObservationFrameError(f"{role} observation evidence role is not allowed")
    eventAt = _dateText(observation.eventAt, f"{role}.eventAt")
    availableAt = _dateText(observation.availableAt, f"{role}.availableAt")
    knowledgeAsOf = _dateText(observation.knowledgeAsOf, f"{role}.knowledgeAsOf")
    if eventAt > availableAt or availableAt > knowledgeAsOf:
        raise DriverObservationFrameError(f"{role} observation timing is invalid")
    if knowledgeAsOf > batchCutoff:
        raise DriverObservationFrameError(f"{role} observation knowledge is after batch cutoff")
    _finite(observation.value, f"{role}.value")


def _selectObservations(
    batch: ProviderObservationBatch,
    *,
    role: str,
    signalId: str,
    unit: str,
    frequency: str,
    evidenceRoles: tuple[str, ...],
    originStart: str,
    originThrough: str,
) -> dict[int, VariableObservation]:
    selected: list[VariableObservation] = []
    batchCutoff = _dateText(batch.cutoffAsOf, f"{role}.cutoffAsOf")
    start = _dateText(originStart, "originStart") if originStart else ""
    through = _dateText(originThrough, "originThrough") if originThrough else ""
    for observation in batch.observations:
        _validateObservation(
            observation,
            role=role,
            signalId=signalId,
            unit=unit,
            frequency=frequency,
            evidenceRoles=evidenceRoles,
            batchCutoff=batchCutoff,
        )
        if observation.signalId != signalId:
            continue
        eventAt = _dateText(observation.eventAt, f"{role}.eventAt")
        if role == "source" and start and eventAt < start:
            continue
        if role == "source" and through and eventAt > through:
            continue
        selected.append(observation)
    if not selected:
        raise DriverObservationFrameError(f"{role} provider batch has no selected observations")
    eventCounts: dict[str, int] = {}
    periodCounts: dict[int, int] = {}
    byPeriod: dict[int, VariableObservation] = {}
    for observation in selected:
        eventAt = _dateText(observation.eventAt, f"{role}.eventAt")
        periodIndex = _periodIndex(eventAt, frequency, f"{role}.eventAt")
        eventCounts[eventAt] = eventCounts.get(eventAt, 0) + 1
        periodCounts[periodIndex] = periodCounts.get(periodIndex, 0) + 1
        byPeriod[periodIndex] = observation
    if any(count > 1 for count in eventCounts.values()) or any(count > 1 for count in periodCounts.values()):
        raise DriverObservationFrameError(f"{role} provider batch has duplicate observations")
    return byPeriod


def _frameRows(
    sourceByPeriod: dict[int, VariableObservation],
    labelByPeriod: dict[int, VariableObservation],
    spec: DriverCoefficientObservationFrameSpec,
) -> tuple[dict, ...]:
    rows = []
    horizon = spec.stepSpan * spec.horizonSteps
    for sourcePeriod in sorted(sourceByPeriod):
        source = sourceByPeriod[sourcePeriod]
        targetPeriod = sourcePeriod + horizon
        label = labelByPeriod.get(targetPeriod)
        if label is None:
            raise DriverObservationFrameError("driver observation frame missing horizon label")
        originEventTime = _dateText(source.eventAt, "originEventTime")
        originKnowledgeAsOf = _dateText(source.knowledgeAsOf, "originKnowledgeAsOf")
        sourceAvailableAt = _dateText(source.availableAt, "sourceAvailableAt")
        targetEventTime = _dateText(label.eventAt, "targetEventTime")
        targetAvailableAt = _dateText(label.availableAt, "targetAvailableAt")
        distance = _periodIndex(targetEventTime, spec.frequency, "targetEventTime") - _periodIndex(
            originEventTime,
            spec.frequency,
            "originEventTime",
        )
        if distance != horizon:
            raise DriverObservationFrameError("driver observation frame horizon mismatch")
        if sourceAvailableAt > originKnowledgeAsOf:
            raise DriverObservationFrameError("source observation knowledge policy is invalid")
        if targetAvailableAt <= originKnowledgeAsOf:
            raise DriverObservationFrameError("label observation is not forward known")
        rows.append(
            {
                "originId": f"{spec.frameId}:{source.observationId}:{label.observationId}",
                "originEventTime": originEventTime,
                "originKnowledgeAsOf": originKnowledgeAsOf,
                "sourceAvailableAt": sourceAvailableAt,
                "targetEventTime": targetEventTime,
                "targetAvailableAt": targetAvailableAt,
                "sourceValue": _finite(source.value, "sourceValue"),
                "targetValue": _finite(label.value, "targetValue"),
                "sourceRef": source.observationId,
                "labelSourceRef": label.observationId,
            }
        )
    if not rows:
        raise DriverObservationFrameError("driver observation frame needs rows")
    return tuple(rows)


def _framePayload(
    *,
    spec: DriverCoefficientObservationFrameSpec,
    specHash: str,
    sourceBatch: ProviderObservationBatch,
    labelBatch: ProviderObservationBatch,
    rows: tuple[dict, ...],
) -> dict:
    return {
        "schemaVersion": DRIVER_OBSERVATION_FRAME_VERSION,
        "frameId": spec.frameId,
        "spec": spec,
        "specHash": specHash,
        "sourceBatchId": sourceBatch.batchId,
        "sourceBatchReceiptId": sourceBatch.batchReceiptId,
        "labelBatchId": labelBatch.batchId,
        "labelBatchReceiptId": labelBatch.batchReceiptId,
        "rows": rows,
    }


def buildDriverCoefficientObservationFrame(
    sourceBatch: ProviderObservationBatch,
    labelBatch: ProviderObservationBatch,
    spec: DriverCoefficientObservationFrameSpec,
) -> DriverCoefficientObservationFrame:
    """Build a calibration or OOS frame from signed provider observations.

    Args:
        sourceBatch: Signed exact provider batch carrying source driver observations.
        labelBatch: Signed exact provider batch carrying realized forward labels.
        spec: Signal, unit, evidence, and horizon contract for row pairing.

    Returns:
        DataFrame plus parent receipt ids whose row refs are provider observation ids.

    Raises:
        DriverObservationFrameError: If batch lineage, meaning, evidence role, timing, or horizon pairing fails.

    Example:
        ``frame = buildDriverCoefficientObservationFrame(sourceBatch, labelBatch, spec)``
    """

    _validateSpec(spec)
    _validateBatch(sourceBatch, role="source")
    _validateBatch(labelBatch, role="label")
    if sourceBatch.entityId != labelBatch.entityId:
        raise DriverObservationFrameError("source and label provider batches use different entities")
    sourceByPeriod = _selectObservations(
        sourceBatch,
        role="source",
        signalId=spec.sourceSignalId,
        unit=spec.sourceUnit,
        frequency=spec.frequency,
        evidenceRoles=spec.sourceEvidenceRoles,
        originStart=spec.originStart,
        originThrough=spec.originThrough,
    )
    labelByPeriod = _selectObservations(
        labelBatch,
        role="label",
        signalId=spec.labelSignalId,
        unit=spec.targetUnit,
        frequency=spec.frequency,
        evidenceRoles=spec.labelEvidenceRoles,
        originStart="",
        originThrough="",
    )
    rows = _frameRows(sourceByPeriod, labelByPeriod, spec)
    frame = pl.DataFrame(rows)
    specHash = canonicalPayloadHash(spec)
    frameHash = canonicalPayloadHash(
        _framePayload(
            spec=spec,
            specHash=specHash,
            sourceBatch=sourceBatch,
            labelBatch=labelBatch,
            rows=rows,
        )
    )
    return DriverCoefficientObservationFrame(
        frameId=spec.frameId,
        frame=frame,
        frameHash=frameHash,
        sourceBatchReceiptId=sourceBatch.batchReceiptId,
        labelBatchReceiptId=labelBatch.batchReceiptId,
        sourceParentReceiptIds=(sourceBatch.batchReceiptId,),
        labelParentReceiptIds=(labelBatch.batchReceiptId,),
        rowCount=len(rows),
        specHash=specHash,
        spec=spec,
    )
