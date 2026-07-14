from __future__ import annotations

from hashlib import sha256
from typing import Mapping

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
    DriverCalibrationTarget,
    DriverCoefficientCalibrationSpec,
    DriverCoefficientOosSpec,
    driverCoefficientAdmissionArtifact,
    driverCoefficientAdmissionParentReceiptIds,
    driverCoefficientAdmissionSubjectHash,
    evaluateDriverCoefficientOosFromObservationFrame,
    fitDriverCoefficientPitFromObservationFrame,
    validateDriverCoefficientAdmission,
)
from dartlab.simulate.driverObservationBatches import (
    DriverObservationBatchError,
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
    DriverObservationFrameError,
    buildDriverCoefficientObservationFrame,
)
from dartlab.simulate.driverPaths import DriverCard, DriverFactorSpec, DriverHistorySource, buildDriverPathSet
from dartlab.simulate.driverRegistry import DriverRegistryCandidate, compileDriverRegistryPathSet
from dartlab.simulate.stateCompiler import StateCompilerError, issueProviderObservationBatch
from dartlab.simulate.vintage import canonicalPayloadBytes


def _context(tmp_path):
    database = tmp_path / "admission.sqlite"
    artifacts = tmp_path / "artifacts"
    initializeAdmissionRegistry(database)
    private = Ed25519PrivateKey.generate()
    privateBytes = private.private_bytes_raw()
    trusted = {
        "lane-key": TrustedIssuer(
            issuerId="lane-issuer",
            issuerKeyId="lane-key",
            publicKey=private.public_key().public_bytes_raw(),
        )
    }
    verifier = AdmissionVerifier(database, artifacts, trusted)
    return database, artifacts, privateBytes, trusted, verifier


def _sourceReceipt(context, payload: dict, *, knowledgeAsOf: str):
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
        parentReceiptIds=(),
        ruleId="driver-lane-source-v1",
        ruleVersion="1",
        ruleHash=sha256(b"driver-lane-source-v1").hexdigest(),
        issuerId="lane-issuer",
        issuerKeyId="lane-key",
        issuerExecutableHash=sha256(b"driver-lane-source-issuer-v1").hexdigest(),
        knowledgeAsOf=knowledgeAsOf,
        revisionPolicy="asKnown",
        coverage="asOfExact",
        frequency="quarter",
        stepSpan=1,
        maxAdmittedStep=0,
        status="verifiedVintage",
        issuedAt=f"{knowledgeAsOf}T000000Z",
        trustedIssuers=trusted,
    )


def _sourceReceiptWithParents(
    context,
    payload: dict,
    *,
    knowledgeAsOf: str,
    parentReceiptIds: tuple[str, ...],
    frequency: str = "day",
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
        ruleId="price-derived-return-v1",
        ruleVersion="1",
        ruleHash=sha256(b"price-derived-return-v1").hexdigest(),
        issuerId="lane-issuer",
        issuerKeyId="lane-key",
        issuerExecutableHash=sha256(b"price-derived-return-issuer-v1").hexdigest(),
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


def _attachRowSourceReceipts(
    context,
    panel: pl.DataFrame,
    *,
    signalId: str,
    revisionColumn: str = "revisionId",
    availableColumn: str = "availableAt",
):
    receipts = {}
    artifactHashes = []
    knowledgeValues = []
    for row in panel.to_dicts():
        knowledgeAsOf = str(row.get("knowledgeAsOf") or row[availableColumn]).replace("-", "")[:8]
        receipt = _sourceReceipt(context, {"row": row, "signalId": signalId}, knowledgeAsOf=knowledgeAsOf)
        revisionId = str(row[revisionColumn])
        receipts[revisionId] = receipt
        artifactHashes.append(receipt.artifactHash)
        knowledgeValues.append(knowledgeAsOf)
    return (
        panel.with_columns(
            pl.Series("knowledgeAsOf", knowledgeValues),
            pl.Series("sourceArtifactHash", artifactHashes),
        ),
        receipts,
    )


def _pricePanel() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "code": ["005930", "005930", "005930", "005930"],
            "date": ["20200101", "20200102", "20200103", "20200104"],
            "availableAt": ["20200102", "20200103", "20200104", "20200105"],
            "revisionId": ["p0", "p1", "p2", "p3"],
            "close": [100.0, 110.0, 99.0, 108.9],
        }
    )


def _attachPriceSourceReceipts(context, panel: pl.DataFrame) -> tuple[pl.DataFrame, dict[str, object]]:
    receipts = {}
    artifactHashes = []
    for row in panel.to_dicts():
        receipt = _sourceReceipt(context, {"priceRow": row}, knowledgeAsOf=str(row["availableAt"]))
        receipts[str(row["revisionId"])] = receipt
        artifactHashes.append(receipt.artifactHash)
    return panel.with_columns(pl.Series("sourceArtifactHash", artifactHashes)), receipts


def _priceReturnReceipts(
    context,
    panel: pl.DataFrame,
    priceReceipts: Mapping[str, object],
    *,
    signalId: str = "equityReturnShock",
    frequency: str = "day",
    returnWindow: int = 1,
    adjustmentPolicyHash: str | None = None,
    parentOverride: tuple[str, ...] | None = None,
):
    policyHash = adjustmentPolicyHash or sha256(b"split-adjusted-close-policy-v1").hexdigest()
    receipts = {}
    rows = panel.sort("date").to_dicts()
    for index in range(returnWindow, len(rows)):
        previous = rows[index - returnWindow]
        current = rows[index]
        previousReceipt = priceReceipts[str(previous["revisionId"])]
        currentReceipt = priceReceipts[str(current["revisionId"])]
        value = float(current["close"]) / float(previous["close"]) - 1.0
        availableAt = max(str(previous["availableAt"]), str(current["availableAt"]))
        revisionId = _priceReturnRevisionId(
            previousRevisionId=str(previous["revisionId"]),
            currentRevisionId=str(current["revisionId"]),
            frequency=frequency,
            returnWindow=returnWindow,
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
            signalId=signalId,
            frequency=frequency,
            returnWindow=returnWindow,
            adjustmentPolicyHash=policyHash,
            previousLeg=previousLeg,
            currentLeg=currentLeg,
            eventAt=str(current["date"]),
            availableAt=availableAt,
            value=value,
        )
        parents = parentOverride or (previousReceipt.receiptId, currentReceipt.receiptId)
        receipts[revisionId] = _sourceReceiptWithParents(
            context,
            payload,
            knowledgeAsOf=availableAt,
            parentReceiptIds=parents,
            frequency=frequency,
        )
    return receipts, policyHash


def _panel(
    values: tuple[float, ...], events: tuple[str, ...], available: tuple[str, ...], *, column: str
) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "eventTime": list(events),
            "availableAt": list(available),
            "revisionId": [f"r{index}" for index in range(len(events))],
            column: list(values),
        }
    )


def _laneSpec(
    *,
    artifactHash: str,
    signalId: str,
    column: str,
    unit: str,
    knowledgeAsOf: str = "20220131",
    evidenceRole: str = "observed",
    sourceRefs: tuple[str, ...] = ("source:fixture",),
    knowledgeAsOfColumn: str = "",
    sourceArtifactHashColumn: str = "",
    requireAvailableAfterEvent: bool = False,
) -> DriverObservationLaneSpec:
    return DriverObservationLaneSpec(
        providerId="macro",
        datasetId="driver-lane-fixture",
        entityId="KR",
        knowledgeAsOf=knowledgeAsOf,
        eventTimeColumn="eventTime",
        availableAtColumn="availableAt",
        revisionIdColumn="revisionId",
        sourceArtifactKind="driverLaneFixture",
        sourceArtifactId=f"fixture:{signalId}",
        sourceArtifactHash=artifactHash,
        signalSpecs=(
            DriverObservationSignalSpec(
                signalId=signalId,
                sourceColumn=column,
                unit=unit,
                frequency="quarter",
                timing="ratio",
                transformId=f"{signalId}-quarterly-change-v1",
                evidenceRole=evidenceRole,
            ),
        ),
        sourceRefs=sourceRefs,
        knowledgeAsOfColumn=knowledgeAsOfColumn,
        sourceArtifactHashColumn=sourceArtifactHashColumn,
        requireAvailableAfterEvent=requireAvailableAfterEvent,
    )


def _filingPanel() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "cik": ["0000320193", "0000320193", "0000320193", "0000320193"],
            "period": ["20200331", "20200630", "20200930", "20201231"],
            "acceptedAt": ["20200501", "20200801", "20201101", "20210201"],
            "accession": ["a1", "a2", "a3", "a4"],
            "opMarginChange": [0.02, -0.01, 0.03, 0.04],
        }
    )


def _filingSignal(evidenceRole: str = "deterministicDerived") -> DriverObservationSignalSpec:
    return DriverObservationSignalSpec(
        "operatingMarginChange",
        "opMarginChange",
        "ratioChange",
        "quarter",
        "ratio",
        "edgar-operating-margin-change-v1",
        evidenceRole,
    )


def _signedBatch(
    context,
    panel: pl.DataFrame,
    *,
    signalId: str,
    column: str,
    unit: str,
    knowledgeAsOf: str = "20220131",
):
    rowPanel, sourceReceipts = _attachRowSourceReceipts(context, panel, signalId=signalId)
    laneHash = sha256(canonicalPayloadBytes({"rows": rowPanel.to_dicts(), "signalId": signalId})).hexdigest()
    batch = buildDriverObservationBatchFromPanel(
        rowPanel,
        _laneSpec(
            artifactHash=laneHash,
            signalId=signalId,
            column=column,
            unit=unit,
            knowledgeAsOf=knowledgeAsOf,
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
        issuerId="lane-issuer",
        issuerKeyId="lane-key",
        issuedAt=f"{knowledgeAsOf}T000000Z",
        trustedIssuers=trusted,
    )


def _frameSpec(frameId: str) -> DriverCoefficientObservationFrameSpec:
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


def _registryResult():
    factor = DriverFactorSpec(
        "fxChange",
        "simpleReturn",
        "quarter",
        "change",
        "fxChange-quarterly-change-v1",
    )
    card = DriverCard(
        cardId="fx-change",
        sourceKind="history",
        providerId="macro",
        datasetId="driver-lane-fixture",
        entityId="KR",
        frequency="quarter",
        stepSpan=1,
        factors=(factor,),
        historyStatus="asKnown",
        sourceRefs=("providerObservationBatch:fit-source",),
    )
    panel = pl.DataFrame(
        {
            "eventTime": ["20200331", "20200630", "20200930", "20201231"],
            "availableAt": ["20200410", "20200710", "20201010", "20210110"],
            "fxChange": [0.10, -0.20, 0.30, 0.40],
        }
    )
    return compileDriverRegistryPathSet(
        (
            DriverRegistryCandidate(
                "fx-change",
                "pathHistory",
                DriverHistorySource(card, panel),
                semanticRefs=("semantics:fx-change",),
                selectionReason="FX change is an observed driver lane.",
            ),
        ),
        registryId="driver-lane-registry",
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
        labelDatasetId="driver-lane-fixture",
        labelSourceRefs=("providerObservationBatch:fit-label",),
        historyStatus="asKnown",
        labelParentReceiptIds=labelParentReceiptIds,
    )


def _issueCoefficientAdmission(context, report):
    database, artifacts, privateBytes, trusted, _verifier = context
    subject = driverCoefficientAdmissionSubjectHash(report)
    artifactHash = putAdmissionArtifact(artifacts, driverCoefficientAdmissionArtifact(report))
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
        issuerId="lane-issuer",
        issuerKeyId="lane-key",
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


def testDriverObservationLaneBatchFeedsCoefficientAdmission(tmp_path) -> None:
    context = _context(tmp_path)
    fitSource = _signedBatch(
        context,
        _panel(
            (0.10, -0.20, 0.30, 0.40),
            ("20200331", "20200630", "20200930", "20201231"),
            ("20200410", "20200710", "20201010", "20210110"),
            column="fx",
        ),
        signalId="fxChange",
        column="fx",
        unit="simpleReturn",
        knowledgeAsOf="20210430",
    )
    fitLabel = _signedBatch(
        context,
        _panel(
            (0.05, -0.10, 0.15, 0.20),
            ("20200630", "20200930", "20201231", "20210331"),
            ("20200705", "20201005", "20210105", "20210405"),
            column="ret",
        ),
        signalId="realizedMarketPriceChange",
        column="ret",
        unit="ratioChangePerStep",
        knowledgeAsOf="20210430",
    )
    oosSource = _signedBatch(
        context,
        _panel(
            (0.20, -0.10, 0.30),
            ("20210331", "20210630", "20210930"),
            ("20210410", "20210710", "20211010"),
            column="fx",
        ),
        signalId="fxChange",
        column="fx",
        unit="simpleReturn",
    )
    oosLabel = _signedBatch(
        context,
        _panel(
            (0.10, -0.05, 0.15),
            ("20210630", "20210930", "20211231"),
            ("20210705", "20211005", "20220105"),
            column="ret",
        ),
        signalId="realizedMarketPriceChange",
        column="ret",
        unit="ratioChangePerStep",
    )
    fitFrame = buildDriverCoefficientObservationFrame(fitSource, fitLabel, _frameSpec("fit-lane-frame"))
    oosFrame = buildDriverCoefficientObservationFrame(oosSource, oosLabel, _frameSpec("oos-lane-frame"))
    receipt = fitDriverCoefficientPitFromObservationFrame(
        _registryResult(),
        _target(fitFrame.labelParentReceiptIds),
        fitFrame,
        DriverCoefficientCalibrationSpec(
            calibrationId="fx-to-price-fit",
            sourceVariableId="fxChange",
            minOrigins=4,
            sourceParentReceiptIds=fitFrame.sourceParentReceiptIds,
        ),
        calibrationKnowledgeAsOf="20210430",
    )
    report = evaluateDriverCoefficientOosFromObservationFrame(
        receipt,
        oosFrame,
        DriverCoefficientOosSpec(
            evaluationId="fx-to-price-oos",
            minOosOrigins=3,
            minSkillVsBaseline=0.1,
            maxRmse=0.01,
            maxAbsBias=0.01,
            baselineValue=0.0,
            frequency="quarter",
            stepSpan=1,
            maxAdmittedStep=1,
            sourceParentReceiptIds=oosFrame.sourceParentReceiptIds,
            labelParentReceiptIds=oosFrame.labelParentReceiptIds,
        ),
        evaluationKnowledgeAsOf="20220131",
    )
    signed = _issueCoefficientAdmission(context, report)
    verified = validateDriverCoefficientAdmission(
        report,
        context[4],
        calibrationReceipt=receipt,
        receiptId=signed.receiptId,
        decisionAsOf="20220202",
    )
    assert report.status == "oosEligible"
    assert verified.sourceParentReceiptIds == (fitSource.batchReceiptId, oosSource.batchReceiptId)


def testPriceReturnObservationBatchBuildsExactProviderBatchAndProjection(tmp_path) -> None:
    context = _context(tmp_path)
    pricePanel, priceReceipts = _attachPriceSourceReceipts(context, _pricePanel())
    returnReceipts, adjustmentPolicyHash = _priceReturnReceipts(context, pricePanel, priceReceipts)
    batch = buildPriceReturnDriverObservationBatch(
        pricePanel,
        code="005930",
        knowledgeAsOf="20200131",
        sourceReceipts=priceReceipts,
        returnReceipts=returnReceipts,
        sourceRefs=("source:gov-price-daily", "adjustment:split-adjusted-close"),
        adjustmentPolicyHash=adjustmentPolicyHash,
    )
    signedBatch = issueProviderObservationBatch(
        batch,
        context[0],
        context[1],
        privateKey=context[2],
        issuerId="lane-issuer",
        issuerKeyId="lane-key",
        issuedAt="20200131T000000Z",
        trustedIssuers=context[3],
    )
    source = driverHistorySourceFromProviderObservationBatch(
        signedBatch,
        cardId="equity-return-history",
        factors=(
            DriverFactorSpec(
                "equityReturnShock",
                "simpleReturn",
                "day",
                "innovation",
                "price-simple-return-day-1-v1",
            ),
        ),
    )
    assert signedBatch.historyStatus == "exact"
    assert signedBatch.sourceReceiptIds == tuple(sorted(receipt.receiptId for receipt in returnReceipts.values()))
    assert [item.evidenceRole for item in signedBatch.observations] == ["deterministicDerived"] * 3
    assert signedBatch.observations[0].availableAt == "20200103"
    assert (
        signedBatch.observations[0].vintage.receiptId
        == returnReceipts[
            _priceReturnRevisionId(previousRevisionId="p0", currentRevisionId="p1", frequency="day", returnWindow=1)
        ].receiptId
    )
    assert any(
        ref.startswith("equityReturnNotOperatingPrice:") for ref in signedBatch.observations[0].vintage.sourceRefs
    )
    assert source.card.historyStatus == "asKnown"
    assert source.panel["equityReturnShock"].to_list() == pytest.approx([0.10, -0.10, 0.10])
    with pytest.raises(DriverObservationBatchError, match="meaning drift"):
        driverHistorySourceFromProviderObservationBatch(
            signedBatch,
            cardId="bad-equity-return-history",
            factors=(
                DriverFactorSpec(
                    "equityReturnShock",
                    "simpleReturn",
                    "day",
                    "level",
                    "price-simple-return-day-1-v1",
                ),
            ),
        )


def testPriceReturnObservationBatchBuildsQuarterlyExactReturns(tmp_path) -> None:
    context = _context(tmp_path)
    rawPanel = pl.DataFrame(
        {
            "code": ["005930", "005930", "005930", "005930"],
            "date": ["20200331", "20200630", "20200930", "20201231"],
            "availableAt": ["20200415", "20200715", "20201015", "20210115"],
            "revisionId": ["q0", "q1", "q2", "q3"],
            "close": [100.0, 110.0, 99.0, 118.8],
        }
    )
    pricePanel, priceReceipts = _attachPriceSourceReceipts(context, rawPanel)
    returnReceipts, adjustmentPolicyHash = _priceReturnReceipts(
        context,
        pricePanel,
        priceReceipts,
        frequency="quarter",
    )
    batch = buildPriceReturnDriverObservationBatch(
        pricePanel,
        code="005930",
        knowledgeAsOf="20210131",
        sourceReceipts=priceReceipts,
        returnReceipts=returnReceipts,
        sourceRefs=("source:gov-price-quarterly", "adjustment:split-adjusted-close"),
        frequency="quarter",
        adjustmentPolicyHash=adjustmentPolicyHash,
    )
    signedBatch = issueProviderObservationBatch(
        batch,
        context[0],
        context[1],
        privateKey=context[2],
        issuerId="lane-issuer",
        issuerKeyId="lane-key",
        issuedAt="20210131T000000Z",
        trustedIssuers=context[3],
    )
    source = driverHistorySourceFromProviderObservationBatch(
        signedBatch,
        cardId="quarterly-equity-return-history",
        factors=(
            DriverFactorSpec(
                "equityReturnShock",
                "simpleReturn",
                "quarter",
                "innovation",
                "price-simple-return-quarter-1-v1",
            ),
        ),
    )
    assert signedBatch.historyStatus == "exact"
    assert [observation.eventAt for observation in signedBatch.observations] == [
        "20200630",
        "20200930",
        "20201231",
    ]
    assert source.card.frequency == "quarter"
    assert source.panel["equityReturnShock"].to_list() == pytest.approx([0.10, -0.10, 0.20])


def testPriceReturnObservationBatchBindsBothPriceLegsAndDerivedArtifact(tmp_path) -> None:
    context = _context(tmp_path)
    pricePanel, priceReceipts = _attachPriceSourceReceipts(context, _pricePanel())
    wrongParents = (priceReceipts["p1"].receiptId,)
    badReturnReceipts, adjustmentPolicyHash = _priceReturnReceipts(
        context,
        pricePanel,
        priceReceipts,
        parentOverride=wrongParents,
    )
    with pytest.raises(DriverObservationBatchError, match="bind both price legs"):
        buildPriceReturnDriverObservationBatch(
            pricePanel,
            code="005930",
            knowledgeAsOf="20200131",
            sourceReceipts=priceReceipts,
            returnReceipts=badReturnReceipts,
            sourceRefs=("source:gov-price-daily",),
            adjustmentPolicyHash=adjustmentPolicyHash,
        )
    returnReceipts, adjustmentPolicyHash = _priceReturnReceipts(context, pricePanel, priceReceipts)
    tamperedClose = pricePanel.with_columns(
        pl.when(pl.col("revisionId") == "p0").then(90.0).otherwise(pl.col("close")).alias("close")
    )
    with pytest.raises(DriverObservationBatchError, match="derived return receipt"):
        buildPriceReturnDriverObservationBatch(
            tamperedClose,
            code="005930",
            knowledgeAsOf="20200131",
            sourceReceipts=priceReceipts,
            returnReceipts=returnReceipts,
            sourceRefs=("source:gov-price-daily",),
            adjustmentPolicyHash=adjustmentPolicyHash,
        )


def testPriceReturnObservationBatchRejectsUnsafeExactInputs(tmp_path) -> None:
    context = _context(tmp_path)
    pricePanel, priceReceipts = _attachPriceSourceReceipts(context, _pricePanel())
    returnReceipts, adjustmentPolicyHash = _priceReturnReceipts(context, pricePanel, priceReceipts)
    with pytest.raises(DriverObservationBatchError, match="operating shock"):
        buildPriceReturnDriverObservationBatch(
            pricePanel,
            code="005930",
            knowledgeAsOf="20200131",
            sourceReceipts=priceReceipts,
            returnReceipts=returnReceipts,
            sourceRefs=("source:gov-price-daily",),
            signalId="marketPriceChange",
            adjustmentPolicyHash=adjustmentPolicyHash,
        )
    with pytest.raises(DriverObservationBatchError, match="explicit availability"):
        buildPriceReturnDriverObservationBatch(
            pricePanel,
            code="005930",
            knowledgeAsOf="20200131",
            sourceReceipts=priceReceipts,
            returnReceipts=returnReceipts,
            sourceRefs=("source:gov-price-daily",),
            availableAtColumn="",
            adjustmentPolicyHash=adjustmentPolicyHash,
        )
    duplicateDate = pl.concat([pricePanel, pricePanel.head(1)])
    with pytest.raises(DriverObservationBatchError, match="duplicate price dates"):
        buildPriceReturnDriverObservationBatch(
            duplicateDate,
            code="005930",
            knowledgeAsOf="20200131",
            sourceReceipts=priceReceipts,
            returnReceipts=returnReceipts,
            sourceRefs=("source:gov-price-daily",),
            adjustmentPolicyHash=adjustmentPolicyHash,
        )
    badClose = pricePanel.with_columns(
        pl.when(pl.col("revisionId") == "p1").then(0.0).otherwise(pl.col("close")).alias("close")
    )
    with pytest.raises(DriverObservationBatchError, match="positive close"):
        buildPriceReturnDriverObservationBatch(
            badClose,
            code="005930",
            knowledgeAsOf="20200131",
            sourceReceipts=priceReceipts,
            returnReceipts=returnReceipts,
            sourceRefs=("source:gov-price-daily",),
            adjustmentPolicyHash=adjustmentPolicyHash,
        )
    with pytest.raises(DriverObservationBatchError, match="derived return receipts"):
        buildPriceReturnDriverObservationBatch(
            pricePanel,
            code="005930",
            knowledgeAsOf="20200131",
            sourceReceipts=priceReceipts,
            returnReceipts={},
            sourceRefs=("source:gov-price-daily",),
            adjustmentPolicyHash=adjustmentPolicyHash,
        )


def testPriceReturnObservationBatchCanServeAsDeterministicForwardLabel(tmp_path) -> None:
    context = _context(tmp_path)
    pricePanel, priceReceipts = _attachPriceSourceReceipts(context, _pricePanel())
    returnReceipts, adjustmentPolicyHash = _priceReturnReceipts(context, pricePanel, priceReceipts)
    batch = buildPriceReturnDriverObservationBatch(
        pricePanel,
        code="005930",
        knowledgeAsOf="20200131",
        sourceReceipts=priceReceipts,
        returnReceipts=returnReceipts,
        sourceRefs=("source:gov-price-daily",),
        adjustmentPolicyHash=adjustmentPolicyHash,
    )
    signedBatch = issueProviderObservationBatch(
        batch,
        context[0],
        context[1],
        privateKey=context[2],
        issuerId="lane-issuer",
        issuerKeyId="lane-key",
        issuedAt="20200131T000000Z",
        trustedIssuers=context[3],
    )
    observedOnly = DriverCoefficientObservationFrameSpec(
        frameId="price-forward-return-observed-only",
        sourceSignalId="equityReturnShock",
        labelSignalId="equityReturnShock",
        sourceVariableId="equityReturnShock",
        targetVariableId="realizedEquityReturn",
        sourceUnit="simpleReturn",
        targetUnit="simpleReturn",
        frequency="day",
        stepSpan=1,
        horizonSteps=1,
        originThrough="20200103",
    )
    with pytest.raises(DriverObservationFrameError, match="evidence role"):
        buildDriverCoefficientObservationFrame(signedBatch, signedBatch, observedOnly)
    deterministicLabel = DriverCoefficientObservationFrameSpec(
        frameId="price-forward-return-deterministic-label",
        sourceSignalId="equityReturnShock",
        labelSignalId="equityReturnShock",
        sourceVariableId="equityReturnShock",
        targetVariableId="realizedEquityReturn",
        sourceUnit="simpleReturn",
        targetUnit="simpleReturn",
        frequency="day",
        stepSpan=1,
        horizonSteps=1,
        originThrough="20200103",
        labelEvidenceRoles=("deterministicDerived",),
    )
    frame = buildDriverCoefficientObservationFrame(signedBatch, signedBatch, deterministicLabel)
    assert frame.rowCount == 2
    assert frame.labelParentReceiptIds == (signedBatch.batchReceiptId,)


def testFilingMetricObservationBatchBuildsExactProviderBatchAndProjection(tmp_path) -> None:
    context = _context(tmp_path)
    panel, sourceReceipts = _attachRowSourceReceipts(
        context,
        _filingPanel(),
        signalId="operatingMarginChange",
        revisionColumn="accession",
        availableColumn="acceptedAt",
    )
    laneHash = sha256(
        canonicalPayloadBytes({"rows": panel.to_dicts(), "signalId": "operatingMarginChange"})
    ).hexdigest()
    batch = buildFilingMetricDriverObservationBatch(
        panel,
        providerId="edgar",
        datasetId="edgar.companyfacts.metric",
        entityId="0000320193",
        knowledgeAsOf="20210430",
        eventTimeColumn="period",
        availableAtColumn="acceptedAt",
        filingIdColumn="accession",
        entityIdColumn="cik",
        sourceArtifactKind="edgarFilingMetricRows",
        sourceArtifactId="0000320193:operatingMarginChange",
        sourceArtifactHash=laneHash,
        signalSpecs=(_filingSignal(),),
        sourceRefs=("source:edgar-companyfacts",),
        sourceArtifactHashColumn="sourceArtifactHash",
        sourceReceipts=sourceReceipts,
        requireExact=True,
    )
    signedBatch = issueProviderObservationBatch(
        batch,
        context[0],
        context[1],
        privateKey=context[2],
        issuerId="lane-issuer",
        issuerKeyId="lane-key",
        issuedAt="20210430T000000Z",
        trustedIssuers=context[3],
    )
    source = driverHistorySourceFromProviderObservationBatch(
        signedBatch,
        cardId="edgar-operating-margin-change-history",
        factors=(
            DriverFactorSpec(
                "operatingMarginChange",
                "ratioChange",
                "quarter",
                "change",
                "edgar-operating-margin-change-v1",
            ),
        ),
    )
    assert signedBatch.historyStatus == "exact"
    assert signedBatch.sourceReceiptIds == tuple(sorted(receipt.receiptId for receipt in sourceReceipts.values()))
    assert all(observation.vintage.fiscalThrough == observation.eventAt for observation in signedBatch.observations)
    assert source.card.historyStatus == "asKnown"
    assert source.panel["operatingMarginChange"].to_list() == [0.02, -0.01, 0.03, 0.04]


def testFilingMetricObservationBatchRejectsLaunderingAndMissingPit(tmp_path) -> None:
    _context(tmp_path)
    panel = _filingPanel()
    laneHash = sha256(b"filing-lane").hexdigest()
    with pytest.raises(DriverObservationBatchError, match="row knowledgeAsOf"):
        buildFilingMetricDriverObservationBatch(
            panel,
            providerId="edgar",
            datasetId="edgar.companyfacts.metric",
            entityId="0000320193",
            knowledgeAsOf="20210430",
            eventTimeColumn="period",
            availableAtColumn="acceptedAt",
            filingIdColumn="accession",
            sourceArtifactKind="edgarFilingMetricRows",
            sourceArtifactId="0000320193:operatingMarginChange",
            sourceArtifactHash=laneHash,
            signalSpecs=(_filingSignal(),),
            sourceRefs=("source:edgar-companyfacts",),
        )
    panelWithKnowledge = panel.with_columns(pl.col("acceptedAt").alias("knowledgeAsOf"))
    with pytest.raises(DriverObservationBatchError, match="deterministicDerived"):
        buildFilingMetricDriverObservationBatch(
            panelWithKnowledge,
            providerId="edgar",
            datasetId="edgar.companyfacts.metric",
            entityId="0000320193",
            knowledgeAsOf="20210430",
            eventTimeColumn="period",
            availableAtColumn="acceptedAt",
            filingIdColumn="accession",
            sourceArtifactKind="edgarFilingMetricRows",
            sourceArtifactId="0000320193:operatingMarginChange",
            sourceArtifactHash=laneHash,
            signalSpecs=(_filingSignal("observed"),),
            sourceRefs=("source:edgar-companyfacts",),
        )
    panelWithHash = panelWithKnowledge.with_columns(pl.lit(laneHash).alias("sourceArtifactHash"))
    with pytest.raises(DriverObservationBatchError, match="row source receipts"):
        buildFilingMetricDriverObservationBatch(
            panelWithHash,
            providerId="edgar",
            datasetId="edgar.companyfacts.metric",
            entityId="0000320193",
            knowledgeAsOf="20210430",
            eventTimeColumn="period",
            availableAtColumn="acceptedAt",
            filingIdColumn="accession",
            sourceArtifactKind="edgarFilingMetricRows",
            sourceArtifactId="0000320193:operatingMarginChange",
            sourceArtifactHash=laneHash,
            signalSpecs=(_filingSignal(),),
            sourceRefs=("source:edgar-companyfacts",),
            requireExact=True,
        )
    badTiming = panelWithKnowledge.with_columns(pl.col("period").alias("acceptedAt"))
    with pytest.raises(DriverObservationBatchError, match="availability must be after event"):
        buildFilingMetricDriverObservationBatch(
            badTiming,
            providerId="edgar",
            datasetId="edgar.companyfacts.metric",
            entityId="0000320193",
            knowledgeAsOf="20210430",
            eventTimeColumn="period",
            availableAtColumn="acceptedAt",
            filingIdColumn="accession",
            sourceArtifactKind="edgarFilingMetricRows",
            sourceArtifactId="0000320193:operatingMarginChange",
            sourceArtifactHash=laneHash,
            signalSpecs=(_filingSignal(),),
            sourceRefs=("source:edgar-companyfacts",),
        )
    with pytest.raises(DriverObservationBatchError, match="provider must be dart or edgar"):
        buildFilingMetricDriverObservationBatch(
            panelWithKnowledge,
            providerId="macro",
            datasetId="macro.metric",
            entityId="KR",
            knowledgeAsOf="20210430",
            eventTimeColumn="period",
            availableAtColumn="acceptedAt",
            filingIdColumn="accession",
            sourceArtifactKind="macroRows",
            sourceArtifactId="KR:metric",
            sourceArtifactHash=laneHash,
            signalSpecs=(_filingSignal(),),
            sourceRefs=("source:macro",),
        )


def testConditionalFilingMetricObservationBatchCannotIssueExactBatch(tmp_path) -> None:
    context = _context(tmp_path)
    panel = _filingPanel().with_columns(pl.col("acceptedAt").alias("knowledgeAsOf"))
    laneHash = sha256(b"conditional-filing-lane").hexdigest()
    batch = buildFilingMetricDriverObservationBatch(
        panel,
        providerId="dart",
        datasetId="dart.retained.metric",
        entityId="005930",
        knowledgeAsOf="20210430",
        eventTimeColumn="period",
        availableAtColumn="acceptedAt",
        filingIdColumn="accession",
        sourceArtifactKind="dartRetainedFilingMetricRows",
        sourceArtifactId="005930:operatingMarginChange",
        sourceArtifactHash=laneHash,
        signalSpecs=(_filingSignal("deterministicDerived"),),
        sourceRefs=("source:dart-retained-finance",),
    )
    assert batch.historyStatus == "conditional"
    with pytest.raises(StateCompilerError, match="exact provider batch"):
        issueProviderObservationBatch(
            batch,
            context[0],
            context[1],
            privateKey=context[2],
            issuerId="lane-issuer",
            issuerKeyId="lane-key",
            issuedAt="20210430T000000Z",
            trustedIssuers=context[3],
        )


def testConditionalDriverObservationLaneCannotIssueExactBatch(tmp_path) -> None:
    context = _context(tmp_path)
    panel = _panel((0.10, 0.20), ("20200331", "20200630"), ("20200410", "20200710"), column="fx")
    artifactHash = sha256(b"conditional").hexdigest()
    batch = buildDriverObservationBatchFromPanel(
        panel,
        _laneSpec(artifactHash=artifactHash, signalId="fxChange", column="fx", unit="simpleReturn"),
    )
    assert batch.historyStatus == "conditional"
    with pytest.raises(StateCompilerError, match="exact provider batch"):
        issueProviderObservationBatch(
            batch,
            context[0],
            context[1],
            privateKey=context[2],
            issuerId="lane-issuer",
            issuerKeyId="lane-key",
            issuedAt="20220131T000000Z",
            trustedIssuers=context[3],
        )


def testDriverObservationLaneRejectsHistorySourcePromotionAndUnsafeInputs(tmp_path) -> None:
    context = _context(tmp_path)
    panel = _panel((0.10, 0.20), ("20200331", "20200630"), ("20200410", "20200710"), column="fx")
    receipt = _sourceReceipt(context, {"rows": panel.to_dicts()}, knowledgeAsOf="20220131")
    spec = _laneSpec(artifactHash=receipt.artifactHash, signalId="fxChange", column="fx", unit="simpleReturn")
    historySource = DriverHistorySource(
        DriverCard(
            "unsafe-history",
            "history",
            "macro",
            "driver-lane-fixture",
            "KR",
            "quarter",
            1,
            (DriverFactorSpec("fxChange", "simpleReturn", "quarter", "change", "fxChange-quarterly-change-v1"),),
            "asKnown",
            ("historyOnly",),
        ),
        pl.DataFrame({"eventTime": ["20200331"], "availableAt": ["20200410"], "fxChange": [0.1]}),
    )
    with pytest.raises(DriverObservationBatchError, match="cannot be promoted"):
        buildDriverObservationBatchFromPanel(historySource, spec, sourceReceipt=receipt, requireExact=True)
    with pytest.raises(DriverObservationBatchError, match="source dataVintage receipt"):
        buildDriverObservationBatchFromPanel(panel, spec, requireExact=True)
    badEvidence = _laneSpec(
        artifactHash=receipt.artifactHash,
        signalId="fxChange",
        column="fx",
        unit="simpleReturn",
        evidenceRole="explicitAssumption",
    )
    with pytest.raises(DriverObservationBatchError, match="signal contract"):
        buildDriverObservationBatchFromPanel(panel, badEvidence, sourceReceipt=receipt, requireExact=True)
    duplicatePanel = pl.concat([panel, panel.head(1)])
    with pytest.raises(DriverObservationBatchError, match="duplicate event"):
        buildDriverObservationBatchFromPanel(duplicatePanel, spec, sourceReceipt=receipt, requireExact=True)


def testDriverObservationLaneKeepsFilingAvailabilityBoundary(tmp_path) -> None:
    context = _context(tmp_path)
    panel = pl.DataFrame(
        {
            "period": ["20200331", "20200630"],
            "rceptDate": ["20200331", "20200814"],
            "rceptNo": ["202005150001", "202008140001"],
            "margin": [0.10, 0.20],
        }
    )
    receipt = _sourceReceipt(context, {"rows": panel.to_dicts()}, knowledgeAsOf="20220131")
    filingSpec = DriverObservationLaneSpec(
        providerId="dart",
        datasetId="retained-finance",
        entityId="005930",
        knowledgeAsOf="20220131",
        eventTimeColumn="period",
        availableAtColumn="rceptDate",
        revisionIdColumn="rceptNo",
        sourceArtifactKind="dartRetainedFinanceRows",
        sourceArtifactId="005930",
        sourceArtifactHash=receipt.artifactHash,
        signalSpecs=(
            DriverObservationSignalSpec(
                "operatingMarginChange",
                "margin",
                "ratioChange",
                "quarter",
                "ratio",
                "dart-operating-margin-change-v1",
                "deterministicDerived",
            ),
        ),
        sourceRefs=("rceptNo",),
        eventDateRole="fiscalThrough",
        requireAvailableAfterEvent=True,
    )
    with pytest.raises(DriverObservationBatchError, match="availability must be after event"):
        buildDriverObservationBatchFromPanel(panel, filingSpec, sourceReceipt=receipt, requireExact=True)
    with pytest.raises(DriverObservationBatchError, match="separate event"):
        buildDriverObservationBatchFromPanel(
            panel,
            DriverObservationLaneSpec(
                **{
                    **{name: getattr(filingSpec, name) for name in filingSpec.__dataclass_fields__},
                    "availableAtColumn": "period",
                }
            ),
            sourceReceipt=receipt,
            requireExact=True,
        )


def testProviderObservationBatchProjectsToDriverHistorySource(tmp_path) -> None:
    context = _context(tmp_path)
    panel = _panel(
        (0.10, -0.20, 0.30, 0.40),
        ("20200331", "20200630", "20200930", "20201231"),
        ("20200410", "20200710", "20201010", "20210110"),
        column="fx",
    )
    signedBatch = _signedBatch(context, panel, signalId="fxChange", column="fx", unit="simpleReturn")
    source = driverHistorySourceFromProviderObservationBatch(
        signedBatch,
        cardId="fx-change-history",
        factors=(DriverFactorSpec("fxChange", "simpleReturn", "quarter", "change", "fxChange-quarterly-change-v1"),),
    )
    assert source.card.historyStatus == "asKnown"
    assert source.panel["fxChange"].to_list() == [0.10, -0.20, 0.30, 0.40]
    pathSet = buildDriverPathSet(
        (source,),
        knowledgeAsOf="20220131",
        horizon=2,
        pathCount=2,
        blockLength=1,
        seed=3,
        minObservations=4,
    )
    assert pathSet.audit.historyStatus == "asKnown"
    assert pathSet.audit.validationStatus == "retrospectiveOnly"
