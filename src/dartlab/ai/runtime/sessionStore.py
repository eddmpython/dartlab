"""네이티브 transcript를 복제하지 않는 세션 매핑 저장소."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from .contracts import RuntimeSession, nowIso


class SessionStore:
    """DartLab ID와 CLI 소유 네이티브 ID만 SQLite에 보관한다."""

    def __init__(self, path: Path):
        self.path = path.expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as database:
            database.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_sessions (
                    session_id TEXT PRIMARY KEY,
                    runtime_id TEXT NOT NULL,
                    native_session_id TEXT NOT NULL,
                    cwd TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            database.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_preferences (
                    preference_key TEXT PRIMARY KEY,
                    preference_value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        """Sig: _connect() -> Iterator[sqlite3.Connection].

        Args: 없음.
        Returns: commit과 close를 보장하는 연결이다.
        Raises: sqlite3.Error if opening fails.
        Example: `with store._connect() as database: ...`.
        """
        database = sqlite3.connect(self.path, timeout=5.0)
        try:
            database.execute("PRAGMA journal_mode=WAL")
            yield database
            database.commit()
        finally:
            database.close()

    def save(self, session: RuntimeSession) -> RuntimeSession:
        """Sig: save(session) -> RuntimeSession.

        Args: session은 저장할 ID 매핑이다.
        Returns: 저장된 세션이다.
        Example: `store.save(session)`.
        """
        with self._connect() as database:
            database.execute(
                """
                INSERT INTO agent_sessions(session_id, runtime_id, native_session_id, cwd, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    runtime_id=excluded.runtime_id,
                    native_session_id=excluded.native_session_id,
                    cwd=excluded.cwd,
                    updated_at=excluded.updated_at
                """,
                (
                    session.sessionId,
                    session.runtimeId,
                    session.nativeSessionId,
                    session.cwd,
                    session.createdAt,
                    session.updatedAt,
                ),
            )
        return session

    def get(self, sessionId: str) -> RuntimeSession | None:
        """Sig: get(sessionId) -> RuntimeSession | None.

        Args: sessionId는 DartLab 세션 ID다.
        Returns: 저장된 매핑 또는 None이다.
        Example: `session = store.get("s")`.
        """
        with self._connect() as database:
            row = database.execute(
                "SELECT runtime_id, native_session_id, cwd, created_at, updated_at "
                "FROM agent_sessions WHERE session_id = ?",
                (sessionId,),
            ).fetchone()
        if row is None:
            return None
        return RuntimeSession(sessionId, str(row[0]), str(row[1]), str(row[2]), str(row[3]), str(row[4]))

    def touch(self, sessionId: str, nativeSessionId: str) -> None:
        """Sig: touch(sessionId, nativeSessionId) -> None.

        Args: DartLab ID와 CLI가 갱신한 네이티브 ID다.
        Returns: None.
        Example: `store.touch("s", "native")`.
        """
        with self._connect() as database:
            database.execute(
                "UPDATE agent_sessions SET native_session_id = ?, updated_at = ? WHERE session_id = ?",
                (nativeSessionId, nowIso(), sessionId),
            )

    def list(self, *, limit: int = 100) -> list[RuntimeSession]:
        """Sig: list(*, limit=100) -> list[RuntimeSession].

        Args: limit는 최신순 최대 개수다.
        Returns: 저장된 세션 매핑 목록이다.
        Example: `sessions = store.list(limit=10)`.
        """
        with self._connect() as database:
            rows = database.execute(
                "SELECT session_id, runtime_id, native_session_id, cwd, created_at, updated_at "
                "FROM agent_sessions ORDER BY updated_at DESC LIMIT ?",
                (max(1, min(limit, 1000)),),
            ).fetchall()
        return [RuntimeSession(*(str(value) for value in row)) for row in rows]

    def delete(self, sessionId: str) -> None:
        """Sig: delete(sessionId) -> None.

        Args: 삭제할 DartLab 세션 ID다.
        Returns: None.
        Example: `store.delete("s")`.
        """
        with self._connect() as database:
            database.execute("DELETE FROM agent_sessions WHERE session_id = ?", (sessionId,))

    def getPreference(self, key: str) -> str | None:
        """서버가 소유하는 로컬 런타임 선호값을 읽는다."""
        with self._connect() as database:
            row = database.execute(
                "SELECT preference_value FROM agent_preferences WHERE preference_key = ?",
                (key,),
            ).fetchone()
        return str(row[0]) if row else None

    def setPreference(self, key: str, value: str) -> None:
        """로컬 런타임 선호값을 원자적으로 저장한다."""
        with self._connect() as database:
            database.execute(
                """
                INSERT INTO agent_preferences(preference_key, preference_value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(preference_key) DO UPDATE SET
                    preference_value=excluded.preference_value,
                    updated_at=excluded.updated_at
                """,
                (key, value, nowIso()),
            )
