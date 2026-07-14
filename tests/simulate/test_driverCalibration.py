from __future__ import annotations

import polars as pl
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from dartlab.simulate.admissionRegistry import (
    AdmissionVerifier,
    TrustedIssuer,
    artifactPath,
    initializeAdmissionRegistry,
    issueAdmissionReceipt,
    putAdmissionArtifact,
)
from dartlab.simulate.driverCalibration import (
    DRIVER_COEFFICIENT_RULE_HASH,
    DRIVER_COEFFICIENT_RULE_ID,
    DRIVER_COEFFICIENT_RULE_VERSION,
    DriverCalibrationError,
    DriverCalibrationTarget,
    DriverCoefficientCalibrationSpec,
    DriverCoefficientOosSpec,
    calibrationReceiptToOperatingExposure,
    driverCoefficientAdmissionArtifact,
    driverCoefficientAdmissionSubjectHash,
    evaluateDriverCoefficientOos,
    fitDriverCoefficientPit,
    validateDriverCoefficientAdmission,
)
from dartlab.simulate.driverPaths import DriverCard, DriverFactorSpec, DriverHistorySource
from dartlab.simulate.driverRegistry import DriverRegistryCandidate, compileDriverRegistryPathSet
from dartlab.simulate.vintage import canonicalPayloadHash


def _registryResult():
    factor = DriverFactorSpec(
        "fxChange",
        "simpleReturn",
        "quarter",
        "change",
        "fx-change-quarterly-v1",
    )
    card = DriverCard(
        cardId="macro-fx-change",
        sourceKind="history",
        providerId="macro",
        datasetId="macro.fx.quarterly",
        entityId="KR",
        frequency="quarter",
        stepSpan=1,
        factors=(factor,),
        historyStatus="asKnown",
        sourceRefs=("artifact:macro/fx.parquet", "artifactHash:" + "a" * 64),
    )
    panel = pl.DataFrame(
        {
            "eventTime": ["20200331", "20200630", "20200930", "20201231"],
            "availableAt": ["20200401", "20200701", "20201001", "20210101"],
            "fxChange": [0.10, -0.20, 0.30, 0.40],
        }
    )
    return compileDriverRegistryPathSet(
        (
            DriverRegistryCandidate(
                "macro-fx",
                "pathHistory",
                DriverHistorySource(card, panel),
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


def _target(evidenceKind: str = "observedOutcome", proxyRef: str = "") -> DriverCalibrationTarget:
    return DriverCalibrationTarget(
        targetVariableId="realizedMarketPriceChange",
        targetShock="marketPriceChange",
        targetUnit="ratioChangePerStep",
        targetEvidenceKind=evidenceKind,
        labelProviderId="gov",
        labelDatasetId="equity.forwardReturn",
        labelSourceRefs=("label:equity-forward-return",),
        historyStatus="asKnown",
        semanticRefs=("semantics:observed-forward-equity-return",),
        targetProxyRef=proxyRef,
    )


def _spec(minOrigins: int = 4) -> DriverCoefficientCalibrationSpec:
    return DriverCoefficientCalibrationSpec(
        calibrationId="fx-to-price-fit",
        sourceVariableId="fxChange",
        minOrigins=minOrigins,
    )


def _frame(**overrides) -> pl.DataFrame:
    values = {
        "originId": ["o1", "o2", "o3", "o4"],
        "originEventTime": ["20200331", "20200630", "20200930", "20201231"],
        "originKnowledgeAsOf": ["20200410", "20200710", "20201010", "20210110"],
        "sourceAvailableAt": ["20200401", "20200701", "20201001", "20210101"],
        "targetEventTime": ["20200630", "20200930", "20201231", "20210331"],
        "targetAvailableAt": ["20200705", "20201005", "20210105", "20210405"],
        "sourceValue": [0.10, -0.20, 0.30, 0.40],
        "targetValue": [0.05, -0.10, 0.15, 0.20],
        "sourceRef": ["source:o1", "source:o2", "source:o3", "source:o4"],
        "labelSourceRef": ["label:o1", "label:o2", "label:o3", "label:o4"],
    }
    values.update(overrides)
    return pl.DataFrame(values)


def _receipt():
    return fitDriverCoefficientPit(
        _registryResult(),
        _target(),
        _frame(),
        _spec(),
        calibrationKnowledgeAsOf="20210430",
    )


def _oosFrame(**overrides) -> pl.DataFrame:
    values = {
        "originId": ["o5", "o6", "o7"],
        "originEventTime": ["20210331", "20210630", "20210930"],
        "originKnowledgeAsOf": ["20210410", "20210710", "20211010"],
        "sourceAvailableAt": ["20210401", "20210701", "20211001"],
        "targetEventTime": ["20210630", "20210930", "20211231"],
        "targetAvailableAt": ["20210705", "20211005", "20220105"],
        "sourceValue": [0.20, -0.10, 0.30],
        "targetValue": [0.10, -0.05, 0.15],
        "sourceRef": ["source:o5", "source:o6", "source:o7"],
        "labelSourceRef": ["label:o5", "label:o6", "label:o7"],
    }
    values.update(overrides)
    return pl.DataFrame(values)


def _oosSpec(minSkill: float = 0.1) -> DriverCoefficientOosSpec:
    return DriverCoefficientOosSpec(
        evaluationId="fx-to-price-oos",
        minOosOrigins=3,
        minSkillVsBaseline=minSkill,
        maxRmse=0.01,
        maxAbsBias=0.01,
        baselineValue=0.0,
        frequency="quarter",
        stepSpan=1,
        maxAdmittedStep=1,
    )


def _trust(tmp_path):
    database = tmp_path / "admission.sqlite"
    artifacts = tmp_path / "artifacts"
    initializeAdmissionRegistry(database)
    private = Ed25519PrivateKey.generate()
    privateBytes = private.private_bytes(
        serialization.Encoding.Raw,
        serialization.PrivateFormat.Raw,
        serialization.NoEncryption(),
    )
    publicBytes = private.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    trusted = {"key-1": TrustedIssuer("issuer-1", "key-1", publicBytes)}
    verifier = AdmissionVerifier(database, artifacts, trusted)
    return database, artifacts, privateBytes, trusted, verifier


def testDriverCalibrationIssuesRetrospectiveReceiptAndExposureRef() -> None:
    registryResult = _registryResult()
    receipt = fitDriverCoefficientPit(
        registryResult,
        _target(),
        _frame(),
        _spec(),
        calibrationKnowledgeAsOf="20210430",
    )
    assert receipt.status == "retrospectiveOnly"
    assert receipt.validationStatus == "retrospectiveOnly"
    assert receipt.coefficient == pytest.approx(0.5)
    assert receipt.coefficientUnit == "ratioChangePerStep/simpleReturn"
    assert receipt.registryHash == registryResult.audit.registryHash
    assert receipt.pathSetInputHash == registryResult.audit.pathSetInputHash
    assert receipt.factorContractHash == registryResult.pathSet.audit.factorContractHash
    assert "coefficientRequiresOosAdmission" in receipt.warnings

    with pytest.raises(DriverCalibrationError, match="requires OOS admission"):
        calibrationReceiptToOperatingExposure(receipt, exposureId="fx-price")


def testDriverCalibrationBlocksPitCutoffLeaks() -> None:
    with pytest.raises(DriverCalibrationError, match="source availability after origin knowledge"):
        fitDriverCoefficientPit(
            _registryResult(),
            _target(),
            _frame(sourceAvailableAt=["20200430", "20200701", "20201001", "20210101"]),
            _spec(),
            calibrationKnowledgeAsOf="20210430",
        )


def testDriverCoefficientOosReportCanBeSignedAndVerified(tmp_path) -> None:
    receipt = _receipt()
    report = evaluateDriverCoefficientOos(
        receipt,
        _oosFrame(),
        _oosSpec(),
        evaluationKnowledgeAsOf="20220131",
    )
    assert report.status == "oosEligible"
    subject = driverCoefficientAdmissionSubjectHash(report)
    database, artifacts, privateBytes, trusted, verifier = _trust(tmp_path)
    artifactHash = putAdmissionArtifact(artifacts, driverCoefficientAdmissionArtifact(report))
    assert artifactHash == subject
    signed = issueAdmissionReceipt(
        database,
        artifacts,
        privateKey=privateBytes,
        kind="driverCoefficient",
        subjectHash=subject,
        artifactHash=artifactHash,
        parentReceiptIds=(),
        ruleId=DRIVER_COEFFICIENT_RULE_ID,
        ruleVersion=DRIVER_COEFFICIENT_RULE_VERSION,
        ruleHash=DRIVER_COEFFICIENT_RULE_HASH,
        issuerId="issuer-1",
        issuerKeyId="key-1",
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
    verified = validateDriverCoefficientAdmission(
        report,
        verifier,
        receiptId=signed.receiptId,
        decisionAsOf="20220202",
    )
    assert verified == signed
    exposure = calibrationReceiptToOperatingExposure(
        receipt,
        exposureId="fx-price",
        oosReport=report,
        admissionReceipt=verified,
    )
    assert exposure.evidenceKind == "measuredAssociation"
    assert exposure.sourceRef == f"driverCoefficientAdmission:{signed.receiptId}"


def testDriverCoefficientOosRejectsOverlapWeakSkillAndTamper(tmp_path) -> None:
    with pytest.raises(DriverCalibrationError, match="overlaps fit window"):
        evaluateDriverCoefficientOos(
            _receipt(),
            _oosFrame(originEventTime=["20201231", "20210630", "20210930"]),
            _oosSpec(),
            evaluationKnowledgeAsOf="20220131",
        )
    with pytest.raises(DriverCalibrationError, match="known at calibration knowledge"):
        evaluateDriverCoefficientOos(
            _receipt(),
            _oosFrame(targetAvailableAt=["20210415", "20211005", "20220105"]),
            _oosSpec(),
            evaluationKnowledgeAsOf="20220131",
        )
    with pytest.raises(DriverCalibrationError, match="exceeds maxAdmittedStep"):
        evaluateDriverCoefficientOos(
            _receipt(),
            _oosFrame(
                targetEventTime=["20211231", "20210930", "20211231"],
                targetAvailableAt=["20220105", "20211005", "20220105"],
            ),
            _oosSpec(),
            evaluationKnowledgeAsOf="20220131",
        )
    weak = evaluateDriverCoefficientOos(
        _receipt(),
        _oosFrame(targetValue=[-0.10, 0.05, -0.15]),
        _oosSpec(),
        evaluationKnowledgeAsOf="20220131",
    )
    assert weak.status == "rejected"
    assert "skillBelowThreshold" in weak.reasons

    report = evaluateDriverCoefficientOos(
        _receipt(),
        _oosFrame(),
        _oosSpec(),
        evaluationKnowledgeAsOf="20220131",
    )
    tamperedRows = (
        report.traceRows[0].__class__(
            **{
                name: report.traceRows[0].targetValue + 1.0
                if name == "targetValue"
                else getattr(report.traceRows[0], name)
                for name in report.traceRows[0].__dataclass_fields__
            }
        ),
        *report.traceRows[1:],
    )
    tampered = report.__class__(
        **{name: tamperedRows if name == "traceRows" else getattr(report, name) for name in report.__dataclass_fields__}
    )
    tampered = tampered.__class__(
        **{
            name: canonicalPayloadHash(
                {field: getattr(tampered, field) for field in tampered.__dataclass_fields__ if field != "reportId"}
            )
            if name == "reportId"
            else getattr(tampered, name)
            for name in tampered.__dataclass_fields__
        }
    )
    with pytest.raises(DriverCalibrationError, match="residual mismatch|outcome hash mismatch"):
        driverCoefficientAdmissionArtifact(tampered)
    database, artifacts, privateBytes, trusted, verifier = _trust(tmp_path)
    subject = putAdmissionArtifact(artifacts, driverCoefficientAdmissionArtifact(report))
    signed = issueAdmissionReceipt(
        database,
        artifacts,
        privateKey=privateBytes,
        kind="driverCoefficient",
        subjectHash=subject,
        artifactHash=subject,
        parentReceiptIds=(),
        ruleId=DRIVER_COEFFICIENT_RULE_ID,
        ruleVersion=DRIVER_COEFFICIENT_RULE_VERSION,
        ruleHash=DRIVER_COEFFICIENT_RULE_HASH,
        issuerId="issuer-1",
        issuerKeyId="key-1",
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
    artifactPath(artifacts, subject).write_bytes(b"tampered")
    with pytest.raises(DriverCalibrationError, match="artifact hash mismatch"):
        validateDriverCoefficientAdmission(report, verifier, receiptId=signed.receiptId, decisionAsOf="20220202")
    with pytest.raises(DriverCalibrationError, match="target label availability after calibration knowledge"):
        fitDriverCoefficientPit(
            _registryResult(),
            _target(),
            _frame(targetAvailableAt=["20200705", "20201005", "20210105", "20210505"]),
            _spec(),
            calibrationKnowledgeAsOf="20210430",
        )


def testDriverCalibrationRejectsProxyAssumptionAndWeakSupport() -> None:
    with pytest.raises(DriverCalibrationError, match="observable label"):
        fitDriverCoefficientPit(
            _registryResult(),
            _target(evidenceKind="explicitAssumption"),
            _frame(),
            _spec(),
            calibrationKnowledgeAsOf="20210430",
        )
    with pytest.raises(DriverCalibrationError, match="proxy target"):
        fitDriverCoefficientPit(
            _registryResult(),
            _target(proxyRef="proxy:revenue-split-to-demand"),
            _frame(),
            _spec(),
            calibrationKnowledgeAsOf="20210430",
        )
    with pytest.raises(DriverCalibrationError, match="support below minOrigins"):
        fitDriverCoefficientPit(
            _registryResult(),
            _target(),
            _frame().head(2),
            _spec(minOrigins=4),
            calibrationKnowledgeAsOf="20210430",
        )
