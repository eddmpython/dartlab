"""분석 메모리 저장소 — SQLite 기반 세션 간 영속.

Company 객체(200~500MB)는 저장하지 않는다.
stockCode + 시점 + 질문 요약 + 결과 요약만 저장하여 메모리 안전.
"""

from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

_DB_FILENAME = "analysisMemory.db"
_MAX_DB_SIZE_MB = 50
_MAX_SUMMARY_CHARS = 500

# 싱글턴 인스턴스
_instance: AnalysisMemory | None = None


@dataclass(frozen=True)
class MemoryRecord:
    """저장된 분석 기록."""

    stockCode: str
    question: str
    questionType: str
    resultSummary: str
    timestamp: float
    grade: str | None = None
    keyMetrics: str = ""


class AnalysisMemory:
    """SQLite 기반 분석 히스토리 저장소."""

    def __init__(self, dbPath: Path | None = None) -> None:
        if dbPath is None:
            dbPath = Path.home() / ".dartlab" / _DB_FILENAME
        self._dbPath = dbPath
        self._conn: sqlite3.Connection | None = None

    def _ensureDb(self) -> sqlite3.Connection:
        """lazy init — AI 분석 시에만 연결."""
        if self._conn is not None:
            return self._conn

        self._dbPath.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self._dbPath), timeout=5)
        conn.execute(
            """CREATE TABLE IF NOT EXISTS analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stockCode TEXT NOT NULL,
                question TEXT NOT NULL,
                questionType TEXT DEFAULT '',
                resultSummary TEXT DEFAULT '',
                grade TEXT DEFAULT '',
                timestamp REAL NOT NULL
            )"""
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_stock ON analysis(stockCode)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ts ON analysis(timestamp)")
        conn.commit()
        self._conn = conn
        return conn

    def _ensureKeyMetricsColumn(self, conn: sqlite3.Connection) -> None:
        """keyMetrics 컬럼이 없으면 추가 (기존 DB 마이그레이션)."""
        try:
            conn.execute("SELECT keyMetrics FROM analysis LIMIT 1")
        except sqlite3.OperationalError:
            conn.execute("ALTER TABLE analysis ADD COLUMN keyMetrics TEXT DEFAULT ''")
            conn.commit()

    def saveAnalysis(
        self,
        stockCode: str,
        question: str,
        questionType: str = "",
        resultSummary: str = "",
        grade: str | None = None,
        keyMetrics: str = "",
    ) -> None:
        """분석 결과 저장.

        keyMetrics: 핵심 수치 구조화 문자열 (예: "ROE=12.3%|영업이익률=8.9%|등급=dCR-AA+")
        """
        conn = self._ensureDb()
        self._ensureKeyMetricsColumn(conn)
        summary = resultSummary[:_MAX_SUMMARY_CHARS] if resultSummary else ""
        metrics = keyMetrics[:500] if keyMetrics else ""
        conn.execute(
            "INSERT INTO analysis (stockCode, question, questionType, resultSummary, grade, keyMetrics, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (stockCode, question[:200], questionType, summary, grade or "", metrics, time.time()),
        )
        conn.commit()
        self._enforceSizeLimit(conn)

    def recallForStock(
        self,
        stockCode: str,
        limit: int = 5,
        decayDays: int = 90,
    ) -> list[MemoryRecord]:
        """종목별 최근 분석 기록 조회 (시간 감쇠 적용)."""
        conn = self._ensureDb()
        self._ensureKeyMetricsColumn(conn)
        cutoff = time.time() - (decayDays * 86400)
        rows = conn.execute(
            "SELECT stockCode, question, questionType, resultSummary, timestamp, grade, keyMetrics "
            "FROM analysis WHERE stockCode = ? AND timestamp > ? "
            "ORDER BY timestamp DESC LIMIT ?",
            (stockCode, cutoff, limit),
        ).fetchall()
        return [
            MemoryRecord(
                stockCode=r[0],
                question=r[1],
                questionType=r[2],
                resultSummary=r[3],
                timestamp=r[4],
                grade=r[5] or None,
                keyMetrics=r[6] or "",
            )
            for r in rows
        ]

    def toPromptContext(self, stockCode: str) -> str:
        """이전 분석 기록을 프롬프트용 텍스트로 변환.

        keyMetrics가 있으면 핵심 수치를 포함하여 멀티턴 참조 가능.
        """
        records = self.recallForStock(stockCode)
        if not records:
            return ""
        lines = ["## 이전 분석 기록"]
        for r in records:
            import datetime

            dt = datetime.datetime.fromtimestamp(r.timestamp).strftime("%Y-%m-%d")
            grade_str = f" [등급: {r.grade}]" if r.grade else ""
            lines.append(f"- **{dt}** ({r.questionType}){grade_str}: {r.question}")
            if r.keyMetrics:
                lines.append(f"  📊 {r.keyMetrics}")
            elif r.resultSummary:
                lines.append(f"  → {r.resultSummary[:200]}")
        return "\n".join(lines)

    def _enforceSizeLimit(self, conn: sqlite3.Connection) -> None:
        """DB 크기 제한 — 초과 시 오래된 레코드 삭제."""
        try:
            dbSize = self._dbPath.stat().st_size / (1024 * 1024)
            if dbSize > _MAX_DB_SIZE_MB:
                conn.execute(
                    "DELETE FROM analysis WHERE id IN (SELECT id FROM analysis ORDER BY timestamp ASC LIMIT 100)"
                )
                conn.execute("VACUUM")
                conn.commit()
        except OSError:
            pass

    def close(self) -> None:
        """연결 종료."""
        if self._conn:
            self._conn.close()
            self._conn = None


def getMemory() -> AnalysisMemory:
    """싱글턴 메모리 인스턴스."""
    global _instance
    if _instance is None:
        _instance = AnalysisMemory()
    return _instance
