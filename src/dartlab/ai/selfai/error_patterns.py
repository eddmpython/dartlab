"""에러 패턴 DB — 코드 실행 에러를 분류하고 복구 힌트를 제공.

SQLite 기반. 에러 시그니처(정규화된 에러 메시지)로 유사 에러를 검색하고,
이전에 성공한 올바른 코드 패턴을 반환한다.

DB 위치: ~/.dartlab/selfai/error_patterns.db
"""

from __future__ import annotations

import logging
import re
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger(__name__)

_DB_DIR = Path.home() / ".dartlab" / "selfai"
_DB_PATH = _DB_DIR / "error_patterns.db"

# ── 에러 시그니처 정규화 ────────────────────────────────────

# 변수명, 종목코드, 숫자 등을 제거하여 에러의 본질만 추출
_NORMALIZE_PATTERNS = [
    (re.compile(r"'[A-Z0-9]{4,10}'"), "'<TICKER>'"),  # 종목코드
    (re.compile(r"'\d{6}'"), "'<CODE>'"),  # 6자리 코드
    (re.compile(r"line \d+"), "line <N>"),  # 줄 번호
    (re.compile(r"column \d+"), "column <N>"),  # 컬럼 번호
    (re.compile(r"0x[0-9a-f]+"), "<ADDR>"),  # 메모리 주소
    (re.compile(r"\d{4}-\d{2}-\d{2}"), "<DATE>"),  # 날짜
    (re.compile(r"\d+\.\d+"), "<FLOAT>"),  # 부동소수점
]


def _normalizeSignature(error_text: str) -> str:
    """에러 메시지를 정규화하여 시그니처로 변환."""
    # Traceback에서 마지막 에러 라인만 추출
    lines = error_text.strip().splitlines()
    # 마지막 의미있는 라인 (빈 줄 제외)
    sig = ""
    for line in reversed(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith("File ") and not stripped.startswith("Traceback"):
            sig = stripped
            break
    if not sig:
        sig = lines[-1] if lines else error_text[:200]

    # 변수명/숫자 정규화
    for pattern, replacement in _NORMALIZE_PATTERNS:
        sig = pattern.sub(replacement, sig)

    return sig[:500]


def _extractErrorType(error_text: str) -> str:
    """에러 텍스트에서 에러 타입 추출 (AttributeError, KeyError 등)."""
    for line in reversed(error_text.strip().splitlines()):
        line = line.strip()
        if "Error" in line and ":" in line:
            return line.split(":")[0].strip().split(".")[-1]
    return "Unknown"


# ── 데이터 클래스 ───────────────────────────────────────────


@dataclass
class ErrorPattern:
    """에러 패턴 레코드."""

    id: int
    error_type: str
    error_signature: str
    wrong_code: str
    correct_code: str
    tool_name: str
    frequency: int
    last_seen: float


# ── DB 관리 ─────────────────────────────────────────────────

_CREATE_SQL = """
CREATE TABLE IF NOT EXISTS error_pattern (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    error_type TEXT NOT NULL,
    error_signature TEXT NOT NULL,
    wrong_code TEXT NOT NULL DEFAULT '',
    correct_code TEXT NOT NULL DEFAULT '',
    tool_name TEXT NOT NULL DEFAULT '',
    frequency INTEGER NOT NULL DEFAULT 1,
    last_seen REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_signature ON error_pattern(error_signature);
CREATE INDEX IF NOT EXISTS idx_tool ON error_pattern(tool_name);
"""


def _getDb() -> sqlite3.Connection:
    """DB 연결. 없으면 생성."""
    _DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB_PATH), timeout=5)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(_CREATE_SQL)
    return conn


# ── 공개 API ────────────────────────────────────────────────


def lookup(error_text: str, *, limit: int = 3) -> list[ErrorPattern]:
    """에러 텍스트에서 유사 패턴을 검색.

    Args:
        error_text: 코드 실행 에러 출력 (traceback 포함)
        limit: 반환할 최대 패턴 수

    Returns:
        빈도순 정렬된 유사 패턴 리스트
    """
    sig = _normalizeSignature(error_text)
    error_type = _extractErrorType(error_text)

    try:
        conn = _getDb()
    except (sqlite3.OperationalError, OSError):
        return []

    try:
        # 1차: 정확한 시그니처 매칭
        rows = conn.execute(
            "SELECT * FROM error_pattern WHERE error_signature = ? ORDER BY frequency DESC LIMIT ?",
            (sig, limit),
        ).fetchall()

        # 2차: 에러 타입 매칭 (시그니처 매칭 부족 시)
        if len(rows) < limit and error_type != "Unknown":
            existing_ids = {r[0] for r in rows}
            type_rows = conn.execute(
                "SELECT * FROM error_pattern WHERE error_type = ? ORDER BY frequency DESC LIMIT ?",
                (error_type, limit * 2),
            ).fetchall()
            for r in type_rows:
                if r[0] not in existing_ids and len(rows) < limit:
                    rows.append(r)

        return [
            ErrorPattern(
                id=r[0],
                error_type=r[1],
                error_signature=r[2],
                wrong_code=r[3],
                correct_code=r[4],
                tool_name=r[5],
                frequency=r[6],
                last_seen=r[7],
            )
            for r in rows
        ]
    except sqlite3.OperationalError:
        return []
    finally:
        conn.close()


def record(
    error_text: str,
    wrong_code: str,
    correct_code: str = "",
    tool_name: str = "",
) -> None:
    """에러 패턴을 DB에 기록. 동일 시그니처면 빈도 증가.

    Args:
        error_text: 에러 출력 텍스트
        wrong_code: 에러를 발생시킨 코드
        correct_code: 올바른 코드 (있으면)
        tool_name: 관련 도구명
    """
    sig = _normalizeSignature(error_text)
    error_type = _extractErrorType(error_text)
    now = time.time()

    try:
        conn = _getDb()
    except (sqlite3.OperationalError, OSError):
        log.warning("error_patterns DB 접근 실패")
        return

    try:
        existing = conn.execute(
            "SELECT id, frequency FROM error_pattern WHERE error_signature = ? AND wrong_code = ?",
            (sig, wrong_code[:2000]),
        ).fetchone()

        if existing:
            conn.execute(
                "UPDATE error_pattern SET frequency = ?, last_seen = ?, correct_code = CASE WHEN ? != '' THEN ? ELSE correct_code END WHERE id = ?",
                (existing[1] + 1, now, correct_code, correct_code, existing[0]),
            )
        else:
            conn.execute(
                "INSERT INTO error_pattern (error_type, error_signature, wrong_code, correct_code, tool_name, frequency, last_seen) VALUES (?, ?, ?, ?, ?, 1, ?)",
                (error_type, sig, wrong_code[:2000], correct_code[:2000], tool_name, now),
            )
        conn.commit()
    except sqlite3.OperationalError:
        log.warning("error_patterns 기록 실패")
    finally:
        conn.close()


def seed_from_known_patterns() -> int:
    """audit에서 확인된 빈출 에러 패턴을 초기 seed로 삽입.

    Returns:
        삽입된 패턴 수
    """
    # audit 20라운드에서 확인된 반복 에러 패턴
    known = [
        {
            "error_type": "TypeError",
            "error_signature": "analysis() takes <N> positional arguments but 1 was given",
            "wrong_code": 'c.analysis("수익성")',
            "correct_code": 'c.analysis("financial", "수익성")',
            "tool_name": "analysis",
        },
        {
            "error_type": "TypeError",
            "error_signature": "analysis() missing 1 required positional argument",
            "wrong_code": 'c.analysis("성장성")',
            "correct_code": 'c.analysis("financial", "성장성")',
            "tool_name": "analysis",
        },
        {
            "error_type": "TypeError",
            "error_signature": "macro() got an unexpected keyword argument 'topic'",
            "wrong_code": 'dartlab.macro(topic="종합")',
            "correct_code": 'dartlab.macro("종합")',
            "tool_name": "macro",
        },
        {
            "error_type": "TypeError",
            "error_signature": "macro() got an unexpected keyword argument 'axis'",
            "wrong_code": 'dartlab.macro(axis="사이클")',
            "correct_code": 'dartlab.macro("사이클")',
            "tool_name": "macro",
        },
        {
            "error_type": "KeyError",
            "error_signature": "KeyError: 'cycle'",
            "wrong_code": 'result["cycle"]',
            "correct_code": "print(result.keys())  # 먼저 키 확인",
            "tool_name": "macro",
        },
        {
            "error_type": "KeyError",
            "error_signature": "KeyError: 'factors'",
            "wrong_code": 'result["factors"]',
            "correct_code": "print(result.keys())  # 먼저 키 확인",
            "tool_name": "macro",
        },
        {
            "error_type": "KeyError",
            "error_signature": "KeyError: 'narrative'",
            "wrong_code": 'result["narrative"]',
            "correct_code": "print(result.keys())  # 먼저 키 확인",
            "tool_name": "macro",
        },
        {
            "error_type": "AttributeError",
            "error_signature": "has no attribute 'empty'",
            "wrong_code": "df.empty",
            "correct_code": "len(df) == 0  # Polars는 .empty 없음",
            "tool_name": "polars",
        },
        {
            "error_type": "AttributeError",
            "error_signature": "has no attribute 'iterrows'",
            "wrong_code": "df.iterrows()",
            "correct_code": "df.iter_rows(named=True)  # Polars 문법",
            "tool_name": "polars",
        },
        {
            "error_type": "AttributeError",
            "error_signature": "has no attribute 'sort_values'",
            "wrong_code": 'df.sort_values("col")',
            "correct_code": 'df.sort("col")  # Polars 문법',
            "tool_name": "polars",
        },
        {
            "error_type": "AttributeError",
            "error_signature": "has no attribute 'to_dict'",
            "wrong_code": "df.to_dict()",
            "correct_code": "df.to_dicts()  # Polars는 to_dicts()",
            "tool_name": "polars",
        },
        {
            "error_type": "MemoryError",
            "error_signature": "c.sections",
            "wrong_code": "c.sections",
            "correct_code": 'c.show("IS")  # sections는 409MB. show(topic)으로 개별 조회',
            "tool_name": "company",
        },
        {
            "error_type": "TimeoutError",
            "error_signature": "scan join timeout",
            "wrong_code": "df1.join(df2, ...)",
            "correct_code": "# scan DataFrame join 금지 (타임아웃). 개별 scan 결과를 순차 해석",
            "tool_name": "scan",
        },
        {
            "error_type": "TypeError",
            "error_signature": "review() should be used only for explicit report requests",
            "wrong_code": 'c.review("수익성")',
            "correct_code": 'c.analysis("financial", "수익성")  # 분석에는 analysis 사용',
            "tool_name": "review",
        },
        {
            "error_type": "AttributeError",
            "error_signature": "has no attribute 'rename'",
            "wrong_code": 'df.rename({"old": "new"})',
            "correct_code": 'df.rename({"old": "new"})  # Polars rename은 동일하나 columns= 불필요',
            "tool_name": "polars",
        },
    ]

    count = 0
    try:
        conn = _getDb()
        for p in known:
            existing = conn.execute(
                "SELECT id FROM error_pattern WHERE error_signature = ? AND wrong_code = ?",
                (p["error_signature"], p["wrong_code"]),
            ).fetchone()
            if not existing:
                conn.execute(
                    "INSERT INTO error_pattern (error_type, error_signature, wrong_code, correct_code, tool_name, frequency, last_seen) VALUES (?, ?, ?, ?, ?, 5, ?)",
                    (
                        p["error_type"],
                        p["error_signature"],
                        p["wrong_code"],
                        p["correct_code"],
                        p["tool_name"],
                        time.time(),
                    ),
                )
                count += 1
        conn.commit()
        conn.close()
    except (sqlite3.OperationalError, OSError):
        log.warning("seed 삽입 실패")

    return count
