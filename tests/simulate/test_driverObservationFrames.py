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
from dartlab.simulate.driverObservationBatches import driverHistorySourceFromProviderObservationBatch
from dartlab.simulate.driverObservationFrames import (
    DriverCoefficientObservationFrameSpec,
    DriverDesignColumnSpec,
    DriverObservationFrameError,
    MultivariableDriverCoefficientObservationFrameSpec,
    buildDriverCoefficientObservationFrame,
    buildMultivariableDriverCoefficientObservationFrame,
)
from dartlab.simulate.driverPaths import DriverCard, DriverFactorSpec, DriverHistorySource
from dartlab.simulate.driverRegistry import DriverRegistryCandidate, compileDriverRegistryPathSet
from dartlab.simulate.stateCompiler import (
    buildProviderObservationBatch,
    issueProviderObservationBatch,
    makeVariableObservation,
)
from dartlab.simulate.vintage import VintageRef


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
    receipt = fitMultivariableDriverCoefficientPitFromObservationFrame(
        _multiRegistryResult(fitFx, fitOil),
        _target(fitFrame.labelParentReceiptIds),
        fitFrame,
        _multiFitSpec(fitFrame.sourceParentReceiptIds),
        calibrationKnowledgeAsOf="20210430",
    )
    assert tuple(term.variableId for term in receipt.coefficientTerms) == ("fxChange", "oilChange")
    assert tuple(term.coefficient for term in receipt.coefficientTerms) == pytest.approx((0.5, 0.25))
    assert receipt.featureSpecHash
    assert receipt.designFrameHash == fitFrame.frameHash
    assert receipt.coefficientVectorHash

    report = evaluateMultivariableDriverCoefficientOosFromObservationFrame(
        receipt,
        oosFrame,
        _multiOosSpec(oosFrame.sourceParentReceiptIds, oosFrame.labelParentReceiptIds),
        evaluationKnowledgeAsOf="20220131",
    )
    assert report.status == "oosEligible"
    with pytest.raises(DriverCalibrationError, match="requires OOS admission"):
        multivariableCalibrationReceiptToOperatingExposures(
            receipt,
            exposureIdPrefix="macro-price",
            oosReport=report,
            admissionReceipt=None,
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
    assert len(exposures) == 2
    assert {exposure.sourceVariableId for exposure in exposures} == {"fxChange", "oilChange"}
    assert {exposure.evidenceKind for exposure in exposures} == {"measuredAssociation"}
    assert {exposure.sourceRef for exposure in exposures} == {f"driverCoefficientAdmission:{signed.receiptId}"}
    assert all(exposure.aggregationGroup for exposure in exposures)
    assert all(exposure.sourceFrequency == "quarter" for exposure in exposures)
    assert all(exposure.sourceTiming == "change" for exposure in exposures)
    assert all(exposure.sourceTransformId == "change-v1" for exposure in exposures)


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
