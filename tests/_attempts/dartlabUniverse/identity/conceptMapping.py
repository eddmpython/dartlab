"""Universe U1 approved concept mapping ledger."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from enum import Enum

from ..canonical import canonicalDigest


class MappingType(str, Enum):
    EXACT = "EXACT"
    BROADER = "BROADER"
    NARROWER = "NARROWER"
    TRANSFORMED = "TRANSFORMED"
    UNRESOLVED = "UNRESOLVED"


class MappingState(str, Enum):
    RESOLVED = "RESOLVED"
    UNRESOLVED = "UNRESOLVED"
    CONFLICTED = "CONFLICTED"


@dataclass(frozen=True, slots=True)
class ConceptMappingRecord:
    sourceNamespace: str
    sourceConcept: str
    canonicalConcept: str | None
    mappingType: MappingType
    scope: str | None
    unitRule: str | None
    signRule: str | None
    periodRule: str | None
    evidenceRef: str
    approved: bool
    mappingVersion: str


@dataclass(frozen=True, slots=True)
class ConceptMappingLedger:
    records: tuple[ConceptMappingRecord, ...]
    version: str


@dataclass(frozen=True, slots=True)
class MappingResult:
    state: MappingState
    sourceNamespace: str
    sourceConcept: str
    candidates: tuple[ConceptMappingRecord, ...]
    reasonCode: str


def _key(namespace: str, concept: str) -> tuple[str, str]:
    return (
        unicodedata.normalize("NFC", namespace.strip()).upper(),
        unicodedata.normalize("NFC", concept.strip()),
    )


def buildConceptMappingLedger(records: tuple[ConceptMappingRecord, ...]) -> ConceptMappingLedger:
    ordered = tuple(
        sorted(
            records,
            key=lambda item: (
                item.sourceNamespace,
                item.sourceConcept,
                item.mappingVersion,
                item.evidenceRef,
            ),
        )
    )
    return ConceptMappingLedger(records=ordered, version=canonicalDigest(ordered))


def resolveConcept(
    sourceConcept: str,
    mappingLedger: ConceptMappingLedger,
    *,
    sourceNamespace: str,
    scope: str | None = None,
) -> MappingResult:
    """Approved exact source key만 해소하고 K-IFRS와 US-GAAP을 자동 합치지 않는다."""
    target = _key(sourceNamespace, sourceConcept)
    candidates = tuple(
        record
        for record in mappingLedger.records
        if record.approved
        and _key(record.sourceNamespace, record.sourceConcept) == target
        and (scope is None or record.scope in {None, scope})
    )
    if not candidates:
        return MappingResult(MappingState.UNRESOLVED, target[0], target[1], (), "NO_APPROVED_MAPPING")
    resolved = tuple(
        record
        for record in candidates
        if record.mappingType is not MappingType.UNRESOLVED and record.canonicalConcept is not None
    )
    canonicalTargets = {record.canonicalConcept for record in resolved}
    if len(canonicalTargets) > 1:
        return MappingResult(MappingState.CONFLICTED, target[0], target[1], candidates, "MULTIPLE_CANONICAL_TARGETS")
    if not resolved:
        return MappingResult(MappingState.UNRESOLVED, target[0], target[1], candidates, "EXPLICIT_UNRESOLVED")
    return MappingResult(MappingState.RESOLVED, target[0], target[1], resolved, "APPROVED_MAPPING")
