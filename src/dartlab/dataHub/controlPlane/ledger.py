"""SQLite metadata와 private CAS를 결합한 DataHub job ledger."""

from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Iterator, Mapping

from dartlab.dataHub.continuation import ArtifactStore, canonicalJsonBytes
from dartlab.dataHub.continuation.privateStorage import securePrivatePath

from .contracts import DataHubJob, DataHubLease, DataHubMaintenanceReport
from .errors import DataHubControlError

_JOB_ID = re.compile(r"^[0-9a-f]{32}$")
_ERROR_CODE = re.compile(r"^[A-Z][A-Z0-9_]{2,127}$")
_MAX_REQUEST_BYTES = 1024 * 1024
_MAX_RESULT_BYTES = 16 * 1024 * 1024


def _identityDigest(value: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 4096:
        raise DataHubControlError("DATA_HUB_INVALID")
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _requirePositiveSeconds(value: float, *, maximum: float) -> float:
    if type(value) not in (int, float) or not math.isfinite(float(value)):
        raise DataHubControlError("DATA_HUB_INVALID")
    normalized = float(value)
    if normalized <= 0 or normalized > maximum:
        raise DataHubControlError("DATA_HUB_INVALID")
    return normalized


def _durableQuery(query: Mapping[str, Any]) -> dict[str, Any]:
    """비동기 query를 기본 immutable refresh 정책으로 정규화한다."""

    if not isinstance(query, Mapping):
        raise DataHubControlError("DATA_HUB_INVALID")
    payload = dict(query)
    if "continuation" not in payload:
        materialization = payload.get("materialization")
        if materialization is None or materialization == "runtime":
            payload["materialization"] = {"mode": "refresh"}
        elif isinstance(materialization, Mapping) and materialization.get("mode", "runtime") == "runtime":
            payload["materialization"] = {"mode": "refresh"}
    return payload


# wire codec 이 Arrow payload 를 base64 로 감싸므로 결과는 원시 대비 약 4/3 로 커진다.
# 여유를 조금 두고 계산한 원시 상한이다.
_MAX_RAW_RESULT_BYTES = (_MAX_RESULT_BYTES * 3) // 4 - 64 * 1024


def _requireResultBudgetFits(query: Any) -> None:
    """결과가 wire 상한을 넘길 예산이면 제출 시점에 거부한다.

    Capabilities:
        6 시간짜리 계산을 세 번 반복한 뒤에야 예산 오류로 죽는 낭비를 막는다.

    Args:
        query: 제출한 query mapping.

    Raises:
        DataHubControlError: query byte 예산이 wire 상한을 넘길 때
            ``DATA_HUB_PAYLOAD_BUDGET``.

    Example:
        ``_requireResultBudgetFits(query)``.

    Guide:
        page 예산과 결과 상한은 서로 다른 계층이라 자동으로 맞춰지지 않는다.

    When:
        job 을 ledger 에 넣기 직전에 검사한다.

    How:
        base64 팽창을 반영한 원시 상한과 query 의 `maxBytes` 를 비교한다.

    See Also:
        ``dartlab.dataHub.transport.resultCodec``.

    Requires:
        예산을 명시하지 않은 query 는 기본값이 상한 안이므로 통과시킨다.

    AI Context:
        worker 재시도는 결정적 예산 위반을 고쳐주지 못한다. 제출에서 막아야 한다.
    """

    if not isinstance(query, dict):
        return
    budget = query.get("budget")
    if not isinstance(budget, dict):
        return
    maxBytes = budget.get("maxBytes")
    if type(maxBytes) is int and maxBytes > _MAX_RAW_RESULT_BYTES:
        raise DataHubControlError("DATA_HUB_PAYLOAD_BUDGET")


class DataHubJobLedger:
    """원격 worker가 경쟁할 수 있는 durable lease queue."""

    def __init__(
        self,
        root: Path,
        *,
        clock: Callable[[], float] = time.time,
    ):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        securePrivatePath(self.root)
        self.databasePath = self.root / "jobs.sqlite3"
        self.artifacts = ArtifactStore(self.root / "artifacts")
        self._clock = clock
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.databasePath,
            timeout=30,
            isolation_level=None,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=30000")
        return connection

    @contextmanager
    def _connection(self, *, immediate: bool = False) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _enableWriteAheadLog(self) -> None:
        """WAL 저널 활성화. `materialization.ledger`, `continuation.continuationStore` 와 동일 계약.

        journal_mode 는 트랜잭션 안에서 바꿀 수 없으므로 `_initialize` 의 IMMEDIATE
        트랜잭션 진입 전에 raw 연결로 한 번 설정한다. WAL 은 DB 파일에 영속하는
        속성이라 이후 연결은 다시 설정할 필요가 없다. 기본 delete 저널이면 reader 가
        writer 를 전면 차단해 worker 수만큼 claim 이 직렬화된다.
        """
        connection = self._connect()
        try:
            connection.execute("PRAGMA journal_mode=WAL")
        finally:
            connection.close()

    def _initialize(self) -> None:
        self._enableWriteAheadLog()
        with self._connection(immediate=True) as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS data_hub_jobs (
                    job_id TEXT PRIMARY KEY,
                    idempotency_digest TEXT UNIQUE,
                    request_digest TEXT NOT NULL,
                    request_bytes INTEGER NOT NULL CHECK(request_bytes >= 0),
                    state TEXT NOT NULL CHECK(state IN ('queued','leased','succeeded','failed','cancelled')),
                    priority INTEGER NOT NULL,
                    attempt_count INTEGER NOT NULL CHECK(attempt_count >= 0),
                    max_attempts INTEGER NOT NULL CHECK(max_attempts > 0),
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    available_at REAL NOT NULL,
                    lease_worker_digest TEXT,
                    lease_epoch INTEGER NOT NULL CHECK(lease_epoch >= 0),
                    lease_expires_at REAL,
                    result_digest TEXT,
                    result_bytes INTEGER CHECK(result_bytes IS NULL OR result_bytes >= 0),
                    error_code TEXT
                );
                CREATE INDEX IF NOT EXISTS data_hub_jobs_claim
                ON data_hub_jobs(state, available_at, priority DESC, created_at, job_id);
                CREATE INDEX IF NOT EXISTS data_hub_jobs_updated
                ON data_hub_jobs(state, updated_at);
                """
            )
        securePrivatePath(self.databasePath)

    @staticmethod
    def _validateJobId(jobId: str) -> None:
        if not isinstance(jobId, str) or _JOB_ID.fullmatch(jobId) is None:
            raise DataHubControlError("DATA_HUB_INVALID")

    @staticmethod
    def _job(row: sqlite3.Row) -> DataHubJob:
        return DataHubJob(
            jobId=row["job_id"],
            state=row["state"],
            requestDigest=row["request_digest"],
            priority=row["priority"],
            attemptCount=row["attempt_count"],
            maxAttempts=row["max_attempts"],
            createdAt=row["created_at"],
            updatedAt=row["updated_at"],
            availableAt=row["available_at"],
            leaseEpoch=row["lease_epoch"],
            leaseExpiresAt=row["lease_expires_at"],
            resultDigest=row["result_digest"],
            errorCode=row["error_code"],
        )

    def submit(
        self,
        query: Mapping[str, Any],
        *,
        idempotencyKey: str | None = None,
        priority: int = 0,
        maxAttempts: int = 3,
    ) -> DataHubJob:
        """Query를 durable queue에 원자 등록한다."""

        if type(priority) is not int or not -100 <= priority <= 100:
            raise DataHubControlError("DATA_HUB_INVALID")
        if type(maxAttempts) is not int or not 1 <= maxAttempts <= 10:
            raise DataHubControlError("DATA_HUB_INVALID")
        requestPayload = canonicalJsonBytes(
            {
                "formatVersion": 1,
                "query": _durableQuery(query),
            }
        )
        if len(requestPayload) > _MAX_REQUEST_BYTES:
            raise DataHubControlError("DATA_HUB_PAYLOAD_BUDGET")
        _requireResultBudgetFits(query)
        requestDigest = hashlib.sha256(requestPayload).hexdigest()
        idempotencyDigest = _identityDigest(idempotencyKey) if idempotencyKey is not None else None
        now = self._clock()
        with self._connection(immediate=True) as connection:
            if idempotencyDigest is not None:
                existing = connection.execute(
                    "SELECT * FROM data_hub_jobs WHERE idempotency_digest=?",
                    (idempotencyDigest,),
                ).fetchone()
                if existing is not None:
                    if existing["request_digest"] != requestDigest:
                        raise DataHubControlError("DATA_HUB_CONFLICT")
                    return self._job(existing)
            committedDigest = self.artifacts.putBytes(requestPayload)
            if committedDigest != requestDigest:
                raise DataHubControlError("DATA_HUB_CORRUPT")
            jobId = uuid.uuid4().hex
            connection.execute(
                """
                INSERT INTO data_hub_jobs (
                    job_id, idempotency_digest, request_digest, request_bytes,
                    state, priority, attempt_count, max_attempts,
                    created_at, updated_at, available_at, lease_epoch
                ) VALUES (?, ?, ?, ?, 'queued', ?, 0, ?, ?, ?, ?, 0)
                """,
                (
                    jobId,
                    idempotencyDigest,
                    requestDigest,
                    len(requestPayload),
                    priority,
                    maxAttempts,
                    now,
                    now,
                    now,
                ),
            )
            row = connection.execute("SELECT * FROM data_hub_jobs WHERE job_id=?", (jobId,)).fetchone()
        if row is None:
            raise DataHubControlError("DATA_HUB_CORRUPT")
        return self._job(row)

    def get(self, jobId: str) -> DataHubJob:
        """Job의 현재 durable 상태를 읽는다."""

        self._validateJobId(jobId)
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM data_hub_jobs WHERE job_id=?", (jobId,)).fetchone()
        if row is None:
            raise DataHubControlError("DATA_HUB_NOT_FOUND")
        return self._job(row)

    def _expireLeases(
        self,
        connection: sqlite3.Connection,
        *,
        now: float,
        maximum: int,
    ) -> tuple[int, int]:
        rows = connection.execute(
            """
            SELECT job_id, attempt_count, max_attempts
            FROM data_hub_jobs
            WHERE state='leased' AND lease_expires_at <= ?
            ORDER BY lease_expires_at, job_id
            LIMIT ?
            """,
            (now, maximum),
        ).fetchall()
        requeued = 0
        failed = 0
        for row in rows:
            if row["attempt_count"] >= row["max_attempts"]:
                state = "failed"
                errorCode = "DATA_HUB_ATTEMPTS_EXHAUSTED"
                failed += 1
            else:
                state = "queued"
                errorCode = None
                requeued += 1
            connection.execute(
                """
                UPDATE data_hub_jobs
                SET state=?, updated_at=?, available_at=?,
                    lease_worker_digest=NULL, lease_expires_at=NULL, error_code=?
                WHERE job_id=? AND state='leased'
                """,
                (state, now, now, errorCode, row["job_id"]),
            )
        return requeued, failed

    def claim(
        self,
        workerId: str,
        *,
        leaseSeconds: float = 60.0,
    ) -> DataHubLease | None:
        """가장 높은 우선순위의 ready job을 worker에게 원자 임대한다."""

        leaseDuration = _requirePositiveSeconds(leaseSeconds, maximum=3600)
        workerDigest = _identityDigest(workerId)
        now = self._clock()
        with self._connection(immediate=True) as connection:
            self._expireLeases(connection, now=now, maximum=100)
            row = connection.execute(
                """
                SELECT *
                FROM data_hub_jobs
                WHERE state='queued' AND available_at <= ?
                ORDER BY priority DESC, created_at, job_id
                LIMIT 1
                """,
                (now,),
            ).fetchone()
            if row is None:
                return None
            leaseEpoch = row["lease_epoch"] + 1
            leaseExpiresAt = now + leaseDuration
            cursor = connection.execute(
                """
                UPDATE data_hub_jobs
                SET state='leased', updated_at=?, lease_worker_digest=?,
                    lease_epoch=?, lease_expires_at=?, attempt_count=attempt_count + 1,
                    error_code=NULL
                WHERE job_id=? AND state='queued'
                """,
                (now, workerDigest, leaseEpoch, leaseExpiresAt, row["job_id"]),
            )
            if cursor.rowcount != 1:
                raise DataHubControlError("DATA_HUB_CONFLICT")
            claimed = connection.execute(
                "SELECT * FROM data_hub_jobs WHERE job_id=?",
                (row["job_id"],),
            ).fetchone()
        if claimed is None:
            raise DataHubControlError("DATA_HUB_CORRUPT")
        requestPayload = self.artifacts.readBytes(
            claimed["request_digest"],
            maxBytes=_MAX_REQUEST_BYTES,
            budgetCode="CONTINUATION_STATE_BUDGET",
        )
        try:
            tree = json.loads(requestPayload)
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise DataHubControlError("DATA_HUB_CORRUPT") from None
        if not isinstance(tree, dict) or set(tree) != {"formatVersion", "query"} or tree["formatVersion"] != 1:
            raise DataHubControlError("DATA_HUB_CORRUPT")
        if not isinstance(tree["query"], dict):
            raise DataHubControlError("DATA_HUB_CORRUPT")
        return DataHubLease(
            job=self._job(claimed),
            workerDigest=workerDigest,
            leaseEpoch=leaseEpoch,
            leaseExpiresAt=leaseExpiresAt,
            request=tree["query"],
        )

    def _leaseRow(
        self,
        connection: sqlite3.Connection,
        *,
        jobId: str,
        workerId: str,
        leaseEpoch: int,
        now: float,
    ) -> sqlite3.Row:
        self._validateJobId(jobId)
        if type(leaseEpoch) is not int or leaseEpoch <= 0:
            raise DataHubControlError("DATA_HUB_INVALID")
        workerDigest = _identityDigest(workerId)
        row = connection.execute("SELECT * FROM data_hub_jobs WHERE job_id=?", (jobId,)).fetchone()
        if row is None:
            raise DataHubControlError("DATA_HUB_NOT_FOUND")
        if (
            row["state"] != "leased"
            or row["lease_worker_digest"] != workerDigest
            or row["lease_epoch"] != leaseEpoch
            or row["lease_expires_at"] is None
            or row["lease_expires_at"] <= now
        ):
            raise DataHubControlError("DATA_HUB_LEASE_LOST")
        return row

    def heartbeat(
        self,
        jobId: str,
        workerId: str,
        leaseEpoch: int,
        *,
        leaseSeconds: float = 60.0,
    ) -> DataHubJob:
        """유효한 worker lease를 bounded 기간만 연장한다."""

        leaseDuration = _requirePositiveSeconds(leaseSeconds, maximum=3600)
        now = self._clock()
        with self._connection(immediate=True) as connection:
            self._leaseRow(
                connection,
                jobId=jobId,
                workerId=workerId,
                leaseEpoch=leaseEpoch,
                now=now,
            )
            connection.execute(
                "UPDATE data_hub_jobs SET updated_at=?, lease_expires_at=? WHERE job_id=?",
                (now, now + leaseDuration, jobId),
            )
            row = connection.execute("SELECT * FROM data_hub_jobs WHERE job_id=?", (jobId,)).fetchone()
        if row is None:
            raise DataHubControlError("DATA_HUB_CORRUPT")
        return self._job(row)

    def complete(
        self,
        jobId: str,
        workerId: str,
        leaseEpoch: int,
        resultPayload: bytes,
    ) -> DataHubJob:
        """유효 lease의 wire result를 CAS에 기록하고 성공 전이한다."""

        if not isinstance(resultPayload, bytes):
            raise DataHubControlError("DATA_HUB_INVALID")
        if len(resultPayload) > _MAX_RESULT_BYTES:
            raise DataHubControlError("DATA_HUB_PAYLOAD_BUDGET")
        now = self._clock()
        with self._connection(immediate=True) as connection:
            self._leaseRow(
                connection,
                jobId=jobId,
                workerId=workerId,
                leaseEpoch=leaseEpoch,
                now=now,
            )
            resultDigest = self.artifacts.putBytes(resultPayload)
            connection.execute(
                """
                UPDATE data_hub_jobs
                SET state='succeeded', updated_at=?, result_digest=?, result_bytes=?,
                    lease_worker_digest=NULL, lease_expires_at=NULL, error_code=NULL
                WHERE job_id=?
                """,
                (now, resultDigest, len(resultPayload), jobId),
            )
            row = connection.execute("SELECT * FROM data_hub_jobs WHERE job_id=?", (jobId,)).fetchone()
        if row is None:
            raise DataHubControlError("DATA_HUB_CORRUPT")
        return self._job(row)

    def fail(
        self,
        jobId: str,
        workerId: str,
        leaseEpoch: int,
        *,
        errorCode: str,
        retryDelaySeconds: float = 0,
    ) -> DataHubJob:
        """Worker 실패를 retry 또는 terminal 실패로 전이한다."""

        if not isinstance(errorCode, str) or _ERROR_CODE.fullmatch(errorCode) is None:
            raise DataHubControlError("DATA_HUB_INVALID")
        delay = _requirePositiveSeconds(retryDelaySeconds, maximum=86400) if retryDelaySeconds else 0.0
        now = self._clock()
        with self._connection(immediate=True) as connection:
            current = self._leaseRow(
                connection,
                jobId=jobId,
                workerId=workerId,
                leaseEpoch=leaseEpoch,
                now=now,
            )
            terminal = current["attempt_count"] >= current["max_attempts"]
            state = "failed" if terminal else "queued"
            finalCode = "DATA_HUB_ATTEMPTS_EXHAUSTED" if terminal else errorCode
            connection.execute(
                """
                UPDATE data_hub_jobs
                SET state=?, updated_at=?, available_at=?, error_code=?,
                    lease_worker_digest=NULL, lease_expires_at=NULL
                WHERE job_id=?
                """,
                (state, now, now + delay, finalCode, jobId),
            )
            row = connection.execute("SELECT * FROM data_hub_jobs WHERE job_id=?", (jobId,)).fetchone()
        if row is None:
            raise DataHubControlError("DATA_HUB_CORRUPT")
        return self._job(row)

    def cancel(self, jobId: str) -> DataHubJob:
        """Queued 또는 leased job을 즉시 terminal 취소로 전이한다."""

        self._validateJobId(jobId)
        now = self._clock()
        with self._connection(immediate=True) as connection:
            row = connection.execute("SELECT * FROM data_hub_jobs WHERE job_id=?", (jobId,)).fetchone()
            if row is None:
                raise DataHubControlError("DATA_HUB_NOT_FOUND")
            if row["state"] not in {"succeeded", "failed", "cancelled"}:
                connection.execute(
                    """
                    UPDATE data_hub_jobs
                    SET state='cancelled', updated_at=?, lease_worker_digest=NULL,
                        lease_expires_at=NULL, error_code='DATA_HUB_CANCELLED'
                    WHERE job_id=?
                    """,
                    (now, jobId),
                )
                row = connection.execute("SELECT * FROM data_hub_jobs WHERE job_id=?", (jobId,)).fetchone()
        if row is None:
            raise DataHubControlError("DATA_HUB_CORRUPT")
        return self._job(row)

    def readResult(self, jobId: str) -> bytes:
        """성공한 job의 검증된 wire result bytes를 읽는다."""

        self._validateJobId(jobId)
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM data_hub_jobs WHERE job_id=?", (jobId,)).fetchone()
        if row is None:
            raise DataHubControlError("DATA_HUB_NOT_FOUND")
        if row["state"] == "cancelled":
            raise DataHubControlError("DATA_HUB_CANCELLED")
        if row["state"] != "succeeded" or row["result_digest"] is None:
            raise DataHubControlError("DATA_HUB_NOT_READY")
        return self.artifacts.readBytes(
            row["result_digest"],
            maxBytes=_MAX_RESULT_BYTES,
            budgetCode="CONTINUATION_STATE_BUDGET",
        )

    def maintain(
        self,
        *,
        maximum: int = 100,
        retentionSeconds: float = 7 * 24 * 60 * 60,
    ) -> DataHubMaintenanceReport:
        """만료 lease와 오래된 terminal job을 bounded하게 정리한다."""

        if type(maximum) is not int or maximum <= 0 or maximum > 10_000:
            raise DataHubControlError("DATA_HUB_INVALID")
        retention = _requirePositiveSeconds(retentionSeconds, maximum=365 * 24 * 60 * 60)
        now = self._clock()
        deleteDigests: list[str] = []
        with self._connection(immediate=True) as connection:
            requeued, failed = self._expireLeases(connection, now=now, maximum=maximum)
            rows = connection.execute(
                """
                SELECT job_id, request_digest, result_digest
                FROM data_hub_jobs
                WHERE state IN ('succeeded','failed','cancelled') AND updated_at <= ?
                ORDER BY updated_at, job_id
                LIMIT ?
                """,
                (now - retention, maximum),
            ).fetchall()
            for row in rows:
                connection.execute("DELETE FROM data_hub_jobs WHERE job_id=?", (row["job_id"],))
                for digest in (row["request_digest"], row["result_digest"]):
                    if digest is None:
                        continue
                    referenced = connection.execute(
                        """
                        SELECT 1 FROM data_hub_jobs
                        WHERE request_digest=? OR result_digest=?
                        LIMIT 1
                        """,
                        (digest, digest),
                    ).fetchone()
                    if referenced is None:
                        deleteDigests.append(digest)
        artifactsDeleted = 0
        for digest in dict.fromkeys(deleteDigests):
            deleted, _freed = self.artifacts.deleteBytes(digest)
            if deleted:
                artifactsDeleted += 1
        return DataHubMaintenanceReport(
            leasesRequeued=requeued,
            leasesFailed=failed,
            jobsDeleted=len(rows),
            artifactsDeleted=artifactsDeleted,
        )
