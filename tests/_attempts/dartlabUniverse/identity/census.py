"""Universe U1 DART and EDGAR identity authority machine census."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Iterable

from ..canonical import canonicalDigest, canonicalJson
from .dartIdentitySource import enumerateDartIdentities
from .edgarIdentitySource import enumerateEdgarIdentities
from .ledger import IdentityEvidence, normalizeIdentifier


@dataclass(frozen=True, slots=True)
class IdentitySourceSummary:
    sourceRef: str
    entityCount: int
    aliasCount: int
    listingAliasCount: int
    sourceRevisions: tuple[str, ...]
    duplicateEntityIds: tuple[str, ...]
    duplicateCanonicalKeys: tuple[tuple[str, str], ...]
    recordsDigest: str


@dataclass(frozen=True, slots=True)
class IdentityCensus:
    sources: tuple[IdentitySourceSummary, ...]
    totalEntityCount: int
    crossSourceEntityCollisions: tuple[str, ...]
    digest: str


def _summarize(sourceRef: str, records: Iterable[IdentityEvidence]) -> tuple[IdentitySourceSummary, set[str]]:
    entityCounts: dict[str, int] = {}
    canonicalCounts: dict[tuple[str, str], int] = {}
    revisions = set()
    aliasCount = 0
    listingAliasCount = 0
    recordCount = 0
    digest = hashlib.sha256()
    for record in records:
        recordCount += 1
        entityCounts[record.entityId] = entityCounts.get(record.entityId, 0) + 1
        canonicalKey = normalizeIdentifier(
            record.canonicalIdentifier.namespace,
            record.canonicalIdentifier.value,
        )
        canonicalCounts[canonicalKey] = canonicalCounts.get(canonicalKey, 0) + 1
        revisions.add(record.sourceRevision)
        aliasCount += len(record.aliases)
        listingAliasCount += sum(alias.namespace in {"KR_STOCK_CODE", "US_TICKER"} for alias in record.aliases)
        encoded = canonicalJson(record)
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    summary = IdentitySourceSummary(
        sourceRef=sourceRef,
        entityCount=recordCount,
        aliasCount=aliasCount,
        listingAliasCount=listingAliasCount,
        sourceRevisions=tuple(sorted(revisions)),
        duplicateEntityIds=tuple(sorted(key for key, count in entityCounts.items() if count > 1)),
        duplicateCanonicalKeys=tuple(sorted(key for key, count in canonicalCounts.items() if count > 1)),
        recordsDigest=digest.hexdigest(),
    )
    return summary, set(entityCounts)


def censusIdentitySources() -> IdentityCensus:
    """Local DART와 EDGAR identity authority를 전수 집계하고 collision을 기록한다."""
    dart, dartIds = _summarize("DART_CORP_CODE_PARQUET", enumerateDartIdentities())
    edgar, edgarIds = _summarize("SEC_TICKERS_PARQUET", enumerateEdgarIdentities())
    sources = (dart, edgar)
    base = {
        "sources": sources,
        "totalEntityCount": sum(source.entityCount for source in sources),
        "crossSourceEntityCollisions": tuple(sorted(dartIds & edgarIds)),
    }
    return IdentityCensus(**base, digest=canonicalDigest(base))
