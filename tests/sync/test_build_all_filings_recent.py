from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import polars as pl

_SCRIPT = Path(__file__).resolve().parents[2] / ".github" / "scripts" / "sync" / "buildAllFilingsRecent.py"


def _loadModule():
    spec = importlib.util.spec_from_file_location("buildAllFilingsRecentForTest", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _frame(rows: list[tuple[str, str, str]]) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "stock_code": [row[0] for row in rows],
            "corp_name": ["회사"] * len(rows),
            "rcept_dt": [row[1] for row in rows],
            "report_nm": ["주요사항보고서"] * len(rows),
            "rcept_no": [row[2] for row in rows],
            "flr_nm": ["제출인"] * len(rows),
        }
    )


def test_bootstrap_reads_legacy_once_and_writes_code_buckets(monkeypatch, tmp_path: Path) -> None:
    mod = _loadModule()
    local = _frame([("005930", "20260717", "new-00"), ("035420", "20260717", "new-03")])
    legacy = _frame([("005930", "20260716", "old-00"), ("068270", "20260716", "old-06")])
    monkeypatch.setattr(mod, "_allFilingsDir", lambda: tmp_path)
    monkeypatch.setattr(mod, "_localFrame", lambda: local)
    monkeypatch.setattr(mod, "_remoteManifest", lambda: None)
    monkeypatch.setattr(mod, "_legacyFrame", lambda: legacy)
    monkeypatch.setattr(mod, "_feedFrame", lambda: None)

    result = mod.build()

    assert result.bootstrap is True
    assert set(result.partitions) == {"00", "03", "06"}
    assert pl.read_parquet(result.partitions["00"])["rcept_no"].to_list() == ["new-00", "old-00"]
    manifest = json.loads(result.manifestPath.read_text(encoding="utf-8"))
    assert manifest["layout"] == "stockCodePrefix2"
    assert manifest["partitionCount"] == 3
    assert manifest["totalRows"] == 4


def test_incremental_build_reads_only_touched_remote_bucket(monkeypatch, tmp_path: Path) -> None:
    mod = _loadModule()
    local = _frame([("005930", "20260717", "new-00")])
    oldBucket = _frame([("005930", "20260716", "old-00")])
    feed = _frame([("035420", "20260716", "feed-03")])
    previous = {
        "formatVersion": 1,
        "partitions": [
            {"bucket": "00", "file": "00_recent.parquet", "rows": 1, "maxDate": "20260716"},
            {"bucket": "03", "file": "03_recent.parquet", "rows": 7, "maxDate": "20260716"},
        ],
    }
    calls: list[str] = []

    def partitionFrame(bucket: str) -> pl.DataFrame | None:
        calls.append(bucket)
        return oldBucket if bucket == "00" else None

    monkeypatch.setattr(mod, "_allFilingsDir", lambda: tmp_path)
    monkeypatch.setattr(mod, "_localFrame", lambda: local)
    monkeypatch.setattr(mod, "_remoteManifest", lambda: previous)
    monkeypatch.setattr(mod, "_legacyFrame", lambda: (_ for _ in ()).throw(AssertionError("legacy read")))
    monkeypatch.setattr(mod, "_partitionFrame", partitionFrame)
    monkeypatch.setattr(mod, "_feedFrame", lambda: feed)

    result = mod.build()

    assert result.bootstrap is False
    assert calls == ["00"]
    assert set(result.partitions) == {"00"}
    assert set(pl.read_parquet(result.partitions["00"])["rcept_no"].to_list()) == {"new-00", "old-00"}
    manifest = json.loads(result.manifestPath.read_text(encoding="utf-8"))
    assert manifest["partitionCount"] == 2
    assert manifest["totalRows"] == 9
    assert set(pl.read_parquet(result.feedPath)["rcept_no"].to_list()) == {"new-00", "feed-03"}
