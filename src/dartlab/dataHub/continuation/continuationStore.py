"""Durable continuation ledger, claim coordinator, replay, and expiry GC."""

from __future__ import annotations

import hashlib
import hmac
import math
import re
import secrets
import sqlite3
import threading
import time
import uuid
from collections.abc import Callable

from dartlab.dataHub.telemetry import dataHubLogger, recordFailure

from .contracts import (
    ArrowPayloadFacts,
    ContinuationError,
    ContinuationPage,
    ContinuationPins,
    ContinuationQueryState,
    IssuedContinuation,
    LoadedContinuationContext,
    PageEnvelope,
)
from .queryState import decodeQueryState, encodeQueryState
from .tokens import childToken, encodeToken, tokenDigest

_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_INITIALIZE_LOCK = threading.Lock()
_PayloadValidator = Callable[..., ArrowPayloadFacts]
_SCHEMA_VERSION = 3
_SWEEP_NAMES = frozenset({"artifacts", "cas", "roots"})


from .storeBase import _LeaseHeartbeat, _resultDigest
from .storeIntegrity import _ContinuationStoreIntegrity

_log = dataHubLogger(__name__)


class ContinuationStore(_ContinuationStoreIntegrity):
    """단일 host의 thread와 process가 공유하는 continuation control plane.

    Args:
        root: private ledger와 CAS 전용 directory.
        policy: page, state, lifetime, claim, GC bounds.
        clock: Unix time supplier.
        payloadValidator: Arrow IPC actual-facts validator seam.

    Returns:
        durable issue, load, redeem, replay, prune 기능을 가진 store.

    Raises:
        ContinuationError: ledger, CAS, pin, payload 검증 실패 시.

    Example:
        ``store = ContinuationStore(controlRoot)``.

    Guide:
        기존 data query 축 내부에서만 사용하고 별도 public axis로 노출하지 않는다.

    SeeAlso:
        ``ContinuationQueryState``, ``PageEnvelope``.

    Requires:
        materialize callback은 pinned source를 읽는 결정적 read여야 한다.

    AIContext:
        SQLite에는 digest와 bounded metadata만, private 원문은 CAS에만 둔다.
    """

    def issue(
        self,
        state: ContinuationQueryState,
        pins: ContinuationPins,
        *,
        ttlSeconds: float | None = None,
    ) -> IssuedContinuation:
        """Private state를 CAS에 넣고 random bearer token을 발급한다.

        Capabilities:
            bounded state CAS registration과 random token issuance를 원자 조정한다.

        Args:
            state: canonical query와 initial owner cursor.
            pins: source, query, contract, Arrow schema pins.
            ttlSeconds: optional absolute chain lifetime override.

        Returns:
            plaintext token을 1회 담은 repr-safe issuance result.

        Raises:
            ContinuationError: state budget 또는 query pin이 다를 때.

        Example:
            ``issued = store.issue(state, pins)``.

        Guide:
            token 원문은 caller만 보관하고 lineage에는 tokenDigest만 쓴다.

        When:
            bounded 첫 page 이후 다음 owner cursor를 외부 caller에게 넘길 때 호출한다.

        How:
            query pin을 검증하고 SQLite write lock 안에서 CAS와 root row를 등록한다.

        SeeAlso:
            ``loadContext``, ``redeem``.

        Requires:
            state.queryPayload는 pins.queryDigest의 정확한 preimage여야 한다.

        AIContext:
            state CAS write와 ledger registration은 같은 SQLite write lock 안에서 수행한다.
        """
        encodedState = encodeQueryState(state, maxBytes=self.policy.maxStateBytes)
        self._validateQueryState(state, pins)
        ttl = self.policy.tokenTtlSeconds if ttlSeconds is None else ttlSeconds
        try:
            if type(ttl) not in (int, float):
                raise ValueError
            ttlValue = float(ttl)
        except (TypeError, ValueError, OverflowError):
            raise ValueError("ttlSeconds는 유한한 양수여야 합니다") from None
        if not math.isfinite(ttlValue) or ttlValue <= 0:
            raise ValueError("ttlSeconds는 유한한 양수여야 합니다")
        now = self._now()
        expiresAt = now + ttlValue
        if not math.isfinite(expiresAt):
            raise ValueError("ttlSeconds가 유효한 만료 시각을 만들 수 없습니다")
        stagedState = self._stageArtifact(encodedState, now=now)
        for _attempt in range(self.policy.maxTokenIssueAttempts):
            token = encodeToken(secrets.token_bytes(32))
            tokenDigestValue = tokenDigest(token)
            try:
                with self._connection() as connection:
                    connection.execute("BEGIN IMMEDIATE")
                    connection.execute(
                        "INSERT INTO continuations (token_digest, chain_root_digest, parent_token_digest, "
                        "state_digest, source_digest, query_digest, contract_digest, schema_digest, "
                        "issued_at, expires_at, status) VALUES (?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, 'PENDING')",
                        (
                            tokenDigestValue,
                            tokenDigestValue,
                            stagedState.digest,
                            pins.sourceDigest,
                            pins.queryDigest,
                            pins.contractDigest,
                            pins.schemaDigest,
                            now,
                            expiresAt,
                        ),
                    )
                    self._referenceArtifact(connection, stagedState, now=now)
                return IssuedContinuation(token, tokenDigestValue, expiresAt)
            except sqlite3.IntegrityError as error:
                if self._isTokenCollision(error):
                    continue
                raise ContinuationError("CONTINUATION_CORRUPT") from None
        raise ContinuationError("CONTINUATION_TOKEN_COLLISION")

    def loadContext(self, token: str) -> LoadedContinuationContext:
        """token을 검증하고 private CAS state와 stored pins를 복원한다.

        Capabilities:
            token 형식, 존재, 만료, state digest, query pin을 한 경로에서 검증한다.

        Args:
            token: issue 또는 이전 page가 반환한 opaque bearer token.

        Returns:
            token 원문이 없는 private state, pins, lifetime context.

        Raises:
            ContinuationError: 형식, 존재, 만료, CAS, state 검증 실패 시.

        Example:
            ``context = store.loadContext(token)``.

        Guide:
            상위 query 복원은 context.state.queryPayload를 내부에서만 decode한다.

        When:
            continuation-only query가 원래 query와 owner cursor를 복원해야 할 때 호출한다.

        How:
            SQLite write lock으로 prune을 막고 bounded CAS state를 읽어 decode한다.

        SeeAlso:
            ``issue``, ``redeem``.

        Requires:
            private state는 repr, gap, SQLite에 복사하지 않는다.

        AIContext:
            BEGIN IMMEDIATE 동안 CAS를 읽어 prune과 registration race를 차단한다.
        """
        return self._loadContext(token, busySeconds=None)

    def _loadContext(self, token: str, *, busySeconds: float | None) -> LoadedContinuationContext:
        tokenDigestValue = tokenDigest(token)
        now = self._now()
        try:
            with self._connection(busySeconds=busySeconds) as connection:
                connection.execute("BEGIN IMMEDIATE")
                row = self._requireLiveRow(
                    connection.execute(
                        "SELECT * FROM continuations WHERE token_digest=?",
                        (tokenDigestValue,),
                    ).fetchone(),
                    now,
                )
                pins = self._pinsFromRow(row)
                stateDigest = self._storedDigest(row["state_digest"])
                artifact = self._requireReferencedArtifact(connection, stateDigest)
                encodedState = self.cas.readBytes(stateDigest, maxBytes=self.policy.maxStateBytes)
                if len(encodedState) != self._storedInt(artifact["byte_count"]):
                    raise ContinuationError("CONTINUATION_CORRUPT")
                state = decodeQueryState(encodedState, maxBytes=self.policy.maxStateBytes)
                self._validateQueryState(state, pins)
                return LoadedContinuationContext(
                    tokenDigest=tokenDigestValue,
                    state=state,
                    pins=pins,
                    issuedAt=self._storedFloat(row["issued_at"]),
                    expiresAt=self._storedFloat(row["expires_at"]),
                )
        except sqlite3.OperationalError as error:
            if self._isSqliteBusy(error):
                raise ContinuationError("CONTINUATION_BUSY") from None
            raise ContinuationError("CONTINUATION_CORRUPT") from None

    def _claim(
        self,
        tokenDigestValue: str,
        pins: ContinuationPins,
        ownerId: str,
        *,
        busySeconds: float | None = None,
    ) -> tuple[str, sqlite3.Row]:
        now = self._now()
        try:
            with self._connection(busySeconds=busySeconds) as connection:
                connection.execute("BEGIN IMMEDIATE")
                row = self._requireLiveRow(
                    connection.execute(
                        "SELECT * FROM continuations WHERE token_digest=?",
                        (tokenDigestValue,),
                    ).fetchone(),
                    now,
                )
                self._validatePins(self._pinsFromRow(row), pins)
                status = row["status"]
                if type(status) is not str or status not in {"PENDING", "RUNNING", "SUCCEEDED"}:
                    raise ContinuationError("CONTINUATION_CORRUPT")
                if status == "SUCCEEDED":
                    return "REPLAY", row
                if status == "PENDING" or self._storedFloat(row["lease_until"]) <= now:
                    changed = connection.execute(
                        "UPDATE continuations SET status='RUNNING', owner_id=?, lease_until=? "
                        "WHERE token_digest=? AND status!='SUCCEEDED'",
                        (ownerId, now + self.policy.leaseSeconds, tokenDigestValue),
                    ).rowcount
                    if changed != 1:
                        raise ContinuationError("CONTINUATION_BUSY")
                    claimed = connection.execute(
                        "SELECT * FROM continuations WHERE token_digest=?",
                        (tokenDigestValue,),
                    ).fetchone()
                    if claimed is None:
                        raise ContinuationError("CONTINUATION_CORRUPT")
                    return "ACQUIRED", claimed
                return "BUSY", row
        except sqlite3.OperationalError as error:
            if self._isSqliteBusy(error):
                raise ContinuationError("CONTINUATION_BUSY") from None
            raise ContinuationError("CONTINUATION_CORRUPT") from None

    def _renew(self, tokenDigestValue: str, ownerId: str) -> bool:
        now = self._now()
        with self._connection() as connection:
            changed = connection.execute(
                "UPDATE continuations SET lease_until=? WHERE token_digest=? AND status='RUNNING' "
                "AND owner_id=? AND expires_at>?",
                (now + self.policy.leaseSeconds, tokenDigestValue, ownerId, now),
            ).rowcount
        return changed == 1

    def _release(self, tokenDigestValue: str, ownerId: str) -> None:
        with self._connection() as connection:
            connection.execute(
                "UPDATE continuations SET status='PENDING', owner_id=NULL, lease_until=0 "
                "WHERE token_digest=? AND status='RUNNING' AND owner_id=?",
                (tokenDigestValue, ownerId),
            )

    def _validatePage(self, envelope: PageEnvelope, pins: ContinuationPins) -> ArrowPayloadFacts:
        if envelope.rowCount > self.policy.maxPageRows:
            raise ContinuationError("CONTINUATION_ROW_BUDGET")
        return self.payloadValidator(
            envelope.payload,
            claimedRowCount=envelope.rowCount,
            expectedSchemaDigest=pins.schemaDigest,
            maxPageBytes=self.policy.maxPageBytes,
            maxLogicalBytes=self.policy.maxPageLogicalBytes,
        )

    def _pageFromRow(
        self,
        connection: sqlite3.Connection,
        token: str,
        row: sqlite3.Row,
        *,
        replayed: bool,
    ) -> ContinuationPage:
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
        if rowCount < 0 or rowCount > self.policy.maxPageRows or byteCount != len(payload):
            raise ContinuationError("CONTINUATION_CORRUPT")
        pins = self._pinsFromRow(row)
        facts = self.payloadValidator(
            payload,
            claimedRowCount=rowCount,
            expectedSchemaDigest=pins.schemaDigest,
            maxPageBytes=self.policy.maxPageBytes,
            maxLogicalBytes=self.policy.maxPageLogicalBytes,
        )
        nextToken = None
        nextTokenDigestValue = row["next_token_digest"]
        nextStateDigest = row["next_state_digest"]
        if (nextTokenDigestValue is None) != (nextStateDigest is None):
            raise ContinuationError("CONTINUATION_CORRUPT")
        if nextTokenDigestValue is not None and nextStateDigest is not None:
            nextTokenDigestValue = self._storedDigest(nextTokenDigestValue)
            nextStateDigest = self._storedDigest(nextStateDigest)
            nextToken = childToken(token, pageDigest, nextStateDigest)
            if not hmac.compare_digest(tokenDigest(nextToken), nextTokenDigestValue):
                raise ContinuationError("CONTINUATION_CORRUPT")
            child = connection.execute(
                "SELECT * FROM continuations WHERE token_digest=?",
                (nextTokenDigestValue,),
            ).fetchone()
            if child is None:
                raise ContinuationError("CONTINUATION_CORRUPT")
            if self._storedDigest(child["state_digest"]) != nextStateDigest:
                raise ContinuationError("CONTINUATION_CORRUPT")
            if self._storedDigest(child["parent_token_digest"]) != self._storedDigest(row["token_digest"]):
                raise ContinuationError("CONTINUATION_CORRUPT")
            if self._storedDigest(child["chain_root_digest"]) != self._storedDigest(row["chain_root_digest"]):
                raise ContinuationError("CONTINUATION_CORRUPT")
            if self._pinsFromRow(child) != pins or self._storedFloat(child["expires_at"]) != self._storedFloat(
                row["expires_at"]
            ):
                raise ContinuationError("CONTINUATION_CORRUPT")
        expectedResultDigest = _resultDigest(
            self._storedDigest(row["token_digest"]),
            pins,
            pageDigest,
            rowCount,
            byteCount,
            nextTokenDigestValue,
        )
        if not hmac.compare_digest(expectedResultDigest, self._storedDigest(row["result_digest"])):
            raise ContinuationError("CONTINUATION_CORRUPT")
        return ContinuationPage(
            pageRef=f"cas:sha256:{pageDigest}",
            pageDigest=pageDigest,
            payload=payload,
            rowCount=facts.rowCount,
            byteCount=facts.byteCount,
            schemaDigest=facts.schemaDigest,
            nextToken=nextToken,
            replayed=replayed,
            resultDigest=expectedResultDigest,
        )

    def _replay(
        self,
        token: str,
        pins: ContinuationPins,
        *,
        busySeconds: float | None = None,
    ) -> ContinuationPage:
        tokenDigestValue = tokenDigest(token)
        try:
            with self._connection(busySeconds=busySeconds) as connection:
                connection.execute("BEGIN IMMEDIATE")
                row = self._requireLiveRow(
                    connection.execute(
                        "SELECT * FROM continuations WHERE token_digest=?",
                        (tokenDigestValue,),
                    ).fetchone(),
                    self._now(),
                )
                self._validatePins(self._pinsFromRow(row), pins)
                if row["status"] != "SUCCEEDED":
                    raise ContinuationError("CONTINUATION_BUSY")
                return self._pageFromRow(connection, token, row, replayed=True)
        except sqlite3.OperationalError as error:
            if self._isSqliteBusy(error):
                raise ContinuationError("CONTINUATION_BUSY") from None
            raise ContinuationError("CONTINUATION_CORRUPT") from None

    def _commit(
        self,
        token: str,
        context: LoadedContinuationContext,
        ownerId: str,
        envelope: PageEnvelope,
    ) -> ContinuationPage:
        facts = self._validatePage(envelope, context.pins)
        pageDigest = hashlib.sha256(envelope.payload).hexdigest()
        encodedNextState = None
        nextStateDigest = None
        nextToken = None
        nextTokenDigestValue = None
        if envelope.nextState is not None:
            self._validateQueryState(envelope.nextState, context.pins)
            encodedNextState = encodeQueryState(envelope.nextState, maxBytes=self.policy.maxStateBytes)
            nextStateDigest = hashlib.sha256(encodedNextState).hexdigest()
            nextToken = childToken(token, pageDigest, nextStateDigest)
            nextTokenDigestValue = tokenDigest(nextToken)
        resultDigest = _resultDigest(
            context.tokenDigest,
            context.pins,
            pageDigest,
            facts.rowCount,
            facts.byteCount,
            nextTokenDigestValue,
        )
        now = self._now()
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            current = connection.execute(
                "SELECT * FROM continuations WHERE token_digest=?",
                (context.tokenDigest,),
            ).fetchone()
            if current is None:
                raise ContinuationError("CONTINUATION_CLAIM_LOST")
            if current["status"] == "SUCCEEDED":
                return self._pageFromRow(connection, token, current, replayed=True)
            if current["status"] != "RUNNING" or current["owner_id"] != ownerId:
                raise ContinuationError("CONTINUATION_CLAIM_LOST")
            self._requireLiveRow(current, self._now())
            self._validatePins(self._pinsFromRow(current), context.pins)
        stagedPage = self._stageArtifact(envelope.payload, now=now)
        stagedNextState = None
        if encodedNextState is not None:
            stagedNextState = self._stageArtifact(encodedNextState, now=now)
            if stagedNextState.digest != nextStateDigest:
                raise ContinuationError("CONTINUATION_CORRUPT")
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            current = connection.execute(
                "SELECT * FROM continuations WHERE token_digest=?",
                (context.tokenDigest,),
            ).fetchone()
            if current is None:
                raise ContinuationError("CONTINUATION_CLAIM_LOST")
            if current["status"] == "SUCCEEDED":
                return self._pageFromRow(connection, token, current, replayed=True)
            if current["status"] != "RUNNING" or current["owner_id"] != ownerId:
                raise ContinuationError("CONTINUATION_CLAIM_LOST")
            commitNow = self._now()
            self._requireLiveRow(current, commitNow)
            self._validatePins(self._pinsFromRow(current), context.pins)
            if stagedPage.digest != pageDigest:
                raise ContinuationError("CONTINUATION_CORRUPT")
            if stagedNextState is not None and nextStateDigest is not None and nextTokenDigestValue is not None:
                try:
                    connection.execute(
                        "INSERT INTO continuations (token_digest, chain_root_digest, parent_token_digest, "
                        "state_digest, source_digest, query_digest, contract_digest, schema_digest, "
                        "issued_at, expires_at, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING')",
                        (
                            nextTokenDigestValue,
                            str(current["chain_root_digest"]),
                            context.tokenDigest,
                            nextStateDigest,
                            context.pins.sourceDigest,
                            context.pins.queryDigest,
                            context.pins.contractDigest,
                            context.pins.schemaDigest,
                            commitNow,
                            self._storedFloat(current["expires_at"]),
                        ),
                    )
                except sqlite3.IntegrityError as error:
                    if self._isTokenCollision(error):
                        raise ContinuationError("CONTINUATION_TOKEN_COLLISION") from None
                    raise ContinuationError("CONTINUATION_CORRUPT") from None
            changed = connection.execute(
                "UPDATE continuations SET status='SUCCEEDED', owner_id=NULL, lease_until=0, "
                "page_digest=?, row_count=?, byte_count=?, next_token_digest=?, next_state_digest=?, "
                "result_digest=?, completed_at=? WHERE token_digest=? AND status='RUNNING' AND owner_id=?",
                (
                    pageDigest,
                    facts.rowCount,
                    facts.byteCount,
                    nextTokenDigestValue,
                    nextStateDigest,
                    resultDigest,
                    commitNow,
                    context.tokenDigest,
                    ownerId,
                ),
            ).rowcount
            if changed != 1:
                raise ContinuationError("CONTINUATION_CLAIM_LOST")
            self._referenceArtifact(connection, stagedPage, now=commitNow)
            if stagedNextState is not None:
                self._referenceArtifact(connection, stagedNextState, now=commitNow)
            committed = connection.execute(
                "SELECT * FROM continuations WHERE token_digest=?",
                (context.tokenDigest,),
            ).fetchone()
            if committed is None:
                raise ContinuationError("CONTINUATION_CORRUPT")
            page = self._pageFromRow(connection, token, committed, replayed=False)
            if page.nextToken != nextToken:
                raise ContinuationError("CONTINUATION_CORRUPT")
            return page

    def redeem(
        self,
        token: str,
        pins: ContinuationPins,
        *,
        materialize: Callable[[ContinuationQueryState], PageEnvelope],
        waitSeconds: float | None = None,
    ) -> ContinuationPage:
        """동일 token에 owner 1회와 immutable page replay를 제공한다.

        Capabilities:
            thread와 process 경합에서 active owner 한 명과 committed page 하나를 보장한다.

        Args:
            token: opaque bearer token.
            pins: 현재 실행이 기대하는 exact pins.
            materialize: private state에서 Arrow IPC page를 만드는 pure callback.
            waitSeconds: caller가 허용한 owner 대기 상한. 정책 상한보다 길어질 수 없다.

        Returns:
            검증된 bounded page와 optional deterministic child token.

        Raises:
            ContinuationError: validation, owner, claim, payload 실패 시.

        Example:
            ``page = store.redeem(token, pins, materialize=owner)``.

        Guide:
            같은 token 재호출은 callback 없이 같은 CAS page를 반환한다.

        When:
            기존 data query 축이 token 하나를 실제 다음 page로 교환할 때 호출한다.

        How:
            context load, atomic claim, heartbeat, Arrow validation, CAS commit 순서로 실행한다.

        SeeAlso:
            ``loadContext``, ``pruneExpired``.

        Requires:
            callback은 side-effect free이고 sourceDigest가 고정한 source만 읽는다.

        AIContext:
            crash recovery는 callback 재실행 가능성이 있어 external side effect exactly-once가 아니다.
        """
        selectedWait = self.policy.waitSeconds
        if waitSeconds is not None:
            if type(waitSeconds) not in (int, float):
                raise ValueError("waitSeconds는 유한한 음수 아닌 수여야 합니다")
            try:
                callerWait = float(waitSeconds)
            except (OverflowError, TypeError, ValueError):
                raise ValueError("waitSeconds는 유한한 음수 아닌 수여야 합니다") from None
            if not math.isfinite(callerWait) or callerWait < 0:
                raise ValueError("waitSeconds는 유한한 음수 아닌 수여야 합니다")
            selectedWait = min(selectedWait, callerWait)
        deadline = time.monotonic() + selectedWait
        context = self._loadContext(
            token,
            busySeconds=max(0.0, deadline - time.monotonic()),
        )
        self._validatePins(context.pins, pins)
        ownerId = uuid.uuid4().hex
        while True:
            remaining = max(0.0, deadline - time.monotonic())
            try:
                status, _ = self._claim(
                    context.tokenDigest,
                    pins,
                    ownerId,
                    busySeconds=remaining,
                )
            except ContinuationError as error:
                if error.code != "CONTINUATION_BUSY":
                    raise
                status = "BUSY"
            if status == "REPLAY":
                return self._replay(
                    token,
                    pins,
                    busySeconds=max(0.0, deadline - time.monotonic()),
                )
            if status == "ACQUIRED":
                break
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ContinuationError("CONTINUATION_BUSY")
            time.sleep(min(self.policy.pollSeconds, remaining))
        try:
            with _LeaseHeartbeat(self, context.tokenDigest, ownerId) as heartbeat:
                try:
                    envelope = materialize(context.state)
                except ContinuationError:
                    raise
                except Exception:
                    recordFailure(_log, "CONTINUATION_OWNER_FAILED")
                    raise ContinuationError("CONTINUATION_OWNER_FAILED") from None
                if not isinstance(envelope, PageEnvelope):
                    raise ContinuationError("CONTINUATION_OWNER_FAILED")
                if heartbeat.lost:
                    raise ContinuationError("CONTINUATION_CLAIM_LOST")
                return self._commit(token, context, ownerId, envelope)
        except Exception:
            self._release(context.tokenDigest, ownerId)
            raise
