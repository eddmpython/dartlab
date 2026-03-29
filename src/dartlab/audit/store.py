"""감사 결과 저장소 — SQLite 메타 + parquet 결과 + JSON review."""

from __future__ import annotations

import json
import sqlite3
from datetime import date
from pathlib import Path
from typing import Any

import polars as pl


def _defaultDataDir() -> Path:
    """프로젝트 data/audit/ (레포 내부 저장)."""
    # src/dartlab/audit/store.py → 5단계 상위 = 프로젝트 루트
    repoRoot = Path(__file__).resolve().parents[3]
    return repoRoot / "data" / "audit"


# ── SQLite 스키마 ──

_CREATE_RUN = """
CREATE TABLE IF NOT EXISTS auditRun (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stockCode TEXT NOT NULL,
    corpName TEXT DEFAULT '',
    sector TEXT DEFAULT '',
    runDate TEXT NOT NULL,
    engineVersion TEXT DEFAULT '',
    totalCalcs INTEGER DEFAULT 0,
    okCalcs INTEGER DEFAULT 0,
    coverageRate REAL DEFAULT 0.0,
    durationSec REAL DEFAULT 0.0,
    status TEXT DEFAULT 'complete'
)
"""

_CREATE_ISSUE = """
CREATE TABLE IF NOT EXISTS auditIssue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    runId INTEGER REFERENCES auditRun(id),
    category TEXT DEFAULT '',
    severity TEXT DEFAULT 'info',
    axis TEXT DEFAULT '',
    blockKey TEXT DEFAULT '',
    description TEXT DEFAULT '',
    resolved INTEGER DEFAULT 0,
    resolvedNote TEXT DEFAULT ''
)
"""

_CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_run_stock ON auditRun(stockCode)",
    "CREATE INDEX IF NOT EXISTS idx_run_date ON auditRun(runDate)",
    "CREATE INDEX IF NOT EXISTS idx_issue_run ON auditIssue(runId)",
    "CREATE INDEX IF NOT EXISTS idx_issue_cat ON auditIssue(category)",
]


class AuditStore:
    """감사 결과 저장소 — SQLite + parquet + JSON."""

    def __init__(self, dataDir: Path | None = None):
        self._dataDir = dataDir or _defaultDataDir()
        self._dbPath = self._dataDir / "audit.db"
        self._conn: sqlite3.Connection | None = None

    def _ensureDb(self) -> sqlite3.Connection:
        """lazy init — 첫 호출 시에만 DB 생성."""
        if self._conn is not None:
            return self._conn
        self._dataDir.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self._dbPath))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(_CREATE_RUN)
        conn.execute(_CREATE_ISSUE)
        for idx in _CREATE_INDEXES:
            conn.execute(idx)
        conn.commit()
        self._conn = conn
        return conn

    # ── 실행 기록 ──

    def saveRun(
        self,
        *,
        stockCode: str,
        corpName: str = "",
        sector: str = "",
        runDate: str = "",
        engineVersion: str = "",
        totalCalcs: int = 0,
        okCalcs: int = 0,
        durationSec: float = 0.0,
        status: str = "complete",
    ) -> int:
        """감사 실행 기록을 저장하고 runId를 반환한다."""
        conn = self._ensureDb()
        if not runDate:
            runDate = date.today().isoformat()
        coverageRate = okCalcs / totalCalcs if totalCalcs > 0 else 0.0
        cursor = conn.execute(
            """INSERT INTO auditRun
               (stockCode, corpName, sector, runDate, engineVersion,
                totalCalcs, okCalcs, coverageRate, durationSec, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (stockCode, corpName, sector, runDate, engineVersion,
             totalCalcs, okCalcs, coverageRate, durationSec, status),
        )
        conn.commit()
        return cursor.lastrowid  # type: ignore[return-value]

    def saveIssues(self, runId: int, issues: list[dict[str, Any]]) -> None:
        """감사 이슈 목록을 저장한다."""
        if not issues:
            return
        conn = self._ensureDb()
        conn.executemany(
            """INSERT INTO auditIssue
               (runId, category, severity, axis, blockKey, description)
               VALUES (?, ?, ?, ?, ?, ?)""",
            [
                (
                    runId,
                    iss.get("category", ""),
                    iss.get("severity", "info"),
                    iss.get("axis", ""),
                    iss.get("blockKey", ""),
                    iss.get("description", ""),
                )
                for iss in issues
            ],
        )
        conn.commit()

    # ── parquet 저장 ──

    def saveParquet(
        self,
        *,
        stockCode: str,
        corpName: str,
        runDate: str,
        rows: list[dict[str, Any]],
    ) -> Path:
        """분석 결과를 parquet으로 저장한다."""
        if not runDate:
            runDate = date.today().isoformat()
        dayDir = self._dataDir / runDate
        dayDir.mkdir(parents=True, exist_ok=True)

        for row in rows:
            row.setdefault("stockCode", stockCode)
            row.setdefault("corpName", corpName)
            row.setdefault("runDate", runDate)

        df = pl.DataFrame(rows)
        outPath = dayDir / f"{stockCode}.parquet"
        df.write_parquet(outPath)
        return outPath

    # ── review JSON 저장 ──

    def saveReviewJson(
        self,
        *,
        stockCode: str,
        runDate: str,
        reviewJson: str,
    ) -> Path:
        """review JSON을 저장한다."""
        if not runDate:
            runDate = date.today().isoformat()
        dayDir = self._dataDir / runDate
        dayDir.mkdir(parents=True, exist_ok=True)
        outPath = dayDir / f"{stockCode}_review.json"
        outPath.write_text(reviewJson, encoding="utf-8")
        return outPath

    # ── 조회 ──

    def queryRuns(
        self,
        stockCode: str | None = None,
        runDate: str | None = None,
        limit: int = 100,
    ) -> pl.DataFrame:
        """감사 실행 기록을 조회한다."""
        conn = self._ensureDb()
        query = "SELECT * FROM auditRun WHERE 1=1"
        params: list[Any] = []
        if stockCode:
            query += " AND stockCode = ?"
            params.append(stockCode)
        if runDate:
            query += " AND runDate = ?"
            params.append(runDate)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        cursor = conn.execute(query, params)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        if not rows:
            return pl.DataFrame(schema={c: pl.Utf8 for c in columns})
        return pl.DataFrame([dict(zip(columns, row)) for row in rows])

    def queryIssues(
        self,
        runId: int | None = None,
        resolved: bool | None = None,
        category: str | None = None,
        limit: int = 500,
    ) -> pl.DataFrame:
        """감사 이슈를 조회한다."""
        conn = self._ensureDb()
        query = "SELECT * FROM auditIssue WHERE 1=1"
        params: list[Any] = []
        if runId is not None:
            query += " AND runId = ?"
            params.append(runId)
        if resolved is not None:
            query += " AND resolved = ?"
            params.append(1 if resolved else 0)
        if category:
            query += " AND category = ?"
            params.append(category)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        cursor = conn.execute(query, params)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        if not rows:
            return pl.DataFrame(schema={c: pl.Utf8 for c in columns})
        return pl.DataFrame([dict(zip(columns, row)) for row in rows])

    def queryParquet(
        self,
        stockCode: str,
        runDate: str | None = None,
    ) -> pl.DataFrame | None:
        """특정 기업의 parquet 결과를 읽는다."""
        if runDate:
            path = self._dataDir / runDate / f"{stockCode}.parquet"
            if path.exists():
                return pl.read_parquet(path)
            return None

        # 최신 날짜 자동 탐색
        candidates = sorted(self._dataDir.glob(f"*/{stockCode}.parquet"), reverse=True)
        if candidates:
            return pl.read_parquet(candidates[0])
        return None

    def completedCodes(self, runDate: str | None = None) -> set[str]:
        """오늘(또는 지정 날짜) 완료된 종목코드 set."""
        conn = self._ensureDb()
        if not runDate:
            runDate = date.today().isoformat()
        cursor = conn.execute(
            "SELECT DISTINCT stockCode FROM auditRun WHERE runDate = ? AND status = 'complete'",
            (runDate,),
        )
        return {row[0] for row in cursor.fetchall()}

    def coverageSummary(self, runDate: str | None = None) -> pl.DataFrame:
        """축별 coverage 통계."""
        if not runDate:
            runDate = date.today().isoformat()
        dayDir = self._dataDir / runDate
        if not dayDir.exists():
            return pl.DataFrame()

        parquets = list(dayDir.glob("*.parquet"))
        if not parquets:
            return pl.DataFrame()

        dfs = [pl.read_parquet(p) for p in parquets]
        combined = pl.concat(dfs)

        return (
            combined
            .group_by("axis", "blockKey")
            .agg(
                pl.col("status").count().alias("total"),
                (pl.col("status") == "ok").sum().alias("ok"),
                (pl.col("status") == "none").sum().alias("none"),
                (pl.col("status") == "error").sum().alias("error"),
            )
            .with_columns(
                (pl.col("ok") / pl.col("total") * 100).round(1).alias("coveragePct")
            )
            .sort("axis", "blockKey")
        )

    # ── 정리 ──

    def close(self) -> None:
        """DB 연결 종료."""
        if self._conn:
            self._conn.close()
            self._conn = None
