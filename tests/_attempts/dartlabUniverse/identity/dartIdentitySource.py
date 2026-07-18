"""Local OpenDART corpCode authority의 read-only identity adapter."""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

import polars as pl

from ..ids import dartOrganizationId, logicalId
from .ledger import AliasRecord, IdentifierRef, IdentityEvidence

_REQUIRED_COLUMNS = frozenset({"corp_code", "corp_name", "stock_code", "modify_date"})


def defaultDartIdentityPath() -> Path:
    return Path.home() / ".dartlab" / "corpCode.parquet"


def enumerateDartIdentities(sourcePath: Path | None = None) -> Iterator[IdentityEvidence]:
    """OpenDART corpCode parquet 전 행을 payload 변경 없이 identity evidence로 변환한다."""
    path = (sourcePath or defaultDartIdentityPath()).resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    sourceBytes = path.read_bytes()
    sourceRevision = hashlib.sha256(sourceBytes).hexdigest()
    observedAt = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
    frame = pl.read_parquet(BytesIO(sourceBytes))
    missing = sorted(_REQUIRED_COLUMNS - set(frame.columns))
    if missing:
        raise ValueError(f"DART identity column 누락: {missing}")
    selected = ["corp_code", "corp_name", "stock_code", "modify_date"]
    if "corp_eng_name" in frame.columns:
        selected.append("corp_eng_name")
    for row in frame.select(selected).sort("corp_code").iter_rows(named=True):
        corpCode = str(row.get("corp_code") or "").strip()
        corpName = str(row.get("corp_name") or "").strip()
        if len(corpCode) != 8 or not corpCode.isdigit() or not corpName:
            raise ValueError(f"DART identity row invalid: {corpCode}")
        rowLocator = f"corp_code={corpCode}"
        evidenceRef = logicalId("identity-evidence", ("DART_CORP_CODE_PARQUET", sourceRevision, rowLocator))
        aliases = [
            AliasRecord("LEGAL_NAME_KO", corpName, None, None, evidenceRef),
        ]
        corpEngName = str(row.get("corp_eng_name") or "").strip()
        if corpEngName:
            aliases.append(AliasRecord("LEGAL_NAME_EN", corpEngName, None, None, evidenceRef))
        stockCode = str(row.get("stock_code") or "").strip()
        if stockCode:
            stockCode = stockCode.upper()
            if len(stockCode) != 6 or not stockCode.isalnum() or not stockCode.isascii():
                raise ValueError(f"DART stockCode invalid: {corpCode}:{stockCode}")
            aliases.append(AliasRecord("KR_STOCK_CODE", stockCode, None, None, evidenceRef))
        yield IdentityEvidence(
            entityId=dartOrganizationId(corpCode),
            jurisdiction="KR",
            canonicalIdentifier=IdentifierRef("DART_CORP_CODE", corpCode),
            legalName=corpName,
            aliases=tuple(sorted(aliases, key=lambda item: (item.namespace, item.value))),
            sourceRef="DART_CORP_CODE_PARQUET",
            sourceRevision=sourceRevision,
            rowLocator=rowLocator,
            observedAt=observedAt,
        )
