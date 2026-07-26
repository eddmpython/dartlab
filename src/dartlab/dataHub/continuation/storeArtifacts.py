"""Continuation artifact staging 과 reference 계층.

분할 근거는 파일 크기 룰이다. 원본 단일 파일이 1,976 줄이라 SQLite 관심사별로
선형 mixin 체인으로 나눈다. 체인 순서는 base, schema, artifacts, gc, integrity 이고
구체 클래스는 `continuationStore.ContinuationStore` 하나뿐이다.
"""

from __future__ import annotations

import hashlib
import re
import sqlite3
import threading
import uuid
from collections.abc import Callable
from typing import TYPE_CHECKING

from .contracts import (
    ArrowPayloadFacts,
    ContinuationError,
)

_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_INITIALIZE_LOCK = threading.Lock()
_PayloadValidator = Callable[..., ArrowPayloadFacts]
_SCHEMA_VERSION = 3
_SWEEP_NAMES = frozenset({"artifacts", "cas", "roots"})


from .storeBase import _ContinuationStoreBase, _StagedArtifact
from .storeSchema import _ContinuationStoreSchema

if TYPE_CHECKING:
    pass


class _ContinuationStoreArtifacts(_ContinuationStoreSchema):
    """Continuation artifact staging 과 reference 계층."""

    def _artifactRegisteredForPublish(self, digest: str, byteCount: int) -> bool:
        if _DIGEST_RE.fullmatch(digest) is None or type(byteCount) is not int or byteCount < 0:
            return False
        with self._connection() as connection:
            row = connection.execute(
                "SELECT byte_count, status FROM continuation_artifacts WHERE digest=?",
                (digest,),
            ).fetchone()
            if row is None:
                return False
            if self._storedInt(row["byte_count"]) != byteCount:
                return False
            return row["status"] in {"STAGED", "REFERENCED"}

    def _stageArtifact(self, payload: bytes, *, now: float) -> _StagedArtifact:
        digest = hashlib.sha256(payload).hexdigest()
        ownerId = uuid.uuid4().hex
        byteCount = len(payload)
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM continuation_artifacts WHERE digest=?",
                (digest,),
            ).fetchone()
            if row is not None and self._storedInt(row["byte_count"]) != byteCount:
                raise ContinuationError("CONTINUATION_CORRUPT")
            if row is not None and row["status"] == "REFERENCED":
                existing = self.cas.readBytes(digest)
                if len(existing) != byteCount:
                    raise ContinuationError("CONTINUATION_CORRUPT")
                return _StagedArtifact(digest, byteCount, ownerId)
            if row is None:
                connection.execute(
                    "INSERT INTO continuation_artifacts "
                    "(digest, byte_count, status, stage_owner, staged_at, referenced_at) "
                    "VALUES (?, ?, 'STAGED', ?, ?, NULL)",
                    (digest, byteCount, ownerId, now),
                )
            else:
                connection.execute(
                    "UPDATE continuation_artifacts SET status='STAGED', stage_owner=?, staged_at=?, "
                    "referenced_at=NULL WHERE digest=?",
                    (ownerId, now, digest),
                )
        # The durable STAGED row makes a crash before publication collectable.
        # A second write transaction closes the registration-check/publication
        # race: maintenance cannot tombstone the row after the check but before
        # the hard-link becomes visible.
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            registered = connection.execute(
                "SELECT byte_count, status FROM continuation_artifacts WHERE digest=?",
                (digest,),
            ).fetchone()
            if (
                registered is None
                or self._storedInt(registered["byte_count"]) != byteCount
                or registered["status"] not in {"STAGED", "REFERENCED"}
            ):
                raise ContinuationError("CONTINUATION_CORRUPT")
            committedDigest = self.cas.putBytes(payload)
            if committedDigest != digest:
                raise ContinuationError("CONTINUATION_CORRUPT")
        return _StagedArtifact(digest, byteCount, ownerId)

    def _referenceArtifact(
        self,
        connection: sqlite3.Connection,
        artifact: _StagedArtifact,
        *,
        now: float,
    ) -> None:
        row = connection.execute(
            "SELECT * FROM continuation_artifacts WHERE digest=?",
            (artifact.digest,),
        ).fetchone()
        if row is None or self._storedInt(row["byte_count"]) != artifact.byteCount:
            raise ContinuationError("CONTINUATION_CORRUPT")
        payload = self.cas.readBytes(artifact.digest)
        if len(payload) != artifact.byteCount:
            raise ContinuationError("CONTINUATION_CORRUPT")
        connection.execute(
            "UPDATE continuation_artifacts SET status='REFERENCED', stage_owner=NULL, referenced_at=? WHERE digest=?",
            (now, artifact.digest),
        )

    @staticmethod
    def _requireReferencedArtifact(
        connection: sqlite3.Connection,
        digest: str,
        *,
        expectedBytes: int | None = None,
    ) -> sqlite3.Row:
        row = connection.execute(
            "SELECT * FROM continuation_artifacts WHERE digest=?",
            (digest,),
        ).fetchone()
        if row is None or row["status"] != "REFERENCED":
            raise ContinuationError("CONTINUATION_CORRUPT")
        byteCount = _ContinuationStoreBase._storedInt(row["byte_count"])
        if byteCount < 0 or (expectedBytes is not None and byteCount != expectedBytes):
            raise ContinuationError("CONTINUATION_CORRUPT")
        return row
