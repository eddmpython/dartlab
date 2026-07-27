"""Decision-time state compilation and the pre-run input contract gate.

실행기가 첫 기간을 굴리기 전에 통과해야 하는 관문을 전부 모았다. 초기 상태를 타입 있는
primitive 로 컴파일하는 일, 그 상태와 경로 집합의 서명 admission 을 검증하는 일, 그리고
경로, 전략, 가중치, 인증 지평이 서로 모순 없는지 보는 일은 모두 "입력이 말이 되는가"라는
하나의 질문이다. 실행 경로에는 이 중 어느 것도 없다.

경계를 그을 때 순서는 손대지 않았다. 검사 순서가 곧 사용자가 처음 받는 에러 메시지를
정하는 계약이라, 함수로 나누되 호출 순서와 그 안의 문장 순서는 원문 그대로 두었다.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Mapping

from dartlab.simulate.parameterDraws import validateParameterDrawSetReceipt
from dartlab.simulate.stateCompiler import (
    CompiledPointInTimeState,
    validatePointInTimeStateReceipt,
)
from dartlab.simulate.stateSupport import (
    INITIAL_STATE_RULE_HASH,
    INITIAL_STATE_RULE_ID,
    INITIAL_STATE_RULE_VERSION,
    StatePrimitive,
    StateSupportError,
    stateAdmissionArtifact,
    stateAdmissionSubjectHash,
)
from dartlab.simulate.vintage import (
    VintageError,
    VintageRef,
    isExactAsKnown,
    validateVintageRef,
    worldStatePayloadHash,
)
from dartlab.simulate.worldContracts import _pathSetContentHash, _validateLawCertificate
from dartlab.simulate.worldModel import WorldModel
from dartlab.simulate.worldTypes import (
    PATH_VALIDATION_SET,
    WEIGHT_KIND_SET,
    ScenarioPath,
    SimulationBlocked,
    SimulationSpecError,
    StrategySpec,
    WorldState,
    _comparableDate,
    _finite,
    _validDigest,
)

if TYPE_CHECKING:
    from dartlab.simulate.admissionRegistry import AdmissionVerifier


def _validateValue(model: WorldModel, variableId: str, value: float | None, label: str) -> float:
    number = _finite(value, label)
    spec = next(v for v in model.variables if v.variableId == variableId)
    if spec.lower is not None and number < spec.lower - 1e-12:
        raise SimulationBlocked(f"{label} below lower bound")
    if spec.upper is not None and number > spec.upper + 1e-12:
        raise SimulationBlocked(f"{label} above upper bound")
    return number


def initialStatePrimitives(model: WorldModel, initial: WorldState) -> tuple[StatePrimitive, ...]:
    """Compile every model-visible initial value into a typed primitive.

    Args:
        model: Variable registry used by the executable.
        initial: Initial values visible to transition laws and policies.

    Returns:
        Variable-id sorted primitives containing unit, role, and finite value.

    Raises:
        SimulationSpecError: If an input is unknown, a shock, missing, or non-finite.

    Example:
        ``state = initialStatePrimitives(model, initial)``
    """

    byId = {variable.variableId: variable for variable in model.variables}
    unknown = sorted(set(initial.values) - set(byId))
    if unknown:
        raise SimulationSpecError(f"unknown initial variables: {unknown}")
    primitives = []
    for variableId in sorted(initial.values):
        spec = byId[variableId]
        if spec.role in {"shock", "metric"}:
            raise SimulationSpecError(f"initial state cannot contain a {spec.role} variable: {variableId}")
        primitives.append(
            StatePrimitive(
                variableId=variableId,
                unit=spec.unit,
                role=spec.role,
                value=_validateValue(model, variableId, initial.values[variableId], f"initial.{variableId}"),
                frequency=spec.frequency,
                timing=spec.timing,
                transformId=spec.transformId,
                evidenceRole=spec.evidenceRole,
            )
        )
    return tuple(primitives)


def worldStateFromCompiled(compiled: CompiledPointInTimeState) -> WorldState:
    """Bind a compiled PIT state to the generic world runtime contract.

    Args:
        compiled: Deterministic state compiled from complete provider batches.

    Returns:
        World state whose values and aggregate vintage derive from the manifest.

    Raises:
        SimulationSpecError: If compiled identity or admission fields drift.

    Example:
        ``initial = worldStateFromCompiled(compiled)``
    """

    if compiled.schemaVersion != "compiled-point-in-time-state-v1":
        raise SimulationSpecError("compiled point-in-time state protocol mismatch")
    if compiled.admissionStatus not in {"documented", "admitted"}:
        raise SimulationSpecError("compiled point-in-time state admission status is invalid")
    if compiled.admissionStatus == "admitted" and not _validDigest(compiled.stateReceiptId):
        raise SimulationSpecError("admitted point-in-time state needs a signed receipt")
    values = {item.variableId: float(item.value) for item in compiled.statePrimitives}
    refs = (f"stateManifest:{compiled.manifestHash}",)
    payloadHash = worldStatePayloadHash(values, step=0, asOf=compiled.decisionAsOf, refs=refs)
    vintage = VintageRef(
        artifactKind="worldState",
        provider="dartlab.stateCompiler",
        artifactId=compiled.stateId,
        artifactHash=compiled.manifestHash,
        payloadHash=payloadHash,
        knowledgeAsOf=compiled.knowledgeAsOf,
        availableAt=compiled.knowledgeAsOf,
        revisionPolicy=compiled.aggregateRevisionPolicy,
        coverage=compiled.aggregateCoverage,
        receiptId=compiled.stateReceiptId,
        contractHash=compiled.stateCompilationContractHash,
        sourceRefs=compiled.providerBatchIds,
    )
    return WorldState(
        values=values,
        asOf=compiled.decisionAsOf,
        refs=refs,
        knowledgeAsOf=compiled.knowledgeAsOf,
        decisionAsOf=compiled.decisionAsOf,
        vintage=vintage,
        stateCompilationContractHash=compiled.stateCompilationContractHash,
        stateManifestHash=compiled.manifestHash,
    )


def initialStateAdmissionArtifact(model: WorldModel, initial: WorldState) -> bytes:
    """Return canonical bytes for the exact executable-visible initial state.

    Args:
        model: Variable registry defining identifiers, units, roles, and bounds.
        initial: Decision-time state with knowledge and decision cutoffs.

    Returns:
        Canonical JSON bytes for a typed ``initialState`` admission receipt.

    Raises:
        SimulationSpecError: If the visible state or cutoffs are incomplete.

    Example:
        ``artifact = initialStateAdmissionArtifact(model, initial)``
    """

    knowledgeAsOf = initial.knowledgeAsOf or initial.asOf
    decisionAsOf = initial.decisionAsOf or knowledgeAsOf
    try:
        return stateAdmissionArtifact(
            initialStatePrimitives(model, initial),
            asOf=initial.asOf,
            knowledgeAsOf=knowledgeAsOf,
            decisionAsOf=decisionAsOf,
        )
    except StateSupportError as error:
        raise SimulationSpecError(str(error)) from error


def initialStateAdmissionSubjectHash(model: WorldModel, initial: WorldState) -> str:
    """Return the exact subject hash a typed initial-state receipt must sign.

    Args:
        model: Variable registry defining the visible state contract.
        initial: Decision-time state and temporal cutoffs.

    Returns:
        SHA-256 digest of ``initialStateAdmissionArtifact``.

    Raises:
        SimulationSpecError: If the state cannot be compiled.

    Example:
        ``subject = initialStateAdmissionSubjectHash(model, initial)``
    """

    knowledgeAsOf = initial.knowledgeAsOf or initial.asOf
    decisionAsOf = initial.decisionAsOf or knowledgeAsOf
    try:
        return stateAdmissionSubjectHash(
            initialStatePrimitives(model, initial),
            asOf=initial.asOf,
            knowledgeAsOf=knowledgeAsOf,
            decisionAsOf=decisionAsOf,
        )
    except StateSupportError as error:
        raise SimulationSpecError(str(error)) from error


def _validateInitialStateAdmission(
    model: WorldModel,
    initial: WorldState,
    admissionVerifier: AdmissionVerifier | None,
) -> None:
    if not initial.admissionReceiptId:
        return
    if not _validDigest(initial.admissionReceiptId):
        raise SimulationSpecError("initial-state admission receipt identifier is invalid")
    if admissionVerifier is None:
        raise SimulationSpecError("initial-state admission needs a runtime admission verifier")
    if initial.vintage is None or not isExactAsKnown(initial.vintage):
        raise SimulationSpecError("initial-state admission needs an exact as-known current state vintage")
    if not _validDigest(initial.vintage.receiptId):
        raise SimulationSpecError("initial-state admission needs a signed point-in-time state receipt")
    if not (_validDigest(initial.stateCompilationContractHash) and _validDigest(initial.stateManifestHash)):
        raise SimulationSpecError("initial-state admission needs signed current state lineage")
    knowledgeAsOf = initial.knowledgeAsOf or initial.asOf
    decisionAsOf = initial.decisionAsOf or knowledgeAsOf
    initialArtifact = initialStateAdmissionArtifact(model, initial)
    initialSubjectHash = initialStateAdmissionSubjectHash(model, initial)
    try:
        from dartlab.simulate.admissionRegistry import artifactPath

        pointInTimeReceipt = validatePointInTimeStateReceipt(
            statePrimitives=initialStatePrimitives(model, initial),
            asOf=initial.asOf,
            knowledgeAsOf=knowledgeAsOf,
            decisionAsOf=decisionAsOf,
            stateCompilationContractHash=initial.stateCompilationContractHash,
            stateManifestHash=initial.stateManifestHash,
            stateReceiptId=initial.vintage.receiptId,
            admissionVerifier=admissionVerifier,
        )
        initialReceipt = admissionVerifier.verify(
            initial.admissionReceiptId,
            expectedSubjectHash=initialSubjectHash,
            expectedKind="initialState",
        )
    except (OSError, RuntimeError, ValueError) as error:
        raise SimulationSpecError(f"initial-state admission verification failed: {error}") from error
    receiptIssuedAt = _comparableDate(initialReceipt.issuedAt)
    if (
        initialReceipt.status != "admitted"
        or initialReceipt.artifactHash != initialSubjectHash
        or (initialReceipt.ruleId, initialReceipt.ruleVersion, initialReceipt.ruleHash)
        != (INITIAL_STATE_RULE_ID, INITIAL_STATE_RULE_VERSION, INITIAL_STATE_RULE_HASH)
        or initialReceipt.parentReceiptIds != (pointInTimeReceipt.receiptId,)
        or receiptIssuedAt is None
        or receiptIssuedAt > _comparableDate(decisionAsOf)
        or artifactPath(admissionVerifier.artifactRoot, initialSubjectHash).read_bytes() != initialArtifact
    ):
        raise SimulationSpecError("initial-state admission lineage mismatch")


def _cleanIssuedActions(
    model: WorldModel,
    strategyId: str,
    step: int,
    issued: Mapping[str, float],
) -> dict[str, float]:
    """정책 또는 일정이 낸 행동 집합과 범위를 같은 계약으로 검증한다."""

    if not isinstance(issued, Mapping):
        raise SimulationSpecError(f"strategy {strategyId} step {step} must return an action mapping")
    actionById = {action.actionId: action for action in model.actions}
    if set(issued) != set(actionById):
        missing = sorted(set(actionById) - set(issued))
        unknown = sorted(set(issued) - set(actionById))
        raise SimulationSpecError(
            f"strategy {strategyId} step {step} action mismatch; missing={missing}, unknown={unknown}"
        )
    clean: dict[str, float] = {}
    for name, value in issued.items():
        action = actionById[name]
        number = _finite(value, f"strategy.{strategyId}.{step}.{name}")
        if number < action.lower - 1e-12 or number > action.upper + 1e-12:
            raise SimulationSpecError(f"action outside bounds: {name}")
        clean[name] = number
    return clean


def _checkRunShape(paths: tuple[ScenarioPath, ...], strategies: tuple[StrategySpec, ...]) -> int:
    """모든 경로와 전략이 같은 양의 기간 지평을 공유하는지 확인하고 그 지평을 돌려준다."""

    if not paths or not strategies:
        raise SimulationSpecError("at least one path and strategy are required")
    horizon = len(paths[0].steps)
    if horizon < 1 or any(len(path.steps) != horizon for path in paths):
        raise SimulationSpecError("all paths must share a positive horizon")
    if any(len(strategy.actionsByStep) != horizon for strategy in strategies):
        raise SimulationSpecError("all strategies must share the path horizon")
    return horizon


def _resolveInitialCutoffs(initial: WorldState) -> tuple[str | None, str | None]:
    """초기 상태의 knowledge와 decision cutoff를 비교 가능한 날짜로 확정한다."""

    if initial.knowledgeAsOf:
        initialKnowledgeDate = _comparableDate(initial.knowledgeAsOf)
        if initialKnowledgeDate is None:
            raise SimulationSpecError("initial state has an invalid knowledge cutoff")
    else:
        initialKnowledgeDate = _comparableDate(initial.asOf)
    if initial.decisionAsOf:
        decisionDate = _comparableDate(initial.decisionAsOf)
        if decisionDate is None:
            raise SimulationSpecError("initial state has an invalid decision cutoff")
    else:
        decisionDate = initialKnowledgeDate
    if initialKnowledgeDate is not None and decisionDate is not None and initialKnowledgeDate > decisionDate:
        raise SimulationSpecError("initial state knowledge is newer than its decision cutoff")
    return initialKnowledgeDate, decisionDate


def _checkInitialVintage(
    initial: WorldState,
    initialKnowledgeDate: str | None,
    decisionDate: str | None,
) -> None:
    """초기 상태 vintage의 내용 해시와 시간 인과를 결정시점 기준으로 검증한다."""

    if initial.vintage is None:
        return
    if decisionDate is None:
        raise SimulationSpecError("initial state vintage needs a decision cutoff")
    try:
        validateVintageRef(
            initial.vintage,
            decisionAsOf=decisionDate,
            expectedArtifactKind="worldState",
            expectedPayloadHash=worldStatePayloadHash(
                initial.values,
                step=initial.step,
                asOf=initial.asOf,
                refs=initial.refs,
            ),
        )
    except VintageError as error:
        if initial.admissionReceiptId:
            raise SimulationSpecError(f"initial-state admission vintage mismatch: {error}") from error
        raise SimulationSpecError(str(error)) from error
    if initial.knowledgeAsOf and initial.vintage.knowledgeAsOf != initialKnowledgeDate:
        raise SimulationSpecError("initial state vintage knowledge cutoff mismatch")


def _checkCompiledStateLineage(initial: WorldState) -> None:
    """컴파일된 초기 상태라면 manifest와 계약 해시가 vintage와 정확히 맞물리게 한다."""

    if not (initial.stateCompilationContractHash or initial.stateManifestHash):
        return
    if initial.vintage is None:
        raise SimulationSpecError("compiled initial state needs an aggregate vintage")
    if (
        not _validDigest(initial.stateCompilationContractHash)
        or not _validDigest(initial.stateManifestHash)
        or initial.vintage.contractHash != initial.stateCompilationContractHash
        or initial.vintage.artifactHash != initial.stateManifestHash
    ):
        raise SimulationSpecError("compiled initial-state manifest contract mismatch")


def _checkLawAdmissionHorizon(model: WorldModel, horizon: int, initialKnowledgeDate: str | None) -> None:
    """인증된 법칙이 요청 지평과 초기 상태 cutoff를 넘지 않는지 확인한다."""

    for law in model.laws:
        certificate = law.certificate
        if law.evidenceKind in {"measuredAssociation", "identifiedIntervention"}:
            _validateLawCertificate(law)
        if certificate is not None and certificate.status == "admitted" and certificate.maxAdmittedStep < horizon:
            raise SimulationSpecError(f"law exceeds admitted horizon: {law.lawId}")
        if certificate is not None and certificate.status == "admitted":
            if initialKnowledgeDate is None:
                raise SimulationSpecError("certified laws need an initial-state knowledge cutoff")
            if certificate.knowledgeAsOf > initialKnowledgeDate:
                raise SimulationSpecError(f"law certificate is newer than initial state: {law.lawId}")


def _checkRunIdentity(paths: tuple[ScenarioPath, ...], strategies: tuple[StrategySpec, ...]) -> None:
    """식별자 중복과 baseline 개수처럼 비교 자체를 무의미하게 만드는 조건을 막는다."""

    if len({p.pathId for p in paths}) != len(paths) or len({s.strategyId for s in strategies}) != len(strategies):
        raise SimulationSpecError("duplicate pathId or strategyId")
    if sum(strategy.isBaseline for strategy in strategies) > 1:
        raise SimulationSpecError("at most one baseline strategy is allowed")


def _checkParameterDrawProvenance(
    model: WorldModel,
    paths: tuple[ScenarioPath, ...],
    decisionDate: str | None,
) -> None:
    """파라미터 추출 경로가 하나의 서명 provenance 영수증과 단위 계약을 공유하게 한다."""

    parameterPaths = tuple(path for path in paths if path.parameterDraws)
    parameterReceipts = {path.parameterDrawReceipt for path in parameterPaths}
    if not any(receipt is not None for receipt in parameterReceipts):
        return
    if None in parameterReceipts or len(parameterReceipts) != 1 or len(parameterPaths) != len(paths):
        raise SimulationSpecError("parameter draw paths must share one provenance receipt")
    receipt = next(iter(parameterReceipts))
    validateParameterDrawSetReceipt(paths, receipt, decisionAsOf=decisionDate)
    expectedUnits = {
        name: unit
        for law in model.laws
        for name, unit in law.pathParameterUnits.items()
        if name in receipt.parameterNames
    }
    if tuple(sorted(expectedUnits.items())) != receipt.parameterUnits:
        raise SimulationSpecError("parameter draw units do not match their consuming laws")


def _checkAdmittedPathContract(path: ScenarioPath, horizon: int, decisionDate: str | None) -> None:
    """admitted 경로 하나가 인증서, 지평, as-known vintage, 시간 인과를 모두 갖췄는지 본다."""

    if not _validDigest(path.certificateId):
        raise SimulationSpecError(f"admitted path needs a certificate: {path.pathId}")
    if path.maxAdmittedStep < horizon:
        raise SimulationSpecError(f"path exceeds admitted horizon: {path.pathId}")
    pathDate = _comparableDate(path.knowledgeAsOf)
    if pathDate is None:
        raise SimulationSpecError(f"admitted path needs a knowledge cutoff: {path.pathId}")
    if path.historyStatus != "asKnown":
        raise SimulationSpecError(f"admitted path needs as-known history: {path.pathId}")
    if path.vintage is None or not isExactAsKnown(path.vintage):
        raise SimulationSpecError(f"admitted path needs an exact as-known vintage: {path.pathId}")
    if not _validDigest(path.vintage.receiptId):
        raise SimulationSpecError(f"admitted path needs a signed vintage receipt: {path.pathId}")
    if decisionDate is None:
        raise SimulationSpecError("admitted paths need an initial-state decision cutoff")
    if pathDate > decisionDate:
        raise SimulationSpecError(f"path is newer than decision state: {path.pathId}")


def _checkPathWeightContract(path: ScenarioPath) -> None:
    """가중치 성격이 선언한 만큼의 근거(가중치 값, admission 인증서)를 실제로 갖췄는지 본다."""

    if path.weightKind == "unweighted" and path.weight is not None:
        raise SimulationSpecError("unweighted path cannot carry a weight")
    if path.weightKind != "unweighted":
        if path.weight is None or not math.isfinite(float(path.weight)) or path.weight <= 0:
            raise SimulationSpecError("weighted path needs a positive finite weight")
    if path.weightKind == "calibrated":
        if path.validationStatus != "admitted" or not _validDigest(path.certificateId):
            raise SimulationSpecError("calibrated paths need an admission certificate")


def _checkPathShocks(model: WorldModel, path: ScenarioPath, shockIds: set[str]) -> None:
    """기간마다 모델이 요구하는 충격이 빠짐없이 있고 허용범위 안인지 확인한다."""

    for step, shocks in enumerate(path.steps):
        if set(shocks) != shockIds:
            missing = sorted(shockIds - set(shocks))
            raise SimulationBlocked(f"path {path.pathId} step {step} missing shocks: {missing}")
        for name, value in shocks.items():
            _validateValue(model, name, value, f"path.{path.pathId}.{step}.{name}")


def _checkPathContract(
    model: WorldModel,
    path: ScenarioPath,
    horizon: int,
    decisionDate: str | None,
    shockIds: set[str],
    pathParameterIds: set[str],
) -> None:
    """경로 하나가 홀로 만족해야 할 파라미터, 격자, vintage, 가중치, 충격 계약을 검사한다."""

    unknownPathParameters = set(path.parameterDraws) - pathParameterIds
    if unknownPathParameters:
        raise SimulationSpecError(f"unknown path parameters for {path.pathId}: {sorted(unknownPathParameters)}")
    for name, value in path.parameterDraws.items():
        _finite(value, f"path.{path.pathId}.parameter.{name}")
    if path.weightKind not in WEIGHT_KIND_SET:
        raise SimulationSpecError(f"unknown weight kind: {path.weightKind}")
    if path.validationStatus not in PATH_VALIDATION_SET:
        raise SimulationSpecError(f"unknown path validation status: {path.validationStatus}")
    if path.validationStatus == "rejected":
        raise SimulationSpecError(f"rejected path cannot execute: {path.pathId}")
    if path.frequency != model.stepFrequency or path.stepSpan != model.stepSpan:
        raise SimulationSpecError(
            f"path step contract mismatch: {path.pathId} is {path.stepSpan} {path.frequency}, "
            f"model needs {model.stepSpan} {model.stepFrequency}"
        )
    if path.maxAdmittedStep < 0:
        raise SimulationSpecError(f"negative admitted horizon: {path.pathId}")
    if path.vintage is not None:
        if decisionDate is None:
            raise SimulationSpecError("path vintage needs an initial-state decision cutoff")
        try:
            validateVintageRef(path.vintage, decisionAsOf=decisionDate)
        except VintageError as error:
            raise SimulationSpecError(str(error)) from error
        if path.knowledgeAsOf and path.vintage.knowledgeAsOf != path.knowledgeAsOf:
            raise SimulationSpecError(f"path vintage knowledge cutoff mismatch: {path.pathId}")
    if path.validationStatus == "admitted":
        _checkAdmittedPathContract(path, horizon, decisionDate)
    _checkPathWeightContract(path)
    _checkPathShocks(model, path, shockIds)


def _checkAdmittedPathAgreement(paths: tuple[ScenarioPath, ...]) -> str:
    """admitted 집합이 하나의 인증서, 지평, cutoff, as-known 이력을 공유하는지 본다."""

    certificates = {path.certificateId for path in paths}
    admittedHorizons = {path.maxAdmittedStep for path in paths}
    knowledgeCutoffs = {path.knowledgeAsOf for path in paths}
    historyStatuses = {path.historyStatus for path in paths}
    if (
        len(certificates) != 1
        or len(admittedHorizons) != 1
        or len(knowledgeCutoffs) != 1
        or historyStatuses != {"asKnown"}
    ):
        raise SimulationSpecError("admitted paths must share one certificate, horizon, and vintage")
    return next(iter(knowledgeCutoffs))


def _checkAdmittedPathBinding(paths: tuple[ScenarioPath, ...]) -> str:
    """선언된 content binding이 실제 경로 집합 내용과 같은 hash인지 다시 계산해 본다."""

    contentHashes = {path.admissionContentHash for path in paths}
    if len(contentHashes) != 1 or not _validDigest(next(iter(contentHashes))):
        raise SimulationSpecError("admitted paths need one content binding")
    contentHash = next(iter(contentHashes))
    if contentHash != _pathSetContentHash(paths):
        raise SimulationSpecError("admitted path content binding mismatch")
    return contentHash


def _checkAdmittedPathSignatures(
    paths: tuple[ScenarioPath, ...],
    admissionVerifier: AdmissionVerifier | None,
) -> tuple[str, VintageRef]:
    """서명 영수증과 typed vintage가 집합 전체에 하나씩만 붙어 있는지 확인한다."""

    receiptIds = {path.admissionReceiptId for path in paths}
    vintages = {path.vintage for path in paths}
    if len(receiptIds) != 1 or not _validDigest(next(iter(receiptIds))):
        raise SimulationSpecError("admitted paths need one signed path-set receipt")
    if len(vintages) != 1:
        raise SimulationSpecError("admitted paths must share one typed vintage")
    if admissionVerifier is None:
        raise SimulationSpecError("admitted paths need a runtime admission verifier")
    receiptId = next(iter(receiptIds))
    vintage = next(iter(vintages))
    if vintage is None:
        raise SimulationSpecError("admitted paths need one typed vintage")
    return receiptId, vintage


def _checkPathSetReceiptBinding(receipt, vintageReceipt, vintage: VintageRef, contentHash: str) -> None:
    """경로 집합 영수증이 서명한 내용과 상속한 vintage 영수증이 실제와 맞는지 본다."""

    if receipt.status != "admitted":
        raise SimulationSpecError("path-set receipt is not admitted")
    if receipt.artifactHash != contentHash:
        raise SimulationSpecError("path-set receipt artifact binding mismatch")
    if vintage.receiptId not in receipt.parentReceiptIds:
        raise SimulationSpecError("path-set receipt does not inherit its vintage receipt")
    if (
        vintageReceipt.status != "verifiedVintage"
        or vintageReceipt.artifactHash != vintage.artifactHash
        or vintageReceipt.knowledgeAsOf != vintage.knowledgeAsOf
        or vintageReceipt.revisionPolicy != vintage.revisionPolicy
        or vintageReceipt.coverage != vintage.coverage
    ):
        raise SimulationSpecError("path vintage receipt contract mismatch")


def _verifyPathSetAdmission(
    model: WorldModel,
    horizon: int,
    decisionDate: str | None,
    admissionVerifier: AdmissionVerifier,
    contentHash: str,
    receiptId: str,
    vintage: VintageRef,
    knowledgeCutoff: str,
) -> None:
    """서명 영수증 두 장을 실제로 검증하고 발급시점과 실행 격자 계약을 대조한다."""

    try:
        receipt = admissionVerifier.verify(
            receiptId,
            expectedSubjectHash=contentHash,
            expectedKind="pathSet",
        )
        vintageReceipt = admissionVerifier.verify(
            vintage.receiptId,
            expectedSubjectHash=vintage.payloadHash,
            expectedKind="dataVintage",
        )
    except RuntimeError as error:
        raise SimulationSpecError(f"path admission verification failed: {error}") from error
    _checkPathSetReceiptBinding(receipt, vintageReceipt, vintage, contentHash)
    receiptIssued = _comparableDate(receipt.issuedAt)
    vintageIssued = _comparableDate(vintageReceipt.issuedAt)
    if (
        decisionDate is None
        or receiptIssued is None
        or vintageIssued is None
        or receiptIssued > decisionDate
        or vintageIssued > decisionDate
    ):
        raise SimulationSpecError("path admission was not available by decisionAsOf")
    if (
        receipt.knowledgeAsOf != knowledgeCutoff
        or receipt.frequency != model.stepFrequency
        or receipt.stepSpan != model.stepSpan
        or receipt.maxAdmittedStep < horizon
        or receipt.revisionPolicy != "asKnown"
        or receipt.coverage != "asOfExact"
    ):
        raise SimulationSpecError("path-set receipt execution contract mismatch")


def _checkPathSetAdmission(
    model: WorldModel,
    paths: tuple[ScenarioPath, ...],
    horizon: int,
    decisionDate: str | None,
    admissionVerifier: AdmissionVerifier | None,
) -> None:
    """경로 집합 전체가 하나의 검증 상태를 공유하는지 보고 admitted면 서명까지 확인한다."""

    validationStatuses = {path.validationStatus for path in paths}
    if len(validationStatuses) != 1:
        raise SimulationSpecError("all paths must share one validation status")
    if validationStatuses != {"admitted"}:
        return
    knowledgeCutoff = _checkAdmittedPathAgreement(paths)
    contentHash = _checkAdmittedPathBinding(paths)
    receiptId, vintage = _checkAdmittedPathSignatures(paths, admissionVerifier)
    _verifyPathSetAdmission(
        model,
        horizon,
        decisionDate,
        admissionVerifier,
        contentHash,
        receiptId,
        vintage,
        knowledgeCutoff,
    )


def _checkStrategyContracts(model: WorldModel, strategies: tuple[StrategySpec, ...]) -> None:
    """폐루프 정책은 버전과 근거를, 정적 일정은 기간별 행동 계약을 갖췄는지 본다."""

    for strategy in strategies:
        if strategy.policyFn is not None:
            if not callable(strategy.policyFn):
                raise SimulationSpecError(f"closed-loop policy must be callable: {strategy.strategyId}")
            if any(issued for issued in strategy.actionsByStep):
                raise SimulationSpecError(
                    f"closed-loop strategy cannot also carry an action schedule: {strategy.strategyId}"
                )
            if not strategy.policyVersion or not strategy.policyProvenance:
                raise SimulationSpecError(
                    f"closed-loop strategy needs policy version and provenance: {strategy.strategyId}"
                )
        else:
            for step, issued in enumerate(strategy.actionsByStep):
                _cleanIssuedActions(model, strategy.strategyId, step, issued)


def _checkInputs(
    model: WorldModel,
    initial: WorldState,
    paths: tuple[ScenarioPath, ...],
    strategies: tuple[StrategySpec, ...],
    admissionVerifier: AdmissionVerifier | None,
) -> int:
    horizon = _checkRunShape(paths, strategies)
    initialKnowledgeDate, decisionDate = _resolveInitialCutoffs(initial)
    _checkInitialVintage(initial, initialKnowledgeDate, decisionDate)
    _checkCompiledStateLineage(initial)
    _validateInitialStateAdmission(model, initial, admissionVerifier)
    _checkLawAdmissionHorizon(model, horizon, initialKnowledgeDate)
    _checkRunIdentity(paths, strategies)
    weightKinds = {path.weightKind for path in paths}
    if len(weightKinds) != 1:
        raise SimulationSpecError("all paths must share one weight interpretation")
    shockIds = {v.variableId for v in model.variables if v.role == "shock"}
    pathParameterIds = {name for law in model.laws for name in law.pathParameterInputs}
    requiredInitial = {name for law in model.laws for name in law.priorInputs}
    initialStatePrimitives(model, initial)
    for name in requiredInitial:
        _validateValue(model, name, initial.values.get(name), f"initial.{name}")
    _checkParameterDrawProvenance(model, paths, decisionDate)
    for path in paths:
        _checkPathContract(model, path, horizon, decisionDate, shockIds, pathParameterIds)
    _checkPathSetAdmission(model, paths, horizon, decisionDate, admissionVerifier)
    if weightKinds == {"calibrated"}:
        totalWeight = sum(float(path.weight) for path in paths if path.weight is not None)
        if abs(totalWeight - 1.0) > 1e-9:
            raise SimulationSpecError("calibrated path weights must sum to one")
    _checkStrategyContracts(model, strategies)
    return horizon
