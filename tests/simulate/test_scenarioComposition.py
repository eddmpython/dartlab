from __future__ import annotations

from dataclasses import replace
from datetime import date, timedelta
from hashlib import sha256

import polars as pl
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from dartlab.simulate.admissionRegistry import (
    AdmissionVerifier,
    TrustedIssuer,
    initializeAdmissionRegistry,
    issueAdmissionReceipt,
    putAdmissionArtifact,
)
from dartlab.simulate.driverCalibration import (
    MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_HASH,
    MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_ID,
    MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_VERSION,
)
from dartlab.simulate.driverPaths import (
    DriverAssumptionSource,
    DriverCard,
    DriverFactorSpec,
    DriverHistorySource,
    buildDriverPathSet,
    composeDriverPathSetWithAssumptions,
    driverFactorsToOperatingSpecs,
)
from dartlab.simulate.operatingBridge import (
    OperatingShockBaseline,
    OperatingTransmissionExposure,
    bridgeOperatingPath,
    sourceFactorContractHash,
)
from dartlab.simulate.operatingWorld import (
    OperatingPrimitive,
    _buildOperatingWorld,
    _initialStateFromInputs,
    buildOperatingStrategy,
    issueOperatingLawCertificate,
    operatingInputsFromCompiledState,
    operatingInputsFromPrimitives,
    runOperatingStrategies,
)
from dartlab.simulate.policyEvaluation import (
    PolicyAdmissionEvidence,
    PolicyEvaluationSpec,
    PolicyOosEpisode,
    PolicyPathPrimitive,
    admitPolicyOosEpisode,
    appendPolicyOosEpisode,
    initializePolicyOosLedger,
    issuePolicyEvaluationCertificate,
    parameterContractHashFor,
    readPolicyOosLedger,
    sealPolicyOosBatch,
)
from dartlab.simulate.scenarioComposition import (
    COMPOSED_CONDITIONAL_PATH_PACKAGE_KIND,
    COMPOSED_CONDITIONAL_PATH_PACKAGE_RULE_HASH,
    COMPOSED_CONDITIONAL_PATH_PACKAGE_RULE_ID,
    COMPOSED_CONDITIONAL_PATH_PACKAGE_RULE_VERSION,
    CONDITIONAL_SCENARIO_EXPERIMENT_RESULT_KIND,
    CONDITIONAL_SCENARIO_EXPERIMENT_RESULT_RULE_HASH,
    CONDITIONAL_SCENARIO_EXPERIMENT_RESULT_RULE_ID,
    CONDITIONAL_SCENARIO_EXPERIMENT_RESULT_RULE_VERSION,
    CONDITIONAL_STRATEGY_EVALUATION_KIND,
    CONDITIONAL_STRATEGY_EVALUATION_RULE_HASH,
    CONDITIONAL_STRATEGY_EVALUATION_RULE_ID,
    CONDITIONAL_STRATEGY_EVALUATION_RULE_VERSION,
    OperatingScenarioCase,
    ScenarioCoefficientBinding,
    ScenarioCompositionError,
    _caseLedgerHashes,
    bindConditionalScenarioExperimentReceipt,
    bindConditionalStrategyEvaluationReceipt,
    buildConditionalStrategyEvaluation,
    compareOneCompanyTwoScenarioStrategies,
    compareOperatingScenarioCases,
    conditionalScenarioExperimentArtifact,
    conditionalScenarioExperimentParentReceiptIds,
    conditionalScenarioExperimentPayload,
    conditionalScenarioExperimentSubjectHash,
    conditionalStrategyEvaluationArtifact,
    conditionalStrategyEvaluationParentReceiptIds,
    conditionalStrategyEvaluationPayload,
    conditionalStrategyEvaluationSubjectHash,
    runConditionalScenarioExperiment,
    scenarioCoefficientBindingHash,
    scenarioCoefficientExposureContractHash,
    scenarioPathPackageArtifact,
    scenarioPathPackageParentReceiptIds,
    scenarioPathPackageSubjectHash,
)
from dartlab.simulate.stateCompiler import (
    StateCompileSpec,
    buildProviderObservationBatch,
    compilePointInTimeState,
    issuePointInTimeState,
    issueProviderObservationBatch,
    makeVariableObservation,
)
from dartlab.simulate.stateSupport import (
    INITIAL_STATE_RULE_HASH,
    INITIAL_STATE_RULE_ID,
    INITIAL_STATE_RULE_VERSION,
    stateAdmissionArtifact,
)
from dartlab.simulate.stateVariables import StateVariableSpec, buildStateVariableRegistry
from dartlab.simulate.vintage import VintageRef, canonicalPayloadBytes, canonicalPayloadHash
from dartlab.simulate.world import (
    bindAdmittedPathContent,
    bindPathAdmissionReceipt,
    constraintContractHash,
    initialStateAdmissionArtifact,
    initialStateAdmissionSubjectHash,
    objectiveContractHash,
    pathSetAdmissionArtifact,
    pathSetAdmissionSubjectHash,
    strategyContractHash,
)

_COEFFICIENT_RECEIPT_ID = "a" * 64
_COEFFICIENT_SUBJECT_HASH = "b" * 64
_COEFFICIENT_RULE_HASH = MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_HASH
_COEFFICIENT_VECTOR_HASH = "d" * 64
_COEFFICIENT_FEATURE_SPEC_HASH = "e" * 64
_COEFFICIENT_DESIGN_FRAME_HASH = "f" * 64
_COEFFICIENT_FIT_DESIGN_FRAME_HASH = "1" * 64
_COEFFICIENT_OOS_DESIGN_FRAME_HASH = "2" * 64
_COEFFICIENT_PARENT_RECEIPTS = ("3" * 64, "4" * 64)


def _trust(tmp_path):
    database = tmp_path / "admission.sqlite"
    artifacts = tmp_path / "artifacts"
    initializeAdmissionRegistry(database)
    private = Ed25519PrivateKey.from_private_bytes(bytes(range(32)))
    public = private.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    trusted = {"test-key": TrustedIssuer("test-issuer", "test-key", public)}
    verifier = AdmissionVerifier(database, artifacts, trusted)
    return database, artifacts, private.private_bytes_raw(), trusted, verifier


def _stamp(day: date) -> str:
    return day.strftime("%Y%m%d")


def _issueTestReceipt(
    context,
    *,
    kind,
    content,
    subjectHash=None,
    status="admitted",
    knowledgeAsOf="20191231",
    issuedAt="20191231T000000Z",
    ruleId=None,
    ruleVersion="1",
    ruleHash=None,
    parentReceiptIds=(),
    frequency="quarter",
    stepSpan=1,
    maxAdmittedStep=0,
):
    database, artifacts, private, trusted = context
    artifactHash = putAdmissionArtifact(artifacts, content)
    return issueAdmissionReceipt(
        database,
        artifacts,
        privateKey=private,
        kind=kind,
        subjectHash=artifactHash if subjectHash is None else subjectHash,
        artifactHash=artifactHash,
        parentReceiptIds=parentReceiptIds,
        ruleId=ruleId or f"test-{kind}",
        ruleVersion=ruleVersion,
        ruleHash=ruleHash or canonicalPayloadHash({"rule": kind}),
        issuerId="test-issuer",
        issuerKeyId="test-key",
        issuerExecutableHash=sha256(b"test-scenario-issuer-v1").hexdigest(),
        knowledgeAsOf=knowledgeAsOf,
        revisionPolicy="asKnown",
        coverage="asOfExact",
        frequency=frequency,
        stepSpan=stepSpan,
        maxAdmittedStep=maxAdmittedStep,
        status=status,
        issuedAt=issuedAt,
        trustedIssuers=trusted,
    )


_OPERATING_STATE_VALUES = {
    "price": 10.0,
    "demandVolume": 200.0,
    "unitCost": 2.0,
    "fixedCost": 50.0,
    "capacityUnits": 100.0,
    "cash": 10_000.0,
    "debt": 20.0,
}
_OPERATING_STATE_UNITS = {
    "price": "currencyPerUnit",
    "demandVolume": "units",
    "unitCost": "currencyPerUnit",
    "fixedCost": "currency",
    "capacityUnits": "units",
    "cash": "currency",
    "debt": "currency",
}


def _issueOperatingCompiledState(
    context,
    *,
    decisionAsOf: str,
    values: dict[str, float] | None = None,
):
    database, artifacts, private, trusted = context
    verifier = AdmissionVerifier(database, artifacts, trusted)
    stateValues = dict(_OPERATING_STATE_VALUES if values is None else values)
    decision = date(int(decisionAsOf[:4]), int(decisionAsOf[4:6]), int(decisionAsOf[6:8]))
    availableAt = _stamp(decision - timedelta(days=1))
    sourceReceipt = _issueTestReceipt(
        context,
        kind="dataVintage",
        content=canonicalPayloadBytes({"operatingState": decisionAsOf, "values": stateValues}),
        status="verifiedVintage",
        knowledgeAsOf=availableAt,
        issuedAt=f"{availableAt}T000000Z",
        frequency="mixed",
    )
    vintage = VintageRef(
        artifactKind="providerObservation",
        provider="fixture",
        artifactId=f"operating-state-{decisionAsOf}",
        artifactHash=sourceReceipt.artifactHash,
        payloadHash=sourceReceipt.subjectHash,
        knowledgeAsOf=availableAt,
        availableAt=availableAt,
        revisionPolicy="asKnown",
        coverage="asOfExact",
        fiscalThrough=availableAt,
        receiptId=sourceReceipt.receiptId,
    )
    observations = tuple(
        makeVariableObservation(
            providerId="fixture",
            datasetId="operating-state",
            entityId="005930",
            signalId=variableId,
            value=value,
            unit=_OPERATING_STATE_UNITS[variableId],
            frequency="quarter",
            timing="stock",
            transformId="identity-v1",
            evidenceRole="observed",
            eventAt=availableAt,
            availableAt=availableAt,
            knowledgeAsOf=availableAt,
            availabilityPrecision="date",
            revisionId=f"r-{decisionAsOf}",
            vintage=vintage,
            normalizationRuleHash=sha256(b"identity-v1").hexdigest(),
        )
        for variableId, value in sorted(stateValues.items())
    )
    signalIds = tuple(sorted(stateValues))
    batch = buildProviderObservationBatch(
        observations,
        providerId="fixture",
        datasetId="operating-state",
        entityId="005930",
        signalIds=signalIds,
        cutoffAsOf=decisionAsOf,
    )
    batch = issueProviderObservationBatch(
        batch,
        database,
        artifacts,
        privateKey=private,
        issuerId="test-issuer",
        issuerKeyId="test-key",
        issuedAt=f"{decisionAsOf}T000000Z",
        trustedIssuers=trusted,
    )
    registry = buildStateVariableRegistry(
        tuple(
            StateVariableSpec(
                variableId=variableId,
                signalId=variableId,
                providerId="fixture",
                datasetId="operating-state",
                unit=_OPERATING_STATE_UNITS[variableId],
                role="state",
                evidenceRole="observed",
                frequency="quarter",
                timing="stock",
                transformId="identity-v1",
                maxStalenessDays=400,
                lower=0.0,
            )
            for variableId in sorted(stateValues)
        )
    )
    compiled = compilePointInTimeState(
        registry,
        (batch,),
        StateCompileSpec(
            entityId="005930",
            market="KR",
            decisionAsOf=decisionAsOf,
            consumerId="operating-world",
            consumerVersion="1",
            variableIds=signalIds,
            requireExact=True,
        ),
        admissionVerifier=verifier,
    )
    return issuePointInTimeState(
        compiled,
        database,
        artifacts,
        privateKey=private,
        issuerId="test-issuer",
        issuerKeyId="test-key",
        issuedAt=f"{decisionAsOf}T000000Z",
        trustedIssuers=trusted,
    )


def _certifiedOperatingInputs(context, *, decisionAsOf: str = "20210104"):
    compiled = _issueOperatingCompiledState(context, decisionAsOf=decisionAsOf)
    inputs = operatingInputsFromCompiledState(
        compiled,
        priceElasticity=0.0,
        capacityUnitsPerCurrency=1.0,
        taxRate=0.0,
    )
    certificate = issueOperatingLawCertificate(
        inputs,
        evidenceRows=(
            {"step": 1, "metric": "operatingProfit", "estimate": 1.0, "threshold": 0.0, "operator": "ge"},
            {"step": 2, "metric": "operatingProfit", "estimate": 1.0, "threshold": 0.0, "operator": "ge"},
        ),
        knowledgeAsOf="20191231",
        evidenceKind="identifiedIntervention",
    )
    inputs = replace(
        inputs,
        operatingLawEvidenceKind="identifiedIntervention",
        operatingLawCertificate=certificate,
        priceChangeEvidenceKind="identifiedIntervention",
        priceChangeCertificateId="3" * 64,
        capacityInvestmentEvidenceKind="identifiedIntervention",
        capacityInvestmentCertificateId="4" * 64,
    )
    model = _buildOperatingWorld(inputs, maxFinancing=200.0, maxInvestment=200.0)
    initial = _initialStateFromInputs(inputs)
    receipt = _issueTestReceipt(
        context,
        kind="initialState",
        content=initialStateAdmissionArtifact(model, initial),
        subjectHash=initialStateAdmissionSubjectHash(model, initial),
        parentReceiptIds=(compiled.stateReceiptId,),
        ruleId=INITIAL_STATE_RULE_ID,
        ruleVersion=INITIAL_STATE_RULE_VERSION,
        ruleHash=INITIAL_STATE_RULE_HASH,
        knowledgeAsOf=inputs.knowledgeAsOf,
        issuedAt=f"{decisionAsOf}T000000Z",
        frequency="mixed",
    )
    return replace(inputs, initialStateAdmissionReceiptId=receipt.receiptId), compiled, receipt


def _issueBasePathReceipt(database, artifacts, private, trusted, basePathSet):
    artifactHash = putAdmissionArtifact(artifacts, pathSetAdmissionArtifact(basePathSet.paths))
    assert artifactHash == pathSetAdmissionSubjectHash(basePathSet.paths)
    receipt = issueAdmissionReceipt(
        database,
        artifacts,
        privateKey=private,
        kind="pathSet",
        subjectHash=artifactHash,
        artifactHash=artifactHash,
        parentReceiptIds=(),
        ruleId="path-admission",
        ruleVersion="1",
        ruleHash=sha256(b"path-admission-v1").hexdigest(),
        issuerId="test-issuer",
        issuerKeyId="test-key",
        issuerExecutableHash=sha256(b"path-issuer-v1").hexdigest(),
        knowledgeAsOf="20250101",
        revisionPolicy="asKnown",
        coverage="asOfExact",
        frequency=basePathSet.audit.frequency,
        stepSpan=basePathSet.audit.stepSpan,
        maxAdmittedStep=2,
        status="admitted",
        issuedAt="20250102T000000Z",
        trustedIssuers=trusted,
    )
    return replace(basePathSet, paths=bindPathAdmissionReceipt(basePathSet.paths, receipt.receiptId))


def _issueScenarioPathPackageReceipt(database, artifacts, private, trusted, pathSet, *, kind=None, status="documented"):
    artifactHash = putAdmissionArtifact(artifacts, scenarioPathPackageArtifact(pathSet))
    assert artifactHash == scenarioPathPackageSubjectHash(pathSet)
    return issueAdmissionReceipt(
        database,
        artifacts,
        privateKey=private,
        kind=kind or COMPOSED_CONDITIONAL_PATH_PACKAGE_KIND,
        subjectHash=artifactHash,
        artifactHash=artifactHash,
        parentReceiptIds=scenarioPathPackageParentReceiptIds(pathSet),
        ruleId=COMPOSED_CONDITIONAL_PATH_PACKAGE_RULE_ID,
        ruleVersion=COMPOSED_CONDITIONAL_PATH_PACKAGE_RULE_VERSION,
        ruleHash=COMPOSED_CONDITIONAL_PATH_PACKAGE_RULE_HASH,
        issuerId="test-issuer",
        issuerKeyId="test-key",
        issuerExecutableHash=sha256(b"scenario-package-issuer-v1").hexdigest(),
        knowledgeAsOf="20250101",
        revisionPolicy="explicitAssumption" if status == "documented" else "asKnown",
        coverage="synthetic" if status == "documented" else "asOfExact",
        frequency=pathSet.audit.frequency,
        stepSpan=pathSet.audit.stepSpan,
        maxAdmittedStep=0,
        status=status,
        issuedAt="20250102T000000Z",
        trustedIssuers=trusted,
    )


def _issueConditionalExperimentReceipt(
    database,
    artifacts,
    private,
    trusted,
    experiment,
    *,
    kind=None,
    revisionPolicy="explicitAssumption",
    coverage="synthetic",
    parentReceiptIds=None,
):
    artifactHash = putAdmissionArtifact(artifacts, conditionalScenarioExperimentArtifact(experiment))
    assert artifactHash == conditionalScenarioExperimentSubjectHash(experiment)
    return issueAdmissionReceipt(
        database,
        artifacts,
        privateKey=private,
        kind=kind or CONDITIONAL_SCENARIO_EXPERIMENT_RESULT_KIND,
        subjectHash=artifactHash,
        artifactHash=artifactHash,
        parentReceiptIds=(
            conditionalScenarioExperimentParentReceiptIds(experiment)
            if parentReceiptIds is None
            else tuple(parentReceiptIds)
        ),
        ruleId=CONDITIONAL_SCENARIO_EXPERIMENT_RESULT_RULE_ID,
        ruleVersion=CONDITIONAL_SCENARIO_EXPERIMENT_RESULT_RULE_VERSION,
        ruleHash=CONDITIONAL_SCENARIO_EXPERIMENT_RESULT_RULE_HASH,
        issuerId="test-issuer",
        issuerKeyId="test-key",
        issuerExecutableHash=sha256(b"conditional-experiment-issuer-v1").hexdigest(),
        knowledgeAsOf="20250101",
        revisionPolicy=revisionPolicy,
        coverage=coverage,
        frequency="scenario",
        stepSpan=1,
        maxAdmittedStep=0,
        status="documented",
        issuedAt="20250102T000000Z",
        trustedIssuers=trusted,
    )


def _issueConditionalStrategyEvaluationReceipt(
    database,
    artifacts,
    private,
    trusted,
    evaluation,
    *,
    kind=None,
    revisionPolicy="explicitAssumption",
    coverage="synthetic",
    parentReceiptIds=None,
):
    artifactHash = putAdmissionArtifact(artifacts, conditionalStrategyEvaluationArtifact(evaluation))
    assert artifactHash == conditionalStrategyEvaluationSubjectHash(evaluation)
    return issueAdmissionReceipt(
        database,
        artifacts,
        privateKey=private,
        kind=kind or CONDITIONAL_STRATEGY_EVALUATION_KIND,
        subjectHash=artifactHash,
        artifactHash=artifactHash,
        parentReceiptIds=(
            conditionalStrategyEvaluationParentReceiptIds(evaluation)
            if parentReceiptIds is None
            else tuple(parentReceiptIds)
        ),
        ruleId=CONDITIONAL_STRATEGY_EVALUATION_RULE_ID,
        ruleVersion=CONDITIONAL_STRATEGY_EVALUATION_RULE_VERSION,
        ruleHash=CONDITIONAL_STRATEGY_EVALUATION_RULE_HASH,
        issuerId="test-issuer",
        issuerKeyId="test-key",
        issuerExecutableHash=sha256(b"conditional-strategy-evaluation-issuer-v1").hexdigest(),
        knowledgeAsOf="20250101",
        revisionPolicy=revisionPolicy,
        coverage=coverage,
        frequency="scenario",
        stepSpan=1,
        maxAdmittedStep=0,
        status="documented",
        issuedAt="20250102T000000Z",
        trustedIssuers=trusted,
    )


def _inputs():
    rows = (
        OperatingPrimitive("price", 10.0, "currencyPerUnit", "explicitAssumption", "assumption://price"),
        OperatingPrimitive("demandVolume", 100.0, "units", "explicitAssumption", "assumption://volume"),
        OperatingPrimitive("unitCost", 6.0, "currencyPerUnit", "explicitAssumption", "assumption://unit-cost"),
        OperatingPrimitive("fixedCost", 100.0, "currency", "explicitAssumption", "assumption://fixed-cost"),
        OperatingPrimitive("capacityUnits", 150.0, "units", "explicitAssumption", "assumption://capacity"),
        OperatingPrimitive("cash", 500.0, "currency", "observed", "filing://cash"),
        OperatingPrimitive("debt", 20.0, "currency", "observed", "filing://debt"),
    )
    return operatingInputsFromPrimitives(
        rows,
        asOf="20250101",
        priceElasticity=1.0,
        capacityUnitsPerCurrency=1.0,
        taxRate=0.0,
    )


def _baselines():
    return tuple(
        OperatingShockBaseline(
            target,
            0.04 if target == "debtRate" else 0.0,
            "effectiveRatePerStep" if target == "debtRate" else "ratioChangePerStep",
            "explicitAssumption",
            f"assumption://baseline/{target}",
        )
        for target in (
            "marketPriceChange",
            "demandChange",
            "unitCostChange",
            "fixedCostChange",
            "capacityChange",
            "debtRate",
        )
    )


def _case(caseId: str, demandShock: tuple[float, ...], variableId: str = "demandShock") -> OperatingScenarioCase:
    card = DriverCard(
        cardId=f"{caseId}-demand",
        sourceKind="explicitAssumption",
        providerId="user",
        datasetId="manual-scenario",
        entityId="005930",
        frequency="quarter",
        stepSpan=1,
        factors=(DriverFactorSpec(variableId, "simpleReturn", "quarter", "innovation", "manual-shock-v1"),),
        historyStatus="explicitAssumption",
        sourceRefs=(f"assumption://{caseId}/demand",),
        assumptionId=f"{caseId}-demand",
        claim=f"{caseId} demand scenario.",
        falsifier="Order book does not move with the demand scenario.",
    )
    pathSet = buildDriverPathSet(
        (
            DriverAssumptionSource(
                card,
                tuple({variableId: value} for value in demandShock),
            ),
        ),
        knowledgeAsOf="20250101",
        horizon=len(demandShock),
        pathCount=1,
        blockLength=1,
        seed=1,
    )
    return OperatingScenarioCase(
        caseId,
        caseId.title(),
        pathSet,
        (
            OperatingTransmissionExposure(
                f"{caseId}-demand-volume",
                variableId,
                "demandChange",
                1.0,
                "ratioChangePerStep/simpleReturn",
                "explicitAssumption",
                f"assumption://{caseId}/demand-volume",
            ),
        ),
        _baselines(),
        refs=(f"scenario://{caseId}",),
    )


def _admittedBasePathSet():
    card = DriverCard(
        cardId="observed-demand-history",
        sourceKind="history",
        providerId="fixture",
        datasetId="driver-history",
        entityId="005930",
        frequency="quarter",
        stepSpan=1,
        factors=(DriverFactorSpec("observedDemandShock", "simpleReturn", "quarter", "innovation", "history-v1"),),
        historyStatus="asKnown",
        sourceRefs=("providerObservationBatch:observed-demand-history",),
    )
    panel = pl.DataFrame(
        {
            "eventTime": ["20240101", "20240401", "20240701", "20241001"],
            "availableAt": ["20240102", "20240402", "20240702", "20241002"],
            "observedDemandShock": [0.01, -0.02, 0.03, 0.02],
        }
    )
    base = buildDriverPathSet(
        (DriverHistorySource(card, panel),),
        knowledgeAsOf="20250101",
        horizon=2,
        pathCount=2,
        blockLength=1,
        seed=5,
        minObservations=4,
    )
    admittedPaths = bindPathAdmissionReceipt(
        bindAdmittedPathContent(
            tuple(
                replace(
                    path,
                    validationStatus="admitted",
                    certificateId="a" * 64,
                    maxAdmittedStep=2,
                    historyStatus="asKnown",
                )
                for path in base.paths
            )
        ),
        "b" * 64,
    )
    return replace(base, paths=admittedPaths)


def _conditionalOverlayCase(
    caseId: str,
    shock: tuple[float, float],
    basePathSet=None,
) -> OperatingScenarioCase:
    card = DriverCard(
        cardId=f"{caseId}-manual-demand-overlay",
        sourceKind="explicitAssumption",
        providerId="user",
        datasetId="manual-scenario",
        entityId="005930",
        frequency="quarter",
        stepSpan=1,
        factors=(DriverFactorSpec("manualDemandAdjustment", "simpleReturn", "quarter", "change", "manual-v1"),),
        historyStatus="explicitAssumption",
        sourceRefs=(f"assumption://{caseId}/manual-demand-overlay",),
        assumptionId=f"{caseId}-manual-demand-overlay",
        claim=f"{caseId} explicit future demand overlay.",
        falsifier="The manual demand overlay is not the tested scenario.",
    )
    pathSet = composeDriverPathSetWithAssumptions(
        basePathSet or _admittedBasePathSet(),
        (DriverAssumptionSource(card, tuple({"manualDemandAdjustment": value} for value in shock)),),
        registryId=f"{caseId}-admitted-base-plus-overlay",
    )
    exposures = (
        OperatingTransmissionExposure(
            f"{caseId}-observed-demand",
            "observedDemandShock",
            "demandChange",
            1.0,
            "ratioChangePerStep/simpleReturn",
            "explicitAssumption",
            f"assumption://{caseId}/law/observed-demand",
        ),
        OperatingTransmissionExposure(
            f"{caseId}-manual-demand",
            "manualDemandAdjustment",
            "demandChange",
            1.0,
            "ratioChangePerStep/simpleReturn",
            "explicitAssumption",
            f"assumption://{caseId}/law/manual-demand",
        ),
    )
    return OperatingScenarioCase(
        caseId,
        caseId.title(),
        pathSet,
        exposures,
        _baselines(),
        refs=(f"scenario://{caseId}",),
    )


def _signedConditionalExperiment(tmp_path, *, stressShock=(-0.03, -0.02), investment=25.0):
    database, artifacts, private, trusted, verifier = _trust(tmp_path)
    basePathSet = _issueBasePathReceipt(database, artifacts, private, trusted, _admittedBasePathSet())
    baseCase = _conditionalOverlayCase("base", (0.01, 0.02), basePathSet)
    stressCase = _conditionalOverlayCase("stress", stressShock, basePathSet)
    baseReceipt = _issueScenarioPathPackageReceipt(database, artifacts, private, trusted, baseCase.pathSet)
    stressReceipt = _issueScenarioPathPackageReceipt(database, artifacts, private, trusted, stressCase.pathSet)
    baseCase = replace(baseCase, admissionVerifier=verifier, scenarioPathPackageReceiptId=baseReceipt.receiptId)
    stressCase = replace(stressCase, admissionVerifier=verifier, scenarioPathPackageReceiptId=stressReceipt.receiptId)
    experiment = runConditionalScenarioExperiment(
        "005930",
        _inputs(),
        (baseCase, stressCase),
        _strategies(investment=investment),
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )
    return database, artifacts, private, trusted, verifier, experiment


def _signedConditionalStrategyEvaluation(tmp_path, *, investment=25.0):
    database, artifacts, private, trusted, verifier, experiment = _signedConditionalExperiment(
        tmp_path,
        investment=investment,
    )
    experimentReceipt = _issueConditionalExperimentReceipt(database, artifacts, private, trusted, experiment)
    sealedExperiment = bindConditionalScenarioExperimentReceipt(experiment, experimentReceipt.receiptId, verifier)
    evaluation = buildConditionalStrategyEvaluation(sealedExperiment)
    return database, artifacts, private, trusted, verifier, sealedExperiment, evaluation


def _measured_case(
    caseId: str,
    shocks: tuple[tuple[float, float], ...],
    *,
    receiptId: str = _COEFFICIENT_RECEIPT_ID,
    fxCoefficient: float = 0.4,
    oilCoefficient: float = -0.2,
    aggregationGroup: str = "macro-demand-vector",
) -> OperatingScenarioCase:
    factors = (
        DriverFactorSpec("fxChange", "simpleReturn", "quarter", "innovation", "simple-return-v1"),
        DriverFactorSpec("oilChange", "simpleReturn", "quarter", "innovation", "simple-return-v1"),
    )
    card = DriverCard(
        cardId=f"{caseId}-macro",
        sourceKind="explicitAssumption",
        providerId="user",
        datasetId="manual-scenario",
        entityId="005930",
        frequency="quarter",
        stepSpan=1,
        factors=factors,
        historyStatus="explicitAssumption",
        sourceRefs=(f"assumption://{caseId}/macro",),
        assumptionId=f"{caseId}-macro",
        claim=f"{caseId} macro scenario.",
        falsifier="Macro factor movement does not change demand.",
    )
    pathSet = buildDriverPathSet(
        (
            DriverAssumptionSource(
                card,
                tuple({"fxChange": fx, "oilChange": oil} for fx, oil in shocks),
            ),
        ),
        knowledgeAsOf="20250101",
        horizon=len(shocks),
        pathCount=1,
        blockLength=1,
        seed=1,
    )
    sourceRef = f"driverCoefficientAdmission:{receiptId}"
    exposures = (
        OperatingTransmissionExposure(
            f"{caseId}-fx-demand",
            "fxChange",
            "demandChange",
            fxCoefficient,
            "ratioChangePerStep/simpleReturn",
            "measuredAssociation",
            sourceRef,
            aggregationGroup=aggregationGroup,
            sourceFrequency="quarter",
            sourceTiming="innovation",
            sourceTransformId="simple-return-v1",
            sourceFactorContractHash=sourceFactorContractHash(
                variableId="fxChange",
                unit="simpleReturn",
                frequency="quarter",
                timing="innovation",
                transformId="simple-return-v1",
            ),
        ),
        OperatingTransmissionExposure(
            f"{caseId}-oil-demand",
            "oilChange",
            "demandChange",
            oilCoefficient,
            "ratioChangePerStep/simpleReturn",
            "measuredAssociation",
            sourceRef,
            aggregationGroup=aggregationGroup,
            sourceFrequency="quarter",
            sourceTiming="innovation",
            sourceTransformId="simple-return-v1",
            sourceFactorContractHash=sourceFactorContractHash(
                variableId="oilChange",
                unit="simpleReturn",
                frequency="quarter",
                timing="innovation",
                transformId="simple-return-v1",
            ),
        ),
    )
    binding = ScenarioCoefficientBinding(
        admissionReceiptId=receiptId,
        subjectHash=_COEFFICIENT_SUBJECT_HASH,
        ruleHash=_COEFFICIENT_RULE_HASH,
        ruleId=MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_ID,
        ruleVersion=MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_VERSION,
        parentReceiptIds=_COEFFICIENT_PARENT_RECEIPTS,
        sourceVariableIds=("fxChange", "oilChange"),
        targetShock="demandChange",
        frequency="quarter",
        stepSpan=1,
        maxAdmittedStep=len(shocks),
        coefficientVectorHash=_COEFFICIENT_VECTOR_HASH,
        featureSpecHash=_COEFFICIENT_FEATURE_SPEC_HASH,
        designFrameHash=_COEFFICIENT_DESIGN_FRAME_HASH,
        exposureContractHash=scenarioCoefficientExposureContractHash(exposures),
        calibrationId="macro-demand-calibration",
        reportId="macro-demand-oos",
        fitDesignFrameHash=_COEFFICIENT_FIT_DESIGN_FRAME_HASH,
        oosDesignFrameHash=_COEFFICIENT_OOS_DESIGN_FRAME_HASH,
        sourceRefs=("oosReport://macro-demand",),
    )
    return OperatingScenarioCase(
        caseId,
        caseId.title(),
        pathSet,
        exposures,
        _baselines(),
        refs=(f"scenario://{caseId}",),
        coefficientBindings=(binding,),
    )


def _strategies(investment: float = 25.0):
    return (
        buildOperatingStrategy(
            "hold",
            priceChange=(0.0, 0.0),
            capacityInvestment=(0.0, 0.0),
            borrow=(0.0, 0.0),
            repay=(0.0, 0.0),
            refs=("strategy://hold",),
            isBaseline=True,
        ),
        buildOperatingStrategy(
            "invest",
            priceChange=(0.0, 0.0),
            capacityInvestment=(investment, 0.0),
            borrow=(0.0, 0.0),
            repay=(0.0, 0.0),
            refs=("strategy://invest",),
        ),
    )


def _policyReadyStrategies(investment: float = 25.0):
    hold, invest = _strategies(investment=investment)
    return (
        replace(hold, policyVersion="static-hold-v1", policyProvenance="fixture://hold"),
        replace(invest, policyVersion="static-invest-v1", policyProvenance="fixture://invest"),
    )


def _observedBaselines():
    return tuple(
        OperatingShockBaseline(
            target,
            0.04 if target == "debtRate" else 0.0,
            "effectiveRatePerStep" if target == "debtRate" else "ratioChangePerStep",
            "observed",
            f"providerObservationBatch:operating-baseline-{target}",
        )
        for target in (
            "marketPriceChange",
            "demandChange",
            "unitCostChange",
            "fixedCostChange",
            "capacityChange",
            "debtRate",
        )
    )


def _admittedHistoryPathSet(context, *, pathCount: int = 125):
    sourceReceipt = _issueTestReceipt(
        context,
        kind="dataVintage",
        content=b"observed demand history known 2019-12-31",
        status="verifiedVintage",
        knowledgeAsOf="20191231",
        issuedAt="20191231T000000Z",
        frequency="quarter",
    )
    vintage = VintageRef(
        artifactKind="driverPathSet",
        provider="fixture",
        artifactId="observed-demand-history",
        artifactHash=sourceReceipt.artifactHash,
        payloadHash=sourceReceipt.subjectHash,
        knowledgeAsOf="20191231",
        availableAt="20191231",
        revisionPolicy="asKnown",
        coverage="asOfExact",
        eventThrough="20191001",
        receiptId=sourceReceipt.receiptId,
    )
    card = DriverCard(
        cardId="observed-demand-history",
        sourceKind="history",
        providerId="fixture",
        datasetId="driver-history",
        entityId="005930",
        frequency="quarter",
        stepSpan=1,
        factors=(DriverFactorSpec("observedDemandShock", "simpleReturn", "quarter", "innovation", "history-v1"),),
        historyStatus="asKnown",
        sourceRefs=("providerObservationBatch:observed-demand-history",),
    )
    panel = pl.DataFrame(
        {
            "eventTime": [
                "20180101",
                "20180401",
                "20180701",
                "20181001",
                "20190101",
                "20190401",
                "20190701",
                "20191001",
            ],
            "availableAt": [
                "20180102",
                "20180402",
                "20180702",
                "20181002",
                "20190102",
                "20190402",
                "20190702",
                "20191002",
            ],
            "observedDemandShock": [0.02, -0.01, 0.03, 0.01, -0.02, 0.04, 0.00, 0.02],
        }
    )
    pathSet = buildDriverPathSet(
        (DriverHistorySource(card, panel),),
        knowledgeAsOf="20191231",
        horizon=2,
        pathCount=pathCount,
        blockLength=1,
        seed=11,
        minObservations=8,
    )
    admitted = bindAdmittedPathContent(
        tuple(
            replace(
                path,
                validationStatus="admitted",
                certificateId="5" * 64,
                maxAdmittedStep=2,
                historyStatus="asKnown",
                vintage=vintage,
            )
            for path in pathSet.paths
        )
    )
    pathReceipt = _issueTestReceipt(
        context,
        kind="pathSet",
        content=pathSetAdmissionArtifact(admitted),
        subjectHash=pathSetAdmissionSubjectHash(admitted),
        parentReceiptIds=(sourceReceipt.receiptId,),
        ruleId="driver-history-path-admission",
        ruleHash=sha256(b"driver-history-path-admission-v1").hexdigest(),
        knowledgeAsOf="20191231",
        issuedAt="20191231T000000Z",
        frequency="quarter",
        maxAdmittedStep=2,
    )
    return replace(pathSet, paths=bindPathAdmissionReceipt(admitted, pathReceipt.receiptId)), sourceReceipt, pathReceipt


def _measuredHistoryCase(
    context,
    verifier,
    *,
    caseId: str,
    compiledState,
):
    pathSet, sourceReceipt, sourcePathReceipt = _admittedHistoryPathSet(context)
    coefficientPayload = {
        "coefficient": "observedDemandShockToDemandChange",
        "source": "observedDemandShock",
        "target": "demandChange",
    }
    coefficientSubject = canonicalPayloadHash(coefficientPayload)
    coefficientReceipt = _issueTestReceipt(
        context,
        kind="driverCoefficient",
        content=canonicalPayloadBytes(coefficientPayload),
        subjectHash=coefficientSubject,
        parentReceiptIds=(sourceReceipt.receiptId,),
        ruleId=MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_ID,
        ruleVersion=MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_VERSION,
        ruleHash=MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_HASH,
        knowledgeAsOf="20191231",
        issuedAt="20191231T000000Z",
        frequency="quarter",
        maxAdmittedStep=2,
    )
    sourceRef = f"driverCoefficientAdmission:{coefficientReceipt.receiptId}"
    exposure = OperatingTransmissionExposure(
        f"{caseId}-observed-demand",
        "observedDemandShock",
        "demandChange",
        1.0,
        "ratioChangePerStep/simpleReturn",
        "measuredAssociation",
        sourceRef,
        aggregationGroup="observed-demand",
        sourceFrequency="quarter",
        sourceTiming="innovation",
        sourceTransformId="history-v1",
        sourceFactorContractHash=sourceFactorContractHash(
            variableId="observedDemandShock",
            unit="simpleReturn",
            frequency="quarter",
            timing="innovation",
            transformId="history-v1",
        ),
    )
    binding = ScenarioCoefficientBinding(
        admissionReceiptId=coefficientReceipt.receiptId,
        subjectHash=coefficientSubject,
        ruleHash=MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_HASH,
        ruleId=MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_ID,
        ruleVersion=MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_VERSION,
        parentReceiptIds=(sourceReceipt.receiptId,),
        sourceVariableIds=("observedDemandShock",),
        targetShock="demandChange",
        frequency="quarter",
        stepSpan=1,
        maxAdmittedStep=2,
        coefficientVectorHash=canonicalPayloadHash({"coefficient": 1.0}),
        featureSpecHash=canonicalPayloadHash({"feature": "observedDemandShock"}),
        designFrameHash=canonicalPayloadHash({"design": "observedDemandShock"}),
        exposureContractHash=scenarioCoefficientExposureContractHash((exposure,)),
        calibrationId="observed-demand-calibration",
        reportId="observed-demand-oos",
        fitDesignFrameHash=canonicalPayloadHash({"fit": "observedDemandShock"}),
        oosDesignFrameHash=canonicalPayloadHash({"oos": "observedDemandShock"}),
        sourceRefs=("providerObservationBatch:observed-demand-history",),
    )
    return (
        OperatingScenarioCase(
            caseId,
            caseId.title(),
            pathSet,
            (exposure,),
            _observedBaselines(),
            refs=(f"scenario://{caseId}",),
            compiledState=compiledState,
            admissionVerifier=verifier,
            coefficientBindings=(binding,),
        ),
        sourceReceipt,
        sourcePathReceipt,
        coefficientReceipt,
    )


def _rawOperatingPaths(case: OperatingScenarioCase):
    factorSpecs = driverFactorsToOperatingSpecs(case.pathSet.factorSpecs)
    return tuple(
        bridgeOperatingPath(
            path,
            case.exposures,
            factorSpecs=factorSpecs,
            baselines=case.baselines,
            compiledState=case.compiledState,
            statePrimitives=case.statePrimitives,
            stateRef=case.stateRef,
            admissionVerifier=case.admissionVerifier,
            pathId=f"{case.caseId}:{path.pathId}",
        ).path
        for path in case.pathSet.paths
    )


def _issueOperatingPathAdmission(context, rawPaths, parentReceiptIds):
    certificateId = "6" * 64
    admitted = bindAdmittedPathContent(
        tuple(
            replace(
                path,
                validationStatus="admitted",
                certificateId=certificateId,
                maxAdmittedStep=2,
            )
            for path in rawPaths
        )
    )
    receipt = _issueTestReceipt(
        context,
        kind="pathSet",
        content=pathSetAdmissionArtifact(admitted),
        subjectHash=pathSetAdmissionSubjectHash(admitted),
        parentReceiptIds=parentReceiptIds,
        ruleId="operating-path-admission",
        ruleHash=sha256(b"operating-path-admission-v1").hexdigest(),
        knowledgeAsOf=admitted[0].knowledgeAsOf,
        issuedAt="20191231T000000Z",
        frequency=admitted[0].frequency,
        stepSpan=admitted[0].stepSpan,
        maxAdmittedStep=2,
    )
    return receipt, bindPathAdmissionReceipt(admitted, receipt.receiptId), certificateId


def _policyEpisodePayload(episode):
    return {
        name: getattr(episode, name)
        for name in episode.__dataclass_fields__
        if name not in {"episodeId", "episodeReceiptId"}
    }


def _issueOperatingPolicyEvidence(
    context,
    ledger,
    verifier,
    *,
    run,
    paths,
    strategies,
    pathReceipt,
):
    database, artifacts, private, trusted = context
    baseline, candidate = strategies
    modelReceipt = _issueTestReceipt(
        context,
        kind="modelExecutable",
        content=b"operating world executable",
        subjectHash=run.executableHash,
    )
    baselineReceipt = _issueTestReceipt(
        context,
        kind="strategy",
        content=b"hold strategy",
        subjectHash=strategyContractHash(baseline),
    )
    candidateReceipt = _issueTestReceipt(
        context,
        kind="strategy",
        content=b"invest strategy",
        subjectHash=strategyContractHash(candidate),
    )
    outcomeReceipt = _issueTestReceipt(
        context,
        kind="dataVintage",
        content=b"operating policy outcome panel known 2021-01-01",
        status="verifiedVintage",
        knowledgeAsOf="20210101",
        issuedAt="20210101T000000Z",
    )
    objective = run.objectives[0]
    parameterContractHash = parameterContractHashFor(paths)
    signedEpisodes = []
    for index in range(40):
        origin = date(2020, 1, 3) + timedelta(days=7 * index)
        originText = _stamp(origin)
        compiled = _issueOperatingCompiledState(context, decisionAsOf=originText)
        primitiveRows = []
        for pathIndex, path in enumerate(paths):
            baseValue = float(pathIndex)
            primitiveRows.append(
                PolicyPathPrimitive(
                    pathId=path.pathId,
                    pathOrdinal=pathIndex,
                    pathWeight=1.0 if path.weight is None else float(path.weight),
                    parameterDrawHash=canonicalPayloadHash(dict(path.parameterDraws)),
                    baselineMetricByStep=(baseValue, baseValue + 0.1),
                    candidateMetricByStep=(baseValue + 2.0, baseValue + 2.2),
                    baselineBreachesByStep=((), ()),
                    candidateBreachesByStep=((), ()),
                    baselineTraceHash=canonicalPayloadHash({"origin": index, "path": pathIndex, "strategy": "hold"}),
                    candidateTraceHash=canonicalPayloadHash({"origin": index, "path": pathIndex, "strategy": "invest"}),
                )
            )
        originKey = canonicalPayloadHash(
            {
                "protocol": "policy-oos-episode-v1",
                "originAsOf": originText,
                "outcomeThrough": _stamp(origin + timedelta(days=28)),
                "executableHash": run.executableHash,
                "baselineContract": strategyContractHash(baseline),
                "candidateContract": strategyContractHash(candidate),
                "objectiveContract": objectiveContractHash(objective),
                "constraintContract": constraintContractHash(run.constraints),
                "pathRuleHash": pathReceipt.ruleHash,
                "parameterContract": parameterContractHash,
                "stateCompilationContract": compiled.stateCompilationContractHash,
            }
        )
        raw = PolicyOosEpisode(
            episodeId="",
            originKey=originKey,
            originOrdinal=index,
            originAsOf=originText,
            outcomeThrough=_stamp(origin + timedelta(days=28)),
            outcomeAvailableAt="20210101",
            evaluationKnowledgeAsOf="20210101",
            evidenceKind="modelReplay",
            runHash=canonicalPayloadHash({"run": index}),
            resultHash=canonicalPayloadHash({"result": index}),
            traceRoot=canonicalPayloadHash({"trace": index}),
            executableHash=run.executableHash,
            parameterHash=run.parameterHash,
            dataVintageHash=run.dataVintageHash,
            initialStateAsOf=compiled.decisionAsOf,
            initialStateKnowledgeAsOf=compiled.knowledgeAsOf,
            initialStateContentHash=compiled.stateId,
            initialStateReceiptId="",
            pointInTimeStateReceiptId=compiled.stateReceiptId,
            stateManifestHash=compiled.manifestHash,
            stateCompilationContractHash=compiled.stateCompilationContractHash,
            stateContractHash=compiled.stateContractHash,
            initialState=compiled.statePrimitives,
            pathAdmissionReceiptId=pathReceipt.receiptId,
            pathContentHash=pathReceipt.subjectHash,
            pathRuleId=pathReceipt.ruleId,
            pathRuleVersion=pathReceipt.ruleVersion,
            pathRuleHash=pathReceipt.ruleHash,
            parameterContractHash=parameterContractHash,
            outcomeVintageReceiptId=outcomeReceipt.receiptId,
            baselineStrategyId=baseline.strategyId,
            baselinePolicyVersion=baseline.policyVersion,
            baselineStrategyContractHash=strategyContractHash(baseline),
            candidateStrategyId=candidate.strategyId,
            candidatePolicyVersion=candidate.policyVersion,
            candidateStrategyContractHash=strategyContractHash(candidate),
            objective=objective,
            objectiveContractHash=objectiveContractHash(objective),
            constraintContractHash=constraintContractHash(run.constraints),
            paths=tuple(primitiveRows),
        )
        raw = replace(raw, episodeId=canonicalPayloadHash(_policyEpisodePayload(raw)))
        initialReceipt = _issueTestReceipt(
            context,
            kind="initialState",
            content=stateAdmissionArtifact(
                raw.initialState,
                asOf=raw.initialStateAsOf,
                knowledgeAsOf=raw.initialStateKnowledgeAsOf,
                decisionAsOf=raw.originAsOf,
            ),
            subjectHash=raw.initialStateContentHash,
            parentReceiptIds=(compiled.stateReceiptId,),
            ruleId=INITIAL_STATE_RULE_ID,
            ruleVersion=INITIAL_STATE_RULE_VERSION,
            ruleHash=INITIAL_STATE_RULE_HASH,
            knowledgeAsOf=raw.initialStateKnowledgeAsOf,
            issuedAt=f"{originText}T000000Z",
            frequency="mixed",
        )
        signed = admitPolicyOosEpisode(
            raw,
            database,
            artifacts,
            privateKey=private,
            initialStateReceiptId=initialReceipt.receiptId,
            modelReceiptId=modelReceipt.receiptId,
            baselineStrategyReceiptId=baselineReceipt.receiptId,
            candidateStrategyReceiptId=candidateReceipt.receiptId,
            issuerId="test-issuer",
            issuerKeyId="test-key",
            issuerExecutableHash=sha256(b"test-policy-issuer-v1").hexdigest(),
            issuedAt="20210101T120000Z",
            trustedIssuers=trusted,
        )
        appendPolicyOosEpisode(ledger, signed, admissionVerifier=verifier)
        signedEpisodes.append(signed)
    snapshot = readPolicyOosLedger(ledger, admissionVerifier=verifier)
    batch = sealPolicyOosBatch(
        snapshot,
        database,
        artifacts,
        privateKey=private,
        issuerId="test-issuer",
        issuerKeyId="test-key",
        issuerExecutableHash="7" * 64,
        issuedAt="20210102T000000Z",
        trustedIssuers=trusted,
    )
    certificate = issuePolicyEvaluationCertificate(
        snapshot,
        batch,
        PolicyEvaluationSpec(materialityMargin=0.5),
        database,
        artifacts,
        privateKey=private,
        issuerId="test-issuer",
        issuerKeyId="test-key",
        issuerExecutableHash="7" * 64,
        issuedAt="20210103T000000Z",
        trustedIssuers=trusted,
    )
    return PolicyAdmissionEvidence(snapshot, batch, certificate)


def _threeStrategies():
    return (
        buildOperatingStrategy(
            "hold",
            priceChange=(0.0, 0.0),
            capacityInvestment=(0.0, 0.0),
            borrow=(0.0, 0.0),
            repay=(0.0, 0.0),
            refs=("strategy://hold",),
            isBaseline=True,
        ),
        buildOperatingStrategy(
            "invest",
            priceChange=(0.0, 0.0),
            capacityInvestment=(35.0, 0.0),
            borrow=(0.0, 0.0),
            repay=(0.0, 0.0),
            refs=("strategy://invest",),
        ),
        buildOperatingStrategy(
            "defend",
            priceChange=(0.04, 0.04),
            capacityInvestment=(0.0, 0.0),
            borrow=(0.0, 0.0),
            repay=(10.0, 0.0),
            refs=("strategy://defend",),
        ),
    )


def _multiVariableCase(
    caseId: str,
    demandShock: tuple[float, float],
    unitCostShock: tuple[float, float],
    capacityShock: tuple[float, float],
) -> OperatingScenarioCase:
    factors = (
        DriverFactorSpec("demandShock", "simpleReturn", "quarter", "innovation", "manual-shock-v1"),
        DriverFactorSpec("unitCostShock", "simpleReturn", "quarter", "innovation", "manual-shock-v1"),
        DriverFactorSpec("capacityShock", "simpleReturn", "quarter", "innovation", "manual-shock-v1"),
    )
    card = DriverCard(
        cardId=f"{caseId}-three-variable",
        sourceKind="explicitAssumption",
        providerId="user",
        datasetId="manual-scenario-grid",
        entityId="005930",
        frequency="quarter",
        stepSpan=1,
        factors=factors,
        historyStatus="explicitAssumption",
        sourceRefs=(f"assumption://{caseId}/three-variable",),
        assumptionId=f"{caseId}-three-variable",
        claim=f"{caseId} demand, unit cost, and capacity assumption set.",
        falsifier="Observed demand, unit cost, or capacity path does not match the assumption set.",
    )
    pathSet = buildDriverPathSet(
        (
            DriverAssumptionSource(
                card,
                tuple(
                    {
                        "demandShock": demandShock[index],
                        "unitCostShock": unitCostShock[index],
                        "capacityShock": capacityShock[index],
                    }
                    for index in range(2)
                ),
            ),
        ),
        knowledgeAsOf="20250101",
        horizon=2,
        pathCount=1,
        blockLength=1,
        seed=7,
    )
    exposures = (
        OperatingTransmissionExposure(
            f"{caseId}-demand",
            "demandShock",
            "demandChange",
            1.0,
            "ratioChangePerStep/simpleReturn",
            "explicitAssumption",
            f"assumption://{caseId}/demand",
        ),
        OperatingTransmissionExposure(
            f"{caseId}-unit-cost",
            "unitCostShock",
            "unitCostChange",
            1.0,
            "ratioChangePerStep/simpleReturn",
            "explicitAssumption",
            f"assumption://{caseId}/unit-cost",
        ),
        OperatingTransmissionExposure(
            f"{caseId}-capacity",
            "capacityShock",
            "capacityChange",
            1.0,
            "ratioChangePerStep/simpleReturn",
            "explicitAssumption",
            f"assumption://{caseId}/capacity",
        ),
    )
    return OperatingScenarioCase(
        caseId,
        caseId.title(),
        pathSet,
        exposures,
        _baselines(),
        refs=(f"scenario://{caseId}",),
    )


def _experimentCases():
    return (
        _multiVariableCase("base", (0.0, 0.0), (0.0, 0.0), (0.0, 0.0)),
        _multiVariableCase("demandUp", (0.12, 0.08), (0.0, 0.0), (0.02, 0.02)),
        _multiVariableCase("costStress", (-0.04, -0.06), (0.16, 0.12), (-0.03, -0.02)),
        _multiVariableCase("capacityStress", (0.04, 0.02), (0.05, 0.03), (-0.18, -0.12)),
    )


def _score(result, strategyId: str, objectiveIndex: int = 0) -> float:
    row = next(item for item in result.strategyScores if item.strategyId == strategyId)
    return row.objectiveScores[objectiveIndex]


def testScenarioCompositionRunsSharedStrategiesAcrossNamedCases() -> None:
    comparison = compareOperatingScenarioCases(
        _inputs(),
        (_case("base", (0.0, 0.0)), _case("stress", (-0.5, -0.5))),
        _strategies(),
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )
    assert comparison.decisionStatus == "conditionalOnly"
    assert comparison.recommendation is None
    assert comparison.strategyIds == ("hold", "invest")
    assert len(comparison.caseResults) == 2
    base, stress = comparison.caseResults
    assert base.caseId == "base"
    assert stress.caseId == "stress"
    assert _score(base, "hold") > _score(stress, "hold")
    assert all(result.counts.interventionCount == 1 for result in comparison.caseResults)
    assert all(result.counts.explicitAssumptionCount > 0 for result in comparison.caseResults)
    assert all(result.decisionStatus == "conditionalOnly" for result in comparison.caseResults)
    assert any("automatic recommendation disabled" in warning for warning in comparison.warnings)
    assert comparison.comparisonHash


def testScenarioCompositionHashBindsCaseAssumptionContent() -> None:
    first = compareOperatingScenarioCases(
        _inputs(),
        (_case("base", (0.0, 0.0)),),
        _strategies(),
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )
    changed = compareOperatingScenarioCases(
        _inputs(),
        (_case("base", (0.0, -0.1)),),
        _strategies(),
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )
    assert first.comparisonHash != changed.comparisonHash
    assert first.caseResults[0].pathSetHash != changed.caseResults[0].pathSetHash


def testConditionalScenarioExperimentSweepsAssumptionsAndStrategies() -> None:
    experiment = runConditionalScenarioExperiment(
        "005930",
        _inputs(),
        _experimentCases(),
        _threeStrategies(),
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )
    assert experiment.schemaVersion == "conditional-scenario-experiment-v1"
    assert experiment.entityId == "005930"
    assert experiment.scenarioCount == 4
    assert experiment.strategyCount == 3
    assert experiment.cellCount == 12
    assert experiment.decisionStatus == "conditionalOnly"
    assert experiment.recommendationCeiling == "conditionalOnly"
    assert experiment.recommendation is None
    assert experiment.strategyIds == ("hold", "invest", "defend")
    assert experiment.assumptionSetIds == ("base", "demandUp", "costStress", "capacityStress")
    assert len(set(experiment.assumptionSetHashes)) == 4
    assert experiment.strategySetHash
    assert experiment.simulationSpecHash
    assert experiment.resultSetHash
    assert experiment.experimentHash
    assert len(experiment.caseLedgers) == 4
    assert len(experiment.caseLedgerHashes) == 4
    assert len(set(experiment.caseLedgerHashes)) == 4
    assert experiment.providerObservationBatchRefs == ()
    assert experiment.explicitAssumptionIds == (
        "base-three-variable",
        "demandUp-three-variable",
        "costStress-three-variable",
        "capacityStress-three-variable",
    )
    assert experiment.pathAssumptionHashes == tuple(ledger.pathAssumptionHash for ledger in experiment.caseLedgers)
    assert all(experiment.pathAssumptionHashes)
    assert len(experiment.strategySummaries) == 3
    assert len(experiment.fragilityCells) == 4
    assert all(summary.totalCellCount == 4 for summary in experiment.strategySummaries)
    assert sum(summary.leaderCellCount for summary in experiment.strategySummaries) >= 4
    assert all(cell.regret >= 0.0 for cell in experiment.cells)
    assert experiment.fragilityCells[0].leaderMargin <= experiment.fragilityCells[-1].leaderMargin
    assert "assumptionSweepPresent" in experiment.blockedReasons
    assert "strategySweepPresent" in experiment.blockedReasons
    assert "automaticRecommendationDisabled" in experiment.blockedReasons
    assert "conditionalExperimentNotPolicyRecommendation" in experiment.blockedReasons
    assert "pathAdmissionMissing" in experiment.blockedReasons
    assert "policyEvaluationCertificateMissing" in experiment.blockedReasons


def testConditionalScenarioExperimentHashBindsAssumptionGridAndResults() -> None:
    first = runConditionalScenarioExperiment(
        "005930",
        _inputs(),
        _experimentCases(),
        _threeStrategies(),
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )
    repeat = runConditionalScenarioExperiment(
        "005930",
        _inputs(),
        _experimentCases(),
        _threeStrategies(),
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )
    changedCases = (
        _multiVariableCase("base", (0.0, 0.0), (0.0, 0.0), (0.0, 0.0)),
        _multiVariableCase("demandUp", (0.18, 0.12), (0.0, 0.0), (0.02, 0.02)),
        _multiVariableCase("costStress", (-0.04, -0.06), (0.16, 0.12), (-0.03, -0.02)),
        _multiVariableCase("capacityStress", (0.04, 0.02), (0.05, 0.03), (-0.18, -0.12)),
    )
    changed = runConditionalScenarioExperiment(
        "005930",
        _inputs(),
        changedCases,
        _threeStrategies(),
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )
    assert first.experimentHash == repeat.experimentHash
    assert first.resultSetHash == repeat.resultSetHash
    assert first.simulationSpecHash == repeat.simulationSpecHash
    assert first.assumptionSetHashes != changed.assumptionSetHashes
    assert first.pathAssumptionHashes != changed.pathAssumptionHashes
    assert first.simulationSpecHash != changed.simulationSpecHash
    assert first.resultSetHash != changed.resultSetHash
    assert first.experimentHash != changed.experimentHash
    assert first.cells != changed.cells


def testConditionalScenarioExperimentRequiresSweepShape() -> None:
    with pytest.raises(ScenarioCompositionError, match="at least two assumption"):
        runConditionalScenarioExperiment(
            "005930",
            _inputs(),
            (_experimentCases()[0],),
            _threeStrategies(),
            debtLimit=1_000.0,
            maxFinancing=200.0,
            maxInvestment=200.0,
        )
    with pytest.raises(ScenarioCompositionError, match="at least two strategies"):
        runConditionalScenarioExperiment(
            "005930",
            _inputs(),
            _experimentCases(),
            (_threeStrategies()[0],),
            debtLimit=1_000.0,
            maxFinancing=200.0,
            maxInvestment=200.0,
        )


def testScenarioCompositionRejectsInterventionInsidePath() -> None:
    with pytest.raises(ScenarioCompositionError, match="intervention actions"):
        compareOperatingScenarioCases(
            _inputs(),
            (_case("bad", (0.1, 0.1), variableId="priceChange"),),
            _strategies(),
            debtLimit=1_000.0,
            maxFinancing=200.0,
            maxInvestment=200.0,
        )


def testScenarioCompositionRejectsDuplicateCaseIds() -> None:
    with pytest.raises(ScenarioCompositionError, match="unique ids"):
        compareOperatingScenarioCases(
            _inputs(),
            (_case("base", (0.0, 0.0)), _case("base", (-0.1, -0.1))),
            _strategies(),
            debtLimit=1_000.0,
            maxFinancing=200.0,
            maxInvestment=200.0,
        )


def testOneCompanyScenarioLoopSummarizesConditionsStateAndStrategyBlocks() -> None:
    loop = compareOneCompanyTwoScenarioStrategies(
        "005930",
        _inputs(),
        (_case("base", (0.0, 0.0)), _case("stress", (-0.5, -0.5))),
        _strategies(),
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )
    assert loop.schemaVersion == "one-company-scenario-loop-v1"
    assert loop.entityId == "005930"
    assert loop.scenarioCount == 2
    assert loop.strategyCount == 2
    assert loop.decisionStatus == "conditionalOnly"
    assert loop.recommendationCeiling == "conditionalOnly"
    assert loop.recommendation is None
    assert loop.strategyIds == ("hold", "invest")
    assert "strategy://hold" in loop.strategyRefs
    assert "filing://cash" in loop.initialStateRefs
    assert "automaticRecommendationDisabled" in loop.blockedReasons
    assert "comparisonDecisionStatus:conditionalOnly" in loop.blockedReasons
    assert loop.loopHash
    base, stress = loop.caseLedgers
    assert base.caseId == "base"
    assert stress.caseId == "stress"
    assert base.factorIds == ("demandShock",)
    assert "scenario://base" in base.conditionRefs
    assert "assumption://base/demand" in base.assumptionRefs
    assert "filing://debt" in base.stateRefs
    assert base.bridgeHashes
    assert base.runHash
    assert base.resultHash
    assert base.executableHash
    assert base.parameterHash
    assert base.dataVintageHash
    assert base.traceRoot
    assert base.strategyScores
    assert base.scoreLeaderStrategies
    assert "explicitAssumptionPresent" in base.blockedReasons
    assert "pathAdmissionIncomplete" in base.blockedReasons
    assert "pathAdmissionMissing" in base.blockedReasons
    assert "policyEvaluationCertificateMissing" in base.blockedReasons


def testAdmittedBasePathReceiptDoesNotTransferToExplicitOverlayScenario() -> None:
    baseCase = _conditionalOverlayCase("base", (0.01, 0.02))
    stressCase = _conditionalOverlayCase("stress", (-0.03, -0.02))
    loop = compareOneCompanyTwoScenarioStrategies(
        "005930",
        _inputs(),
        (baseCase, stressCase),
        _strategies(),
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )
    base, stress = loop.caseLedgers
    assert loop.recommendation is None
    assert base.pathHistoryInputHash == stress.pathHistoryInputHash
    assert base.basePathSetHash == stress.basePathSetHash
    assert base.basePathAdmissionReceiptId == "b" * 64
    assert base.basePathAdmissionReceiptId == stress.basePathAdmissionReceiptId
    assert base.basePathAdmissionContentHash == pathSetAdmissionSubjectHash(_admittedBasePathSet().paths)
    assert base.basePathAdmissionSubjectHash == base.basePathAdmissionContentHash
    assert base.basePathValidationStatus == "admitted"
    assert base.basePathMaxAdmittedStep == 2
    assert base.pathAssumptionHash != stress.pathAssumptionHash
    assert base.pathOverlayHash != stress.pathOverlayHash
    assert base.composedPathSetHash != base.basePathSetHash
    assert base.composedPathSetHash != stress.composedPathSetHash
    assert base.basePathAdmissionScope == "historyOnly"
    assert base.composedPathAdmissionStatus == "notAdmitted"
    assert base.pathAdmissionTransferStatus == "notTransferred"
    assert "basePathAdmittedButOverlayConditional" in base.pathAdmissionTransferBlockedBy
    assert "explicitFutureAdjustmentPresent" in base.pathAdmissionTransferBlockedBy
    assert "pathAdmissionNotTransferredFromObservedHistory" in base.pathAdmissionTransferBlockedBy
    assert base.pathAdmissionReceiptId == ""
    assert base.pathAdmissionContentHash == ""
    assert base.pathCertificateIds == ()
    assert base.policyEvaluationCertificateId == ""
    assert base.policyEvaluationCertificateReceiptId == ""
    assert base.policyEvaluationCertificateStatus == ""
    assert base.policyEvaluationParentReceiptIds == ()
    assert base.recommendationSource == ""
    assert base.recommendationEvidenceKind == ""
    assert base.recommendationEvidenceReceiptId == ""
    assert base.conditionalReceiptIdsExcludedFromPolicy == ()
    assert "basePathAdmittedButOverlayConditional" in base.blockedReasons
    assert "basePathAdmissionScopeHistoryOnly" in base.blockedReasons
    assert "composedPathAdmissionNotGranted" in base.blockedReasons
    assert "explicitOverlayBlocksPolicyRecommendation" in base.blockedReasons
    assert "pathAdmissionMissing" in base.blockedReasons
    assert "policyEvaluationRequiresAdmittedComposedPath" in base.blockedReasons
    assert "policyEvaluationCertificateMissing" in base.blockedReasons
    assert "policyEvidenceMissing" in base.blockedReasons
    assert "automaticRecommendationDisabled" in loop.blockedReasons

    pathVintage = VintageRef(
        artifactKind="driverPathSet",
        provider="fixture",
        artifactId="base-path-vintage",
        artifactHash="c" * 64,
        payloadHash="d" * 64,
        knowledgeAsOf="20250101",
        availableAt="20250101",
        revisionPolicy="asKnown",
        coverage="asOfExact",
        eventThrough="20241001",
        receiptId="e" * 64,
    )
    launderedPaths = tuple(
        replace(
            path,
            validationStatus="admitted",
            certificateId="a" * 64,
            maxAdmittedStep=2,
            historyStatus="asKnown",
            admissionContentHash=base.basePathAdmissionContentHash,
            admissionReceiptId=base.basePathAdmissionReceiptId,
            vintage=pathVintage,
        )
        for path in baseCase.pathSet.paths
    )
    launderedCase = replace(baseCase, pathSet=replace(baseCase.pathSet, paths=launderedPaths))
    with pytest.raises(ScenarioCompositionError, match="explicit overlay cannot carry path admission"):
        compareOneCompanyTwoScenarioStrategies(
            "005930",
            _inputs(),
            (launderedCase, stressCase),
            _strategies(),
            debtLimit=1_000.0,
            maxFinancing=200.0,
            maxInvestment=200.0,
        )


def testConditionalPathPackageReceiptDocumentsOverlayWithoutRecommendation(tmp_path) -> None:
    database, artifacts, private, trusted, verifier = _trust(tmp_path)
    basePathSet = _issueBasePathReceipt(database, artifacts, private, trusted, _admittedBasePathSet())
    baseCase = _conditionalOverlayCase("base", (0.01, 0.02), basePathSet)
    stressCase = _conditionalOverlayCase("stress", (-0.03, -0.02), basePathSet)
    baseReceipt = _issueScenarioPathPackageReceipt(database, artifacts, private, trusted, baseCase.pathSet)
    stressReceipt = _issueScenarioPathPackageReceipt(database, artifacts, private, trusted, stressCase.pathSet)
    baseCase = replace(baseCase, admissionVerifier=verifier, scenarioPathPackageReceiptId=baseReceipt.receiptId)
    stressCase = replace(stressCase, admissionVerifier=verifier, scenarioPathPackageReceiptId=stressReceipt.receiptId)

    loop = compareOneCompanyTwoScenarioStrategies(
        "005930",
        _inputs(),
        (baseCase, stressCase),
        _strategies(),
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )

    base, stress = loop.caseLedgers
    assert loop.recommendation is None
    assert base.scenarioPathPackageHash == scenarioPathPackageSubjectHash(baseCase.pathSet)
    assert base.scenarioPathPackageSubjectHash == base.scenarioPathPackageHash
    assert base.scenarioPathPackageReceiptId == baseReceipt.receiptId
    assert base.scenarioPathPackageReceiptKind == COMPOSED_CONDITIONAL_PATH_PACKAGE_KIND
    assert base.scenarioPathPackageReceiptStatus == "documented"
    assert base.scenarioPathPackageParentReceiptIds == scenarioPathPackageParentReceiptIds(baseCase.pathSet)
    assert base.basePathAdmissionReceiptId in base.scenarioPathPackageParentReceiptIds
    assert base.pathAdmissionReceiptId == ""
    assert base.pathAdmissionContentHash == ""
    assert base.pathCertificateIds == ()
    assert base.policyEvaluationCertificateId == ""
    assert base.policyEvaluationCertificateReceiptId == ""
    assert base.policyEvaluationCertificateStatus == ""
    assert base.policyEvaluationParentReceiptIds == ()
    assert base.recommendationSource == ""
    assert base.recommendationEvidenceKind == ""
    assert base.recommendationEvidenceReceiptId == ""
    assert base.conditionalReceiptIdsExcludedFromPolicy == (baseReceipt.receiptId,)
    assert base.composedPathAdmissionStatus == "notAdmitted"
    assert base.pathAdmissionTransferStatus == "notTransferred"
    assert "conditionalReceiptNotPathAdmission" in base.blockedReasons
    assert "conditionalReceiptIdsExcludedFromPolicy" in base.blockedReasons
    assert "policyAdmittedRecommendationBlocked" in base.blockedReasons
    assert "explicitOverlayBlocksPolicyRecommendation" in base.blockedReasons
    assert "policyEvaluationRequiresAdmittedComposedPath" in base.blockedReasons
    assert "policyEvidenceMissing" in base.blockedReasons
    assert f"composedPathPackage:{baseReceipt.receiptId}" in base.conditionRefs
    assert f"composedPathSubject:{base.scenarioPathPackageSubjectHash}" in base.conditionRefs
    assert f"basePathAdmission:{base.basePathAdmissionReceiptId}" in base.conditionRefs
    assert f"explicitOverlay:{base.pathOverlayHash}" in base.conditionRefs
    for stepHash in base.pathAssumptionStepHashes:
        assert f"explicitAssumptionStep:{stepHash}" in base.conditionRefs
    assert stress.scenarioPathPackageReceiptId == stressReceipt.receiptId
    assert stress.scenarioPathPackageSubjectHash != base.scenarioPathPackageSubjectHash

    repeatBase = _conditionalOverlayCase("base", (0.01, 0.02), basePathSet)
    changedBase = _conditionalOverlayCase("base", (0.01, 0.03), basePathSet)
    assert scenarioPathPackageSubjectHash(repeatBase.pathSet) == base.scenarioPathPackageSubjectHash
    assert scenarioPathPackageSubjectHash(changedBase.pathSet) != base.scenarioPathPackageSubjectHash


def testConditionalPathPackageReceiptCannotBeUsedAsPathAdmission(tmp_path) -> None:
    database, artifacts, private, trusted, verifier = _trust(tmp_path)
    basePathSet = _issueBasePathReceipt(database, artifacts, private, trusted, _admittedBasePathSet())
    baseCase = _conditionalOverlayCase("base", (0.01, 0.02), basePathSet)
    stressCase = _conditionalOverlayCase("stress", (-0.03, -0.02), basePathSet)
    receipt = _issueScenarioPathPackageReceipt(database, artifacts, private, trusted, baseCase.pathSet)
    baseCase = replace(baseCase, admissionVerifier=verifier, scenarioPathPackageReceiptId=receipt.receiptId)
    stressCase = replace(stressCase, admissionVerifier=verifier)

    launderedPaths = tuple(
        replace(
            path,
            validationStatus="admitted",
            certificateId="a" * 64,
            maxAdmittedStep=2,
            historyStatus="asKnown",
            admissionContentHash=scenarioPathPackageSubjectHash(baseCase.pathSet),
            admissionReceiptId=receipt.receiptId,
        )
        for path in baseCase.pathSet.paths
    )
    launderedCase = replace(baseCase, pathSet=replace(baseCase.pathSet, paths=launderedPaths))
    with pytest.raises(ScenarioCompositionError, match="explicit overlay cannot carry path admission"):
        compareOneCompanyTwoScenarioStrategies(
            "005930",
            _inputs(),
            (launderedCase, stressCase),
            _strategies(),
            debtLimit=1_000.0,
            maxFinancing=200.0,
            maxInvestment=200.0,
        )


def testConditionalPathPackageReceiptRejectsAdmissionKindOrStatus(tmp_path) -> None:
    database, artifacts, private, trusted, verifier = _trust(tmp_path)
    basePathSet = _issueBasePathReceipt(database, artifacts, private, trusted, _admittedBasePathSet())
    baseCase = _conditionalOverlayCase("base", (0.01, 0.02), basePathSet)
    stressCase = _conditionalOverlayCase("stress", (-0.03, -0.02), basePathSet)
    wrongKind = _issueScenarioPathPackageReceipt(
        database,
        artifacts,
        private,
        trusted,
        baseCase.pathSet,
        kind="pathSet",
    )
    with pytest.raises(ScenarioCompositionError, match="scenario path package receipt verification failed"):
        compareOneCompanyTwoScenarioStrategies(
            "005930",
            _inputs(),
            (
                replace(baseCase, admissionVerifier=verifier, scenarioPathPackageReceiptId=wrongKind.receiptId),
                stressCase,
            ),
            _strategies(),
            debtLimit=1_000.0,
            maxFinancing=200.0,
            maxInvestment=200.0,
        )

    admittedStatus = _issueScenarioPathPackageReceipt(
        database,
        artifacts,
        private,
        trusted,
        stressCase.pathSet,
        status="admitted",
    )
    with pytest.raises(ScenarioCompositionError, match="scenario path package receipt contract mismatch"):
        compareOneCompanyTwoScenarioStrategies(
            "005930",
            _inputs(),
            (
                baseCase,
                replace(stressCase, admissionVerifier=verifier, scenarioPathPackageReceiptId=admittedStatus.receiptId),
            ),
            _strategies(),
            debtLimit=1_000.0,
            maxFinancing=200.0,
            maxInvestment=200.0,
        )


def testHistoryOnlyOperatingPathAndPolicyCertificateOpenRecommendation(tmp_path) -> None:
    database, artifacts, private, trusted, verifier = _trust(tmp_path)
    context = (database, artifacts, private, trusted)
    ledger = tmp_path / "policy-oos.sqlite"
    initializePolicyOosLedger(ledger)
    inputs, compiled, initialReceipt = _certifiedOperatingInputs(context)
    strategies = _policyReadyStrategies()
    case, sourceReceipt, sourcePathReceipt, coefficientReceipt = _measuredHistoryCase(
        context,
        verifier,
        caseId="base",
        compiledState=compiled,
    )
    rawPaths = _rawOperatingPaths(case)
    operatingReceipt, admittedPaths, operatingCertificateId = _issueOperatingPathAdmission(
        context,
        rawPaths,
        (
            sourceReceipt.receiptId,
            sourcePathReceipt.receiptId,
            coefficientReceipt.receiptId,
        ),
    )
    case = replace(
        case,
        operatingPathAdmissionReceiptId=operatingReceipt.receiptId,
        operatingPathCertificateId=operatingCertificateId,
    )
    preliminary = runOperatingStrategies(
        inputs,
        admittedPaths,
        strategies,
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
        admissionVerifier=verifier,
    )
    assert preliminary.decisionStatus == "conditionalOnly"
    assert preliminary.recommendation is None

    policyEvidence = _issueOperatingPolicyEvidence(
        context,
        ledger,
        verifier,
        run=preliminary,
        paths=admittedPaths,
        strategies=strategies,
        pathReceipt=operatingReceipt,
    )
    comparison = compareOperatingScenarioCases(
        inputs,
        (replace(case, policyAdmissionEvidence=policyEvidence),),
        strategies,
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
        policyObjectiveIndex=0,
    )

    result = comparison.caseResults[0]
    assert comparison.decisionStatus == "comparable"
    assert comparison.recommendation == "invest"
    assert result.decisionStatus == "comparable"
    assert result.recommendation == "invest"
    assert result.initialStateAdmissionReceiptId == initialReceipt.receiptId
    assert result.pathAdmissionReceiptId == operatingReceipt.receiptId
    assert result.pathAdmissionContentHash == pathSetAdmissionSubjectHash(admittedPaths)
    assert result.pathAdmissionContentHash == operatingReceipt.subjectHash
    assert result.pathCertificateIds == (operatingCertificateId,)
    assert result.policyEvaluationEligibility == "eligible"
    assert result.policyEvaluationCertificateId == policyEvidence.certificate.certificateId
    assert result.policyEvaluationCertificateReceiptId == policyEvidence.certificate.certificateReceiptId
    assert result.policyEvaluationCertificateStatus == "policyAdmitted"
    assert result.policyEvaluationParentReceiptIds == (policyEvidence.certificate.batchReceiptId,)
    assert result.recommendationSource == "policyAdmitted"
    assert result.recommendationEvidenceKind == "policyEvaluationCertificate"
    assert result.recommendationEvidenceReceiptId == policyEvidence.certificate.certificateReceiptId
    assert result.conditionalReceiptIdsExcludedFromPolicy == ()
    assert result.composedPathAdmissionStatus == "admitted"
    assert result.pathAdmissionTransferStatus == "composedPathAdmitted"
    assert result.pathAdmissionTransferBlockedBy == ()
    assert result.counts.explicitAssumptionCount == 0
    assert result.counts.conditionalWarningCount == 0
    assert result.counts.unvalidatedPathCount == 0
    assert result.counts.retrospectivePathCount == 0
    assert result.counts.admittedPathCount == result.counts.pathCount
    assert "policyEvaluationCertificateMissing" not in result.warnings
    assert all("automatic recommendation disabled" not in warning for warning in comparison.warnings)


def testConditionalScenarioExperimentReceiptDocumentsResultsWithoutRecommendation(tmp_path) -> None:
    database, artifacts, private, trusted, verifier, experiment = _signedConditionalExperiment(tmp_path)
    receipt = _issueConditionalExperimentReceipt(database, artifacts, private, trusted, experiment)
    sealed = bindConditionalScenarioExperimentReceipt(experiment, receipt.receiptId, verifier)
    payload = conditionalScenarioExperimentPayload(experiment)
    parentReceiptIds = conditionalScenarioExperimentParentReceiptIds(experiment)

    assert sealed.experimentReceiptSubjectHash == conditionalScenarioExperimentSubjectHash(experiment)
    assert sealed.experimentReceiptId == receipt.receiptId
    assert sealed.experimentReceiptKind == CONDITIONAL_SCENARIO_EXPERIMENT_RESULT_KIND
    assert sealed.experimentReceiptStatus == "documented"
    assert sealed.experimentReceiptParentReceiptIds == parentReceiptIds
    assert payload["recommendationStatus"] == "disabled"
    assert payload["recommendation"] is None
    assert payload["experiment"]["experimentHash"] == experiment.experimentHash
    assert payload["experiment"]["comparisonReplayHash"]
    assert payload["experiment"]["simulationSpecHash"] == experiment.simulationSpecHash
    assert payload["results"]["resultSetHash"] == experiment.resultSetHash
    assert payload["results"]["strategySummaries"]
    assert payload["results"]["fragilityCells"]
    assert payload["metrics"]["comparisonRuleHash"]
    assert payload["metrics"]["fragilityDefinitionHash"]
    assert payload["metrics"]["blockerRuleHash"]
    assert "conditionalExperimentNotPolicyRecommendation" in sealed.blockedReasons
    assert "automaticRecommendationDisabled" in sealed.blockedReasons
    assert sealed.recommendation is None
    assert sealed.experimentReceiptId != sealed.caseLedgers[0].scenarioPathPackageReceiptId
    assert all(ledger.scenarioPathPackageReceiptId in parentReceiptIds for ledger in sealed.caseLedgers)
    assert all(ledger.policyEvaluationCertificateId == "" for ledger in sealed.caseLedgers)
    assert all(ledger.pathAdmissionReceiptId == "" for ledger in sealed.caseLedgers)


def testConditionalScenarioExperimentReceiptBindsResultAndStrategyContent(tmp_path) -> None:
    _, _, _, _, _, first = _signedConditionalExperiment(tmp_path / "first")
    _, _, _, _, _, repeat = _signedConditionalExperiment(tmp_path / "repeat")
    changedDatabase, changedArtifacts, changedPrivate, changedTrusted, changedVerifier, changed = (
        _signedConditionalExperiment(tmp_path / "changed", investment=80.0)
    )
    assert conditionalScenarioExperimentSubjectHash(first) == conditionalScenarioExperimentSubjectHash(repeat)
    assert first.experimentHash == repeat.experimentHash
    assert conditionalScenarioExperimentSubjectHash(first) != conditionalScenarioExperimentSubjectHash(changed)
    assert first.strategySetHash != changed.strategySetHash
    assert first.resultSetHash != changed.resultSetHash

    receipt = _issueConditionalExperimentReceipt(
        changedDatabase, changedArtifacts, changedPrivate, changedTrusted, changed
    )
    tampered = replace(changed, strategySummaries=())
    with pytest.raises(ScenarioCompositionError, match="conditional experiment receipt verification failed"):
        bindConditionalScenarioExperimentReceipt(tampered, receipt.receiptId, changedVerifier)


def testCaseLedgerHashBindsExecutionTraceAndProviderLineage(tmp_path) -> None:
    _, _, _, _, _, experiment = _signedConditionalExperiment(tmp_path)
    ledger = experiment.caseLedgers[0]
    baseline = experiment.caseLedgerHashes[0]

    changes = (
        replace(ledger, executableHash="9" * 64),
        replace(ledger, traceRoot=canonicalPayloadHash({"tamperedTrace": ledger.caseId})),
        replace(ledger, traceCount=ledger.traceCount + 1),
        replace(ledger, retainedTraceCount=ledger.retainedTraceCount + 1),
        replace(ledger, recommendationCeiling="tampered"),
        replace(ledger, providerLaneLineageHash="8" * 64),
        replace(ledger, providerObservationBatchReceiptIds=("7" * 64,)),
        replace(ledger, rawSourceRefs=(*ledger.rawSourceRefs, "source:tampered")),
    )

    for changedLedger in changes:
        assert _caseLedgerHashes((changedLedger,))[0] != baseline


def testRawProviderObservationStringDoesNotBecomeReceiptLineage(tmp_path) -> None:
    _, _, _, _, _, experiment = _signedConditionalExperiment(tmp_path)
    base = experiment.caseLedgers[0]
    payload = conditionalScenarioExperimentPayload(experiment)
    payloadCase = payload["cases"][0]

    assert "providerObservationBatch:observed-demand-history" in base.providerObservationBatchRefs
    assert base.providerObservationBatchReceiptIds == ()
    assert "exactProviderObservationBatch" not in base.providerLineageStatus
    assert "unverifiedProviderObservationRef" in base.providerLineageStatus
    assert payload["inputs"]["providerObservationBatchReceiptIds"] == ()
    assert payloadCase["providerObservationBatchReceiptIds"] == ()
    assert payloadCase["providerLaneLineageHash"] == base.providerLaneLineageHash


def testConditionalScenarioExperimentReceiptRejectsWrongKindOrMissingParents(tmp_path) -> None:
    database, artifacts, private, trusted, verifier, experiment = _signedConditionalExperiment(tmp_path)
    wrongKind = _issueConditionalExperimentReceipt(
        database,
        artifacts,
        private,
        trusted,
        experiment,
        kind="policyEvaluation",
    )
    with pytest.raises(ScenarioCompositionError, match="conditional experiment receipt verification failed"):
        bindConditionalScenarioExperimentReceipt(experiment, wrongKind.receiptId, verifier)

    missingParents = _issueConditionalExperimentReceipt(
        database,
        artifacts,
        private,
        trusted,
        experiment,
        parentReceiptIds=(),
    )
    with pytest.raises(ScenarioCompositionError, match="conditional experiment receipt parent mismatch"):
        bindConditionalScenarioExperimentReceipt(experiment, missingParents.receiptId, verifier)

    wrongVintage = _issueConditionalExperimentReceipt(
        database,
        artifacts,
        private,
        trusted,
        experiment,
        revisionPolicy="asKnown",
        coverage="asOfExact",
    )
    with pytest.raises(ScenarioCompositionError, match="conditional experiment receipt contract mismatch"):
        bindConditionalScenarioExperimentReceipt(experiment, wrongVintage.receiptId, verifier)


def testConditionalStrategyEvaluationReceiptDocumentsJudgementWithoutRecommendation(tmp_path) -> None:
    database, artifacts, private, trusted, verifier, sealedExperiment, evaluation = (
        _signedConditionalStrategyEvaluation(tmp_path)
    )
    receipt = _issueConditionalStrategyEvaluationReceipt(database, artifacts, private, trusted, evaluation)
    sealedEvaluation = bindConditionalStrategyEvaluationReceipt(evaluation, receipt.receiptId, verifier)
    payload = conditionalStrategyEvaluationPayload(evaluation)
    parentReceiptIds = conditionalStrategyEvaluationParentReceiptIds(evaluation)

    assert sealedEvaluation.evaluationReceiptSubjectHash == conditionalStrategyEvaluationSubjectHash(evaluation)
    assert sealedEvaluation.evaluationReceiptId == receipt.receiptId
    assert sealedEvaluation.evaluationReceiptKind == CONDITIONAL_STRATEGY_EVALUATION_KIND
    assert sealedEvaluation.evaluationReceiptStatus == "documented"
    assert sealedEvaluation.evaluationReceiptParentReceiptIds == parentReceiptIds
    assert parentReceiptIds == (sealedExperiment.experimentReceiptId,)
    assert payload["recommendationStatus"] == "disabled"
    assert payload["recommendation"] is None
    assert payload["experimentResult"]["experimentReceiptId"] == sealedExperiment.experimentReceiptId
    assert payload["experimentResult"]["experimentReceiptSubjectHash"] == sealedExperiment.experimentReceiptSubjectHash
    assert payload["strategyJudgement"]["conditionalLeaderStrategyIds"] == evaluation.conditionalLeaderStrategyIds
    assert payload["strategyJudgement"]["strategyRows"]
    assert payload["strategyJudgement"]["fragileCases"]
    assert payload["hashes"]["leaderboardHash"] == evaluation.leaderboardHash
    assert payload["hashes"]["fragilitySummaryHash"] == evaluation.fragilitySummaryHash
    assert payload["hashes"]["blockerSummaryHash"] == evaluation.blockerSummaryHash
    assert payload["rules"]["selectionRuleHash"] == evaluation.selectionRuleHash
    assert payload["rules"]["robustnessRuleHash"] == evaluation.robustnessRuleHash
    assert "conditionalStrategyEvaluationDocumentedOnly" in sealedEvaluation.blockedReasons
    assert "strategyEvaluationReceiptNotPolicyCertificate" in sealedEvaluation.blockedReasons
    assert "conditionalExperimentNotPolicyRecommendation" in sealedEvaluation.blockedReasons
    assert "automaticRecommendationDisabled" in sealedEvaluation.blockedReasons
    assert "scoreLeaderNotRecommendation" in sealedEvaluation.blockedReasons
    assert sealedEvaluation.recommendation is None
    assert sealedEvaluation.pathAdmissionReceiptIds == ()
    assert sealedEvaluation.policyEvaluationCertificateIds == ()
    assert sealedEvaluation.evaluationReceiptId != sealedExperiment.experimentReceiptId
    assert sealedEvaluation.evaluationReceiptId not in sealedExperiment.experimentReceiptParentReceiptIds


def testConditionalStrategyEvaluationHashBindsExperimentAndRuleContent(tmp_path) -> None:
    _, _, _, _, _, _, first = _signedConditionalStrategyEvaluation(tmp_path / "first")
    _, _, _, _, _, _, repeat = _signedConditionalStrategyEvaluation(tmp_path / "repeat")
    changedDatabase, changedArtifacts, changedPrivate, changedTrusted, changedVerifier, _, changed = (
        _signedConditionalStrategyEvaluation(tmp_path / "changed", investment=80.0)
    )

    assert conditionalStrategyEvaluationSubjectHash(first) == conditionalStrategyEvaluationSubjectHash(repeat)
    assert first.evaluationHash == repeat.evaluationHash
    assert conditionalStrategyEvaluationSubjectHash(first) != conditionalStrategyEvaluationSubjectHash(changed)
    assert first.strategySetHash != changed.strategySetHash
    assert first.evaluationHash != changed.evaluationHash

    receipt = _issueConditionalStrategyEvaluationReceipt(
        changedDatabase,
        changedArtifacts,
        changedPrivate,
        changedTrusted,
        changed,
    )
    tampered = replace(changed, strategyRows=())
    with pytest.raises(ScenarioCompositionError, match="conditional strategy evaluation hash mismatch"):
        bindConditionalStrategyEvaluationReceipt(tampered, receipt.receiptId, changedVerifier)


def testConditionalStrategyEvaluationReceiptRejectsPolicyLaundering(tmp_path) -> None:
    database, artifacts, private, trusted, verifier, experiment = _signedConditionalExperiment(tmp_path / "unsealed")
    with pytest.raises(ScenarioCompositionError, match="sealed conditional experiment receipt"):
        buildConditionalStrategyEvaluation(experiment)

    database, artifacts, private, trusted, verifier, _, evaluation = _signedConditionalStrategyEvaluation(tmp_path)
    wrongKind = _issueConditionalStrategyEvaluationReceipt(
        database,
        artifacts,
        private,
        trusted,
        evaluation,
        kind="policyEvaluation",
    )
    with pytest.raises(ScenarioCompositionError, match="conditional strategy evaluation receipt verification failed"):
        bindConditionalStrategyEvaluationReceipt(evaluation, wrongKind.receiptId, verifier)

    missingParents = _issueConditionalStrategyEvaluationReceipt(
        database,
        artifacts,
        private,
        trusted,
        evaluation,
        parentReceiptIds=(),
    )
    with pytest.raises(ScenarioCompositionError, match="conditional strategy evaluation receipt parent mismatch"):
        bindConditionalStrategyEvaluationReceipt(evaluation, missingParents.receiptId, verifier)

    wrongVintage = _issueConditionalStrategyEvaluationReceipt(
        database,
        artifacts,
        private,
        trusted,
        evaluation,
        revisionPolicy="asKnown",
        coverage="asOfExact",
    )
    with pytest.raises(ScenarioCompositionError, match="conditional strategy evaluation receipt contract mismatch"):
        bindConditionalStrategyEvaluationReceipt(evaluation, wrongVintage.receiptId, verifier)


def testOneCompanyScenarioLoopCarriesAdmittedCoefficientBindingLedger() -> None:
    loop = compareOneCompanyTwoScenarioStrategies(
        "005930",
        _inputs(),
        (_measured_case("base", ((0.0, 0.0), (0.1, -0.1))), _measured_case("stress", ((-0.2, 0.3), (-0.1, 0.2)))),
        _strategies(),
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )
    assert loop.decisionStatus == "conditionalOnly"
    assert loop.recommendationCeiling == "conditionalOnly"
    assert loop.recommendation is None
    base, _ = loop.caseLedgers
    binding = _measured_case("base", ((0.0, 0.0), (0.1, -0.1))).coefficientBindings[0]
    assert base.coefficientAdmissionReceiptIds == (_COEFFICIENT_RECEIPT_ID,)
    assert base.coefficientBindingHashes == (scenarioCoefficientBindingHash(binding),)
    assert base.coefficientParentReceiptIds == _COEFFICIENT_PARENT_RECEIPTS
    assert f"driverCoefficientAdmission:{_COEFFICIENT_RECEIPT_ID}" in base.conditionRefs
    assert f"coefficientBinding:{scenarioCoefficientBindingHash(binding)}" in base.conditionRefs
    assert f"coefficientVector:{_COEFFICIENT_VECTOR_HASH}" in base.conditionRefs
    assert (
        "coefficientParentReceipt:3333333333333333333333333333333333333333333333333333333333333333"
        in base.conditionRefs
    )
    assert len(base.exposureLedgers) == 2
    assert {row.evidenceKind for row in base.exposureLedgers} == {"measuredAssociation"}
    assert {row.admissionReceiptId for row in base.exposureLedgers} == {_COEFFICIENT_RECEIPT_ID}
    assert {row.aggregationGroup for row in base.exposureLedgers} == {"macro-demand-vector"}
    assert {row.sourceVariableId for row in base.exposureLedgers} == {"fxChange", "oilChange"}
    assert all(row.sourceFactorContractHash for row in base.exposureLedgers)
    assert "pathAdmissionMissing" in base.blockedReasons
    assert "policyEvaluationCertificateMissing" in base.blockedReasons
    assert "automaticRecommendationDisabled" in loop.blockedReasons


def testOneCompanyScenarioLoopHashBindsCoefficientBindingContent() -> None:
    first = compareOneCompanyTwoScenarioStrategies(
        "005930",
        (_inputs()),
        (_measured_case("base", ((0.0, 0.0), (0.1, -0.1))), _measured_case("stress", ((-0.2, 0.3), (-0.1, 0.2)))),
        _strategies(),
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )
    changedCoefficient = compareOneCompanyTwoScenarioStrategies(
        "005930",
        _inputs(),
        (
            _measured_case("base", ((0.0, 0.0), (0.1, -0.1)), fxCoefficient=0.5),
            _measured_case("stress", ((-0.2, 0.3), (-0.1, 0.2))),
        ),
        _strategies(),
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )
    changedGroup = compareOneCompanyTwoScenarioStrategies(
        "005930",
        _inputs(),
        (
            _measured_case("base", ((0.0, 0.0), (0.1, -0.1)), aggregationGroup="macro-demand-alt"),
            _measured_case("stress", ((-0.2, 0.3), (-0.1, 0.2))),
        ),
        _strategies(),
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )
    changedReceipt = compareOneCompanyTwoScenarioStrategies(
        "005930",
        _inputs(),
        (
            _measured_case("base", ((0.0, 0.0), (0.1, -0.1)), receiptId="5" * 64),
            _measured_case("stress", ((-0.2, 0.3), (-0.1, 0.2))),
        ),
        _strategies(),
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )
    assert first.loopHash != changedCoefficient.loopHash
    assert first.loopHash != changedGroup.loopHash
    assert first.loopHash != changedReceipt.loopHash


def testOneCompanyScenarioLoopRejectsMeasuredExposureWithoutBinding() -> None:
    base = _measured_case("base", ((0.0, 0.0), (0.1, -0.1)))
    with pytest.raises(ScenarioCompositionError, match="coefficient binding"):
        compareOneCompanyTwoScenarioStrategies(
            "005930",
            _inputs(),
            (
                replace(base, coefficientBindings=()),
                _measured_case("stress", ((-0.2, 0.3), (-0.1, 0.2))),
            ),
            _strategies(),
            debtLimit=1_000.0,
            maxFinancing=200.0,
            maxInvestment=200.0,
        )


def testOneCompanyScenarioLoopRejectsTamperedCoefficientBindingContract() -> None:
    base = _measured_case("base", ((0.0, 0.0), (0.1, -0.1)))
    tampered = replace(base.coefficientBindings[0], exposureContractHash="6" * 64)
    with pytest.raises(ScenarioCompositionError, match="exposure contract"):
        compareOneCompanyTwoScenarioStrategies(
            "005930",
            _inputs(),
            (
                replace(base, coefficientBindings=(tampered,)),
                _measured_case("stress", ((-0.2, 0.3), (-0.1, 0.2))),
            ),
            _strategies(),
            debtLimit=1_000.0,
            maxFinancing=200.0,
            maxInvestment=200.0,
        )


def testOneCompanyScenarioLoopRequiresTwoCasesAndTwoStrategies() -> None:
    with pytest.raises(ScenarioCompositionError, match="exactly two scenario"):
        compareOneCompanyTwoScenarioStrategies(
            "005930",
            _inputs(),
            (_case("base", (0.0, 0.0)),),
            _strategies(),
            debtLimit=1_000.0,
            maxFinancing=200.0,
            maxInvestment=200.0,
        )
    with pytest.raises(ScenarioCompositionError, match="exactly two strategies"):
        compareOneCompanyTwoScenarioStrategies(
            "005930",
            _inputs(),
            (_case("base", (0.0, 0.0)), _case("stress", (-0.5, -0.5))),
            (_strategies()[0],),
            debtLimit=1_000.0,
            maxFinancing=200.0,
            maxInvestment=200.0,
        )


def testOneCompanyScenarioLoopHashBindsAssumptionAndStrategyContent() -> None:
    first = compareOneCompanyTwoScenarioStrategies(
        "005930",
        _inputs(),
        (_case("base", (0.0, 0.0)), _case("stress", (-0.5, -0.5))),
        _strategies(),
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )
    changedAssumption = compareOneCompanyTwoScenarioStrategies(
        "005930",
        _inputs(),
        (_case("base", (0.0, 0.0)), _case("stress", (-0.4, -0.4))),
        _strategies(),
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )
    changedStrategy = compareOneCompanyTwoScenarioStrategies(
        "005930",
        _inputs(),
        (_case("base", (0.0, 0.0)), _case("stress", (-0.5, -0.5))),
        _strategies(investment=30.0),
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )
    assert first.loopHash != changedAssumption.loopHash
    assert first.loopHash != changedStrategy.loopHash


def testOneCompanyScenarioLoopRejectsDuplicateStrategyIds() -> None:
    hold, _ = _strategies()
    duplicate = buildOperatingStrategy(
        "hold",
        priceChange=(0.0, 0.0),
        capacityInvestment=(10.0, 0.0),
        borrow=(0.0, 0.0),
        repay=(0.0, 0.0),
        refs=("strategy://hold-duplicate",),
    )
    with pytest.raises(ScenarioCompositionError, match="strategy ids"):
        compareOneCompanyTwoScenarioStrategies(
            "005930",
            _inputs(),
            (_case("base", (0.0, 0.0)), _case("stress", (-0.5, -0.5))),
            (hold, duplicate),
            debtLimit=1_000.0,
            maxFinancing=200.0,
            maxInvestment=200.0,
        )
