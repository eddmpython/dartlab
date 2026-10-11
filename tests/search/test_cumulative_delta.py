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
    # 문서 2 개 중 1 개 변경은 50% 다. 자동 compaction 임계를 넘기지 않게 올려 일간 delta 경로만 본다.
    monkeypatch.setenv("DARTLAB_SEARCH_AUTO_COMPACTION_RATIO", "0.9")

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


def test_build_script_compacts_main_when_cumulative_delta_exceeds_ratio(tmp_path, monkeypatch) -> None:
    """누적 delta 가 active 대비 임계를 넘으면 일간 실행도 main 을 압축하고 delta 를 비운다.

    압축 크기 128MB 예산 시절에는 compaction 이 한 번도 돌지 못해 delta 가 105 만 행까지 쌓였다(2026-10).
    """
    import dartlab.config as cfg
    from dartlab.providers.dart.search.catalog import normalizeCatalogRows

    monkeypatch.setattr(cfg, "dataDir", str(tmp_path / "data"))
    basePath = tmp_path / "base.parquet"
    currentPath = tmp_path / "current.parquet"
    normalizeCatalogRows(
        [{"source": "allFilings", "rcept_no": f"R{i}", "text": f"document {i}", "date": "20260701"} for i in range(4)]
    ).write_parquet(basePath)
    normalizeCatalogRows(
        [{"source": "allFilings", "rcept_no": f"R{i}", "text": f"document {i}", "date": "20260701"} for i in range(4)]
        + [
            {"source": "allFilings", "rcept_no": f"N{i}", "text": f"new filing {i}", "date": "20261010"}
            for i in range(2)
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
                "dataAsOf": "20261010",
                "builtAt": "2026-10-10T00:00:00Z",
                "files": [{"path": "x.parquet", "rowCount": 6}],
                "totalRows": 6,
                "changedRows": 2,
                "deletedRows": 0,
                "producer": "test",
            }
        ),
        encoding="utf-8",
    )
    script = Path(__file__).resolve().parents[2] / ".github" / "scripts" / "search" / "buildSearchMain.py"
    spec = importlib.util.spec_from_file_location("buildSearchMainCompactionTest", script)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setenv("DARTLAB_SEARCH_SOURCE_MANIFESTS", str(manifestPath))
    monkeypatch.setenv("DARTLAB_SEARCH_EXPECTED_SOURCES", "allFilings")
    monkeypatch.delenv("FORCE_FULL", raising=False)
    monkeypatch.setenv("DARTLAB_SEARCH_AUTO_COMPACTION_RATIO", "0.25")

    monkeypatch.setenv("DARTLAB_SEARCH_CURRENT_CATALOG", str(basePath))
    assert mod._buildMainFromCatalog("catalog") == 4
    outDir = Path(cfg.dataDir) / "dart" / "contentIndex"

    monkeypatch.setenv("DARTLAB_SEARCH_CURRENT_CATALOG", str(currentPath))
    assert mod._buildMainFromCatalog("catalog") == 6  # 2/6 = 33% > 25%

    assert not (outDir / "delta.postings.bin").exists()
    assert json.loads((outDir / "main_info.json").read_text(encoding="utf-8"))["nDocs"] == 6
    assert (outDir / "main_catalog_snapshot.parquet").read_bytes() == currentPath.read_bytes()


def test_compaction_budget_counts_rows_not_compressed_bytes(tmp_path, monkeypatch) -> None:
    import polars as pl

    script = Path(__file__).resolve().parents[2] / ".github" / "scripts" / "search" / "buildSearchMain.py"
    spec = importlib.util.spec_from_file_location("buildSearchMainBudgetTest", script)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    path = tmp_path / "catalog.parquet"
    pl.DataFrame({"searchText": ["본문" * 5000] * 50}).write_parquet(path)
    monkeypatch.delenv("DARTLAB_SEARCH_ALLOW_UNBOUNDED_COMPACTION", raising=False)
    monkeypatch.setenv("DARTLAB_SEARCH_MAX_COMPACTION_ROWS", "100")
    assert mod._catalogCompactionAllowed(path) is True
    monkeypatch.setenv("DARTLAB_SEARCH_MAX_COMPACTION_ROWS", "10")
    assert mod._catalogCompactionAllowed(path) is False
