"""Universe U1 immutable organization identity ledger."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass

from ..canonical import canonicalDigest


def normalizeIdentifier(namespace: str, value: str) -> tuple[str, str]:
    normalizedNamespace = unicodedata.normalize("NFC", namespace.strip()).upper()
    normalizedValue = unicodedata.normalize("NFC", value.strip())
    if normalizedNamespace in {"SEC_CIK", "DART_CORP_CODE"}:
        normalizedValue = normalizedValue.zfill(10 if normalizedNamespace == "SEC_CIK" else 8)
    elif normalizedNamespace in {"US_TICKER", "KR_STOCK_CODE", "ISIN"}:
        normalizedValue = normalizedValue.upper()
    elif normalizedNamespace.startswith("LEGAL_NAME"):
        normalizedValue = " ".join(normalizedValue.casefold().split())
    if not normalizedNamespace or not normalizedValue:
        raise ValueError("identity namespace와 value는 비어 있을 수 없음")
    return normalizedNamespace, normalizedValue


@dataclass(frozen=True, slots=True)
class IdentifierRef:
    namespace: str
    value: str


@dataclass(frozen=True, slots=True)
class AliasRecord:
    namespace: str
    value: str
    validFrom: str | None
    validTo: str | None
    sourceEvidenceRef: str
    confidence: float = 1.0


@dataclass(frozen=True, slots=True)
class IdentityEvidence:
    entityId: str
    jurisdiction: str
    canonicalIdentifier: IdentifierRef
    legalName: str
    aliases: tuple[AliasRecord, ...]
    sourceRef: str
    sourceRevision: str
    rowLocator: str
    observedAt: str


@dataclass(frozen=True, slots=True)
class IdentityLedger:
    records: tuple[IdentityEvidence, ...]
    revision: str
    duplicateCanonicalKeys: tuple[tuple[str, str], ...]
    duplicateEntityIds: tuple[str, ...]


def buildIdentityLedger(records: tuple[IdentityEvidence, ...]) -> IdentityLedger:
    """Identity evidence를 stable order로 묶고 canonical collision을 fail-visible로 기록한다."""
    ordered = tuple(sorted(records, key=lambda item: (item.entityId, item.sourceRef, item.rowLocator)))
    canonicalCounts: dict[tuple[str, str], int] = {}
    entityCounts: dict[str, int] = {}
    for record in ordered:
        canonicalKey = normalizeIdentifier(
            record.canonicalIdentifier.namespace,
            record.canonicalIdentifier.value,
        )
        canonicalCounts[canonicalKey] = canonicalCounts.get(canonicalKey, 0) + 1
        entityCounts[record.entityId] = entityCounts.get(record.entityId, 0) + 1
    duplicateCanonical = tuple(sorted(key for key, count in canonicalCounts.items() if count > 1))
    duplicateEntities = tuple(sorted(key for key, count in entityCounts.items() if count > 1))
    base = {
        "records": ordered,
        "duplicateCanonicalKeys": duplicateCanonical,
        "duplicateEntityIds": duplicateEntities,
    }
    return IdentityLedger(
        records=ordered,
        revision=canonicalDigest(base),
        duplicateCanonicalKeys=duplicateCanonical,
        duplicateEntityIds=duplicateEntities,
    )
