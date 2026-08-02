"""대화 본문을 저장하지 않는 Product Outcome 로컬 원장."""

from __future__ import annotations

import hashlib
import os
import sqlite3
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

OutcomeState = Literal["started", "scoped", "grounded", "delivered", "verified", "retained"]
OUTCOME_STATES: tuple[OutcomeState, ...] = (
    "started",
    "scoped",
    "grounded",
    "delivered",
    "verified",
    "retained",
)


def _nowIso() -> str:
    """현재 UTC 시각을 ISO 8601 문자열로 반환한다."""
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class OutcomeRecord:
    """민감한 AI 입출력 없이 결과 진행 상태만 표현한다.

    Capabilities: 결과 식별자, 기능, 상태, 시각을 직렬화한다.
    Args: outcomeId, feature, state, createdAt, updatedAt을 받는다.
    Returns: `toDict`가 JSON 직렬화 가능한 dict를 반환한다.
    Example: `OutcomeRecord("o", "ask", "started", now, now).toDict()`.
    Guide: AI 역할은 답변 내용 대신 결과 단계만 관찰하는 것이다.
    SeeAlso: `OutcomeStore`.
    Requires: 표준 라이브러리만 사용한다.
    AIContext: 질문, 답변, 모델, 토큰, 파일 경로를 이 계약에 추가하지 않는다.
    LLM Specifications: AntiPatterns=content capture; OutputSchema=five scalar fields;
        Prerequisites=opaque id; Freshness=updatedAt; Dataflow=service to store;
        TargetMarkets=all.
    """

    outcomeId: str
    feature: str
    state: OutcomeState
    createdAt: str
    updatedAt: str

    def toDict(self) -> dict[str, str]:
        """결과 레코드의 다섯 공개 필드를 dict로 반환한다."""
        return asdict(self)


class OutcomeStore:
    """순서가 보장된 SQLite 결과 원장을 관리한다.

    Capabilities: 시작, 단일 단계 전이, 조회, 익명 집계를 제공한다.
    Args: path는 SQLite 파일 경로다.
    Returns: 메서드별 OutcomeRecord 또는 집계 dict다.
    Example: `OutcomeStore(path).start("id", feature="ask")`.
    Guide: AI 역할은 실행 경계에서 상태만 전진시키는 것이다.
    SeeAlso: `startOutcome`, `verifyOutcomeEvidence`.
    Requires: 쓰기 가능한 로컬 디렉터리와 SQLite다.
    AIContext: 사용자 대화와 실행 세부정보를 저장하지 않는다.
    LLM Specifications: AntiPatterns=skipped transition and text storage;
        OutputSchema=OutcomeRecord; Prerequisites=opaque id; Freshness=transactional;
        Dataflow=runtime event to state; TargetMarkets=all.
    """

    def __init__(self, path: Path):
        self.path = path.expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as database:
            database.execute(
                """
                CREATE TABLE IF NOT EXISTS product_outcomes (
                    outcome_id TEXT PRIMARY KEY,
                    feature TEXT NOT NULL,
                    state TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            database.execute(
                "CREATE INDEX IF NOT EXISTS idx_product_outcomes_feature_state ON product_outcomes(feature, state)"
            )
            database.execute(
                """
                CREATE TABLE IF NOT EXISTS product_outcome_evidence (
                    outcome_id TEXT NOT NULL,
                    ref_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (outcome_id, ref_hash),
                    FOREIGN KEY (outcome_id) REFERENCES product_outcomes(outcome_id)
                )
                """
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        """commit과 close가 보장된 SQLite 연결을 연다."""
        database = sqlite3.connect(self.path, timeout=5.0)
        try:
            database.execute("PRAGMA journal_mode=WAL")
            yield database
            database.commit()
        finally:
            database.close()

    def start(self, outcomeId: str, *, feature: str) -> OutcomeRecord:
        """불투명 ID로 `started` 결과 레코드를 만든다."""
        if not outcomeId.strip() or not feature.strip():
            raise ValueError("outcomeId와 feature는 비어 있을 수 없습니다")
        stamp = _nowIso()
        with self._connect() as database:
            database.execute(
                "INSERT INTO product_outcomes(outcome_id, feature, state, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (outcomeId, feature, OUTCOME_STATES[0], stamp, stamp),
            )
        return OutcomeRecord(outcomeId, feature, OUTCOME_STATES[0], stamp, stamp)

    def advance(self, outcomeId: str, state: OutcomeState) -> OutcomeRecord:
        """결과를 바로 다음 상태로만 전진시킨다."""
        with self._connect() as database:
            row = database.execute(
                "SELECT feature, state, created_at FROM product_outcomes WHERE outcome_id = ?", (outcomeId,)
            ).fetchone()
            if row is None:
                raise KeyError(outcomeId)
            current = str(row[1])
            if state not in OUTCOME_STATES or OUTCOME_STATES.index(state) != OUTCOME_STATES.index(current) + 1:
                raise ValueError(f"허용되지 않은 결과 전이: {current} -> {state}")
            stamp = _nowIso()
            database.execute(
                "UPDATE product_outcomes SET state = ?, updated_at = ? WHERE outcome_id = ?",
                (state, stamp, outcomeId),
            )
        return OutcomeRecord(outcomeId, str(row[0]), state, str(row[2]), stamp)

    def get(self, outcomeId: str) -> OutcomeRecord:
        """현재 결과 레코드를 조회한다."""
        with self._connect() as database:
            row = database.execute(
                "SELECT feature, state, created_at, updated_at FROM product_outcomes WHERE outcome_id = ?",
                (outcomeId,),
            ).fetchone()
        if row is None:
            raise KeyError(outcomeId)
        return OutcomeRecord(outcomeId, str(row[0]), str(row[1]), str(row[2]), str(row[3]))  # type: ignore[arg-type]

    def registerEvidence(self, outcomeId: str, refIds: list[str]) -> int:
        """실제 tool 결과의 ref ID를 SHA-256 hash로만 등록한다."""
        refs = {self._refHash(value) for value in refIds if value.strip()}
        stamp = _nowIso()
        with self._connect() as database:
            if database.execute("SELECT 1 FROM product_outcomes WHERE outcome_id = ?", (outcomeId,)).fetchone() is None:
                raise KeyError(outcomeId)
            before = database.total_changes
            database.executemany(
                "INSERT OR IGNORE INTO product_outcome_evidence(outcome_id, ref_hash, created_at) VALUES (?, ?, ?)",
                ((outcomeId, refHash, stamp) for refHash in refs),
            )
            return database.total_changes - before

    def verifyEvidence(self, outcomeId: str, refId: str) -> OutcomeRecord:
        """delivered 결과의 정확한 ref receipt만 verified로 전진시킨다."""
        refHash = self._refHash(refId)
        with self._connect() as database:
            row = database.execute(
                "SELECT feature, state, created_at, updated_at FROM product_outcomes WHERE outcome_id = ?",
                (outcomeId,),
            ).fetchone()
            if row is None:
                raise KeyError(outcomeId)
            matched = database.execute(
                "SELECT 1 FROM product_outcome_evidence WHERE outcome_id = ? AND ref_hash = ?",
                (outcomeId, refHash),
            ).fetchone()
            if matched is None:
                raise KeyError("evidence ref가 이 outcome에 속하지 않습니다")
            current = str(row[1])
            if current in {"verified", "retained"}:
                return OutcomeRecord(outcomeId, str(row[0]), current, str(row[2]), str(row[3]))  # type: ignore[arg-type]
            if current != "delivered":
                raise ValueError(f"delivered 이전에는 verified로 전이할 수 없습니다: {current}")
            stamp = _nowIso()
            database.execute(
                "UPDATE product_outcomes SET state = 'verified', updated_at = ? WHERE outcome_id = ?",
                (stamp, outcomeId),
            )
        return OutcomeRecord(outcomeId, str(row[0]), "verified", str(row[2]), stamp)

    @staticmethod
    def _refHash(refId: str) -> str:
        """원본 evidence ref ID를 저장용 SHA-256 digest로 바꾼다."""
        value = refId.strip()
        if not value:
            raise ValueError("refId는 비어 있을 수 없습니다")
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    def snapshot(self, *, feature: str | None = None) -> dict[str, object]:
        """질문과 답변을 제외한 상태별 익명 집계를 반환한다."""
        query = "SELECT state, COUNT(*) FROM product_outcomes"
        params: tuple[str, ...] = ()
        if feature:
            query += " WHERE feature = ?"
            params = (feature,)
        query += " GROUP BY state"
        with self._connect() as database:
            rows = database.execute(query, params).fetchall()
        counts = {state: 0 for state in OUTCOME_STATES}
        for state, count in rows:
            if state in counts:
                counts[state] = int(count)
        return {"total": sum(counts.values()), "states": counts}


_DEFAULT_STORE: OutcomeStore | None = None


def _storePath() -> Path:
    """환경 설정 또는 사용자 DartLab 디렉터리의 DB 경로를 반환한다."""
    configured = os.environ.get("DARTLAB_OUTCOME_DB")
    return Path(configured) if configured else Path.home() / ".dartlab" / "productOutcome.sqlite3"


def _defaultStore() -> OutcomeStore:
    """현재 설정 경로와 일치하는 프로세스 공유 저장소를 반환한다."""
    global _DEFAULT_STORE
    path = _storePath().expanduser().resolve()
    if _DEFAULT_STORE is None or _DEFAULT_STORE.path != path:
        _DEFAULT_STORE = OutcomeStore(path)
    return _DEFAULT_STORE


def startOutcome(*, feature: str = "ask", outcomeId: str | None = None) -> OutcomeRecord:
    """새 `started` 결과 레코드를 만든다."""
    return _defaultStore().start(outcomeId or uuid.uuid4().hex, feature=feature)


def advanceOutcome(outcomeId: str, state: OutcomeState) -> OutcomeRecord:
    """결과를 바로 다음 상태로 전진시킨다."""
    return _defaultStore().advance(outcomeId, state)


def registerOutcomeEvidence(outcomeId: str, refIds: list[str]) -> int:
    """실제 tool 결과의 evidence receipt를 등록한다."""
    return _defaultStore().registerEvidence(outcomeId, refIds)


def verifyOutcomeEvidence(outcomeId: str, refId: str) -> OutcomeRecord:
    """사용자가 연 정확한 evidence receipt를 검증한다."""
    return _defaultStore().verifyEvidence(outcomeId, refId)


def outcomeSnapshot(*, feature: str | None = None) -> dict[str, object]:
    """로컬 content-free 결과 집계를 반환한다."""
    return _defaultStore().snapshot(feature=feature)


__all__ = [
    "OUTCOME_STATES",
    "OutcomeRecord",
    "OutcomeState",
    "OutcomeStore",
    "advanceOutcome",
    "outcomeSnapshot",
    "registerOutcomeEvidence",
    "startOutcome",
    "verifyOutcomeEvidence",
]
