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
    PARENT_COVERAGE_VERSION,
    DriverCalibrationError,
    DriverCalibrationTarget,
    DriverCoefficientCalibrationSpec,
    DriverCoefficientOosSpec,
    calibrationReceiptToOperatingExposure,
    driverCoefficientAdmissionArtifact,
    driverCoefficientAdmissionParentReceiptIds,
    driverCoefficientAdmissionSubjectHash,
    evaluateDriverCoefficientOos,
    fitDriverCoefficientPit,
    validateDriverCoefficientAdmission,
)
from dartlab.simulate.driverPaths import DriverCard, DriverFactorSpec, DriverHistorySource
from dartlab.simulate.driverRegistry import DriverRegistryCandidate, compileDriverRegistryPathSet
from dartlab.simulate.operatingBridge import sourceFactorContractHash
from dartlab.simulate.vintage import canonicalPayloadBytes, canonicalPayloadHash


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


def _target(
    evidenceKind: str = "observedOutcome",
    proxyRef: str = "",
    *,
    labelParentReceiptIds: tuple[str, ...] = (),
) -> DriverCalibrationTarget:
    return DriverCalibrationTarget(
        targetVariableId="realizedMarketPriceChange",
        targetShock="marketPriceChange",
        targetUnit="ratioChangePerStep",
        targetEvidenceKind=evidenceKind,
        labelProviderId="gov",
        labelDatasetId="equity.forwardReturn",
        labelSourceRefs=("label:equity-forward-return",),
        historyStatus="asKnown",
        labelParentReceiptIds=labelParentReceiptIds,
        semanticRefs=("semantics:observed-forward-equity-return",),
        targetProxyRef=proxyRef,
    )


def _spec(
    minOrigins: int = 4,
    *,
    sourceParentReceiptIds: tuple[str, ...] = (),
) -> DriverCoefficientCalibrationSpec:
    return DriverCoefficientCalibrationSpec(
        calibrationId="fx-to-price-fit",
        sourceVariableId="fxChange",
        minOrigins=minOrigins,
        sourceParentReceiptIds=sourceParentReceiptIds,
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


def _receipt(
    *,
    sourceParentReceiptIds: tuple[str, ...] = (),
    labelParentReceiptIds: tuple[str, ...] = (),
):
    return fitDriverCoefficientPit(
        _registryResult(),
        _target(labelParentReceiptIds=labelParentReceiptIds),
        _frame(),
        _spec(sourceParentReceiptIds=sourceParentReceiptIds),
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


def _oosSpec(
    minSkill: float = 0.1,
    *,
    sourceParentReceiptIds: tuple[str, ...] = (),
    labelParentReceiptIds: tuple[str, ...] = (),
) -> DriverCoefficientOosSpec:
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
        sourceParentReceiptIds=sourceParentReceiptIds,
        labelParentReceiptIds=labelParentReceiptIds,
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


def _issueParent(
    database,
    artifacts,
    privateBytes,
    trusted,
    *,
    name: str,
    knowledgeAsOf: str,
    coverageRows: tuple[dict, ...] = (),
    kind: str = "dataVintage",
    status: str = "verifiedVintage",
):
    payload = {
        "schemaVersion": PARENT_COVERAGE_VERSION,
        "name": name,
        "knowledgeAsOf": knowledgeAsOf,
        "rows": coverageRows,
    }
    artifactHash = putAdmissionArtifact(artifacts, canonicalPayloadBytes(payload))
    subjectHash = canonicalPayloadHash(payload)
    return issueAdmissionReceipt(
        database,
        artifacts,
        privateKey=privateBytes,
        kind=kind,
        subjectHash=subjectHash,
        artifactHash=artifactHash,
        parentReceiptIds=(),
        ruleId="vintage-as-known",
        ruleVersion="1",
        ruleHash="c" * 64,
        issuerId="issuer-1",
        issuerKeyId="key-1",
        issuerExecutableHash="d" * 64,
        knowledgeAsOf=knowledgeAsOf,
        revisionPolicy="asKnown",
        coverage="asOfExact",
        frequency="quarter",
        stepSpan=1,
        maxAdmittedStep=1,
        status=status,
        issuedAt="20220201T000000Z",
        trustedIssuers=trusted,
    )


def _sourceCoverageRows(frame: pl.DataFrame) -> tuple[dict, ...]:
    return tuple(
        {
            "ref": str(row["sourceRef"]),
            "role": "source",
            "variableId": "fxChange",
            "eventTime": str(row["originEventTime"]),
            "availableAt": str(row["sourceAvailableAt"]),
            "value": row["sourceValue"],
            "unit": "simpleReturn",
        }
        for row in frame.to_dicts()
    )


def _labelCoverageRows(frame: pl.DataFrame) -> tuple[dict, ...]:
    return tuple(
        {
            "ref": str(row["labelSourceRef"]),
            "role": "label",
            "variableId": "realizedMarketPriceChange",
            "eventTime": str(row["targetEventTime"]),
            "availableAt": str(row["targetAvailableAt"]),
            "value": row["targetValue"],
            "unit": "ratioChangePerStep",
        }
        for row in frame.to_dicts()
    )


def _parentReceipts(database, artifacts, privateBytes, trusted):
    fitFrame = _frame()
    oosFrame = _oosFrame()
    fitSource = _issueParent(
        database,
        artifacts,
        privateBytes,
        trusted,
        name="fit-source",
        knowledgeAsOf="20210430",
        coverageRows=_sourceCoverageRows(fitFrame),
    )
    fitLabel = _issueParent(
        database,
        artifacts,
        privateBytes,
        trusted,
        name="fit-label",
        knowledgeAsOf="20210430",
        coverageRows=_labelCoverageRows(fitFrame),
    )
    oosSource = _issueParent(
        database,
        artifacts,
        privateBytes,
        trusted,
        name="oos-source",
        knowledgeAsOf="20220131",
        coverageRows=_sourceCoverageRows(oosFrame),
    )
    oosLabel = _issueParent(
        database,
        artifacts,
        privateBytes,
        trusted,
        name="oos-label",
        knowledgeAsOf="20220131",
        coverageRows=_labelCoverageRows(oosFrame),
    )
    return fitSource, fitLabel, oosSource, oosLabel


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
    assert receipt.sourceFrequency == "quarter"
    assert receipt.sourceTiming == "change"
    assert receipt.sourceTransformId == "fx-change-quarterly-v1"
    assert receipt.sourceFactorContractHash == sourceFactorContractHash(
        variableId="fxChange",
        unit="simpleReturn",
        frequency="quarter",
        timing="change",
        transformId="fx-change-quarterly-v1",
    )
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
    database, artifacts, privateBytes, trusted, verifier = _trust(tmp_path)
    fitSource, fitLabel, oosSource, oosLabel = _parentReceipts(database, artifacts, privateBytes, trusted)
    receipt = _receipt(
        sourceParentReceiptIds=(fitSource.receiptId,),
        labelParentReceiptIds=(fitLabel.receiptId,),
    )
    report = evaluateDriverCoefficientOos(
        receipt,
        _oosFrame(),
        _oosSpec(
            sourceParentReceiptIds=(oosSource.receiptId,),
            labelParentReceiptIds=(oosLabel.receiptId,),
        ),
        evaluationKnowledgeAsOf="20220131",
    )
    assert report.status == "oosEligible"
    subject = driverCoefficientAdmissionSubjectHash(report)
    artifactHash = putAdmissionArtifact(artifacts, driverCoefficientAdmissionArtifact(report))
    assert artifactHash == subject
    missingParentSigned = issueAdmissionReceipt(
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
    with pytest.raises(DriverCalibrationError, match="contract mismatch"):
        validateDriverCoefficientAdmission(
            report,
            verifier,
            calibrationReceipt=receipt,
            receiptId=missingParentSigned.receiptId,
            decisionAsOf="20220202",
        )
    shallowRuleHash = canonicalPayloadHash({"rule": DRIVER_COEFFICIENT_RULE_ID, "version": "1"})
    assert DRIVER_COEFFICIENT_RULE_HASH != shallowRuleHash
    shallowRuleSigned = issueAdmissionReceipt(
        database,
        artifacts,
        privateKey=privateBytes,
        kind="driverCoefficient",
        subjectHash=subject,
        artifactHash=artifactHash,
        parentReceiptIds=driverCoefficientAdmissionParentReceiptIds(report),
        ruleId=DRIVER_COEFFICIENT_RULE_ID,
        ruleVersion=DRIVER_COEFFICIENT_RULE_VERSION,
        ruleHash=shallowRuleHash,
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
    with pytest.raises(DriverCalibrationError, match="contract mismatch"):
        validateDriverCoefficientAdmission(
            report,
            verifier,
            calibrationReceipt=receipt,
            receiptId=shallowRuleSigned.receiptId,
            decisionAsOf="20220202",
        )
    signed = issueAdmissionReceipt(
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
        calibrationReceipt=receipt,
        receiptId=signed.receiptId,
        decisionAsOf="20220202",
    )
    assert verified.receipt == signed
    assert verified.sourceParentReceiptIds == (fitSource.receiptId, oosSource.receiptId)
    assert verified.labelParentReceiptIds == (fitLabel.receiptId, oosLabel.receiptId)
    exposure = calibrationReceiptToOperatingExposure(
        receipt,
        exposureId="fx-price",
        oosReport=report,
        admissionReceipt=verified,
    )
    assert exposure.evidenceKind == "measuredAssociation"
    assert exposure.sourceRef == f"driverCoefficientAdmission:{signed.receiptId}"
    assert exposure.sourceFrequency == receipt.sourceFrequency
    assert exposure.sourceTiming == receipt.sourceTiming
    assert exposure.sourceTransformId == receipt.sourceTransformId
    assert exposure.sourceFactorContractHash == receipt.sourceFactorContractHash


def testDriverCoefficientAdmissionRequiresParentRowCoverage(tmp_path) -> None:
    database, artifacts, privateBytes, trusted, verifier = _trust(tmp_path)
    fitFrame = _frame()
    oosFrame = _oosFrame()
    fitSource = _issueParent(
        database,
        artifacts,
        privateBytes,
        trusted,
        name="fit-source-gap",
        knowledgeAsOf="20210430",
        coverageRows=tuple(row for row in _sourceCoverageRows(fitFrame) if row["ref"] != "source:o1"),
    )
    fitLabel = _issueParent(
        database,
        artifacts,
        privateBytes,
        trusted,
        name="fit-label",
        knowledgeAsOf="20210430",
        coverageRows=_labelCoverageRows(fitFrame),
    )
    oosSource = _issueParent(
        database,
        artifacts,
        privateBytes,
        trusted,
        name="oos-source",
        knowledgeAsOf="20220131",
        coverageRows=_sourceCoverageRows(oosFrame),
    )
    oosLabel = _issueParent(
        database,
        artifacts,
        privateBytes,
        trusted,
        name="oos-label",
        knowledgeAsOf="20220131",
        coverageRows=_labelCoverageRows(oosFrame),
    )
    receipt = _receipt(
        sourceParentReceiptIds=(fitSource.receiptId,),
        labelParentReceiptIds=(fitLabel.receiptId,),
    )
    report = evaluateDriverCoefficientOos(
        receipt,
        oosFrame,
        _oosSpec(
            sourceParentReceiptIds=(oosSource.receiptId,),
            labelParentReceiptIds=(oosLabel.receiptId,),
        ),
        evaluationKnowledgeAsOf="20220131",
    )
    subject = putAdmissionArtifact(artifacts, driverCoefficientAdmissionArtifact(report))
    signed = issueAdmissionReceipt(
        database,
        artifacts,
        privateKey=privateBytes,
        kind="driverCoefficient",
        subjectHash=subject,
        artifactHash=subject,
        parentReceiptIds=driverCoefficientAdmissionParentReceiptIds(report),
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
    with pytest.raises(DriverCalibrationError, match="fit source parent coverage missing row refs"):
        validateDriverCoefficientAdmission(
            report,
            verifier,
            calibrationReceipt=receipt,
            receiptId=signed.receiptId,
            decisionAsOf="20220202",
        )


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
    missingParents = evaluateDriverCoefficientOos(
        _receipt(),
        _oosFrame(),
        _oosSpec(),
        evaluationKnowledgeAsOf="20220131",
    )
    assert missingParents.status == "rejected"
    assert "fitSourceParentsMissing" in missingParents.reasons
    assert "oosLabelParentsMissing" in missingParents.reasons

    database, artifacts, privateBytes, trusted, verifier = _trust(tmp_path)
    fitSource, fitLabel, oosSource, oosLabel = _parentReceipts(database, artifacts, privateBytes, trusted)
    receipt = _receipt(
        sourceParentReceiptIds=(fitSource.receiptId,),
        labelParentReceiptIds=(fitLabel.receiptId,),
    )
    report = evaluateDriverCoefficientOos(
        receipt,
        _oosFrame(),
        _oosSpec(
            sourceParentReceiptIds=(oosSource.receiptId,),
            labelParentReceiptIds=(oosLabel.receiptId,),
        ),
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
    subject = putAdmissionArtifact(artifacts, driverCoefficientAdmissionArtifact(report))
    sourceOnlySigned = issueAdmissionReceipt(
        database,
        artifacts,
        privateKey=privateBytes,
        kind="driverCoefficient",
        subjectHash=subject,
        artifactHash=subject,
        parentReceiptIds=(fitSource.receiptId, oosSource.receiptId),
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
    with pytest.raises(DriverCalibrationError, match="contract mismatch"):
        validateDriverCoefficientAdmission(
            report,
            verifier,
            calibrationReceipt=receipt,
            receiptId=sourceOnlySigned.receiptId,
            decisionAsOf="20220202",
        )
    badDatabase, badArtifacts, badPrivateBytes, badTrusted, badVerifier = _trust(tmp_path / "bad-parent")
    badFitSource = _issueParent(
        badDatabase,
        badArtifacts,
        badPrivateBytes,
        badTrusted,
        name="bad-fit-source",
        knowledgeAsOf="20210430",
        kind="pathSet",
        status="admitted",
    )
    badFitLabel = _issueParent(
        badDatabase,
        badArtifacts,
        badPrivateBytes,
        badTrusted,
        name="bad-fit-label",
        knowledgeAsOf="20210430",
    )
    badOosSource = _issueParent(
        badDatabase,
        badArtifacts,
        badPrivateBytes,
        badTrusted,
        name="bad-oos-source",
        knowledgeAsOf="20220131",
    )
    badOosLabel = _issueParent(
        badDatabase,
        badArtifacts,
        badPrivateBytes,
        badTrusted,
        name="bad-oos-label",
        knowledgeAsOf="20220131",
    )
    badReceipt = _receipt(
        sourceParentReceiptIds=(badFitSource.receiptId,),
        labelParentReceiptIds=(badFitLabel.receiptId,),
    )
    badReport = evaluateDriverCoefficientOos(
        badReceipt,
        _oosFrame(),
        _oosSpec(
            sourceParentReceiptIds=(badOosSource.receiptId,),
            labelParentReceiptIds=(badOosLabel.receiptId,),
        ),
        evaluationKnowledgeAsOf="20220131",
    )
    badSubject = putAdmissionArtifact(badArtifacts, driverCoefficientAdmissionArtifact(badReport))
    badSigned = issueAdmissionReceipt(
        badDatabase,
        badArtifacts,
        privateKey=badPrivateBytes,
        kind="driverCoefficient",
        subjectHash=badSubject,
        artifactHash=badSubject,
        parentReceiptIds=driverCoefficientAdmissionParentReceiptIds(badReport),
        ruleId=DRIVER_COEFFICIENT_RULE_ID,
        ruleVersion=DRIVER_COEFFICIENT_RULE_VERSION,
        ruleHash=DRIVER_COEFFICIENT_RULE_HASH,
        issuerId="issuer-1",
        issuerKeyId="key-1",
        issuerExecutableHash="b" * 64,
        knowledgeAsOf=badReport.evaluationKnowledgeAsOf,
        revisionPolicy="asKnown",
        coverage="asOfExact",
        frequency=badReport.frequency,
        stepSpan=badReport.stepSpan,
        maxAdmittedStep=badReport.maxAdmittedStep,
        status="admitted",
        issuedAt="20220201T000000Z",
        trustedIssuers=badTrusted,
    )
    with pytest.raises(DriverCalibrationError, match="fit source parent receipt must be verified vintage"):
        validateDriverCoefficientAdmission(
            badReport,
            badVerifier,
            calibrationReceipt=badReceipt,
            receiptId=badSigned.receiptId,
            decisionAsOf="20220202",
        )
    signed = issueAdmissionReceipt(
        database,
        artifacts,
        privateKey=privateBytes,
        kind="driverCoefficient",
        subjectHash=subject,
        artifactHash=subject,
        parentReceiptIds=driverCoefficientAdmissionParentReceiptIds(report),
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
        validateDriverCoefficientAdmission(
            report,
            verifier,
            calibrationReceipt=receipt,
            receiptId=signed.receiptId,
            decisionAsOf="20220202",
        )
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
