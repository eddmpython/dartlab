"""CLI 대화 히스토리 — SQLite 기반 세션 연속.

`dartlab ask --continue "다음 질문"` 형태로 이전 대화를 이어간다.
"""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any


def _db_path() -> Path:
    p = Path.home() / ".dartlab" / "chat.db"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_db_path()))
    conn.execute(
        """CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_code TEXT NOT NULL,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        )"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL REFERENCES sessions(id),
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at REAL NOT NULL
        )"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS token_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER REFERENCES sessions(id),
            provider TEXT NOT NULL,
            model TEXT,
            input_tokens INTEGER DEFAULT 0,
            output_tokens INTEGER DEFAULT 0,
            cost_usd REAL DEFAULT 0,
            created_at REAL NOT NULL
        )"""
    )
    conn.commit()
    return conn


def get_latest_session(stock_code: str) -> int | None:
    """해당 종목의 최근 세션 ID."""
    conn = _connect()
    row = conn.execute(
        "SELECT id FROM sessions WHERE stock_code = ? ORDER BY updated_at DESC LIMIT 1",
        (stock_code,),
    ).fetchone()
    conn.close()
    return row[0] if row else None


def create_session(stock_code: str) -> int:
    """새 세션 생성."""
    conn = _connect()
    now = time.time()
    cur = conn.execute(
        "INSERT INTO sessions (stock_code, created_at, updated_at) VALUES (?, ?, ?)",
        (stock_code, now, now),
    )
    session_id = cur.lastrowid
    conn.commit()
    conn.close()
    return session_id


def add_message(session_id: int, role: str, content: str) -> None:
    """세션에 메시지 추가."""
    conn = _connect()
    now = time.time()
    conn.execute(
        "INSERT INTO messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
        (session_id, role, content, now),
    )
    conn.execute(
        "UPDATE sessions SET updated_at = ? WHERE id = ?",
        (now, session_id),
    )
    conn.commit()
    conn.close()


def get_messages(session_id: int) -> list[dict[str, str]]:
    """세션의 전체 메시지."""
    conn = _connect()
    rows = conn.execute(
        "SELECT role, content FROM messages WHERE session_id = ? ORDER BY created_at",
        (session_id,),
    ).fetchall()
    conn.close()
    return [{"role": r, "content": c} for r, c in rows]


def record_usage(
    session_id: int | None,
    provider: str,
    model: str | None = None,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cost_usd: float = 0.0,
) -> None:
    """토큰 사용량 기록."""
    conn = _connect()
    conn.execute(
        "INSERT INTO token_usage (session_id, provider, model, input_tokens, output_tokens, cost_usd, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (session_id, provider, model, input_tokens, output_tokens, cost_usd, time.time()),
    )
    conn.commit()
    conn.close()


def get_total_usage() -> dict[str, Any]:
    """누적 사용량 통계."""
    conn = _connect()
    row = conn.execute(
        "SELECT COUNT(*), COALESCE(SUM(input_tokens), 0), COALESCE(SUM(output_tokens), 0), COALESCE(SUM(cost_usd), 0) FROM token_usage"
    ).fetchone()
    conn.close()
    return {
        "총_요청수": row[0],
        "입력_토큰": row[1],
        "출력_토큰": row[2],
        "총_비용_USD": round(row[3], 4),
    }
