"""대화 본문 없이 exact evidence projection만 보존하는 작은 저장소."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

_MAX_EVIDENCE_BYTES = 64 * 1024


class EvidenceStore:
    """서버 재시작 뒤에도 사용자가 본 근거를 다시 확인할 수 있게 한다."""

    def __init__(self, path: Path, *, maxRows: int = 4096):
        self.path = path.expanduser().resolve()
        self.maxRows = max(128, maxRows)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as database:
            database.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_evidence (
                    outcome_id TEXT NOT NULL,
                    ref_id TEXT NOT NULL,
                    detail_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY(outcome_id, ref_id)
                )
                """
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        database = sqlite3.connect(self.path, timeout=5.0)
        try:
            database.execute("PRAGMA journal_mode=WAL")
            yield database
            database.commit()
        finally:
            database.close()

    def save(self, outcomeId: str, detail: dict[str, Any]) -> None:
        """공개 projection 한 건을 upsert하고 오래된 row를 제한한다."""
        refId = str(detail.get("id") or "")
        if not outcomeId or not refId:
            return
        encoded = json.dumps(detail, ensure_ascii=False, separators=(",", ":"), default=str)
        if len(encoded.encode("utf-8")) > _MAX_EVIDENCE_BYTES:
            raise ValueError("evidence projection exceeds 64 KiB")
        with self._connect() as database:
            database.execute(
                """
                INSERT INTO agent_evidence(outcome_id, ref_id, detail_json)
                VALUES (?, ?, ?)
                ON CONFLICT(outcome_id, ref_id) DO UPDATE SET
                    detail_json=excluded.detail_json,
                    created_at=CURRENT_TIMESTAMP
                """,
                (outcomeId, refId, encoded),
            )
            database.execute(
                """
                DELETE FROM agent_evidence WHERE rowid IN (
                    SELECT rowid FROM agent_evidence
                    ORDER BY created_at DESC, rowid DESC
                    LIMIT -1 OFFSET ?
                )
                """,
                (self.maxRows,),
            )

    def get(self, outcomeId: str, refId: str) -> dict[str, Any] | None:
        """outcome과 exact ref가 모두 일치하는 projection만 반환한다."""
        with self._connect() as database:
            row = database.execute(
                "SELECT detail_json FROM agent_evidence WHERE outcome_id = ? AND ref_id = ?",
                (outcomeId, refId),
            ).fetchone()
        if row is None:
            return None
        value = json.loads(str(row[0]))
        return value if isinstance(value, dict) else None
