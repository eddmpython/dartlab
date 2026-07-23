"""Provider filing facts to point-in-time state adapter contracts."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from hashlib import sha256
from pathlib import Path
from typing import Mapping

import polars as pl

from dartlab.analysis.financial.filingFeatures import (
    EDGAR_FINANCIAL_FEATURE_MAPPINGS as _FINANCIAL_STATE_VARIABLES,
)
from dartlab.analysis.financial.filingFeatures import (
    EDGAR_FINANCIAL_FEATURE_NORMALIZATION_HASH,
)
from dartlab.simulate.admissionRegistry import (
    AdmissionReceipt,
    TrustedIssuer,
    issueAdmissionReceipt,
    putAdmissionArtifact,
)
from dartlab.simulate.edgarPitState import (
    CompiledQuarterlyFinancialState,
    EdgarStateError,
    compileEdgarQuarterlyFinancialState,
)
from dartlab.simulate.stateCompiler import (
    ProviderObservationBatch,
    buildProviderObservationBatch,
    makeVariableObservation,
)
from dartlab.simulate.stateVariables import StateVariableRegistry, StateVariableSpec, buildStateVariableRegistry
from dartlab.simulate.vintage import VintageRef, canonicalPayloadBytes

EDGAR_QUARTERLY_FINANCIAL_DATASET_ID = "quarterly-financial"
EDGAR_QUARTERLY_FINANCIAL_SOURCE_RULE_ID = "edgar-quarterly-financial-source"
EDGAR_QUARTERLY_FINANCIAL_SOURCE_RULE_VERSION = "1"
EDGAR_QUARTERLY_FINANCIAL_SOURCE_RULE_HASH = sha256(b"dartlab.edgar-quarterly-financial-source.v1").hexdigest()
EDGAR_QUARTERLY_FINANCIAL_SOURCE_EXECUTABLE_HASH = sha256(
    b"dartlab.edgar-quarterly-financial-source-issuer.v1"
).hexdigest()
EDGAR_QUARTERLY_FINANCIAL_NORMALIZATION_HASH = EDGAR_FINANCIAL_FEATURE_NORMALIZATION_HASH
DART_RETAINED_FINANCE_DATASET_ID = "retained-finance"
DART_RETAINED_FINANCE_LIMITATION = "dartRetainedFinanceRowsAreConditionalUntilRawFilingReceiptsExist"


class FilingStateAdapterError(ValueError):
    """공급자 filing 상태 어댑터 입력, source receipt, 또는 의미 계약이 잘못되면 발생한다."""


@dataclass(frozen=True)
class EdgarQuarterlyFinancialSourceArtifact:
    """EDGAR companyfacts rows frozen for one decision cutoff."""

    facts: pl.DataFrame
    content: bytes
    artifactHash: str
    entityId: str
    knowledgeAsOf: str
    rowCount: int


@dataclass(frozen=True)
class EdgarQuarterlyFinancialAdapterResult:
    """EDGAR source artifact, compiled state, and provider observation batch."""

    sourceArtifact: EdgarQuarterlyFinancialSourceArtifact
    compiled: CompiledQuarterlyFinancialState
    batch: ProviderObservationBatch


def _dateText(value: str, label: str) -> str:
    text = str(value).replace("-", "")
    if len(text) != 8 or not text.isdigit():
        raise FilingStateAdapterError(f"invalid {label}: {value}")
    try:
        date(int(text[:4]), int(text[4:6]), int(text[6:8]))
    except ValueError as error:
        raise FilingStateAdapterError(f"invalid {label}: {value}") from error
    return text


def _validDigest(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value.lower())


def _normalizeDateExpr(column: str) -> pl.Expr:
    return (
        pl.when(pl.col(column).is_null())
        .then(None)
        .otherwise(pl.col(column).cast(pl.Utf8).str.replace_all("-", "").str.slice(0, 8))
        .alias(column)
    )


def _isoDateExpr(column: str) -> pl.Expr:
    compact = pl.col(column)
    return (
        pl.when(compact.is_null())
        .then(None)
        .otherwise(compact.str.slice(0, 4) + "-" + compact.str.slice(4, 2) + "-" + compact.str.slice(6, 2))
        .alias(column)
    )


def _canonicalRows(frame: pl.DataFrame) -> tuple[dict[str, str | float | None], ...]:
    rows = []
    for row in frame.iter_rows(named=True):
        value = float(row["val"])
        if not math.isfinite(value):
            raise FilingStateAdapterError("EDGAR source fact contains a non-finite value")
        rows.append(
            {
                "namespace": str(row["namespace"]),
                "tag": str(row["tag"]),
                "unit": str(row["unit"]),
                "val": value,
                "form": str(row["form"]),
                "filed": str(row["filed"]),
                "start": None if row["start"] is None else str(row["start"]),
                "end": None if row["end"] is None else str(row["end"]),
                "accn": str(row["accn"]),
            }
        )
    return tuple(rows)


def buildEdgarQuarterlyFinancialSourceArtifact(
    facts: pl.DataFrame,
    *,
    entityId: str,
    knowledgeAsOf: str,
) -> EdgarQuarterlyFinancialSourceArtifact:
    """Freeze cutoff-filtered EDGAR companyfacts rows as canonical bytes.

    Args:
        facts: EDGAR companyfacts rows with namespace, tag, unit, value, filing date, period, and accession.
        entityId: Company identity used by the simulator, such as ticker or CIK.
        knowledgeAsOf: Decision cutoff used to exclude future filings.

    Returns:
        Canonical source artifact plus the filtered facts used by the PIT compiler.

    Raises:
        FilingStateAdapterError: If required columns or dates are invalid.

    Example:
        ``source = buildEdgarQuarterlyFinancialSourceArtifact(facts, entityId="AAPL", knowledgeAsOf="20250201")``
    """

    if not entityId:
        raise FilingStateAdapterError("EDGAR source artifact needs an entityId")
    required = {"namespace", "tag", "unit", "val", "form", "filed", "start", "end", "accn"}
    missing = required - set(facts.columns)
    if missing:
        raise FilingStateAdapterError(f"EDGAR source facts missing columns: {sorted(missing)}")
    cutoff = _dateText(knowledgeAsOf, "knowledgeAsOf")
    normalized = (
        facts.select("namespace", "tag", "unit", "val", "form", "filed", "start", "end", "accn")
        .with_columns(
            pl.col("namespace").cast(pl.Utf8),
            pl.col("tag").cast(pl.Utf8),
            pl.col("unit").cast(pl.Utf8),
            pl.col("form").cast(pl.Utf8),
            pl.col("accn").cast(pl.Utf8),
            pl.col("val").cast(pl.Float64, strict=False).alias("val"),
            _normalizeDateExpr("filed"),
            _normalizeDateExpr("start"),
            _normalizeDateExpr("end"),
        )
        .filter(
            (pl.col("namespace") == "us-gaap")
            & (pl.col("filed") <= cutoff)
            & pl.col("form").str.contains(r"^10-[KQ](?:/A)?$")
        )
        .sort(["namespace", "tag", "unit", "form", "filed", "start", "end", "accn", "val"], nulls_last=True)
    )
    rows = _canonicalRows(normalized)
    content = canonicalPayloadBytes(
        {
            "schemaVersion": "edgar-quarterly-financial-source-v1",
            "provider": "edgar",
            "datasetId": EDGAR_QUARTERLY_FINANCIAL_DATASET_ID,
            "entityId": entityId,
            "knowledgeAsOf": cutoff,
            "selectionRule": "us-gaap-periodic-filed-on-or-before-cutoff-v1",
            "rows": rows,
        }
    )
    compilerFacts = normalized.with_columns(_isoDateExpr("filed"), _isoDateExpr("start"), _isoDateExpr("end"))
    return EdgarQuarterlyFinancialSourceArtifact(
        facts=compilerFacts,
        content=content,
        artifactHash=sha256(content).hexdigest(),
        entityId=entityId,
        knowledgeAsOf=cutoff,
        rowCount=normalized.height,
    )


def issueEdgarQuarterlyFinancialSource(
    source: EdgarQuarterlyFinancialSourceArtifact,
    databasePath: str | Path,
    artifactRoot: str | Path,
    *,
    privateKey: bytes,
    issuerId: str,
    issuerKeyId: str,
    issuedAt: str,
    trustedIssuers: Mapping[str, TrustedIssuer],
) -> AdmissionReceipt:
    """Issue an exact EDGAR source dataVintage receipt for one frozen artifact.

    Args:
        source: Canonical EDGAR source artifact built by this adapter.
        databasePath: Append-only admission registry.
        artifactRoot: Content-addressed artifact store.
        privateKey: Source issuer private key bytes.
        issuerId: Trusted issuer identity.
        issuerKeyId: Trusted issuer key identity.
        issuedAt: Receipt issue time.
        trustedIssuers: Runtime issuer allowlist.

    Returns:
        Verified dataVintage receipt over the source artifact.

    Raises:
        FilingStateAdapterError: If the source content and hash drift.

    Example:
        ``receipt = issueEdgarQuarterlyFinancialSource(source, registry, artifacts, ...)``
    """

    artifactHash = putAdmissionArtifact(artifactRoot, source.content)
    if artifactHash != source.artifactHash:
        raise FilingStateAdapterError("EDGAR source artifact hash mismatch")
    return issueAdmissionReceipt(
        databasePath,
        artifactRoot,
        privateKey=privateKey,
        kind="dataVintage",
        subjectHash=source.artifactHash,
        artifactHash=source.artifactHash,
        parentReceiptIds=(),
        ruleId=EDGAR_QUARTERLY_FINANCIAL_SOURCE_RULE_ID,
        ruleVersion=EDGAR_QUARTERLY_FINANCIAL_SOURCE_RULE_VERSION,
        ruleHash=EDGAR_QUARTERLY_FINANCIAL_SOURCE_RULE_HASH,
        issuerId=issuerId,
        issuerKeyId=issuerKeyId,
        issuerExecutableHash=EDGAR_QUARTERLY_FINANCIAL_SOURCE_EXECUTABLE_HASH,
        knowledgeAsOf=source.knowledgeAsOf,
        revisionPolicy="asKnown",
        coverage="asOfExact",
        frequency="quarter",
        stepSpan=1,
        maxAdmittedStep=0,
        status="verifiedVintage",
        issuedAt=issuedAt,
        trustedIssuers=trustedIssuers,
    )


def buildEdgarQuarterlyFinancialStateRegistry() -> StateVariableRegistry:
    """Build the reduced financial-state variable registry for EDGAR quarters.

    Args:
        None.

    Returns:
        Meaning registry for exact EDGAR financial variables. Latent demand is a downstream assumption.

    Raises:
        StateVariableError: Propagated if an internal mapping becomes invalid.

    Example:
        ``registry = buildEdgarQuarterlyFinancialStateRegistry()``
    """

    return buildStateVariableRegistry(
        tuple(
            StateVariableSpec(
                variableId=item.variableId,
                signalId=item.variableId,
                providerId="edgar",
                datasetId=EDGAR_QUARTERLY_FINANCIAL_DATASET_ID,
                unit=item.unit,
                role="state",
                evidenceRole=item.evidenceRole,
                frequency="quarter",
                timing=item.timing,
                transformId=item.transformId,
                maxStalenessDays=400,
                lower=item.lower,
                upper=item.upper,
            )
            for item in _FINANCIAL_STATE_VARIABLES
        )
    )


def _sourceRefs(compiled: CompiledQuarterlyFinancialState) -> tuple[str, ...]:
    refs = set()
    for item in compiled.evidence:
        refs.add(f"{item.accession}|{item.tag}|{item.fiscalStart}|{item.fiscalEnd}|{item.status}")
        refs.update(item.derivationInputs)
    return tuple(sorted(refs))


def _latestSelectedFilingDate(compiled: CompiledQuarterlyFinancialState) -> str:
    try:
        return max(_dateText(item.filedAt, "evidence filedAt") for item in compiled.evidence)
    except ValueError as error:
        raise EdgarStateError("compiled EDGAR state has no filing evidence") from error


def _validateSourceReceipt(
    source: EdgarQuarterlyFinancialSourceArtifact,
    sourceReceipt: AdmissionReceipt | None,
) -> tuple[str, str, str]:
    if sourceReceipt is None:
        return "", "latestRetained", "periodOnly"
    if (
        sourceReceipt.kind != "dataVintage"
        or sourceReceipt.subjectHash != source.artifactHash
        or sourceReceipt.artifactHash != source.artifactHash
        or sourceReceipt.ruleId != EDGAR_QUARTERLY_FINANCIAL_SOURCE_RULE_ID
        or sourceReceipt.ruleVersion != EDGAR_QUARTERLY_FINANCIAL_SOURCE_RULE_VERSION
        or sourceReceipt.ruleHash != EDGAR_QUARTERLY_FINANCIAL_SOURCE_RULE_HASH
        or sourceReceipt.issuerExecutableHash != EDGAR_QUARTERLY_FINANCIAL_SOURCE_EXECUTABLE_HASH
        or sourceReceipt.knowledgeAsOf != source.knowledgeAsOf
        or sourceReceipt.revisionPolicy != "asKnown"
        or sourceReceipt.coverage != "asOfExact"
        or sourceReceipt.status != "verifiedVintage"
    ):
        raise FilingStateAdapterError("EDGAR source receipt does not match the source artifact")
    return sourceReceipt.receiptId, "asKnown", "asOfExact"


def _observationVintage(
    *,
    entityId: str,
    source: EdgarQuarterlyFinancialSourceArtifact,
    compiled: CompiledQuarterlyFinancialState,
    availableAt: str,
    sourceReceipt: AdmissionReceipt | None,
) -> VintageRef:
    receiptId, revisionPolicy, coverage = _validateSourceReceipt(source, sourceReceipt)
    return VintageRef(
        artifactKind="edgarQuarterlyFinancialFacts",
        provider="edgar",
        artifactId=f"{entityId}:{source.knowledgeAsOf}:{source.artifactHash}",
        artifactHash=source.artifactHash,
        payloadHash=source.artifactHash,
        knowledgeAsOf=source.knowledgeAsOf,
        availableAt=availableAt,
        revisionPolicy=revisionPolicy,
        coverage=coverage,
        fiscalThrough=compiled.fiscalThrough,
        receiptId=receiptId,
        contractHash=EDGAR_QUARTERLY_FINANCIAL_NORMALIZATION_HASH,
        sourceRefs=_sourceRefs(compiled),
    )


def buildEdgarQuarterlyFinancialObservationBatch(
    facts: pl.DataFrame,
    *,
    entityId: str,
    decisionAsOf: str,
    sourceReceipt: AdmissionReceipt | None = None,
) -> EdgarQuarterlyFinancialAdapterResult:
    """Compile EDGAR companyfacts into a provider observation batch.

    Args:
        facts: EDGAR companyfacts rows for one entity.
        entityId: Company identity used by the simulator, such as ticker or CIK.
        decisionAsOf: Decision cutoff for the as-known query.
        sourceReceipt: Optional exact dataVintage receipt for the frozen source artifact.

    Returns:
        Source artifact, compiled financial state, and provider observation batch.

    Raises:
        FilingStateAdapterError: If source receipt or variable meaning is invalid.

    Example:
        ``result = buildEdgarQuarterlyFinancialObservationBatch(facts, entityId="AAPL", decisionAsOf="20250201")``
    """

    if not entityId:
        raise FilingStateAdapterError("EDGAR adapter needs an entityId")
    source = buildEdgarQuarterlyFinancialSourceArtifact(facts, entityId=entityId, knowledgeAsOf=decisionAsOf)
    compiled = compileEdgarQuarterlyFinancialState(source.facts, knowledgeAsOf=source.knowledgeAsOf)
    availableAt = _latestSelectedFilingDate(compiled)
    vintage = _observationVintage(
        entityId=entityId,
        source=source,
        compiled=compiled,
        availableAt=availableAt,
        sourceReceipt=sourceReceipt,
    )
    observations = tuple(
        makeVariableObservation(
            providerId="edgar",
            datasetId=EDGAR_QUARTERLY_FINANCIAL_DATASET_ID,
            entityId=entityId,
            signalId=item.variableId,
            value=float(getattr(compiled.state, item.fieldName)),
            unit=item.unit,
            frequency="quarter",
            timing=item.timing,
            transformId=item.transformId,
            evidenceRole=item.evidenceRole,
            eventAt=compiled.fiscalThrough,
            availableAt=availableAt,
            knowledgeAsOf=source.knowledgeAsOf,
            availabilityPrecision="date",
            revisionId=compiled.stateHash,
            vintage=vintage,
            normalizationRuleHash=EDGAR_QUARTERLY_FINANCIAL_NORMALIZATION_HASH,
        )
        for item in _FINANCIAL_STATE_VARIABLES
    )
    registry = buildEdgarQuarterlyFinancialStateRegistry()
    batch = buildProviderObservationBatch(
        observations,
        providerId="edgar",
        datasetId=EDGAR_QUARTERLY_FINANCIAL_DATASET_ID,
        entityId=entityId,
        signalIds=tuple(item.signalId for item in registry.specs),
        cutoffAsOf=source.knowledgeAsOf,
    )
    return EdgarQuarterlyFinancialAdapterResult(source, compiled, batch)


def buildDartRetainedFinanceVintage(
    *,
    entityId: str,
    artifactHash: str,
    knowledgeAsOf: str,
    fiscalThrough: str = "",
    sourceRefs: tuple[str, ...] = (),
) -> VintageRef:
    """Represent retained DART finance rows as conditional evidence only.

    Args:
        entityId: DART stock code or company identity.
        artifactHash: Content hash of the retained finance rows artifact.
        knowledgeAsOf: Cutoff label of the retained snapshot.
        fiscalThrough: Optional fiscal period covered by the rows.
        sourceRefs: Optional row or filing references retained by the caller.

    Returns:
        VintageRef with latestRetained and periodOnly coverage.

    Raises:
        FilingStateAdapterError: If identity, hash, or cutoff is invalid.

    Example:
        ``vintage = buildDartRetainedFinanceVintage(entityId="005930", artifactHash=digest, knowledgeAsOf="20250515")``
    """

    if not entityId:
        raise FilingStateAdapterError("DART retained finance vintage needs an entityId")
    if not _validDigest(artifactHash):
        raise FilingStateAdapterError("DART retained finance artifact hash is invalid")
    cutoff = _dateText(knowledgeAsOf, "knowledgeAsOf")
    fiscal = _dateText(fiscalThrough, "fiscalThrough") if fiscalThrough else ""
    return VintageRef(
        artifactKind="dartRetainedFinanceRows",
        provider="dart",
        artifactId=f"{entityId}:{artifactHash}",
        artifactHash=artifactHash,
        payloadHash=artifactHash,
        knowledgeAsOf=cutoff,
        availableAt=cutoff,
        revisionPolicy="latestRetained",
        coverage="periodOnly",
        fiscalThrough=fiscal,
        contractHash=sha256(DART_RETAINED_FINANCE_LIMITATION.encode("utf-8")).hexdigest(),
        sourceRefs=tuple(sorted(sourceRefs)),
    )
