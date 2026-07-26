"""Continuation ledger 무결성 검증 계층.

분할 근거는 파일 크기 룰이다. 원본 단일 파일이 1,976 줄이라 SQLite 관심사별로
선형 mixin 체인으로 나눈다. 체인 순서는 base, schema, artifacts, gc, integrity 이고
구체 클래스는 `continuationStore.ContinuationStore` 하나뿐이다.
"""

from __future__ import annotations

import hmac
import re
import sqlite3
import threading
from collections.abc import Callable
from pathlib import Path

from .contracts import (
    ArrowPayloadFacts,
    ContinuationError,
)
from .privateStorage import verifyPrivatePath
from .queryState import decodeQueryState

_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_INITIALIZE_LOCK = threading.Lock()
_PayloadValidator = Callable[..., ArrowPayloadFacts]
_SCHEMA_VERSION = 3
_SWEEP_NAMES = frozenset({"artifacts", "cas", "roots"})


from .storeBase import _resultDigest
from .storeGc import _ContinuationStoreGc


class _ContinuationStoreIntegrity(_ContinuationStoreGc):
    """Continuation ledger 무결성 검증 계층."""

    def _verifySucceededRow(
        self,
        connection: sqlite3.Connection,
        row: sqlite3.Row,
        rowsByDigest: dict[str, sqlite3.Row],
    ) -> None:
        required = ("page_digest", "row_count", "byte_count", "result_digest")
        if any(row[name] is None for name in required):
            raise ContinuationError("CONTINUATION_CORRUPT")
        pageDigest = self._storedDigest(row["page_digest"])
        byteCount = self._storedInt(row["byte_count"])
        self._requireReferencedArtifact(connection, pageDigest, expectedBytes=byteCount)
        payload = self.cas.readBytes(
            pageDigest,
            maxBytes=self.policy.maxPageBytes,
            budgetCode="CONTINUATION_BYTE_BUDGET",
        )
        rowCount = self._storedInt(row["row_count"])
        if byteCount != len(payload) or rowCount < 0 or rowCount > self.policy.maxPageRows:
            raise ContinuationError("CONTINUATION_CORRUPT")
        pins = self._pinsFromRow(row)
        self.payloadValidator(
            payload,
            claimedRowCount=rowCount,
            expectedSchemaDigest=pins.schemaDigest,
            maxPageBytes=self.policy.maxPageBytes,
            maxLogicalBytes=self.policy.maxPageLogicalBytes,
        )
        childDigest = row["next_token_digest"]
        nextStateDigest = row["next_state_digest"]
        if (childDigest is None) != (nextStateDigest is None):
            raise ContinuationError("CONTINUATION_CORRUPT")
        if childDigest is not None:
            childDigest = self._storedDigest(childDigest)
            nextStateDigest = self._storedDigest(nextStateDigest)
            child = rowsByDigest.get(childDigest)
            if child is None or child["state_digest"] != nextStateDigest:
                raise ContinuationError("CONTINUATION_CORRUPT")
            if child["parent_token_digest"] != row["token_digest"]:
                raise ContinuationError("CONTINUATION_CORRUPT")
            if child["chain_root_digest"] != row["chain_root_digest"]:
                raise ContinuationError("CONTINUATION_CORRUPT")
            if self._pinsFromRow(child) != pins:
                raise ContinuationError("CONTINUATION_CORRUPT")
            if self._storedFloat(child["expires_at"]) != self._storedFloat(row["expires_at"]):
                raise ContinuationError("CONTINUATION_CORRUPT")
        expected = _resultDigest(
            self._storedDigest(row["token_digest"]),
            pins,
            pageDigest,
            rowCount,
            byteCount,
            childDigest,
        )
        if not hmac.compare_digest(expected, self._storedDigest(row["result_digest"])):
            raise ContinuationError("CONTINUATION_CORRUPT")

    def verifyIntegrity(self) -> bool:
        """SQLite graph, private state, pins, Arrow pages, CAS를 전수 검증한다.

        Args:
            없음.

        Returns:
            모든 검증을 통과하면 True.

        Raises:
            ContinuationError: ledger 또는 artifact가 불완전할 때.

        Example:
            ``assert store.verifyIntegrity()``.

        Guide:
            owner callback을 호출하지 않으며 bearer token 원문도 요구하지 않는다.

        SeeAlso:
            ``pruneExpired``.

        Requires:
            같은 root를 다른 코드가 직접 수정하지 않는다.

        AIContext:
            actual Arrow rows와 schema까지 읽어 promotion evidence를 만든다.
        """
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            check = connection.execute("PRAGMA integrity_check").fetchone()
            foreignKeyErrors = connection.execute("PRAGMA foreign_key_check").fetchall()
            version = connection.execute("PRAGMA user_version").fetchone()
            rows = connection.execute("SELECT * FROM continuations ORDER BY token_digest").fetchall()
            artifacts = connection.execute("SELECT * FROM continuation_artifacts ORDER BY digest").fetchall()
            if check is None or check[0] != "ok" or foreignKeyErrors:
                raise ContinuationError("CONTINUATION_CORRUPT")
            if version is None or self._storedInt(version[0]) != _SCHEMA_VERSION:
                raise ContinuationError("CONTINUATION_CORRUPT")
            try:
                self._validateSchemaV3(connection)
            except ContinuationError:
                raise ContinuationError("CONTINUATION_CORRUPT") from None

            for path in (
                self.root,
                self.databasePath,
                self.cas.root,
                self.cas.root / "objects",
                self.cas.legacyObjectRoot,
                self.cas.objectRoot,
            ):
                verifyPrivatePath(path)
            for suffix in ("-wal", "-shm"):
                sidecar = Path(f"{self.databasePath}{suffix}")
                if sidecar.exists():
                    verifyPrivatePath(sidecar)

            artifactDigests = {self._storedDigest(row["digest"]) for row in artifacts}
            casDigests = set(self.cas.iterDigests())
            if artifactDigests != casDigests:
                raise ContinuationError("CONTINUATION_CORRUPT")
            for artifact in artifacts:
                digest = self._storedDigest(artifact["digest"])
                byteCount = self._storedInt(artifact["byte_count"])
                if artifact["status"] != "REFERENCED":
                    raise ContinuationError("CONTINUATION_CORRUPT")
                if artifact["stage_owner"] is not None or artifact["referenced_at"] is None:
                    raise ContinuationError("CONTINUATION_CORRUPT")
                self._storedFloat(artifact["staged_at"])
                self._storedFloat(artifact["referenced_at"])
                if not self._artifactReferenced(connection, digest):
                    raise ContinuationError("CONTINUATION_CORRUPT")
                payload = self.cas.readBytes(digest)
                if len(payload) != byteCount:
                    raise ContinuationError("CONTINUATION_CORRUPT")

            rowsByDigest = {self._storedDigest(row["token_digest"]): row for row in rows}
            for row in rows:
                tokenDigestValue = self._storedDigest(row["token_digest"])
                rootDigest = self._storedDigest(row["chain_root_digest"])
                stateDigest = self._storedDigest(row["state_digest"])
                issuedAt = self._storedFloat(row["issued_at"])
                expiresAt = self._storedFloat(row["expires_at"])
                leaseUntil = self._storedFloat(row["lease_until"])
                if expiresAt <= issuedAt:
                    raise ContinuationError("CONTINUATION_CORRUPT")
                if row["completed_at"] is not None:
                    completedAt = self._storedFloat(row["completed_at"])
                    if completedAt < issuedAt:
                        raise ContinuationError("CONTINUATION_CORRUPT")
                root = rowsByDigest.get(rootDigest)
                if root is None or root["parent_token_digest"] is not None:
                    raise ContinuationError("CONTINUATION_CORRUPT")
                if self._storedFloat(root["expires_at"]) != expiresAt:
                    raise ContinuationError("CONTINUATION_CORRUPT")
                pins = self._pinsFromRow(row)
                artifact = self._requireReferencedArtifact(connection, stateDigest)
                stateBytes = self.cas.readBytes(stateDigest, maxBytes=self.policy.maxStateBytes)
                if self._storedInt(artifact["byte_count"]) != len(stateBytes):
                    raise ContinuationError("CONTINUATION_CORRUPT")
                state = decodeQueryState(stateBytes, maxBytes=self.policy.maxStateBytes)
                self._validateQueryState(state, pins)
                parentDigest = row["parent_token_digest"]
                if parentDigest is not None:
                    parentDigest = self._storedDigest(parentDigest)
                    parent = rowsByDigest.get(parentDigest)
                    if parent is None or str(parent["chain_root_digest"]) != rootDigest:
                        raise ContinuationError("CONTINUATION_CORRUPT")
                    if parent["status"] != "SUCCEEDED" or parent["next_token_digest"] != tokenDigestValue:
                        raise ContinuationError("CONTINUATION_CORRUPT")
                status = row["status"]
                if status == "PENDING":
                    if row["owner_id"] is not None or leaseUntil != 0:
                        raise ContinuationError("CONTINUATION_CORRUPT")
                    if any(
                        row[name] is not None
                        for name in (
                            "page_digest",
                            "row_count",
                            "byte_count",
                            "next_token_digest",
                            "next_state_digest",
                            "result_digest",
                            "completed_at",
                        )
                    ):
                        raise ContinuationError("CONTINUATION_CORRUPT")
                elif status == "RUNNING":
                    if type(row["owner_id"]) is not str or not row["owner_id"] or leaseUntil <= 0:
                        raise ContinuationError("CONTINUATION_CORRUPT")
                    if any(
                        row[name] is not None
                        for name in (
                            "page_digest",
                            "row_count",
                            "byte_count",
                            "next_token_digest",
                            "next_state_digest",
                            "result_digest",
                            "completed_at",
                        )
                    ):
                        raise ContinuationError("CONTINUATION_CORRUPT")
                elif status == "SUCCEEDED":
                    if row["owner_id"] is not None or leaseUntil != 0 or row["completed_at"] is None:
                        raise ContinuationError("CONTINUATION_CORRUPT")
                    self._verifySucceededRow(connection, row, rowsByDigest)
                else:
                    raise ContinuationError("CONTINUATION_CORRUPT")
        return True
