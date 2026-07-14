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
    _priceReturnPayload,
    _priceReturnRevisionId,
    buildDriverObservationBatchFromPanel,
    buildFilingMetricDriverObservationBatch,
    buildPriceReturnDriverObservationBatch,
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
from dartlab.simulate.driverSources import (
    filingMetricDriverHistorySource,
    macroDriverHistorySource,
    panelMetricDriverHistorySource,
)
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
    runConditionalScenarioExperiment,
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
from dartlab.simulate.vintage import VintageRef, canonicalPayloadBytes
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


def _sourceReceiptWithParents(
    context,
    payload: dict,
    *,
    knowledgeAsOf: str,
    parentReceiptIds: tuple[str, ...],
    frequency: str,
):
    database, artifacts, privateBytes, trusted, _verifier = context
    content = canonicalPayloadBytes(payload)
    artifactHash = putAdmissionArtifact(artifacts, content)
    return issueAdmissionReceipt(
        database,
        artifacts,
        privateKey=privateBytes,
        kind="dataVintage",
        subjectHash=artifactHash,
        artifactHash=artifactHash,
        parentReceiptIds=tuple(sorted(parentReceiptIds)),
        ruleId="provider-derived-vintage-v1",
        ruleVersion="1",
        ruleHash=sha256(b"provider-derived-vintage-v1").hexdigest(),
        issuerId="provider-issuer",
        issuerKeyId="provider-key",
        issuerExecutableHash=sha256(b"provider-derived-vintage-issuer-v1").hexdigest(),
        knowledgeAsOf=knowledgeAsOf,
        revisionPolicy="asKnown",
        coverage="asOfExact",
        frequency=frequency,
        stepSpan=1,
        maxAdmittedStep=0,
        status="verifiedVintage",
        issuedAt=f"{knowledgeAsOf}T000000Z",
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


def _filingMetricRegistrySource() -> DriverHistorySource:
    factor = DriverFactorSpec(
        "operatingMarginChange",
        "ratioChange",
        "quarter",
        "change",
        "dart-operating-margin-change-v1",
        sourceColumn="opMarginChange",
    )
    panel = pl.DataFrame(
        {
            "code": ["005930", "005930", "005930", "005930"],
            "period": ["20200331", "20200331", "20200630", "20200930"],
            "rceptDate": ["20200515", "20210517", "20200814", "20201116"],
            "rceptNo": ["202005150001", "202105170009", "202008140001", "202011160001"],
            "opMarginChange": [0.02, 9.99, -0.01, 0.03],
        }
    )
    return filingMetricDriverHistorySource(
        panel,
        cardId="dart-operating-margin-change",
        providerId="dart",
        datasetId="dart.finance.retained",
        entityId="005930",
        entityIdColumn="code",
        frequency="quarter",
        stepSpan=1,
        factors=(factor,),
        sourceRefs=("data/dart/finance/005930.parquet", "transform:operating-margin-change"),
        knowledgeAsOf="20201231",
        eventTimeColumn="period",
        availableAtColumn="rceptDate",
        filingIdColumn="rceptNo",
    )


def _industryTimeSeriesRegistrySource() -> DriverHistorySource:
    factor = DriverFactorSpec(
        "industryOrderChange",
        "simpleReturn",
        "quarter",
        "change",
        "industry-order-change-quarterly-v1",
        sourceColumn="orderChange",
    )
    panel = pl.DataFrame(
        {
            "eventTime": ["20200331", "20200630", "20200930"],
            "availableAt": ["20200410", "20200710", "20201012"],
            "orderChange": [0.01, -0.03, 0.04],
        }
    )
    return panelMetricDriverHistorySource(
        panel,
        cardId="industry-order-change",
        providerId="industry",
        datasetId="industry.metric.quarterly",
        entityId="semiconductor",
        frequency="quarter",
        stepSpan=1,
        factors=(factor,),
        sourceRefs=("data/industry/metrics/semiconductor.parquet",),
        knowledgeAsOf="20201231",
    )


def _registryExplicitDemandAdjustment(caseId: str, shock: float) -> DriverAssumptionSource:
    factor = DriverFactorSpec(
        "manualDemandAdjustment",
        "simpleReturn",
        "quarter",
        "change",
        "manual-demand-adjustment-v1",
    )
    card = DriverCard(
        cardId=f"{caseId}-manual-demand-adjustment",
        sourceKind="explicitAssumption",
        providerId="user",
        datasetId="manual-scenario",
        entityId="005930",
        frequency="quarter",
        stepSpan=1,
        factors=(factor,),
        historyStatus="explicitAssumption",
        sourceRefs=(f"assumption://{caseId}/manual-demand-adjustment",),
        assumptionId=f"{caseId}-manual-demand-adjustment",
        claim=f"{caseId} manual future demand adjustment.",
        falsifier="The declared future demand adjustment is not the scenario being tested.",
    )
    return DriverAssumptionSource(card, ({"manualDemandAdjustment": shock},))


def _registryScenarioCaseWithFilingIndustryAndAdjustment(caseId: str, shock: float, verifier) -> OperatingScenarioCase:
    registry = compileDriverRegistryPathSet(
        (
            DriverRegistryCandidate(
                "dart-filing-margin",
                "pathHistory",
                _filingMetricRegistrySource(),
                semanticRefs=("semantics:financial-filing-change-path",),
                selectionReason="Quarterly filing metric transformed to ratio change.",
            ),
            DriverRegistryCandidate(
                "industry-orders",
                "pathHistory",
                _industryTimeSeriesRegistrySource(),
                semanticRefs=("semantics:industry-time-series-path",),
                selectionReason="Industry metric has real eventTime and availableAt.",
            ),
            DriverRegistryCandidate(
                f"{caseId}-manual-demand",
                "explicitAssumption",
                _registryExplicitDemandAdjustment(caseId, shock),
                semanticRefs=(f"semantics:{caseId}:explicit-future-demand-adjustment",),
                selectionReason="Manual future demand adjustment for this assumption set.",
            ),
        ),
        registryId=f"{caseId}-dart-industry-demand-registry",
        knowledgeAsOf="20201231",
        horizon=1,
        pathCount=2,
        blockLength=1,
        seed=29,
        minObservations=3,
    )
    exposures = (
        OperatingTransmissionExposure(
            f"{caseId}-filing-margin-unit-cost",
            "operatingMarginChange",
            "unitCostChange",
            -0.5,
            "ratioChangePerStep/ratioChange",
            "explicitAssumption",
            f"assumption://{caseId}/law/filing-margin-to-unit-cost",
        ),
        OperatingTransmissionExposure(
            f"{caseId}-industry-orders-demand",
            "industryOrderChange",
            "demandChange",
            0.8,
            "ratioChangePerStep/simpleReturn",
            "explicitAssumption",
            f"assumption://{caseId}/law/industry-orders-to-demand",
        ),
        OperatingTransmissionExposure(
            f"{caseId}-manual-demand",
            "manualDemandAdjustment",
            "demandChange",
            1.0,
            "ratioChangePerStep/simpleReturn",
            "explicitAssumption",
            f"assumption://{caseId}/law/manual-demand-adjustment",
        ),
    )
    return OperatingScenarioCase(
        caseId,
        caseId.title(),
        registry.pathSet,
        exposures,
        _operatingBaselines(),
        refs=(f"scenario://{caseId}",),
        admissionVerifier=verifier,
        driverRegistryAudit=registry.audit,
    )


def _quarterEvidenceDates() -> tuple[str, ...]:
    return (
        "20191231",
        "20200331",
        "20200630",
        "20200930",
        "20201231",
        "20210331",
        "20210630",
    )


def _quarterAvailability(dateText: str) -> str:
    return {
        "20191231": "20200115",
        "20200331": "20200415",
        "20200630": "20200715",
        "20200930": "20201015",
        "20201231": "20210115",
        "20210331": "20210415",
        "20210630": "20210715",
    }[dateText]


def _signProviderDriverBatch(context, batch, *, cutoffAsOf: str):
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


def _attachExactRowReceipts(context, panel: pl.DataFrame, *, revisionColumn: str, availableColumn: str, label: str):
    receipts = {}
    artifactHashes = []
    knowledgeValues = []
    for row in panel.to_dicts():
        knowledgeAsOf = str(row[availableColumn])
        receipt = _sourceReceipt(
            context,
            canonicalPayloadBytes({"label": label, "row": row}),
            knowledgeAsOf=knowledgeAsOf,
            issuedAt=f"{knowledgeAsOf}T000000Z",
        )
        receipts[str(row[revisionColumn])] = receipt
        artifactHashes.append(receipt.artifactHash)
        knowledgeValues.append(knowledgeAsOf)
    return (
        panel.with_columns(
            pl.Series("knowledgeAsOf", knowledgeValues),
            pl.Series("sourceArtifactHash", artifactHashes),
        ),
        receipts,
    )


def _exactEdgarQuarterlyMetricSource(context) -> DriverHistorySource:
    events = _quarterEvidenceDates()[1:]
    accepted = tuple(_quarterAvailability(event) for event in events)
    panel = pl.DataFrame(
        {
            "cik": ["0000320193"] * len(events),
            "period": list(events),
            "acceptedAt": list(accepted),
            "accession": [f"0000320193-21-{index:06d}" for index in range(1, len(events) + 1)],
            "operatingMarginChange": [0.015, -0.006, 0.012, 0.021, -0.009, 0.026],
        }
    )
    panel, sourceReceipts = _attachExactRowReceipts(
        context,
        panel,
        revisionColumn="accession",
        availableColumn="acceptedAt",
        label="edgar-companyfacts-operating-margin",
    )
    normalizationHash = sha256(b"edgar-operating-margin-change-quarterly-normalization-v1").hexdigest()
    laneHash = sha256(
        canonicalPayloadBytes(
            {
                "providerId": "edgar",
                "datasetId": "edgar.companyfacts.metric",
                "entityId": "0000320193",
                "rows": panel.to_dicts(),
                "signalId": "operatingMarginChange",
                "normalizationHash": normalizationHash,
            }
        )
    ).hexdigest()
    batch = buildFilingMetricDriverObservationBatch(
        panel,
        providerId="edgar",
        datasetId="edgar.companyfacts.metric",
        entityId="0000320193",
        knowledgeAsOf="20210715",
        eventTimeColumn="period",
        availableAtColumn="acceptedAt",
        filingIdColumn="accession",
        entityIdColumn="cik",
        sourceArtifactKind="edgarFilingMetricRows",
        sourceArtifactId="0000320193:operatingMarginChange:quarter-grid",
        sourceArtifactHash=laneHash,
        signalSpecs=(
            DriverObservationSignalSpec(
                "operatingMarginChange",
                "operatingMarginChange",
                "ratioChange",
                "quarter",
                "ratio",
                "edgar-operating-margin-change-quarterly-v1",
                "deterministicDerived",
                normalizationHash,
            ),
        ),
        sourceRefs=(
            "source:edgar-companyfacts",
            "filingTrace:edgar-companyfacts-0000320193-quarter-grid",
            "normalization:edgar-operating-margin-change-quarterly-v1",
        ),
        sourceArtifactHashColumn="sourceArtifactHash",
        sourceReceipts=sourceReceipts,
        requireExact=True,
    )
    signedBatch = _signProviderDriverBatch(context, batch, cutoffAsOf="20210715")
    return driverHistorySourceFromProviderObservationBatch(
        signedBatch,
        cardId="edgar-operating-margin-change-quarterly",
        factors=(
            DriverFactorSpec(
                "operatingMarginChange",
                "ratioChange",
                "quarter",
                "change",
                "edgar-operating-margin-change-quarterly-v1",
            ),
        ),
        sourceRefs=(
            *(f"sourceReceiptRef:{receiptId}" for receiptId in signedBatch.sourceReceiptIds),
            "source:edgar-companyfacts",
            "filingTrace:edgar-companyfacts-0000320193-quarter-grid",
            "filingIdColumn:accession",
            f"normalizationContractHash:{normalizationHash}",
            "factorMapping:operatingMarginChange->operatingMarginChange",
        ),
    )


def _exactQuarterlyPricePanel() -> pl.DataFrame:
    dates = _quarterEvidenceDates()
    return pl.DataFrame(
        {
            "date": list(dates),
            "availableAt": [_quarterAvailability(dateText) for dateText in dates],
            "code": ["005930"] * len(dates),
            "revisionId": [f"krx-005930-{dateText}" for dateText in dates],
            "close": [100.0, 103.0, 101.455, 104.49865, 102.93117025, 106.01893536, 108.13931407],
        }
    )


def _attachExactPriceReceipts(context, panel: pl.DataFrame) -> tuple[pl.DataFrame, dict[str, object]]:
    receipts = {}
    artifactHashes = []
    for row in panel.to_dicts():
        receipt = _sourceReceipt(
            context,
            canonicalPayloadBytes({"label": "gov-price-close", "row": row}),
            knowledgeAsOf=str(row["availableAt"]),
            issuedAt=f"{row['availableAt']}T000000Z",
        )
        receipts[str(row["revisionId"])] = receipt
        artifactHashes.append(receipt.artifactHash)
    return panel.with_columns(pl.Series("sourceArtifactHash", artifactHashes)), receipts


def _exactPriceReturnReceipts(
    context,
    panel: pl.DataFrame,
    priceReceipts: dict[str, object],
    *,
    adjustmentPolicyHash: str,
) -> dict[str, object]:
    receipts = {}
    rows = panel.sort("date").to_dicts()
    for previous, current in zip(rows, rows[1:]):
        previousReceipt = priceReceipts[str(previous["revisionId"])]
        currentReceipt = priceReceipts[str(current["revisionId"])]
        value = float(current["close"]) / float(previous["close"]) - 1.0
        availableAt = max(str(previous["availableAt"]), str(current["availableAt"]))
        revisionId = _priceReturnRevisionId(
            previousRevisionId=str(previous["revisionId"]),
            currentRevisionId=str(current["revisionId"]),
            frequency="quarter",
            returnWindow=1,
        )
        previousLeg = {
            "eventAt": str(previous["date"]),
            "availableAt": str(previous["availableAt"]),
            "revisionId": str(previous["revisionId"]),
            "close": float(previous["close"]),
            "sourceArtifactHash": str(previous["sourceArtifactHash"]),
            "receiptId": previousReceipt.receiptId,
        }
        currentLeg = {
            "eventAt": str(current["date"]),
            "availableAt": str(current["availableAt"]),
            "revisionId": str(current["revisionId"]),
            "close": float(current["close"]),
            "sourceArtifactHash": str(current["sourceArtifactHash"]),
            "receiptId": currentReceipt.receiptId,
        }
        payload = _priceReturnPayload(
            providerId="gov",
            datasetId="gov.prices.returns",
            entityId="005930",
            signalId="equityReturnShock",
            frequency="quarter",
            returnWindow=1,
            adjustmentPolicyHash=adjustmentPolicyHash,
            previousLeg=previousLeg,
            currentLeg=currentLeg,
            eventAt=str(current["date"]),
            availableAt=availableAt,
            value=value,
        )
        receipts[revisionId] = _sourceReceiptWithParents(
            context,
            payload,
            knowledgeAsOf=availableAt,
            parentReceiptIds=(previousReceipt.receiptId, currentReceipt.receiptId),
            frequency="quarter",
        )
    return receipts


def _exactQuarterlyPriceReturnSource(context) -> DriverHistorySource:
    panel, priceReceipts = _attachExactPriceReceipts(context, _exactQuarterlyPricePanel())
    adjustmentPolicyHash = sha256(b"split-dividend-adjusted-close-policy-v1").hexdigest()
    returnReceipts = _exactPriceReturnReceipts(
        context,
        panel,
        priceReceipts,
        adjustmentPolicyHash=adjustmentPolicyHash,
    )
    batch = buildPriceReturnDriverObservationBatch(
        panel,
        code="005930",
        knowledgeAsOf="20210715",
        sourceReceipts=priceReceipts,
        returnReceipts=returnReceipts,
        sourceRefs=(
            "source:gov-price-close",
            "series:krx:005930:quarterly-close",
            f"adjustmentPolicyHash:{adjustmentPolicyHash}",
        ),
        frequency="quarter",
        adjustmentPolicyHash=adjustmentPolicyHash,
    )
    signedBatch = _signProviderDriverBatch(context, batch, cutoffAsOf="20210715")
    priceReceiptRefs = tuple(
        f"priceSourceLegReceiptId:{receipt.receiptId}"
        for _revisionId, receipt in sorted(priceReceipts.items(), key=lambda item: item[0])
    )
    returnReceiptRefs = tuple(
        f"derivedReturnReceiptId:{receipt.receiptId}"
        for _revisionId, receipt in sorted(returnReceipts.items(), key=lambda item: item[0])
    )
    return driverHistorySourceFromProviderObservationBatch(
        signedBatch,
        cardId="exact-quarterly-equity-return",
        factors=(
            DriverFactorSpec(
                "equityReturnShock",
                "simpleReturn",
                "quarter",
                "innovation",
                "price-simple-return-quarter-1-v1",
            ),
        ),
        sourceRefs=(
            "source:gov-price-close",
            "series:krx:005930:quarterly-close",
            *priceReceiptRefs,
            *returnReceiptRefs,
            f"adjustmentPolicyHash:{adjustmentPolicyHash}",
            "returnTransform:price-simple-return-quarter-1-v1",
            "returnFormula:simpleReturn=currentClose/previousClose-1",
            "factorMapping:equityReturnShock->equityReturnShock",
        ),
    )


def _quarterlyMacroInnovationSource() -> DriverHistorySource:
    dates = _quarterEvidenceDates()
    macro = pl.DataFrame(
        {
            "date": list(dates),
            "oil": [100.0, 102.0, 99.96, 103.9584, 101.879232, 104.935609, 107.034321],
        }
    )
    return macroDriverHistorySource(
        macro,
        knowledgeAsOf="20210715",
        sourceRefs=(
            "data/macro/quarterly-fixture",
            "macroSeriesId:fred:DCOILWTICO",
            "macroRevisionPolicy:revised-history",
        ),
        cardId="macro-oil-quarterly-innovation",
        factorIds=("oil",),
        frequency="quarter",
    )


def _edgarPriceMacroRegistrySources(context) -> tuple[DriverHistorySource, DriverHistorySource, DriverHistorySource]:
    return (
        _exactEdgarQuarterlyMetricSource(context),
        _exactQuarterlyPriceReturnSource(context),
        _quarterlyMacroInnovationSource(),
    )


def _quarterlyRegistryExplicitDemandAdjustment(caseId: str, shock: float) -> DriverAssumptionSource:
    factor = DriverFactorSpec(
        "manualDemandAdjustment",
        "simpleReturn",
        "quarter",
        "change",
        "manual-demand-adjustment-quarterly-v1",
    )
    card = DriverCard(
        cardId=f"{caseId}-manual-demand-adjustment-quarterly",
        sourceKind="explicitAssumption",
        providerId="user",
        datasetId="manual-scenario",
        entityId="005930",
        frequency="quarter",
        stepSpan=1,
        factors=(factor,),
        historyStatus="explicitAssumption",
        sourceRefs=(f"assumption://{caseId}/manual-demand-adjustment-quarterly",),
        assumptionId=f"{caseId}-manual-demand-adjustment-quarterly",
        claim=f"{caseId} manual future demand adjustment on the quarterly grid.",
        falsifier="The declared future demand adjustment is not the scenario being tested.",
    )
    return DriverAssumptionSource(card, ({"manualDemandAdjustment": shock},))


def _quarterlyRegistryExplicitDemandAdjustmentPath(
    caseId: str,
    shocks: tuple[float, float, float, float],
) -> DriverAssumptionSource:
    factor = DriverFactorSpec(
        "manualDemandAdjustment",
        "simpleReturn",
        "quarter",
        "change",
        "manual-demand-adjustment-quarterly-v1",
    )
    card = DriverCard(
        cardId=f"{caseId}-manual-demand-adjustment-quarterly-path",
        sourceKind="explicitAssumption",
        providerId="user",
        datasetId="manual-scenario",
        entityId="005930",
        frequency="quarter",
        stepSpan=1,
        factors=(factor,),
        historyStatus="explicitAssumption",
        sourceRefs=(f"assumption://{caseId}/manual-demand-adjustment-quarterly-path",),
        assumptionId=f"{caseId}-manual-demand-adjustment-quarterly-path",
        claim=f"{caseId} manual future demand adjustment path on the quarterly grid.",
        falsifier="The declared future demand adjustment path is not the scenario being tested.",
    )
    return DriverAssumptionSource(card, tuple({"manualDemandAdjustment": shock} for shock in shocks))


def _registryScenarioCaseWithEdgarPriceMacroAndAdjustment(
    caseId: str,
    shock: float,
    verifier,
    sources: tuple[DriverHistorySource, DriverHistorySource, DriverHistorySource],
) -> OperatingScenarioCase:
    edgarSource, priceSource, macroSource = sources
    registry = compileDriverRegistryPathSet(
        (
            DriverRegistryCandidate(
                "edgar-filing-margin",
                "pathHistory",
                edgarSource,
                semanticRefs=("semantics:edgar-financial-filing-change-path",),
                selectionReason="Exact EDGAR filing metric is projected from a signed provider batch.",
            ),
            DriverRegistryCandidate(
                "price-return-exact",
                "pathHistory",
                priceSource,
                semanticRefs=("semantics:exact-equity-return-path",),
                selectionReason="Exact derived equity return keeps source price legs and return receipts.",
            ),
            DriverRegistryCandidate(
                "macro-oil-innovation",
                "pathHistory",
                macroSource,
                semanticRefs=("semantics:macro-quarterly-innovation-path",),
                selectionReason="Macro level history is transformed to quarterly innovation before admission.",
            ),
            DriverRegistryCandidate(
                f"{caseId}-manual-demand-quarterly",
                "explicitAssumption",
                _quarterlyRegistryExplicitDemandAdjustment(caseId, shock),
                semanticRefs=(f"semantics:{caseId}:explicit-future-demand-adjustment-quarterly",),
                selectionReason="Manual future demand adjustment for this assumption set.",
            ),
        ),
        registryId=f"{caseId}-edgar-price-macro-demand-registry",
        knowledgeAsOf="20210715",
        horizon=1,
        pathCount=3,
        blockLength=2,
        seed=37,
        minObservations=6,
    )
    exposures = (
        OperatingTransmissionExposure(
            f"{caseId}-edgar-margin-unit-cost",
            "operatingMarginChange",
            "unitCostChange",
            -0.4,
            "ratioChangePerStep/ratioChange",
            "explicitAssumption",
            f"assumption://{caseId}/law/edgar-margin-to-unit-cost",
        ),
        OperatingTransmissionExposure(
            f"{caseId}-equity-return-market-price",
            "equityReturnShock",
            "marketPriceChange",
            0.35,
            "ratioChangePerStep/simpleReturn",
            "explicitAssumption",
            f"assumption://{caseId}/law/equity-return-to-market-price",
        ),
        OperatingTransmissionExposure(
            f"{caseId}-oil-unit-cost",
            "oil",
            "unitCostChange",
            0.25,
            "ratioChangePerStep/simpleReturn",
            "explicitAssumption",
            f"assumption://{caseId}/law/oil-to-unit-cost",
        ),
        OperatingTransmissionExposure(
            f"{caseId}-manual-demand-quarterly",
            "manualDemandAdjustment",
            "demandChange",
            1.0,
            "ratioChangePerStep/simpleReturn",
            "explicitAssumption",
            f"assumption://{caseId}/law/manual-demand-adjustment-quarterly",
        ),
    )
    return OperatingScenarioCase(
        caseId,
        caseId.title(),
        registry.pathSet,
        exposures,
        _operatingBaselines(),
        refs=(f"scenario://{caseId}",),
        admissionVerifier=verifier,
        driverRegistryAudit=registry.audit,
    )


def _registryScenarioCaseWithEdgarPriceMacroAndAdjustmentPath(
    caseId: str,
    shocks: tuple[float, float, float, float],
    verifier,
    sources: tuple[DriverHistorySource, DriverHistorySource, DriverHistorySource],
) -> OperatingScenarioCase:
    edgarSource, priceSource, macroSource = sources
    registry = compileDriverRegistryPathSet(
        (
            DriverRegistryCandidate(
                "edgar-filing-margin",
                "pathHistory",
                edgarSource,
                semanticRefs=("semantics:edgar-financial-filing-change-path",),
                selectionReason="Exact EDGAR filing metric is projected from a signed provider batch.",
            ),
            DriverRegistryCandidate(
                "price-return-exact",
                "pathHistory",
                priceSource,
                semanticRefs=("semantics:exact-equity-return-path",),
                selectionReason="Exact derived equity return keeps source price legs and return receipts.",
            ),
            DriverRegistryCandidate(
                "macro-oil-innovation",
                "pathHistory",
                macroSource,
                semanticRefs=("semantics:macro-quarterly-innovation-path",),
                selectionReason="Macro level history is transformed to quarterly innovation before admission.",
            ),
            DriverRegistryCandidate(
                f"{caseId}-manual-demand-quarterly-path",
                "explicitAssumption",
                _quarterlyRegistryExplicitDemandAdjustmentPath(caseId, shocks),
                semanticRefs=(f"semantics:{caseId}:explicit-future-demand-adjustment-quarterly-path",),
                selectionReason="Manual future demand adjustment path for this assumption set.",
            ),
        ),
        registryId=f"{caseId}-edgar-price-macro-demand-path-registry",
        knowledgeAsOf="20210715",
        horizon=4,
        pathCount=4,
        blockLength=2,
        seed=41,
        minObservations=6,
    )
    exposures = (
        OperatingTransmissionExposure(
            f"{caseId}-edgar-margin-unit-cost",
            "operatingMarginChange",
            "unitCostChange",
            -0.4,
            "ratioChangePerStep/ratioChange",
            "explicitAssumption",
            f"assumption://{caseId}/law/edgar-margin-to-unit-cost",
        ),
        OperatingTransmissionExposure(
            f"{caseId}-equity-return-market-price",
            "equityReturnShock",
            "marketPriceChange",
            0.35,
            "ratioChangePerStep/simpleReturn",
            "explicitAssumption",
            f"assumption://{caseId}/law/equity-return-to-market-price",
        ),
        OperatingTransmissionExposure(
            f"{caseId}-oil-unit-cost",
            "oil",
            "unitCostChange",
            0.25,
            "ratioChangePerStep/simpleReturn",
            "explicitAssumption",
            f"assumption://{caseId}/law/oil-to-unit-cost",
        ),
        OperatingTransmissionExposure(
            f"{caseId}-manual-demand-quarterly-path",
            "manualDemandAdjustment",
            "demandChange",
            1.0,
            "ratioChangePerStep/simpleReturn",
            "explicitAssumption",
            f"assumption://{caseId}/law/manual-demand-adjustment-quarterly-path",
        ),
    )
    return OperatingScenarioCase(
        caseId,
        caseId.title(),
        registry.pathSet,
        exposures,
        _operatingBaselines(),
        refs=(f"scenario://{caseId}",),
        admissionVerifier=verifier,
        driverRegistryAudit=registry.audit,
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


def _oneStepExperimentStrategies():
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
        buildOperatingStrategy(
            "defend",
            priceChange=(0.03,),
            capacityInvestment=(0.0,),
            borrow=(0.0,),
            repay=(10.0,),
            refs=("strategy://defend",),
        ),
    )


def _fourQuarterExperimentStrategies():
    return (
        buildOperatingStrategy(
            "hold",
            priceChange=(0.0, 0.0, 0.0, 0.0),
            capacityInvestment=(0.0, 0.0, 0.0, 0.0),
            borrow=(0.0, 0.0, 0.0, 0.0),
            repay=(0.0, 0.0, 0.0, 0.0),
            refs=("strategy://hold",),
            isBaseline=True,
        ),
        buildOperatingStrategy(
            "earlyInvest",
            priceChange=(0.03, 0.03, 0.02, 0.02),
            capacityInvestment=(100.0, 0.0, 0.0, 0.0),
            borrow=(40.0, 0.0, 0.0, 0.0),
            repay=(0.0, 0.0, 0.0, 0.0),
            refs=("strategy://early-invest",),
        ),
        buildOperatingStrategy(
            "defend",
            priceChange=(0.03, 0.03, 0.02, 0.02),
            capacityInvestment=(0.0, 0.0, 0.0, 0.0),
            borrow=(0.0, 0.0, 0.0, 0.0),
            repay=(0.0, 5.0, 5.0, 5.0),
            refs=("strategy://defend",),
        ),
        buildOperatingStrategy(
            "lateInvest",
            priceChange=(0.03, 0.03, 0.02, 0.02),
            capacityInvestment=(0.0, 0.0, 100.0, 0.0),
            borrow=(0.0, 0.0, 40.0, 0.0),
            repay=(0.0, 0.0, 0.0, 0.0),
            refs=("strategy://late-invest",),
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


def testProviderHistoryAdmittedStateAndAdjustmentsFeedConditionalExperiment(tmp_path) -> None:
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
    cases = (
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
            "upside",
            0.04,
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
        _scenarioCaseWithProviderHistoryAndAdjustment(
            "shock",
            -0.08,
            fitFx,
            fitOil,
            exposures,
            binding,
            context[4],
        ),
    )
    experiment = runConditionalScenarioExperiment(
        "005930",
        inputs,
        cases,
        _oneStepExperimentStrategies(),
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )
    assert experiment.scenarioCount == 4
    assert experiment.strategyCount == 3
    assert experiment.cellCount == 12
    assert experiment.strategyIds == ("hold", "invest", "defend")
    assert experiment.assumptionSetIds == ("base", "upside", "stress", "shock")
    assert experiment.recommendation is None
    assert experiment.decisionStatus == "conditionalOnly"
    assert experiment.recommendationCeiling == "conditionalOnly"
    assert len(experiment.caseLedgerHashes) == 4
    assert len(set(experiment.caseLedgerHashes)) == 4
    assert f"initialStateAdmission:{inputs.initialStateAdmissionReceiptId}" in experiment.initialStateRefs
    assert any(ref.startswith("stateReceipt:") for ref in experiment.initialStateRefs)
    assert any(ref.startswith("stateManifest:") for ref in experiment.initialStateRefs)
    assert any(ref.startswith("stateCompilationContract:") for ref in experiment.initialStateRefs)
    assert any(ref.startswith("providerBatchReceipt:") for ref in experiment.initialStateRefs)
    assert any(ref.startswith("observation:") for ref in experiment.initialStateRefs)
    providerRefs = tuple(
        dict.fromkeys(ref for ledger in experiment.caseLedgers for ref in ledger.providerObservationBatchRefs)
    )
    explicitAssumptionIds = tuple(
        dict.fromkeys(
            assumptionId for ledger in experiment.caseLedgers for assumptionId in ledger.explicitAssumptionIds
        )
    )
    pathHistoryInputHashes = tuple(
        dict.fromkeys(ledger.pathHistoryInputHash for ledger in experiment.caseLedgers if ledger.pathHistoryInputHash)
    )
    pathAssumptionHashes = tuple(
        dict.fromkeys(ledger.pathAssumptionHash for ledger in experiment.caseLedgers if ledger.pathAssumptionHash)
    )
    assert experiment.providerObservationBatchRefs == providerRefs
    assert experiment.explicitAssumptionIds == explicitAssumptionIds
    assert experiment.pathHistoryInputHashes == pathHistoryInputHashes
    assert experiment.pathAssumptionHashes == pathAssumptionHashes
    assert any(ref.startswith("providerObservationBatch:") for ref in experiment.providerObservationBatchRefs)
    assert any(ref.startswith("providerObservationBatchId:") for ref in experiment.providerObservationBatchRefs)
    assert experiment.explicitAssumptionIds == (
        "base-explicit-price-adjustment",
        "upside-explicit-price-adjustment",
        "stress-explicit-price-adjustment",
        "shock-explicit-price-adjustment",
    )
    assert experiment.pathHistoryInputHashes == tuple(ledger.pathHistoryInputHash for ledger in experiment.caseLedgers)
    assert experiment.pathAssumptionHashes == tuple(ledger.pathAssumptionHash for ledger in experiment.caseLedgers)
    assert all(experiment.pathHistoryInputHashes)
    assert all(experiment.pathAssumptionHashes)
    assert all(
        ledger.initialStateAdmissionReceiptId == inputs.initialStateAdmissionReceiptId
        for ledger in experiment.caseLedgers
    )
    assert all("initialStateAdmissionMissing" not in ledger.blockedReasons for ledger in experiment.caseLedgers)
    assert "initialStateAdmissionMissing" not in experiment.blockedReasons
    assert "assumptionSweepPresent" in experiment.blockedReasons
    assert "strategySweepPresent" in experiment.blockedReasons
    assert "automaticRecommendationDisabled" in experiment.blockedReasons
    assert "conditionalExperimentNotPolicyRecommendation" in experiment.blockedReasons
    assert "pathAdmissionMissing" in experiment.blockedReasons
    assert "policyEvaluationCertificateMissing" in experiment.blockedReasons
    assert "scoreLeaderNotRecommendation" in experiment.blockedReasons
    assert len(experiment.strategySummaries) == 3
    assert all(summary.totalCellCount == 4 for summary in experiment.strategySummaries)
    assert any(summary.leaderCellCount for summary in experiment.strategySummaries)
    assert len(experiment.fragilityCells) == 4
    assert {row.caseId for row in experiment.fragilityCells} == {"base", "upside", "stress", "shock"}
    assert any(cell.regret > 0.0 for cell in experiment.cells)
    assert len({round(row.leaderMargin, 12) for row in experiment.fragilityCells}) > 1
    assert signed.receiptId in experiment.caseLedgers[0].coefficientAdmissionReceiptIds

    changedCases = (
        _scenarioCaseWithProviderHistoryAndAdjustment(
            "base",
            0.02,
            fitFx,
            fitOil,
            exposures,
            binding,
            context[4],
        ),
        *cases[1:],
    )
    changed = runConditionalScenarioExperiment(
        "005930",
        inputs,
        changedCases,
        _oneStepExperimentStrategies(),
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )
    assert changed.providerObservationBatchRefs == experiment.providerObservationBatchRefs
    assert changed.explicitAssumptionIds == experiment.explicitAssumptionIds
    assert changed.pathHistoryInputHashes == experiment.pathHistoryInputHashes
    assert changed.pathAssumptionHashes != experiment.pathAssumptionHashes
    assert changed.assumptionSetHashes != experiment.assumptionSetHashes
    assert changed.simulationSpecHash != experiment.simulationSpecHash
    assert changed.resultSetHash != experiment.resultSetHash
    assert changed.experimentHash != experiment.experimentHash


def testRegistryFilingIndustryLanesFeedConditionalExperimentWithAdmittedState(tmp_path) -> None:
    context = _trust(tmp_path)
    inputs = _admittedOperatingInputs(context)
    cases = (
        _registryScenarioCaseWithFilingIndustryAndAdjustment("base", 0.00, context[4]),
        _registryScenarioCaseWithFilingIndustryAndAdjustment("upside", 0.05, context[4]),
        _registryScenarioCaseWithFilingIndustryAndAdjustment("stress", -0.04, context[4]),
        _registryScenarioCaseWithFilingIndustryAndAdjustment("shock", -0.09, context[4]),
    )
    experiment = runConditionalScenarioExperiment(
        "005930",
        inputs,
        cases,
        _oneStepExperimentStrategies(),
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )
    assert experiment.scenarioCount == 4
    assert experiment.strategyCount == 3
    assert experiment.cellCount == 12
    assert experiment.recommendation is None
    assert experiment.decisionStatus == "conditionalOnly"
    assert len(experiment.driverRegistryHashes) == 4
    assert "dart-filing-margin" in experiment.driverRegistryLaneIds
    assert "industry-orders" in experiment.driverRegistryLaneIds
    assert "semantics:financial-filing-change-path" in experiment.driverRegistrySemanticRefs
    assert "semantics:industry-time-series-path" in experiment.driverRegistrySemanticRefs
    assert "data/dart/finance/005930.parquet" in experiment.driverRegistrySourceRefs
    assert "data/industry/metrics/semiconductor.parquet" in experiment.driverRegistrySourceRefs
    assert "driverRegistryContainsRevisedHistory" in experiment.driverRegistryWarnings
    assert "driverRegistryContainsExplicitAssumption" in experiment.driverRegistryWarnings
    assert "filingSourceNotExactAsKnown" in experiment.driverRegistryWarnings
    assert "dartRetainedFinanceRowsAreConditionalUntilRawFilingReceiptsExist" in experiment.driverRegistryWarnings
    assert f"initialStateAdmission:{inputs.initialStateAdmissionReceiptId}" in experiment.initialStateRefs
    assert "initialStateAdmissionMissing" not in experiment.blockedReasons
    assert "automaticRecommendationDisabled" in experiment.blockedReasons
    assert "conditionalExperimentNotPolicyRecommendation" in experiment.blockedReasons
    assert "pathAdmissionMissing" in experiment.blockedReasons
    assert "policyEvaluationCertificateMissing" in experiment.blockedReasons

    base = experiment.caseLedgers[0]
    assert base.driverRegistryLedger is not None
    assert base.driverRegistryLedger.registryHash in experiment.driverRegistryHashes
    assert base.driverRegistryLedger.laneIds == ("dart-filing-margin", "industry-orders", "base-manual-demand")
    assert base.driverRegistryLedger.cardIds == (
        "dart-operating-margin-change",
        "industry-order-change",
        "base-manual-demand-adjustment",
    )
    assert base.driverRegistryLedger.factorIds == (
        "operatingMarginChange",
        "industryOrderChange",
        "manualDemandAdjustment",
    )
    assert base.driverRegistryLedger.commonObservationCount == 3
    assert base.driverRegistryLedger.sourceObservationCounts == (("dart-filing-margin", 3), ("industry-orders", 3))
    assert base.driverRegistryLedger.eventStart == "20200331"
    assert base.driverRegistryLedger.eventEnd == "20200930"
    assert base.driverRegistryLedger.pathSetHash == base.pathSetHash
    assert base.driverRegistryLedger.pathSetInputHash == base.pathSetInputHash
    assert base.driverRegistryLedger.validationStatus == "unvalidated"
    assert base.driverRegistryLedger.historyStatus == "explicitAssumption"
    assert f"driverRegistry:{base.driverRegistryLedger.registryHash}" in base.conditionRefs
    assert "driverRegistryLane:dart-filing-margin" in base.conditionRefs
    assert "driverRegistryLane:industry-orders" in base.conditionRefs
    assert "filingTrace:" in " ".join(base.pathSourceRefs)
    assert "data/industry/metrics/semiconductor.parquet" in base.pathSourceRefs
    assert "assumption://base/manual-demand-adjustment" in base.assumptionRefs
    assert base.explicitAssumptionIds == ("base-manual-demand-adjustment",)
    assert base.pathAdmissionReceiptId == ""
    assert base.policyEvaluationCertificateId == ""
    assert base.composedPathAdmissionStatus == "notAdmitted"
    assert "explicitFutureAdjustmentPresent" in base.blockedReasons
    assert "scoreLeaderNotRecommendation" in base.blockedReasons

    actionIds = {"priceChange", "capacityInvestment", "borrow", "repay"}
    for case in cases:
        assert not set(case.pathSet.audit.driverCardIds) & actionIds
        for path in case.pathSet.paths:
            for step in path.steps:
                assert not set(step) & actionIds
    assert all(ref.startswith("strategy://") for strategy in _oneStepExperimentStrategies() for ref in strategy.refs)
    assert len(experiment.strategySummaries) == 3
    assert len(experiment.fragilityCells) == 4
    assert any(cell.regret > 0.0 for cell in experiment.cells)
    assert len({round(row.leaderMargin, 12) for row in experiment.fragilityCells}) > 1
    assert len(set(experiment.pathHistoryInputHashes)) == 1
    assert len(set(experiment.pathAssumptionHashes)) == 4

    changedCases = (
        _registryScenarioCaseWithFilingIndustryAndAdjustment("base", 0.03, context[4]),
        *cases[1:],
    )
    changed = runConditionalScenarioExperiment(
        "005930",
        inputs,
        changedCases,
        _oneStepExperimentStrategies(),
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )
    assert changed.driverRegistrySourceRefs == experiment.driverRegistrySourceRefs
    assert changed.pathHistoryInputHashes == experiment.pathHistoryInputHashes
    assert changed.pathAssumptionHashes != experiment.pathAssumptionHashes
    assert changed.assumptionSetHashes != experiment.assumptionSetHashes
    assert changed.driverRegistryHashes != experiment.driverRegistryHashes
    assert changed.simulationSpecHash != experiment.simulationSpecHash
    assert changed.resultSetHash != experiment.resultSetHash
    assert changed.experimentHash != experiment.experimentHash


def testRegistryEdgarExactPriceAndMacroLanesFeedConditionalExperiment(tmp_path) -> None:
    context = _trust(tmp_path)
    inputs = _admittedOperatingInputs(context)
    sources = _edgarPriceMacroRegistrySources(context)
    cases = (
        _registryScenarioCaseWithEdgarPriceMacroAndAdjustment("base", 0.00, context[4], sources),
        _registryScenarioCaseWithEdgarPriceMacroAndAdjustment("upside", 0.04, context[4], sources),
        _registryScenarioCaseWithEdgarPriceMacroAndAdjustment("stress", -0.03, context[4], sources),
        _registryScenarioCaseWithEdgarPriceMacroAndAdjustment("shock", -0.08, context[4], sources),
    )
    experiment = runConditionalScenarioExperiment(
        "005930",
        inputs,
        cases,
        _oneStepExperimentStrategies(),
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )

    assert experiment.scenarioCount == 4
    assert experiment.strategyCount == 3
    assert experiment.cellCount == 12
    assert experiment.decisionStatus == "conditionalOnly"
    assert experiment.recommendation is None
    assert "automaticRecommendationDisabled" in experiment.blockedReasons
    assert "conditionalExperimentNotPolicyRecommendation" in experiment.blockedReasons
    assert "pathAdmissionMissing" in experiment.blockedReasons
    assert "policyEvaluationCertificateMissing" in experiment.blockedReasons

    assert "edgar-filing-margin" in experiment.driverRegistryLaneIds
    assert "price-return-exact" in experiment.driverRegistryLaneIds
    assert "macro-oil-innovation" in experiment.driverRegistryLaneIds
    assert "semantics:edgar-financial-filing-change-path" in experiment.driverRegistrySemanticRefs
    assert "semantics:exact-equity-return-path" in experiment.driverRegistrySemanticRefs
    assert "semantics:macro-quarterly-innovation-path" in experiment.driverRegistrySemanticRefs
    assert "source:edgar-companyfacts" in experiment.driverRegistrySourceRefs
    assert "source:gov-price-close" in experiment.driverRegistrySourceRefs
    assert "simulate.driverSources:macroDriverHistorySource" in experiment.driverRegistrySourceRefs
    assert "macroReleaseVintageUnavailable" in experiment.driverRegistryWarnings
    assert "driverRegistryContainsRevisedHistory" in experiment.driverRegistryWarnings
    assert "driverRegistryContainsExplicitAssumption" in experiment.driverRegistryWarnings
    assert "priceVintageUnavailable" not in experiment.driverRegistryWarnings
    assert "filingSourceNotExactAsKnown" not in experiment.driverRegistryWarnings

    providerRefs = tuple(
        dict.fromkeys(ref for ledger in experiment.caseLedgers for ref in ledger.providerObservationBatchRefs)
    )
    explicitAssumptionIds = tuple(
        dict.fromkeys(
            assumptionId for ledger in experiment.caseLedgers for assumptionId in ledger.explicitAssumptionIds
        )
    )
    assert experiment.providerObservationBatchRefs == providerRefs
    assert len(experiment.providerObservationBatchRefs) == 4
    assert any(ref.startswith("providerObservationBatch:") for ref in experiment.providerObservationBatchRefs)
    assert any(ref.startswith("providerObservationBatchId:") for ref in experiment.providerObservationBatchRefs)
    assert experiment.explicitAssumptionIds == explicitAssumptionIds
    assert experiment.explicitAssumptionIds == (
        "base-manual-demand-adjustment-quarterly",
        "upside-manual-demand-adjustment-quarterly",
        "stress-manual-demand-adjustment-quarterly",
        "shock-manual-demand-adjustment-quarterly",
    )

    base = experiment.caseLedgers[0]
    assert base.driverRegistryLedger is not None
    assert base.driverRegistryLedger.laneIds == (
        "edgar-filing-margin",
        "price-return-exact",
        "macro-oil-innovation",
        "base-manual-demand-quarterly",
    )
    assert base.driverRegistryLedger.cardIds == (
        "edgar-operating-margin-change-quarterly",
        "exact-quarterly-equity-return",
        "macro-oil-quarterly-innovation",
        "base-manual-demand-adjustment-quarterly",
    )
    assert base.driverRegistryLedger.factorIds == (
        "operatingMarginChange",
        "equityReturnShock",
        "oil",
        "manualDemandAdjustment",
    )
    assert base.driverRegistryLedger.commonObservationCount == 6
    assert base.driverRegistryLedger.sourceObservationCounts == (
        ("edgar-filing-margin", 6),
        ("price-return-exact", 6),
        ("macro-oil-innovation", 6),
    )
    assert base.driverRegistryLedger.eventStart == "20200331"
    assert base.driverRegistryLedger.eventEnd == "20210630"
    assert base.driverRegistryLedger.pathSetHash == base.pathSetHash
    assert base.driverRegistryLedger.pathSetInputHash == base.pathSetInputHash
    assert base.observedHistoryStatus == "revisedHistory"
    assert base.futureAdjustmentStatus == "explicitAssumption"
    assert "explicitFutureAdjustmentPresent" in base.blockedReasons
    assert "scoreLeaderNotRecommendation" in base.blockedReasons
    assert any(ref.startswith("sourceReceiptRef:") for ref in base.pathSourceRefs)
    assert any(ref.startswith("priceSourceLegReceiptId:") for ref in base.pathSourceRefs)
    assert any(ref.startswith("derivedReturnReceiptId:") for ref in base.pathSourceRefs)
    assert any(ref.startswith("adjustmentPolicyHash:") for ref in base.pathSourceRefs)
    assert "returnFormula:simpleReturn=currentClose/previousClose-1" in base.pathSourceRefs
    assert "macroRevisionPolicy:revised-history" in base.pathSourceRefs
    assert "assumption://base/manual-demand-adjustment-quarterly" in base.assumptionRefs
    assert base.explicitAssumptionIds == ("base-manual-demand-adjustment-quarterly",)
    assert base.pathAdmissionReceiptId == ""
    assert base.policyEvaluationCertificateId == ""

    assert len(experiment.strategySummaries) == 3
    assert len(experiment.fragilityCells) == 4
    assert len(set(experiment.pathHistoryInputHashes)) == 1
    assert len(set(experiment.pathAssumptionHashes)) == 4

    changedCases = (
        _registryScenarioCaseWithEdgarPriceMacroAndAdjustment("base", 0.02, context[4], sources),
        *cases[1:],
    )
    changed = runConditionalScenarioExperiment(
        "005930",
        inputs,
        changedCases,
        _oneStepExperimentStrategies(),
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )
    assert changed.providerObservationBatchRefs == experiment.providerObservationBatchRefs
    assert changed.pathHistoryInputHashes == experiment.pathHistoryInputHashes
    assert changed.explicitAssumptionIds == experiment.explicitAssumptionIds
    assert changed.pathAssumptionHashes != experiment.pathAssumptionHashes
    assert changed.assumptionSetHashes != experiment.assumptionSetHashes
    assert changed.simulationSpecHash != experiment.simulationSpecHash
    assert changed.resultSetHash != experiment.resultSetHash
    assert changed.experimentHash != experiment.experimentHash


def testRegistryEdgarPriceMacroMultiStepExperimentShowsStrategyFragility(tmp_path) -> None:
    context = _trust(tmp_path)
    inputs = _admittedOperatingInputs(context)
    sources = _edgarPriceMacroRegistrySources(context)
    cases = (
        _registryScenarioCaseWithEdgarPriceMacroAndAdjustmentPath(
            "base",
            (0.00, 0.00, 0.00, 0.00),
            context[4],
            sources,
        ),
        _registryScenarioCaseWithEdgarPriceMacroAndAdjustmentPath(
            "upside",
            (0.25, 0.25, 0.20, 0.15),
            context[4],
            sources,
        ),
        _registryScenarioCaseWithEdgarPriceMacroAndAdjustmentPath(
            "stress",
            (-0.05, -0.08, -0.08, -0.05),
            context[4],
            sources,
        ),
        _registryScenarioCaseWithEdgarPriceMacroAndAdjustmentPath(
            "shock",
            (-0.12, -0.10, -0.08, -0.05),
            context[4],
            sources,
        ),
    )
    strategies = _fourQuarterExperimentStrategies()
    experiment = runConditionalScenarioExperiment(
        "005930",
        inputs,
        cases,
        strategies,
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )

    assert experiment.scenarioCount == 4
    assert experiment.strategyCount == 4
    assert experiment.cellCount == 16
    assert experiment.decisionStatus == "conditionalOnly"
    assert experiment.recommendation is None
    assert "automaticRecommendationDisabled" in experiment.blockedReasons
    assert "conditionalExperimentNotPolicyRecommendation" in experiment.blockedReasons
    assert "pathAdmissionMissing" in experiment.blockedReasons
    assert "policyEvaluationCertificateMissing" in experiment.blockedReasons

    assert all(case.pathSet.audit.horizon == 4 for case in cases)
    assert all(len(path.steps) == 4 for case in cases for path in case.pathSet.paths)
    assert all(len(strategy.actionsByStep) == 4 for strategy in strategies)
    assert all(len(ledger.pathAssumptionStepHashes) == 4 for ledger in experiment.caseLedgers)
    assert len(experiment.pathAssumptionStepHashes) == 4
    assert all(len(stepHashes) == 4 for stepHashes in experiment.pathAssumptionStepHashes)
    assert len(set(experiment.pathHistoryInputHashes)) == 1
    assert len(set(experiment.pathAssumptionHashes)) == 4
    assert len(set(experiment.assumptionSetHashes)) == 4

    actionIds = {"priceChange", "capacityInvestment", "borrow", "repay"}
    stateIds = {"price", "demandVolume", "unitCost", "fixedCost", "capacityUnits", "cash", "debt"}
    for case in cases:
        factorIds = {factor.variableId for factor in case.pathSet.factorSpecs}
        assert factorIds.isdisjoint(actionIds)
        assert factorIds.isdisjoint(stateIds)
        assert all(actionId not in step for path in case.pathSet.paths for step in path.steps for actionId in actionIds)
        assert all(stateId not in step for path in case.pathSet.paths for step in path.steps for stateId in stateIds)
    assert all(set(actionRow) == actionIds for strategy in strategies for actionRow in strategy.actionsByStep)

    leaderSets = {ledger.scoreLeaderStrategies for ledger in experiment.caseLedgers}
    assert len(leaderSets) >= 2
    assert "scenarioScoreLeadersDiverge" in experiment.blockedReasons
    assert any(0.0 < summary.leaderFrequency < 1.0 for summary in experiment.strategySummaries)
    assert len(experiment.fragilityCells) == 4
    assert any(cell.regret > 0.0 for cell in experiment.cells)
    assert any(
        len({score.objectiveScores[0] for score in ledger.strategyScores}) > 1 for ledger in experiment.caseLedgers
    )

    repeated = runConditionalScenarioExperiment(
        "005930",
        inputs,
        cases,
        strategies,
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )
    assert repeated.experimentHash == experiment.experimentHash

    changedCases = (
        _registryScenarioCaseWithEdgarPriceMacroAndAdjustmentPath(
            "base",
            (0.00, 0.00, 0.07, 0.00),
            context[4],
            sources,
        ),
        *cases[1:],
    )
    changed = runConditionalScenarioExperiment(
        "005930",
        inputs,
        changedCases,
        strategies,
        debtLimit=1_000.0,
        maxFinancing=200.0,
        maxInvestment=200.0,
    )
    assert changed.providerObservationBatchRefs == experiment.providerObservationBatchRefs
    assert changed.pathHistoryInputHashes == experiment.pathHistoryInputHashes
    assert changed.explicitAssumptionIds == experiment.explicitAssumptionIds
    assert changed.pathAssumptionStepHashes[0][0] == experiment.pathAssumptionStepHashes[0][0]
    assert changed.pathAssumptionStepHashes[0][1] == experiment.pathAssumptionStepHashes[0][1]
    assert changed.pathAssumptionStepHashes[0][2] != experiment.pathAssumptionStepHashes[0][2]
    assert changed.pathAssumptionStepHashes[0][3] == experiment.pathAssumptionStepHashes[0][3]
    assert changed.pathAssumptionHashes != experiment.pathAssumptionHashes
    assert changed.assumptionSetHashes != experiment.assumptionSetHashes
    assert changed.simulationSpecHash != experiment.simulationSpecHash
    assert changed.resultSetHash != experiment.resultSetHash
    assert changed.experimentHash != experiment.experimentHash


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
