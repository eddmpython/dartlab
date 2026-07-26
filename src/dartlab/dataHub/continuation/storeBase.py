"""Continuation ledger 연결, 시각, row 복원 원시 계층.

분할 근거는 파일 크기 룰이다. 원본 단일 파일이 1,976 줄이라 SQLite 관심사별로
선형 mixin 체인으로 나눈다. 체인 순서는 base, schema, artifacts, gc, integrity 이고
구체 클래스는 `continuationStore.ContinuationStore` 하나뿐이다.
"""

from __future__ import annotations

import hmac
import math
import re
import sqlite3
import threading
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .arrowPayload import validateArrowIpcPayload
from .artifactStore import ArtifactStore
from .contracts import (
    ArrowPayloadFacts,
    ContinuationError,
    ContinuationPins,
    ContinuationPolicy,
    ContinuationQueryState,
    bytesDigest,
    canonicalDigest,
)
from .privateStorage import _resolvePrivateRoot, securePrivatePath

if TYPE_CHECKING:
    from .continuationStore import ContinuationStore

_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_INITIALIZE_LOCK = threading.Lock()
_PayloadValidator = Callable[..., ArrowPayloadFacts]
_SCHEMA_VERSION = 3
_SWEEP_NAMES = frozenset({"artifacts", "cas", "roots"})


@dataclass(frozen=True, slots=True)
class _StagedArtifact:
    digest: str
    byteCount: int
    ownerId: str


@dataclass(frozen=True, slots=True)
class _SweepCursor:
    name: str
    digest: str
    value: float
    cycle: int


def _resultDigest(
    tokenDigestValue: str,
    pins: ContinuationPins,
    pageDigest: str,
    rowCount: int,
    byteCount: int,
    nextTokenDigest: str | None,
) -> str:
    return canonicalDigest(
        {
            "tokenDigest": tokenDigestValue,
            "sourceDigest": pins.sourceDigest,
            "queryDigest": pins.queryDigest,
            "contractDigest": pins.contractDigest,
            "schemaDigest": pins.schemaDigest,
            "pageDigest": pageDigest,
            "rowCount": rowCount,
            "byteCount": byteCount,
            "nextTokenDigest": nextTokenDigest,
        }
    )


class _LeaseHeartbeat:
    """Live owner의 SQLite lease를 별도 connection에서 갱신한다."""

    def __init__(self, store: ContinuationStore, tokenDigestValue: str, ownerId: str):
        self.store = store
        self.tokenDigestValue = tokenDigestValue
        self.ownerId = ownerId
        self.stopEvent = threading.Event()
        self.lost = False
        self.thread = threading.Thread(target=self._run, name="continuation-heartbeat", daemon=True)

    def _run(self) -> None:
        interval = max(0.01, self.store.policy.leaseSeconds / 3.0)
        while not self.stopEvent.wait(interval):
            try:
                renewed = self.store._renew(self.tokenDigestValue, self.ownerId)
            except Exception:
                renewed = False
            if not renewed:
                self.lost = True
                return

    def __enter__(self) -> _LeaseHeartbeat:
        self.thread.start()
        return self

    def __exit__(self, excType: object, exc: object, traceback: object) -> None:
        self.stopEvent.set()
        self.thread.join(timeout=max(1.0, self.store.policy.leaseSeconds))


class _ContinuationStoreBase:
    """Continuation ledger 연결, 시각, row 복원 원시 계층."""

    def __init__(
        self,
        root: Path,
        policy: ContinuationPolicy | None = None,
        clock: Callable[[], float] = time.time,
        payloadValidator: _PayloadValidator = validateArrowIpcPayload,
    ):
        self.root = _resolvePrivateRoot(root)
        self.root.mkdir(parents=True, exist_ok=True)
        securePrivatePath(self.root)
        self.policy = policy or ContinuationPolicy()
        if not callable(clock):
            raise ContinuationError("CONTINUATION_CLOCK_INVALID")
        self.clock = clock
        self.payloadValidator = payloadValidator
        self.databasePath = self.root / "continuations.sqlite"
        self.cas = ArtifactStore(
            self.root / "cas",
            registrationCheck=self._artifactRegisteredForPublish,
        )
        with _INITIALIZE_LOCK:
            self._initialize()
        securePrivatePath(self.databasePath)

    def _connect(self, *, busySeconds: float | None = None) -> sqlite3.Connection:
        timeout = 15.0 if busySeconds is None else min(15.0, max(0.0, busySeconds))
        connection = sqlite3.connect(self.databasePath, timeout=timeout)
        try:
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("PRAGMA synchronous=FULL")
            connection.execute(f"PRAGMA busy_timeout={int(timeout * 1000)}")
            securePrivatePath(self.databasePath)
            for suffix in ("-wal", "-shm"):
                sidecar = Path(f"{self.databasePath}{suffix}")
                if sidecar.exists():
                    securePrivatePath(sidecar)
        except Exception:
            connection.close()
            raise
        return connection

    @contextmanager
    def _connection(self, *, busySeconds: float | None = None) -> Iterator[sqlite3.Connection]:
        connection = self._connect(busySeconds=busySeconds)
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _now(self) -> float:
        try:
            value = self.clock()
            if type(value) not in (int, float):
                raise ValueError
            number = float(value)
        except Exception:
            raise ContinuationError("CONTINUATION_CLOCK_INVALID") from None
        if not math.isfinite(number) or number < 0:
            raise ContinuationError("CONTINUATION_CLOCK_INVALID")
        return number

    @staticmethod
    def _storedFloat(value: Any) -> float:
        if type(value) not in (int, float):
            raise ContinuationError("CONTINUATION_CORRUPT")
        try:
            number = float(value)
        except (TypeError, ValueError, OverflowError):
            raise ContinuationError("CONTINUATION_CORRUPT") from None
        if not math.isfinite(number) or number < 0:
            raise ContinuationError("CONTINUATION_CORRUPT")
        return number

    @staticmethod
    def _storedInt(value: Any, *, minimum: int = 0) -> int:
        if type(value) is not int or value < minimum:
            raise ContinuationError("CONTINUATION_CORRUPT")
        return value

    @staticmethod
    def _isTokenCollision(error: sqlite3.IntegrityError) -> bool:
        codes = {
            getattr(sqlite3, "SQLITE_CONSTRAINT_PRIMARYKEY", -1),
            getattr(sqlite3, "SQLITE_CONSTRAINT_UNIQUE", -1),
        }
        return (
            getattr(error, "sqlite_errorcode", None) in codes
            and str(error) == "UNIQUE constraint failed: continuations.token_digest"
        )

    @staticmethod
    def _isSqliteBusy(error: sqlite3.OperationalError) -> bool:
        code = getattr(error, "sqlite_errorcode", None)
        if type(code) is int and (code & 0xFF) in {
            getattr(sqlite3, "SQLITE_BUSY", 5),
            getattr(sqlite3, "SQLITE_LOCKED", 6),
        }:
            return True
        return str(error) in {"database is locked", "database table is locked"}

    @staticmethod
    def _storedDigest(value: Any) -> str:
        if type(value) is not str or _DIGEST_RE.fullmatch(value) is None:
            raise ContinuationError("CONTINUATION_CORRUPT")
        return value

    @staticmethod
    def _decodeSweepRow(row: sqlite3.Row | None) -> _SweepCursor:
        if row is None:
            raise ContinuationError("CONTINUATION_CORRUPT")
        name = row["sweep_name"]
        digest = row["cursor_digest"]
        if type(name) is not str or name not in _SWEEP_NAMES:
            raise ContinuationError("CONTINUATION_CORRUPT")
        if type(digest) is not str or (digest and _DIGEST_RE.fullmatch(digest) is None):
            raise ContinuationError("CONTINUATION_CORRUPT")
        value = _ContinuationStoreBase._storedFloat(row["cursor_value"])
        cycle = _ContinuationStoreBase._storedInt(row["cycle"])
        _ContinuationStoreBase._storedFloat(row["updated_at"])
        if name == "cas":
            prefix = int(value)
            if value != prefix or not 0 <= prefix <= 0xFF:
                raise ContinuationError("CONTINUATION_CORRUPT")
            if digest:
                raise ContinuationError("CONTINUATION_CORRUPT")
        elif name == "artifacts" and value != 0:
            raise ContinuationError("CONTINUATION_CORRUPT")
        return _SweepCursor(name, digest, value, cycle)

    @staticmethod
    def _loadSweep(connection: sqlite3.Connection, name: str) -> _SweepCursor:
        if name not in _SWEEP_NAMES:
            raise ContinuationError("CONTINUATION_CORRUPT")
        return _ContinuationStoreBase._decodeSweepRow(
            connection.execute(
                "SELECT sweep_name, cursor_digest, cursor_value, cycle, updated_at "
                "FROM continuation_sweeps WHERE sweep_name=?",
                (name,),
            ).fetchone()
        )

    @staticmethod
    def _saveSweep(
        connection: sqlite3.Connection,
        cursor: _SweepCursor,
        *,
        now: float,
    ) -> None:
        if cursor.name not in _SWEEP_NAMES:
            raise ContinuationError("CONTINUATION_CORRUPT")
        changed = connection.execute(
            "UPDATE continuation_sweeps SET cursor_digest=?, cursor_value=?, cycle=?, updated_at=? WHERE sweep_name=?",
            (cursor.digest, cursor.value, cursor.cycle, now, cursor.name),
        ).rowcount
        if changed != 1:
            raise ContinuationError("CONTINUATION_CORRUPT")

    @staticmethod
    def _pinsFromRow(row: sqlite3.Row) -> ContinuationPins:
        return ContinuationPins(
            sourceDigest=_ContinuationStoreBase._storedDigest(row["source_digest"]),
            queryDigest=_ContinuationStoreBase._storedDigest(row["query_digest"]),
            contractDigest=_ContinuationStoreBase._storedDigest(row["contract_digest"]),
            schemaDigest=_ContinuationStoreBase._storedDigest(row["schema_digest"]),
        )

    @staticmethod
    def _validatePins(stored: ContinuationPins, current: ContinuationPins) -> None:
        mismatches = (
            (stored.sourceDigest, current.sourceDigest, "CONTINUATION_SOURCE_STALE"),
            (stored.queryDigest, current.queryDigest, "CONTINUATION_QUERY_STALE"),
            (stored.contractDigest, current.contractDigest, "CONTINUATION_CONTRACT_STALE"),
            (stored.schemaDigest, current.schemaDigest, "CONTINUATION_SCHEMA_STALE"),
        )
        for storedValue, currentValue, code in mismatches:
            if not hmac.compare_digest(storedValue, currentValue):
                raise ContinuationError(code)

    @staticmethod
    def _validateQueryState(state: ContinuationQueryState, pins: ContinuationPins) -> None:
        if not hmac.compare_digest(bytesDigest(state.queryPayload), pins.queryDigest):
            raise ContinuationError("CONTINUATION_QUERY_STALE")

    @staticmethod
    def _requireLiveRow(row: sqlite3.Row | None, now: float) -> sqlite3.Row:
        if row is None:
            raise ContinuationError("CONTINUATION_INVALID")
        expired = _ContinuationStoreBase._storedFloat(row["expires_at"]) <= now
        if expired:
            raise ContinuationError("CONTINUATION_EXPIRED")
        return row
