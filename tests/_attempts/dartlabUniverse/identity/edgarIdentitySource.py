"""Local SEC ticker and CIK authority의 read-only identity adapter."""

from __future__ import annotations

import hashlib
from collections.abc import Iterator, Mapping
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

import polars as pl

from ..ids import edgarOrganizationId, logicalId
from .ledger import AliasRecord, IdentifierRef, IdentityEvidence

_REQUIRED_COLUMNS = frozenset({"ticker", "cik", "title"})


def defaultEdgarIdentityPath(repoRoot: Path | None = None) -> Path:
    root = repoRoot or Path(__file__).resolve().parents[4]
    return root / "data" / "edgar" / "tickers.parquet"


def enumerateEdgarIdentities(
    sourcePath: Path | None = None,
    *,
    validityByTicker: Mapping[str, tuple[str | None, str | None]] | None = None,
) -> Iterator[IdentityEvidence]:
    """SEC ticker parquet을 CIK로 묶고 복수 ticker를 alias로 보존한다."""
    path = (sourcePath or defaultEdgarIdentityPath()).resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    sourceBytes = path.read_bytes()
    sourceRevision = hashlib.sha256(sourceBytes).hexdigest()
    observedAt = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
    frame = pl.read_parquet(BytesIO(sourceBytes))
    missing = sorted(_REQUIRED_COLUMNS - set(frame.columns))
    if missing:
        raise ValueError(f"EDGAR identity column 누락: {missing}")
    validity = {key.upper(): value for key, value in (validityByTicker or {}).items()}
    rowsByCik: dict[str, list[dict[str, object]]] = {}
    for row in frame.select("ticker", "cik", "title").iter_rows(named=True):
        cikText = str(row.get("cik") or "").strip()
        if not cikText.isdigit() or len(cikText) > 10:
            raise ValueError(f"EDGAR CIK invalid: {cikText}")
        cik = cikText.zfill(10)
        rowsByCik.setdefault(cik, []).append(row)
    for cik, rows in sorted(rowsByCik.items()):
        titles = sorted({str(row.get("title") or "").strip() for row in rows if str(row.get("title") or "").strip()})
        if not titles:
            raise ValueError(f"EDGAR title 누락: {cik}")
        rowLocator = f"cik={cik}"
        evidenceRef = logicalId("identity-evidence", ("SEC_TICKERS_PARQUET", sourceRevision, rowLocator))
        aliases = [AliasRecord("LEGAL_NAME_EN", title, None, None, evidenceRef) for title in titles]
        for row in rows:
            ticker = str(row.get("ticker") or "").upper().strip()
            if not ticker:
                raise ValueError(f"EDGAR ticker 누락: {cik}")
            validFrom, validTo = validity.get(ticker, (None, None))
            aliases.append(AliasRecord("US_TICKER", ticker, validFrom, validTo, evidenceRef))
        yield IdentityEvidence(
            entityId=edgarOrganizationId(cik),
            jurisdiction="US",
            canonicalIdentifier=IdentifierRef("SEC_CIK", cik),
            legalName=titles[0],
            aliases=tuple(sorted(set(aliases), key=lambda item: (item.namespace, item.value))),
            sourceRef="SEC_TICKERS_PARQUET",
            sourceRevision=sourceRevision,
            rowLocator=rowLocator,
            observedAt=observedAt,
        )
