"""Universe U1 deterministic logical, version, row, block ID 규칙."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from pathlib import PurePosixPath
from typing import Any

from .canonical import canonicalJson

_KIND_RE = re.compile(r"^[a-z][a-z0-9-]{0,62}$")
_DU_ID_RE = re.compile(r"^du:v1:([a-z][a-z0-9-]{0,62}):([0-9a-f]{64})$")


def normalizePath(path: str, *, caseSensitive: bool = True) -> str:
    """Source path를 NFC POSIX 상대 경로로 정규화한다."""
    normalized = unicodedata.normalize("NFC", str(path).replace("\\", "/"))
    pure = PurePosixPath(normalized)
    if pure.is_absolute() or not pure.parts or ".." in pure.parts:
        raise ValueError(f"안전하지 않은 source path: {path}")
    result = pure.as_posix()
    return result if caseSensitive else result.casefold()


def _validateKind(kind: str) -> str:
    normalized = str(kind).strip().lower()
    if not _KIND_RE.fullmatch(normalized):
        raise ValueError(f"잘못된 Universe ID kind: {kind}")
    return normalized


def logicalId(kind: str, canonicalTuple: Any) -> str:
    """종류와 canonical tuple에서 stable logical ID를 만든다."""
    normalizedKind = _validateKind(kind)
    digest = hashlib.sha256(canonicalJson({"kind": normalizedKind, "logical": canonicalTuple})).hexdigest()
    return f"du:v1:{normalizedKind}:{digest}"


def versionId(logicalIdValue: str, revisionTuple: Any) -> str:
    """Logical ID와 source revision tuple에서 immutable version ID를 만든다."""
    match = _DU_ID_RE.fullmatch(logicalIdValue)
    if match is None:
        raise ValueError(f"잘못된 logical ID: {logicalIdValue}")
    kind = _validateKind(f"{match.group(1)}-version")
    digest = hashlib.sha256(canonicalJson({"logicalId": logicalIdValue, "revision": revisionTuple})).hexdigest()
    return f"du:v1:{kind}:{digest}"


def hfRepoIds(repoId: str, revision: str) -> tuple[str, str]:
    repo = unicodedata.normalize("NFC", repoId.strip()).casefold()
    logical = logicalId("hf-repo", (repo,))
    return logical, versionId(logical, (revision,))


def hfFileIds(repoId: str, path: str, revision: str, oid: str) -> tuple[str, str]:
    repo = unicodedata.normalize("NFC", repoId.strip()).casefold()
    logical = logicalId("hf-file", (repo, normalizePath(path)))
    return logical, versionId(logical, (revision, oid))


def dartOrganizationId(corpCode: str) -> str:
    normalized = str(corpCode).strip()
    if not re.fullmatch(r"\d{8}", normalized):
        raise ValueError(f"DART corpCode는 8자리여야 함: {corpCode}")
    return logicalId("organization", ("KR", "DART_CORP_CODE", normalized))


def edgarOrganizationId(cik: str) -> str:
    text = str(cik).strip()
    if not text.isdigit() or len(text) > 10:
        raise ValueError(f"EDGAR CIK는 10자리 이하 숫자여야 함: {cik}")
    return logicalId("organization", ("US", "SEC_CIK", text.zfill(10)))


def securityId(marketNamespace: str, listingIdentifier: str, validFrom: str | None) -> str:
    namespace = unicodedata.normalize("NFC", marketNamespace.strip()).upper()
    identifier = unicodedata.normalize("NFC", listingIdentifier.strip()).upper()
    if not namespace or not identifier:
        raise ValueError("security namespace와 identifier는 비어 있을 수 없음")
    return logicalId("security", (namespace, identifier, validFrom))


def blogPostIds(repoId: str, path: str, gitBlobDigest: str) -> tuple[str, str]:
    logical = logicalId("blog-post", (repoId.casefold(), normalizePath(path)))
    return logical, versionId(logical, (gitBlobDigest,))


def blogBlockIds(
    postId: str,
    headingLineage: tuple[str, ...],
    stableBlockKey: str,
    contentDigest: str,
) -> tuple[str, str]:
    logical = logicalId("blog-block", (postId, headingLineage, stableBlockKey))
    return logical, versionId(logical, (contentDigest,))


def rowId(fileLogicalId: str, tableId: str, businessKey: Any) -> str:
    if businessKey is None:
        raise ValueError("business key 없는 행은 rowVersionId를 사용해야 함")
    return logicalId("row", (fileLogicalId, tableId, businessKey))


def rowVersionId(fileVersionId: str, rowGroup: int, rowOffset: int) -> str:
    if rowGroup < 0 or rowOffset < 0:
        raise ValueError("rowGroup과 rowOffset은 0 이상이어야 함")
    return logicalId("row-version", (fileVersionId, rowGroup, rowOffset))


def cellId(rowIdentity: str, columnName: str, *, revisionScoped: bool = False) -> str:
    kind = "cell-version" if revisionScoped else "cell"
    return logicalId(kind, (rowIdentity, unicodedata.normalize("NFC", columnName)))
