"""dataAudit — sync / prebuild 단계 data lineage 추적 (T7-2).

데이터 거버넌스 KPI 의 핵심: *어떤 데이터가 언제 어느 source 에서 다운로드됐는지*
추적 가능한 audit trail. HF dataset version + sync workflow 진입 시점에 자동 호출.

저장 위치: ``data/_lineage/{date}.jsonl`` (gitignored, 로컬 디버그용).
HF dataset metadata 동기화는 후속 (T7-5 와 통합).

API:
    recordLineage(source, version, downloadedAt, hash) -> Path  # 단일 항목
    appendLineage(record) -> Path  # dict 형식
    readLineage(since, source) -> list[dict]

Example::

    from dartlab.core.dataAudit import recordLineage
    recordLineage(
        source="DART OpenAPI list",
        version="2026-05-23",
        downloadedAt="2026-05-23T17:00:00Z",
        recordHash="sha256:abc123...",
    )

스키마 (jsonl 한 줄):
    {
        "recordedAt": ISO,
        "source": str,
        "version": str,
        "downloadedAt": ISO,
        "recordHash": str,
        "rowCount": int (optional),
        "extra": dict (optional)
    }
"""

from __future__ import annotations

import datetime as dt
import json
import os
import stat
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from dartlab.core.logger import logEvent


class LineageReadError(RuntimeError):
    """lineage 저장소를 완전하게 읽거나 검증하지 못한 경우."""

    def __init__(self, message: str, *, path: Path, lineNumber: int | None = None) -> None:
        location = f"{path}:{lineNumber}" if lineNumber is not None else str(path)
        super().__init__(f"{message}: {location}")
        self.path = path
        self.lineNumber = lineNumber


def _parseRecordedAt(value: object) -> dt.datetime:
    if not isinstance(value, str) or not value.strip():
        raise TypeError("recordedAt must be a non-empty string")
    recorded = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if recorded.tzinfo is None or recorded.utcoffset() is None:
        raise ValueError("recordedAt must include a timezone")
    return recorded


def _lineageFiles(baseDir: Path) -> list[Path]:
    try:
        directoryStat = baseDir.stat()
    except FileNotFoundError:
        return []
    except OSError as exc:
        raise LineageReadError("lineage 디렉터리 접근 실패", path=baseDir) from exc
    if not stat.S_ISDIR(directoryStat.st_mode):
        raise LineageReadError("lineage 경로가 디렉터리가 아닙니다", path=baseDir)
    try:
        return sorted(baseDir.glob("*.jsonl"))
    except OSError as exc:
        raise LineageReadError("lineage 파일 목록 조회 실패", path=baseDir) from exc


def _parseLineageRecord(line: str, *, path: Path, lineNumber: int) -> tuple[dt.datetime, dict[str, Any]]:
    try:
        record = json.loads(line)
    except json.JSONDecodeError as exc:
        raise LineageReadError("lineage JSON 파싱 실패", path=path, lineNumber=lineNumber) from exc
    if not isinstance(record, dict):
        raise LineageReadError("lineage record가 object가 아닙니다", path=path, lineNumber=lineNumber)
    try:
        recorded = _parseRecordedAt(record.get("recordedAt"))
    except (TypeError, ValueError) as exc:
        raise LineageReadError("lineage recordedAt 파싱 실패", path=path, lineNumber=lineNumber) from exc
    return recorded, record


def _readLineageFile(path: Path) -> Iterator[tuple[dt.datetime, dict[str, Any]]]:
    try:
        with path.open(encoding="utf-8") as stream:
            for lineNumber, line in enumerate(stream, start=1):
                stripped = line.strip()
                if stripped:
                    yield _parseLineageRecord(stripped, path=path, lineNumber=lineNumber)
    except LineageReadError:
        raise
    except (OSError, UnicodeDecodeError) as exc:
        raise LineageReadError("lineage 파일 읽기 실패", path=path) from exc


def _defaultLineageDir() -> Path:
    """기본 lineage 저장 디렉터리.

    ``DARTLAB_LINEAGE_DIR`` env override 가능. 기본 ``data/_lineage/`` (cwd 기준).
    """
    custom = os.getenv("DARTLAB_LINEAGE_DIR")
    if custom:
        return Path(custom)
    return Path.cwd() / "data" / "_lineage"


def _todayFile(baseDir: Path | None = None) -> Path:
    """오늘 날짜 jsonl 파일 경로."""
    baseDir = baseDir or _defaultLineageDir()
    today = dt.datetime.now(dt.UTC).strftime("%Y-%m-%d")
    return baseDir / f"{today}.jsonl"


def _emitLineageEvent(record: dict[str, Any]) -> None:
    """T1-1 logEvent 통합 — lineage 기록 시 구조화 이벤트 발급."""
    logEvent(
        "info",
        "data_lineage_recorded",
        source=record.get("source", ""),
        version=record.get("version", ""),
        row_count=record.get("rowCount", -1),
    )


def appendLineage(record: dict[str, Any], *, baseDir: Path | None = None) -> Path:
    """단일 lineage 항목을 오늘자 jsonl 에 append (T10-4).

    Capabilities:
        dict 형식 record 를 그대로 jsonl line append. recordLineage 의 lower-level
        API — 임의 metadata 전달 가능.

    Args:
        record: lineage dict.
        baseDir: 저장 root override (테스트용).

    Returns:
        쓰여진 jsonl 파일 경로.

    Example:
        >>> from dartlab.core.dataAudit import appendLineage
        >>> appendLineage({"source": "custom", "value": 42})

    Guide:
        recordLineage 가 더 strict (필수 필드 명시). appendLineage 는 자유.

    SeeAlso:
        recordLineage: 사용자 친화 wrapper.
        readLineage: 조회.

    Requires:
        쓰기 권한.

    AIContext:
        T7-2 데이터 거버넌스 트랙 lower-level entry.

    Raises:
        OSError: 디스크 쓰기 실패.
        ValueError: 명시한 recordedAt이 timezone-aware ISO datetime이 아닌 경우.
    """
    record = {"recordedAt": dt.datetime.now(dt.UTC).isoformat(), **record}
    try:
        _parseRecordedAt(record["recordedAt"])
    except (TypeError, ValueError) as exc:
        raise ValueError("recordedAt must be a timezone-aware ISO datetime") from exc
    filePath = _todayFile(baseDir)
    filePath.parent.mkdir(parents=True, exist_ok=True)
    with filePath.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    _emitLineageEvent(record)  # T1-1 structured log 발급
    return filePath


def recordLineage(
    source: str,
    *,
    version: str = "",
    downloadedAt: str = "",
    recordHash: str = "",
    rowCount: int | None = None,
    extra: dict[str, Any] | None = None,
    baseDir: Path | None = None,
) -> Path:
    """data lineage 단일 항목 기록 — 사용자 친화 wrapper (T10-4).

    Capabilities:
        sync workflow / prebuild 단계 진입 시 *어떤 source 의 어떤 version* 이
        언제 다운로드됐는지 jsonl line append. T7-2 (데이터 거버넌스) 의 단일
        진입점.

    Args:
        source: 데이터 source 식별자 (예: "DART OpenAPI list", "FRED FEDFUNDS").
        version: 데이터 버전 (날짜 또는 semver).
        downloadedAt: ISO datetime. 빈 문자열이면 현재 시각.
        recordHash: sha256 등 무결성 hash.
        rowCount: 행 수 (선택).
        extra: 추가 메타 dict (선택).
        baseDir: 저장 root override (테스트용).

    Returns:
        쓰여진 jsonl 파일 Path (오늘자).

    Example:
        >>> recordLineage(
        ...     source="DART OpenAPI",
        ...     version="2026-05-23",
        ...     downloadedAt="2026-05-23T17:00:00Z",
        ...     recordHash="sha256:abc",
        ...     rowCount=4123,
        ... )

    Guide:
        sync workflow 안 `.github/scripts/sync/*.py` 의 `main()` 진입 시점에
        호출. prebuild 는 본 함수 호출 금지 (offline guard 정합).

    SeeAlso:
        appendLineage: dict 직접 append.
        readLineage: 조회.
        dataDriftCheck (T7-5): drift 검출.

    Requires:
        data/_lineage/ 쓰기 권한. DARTLAB_LINEAGE_DIR env override 가능.

    AIContext:
        T7-2 (데이터 거버넌스 KPI) 가중 25 percent 의 핵심 신호. metrics workflow
        T1-2 가 시계열로 수집.

    Raises:
        OSError: 디스크 쓰기 실패.
    """
    record: dict[str, Any] = {
        "source": source,
        "version": version,
        "downloadedAt": downloadedAt or dt.datetime.now(dt.UTC).isoformat(),
        "recordHash": recordHash,
    }
    if rowCount is not None:
        record["rowCount"] = rowCount
    if extra:
        record["extra"] = dict(extra)
    return appendLineage(record, baseDir=baseDir)


def readLineage(
    *,
    sinceDays: int = 30,
    source: str | None = None,
    baseDir: Path | None = None,
) -> list[dict[str, Any]]:
    """저장된 lineage 조회 — 최근 N 일 + source 필터 옵션 (T10-4).

    Capabilities:
        data/_lineage/{date}.jsonl 파일들을 읽어 rolling window 안 record 만
        반환. metrics workflow (T1-2) 가 본 함수로 시계열 수집.

    Args:
        sinceDays: rolling window 일 수 (기본 30).
        source: 특정 source 만 (None 이면 전체).
        baseDir: 저장 root override.

    Returns:
        시간 순서 (recordedAt asc) 정렬된 dict 리스트.

    Example:
        >>> from dartlab.core.dataAudit import readLineage
        >>> records = readLineage(sinceDays=7, source="DART OpenAPI")
        >>> for r in records:
        ...     print(r["recordedAt"], r["version"])

    Guide:
        대용량 lineage 시 sinceDays 축소 권장. baseDir 미지정 시 cwd 기준.

    SeeAlso:
        recordLineage / appendLineage.
        dataDriftCheck (T7-5): drift 검출.

    Requires:
        data/_lineage/ 존재 (없으면 빈 리스트).

    AIContext:
        T7-2 데이터 거버넌스 트랙. metrics workflow 통합.

    Raises:
        TypeError: sinceDays가 정수가 아닌 경우.
        ValueError: sinceDays가 음수인 경우.
        LineageReadError: lineage 경로, 파일, JSON 또는 timestamp가 손상된 경우.
    """
    if isinstance(sinceDays, bool) or not isinstance(sinceDays, int):
        raise TypeError("sinceDays must be an integer")
    if sinceDays < 0:
        raise ValueError("sinceDays must be greater than or equal to zero")
    resolvedBaseDir = baseDir or _defaultLineageDir()
    cutoff = dt.datetime.now(dt.UTC) - dt.timedelta(days=sinceDays)
    records: list[tuple[dt.datetime, dict[str, Any]]] = []
    for jsonlFile in _lineageFiles(resolvedBaseDir):
        for recorded, record in _readLineageFile(jsonlFile):
            if recorded < cutoff:
                continue
            if source and record.get("source") != source:
                continue
            records.append((recorded, record))
    records.sort(key=lambda item: item[0])
    return [record for _, record in records]


__all__ = ["LineageReadError", "appendLineage", "recordLineage", "readLineage"]
