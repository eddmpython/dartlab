from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import polars as pl

from dartlab.providers.dart.search.catalog import normalizeCatalogRows
from dartlab.providers.dart.search.catalogDeltaIo import (
    catalogDeltaSummaryFromPaths,
    exportDeltaRowsForContentIndexFromPaths,
    filterCatalogByDate,
)


def _write(path: Path, rows: list[dict]) -> None:
    normalizeCatalogRows(rows).write_parquet(path)


def test_parquet_delta_is_fingerprint_streamed_and_keeps_tombstones(tmp_path, monkeypatch) -> None:
    previous = tmp_path / "previous.parquet"
    current = tmp_path / "current.parquet"
    payload = "대규모 본문 " * 1000
    _write(
        previous,
        [
            {"source": "allFilings", "rcept_no": "A", "text": payload},
            {"source": "news", "url": "https://n.test/b", "title": "old"},
            {"source": "allFilings", "rcept_no": "C", "text": "deleted later"},
        ],
    )
    _write(
        current,
        [
            {"source": "allFilings", "rcept_no": "A", "text": payload},
            {"source": "news", "url": "https://n.test/b", "title": "new"},
            {
                "source": "allFilings",
                "sourceRef": "fallback-ref",
                "sectionKey": "fallback-title",
                "rcept_dt": "20260717",
                "text": "brand new",
            },
        ],
    )

    def _eagerReadForbidden(*args, **kwargs):
        raise AssertionError("catalog delta must not eagerly read full parquet snapshots")

    monkeypatch.setattr(pl, "read_parquet", _eagerReadForbidden)
    summary = catalogDeltaSummaryFromPaths(previous, current)
    delta = exportDeltaRowsForContentIndexFromPaths(previous, current)

    assert summary == {
        "newDocs": 1,
        "changedDocs": 1,
        "deletedDocs": 1,
        "unchangedDocs": 1,
        "totalCurrentDocs": 3,
        "totalPreviousDocs": 3,
    }
    rows = {row["rcept_no"] or row["sourceRef"]: row for row in delta.iter_rows(named=True)}
    assert set(rows) == {"news:bb0957515b5d0638", "fallback-ref", "C"}
    assert rows["C"]["deleted"] is True
    assert rows["C"]["section_content"] == ""
    assert rows["fallback-ref"]["deleted"] is False
    assert rows["fallback-ref"]["section_title"] == "fallback-title"
    assert rows["fallback-ref"]["sourceDataAsOf"] == "20260717"


def test_filter_catalog_by_date_streams_to_atomic_parquet(tmp_path) -> None:
    source = tmp_path / "source.parquet"
    out = tmp_path / "lite.parquet"
    _write(
        source,
        [
            {"source": "allFilings", "rcept_no": "A", "rcept_dt": "20250101", "text": "old"},
            {"source": "allFilings", "rcept_no": "B", "rcept_dt": "2026-06-01", "text": "new"},
        ],
    )

    assert filterCatalogByDate(source, out, "20260101") == 1
    assert pl.read_parquet(out).get_column("rceptNo").to_list() == ["B"]
    assert not (tmp_path / "lite.parquet.tmp").exists()


def test_bootstrap_promotes_only_a_no_delta_catalog_matching_main(tmp_path) -> None:
    modulePath = Path(".github/scripts/search/buildSearchMain.py")
    spec = importlib.util.spec_from_file_location("buildSearchMainMemoryTest", modulePath)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    indexDir = tmp_path / "contentIndex"
    indexDir.mkdir()
    previous = indexDir / "catalog_snapshot.parquet"
    _write(
        previous,
        [
            {"source": "allFilings", "rcept_no": "A", "text": "a"},
            {"source": "allFilings", "rcept_no": "B", "text": "b"},
        ],
    )
    (indexDir / "main.postings.bin").write_bytes(b"main")
    (indexDir / "main_info.json").write_text(json.dumps({"nDocs": 2}), encoding="utf-8")
    (indexDir / "previous_manifest.json").write_text(json.dumps({"hasDelta": False}), encoding="utf-8")
    target = indexDir / "main_catalog_snapshot.parquet"

    assert module._bootstrapMainCatalog(indexDir, target, previous) is True
    assert target.read_bytes() == previous.read_bytes()

    target.unlink()
    (indexDir / "previous_manifest.json").write_text(json.dumps({"hasDelta": True}), encoding="utf-8")
    assert module._bootstrapMainCatalog(indexDir, target, previous) is False
    assert not target.exists()
