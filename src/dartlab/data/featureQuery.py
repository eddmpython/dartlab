"""Provider-neutral feature history와 point-in-time selection kernel."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from typing import Literal

from dartlab.data.featureObservation import VariableObservation, validateVariableObservation
from dartlab.data.featureRegistry import (
    StateVariableRegistry,
    StateVariableSpec,
    buildStateVariableRegistry,
)
from dartlab.data.vintage import canonicalPayloadHash, isExactAsKnown, validateVintageRef

FEATURE_OBSERVATION_INPUT_SCHEMA = "feature-observation-input-v1"
FEATURE_OBSERVATION_SET_SCHEMA = "feature-observation-set-v1"
FEATURE_READ_QUERY_SCHEMA = "feature-read-query-v1"
FEATURE_READ_RESULT_SCHEMA = "feature-read-result-v1"
FEATURE_SELECTION_RULE_ID = "latest-event-then-availability-revision-v1"


class FeatureQueryError(ValueError):
    """Feature dataset, bitemporal cutoff 또는 selection 계약이 잘못되면 발생한다."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class FeatureObservationSet:
    """하나의 feature registry와 검증된 revision 관측 전체를 내용 결속한다."""

    registry: StateVariableRegistry
    observations: tuple[VariableObservation, ...]
    observationSetHash: str
    schemaVersion: str = FEATURE_OBSERVATION_SET_SCHEMA


@dataclass(frozen=True)
class FeatureReadQuery:
    """Feature history 또는 한 시점의 latest-known view를 고정한다."""

    featureIds: tuple[str, ...] = ()
    entityIds: tuple[str, ...] = ()
    validAt: str | None = None
    knownAt: str | None = None
    mode: Literal["history", "pointInTime"] = "history"
    requireExact: bool = False
    schemaVersion: str = FEATURE_READ_QUERY_SCHEMA


@dataclass(frozen=True)
class FeatureSelection:
    """Feature definition 하나와 선택된 source observation의 결합."""

    featureId: str
    featureVersionId: str
    observation: VariableObservation
    exactAsKnown: bool


@dataclass(frozen=True)
class FeatureReadResult:
    """결정적 feature selection, 결손, query identity를 함께 반환한다."""

    selections: tuple[FeatureSelection, ...]
    missing: tuple[tuple[str, str], ...]
    registryHash: str
    observationSetHash: str
    queryHash: str
    mode: Literal["history", "pointInTime"]
    validAt: str | None
    knownAt: str | None
    exactAsKnown: bool
    schemaVersion: str = FEATURE_READ_RESULT_SCHEMA


def _dateText(value: str, label: str) -> str:
    text = str(value).replace("-", "")
    if len(text) != 8 or not text.isdigit():
        raise FeatureQueryError("FEATURE_TIME_INVALID", f"invalid {label}: {value}")
    try:
        date(int(text[:4]), int(text[4:6]), int(text[6:8]))
    except ValueError as error:
        raise FeatureQueryError("FEATURE_TIME_INVALID", f"invalid {label}: {value}") from error
    return text


def _sourceKey(spec: StateVariableSpec) -> tuple[str, ...]:
    return (
        spec.providerId,
        spec.datasetId,
        spec.signalId,
        spec.unit,
        spec.frequency,
        spec.timing,
        spec.transformId,
        spec.evidenceRole,
    )


def _observationSourceKey(observation: VariableObservation) -> tuple[str, ...]:
    return (
        observation.providerId,
        observation.datasetId,
        observation.signalId,
        observation.unit,
        observation.frequency,
        observation.timing,
        observation.transformId,
        observation.evidenceRole,
    )


def _primaryKey(observation: VariableObservation) -> tuple[str, ...]:
    return (
        observation.providerId,
        observation.datasetId,
        observation.entityId,
        observation.signalId,
        observation.eventAt,
        observation.availableAt,
        observation.revisionId,
    )


def _featureVersionId(spec: StateVariableSpec, normalizationRuleHash: str) -> str:
    return "feature-version:" + canonicalPayloadHash(
        {
            "schemaVersion": "feature-definition-v1",
            "spec": spec,
            "normalizationRuleHash": normalizationRuleHash,
        }
    )


def _orderKey(observation: VariableObservation) -> tuple[str, ...]:
    return (
        observation.providerId,
        observation.datasetId,
        observation.entityId,
        observation.signalId,
        observation.eventAt,
        observation.availableAt,
        observation.knowledgeAsOf,
        observation.revisionId,
        observation.observationId,
    )


def buildFeatureObservationSet(
    registry: StateVariableRegistry,
    observations: tuple[VariableObservation, ...],
) -> FeatureObservationSet:
    """Registry와 revision observation 전체를 검증하고 내용 기반 dataset으로 고정한다.

    Args:
        registry: Feature 의미와 source 계약의 정본.
        observations: 여러 entity, event time, revision을 포함할 수 있는 관측 tuple.

    Returns:
        정렬되고 content-addressed된 ``FeatureObservationSet``.

    Raises:
        FeatureQueryError: Registry drift, unknown source, duplicate key 또는 observation 오류가 있을 때.

    Example:
        ``dataset = buildFeatureObservationSet(registry, observations)``
    """

    try:
        expectedRegistry = buildStateVariableRegistry(registry.specs)
    except ValueError as error:
        raise FeatureQueryError("FEATURE_REGISTRY_INVALID", str(error)) from error
    if registry != expectedRegistry:
        raise FeatureQueryError("FEATURE_REGISTRY_DRIFT", "registry content hash가 specs와 다릅니다")
    specsBySource: dict[tuple[str, ...], list[StateVariableSpec]] = {}
    for spec in registry.specs:
        specsBySource.setdefault(_sourceKey(spec), []).append(spec)
    for sourceSpecs in specsBySource.values():
        if len(sourceSpecs) > 1 and any(spec.role == "observedFeature" for spec in sourceSpecs):
            raise FeatureQueryError(
                "FEATURE_SOURCE_AMBIGUOUS",
                ", ".join(spec.variableId for spec in sourceSpecs),
            )
    allowedSources = set(specsBySource)
    ordered = tuple(sorted(observations, key=_orderKey))
    primaryKeys: set[tuple[str, ...]] = set()
    observationIds: set[str] = set()
    for observation in ordered:
        try:
            validateVariableObservation(observation)
            validateVintageRef(observation.vintage, decisionAsOf=observation.knowledgeAsOf)
        except ValueError as error:
            raise FeatureQueryError("FEATURE_OBSERVATION_INVALID", str(error)) from error
        if _observationSourceKey(observation) not in allowedSources:
            raise FeatureQueryError(
                "FEATURE_SOURCE_UNKNOWN",
                f"registry에 없는 observation source: {observation.providerId}/{observation.datasetId}/{observation.signalId}",
            )
        sourceSpecs = specsBySource[_observationSourceKey(observation)]
        if any(spec.role == "observedFeature" for spec in sourceSpecs):
            market, separator, entity = observation.entityId.partition(":")
            if not separator or not market or not entity or ":" in entity:
                raise FeatureQueryError(
                    "FEATURE_ENTITY_INVALID",
                    "observedFeature entityId는 MARKET:ID 형식이어야 합니다",
                )
        primaryKey = _primaryKey(observation)
        if primaryKey in primaryKeys:
            raise FeatureQueryError("FEATURE_PRIMARY_KEY_DUPLICATE", "/".join(primaryKey))
        if observation.observationId in observationIds:
            raise FeatureQueryError("FEATURE_OBSERVATION_DUPLICATE", observation.observationId)
        primaryKeys.add(primaryKey)
        observationIds.add(observation.observationId)
    normalizationBySource: dict[tuple[str, ...], set[str]] = {}
    for observation in ordered:
        normalizationBySource.setdefault(_observationSourceKey(observation), set()).add(
            observation.normalizationRuleHash
        )
    if any(len(hashes) > 1 for hashes in normalizationBySource.values()):
        raise FeatureQueryError(
            "FEATURE_NORMALIZATION_DRIFT",
            "한 feature observation set 안에서 normalization rule이 바뀌었습니다",
        )
    payload = {
        "schemaVersion": FEATURE_OBSERVATION_SET_SCHEMA,
        "registryHash": registry.registryHash,
        "observations": ordered,
    }
    return FeatureObservationSet(registry, ordered, canonicalPayloadHash(payload))


def featureObservationSetFromValue(value: object) -> FeatureObservationSet | None:
    """Owner-neutral mapping envelope를 검증된 feature observation set으로 변환한다.

    Args:
        value: 이미 검증된 set 또는 lower owner가 반환한 plain mapping.

    Returns:
        Feature observation set. Feature envelope가 아니면 ``None``.

    Raises:
        FeatureQueryError: Envelope라고 선언했지만 schema나 content가 잘못된 경우.

    Example:
        ``dataset = featureObservationSetFromValue(ownerPayload)``
    """

    if isinstance(value, FeatureObservationSet):
        return value
    if not isinstance(value, Mapping) or value.get("schemaVersion") != FEATURE_OBSERVATION_INPUT_SCHEMA:
        return None
    if set(value) != {"schemaVersion", "specs", "observations"}:
        raise FeatureQueryError("FEATURE_INPUT_INVALID", "feature input envelope field가 유효하지 않습니다")
    rawSpecs = value["specs"]
    rawObservations = value["observations"]
    if (
        not isinstance(rawSpecs, Sequence)
        or isinstance(rawSpecs, (str, bytes))
        or not isinstance(rawObservations, Sequence)
        or isinstance(rawObservations, (str, bytes))
    ):
        raise FeatureQueryError("FEATURE_INPUT_INVALID", "specs와 observations는 sequence여야 합니다")
    try:
        specs = tuple(StateVariableSpec(**dict(item)) for item in rawSpecs if isinstance(item, Mapping))
        if len(specs) != len(rawSpecs):
            raise TypeError("feature spec item이 mapping이 아닙니다")
        observations = []
        for item in rawObservations:
            if not isinstance(item, Mapping):
                raise TypeError("feature observation item이 mapping이 아닙니다")
            payload = dict(item)
            suppliedId = payload.pop("observationId", None)
            vintage = payload.get("vintage")
            if isinstance(vintage, Mapping):
                vintagePayload = dict(vintage)
                if "sourceRefs" in vintagePayload:
                    sourceRefs = vintagePayload["sourceRefs"]
                    if (
                        not isinstance(sourceRefs, Sequence)
                        or isinstance(sourceRefs, (str, bytes))
                        or any(type(item) is not str for item in sourceRefs)
                    ):
                        raise TypeError("vintage sourceRefs는 string sequence여야 합니다")
                    vintagePayload["sourceRefs"] = tuple(sourceRefs)
                from dartlab.data.vintage import VintageRef

                payload["vintage"] = VintageRef(**vintagePayload)
            from dartlab.data.featureObservation import makeVariableObservation

            observation = makeVariableObservation(**payload)
            if suppliedId is not None and suppliedId != observation.observationId:
                raise FeatureQueryError("FEATURE_OBSERVATION_INVALID", "supplied observationId가 content와 다릅니다")
            observations.append(observation)
        return buildFeatureObservationSet(buildStateVariableRegistry(specs), tuple(observations))
    except FeatureQueryError:
        raise
    except (TypeError, ValueError, KeyError) as error:
        raise FeatureQueryError("FEATURE_INPUT_INVALID", str(error)) from error


def _normalizedQuery(dataset: FeatureObservationSet, query: FeatureReadQuery) -> FeatureReadQuery:
    if query.schemaVersion != FEATURE_READ_QUERY_SCHEMA or query.mode not in {"history", "pointInTime"}:
        raise FeatureQueryError("FEATURE_QUERY_INVALID", "feature read protocol이 유효하지 않습니다")
    availableFeatures = {spec.variableId for spec in dataset.registry.specs}
    featureIds = tuple(sorted(set(query.featureIds))) if query.featureIds else tuple(sorted(availableFeatures))
    unknown = tuple(sorted(set(featureIds) - availableFeatures))
    if unknown:
        raise FeatureQueryError("FEATURE_ID_UNKNOWN", ", ".join(unknown))
    entityIds = tuple(sorted(set(query.entityIds)))
    if any(not entityId for entityId in entityIds):
        raise FeatureQueryError("FEATURE_ENTITY_INVALID", "entityId가 비었습니다")
    if query.requireExact and not entityIds:
        raise FeatureQueryError(
            "FEATURE_EXACT_SCOPE_REQUIRED",
            "requireExact query에는 명시적인 entityIds가 필요합니다",
        )
    validAt = _dateText(query.validAt, "validAt") if query.validAt is not None else None
    knownAt = _dateText(query.knownAt, "knownAt") if query.knownAt is not None else None
    if query.mode == "pointInTime" and knownAt is None:
        raise FeatureQueryError("FEATURE_KNOWN_AT_REQUIRED", "pointInTime query에는 knownAt이 필요합니다")
    return FeatureReadQuery(
        featureIds=featureIds,
        entityIds=entityIds,
        validAt=validAt,
        knownAt=knownAt,
        mode=query.mode,
        requireExact=query.requireExact,
    )


def _eligible(observation: VariableObservation, query: FeatureReadQuery) -> bool:
    if query.entityIds and observation.entityId not in query.entityIds:
        return False
    eventAt = _dateText(observation.eventAt, "eventAt")
    availableAt = _dateText(observation.availableAt, "availableAt")
    knowledgeAsOf = _dateText(observation.knowledgeAsOf, "knowledgeAsOf")
    if query.validAt is not None and eventAt > query.validAt:
        return False
    return query.knownAt is None or (availableAt <= query.knownAt and knowledgeAsOf <= query.knownAt)


def _selectionExact(observation: VariableObservation, *, knownAt: str | None) -> bool:
    return (
        knownAt is not None
        and _dateText(observation.availableAt, "availableAt") != knownAt
        and isExactAsKnown(observation.vintage)
        and observation.evidenceRole
        in {
            "observed",
            "deterministicDerived",
            "admittedEstimate",
        }
    )


def _validateSelectedValue(
    spec: StateVariableSpec,
    observation: VariableObservation,
    *,
    knownAt: str | None,
    enforceStaleness: bool,
) -> None:
    value = float(observation.value)
    if spec.lower is not None and value < spec.lower:
        raise FeatureQueryError("FEATURE_VALUE_BELOW_BOUND", spec.variableId)
    if spec.upper is not None and value > spec.upper:
        raise FeatureQueryError("FEATURE_VALUE_ABOVE_BOUND", spec.variableId)
    if enforceStaleness and knownAt is not None:
        cutoff = date(int(knownAt[:4]), int(knownAt[4:6]), int(knownAt[6:8]))
        available = _dateText(observation.availableAt, "availableAt")
        availableDate = date(int(available[:4]), int(available[4:6]), int(available[6:8]))
        if (cutoff - availableDate).days > spec.maxStalenessDays:
            raise FeatureQueryError("FEATURE_OBSERVATION_STALE", spec.variableId)


def readFeatures(dataset: FeatureObservationSet, query: FeatureReadQuery) -> FeatureReadResult:
    """같은 observation set에서 offline history와 online PIT view를 선택한다.

    Args:
        dataset: 검증된 registry와 revision observations.
        query: Feature, entity, valid time, knowledge time과 selection mode.

    Returns:
        선택 결과, 명시 entity의 결손, registry와 query content hash.

    Raises:
        FeatureQueryError: Dataset drift, 미래 지식, ambiguous revision 또는 exactness 위반 시.

    Example:
        ``result = readFeatures(dataset, FeatureReadQuery(knownAt="2025-02-01", mode="pointInTime"))``
    """

    if dataset.schemaVersion != FEATURE_OBSERVATION_SET_SCHEMA:
        raise FeatureQueryError("FEATURE_DATASET_INVALID", "feature observation set protocol이 다릅니다")
    expected = buildFeatureObservationSet(dataset.registry, dataset.observations)
    if dataset != expected:
        raise FeatureQueryError("FEATURE_DATASET_DRIFT", "observationSetHash가 실제 observations와 다릅니다")
    normalized = _normalizedQuery(dataset, query)
    specById = {spec.variableId: spec for spec in dataset.registry.specs}
    observationsBySource: dict[tuple[str, ...], list[VariableObservation]] = {}
    for observation in dataset.observations:
        observationsBySource.setdefault(_observationSourceKey(observation), []).append(observation)

    selected: list[FeatureSelection] = []
    missing: list[tuple[str, str]] = []
    targetEntities = normalized.entityIds or tuple(
        sorted(
            {
                observation.entityId
                for featureId in normalized.featureIds
                for observation in observationsBySource.get(_sourceKey(specById[featureId]), ())
                if _eligible(observation, normalized)
            }
        )
    )
    for featureId in normalized.featureIds:
        spec = specById[featureId]
        candidates = tuple(
            observation
            for observation in observationsBySource.get(_sourceKey(spec), ())
            if _eligible(observation, normalized)
        )
        for entityId in targetEntities:
            entityRows = tuple(observation for observation in candidates if observation.entityId == entityId)
            if not entityRows:
                missing.append((featureId, entityId))
                continue
            if normalized.mode == "history":
                chosen = tuple(sorted(entityRows, key=_orderKey))
            else:
                ordered = tuple(
                    sorted(
                        entityRows,
                        key=lambda item: (
                            item.eventAt,
                            item.availableAt,
                            item.knowledgeAsOf,
                            item.observationId,
                        ),
                    )
                )
                topKey = (
                    ordered[-1].eventAt,
                    ordered[-1].availableAt,
                    ordered[-1].knowledgeAsOf,
                )
                tied = tuple(item for item in ordered if (item.eventAt, item.availableAt, item.knowledgeAsOf) == topKey)
                if len({item.observationId for item in tied}) != 1:
                    raise FeatureQueryError("FEATURE_REVISION_AMBIGUOUS", f"{featureId}/{entityId}")
                chosen = (ordered[-1],)
            for observation in chosen:
                _validateSelectedValue(
                    spec,
                    observation,
                    knownAt=normalized.knownAt,
                    enforceStaleness=normalized.mode == "pointInTime",
                )
                selected.append(
                    FeatureSelection(
                        featureId,
                        _featureVersionId(spec, observation.normalizationRuleHash),
                        observation,
                        _selectionExact(observation, knownAt=normalized.knownAt),
                    )
                )

    selections = tuple(
        sorted(
            selected,
            key=lambda item: (item.featureId, item.observation.entityId, *_orderKey(item.observation)),
        )
    )
    exact = bool(selections) and not missing and all(item.exactAsKnown for item in selections)
    if normalized.requireExact and (not exact or missing):
        raise FeatureQueryError("FEATURE_EXACT_REQUIRED", "exact as-known coverage가 완전하지 않습니다")
    queryPayload = {
        "schemaVersion": FEATURE_READ_QUERY_SCHEMA,
        "registryHash": dataset.registry.registryHash,
        "observationSetHash": dataset.observationSetHash,
        "featureIds": normalized.featureIds,
        "entityIds": normalized.entityIds,
        "validAt": normalized.validAt,
        "knownAt": normalized.knownAt,
        "mode": normalized.mode,
        "requireExact": normalized.requireExact,
        "selectionRuleId": FEATURE_SELECTION_RULE_ID,
    }
    return FeatureReadResult(
        selections=selections,
        missing=tuple(sorted(missing)),
        registryHash=dataset.registry.registryHash,
        observationSetHash=dataset.observationSetHash,
        queryHash=canonicalPayloadHash(queryPayload),
        mode=normalized.mode,
        validAt=normalized.validAt,
        knownAt=normalized.knownAt,
        exactAsKnown=exact,
    )


__all__ = [
    "FEATURE_OBSERVATION_INPUT_SCHEMA",
    "FEATURE_OBSERVATION_SET_SCHEMA",
    "FEATURE_READ_QUERY_SCHEMA",
    "FEATURE_READ_RESULT_SCHEMA",
    "FEATURE_SELECTION_RULE_ID",
    "FeatureObservationSet",
    "FeatureQueryError",
    "FeatureReadQuery",
    "FeatureReadResult",
    "FeatureSelection",
    "buildFeatureObservationSet",
    "featureObservationSetFromValue",
    "readFeatures",
]
