"""Compile executable-visible state from complete point-in-time provider batches."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, replace
from datetime import date
from hashlib import sha256
from pathlib import Path
from typing import Mapping

from dartlab.simulate.admissionRegistry import (
    AdmissionReceipt,
    AdmissionVerifier,
    TrustedIssuer,
    artifactPath,
    issueAdmissionReceipt,
    putAdmissionArtifact,
)
from dartlab.simulate.stateSupport import (
    StatePrimitive,
    stateAdmissionSubjectHash,
    stateContractHash,
)
from dartlab.simulate.stateVariables import (
    STATE_EVIDENCE_ROLES,
    STATE_TIMINGS,
    StateVariableError,
    StateVariableRegistry,
    StateVariableSpec,
    buildStateVariableRegistry,
    stateVariableContractHash,
)
from dartlab.simulate.vintage import (
    VintageError,
    VintageRef,
    canonicalPayloadBytes,
    canonicalPayloadHash,
    isExactAsKnown,
    validateVintageRef,
)

OBSERVATION_BATCH_RULE_ID = "complete-provider-observation-batch"
OBSERVATION_BATCH_RULE_VERSION = "1"
OBSERVATION_BATCH_RULE_HASH = sha256(b"dartlab.complete-provider-observation-batch.v1").hexdigest()
OBSERVATION_BATCH_EXECUTABLE_HASH = sha256(b"dartlab.provider-observation-batch-issuer.v1").hexdigest()
PIT_STATE_RULE_ID = "compiled-point-in-time-state"
PIT_STATE_RULE_VERSION = "1"
PIT_STATE_RULE_HASH = sha256(b"dartlab.compiled-point-in-time-state.v1").hexdigest()
PIT_STATE_EXECUTABLE_HASH = sha256(b"dartlab.point-in-time-state-compiler.v1").hexdigest()
STATE_SELECTION_RULE_ID = "latest-event-then-revision-v1"
STATE_CUTOFF_POLICY_ID = "date-only-same-day-conditional-v1"
VARIABLE_OBSERVATION_SCHEMA = "variable-observation-v1"
PROVIDER_OBSERVATION_BATCH_SCHEMA = "provider-observation-batch-v1"
STATE_COMPILE_SPEC_SCHEMA = "state-compile-spec-v1"
COMPILED_PIT_STATE_SCHEMA = "compiled-point-in-time-state-v1"


class StateCompilerError(ValueError):
    """상태 관측, complete batch, 시점 또는 admission 계보가 잘못되면 발생한다."""


def _dateText(value: str, label: str) -> str:
    text = str(value).replace("-", "")[:8]
    if len(text) != 8 or not text.isdigit():
        raise StateCompilerError(f"invalid {label}: {value}")
    return text


def _dateValue(value: str, label: str) -> date:
    text = _dateText(value, label)
    try:
        return date(int(text[:4]), int(text[4:6]), int(text[6:8]))
    except ValueError as error:
        raise StateCompilerError(f"invalid {label}: {value}") from error


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


@dataclass(frozen=True)
class ProviderObservationBatch:
    """고정된 공급자 query에서 cutoff까지 가능한 후보 관측 전부를 보존한다."""

    batchId: str
    batchReceiptId: str
    queryContractHash: str
    providerId: str
    datasetId: str
    entityId: str
    signalIds: tuple[str, ...]
    cutoffAsOf: str
    observations: tuple[VariableObservation, ...]
    observationRoot: str
    sourceReceiptIds: tuple[str, ...]
    historyStatus: str
    schemaVersion: str = PROVIDER_OBSERVATION_BATCH_SCHEMA


@dataclass(frozen=True)
class StateCompileSpec:
    """한 의사결정 origin의 소비자, 변수 범위와 exact 요구를 고정한다."""

    entityId: str
    market: str
    decisionAsOf: str
    consumerId: str
    consumerVersion: str
    variableIds: tuple[str, ...]
    requireExact: bool = False
    schemaVersion: str = STATE_COMPILE_SPEC_SCHEMA


@dataclass(frozen=True)
class CompiledPointInTimeState:
    """complete provider batches에서 결정론적으로 선택한 실행 초기 상태다."""

    stateId: str
    manifestHash: str
    registryHash: str
    stateContractHash: str
    stateCompilationContractHash: str
    entityId: str
    market: str
    decisionAsOf: str
    knowledgeAsOf: str
    statePrimitives: tuple[StatePrimitive, ...]
    selectedObservationIds: tuple[str, ...]
    providerBatchIds: tuple[str, ...]
    providerBatchReceiptIds: tuple[str, ...]
    historyStatus: str
    admissionStatus: str
    aggregateRevisionPolicy: str
    aggregateCoverage: str
    limitations: tuple[str, ...]
    manifestArtifact: bytes
    stateReceiptId: str = ""
    schemaVersion: str = COMPILED_PIT_STATE_SCHEMA


def _observationPayload(observation: VariableObservation) -> dict:
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

    provisional = VariableObservation(observationId="", **values)
    return replace(provisional, observationId=canonicalPayloadHash(_observationPayload(provisional)))


def _validateObservation(observation: VariableObservation) -> None:
    if observation.schemaVersion != VARIABLE_OBSERVATION_SCHEMA:
        raise StateCompilerError("variable observation protocol mismatch")
    if observation.observationId != canonicalPayloadHash(_observationPayload(observation)):
        raise StateCompilerError("variable observation content hash mismatch")
    if not math.isfinite(float(observation.value)):
        raise StateCompilerError("variable observation is not finite")
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
        raise StateCompilerError("variable observation contract is incomplete")
    eventAt = _dateText(observation.eventAt, "eventAt")
    availableAt = _dateText(observation.availableAt, "availableAt")
    knowledgeAsOf = _dateText(observation.knowledgeAsOf, "knowledgeAsOf")
    if eventAt > availableAt or availableAt > knowledgeAsOf:
        raise StateCompilerError("variable observation time order is invalid")
    if observation.vintage.availableAt != availableAt or observation.vintage.knowledgeAsOf != knowledgeAsOf:
        raise StateCompilerError("variable observation vintage cutoff mismatch")


def _queryPayload(
    *,
    providerId: str,
    datasetId: str,
    entityId: str,
    signalIds: tuple[str, ...],
    cutoffAsOf: str,
) -> dict:
    return {
        "providerId": providerId,
        "datasetId": datasetId,
        "entityId": entityId,
        "signalIds": tuple(sorted(signalIds)),
        "cutoffAsOf": _dateText(cutoffAsOf, "cutoffAsOf"),
        "selectionRuleId": STATE_SELECTION_RULE_ID,
        "cutoffPolicyId": STATE_CUTOFF_POLICY_ID,
    }


def _batchPayload(batch: ProviderObservationBatch) -> dict:
    return {
        name: getattr(batch, name) for name in batch.__dataclass_fields__ if name not in {"batchId", "batchReceiptId"}
    }


def buildProviderObservationBatch(
    observations: tuple[VariableObservation, ...],
    *,
    providerId: str,
    datasetId: str,
    entityId: str,
    signalIds: tuple[str, ...],
    cutoffAsOf: str,
) -> ProviderObservationBatch:
    """Freeze all candidates available for one fixed provider query.

    Args:
        observations: Provider rows, including revisions, around the cutoff.
        providerId: Required provider identity.
        datasetId: Required dataset identity.
        entityId: Company or market entity identity.
        signalIds: Exact signal scope covered by the query.
        cutoffAsOf: Decision-date cutoff for the provider batch.

    Returns:
        Deterministic unsigned complete observation batch.

    Raises:
        StateCompilerError: If rows or query coverage drift.

    Example:
        ``batch = buildProviderObservationBatch(rows, providerId="edgar", ...)``
    """

    cutoff = _dateText(cutoffAsOf, "cutoffAsOf")
    scope = tuple(sorted(set(signalIds)))
    if not providerId or not datasetId or not entityId or not scope:
        raise StateCompilerError("provider observation query is incomplete")
    eligible = []
    for observation in observations:
        _validateObservation(observation)
        if (
            observation.providerId != providerId
            or observation.datasetId != datasetId
            or observation.entityId != entityId
            or observation.signalId not in scope
        ):
            raise StateCompilerError("observation is outside its provider batch query")
        if _dateText(observation.knowledgeAsOf, "knowledgeAsOf") <= cutoff:
            eligible.append(observation)
    ordered = tuple(
        sorted(
            eligible,
            key=lambda item: (item.signalId, item.eventAt, item.availableAt, item.observationId),
        )
    )
    queryHash = canonicalPayloadHash(
        _queryPayload(
            providerId=providerId,
            datasetId=datasetId,
            entityId=entityId,
            signalIds=scope,
            cutoffAsOf=cutoff,
        )
    )
    sourceReceiptIds = tuple(sorted({item.vintage.receiptId for item in ordered if item.vintage.receiptId}))
    policies = {item.vintage.revisionPolicy for item in ordered}
    coverages = {item.vintage.coverage for item in ordered}
    historyStatus = "exact" if policies == {"asKnown"} and coverages == {"asOfExact"} else "conditional"
    provisional = ProviderObservationBatch(
        batchId="",
        batchReceiptId="",
        queryContractHash=queryHash,
        providerId=providerId,
        datasetId=datasetId,
        entityId=entityId,
        signalIds=scope,
        cutoffAsOf=cutoff,
        observations=ordered,
        observationRoot=canonicalPayloadHash(tuple(item.observationId for item in ordered)),
        sourceReceiptIds=sourceReceiptIds,
        historyStatus=historyStatus,
    )
    return replace(provisional, batchId=canonicalPayloadHash(_batchPayload(provisional)))


def _validateBatch(batch: ProviderObservationBatch) -> None:
    expected = buildProviderObservationBatch(
        batch.observations,
        providerId=batch.providerId,
        datasetId=batch.datasetId,
        entityId=batch.entityId,
        signalIds=batch.signalIds,
        cutoffAsOf=batch.cutoffAsOf,
    )
    if replace(batch, batchReceiptId="") != expected:
        raise StateCompilerError("provider observation batch does not reproduce")


def issueProviderObservationBatch(
    batch: ProviderObservationBatch,
    databasePath: str | Path,
    artifactRoot: str | Path,
    *,
    privateKey: bytes,
    issuerId: str,
    issuerKeyId: str,
    issuedAt: str,
    trustedIssuers: Mapping[str, TrustedIssuer],
) -> ProviderObservationBatch:
    """Issue a fixed-rule receipt for one complete provider query.

    Args:
        batch: Reproducible unsigned provider observation batch.
        databasePath: Append-only admission registry.
        artifactRoot: Content-addressed artifact store.
        privateKey: Provider-batch issuer private key bytes.
        issuerId: Trusted provider-batch issuer identity.
        issuerKeyId: Trusted provider-batch key identity.
        issuedAt: Registry issue time.
        trustedIssuers: Runtime issuer allowlist.

    Returns:
        Same batch carrying its verified-vintage receipt ID.

    Raises:
        StateCompilerError: If the batch or every used source is not exact.

    Example:
        ``signed = issueProviderObservationBatch(batch, registry, artifacts, ...)``
    """

    _validateBatch(batch)
    requiredParents = tuple(sorted({item.vintage.receiptId for item in batch.observations}))
    if (
        batch.batchReceiptId
        or batch.historyStatus != "exact"
        or not requiredParents
        or any(not _validDigest(item) for item in requiredParents)
        or batch.sourceReceiptIds != requiredParents
    ):
        raise StateCompilerError("exact provider batch needs every signed source")
    artifactHash = putAdmissionArtifact(artifactRoot, canonicalPayloadBytes(_batchPayload(batch)))
    if artifactHash != batch.batchId:
        raise StateCompilerError("provider observation batch artifact mismatch")
    receipt = issueAdmissionReceipt(
        databasePath,
        artifactRoot,
        privateKey=privateKey,
        kind="providerObservationBatch",
        subjectHash=batch.queryContractHash,
        artifactHash=artifactHash,
        parentReceiptIds=batch.sourceReceiptIds,
        ruleId=OBSERVATION_BATCH_RULE_ID,
        ruleVersion=OBSERVATION_BATCH_RULE_VERSION,
        ruleHash=OBSERVATION_BATCH_RULE_HASH,
        issuerId=issuerId,
        issuerKeyId=issuerKeyId,
        issuerExecutableHash=OBSERVATION_BATCH_EXECUTABLE_HASH,
        knowledgeAsOf=batch.cutoffAsOf,
        revisionPolicy="asKnown",
        coverage="asOfExact",
        frequency="mixed",
        stepSpan=1,
        maxAdmittedStep=0,
        status="verifiedVintage",
        issuedAt=issuedAt,
        trustedIssuers=trustedIssuers,
    )
    return replace(batch, batchReceiptId=receipt.receiptId)


def _verifyBatch(
    batch: ProviderObservationBatch,
    verifier: AdmissionVerifier,
    *,
    decisionAsOf: str,
) -> AdmissionReceipt:
    _validateBatch(batch)
    if not _validDigest(batch.batchReceiptId):
        raise StateCompilerError("provider observation batch is not signed")
    try:
        receipt = verifier.verify(
            batch.batchReceiptId,
            expectedSubjectHash=batch.queryContractHash,
            expectedKind="providerObservationBatch",
        )
    except RuntimeError as error:
        raise StateCompilerError(f"provider observation batch failed: {error}") from error
    for observation in batch.observations:
        try:
            source = verifier.verify(
                observation.vintage.receiptId,
                expectedKind="dataVintage",
            )
        except RuntimeError as error:
            raise StateCompilerError(f"provider observation source failed: {error}") from error
        if (
            source.artifactHash != observation.vintage.artifactHash
            or source.subjectHash != observation.vintage.payloadHash
            or source.knowledgeAsOf != observation.vintage.knowledgeAsOf
            or source.status != "verifiedVintage"
            or source.revisionPolicy != "asKnown"
            or source.coverage != "asOfExact"
            or _dateText(source.issuedAt, "source issuedAt") > _dateText(decisionAsOf, "decisionAsOf")
        ):
            raise StateCompilerError("provider observation source contract mismatch")
    if (
        receipt.artifactHash != batch.batchId
        or receipt.parentReceiptIds != batch.sourceReceiptIds
        or (receipt.ruleId, receipt.ruleVersion, receipt.ruleHash)
        != (OBSERVATION_BATCH_RULE_ID, OBSERVATION_BATCH_RULE_VERSION, OBSERVATION_BATCH_RULE_HASH)
        or receipt.issuerExecutableHash != OBSERVATION_BATCH_EXECUTABLE_HASH
        or receipt.status != "verifiedVintage"
        or receipt.revisionPolicy != "asKnown"
        or receipt.coverage != "asOfExact"
        or receipt.knowledgeAsOf != batch.cutoffAsOf
        or _dateText(receipt.issuedAt, "batch issuedAt") > _dateText(decisionAsOf, "decisionAsOf")
        or artifactPath(verifier.artifactRoot, batch.batchId).read_bytes()
        != canonicalPayloadBytes(_batchPayload(replace(batch, batchReceiptId="")))
    ):
        raise StateCompilerError("provider observation batch signed contract mismatch")
    return receipt


def validateProviderObservationBatch(
    batch: ProviderObservationBatch,
    admissionVerifier: AdmissionVerifier,
    *,
    decisionAsOf: str | None = None,
) -> AdmissionReceipt:
    """Validate one signed complete provider query and all exact source parents.

    Args:
        batch: Signed provider observation batch to reproduce and verify.
        admissionVerifier: Runtime receipt, trusted issuer, and artifact verifier.
        decisionAsOf: Optional consumer cutoff. Defaults to the batch cutoff and cannot
            precede it.

    Returns:
        Verified provider observation batch receipt.

    Raises:
        StateCompilerError: If content, query, source receipts, issue timing, or exact
            as-known coverage drifts.

    Example:
        ``receipt = validateProviderObservationBatch(batch, verifier, decisionAsOf="20251231")``
    """

    decision = _dateText(decisionAsOf or batch.cutoffAsOf, "decisionAsOf")
    if _dateText(batch.cutoffAsOf, "batch.cutoffAsOf") > decision:
        raise StateCompilerError("provider observation batch is newer than the consumer cutoff")
    return _verifyBatch(batch, admissionVerifier, decisionAsOf=decision)


def _aggregateVintage(selected: tuple[VariableObservation, ...]) -> tuple[str, str]:
    policies = {item.vintage.revisionPolicy for item in selected}
    coverages = {item.vintage.coverage for item in selected}
    return (
        next(iter(policies)) if len(policies) == 1 else "synthetic",
        next(iter(coverages)) if len(coverages) == 1 else "synthetic",
    )


def _manifestPayload(
    *,
    registry: StateVariableRegistry,
    selectedSpecs: tuple[StateVariableSpec, ...],
    spec: StateCompileSpec,
    primitives: tuple[StatePrimitive, ...],
    selected: tuple[VariableObservation, ...],
    batches: tuple[ProviderObservationBatch, ...],
    compilationContractHash: str,
    historyStatus: str,
    revisionPolicy: str,
    coverage: str,
    limitations: tuple[str, ...],
) -> dict:
    return {
        "schemaVersion": COMPILED_PIT_STATE_SCHEMA,
        "registry": registry,
        "selectedSpecs": selectedSpecs,
        "compileSpec": spec,
        "stateContractHash": stateContractHash(primitives),
        "stateCompilationContractHash": compilationContractHash,
        "knowledgeAsOf": max(item.knowledgeAsOf for item in selected),
        "statePrimitives": primitives,
        "selectedObservationIds": tuple(item.observationId for item in selected),
        "providerBatchIds": tuple(item.batchId for item in batches),
        "providerBatchReceiptIds": tuple(item.batchReceiptId for item in batches),
        "historyStatus": historyStatus,
        "admissionStatus": "documented",
        "aggregateRevisionPolicy": revisionPolicy,
        "aggregateCoverage": coverage,
        "limitations": limitations,
    }


def compilePointInTimeState(
    registry: StateVariableRegistry,
    batches: tuple[ProviderObservationBatch, ...],
    spec: StateCompileSpec,
    *,
    admissionVerifier: AdmissionVerifier | None = None,
) -> CompiledPointInTimeState:
    """Compile an as-of state only from complete provider batches.

    Args:
        registry: Frozen meaning and source contract.
        batches: One complete batch per required provider and dataset query.
        spec: Consumer, entity, cutoff, and exactness contract.
        admissionVerifier: Required to verify signed provider batches.

    Returns:
        Deterministic state, manifest, history status, and admission status.

    Raises:
        StateCompilerError: If required data, meaning, freshness, or lineage fails.

    Example:
        ``compiled = compilePointInTimeState(registry, batches, spec)``
    """

    try:
        expectedRegistry = buildStateVariableRegistry(registry.specs)
    except StateVariableError as error:
        raise StateCompilerError(str(error)) from error
    if registry != expectedRegistry or spec.schemaVersion != STATE_COMPILE_SPEC_SCHEMA:
        raise StateCompilerError("state compilation protocol mismatch")
    decision = _dateText(spec.decisionAsOf, "decisionAsOf")
    if not spec.entityId or not spec.market or not spec.consumerId or not spec.consumerVersion:
        raise StateCompilerError("state compile consumer contract is incomplete")
    variableIds = tuple(sorted(spec.variableIds))
    if not variableIds or len(set(variableIds)) != len(variableIds):
        raise StateCompilerError("state compile needs unique required variables")
    byId = {item.variableId: item for item in registry.specs}
    unknown = sorted(set(variableIds) - set(byId))
    if unknown:
        raise StateCompilerError(f"state compile has unknown variables: {unknown}")
    selectedSpecs = tuple(byId[item] for item in variableIds)
    expectedGroups: dict[tuple[str, str], tuple[str, ...]] = {}
    for item in selectedSpecs:
        key = (item.providerId, item.datasetId)
        expectedGroups[key] = tuple(sorted((*expectedGroups.get(key, ()), item.signalId)))
    batchByGroup: dict[tuple[str, str], ProviderObservationBatch] = {}
    for batch in batches:
        key = (batch.providerId, batch.datasetId)
        if key in batchByGroup:
            raise StateCompilerError("duplicate provider observation batch")
        batchByGroup[key] = batch
    if set(batchByGroup) != set(expectedGroups):
        raise StateCompilerError("provider observation batch coverage is incomplete")
    inputsVerified = admissionVerifier is not None
    orderedBatches = tuple(batchByGroup[key] for key in sorted(batchByGroup))
    for key, signals in expectedGroups.items():
        batch = batchByGroup[key]
        if batch.entityId != spec.entityId or batch.cutoffAsOf != decision or batch.signalIds != signals:
            raise StateCompilerError("provider observation batch query contract mismatch")
        if admissionVerifier is not None:
            _verifyBatch(batch, admissionVerifier, decisionAsOf=decision)
        elif batch.batchReceiptId:
            raise StateCompilerError("signed provider batch needs a runtime verifier")
    limitations: list[str] = []
    historyExact = True
    selectedRows: list[VariableObservation] = []
    primitives: list[StatePrimitive] = []
    for variable in selectedSpecs:
        batch = batchByGroup[(variable.providerId, variable.datasetId)]
        candidates = tuple(item for item in batch.observations if item.signalId == variable.signalId)
        if not candidates:
            raise StateCompilerError(f"required state observation is missing: {variable.variableId}")
        eligible = []
        for observation in candidates:
            _validateObservation(observation)
            if _dateText(observation.knowledgeAsOf, "knowledgeAsOf") > decision:
                continue
            if (
                observation.unit != variable.unit
                or observation.frequency != variable.frequency
                or observation.timing != variable.timing
                or observation.transformId != variable.transformId
                or observation.evidenceRole != variable.evidenceRole
            ):
                raise StateCompilerError(f"state observation meaning drift: {variable.variableId}")
            try:
                validateVintageRef(observation.vintage, decisionAsOf=decision)
            except VintageError as error:
                raise StateCompilerError(str(error)) from error
            eligible.append(observation)
        if not eligible:
            raise StateCompilerError(f"required state observation is future-only: {variable.variableId}")
        ordered = sorted(
            eligible,
            key=lambda item: (item.eventAt, item.availableAt, item.knowledgeAsOf, item.revisionId, item.observationId),
        )
        topKey = (
            ordered[-1].eventAt,
            ordered[-1].availableAt,
            ordered[-1].knowledgeAsOf,
            ordered[-1].revisionId,
        )
        tied = [
            item for item in ordered if (item.eventAt, item.availableAt, item.knowledgeAsOf, item.revisionId) == topKey
        ]
        if len({item.observationId for item in tied}) != 1:
            raise StateCompilerError(f"ambiguous state observation revision: {variable.variableId}")
        selected = ordered[-1]
        age = (_dateValue(decision, "decisionAsOf") - _dateValue(selected.availableAt, "availableAt")).days
        if age > variable.maxStalenessDays:
            raise StateCompilerError(f"required state observation is stale: {variable.variableId}")
        number = float(selected.value)
        if variable.lower is not None and number < variable.lower:
            raise StateCompilerError(f"state value is below its bound: {variable.variableId}")
        if variable.upper is not None and number > variable.upper:
            raise StateCompilerError(f"state value is above its bound: {variable.variableId}")
        selectedExact = (
            isExactAsKnown(selected.vintage)
            and selected.evidenceRole in {"observed", "deterministicDerived", "admittedEstimate"}
            and _dateText(selected.availableAt, "availableAt") != decision
        )
        if not selectedExact:
            historyExact = False
            limitations.append(f"conditionalObservation:{variable.variableId}")
        selectedRows.append(selected)
        primitives.append(
            StatePrimitive(
                variableId=variable.variableId,
                unit=variable.unit,
                role=variable.role,
                value=number,
                frequency=variable.frequency,
                timing=variable.timing,
                transformId=variable.transformId,
                evidenceRole=variable.evidenceRole,
            )
        )
    if spec.requireExact and not historyExact:
        raise StateCompilerError("state compile requires exact as-known observations")
    if not inputsVerified:
        limitations.append("unsignedProviderBatches")
    primitiveTuple = tuple(primitives)
    selectedTuple = tuple(selectedRows)
    stateContract = stateContractHash(primitiveTuple)
    variableContract = stateVariableContractHash(selectedSpecs)
    if stateContract != variableContract:
        raise StateCompilerError("compiled primitive contract drifted from the variable registry")
    compilationContract = canonicalPayloadHash(
        {
            "registryHash": registry.registryHash,
            "stateContractHash": stateContract,
            "consumerId": spec.consumerId,
            "consumerVersion": spec.consumerVersion,
            "variableIds": variableIds,
            "providerQueries": tuple((key, expectedGroups[key]) for key in sorted(expectedGroups)),
            "selectionRuleId": STATE_SELECTION_RULE_ID,
            "cutoffPolicyId": STATE_CUTOFF_POLICY_ID,
            "compilerExecutableHash": PIT_STATE_EXECUTABLE_HASH,
        }
    )
    historyStatus = "exact" if historyExact else "conditional"
    revisionPolicy, coverage = _aggregateVintage(selectedTuple)
    limitationTuple = tuple(sorted(set(limitations)))
    manifestPayload = _manifestPayload(
        registry=registry,
        selectedSpecs=selectedSpecs,
        spec=replace(spec, decisionAsOf=decision, variableIds=variableIds),
        primitives=primitiveTuple,
        selected=selectedTuple,
        batches=orderedBatches,
        compilationContractHash=compilationContract,
        historyStatus=historyStatus,
        revisionPolicy=revisionPolicy,
        coverage=coverage,
        limitations=limitationTuple,
    )
    artifact = canonicalPayloadBytes(manifestPayload)
    knowledgeAsOf = max(item.knowledgeAsOf for item in selectedTuple)
    stateId = stateAdmissionSubjectHash(
        primitiveTuple,
        asOf=decision,
        knowledgeAsOf=knowledgeAsOf,
        decisionAsOf=decision,
    )
    return CompiledPointInTimeState(
        stateId=stateId,
        manifestHash=canonicalPayloadHash(manifestPayload),
        registryHash=registry.registryHash,
        stateContractHash=stateContract,
        stateCompilationContractHash=compilationContract,
        entityId=spec.entityId,
        market=spec.market,
        decisionAsOf=decision,
        knowledgeAsOf=knowledgeAsOf,
        statePrimitives=primitiveTuple,
        selectedObservationIds=tuple(item.observationId for item in selectedTuple),
        providerBatchIds=tuple(item.batchId for item in orderedBatches),
        providerBatchReceiptIds=tuple(item.batchReceiptId for item in orderedBatches),
        historyStatus=historyStatus,
        admissionStatus="documented",
        aggregateRevisionPolicy=revisionPolicy,
        aggregateCoverage=coverage,
        limitations=limitationTuple,
        manifestArtifact=artifact,
    )


def issuePointInTimeState(
    compiled: CompiledPointInTimeState,
    databasePath: str | Path,
    artifactRoot: str | Path,
    *,
    privateKey: bytes,
    issuerId: str,
    issuerKeyId: str,
    issuedAt: str,
    trustedIssuers: Mapping[str, TrustedIssuer],
) -> CompiledPointInTimeState:
    """Issue a state receipt whose exact parents are complete provider batches.

    Args:
        compiled: Exact documented state built with verified provider batches.
        databasePath: Append-only admission registry.
        artifactRoot: Content-addressed artifact store.
        privateKey: State-compiler issuer private key bytes.
        issuerId: Trusted state-compiler issuer identity.
        issuerKeyId: Trusted state-compiler key identity.
        issuedAt: State receipt issue time.
        trustedIssuers: Runtime issuer allowlist.

    Returns:
        Compiled state promoted to admitted with its receipt ID.

    Raises:
        StateCompilerError: If state or parent coverage is not exact.

    Example:
        ``issued = issuePointInTimeState(compiled, registry, artifacts, ...)``
    """

    if (
        compiled.stateReceiptId
        or compiled.historyStatus != "exact"
        or compiled.admissionStatus != "documented"
        or "unsignedProviderBatches" in compiled.limitations
        or not compiled.providerBatchReceiptIds
        or any(not _validDigest(item) for item in compiled.providerBatchReceiptIds)
    ):
        raise StateCompilerError("only exact verified compiled states can be issued")
    artifactHash = putAdmissionArtifact(artifactRoot, compiled.manifestArtifact)
    if artifactHash != compiled.manifestHash:
        raise StateCompilerError("compiled state manifest artifact mismatch")
    receipt = issueAdmissionReceipt(
        databasePath,
        artifactRoot,
        privateKey=privateKey,
        kind="pointInTimeState",
        subjectHash=compiled.stateId,
        artifactHash=artifactHash,
        parentReceiptIds=compiled.providerBatchReceiptIds,
        ruleId=PIT_STATE_RULE_ID,
        ruleVersion=PIT_STATE_RULE_VERSION,
        ruleHash=PIT_STATE_RULE_HASH,
        issuerId=issuerId,
        issuerKeyId=issuerKeyId,
        issuerExecutableHash=PIT_STATE_EXECUTABLE_HASH,
        knowledgeAsOf=compiled.knowledgeAsOf,
        revisionPolicy="asKnown",
        coverage="asOfExact",
        frequency="mixed",
        stepSpan=1,
        maxAdmittedStep=0,
        status="verifiedVintage",
        issuedAt=issuedAt,
        trustedIssuers=trustedIssuers,
    )
    return replace(compiled, admissionStatus="admitted", stateReceiptId=receipt.receiptId)


def _vintageFromPayload(payload: dict) -> VintageRef:
    try:
        payload = dict(payload)
        payload["sourceRefs"] = tuple(payload.get("sourceRefs", ()))
        return VintageRef(**payload)
    except (KeyError, TypeError, ValueError) as error:
        raise StateCompilerError("provider batch vintage payload is malformed") from error


def _observationFromPayload(payload: dict) -> VariableObservation:
    try:
        payload = dict(payload)
        payload["vintage"] = _vintageFromPayload(payload["vintage"])
        return VariableObservation(**payload)
    except (KeyError, TypeError, ValueError) as error:
        raise StateCompilerError("provider batch observation payload is malformed") from error


def _batchFromArtifact(receipt: AdmissionReceipt, raw: bytes) -> ProviderObservationBatch:
    try:
        payload = json.loads(raw)
        if canonicalPayloadBytes(payload) != raw:
            raise StateCompilerError("provider batch artifact is not canonical")
        payload["signalIds"] = tuple(payload["signalIds"])
        payload["observations"] = tuple(_observationFromPayload(item) for item in payload["observations"])
        payload["sourceReceiptIds"] = tuple(payload["sourceReceiptIds"])
        batch = ProviderObservationBatch(
            batchId=receipt.artifactHash,
            batchReceiptId=receipt.receiptId,
            **payload,
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise StateCompilerError("provider batch artifact is malformed") from error
    _validateBatch(batch)
    return batch


def _manifestInputs(
    raw: bytes, verifier: AdmissionVerifier
) -> tuple[
    StateVariableRegistry,
    tuple[ProviderObservationBatch, ...],
    StateCompileSpec,
    dict,
]:
    try:
        payload = json.loads(raw)
        if canonicalPayloadBytes(payload) != raw:
            raise StateCompilerError("point-in-time manifest is not canonical")
        registryPayload = payload["registry"]
        registry = StateVariableRegistry(
            specs=tuple(StateVariableSpec(**item) for item in registryPayload["specs"]),
            registryHash=registryPayload["registryHash"],
            schemaVersion=registryPayload["schemaVersion"],
        )
        specPayload = dict(payload["compileSpec"])
        specPayload["variableIds"] = tuple(specPayload["variableIds"])
        spec = StateCompileSpec(**specPayload)
        receiptIds = tuple(payload["providerBatchReceiptIds"])
        batches = []
        for receiptId in receiptIds:
            receipt = verifier.verify(receiptId, expectedKind="providerObservationBatch")
            batchRaw = artifactPath(verifier.artifactRoot, receipt.artifactHash).read_bytes()
            batches.append(_batchFromArtifact(receipt, batchRaw))
        return registry, tuple(batches), spec, payload
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        if isinstance(error, StateCompilerError):
            raise
        raise StateCompilerError("point-in-time manifest payload is malformed") from error


def validatePointInTimeStateReceipt(
    *,
    statePrimitives: tuple[StatePrimitive, ...],
    asOf: str,
    knowledgeAsOf: str,
    decisionAsOf: str,
    stateCompilationContractHash: str,
    stateManifestHash: str,
    stateReceiptId: str,
    admissionVerifier: AdmissionVerifier,
) -> AdmissionReceipt:
    """Recompile a signed PIT manifest and validate its exact parent coverage.

    Args:
        statePrimitives: Exact executable-visible state expected by the caller.
        asOf: Aggregate state label used by the initial-state artifact.
        knowledgeAsOf: Latest selected observation knowledge cutoff.
        decisionAsOf: Decision cutoff used by the compiler.
        stateCompilationContractHash: Expected registry, query, and compiler contract.
        stateManifestHash: Expected complete manifest artifact hash.
        stateReceiptId: Fixed-rule point-in-time state receipt.
        admissionVerifier: Runtime receipt and artifact verifier.

    Returns:
        Verified point-in-time state receipt.

    Raises:
        StateCompilerError: If manifest, recompilation, rule, or parent tuple fails.

    Example:
        ``receipt = validatePointInTimeStateReceipt(..., admissionVerifier=verifier)``
    """

    stateId = stateAdmissionSubjectHash(
        statePrimitives,
        asOf=asOf,
        knowledgeAsOf=knowledgeAsOf,
        decisionAsOf=decisionAsOf,
    )
    try:
        receipt = admissionVerifier.verify(
            stateReceiptId,
            expectedSubjectHash=stateId,
            expectedKind="pointInTimeState",
        )
    except RuntimeError as error:
        raise StateCompilerError(f"point-in-time state receipt failed: {error}") from error
    if (
        receipt.artifactHash != stateManifestHash
        or (receipt.ruleId, receipt.ruleVersion, receipt.ruleHash)
        != (PIT_STATE_RULE_ID, PIT_STATE_RULE_VERSION, PIT_STATE_RULE_HASH)
        or receipt.issuerExecutableHash != PIT_STATE_EXECUTABLE_HASH
        or receipt.status != "verifiedVintage"
        or receipt.revisionPolicy != "asKnown"
        or receipt.coverage != "asOfExact"
        or receipt.knowledgeAsOf != _dateText(knowledgeAsOf, "knowledgeAsOf")
        or _dateText(receipt.issuedAt, "state issuedAt") > _dateText(decisionAsOf, "decisionAsOf")
    ):
        raise StateCompilerError("point-in-time state signed contract mismatch")
    raw = artifactPath(admissionVerifier.artifactRoot, stateManifestHash).read_bytes()
    registry, batches, spec, payload = _manifestInputs(raw, admissionVerifier)
    rebuilt = compilePointInTimeState(registry, batches, spec, admissionVerifier=admissionVerifier)
    if (
        rebuilt.manifestArtifact != raw
        or rebuilt.manifestHash != stateManifestHash
        or rebuilt.stateId != stateId
        or rebuilt.statePrimitives != statePrimitives
        or rebuilt.knowledgeAsOf != _dateText(knowledgeAsOf, "knowledgeAsOf")
        or rebuilt.decisionAsOf != _dateText(decisionAsOf, "decisionAsOf")
        or rebuilt.stateCompilationContractHash != stateCompilationContractHash
        or rebuilt.providerBatchReceiptIds != receipt.parentReceiptIds
        or tuple(payload["providerBatchIds"]) != tuple(item.batchId for item in batches)
    ):
        raise StateCompilerError("point-in-time state manifest does not reproduce")
    return receipt


def validateCompiledPointInTimeState(
    compiled: CompiledPointInTimeState,
    admissionVerifier: AdmissionVerifier,
) -> AdmissionReceipt:
    """Validate an issued compiled state through the raw manifest replay path.

    Args:
        compiled: Admitted compiled point-in-time state.
        admissionVerifier: Runtime receipt and artifact verifier.

    Returns:
        Verified point-in-time state receipt.

    Raises:
        StateCompilerError: If the compiled object or lineage was changed.

    Example:
        ``receipt = validateCompiledPointInTimeState(compiled, verifier)``
    """

    if compiled.admissionStatus != "admitted" or not compiled.stateReceiptId:
        raise StateCompilerError("compiled state is not admitted")
    return validatePointInTimeStateReceipt(
        statePrimitives=compiled.statePrimitives,
        asOf=compiled.decisionAsOf,
        knowledgeAsOf=compiled.knowledgeAsOf,
        decisionAsOf=compiled.decisionAsOf,
        stateCompilationContractHash=compiled.stateCompilationContractHash,
        stateManifestHash=compiled.manifestHash,
        stateReceiptId=compiled.stateReceiptId,
        admissionVerifier=admissionVerifier,
    )
