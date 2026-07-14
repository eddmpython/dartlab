from __future__ import annotations

from dataclasses import replace
from hashlib import sha256

import polars as pl
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from dartlab.simulate.admissionRegistry import (
    AdmissionVerifier,
    TrustedIssuer,
    initializeAdmissionRegistry,
    issueAdmissionReceipt,
    putAdmissionArtifact,
)
from dartlab.simulate.driverCalibration import (
    DRIVER_COEFFICIENT_RULE_HASH,
    DRIVER_COEFFICIENT_RULE_ID,
    DRIVER_COEFFICIENT_RULE_VERSION,
    MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_HASH,
    MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_ID,
    MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_VERSION,
    DriverCalibrationError,
    DriverCalibrationTarget,
    DriverCoefficientCalibrationSpec,
    DriverCoefficientOosSpec,
    MultivariableDriverCoefficientCalibrationSpec,
    MultivariableDriverCoefficientOosSpec,
    calibrationReceiptToOperatingExposure,
    driverCoefficientAdmissionArtifact,
    driverCoefficientAdmissionParentReceiptIds,
    driverCoefficientAdmissionSubjectHash,
    evaluateDriverCoefficientOos,
    evaluateDriverCoefficientOosFromObservationFrame,
    evaluateMultivariableDriverCoefficientOosFromObservationFrame,
    fitDriverCoefficientPit,
    fitDriverCoefficientPitFromObservationFrame,
    fitMultivariableDriverCoefficientPitFromObservationFrame,
    multivariableCalibrationReceiptToOperatingExposures,
    multivariableDriverCoefficientAdmissionArtifact,
    multivariableDriverCoefficientAdmissionParentReceiptIds,
    multivariableDriverCoefficientAdmissionSubjectHash,
    validateDriverCoefficientAdmission,
    validateMultivariableDriverCoefficientAdmission,
)
from dartlab.simulate.driverObservationBatches import (
    DriverObservationLaneSpec,
    DriverObservationSignalSpec,
    buildDriverObservationBatchFromPanel,
    driverHistorySourceFromProviderObservationBatch,
)
from dartlab.simulate.driverObservationFrames import (
    DriverCoefficientObservationFrameSpec,
    DriverDesignColumnSpec,
    DriverObservationFrameError,
    MultivariableDriverCoefficientObservationFrameSpec,
    buildDriverCoefficientObservationFrame,
    buildMultivariableDriverCoefficientObservationFrame,
)
from dartlab.simulate.driverPaths import (
    DriverAssumptionSource,
    DriverCard,
    DriverFactorSpec,
    DriverHistorySource,
    buildDriverPathSet,
)
from dartlab.simulate.driverRegistry import DriverRegistryCandidate, compileDriverRegistryPathSet
from dartlab.simulate.operatingBridge import OperatingShockBaseline, OperatingTransmissionExposure
from dartlab.simulate.operatingWorld import (
    OperatingPrimitive,
    _buildOperatingWorld,
    _initialStateFromInputs,
    buildOperatingStrategy,
    operatingInputsFromCompiledState,
    operatingInputsFromPrimitives,
)
from dartlab.simulate.scenarioComposition import (
    OperatingScenarioCase,
    ScenarioCompositionError,
    buildScenarioCoefficientBindingFromVerifiedMultivariableAdmission,
    compareOneCompanyTwoScenarioStrategies,
    scenarioCoefficientBindingHash,
    scenarioCoefficientExposureContractHash,
)
from dartlab.simulate.stateCompiler import (
    StateCompileSpec,
    buildProviderObservationBatch,
    compilePointInTimeState,
    issuePointInTimeState,
    issueProviderObservationBatch,
    makeVariableObservation,
)
from dartlab.simulate.stateSupport import INITIAL_STATE_RULE_HASH, INITIAL_STATE_RULE_ID, INITIAL_STATE_RULE_VERSION
from dartlab.simulate.stateVariables import StateVariableSpec, buildStateVariableRegistry
from dartlab.simulate.vintage import VintageRef
from dartlab.simulate.world import (
    SimulationSpecError,
    initialStateAdmissionArtifact,
    initialStateAdmissionSubjectHash,
)


def _trust(tmp_path):
    database = tmp_path / "admission.sqlite"
    artifacts = tmp_path / "artifacts"
    initializeAdmissionRegistry(database)
    private = Ed25519PrivateKey.generate()
    privateBytes = private.private_bytes_raw()
    trusted = {
        "provider-key": TrustedIssuer(
            issuerId="provider-issuer",
            issuerKeyId="provider-key",
            publicKey=private.public_key().public_bytes_raw(),
        )
    }
    verifier = AdmissionVerifier(database, artifacts, trusted)
    return database, artifacts, privateBytes, trusted, verifier


def _sourceReceipt(context, content: bytes, *, knowledgeAsOf: str, issuedAt: str):
    database, artifacts, privateBytes, trusted, _verifier = context
    artifactHash = putAdmissionArtifact(artifacts, content)
    return issueAdmissionReceipt(
        database,
        artifacts,
        privateKey=privateBytes,
        kind="dataVintage",
        subjectHash=artifactHash,
        artifactHash=artifactHash,
        parentReceiptIds=(),
        ruleId="provider-source-v1",
        ruleVersion="1",
        ruleHash=sha256(b"provider-source-v1").hexdigest(),
        issuerId="provider-issuer",
        issuerKeyId="provider-key",
        issuerExecutableHash=sha256(b"provider-source-issuer-v1").hexdigest(),
        knowledgeAsOf=knowledgeAsOf,
        revisionPolicy="asKnown",
        coverage="asOfExact",
        frequency="quarter",
        stepSpan=1,
        maxAdmittedStep=0,
        status="verifiedVintage",
        issuedAt=issuedAt,
        trustedIssuers=trusted,
    )


def _operatingStateSpecs() -> tuple[StateVariableSpec, ...]:
    values = (
        ("price", "currencyPerUnit", 10.0),
        ("demandVolume", "units", 100.0),
        ("unitCost", "currencyPerUnit", 6.0),
        ("fixedCost", "currency", 100.0),
        ("capacityUnits", "units", 150.0),
        ("cash", "currency", 500.0),
        ("debt", "currency", 20.0),
    )
    return tuple(
        StateVariableSpec(
            variableId=variableId,
            signalId=variableId,
            providerId="edgar",
            datasetId="operating-state-fixture",
            unit=unit,
            role="state",
            evidenceRole="observed",
            frequency="quarter",
            timing="stock",
            transformId="level-v1",
            maxStalenessDays=400,
            lower=0.0,
        )
        for variableId, unit, _value in values
    )


def _admittedOperatingInputs(context):
    database, artifacts, privateBytes, trusted, verifier = context
    decisionAsOf = "20220131"
    availableAt = "20220115"
    eventAt = "20211231"
    observations = []
    for spec in _operatingStateSpecs():
        value = {
            "price": 10.0,
            "demandVolume": 100.0,
            "unitCost": 6.0,
            "fixedCost": 100.0,
            "capacityUnits": 150.0,
            "cash": 500.0,
            "debt": 20.0,
        }[spec.variableId]
        sourceReceipt = _sourceReceipt(
            context,
            f"operating-state:{spec.variableId}:{value}".encode(),
            knowledgeAsOf=availableAt,
            issuedAt=f"{availableAt}T000000Z",
        )
        vintage = VintageRef(
            artifactKind="providerObservation",
            provider="edgar",
            artifactId=f"operating-state:{spec.variableId}:original",
            artifactHash=sourceReceipt.artifactHash,
            payloadHash=sourceReceipt.artifactHash,
            knowledgeAsOf=availableAt,
            availableAt=availableAt,
            revisionPolicy="asKnown",
            coverage="asOfExact",
            fiscalThrough=eventAt,
            receiptId=sourceReceipt.receiptId,
        )
        observations.append(
            makeVariableObservation(
                providerId="edgar",
                datasetId="operating-state-fixture",
                entityId="005930",
                signalId=spec.signalId,
                value=value,
                unit=spec.unit,
                frequency=spec.frequency,
                timing=spec.timing,
                transformId=spec.transformId,
                evidenceRole=spec.evidenceRole,
                eventAt=eventAt,
                availableAt=availableAt,
                knowledgeAsOf=availableAt,
                availabilityPrecision="date",
                revisionId="original",
                vintage=vintage,
                normalizationRuleHash=sha256(b"operating-state-fixture-v1").hexdigest(),
            )
        )
    batch = issueProviderObservationBatch(
        buildProviderObservationBatch(
            tuple(observations),
            providerId="edgar",
            datasetId="operating-state-fixture",
            entityId="005930",
            signalIds=tuple(spec.signalId for spec in _operatingStateSpecs()),
            cutoffAsOf=decisionAsOf,
        ),
        database,
        artifacts,
        privateKey=privateBytes,
        issuerId="provider-issuer",
        issuerKeyId="provider-key",
        issuedAt=f"{decisionAsOf}T000000Z",
        trustedIssuers=trusted,
    )
    compiled = compilePointInTimeState(
        buildStateVariableRegistry(_operatingStateSpecs()),
        (batch,),
        StateCompileSpec(
            entityId="005930",
            market="KR",
            decisionAsOf=decisionAsOf,
            consumerId="one-company-scenario-loop",
            consumerVersion="1",
            variableIds=tuple(spec.variableId for spec in _operatingStateSpecs()),
            requireExact=True,
        ),
        admissionVerifier=verifier,
    )
    compiled = issuePointInTimeState(
        compiled,
        database,
        artifacts,
        privateKey=privateBytes,
        issuerId="provider-issuer",
        issuerKeyId="provider-key",
        issuedAt=f"{decisionAsOf}T000000Z",
        trustedIssuers=trusted,
    )
    inputs = operatingInputsFromCompiledState(
        compiled,
        priceElasticity=1.0,
        capacityUnitsPerCurrency=1.0,
        taxRate=0.0,
    )
    model = _buildOperatingWorld(inputs, maxFinancing=200.0, maxInvestment=200.0)
    initial = _initialStateFromInputs(inputs)
    initialArtifact = initialStateAdmissionArtifact(model, initial)
    initialSubjectHash = initialStateAdmissionSubjectHash(model, initial)
    initialArtifactHash = putAdmissionArtifact(artifacts, initialArtifact)
    assert initialArtifactHash == initialSubjectHash
    initialReceipt = issueAdmissionReceipt(
        database,
        artifacts,
        privateKey=privateBytes,
        kind="initialState",
        subjectHash=initialSubjectHash,
        artifactHash=initialArtifactHash,
        parentReceiptIds=(compiled.stateReceiptId,),
        ruleId=INITIAL_STATE_RULE_ID,
        ruleVersion=INITIAL_STATE_RULE_VERSION,
        ruleHash=INITIAL_STATE_RULE_HASH,
        issuerId="provider-issuer",
        issuerKeyId="provider-key",
        issuerExecutableHash=sha256(b"operating-initial-state-issuer-v1").hexdigest(),
        knowledgeAsOf=compiled.knowledgeAsOf,
        revisionPolicy="asKnown",
        coverage="asOfExact",
        frequency=inputs.stepFrequency,
        stepSpan=inputs.stepSpan,
        maxAdmittedStep=0,
        status="admitted",
        issuedAt=f"{decisionAsOf}T000000Z",
        trustedIssuers=trusted,
    )
    return replace(inputs, initialStateAdmissionReceiptId=initialReceipt.receiptId)


def _observation(
    context,
    *,
    signalId: str,
    value: float,
    unit: str,
    eventAt: str,
    availableAt: str,
    knowledgeAsOf: str,
    evidenceRole: str = "observed",
    revisionId: str = "original",
    timing: str = "ratio",
    transformId: str = "change-v1",
):
    receipt = _sourceReceipt(
        context,
        f"{signalId}:{eventAt}:{value}:{revisionId}".encode(),
        knowledgeAsOf=knowledgeAsOf,
        issuedAt=f"{knowledgeAsOf}T000000Z",
    )
    vintage = VintageRef(
        artifactKind="providerObservation",
        provider="macro",
        artifactId=f"{signalId}:{eventAt}:{revisionId}",
        artifactHash=receipt.artifactHash,
        payloadHash=receipt.artifactHash,
        knowledgeAsOf=knowledgeAsOf,
        availableAt=availableAt,
        revisionPolicy="asKnown",
        coverage="asOfExact",
        eventThrough=eventAt,
        receiptId=receipt.receiptId,
        sourceRefs=(f"raw:{signalId}:{eventAt}",),
    )
    return makeVariableObservation(
        providerId="macro",
        datasetId="driver-observation-fixture",
        entityId="KR",
        signalId=signalId,
        value=value,
        unit=unit,
        frequency="quarter",
        timing=timing,
        transformId=transformId,
        evidenceRole=evidenceRole,
        eventAt=eventAt,
        availableAt=availableAt,
        knowledgeAsOf=knowledgeAsOf,
        availabilityPrecision="date",
        revisionId=revisionId,
        vintage=vintage,
        normalizationRuleHash=sha256(b"driver-observation-fixture-v1").hexdigest(),
    )


def _signedBatch(context, observations, *, signalId: str, cutoffAsOf: str):
    database, artifacts, privateBytes, trusted, _verifier = context
    unsigned = buildProviderObservationBatch(
        tuple(observations),
        providerId="macro",
        datasetId="driver-observation-fixture",
        entityId="KR",
        signalIds=(signalId,),
        cutoffAsOf=cutoffAsOf,
    )
    return issueProviderObservationBatch(
        unsigned,
        database,
        artifacts,
        privateKey=privateBytes,
        issuerId="provider-issuer",
        issuerKeyId="provider-key",
        issuedAt=f"{cutoffAsOf}T000000Z",
        trustedIssuers=trusted,
    )


def _signedDriverLaneBatch(context, *, signalId: str, values, events, knowledgeDates, cutoffAsOf: str):
    rows = []
    sourceReceipts = {}
    for index, (value, eventAt, knowledgeAsOf) in enumerate(zip(values, events, knowledgeDates)):
        revisionId = f"{signalId}-r{index}"
        receipt = _sourceReceipt(
            context,
            f"{signalId}:{eventAt}:{knowledgeAsOf}:{value}:{revisionId}".encode(),
            knowledgeAsOf=knowledgeAsOf,
            issuedAt=f"{knowledgeAsOf}T000000Z",
        )
        rows.append(
            {
                "eventTime": eventAt,
                "availableAt": knowledgeAsOf,
                "knowledgeAsOf": knowledgeAsOf,
                "revisionId": revisionId,
                "sourceArtifactHash": receipt.artifactHash,
                signalId: value,
            }
        )
        sourceReceipts[revisionId] = receipt
    laneHash = sha256(f"driver-lane:{signalId}:{cutoffAsOf}".encode()).hexdigest()
    batch = buildDriverObservationBatchFromPanel(
        pl.DataFrame(rows),
        DriverObservationLaneSpec(
            providerId="macro",
            datasetId="driver-observation-lane-fixture",
            entityId="KR",
            knowledgeAsOf=cutoffAsOf,
            eventTimeColumn="eventTime",
            availableAtColumn="availableAt",
            revisionIdColumn="revisionId",
            sourceArtifactKind="driverLaneFixture",
            sourceArtifactId=f"fixture:{signalId}",
            sourceArtifactHash=laneHash,
            signalSpecs=(
                DriverObservationSignalSpec(
                    signalId=signalId,
                    sourceColumn=signalId,
                    unit="simpleReturn",
                    frequency="quarter",
                    timing="ratio",
                    transformId="change-v1",
                    evidenceRole="observed",
                ),
            ),
            sourceRefs=(f"source:driver-lane-fixture:{signalId}",),
            knowledgeAsOfColumn="knowledgeAsOf",
            sourceArtifactHashColumn="sourceArtifactHash",
        ),
        sourceReceipts=sourceReceipts,
        requireExact=True,
    )
    database, artifacts, privateBytes, trusted, _verifier = context
    return issueProviderObservationBatch(
        batch,
        database,
        artifacts,
        privateKey=privateBytes,
        issuerId="provider-issuer",
        issuerKeyId="provider-key",
        issuedAt=f"{cutoffAsOf}T000000Z",
        trustedIssuers=trusted,
    )


def _sourceObservations(context, *, values, events, knowledgeDates):
    return tuple(
        _observation(
            context,
            signalId="fxChange",
            value=value,
            unit="simpleReturn",
            eventAt=eventAt,
            availableAt=availableAt,
            knowledgeAsOf=knowledgeAsOf,
        )
        for value, eventAt, availableAt, knowledgeAsOf in zip(values, events, knowledgeDates, knowledgeDates)
    )


def _sourceObservationsFor(
    context,
    *,
    signalId: str,
    values,
    events,
    knowledgeDates,
    evidenceRole: str = "observed",
    timing: str = "ratio",
    transformId: str = "change-v1",
):
    return tuple(
        _observation(
            context,
            signalId=signalId,
            value=value,
            unit="simpleReturn",
            eventAt=eventAt,
            availableAt=availableAt,
            knowledgeAsOf=knowledgeAsOf,
            evidenceRole=evidenceRole,
            timing=timing,
            transformId=transformId,
        )
        for value, eventAt, availableAt, knowledgeAsOf in zip(values, events, knowledgeDates, knowledgeDates)
    )


def _labelObservations(context, *, values, events, availableDates, knowledgeDates, evidenceRole: str = "observed"):
    return tuple(
        _observation(
            context,
            signalId="realizedMarketPriceChange",
            value=value,
            unit="ratioChangePerStep",
            eventAt=eventAt,
            availableAt=availableAt,
            knowledgeAsOf=knowledgeAsOf,
            evidenceRole=evidenceRole,
        )
        for value, eventAt, availableAt, knowledgeAsOf in zip(values, events, availableDates, knowledgeDates)
    )


def _fitBatches(context):
    source = _sourceObservations(
        context,
        values=(0.10, -0.20, 0.30, 0.40),
        events=("20200331", "20200630", "20200930", "20201231"),
        knowledgeDates=("20200410", "20200710", "20201010", "20210110"),
    )
    labels = _labelObservations(
        context,
        values=(0.05, -0.10, 0.15, 0.20),
        events=("20200630", "20200930", "20201231", "20210331"),
        availableDates=("20200705", "20201005", "20210105", "20210405"),
        knowledgeDates=("20200710", "20201010", "20210110", "20210410"),
    )
    return (
        _signedBatch(context, source, signalId="fxChange", cutoffAsOf="20210430"),
        _signedBatch(context, labels, signalId="realizedMarketPriceChange", cutoffAsOf="20210430"),
    )


def _oosBatches(context):
    source = _sourceObservations(
        context,
        values=(0.20, -0.10, 0.30),
        events=("20210331", "20210630", "20210930"),
        knowledgeDates=("20210410", "20210710", "20211010"),
    )
    labels = _labelObservations(
        context,
        values=(0.10, -0.05, 0.15),
        events=("20210630", "20210930", "20211231"),
        availableDates=("20210705", "20211005", "20220105"),
        knowledgeDates=("20210710", "20211010", "20220110"),
    )
    return (
        _signedBatch(context, source, signalId="fxChange", cutoffAsOf="20220131"),
        _signedBatch(context, labels, signalId="realizedMarketPriceChange", cutoffAsOf="20220131"),
    )


def _frameSpec(frameId: str = "fx-price-frame") -> DriverCoefficientObservationFrameSpec:
    return DriverCoefficientObservationFrameSpec(
        frameId=frameId,
        sourceSignalId="fxChange",
        labelSignalId="realizedMarketPriceChange",
        sourceVariableId="fxChange",
        targetVariableId="realizedMarketPriceChange",
        sourceUnit="simpleReturn",
        targetUnit="ratioChangePerStep",
        frequency="quarter",
        stepSpan=1,
        horizonSteps=1,
    )


def _designSpec(frameId: str = "macro-price-design") -> MultivariableDriverCoefficientObservationFrameSpec:
    return MultivariableDriverCoefficientObservationFrameSpec(
        frameId=frameId,
        sourceColumns=(
            DriverDesignColumnSpec(
                variableId="fxChange",
                signalId="fxChange",
                unit="simpleReturn",
                frequency="quarter",
                transformId="change-v1",
            ),
            DriverDesignColumnSpec(
                variableId="oilChange",
                signalId="oilChange",
                unit="simpleReturn",
                frequency="quarter",
                transformId="change-v1",
            ),
        ),
        labelSignalId="realizedMarketPriceChange",
        targetVariableId="realizedMarketPriceChange",
        targetUnit="ratioChangePerStep",
        frequency="quarter",
        stepSpan=1,
        horizonSteps=1,
    )


def _registryResult(sourceBatch=None):
    factor = DriverFactorSpec(
        "fxChange",
        "simpleReturn",
        "quarter",
        "change",
        "change-v1",
    )
    if sourceBatch is None:
        card = DriverCard(
            cardId="macro-fx-change",
            sourceKind="history",
            providerId="macro",
            datasetId="driver-observation-fixture",
            entityId="KR",
            frequency="quarter",
            stepSpan=1,
            factors=(factor,),
            historyStatus="asKnown",
            sourceRefs=("providerObservationBatch:fit-source",),
        )
        source = DriverHistorySource(
            card,
            pl.DataFrame(
                {
                    "eventTime": ["20200331", "20200630", "20200930", "20201231"],
                    "availableAt": ["20200410", "20200710", "20201010", "20210110"],
                    "fxChange": [0.10, -0.20, 0.30, 0.40],
                }
            ),
        )
    else:
        source = driverHistorySourceFromProviderObservationBatch(
            sourceBatch,
            cardId="macro-fx-change",
            factors=(factor,),
            stepSpan=1,
            sourceRefs=("semantics:provider-observation-projection",),
        )
    return compileDriverRegistryPathSet(
        (
            DriverRegistryCandidate(
                "macro-fx",
                "pathHistory",
                source,
                semanticRefs=("semantics:macro-fx-change-path",),
                selectionReason="FX quarterly change is an observable macro path.",
            ),
        ),
        registryId="macro-driver-registry",
        knowledgeAsOf="20210131",
        horizon=2,
        pathCount=2,
        blockLength=1,
        seed=7,
        minObservations=4,
    )


def _multiRegistryResult(fxBatch=None, oilBatch=None):
    fxFactor = DriverFactorSpec("fxChange", "simpleReturn", "quarter", "change", "change-v1")
    oilFactor = DriverFactorSpec("oilChange", "simpleReturn", "quarter", "change", "change-v1")
    if fxBatch is None:
        fxSource = DriverHistorySource(
            DriverCard(
                cardId="macro-fx-change",
                sourceKind="history",
                providerId="macro",
                datasetId="driver-observation-fixture",
                entityId="KR",
                frequency="quarter",
                stepSpan=1,
                factors=(fxFactor,),
                historyStatus="asKnown",
                sourceRefs=("providerObservationBatch:fit-fx-source",),
            ),
            pl.DataFrame(
                {
                    "eventTime": ["20200331", "20200630", "20200930", "20201231"],
                    "availableAt": ["20200410", "20200710", "20201010", "20210110"],
                    "fxChange": [0.10, -0.20, 0.30, 0.40],
                }
            ),
        )
    else:
        fxSource = driverHistorySourceFromProviderObservationBatch(
            fxBatch,
            cardId="macro-fx-change",
            factors=(fxFactor,),
            stepSpan=1,
            sourceRefs=("semantics:provider-observation-projection",),
        )
    if oilBatch is None:
        oilSource = DriverHistorySource(
            DriverCard(
                cardId="macro-oil-change",
                sourceKind="history",
                providerId="macro",
                datasetId="driver-observation-fixture",
                entityId="KR",
                frequency="quarter",
                stepSpan=1,
                factors=(oilFactor,),
                historyStatus="asKnown",
                sourceRefs=("providerObservationBatch:fit-oil-source",),
            ),
            pl.DataFrame(
                {
                    "eventTime": ["20200331", "20200630", "20200930", "20201231"],
                    "availableAt": ["20200410", "20200710", "20201010", "20210110"],
                    "oilChange": [0.05, 0.10, -0.05, 0.20],
                }
            ),
        )
    else:
        oilSource = driverHistorySourceFromProviderObservationBatch(
            oilBatch,
            cardId="macro-oil-change",
            factors=(oilFactor,),
            stepSpan=1,
            sourceRefs=("semantics:provider-observation-projection",),
        )
    return compileDriverRegistryPathSet(
        (
            DriverRegistryCandidate(
                "macro-fx",
                "pathHistory",
                fxSource,
                semanticRefs=("semantics:macro-fx-change-path",),
                selectionReason="FX quarterly change is an observable macro path.",
            ),
            DriverRegistryCandidate(
                "macro-oil",
                "pathHistory",
                oilSource,
                semanticRefs=("semantics:macro-oil-change-path",),
                selectionReason="Oil quarterly change is an observable macro path.",
            ),
        ),
        registryId="macro-driver-registry",
        knowledgeAsOf="20210131",
        horizon=2,
        pathCount=2,
        blockLength=1,
        seed=7,
        minObservations=4,
    )


def _target(labelParentReceiptIds: tuple[str, ...]) -> DriverCalibrationTarget:
    return DriverCalibrationTarget(
        targetVariableId="realizedMarketPriceChange",
        targetShock="marketPriceChange",
        targetUnit="ratioChangePerStep",
        targetEvidenceKind="observedOutcome",
        labelProviderId="macro",
        labelDatasetId="driver-observation-fixture",
        labelSourceRefs=("providerObservationBatch:fit-label",),
        historyStatus="asKnown",
        labelParentReceiptIds=labelParentReceiptIds,
        semanticRefs=("semantics:observed-forward-equity-return",),
    )


def _fitSpec(sourceParentReceiptIds: tuple[str, ...]) -> DriverCoefficientCalibrationSpec:
    return DriverCoefficientCalibrationSpec(
        calibrationId="fx-to-price-fit",
        sourceVariableId="fxChange",
        minOrigins=4,
        sourceParentReceiptIds=sourceParentReceiptIds,
    )


def _oosSpec(
    sourceParentReceiptIds: tuple[str, ...],
    labelParentReceiptIds: tuple[str, ...],
) -> DriverCoefficientOosSpec:
    return DriverCoefficientOosSpec(
        evaluationId="fx-to-price-oos",
        minOosOrigins=3,
        minSkillVsBaseline=0.1,
        maxRmse=0.01,
        maxAbsBias=0.01,
        baselineValue=0.0,
        frequency="quarter",
        stepSpan=1,
        maxAdmittedStep=1,
        sourceParentReceiptIds=sourceParentReceiptIds,
        labelParentReceiptIds=labelParentReceiptIds,
    )


def _multiFitBatches(context):
    events = ("20200331", "20200630", "20200930", "20201231")
    knowledgeDates = ("20200410", "20200710", "20201010", "20210110")
    fxValues = (0.10, -0.20, 0.30, 0.40)
    oilValues = (0.05, 0.10, -0.05, 0.20)
    labels = tuple(0.5 * fx + 0.25 * oil for fx, oil in zip(fxValues, oilValues))
    return (
        _signedBatch(
            context,
            _sourceObservationsFor(
                context,
                signalId="fxChange",
                values=fxValues,
                events=events,
                knowledgeDates=knowledgeDates,
            ),
            signalId="fxChange",
            cutoffAsOf="20210430",
        ),
        _signedBatch(
            context,
            _sourceObservationsFor(
                context,
                signalId="oilChange",
                values=oilValues,
                events=events,
                knowledgeDates=knowledgeDates,
            ),
            signalId="oilChange",
            cutoffAsOf="20210430",
        ),
        _signedBatch(
            context,
            _labelObservations(
                context,
                values=labels,
                events=("20200630", "20200930", "20201231", "20210331"),
                availableDates=("20200705", "20201005", "20210105", "20210405"),
                knowledgeDates=("20200710", "20201010", "20210110", "20210410"),
            ),
            signalId="realizedMarketPriceChange",
            cutoffAsOf="20210430",
        ),
    )


def _multiFitLaneBatches(context):
    events = ("20200331", "20200630", "20200930", "20201231")
    knowledgeDates = ("20200410", "20200710", "20201010", "20210110")
    fxValues = (0.10, -0.20, 0.30, 0.40)
    oilValues = (0.05, 0.10, -0.05, 0.20)
    labels = tuple(0.5 * fx + 0.25 * oil for fx, oil in zip(fxValues, oilValues))
    return (
        _signedDriverLaneBatch(
            context,
            signalId="fxChange",
            values=fxValues,
            events=events,
            knowledgeDates=knowledgeDates,
            cutoffAsOf="20210430",
        ),
        _signedDriverLaneBatch(
            context,
            signalId="oilChange",
            values=oilValues,
            events=events,
            knowledgeDates=knowledgeDates,
            cutoffAsOf="20210430",
        ),
        _signedBatch(
            context,
            _labelObservations(
                context,
                values=labels,
                events=("20200630", "20200930", "20201231", "20210331"),
                availableDates=("20200705", "20201005", "20210105", "20210405"),
                knowledgeDates=("20200710", "20201010", "20210110", "20210410"),
            ),
            signalId="realizedMarketPriceChange",
            cutoffAsOf="20210430",
        ),
    )


def _multiOosBatches(context):
    events = ("20210331", "20210630", "20210930")
    knowledgeDates = ("20210410", "20210710", "20211010")
    fxValues = (0.20, -0.10, 0.30)
    oilValues = (0.10, 0.20, -0.10)
    labels = tuple(0.5 * fx + 0.25 * oil for fx, oil in zip(fxValues, oilValues))
    return (
        _signedBatch(
            context,
            _sourceObservationsFor(
                context,
                signalId="fxChange",
                values=fxValues,
                events=events,
                knowledgeDates=knowledgeDates,
            ),
            signalId="fxChange",
            cutoffAsOf="20220131",
        ),
        _signedBatch(
            context,
            _sourceObservationsFor(
                context,
                signalId="oilChange",
                values=oilValues,
                events=events,
                knowledgeDates=knowledgeDates,
            ),
            signalId="oilChange",
            cutoffAsOf="20220131",
        ),
        _signedBatch(
            context,
            _labelObservations(
                context,
                values=labels,
                events=("20210630", "20210930", "20211231"),
                availableDates=("20210705", "20211005", "20220105"),
                knowledgeDates=("20210710", "20211010", "20220110"),
            ),
            signalId="realizedMarketPriceChange",
            cutoffAsOf="20220131",
        ),
    )


def _multiFitSpec(sourceParentReceiptIds: tuple[str, ...]) -> MultivariableDriverCoefficientCalibrationSpec:
    return MultivariableDriverCoefficientCalibrationSpec(
        calibrationId="macro-vector-to-price-fit",
        sourceVariableIds=("fxChange", "oilChange"),
        minOrigins=4,
        sourceParentReceiptIds=sourceParentReceiptIds,
    )


def _multiOosSpec(
    sourceParentReceiptIds: tuple[str, ...],
    labelParentReceiptIds: tuple[str, ...],
) -> MultivariableDriverCoefficientOosSpec:
    return MultivariableDriverCoefficientOosSpec(
        evaluationId="macro-vector-to-price-oos",
        minOosOrigins=3,
        minSkillVsBaseline=0.1,
        maxRmse=0.001,
        maxAbsBias=0.001,
        baselineValue=0.0,
        frequency="quarter",
        stepSpan=1,
        maxAdmittedStep=1,
        sourceParentReceiptIds=sourceParentReceiptIds,
        labelParentReceiptIds=labelParentReceiptIds,
    )


def _issueCoefficientAdmission(context, report):
    database, artifacts, privateBytes, trusted, _verifier = context
    subject = driverCoefficientAdmissionSubjectHash(report)
    artifactHash = putAdmissionArtifact(artifacts, driverCoefficientAdmissionArtifact(report))
    assert artifactHash == subject
    return issueAdmissionReceipt(
        database,
        artifacts,
        privateKey=privateBytes,
        kind="driverCoefficient",
        subjectHash=subject,
        artifactHash=artifactHash,
        parentReceiptIds=driverCoefficientAdmissionParentReceiptIds(report),
        ruleId=DRIVER_COEFFICIENT_RULE_ID,
        ruleVersion=DRIVER_COEFFICIENT_RULE_VERSION,
        ruleHash=DRIVER_COEFFICIENT_RULE_HASH,
        issuerId="provider-issuer",
        issuerKeyId="provider-key",
        issuerExecutableHash="b" * 64,
        knowledgeAsOf=report.evaluationKnowledgeAsOf,
        revisionPolicy="asKnown",
        coverage="asOfExact",
        frequency=report.frequency,
        stepSpan=report.stepSpan,
        maxAdmittedStep=report.maxAdmittedStep,
        status="admitted",
        issuedAt="20220201T000000Z",
        trustedIssuers=trusted,
    )


def _issueMultivariableCoefficientAdmission(context, report):
    database, artifacts, privateBytes, trusted, _verifier = context
    subject = multivariableDriverCoefficientAdmissionSubjectHash(report)
    artifactHash = putAdmissionArtifact(artifacts, multivariableDriverCoefficientAdmissionArtifact(report))
    assert artifactHash == subject
    return issueAdmissionReceipt(
        database,
        artifacts,
        privateKey=privateBytes,
        kind="driverCoefficient",
        subjectHash=subject,
        artifactHash=artifactHash,
        parentReceiptIds=multivariableDriverCoefficientAdmissionParentReceiptIds(report),
        ruleId=MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_ID,
        ruleVersion=MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_VERSION,
        ruleHash=MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_HASH,
        issuerId="provider-issuer",
        issuerKeyId="provider-key",
        issuerExecutableHash="c" * 64,
        knowledgeAsOf=report.evaluationKnowledgeAsOf,
        revisionPolicy="asKnown",
        coverage="asOfExact",
        frequency=report.frequency,
        stepSpan=report.stepSpan,
        maxAdmittedStep=report.maxAdmittedStep,
        status="admitted",
        issuedAt="20220201T000000Z",
        trustedIssuers=trusted,
    )


def _fitAndReport(context, fitFrame, oosFrame, registryResult=None):
    receipt = fitDriverCoefficientPitFromObservationFrame(
        registryResult or _registryResult(),
        _target(fitFrame.labelParentReceiptIds),
        fitFrame,
        _fitSpec(fitFrame.sourceParentReceiptIds),
        calibrationKnowledgeAsOf="20210430",
    )
    report = evaluateDriverCoefficientOosFromObservationFrame(
        receipt,
        oosFrame,
        _oosSpec(oosFrame.sourceParentReceiptIds, oosFrame.labelParentReceiptIds),
        evaluationKnowledgeAsOf="20220131",
    )
    signed = _issueCoefficientAdmission(context, report)
    return receipt, report, signed


def _multivariableAdmissionBundle(context, *, fitBatches=None, oosBatches=None):
    fitFx, fitOil, fitLabel = fitBatches or _multiFitBatches(context)
    oosFx, oosOil, oosLabel = oosBatches or _multiOosBatches(context)
    fitFrame = buildMultivariableDriverCoefficientObservationFrame(
        (fitFx, fitOil),
        fitLabel,
        _designSpec("macro-vector-fit"),
    )
    oosFrame = buildMultivariableDriverCoefficientObservationFrame(
        (oosFx, oosOil),
        oosLabel,
        _designSpec("macro-vector-oos"),
    )
    receipt = fitMultivariableDriverCoefficientPitFromObservationFrame(
        _multiRegistryResult(fitFx, fitOil),
        _target(fitFrame.labelParentReceiptIds),
        fitFrame,
        _multiFitSpec(fitFrame.sourceParentReceiptIds),
        calibrationKnowledgeAsOf="20210430",
    )
    report = evaluateMultivariableDriverCoefficientOosFromObservationFrame(
        receipt,
        oosFrame,
        _multiOosSpec(oosFrame.sourceParentReceiptIds, oosFrame.labelParentReceiptIds),
        evaluationKnowledgeAsOf="20220131",
    )
    signed = _issueMultivariableCoefficientAdmission(context, report)
    verified = validateMultivariableDriverCoefficientAdmission(
        report,
        context[4],
        calibrationReceipt=receipt,
        receiptId=signed.receiptId,
        decisionAsOf="20220202",
    )
    exposures = multivariableCalibrationReceiptToOperatingExposures(
        receipt,
        exposureIdPrefix="macro-price",
        oosReport=report,
        admissionReceipt=verified,
    )
    return fitFx, fitOil, fitFrame, oosFrame, receipt, report, signed, verified, exposures


def _operatingInputs():
    return operatingInputsFromPrimitives(
        (
            OperatingPrimitive("price", 10.0, "currencyPerUnit", "explicitAssumption", "assumption://price"),
            OperatingPrimitive("demandVolume", 100.0, "units", "explicitAssumption", "assumption://volume"),
            OperatingPrimitive("unitCost", 6.0, "currencyPerUnit", "explicitAssumption", "assumption://unit-cost"),
            OperatingPrimitive("fixedCost", 100.0, "currency", "explicitAssumption", "assumption://fixed-cost"),
            OperatingPrimitive("capacityUnits", 150.0, "units", "explicitAssumption", "assumption://capacity"),
            OperatingPrimitive("cash", 500.0, "currency", "observed", "filing://cash"),
            OperatingPrimitive("debt", 20.0, "currency", "observed", "filing://debt"),
        ),
        asOf="20220131",
        priceElasticity=1.0,
        capacityUnitsPerCurrency=1.0,
        taxRate=0.0,
    )


def _operatingBaselines():
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


def _scenarioCaseWithCoefficientBinding(caseId, shock, exposures, binding, verifier):
    factorSpecs = (
        DriverFactorSpec("fxChange", "simpleReturn", "quarter", "change", "change-v1"),
        DriverFactorSpec("oilChange", "simpleReturn", "quarter", "change", "change-v1"),
    )
    card = DriverCard(
        cardId=f"{caseId}-macro-vector",
        sourceKind="explicitAssumption",
        providerId="user",
        datasetId="manual-scenario",
        entityId="KR",
        frequency="quarter",
        stepSpan=1,
        factors=factorSpecs,
        historyStatus="explicitAssumption",
        sourceRefs=(f"assumption://{caseId}/macro-vector",),
        assumptionId=f"{caseId}-macro-vector",
        claim=f"{caseId} macro vector scenario.",
        falsifier="Macro vector does not move the target operating price shock.",
    )
    pathSet = buildDriverPathSet(
        (
            DriverAssumptionSource(
                card,
                ({"fxChange": shock[0], "oilChange": shock[1]},),
            ),
        ),
        knowledgeAsOf="20220131",
        horizon=1,
        pathCount=1,
        blockLength=1,
        seed=11,
    )
    return OperatingScenarioCase(
        caseId,
        caseId.title(),
        pathSet,
        exposures,
        _operatingBaselines(),
        refs=(f"scenario://{caseId}",),
        coefficientBindings=(binding,),
        admissionVerifier=verifier,
    )


def _scenarioCaseWithProviderHistoryAndAdjustment(caseId, shock, fitFx, fitOil, exposures, binding, verifier):
    fxFactor = DriverFactorSpec("fxChange", "simpleReturn", "quarter", "change", "change-v1")
    oilFactor = DriverFactorSpec("oilChange", "simpleReturn", "quarter", "change", "change-v1")
    adjustmentFactor = DriverFactorSpec(
        "explicitPriceAdjustment",
        "simpleReturn",
        "quarter",
        "change",
        "manual-price-adjustment-v1",
    )
    fxSource = driverHistorySourceFromProviderObservationBatch(
        fitFx,
        cardId=f"{caseId}-observed-fx",
        factors=(fxFactor,),
        stepSpan=1,
        sourceRefs=(f"semantics:{caseId}:observed-fx",),
    )
    oilSource = driverHistorySourceFromProviderObservationBatch(
        fitOil,
        cardId=f"{caseId}-observed-oil",
        factors=(oilFactor,),
        stepSpan=1,
        sourceRefs=(f"semantics:{caseId}:observed-oil",),
    )
    adjustmentCard = DriverCard(
        cardId=f"{caseId}-explicit-price-adjustment",
        sourceKind="explicitAssumption",
        providerId="user",
        datasetId="manual-scenario",
        entityId="KR",
        frequency="quarter",
        stepSpan=1,
        factors=(adjustmentFactor,),
        historyStatus="explicitAssumption",
        sourceRefs=(f"assumption://{caseId}/explicit-price-adjustment",),
        assumptionId=f"{caseId}-explicit-price-adjustment",
        claim=f"{caseId} explicit future price adjustment.",
        falsifier="The declared future price adjustment is not the scenario being tested.",
    )
    pathSet = buildDriverPathSet(
        (
            fxSource,
            oilSource,
            DriverAssumptionSource(
                adjustmentCard,
                ({"explicitPriceAdjustment": shock},),
            ),
        ),
        knowledgeAsOf="20220131",
        horizon=1,
        pathCount=2,
        blockLength=1,
        seed=13,
        minObservations=4,
    )
    adjustmentExposure = OperatingTransmissionExposure(
        f"{caseId}-explicit-price-adjustment",
        "explicitPriceAdjustment",
        "marketPriceChange",
        1.0,
        "ratioChangePerStep/simpleReturn",
        "explicitAssumption",
        f"assumption://{caseId}/explicit-price-adjustment/exposure",
    )
    return OperatingScenarioCase(
        caseId,
        caseId.title(),
        pathSet,
        (*exposures, adjustmentExposure),
        _operatingBaselines(),
        refs=(f"scenario://{caseId}",),
        coefficientBindings=(binding,),
        admissionVerifier=verifier,
    )


def _oneStepStrategies():
    return (
        buildOperatingStrategy(
            "hold",
            priceChange=(0.0,),
            capacityInvestment=(0.0,),
            borrow=(0.0,),
            repay=(0.0,),
            refs=("strategy://hold",),
            isBaseline=True,
        ),
        buildOperatingStrategy(
            "invest",
            priceChange=(0.0,),
            capacityInvestment=(25.0,),
            borrow=(0.0,),
            repay=(0.0,),
            refs=("strategy://invest",),
        ),
    )


def testProviderObservationBatchesBuildCoefficientFrameAndAdmission(tmp_path) -> None:
    context = _trust(tmp_path)
    fitSource, fitLabel = _fitBatches(context)
    oosSource, oosLabel = _oosBatches(context)
    fitFrame = buildDriverCoefficientObservationFrame(fitSource, fitLabel, _frameSpec("fit-frame"))
    oosFrame = buildDriverCoefficientObservationFrame(oosSource, oosLabel, _frameSpec("oos-frame"))

    assert fitFrame.rowCount == 4
    assert oosFrame.rowCount == 3
    assert fitFrame.sourceParentReceiptIds == (fitSource.batchReceiptId,)
    assert fitFrame.labelParentReceiptIds == (fitLabel.batchReceiptId,)
    assert fitFrame.frame.select("sourceRef").to_series().to_list()[0] == fitSource.observations[0].observationId

    registryResult = _registryResult(fitSource)
    assert f"providerObservationBatch:{fitSource.batchReceiptId}" in registryResult.audit.sourceRefs

    receipt, report, signed = _fitAndReport(context, fitFrame, oosFrame, registryResult)
    verified = validateDriverCoefficientAdmission(
        report,
        context[4],
        calibrationReceipt=receipt,
        receiptId=signed.receiptId,
        decisionAsOf="20220202",
    )
    assert report.status == "oosEligible"
    assert verified.sourceParentReceiptIds == (fitSource.batchReceiptId, oosSource.batchReceiptId)
    assert verified.labelParentReceiptIds == (fitLabel.batchReceiptId, oosLabel.batchReceiptId)
    exposure = calibrationReceiptToOperatingExposure(
        receipt,
        exposureId="fx-price-admitted",
        oosReport=report,
        admissionReceipt=verified,
    )
    assert exposure.evidenceKind == "measuredAssociation"
    assert exposure.sourceRef == f"driverCoefficientAdmission:{signed.receiptId}"
    assert exposure.sourceVariableId == receipt.sourceVariableId
    assert exposure.targetShock == receipt.targetShock
    assert exposure.coefficientUnit == "ratioChangePerStep/simpleReturn"
    assert exposure.sourceFrequency == receipt.sourceFrequency == "quarter"
    assert exposure.sourceTiming == receipt.sourceTiming == "change"
    assert exposure.sourceTransformId == receipt.sourceTransformId == "change-v1"
    assert exposure.sourceFactorContractHash == receipt.sourceFactorContractHash


def testMultivariableObservationFrameBuildsExactDesignFrame(tmp_path) -> None:
    context = _trust(tmp_path)
    events = ("20200331", "20200630", "20200930", "20201231")
    knowledgeDates = ("20200410", "20200710", "20201010", "20210110")
    fxBatch = _signedBatch(
        context,
        _sourceObservationsFor(
            context,
            signalId="fxChange",
            values=(0.10, -0.20, 0.30, 0.40),
            events=events,
            knowledgeDates=knowledgeDates,
        ),
        signalId="fxChange",
        cutoffAsOf="20210430",
    )
    oilBatch = _signedBatch(
        context,
        _sourceObservationsFor(
            context,
            signalId="oilChange",
            values=(0.05, 0.10, -0.05, 0.20),
            events=events,
            knowledgeDates=knowledgeDates,
        ),
        signalId="oilChange",
        cutoffAsOf="20210430",
    )
    labelBatch = _signedBatch(
        context,
        _labelObservations(
            context,
            values=(0.05, -0.10, 0.15, 0.20),
            events=("20200630", "20200930", "20201231", "20210331"),
            availableDates=("20200705", "20201005", "20210105", "20210405"),
            knowledgeDates=("20200710", "20201010", "20210110", "20210410"),
        ),
        signalId="realizedMarketPriceChange",
        cutoffAsOf="20210430",
    )
    frame = buildMultivariableDriverCoefficientObservationFrame(
        (fxBatch, oilBatch),
        labelBatch,
        _designSpec(),
    )
    assert frame.rowCount == 4
    assert frame.sourceParentReceiptIds == (fxBatch.batchReceiptId, oilBatch.batchReceiptId)
    assert frame.labelParentReceiptIds == (labelBatch.batchReceiptId,)
    assert frame.frame["sourceValue__fxChange"].to_list() == pytest.approx([0.10, -0.20, 0.30, 0.40])
    assert frame.frame["sourceValue__oilChange"].to_list() == pytest.approx([0.05, 0.10, -0.05, 0.20])
    assert frame.frame["sourceRef__fxChange"].to_list()[0] == fxBatch.observations[0].observationId
    assert frame.frame["sourceRef__oilChange"].to_list()[0] == oilBatch.observations[0].observationId
    assert frame.frame["originKnowledgeAsOf"].to_list()[0] == "20200410"
    reversedFrame = buildMultivariableDriverCoefficientObservationFrame(
        (oilBatch, fxBatch),
        labelBatch,
        MultivariableDriverCoefficientObservationFrameSpec(
            **{
                **{
                    name: getattr(_designSpec("macro-price-design-reversed"), name)
                    for name in _designSpec().__dataclass_fields__
                },
                "sourceColumns": tuple(reversed(_designSpec().sourceColumns)),
            }
        ),
    )
    assert reversedFrame.columnOrderHash != frame.columnOrderHash
    assert reversedFrame.frameHash != frame.frameHash


def testMultivariableObservationFrameDropsMissingSourceOriginsWithoutFilling(tmp_path) -> None:
    context = _trust(tmp_path)
    fxBatch = _signedBatch(
        context,
        _sourceObservationsFor(
            context,
            signalId="fxChange",
            values=(0.10, -0.20, 0.30, 0.40),
            events=("20200331", "20200630", "20200930", "20201231"),
            knowledgeDates=("20200410", "20200710", "20201010", "20210110"),
        ),
        signalId="fxChange",
        cutoffAsOf="20210430",
    )
    oilBatch = _signedBatch(
        context,
        _sourceObservationsFor(
            context,
            signalId="oilChange",
            values=(0.05, -0.05, 0.20),
            events=("20200331", "20200930", "20201231"),
            knowledgeDates=("20200410", "20201010", "20210110"),
        ),
        signalId="oilChange",
        cutoffAsOf="20210430",
    )
    labelBatch = _signedBatch(
        context,
        _labelObservations(
            context,
            values=(0.05, -0.10, 0.15, 0.20),
            events=("20200630", "20200930", "20201231", "20210331"),
            availableDates=("20200705", "20201005", "20210105", "20210405"),
            knowledgeDates=("20200710", "20201010", "20210110", "20210410"),
        ),
        signalId="realizedMarketPriceChange",
        cutoffAsOf="20210430",
    )
    frame = buildMultivariableDriverCoefficientObservationFrame((fxBatch, oilBatch), labelBatch, _designSpec())
    assert frame.rowCount == 3
    assert frame.droppedOriginCount == 1
    assert dict(frame.missingCountByVariable) == {"fxChange": 0, "oilChange": 1}
    assert frame.frame["originEventTime"].to_list() == ["20200331", "20200930", "20201231"]
    assert frame.frame["sourceValue__oilChange"].null_count() == 0


def testMultivariableObservationFrameRejectsUnsafeInputs(tmp_path) -> None:
    context = _trust(tmp_path)
    fxBatch = _signedBatch(
        context,
        _sourceObservationsFor(
            context,
            signalId="fxChange",
            values=(0.10, -0.20, 0.30, 0.40),
            events=("20200331", "20200630", "20200930", "20201231"),
            knowledgeDates=("20200410", "20200710", "20201010", "20210110"),
        ),
        signalId="fxChange",
        cutoffAsOf="20210430",
    )
    assumptionBatch = _signedBatch(
        context,
        _sourceObservationsFor(
            context,
            signalId="oilChange",
            values=(0.05, 0.10, -0.05, 0.20),
            events=("20200331", "20200630", "20200930", "20201231"),
            knowledgeDates=("20200410", "20200710", "20201010", "20210110"),
            evidenceRole="explicitAssumption",
        ),
        signalId="oilChange",
        cutoffAsOf="20210430",
    )
    validLabel = _signedBatch(
        context,
        _labelObservations(
            context,
            values=(0.05, -0.10, 0.15, 0.20),
            events=("20200630", "20200930", "20201231", "20210331"),
            availableDates=("20200705", "20201005", "20210105", "20210405"),
            knowledgeDates=("20200710", "20201010", "20210110", "20210410"),
        ),
        signalId="realizedMarketPriceChange",
        cutoffAsOf="20210430",
    )
    with pytest.raises(DriverObservationFrameError, match="evidence role"):
        buildMultivariableDriverCoefficientObservationFrame((fxBatch, assumptionBatch), validLabel, _designSpec())
    oilBatch = _signedBatch(
        context,
        _sourceObservationsFor(
            context,
            signalId="oilChange",
            values=(0.05, 0.10, -0.05, 0.20),
            events=("20200331", "20200630", "20200930", "20201231"),
            knowledgeDates=("20200410", "20200710", "20201010", "20210110"),
        ),
        signalId="oilChange",
        cutoffAsOf="20210430",
    )
    transformDriftFxBatch = _signedBatch(
        context,
        _sourceObservationsFor(
            context,
            signalId="fxChange",
            values=(0.10, -0.20, 0.30, 0.40),
            events=("20200331", "20200630", "20200930", "20201231"),
            knowledgeDates=("20200410", "20200710", "20201010", "20210110"),
            transformId="wrong-change-v1",
        ),
        signalId="fxChange",
        cutoffAsOf="20210430",
    )
    with pytest.raises(DriverObservationFrameError, match="transform drift"):
        buildMultivariableDriverCoefficientObservationFrame(
            (transformDriftFxBatch, oilBatch), validLabel, _designSpec()
        )
    timingDriftOilBatch = _signedBatch(
        context,
        _sourceObservationsFor(
            context,
            signalId="oilChange",
            values=(0.05, 0.10, -0.05, 0.20),
            events=("20200331", "20200630", "20200930", "20201231"),
            knowledgeDates=("20200410", "20200710", "20201010", "20210110"),
            timing="stock",
        ),
        signalId="oilChange",
        cutoffAsOf="20210430",
    )
    with pytest.raises(DriverObservationFrameError, match="timing drift"):
        buildMultivariableDriverCoefficientObservationFrame((fxBatch, timingDriftOilBatch), validLabel, _designSpec())
    delayedFxBatch = _signedBatch(
        context,
        _sourceObservationsFor(
            context,
            signalId="fxChange",
            values=(0.10, -0.20, 0.30, 0.40),
            events=("20200331", "20200630", "20200930", "20201231"),
            knowledgeDates=("20200710", "20200710", "20201010", "20210110"),
        ),
        signalId="fxChange",
        cutoffAsOf="20210430",
    )
    delayedOilBatch = _signedBatch(
        context,
        _sourceObservationsFor(
            context,
            signalId="oilChange",
            values=(0.05, 0.10, -0.05, 0.20),
            events=("20200331", "20200630", "20200930", "20201231"),
            knowledgeDates=("20200710", "20200710", "20201010", "20210110"),
        ),
        signalId="oilChange",
        cutoffAsOf="20210430",
    )
    leakingLabel = _signedBatch(
        context,
        _labelObservations(
            context,
            values=(0.05, -0.10, 0.15, 0.20),
            events=("20200630", "20200930", "20201231", "20210331"),
            availableDates=("20200705", "20201005", "20210105", "20210405"),
            knowledgeDates=("20200710", "20201010", "20210110", "20210410"),
        ),
        signalId="realizedMarketPriceChange",
        cutoffAsOf="20210430",
    )
    with pytest.raises(DriverObservationFrameError, match="not forward known"):
        buildMultivariableDriverCoefficientObservationFrame(
            (delayedFxBatch, delayedOilBatch), leakingLabel, _designSpec()
        )
    duplicateSpec = MultivariableDriverCoefficientObservationFrameSpec(
        **{
            **{name: getattr(_designSpec("duplicate-design"), name) for name in _designSpec().__dataclass_fields__},
            "sourceColumns": (
                _designSpec().sourceColumns[0],
                DriverDesignColumnSpec(
                    variableId="fxChange",
                    signalId="oilChange",
                    unit="simpleReturn",
                    frequency="quarter",
                    transformId="change-v1",
                ),
            ),
        }
    )
    with pytest.raises(DriverObservationFrameError, match="source variables must be unique"):
        buildMultivariableDriverCoefficientObservationFrame((fxBatch, oilBatch), leakingLabel, duplicateSpec)
    with pytest.raises(DriverObservationFrameError, match="must be signed"):
        buildMultivariableDriverCoefficientObservationFrame(
            (replace(fxBatch, batchReceiptId=""), oilBatch), leakingLabel, _designSpec()
        )


def testMultivariableDesignFrameFitsOosAdmissionAndExposures(tmp_path) -> None:
    context = _trust(tmp_path)
    _fitFx, _fitOil, fitFrame, oosFrame, receipt, report, signed, verified, exposures = _multivariableAdmissionBundle(
        context
    )
    assert tuple(term.variableId for term in receipt.coefficientTerms) == ("fxChange", "oilChange")
    assert tuple(term.coefficient for term in receipt.coefficientTerms) == pytest.approx((0.5, 0.25))
    assert receipt.featureSpecHash
    assert receipt.designFrameHash == fitFrame.frameHash
    assert receipt.coefficientVectorHash
    assert report.status == "oosEligible"
    with pytest.raises(DriverCalibrationError, match="requires OOS admission"):
        multivariableCalibrationReceiptToOperatingExposures(
            receipt,
            exposureIdPrefix="macro-price",
            oosReport=report,
            admissionReceipt=None,
        )
    assert len(exposures) == 2
    assert {exposure.sourceVariableId for exposure in exposures} == {"fxChange", "oilChange"}
    assert {exposure.evidenceKind for exposure in exposures} == {"measuredAssociation"}
    assert {exposure.sourceRef for exposure in exposures} == {f"driverCoefficientAdmission:{signed.receiptId}"}
    assert all(exposure.aggregationGroup for exposure in exposures)
    assert all(exposure.sourceFrequency == "quarter" for exposure in exposures)
    assert all(exposure.sourceTiming == "change" for exposure in exposures)
    assert all(exposure.sourceTransformId == "change-v1" for exposure in exposures)
    binding = buildScenarioCoefficientBindingFromVerifiedMultivariableAdmission(
        receipt,
        report,
        verified,
        exposures,
    )
    assert binding.admissionReceiptId == signed.receiptId
    assert binding.subjectHash == multivariableDriverCoefficientAdmissionSubjectHash(report)
    assert binding.ruleId == MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_ID
    assert binding.ruleVersion == MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_VERSION
    assert binding.ruleHash == MULTIVARIABLE_DRIVER_COEFFICIENT_RULE_HASH
    assert binding.parentReceiptIds == multivariableDriverCoefficientAdmissionParentReceiptIds(report)
    assert binding.sourceVariableIds == receipt.sourceVariableIds
    assert binding.coefficientVectorHash == receipt.coefficientVectorHash
    assert binding.featureSpecHash == receipt.featureSpecHash
    assert binding.designFrameHash == fitFrame.frameHash
    assert binding.fitDesignFrameHash == fitFrame.frameHash
    assert binding.oosDesignFrameHash == oosFrame.frameHash
    assert binding.exposureContractHash == scenarioCoefficientExposureContractHash(exposures)
    with pytest.raises(ScenarioCompositionError, match="exposure does not match"):
        buildScenarioCoefficientBindingFromVerifiedMultivariableAdmission(
            receipt,
            report,
            verified,
            (replace(exposures[0], coefficient=0.6), exposures[1]),
        )


def testMultivariableAdmissionBindingRunsOneCompanyScenarioLoop(tmp_path) -> None:
    context = _trust(tmp_path)
    (
        _fitFx,
        _fitOil,
        _fitFrame,
        _oosFrame,
        receipt,
        report,
        signed,
        verified,
        exposures,
    ) = _multivariableAdmissionBundle(context)
    binding = buildScenarioCoefficientBindingFromVerifiedMultivariableAdmission(
        receipt,
        report,
        verified,
        exposures,
    )
    loop = compareOneCompanyTwoScenarioStrategies(
        "005930",
        _operatingInputs(),
        (
            _scenarioCaseWithCoefficientBinding("base", (0.05, 0.02), exposures, binding, context[4]),
            _scenarioCaseWithCoefficientBinding("stress", (-0.10, 0.05), exposures, binding, context[4]),
        ),
        _oneStepStrategies(),
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )
    assert loop.decisionStatus == "conditionalOnly"
    assert loop.recommendationCeiling == "conditionalOnly"
    assert loop.recommendation is None
    base, _stress = loop.caseLedgers
    assert base.coefficientAdmissionReceiptIds == (signed.receiptId,)
    assert base.coefficientBindingHashes == (scenarioCoefficientBindingHash(binding),)
    assert base.coefficientParentReceiptIds == multivariableDriverCoefficientAdmissionParentReceiptIds(report)
    assert len(base.exposureLedgers) == 2
    assert {row.admissionReceiptId for row in base.exposureLedgers} == {signed.receiptId}
    assert {row.sourceVariableId for row in base.exposureLedgers} == {"fxChange", "oilChange"}
    assert base.pathAdmissionReceiptId == ""
    assert base.initialStateAdmissionReceiptId == ""
    assert base.policyEvaluationCertificateId == ""
    assert "pathAdmissionMissing" in base.blockedReasons
    assert "initialStateAdmissionMissing" in base.blockedReasons
    assert "policyEvaluationCertificateMissing" in base.blockedReasons
    assert "automaticRecommendationDisabled" in loop.blockedReasons


def testProviderHistoryAndExplicitAdjustmentFeedScenarioLoopWithoutPathAdmission(tmp_path) -> None:
    context = _trust(tmp_path)
    fitFx, fitOil, _fitFrame, _oosFrame, receipt, report, signed, verified, exposures = _multivariableAdmissionBundle(
        context,
        fitBatches=_multiFitLaneBatches(context),
    )
    binding = buildScenarioCoefficientBindingFromVerifiedMultivariableAdmission(
        receipt,
        report,
        verified,
        exposures,
    )
    loop = compareOneCompanyTwoScenarioStrategies(
        "005930",
        _operatingInputs(),
        (
            _scenarioCaseWithProviderHistoryAndAdjustment(
                "base",
                0.01,
                fitFx,
                fitOil,
                exposures,
                binding,
                context[4],
            ),
            _scenarioCaseWithProviderHistoryAndAdjustment(
                "stress",
                -0.03,
                fitFx,
                fitOil,
                exposures,
                binding,
                context[4],
            ),
        ),
        _oneStepStrategies(),
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )
    assert loop.recommendation is None
    base, _stress = loop.caseLedgers
    assert base.pathSetInputHash
    assert base.pathRegistryHash
    assert base.pathFactorContractHash
    assert base.scenarioPathPackageHash
    assert base.pathHistoryInputHash
    assert base.basePathSetHash
    assert base.pathAssumptionHash
    assert base.pathOverlayHash
    assert base.observedHistoryStatus == "asKnown"
    assert base.futureAdjustmentStatus == "explicitAssumption"
    assert base.composedPathSetHash == base.pathSetHash
    assert base.basePathAdmissionReceiptId == ""
    assert base.basePathAdmissionScope == "historyOnly"
    assert base.composedPathAdmissionStatus == "notAdmitted"
    assert base.pathAdmissionTransferStatus == "notTransferred"
    assert base.pathAdmissionTransferBlockedBy == (
        "explicitFutureAdjustmentPresent",
        "pathAdmissionNotTransferredFromObservedHistory",
        "composedPathAdmissionNotGranted",
    )
    assert base.policyEvaluationEligibility == "blocked"
    assert base.recommendationCeiling == "conditionalOnly"
    assert base.pathAdmissionReceiptId == ""
    assert base.policyEvaluationCertificateId == ""
    assert base.counts.pathCount == 2
    assert base.counts.providerBatchRefCount == 2
    assert base.counts.explicitAssumptionCount > 0
    assert base.explicitAssumptionIds == ("base-explicit-price-adjustment",)
    assert any(ref.startswith("providerObservationBatch:") for ref in base.providerObservationBatchRefs)
    assert any(ref.startswith("providerObservationBatchId:") for ref in base.providerObservationBatchRefs)
    assert "assumption://base/explicit-price-adjustment" in base.pathSourceRefs
    assert "explicitFutureAdjustmentPresent" in base.blockedReasons
    assert "unvalidatedPathPresent" in base.blockedReasons
    assert "composedPathAdmissionNotGranted" in base.blockedReasons
    assert "pathAdmissionNotTransferredFromObservedHistory" in base.blockedReasons
    assert "policyEvaluationRequiresAdmittedComposedPath" in base.blockedReasons
    assert "scoreLeaderNotRecommendation" in base.blockedReasons
    assert "pathAdmissionMissing" in base.blockedReasons
    assert "policyEvaluationCertificateMissing" in base.blockedReasons
    assert "automaticRecommendationDisabled" in loop.blockedReasons
    forbiddenPrefixes = ("pathAdmission:", "pathSetAdmission:", "policyEvaluation:", "policyCertificate:")
    assert not any(ref.startswith(forbiddenPrefixes) for ref in base.conditionRefs)
    assert base.coefficientAdmissionReceiptIds == (signed.receiptId,)
    assert {row.sourceVariableId for row in base.exposureLedgers} == {
        "fxChange",
        "oilChange",
        "explicitPriceAdjustment",
    }
    changed = compareOneCompanyTwoScenarioStrategies(
        "005930",
        _operatingInputs(),
        (
            _scenarioCaseWithProviderHistoryAndAdjustment(
                "base",
                0.02,
                fitFx,
                fitOil,
                exposures,
                binding,
                context[4],
            ),
            _scenarioCaseWithProviderHistoryAndAdjustment(
                "stress",
                -0.03,
                fitFx,
                fitOil,
                exposures,
                binding,
                context[4],
            ),
        ),
        _oneStepStrategies(),
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )
    changedBase = changed.caseLedgers[0]
    assert changedBase.pathHistoryInputHash == base.pathHistoryInputHash
    assert changedBase.basePathSetHash == base.basePathSetHash
    assert changedBase.pathAssumptionHash != base.pathAssumptionHash
    assert changedBase.pathOverlayHash != base.pathOverlayHash
    assert changedBase.composedPathSetHash != base.composedPathSetHash
    assert changedBase.scenarioPathPackageHash != base.scenarioPathPackageHash
    assert changed.loopHash != loop.loopHash


def testAdmittedCurrentStateFeedsScenarioLoopWithoutOpeningRecommendation(tmp_path) -> None:
    context = _trust(tmp_path)
    fitFx, fitOil, _fitFrame, _oosFrame, receipt, report, signed, verified, exposures = _multivariableAdmissionBundle(
        context,
        fitBatches=_multiFitLaneBatches(context),
    )
    binding = buildScenarioCoefficientBindingFromVerifiedMultivariableAdmission(
        receipt,
        report,
        verified,
        exposures,
    )
    inputs = _admittedOperatingInputs(context)
    loop = compareOneCompanyTwoScenarioStrategies(
        "005930",
        inputs,
        (
            _scenarioCaseWithProviderHistoryAndAdjustment(
                "base",
                0.01,
                fitFx,
                fitOil,
                exposures,
                binding,
                context[4],
            ),
            _scenarioCaseWithProviderHistoryAndAdjustment(
                "stress",
                -0.03,
                fitFx,
                fitOil,
                exposures,
                binding,
                context[4],
            ),
        ),
        _oneStepStrategies(),
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )
    assert loop.recommendation is None
    base, _stress = loop.caseLedgers
    assert base.initialStateAdmissionReceiptId == inputs.initialStateAdmissionReceiptId
    assert f"initialStateAdmission:{inputs.initialStateAdmissionReceiptId}" in base.stateRefs
    assert any(ref.startswith("stateReceipt:") for ref in base.stateRefs)
    assert any(ref.startswith("stateManifest:") for ref in base.stateRefs)
    assert any(ref.startswith("stateCompilationContract:") for ref in base.stateRefs)
    assert any(ref.startswith("providerBatchReceipt:") for ref in base.stateRefs)
    assert any(ref.startswith("observation:") for ref in base.stateRefs)
    assert "initialStateAdmissionMissing" not in base.blockedReasons
    assert base.pathAdmissionReceiptId == ""
    assert base.policyEvaluationCertificateId == ""
    assert "unvalidatedPathPresent" in base.blockedReasons
    assert "pathAdmissionMissing" in base.blockedReasons
    assert "policyEvaluationCertificateMissing" in base.blockedReasons
    assert "automaticRecommendationDisabled" in loop.blockedReasons

    changedState = dict(inputs.state)
    changedState["cash"] = changedState["cash"] + 1.0
    with pytest.raises(SimulationSpecError, match="initial-state admission"):
        compareOneCompanyTwoScenarioStrategies(
            "005930",
            replace(inputs, state=changedState),
            (
                _scenarioCaseWithProviderHistoryAndAdjustment(
                    "base",
                    0.01,
                    fitFx,
                    fitOil,
                    exposures,
                    binding,
                    context[4],
                ),
                _scenarioCaseWithProviderHistoryAndAdjustment(
                    "stress",
                    -0.03,
                    fitFx,
                    fitOil,
                    exposures,
                    binding,
                    context[4],
                ),
            ),
            _oneStepStrategies(),
            debtLimit=1_000.0,
            maxFinancing=200.0,
            maxInvestment=200.0,
        )

    with pytest.raises(SimulationSpecError, match="runtime admission verifier"):
        compareOneCompanyTwoScenarioStrategies(
            "005930",
            inputs,
            (
                _scenarioCaseWithProviderHistoryAndAdjustment(
                    "base",
                    0.01,
                    fitFx,
                    fitOil,
                    exposures,
                    binding,
                    None,
                ),
                _scenarioCaseWithProviderHistoryAndAdjustment(
                    "stress",
                    -0.03,
                    fitFx,
                    fitOil,
                    exposures,
                    binding,
                    None,
                ),
            ),
            _oneStepStrategies(),
            debtLimit=1_000.0,
            maxFinancing=200.0,
            maxInvestment=200.0,
        )


def testMultivariableAdmissionRejectsTamperedFeatureCellRef(tmp_path) -> None:
    context = _trust(tmp_path)
    fitFx, fitOil, fitLabel = _multiFitBatches(context)
    oosFx, oosOil, oosLabel = _multiOosBatches(context)
    fitFrame = buildMultivariableDriverCoefficientObservationFrame(
        (fitFx, fitOil),
        fitLabel,
        _designSpec("macro-vector-fit"),
    )
    oosFrame = buildMultivariableDriverCoefficientObservationFrame(
        (oosFx, oosOil),
        oosLabel,
        _designSpec("macro-vector-oos"),
    )
    tamperedFitFrame = replace(
        fitFrame,
        frame=fitFrame.frame.with_columns(pl.lit("providerObservation:alias").alias("sourceRef__fxChange")),
    )
    receipt = fitMultivariableDriverCoefficientPitFromObservationFrame(
        _multiRegistryResult(fitFx, fitOil),
        _target(tamperedFitFrame.labelParentReceiptIds),
        tamperedFitFrame,
        _multiFitSpec(tamperedFitFrame.sourceParentReceiptIds),
        calibrationKnowledgeAsOf="20210430",
    )
    report = evaluateMultivariableDriverCoefficientOosFromObservationFrame(
        receipt,
        oosFrame,
        _multiOosSpec(oosFrame.sourceParentReceiptIds, oosFrame.labelParentReceiptIds),
        evaluationKnowledgeAsOf="20220131",
    )
    signed = _issueMultivariableCoefficientAdmission(context, report)
    with pytest.raises(DriverCalibrationError, match="fit source parent coverage missing row refs"):
        validateMultivariableDriverCoefficientAdmission(
            report,
            context[4],
            calibrationReceipt=receipt,
            receiptId=signed.receiptId,
            decisionAsOf="20220202",
        )


def testMultivariableFitRejectsFeatureOrderAndRankDeficiency(tmp_path) -> None:
    context = _trust(tmp_path)
    fitFx, fitOil, fitLabel = _multiFitBatches(context)
    fitFrame = buildMultivariableDriverCoefficientObservationFrame(
        (fitFx, fitOil),
        fitLabel,
        _designSpec("macro-vector-fit"),
    )
    reversedSpec = MultivariableDriverCoefficientCalibrationSpec(
        calibrationId="macro-vector-to-price-fit",
        sourceVariableIds=("oilChange", "fxChange"),
        minOrigins=4,
        sourceParentReceiptIds=fitFrame.sourceParentReceiptIds,
    )
    with pytest.raises(DriverCalibrationError, match="binding mismatch"):
        fitMultivariableDriverCoefficientPitFromObservationFrame(
            _multiRegistryResult(fitFx, fitOil),
            _target(fitFrame.labelParentReceiptIds),
            fitFrame,
            reversedSpec,
            calibrationKnowledgeAsOf="20210430",
        )

    rankPath = tmp_path / "rank"
    rankPath.mkdir()
    rankContext = _trust(rankPath)
    events = ("20200331", "20200630", "20200930", "20201231")
    knowledgeDates = ("20200410", "20200710", "20201010", "20210110")
    fxValues = (0.10, -0.20, 0.30, 0.40)
    oilValues = tuple(value * 2 for value in fxValues)
    rankFx = _signedBatch(
        rankContext,
        _sourceObservationsFor(
            rankContext,
            signalId="fxChange",
            values=fxValues,
            events=events,
            knowledgeDates=knowledgeDates,
        ),
        signalId="fxChange",
        cutoffAsOf="20210430",
    )
    rankOil = _signedBatch(
        rankContext,
        _sourceObservationsFor(
            rankContext,
            signalId="oilChange",
            values=oilValues,
            events=events,
            knowledgeDates=knowledgeDates,
        ),
        signalId="oilChange",
        cutoffAsOf="20210430",
    )
    rankLabel = _signedBatch(
        rankContext,
        _labelObservations(
            rankContext,
            values=tuple(0.5 * value for value in fxValues),
            events=("20200630", "20200930", "20201231", "20210331"),
            availableDates=("20200705", "20201005", "20210105", "20210405"),
            knowledgeDates=("20200710", "20201010", "20210110", "20210410"),
        ),
        signalId="realizedMarketPriceChange",
        cutoffAsOf="20210430",
    )
    rankFrame = buildMultivariableDriverCoefficientObservationFrame(
        (rankFx, rankOil),
        rankLabel,
        _designSpec("macro-vector-rank"),
    )
    with pytest.raises(DriverCalibrationError, match="rank deficient"):
        fitMultivariableDriverCoefficientPitFromObservationFrame(
            _multiRegistryResult(rankFx, rankOil),
            _target(rankFrame.labelParentReceiptIds),
            rankFrame,
            _multiFitSpec(rankFrame.sourceParentReceiptIds),
            calibrationKnowledgeAsOf="20210430",
        )


def testDriverObservationFrameRejectsUnsignedDuplicateMissingAndDrift(tmp_path) -> None:
    context = _trust(tmp_path)
    fitSource, fitLabel = _fitBatches(context)
    unsignedSource = replace(fitSource, batchReceiptId="")
    with pytest.raises(DriverObservationFrameError, match="must be signed"):
        buildDriverCoefficientObservationFrame(unsignedSource, fitLabel, _frameSpec())

    duplicateObservation = _observation(
        context,
        signalId="fxChange",
        value=0.11,
        unit="simpleReturn",
        eventAt="20200331",
        availableAt="20200410",
        knowledgeAsOf="20200410",
        revisionId="amended",
    )
    duplicate = (*tuple(fitSource.observations), duplicateObservation)
    duplicateBatch = _signedBatch(context, duplicate, signalId="fxChange", cutoffAsOf="20210430")
    with pytest.raises(DriverObservationFrameError, match="duplicate observations"):
        buildDriverCoefficientObservationFrame(duplicateBatch, fitLabel, _frameSpec())

    shortLabelBatch = _signedBatch(
        context,
        tuple(fitLabel.observations[:-1]),
        signalId="realizedMarketPriceChange",
        cutoffAsOf="20210430",
    )
    with pytest.raises(DriverObservationFrameError, match="missing horizon label"):
        buildDriverCoefficientObservationFrame(fitSource, shortLabelBatch, _frameSpec())

    badUnitObservation = _observation(
        context,
        signalId="fxChange",
        value=0.10,
        unit="percent",
        eventAt="20200331",
        availableAt="20200410",
        knowledgeAsOf="20200410",
        revisionId="percent-unit",
    )
    badUnit = _signedBatch(
        context,
        (badUnitObservation, *fitSource.observations[1:]),
        signalId="fxChange",
        cutoffAsOf="20210430",
    )
    with pytest.raises(DriverObservationFrameError, match="meaning drift"):
        buildDriverCoefficientObservationFrame(badUnit, fitLabel, _frameSpec())


def testDriverObservationFrameRejectsAssumptionLabelsAndForwardLeakage(tmp_path) -> None:
    context = _trust(tmp_path)
    fitSource, fitLabel = _fitBatches(context)
    assumptionLabels = _labelObservations(
        context,
        values=(0.05, -0.10, 0.15, 0.20),
        events=("20200630", "20200930", "20201231", "20210331"),
        availableDates=("20200705", "20201005", "20210105", "20210405"),
        knowledgeDates=("20200710", "20201010", "20210110", "20210410"),
        evidenceRole="explicitAssumption",
    )
    assumptionBatch = _signedBatch(
        context,
        assumptionLabels,
        signalId="realizedMarketPriceChange",
        cutoffAsOf="20210430",
    )
    with pytest.raises(DriverObservationFrameError, match="evidence role"):
        buildDriverCoefficientObservationFrame(fitSource, assumptionBatch, _frameSpec())

    delayedSource = _observation(
        context,
        signalId="fxChange",
        value=0.10,
        unit="simpleReturn",
        eventAt="20200331",
        availableAt="20200410",
        knowledgeAsOf="20200710",
        revisionId="delayed-knowledge",
    )
    delayedSourceBatch = _signedBatch(
        context,
        (delayedSource, *fitSource.observations[1:]),
        signalId="fxChange",
        cutoffAsOf="20210430",
    )
    with pytest.raises(DriverObservationFrameError, match="not forward known"):
        buildDriverCoefficientObservationFrame(delayedSourceBatch, fitLabel, _frameSpec())


def testDriverObservationFrameTamperedRowFailsParentCoverage(tmp_path) -> None:
    context = _trust(tmp_path)
    fitSource, fitLabel = _fitBatches(context)
    oosSource, oosLabel = _oosBatches(context)
    fitFrame = buildDriverCoefficientObservationFrame(fitSource, fitLabel, _frameSpec("fit-frame"))
    oosFrame = buildDriverCoefficientObservationFrame(oosSource, oosLabel, _frameSpec("oos-frame"))
    rows = fitFrame.frame.to_dicts()
    rows[0]["sourceRef"] = "missing-observation-id"
    tamperedFitFrame = replace(fitFrame, frame=pl.DataFrame(rows))
    receipt, report, signed = _fitAndReport(context, tamperedFitFrame, oosFrame)
    with pytest.raises(DriverCalibrationError, match="fit source parent coverage missing row refs"):
        validateDriverCoefficientAdmission(
            report,
            context[4],
            calibrationReceipt=receipt,
            receiptId=signed.receiptId,
            decisionAsOf="20220202",
        )


def testProviderObservationAdmissionRejectsVintageSourceRefAlias(tmp_path) -> None:
    context = _trust(tmp_path)
    fitSource, fitLabel = _fitBatches(context)
    oosSource, oosLabel = _oosBatches(context)
    fitFrame = buildDriverCoefficientObservationFrame(fitSource, fitLabel, _frameSpec("fit-frame"))
    oosFrame = buildDriverCoefficientObservationFrame(oosSource, oosLabel, _frameSpec("oos-frame"))
    rows = fitFrame.frame.to_dicts()
    rows[0]["sourceRef"] = fitSource.observations[0].vintage.sourceRefs[0]
    aliasFitFrame = replace(fitFrame, frame=pl.DataFrame(rows))
    receipt, report, signed = _fitAndReport(context, aliasFitFrame, oosFrame)
    with pytest.raises(DriverCalibrationError, match="fit source parent coverage missing row refs"):
        validateDriverCoefficientAdmission(
            report,
            context[4],
            calibrationReceipt=receipt,
            receiptId=signed.receiptId,
            decisionAsOf="20220202",
        )


def testProviderObservationAdmissionRejectsRawDataFrameCoefficient(tmp_path) -> None:
    context = _trust(tmp_path)
    fitSource, fitLabel = _fitBatches(context)
    oosSource, oosLabel = _oosBatches(context)
    fitFrame = buildDriverCoefficientObservationFrame(fitSource, fitLabel, _frameSpec("fit-frame"))
    oosFrame = buildDriverCoefficientObservationFrame(oosSource, oosLabel, _frameSpec("oos-frame"))
    receipt = fitDriverCoefficientPit(
        _registryResult(),
        _target(fitFrame.labelParentReceiptIds),
        fitFrame.frame,
        _fitSpec(fitFrame.sourceParentReceiptIds),
        calibrationKnowledgeAsOf="20210430",
    )
    report = evaluateDriverCoefficientOos(
        receipt,
        oosFrame.frame,
        _oosSpec(oosFrame.sourceParentReceiptIds, oosFrame.labelParentReceiptIds),
        evaluationKnowledgeAsOf="20220131",
    )
    signed = _issueCoefficientAdmission(context, report)
    with pytest.raises(DriverCalibrationError, match="fit observation frame binding is missing"):
        validateDriverCoefficientAdmission(
            report,
            context[4],
            calibrationReceipt=receipt,
            receiptId=signed.receiptId,
            decisionAsOf="20220202",
        )


def testProviderObservationAdmissionRejectsFrameHashTamper(tmp_path) -> None:
    context = _trust(tmp_path)
    fitSource, fitLabel = _fitBatches(context)
    oosSource, oosLabel = _oosBatches(context)
    fitFrame = buildDriverCoefficientObservationFrame(fitSource, fitLabel, _frameSpec("fit-frame"))
    oosFrame = buildDriverCoefficientObservationFrame(oosSource, oosLabel, _frameSpec("oos-frame"))
    tamperedFitFrame = replace(fitFrame, frameHash="0" * 64)
    receipt, report, signed = _fitAndReport(context, tamperedFitFrame, oosFrame)
    with pytest.raises(DriverCalibrationError, match="fit observation frame replay mismatch"):
        validateDriverCoefficientAdmission(
            report,
            context[4],
            calibrationReceipt=receipt,
            receiptId=signed.receiptId,
            decisionAsOf="20220202",
        )


def testDriverObservationFrameRejectsUnderlyingVintageReceiptAsParent(tmp_path) -> None:
    context = _trust(tmp_path)
    fitSource, fitLabel = _fitBatches(context)
    oosSource, oosLabel = _oosBatches(context)
    fitFrame = buildDriverCoefficientObservationFrame(fitSource, fitLabel, _frameSpec("fit-frame"))
    oosFrame = buildDriverCoefficientObservationFrame(oosSource, oosLabel, _frameSpec("oos-frame"))
    rawFitFrame = replace(
        fitFrame,
        sourceParentReceiptIds=(fitSource.observations[0].vintage.receiptId,),
        labelParentReceiptIds=(fitLabel.observations[0].vintage.receiptId,),
    )
    rawOosFrame = replace(
        oosFrame,
        sourceParentReceiptIds=(oosSource.observations[0].vintage.receiptId,),
        labelParentReceiptIds=(oosLabel.observations[0].vintage.receiptId,),
    )
    with pytest.raises(DriverCalibrationError, match="fit observation frame binding mismatch"):
        _fitAndReport(context, rawFitFrame, rawOosFrame)
