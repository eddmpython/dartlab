"""Provider-neutral content-addressed feature observation의 공용 data 정본."""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from datetime import date

from dartlab.data.featureRegistry import STATE_EVIDENCE_ROLES, STATE_TIMINGS
from dartlab.data.vintage import VintageRef, canonicalPayloadHash

VARIABLE_OBSERVATION_SCHEMA = "variable-observation-v1"


class FeatureObservationError(ValueError):
    """관측값의 내용 결속, 의미 또는 시간 계약이 잘못되면 발생한다."""


def _dateText(value: str, label: str) -> str:
    text = str(value).replace("-", "")
    if len(text) != 8 or not text.isdigit():
        raise FeatureObservationError(f"invalid {label}: {value}")
    try:
        date(int(text[:4]), int(text[4:6]), int(text[6:8]))
    except ValueError as error:
        raise FeatureObservationError(f"invalid {label}: {value}") from error
    return text


def _validDigest(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value.lower())


@dataclass(frozen=True)
class VariableObservation:
    """공급자 신호 하나의 값, 의미, 수정판, 공개시점, 원천 빈티지를 보존한다."""

    observationId: str
    providerId: str
    datasetId: str
    entityId: str
    signalId: str
    value: float
    unit: str
    frequency: str
    timing: str
    transformId: str
    evidenceRole: str
    eventAt: str
    availableAt: str
    knowledgeAsOf: str
    availabilityPrecision: str
    revisionId: str
    vintage: VintageRef
    normalizationRuleHash: str
    schemaVersion: str = VARIABLE_OBSERVATION_SCHEMA


def observationPayload(observation: VariableObservation) -> dict:
    """Return the content-bound fields of one feature observation.

    Args:
        observation: Observation whose content-addressed identifier is excluded.

    Returns:
        Dataclass field mapping without ``observationId``.

    Raises:
        AttributeError: If a structurally incompatible object is supplied.

    Example:
        ``payload = observationPayload(observation)``
    """

    return {name: getattr(observation, name) for name in observation.__dataclass_fields__ if name != "observationId"}


def makeVariableObservation(**values) -> VariableObservation:
    """Create a content-addressed provider observation.

    Args:
        values: Every ``VariableObservation`` field except ``observationId``.

    Returns:
        Observation whose ID binds value, meaning, timing, revision, and vintage.

    Raises:
        TypeError: If a required dataclass field is absent.

    Example:
        ``observation = makeVariableObservation(providerId="edgar", ...)``
    """

    normalized = dict(values)
    for fieldName in ("eventAt", "availableAt", "knowledgeAsOf"):
        if fieldName in normalized:
            normalized[fieldName] = _dateText(normalized[fieldName], fieldName)
    vintage = normalized.get("vintage")
    if isinstance(vintage, VintageRef):
        normalized["vintage"] = replace(
            vintage,
            knowledgeAsOf=_dateText(vintage.knowledgeAsOf, "vintage.knowledgeAsOf"),
            availableAt=_dateText(vintage.availableAt, "vintage.availableAt"),
            fiscalThrough=(_dateText(vintage.fiscalThrough, "vintage.fiscalThrough") if vintage.fiscalThrough else ""),
            eventThrough=_dateText(vintage.eventThrough, "vintage.eventThrough") if vintage.eventThrough else "",
            fitThrough=_dateText(vintage.fitThrough, "vintage.fitThrough") if vintage.fitThrough else "",
        )
    provisional = VariableObservation(observationId="", **normalized)
    return replace(provisional, observationId=canonicalPayloadHash(observationPayload(provisional)))


def validateVariableObservation(observation: VariableObservation) -> VariableObservation:
    """Validate one content-addressed feature observation contract.

    Args:
        observation: Observation to verify for content, meaning, and time order.

    Returns:
        The unchanged validated observation.

    Raises:
        FeatureObservationError: If protocol, hash, value, meaning, or cutoff is invalid.

    Example:
        ``validated = validateVariableObservation(observation)``
    """

    if not isinstance(observation, VariableObservation) or observation.schemaVersion != VARIABLE_OBSERVATION_SCHEMA:
        raise FeatureObservationError("variable observation protocol mismatch")
    if observation.observationId != canonicalPayloadHash(observationPayload(observation)):
        raise FeatureObservationError("variable observation content hash mismatch")
    if not math.isfinite(float(observation.value)):
        raise FeatureObservationError("variable observation is not finite")
    if (
        not observation.providerId
        or not observation.datasetId
        or not observation.entityId
        or not observation.signalId
        or not observation.revisionId
        or not observation.unit
        or not observation.frequency
        or not observation.transformId
        or observation.timing not in STATE_TIMINGS
        or observation.evidenceRole not in STATE_EVIDENCE_ROLES
        or observation.availabilityPrecision != "date"
        or not _validDigest(observation.normalizationRuleHash)
    ):
        raise FeatureObservationError("variable observation contract is incomplete")
    eventAt = _dateText(observation.eventAt, "eventAt")
    availableAt = _dateText(observation.availableAt, "availableAt")
    knowledgeAsOf = _dateText(observation.knowledgeAsOf, "knowledgeAsOf")
    if eventAt > availableAt or availableAt > knowledgeAsOf:
        raise FeatureObservationError("variable observation time order is invalid")
    if observation.vintage.availableAt != availableAt or observation.vintage.knowledgeAsOf != knowledgeAsOf:
        raise FeatureObservationError("variable observation vintage cutoff mismatch")
    return observation


__all__ = [
    "FeatureObservationError",
    "VARIABLE_OBSERVATION_SCHEMA",
    "VariableObservation",
    "makeVariableObservation",
    "observationPayload",
    "validateVariableObservation",
]
