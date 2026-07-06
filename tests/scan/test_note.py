"""scanNote 런타임 reader 테스트.

임시 parquet + monkeypatch 로 read 경로를 결정적으로 검증한다 (네트워크·베이크 불요).
"""

from __future__ import annotations

import polars as pl
import pytest

import dartlab.scan.note as note_mod
from dartlab.scan.note import _NOTE_READ_SCHEMA, scanNote, scanNoteList

pytestmark = pytest.mark.unit


def _writeNote(tmp_path, bare: str, df: pl.DataFrame) -> None:
    noteDir = tmp_path / "note"
    noteDir.mkdir(exist_ok=True)
    df.write_parquet(str(noteDir / f"{bare}.parquet"))


def test_reads_note_parquet_with_valueNum(tmp_path, monkeypatch):
    df = pl.DataFrame(
        {
            "stockCode": ["005930", "005930", "000660"],
            "account": ["상품", "제품", "제품"],
            "label": ["상품", "제품", "제품"],
            "period": ["2024", "2024", "2024"],
            "value": ["1,000", "△500", "2,000"],
        }
    )
    _writeNote(tmp_path, "inventory", df)
    monkeypatch.setattr(note_mod, "_ensureScanData", lambda **_: tmp_path)

    out = scanNote("재고자산")  # 한글 label -> inventory
    assert out.height == 3
    assert set(out.columns) == set(_NOTE_READ_SCHEMA)
    got = {(r["stockCode"], r["account"]): r["valueNum"] for r in out.iter_rows(named=True)}
    assert got[("005930", "상품")] == 1000.0
    assert got[("005930", "제품")] == -500.0  # 삼각형 음수 파싱
    assert got[("000660", "제품")] == 2000.0


def test_resolves_conceptId_bareName_and_label(tmp_path, monkeypatch):
    df = pl.DataFrame(
        {
            "stockCode": ["005930"],
            "account": ["당기법인세"],
            "label": ["당기법인세"],
            "period": ["2024"],
            "value": ["100"],
        }
    )
    _writeNote(tmp_path, "tax", df)
    monkeypatch.setattr(note_mod, "_ensureScanData", lambda **_: tmp_path)

    for key in ("tax", "note.tax", "법인세"):
        out = scanNote(key)
        assert out.height == 1, f"resolve 실패: {key}"


def test_missing_file_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(note_mod, "_ensureScanData", lambda **_: tmp_path)

    def _boom(scanDir, rel):
        raise RuntimeError("no remote file")

    monkeypatch.setattr(note_mod, "_downloadScanFile", _boom)

    out = scanNote("재고자산")
    assert out.height == 0
    assert set(out.columns) == set(_NOTE_READ_SCHEMA)


def test_unknown_concept_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(note_mod, "_ensureScanData", lambda **_: tmp_path)
    out = scanNote("존재하지않는개념xyz")
    assert out.height == 0
    assert set(out.columns) == set(_NOTE_READ_SCHEMA)


def test_scanNoteList_shape():
    rows = scanNoteList()
    assert rows, "scanNoteList 비었음"
    assert all({"name", "label", "conceptId", "disclosureKey"} <= set(r) for r in rows)
    names = {r["name"] for r in rows}
    assert "inventory" in names and "tax" in names
