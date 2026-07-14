from __future__ import annotations

from datetime import date, timedelta
from hashlib import sha256
from pathlib import Path

import polars as pl
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from dartlab.simulate.admissionRegistry import (
    AdmissionVerifier,
    TrustedIssuer,
    initializeAdmissionRegistry,
)
from dartlab.simulate.filingStateAdapters import (
    FilingStateAdapterError,
    buildDartRetainedFinanceVintage,
    buildEdgarQuarterlyFinancialObservationBatch,
    buildEdgarQuarterlyFinancialSourceArtifact,
    buildEdgarQuarterlyFinancialStateRegistry,
    issueEdgarQuarterlyFinancialSource,
)
from dartlab.simulate.stateCompiler import (
    StateCompilerError,
    StateCompileSpec,
    buildProviderObservationBatch,
    compilePointInTimeState,
    issueProviderObservationBatch,
    makeVariableObservation,
)


def _context(tmp_path):
    registry = tmp_path / "admission.sqlite"
    artifacts = tmp_path / "artifacts"
    initializeAdmissionRegistry(registry)
    private = Ed25519PrivateKey.generate()
    privateBytes = private.private_bytes_raw()
    trusted = {
        "source-key": TrustedIssuer(
            issuerId="source-issuer",
            issuerKeyId="source-key",
            publicKey=private.public_key().public_bytes_raw(),
        )
    }
    return registry, artifacts, privateBytes, trusted


def _filing(accn: str, filed: str, fiscalEnd: str, scale: float = 1.0) -> pl.DataFrame:
    stock = {
        "CashAndCashEquivalentsAtCarryingValue": 10.0,
        "AccountsReceivableNetCurrent": 20.0,
        "InventoryNet": 5.0,
        "AccountsPayableCurrent": 15.0,
        "PropertyPlantAndEquipmentGross": 80.0,
        "PropertyPlantAndEquipmentNet": 30.0,
        "Assets": 100.0,
        "Liabilities": 60.0,
        "StockholdersEquity": 40.0,
        "LongTermDebtCurrent": 8.0,
        "LongTermDebtNoncurrent": 12.0,
        "LongTermDebt": 20.0,
    }
    rows = [
        {
            "namespace": "us-gaap",
            "tag": tag,
            "unit": "USD",
            "val": value * scale,
            "form": "10-Q",
            "filed": filed,
            "start": None,
            "end": fiscalEnd,
            "accn": accn,
        }
        for tag, value in stock.items()
    ]
    end = date.fromisoformat(fiscalEnd)
    for lag in range(3, -1, -1):
        qEnd = end - timedelta(days=91 * lag)
        qStart = qEnd - timedelta(days=89)
        for tag, value in (
            ("RevenueFromContractWithCustomerExcludingAssessedTax", 100.0),
            ("OperatingIncomeLoss", 20.0),
        ):
            rows.append(
                {
                    "namespace": "us-gaap",
                    "tag": tag,
                    "unit": "USD",
                    "val": value * scale,
                    "form": "10-Q",
                    "filed": filed,
                    "start": qStart.isoformat(),
                    "end": qEnd.isoformat(),
                    "accn": accn,
                }
            )
    return pl.DataFrame(rows)


def _compileSpec(decisionAsOf: str = "20250201", *, requireExact: bool = False) -> StateCompileSpec:
    return StateCompileSpec(
        entityId="AAPL",
        market="US",
        decisionAsOf=decisionAsOf,
        consumerId="quarterly-operating-world",
        consumerVersion="1",
        variableIds=tuple(item.variableId for item in buildEdgarQuarterlyFinancialStateRegistry().specs),
        requireExact=requireExact,
    )


def testEdgarSourceArtifactIgnoresFutureRowsAtPastCutoff() -> None:
    original = _filing("original", "2025-01-30", "2024-12-31")
    amendment = _filing("amendment", "2025-03-15", "2024-12-31", scale=1.1)
    before = buildEdgarQuarterlyFinancialSourceArtifact(original, entityId="AAPL", knowledgeAsOf="20250201")
    withFuture = buildEdgarQuarterlyFinancialSourceArtifact(
        pl.concat([original, amendment]),
        entityId="AAPL",
        knowledgeAsOf="20250201",
    )
    after = buildEdgarQuarterlyFinancialSourceArtifact(
        pl.concat([original, amendment]),
        entityId="AAPL",
        knowledgeAsOf="20250401",
    )
    assert before.artifactHash == withFuture.artifactHash
    assert before.artifactHash != after.artifactHash


def testEdgarAdapterMapsFinancialStateMeaning() -> None:
    result = buildEdgarQuarterlyFinancialObservationBatch(
        _filing("original", "2025-01-30", "2024-12-31"),
        entityId="AAPL",
        decisionAsOf="20250201",
    )
    specs = {item.variableId: item for item in buildEdgarQuarterlyFinancialStateRegistry().specs}
    observations = {item.signalId: item for item in result.batch.observations}
    assert set(observations) == set(specs)
    assert observations["financial.revenue"].evidenceRole == "deterministicDerived"
    assert observations["financial.operatingMargin"].evidenceRole == "deterministicDerived"
    assert observations["financial.debt"].evidenceRole == "deterministicDerived"
    assert observations["financial.revenue"].value == 100.0
    assert observations["financial.operatingMargin"].value == pytest.approx(0.2)
    assert observations["financial.revenue"].availableAt == "20250130"
    assert result.batch.historyStatus == "conditional"


def testEdgarExactSourceReceiptIssuesProviderBatchAndPitState(tmp_path) -> None:
    context = _context(tmp_path)
    registryPath, artifacts, privateBytes, trusted = context
    facts = _filing("original", "2025-01-30", "2024-12-31")
    unsigned = buildEdgarQuarterlyFinancialObservationBatch(facts, entityId="AAPL", decisionAsOf="20250201")
    sourceReceipt = issueEdgarQuarterlyFinancialSource(
        unsigned.sourceArtifact,
        registryPath,
        artifacts,
        privateKey=privateBytes,
        issuerId="source-issuer",
        issuerKeyId="source-key",
        issuedAt="20250201T000000Z",
        trustedIssuers=trusted,
    )
    exact = buildEdgarQuarterlyFinancialObservationBatch(
        facts,
        entityId="AAPL",
        decisionAsOf="20250201",
        sourceReceipt=sourceReceipt,
    )
    signedBatch = issueProviderObservationBatch(
        exact.batch,
        registryPath,
        artifacts,
        privateKey=privateBytes,
        issuerId="source-issuer",
        issuerKeyId="source-key",
        issuedAt="20250201T000000Z",
        trustedIssuers=trusted,
    )
    verifier = AdmissionVerifier(registryPath, artifacts, trusted)
    compiled = compilePointInTimeState(
        buildEdgarQuarterlyFinancialStateRegistry(),
        (signedBatch,),
        _compileSpec(requireExact=True),
        admissionVerifier=verifier,
    )
    assert compiled.historyStatus == "exact"
    values = {item.variableId: item.value for item in compiled.statePrimitives}
    assert values["financial.revenue"] == 100.0
    assert values["financial.cash"] == 10.0


def testEdgarSameDayFilingCannotBecomeExactEvenWithSourceReceipt(tmp_path) -> None:
    context = _context(tmp_path)
    registryPath, artifacts, privateBytes, trusted = context
    facts = _filing("original", "2025-01-30", "2024-12-31")
    unsigned = buildEdgarQuarterlyFinancialObservationBatch(facts, entityId="AAPL", decisionAsOf="20250130")
    sourceReceipt = issueEdgarQuarterlyFinancialSource(
        unsigned.sourceArtifact,
        registryPath,
        artifacts,
        privateKey=privateBytes,
        issuerId="source-issuer",
        issuerKeyId="source-key",
        issuedAt="20250130T000000Z",
        trustedIssuers=trusted,
    )
    exactBatch = buildEdgarQuarterlyFinancialObservationBatch(
        facts,
        entityId="AAPL",
        decisionAsOf="20250130",
        sourceReceipt=sourceReceipt,
    ).batch
    signedBatch = issueProviderObservationBatch(
        exactBatch,
        registryPath,
        artifacts,
        privateKey=privateBytes,
        issuerId="source-issuer",
        issuerKeyId="source-key",
        issuedAt="20250130T000000Z",
        trustedIssuers=trusted,
    )
    verifier = AdmissionVerifier(registryPath, artifacts, trusted)
    with pytest.raises(StateCompilerError, match="requires exact"):
        compilePointInTimeState(
            buildEdgarQuarterlyFinancialStateRegistry(),
            (signedBatch,),
            _compileSpec("20250130", requireExact=True),
            admissionVerifier=verifier,
        )


def testMismatchedEdgarSourceReceiptIsRejectedBeforeBatchBuild(tmp_path) -> None:
    context = _context(tmp_path)
    registryPath, artifacts, privateBytes, trusted = context
    original = _filing("original", "2025-01-30", "2024-12-31")
    changed = _filing("changed", "2025-01-30", "2024-12-31", scale=1.1)
    source = buildEdgarQuarterlyFinancialObservationBatch(original, entityId="AAPL", decisionAsOf="20250201")
    receipt = issueEdgarQuarterlyFinancialSource(
        source.sourceArtifact,
        registryPath,
        artifacts,
        privateKey=privateBytes,
        issuerId="source-issuer",
        issuerKeyId="source-key",
        issuedAt="20250201T000000Z",
        trustedIssuers=trusted,
    )
    with pytest.raises(FilingStateAdapterError, match="does not match"):
        buildEdgarQuarterlyFinancialObservationBatch(
            changed,
            entityId="AAPL",
            decisionAsOf="20250201",
            sourceReceipt=receipt,
        )


def testDartRetainedFinanceVintageCannotIssueExactBatch(tmp_path) -> None:
    context = _context(tmp_path)
    registryPath, artifacts, privateBytes, trusted = context
    artifactHash = sha256(b"retained").hexdigest()
    vintage = buildDartRetainedFinanceVintage(
        entityId="005930",
        artifactHash=artifactHash,
        knowledgeAsOf="20250515",
        fiscalThrough="20250331",
        sourceRefs=("rcept_no:20250515000001",),
    )
    observation = makeVariableObservation(
        providerId="dart",
        datasetId="retained-finance",
        entityId="005930",
        signalId="financial.revenue",
        value=100.0,
        unit="KRW",
        frequency="quarter",
        timing="flow",
        transformId="level-v1",
        evidenceRole="observed",
        eventAt="20250331",
        availableAt="20250515",
        knowledgeAsOf="20250515",
        availabilityPrecision="date",
        revisionId="20250515000001",
        vintage=vintage,
        normalizationRuleHash=sha256(b"dart-retained-finance-v1").hexdigest(),
    )
    batch = buildProviderObservationBatch(
        (observation,),
        providerId="dart",
        datasetId="retained-finance",
        entityId="005930",
        signalIds=("financial.revenue",),
        cutoffAsOf="20250516",
    )
    assert batch.historyStatus == "conditional"
    with pytest.raises(StateCompilerError, match="exact provider batch"):
        issueProviderObservationBatch(
            batch,
            registryPath,
            artifacts,
            privateKey=privateBytes,
            issuerId="source-issuer",
            issuerKeyId="source-key",
            issuedAt="20250516T000000Z",
            trustedIssuers=trusted,
        )


def testDartRetainedFinanceVintageContractIsFixedConditional() -> None:
    vintage = buildDartRetainedFinanceVintage(
        entityId="005930",
        artifactHash=sha256(b"retained").hexdigest(),
        knowledgeAsOf="20250515",
    )
    assert vintage.revisionPolicy == "latestRetained"
    assert vintage.coverage == "periodOnly"
    assert vintage.receiptId == ""
    assert len(vintage.contractHash) == 64


def testRealAaplAdapterBuildsQuarterlyStateWhenStoreIsInstalled() -> None:
    path = Path("data/edgar/finance/0000320193.parquet")
    if not path.exists():
        pytest.skip("AAPL companyfacts store is not installed")
    result = buildEdgarQuarterlyFinancialObservationBatch(
        pl.read_parquet(path),
        entityId="AAPL",
        decisionAsOf="20260713",
    )
    observations = {item.signalId: item for item in result.batch.observations}
    assert result.compiled.fiscalThrough == "20260328"
    assert observations["financial.revenue"].value == 111_184_000_000.0
    assert observations["financial.cash"].value == 45_572_000_000.0
    assert observations["financial.revenue"].availableAt <= "20260713"
    assert result.sourceArtifact.rowCount > len(result.compiled.evidence)
