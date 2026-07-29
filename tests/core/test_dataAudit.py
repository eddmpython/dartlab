"""data lineage reader의 완전성 계약 회귀 테스트."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pytest

from dartlab.core.dataAudit import LineageReadError, appendLineage, readLineage

pytestmark = pytest.mark.unit


def test_readLineage_missingDirectoryIsEmpty(tmp_path) -> None:
    """아직 생성되지 않은 lineage 디렉터리는 기록 0건을 뜻한다."""
    assert readLineage(baseDir=tmp_path / "missing") == []


def test_readLineage_corruptJsonRaisesWithLocation(tmp_path) -> None:
    """손상 line을 빼고 부분 목록을 반환하지 않는다."""
    path = tmp_path / "2026-07-29.jsonl"
    valid = {"recordedAt": "2026-07-29T00:00:00+00:00", "source": "A"}
    path.write_text(json.dumps(valid) + "\n{broken\n", encoding="utf-8")

    with pytest.raises(LineageReadError, match=r"2026-07-29\.jsonl:2"):
        readLineage(sinceDays=3650, baseDir=tmp_path)


def test_readLineage_invalidUtf8RaisesTyped(tmp_path) -> None:
    """UTF-8이 아닌 lineage 파일도 raw decoder 오류로 새지 않는다."""
    path = tmp_path / "2026-07-29.jsonl"
    path.write_bytes(b"\xff\xfe")

    with pytest.raises(LineageReadError, match=r"2026-07-29\.jsonl"):
        readLineage(sinceDays=3650, baseDir=tmp_path)


def test_readLineage_fileReadFailureRaisesTyped(tmp_path, monkeypatch) -> None:
    """파일 접근 실패를 해당 파일의 기록 0건으로 축약하지 않는다."""
    path = tmp_path / "2026-07-29.jsonl"
    path.write_text("{}\n", encoding="utf-8")
    realOpen = Path.open

    def failTarget(self, *args, **kwargs):
        if self == path:
            raise PermissionError("simulated read failure")
        return realOpen(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", failTarget)

    with pytest.raises(LineageReadError, match=r"2026-07-29\.jsonl"):
        readLineage(sinceDays=3650, baseDir=tmp_path)


def test_readLineage_invalidRecordedAtRaisesWithLocation(tmp_path) -> None:
    """필수 timestamp가 없는 record를 오래된 항목처럼 건너뛰지 않는다."""
    path = tmp_path / "2026-07-29.jsonl"
    path.write_text(json.dumps({"source": "A"}) + "\n", encoding="utf-8")

    with pytest.raises(LineageReadError, match=r"2026-07-29\.jsonl:1"):
        readLineage(sinceDays=3650, baseDir=tmp_path)


def test_readLineage_sortsByInstantAcrossOffsets(tmp_path) -> None:
    """문자열이 아니라 실제 instant 순서로 정렬한다."""
    path = tmp_path / "2026-07-29.jsonl"
    records = [
        {"recordedAt": "2026-07-29T09:00:00+09:00", "source": "later"},
        {"recordedAt": "2026-07-28T23:30:00+00:00", "source": "earlier"},
    ]
    path.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")

    result = readLineage(sinceDays=3650, baseDir=tmp_path)

    assert [record["source"] for record in result] == ["earlier", "later"]


def test_appendLineage_preservesValidExplicitRecordedAt(tmp_path) -> None:
    """lower-level writer의 명시적 historical recordedAt 계약을 보존한다."""
    recordedAt = (dt.datetime.now(dt.UTC) - dt.timedelta(days=1)).isoformat()

    appendLineage({"recordedAt": recordedAt, "source": "historical"}, baseDir=tmp_path)

    result = readLineage(sinceDays=2, baseDir=tmp_path)
    assert result[0]["recordedAt"] == recordedAt


def test_appendLineage_rejectsInvalidExplicitRecordedAt(tmp_path) -> None:
    """strict reader가 읽을 수 없는 timestamp를 writer가 만들지 않는다."""
    with pytest.raises(ValueError, match="recordedAt"):
        appendLineage({"recordedAt": "garbage", "source": "broken"}, baseDir=tmp_path)
    assert list(tmp_path.glob("*.jsonl")) == []


def test_readLineage_rejectsInvalidSinceDays(tmp_path) -> None:
    """rolling window는 0 이상의 정수만 받는다."""
    with pytest.raises(ValueError, match="sinceDays"):
        readLineage(sinceDays=-1, baseDir=tmp_path)
    with pytest.raises(TypeError, match="sinceDays"):
        readLineage(sinceDays=True, baseDir=tmp_path)
