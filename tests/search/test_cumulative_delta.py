from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


def test_cumulative_delta_overrides_changed_and_deleted_main_rows(tmp_path, monkeypatch) -> None:
    import polars as pl

    import dartlab.config as cfg

    monkeypatch.setattr(cfg, "dataDir", str(tmp_path))
    monkeypatch.setenv("DARTLAB_NO_HF_DOWNLOAD", "1")
    from dartlab.providers.dart.search import fieldIndex as FI
    from dartlab.providers.dart.search import fieldIndexRebuild as FIR
    from dartlab.providers.dart.search.catalog import normalizeCatalogRows
    from dartlab.providers.dart.search.pipeline import exportDeltaRowsForContentIndex

    monkeypatch.setattr(FIR, "_HF_CONTENTINDEX_ATTEMPTED", True, raising=False)
    FI.clearCache()

    base = normalizeCatalogRows(
        [
            {"source": "allFilings", "rcept_no": "A", "text": "olduniqueterm", "date": "20260701"},
            {"source": "allFilings", "rcept_no": "B", "text": "deleteduniqueterm", "date": "20260701"},
        ]
    )
    current = normalizeCatalogRows(
        [
            {"source": "allFilings", "rcept_no": "A", "text": "newuniqueterm", "date": "20260717"},
            {"source": "allFilings", "rcept_no": "C", "text": "addeduniqueterm", "date": "20260717"},
        ]
    )
    FIR.rebuildMainFromCatalog(base, showProgress=False)
    deltaRows = exportDeltaRowsForContentIndex(base, current)
    assert deltaRows.height == 3
    assert deltaRows.filter(pl.col("deleted")).height == 1

    FIR.rebuildDeltaFromCatalog(deltaRows)
    manifest = FIR.writeIndexManifest(FI._contentIndexDir(), buildCommand="test.cumulativeDelta")
    FI.clearCache()

    assert FI.searchContent("olduniqueterm").is_empty()
    assert FI.searchContent("deleteduniqueterm").is_empty()
    assert FI.searchContent("newuniqueterm")["rcept_no"].to_list() == ["A"]
    assert FI.searchContent("addeduniqueterm")["rcept_no"].to_list() == ["C"]
    assert manifest["hasDelta"] is True
    assert manifest["deletedDocs"] == 1
    assert manifest["nDocsByTier"]["full"] == 2
    assert "delta_overrides.json" in manifest["requiredFiles"]
    stored = json.loads((FI._contentIndexDir() / "delta_overrides.json").read_text(encoding="utf-8"))
    assert any(row.get("deleted") for row in stored)


def test_build_script_keeps_main_bytes_unchanged_on_daily_catalog_change(tmp_path, monkeypatch) -> None:
    import dartlab.config as cfg
    from dartlab.providers.dart.search.catalog import normalizeCatalogRows

    monkeypatch.setattr(cfg, "dataDir", str(tmp_path / "data"))
    basePath = tmp_path / "base.parquet"
    currentPath = tmp_path / "current.parquet"
    normalizeCatalogRows(
        [
            {"source": "allFilings", "rcept_no": "A", "text": "base document", "date": "20260701"},
            {"source": "allFilings", "rcept_no": "B", "text": "stable document", "date": "20260701"},
        ]
    ).write_parquet(basePath)
    normalizeCatalogRows(
        [
            {"source": "allFilings", "rcept_no": "A", "text": "changed document", "date": "20260717"},
            {"source": "allFilings", "rcept_no": "B", "text": "stable document", "date": "20260701"},
        ]
    ).write_parquet(currentPath)
    manifestPath = tmp_path / "allFilings.source_manifest.json"
    manifestPath.write_text(
        json.dumps(
            {
                "source": "allFilings",
                "sourceVersion": "v1",
                "schemaVersion": "2026-07",
                "snapshotScope": "full",
                "dataAsOf": "20260717",
                "builtAt": "2026-07-17T00:00:00Z",
                "files": [{"path": "x.parquet", "rowCount": 2}],
                "totalRows": 2,
                "changedRows": 1,
                "deletedRows": 0,
                "producer": "test",
            }
        ),
        encoding="utf-8",
    )
    script = Path(__file__).resolve().parents[2] / ".github" / "scripts" / "search" / "buildSearchMain.py"
    spec = importlib.util.spec_from_file_location("buildSearchMainDeltaTest", script)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setenv("DARTLAB_SEARCH_SOURCE_MANIFESTS", str(manifestPath))
    monkeypatch.setenv("DARTLAB_SEARCH_EXPECTED_SOURCES", "allFilings")
    monkeypatch.delenv("FORCE_FULL", raising=False)

    monkeypatch.setenv("DARTLAB_SEARCH_CURRENT_CATALOG", str(basePath))
    assert mod._buildMainFromCatalog("catalog") == 2
    outDir = Path(cfg.dataDir) / "dart" / "contentIndex"
    mainBefore = (outDir / "main.postings.bin").read_bytes()

    monkeypatch.setenv("DARTLAB_SEARCH_CURRENT_CATALOG", str(currentPath))
    assert mod._buildMainFromCatalog("catalog") == 2

    assert (outDir / "main.postings.bin").read_bytes() == mainBefore
    assert (outDir / "delta.postings.bin").exists()
    assert (outDir / "catalog_snapshot.parquet").read_bytes() == currentPath.read_bytes()
    assert (outDir / "main_catalog_snapshot.parquet").read_bytes() == basePath.read_bytes()
