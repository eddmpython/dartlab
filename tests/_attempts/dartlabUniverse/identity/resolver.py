"""Universe U1 exact identifier resolver with ambiguous-name fail closure."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from .ledger import IdentifierRef, IdentityLedger, normalizeIdentifier


class ResolutionState(str, Enum):
    RESOLVED = "RESOLVED"
    UNRESOLVED = "UNRESOLVED"
    AMBIGUOUS = "AMBIGUOUS"
    CONFLICTING_IDENTIFIERS = "CONFLICTING_IDENTIFIERS"


@dataclass(frozen=True, slots=True)
class ResolutionResult:
    state: ResolutionState
    entityId: str | None
    candidateEntityIds: tuple[str, ...]
    matchedRefs: tuple[IdentifierRef, ...]
    reasonCode: str


def _parseAt(value: str | None) -> datetime | None:
    if value is None:
        return None
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"timezone 없는 identity validAt: {value}")
    return parsed.astimezone(timezone.utc)


def _aliasActive(validAt: datetime | None, validFrom: str | None, validTo: str | None) -> bool:
    if validAt is None:
        return True
    if validFrom is not None and validAt < _parseAt(validFrom):
        return False
    return validTo is None or validAt < _parseAt(validTo)


def resolveOrganization(
    identifierRefs: tuple[IdentifierRef, ...],
    ledger: IdentityLedger,
    *,
    validAt: str | None = None,
) -> ResolutionResult:
    """Exact canonical 또는 active alias 교집합으로 조직을 해소하며 이름만으로 merge하지 않는다."""
    if not identifierRefs:
        return ResolutionResult(ResolutionState.UNRESOLVED, None, (), (), "NO_IDENTIFIER")
    at = _parseAt(validAt)
    candidateSets = []
    matchedRefs = []
    for ref in identifierRefs:
        target = normalizeIdentifier(ref.namespace, ref.value)
        candidates = set()
        for record in ledger.records:
            canonical = normalizeIdentifier(
                record.canonicalIdentifier.namespace,
                record.canonicalIdentifier.value,
            )
            if canonical == target:
                candidates.add(record.entityId)
            for alias in record.aliases:
                if not _aliasActive(at, alias.validFrom, alias.validTo):
                    continue
                if normalizeIdentifier(alias.namespace, alias.value) == target:
                    candidates.add(record.entityId)
        if candidates:
            candidateSets.append(candidates)
            matchedRefs.append(ref)
        else:
            candidateSets.append(set())
    if not any(candidateSets):
        return ResolutionResult(ResolutionState.UNRESOLVED, None, (), (), "NO_MATCH")
    if any(not candidates for candidates in candidateSets):
        union = tuple(sorted(set().union(*candidateSets)))
        return ResolutionResult(
            ResolutionState.CONFLICTING_IDENTIFIERS,
            None,
            union,
            tuple(matchedRefs),
            "IDENTIFIER_PARTIAL_CONFLICT",
        )
    intersection = set.intersection(*candidateSets)
    if len(intersection) == 1:
        entityId = next(iter(intersection))
        return ResolutionResult(
            ResolutionState.RESOLVED,
            entityId,
            (entityId,),
            tuple(matchedRefs),
            "EXACT_IDENTIFIER_INTERSECTION",
        )
    if not intersection:
        union = tuple(sorted(set().union(*candidateSets)))
        return ResolutionResult(
            ResolutionState.CONFLICTING_IDENTIFIERS,
            None,
            union,
            tuple(matchedRefs),
            "IDENTIFIER_SET_CONFLICT",
        )
    return ResolutionResult(
        ResolutionState.AMBIGUOUS,
        None,
        tuple(sorted(intersection)),
        tuple(matchedRefs),
        "MULTIPLE_EXACT_CANDIDATES",
    )
