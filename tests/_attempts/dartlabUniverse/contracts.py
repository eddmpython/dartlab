"""Universe U1 knowledge, evidence, time 계약과 fail-closed validator."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .canonical import canonicalDigest

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class EpistemicClass(str, Enum):
    OBSERVED = "OBSERVED"
    DERIVED = "DERIVED"
    SIMULATED = "SIMULATED"
    ASSERTED = "ASSERTED"
    INFERRED = "INFERRED"
    ASSUMPTION = "ASSUMPTION"


class VerificationState(str, Enum):
    DISCOVERED = "DISCOVERED"
    ADDRESSABLE = "ADDRESSABLE"
    STRUCTURED = "STRUCTURED"
    UNRESOLVED = "UNRESOLVED"
    VERIFIED = "VERIFIED"
    CONFLICTED = "CONFLICTED"
    RETRACTED = "RETRACTED"
    TOMBSTONED = "TOMBSTONED"
    REJECTED = "REJECTED"


class Visibility(str, Enum):
    PUBLIC = "PUBLIC"
    LOCAL = "LOCAL"
    PRIVATE = "PRIVATE"
    RESTRICTED = "RESTRICTED"
    UNKNOWN = "UNKNOWN"


class Replayability(str, Enum):
    VERIFIED = "VERIFIED"
    LOCAL_CAPTURED = "LOCAL_CAPTURED"
    NONREPLAYABLE = "NONREPLAYABLE"


@dataclass(frozen=True, slots=True)
class TimeRange:
    start: str | None = None
    end: str | None = None


@dataclass(frozen=True, slots=True)
class SystemTime:
    knownAt: str
    observedAt: str | None = None
    ingestedAt: str | None = None
    retractedAt: str | None = None


@dataclass(frozen=True, slots=True)
class UniverseEvidence:
    evidenceId: str
    sourceKind: str
    sourceRef: str
    sourceRevision: str
    resourceVersionId: str
    locator: tuple[tuple[str, str], ...]
    contentDigest: str
    retrievedAt: str
    visibility: Visibility
    licenseRef: str | None = None
    quoteDigest: str | None = None


@dataclass(frozen=True, slots=True)
class UniverseStatement:
    statementId: str
    subjectRef: str
    predicate: str
    objectRef: str | None
    value: Any | None
    valueType: str | None
    validTime: TimeRange
    systemTime: SystemTime
    epistemicClass: EpistemicClass
    verificationState: VerificationState
    evidenceRefs: tuple[str, ...]
    derivationRef: str | None = None
    assumptionRefs: tuple[str, ...] = ()
    confidence: float | None = None
    visibility: Visibility = Visibility.LOCAL


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    code: str
    path: str
    detail: str


@dataclass(frozen=True, slots=True)
class ValidationReport:
    valid: bool
    issues: tuple[ValidationIssue, ...]
    digest: str


def _report(issues: list[ValidationIssue]) -> ValidationReport:
    ordered = tuple(sorted(issues, key=lambda item: (item.code, item.path, item.detail)))
    return ValidationReport(valid=not ordered, issues=ordered, digest=canonicalDigest(ordered))


def validateStatement(statement: UniverseStatement) -> ValidationReport:
    """Statement의 값, 근거, 파생, 가정, confidence 불변식을 검증한다."""
    issues = []
    hasObject = statement.objectRef is not None
    hasValue = statement.value is not None
    if hasObject == hasValue:
        issues.append(ValidationIssue("OBJECT_VALUE_XOR", "statement", "objectRef와 value 중 정확히 하나 필요"))
    if statement.epistemicClass is EpistemicClass.OBSERVED and not statement.evidenceRefs:
        issues.append(ValidationIssue("OBSERVED_EVIDENCE_REQUIRED", "evidenceRefs", "OBSERVED 근거 누락"))
    if (
        statement.epistemicClass
        in {
            EpistemicClass.DERIVED,
            EpistemicClass.SIMULATED,
            EpistemicClass.INFERRED,
        }
        and not statement.derivationRef
    ):
        issues.append(ValidationIssue("DERIVATION_REQUIRED", "derivationRef", "파생 계보 누락"))
    if statement.epistemicClass is EpistemicClass.SIMULATED and not statement.assumptionRefs:
        issues.append(ValidationIssue("SIMULATION_ASSUMPTION_REQUIRED", "assumptionRefs", "가정 누락"))
    if statement.confidence is not None and not 0.0 <= statement.confidence <= 1.0:
        issues.append(ValidationIssue("CONFIDENCE_RANGE", "confidence", "0과 1 사이여야 함"))
    if statement.visibility is Visibility.PUBLIC and statement.verificationState is VerificationState.UNRESOLVED:
        issues.append(ValidationIssue("PUBLIC_UNRESOLVED", "visibility", "미해결 statement 공개 금지"))
    if statement.visibility is Visibility.UNKNOWN:
        issues.append(ValidationIssue("UNKNOWN_VISIBILITY", "visibility", "공개 가능성을 판단할 수 없음"))
    return _report(issues)


_LOCATOR_FIELDS = {
    "HF_FILE": frozenset({"repo", "revision", "path", "oid"}),
    "PARQUET_ROW": frozenset({"fileVersionId", "rowGroup", "rowOffset"}),
    "DART": frozenset({"corpCode", "rceptNo", "document"}),
    "EDGAR": frozenset({"cik", "accession", "form"}),
    "BLOG": frozenset({"gitCommit", "path", "astPath"}),
    "MEDIA": frozenset({"objectDigest"}),
    "ENGINE_RESULT": frozenset({"executionId", "outputPath", "outputDigest"}),
}


def validateEvidence(
    evidence: UniverseEvidence,
    sourceRevisions: tuple[tuple[str, str], ...],
) -> ValidationReport:
    """Evidence locator와 snapshot source revision 결합을 검증한다."""
    issues = []
    locator = dict(evidence.locator)
    required = _LOCATOR_FIELDS.get(evidence.sourceKind)
    if required is None:
        issues.append(ValidationIssue("UNKNOWN_SOURCE_KIND", "sourceKind", evidence.sourceKind))
    else:
        missing = sorted(field for field in required if not locator.get(field))
        for field in missing:
            issues.append(ValidationIssue("LOCATOR_FIELD_REQUIRED", f"locator.{field}", evidence.sourceKind))
    revisionMap = dict(sourceRevisions)
    if revisionMap.get(evidence.sourceRef) != evidence.sourceRevision:
        issues.append(ValidationIssue("SOURCE_REVISION_MISMATCH", "sourceRevision", evidence.sourceRef))
    if not _SHA256_RE.fullmatch(evidence.contentDigest):
        issues.append(ValidationIssue("CONTENT_DIGEST_INVALID", "contentDigest", evidence.contentDigest))
    if evidence.quoteDigest is not None and not _SHA256_RE.fullmatch(evidence.quoteDigest):
        issues.append(ValidationIssue("QUOTE_DIGEST_INVALID", "quoteDigest", evidence.quoteDigest))
    if evidence.visibility is Visibility.UNKNOWN:
        issues.append(ValidationIssue("UNKNOWN_VISIBILITY", "visibility", "evidence 공개 금지"))
    return _report(issues)
