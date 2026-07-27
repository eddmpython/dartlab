"""Auditable multi-step world evolution and strategy comparison contracts.

이 파일은 실행기다. 같은 세계 경로 위에서 전략을 하나씩 굴리고, 재현 해시와 감사 추적을
붙여 돌려준다. 그 앞뒤에 붙던 것들(계약 자료형, 계약 해시, 모델 컴파일, 입력 검사, 목적
집계)은 각각 형제 모듈로 나갔다. 여기 남은 것은 "무엇을 어떤 순서로 부르는가"뿐이다.

`dartlab.simulate.world` 는 여전히 그 전부의 단일 진입점이다. 아래 import 는 그래서
단순한 의존이 아니라 공개 표면 재수출이다. 기존 호출부가 그대로 동작해야 한다.
"""

from __future__ import annotations

from hashlib import sha256
from typing import TYPE_CHECKING

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
from dartlab.simulate.worldContracts import (
    _lawCertificatePayload,
    _lawContractPayload,
    _pathSetContentHash,
    _pathSetPayload,
    _validateLawCertificate,
    bindAdmittedPathContent,
    bindPathAdmissionReceipt,
    constraintContractHash,
    dataVintageHashFor,
    issueLawCertificate,
    objectiveContractHash,
    pathSetAdmissionArtifact,
    pathSetAdmissionSubjectHash,
    strategyContractHash,
    traceRootFor,
)
from dartlab.simulate.worldInputs import (
    _checkInputs,
    _cleanIssuedActions,
    _validateInitialStateAdmission,
    _validateValue,
    initialStateAdmissionArtifact,
    initialStateAdmissionSubjectHash,
    initialStatePrimitives,
    worldStateFromCompiled,
)
from dartlab.simulate.worldModel import WorldModel
from dartlab.simulate.worldScoring import (
    _aggregate,
    _buildDecision,
    _collectQualificationIssues,
    _constraintBreaches,
    _CvarSpill,
    _ObjectiveLedger,
    _pareto,
    _pathMetric,
    _selectRecommendation,
    _validateConstraintContracts,
    _validateObjectiveContracts,
    _validateTraceLimit,
    _weightLabelFor,
)
from dartlab.simulate.worldTypes import (
    EVIDENCE_SET,
    LAW_CERTIFICATE_STATUS_SET,
    PATH_VALIDATION_SET,
    ROLE_SET,
    WEIGHT_KIND_SET,
    ActionSpec,
    ConstraintSpec,
    LawCertificate,
    LawFn,
    LawSpec,
    LawTrace,
    ObjectiveSpec,
    PathTrace,
    PolicyContext,
    PolicyFn,
    ScenarioPath,
    SimulationBlocked,
    SimulationRun,
    SimulationSpecError,
    StepContext,
    StepTrace,
    StrategyEvaluation,
    StrategySpec,
    VariableSpec,
    WorldState,
    _canonical,
    _comparableDate,
    _finite,
    _freezeMapping,
    _stableHash,
    _validDigest,
)

if TYPE_CHECKING:
    from dartlab.simulate.admissionRegistry import AdmissionVerifier
    from dartlab.simulate.policyEvaluation import PolicyAdmissionEvidence


def executableHashFor(model: WorldModel, strategies: tuple[StrategySpec, ...]) -> str:
    """Return the executable hash used by policy admission and runtime.

    Args:
        model: Compiled variable, action, and transition-law contract.
        strategies: Static schedules or versioned closed-loop policies.

    Returns:
        SHA-256 digest of law and policy executable identities.

    Raises:
        SimulationSpecError: Raised later by model construction for malformed inputs.

    Example:
        ``digest = executableHashFor(model, strategies)``
    """

    return _stableHash(
        {
            "modelId": model.modelId,
            "modelVersion": model.version,
            "laws": tuple((law.lawId, law.version, law.fn) for law in model.laws),
            "policies": tuple(
                (strategy.strategyId, strategy.policyVersion, strategy.policyFn)
                for strategy in strategies
                if strategy.policyFn is not None
            ),
        }
    )


def _decisionCutoff(initial: WorldState) -> str:
    """실행 원장이 기록할 결정시점을 decision, knowledge, asOf 순으로 확정한다."""

    return (
        _comparableDate(initial.decisionAsOf)
        or _comparableDate(initial.knowledgeAsOf)
        or _comparableDate(initial.asOf)
        or ""
    )


def _verifyCurrentStateAdmission(
    model: WorldModel,
    initial: WorldState,
    admissionVerifier: AdmissionVerifier,
    decisionAsOf: str,
):
    """정책 승인이 요구하는 현재 초기 상태의 서명 계보를 끝까지 확인한다."""

    from dartlab.simulate.admissionRegistry import artifactPath

    if initial.vintage is None or not isExactAsKnown(initial.vintage):
        raise SimulationSpecError("policy admission needs an exact as-known current initial state")
    if (
        not _validDigest(initial.admissionReceiptId)
        or not _validDigest(initial.vintage.receiptId)
        or not _validDigest(initial.stateCompilationContractHash)
        or not _validDigest(initial.stateManifestHash)
    ):
        raise SimulationSpecError("policy admission needs signed current initial-state lineage")
    initialArtifact = initialStateAdmissionArtifact(model, initial)
    initialSubjectHash = initialStateAdmissionSubjectHash(model, initial)
    currentPrimitives = initialStatePrimitives(model, initial)
    pointInTimeReceipt = validatePointInTimeStateReceipt(
        statePrimitives=currentPrimitives,
        asOf=initial.asOf,
        knowledgeAsOf=initial.knowledgeAsOf,
        decisionAsOf=initial.decisionAsOf,
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
    if (
        initialReceipt.status != "admitted"
        or initialReceipt.artifactHash != initialSubjectHash
        or (initialReceipt.ruleId, initialReceipt.ruleVersion, initialReceipt.ruleHash)
        != (INITIAL_STATE_RULE_ID, INITIAL_STATE_RULE_VERSION, INITIAL_STATE_RULE_HASH)
        or initialReceipt.parentReceiptIds != (pointInTimeReceipt.receiptId,)
        or initial.vintage.artifactHash != initial.stateManifestHash
        or initial.vintage.contractHash != initial.stateCompilationContractHash
        or pointInTimeReceipt.knowledgeAsOf != initial.knowledgeAsOf
        or _comparableDate(initialReceipt.issuedAt) > decisionAsOf
        or _comparableDate(pointInTimeReceipt.issuedAt) > decisionAsOf
        or artifactPath(admissionVerifier.artifactRoot, initialSubjectHash).read_bytes() != initialArtifact
    ):
        raise SimulationSpecError("current initial-state admission lineage mismatch")
    return currentPrimitives


def _verifyPolicyAdmission(
    model: WorldModel,
    initial: WorldState,
    paths: tuple[ScenarioPath, ...],
    strategies: tuple[StrategySpec, ...],
    constraints: tuple[ConstraintSpec, ...],
    objectives: tuple[ObjectiveSpec, ...],
    *,
    admissionVerifier: AdmissionVerifier | None,
    policyAdmissionEvidence: PolicyAdmissionEvidence,
    decisionAsOf: str,
    executableHash: str,
    pathAdmissionReceiptId: str,
    horizon: int,
) -> tuple[str, str]:
    """정책 평가 인증서가 이 실행의 계약과 계보에 정확히 결속됐는지 확인한다."""

    if admissionVerifier is None:
        raise SimulationSpecError("policy admission evidence needs a runtime admission verifier")
    baselineStrategies = tuple(strategy for strategy in strategies if strategy.isBaseline)
    candidateStrategies = tuple(strategy for strategy in strategies if not strategy.isBaseline)
    if len(strategies) != 2 or len(baselineStrategies) != 1 or len(candidateStrategies) != 1:
        raise SimulationSpecError("policy admission evidence needs exactly one baseline and one candidate")
    if len(objectives) != 1:
        raise SimulationSpecError("policy admission evidence needs exactly one objective")
    try:
        from dartlab.simulate.policyEvaluation import (
            parameterContractHashFor,
            validatePolicyEvaluationCertificate,
        )

        currentPrimitives = _verifyCurrentStateAdmission(model, initial, admissionVerifier, decisionAsOf)
        pathReceipt = admissionVerifier.verify(
            pathAdmissionReceiptId,
            expectedSubjectHash=pathSetAdmissionSubjectHash(paths),
            expectedKind="pathSet",
        )
        validatePolicyEvaluationCertificate(
            policyAdmissionEvidence.snapshot,
            policyAdmissionEvidence.batch,
            policyAdmissionEvidence.certificate,
            admissionVerifier,
            decisionAsOf=decisionAsOf,
            executableHash=executableHash,
            baselineStrategyContractHash=strategyContractHash(baselineStrategies[0]),
            candidateStrategyContractHash=strategyContractHash(candidateStrategies[0]),
            objectiveContractHash=objectiveContractHash(objectives[0]),
            constraintContractHash=constraintContractHash(constraints),
            pathRuleHash=pathReceipt.ruleHash,
            parameterContractHash=parameterContractHashFor(paths),
            pathFrequency=pathReceipt.frequency,
            pathStepSpan=pathReceipt.stepSpan,
            pathHorizon=horizon,
            currentState=currentPrimitives,
            stateCompilationContractHash=initial.stateCompilationContractHash,
        )
    except (OSError, RuntimeError, ValueError) as error:
        raise SimulationSpecError(f"policy admission verification failed: {error}") from error
    return (
        policyAdmissionEvidence.certificate.certificateId,
        policyAdmissionEvidence.certificate.stateSupport.supportId,
    )


def _runLaws(
    model: WorldModel,
    path: ScenarioPath,
    step: int,
    prior: dict[str, float],
    shocks: dict[str, float],
    effective: dict[str, float],
    actionCost: float,
) -> tuple[dict[str, float], list[LawTrace]]:
    """컴파일된 실행 순서대로 법칙을 굴려 이번 기간의 현재값과 법칙 trace를 만든다."""

    current: dict[str, float] = {}
    lawTraces: list[LawTrace] = []
    for law in model._orderedLaws:
        if law.status == "blocked":
            raise SimulationBlocked(f"law blocked: {law.lawId}")
        inputValues: dict[str, float] = {}
        for name in law.priorInputs:
            inputValues[f"prior.{name}"] = _finite(prior.get(name), f"{law.lawId}.prior.{name}")
        for name in law.currentInputs:
            inputValues[f"current.{name}"] = _finite(current.get(name), f"{law.lawId}.current.{name}")
        for name in law.shockInputs:
            inputValues[f"shock.{name}"] = _finite(shocks.get(name), f"{law.lawId}.shock.{name}")
        for name in law.actionInputs:
            inputValues[f"action.{name}"] = _finite(effective.get(name), f"{law.lawId}.action.{name}")
        lawPathParameters = {
            name: _finite(path.parameterDraws[name], f"{law.lawId}.pathParameter.{name}")
            for name in law.pathParameterInputs
            if name in path.parameterDraws
        }
        for name, value in lawPathParameters.items():
            inputValues[f"pathParameter.{name}"] = value
        if law.usesActionCost:
            inputValues["actionCost"] = actionCost
        lawPrior = {name: prior[name] for name in law.priorInputs}
        lawCurrent = {name: current[name] for name in law.currentInputs}
        lawShocks = {name: shocks[name] for name in law.shockInputs}
        lawActions = {name: effective[name] for name in law.actionInputs}
        ctx = StepContext(
            step=step,
            prior=_freezeMapping(lawPrior),
            current=_freezeMapping(lawCurrent),
            shocks=_freezeMapping(lawShocks),
            issuedActions=_freezeMapping({}),
            actions=_freezeMapping(lawActions),
            pathParameters=_freezeMapping(lawPathParameters),
            actionCost=actionCost if law.usesActionCost else 0.0,
        )
        produced = dict(law.fn(ctx))
        if set(produced) != set(law.outputs):
            raise SimulationBlocked(f"law output mismatch: {law.lawId}")
        clean = {
            name: _validateValue(model, name, value, f"{law.lawId}.output.{name}") for name, value in produced.items()
        }
        current.update(clean)
        lawTraces.append(
            LawTrace(
                lawId=law.lawId,
                inputs=inputValues,
                outputs=clean,
                evidenceKind=law.evidenceKind,
                provenance=law.provenance,
                version=law.version,
                parameters=law.parameters,
                pathParameters=lawPathParameters,
                certificateId=law.certificate.certificateId if law.certificate is not None else "",
            )
        )
    return current, lawTraces


def _issueActions(
    model: WorldModel,
    strategy: StrategySpec,
    step: int,
    prior: dict[str, float],
    issuedHistory: list[dict[str, float]],
    actionById: dict[str, ActionSpec],
) -> dict[str, float]:
    """이번 기간에 발행할 행동을 정적 일정 또는 폐루프 정책에서 같은 계약으로 받는다."""

    if strategy.policyFn is None:
        rawIssued = strategy.actionsByStep[step]
    else:
        priorActions = issuedHistory[-1] if issuedHistory else {name: 0.0 for name in actionById}
        policyContext = PolicyContext(
            step=step,
            prior=_freezeMapping(prior),
            priorActions=_freezeMapping(priorActions),
        )
        rawIssued = strategy.policyFn(policyContext)
    return _cleanIssuedActions(model, strategy.strategyId, step, rawIssued)


def _executePath(
    model: WorldModel,
    initial: WorldState,
    path: ScenarioPath,
    strategy: StrategySpec,
    constraints: tuple[ConstraintSpec, ...],
    horizon: int,
    actionById: dict[str, ActionSpec],
) -> PathTrace:
    """한 전략과 한 경로 조합을 지평 끝까지 전개해 전체 기간 trace를 만든다."""

    prior = {name: _finite(value, f"initial.{name}") for name, value in initial.values.items()}
    stepTraces: list[StepTrace] = []
    issuedHistory: list[dict[str, float]] = []
    for step in range(horizon):
        issued = _issueActions(model, strategy, step, prior, issuedHistory, actionById)
        issuedHistory.append(issued)
        effective: dict[str, float] = {}
        for actionId, action in actionById.items():
            sourceStep = step - action.leadSteps
            effective[actionId] = issuedHistory[sourceStep][actionId] if sourceStep >= 0 else 0.0
        actionCost = sum(abs(issued[name]) * actionById[name].costPerUnit for name in issued)
        shocks = {name: _finite(value, f"path.{path.pathId}.{step}.{name}") for name, value in path.steps[step].items()}
        current, lawTraces = _runLaws(model, path, step, prior, shocks, effective, actionCost)
        after = dict(prior)
        after.update(current)
        breaches = _constraintBreaches(constraints, after, "eachStep")
        if step == horizon - 1:
            breaches += _constraintBreaches(constraints, after, "terminal")
        stepTraces.append(
            StepTrace(
                step=step,
                before=dict(prior),
                shocks=shocks,
                issuedActions=issued,
                effectiveActions=effective,
                actionCost=actionCost,
                after=after,
                laws=tuple(lawTraces),
                breaches=breaches,
            )
        )
        prior = after
    return PathTrace(
        strategyId=strategy.strategyId,
        pathId=path.pathId,
        initial={name: _finite(value, f"initial.{name}") for name, value in initial.values.items()},
        steps=tuple(stepTraces),
        policyVersion=strategy.policyVersion,
        policyProvenance=strategy.policyProvenance,
        status="ok",
    )


def _runLedger(
    model: WorldModel,
    initial: WorldState,
    paths: tuple[ScenarioPath, ...],
    strategies: tuple[StrategySpec, ...],
    constraints: tuple[ConstraintSpec, ...],
    horizon: int,
    traceLimit: int | None,
    ledger: _ObjectiveLedger,
) -> tuple[list[PathTrace], int, str]:
    """전략 x 경로 격자를 선언 순서대로 전개하며 trace 체인과 목적 원장을 함께 쌓는다."""

    actionById = {action.actionId: action for action in model.actions}
    traces: list[PathTrace] = []
    traceChain = sha256()
    traceCount = 0
    for strategyIndex, strategy in enumerate(strategies):
        for pathIndex, path in enumerate(paths):
            trace = _executePath(model, initial, path, strategy, constraints, horizon, actionById)
            traceCount += 1
            traceChain.update(bytes.fromhex(_stableHash({"trace": trace})))
            if traceLimit is None or len(traces) < traceLimit:
                traces.append(trace)
            ledger.record(strategyIndex, strategy.strategyId, pathIndex, trace)
    return traces, traceCount, traceChain.hexdigest()


def simulateWorld(
    model: WorldModel,
    initial: WorldState,
    paths: tuple[ScenarioPath, ...],
    strategies: tuple[StrategySpec, ...],
    *,
    constraints: tuple[ConstraintSpec, ...] = (),
    objectives: tuple[ObjectiveSpec, ...] = (),
    inputWarnings: tuple[str, ...] = (),
    traceLimit: int | None = None,
    admissionVerifier: AdmissionVerifier | None = None,
    policyAdmissionEvidence: PolicyAdmissionEvidence | None = None,
) -> SimulationRun:
    """Evolve every strategy over the same explicit world paths.

    Static strategies contain schedules. Closed-loop policies receive only the
    state and action known before the current shock, never a path or future
    outcome.

    Args:
        model: Variable, action, and transition-law contract.
        initial: Decision-time world state.
        paths: Common scenario paths shared by every strategy.
        strategies: Candidate static schedules or closed-loop policies.
        constraints: Hard constraints checked after each transition.
        objectives: Metrics used to rank feasible strategy outcomes.
        inputWarnings: Pre-existing warnings carried into the run.
        traceLimit: Optional retained trace cap.
        admissionVerifier: Optional verifier for admitted initial state, paths, and policies.
        policyAdmissionEvidence: Optional policy evaluation certificate package.

    Returns:
        Deterministic simulation run ledger and strategy evaluations.

    Raises:
        SimulationSpecError: Inputs, admission evidence, path contracts, or objective contracts are invalid.
        SimulationBlocked: Runtime transition or constraint evaluation blocks a path.

    Example:
        ``run = simulateWorld(model, initial, paths, strategies, constraints=constraints, objectives=objectives)``
    """

    horizon = _checkInputs(model, initial, paths, strategies, admissionVerifier)
    decisionAsOf = _decisionCutoff(initial)
    pathAdmissionReceiptId = paths[0].admissionReceiptId if paths[0].validationStatus == "admitted" else ""
    _validateTraceLimit(traceLimit)
    variableIds = {variable.variableId for variable in model.variables}
    _validateObjectiveContracts(objectives, variableIds)
    _validateConstraintContracts(constraints, variableIds)

    executableHash = executableHashFor(model, strategies)
    policyAdmissionIssues = ["policyEvaluation"]
    policyEvaluationCertificateId = ""
    stateSupportId = ""
    if policyAdmissionEvidence is not None:
        policyEvaluationCertificateId, stateSupportId = _verifyPolicyAdmission(
            model,
            initial,
            paths,
            strategies,
            constraints,
            objectives,
            admissionVerifier=admissionVerifier,
            policyAdmissionEvidence=policyAdmissionEvidence,
            decisionAsOf=decisionAsOf,
            executableHash=executableHash,
            pathAdmissionReceiptId=pathAdmissionReceiptId,
            horizon=horizon,
        )
        policyAdmissionIssues = []

    cvarSpill = _CvarSpill() if traceLimit is not None and any(item.risk == "cvar" for item in objectives) else None
    weights = [1.0 if path.weight is None else float(path.weight) for path in paths]
    ledger = _ObjectiveLedger(strategies, objectives, weights, traceLimit, cvarSpill)
    traces, traceCount, traceChainDigest = _runLedger(
        model, initial, paths, strategies, constraints, horizon, traceLimit, ledger
    )
    evaluations = ledger.evaluations(strategies)
    if cvarSpill is not None:
        cvarSpill.close()

    issues = _collectQualificationIssues(model, paths)
    warnings, decisionStatus, baselineIds = _buildDecision(
        issues,
        strategies,
        objectives,
        inputWarnings,
        traceLimit,
        len(traces),
        traceCount,
        policyAdmissionIssues,
    )
    evaluationTuple = tuple(evaluations)
    pareto = _pareto(evaluationTuple) if objectives else ()
    recommendation = _selectRecommendation(decisionStatus, evaluations, pareto, objectives, strategies, baselineIds)
    weightLabel = _weightLabelFor(paths)
    payload = {
        "model": model,
        "initial": initial,
        "paths": paths,
        "strategies": strategies,
        "constraints": constraints,
        "objectives": objectives,
        "inputWarnings": inputWarnings,
        "traceLimit": traceLimit,
        "policyEvaluationCertificateId": policyEvaluationCertificateId,
    }
    runHash = _stableHash(payload)
    parameterHash = _stableHash(
        {
            "laws": tuple((law.lawId, law.parameters) for law in model.laws),
            "actions": model.actions,
            "pathParameterDraws": tuple((path.pathId, path.parameterDraws) for path in paths),
            "constraints": constraints,
            "objectives": objectives,
        }
    )
    dataVintageHash = dataVintageHashFor(initial, paths)
    traceRoot = _stableHash({"traceCount": traceCount, "traceChain": traceChainDigest})
    status = "partial" if issues.unqualifiedLaws else "ok"
    resultPayload = {
        "status": status,
        "decisionStatus": decisionStatus,
        "weightLabel": weightLabel,
        "recommendation": recommendation,
        "paretoStrategies": pareto,
        "evaluations": evaluationTuple,
        "traceRoot": traceRoot,
        "traceCount": traceCount,
        "retainedTraceCount": len(traces),
        "decisionAsOf": decisionAsOf,
        "initialStateAdmissionReceiptId": initial.admissionReceiptId,
        "pathAdmissionReceiptId": pathAdmissionReceiptId,
        "policyEvaluationCertificateId": policyEvaluationCertificateId,
        "stateSupportId": stateSupportId,
        "constraints": constraints,
        "objectives": objectives,
        "warnings": tuple(warnings),
    }
    return SimulationRun(
        runHash=runHash,
        executableHash=executableHash,
        parameterHash=parameterHash,
        dataVintageHash=dataVintageHash,
        resultHash=_stableHash(resultPayload),
        traceRoot=traceRoot,
        traceCount=traceCount,
        retainedTraceCount=len(traces),
        decisionAsOf=decisionAsOf,
        initialStateAdmissionReceiptId=initial.admissionReceiptId,
        pathAdmissionReceiptId=pathAdmissionReceiptId,
        policyEvaluationCertificateId=policyEvaluationCertificateId,
        stateSupportId=stateSupportId,
        status=status,
        decisionStatus=decisionStatus,
        weightLabel=weightLabel,
        recommendation=recommendation,
        paretoStrategies=pareto,
        evaluations=evaluationTuple,
        traces=tuple(traces),
        constraints=tuple(constraints),
        objectives=tuple(objectives),
        warnings=tuple(warnings),
    )
