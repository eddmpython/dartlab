"""Published source changes must reach catalogs even after a producer was interrupted."""

from __future__ import annotations

import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest

pytestmark = pytest.mark.unit


def test_reconcileDownloadsOnlyUnindexedBytesAtPinnedRevision(monkeypatch, tmp_path):
    import huggingface_hub

    from dartlab.pipeline import searchCatalog as mod

    payloads = {"005930": b"new half-year", "000660": b"already indexed", "005380": b"new company"}
    entries = [
        SimpleNamespace(
            path=f"dart/panel/{code}.parquet",
            size=len(data),
            lfs=SimpleNamespace(sha256=hashlib.sha256(data).hexdigest()),
        )
        for code, data in payloads.items()
    ]
    calls = []

    class Api:
        def list_repo_tree(self, repo, prefix, **kwargs):
            assert kwargs["revision"] == "pinned"
            return entries

    def download(url, path, token):
        assert "/resolve/pinned/" in url
        calls.append(path.name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payloads[path.stem])
        return path.stat().st_size

    monkeypatch.setattr(huggingface_hub, "HfApi", lambda **kwargs: Api())
    monkeypatch.setattr(mod, "_download", download)
    manifest = {
        "files": [
            {"path": "data/dart/panel/000660.parquet", "sha256": entries[1].lfs.sha256},
            {"path": "data/dart/panel/005930.parquet", "hash": "legacy-digest"},
        ]
    }
    batches = list(mod.reconcileSourceFiles("dartPanel", manifest, repo="repo", revision="pinned", workDir=tmp_path))
    paths = [path for batch in batches for path in batch]
    assert {path.name for path in paths} == {"005930.parquet", "005380.parquet"}
    assert set(calls) == {path.name for path in paths}
    assert all(not path.exists() for path in paths)


def test_reconcileRejectsCorruptDownload(monkeypatch, tmp_path):
    import huggingface_hub

    from dartlab.pipeline import searchCatalog as mod

    entry = SimpleNamespace(
        path="dart/panel/005930.parquet", size=3, lfs=SimpleNamespace(sha256=hashlib.sha256(b"yes").hexdigest())
    )
    monkeypatch.setattr(
        huggingface_hub, "HfApi", lambda **kwargs: SimpleNamespace(list_repo_tree=lambda *args, **kwargs: [entry])
    )

    def download(url, path, token):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"bad")
        return 3

    monkeypatch.setattr(mod, "_download", download)
    with pytest.raises(ValueError, match="SHA256 mismatch"):
        list(mod.reconcileSourceFiles("dartPanel", {}, repo="repo", revision="pinned", workDir=tmp_path))
