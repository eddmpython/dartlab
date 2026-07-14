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
DRIVER_DESIGN_FRAME_VERSION = "driver-coefficient-design-frame-v1"
SELECTION_RULE_ID = "single-observation-per-signal-event-v1"
ORIGIN_KNOWLEDGE_POLICY_ID = "sourceObservationKnowledgeAsOf"
MULTISOURCE_ORIGIN_KNOWLEDGE_POLICY_ID = "maxSourceObservationKnowledgeAsOf"
SOURCE_REF_POLICY_ID = "observationId"
DESIGN_MISSING_POLICY_ID = "completeCaseIntersection"


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


@dataclass(frozen=True)
class DriverDesignColumnSpec:
    """One source column in a multivariable driver design frame."""

    variableId: str
    signalId: str
    unit: str
    frequency: str
    transformId: str
    timing: str = "ratio"
    evidenceRoles: tuple[str, ...] = ("observed", "deterministicDerived")

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidenceRoles", tuple(self.evidenceRoles))


@dataclass(frozen=True)
class MultivariableDriverCoefficientObservationFrameSpec:
    """Several source batches and one forward label batch under one design matrix contract."""

    frameId: str
    sourceColumns: tuple[DriverDesignColumnSpec, ...]
    labelSignalId: str
    targetVariableId: str
    targetUnit: str
    frequency: str
    stepSpan: int
    horizonSteps: int
    originStart: str = ""
    originThrough: str = ""
    labelEvidenceRoles: tuple[str, ...] = ("observed",)
    selectionRuleId: str = SELECTION_RULE_ID
    originKnowledgePolicy: str = MULTISOURCE_ORIGIN_KNOWLEDGE_POLICY_ID
    sourceRefPolicy: str = SOURCE_REF_POLICY_ID
    missingPolicy: str = DESIGN_MISSING_POLICY_ID
    schemaVersion: str = DRIVER_DESIGN_FRAME_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "sourceColumns", tuple(self.sourceColumns))
        object.__setattr__(self, "labelEvidenceRoles", tuple(self.labelEvidenceRoles))


@dataclass(frozen=True)
class MultivariableDriverCoefficientObservationFrame:
    """Exact provider observation batches joined into a replayable multivariable design frame."""

    frameId: str
    frame: pl.DataFrame
    frameHash: str
    sourceBatchReceiptIds: tuple[str, ...]
    labelBatchReceiptId: str
    sourceParentReceiptIds: tuple[str, ...]
    labelParentReceiptIds: tuple[str, ...]
    rowCount: int
    droppedOriginCount: int
    droppedOriginHash: str
    missingCountByVariable: tuple[tuple[str, int], ...]
    columnOrderHash: str
    specHash: str
    spec: MultivariableDriverCoefficientObservationFrameSpec | None = None
    schemaVersion: str = DRIVER_DESIGN_FRAME_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "sourceBatchReceiptIds", tuple(self.sourceBatchReceiptIds))
        object.__setattr__(self, "sourceParentReceiptIds", tuple(self.sourceParentReceiptIds))
        object.__setattr__(self, "labelParentReceiptIds", tuple(self.labelParentReceiptIds))
        object.__setattr__(self, "missingCountByVariable", tuple(self.missingCountByVariable))


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


def _validateDesignSpec(spec: MultivariableDriverCoefficientObservationFrameSpec) -> None:
    if (
        spec.schemaVersion != DRIVER_DESIGN_FRAME_VERSION
        or not spec.frameId
        or not spec.sourceColumns
        or not spec.labelSignalId
        or not spec.targetVariableId
        or not spec.targetUnit
        or not spec.frequency
        or spec.stepSpan < 1
        or spec.horizonSteps < 1
        or not spec.labelEvidenceRoles
    ):
        raise DriverObservationFrameError("driver design frame spec is incomplete")
    if (
        spec.selectionRuleId != SELECTION_RULE_ID
        or spec.originKnowledgePolicy != MULTISOURCE_ORIGIN_KNOWLEDGE_POLICY_ID
        or spec.sourceRefPolicy != SOURCE_REF_POLICY_ID
        or spec.missingPolicy != DESIGN_MISSING_POLICY_ID
    ):
        raise DriverObservationFrameError("driver design frame policy is unsupported")
    variableIds = [column.variableId for column in spec.sourceColumns]
    if len(set(variableIds)) != len(variableIds):
        raise DriverObservationFrameError("driver design frame source variables must be unique")
    for column in spec.sourceColumns:
        if (
            not column.variableId
            or not column.signalId
            or not column.unit
            or column.frequency != spec.frequency
            or not column.timing
            or not column.transformId
            or not column.evidenceRoles
        ):
            raise DriverObservationFrameError("driver design frame source column is incomplete")
    if spec.originStart:
        _dateText(spec.originStart, "originStart")
    if spec.originThrough:
        _dateText(spec.originThrough, "originThrough")
    if spec.originStart and spec.originThrough and spec.originStart > spec.originThrough:
        raise DriverObservationFrameError("driver design frame origin window is inverted")


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
    timing: str = "",
    transformId: str = "",
) -> None:
    if observation.signalId != signalId:
        return
    if observation.unit != unit or observation.frequency != frequency:
        raise DriverObservationFrameError(f"{role} observation meaning drift")
    if timing and observation.timing != timing:
        raise DriverObservationFrameError(f"{role} observation timing drift")
    if transformId and observation.transformId != transformId:
        raise DriverObservationFrameError(f"{role} observation transform drift")
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
    timing: str = "",
    transformId: str = "",
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
            timing=timing,
            transformId=transformId,
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


def _sourceValueColumn(variableId: str) -> str:
    return f"sourceValue__{variableId}"


def _sourceRefColumn(variableId: str) -> str:
    return f"sourceRef__{variableId}"


def _sourceAvailableColumn(variableId: str) -> str:
    return f"sourceAvailableAt__{variableId}"


def _sourceKnowledgeColumn(variableId: str) -> str:
    return f"sourceKnowledgeAsOf__{variableId}"


def _sourceEventColumn(variableId: str) -> str:
    return f"sourceEventTime__{variableId}"


def _columnOrderPayload(sourceColumns: tuple[DriverDesignColumnSpec, ...]) -> tuple[dict, ...]:
    return tuple(
        {
            "position": index,
            "variableId": column.variableId,
            "signalId": column.signalId,
            "unit": column.unit,
            "frequency": column.frequency,
            "timing": column.timing,
            "transformId": column.transformId,
            "evidenceRoles": column.evidenceRoles,
        }
        for index, column in enumerate(sourceColumns)
    )


def _multivariableFrameRows(
    sourceByColumn: tuple[tuple[DriverDesignColumnSpec, dict[int, VariableObservation]], ...],
    labelByPeriod: dict[int, VariableObservation],
    spec: MultivariableDriverCoefficientObservationFrameSpec,
    columnOrderHash: str,
) -> tuple[tuple[dict, ...], tuple[tuple[str, int], ...], int, str]:
    horizon = spec.stepSpan * spec.horizonSteps
    periodSets = [set(byPeriod) for _column, byPeriod in sourceByColumn]
    commonPeriods = set.intersection(*periodSets) if periodSets else set()
    if not commonPeriods:
        raise DriverObservationFrameError("driver design frame has no common source row universe")
    allPeriods = set.union(*periodSets) if periodSets else set()
    droppedPayload = []
    for period in sorted(allPeriods - commonPeriods):
        droppedPayload.append(
            {
                "periodIndex": period,
                "missingVariableIds": tuple(
                    column.variableId for column, byPeriod in sourceByColumn if period not in byPeriod
                ),
            }
        )
    missingCountByVariable = tuple(
        (column.variableId, len(allPeriods - set(byPeriod))) for column, byPeriod in sourceByColumn
    )
    droppedOriginHash = canonicalPayloadHash(
        {
            "schemaVersion": DRIVER_DESIGN_FRAME_VERSION,
            "missingPolicy": spec.missingPolicy,
            "droppedOrigins": tuple(droppedPayload),
        }
    )
    rows = []
    for sourcePeriod in sorted(commonPeriods):
        firstSource = sourceByColumn[0][1][sourcePeriod]
        targetPeriod = sourcePeriod + horizon
        label = labelByPeriod.get(targetPeriod)
        if label is None:
            raise DriverObservationFrameError("driver design frame missing horizon label")
        originEventTime = _dateText(firstSource.eventAt, "originEventTime")
        targetEventTime = _dateText(label.eventAt, "targetEventTime")
        targetAvailableAt = _dateText(label.availableAt, "targetAvailableAt")
        distance = _periodIndex(targetEventTime, spec.frequency, "targetEventTime") - _periodIndex(
            originEventTime,
            spec.frequency,
            "originEventTime",
        )
        if distance != horizon:
            raise DriverObservationFrameError("driver design frame horizon mismatch")
        sourceRefs = []
        sourceValues = []
        sourceAvailableDates = []
        sourceKnowledgeDates = []
        row = {
            "originId": "",
            "originEventTime": originEventTime,
            "originKnowledgeAsOf": "",
            "sourceAvailableAt": "",
            "targetEventTime": targetEventTime,
            "targetAvailableAt": targetAvailableAt,
            "targetValue": _finite(label.value, "targetValue"),
            "labelSourceRef": label.observationId,
            "columnOrderHash": columnOrderHash,
        }
        for column, byPeriod in sourceByColumn:
            source = byPeriod[sourcePeriod]
            sourceEventTime = _dateText(source.eventAt, f"{column.variableId}.eventAt")
            if sourceEventTime != originEventTime:
                raise DriverObservationFrameError("driver design frame source event grid drift")
            sourceAvailableAt = _dateText(source.availableAt, f"{column.variableId}.availableAt")
            sourceKnowledgeAsOf = _dateText(source.knowledgeAsOf, f"{column.variableId}.knowledgeAsOf")
            if sourceAvailableAt > sourceKnowledgeAsOf:
                raise DriverObservationFrameError("driver design frame source knowledge policy is invalid")
            sourceRefs.append(source.observationId)
            sourceValues.append(_finite(source.value, column.variableId))
            sourceAvailableDates.append(sourceAvailableAt)
            sourceKnowledgeDates.append(sourceKnowledgeAsOf)
            row[_sourceValueColumn(column.variableId)] = _finite(source.value, column.variableId)
            row[_sourceRefColumn(column.variableId)] = source.observationId
            row[_sourceAvailableColumn(column.variableId)] = sourceAvailableAt
            row[_sourceKnowledgeColumn(column.variableId)] = sourceKnowledgeAsOf
            row[_sourceEventColumn(column.variableId)] = sourceEventTime
        originKnowledgeAsOf = max(sourceKnowledgeDates)
        sourceAvailableAt = max(sourceAvailableDates)
        if targetAvailableAt <= originKnowledgeAsOf:
            raise DriverObservationFrameError("driver design frame label observation is not forward known")
        row["originKnowledgeAsOf"] = originKnowledgeAsOf
        row["sourceAvailableAt"] = sourceAvailableAt
        row["originId"] = f"{spec.frameId}:{columnOrderHash}:{':'.join(sourceRefs)}:{label.observationId}"
        rows.append(row)
    if not rows:
        raise DriverObservationFrameError("driver design frame needs rows")
    return tuple(rows), missingCountByVariable, len(droppedPayload), droppedOriginHash


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


def _designFramePayload(
    *,
    spec: MultivariableDriverCoefficientObservationFrameSpec,
    specHash: str,
    columnOrderHash: str,
    sourceBatches: tuple[ProviderObservationBatch, ...],
    labelBatch: ProviderObservationBatch,
    rows: tuple[dict, ...],
    missingCountByVariable: tuple[tuple[str, int], ...],
    droppedOriginCount: int,
    droppedOriginHash: str,
) -> dict:
    return {
        "schemaVersion": DRIVER_DESIGN_FRAME_VERSION,
        "frameId": spec.frameId,
        "spec": spec,
        "specHash": specHash,
        "columnOrderHash": columnOrderHash,
        "sourceBatchIds": tuple(batch.batchId for batch in sourceBatches),
        "sourceBatchReceiptIds": tuple(batch.batchReceiptId for batch in sourceBatches),
        "labelBatchId": labelBatch.batchId,
        "labelBatchReceiptId": labelBatch.batchReceiptId,
        "missingPolicy": spec.missingPolicy,
        "missingCountByVariable": missingCountByVariable,
        "droppedOriginCount": droppedOriginCount,
        "droppedOriginHash": droppedOriginHash,
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


def buildMultivariableDriverCoefficientObservationFrame(
    sourceBatches: tuple[ProviderObservationBatch, ...],
    labelBatch: ProviderObservationBatch,
    spec: MultivariableDriverCoefficientObservationFrameSpec,
) -> MultivariableDriverCoefficientObservationFrame:
    """Build a replayable multivariable design frame from signed provider observations.

    Args:
        sourceBatches: Signed exact source batches. Order must match ``spec.sourceColumns``.
        labelBatch: Signed exact forward label batch.
        spec: Column order, missing policy, label, and horizon contract.

    Returns:
        Wide design frame with one source value and source ref column per variable.

    Raises:
        DriverObservationFrameError: If source batches, column order, missing policy, timing, or label lineage fails.

    Example:
        ``frame = buildMultivariableDriverCoefficientObservationFrame((fxBatch, priceBatch), labelBatch, spec)``
    """

    _validateDesignSpec(spec)
    sourceTuple = tuple(sourceBatches)
    if len(sourceTuple) != len(spec.sourceColumns):
        raise DriverObservationFrameError("driver design frame source batch count mismatch")
    for index, batch in enumerate(sourceTuple):
        _validateBatch(batch, role=f"source[{index}]")
    _validateBatch(labelBatch, role="label")
    entities = {batch.entityId for batch in (*sourceTuple, labelBatch)}
    if len(entities) != 1:
        raise DriverObservationFrameError("driver design frame provider batches use different entities")
    sourceByColumn = []
    for column, batch in zip(spec.sourceColumns, sourceTuple):
        sourceByColumn.append(
            (
                column,
                _selectObservations(
                    batch,
                    role=f"source[{column.variableId}]",
                    signalId=column.signalId,
                    unit=column.unit,
                    frequency=spec.frequency,
                    evidenceRoles=column.evidenceRoles,
                    originStart=spec.originStart,
                    originThrough=spec.originThrough,
                    timing=column.timing,
                    transformId=column.transformId,
                ),
            )
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
    columnOrderHash = canonicalPayloadHash(_columnOrderPayload(spec.sourceColumns))
    rows, missingCountByVariable, droppedOriginCount, droppedOriginHash = _multivariableFrameRows(
        tuple(sourceByColumn),
        labelByPeriod,
        spec,
        columnOrderHash,
    )
    frame = pl.DataFrame(rows)
    specHash = canonicalPayloadHash(spec)
    frameHash = canonicalPayloadHash(
        _designFramePayload(
            spec=spec,
            specHash=specHash,
            columnOrderHash=columnOrderHash,
            sourceBatches=sourceTuple,
            labelBatch=labelBatch,
            rows=rows,
            missingCountByVariable=missingCountByVariable,
            droppedOriginCount=droppedOriginCount,
            droppedOriginHash=droppedOriginHash,
        )
    )
    return MultivariableDriverCoefficientObservationFrame(
        frameId=spec.frameId,
        frame=frame,
        frameHash=frameHash,
        sourceBatchReceiptIds=tuple(batch.batchReceiptId for batch in sourceTuple),
        labelBatchReceiptId=labelBatch.batchReceiptId,
        sourceParentReceiptIds=tuple(batch.batchReceiptId for batch in sourceTuple),
        labelParentReceiptIds=(labelBatch.batchReceiptId,),
        rowCount=len(rows),
        droppedOriginCount=droppedOriginCount,
        droppedOriginHash=droppedOriginHash,
        missingCountByVariable=missingCountByVariable,
        columnOrderHash=columnOrderHash,
        specHash=specHash,
        spec=spec,
    )
